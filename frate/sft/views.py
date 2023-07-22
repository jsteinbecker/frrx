from django.db.models import OuterRef
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from frate.sft.forms import ShiftEditForm
from frate.models import Organization, Department, TimePhase, ShiftTraining, Schedule, BaseTemplateSlot, Slot
from frate.sft.models import Shift
from frate.empl.models import Employee

from django.urls import reverse


def sft_list(request, dept):
    department = get_object_or_404(Department, slug=dept)
    shifts = Shift.objects.filter(department=department)
    return render(request, 'sft/list.html', {'shifts':shifts, 'dept': dept})

def sft_new(request, dept):
    department = get_object_or_404(Department, slug=dept)
    form = ShiftEditForm(initial={'department':department})
    if request.method == 'POST':
        form = ShiftEditForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('dept:sft:list', args=[dept]))
        return render(request, 'sft/new.html', {'dept':department, 'form':form})
    return render(request, 'sft/new.html', {'dept':department, 'form':form})

def sft_detail(request, dept, sft):

    department = get_object_or_404(Department, slug=dept)
    sft = get_object_or_404(Shift, slug=sft, department=department)
    form = ShiftEditForm(instance=sft)
    if request.method == 'POST':
        form = ShiftEditForm(request.POST, instance=sft)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('dept:sft:list', args=[dept]))
        return render(request, 'sft/detail.html', {'shift':sft, 'form':form})
    return render(request, 'sft/detail.html', {'shift':sft, 'form':form})

def sft_tallies(request, dept, sft):

    department = get_object_or_404(Department, slug=dept)
    shift = get_object_or_404(Shift, slug=sft, department=department)
    slots = Slot.objects.filter(shift=shift).order_by('employee','workday__date')
    empties = slots.filter(employee=None)
    employees = Employee.objects.filter(pk__in=slots.values_list('employee', flat=True))
    return render(request, 'sft/tallies.html', {'shift':shift, 'slots':slots, 'empties':empties, 'employees':employees})