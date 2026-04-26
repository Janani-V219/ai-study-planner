import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from collections import defaultdict

class AIScheduler:
    def __init__(self, subjects, available_hours_per_day=4):
        self.subjects = subjects
        self.available_hours_per_day = available_hours_per_day
        
    def calculate_urgency_score(self, subject):
        now = timezone.now()
        days_left = max(1, (subject.deadline - now).days)
        
        if days_left <= 1:
            urgency = 100
        elif days_left <= 3:
            urgency = 80
        elif days_left <= 7:
            urgency = 60
        elif days_left <= 14:
            urgency = 40
        else:
            urgency = 20
            
        return urgency
    
    def calculate_difficulty_weight(self, subject):
        return subject.difficulty * 0.5
    
    def calculate_priority_score(self, subject):
        urgency = self.calculate_urgency_score(subject)
        difficulty_weight = self.calculate_difficulty_weight(subject)
        hours_needed = subject.hours_needed
        
        priority = (urgency * 0.4) + (difficulty_weight * 20 * 0.3) + (hours_needed * 0.3)
        return priority
    
    def generate_schedule(self):
        schedule = []
        current_date = timezone.now().date()
        
        subjects_with_priority = []
        for subject in self.subjects:
            priority = self.calculate_priority_score(subject)
            subjects_with_priority.append({
                'subject': subject,
                'priority': priority,
                'hours_needed': subject.hours_needed
            })
        
        subjects_with_priority.sort(key=lambda x: x['priority'], reverse=True)
        
        daily_schedule = defaultdict(list)
        remaining_hours = {s['subject'].id: s['hours_needed'] for s in subjects_with_priority}
        
        days_to_schedule = 14
        day_count = 0
        
        while any(hours > 0 for hours in remaining_hours.values()) and day_count < days_to_schedule:
            current_date = timezone.now().date() + timedelta(days=day_count)
            
            hours_allocated_today = 0
            daily_subjects = []
            
            for subject_info in subjects_with_priority:
                subject = subject_info['subject']
                if remaining_hours[subject.id] > 0:
                    study_hours = min(2, remaining_hours[subject.id])
                    
                    if subject_info['priority'] > 70:
                        study_hours = min(3, remaining_hours[subject.id])
                    
                    if hours_allocated_today + study_hours <= self.available_hours_per_day:
                        daily_subjects.append({
                            'subject': subject,
                            'hours': study_hours,
                            'priority': subject_info['priority']
                        })
                        remaining_hours[subject.id] -= study_hours
                        hours_allocated_today += study_hours
                    
                    if hours_allocated_today >= self.available_hours_per_day:
                        break
            
            daily_schedule[day_count] = daily_subjects
            day_count += 1
        
        return daily_schedule
    
    def adjust_based_on_performance(self, progress_data):
        adjustments = []
        
        for progress in progress_data:
            subject = progress.subject
            if progress.confidence_level < 40:
                adjustments.append({
                    'subject': subject,
                    'action': 'increase',
                    'hours': 1,
                    'reason': f"Low confidence ({progress.confidence_level}%) in {subject.name}"
                })
            elif progress.confidence_level > 80:
                adjustments.append({
                    'subject': subject,
                    'action': 'decrease',
                    'hours': 0.5,
                    'reason': f"High confidence ({progress.confidence_level}%) in {subject.name}"
                })
            
            if progress.quiz_score < 50:
                adjustments.append({
                    'subject': subject,
                    'action': 'increase',
                    'hours': 1.5,
                    'reason': f"Low quiz score ({progress.quiz_score}%) in {subject.name}"
                })
        
        return adjustments

class PerformanceAnalyzer:
    @staticmethod
    def predict_performance_trend(progress_history):
        if len(progress_history) < 3:
            return "Not enough data for prediction"
        
        scores = [p.quiz_score for p in progress_history]
        trend = np.polyfit(range(len(scores)), scores, 1)[0]
        
        if trend > 5:
            return "Rapidly improving - Keep up the great work!"
        elif trend > 0:
            return "Slowly improving - Consistency is key!"
        elif trend == 0:
            return "Stable performance - Try to push harder"
        else:
            return "Declining performance - Need immediate intervention"
    
    @staticmethod
    def get_study_recommendations(user, subjects, progress_data):
        recommendations = []
        
        study_sessions = defaultdict(int)
        for progress in progress_data:
            study_sessions[progress.subject.name] += progress.hours_studied
        
        for subject in subjects:
            total_studied = study_sessions.get(subject.name, 0)
            hours_needed = subject.hours_needed
            days_left = max(1, (subject.deadline - timezone.now()).days)
            
            required_daily = (hours_needed - total_studied) / days_left
            
            if required_daily > 3:
                recommendations.append({
                    'subject': subject,
                    'priority': 100,
                    'text': f"⚠️ CRITICAL: Need {required_daily:.1f} hours/day for {subject.name}. Consider adjusting schedule!"
                })
            elif required_daily > 2:
                recommendations.append({
                    'subject': subject,
                    'priority': 80,
                    'text': f"⚠️ HIGH PRIORITY: Study {required_daily:.1f} hours/day for {subject.name}"
                })
            elif required_daily > 1:
                recommendations.append({
                    'subject': subject,
                    'priority': 60,
                    'text': f"📚 Study {required_daily:.1f} hours/day for {subject.name} to stay on track"
                })
            else:
                recommendations.append({
                    'subject': subject,
                    'priority': 40,
                    'text': f"✅ On track for {subject.name} - Maintain current pace"
                })
        
        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)[:5]