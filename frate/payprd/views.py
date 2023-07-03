from frate.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def ppd_list(request, dept, sch, ver):
    schedule = get_object_or_404(Schedule, department__slug=dept, slug=sch)
    version = get_object_or_404(schedule.versions, n=ver)
    pay_periods = version.periods.all()
    return render(request, 'payprd/list.html', {'pay_periods': pay_periods, 'version': version})