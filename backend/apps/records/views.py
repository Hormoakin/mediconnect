# ══════════════════════════════════════════════════════════════
# apps/records/views.py
# ══════════════════════════════════════════════════════════════
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from apps.accounts.permissions import IsDoctor
from .models import ClinicalRecord, MedicalDocument
from .serializers import ClinicalRecordSerializer, MedicalDocumentSerializer
 
 
class ClinicalRecordListCreateView(generics.ListCreateAPIView):
    '''
    GET  /api/v1/records/        — Get patient medical records (FR-03.4)
    POST /api/v1/records/        — Create clinical note (FR-03.3, Doctor only)
    '''
    serializer_class   = ClinicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        user = self.request.user
        qs   = ClinicalRecord.objects.select_related('patient', 'doctor__user')
        if user.role == 'patient':
            return qs.filter(patient=user, is_confidential=False)
        elif user.role == 'doctor':
            return qs.filter(doctor=user.doctor_profile)
        elif user.role == 'admin':
            return qs.all()
        return qs.none()
 
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsDoctor()]
        return [permissions.IsAuthenticated()]
 
 
class ClinicalRecordDetailView(generics.RetrieveUpdateAPIView):
    serializer_class   = ClinicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return ClinicalRecord.objects.filter(doctor=user.doctor_profile)
        return ClinicalRecord.objects.filter(patient=user)
 
 
class MedicalDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class   = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes     = []  # MultiPartParser/FormParser added at runtime for file uploads
 
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalDocument.objects.filter(patient=user)
        elif user.role == 'doctor':
            return MedicalDocument.objects.filter(
                patient__patient_appointments__doctor=user.doctor_profile
            ).distinct()
        return MedicalDocument.objects.all()
 
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

