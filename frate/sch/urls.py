from frate.models import Employee, Schedule, Slot, Shift

from django.urls import path, include
from .views import sch_list, sch_detail, sch_new, ver_detail

app_name = 'sch'

urlpatterns = [
        path('', sch_list, name='list'),
        path('create/', sch_new, name='new'),
        path('<sch>/', sch_detail, name='detail'),
        path('<sch>/v/<ver>/', ver_detail, name='ver'),
        path('<sch>/v/<ver>/wd/', include('frate.wday.urls', namespace='wd')),

    ]
