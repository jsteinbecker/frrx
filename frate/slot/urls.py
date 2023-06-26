from django.urls import path, include

from frate.models import Employee, Schedule, Slot, Shift
from .views import *

app_name = 'slot'

urlpatterns = [

        path('', detail, name='detail'),
        path('hx/', hx_detail, name='hx_detail'),

        path('assign/', assign, name='assign'),

    ]

