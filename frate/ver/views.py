from django.db.models import Sum, Q

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

    periods = version.periods.filter(employee=employee)
    for period in periods:
        period.save()
    for d in details:
        if d['pto']:
            d['pto'].save()

    return render(request, 'empl/ver/empl-version.html', {
        'employee': employee,
        'version': version,
        'workday_details': details,
        'pay_periods': prds,
        'periods': periods,
                  })


def ver_clear(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.slots.all().update(employee=None)
    version.save()
    return redirect(version.url)

def ver_delete(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.delete()
    return redirect(schedule.url)

def ver_pay_period_breakdown(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    employees = {}
    for employee in sch.employees.all():
        employees[employee] = empl_ver_hours_by_period(employee, sch, ver)
    employees = sch.employees.all()
    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'n': ver.n,
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

def ver_unfavorables(request, dept, sch, ver):
    from frate.calculate import version_inequity

    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    slots = ver.slots.all().exclude(Q(shift__phase=F('employee__phase_pref')))
    inequity, employees = version_inequity(sch.slug, ver.n)

    context = {'dept': dept,
                'sch': sch,
                'ver': ver,
                'unfavorables': slots,
                'employees': employees.order_by('-unfavorables'),
                'inequity': inequity }
    return render(request, 'ver/unfavorables.html', context)


def ver_unfavorables_clear_for_empl(request, dept, sch, ver, empl):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    empl = Employee.objects.get(slug=empl, department=dept)

    slots = ver.slots.filter(employee=empl).exclude(Q(shift__phase=F('employee__phase_pref')))
    slots.update(employee=None)

    messages.success(request, "Unfavorable shifts cleared for {}".format(empl))

    return HttpResponseRedirect('../../')

def ver_solve_unfav_balancing(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    ver.solve_unfav_balancing()
    return HttpResponseRedirect('../../')
