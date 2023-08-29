from django.shortcuts import render, redirect

from .models import VersionEmployee
from frate.models import Version, Employee

from .tables import VersionEmployeeTable

from django_tables2 import RequestConfig



def ver_empl_list(request, dept, sch, ver):
    version = Version.objects.get(schedule__department__slug=dept,
                                  schedule__slug=sch,
                                  n=ver)

    ver_employees = version.version_employees.all()
    table = VersionEmployeeTable(ver_employees)

    context = {
        'table': table,
        'version': version,
        'employees': ver_employees
    }

    return render(request, 'ver/empl/ver_employees.html', context)
