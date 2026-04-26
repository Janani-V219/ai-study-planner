from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-subject/', views.add_subject, name='add_subject'),
    path('schedule/', views.view_schedule, name='view_schedule'),
    path('record-progress/', views.record_progress, name='record_progress'),
    path('analytics/', views.performance_analytics, name='analytics'),
    path('api/schedule-data/', views.api_get_schedule_data, name='api_schedule'),
    path('delete-subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),
]