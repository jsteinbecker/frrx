from django.urls import path
from .views import (empl_ver_hours_by_period, ver_detail, ver_assign_templates,
                    ver_solve, ver_empl, ver_pay_period_breakdown, ver_new, ver_clear, ver_empty_slots)
from django.urls import include


app_name = 'ver'


urlpatterns = [
        path('new-version/', ver_new, name='new'),
        path('<ver>/', ver_detail, name='detail'),

        path('<ver>/pay-period-breakdown/', ver_pay_period_breakdown, name='pay-period-breakdown'),
        path('<ver>/empty-slots/', ver_empty_slots, name='empty-slots'),

        path('<ver>/assign-templates/', ver_assign_templates, name='assign-templates'),
        path('<ver>/solve/', ver_solve, name='solve'),
        path('<ver>/clear/', ver_clear, name='clear'),
        path('<ver>/empl/<empl>/', ver_empl, name='empl'),

        path('<ver>/wd/', include('frate.wday.urls', namespace='wd')),

    ]