# ══════════════════════════════════════════════════════════════
# backend/apps/doctors/tests/test_doctors.py
# ══════════════════════════════════════════════════════════════
@pytest.mark.django_db
class TestDoctorSearch:
 
    def test_list_doctors_returns_active_only(self, patient_client, doctor_user, db):
        # Create an inactive doctor
        inactive_doctor = make_doctor_user()
        inactive_doctor.is_active = False
        inactive_doctor.save()
 
        response = patient_client.get(reverse('doctor-list'))
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        # Inactive doctor should not appear
        emails = [d['user_email'] for d in results]
        assert inactive_doctor.email not in emails
 
    def test_search_by_speciality(self, patient_client, doctor_user, db):
        response = patient_client.get(
            reverse('doctor-list') + '?search=General'
        )
        assert response.status_code == status.HTTP_200_OK
 
    def test_get_doctor_available_slots(self, patient_client, doctor_user, db):
        from apps.accounts.models import DoctorAvailability
        DoctorAvailability.objects.create(
            doctor=doctor_user.doctor_profile,
            day_of_week=0,  # Monday
            start_time='09:00',
            end_time='17:00',
            slot_duration=30,
            is_active=True,
        )
        from datetime import date, timedelta
        # Find the next Monday
        today     = date.today()
        days_ahead = (0 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_ahead)
 
        response = patient_client.get(
            reverse('doctor-slots', kwargs={'pk': doctor_user.doctor_profile.id})
            + f'?date={next_monday}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'available_slots' in response.data
        assert len(response.data['available_slots']) > 0
 
    def test_slots_returns_empty_for_unavailable_day(
        self, patient_client, doctor_user, db
    ):
        """If doctor has no availability on that weekday, return empty list."""
        from datetime import date, timedelta
        # Pick next Sunday (day 6) — doctor has no Sunday availability
        today      = date.today()
        days_ahead = (6 - today.weekday()) % 7 or 7
        next_sunday = today + timedelta(days=days_ahead)
 
        response = patient_client.get(
            reverse('doctor-slots', kwargs={'pk': doctor_user.doctor_profile.id})
            + f'?date={next_sunday}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['available_slots'] == []
 
