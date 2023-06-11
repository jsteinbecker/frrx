from django.urls import path
from .views import empl_new, empl_list, empl_detail, empl_templates, get_options, empl_templates_update


app_name = 'empl'

urlpatterns = [
        path('', empl_list, name='list'),
        path('create/', empl_new, name='new'),
        path('<empl>/', empl_detail, name='detail'),
        path('<empl>/templates/', empl_templates, name='templates'),
        path('<empl>/templates/get-options/', get_options, name='options'),
        path('<empl>/templates/update/', empl_templates_update, name='update')
    ]

