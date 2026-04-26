// FullCalendar Integration
document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            editable: true,
            droppable: true,
            dragScroll: true,
            height: 'auto',
            slotMinTime: '08:00:00',
            slotMaxTime: '22:00:00',
            allDaySlot: false,
            eventDrop: function(info) {
                updateScheduleOnServer(info.event);
            },
            eventResize: function(info) {
                updateScheduleOnServer(info.event);
            },
            events: '/api/study-events/',
            eventDidMount: function(info) {
                if (info.event.extendedProps.progress) {
                    const progressBar = document.createElement('div');
                    progressBar.className = 'progress-bar-inline';
                    progressBar.style.position = 'absolute';
                    progressBar.style.bottom = '0';
                    progressBar.style.left = '0';
                    progressBar.style.height = '3px';
                    progressBar.style.width = '100%';
                    progressBar.style.background = 'rgba(255, 255, 255, 0.3)';
                    progressBar.innerHTML = `<div class="progress-fill" style="width: ${info.event.extendedProps.progress}%; height: 100%; background: white;"></div>`;
                    info.el.appendChild(progressBar);
                }
            },
            eventClick: function(info) {
                showEventDetails(info.event);
            }
        });
        
        calendar.render();
    }
});

// Pomodoro Timer Class
class PomodoroTimer {
    constructor() {
        this.timeLeft = 25 * 60;
        this.timerId = null;
        this.isRunning = false;
        this.currentSession = null;
    }
    
    start() {
        if (!this.isRunning) {
            const subject = document.getElementById('current-subject');
            if (!subject.value) {
                alert('Please select a subject first!');
                return;
            }
            this.isRunning = true;
            this.timerId = setInterval(() => this.tick(), 1000);
        }
    }
    
    pause() {
        clearInterval(this.timerId);
        this.isRunning = false;
    }
    
    reset() {
        this.pause();
        this.timeLeft = 25 * 60;
        this.updateDisplay();
    }
    
    tick() {
        if (this.timeLeft > 0) {
            this.timeLeft--;
            this.updateDisplay();
        } else {
            this.complete();
        }
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        const display = document.getElementById('timer-display');
        if (display) {
            display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    complete() {
        this.pause();
        this.saveSession();
        this.showNotification('Pomodoro Complete!', 'Time for a break! 🎉');
        this.reset();
    }
    
    saveSession() {
        const subjectId = document.getElementById('current-subject').value;
        fetch('/api/pomodoro/complete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                duration: 25,
                subject_id: subjectId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStreak();
            }
        });
    }
    
    showNotification(title, message) {
        if (Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize Pomodoro Timer
const pomodoro = new PomodoroTimer();

// Update AI Recommendations
function updateAIRecommendations() {
    fetch('/api/ai-recommendations/')
        .then(response => response.json())
        .then(data => {
            const panel = document.getElementById('ai-recommendations');
            if (panel) {
                panel.innerHTML = '';
                if (data.recommendations && data.recommendations.length > 0) {
                    data.recommendations.forEach(rec => {
                        const alertClass = rec.type === 'urgent' ? 'danger' : 
                                         rec.type === 'warning' ? 'warning' : 'info';
                        panel.innerHTML += `
                            <div class="ai-recommendation alert alert-${alertClass}">
                                <strong><i class="fas fa-robot me-2"></i>${rec.title}</strong>
                                <p class="mt-2 mb-1">${rec.message}</p>
                                <small>💡 ${rec.action}</small>
                            </div>
                        `;
                    });
                } else {
                    panel.innerHTML = '<div class="alert alert-success">🎉 Great job! You\'re on track!</div>';
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// Update Streak
function updateStreak() {
    fetch('/api/streak/')
        .then(response => response.json())
        .then(data => {
            const currentStreak = document.getElementById('current-streak');
            const longestStreak = document.getElementById('longest-streak');
            if (currentStreak) currentStreak.textContent = data.current_streak;
            if (longestStreak) longestStreak.textContent = data.longest_streak;
        });
}

// Auto-reschedule function
function autoReschedule() {
    fetch('/api/auto-reschedule/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

// Update schedule on server
function updateScheduleOnServer(event) {
    fetch('/api/update-schedule/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            event_id: event.id,
            start: event.start,
            end: event.end
        })
    });
}

// Show event details
function showEventDetails(event) {
    alert(`Subject: ${event.title}\nTime: ${event.start.toLocaleString()}\nProgress: ${event.extendedProps.progress || 0}%`);
}

// Dark Mode Toggle
function toggleDarkMode() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update icon
    const icon = document.querySelector('#theme-toggle i');
    if (icon) {
        icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Get cookie helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateAIRecommendations();
    updateStreak();
    
    // Request notification permission
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Auto-refresh AI recommendations every 30 seconds
    setInterval(updateAIRecommendations, 30000);
    setInterval(updateStreak, 60000);
});