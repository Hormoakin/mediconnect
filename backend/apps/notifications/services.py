# ══════════════════════════════════════════════════════════════
# apps/notifications/services.py
# Twilio SMS and SendGrid Email service classes.
# ══════════════════════════════════════════════════════════════
import logging
from django.conf import settings
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)


class SMSService:
    """
    Twilio SMS integration for MediConnect.
    All Nigerian mobile networks supported via Twilio.
    Implements FR-02.4, FR-05.5, FR-06.2, FR-06.3.
    """
    def __init__(self):
        from twilio.rest import Client
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER

    def send(self, to_phone: str, message: str, user=None,
             notif_type=Notification.NotifType.APPOINTMENT_CONFIRMATION,
             reference_id='') -> bool:
        """
        Send SMS and log the result to the Notification table.
        Returns True on success, False on failure.
        """
        notif = Notification.objects.create(
            user=user,
            notif_type=notif_type,
            channel=Notification.Channel.SMS,
            recipient=to_phone,
            message=message,
            status=Notification.Status.PENDING,
            reference_id=str(reference_id),
        )
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_phone,
            )
            notif.status      = Notification.Status.SENT
            notif.provider_id = msg.sid
            notif.sent_at     = timezone.now()
            notif.save(update_fields=['status', 'provider_id', 'sent_at'])
            logger.info(f"SMS sent to {to_phone} — SID: {msg.sid}")
            return True
        except Exception as e:
            notif.status        = Notification.Status.FAILED
            notif.error_message = str(e)
            notif.save(update_fields=['status', 'error_message'])
            logger.error(f"SMS failed to {to_phone}: {e}")
            return False

    def send_appointment_confirmation(self, appointment):
        doctor = appointment.doctor.user.full_name
        dt     = appointment.scheduled_at.strftime('%d %b %Y at %I:%M %p')
        msg    = (
            f"MediConnect: Your appointment with Dr. {doctor} is confirmed "
            f"for {dt}. Reply CANCEL to cancel. Call 0800-MEDI for help."
        )
        return self.send(
            to_phone=appointment.patient.phone,
            message=msg,
            user=appointment.patient,
            notif_type=Notification.NotifType.APPOINTMENT_CONFIRMATION,
            reference_id=appointment.id,
        )

    def send_appointment_reminder(self, appointment, hours_before=24):
        doctor = appointment.doctor.user.full_name
        dt     = appointment.scheduled_at.strftime('%d %b %Y at %I:%M %p')
        msg    = (
            f"MediConnect Reminder: Your appointment with Dr. {doctor} "
            f"is in {hours_before} hour{'s' if hours_before > 1 else ''}. "
            f"Date: {dt}. Reply CANCEL to cancel."
        )
        notif_type = (
            Notification.NotifType.APPOINTMENT_REMINDER_24H if hours_before == 24
            else Notification.NotifType.APPOINTMENT_REMINDER_2H
        )
        return self.send(
            to_phone=appointment.patient.phone,
            message=msg,
            user=appointment.patient,
            notif_type=notif_type,
            reference_id=appointment.id,
        )

    def send_prescription_notification(self, prescription):
        msg = (
            f"MediConnect: Dr. {prescription.doctor.user.full_name} has issued "
            f"a prescription for {prescription.medication} ({prescription.dosage}). "
            f"Please collect from your pharmacy. Rx #{prescription.id}."
        )
        return self.send(
            to_phone=prescription.patient.phone,
            message=msg,
            user=prescription.patient,
            notif_type=Notification.NotifType.PRESCRIPTION_ISSUED,
            reference_id=prescription.id,
        )


class EmailService:
    """
    SendGrid email integration for MediConnect.
    Uses dynamic transactional templates for professional formatting.
    Implements FR-02.5, FR-06.2.
    """
    TEMPLATES = {
        'appointment_confirmation': 'd-appointment-confirmation-template-id',
        'appointment_reminder':     'd-appointment-reminder-template-id',
        'appointment_cancellation': 'd-appointment-cancellation-template-id',
        'prescription_issued':      'd-prescription-issued-template-id',
        'prescription_dispensed':   'd-prescription-dispensed-template-id',
        'welcome':                  'd-welcome-template-id',
        'password_reset':           'd-password-reset-template-id',
    }

    def __init__(self):
        import sendgrid
        self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    def send_template(self, to_email: str, template_key: str,
                      template_data: dict, user=None,
                      notif_type=Notification.NotifType.APPOINTMENT_CONFIRMATION,
                      reference_id='') -> bool:
        from sendgrid.helpers.mail import Mail, To, DynamicTemplateData

        notif = Notification.objects.create(
            user=user,
            notif_type=notif_type,
            channel=Notification.Channel.EMAIL,
            recipient=to_email,
            message=f"Email: {template_key}",
            status=Notification.Status.PENDING,
            reference_id=str(reference_id),
        )
        try:
            message = Mail(
                from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_NAME),
                to_emails=to_email,
            )
            message.template_id           = self.TEMPLATES.get(template_key, '')
            message.dynamic_template_data = template_data

            response = self.sg.send(message)
            success  = response.status_code in (200, 201, 202)

            notif.status  = Notification.Status.SENT if success else Notification.Status.FAILED
            notif.sent_at = timezone.now() if success else None
            notif.save(update_fields=['status', 'sent_at'])
            logger.info(f"Email {'sent' if success else 'failed'} to {to_email} ({template_key})")
            return success
        except Exception as e:
            notif.status        = Notification.Status.FAILED
            notif.error_message = str(e)
            notif.save(update_fields=['status', 'error_message'])
            logger.error(f"Email failed to {to_email}: {e}")
            return False

    def send_appointment_confirmation(self, appointment):
        return self.send_template(
            to_email=appointment.patient.email,
            template_key='appointment_confirmation',
            template_data={
                'patient_name':  appointment.patient.full_name,
                'doctor_name':   f"Dr. {appointment.doctor.user.full_name}",
                'appt_date':     appointment.scheduled_at.strftime('%A, %d %B %Y'),
                'appt_time':     appointment.scheduled_at.strftime('%I:%M %p'),
                'hospital':      appointment.doctor.hospital_name,
                'appointment_id': str(appointment.id),
                'cancel_url':    f"https://mediconnect.salman-aak.com/appointments/{appointment.id}/cancel",
            },
            user=appointment.patient,
            notif_type=Notification.NotifType.APPOINTMENT_CONFIRMATION,
            reference_id=appointment.id,
        )

