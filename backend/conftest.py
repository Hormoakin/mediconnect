# ══════════════════════════════════════════════════════════════
# backend/conftest.py
# Shared pytest fixtures and factory helpers for all test modules.
# ══════════════════════════════════════════════════════════════
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ── User factories ────────────────────────────────────────────
def make_user(role: str, **kwargs) -> User:
    """Create a test user with the given role."""
    defaults = {
        'email':     f'test_{role}_{User.objects.count()}@test.com',
        'username':  f'test_{role}_{User.objects.count()}',
        'full_name': f'Test {role.title()}',
        'phone':     '+2348012345678',
        'role':      role,
        'is_active': True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_password('TestPass123!')
    user.save()
    return user


def make_doctor_user(**kwargs):
    from apps.accounts.models import DoctorProfile
    user = make_user('doctor', **kwargs)
    DoctorProfile.objects.create(
        user=user,
        speciality=kwargs.get('speciality', 'General Practitioner'),
        license_number=f'LIC-{user.id:04d}',
        bio='Test doctor bio.',
        years_experience=5,
        consultation_fee=5000.00,
        rating=4.5,
        is_available=True,
        hospital_name='Test Hospital',
    )
    return user


def make_patient_user(**kwargs):
    from apps.accounts.models import PatientProfile
    user = make_user('patient', **kwargs)
    PatientProfile.objects.create(user=user)
    return user


def auth_client(user) -> APIClient:
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


# ── Pytest fixtures ────────────────────────────────────────────
@pytest.fixture
def patient_user(db):
    return make_patient_user()


@pytest.fixture
def doctor_user(db):
    return make_doctor_user()


@pytest.fixture
def pharmacist_user(db):
    return make_user('pharmacist')


@pytest.fixture
def admin_user(db):
    return make_user('admin')


@pytest.fixture
def patient_client(patient_user):
    return auth_client(patient_user)


@pytest.fixture
def doctor_client(doctor_user):
    return auth_client(doctor_user)


@pytest.fixture
def pharmacist_client(pharmacist_user):
    return auth_client(pharmacist_user)


@pytest.fixture
def admin_client(admin_user):
    return auth_client(admin_user)


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def appointment(db, patient_user, doctor_user):
    """Creates a confirmed appointment between patient and doctor."""
    from apps.appointments.models import Appointment
    from django.utils import timezone
    from datetime import timedelta
    return Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_user.doctor_profile,
        scheduled_at=timezone.now() + timedelta(days=2),
        duration_mins=30,
        status='confirmed',
        reason='Routine check-up',
    )


@pytest.fixture
def prescription(db, patient_user, doctor_user, appointment):
    """Creates an issued prescription linked to an appointment."""
    from apps.prescriptions.models import Prescription
    return Prescription.objects.create(
        appointment=appointment,
        patient=patient_user,
        doctor=doctor_user.doctor_profile,
        medication='Amoxicillin',
        dosage='500mg',
        frequency='Three times daily',
        duration_days=7,
        instructions='Take after meals.',
    )
