from frate.models import Employee, Schedule, Slot, Shift, Department
from django.shortcuts import render, get_object_or_404, redirect


def sch_list(request, dept):
    schedules = Schedule.objects.filter(department__slug=dept)
    return render(request, 'sch/sch-list.html', {'schedules': schedules, 'department': dept})

def sch_new(request, dept):
    department = get_object_or_404(Department, slug=dept)
    start_date = department.get_first_unused_start_date()
    sch = Schedule(department=department, start_date=start_date)
    sch.save()
    return redirect('dept:sch:detail', dept=dept, sch=sch.slug)

def sch_detail(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    return render(request, 'sch/sch-detail.html', {'schedule': schedule})

def ver_detail(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    return render(request, 'ver/ver-detail.html', {'version': version})


