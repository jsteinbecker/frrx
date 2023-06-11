from frate.models import Department
import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect


def dept_get_new_start_date (request, dept):
    dept = Department.objects.get(slug=dept)
    start_date = dept.initial_start_date
    while dept.schedules.filter(start_date=start_date).exists():
        start_date += datetime.timedelta(days=dept.schedule_week_length * 7)
    return HttpResponse(start_date, status=200)

def dept_build_new_sch(request, dept):
    dept = Department.objects.get(slug=dept)
    start_date = dept_get_new_start_date(request, dept.slug).content.decode('utf-8')
    sch = dept.schedules.create(start_date=start_date,)
    sch.save()
    if sch:
        return HttpResponse(f"{sch.slug}", status=201)
    else:
        return HttpResponse("Schedule not created", status=400)

def dept_get_sch_list(request, dept):
    dept = Department.objects.get(slug=dept.slug)
    sch_list = dept.schedules.all()
    return HttpResponse(sch_list, status=200)
