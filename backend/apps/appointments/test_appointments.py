# ══════════════════════════════════════════════════════════════
# backend/apps/appointments/tests/test_appointments.py
# ══════════════════════════════════════════════════════════════
@pytest.mark.django_db
class TestAppointmentBooking:
 
    def test_patient_can_book_appointment(self, patient_client, doctor_user, db):
        from django.utils import timezone
        from datetime import timedelta
        url  = reverse('appointment-list-create')
        data = {
            'doctor':       doctor_user.doctor_profile.id,
            'scheduled_at': (timezone.now() + timedelta(days=3)).isoformat(),
            'reason':       'Fever and headache for 3 days',
        }
        response = patient_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert 'id' in response.data
 
    def test_patient_list_sees_only_own_appointments(
        self, patient_client, patient_user, doctor_user, appointment, db
    ):
        # Create another patient's appointment
        from apps.appointments.models import Appointment
        from django.utils import timezone
        from datetime import timedelta
        other_patient = make_patient_user()
        Appointment.objects.create(
            patient=other_patient,
            doctor=doctor_user.doctor_profile,
            scheduled_at=timezone.now() + timedelta(days=4),
        )
        response = patient_client.get(reverse('appointment-list-create'))
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        ids = [a['patient'] for a in results]
        assert all(pid == patient_user.id for pid in ids)
 
    def test_double_booking_prevented(self, patient_client, doctor_user, appointment, db):
        """FR-02.3: slot locking must prevent double-booking."""
        url  = reverse('appointment-list-create')
        data = {
            'doctor':       doctor_user.doctor_profile.id,
            'scheduled_at': appointment.scheduled_at.isoformat(),
            'reason':       'Conflicting booking attempt',
        }
        response = patient_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    def test_appointment_in_past_rejected(self, patient_client, doctor_user, db):
        from django.utils import timezone
        from datetime import timedelta
        response = patient_client.post(reverse('appointment-list-create'), {
            'doctor':       doctor_user.doctor_profile.id,
            'scheduled_at': (timezone.now() - timedelta(hours=1)).isoformat(),
            'reason':       'Past appointment',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    def test_doctor_can_mark_appointment_completed(self, doctor_client, appointment, db):
        url      = reverse('appointment-detail', kwargs={'pk': appointment.id})
        response = doctor_client.patch(url, {'status': 'completed'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
 
    def test_patient_cannot_mark_appointment_completed(self, patient_client, appointment, db):
        """Only doctors can update appointment status."""
        url      = reverse('appointment-detail', kwargs={'pk': appointment.id})
        response = patient_client.patch(url, {'status': 'completed'}, format='json')
        # Patient serialiser doesn't include status field for update
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN
        )
 
    def test_cancel_appointment(self, patient_client, appointment, db):
        url      = reverse('appointment-detail', kwargs={'pk': appointment.id})
        response = patient_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'
 
