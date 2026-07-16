# ══════════════════════════════════════════════════════════════
# backend/apps/prescriptions/tests/test_prescriptions.py
# ══════════════════════════════════════════════════════════════
@pytest.mark.django_db
class TestPrescriptionLifecycle:
 
    def test_doctor_can_issue_prescription(
        self, doctor_client, patient_user, appointment, db
    ):
        response = doctor_client.post(reverse('prescription-list-create'), {
            'patient':      patient_user.id,
            'appointment':  appointment.id,
            'medication':   'Artemether-Lumefantrine',
            'dosage':       '80mg/480mg',
            'frequency':    'Twice daily for 3 days',
            'duration_days': 3,
            'instructions': 'Take with food.',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'issued'
        assert 'expires_at' in response.data
 
    def test_prescription_expires_30_days(self, prescription, db):
        """Prescriptions must expire 30 days from issue (FR-06.5)."""
        from django.utils import timezone
        from datetime import timedelta
        delta = prescription.expires_at - prescription.issued_at
        assert 29 <= delta.days <= 31
 
    def test_patient_can_view_own_prescriptions(
        self, patient_client, prescription, db
    ):
        response = patient_client.get(reverse('prescription-list-create'))
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        ids = [rx['id'] for rx in results]
        assert prescription.id in ids
 
    def test_prescription_status_machine(self, pharmacist_client, prescription, db):
        """Status must follow issued → dispensed (not skip states)."""
        # Cannot go directly to 'expired' via the dispense endpoint
        url = reverse('prescription-dispense', kwargs={'pk': prescription.id})
        response = pharmacist_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        prescription.refresh_from_db()
        assert prescription.status == 'dispensed'
        # Dispensed at timestamp must be set
        assert prescription.dispensed_at is not None
 
 
