from django.db.models import Sum

from frate.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.urls import reverse


from frate.calculate import empl_ver_hours_by_period


def ver_new(request, dept, sch):
    schedule = get_object_or_404(Schedule,department__slug=dept, slug=sch)
    ver = schedule.versions.create(n=schedule.versions.count()+1)
    ver.save()
    return HttpResponseRedirect("../../")

def ver_detail(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.save()
    return render(request, 'ver/detail.html', {'version': version})


def ver_assign_templates(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.assign_positive_templates()
    return redirect(version.url)

def ver_solve(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.solve()
    return redirect(version.url)

def ver_empl(request, dept, sch, ver, empl):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    employee = get_object_or_404(Employee, slug=empl)
    workdays = version.workdays.all()
    details = [workday.get_employee_details(employee) for workday in workdays]
    prds = set(version.workdays.values_list('pd_id', flat=True).distinct())
    prds = {prd: version.slots.filter(employee=employee,
                                      workday__pd_id=prd).aggregate(hours=Sum('shift__hours')
                                    )['hours'] for prd in prds}
    print(prds)

    return render(request, 'empl/ver/empl-version.html', {
        'employee': employee,
        'version': version,
        'workday_details': details,
        'pay_periods': prds,})

def ver_clear(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.slots.all().update(employee=None)
    version.save()
    return redirect(version.url)

def ver_pay_period_breakdown(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    employees = {}
    for employee in sch.employees.all():
        employees[employee] = empl_ver_hours_by_period(employee, sch, ver)
    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'employees': employees}
    return render(request, 'ver/pay-period-breakdown.html', context)


def ver_empty_slots(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    slots = ver.slots.filter(employee=None)
    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'empty_slots': slots}
    return render(request, 'ver/empty-slots.html', context)

