from django.urls import path, include
from .api import (dept_get_new_start_date,
                  dept_build_new_sch,
                 dept_get_sch_list)
from .views import dept_detail


app_name = 'dept'


urlpatterns = [

    path('<dept>/', dept_detail, name='detail'),
    path('<dept>/get/new-start-date/', dept_get_new_start_date, name='new_start_date'),
    path('<dept>/get/sch-list/', dept_get_sch_list, name='get_sch_list'),
    path('<dept>/create/new-sch/', dept_build_new_sch, name='build-new-sch'),

    path('<dept>/employee/', include('frate.empl.urls', namespace='empl')),
    path('<dept>/schedule/', include('frate.sch.urls', namespace='sch')),
    ]

