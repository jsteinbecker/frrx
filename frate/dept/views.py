from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.urls import reverse
from django import forms

from frate.models import Department, Role, Employee
from .forms import DeptEditForm
from frate.forms import NewRoleForm, \
                        RTScheduleSlotFormPart1, \
                        RTScheduleSlotFormPart2Direct, \
                        RTScheduleSlotFormPart2Rotating

def dept_detail(request, dept):
    dept = Department.objects.get(slug=dept)
    rts_form = NewRoleForm()
    context = {'dept': dept, 'rts_form': rts_form}
    return render(request, 'dept/dept-detail.html', context)

def edit_dept(request, dept):
    dept = Department.objects.get(slug=dept)
    form = DeptEditForm(instance=dept)
    if request.method == 'POST':
        form = DeptEditForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('../')
    return render(request, 'dept/edit.html', {'form': form})



def role_new(request, dept):
    form = NewRoleForm()
    if request.method == 'POST':
        rts = request.POST.get('name')
        week_count = int(request.POST.get('week_count'))
        dept = Department.objects.get(slug=dept)
        max_employees = int(request.POST.get('max_employees'))
        rts = Role.objects.get_or_create(department=dept,
                                         name=rts,
                                         slug=slugify(rts),
                                         week_count=week_count,
                                         max_employees=max_employees)[0]
        rts.save()
        return HttpResponseRedirect(f'../{rts.slug}/')
    return render(request, 'role/new.html', {'form': form})

def rts_detail(request, dept, role):
    dept = Department.objects.get(slug=dept)
    rts = Role.objects.get(department=dept, slug=role)
    context = {'dept': dept, 'role': rts}
    return render(request, 'dept/rts/detail.html', context)

def rts_assign(request, dept, role):
    dept = Department.objects.get(slug=dept)
    rts = Role.objects.get(department=dept, slug=role)
    if request.method == 'POST':
        assigned = request.POST.getlist('assigned')
        print(assigned)
        if len(assigned) > rts.max_employees:
            return HttpResponse('Too many employees assigned')
        else:
            rts.employees.clear()
            for empl in assigned:
                rts.employees.add(Employee.objects.get(slug=empl))
            rts.save()
    context = {'dept': dept, 'role': rts}
    return HttpResponseRedirect('../')

def rts_slotform_1(request, dept, rts, sd_id):
    dept = Department.objects.get(slug=dept)
    rts = Role.objects.get(department=dept, slug=rts)
    templ = rts.slots.get(sd_id=sd_id)
    form = RTScheduleSlotFormPart1(instance=templ)
    if request.method == 'POST':
        form = RTScheduleSlotFormPart1(request.POST, instance=templ)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f'../{sd_id}/')
    return render(request, 'dept/rts/rts-slot-form.html', {'form': form, 'sd_id': sd_id})

def rts_slotform_2_direct(request, dept, rts, sd_id):
    dept = Department.objects.get(slug=dept)
    rts = Role.objects.get(department=dept, slug=rts)
    templ = rts.slots.get(sd_id=sd_id)
    form = RTScheduleSlotFormPart2Direct(instance=templ)
    if request.method == 'POST':
        form = RTScheduleSlotFormPart2Direct(request.POST, instance=templ)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f'../{sd_id}/')
    return render(request, 'dept/rts/rts-slot-form.html', {'form': form, 'sd_id': sd_id})

def rts_slotform_2_rotating(request, dept, rts, sd_id):
    dept = Department.objects.get(slug=dept)
    rts = Role.objects.get(department=dept, slug=rts)
    templ = rts.slots.get(sd_id=sd_id)
    form = RTScheduleSlotFormPart2Rotating(instance=templ)
    if request.method == 'POST':
        form = RTScheduleSlotFormPart2Rotating(request.POST, instance=templ)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f'../{sd_id}/')
    return render(request, 'dept/rts/rts-slot-form.html', {'form': form, 'sd_id': sd_id})