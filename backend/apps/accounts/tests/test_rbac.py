# ══════════════════════════════════════════════════════════════
# backend/apps/accounts/tests/test_rbac.py
# Role-Based Access Control enforcement tests
# 22 test cases covering all role/endpoint combinations
# ══════════════════════════════════════════════════════════════
@pytest.mark.django_db
class TestRBACEnforcement:
 
    # ── Doctor-only endpoints ─────────────────────────────────
    def test_patient_cannot_create_clinical_record(self, patient_client, db):
        response = patient_client.post(reverse('record-list-create'), {
            'patient': 1, 'chief_complaint': 'test', 'diagnosis': 'test'
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_patient_cannot_issue_prescription(self, patient_client, appointment, db):
        response = patient_client.post(reverse('prescription-list-create'), {
            'patient': appointment.patient.id,
            'appointment': appointment.id,
            'medication': 'Amoxicillin', 'dosage': '500mg',
            'frequency': 'TDS', 'duration_days': 7,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_pharmacist_cannot_create_prescription(self, pharmacist_client, appointment, db):
        response = pharmacist_client.post(reverse('prescription-list-create'), {
            'patient': appointment.patient.id,
            'medication': 'Test', 'dosage': '10mg',
            'frequency': 'OD', 'duration_days': 3,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    # ── Pharmacist-only endpoints ─────────────────────────────
    def test_patient_cannot_dispense_prescription(
        self, patient_client, prescription, db
    ):
        url      = reverse('prescription-dispense', kwargs={'pk': prescription.id})
        response = patient_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_doctor_cannot_dispense_prescription(
        self, doctor_client, prescription, db
    ):
        url      = reverse('prescription-dispense', kwargs={'pk': prescription.id})
        response = doctor_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_pharmacist_can_dispense_prescription(
        self, pharmacist_client, prescription, db
    ):
        url      = reverse('prescription-dispense', kwargs={'pk': prescription.id})
        response = pharmacist_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        prescription.refresh_from_db()
        assert prescription.status == 'dispensed'
 
    def test_cannot_dispense_already_dispensed_prescription(
        self, pharmacist_client, prescription, db
    ):
        """Double-dispensing must be prevented."""
        url = reverse('prescription-dispense', kwargs={'pk': prescription.id})
        pharmacist_client.patch(url)              # First dispense
        response = pharmacist_client.patch(url)   # Second attempt
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    # ── Admin-only endpoints ──────────────────────────────────
    def test_patient_cannot_access_admin_stats(self, patient_client, db):
        response = patient_client.get(reverse('admin-stats'))
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_doctor_cannot_access_admin_stats(self, doctor_client, db):
        response = doctor_client.get(reverse('admin-stats'))
        assert response.status_code == status.HTTP_403_FORBIDDEN
 
    def test_admin_can_access_stats(self, admin_client, db):
        response = admin_client.get(reverse('admin-stats'))
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'appointments' in response.data
 
    # ── Patient data isolation ────────────────────────────────
    def test_patient_cannot_access_other_patient_appointments(
        self, db, doctor_user
    ):
        """FR-03: patients see only their own records."""
        from apps.appointments.models import Appointment
        from django.utils import timezone
        from datetime import timedelta
 
        patient_a = make_patient_user()
        patient_b = make_patient_user()
 
        appt = Appointment.objects.create(
            patient=patient_b,
            doctor=doctor_user.doctor_profile,
            scheduled_at=timezone.now() + timedelta(days=1),
        )
 
        client_a = auth_client(patient_a)
        url      = reverse('appointment-detail', kwargs={'pk': appt.id})
        response = client_a.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
 
