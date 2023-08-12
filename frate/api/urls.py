from .views import *
from django.urls import path, include
from frate.components.cal import display_month


app_name = 'api'

urlpatterns = [

        path('user/', get_user, name='get-user'),
        path('user/org/', get_user_org, name='get-user-org'),

    ]