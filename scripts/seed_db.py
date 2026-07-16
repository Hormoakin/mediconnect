#!/usr/bin/env python3
"""
scripts/seed_db.py
Seeds the MediConnect database with test users for load testing.
Creates:
  - 500 patient users   (loadtest_patient_1@test.com … _500@test.com)
  - 20  doctor users    (loadtest_doctor_1@test.com  … _20@test.com)
  - Doctor availability slots for all 20 doctors (Mon–Fri, 9am–5pm)
  - 100 sample appointments (distributed across doctors)

Run:
  docker exec -it mediconnect_backend python scripts/seed_db.py
  OR:
  kubectl exec -n mediconnect deploy/backend -- python scripts/seed_db.py
"""
import os
import django
import random
from datetime import datetime, timedelta, time as dtime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import DoctorProfile, PatientProfile, DoctorAvailability
from apps.appointments.models import Appointment
from django.utils import timezone

User = get_user_model()

PASSWORD     = "TestLoad123!"
SPECIALITIES = [
    "General Practitioner", "Cardiologist", "Neurologist",
    "Paediatrician", "Dermatologist", "Gynaecologist",
    "Orthopaedic Surgeon", "Psychiatrist", "Endocrinologist",
    "Pulmonologist", "Gastroenterologist", "Urologist",
    "Haematologist", "Ophthalmologist", "ENT Specialist",
    "Oncologist", "Rheumatologist", "Nephrologist",
    "Emergency Medicine", "General Surgeon",
]
HOSPITALS = [
    "Lagos University Teaching Hospital", "Eko Hospital",
    "Reddington Hospital", "Lagoon Hospital",
    "St. Nicholas Hospital", "Nigerian Navy Reference Hospital",
    "General Hospital Gbagada", "Island General Hospital",
]

def seed_patients(n=500):
    print(f"Creating {n} test patients...")
    created = 0
    for i in range(1, n + 1):
        email = f"loadtest_patient_{i}@test.com"
        if User.objects.filter(email=email).exists():
            continue
        user = User(
            email=email,
            username=f"loadtest_patient_{i}",
            full_name=f"Load Test Patient {i}",
            phone=f"+234801{i:07d}",
            role="patient",
            is_active=True,
        )
        user.set_password(PASSWORD)
        user.save()
        PatientProfile.objects.get_or_create(user=user)
        created += 1
    print(f"  ✅ Created {created} patients ({n - created} already existed)")


def seed_doctors(n=20):
    print(f"Creating {n} test doctors...")
    created = 0
    for i in range(1, n + 1):
        email = f"loadtest_doctor_{i}@test.com"
        if User.objects.filter(email=email).exists():
            continue
        speciality = SPECIALITIES[(i - 1) % len(SPECIALITIES)]
        user = User(
            email=email,
            username=f"loadtest_doctor_{i}",
            full_name=f"Dr. Load Test Doctor {i}",
            phone=f"+234802{i:07d}",
            role="doctor",
            is_active=True,
        )
        user.set_password(PASSWORD)
        user.save()

        DoctorProfile.objects.create(
            user=user,
            speciality=speciality,
            license_number=f"TEST-LIC-{i:04d}",
            bio=f"Test doctor specialising in {speciality}.",
            years_experience=random.randint(2, 20),
            consultation_fee=random.choice([5000, 8000, 10000, 15000, 20000]),
            rating=round(random.uniform(3.5, 5.0), 1),
            is_available=True,
            hospital_name=random.choice(HOSPITALS),
        )
        created += 1

    print(f"  ✅ Created {created} doctors ({n - created} already existed)")

    # Add Mon–Fri 9am–5pm availability for all test doctors
    print("  Adding availability slots...")
    for doctor_profile in DoctorProfile.objects.filter(
        user__email__startswith="loadtest_doctor_"
    ):
        for day in range(0, 5):   # Mon=0 … Fri=4
            DoctorAvailability.objects.get_or_create(
                doctor=doctor_profile,
                day_of_week=day,
                defaults={
                    "start_time":    dtime(9, 0),
                    "end_time":      dtime(17, 0),
                    "slot_duration": 30,
                    "is_active":     True,
                }
            )
    print("  ✅ Availability slots created (Mon–Fri 09:00–17:00, 30-min slots)")


def seed_appointments(n=100):
    print(f"Creating {n} sample appointments...")
    patients = list(User.objects.filter(email__startswith="loadtest_patient_")[:50])
    doctors  = list(DoctorProfile.objects.filter(
        user__email__startswith="loadtest_doctor_"
    ))

    if not patients or not doctors:
        print("  ⚠️  No test patients or doctors found — run seed_patients and seed_doctors first")
        return

    created = 0
    for i in range(n):
        patient = random.choice(patients)
        doctor  = random.choice(doctors)
        days    = random.randint(1, 60)
        hour    = random.randint(9, 16)
        minute  = random.choice([0, 30])
        dt      = timezone.now() + timedelta(days=days, hours=hour - timezone.now().hour)
        dt      = dt.replace(minute=minute, second=0, microsecond=0)

        if not Appointment.objects.filter(
            doctor=doctor, scheduled_at=dt, status__in=["pending", "confirmed"]
        ).exists():
            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                scheduled_at=dt,
                duration_mins=30,
                status=random.choice(["pending", "confirmed"]),
                reason="Load test appointment",
                reminder_sent_24h=False,
                reminder_sent_2h=False,
            )
            created += 1

    print(f"  ✅ Created {created} appointments")


if __name__ == "__main__":
    print("\n🌱 Seeding MediConnect database for load testing...\n")
    seed_patients(500)
    seed_doctors(20)
    seed_appointments(100)
    print("\n✅ Database seeded! Ready for Locust load testing.")
    print(f"   Patient credentials: loadtest_patient_N@test.com / {PASSWORD}")
    print(f"   Doctor credentials:  loadtest_doctor_N@test.com  / {PASSWORD}")
