from frate.models import Employee, Schedule, Slot, Shift

from django.urls import path, include
from .views import sch_list, sch_detail, sch_new, sch_delete

app_name = 'sch'

urlpatterns = [
        path('', sch_list, name='list'),
        path('create/', sch_new, name='new'),
        path('<sch>/', sch_detail, name='detail'),
        path('<sch>/delete/', sch_delete, name='delete'),
        path('<sch>/v/', include('frate.ver.urls', namespace='ver')),

    ]
