from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from .models import Subject, StudySession, StudyProgress, StudyRecommendation
from .ai_logic import AIScheduler, PerformanceAnalyzer
from datetime import datetime, timedelta
import json

def home(request):
    return render(request, 'planner/home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'planner/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'planner/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    subjects = Subject.objects.filter(user=request.user)
    
    total_subjects = subjects.count()
    completed_sessions = StudySession.objects.filter(
        subject__user=request.user,
        completed=True
    ).count()
    total_study_hours = StudyProgress.objects.filter(
        user=request.user
    ).aggregate(total=models.Sum('hours_studied'))['total'] or 0
    
    upcoming_deadlines = subjects.filter(
        deadline__gte=timezone.now()
    ).order_by('deadline')[:5]
    
    context = {
        'total_subjects': total_subjects,
        'completed_sessions': completed_sessions,
        'total_study_hours': round(total_study_hours, 1),
        'upcoming_deadlines': upcoming_deadlines,
    }
    return render(request, 'planner/dashboard.html', context)

@login_required
def add_subject(request):
    if request.method == 'POST':
        name = request.POST['name']
        deadline_str = request.POST['deadline']
        difficulty = int(request.POST['difficulty'])
        hours_needed = int(request.POST['hours_needed'])
        
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        
        subject = Subject.objects.create(
            user=request.user,
            name=name,
            deadline=deadline,
            difficulty=difficulty,
            hours_needed=hours_needed
        )
        
        messages.success(request, f'Subject "{name}" added successfully!')
        return redirect('view_schedule')
    
    return render(request, 'planner/add_subject.html')

@login_required
def view_schedule(request):
    subjects = Subject.objects.filter(user=request.user)
    
    if not subjects:
        messages.warning(request, 'Please add subjects first to generate schedule')
        return redirect('add_subject')
    
    scheduler = AIScheduler(list(subjects), available_hours_per_day=4)
    schedule_data = scheduler.generate_schedule()
    
    schedule = []
    current_date = timezone.now().date()
    
    for day_index, daily_subjects in schedule_data.items():
        date = current_date + timedelta(days=day_index)
        schedule.append({
            'date': date,
            'subjects': daily_subjects
        })
    
    progress_data = StudyProgress.objects.filter(user=request.user)
    recommendations = PerformanceAnalyzer.get_study_recommendations(
        request.user, list(subjects), list(progress_data)
    )
    
    context = {
        'schedule': schedule[:7],
        'recommendations': recommendations,
        'subjects': subjects,
    }
    return render(request, 'planner/schedule.html', context)

@login_required
def record_progress(request):
    if request.method == 'POST':
        subject_id = request.POST['subject_id']
        hours_studied = float(request.POST['hours_studied'])
        confidence_level = int(request.POST['confidence_level'])
        quiz_score = int(request.POST['quiz_score'])
        
        subject = get_object_or_404(Subject, id=subject_id, user=request.user)
        
        progress = StudyProgress.objects.create(
            user=request.user,
            subject=subject,
            hours_studied=hours_studied,
            confidence_level=confidence_level,
            quiz_score=quiz_score
        )
        
        today = timezone.now().date()
        session, created = StudySession.objects.get_or_create(
            subject=subject,
            date=today,
            defaults={
                'start_time': timezone.now(),
                'end_time': timezone.now() + timedelta(hours=hours_studied),
                'completed': True,
                'performance_score': quiz_score
            }
        )
        
        if not created:
            session.completed = True
            session.performance_score = quiz_score
            session.save()
        
        scheduler = AIScheduler([subject])
        adjustments = scheduler.adjust_based_on_performance([progress])
        
        if adjustments:
            messages.info(request, f"AI Suggestion: {adjustments[0]['reason']}")
        
        messages.success(request, 'Progress recorded successfully!')
        return redirect('view_schedule')
    
    subjects = Subject.objects.filter(user=request.user)
    context = {'subjects': subjects}
    return render(request, 'planner/record_progress.html', context)

@login_required
def performance_analytics(request):
    progress_data = StudyProgress.objects.filter(
        user=request.user
    ).order_by('-date')[:30]
    
    subject_performance = {}
    for progress in progress_data:
        subject_name = progress.subject.name
        if subject_name not in subject_performance:
            subject_performance[subject_name] = {
                'scores': [],
                'confidence': [],
                'hours': []
            }
        subject_performance[subject_name]['scores'].append(progress.quiz_score)
        subject_performance[subject_name]['confidence'].append(progress.confidence_level)
        subject_performance[subject_name]['hours'].append(progress.hours_studied)
    
    for subject in subject_performance:
        if subject_performance[subject]['scores']:
            subject_performance[subject]['avg_score'] = sum(subject_performance[subject]['scores']) / len(subject_performance[subject]['scores'])
            subject_performance[subject]['avg_confidence'] = sum(subject_performance[subject]['confidence']) / len(subject_performance[subject]['confidence'])
            subject_performance[subject]['total_hours'] = sum(subject_performance[subject]['hours'])
        else:
            subject_performance[subject]['avg_score'] = 0
            subject_performance[subject]['avg_confidence'] = 0
            subject_performance[subject]['total_hours'] = 0
    
    trend = PerformanceAnalyzer.predict_performance_trend(list(progress_data))
    
    context = {
        'subject_performance': subject_performance,
        'trend_prediction': trend,
        'recent_progress': progress_data[:10]
    }
    return render(request, 'planner/analytics.html', context)

@login_required
def api_get_schedule_data(request):
    subjects = Subject.objects.filter(user=request.user)
    scheduler = AIScheduler(list(subjects))
    schedule_data = scheduler.generate_schedule()
    
    schedule_json = {}
    for day, subjects_list in schedule_data.items():
        schedule_json[day] = [
            {
                'name': s['subject'].name,
                'hours': s['hours'],
                'priority': s['priority']
            }
            for s in subjects_list
        ]
    
    return JsonResponse(schedule_json)

@login_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, user=request.user)
    subject.delete()
    messages.success(request, 'Subject deleted successfully')
    return redirect('view_schedule')