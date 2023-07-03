from django.urls import path, include
from frate.models import Employee, Schedule, Slot, Shift

from .views import SlotViews, WdViews

# /frate/ver/urls.py
app_name = 'wd'

urlpatterns = [
        path('<wd>/', WdViews.detail, name='detail'),
        path('<wd>/assign-rotating/', WdViews.assign_rotating, name='assign-rotating'),
        path('<wd>/<empl>/delete-pto/', WdViews.delete_pto, name='delete-pto'),

        path('<wd>/<sft>/', include('frate.slot.urls', namespace='slot')),
    ]
