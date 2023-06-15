from django.shortcuts import render
from django.http import HttpResponse
from frate.models import Department

def dept_detail(request, dept):
    dept = Department.objects.get(slug=dept)

    context = {'dept': dept,}
    return render(request, 'dept/dept-detail.html', context)
