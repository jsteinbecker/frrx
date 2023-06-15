from django.urls import path
from .views import (empl_new, empl_list, empl_detail, empl_templates, get_options, empl_templates_update,
                    empl_templates_update_to_tdo, add_pto_req, empl_templates_to_generic,
                    empl_templates_update_to_rotating
                    )


app_name = 'empl'

urlpatterns = [
        path('', empl_list, name='list'),
        path('create/', empl_new, name='new'),
        path('<empl>/', empl_detail, name='detail'),
        path('<empl>/templates/', empl_templates, name='templates'),
        path('<empl>/templates/get-options/', get_options, name='options'),
        path('<empl>/templates/update/', empl_templates_update, name='update'),
        path('<empl>/templates/update-rotating/', empl_templates_update_to_rotating, name='update-as-rotating'),
        path('<empl>/templates/update-as-tdo/', empl_templates_update_to_tdo, name='update-as-tdo'),
        path('<empl>/templates/reset/', empl_templates_to_generic, name='reset-to-available'),
        path('<empl>/add-pto/', add_pto_req, name='add-pto'),
    ]

