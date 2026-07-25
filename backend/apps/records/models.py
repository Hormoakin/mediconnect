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
 
