from frate.models import Employee, Schedule, Slot, Shift, Department, Workday

from django.shortcuts import render, get_object_or_404, redirect


def wd_detail(request, dept, sch, ver, wd):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    workday = get_object_or_404(version.workdays, sd_id=wd)
    return render(request, 'wd/wd-detail.html', {'workday': workday})
