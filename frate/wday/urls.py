from django.urls import path
from frate.models import Employee, Schedule, Slot, Shift

from .views import wd_detail

app_name = 'wd'

urlpatterns = [
        path('<wd>/', wd_detail, name='detail'),
    ]
