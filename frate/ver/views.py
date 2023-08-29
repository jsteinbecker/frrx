from django.contrib import messages
from django.db.models import Q, F, Sum

from frate.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect

from frate.sch.models import Schedule
from frate.ver.models import Version
from frate.slot.protocols import RotatingTemplateAssignmentProtocol
from frate.ver.tables import ShiftSummaryTable


def ver_new(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    ver = schedule.versions.create(n=schedule.versions.count() + 1)
    ver.save()
    return HttpResponseRedirect("../../")


def ver_final(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    if schedule.versions.filter(status='P').exists():
        return redirect(schedule.versions.get(status='P').url)
    else:
        messages.error(request, "No final version exists for this schedule.")
        return redirect(schedule.url)


def ver_detail(request, dept, sch, ver):
    from .calculate import calc_n_ptoreqs

    can_edit = request.user.has_perm('sch.change_schedule') or request.user.is_superuser

    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = schedule.versions.get(n=ver)
    version.save()

    n_pto_reqs = calc_n_ptoreqs(version)
    return render(request, 'ver/detail.html', {
        'version': version,
        'n_pto_reqs': n_pto_reqs,
        'can_edit': can_edit})


def ver_matrix(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = schedule.versions.get(n=ver)
    return render(request, 'ver/scheduling-matrix.html', {'version': version})


def ver_assign_templates(request, dept, sch, ver):
    """
    ACTION : ASSIGN ALL VERSION TEMPLATES

    [redirects to main version view]
    """
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.assign_positive_templates()
    rotating = version.slots.filter(rotating_templates__isnull=False)
    for slot in rotating:
        protocol = RotatingTemplateAssignmentProtocol(slot)
        x = protocol.execute()
        print(x)
    return redirect(version.url)


def ver_solve(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver) # type: Version
    version.solve(user=request.user)
    return redirect(version.url)


def ver_empl(request, dept, sch, ver, empl):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    employee = get_object_or_404(Employee, slug=empl)
    workdays = version.workdays.all()
    details = [workday.get_employee_details(employee) for workday in workdays]
    periods = version.periods.filter(employee=employee)
    for period in periods:
        period.save()

    from .tables import EmployeePayPeriodSummaryTable
    table = EmployeePayPeriodSummaryTable(periods)

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
        'table': table,
    })


def ver_clear(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    version.slots.all().update(employee=None)
    version.save()
    version.solution_attempts.all().delete()
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
    periods = ver.periods.all()
    for period in periods:
        period.save()

    total_discrep = periods.aggregate(Sum('discrepancy'))['discrepancy__sum']

    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'n': ver.n,
               'employees': employees,
               'periods': periods,
               'total_discrep': total_discrep, }

    return render(request, 'ver/pay-period-breakdown.html', context)


def ver_empty_slots(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    slots = ver.slots.filter(employee=None)
    empty_days = Workday.objects.filter(pk__in=slots.values('workday__pk').distinct())
    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'empty_days': empty_days,
               'empty_slots': slots}
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
    n_unfavs = base_unfavs.filter(employee__isnull=True).count()

    allocations = distribute_unfavorables(employees, n_unfavs)  # type: Dict[Employee, int]

    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'n_unfavs': n_unfavs,
               'unfavorables': slots,
               'employees': employees.order_by('-unfavorables'),
               'allocations': allocations,
               'inequity': inequity}

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
               'missing_assignments': missing_assignments, }
    return render(request, 'ver/templating.html', context)


def ver_warn_streak(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    streak_exceeds_pref = ver.slots.filter(employee__streak_pref__lt=F('streak')).annotate(
        diff=F('streak') - F('employee__streak_pref')).order_by('employee', '-diff')

    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'warnings': streak_exceeds_pref, }

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


def ver_warn_untrained(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    ver_slots = ver.slots.all()
    untrained = (ver_slots.filter(employee__isnull=False)
                          .exclude(employee__shifttraining__shift=F('shift')))
    context = {'ver': ver,
               'untrained': untrained, }
    return render(request, 'ver/warn-untrained.html', context)


def ver_scorecard(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    scorecard = ver.scorecard
    context = {'ver': ver,
                'scorecard': scorecard, }
    return render(request, 'ver/scorecard.html', context)


def ver_shifts(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)

    shifts = ver.schedule.shifts.all()

    for shift in shifts:
        shift.percent_filled = ver.slots.filter(shift=shift)\
                                        .exclude(employee=None).count() / ver.slots.filter(shift=shift).count()

    table = ShiftSummaryTable(shifts)

    context = {'dept': dept,
               'sch': sch,
               'ver': ver,
               'shifts': shifts,
               'table': table}

    return render(request, 'ver/shifts-list.html', context)


def ver_as_shift(request, dept, sch, ver, sft):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)
    ver = Version.objects.get(schedule=sch, n=ver)
    sft = ver.schedule.shifts.get(name__iexact=sft)

    workdays = ver.workdays.all()
    slots = []
    for workday in workdays:
        slots.append(workday.slots.filter(shift=sft))

    context = {'ver': ver,
               'shift': sft,
               'workdays': workdays,
               'slots': slots, }
    return render(request, 'ver/shift.html', context)


def ver_backfill_priority(request, dept, sch, ver):
    dept = Department.objects.get(slug=dept)
    sch = Schedule.objects.get(department=dept, slug=sch)

    if request.method == 'POST':
        for slot, option in request.POST.items():
            if slot != 'csrfmiddlewaretoken':
                slot = Slot.objects.get(pk=slot)
                employee = Employee.objects.get(pk=option)
                slot.set_employee(employee)
                slot.save()

    ver = Version.objects.get(schedule=sch, n=ver)
    priority_slots = ver.slots.backfill_required()

    context = {
        'ver': ver,
        'priority_slots': priority_slots
    }
    return render(request, 'ver/backfill.html', context)