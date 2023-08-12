import datetime

from django.db.models import When, Case, F, CharField

from frate.models import Slot, Department
from frate.sch.models import Schedule
from frate.sft.models import Shift
from frate.empl.models import Employee
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.edit import FormMixin
from .tables import VersionTable



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
    table = VersionTable(schedule.versions.exclude(status=Schedule.StatusChoices.ARCHIVED))
    return render(request, 'sch/sch-detail.html', {
        'schedule': schedule,
        'table': table,
        'today': datetime.date.today()
    })


def sch_delete(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    schedule.delete()
    return redirect('dept:sch:list', dept=dept)


def sch_unarchive(request, dept, sch):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    for version in schedule.versions.archived():
        version.status = Schedule.StatusChoices.DRAFT
        version.save()
    return redirect('dept:sch:detail', dept=dept, sch=sch)


class InfoViews:

    @staticmethod
    def sch_employee_list(request, dept, sch):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        employees = schedule.employees.all()
        return render(request, 'sch/sch-employee-list.html', {'schedule': schedule, 'employees': employees})

    @staticmethod
    def sch_role_list(request, dept, sch):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        roles = schedule.roles.all()
        return render(request, 'sch/sch-role-list.html', {'schedule': schedule, 'roles': roles})
