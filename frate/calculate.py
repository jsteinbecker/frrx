from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from .models import Department, Role, Employee, Slot, Shift, Version, Schedule


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
                                    Sum('shift__hours'),Value(0)))['shift__hours__sum']
    return data

