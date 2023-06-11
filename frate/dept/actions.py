from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from frate.models import Department
from django.urls import reverse


def build_new_sch(request, dept):
    dept = Department.objects.get(slug=dept)
    start_date = reverse("new_start_date", args=[dept.slug])
    sch = dept.schedules.create(start_date=start_date,)
    sch.save()
    if sch:
        return HttpResponse(f"{sch.slug}", status=201)
    else:
        return HttpResponse("Schedule not created", status=400)
