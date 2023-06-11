from django.forms import formset_factory
from django.shortcuts import render
from django.views.generic import ListView

# Create your views here.

from django.http import HttpResponse

from frate.models import Employee


def template_slot_edit(request, empl):
    from .forms import TemplateSlotForm
    template = 'template_slot_edit.html'

    empl = Employee.objects.get(slug=empl)
    day_count = empl.department.schedule_week_length * 7
    days = [(d, "Sun Mon Tue Wed Thu Fri Sat".split()[d % 7]) for d in range(day_count)]
    formset = formset_factory(TemplateSlotForm, extra=day_count,  )
    form = formset(initial=[{'sd_id': d,'employee':empl} for d in range(day_count)])

    context = {
        'empl': empl,
        'days' : days,
        'formset': form,
    }
    return render(request, template, context)