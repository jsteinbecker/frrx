from django.urls import path
from frate.models import Employee, Schedule, Slot, Shift

from .views import SlotViews, WdViews

app_name = 'wd'

urlpatterns = [
        path('<wd>/', WdViews.detail, name='detail'),
        path('<wd>/assign-rotating/', WdViews.assign_rotating, name='assign-rotating'),

        path('<wd>/assign/<sft>/<empl>/', SlotViews.assign, name='assign'),
    ]
