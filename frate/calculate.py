from django.db.models import Sum, Value, OuterRef, Count, Min, Max, Subquery
from django.db.models.functions import Coalesce
from .models import Department, Role, Slot, Schedule
from .sft.models import Shift
from .empl.models import Employee
from .ver.models import Version


def empl_ver_hours_by_period (empl, sch, ver):

    if isinstance(empl, str):
        empl = Employee.objects.get(slug=empl)
    if isinstance(sch, str):
        sch = Schedule.objects.get(slug=sch)
    if isinstance(ver, str):
        ver = Version.objects.get(n=ver, schedule=sch)

    prds = set(ver.workdays.values_list('pd_id', flat=True))
    data = {}
    for prd in prds:
        data[prd] = ver.slots.filter(employee=empl, workday__pd_id=prd) \
                            .aggregate(shift__hours__sum=Coalesce(
                                    Sum('shift__hours'),
                                    Value(0)))['shift__hours__sum']
    return data


def version_inequity(sch, ver):

    schedule = Schedule.objects.get(slug=sch)
    version = Version.objects.get(n=ver, schedule=schedule)

    enrolled_employees = version.schedule.employees.filter(enrolled_in_inequity_monitoring=True)

    from django.db.models import IntegerField
    enrolled_employees = enrolled_employees.annotate(
        unfavorables=Subquery(
            version.slots.filter(shift__phase__rank__gt=1, employee=OuterRef('pk')).values('employee').annotate(
                cnt=Count('employee')).values('cnt'),
            output_field=IntegerField(),
        )
    )

    max_unfavorables = enrolled_employees.aggregate(max=Coalesce(Max('unfavorables'), Value(0)))['max']
    min_unfavorables = enrolled_employees.aggregate(min=Coalesce(Min('unfavorables'), Value(0)))['min']

    return (max_unfavorables - min_unfavorables), enrolled_employees


def distribute_unfavorables(employees, num_shifts) -> dict['Employee', int]:
    total_fte = employees.aggregate(fte=Sum('fte'))['fte']
    employee_dict = {e: e.fte for e in employees}

    shift_allocation = {}
    remainders = {}
    for employee, fte in employee_dict.items():
        allocation = round((fte / total_fte) * num_shifts)
        shift_allocation[employee] = allocation
        remainders[employee] = (fte / total_fte) * num_shifts - allocation

    remainder = num_shifts - sum(remainders.values())

    remainders = sorted(remainders.items(), key=lambda x: x[1], reverse=True)
    for employee, remainder in remainders:
        if remainder > 0:
            shift_allocation[employee] += 1
            remainder -= 1
        if remainder == 0:
            break


    return shift_allocation
