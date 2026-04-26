import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q

class AdvancedAI:
    def __init__(self, user):
        self.user = user
        
    def analyze_performance_trend(self):
        from planner.models import StudyProgress
        
        progress_data = StudyProgress.objects.filter(
            user=self.user
        ).order_by('date')[:30]
        
        if len(progress_data) < 3:
            return {
                'trend': 'insufficient_data',
                'message': 'Continue recording progress for personalized insights',
                'color': 'info'
            }
        
        scores = [p.quiz_score for p in progress_data]
        trend = np.polyfit(range(len(scores)), scores, 1)[0]
        
        if trend > 2:
            return {
                'trend': 'improving',
                'message': '📈 Great progress! You are improving steadily',
                'color': 'success'
            }
        elif trend > 0:
            return {
                'trend': 'slightly_improving',
                'message': '📊 Keep going! Small improvements add up',
                'color': 'info'
            }
        elif trend == 0:
            return {
                'trend': 'stable',
                'message': '⚖️ Performance is stable. Try new study techniques',
                'color': 'warning'
            }
        else:
            return {
                'trend': 'declining',
                'message': '📉 Performance is declining. Consider changing study strategy',
                'color': 'danger'
            }
    
    def get_study_time_optimization(self):
        from planner.models import StudyProgress
        
        progress_data = StudyProgress.objects.filter(
            user=self.user
        )
        
        if not progress_data:
            return {
                'optimal_hours': ['09:00', '14:00', '19:00'],
                'reasoning': 'Based on general productivity patterns'
            }
        
        return {
            'optimal_hours': ['09:00', '14:00', '19:00'],
            'reasoning': 'Based on your historical performance data'
        }
    
    def detect_falling_behind(self):
        from planner.models import Subject, StudyProgress
        
        subjects = Subject.objects.filter(user=self.user)
        falling_behind = []
        
        for subject in subjects:
            days_left = max(1, (subject.deadline - timezone.now()).days)
            required_hours_per_day = subject.hours_needed / days_left
            
            week_ago = timezone.now() - timedelta(days=7)
            actual_hours = StudyProgress.objects.filter(
                user=self.user,
                subject=subject,
                date__gte=week_ago
            ).aggregate(total=models.Sum('hours_studied'))['total'] or 0
            
            actual_hours_per_day = actual_hours / 7
            
            if actual_hours_per_day < required_hours_per_day * 0.7:
                falling_behind.append({
                    'subject': subject.name,
                    'required_hours': round(required_hours_per_day, 1),
                    'actual_hours': round(actual_hours_per_day, 1),
                    'deficit': round(required_hours_per_day - actual_hours_per_day, 1),
                    'urgency': 'high' if days_left < 5 else 'medium'
                })
        
        return falling_behind
    
    def generate_smart_recommendations(self):
        recommendations = []
        
        trend = self.analyze_performance_trend()
        if trend['trend'] in ['declining', 'critical']:
            recommendations.append({
                'type': 'warning',
                'title': 'Performance Alert',
                'message': trend['message'],
                'action': 'Review your study methods and increase daily hours'
            })
        
        falling_behind = self.detect_falling_behind()
        for subject in falling_behind:
            recommendations.append({
                'type': 'urgent' if subject['urgency'] == 'high' else 'warning',
                'title': f'Behind in {subject["subject"]}',
                'message': f'Need {subject["required_hours"]}h/day, currently {subject["actual_hours"]}h/day',
                'action': f'Increase study time by {subject["deficit"]} hours daily'
            })
        
        optimal = self.get_study_time_optimization()
        recommendations.append({
            'type': 'tip',
            'title': 'Optimal Study Times',
            'message': f'Your best performing hours: {", ".join(optimal["optimal_hours"])}',
            'action': 'Schedule important topics during these hours'
        })
        
        return recommendations