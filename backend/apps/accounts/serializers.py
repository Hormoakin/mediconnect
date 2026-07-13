"""
apps/accounts/serializers.py
Authentication and user profile serializers.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, DoctorProfile, PatientProfile, DoctorAvailability


class MediConnectTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that embeds role, full_name, and user_id
    into the token payload. This allows the frontend to read the role
    from the decoded JWT without a separate /api/v1/users/me/ call
    on every page load.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed role-specific claims
        token['role']      = user.role
        token['full_name'] = user.full_name
        token['user_id']   = user.id
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id':         self.user.id,
            'email':      self.user.email,
            'full_name':  self.user.full_name,
            'role':       self.user.role,
            'is_verified': self.user.is_verified,
        }
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles new user registration (FR-01.1).
    Validates password strength and uniqueness of email.
    """
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'full_name', 'phone',
            'role', 'password', 'confirm_password'
        ]
        extra_kwargs = {
            'email':    {'required': True},
            'role':     {'required': True},
            'full_name':{'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        # Validate role — only patient and doctor can self-register
        allowed_self_register_roles = [User.Role.PATIENT, User.Role.DOCTOR]
        if attrs['role'] not in allowed_self_register_roles:
            raise serializers.ValidationError(
                {'role': 'Pharmacist and Administrator accounts must be created by an administrator.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # PBKDF2 hashing via Django's AbstractUser
        user.save()

        # Auto-create role-specific profile
        if user.role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user)
        elif user.role == User.Role.DOCTOR:
            DoctorProfile.objects.create(
                user=user,
                speciality='General Practice',
                license_number=f'TEMP-{user.id}',
            )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read/write serializer for the authenticated user's own profile (FR-01.4).
    """
    doctor_profile  = serializers.SerializerMethodField()
    patient_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone',
            'role', 'is_verified', 'profile_photo', 'date_joined',
            'doctor_profile', 'patient_profile',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'date_joined']

    def get_doctor_profile(self, obj):
        if obj.is_doctor and hasattr(obj, 'doctor_profile'):
            return DoctorProfileSerializer(obj.doctor_profile).data
        return None

    def get_patient_profile(self, obj):
        if obj.is_patient and hasattr(obj, 'patient_profile'):
            return PatientProfileSerializer(obj.patient_profile).data
        return None


class DoctorProfileSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email     = serializers.CharField(source='user.email', read_only=True)
    user_phone     = serializers.CharField(source='user.phone', read_only=True)
    availability   = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user_id', 'user_full_name', 'user_email', 'user_phone',
            'speciality', 'license_number', 'bio', 'years_experience',
            'consultation_fee', 'rating', 'total_reviews',
            'is_available', 'hospital_name', 'hospital_address',
            'availability',
        ]
        read_only_fields = ['id', 'user_id', 'rating', 'total_reviews']

    def get_availability(self, obj):
        return DoctorAvailabilitySerializer(
            obj.availability.filter(is_active=True), many=True
        ).data


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'slot_duration', 'is_active']


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'date_of_birth', 'blood_group', 'genotype',
            'allergies', 'chronic_conditions', 'current_medications',
            'next_of_kin_name', 'next_of_kin_phone', 'emergency_contact',
            'updated_at',
        ]


class PasswordChangeSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect current password.')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            # Don't reveal whether email exists (security best practice)
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token        = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

