"""
apps/accounts/views.py
Authentication and user profile API views.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DoctorProfile, PatientProfile, DoctorAvailability
from .serializers import (
    MediConnectTokenObtainSerializer, UserRegistrationSerializer,
    UserProfileSerializer, DoctorProfileSerializer,
    DoctorAvailabilitySerializer, PatientProfileSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer,
)
from .permissions import IsDoctor, IsAdminRole, IsPatient
from apps.notifications.services import EmailService

import logging
logger = logging.getLogger(__name__)
User = get_user_model()


class AuthRateThrottle(AnonRateThrottle):
    rate = '10/minute'  # Stricter throttle for auth endpoints (brute-force protection)


# ── Authentication Endpoints ──────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Authenticates user, returns JWT access + refresh tokens.
    Custom serializer embeds role, full_name, user_id in token.
    """
    serializer_class = MediConnectTokenObtainSerializer
    throttle_classes = [AuthRateThrottle]


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Creates a new patient or doctor account (FR-01.1).
    Sends welcome email via SendGrid on success.
    """
    permission_classes  = [permissions.AllowAny]
    serializer_class    = UserRegistrationSerializer
    throttle_classes    = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens immediately after registration
        refresh = RefreshToken.for_user(user)

        # Send welcome email asynchronously via Celery
        from apps.notifications.tasks import send_welcome_email
        send_welcome_email.delay(user.id)

        return Response({
            'message': 'Account created successfully.',
            'user': {
                'id':        user.id,
                'email':     user.email,
                'full_name': user.full_name,
                'role':      user.role,
            },
            'tokens': {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def logout_view(request):
    """
    POST /api/v1/auth/logout/
    Blacklists the provided refresh token (FR-01.2).
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'message': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'message': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    POST /api/v1/auth/password-reset/
    Sends password reset email via SendGrid (FR-01.5).
    Always returns 200 to avoid email enumeration.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    user_qs = User.objects.filter(email=email, is_active=True)
    if user_qs.exists():
        from apps.notifications.tasks import send_password_reset_email
        send_password_reset_email.delay(user_qs.first().id)

    return Response({
        'message': 'If an account exists with that email, a password reset link has been sent.'
    }, status=status.HTTP_200_OK)


# ── User Profile Endpoints ─────────────────────────────────────

class UserMeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/users/me/ — Get own profile (FR-01.4)
    PUT  /api/v1/users/me/ — Update own profile (FR-01.4)
    """
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
def change_password(request):
    """
    POST /api/v1/users/me/change-password/
    """
    serializer = PasswordChangeSerializer(
        data=request.data, context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({'message': 'Password updated successfully.'})


# ── Doctor Endpoints ───────────────────────────────────────────

class DoctorListView(generics.ListAPIView):
    """
    GET /api/v1/doctors/
    List all active doctors with filter, search and ordering (FR-02.1).
    Accessible to all authenticated users.
    """
    serializer_class   = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['speciality', 'is_available']
    search_fields      = ['user__full_name', 'speciality', 'hospital_name']
    ordering_fields    = ['rating', 'years_experience', 'consultation_fee']
    ordering           = ['-rating']

    def get_queryset(self):
        return DoctorProfile.objects.filter(
            user__is_active=True
        ).select_related('user').prefetch_related('availability')


class DoctorDetailView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/doctors/{id}/  — Get doctor profile
    PUT  /api/v1/doctors/{id}/  — Update own doctor profile (doctor only)
    """
    serializer_class   = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = DoctorProfile.objects.select_related('user')

    def update(self, request, *args, **kwargs):
        # Only the doctor themselves can update their profile
        instance = self.get_object()
        if instance.user != request.user and request.user.role != 'admin':
            return Response(
                {'message': 'You can only update your own profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


@api_view(['GET'])
def doctor_available_slots(request, pk):
    """
    GET /api/v1/doctors/{id}/slots/?date=2026-07-15
    Returns available booking slots for a doctor on a specific date (FR-02.2).
    """
    from datetime import datetime, timedelta
    from apps.appointments.models import Appointment

    doctor = get_object_or_404(DoctorProfile, pk=pk, user__is_active=True)
    date_str = request.query_params.get('date')

    if not date_str:
        return Response(
            {'message': 'Date parameter is required. Format: ?date=YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    day_of_week = target_date.weekday()
    availability = doctor.availability.filter(day_of_week=day_of_week, is_active=True)

    if not availability.exists():
        return Response({'available_slots': [], 'message': 'Doctor is not available on this day.'})

    # Build all possible slots from availability
    all_slots = []
    for avail in availability:
        current = datetime.combine(target_date, avail.start_time)
        end     = datetime.combine(target_date, avail.end_time)
        while current + timedelta(minutes=avail.slot_duration) <= end:
            all_slots.append(current)
            current += timedelta(minutes=avail.slot_duration)

    # Exclude already-booked slots
    booked = Appointment.objects.filter(
        doctor=doctor,
        scheduled_at__date=target_date,
        status__in=['pending', 'confirmed']
    ).values_list('scheduled_at', flat=True)

    booked_times = {b.replace(tzinfo=None) for b in booked}
    available = [s for s in all_slots if s not in booked_times]

    return Response({
        'doctor_id': pk,
        'date': date_str,
        'available_slots': [s.strftime('%H:%M') for s in available],
        'slot_duration_minutes': availability.first().slot_duration,
    })


class DoctorAvailabilityView(generics.ListCreateAPIView):
    """
    GET  /api/v1/doctors/{pk}/availability/ — View availability schedule
    POST /api/v1/doctors/{pk}/availability/ — Set availability (doctor only)
    """
    serializer_class   = DoctorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(
            doctor__pk=self.kwargs['pk'], is_active=True
        )

    def perform_create(self, serializer):
        if self.request.user.role != 'doctor':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only doctors can set availability.')
        doctor = self.request.user.doctor_profile
        serializer.save(doctor=doctor)

