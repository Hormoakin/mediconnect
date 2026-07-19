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

