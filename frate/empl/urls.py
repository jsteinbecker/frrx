from django.urls import path, include

from .views import (empl_new, empl_list, empl_detail, empl_templates, get_options,
                    empl_inequity_monitoring, empl_templates_update,
                    empl_templates_update_to_tdo, add_pto_req, empl_templates_to_generic,
                    empl_templates_update_to_rotating, update_trainings, empl_search,
                    Utils, empl_sort_shifts, empl_edit
                    )

"""
=======================================
////// _ _ _ EMPLOYEE URLS _ _ _ //////
=======================================
"""

app_name = 'empl'

urlpatterns = [
    path('', empl_list, name='list'),
    path('create/', empl_new, name='new'),
    path('search/', empl_search, name='search'),
    path('inequity/', empl_inequity_monitoring, name='inequity'),

    path('<empl>/', empl_detail, name='detail'),
    path('<empl>/edit/', empl_edit, name='edit'),
    path('<empl>/sort-shifts/',empl_sort_shifts, name='sort-shifts'),
    path('<empl>/update-training/',update_trainings, name='update-training'),

    path('<empl>/templates/',empl_templates, name='templates'),
    path('<empl>/templates/get-options/',get_options, name='options'),
    path('<empl>/templates/update/',empl_templates_update, name='update'),
    path('<empl>/templates/update-rotating/',empl_templates_update_to_rotating, name='update-as-rotating'),
    path('<empl>/templates/update-as-tdo/',empl_templates_update_to_tdo, name='update-as-tdo'),
    path('<empl>/templates/reset/',empl_templates_to_generic, name='reset-to-available'),
    path('<empl>/templates/swap-template-week-ct/',Utils.swap_template_week_ct, name='swap-template-week-ct'),

    path('<empl>/add-pto/',add_pto_req, name='add-pto'),
    path('<empl>/validate-date/',Utils.validate_date, name='val-date'),
    path('<empl>/', include('frate.profile.urls', namespace='profile')),
]
