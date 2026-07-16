# ══════════════════════════════════════════════════════════════
# backend/apps/notifications/tests/test_notifications.py
# Tests for Twilio and SendGrid notification services (mocked)
# ══════════════════════════════════════════════════════════════
@pytest.mark.django_db
class TestNotificationService:
 
    @patch('apps.notifications.services.Client')
    def test_sms_sent_on_appointment_confirmation(
        self, mock_twilio, patient_user, doctor_user, db
    ):
        from apps.appointments.models import Appointment
        from apps.notifications.services import SMSService
        from django.utils import timezone
        from datetime import timedelta
 
        mock_messages = MagicMock()
        mock_messages.create.return_value = MagicMock(sid='SM123', status='sent')
        mock_twilio.return_value.messages = mock_messages
 
        sms  = SMSService()
        appt = Appointment(
            patient=patient_user,
            doctor=doctor_user.doctor_profile,
            scheduled_at=timezone.now() + timedelta(days=2),
        )
        appt.save()
 
        result = sms.send_appointment_confirmation(appt)
        assert result is True
        mock_messages.create.assert_called_once()
 
    @patch('apps.notifications.services.Client')
    def test_sms_failure_logged_not_raised(
        self, mock_twilio, patient_user, doctor_user, db
    ):
        """SMS failure must be logged but must NOT crash the booking flow."""
        from apps.notifications.services import SMSService
        from apps.appointments.models import Appointment
        from django.utils import timezone
        from datetime import timedelta
 
        mock_twilio.return_value.messages.create.side_effect = Exception("Twilio error")
 
        sms  = SMSService()
        appt = Appointment(
            patient=patient_user,
            doctor=doctor_user.doctor_profile,
            scheduled_at=timezone.now() + timedelta(days=2),
        )
        appt.save()
 
        result = sms.send_appointment_confirmation(appt)
        assert result is False   # Returns False, does not raise
 
    @patch('apps.notifications.services.Client')
    def test_notification_log_created_on_send(
        self, mock_twilio, patient_user, db
    ):
        from apps.notifications.services import SMSService
        from apps.notifications.models import Notification
 
        mock_twilio.return_value.messages.create.return_value = MagicMock(
            sid='SM456', status='sent'
        )
 
        patient_user.phone = '+2348012345678'
        patient_user.save()
 
        sms = SMSService()
        sms.send(
            to_phone=patient_user.phone,
            message='Test message',
            user=patient_user,
            notif_type=Notification.NotifType.APPOINTMENT_CONFIRMATION,
        )
 
        notif = Notification.objects.filter(user=patient_user).first()
        assert notif is not None
        assert notif.status == Notification.Status.SENT
        assert notif.provider_id == 'SM456'
 
