from frate.models import *
from django.http import JsonResponse

from frate.sch.models import Schedule
from frate.ver.models import Version


def get_most_unfavorable_employee(request, dept, sch, ver):
    """
    Get the most unfavorable employee

    :param request: request
    :param dept:    department slug
    :param sch:     schedule slug
    :param ver:     version number

    :return:        JsonResponse
    """

    department = Department.objects.get(slug=dept)
    schedule   = Schedule.objects.get(slug=sch, department=department)
    version    = Version.objects.get(n=ver, schedule=schedule)
    employees  = schedule.employees.filter(enrolled_in_inequity_monitoring=True)

    data = { employee.slug.upper(): version.slots.filter(employee=employee).exclude(
                                                        shift__phase=employee.phase_pref).count() \
                                for employee in employees }

    max_empl = max(data, key=data.get)

    return JsonResponse({'DATA': data,
                         'MAX': max_empl,
                         'MAX_COUNT': data[max_empl]})


def get_user(request):
    return JsonResponse({'USER': request.user.username})


def get_user_org(request):
    profile = Employee.objects.filter(user=request.user).first()
    dept = profile.department if profile else None
    org = dept.organization if dept else None
    return JsonResponse({'ORG': org.name, 'DEPT': dept.name, 'EMPL': profile.name})


class CustomOption:

    def __init__(self, employee, wkhrs, pdhrs):
        self.employee = employee
        self.wk_hrs = wkhrs
        self.pd_hrs = pdhrs


class SlotOptionSet:

    def __str__(self):
        return f'{self.slot} OPTIONS'

    def __init__(self, slot):
        self.slot = slot
        self.wk_id = slot.workday.wk_id
        self.pd_id = slot.workday.pd_id
        self.options = []
        self.incompatible_employees = []
        self._build_incompatible_employees()
        self._build_options()
        self.best_option = self.options[0] if self.options else None
        self.shift = self.slot.shift

    def _build_incompatible_employees(self):
        self.incompatible_employees = []
        if self.slot.incompatible_slots():
            self.incompatible_employees = list(set(self.slot.incompatible_slots().values_list('employee__slug', flat=True)))
        else:
            self.incompatible_employees = []

    def _build_options(self):
        self.options = []
        for employee in self.slot.workday.version.schedule.employees.all():
            if employee.shifts.filter(pk=self.slot.shift.pk).exists() and \
                employee not in self.slot.workday.on_pto and \
                employee not in self.slot.workday.on_tdo and \
                employee not in self.incompatible_employees:
                    wk_hrs = sum(list(self.slot.version.slots.filter(employee=employee, workday__wk_id=self.wk_id)\
                                .values_list('shift__hours', flat=True)))
                    pd_hrs = sum(list(self.slot.version.slots.filter(employee=employee, workday__pd_id=self.pd_id)\
                                .values_list('shift__hours', flat=True)))
                    option = CustomOption(employee, wk_hrs, pd_hrs)
                    self.options.append(option)

                    self.options.append(CustomOption(employee, wk_hrs, pd_hrs))
            if self.options:
                self.options.sort(key=lambda x: (x.pd_hrs, x.wk_hrs))

    def get_options(self):
        return self.options

    def get_options_json(self):
        return JsonResponse({'OPTIONS': self.options})




