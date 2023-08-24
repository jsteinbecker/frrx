from pprint import pprint

from django.contrib import messages
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce

from frate.models import Slot, Department, RoleSlot
from ..sch.models import Schedule
from .models import Workday
from ..sft.models import Shift
from ..empl.models import Employee
from django.views.decorators.cache import cache_page
from .forms import AddPtoRequestForm
from django.http import HttpResponse, JsonResponse

from django.shortcuts import render, get_object_or_404, redirect

from frate.slot.protocols import RotatingTemplateAssignmentProtocol


class QuerySets:

    @staticmethod
    def on_deck(request, dept, sch, ver, wd):
        dept = get_object_or_404(Department, slug=dept)
        schedule = get_object_or_404(Schedule, department=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        in_slots = workday.slots.filter(employee__isnull=True).values_list('pk', flat=True)
        pto = workday.on_pto.all()
        tdo = workday.on_tdo.all()
        return JsonResponse({'on_deck': list(schedule.employees
                                        .exclude(pk__in=pto)
                                        .exclude(pk__in=tdo)
                                        .exclude(pk__in=in_slots)
                                        .values_list('pk', flat=True))})


class WdViews:

    @staticmethod
    def detail(request, dept, sch, ver, wd):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        workday.save()

        role_slots = RoleSlot.objects.filter(pk__in=workday.version.schedule.roles\
                                             .values_list('leader_slots__pk', flat=True),
                                             sd_id=wd,
                                             ).select_related('leader__role')\
                                             .prefetch_related('leader__role__employees')

        on_deck = workday.on_deck.annotate(week_hours=Coalesce(
                                                        Sum(version.slots.filter(
                                                            employee=F('employee'),
                                                            workday__wk_id=workday.wk_id).values('shift__hours')),
                                                        Value(0)))

        if request.method == 'POST':
            form = AddPtoRequestForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'PTO request added.')
            else:
                messages.error(request, 'PTO request not added.')

        if request.user.is_staff:
            can_edit = True
        else:
            can_edit = False

        return render(request, 'wd/detail.html', {
            'workday': workday,
            'on_deck': on_deck,
            'role_slots': role_slots,
            'shifts': workday.version.schedule.shifts.all(),
            'can_edit': can_edit,
            'pto_form': AddPtoRequestForm(initial={'workday': workday,
                                                   'department': workday.version.schedule.department,
                                                   'on_deck': on_deck})
        })

    @staticmethod
    def assign_rotating(request, dept, sch, ver, wd):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        for slot in workday.slots.all():
            worker = RotatingTemplateAssignmentProtocol(slot)
            worker.execute()
        return redirect(workday.url)

    @staticmethod
    def delete_pto(request, dept, sch, ver, wd, empl):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        employee = get_object_or_404(Employee, slug=empl, department=schedule.department)
        ptoreq = workday.pto_requests.filter(employee=employee)
        if ptoreq.exists():
            ptoreq.delete()
            messages.success(request, 'PTO request deleted.')
            return HttpResponse('PTO request deleted.', status=200)
        else:
            messages.error(request, 'PTO request not found.')
            return HttpResponse('PTO request not found.', status=404)

    @staticmethod
    def create_pto(request, dept, sch, ver, wd, empl):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        employee = get_object_or_404(schedule.employees, slug=empl, department=schedule.department)
        if workday.pto_requests.filter(employee=employee).exists():
            messages.error(request, 'PTO request already exists.')
            return HttpResponse('PTO request already exists.', status=400)
        else:
            workday.pto_requests.create(employee=employee)

            token = workday.tokens.get(employee=employee)
            token.position = 'PTO'
            token.save()

            return redirect(workday.url)

    @staticmethod
    def solve(request, dept, sch, ver, wd):
        schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
        version = get_object_or_404(schedule.versions, n=ver)
        workday = get_object_or_404(version.workdays, sd_id=wd)
        for slot in workday.slots.all():
            slot.solve()
        return redirect(workday.url)

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
