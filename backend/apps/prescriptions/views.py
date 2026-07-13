# ══════════════════════════════════════════════════════════════
# apps/prescriptions/views.py
# ══════════════════════════════════════════════════════════════
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils import timezone
from apps.accounts.permissions import IsDoctor, IsPharmacist
from .models import Prescription


class PrescriptionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/prescriptions/ — List prescriptions for current user
    POST /api/v1/prescriptions/ — Issue new prescription (FR-06.1, Doctor only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import PrescriptionSerializer, PrescriptionCreateSerializer
        if self.request.method == 'POST':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        user = self.request.user
        qs   = Prescription.objects.select_related(
            'patient', 'doctor__user', 'pharmacist'
        )
        if user.role == 'patient':
            return qs.filter(patient=user)
        elif user.role == 'doctor':
            return qs.filter(doctor=user.doctor_profile)
        elif user.role == 'pharmacist':
            return qs.filter(status=Prescription.Status.ISSUED)
        elif user.role == 'admin':
            return qs.all()
        return qs.none()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsDoctor()]
        return [permissions.IsAuthenticated()]


@api_view(['PATCH'])
def dispense_prescription(request, pk):
    """
    PATCH /api/v1/prescriptions/{id}/dispense/
    Pharmacist marks prescription as dispensed (FR-06.4).
    Creates a complete dispensing record with timestamp.
    """
    if request.user.role != 'pharmacist':
        return Response(
            {'message': 'Only pharmacists can dispense prescriptions.'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.shortcuts import get_object_or_404
    prescription = get_object_or_404(Prescription, pk=pk)

    if prescription.status != Prescription.Status.ISSUED:
        return Response(
            {'message': f'Prescription cannot be dispensed. Current status: {prescription.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    prescription.status       = Prescription.Status.DISPENSED
    prescription.pharmacist   = request.user
    prescription.dispensed_at = timezone.now()
    prescription.save(update_fields=['status', 'pharmacist', 'dispensed_at'])

    # Notify patient that prescription has been dispensed
    from apps.notifications.tasks import send_dispensing_notification
    send_dispensing_notification.delay(prescription.id)

    return Response({'message': 'Prescription marked as dispensed successfully.'})


# ══════════════════════════════════════════════════════════════
# apps/records/models.py
# Electronic Health Records — implements FR-03
# ══════════════════════════════════════════════════════════════
from django.db import models as db_models

class ClinicalRecord(db_models.Model):
    """
    Stores structured clinical records per consultation.
    Separate from PatientProfile (the evergreen demographic record);
    ClinicalRecord captures the output of each specific consultation.
    """
    patient      = db_models.ForeignKey(
        'accounts.User', on_delete=db_models.PROTECT,
        related_name='clinical_records',
        limit_choices_to={'role': 'patient'}
    )
    doctor       = db_models.ForeignKey(
        'accounts.DoctorProfile', on_delete=db_models.PROTECT,
        related_name='clinical_records'
    )
    appointment  = db_models.ForeignKey(
        'appointments.Appointment', on_delete=db_models.SET_NULL,
        null=True, blank=True, related_name='clinical_record'
    )
    # SOAP note structure (Subjective, Objective, Assessment, Plan)
    chief_complaint       = db_models.TextField()
    history_of_illness    = db_models.TextField(blank=True)
    examination_findings  = db_models.TextField(blank=True)
    diagnosis             = db_models.TextField()
    treatment_plan        = db_models.TextField(blank=True)
    follow_up_date        = db_models.DateField(null=True, blank=True)
    is_confidential       = db_models.BooleanField(default=False)
    created_at            = db_models.DateTimeField(auto_now_add=True)
    updated_at            = db_models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_records'
        ordering = ['-created_at']

    def __str__(self):
        return f"Record #{self.id} — {self.patient.full_name} by Dr. {self.doctor.user.full_name}"


class MedicalDocument(db_models.Model):
    """
    Uploaded medical documents (lab results, X-rays, etc.).
    Stored on AWS S3 (FR-03.6).
    """
    class DocumentType(db_models.TextChoices):
        LAB_RESULT  = 'lab_result',  'Lab Result'
        XRAY        = 'xray',        'X-Ray'
        SCAN        = 'scan',        'Scan / Ultrasound'
        REPORT      = 'report',      'Medical Report'
        OTHER       = 'other',       'Other'

    patient        = db_models.ForeignKey(
        'accounts.User', on_delete=db_models.CASCADE, related_name='documents'
    )
    uploaded_by    = db_models.ForeignKey(
        'accounts.User', on_delete=db_models.SET_NULL,
        null=True, related_name='uploaded_documents'
    )
    clinical_record = db_models.ForeignKey(
        ClinicalRecord, on_delete=db_models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    document_type  = db_models.CharField(max_length=20, choices=DocumentType.choices)
    title          = db_models.CharField(max_length=200)
    file           = db_models.FileField(upload_to='medical-documents/%Y/%m/')
    description    = db_models.TextField(blank=True)
    created_at     = db_models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medical_documents'
        ordering = ['-created_at']

