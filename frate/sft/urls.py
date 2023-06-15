from django.urls import path,include
from . import views

app_name = 'sft'

urlpatterns = [
    path('<sft>/', views.sft_detail, name='detail'),
    ]