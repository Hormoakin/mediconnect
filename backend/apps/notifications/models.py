"""
apps/notifications/models.py
Notification log for all SMS and email communications.
"""
from django.db import models


class Notification(models.Model):
    """
    Persistent log of every outbound SMS and email notification.
    Provides audit trail and delivery tracking for FR-02.4, FR-02.5,
    FR-06.2, FR-06.3, FR-05.5.
    """
    class Channel(models.TextChoices):
        SMS   = 'sms',   'SMS'
        EMAIL = 'email', 'Email'

    class NotifType(models.TextChoices):
        APPOINTMENT_CONFIRMATION = 'appt_confirmation',  'Appointment Confirmation'
        APPOINTMENT_REMINDER_24H = 'appt_reminder_24h',  '24-Hour Reminder'
        APPOINTMENT_REMINDER_2H  = 'appt_reminder_2h',   '2-Hour Reminder'
        APPOINTMENT_CANCELLATION = 'appt_cancellation',  'Appointment Cancellation'
        PRESCRIPTION_ISSUED      = 'rx_issued',          'Prescription Issued'
        PRESCRIPTION_DISPENSED   = 'rx_dispensed',       'Prescription Dispensed'
        NEW_MESSAGE              = 'new_message',        'New Message Alert'
        WELCOME                  = 'welcome',            'Welcome'
        PASSWORD_RESET           = 'password_reset',     'Password Reset'

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        SENT     = 'sent',     'Sent'
        FAILED   = 'failed',   'Failed'
        SKIPPED  = 'skipped',  'Skipped'

    user          = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='notifications'
    )
    notif_type    = models.CharField(max_length=30, choices=NotifType.choices)
    channel       = models.CharField(max_length=10, choices=Channel.choices)
    recipient     = models.CharField(max_length=200)   # phone or email
    message       = models.TextField()
    status        = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference_id  = models.CharField(max_length=50, blank=True)  # appointment_id or rx_id
    provider_id   = models.CharField(max_length=100, blank=True) # Twilio SID or SendGrid message id
    error_message = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    sent_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['user', 'notif_type']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.channel.upper()}] {self.notif_type} → {self.recipient} ({self.status})"


class Message(models.Model):
    """
    Real-time doctor-patient messages.
    Persisted to PostgreSQL for history and read receipts (FR-05.4).
    WebSocket delivery is handled by the Socket.io server.
    """
    sender    = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='received_messages'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages'
    )
    content   = models.TextField()
    is_read   = models.BooleanField(default=False)
    read_at   = models.DateTimeField(null=True, blank=True)
    sent_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['sent_at']
        indexes  = [
            models.Index(fields=['sender', 'recipient', 'sent_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.full_name} to {self.recipient.full_name}"

