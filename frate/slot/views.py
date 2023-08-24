from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string

from frate.models import Slot
from frate.sch.models import Schedule
from frate.sft.models import Shift
from frate.empl.models import Employee


"""
============================
| VIEWS   |   SLOTS        |
============================
|                          |
| dept: sch: ver: wd: slot |
|                          |
============================
"""


def detail(request, dept, sch, ver, wd, sft):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    slot = get_object_or_404(workday.slots, shift__slug=sft)
    slot.save()

    options = slot.options.all()
    for option in options:
        option.save()

    if request.method == 'POST':
        employee = get_object_or_404(schedule.employees, slug=request.POST['employee'])
        slot.set_employee(employee)
        slot.filled_by = 'U'
        slot.save()
        messages.success(request, 'Slot assigned to {}'.format(employee))
        return redirect(workday.url)

    return render(request, 'frate/slot/templates/slot/detail.html', {
        'slot': slot,
        'employees': schedule.employees.all(),
        'streak': slot.get_streak(),
        'today': slot.workday.date,
        'options': options,

    })


def hx_detail(request, dept, sch, ver, wd, sft):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    slot = get_object_or_404(workday.slots, shift__slug=sft)
    slot.save()

    options = slot.options.all()
    for option in options:
        option.save()

    if request.method == 'POST':
        employee = get_object_or_404(schedule.employees, slug=request.POST['employee'])
        slot.set_employee(employee)
        slot.filled_by = 'U'
        slot.save()
        messages.success(request, '{} assigned to {}'.format(slot, employee))
        return redirect(workday.url)

    return render(request, 'frate/slot/templates/slot/hx-detail.html', {
        'slot': slot,
        'employees': schedule.employees.all(),
    })



def clear(request, dept, sch, ver, wd, sft):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    slot = get_object_or_404(workday.slots, shift__slug=sft)
    slot.employee = None
    slot.save()
    messages.info(request, 'Slot cleared')
    return redirect(workday.url)
