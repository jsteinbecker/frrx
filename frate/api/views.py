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
