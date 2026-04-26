from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from .models import StudyStreak, PomodoroSession, Notification
from .ai_recommendations import AdvancedAI
from planner.models import StudySession, Subject, StudyProgress

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_study_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    sessions = StudySession.objects.filter(
        subject__user=request.user,
        date__range=[start, end]
    )
    
    events = []
    for session in sessions:
        events.append({
            'id': session.id,
            'title': session.subject.name,
            'start': f"{session.date}T{session.start_time}",
            'end': f"{session.date}T{session.end_time}",
            'backgroundColor': get_subject_color(session.subject),
            'extendedProps': {
                'progress': calculate_progress(session)
            }
        })
    
    return Response(events)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_recommendations(request):
    ai = AdvancedAI(request.user)
    recommendations = ai.generate_smart_recommendations()
    return Response({'recommendations': recommendations})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_pomodoro(request):
    data = request.data
    subject_id = data.get('subject_id')
    duration = data.get('duration', 25)
    
    subject = Subject.objects.get(id=subject_id, user=request.user)
    
    PomodoroSession.objects.create(
        user=request.user,
        subject=subject,
        duration=duration,
        completed=True
    )
    
    update_study_streak(request.user)
    
    return Response({'success': True})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_streak_info(request):
    streak, created = StudyStreak.objects.get_or_create(user=request.user)
    return Response({
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_reschedule(request):
    ai = AdvancedAI(request.user)
    falling_behind = ai.detect_falling_behind()
    
    for subject_info in falling_behind:
        missed_sessions = StudySession.objects.filter(
            subject__name=subject_info['subject'],
            subject__user=request.user,
            completed=False,
            date__lt=timezone.now().date()
        )
        
        for session in missed_sessions:
            new_date = timezone.now().date() + timedelta(days=1)
            session.date = new_date
            session.save()
            
            Notification.objects.create(
                user=request.user,
                title=f'Rescheduled: {subject_info["subject"]}',
                message=f'Missed session rescheduled to {new_date}',
                notification_type='reminder'
            )
    
    return Response({'success': True})

def update_study_streak(user):
    streak, created = StudyStreak.objects.get_or_create(user=user)
    today = timezone.now().date()
    
    if streak.last_study_date == today - timedelta(days=1):
        streak.current_streak += 1
    elif streak.last_study_date != today:
        streak.current_streak = 1
    
    streak.last_study_date = today
    
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak
        
        Notification.objects.create(
            user=user,
            title='🏆 Achievement Unlocked!',
            message=f'New record! {streak.current_streak} day study streak!',
            notification_type='achievement'
        )
    
    streak.save()

def get_subject_color(subject):
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308']
    return colors[hash(subject.name) % len(colors)]

def calculate_progress(session):
    total_hours = session.subject.hours_needed
    completed_hours = StudyProgress.objects.filter(
        subject=session.subject
    ).aggregate(total=Sum('hours_studied'))['total'] or 0
    
    return min(100, int((completed_hours / total_hours) * 100)) if total_hours > 0 else 0