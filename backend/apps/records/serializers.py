# ══════════════════════════════════════════════════════════════
# apps/records/serializers.py
# ══════════════════════════════════════════════════════════════

from rest_framework import serializers
from .models import ClinicalRecord, MedicalDocument
 
 
class ClinicalRecordSerializer(serializers.ModelSerializer):
    doctor_name  = serializers.CharField(source='doctor.user.full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
 
    class Meta:
        model = ClinicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name', 'appointment',
            'chief_complaint', 'history_of_illness', 'examination_findings',
            'diagnosis', 'treatment_plan', 'follow_up_date', 'is_confidential',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
 
    def validate(self, attrs):
        request = self.context['request']
        if request.user.role == 'doctor':
            attrs['doctor'] = request.user.doctor_profile
        return attrs
 
 
class MedicalDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
 
    class Meta:
        model = MedicalDocument
        fields = [
            'id', 'patient', 'uploaded_by', 'uploaded_by_name', 'clinical_record',
            'document_type', 'title', 'file', 'description', 'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at']

