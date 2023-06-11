"""frrx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin, messages
from django.contrib.auth import authenticate
from django.urls import include
from django.urls import path
from django.shortcuts import render
from frate import views
from django.http import HttpResponse, HttpResponseRedirect
from frate.models import Department

def index (request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/auth/')
    return render(request, 'index.html')

def auth_index (request):
    context = {
        'departments': Department.objects.all(),
    }
    return render(request, 'index_auth.html', context)

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
    path('department/', include('frate.dept.urls', namespace='dept')),
]
