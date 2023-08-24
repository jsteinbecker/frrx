from django.urls import path,include
from . import views

app_name = 'sft'

urlpatterns = [
    path('', views.sft_list, name='list'),
    path('new/', views.sft_new, name='new'),
    path('<sft>/', views.sft_detail, name='detail'),
    path('<sft>/tallies/', views.sft_tallies, name='tallies'),
    path('<sft>/rank-summary/', views.sft_rank_summary, name='rank-summary'),

    ]