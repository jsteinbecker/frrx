from django.urls import path,include
from . import views

app_name = 'sft'

urlpatterns = [
    path('', views.sft_list, name='list'),
    path('new/', views.sft_new, name='new'),
    path('<sft>/', views.sft_detail, name='detail'),
    ]