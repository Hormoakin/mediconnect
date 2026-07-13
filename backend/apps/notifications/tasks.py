"""
apps/notifications/tasks.py
Celery async tasks for all MediConnect notifications.
These run in the Celery worker pod, not in the Django API process,
so they do NOT block API response times (protecting NFR-01).
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_confirmation(self, appointment_id: int):
    """
    Send SMS + email confirmation when a new appointment is booked (FR-02.5).
    Triggered automatically in Appointment.save() for new instances.
    """
    try:
        from apps.appointments.models import Appointment
        from .services import SMSService, EmailService

        appt = Appointment.objects.select_related(
            'patient', 'doctor__user'
        ).get(pk=appointment_id)

        sms   = SMSService()
        email = EmailService()

        if appt.patient.phone:
            sms.send_appointment_confirmation(appt)

        email.send_appointment_confirmation(appt)
        logger.info(f"Appointment confirmation sent for appt #{appointment_id}")

    except Exception as exc:
        logger.error(f"send_appointment_confirmation failed for #{appointment_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_cancellation(self, appointment_id: int, cancelled_by: int):
    """
    Notify both parties when an appointment is cancelled (FR-02.6).
    """
    try:
        from apps.appointments.models import Appointment
        from apps.accounts.models import User
        from .services import SMSService, EmailService
        from .models import Notification

        appt    = Appointment.objects.select_related('patient', 'doctor__user').get(pk=appointment_id)
        canceller = User.objects.get(pk=cancelled_by)
        sms     = SMSService()

        dt = appt.scheduled_at.strftime('%d %b %Y at %I:%M %p')

        # Notify the other party
        if canceller.role == 'patient':
            # Notify doctor
            if appt.doctor.user.phone:
                msg = (
                    f"MediConnect: {appt.patient.full_name} has cancelled their "
                    f"appointment scheduled for {dt}."
                )
                sms.send(
                    to_phone=appt.doctor.user.phone,
                    message=msg,
                    user=appt.doctor.user,
                    notif_type=Notification.NotifType.APPOINTMENT_CANCELLATION,
                    reference_id=appointment_id,
                )
        else:
            # Notify patient
            if appt.patient.phone:
                msg = (
                    f"MediConnect: Dr. {appt.doctor.user.full_name} has cancelled "
                    f"your appointment scheduled for {dt}. Please rebook."
                )
                sms.send(
                    to_phone=appt.patient.phone,
                    message=msg,
                    user=appt.patient,
                    notif_type=Notification.NotifType.APPOINTMENT_CANCELLATION,
                    reference_id=appointment_id,
                )

    except Exception as exc:
        logger.error(f"send_appointment_cancellation failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_appointment_reminders():
    """
    Send 24-hour reminders for upcoming appointments (FR-02.4).
    Runs every hour via Celery beat (celery.py beat_schedule).
    """
    from apps.appointments.models import Appointment
    from .services import SMSService

    sms = SMSService()
    now = timezone.now()

    # Find appointments in the 23–25 hour window ahead
    upcoming = Appointment.objects.filter(
        status__in=['pending', 'confirmed'],
        reminder_sent_24h=False,
        scheduled_at__gte=now + timedelta(hours=23),
        scheduled_at__lte=now + timedelta(hours=25),
    ).select_related('patient', 'doctor__user')

    sent_count = 0
    for appt in upcoming:
        if appt.patient.phone:
            success = sms.send_appointment_reminder(appt, hours_before=24)
            if success:
                appt.reminder_sent_24h = True
                appt.save(update_fields=['reminder_sent_24h'])
                sent_count += 1

    logger.info(f"24h reminders sent: {sent_count}")
    return sent_count


@shared_task
def send_two_hour_reminders():
    """
    Send 2-hour reminders for upcoming appointments (FR-02.4).
    Runs every 15 minutes via Celery beat.
    """
    from apps.appointments.models import Appointment
    from .services import SMSService

    sms = SMSService()
    now = timezone.now()

    upcoming = Appointment.objects.filter(
        status__in=['pending', 'confirmed'],
        reminder_sent_2h=False,
        scheduled_at__gte=now + timedelta(hours=1, minutes=50),
        scheduled_at__lte=now + timedelta(hours=2, minutes=10),
    ).select_related('patient', 'doctor__user')

    sent_count = 0
    for appt in upcoming:
        if appt.patient.phone:
            success = sms.send_appointment_reminder(appt, hours_before=2)
            if success:
                appt.reminder_sent_2h = True
                appt.save(update_fields=['reminder_sent_2h'])
                sent_count += 1

    logger.info(f"2h reminders sent: {sent_count}")
    return sent_count


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_prescription_notification(self, prescription_id: int):
    """
    Notify patient (SMS + email) when a new prescription is issued (FR-06.2).
    Triggered automatically in Prescription.save() for new instances.
    """
    try:
        from apps.prescriptions.models import Prescription
        from .services import SMSService

        rx  = Prescription.objects.select_related(
            'patient', 'doctor__user'
        ).get(pk=prescription_id)
        sms = SMSService()

        if rx.patient.phone:
            sms.send_prescription_notification(rx)
        logger.info(f"Prescription notification sent for Rx #{prescription_id}")

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dispensing_notification(self, prescription_id: int):
    """
    Notify patient when prescription is dispensed (FR-06.4 follow-up).
    """
    try:
        from apps.prescriptions.models import Prescription
        from .services import SMSService
        from .models import Notification

        rx  = Prescription.objects.select_related('patient', 'pharmacist').get(pk=prescription_id)
        sms = SMSService()
        pharmacist = rx.pharmacist.full_name if rx.pharmacist else 'your pharmacist'

        if rx.patient.phone:
            msg = (
                f"MediConnect: Your prescription for {rx.medication} "
                f"has been dispensed by {pharmacist}. Rx #{prescription_id}."
            )
            sms.send(
                to_phone=rx.patient.phone,
                message=msg,
                user=rx.patient,
                notif_type=Notification.NotifType.PRESCRIPTION_DISPENSED,
                reference_id=prescription_id,
            )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_welcome_email(self, user_id: int):
    """
    Send welcome email after registration.
    """
    try:
        from django.contrib.auth import get_user_model
        from .services import EmailService
        from .models import Notification

        User  = get_user_model()
        user  = User.objects.get(pk=user_id)
        email = EmailService()
        email.send_template(
            to_email=user.email,
            template_key='welcome',
            template_data={
                'full_name':  user.full_name,
                'role':       user.get_role_display() if hasattr(user, 'get_role_display') else user.role,
                'login_url':  'https://mediconnect.salman-aak.com/login',
            },
            user=user,
            notif_type=Notification.NotifType.WELCOME,
            reference_id=user_id,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_password_reset_email(self, user_id: int):
    """
    Generate a password reset token and send email (FR-01.5).
    """
    try:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from .services import EmailService
        from .models import Notification

        User  = get_user_model()
        user  = User.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid   = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = f"https://mediconnect.salman-aak.com/reset-password?uid={uid}&token={token}"

        email = EmailService()
        email.send_template(
            to_email=user.email,
            template_key='password_reset',
            template_data={
                'full_name': user.full_name,
                'reset_url': reset_url,
                'expires':   '24 hours',
            },
            user=user,
            notif_type=Notification.NotifType.PASSWORD_RESET,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

