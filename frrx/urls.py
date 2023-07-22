from django.conf.urls.static import static
from django.contrib import admin, messages
from django.contrib.auth import authenticate
from django.urls import include
from django.urls import path
from django.shortcuts import render
from frate import views
from django.http import HttpResponse, HttpResponseRedirect
from frate.models import Department
from frrx import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
import datetime



def go_to_current_schedule(request):
    user = request.user
    if user.is_authenticated:
        employee = user.employee
        schedule = employee.department.schedules.filter(start_date__lte=datetime.date.today()).first()
        return redirect(schedule.url)

def go_to_department(request):
    user = request.user
    if user.is_authenticated:
        employee = user.employee
        return redirect(employee.department.url)

def index (request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/auth/')
    return render(request, 'main/index.html')

def auth_index (request):
    context = {
        'departments': Department.objects.all(),
    }
    return render(request, 'main/index_auth.html', context)

def login (request):
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        un = request.POST['username']
        pw = request.POST['password']
        user = authenticate(request, username=un, password=pw)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/auth/')
        else:
            messages.error(request, 'Invalid username or password.')
        return HttpResponseRedirect('/')


urlpatterns = [

        path('grappelli/', include('grappelli.urls')),  # grappelli URLS
        path('admin/', admin.site.urls),  # admin site
        path('', index, name='index'),
        path('login/', login, name='login'),
        path('auth/', auth_index, name='auth_index'),
        path('api/', include('frate.api.urls', namespace='api')),
        path('department/', include('frate.dept.urls', namespace='dept')),
        path('to-user-dept/', go_to_department, name='goto-dept'),
        path('to-user-sch/', go_to_current_schedule, name='goto-sch'),

    ] + static(settings.MEDIA_URL,

               document_root=settings.MEDIA_ROOT)
