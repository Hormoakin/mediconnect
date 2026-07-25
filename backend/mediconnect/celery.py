# ══════════════════════════════════════════════════════════════
# mediconnect/celery.py — Celery Application Configuration
# ══════════════════════════════════════════════════════════════
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect.settings.production')

app = Celery('mediconnect')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Periodic Tasks (Appointment Reminders) ────────────────────
app.conf.beat_schedule = {
    # Run every hour to check for upcoming appointments
    'send-24h-appointment-reminders': {
        'task': 'apps.notifications.tasks.send_appointment_reminders',
        'schedule': crontab(minute=0),  # Top of every hour
    },
    # Run every 15 minutes for 2-hour reminders (more time-sensitive)
    'send-2h-appointment-reminders': {
        'task': 'apps.notifications.tasks.send_two_hour_reminders',
        'schedule': crontab(minute='*/15'),
    },
    # Daily at 8 AM Lagos time — check uncollected prescriptions (FR-06.5)
    'flag-uncollected-prescriptions': {
        'task': 'apps.prescriptions.tasks.flag_uncollected_prescriptions',
        'schedule': crontab(hour=8, minute=0),
    },
    # Daily at midnight — expire old prescriptions
    'expire-old-prescriptions': {
        'task': 'apps.prescriptions.tasks.expire_old_prescriptions',
        'schedule': crontab(hour=0, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
