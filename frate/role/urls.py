from django.urls import path
from .views import (new_role, detail, role_list, update_to_off, update_to_generic,
                    update_to_direct, update_to_direct_submitted, update_to_rotating, update_to_rotating_submitted,
                    delete_role, assign_empls)
from frate.dept.views import role_new


app_name = 'role'

urlpatterns = [

        path('', role_list , name='list'),
        path('new/', role_new, name='new'),
        path('<role>/', detail, name='detail'),

        path('<role>/off/', update_to_off, name='to-off'),
        path('<role>/generic/', update_to_generic, name='to-generic'),
        path('<role>/direct/', update_to_direct, name='to-direct'),
        path('<role>/direct/submit/', update_to_direct_submitted, name='to-direct-submit'),
        path('<role>/rotating/', update_to_rotating, name='to-rotating'),
        path('<role>/rotating/submit/', update_to_rotating_submitted, name='to-rotating-submit'),

        path('<role>/delete/', delete_role, name='delete'),

        path('<role>/assign/', assign_empls, name='assign'),

    ]