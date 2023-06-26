from django.urls import path, include
from .api import (dept_get_new_start_date,
                  dept_build_new_sch,
                 dept_get_sch_list)
from .views import (dept_detail, rts_detail, role_new, edit_dept, rts_assign,
                    rts_slotform_1, rts_slotform_2_direct, rts_slotform_2_rotating)


app_name = 'dept'


urlpatterns = [

    path('<dept>/', dept_detail, name='detail'),
    path('<dept>/edit/', edit_dept, name='edit'),
    path('<dept>/get/new-start-date/', dept_get_new_start_date, name='new_start_date'),
    path('<dept>/get/sch-list/', dept_get_sch_list, name='get_sch_list'),
    path('<dept>/create/new-sch/', dept_build_new_sch, name='build-new-sch'),

    # path('<dept>/role/', role_redirect, name='role-redirect'),
    # path('<dept>/role/<role>/', rts_detail, name='role-detail'),
    # path('<dept>/role/<role>/employees-assigned/', rts_assign, name='role-redirect'),
    # path('<dept>/role/<role>/<sd_id>/', rts_slotform_1, name='role-slot'),
    # path('<dept>/role/<role>/<sd_id>/r/', rts_slotform_2_rotating, name='role-slot-rotating/'),
    # path('<dept>/role/<role>/<sd_id>/d/', rts_slotform_2_direct, name='role-slot-direct/'),

    path('<dept>/employee/', include('frate.empl.urls', namespace='empl')),
    path('<dept>/schedule/', include('frate.sch.urls',  namespace='sch')),
    path('<dept>/shift/',    include('frate.sft.urls',  namespace='sft')),
    path('<dept>/role/',     include('frate.role.urls', namespace='role')),
    ]

