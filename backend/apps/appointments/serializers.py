"""
apps/appointments/serializers.py
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, DoctorReview
from apps.accounts.serializers import DoctorProfileSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name       = serializers.CharField(source='doctor.user.full_name', read_only=True)
    doctor_speciality = serializers.CharField(source='doctor.speciality', read_only=True)
    patient_name      = serializers.CharField(source='patient.full_name', read_only=True)
    is_upcoming       = serializers.BooleanField(read_only=True)
    can_cancel        = serializers.SerializerMethodField()
    has_review        = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'doctor_speciality', 'scheduled_at', 'duration_mins',
            'status', 'reason', 'doctor_notes', 'is_upcoming',
            'can_cancel', 'has_review', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'doctor_notes', 'created_at']

    def get_can_cancel(self, obj):
        return obj.can_be_cancelled()

    def get_has_review(self, obj):
        return hasattr(obj, 'review')

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Appointment must be scheduled in the future.')
        return value

    def validate(self, attrs):
        # Ensure patient field is set to the current user for patients
        request = self.context.get('request')
        if request and request.user.role == 'patient':
            attrs['patient'] = request.user
        return attrs


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Appointment
        fields = ['doctor', 'scheduled_at', 'duration_mins', 'reason']

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Appointment must be scheduled in the future.')
        return value

    def create(self, validated_data):
        # Automatically set patient to the requesting user
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    """Restricted serializer for status updates only (doctor use)."""
    class Meta:
        model  = Appointment
        fields = ['status', 'doctor_notes']

    def validate_status(self, value):
        instance = self.instance
        allowed_transitions = {
            'pending':   ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled', 'no_show'],
            'completed': [],
            'cancelled': [],
            'no_show':   [],
        }
        current = instance.status if instance else 'pending'
        if value not in allowed_transitions.get(current, []):
            raise serializers.ValidationError(
                f"Cannot transition from '{current}' to '{value}'."
            )
        return value


class DoctorReviewSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model  = DoctorReview
        fields = ['id', 'appointment', 'patient', 'patient_name', 'doctor', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'patient', 'patient_name', 'created_at']

    def validate_appointment(self, value):
        request = self.context['request']
        if value.patient != request.user:
            raise serializers.ValidationError('You can only review your own appointments.')
        if value.status != 'completed':
            raise serializers.ValidationError('You can only review completed appointments.')
        if hasattr(value, 'review'):
            raise serializers.ValidationError('You have already reviewed this appointment.')
        return value

    def create(self, validated_data):
        validated_data['patient'] = self.context['request'].user
        validated_data['doctor']  = validated_data['appointment'].doctor
        return super().create(validated_data)

