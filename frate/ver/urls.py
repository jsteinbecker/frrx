from django.urls import path
from .views import *
from django.urls import include


app_name = 'ver'


urlpatterns = [
        path('new-version/', ver_new, name='new'),
        path('<ver>/', ver_detail, name='detail'),

        path('<ver>/pay-period-breakdown/', ver_pay_period_breakdown, name='pay-period-breakdown'),
        path('<ver>/empty-slots/', ver_empty_slots, name='empty-slots'),

        path('<ver>/unfavorables/', ver_unfavorables, name='unfavorables'),
        path('<ver>/unfavorables/<empl>/clear/', ver_unfavorables_clear_for_empl, name='unfavorables-clear'),

        path('<ver>/assign-templates/', ver_assign_templates, name='assign-templates'),
        path('<ver>/solve/', ver_solve, name='solve'),
        path('<ver>/clear/', ver_clear, name='clear'),
        path('<ver>/delete/', ver_delete, name='delete'),

        path('<ver>/empl/<empl>/', ver_empl, name='empl'),

        path('<ver>/wd/',       include('frate.wday.urls', namespace='wd')),
        path('<ver>/pay-prd/',  include('frate.payprd.urls', namespace='ppd')),

    ]