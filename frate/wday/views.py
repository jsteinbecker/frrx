from django.contrib import messages

from frate.models import Employee, Schedule, Slot, Shift, Department, Workday
from django.views.decorators.cache import cache_page
from .forms import AddPtoRequestForm
from django.http import HttpResponse

from django.shortcuts import render, get_object_or_404, redirect


class WdViews:

    @staticmethod
    def detail(request, dept, sch, ver, wd):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        workday.save()
        for slot in workday.slots.all():
            slot.save()
            for opt in slot.options.all():
                opt.save()

        if request.method=='POST':
            print(request.POST)
            form = AddPtoRequestForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'PTO request added.')
            else:
                messages.error(request, 'PTO request not added.')
        return render(request, 'wd/detail.html', {
            'workday': workday,
            'employees': workday.version.schedule.employees.all(),
            'shifts': workday.version.schedule.shifts.all(),
            'pto_form': AddPtoRequestForm(initial={'workday': workday,'department': workday.version.schedule.department})
        })

    @staticmethod
    def assign_rotating(request, dept, sch, ver, wd):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        workday.assign_rotating_templates()
        return redirect(workday.url)

    @staticmethod
    def delete_pto(request, dept, sch, ver, wd, empl):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        employee = get_object_or_404(schedule.employees, slug=empl, department=schedule.department)
        ptoreq = workday.pto_requests.filter(employee=employee)
        if ptoreq.exists():
            ptoreq.delete()
            return redirect(workday.url)
        else:
            messages.error(request, 'PTO request not found.')
            return HttpResponse('PTO request not found.', status=404)


class SlotViews:

    @staticmethod
    def assign(request, dept, sch, ver, wd, sft, empl):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd) # type: Workday
        slot = get_object_or_404(workday.slots, shift__slug=sft) # type: Slot
        employee = get_object_or_404(schedule.employees, slug=empl)
        if slot.direct_template == employee:
            slot.set_employee(employee)
            slot.save()
            print('direct')
            return redirect(workday.url)
        elif slot.rotating_templates.filter(pk=employee.pk).exists():
            slot.set_employee(employee)
            slot.save()
        elif slot.generic_templates.filter(pk=employee.pk).exists():
            slot.set_employee(employee)
            slot.save()
        return redirect(workday.url)
