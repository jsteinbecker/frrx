from django.urls import path, include

from frate.models import Slot
from ..sch.models import Schedule
from ..sft.models import Shift
from ..empl.models import Employee
from . import views

app_name = 'slot'

urlpatterns = [

        path('', views.detail, name='detail'),
        path('hx/', views.hx_detail, name='hx_detail'),

        path('assign/', views.assign, name='assign'),
        path('clear/', views.clear, name='clear'),

    ]

