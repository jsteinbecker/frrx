from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
import yaml

from ..forms import NewRoleForm
from .models import Role
from .tables import RoleTable
from ..empl.models import Employee
from ..models import Department


def new_role(request):
    if request.method == 'POST':
        form = NewRoleForm(request.POST)
        if form.is_valid():
            dept = form.cleaned_data['department']
            role = form.cleaned_data['role']
            week_count = form.cleaned_data['week_count']
            max_employees = form.cleaned_data['max_employees']
            rts = Role.objects.get_or_create(department=dept,
                                             name=role,
                                             slug=slugify(role),
                                             week_count=week_count,
                                             max_employees=max_employees)[0]
            rts.save()
            return HttpResponseRedirect(f'{rts.slug}/')
    return HttpResponseRedirect('../')


def role_list(request, dept):
    dept = Department.objects.get(slug=dept)
    roles = Role.objects.filter(department=dept)
    table = RoleTable(roles)
    return render(request, 'role/list.html', {
        'roles': roles,
        'table': table,
        'dept': dept})


def role_doc(request, dept):
    data = yaml.load(open('frate/role/docs.yaml'), Loader=yaml.FullLoader)
    descr = data['description']
    return render(request, 'role/_doc.html', {'description': descr,})


def detail(request, dept, role):
    rts = Role.objects.get(department__slug=dept, slug=role)
    dept = rts.department
    weeks = []
    week = []
    for slot in rts.leader_slots.all():
        week.append(slot)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if len(week) > 0:
        weeks.append(week)
    repetitions = dept.schedule_week_length // rts.week_count

    if request.method == 'POST':
        form = NewRoleForm(request.POST)
        if form.is_valid():
            dept = form.cleaned_data['department']
            role = form.cleaned_data['role']
            week_count = form.cleaned_data['week_count']
            max_employees = form.cleaned_data['max_employees']
            rts = Role.objects.get_or_create(department=dept,
                                             name=role,
                                             slug=slugify(role),
                                             week_count=week_count,
                                             max_employees=max_employees)[0]
            rts.save()
            return HttpResponseRedirect(f'{rts.slug}/')

    return render(request, 'role/detail.html', {
        'weeks': weeks,
        'role': rts,
        'repetitions': repetitions})


def delete_role(request, dept, role):
    rts = Role.objects.get(department__slug=dept, slug=role)
    rts.delete()
    return HttpResponseRedirect(f'../../')


def assign_empls(request, dept, role):
    role = Role.objects.get(department__slug=dept, slug=role)
    shifts = []

    for slot in role.leader_slots.filter(type='D'):
        shifts.append(slot.shifts.first())
    for slot in role.leader_slots.filter(type='R'):
        for shift in slot.shifts.all():
            shifts.append(shift)

    shifts = set(shifts)
    other_roles = Role.objects.filter(department__slug=dept).exclude(pk=role.pk)

    if shifts:
        employee_options = Employee.objects.filter(department__slug=dept,
                                                   shifts__in=shifts) \
            .exclude(roles__in=other_roles) \
            .exclude(pk__in=role.employees.values('pk')) \
            .distinct()
    else:
        employee_options = Employee.objects.filter(department__slug=dept) \
            .exclude(roles__in=other_roles) \
            .exclude(pk__in=role.employees.values('pk')) \
            .distinct()

    if request.method == 'POST':
        empl = request.POST.get('employee')
        empl = Employee.objects.get(pk=empl)
        if not role.employees.filter(pk=empl.pk).exists():
            if role.employees.count() < role.max_employees:
                role.employees.add(empl)
                messages.success(request, f'{empl} added to {role}')
            else:
                messages.error(request, f'{role} is full')
        else:
            messages.error(request, f'{empl} already assigned to {role}')
        return HttpResponseRedirect(f'../')

    return render(request, 'role/assign.html', {
        'role': role,
        'employee_options': employee_options})


def remove_empl(request, dept, role):
    if request.method == 'POST':
        empl = request.POST.get('employee')
        empl = Employee.objects.get(pk=empl)
        role = Role.objects.get(department__slug=dept, slug=role)
        role.employees.remove(empl)
        messages.success(request, f'{empl} removed from {role}')
        return HttpResponseRedirect(f'../')
    messages.error(request, 'No employee selected')
    return HttpResponseRedirect(f'../')


def update_to_off(request, dept, role):
    if request.method == 'POST':
        sd_ids = request.POST.getlist('sd_ids')
        role = Role.objects.get(department__slug=dept, slug=role)
        role.leader_slots.filter(sd_id__in=sd_ids).update(type='O')
    return HttpResponseRedirect(f'../')


def update_to_generic(request, dept, role):
    if request.method == 'POST':
        sd_ids = request.POST.getlist('sd_ids')
        role = Role.objects.get(department__slug=dept, slug=role)
        role.leader_slots.filter(sd_id__in=sd_ids).update(type='G')

    return HttpResponseRedirect(f'../')


def update_to_direct(request, dept, role):

    sd_ids__initial = request.POST.getlist('sd_ids')
    role = Role.objects.get(department__slug=dept, slug=role)
    sd_ids = [int(sd_id) - 1 for sd_id in sd_ids__initial]

    unassigned = []
    for ls in role.leader_slots.filter(sd_id__in=sd_ids):
        unassigned.append(ls.unassigned_shifts())
    intersection = set(unassigned[0])
    for u in unassigned[1:]:
        intersection = intersection.intersection(set(u))

    sd_ids = [sd_id + 1 for sd_id in sd_ids]

    return render(request, 'role/d-template.html', {
        'role': role,
        'sd_ids': sd_ids,
        'unassigned': intersection})


def update_to_direct_submitted(request, dept, role):
    if request.method == 'POST':
        sd_ids = request.POST.getlist('sd_ids')
        shift = request.POST.get('shift')
        role = Role.objects.get(department__slug=dept, slug=role)
        sd_ids = [int(sd_id) for sd_id in sd_ids]

        slots = role.leader_slots.filter(sd_id__in=sd_ids)
        for slot in slots:
            slot.type = 'D'
            slot.shifts.set([shift])
            slot.save()

        messages.success(request, f'Updated {slots.count()} slots to direct.')

        return HttpResponseRedirect(f'../../')

    return HttpResponseRedirect(f'../')


def update_to_rotating(request, dept, role):
    sd_ids = request.POST.getlist('sd_ids')
    role = Role.objects.get(department__slug=dept, slug=role)

    unassigned = []
    for l in role.leader_slots.filter(sd_id__in=sd_ids):
        unassigned.append(l.unassigned_shifts())
    intersection = set(unassigned[0])
    for u in unassigned[1:]:
        intersection = intersection.intersection(set(u))

    return render(request, 'role/r-template.html', {
        'role': role,
        'sd_ids': sd_ids,
        'unassigned': intersection})


def update_to_rotating_submitted(request, dept, role):
    if request.method == 'POST':
        sd_ids = request.POST.getlist('sd_ids')
        shifts = request.POST.getlist('shifts')
        role = Role.objects.get(department__slug=dept, slug=role)
        sd_ids = [int(sd_id) for sd_id in sd_ids]

        slots = role.leader_slots.filter(sd_id__in=sd_ids)
        for slot in slots:
            slot.type = 'R'
            slot.shifts.set(shifts)
            slot.save()

        messages.success(request, f'Updated {slots.count()} slots to rotating.')

        return HttpResponseRedirect(f'../../')

    return HttpResponseRedirect(f'../')
