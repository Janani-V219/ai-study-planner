from django.db import models
from django.contrib.auth.models import User
from planner.models import Subject

class StudyStreak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    streak_history = models.JSONField(default=dict)

class PomodoroSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=25)
    completed = models.BooleanField(default=False)
    breaks_taken = models.IntegerField(default=0)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, choices=[
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('achievement', 'Achievement'),
        ('recommendation', 'Recommendation')
    ])