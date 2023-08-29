from django.urls import path
from .views import *
from django.urls import include
from . import actions
from .ver_empl.views import ver_empl_list
from .api.api import VersionApiViews


app_name = 'ver'


urlpatterns = [

        path('new-version/', ver_new, name='new'),
        path('final/', ver_final, name='final'),
        path('<ver>/', ver_detail, name='detail'),

        path('<ver>/scheduling-matrix/', ver_matrix, name='matrix'),

        path('<ver>/pay-period-breakdown/', ver_pay_period_breakdown, name='pay-period-breakdown'),
        path('<ver>/employees/', ver_empl_list, name='ver-empls'),
        path('<ver>/empty-slots/', ver_empty_slots, name='empty-slots'),
        path('<ver>/templating/', ver_templating, name='templating'),
        path('<ver>/untrained/', ver_warn_untrained, name='untrained'),
        path('<ver>/scorecard/', ver_scorecard, name='scorecard'),
        path('<ver>/backfill/', ver_backfill_priority, name='backfill'),

        path('<ver>/shifts/', ver_shifts, name='shifts'),
        path('<ver>/shifts/<sft>/', ver_as_shift, name='as-shift'),

        path('<ver>/warnings/streak/', ver_warn_streak, name='warnings-streak'),
        path('<ver>/warnings/streak/fix/', ver_streak_fix, name='streak-fix'),

        path('<ver>/unfavorables/', ver_unfavorables, name='unfavorables'),
        path('<ver>/unfavorables/<empl>/', ver_unfavorables_for_empl, name='unfavorables-for-empl'),
        path('<ver>/unfavorables/<empl>/clear/', ver_unfavorables_clear_for_empl, name='unfavorables-clear'),

        path('<ver>/assign-templates/', ver_assign_templates, name='assign-templates'),
        path('<ver>/solve/', ver_solve, name='solve'),
        path('<ver>/clear/', ver_clear, name='clear'),
        path('<ver>/delete/', ver_delete, name='delete'),
        path('<ver>/verify-suboptimal-publish/', actions.verify_suboptimal_publish, name='publish-suboptimal'),
        path('<ver>/publish/', actions.publish, name='publish'),
        path('<ver>/unpublish/', actions.unpublish, name='unpublish'),

        path('<ver>/empl/<empl>/', ver_empl, name='empl'),

        path('<ver>/wd/',       include('frate.wday.urls', namespace='wd')),
        path('<ver>/pay-prd/',  include('frate.payprd.urls', namespace='ppd')),

        path('', include('frate.ver.api.urls', namespace='ver-api')),


    ]
