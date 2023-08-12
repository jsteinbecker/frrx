from .views import generate_verif_token
from django.urls import path



app_name = 'profile'

urlpatterns = [

    path('verif-token/', generate_verif_token, name='generate_verif_token'),

    ]