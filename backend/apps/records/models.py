"""
apps/prescriptions/models.py
Electronic prescription management — implements FR-06.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Prescription(models.Model):
    """
    Electronic prescription lifecycle:
    issued → dispensed (or cancelled / expired)
    Status CHECK constraint encodes FR-06.4–FR-06.6 lifecycle.
    """
    class Status(models.TextChoices):
        ISSUED    = 'issued',    'Issued'
        DISPENSED = 'dispensed', 'Dispensed'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED   = 'expired',   'Expired'

    appointment  = models.ForeignKey(
        'appointments.Appointment', on_delete=models.PROTECT,
        related_name='prescriptions', null=True, blank=True
    )
    patient      = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT,
        related_name='prescriptions',
        limit_choices_to={'role': 'patient'}
    )
    doctor       = models.ForeignKey(
        'accounts.DoctorProfile', on_delete=models.PROTECT,
        related_name='prescriptions_issued'
    )
    pharmacist   = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prescriptions_dispensed',
        limit_choices_to={'role': 'pharmacist'}
    )
    # Medication details (FR-06.1)
    medication    = models.CharField(max_length=200)
    dosage        = models.CharField(max_length=100)
    frequency     = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    instructions  = models.TextField(blank=True)

    status        = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ISSUED
    )
    issued_at     = models.DateTimeField(auto_now_add=True)
    dispensed_at  = models.DateTimeField(null=True, blank=True)
    expires_at    = models.DateTimeField()
    follow_up_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-issued_at']
        indexes  = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['pharmacist', 'status']),
            models.Index(fields=['expires_at']),
        ]

    def save(self, *args, **kwargs):
        # Auto-set expiry to 30 days from issue (FR-06.5)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Notify patient and pharmacist on new prescription (FR-06.2, FR-06.3)
        if is_new:
            from apps.notifications.tasks import send_prescription_notification
            send_prescription_notification.delay(self.id)

    def __str__(self):
        return f"Rx #{self.id} — {self.medication} for {self.patient.full_name}"

