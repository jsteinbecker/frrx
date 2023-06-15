from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from frate.models import Organization, Department, TimePhase, ShiftTraining, Shift, Employee, Schedule, BaseTemplateSlot, Slot

from django.urls import reverse



def sft_detail(request, dept, sft):
    department = get_object_or_404(Department, slug=dept)
    sft = get_object_or_404(Shift, slug=sft, department=department)
    return render(request, 'sft/detail.html', {'shift':sft})