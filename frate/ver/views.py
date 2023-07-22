from django.db.models import Q, F, Sum

from frate.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect

from frate.ver.models import Version


def ver_new(request, dept, sch):
    schedule = get_object_or_404(Schedule,department__slug=dept, slug=sch)
    ver = schedule.versions.create(n=schedule.versions.count()+1)
    ver.save()
    return HttpResponseRedirect("../../")

def ver_detail(request, dept, sch, ver):
    from .calculate import calc_n_ptoreqs

    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.save()

    n_pto_reqs = calc_n_ptoreqs(version)
    return render(request, 'ver/detail.html', {'version': version,
                                               'n_pto_reqs': n_pto_reqs,})


def ver_assign_templates(request, dept, sch, ver):
    """
    ACTION : ASSIGN ALL VERSION TEMPLATES

    [redirects to main version view]
    """
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
    periods = version.periods.filter(employee=employee)
    print(employee,'periods:',periods.count())
    for period in periods:
        period.save()
    for d in details:
        if d['pto']:
            d['pto'].save()
            for p in d['pto'].pto_slots.all():
                p.save()
    return render(request, 'empl/ver/empl-version.html', {
        'employee': employee,
        'version': version,
        'workday_details': details,
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
    employees = sch.employees.all()
    periods = ver.periods.all() # type: QuerySet[PayPeriod]
    for period in periods:
        period.save()

    hr_dist_score = periods.aggregate(Sum('discrepancy'))['discrepancy__sum']

    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'n': ver.n,
               'employees': employees,
               'periods': periods,
               'hr_dist_score': hr_dist_score, }

    return render(request, 'ver/pay-period-breakdown.html', context)


def ver_empty_slots(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    slots = ver.slots.filter(employee=None)
    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'empty_slots': slots }
    return render(request, 'ver/empty-slots.html', context)

def ver_unfavorables(request, dept, sch, ver):
    from frate.calculate import version_inequity, distribute_unfavorables

    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)

    slots = ver.slots.all().exclude(Q(shift__phase_id='employee__phase_pref')) \
                           .filter(employee__isnull=False) \
                           .filter(period__employee__enrolled_in_inequity_monitoring=True)

    inequity, employees = version_inequity(sch.slug, ver.n)

    base_unfavs = ver.slots.exclude(shift__phase=F('employee__phase_pref')) \
                        .exclude(direct_template__isnull=False) \
                        .exclude(rotating_templates__isnull=False)
    n_unfavs =  base_unfavs.filter(employee__isnull=True).count()

    allocations = distribute_unfavorables(employees, n_unfavs) # type: Dict[Employee, int]


    context = {'dept': dept,
                'sch': sch,
                'ver': ver,
                'n_unfavs': n_unfavs,
                'unfavorables': slots,
                'employees': employees.order_by('-unfavorables'),
                'allocations': allocations,
                'inequity': inequity }

    return render(request, 'ver/unfavorables.html', context)

def ver_unfavorables_for_empl(request, dept, sch, ver, empl):
    from frate.calculate import version_inequity

    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    empl = Employee.objects.get(slug=empl, department=dept)

    slots = ver.slots.filter(employee=empl).exclude(Q(shift__phase=F('employee__phase_pref')))
    inequity, employees = version_inequity(sch.slug, ver.n)

    return render(request, 'ver/empl/unfavorables.html', {
        'dept': dept,
        'sch': sch,
        'ver': ver,
        'employee': empl,
        'unfavorables': slots,
        'inequity': inequity,
    })
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

def ver_templating(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    workdays = ver.workdays.all()

    missing_assignments = []
    for workday in workdays:
        for employee in workday.templated_employees.all():
            if employee not in workday.employees.all():
                missing_assignments.append((workday, employee))

    context = {'dept': dept,
                'sch': sch,
                'ver': ver,
                'workdays': workdays,
                'missing_assignments': missing_assignments,}
    return render(request, 'ver/templating.html', context)

def ver_warn_streak(request, dept, sch, ver):

    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    streak_exceeds_pref = ver.slots.filter(employee__streak_pref__lt=F('streak')).annotate(
        diff=F('streak') - F('employee__streak_pref')).order_by('-diff')

    context = {'dept': dept,
                'sch': sch,
                'ver': ver,
                'warnings': streak_exceeds_pref,}

    return render(request, 'ver/warn-streak.html', context)

def ver_streak_fix(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    streak_exceeds_pref = ver.slots.filter(employee__streak_pref__lt=F('streak')).annotate(
        diff=F('streak') - F('employee__streak_pref'))

    for slot in streak_exceeds_pref:
        if slot.allowed_as_streak_breakpoint:
            slot_streak_siblings = slot.get_streak()
            slot.employee = None
            slot.save()
            for sibling in slot_streak_siblings:
                sibling.save()

    return HttpResponseRedirect('../')

