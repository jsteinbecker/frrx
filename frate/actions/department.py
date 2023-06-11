from frate.models import Department
from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect



def department_index (request):
    return render(request, 'department_index.html')

def dept_get_new_start_date (request, dept):
    dept = Department.objects.get(slug=dept)
    return HttpResponse(dept.get_new_start_date())







