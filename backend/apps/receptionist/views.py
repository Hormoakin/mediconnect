from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

import secrets
 
User = get_user_model()
 
 
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def receptionist_dashboard_stats(request):
    """
    GET /api/v1/receptionist/stats/
    Dashboard statistics for the receptionist front desk.
    Shows today's appointments, waiting patients, and quick actions.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    from apps.appointments.models import Appointment
    today = timezone.now().date()
 
    stats = {
        'appointments_today':   Appointment.objects.filter(scheduled_at__date=today).count(),
        'pending_today':        Appointment.objects.filter(scheduled_at__date=today, status='pending').count(),
        'confirmed_today':      Appointment.objects.filter(scheduled_at__date=today, status='confirmed').count(),
        'completed_today':      Appointment.objects.filter(scheduled_at__date=today, status='completed').count(),
        'total_patients':       User.objects.filter(role='patient', is_active=True).count(),
        'total_doctors':        User.objects.filter(role='doctor', is_active=True).count(),
        'booked_on_behalf':     Appointment.objects.filter(
            booked_by=request.user,
            created_at__date=today
        ).count() if hasattr(Appointment, 'booked_by') else 0,
    }
    return Response(stats)
 
 
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_patients(request):
    """
    GET /api/v1/receptionist/patients/search/?q=Ada&phone=0803...
    Search for existing patients by name, email, or phone number.
    Used by receptionist to find a patient before booking on their behalf.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    query = request.query_params.get('q', '').strip()
    phone = request.query_params.get('phone', '').strip()
 
    if not query and not phone:
        return Response(
            {'message': 'Provide at least one search parameter: q (name/email) or phone.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    patients = User.objects.filter(role='patient', is_active=True)
 
    if query:
        from django.db.models import Q
        patients = patients.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )
    if phone:
        patients = patients.filter(phone__icontains=phone)
 
    from apps.accounts.serializers import UserProfileSerializer
    return Response({
        'count': patients.count(),
        'results': UserProfileSerializer(patients[:20], many=True).data,
    })
 
 
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_walk_in_patient(request):
    """
    POST /api/v1/receptionist/patients/create/
    Create a new patient account on behalf of a walk-in or phone-in patient.
    The patient may later claim this account via password reset with their email.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    from apps.accounts.serializers import UserRegistrationSerializer
    import secrets
 
    data = request.data.copy()
    data['role'] = 'patient'
 
    # Auto-generate a secure temporary password — patient resets via email
    temp_password = secrets.token_urlsafe(12)
    data['password']         = temp_password
    data['confirm_password'] = temp_password
 
    # Auto-generate username if not provided
    if not data.get('username'):
        base = data.get('full_name', 'patient').lower().replace(' ', '_')
        data['username'] = f"{base}_{User.objects.filter(role='patient').count() + 1}"
 
    serializer = UserRegistrationSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        # Send password reset email so patient can set their own password
        from apps.notifications.tasks import send_password_reset_email
        send_password_reset_email.delay(user.id)
        return Response({
            'message': 'Patient account created. A password setup email has been sent.',
            'patient': {
                'id':        user.id,
                'full_name': user.full_name,
                'email':     user.email,
                'phone':     user.phone,
            },
        }, status=status.HTTP_201_CREATED)
 
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def book_appointment_on_behalf(request):
    """
    POST /api/v1/receptionist/appointments/book/
    Book an appointment on behalf of a patient (walk-in or phone-in).
    Records which receptionist made the booking for audit purposes.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    patient_id = request.data.get('patient_id')
    doctor_id  = request.data.get('doctor_id')
    scheduled_at = request.data.get('scheduled_at')
    reason       = request.data.get('reason', 'Walk-in/phone booking via receptionist')
    notes        = request.data.get('receptionist_notes', '')
 
    if not all([patient_id, doctor_id, scheduled_at]):
        return Response(
            {'message': 'patient_id, doctor_id, and scheduled_at are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    patient = get_object_or_404(User, pk=patient_id, role='patient', is_active=True)
 
    from apps.accounts.models import DoctorProfile
    from apps.appointments.models import Appointment
    from django.utils.dateparse import parse_datetime
 
    doctor = get_object_or_404(DoctorProfile, pk=doctor_id, user__is_active=True)
 
    scheduled_dt = parse_datetime(scheduled_at)
    if not scheduled_dt or scheduled_dt <= timezone.now():
        return Response({'message': 'scheduled_at must be a future datetime.'}, status=400)
 
    try:
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            scheduled_at=scheduled_dt,
            reason=reason,
            duration_mins=request.data.get('duration_mins', 30),
            status='confirmed',  # Receptionist bookings are auto-confirmed
        )
        # Log which receptionist made the booking
        from apps.accounts.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.CREATE,
            resource_type='appointment',
            resource_id=str(appointment.id),
            description=(
                f"Receptionist {request.user.full_name} booked appointment "
                f"for patient {patient.full_name} with Dr. {doctor.user.full_name} "
                f"on behalf. Notes: {notes}"
            ),
        )
        return Response({
            'message': f'Appointment booked for {patient.full_name} with Dr. {doctor.user.full_name}.',
            'appointment_id': appointment.id,
            'scheduled_at': appointment.scheduled_at,
            'status': appointment.status,
        }, status=status.HTTP_201_CREATED)
 
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
 
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def today_schedule(request):
    """
    GET /api/v1/receptionist/schedule/today/
    View all appointments for today across all doctors.
    Receptionist uses this for front-desk coordination.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    from apps.appointments.models import Appointment
    from apps.appointments.serializers import AppointmentSerializer
 
    today = timezone.now().date()
    appointments = Appointment.objects.filter(
        scheduled_at__date=today
    ).select_related(
        'patient', 'doctor__user'
    ).order_by('scheduled_at')
 
    return Response({
        'date': str(today),
        'total': appointments.count(),
        'appointments': AppointmentSerializer(appointments, many=True).data,
    })
 
 
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_doctors(request):
    """
    GET /api/v1/receptionist/doctors/available/?speciality=General&date=2026-08-01
    List available doctors for walk-in or phone booking.
    """
    if request.user.role not in ('receptionist', 'admin'):
        return Response({'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
 
    from apps.accounts.models import DoctorProfile
    from apps.accounts.serializers import DoctorProfileSerializer
 
    speciality = request.query_params.get('speciality', '')
    qs = DoctorProfile.objects.filter(
        user__is_active=True, is_available=True
    ).select_related('user').prefetch_related('availability')
 
    if speciality:
        qs = qs.filter(speciality__icontains=speciality)
 
    return Response({
        'count': qs.count(),
        'doctors': DoctorProfileSerializer(qs, many=True).data,
    })
 
