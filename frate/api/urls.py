from .views import *
from django.urls import path, include
from frate.components.cal import display_month


app_name = 'api'

urlpatterns = [

        path('most-unfavs-empl/<dept>/<sch>/<ver>/', get_most_unfavorable_employee, name='most-unfavs-empl'),

        path('get-calendar/<y>/<m>/', display_month, name='cal-month'),

    ]