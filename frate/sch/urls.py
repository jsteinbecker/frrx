from frate.models import Slot
from .models import Schedule
from ..sft.models import Shift
from ..empl.models import Employee

from django.urls import path, include
from .views import sch_list, sch_detail, sch_new, sch_delete, InfoViews, sch_unarchive

app_name = 'sch'

urlpatterns = [
        path('', sch_list, name='list'),
        path('create/', sch_new, name='new'),
        path('<sch>/', sch_detail, name='detail'),
        path('<sch>/unarchive/', sch_unarchive, name='unarchive'),
        path('<sch>/delete/', sch_delete, name='delete'),
        path('<sch>/v/', include('frate.ver.urls', namespace='ver')),

        path('<sch>/employee-list/', InfoViews.sch_employee_list, name='sch-empl-list'),
        path('<sch>/role-list/', InfoViews.sch_role_list, name='sch-role-list'),
        path('<sch>/best/', InfoViews.sch_best_version, name='sch-best-ver'),
    ]
