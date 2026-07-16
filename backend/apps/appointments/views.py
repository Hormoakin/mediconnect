# ══════════════════════════════════════════════════════════════
# apps/appointments/views.py
# ══════════════════════════════════════════════════════════════
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.accounts.permissions import IsDoctor, IsPatient, IsPatientOrDoctor

from apps.accounts.permissions import (
    IsDoctor,
    IsPatient,
    IsPatientOrDoctor,
)

from .models import (
    Appointment,
    DoctorReview,
)

from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
    DoctorReviewSerializer,
)

class AppointmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/appointments/ — List appointments for the current user
    POST /api/v1/appointments/ — Book a new appointment (FR-02.2, FR-02.3)
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_fields   = ['status']
    ordering_fields    = ['scheduled_at', 'created_at']
    ordering           = ['-scheduled_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        qs   = Appointment.objects.select_related(
            'patient', 'doctor__user'
        ).prefetch_related('review')

        if user.role == 'patient':
            return qs.filter(patient=user)
        elif user.role == 'doctor':
            return qs.filter(doctor=user.doctor_profile)
        elif user.role == 'admin':
            return qs.all()
        return qs.none()


class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/appointments/{id}/ — Get appointment details
    PATCH  /api/v1/appointments/{id}/ — Update status/notes (FR-02.7)
    DELETE /api/v1/appointments/{id}/ — Cancel appointment (FR-02.6)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            if self.request.user.role == 'doctor':
                return AppointmentStatusUpdateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Appointment.objects.filter(patient=user)
        elif user.role == 'doctor':
            return Appointment.objects.filter(doctor=user.doctor_profile)
        return Appointment.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Cancel appointment rather than hard-deleting."""
        appointment = self.get_object()
        if not appointment.can_be_cancelled():
            return Response(
                {'message': 'This appointment cannot be cancelled (less than 2 hours away or already completed).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=['status'])

        # Notify other party of cancellation
        from apps.notifications.tasks import send_appointment_cancellation
        send_appointment_cancellation.delay(appointment.id, cancelled_by=request.user.id)

        return Response({'message': 'Appointment cancelled successfully.'}, status=status.HTTP_200_OK)


class DoctorReviewCreateView(generics.CreateAPIView):
    """
    POST /api/v1/appointments/{pk}/review/
    Patient submits a review for a completed appointment.
    """
    serializer_class   = DoctorReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

