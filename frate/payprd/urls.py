from django.urls import reverse, path, include

from . import views

# EXTENDS
# /frate/ver/urls.py

app_name = 'prd'

urlpatterns = [

        path('', views.ppd_list, name='list'),

    ]