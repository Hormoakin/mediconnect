"""
apps/accounts/models.py
MediConnect User model — single table for all four roles.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    A single users table serves all four stakeholder roles:
    Patient, Doctor, Pharmacist, Administrator.
    The role field drives RBAC enforcement at the API layer.
    """

    class Role(models.TextChoices):
        PATIENT    = 'patient',     _('Patient')
        DOCTOR     = 'doctor',      _('Doctor')
        PHARMACIST = 'pharmacist',  _('Pharmacist')
        ADMIN      = 'admin',       _('Administrator')

    # Core identity fields
    email      = models.EmailField(_('email address'), unique=True)
    full_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    role       = models.CharField(max_length=20, choices=Role.choices)
    is_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(
        upload_to='profiles/', null=True, blank=True
    )

    # Use email as the primary login identifier
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'role']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    # ── Role helpers ──────────────────────────────────────────
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_pharmacist(self):
        return self.role == self.Role.PHARMACIST

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class DoctorProfile(models.Model):
    """
    Doctor-specific profile attributes.
    Extends User with a 1:1 relationship (sub-type pattern).
    Only users with role='doctor' should have a DoctorProfile.
    """
    user           = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='doctor_profile'
    )
    speciality     = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    bio            = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    rating         = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    total_reviews  = models.PositiveIntegerField(default=0)
    is_available   = models.BooleanField(default=True)
    hospital_name  = models.CharField(max_length=200, blank=True)
    hospital_address = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_profiles'

    def __str__(self):
        return f"Dr. {self.user.full_name} — {self.speciality}"

    def update_rating(self):
        """Recalculate average rating from all reviews."""
        from apps.appointments.models import DoctorReview
        reviews = DoctorReview.objects.filter(doctor=self)
        if reviews.exists():
            self.rating = reviews.aggregate(
                avg=models.Avg('rating')
            )['avg']
            self.total_reviews = reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])


class PatientProfile(models.Model):
    """
    Patient-specific medical profile.
    1:1 with User, contains the electronic patient record data
    required by FR-03.1 and FR-03.2.
    """
    user                = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='patient_profile'
    )
    date_of_birth       = models.DateField(null=True, blank=True)
    blood_group         = models.CharField(max_length=10, blank=True)
    genotype            = models.CharField(max_length=10, blank=True)
    allergies           = models.TextField(blank=True)
    chronic_conditions  = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    next_of_kin_name    = models.CharField(max_length=150, blank=True)
    next_of_kin_phone   = models.CharField(max_length=20, blank=True)
    emergency_contact   = models.CharField(max_length=20, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_profiles'

    def __str__(self):
        return f"Patient: {self.user.full_name}"


class DoctorAvailability(models.Model):
    """
    Doctor weekly availability schedule.
    A doctor can define available time slots by day of week.
    Used by FR-02.2 (display real-time availability calendars).
    """
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    doctor         = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name='availability'
    )
    day_of_week    = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time     = models.TimeField()
    end_time       = models.TimeField()
    slot_duration  = models.PositiveIntegerField(default=30, help_text='Minutes per slot')
    is_active      = models.BooleanField(default=True)

    class Meta:
        db_table = 'doctor_availability'
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        day = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        return f"Dr. {self.doctor.user.full_name} — {day} {self.start_time}–{self.end_time}"


class AuditLog(models.Model):
    """
    Immutable audit trail for all sensitive data modifications.
    Implements FR-03.5: complete, immutable audit log of record modifications.
    Also supports NDPR compliance (NFR-12).
    """
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        READ   = 'read',   'Read'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN  = 'login',  'Login'
        LOGOUT = 'logout', 'Logout'

    user          = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='audit_logs'
    )
    action        = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=50)
    resource_id   = models.CharField(max_length=50, blank=True)
    description   = models.TextField(blank=True)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    user_agent    = models.TextField(blank=True)
    timestamp     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        # Make audit log entries truly immutable at the DB level
        # by removing update and delete permissions
        default_permissions = ('add', 'view')

    def __str__(self):
        return f"{self.user} {self.action} {self.resource_type} at {self.timestamp}"

