from django.urls import path, include
from frate.models import Slot
from ..sch.models import Schedule
from ..sft.models import Shift
from ..empl.models import Employee

from .views import SlotViews, WdViews, QuerySets

# /frate/ver/urls.py
app_name = 'wd'

urlpatterns = [
        path('<wd>/',                   WdViews.detail,          name='detail'),
        path('<wd>/on-deck/',           QuerySets.on_deck,       name='on-deck'),
        path('<wd>/assign-rotating/',   WdViews.assign_rotating, name='assign-rotating'),
        path('<wd>/<empl>/delete-pto/', WdViews.delete_pto,      name='delete-pto'),
        path('<wd>/<empl>/create-pto/', WdViews.create_pto,      name='create-pto'),


        path('<wd>/<sft>/', include('frate.slot.urls', namespace='slot')),

    ]
