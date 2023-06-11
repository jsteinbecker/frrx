from django.db.models import F
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
        'template_slots': template_sch.template_slots.filter(following__isnull=True),
    })

def get_options(request,dept,empl,**kwargs):
    sd_ids = request.GET.get('sdids')
    dept = Department.objects.get(slug=dept)
    empl = Employee.objects.get(slug=empl)
    if sd_ids:
        sd_ids = sd_ids.split(',')
        sd_ids = [int(sd_id) for sd_id in sd_ids]

        weekdays = []
        for sd_id in sd_ids:
            wd = "SMTWRFA"[sd_id % 7]
            if wd not in weekdays:
                weekdays.append(wd)
        weekdays = set(weekdays)
        print("WEEKDAYS",weekdays)
        options = dept.shifts.filter(employees__shifts=F('pk'))
        for wd in weekdays:
            options = options.filter(weekdays__contains=wd)

        options = dept.shifts.filter(slug__in=list(set(options.values_list('slug',flat=True))))

    return render(request, 'empl/empl-options.html', {
            'shifts':options, 'dept':dept, 'empl':empl, 'sdids':sd_ids})

def empl_templates_update(request, dept, empl):
    if request.method == 'POST':
        sd_ids = request.POST.getlist('sdids')

        sd_ids = [int(sd_id) for sd_id in sd_ids]

        for sd_id in sd_ids:
            ts = empl.template_slots.filter(sd_id=sd_id).first()
            if ts:
                ts.direct_shift = request.POST.get('shift')
                ts.type = 'D'
                ts.save()
                print("SAVED",ts)
        return HttpResponse("OK")

