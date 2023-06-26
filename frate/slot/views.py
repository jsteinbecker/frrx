from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect

from frate.models import Employee, Schedule, Slot, Shift



def detail(request, dept, sch, ver, wd, sft):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    slot = get_object_or_404(workday.slots, shift__slug=sft)
    return render(request, 'slot/detail.html', {
        'slot': slot,
        'employees': schedule.employees.all(),
    })

def hx_detail(request, dept, sch, ver, wd, sft):

    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    slot = get_object_or_404(workday.slots, shift__slug=sft)
    trained = Employee.objects.filter(department=schedule.department, shifttraining__shift=slot.shift)
    blocked = slot.conflict_blockers() & slot.fte_blockers()
    options = trained.exclude(pk__in=blocked)

    if options.exists():
        for option in options:
            week_hours = version.slots.filter(employee=option, workday__wk_id=slot.workday.wk_id).values('workday__wk_id')\
                                    .aggregate(hours=Sum('shift__hours'))['hours'] or 0
            option.week_hours = week_hours
            option.pickable = True if week_hours < (40 - slot.shift.hours) else False

    if request.method == 'POST':
        employee = get_object_or_404(schedule.employees, slug=request.POST['employee'])
        slot.set_employee(employee)
        slot.filled_by = 'U'
        slot.save()
        messages.success(request, 'Slot assigned to {}'.format(employee))
        return redirect(version.url+'empty-slots/')


    return render(request, 'slot/hx-detail.html', {
        'slot': slot,
        'employees': schedule.employees.all(),
        'options': options,
    })


def assign(request, dept, sch, ver, wd, sft, empl):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd) # type: Workday
    slot = get_object_or_404(workday.slots, shift__slug=sft) # type: Slot
    employee = get_object_or_404(schedule.employees, slug=empl)
    slot.set_employee(employee)
    slot.save()
    return redirect(workday.url)