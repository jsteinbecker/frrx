import datetime

from django.db.models import When, Case, F, CharField

from frate.models import Employee, Schedule, Slot, Shift, Department
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.edit import FormMixin


def sch_list(request, dept):
    schedules = Schedule.objects.filter(department__slug=dept)
    department = get_object_or_404(Department, slug=dept)
    return render(request, 'sch/sch-list.html', {'schedules': schedules, 'department': department})

def sch_new(request, dept):
    department = get_object_or_404(Department, slug=dept)
    start_date = department.get_first_unused_start_date()
    sch = Schedule(department=department, start_date=start_date)
    sch.save()
    return redirect('dept:sch:detail', dept=dept, sch=sch.slug)

def sch_detail(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    schedule.save()
    return render(request, 'sch/sch-detail.html', {'schedule': schedule, 'today': datetime.date.today()})

def sch_delete(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    schedule.delete()
    return redirect('dept:sch:list', dept=dept)

