from django.urls import path
from . import views

urlpatterns = [
    path('api/study-events/', views.get_study_events, name='study_events'),
    path('api/ai-recommendations/', views.get_ai_recommendations, name='ai_recommendations'),
    path('api/pomodoro/complete/', views.complete_pomodoro, name='complete_pomodoro'),
    path('api/streak/', views.get_streak_info, name='streak_info'),
    path('api/auto-reschedule/', views.auto_reschedule, name='auto_reschedule'),
]