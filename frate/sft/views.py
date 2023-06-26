from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from frate.forms import ShiftEditForm
from frate.models import Organization, Department, TimePhase, ShiftTraining, Shift, Employee, Schedule, BaseTemplateSlot, Slot

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