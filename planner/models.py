from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subject(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Very Easy'),
        (2, 'Easy'),
        (3, 'Medium'),
        (4, 'Hard'),
        (5, 'Very Hard'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    deadline = models.DateTimeField()
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=3)
    hours_needed = models.IntegerField(help_text="Total hours needed to master this subject")
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class StudySession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    completed = models.BooleanField(default=False)
    performance_score = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.subject.name} - {self.date}"

class StudyProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    hours_studied = models.FloatField()
    confidence_level = models.IntegerField(default=50)
    quiz_score = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.subject.name} - {self.date}"

class StudyRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    recommendation_text = models.TextField()
    priority_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendation for {self.subject.name}"