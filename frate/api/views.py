from frate.models import *
from django.http import JsonResponse

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



