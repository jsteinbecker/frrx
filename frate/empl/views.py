import datetime
import json

from django.contrib import messages
from django.db.models import F, Count
from django.shortcuts import render
from frate.forms import EmployeeCreateForm
from frate.models import Department, Employee, BaseTemplateSlot, Shift
from django.http import HttpResponseRedirect, HttpResponse


def empl_list(request, dept):
    dept = Department.objects.get(slug=dept)
    empls = Employee.objects.filter(department=dept)

    return render(request, 'empl/empl-list.html', {
        'employees':empls,
        'dept':dept,
        'title': 'Employees'
    })

def empl_new(request, dept):
    dept = Department.objects.get(slug=dept)
    form = EmployeeCreateForm(initial={'department':dept})
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/department/'+dept.slug+'/employee/')
    return render(request, 'empl/empl-new.html', {
        'form': form,
        'dept':dept.name,
        'title': 'New Employee'
    })

def empl_detail(request, dept, empl):
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)
    return render(request, 'empl/empl-detail.html', {'employee':empl, 'dept':dept, 'title': 'Employee Detail'})

def empl_templates(request, dept, empl):
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)
    template_sch = empl.template_schedules.get_or_create(status='A')[0]
    template_sch.save()


    return render(request, 'empl/empl-templates.html', {
        'employee':empl,
        'dept':dept,
        'title': 'Employee Templates',
        'template_slots': template_sch.template_slots.filter(following__isnull=True)\
                             .annotate(rotating_shifts_count=Count('rotating_shifts')
        ),
        'template_sch': template_sch,
    })

def get_options(request,dept,empl):
    sd_ids = request.GET.get('sdids').split(',')
    sd_ids = [int(sd_id) for sd_id in sd_ids]
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)

    weekdays = []
    for sd_id in sd_ids:
        wd = "SMTWRFA"[sd_id % 7 - 1]
        if wd not in weekdays:
            weekdays.append(wd)
    weekdays = set(weekdays)
    print("WEEKDAYS",weekdays)

    allowed = []
    for shift in empl.shifts.all():
        if all([wd in shift.weekdays for wd in weekdays]):
            print(shift)
            allowed.append(shift.pk)

    if allowed:
        shifts = Shift.objects.filter(pk__in=allowed)
    else:
        shifts = Shift.objects.none()

    return render(request, 'empl/template-slots/ts-form.html', {
                'shifts':shifts, 'dept':dept, 'empl':empl, 'sdids':sd_ids})

def empl_templates_update(request, dept, empl):
    if request.method == 'POST':
        sd_ids = json.loads(request.POST.get('sdids'))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)
        shift = Shift.objects.get(slug=request.POST.get('shift'))

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = shift
                ts.type = 'D'
                ts.save()

        return HttpResponseRedirect(f"/department/{dept.slug}/employee/{empl.slug}/templates/")

def empl_templates_update_to_rotating(request, dept, empl):
    if request.method == 'POST':
        sd_ids = json.loads(request.POST.get('sdids'))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)
        shifts = Shift.objects.filter(slug__in=request.POST.getlist('shifts'))

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.rotating_shifts.set(shifts)
                ts.type = 'R'
                ts.save()

        return HttpResponseRedirect(f"/department/{dept.slug}/employee/{empl.slug}/templates/")

def empl_templates_update_to_tdo(request, dept, empl):
    if request.method == 'POST':
        sd_ids = json.loads(request.POST.get('sdids'))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.type = 'O'
                ts.save()
                print("SAVED",ts)
        return HttpResponseRedirect(f"/department/{dept.slug}/employee/{empl.slug}/templates/")

def empl_templates_to_generic(request, dept, empl):
    if request.method == 'POST':
        sd_ids = json.loads(request.POST.get('sdids'))
        sd_ids = [int(sd_id) for sd_id in sd_ids]
        dept = Department.objects.get(slug=dept)
        empl = Employee.objects.get(slug=empl)

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = None
                ts.type = 'G'
                ts.save()
                print("SAVED",ts)
        return HttpResponseRedirect(f"/department/{dept.slug}/employee/{empl.slug}/templates/")

def add_pto_req(request, dept, empl):
    if request.method == 'POST':
        print(request.POST)
        day = int(request.POST.get('day'))
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        date = datetime.date(year, month, day)
        empl = Employee.objects.get(slug=empl, department__slug=dept)
        empl.pto_requests.create(date=date)
        messages.success(request, f"PTO Request Added for {date.strftime('%m/%d/%Y')}")
        return HttpResponseRedirect(empl.url)
    return HttpResponse("ERROR")