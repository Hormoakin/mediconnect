# ══════════════════════════════════════════════════════════════
# ENHANCEMENT 2: ENHANCED ADMINISTRATOR ROLE
# Full CRUD management for users, doctors, patients, appointments
# ══════════════════════════════════════════════════════════════

# apps/admin_panel/enhanced_views.py

from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def admin_only(request):
    return request.user.is_authenticated and request.user.role == 'admin'


# ── USER MANAGEMENT (Full CRUD) ───────────────────────────────

class AdminUserListCreateView(APIView):
    """
    GET  /api/v1/admin/users/         — List all users with filters
    POST /api/v1/admin/users/         — Create any role user (including receptionist/pharmacist/admin)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not admin_only(request):
            return Response({'message': 'Access restricted to administrators.'}, status=403)

        role   = request.query_params.get('role', '')
        search = request.query_params.get('search', '')
        active = request.query_params.get('is_active', '')

        qs = User.objects.all().order_by('-date_joined')
        if role:    qs = qs.filter(role=role)
        if search:  qs = qs.filter(Q(full_name__icontains=search) | Q(email__icontains=search))
        if active:  qs = qs.filter(is_active=active.lower() == 'true')

        from apps.accounts.serializers import UserProfileSerializer
        return Response({
            'total': qs.count(),
            'results': UserProfileSerializer(qs[:200], many=True).data,
        })

    def post(self, request):
        if not admin_only(request):
            return Response({'message': 'Access restricted to administrators.'}, status=403)

        data = request.data.copy()
        if not data.get('password'):
            import secrets
            pwd = secrets.token_urlsafe(12)
            data['password']         = pwd
            data['confirm_password'] = pwd

        from apps.accounts.serializers import UserRegistrationSerializer
        # Admin can create ANY role — temporarily allow all roles
        serializer = UserRegistrationSerializer(data=data)

        # Override the role restriction for admin
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Admin {request.user.email} created user {user.email} (role: {user.role})")
            return Response({
                'message': f'User {user.full_name} ({user.role}) created successfully.',
                'user_id': user.id,
                'email': user.email,
                'role': user.role,
                'temp_password_set': not request.data.get('password'),
            }, status=201)

        # If validation fails due to role restriction, bypass for admin
        if 'role' in str(serializer.errors):
            role = data.get('role', '')
            allowed = ['patient', 'doctor', 'pharmacist', 'receptionist', 'admin']
            if role not in allowed:
                return Response({'message': f'Invalid role. Choose from: {allowed}'}, status=400)
            # Create user directly for admin/pharmacist/receptionist
            from apps.accounts.models import DoctorProfile, PatientProfile, ReceptionistProfile
            import secrets
            temp_pwd = data.get('password') or secrets.token_urlsafe(12)
            user = User(
                email=data['email'],
                username=data.get('username', data['email'].split('@')[0]),
                full_name=data['full_name'],
                phone=data.get('phone', ''),
                role=role,
                is_active=True,
            )
            user.set_password(temp_pwd)
            user.save()
            if role == 'patient':
                PatientProfile.objects.create(user=user)
            elif role == 'doctor':
                DoctorProfile.objects.create(user=user, speciality=data.get('speciality','General Practice'), license_number=f'TEMP-{user.id}')
            elif role == 'receptionist':
                ReceptionistProfile.objects.create(user=user)
            return Response({
                'message': f'User {user.full_name} ({role}) created.',
                'user_id': user.id,
            }, status=201)

        return Response(serializer.errors, status=400)


class AdminUserDetailView(APIView):
    """
    GET    /api/v1/admin/users/{id}/               — Get user details
    PATCH  /api/v1/admin/users/{id}/               — Update user (name, role, active status)
    DELETE /api/v1/admin/users/{id}/               — Permanently delete user
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_user(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.serializers import UserProfileSerializer
        user = self._get_user(pk)
        return Response(UserProfileSerializer(user).data)

    def patch(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        user = self._get_user(pk)
        # Prevent admin from modifying their own role
        if user == request.user and 'role' in request.data:
            return Response({'message': 'Administrators cannot change their own role.'}, status=400)

        allowed_fields = ['full_name', 'phone', 'role', 'is_active', 'is_verified']
        updated = []
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
                updated.append(field)
        if 'password' in request.data:
            user.set_password(request.data['password'])
            updated.append('password')
        user.save()

        logger.info(f"Admin {request.user.email} updated user {user.email}: {updated}")
        return Response({
            'message': f'User {user.full_name} updated.',
            'updated_fields': updated,
        })

    def delete(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        user = self._get_user(pk)
        if user == request.user:
            return Response({'message': 'Administrators cannot delete their own account.'}, status=400)
        name = user.full_name
        user.delete()
        logger.info(f"Admin {request.user.email} deleted user {name} (id:{pk})")
        return Response({'message': f'User {name} permanently deleted.'})


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def admin_toggle_user_active(request, pk):
    """
    PATCH /api/v1/admin/users/{id}/toggle-active/
    Suspend or reactivate a user account without permanent deletion.
    """
    if not admin_only(request):
        return Response({'message': 'Admin only.'}, status=403)
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    action = 'activated' if user.is_active else 'suspended'
    return Response({'message': f'User {user.full_name} {action}.', 'is_active': user.is_active})


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def admin_reset_password(request, pk):
    """
    PATCH /api/v1/admin/users/{id}/reset-password/
    Generate a new temporary password and trigger password reset email.
    """
    if not admin_only(request):
        return Response({'message': 'Admin only.'}, status=403)
    user = get_object_or_404(User, pk=pk)
    from apps.notifications.tasks import send_password_reset_email
    send_password_reset_email.delay(user.id)
    return Response({'message': f'Password reset email sent to {user.email}.'})


# ── DOCTOR MANAGEMENT ─────────────────────────────────────────

class AdminDoctorListView(APIView):
    """
    GET  /api/v1/admin/doctors/       — List all doctors with full profile
    POST /api/v1/admin/doctors/       — Create doctor profile for existing user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.models import DoctorProfile
        from apps.accounts.serializers import DoctorProfileSerializer
        qs = DoctorProfile.objects.select_related('user').prefetch_related('availability')
        speciality = request.query_params.get('speciality', '')
        available  = request.query_params.get('available', '')
        if speciality: qs = qs.filter(speciality__icontains=speciality)
        if available:  qs = qs.filter(is_available=available.lower() == 'true')
        return Response({'count': qs.count(), 'results': DoctorProfileSerializer(qs, many=True).data})

    def post(self, request):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.models import DoctorProfile
        from apps.accounts.serializers import DoctorProfileSerializer
        user = get_object_or_404(User, pk=request.data.get('user_id'), role='doctor')
        if hasattr(user, 'doctor_profile'):
            return Response({'message': 'Doctor profile already exists for this user.'}, status=400)
        serializer = DoctorProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AdminDoctorDetailView(APIView):
    """
    GET    /api/v1/admin/doctors/{id}/    — Get doctor profile
    PATCH  /api/v1/admin/doctors/{id}/    — Update doctor profile
    DELETE /api/v1/admin/doctors/{id}/    — Remove doctor profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.models import DoctorProfile
        from apps.accounts.serializers import DoctorProfileSerializer
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        return Response(DoctorProfileSerializer(doctor).data)

    def patch(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.models import DoctorProfile
        from apps.accounts.serializers import DoctorProfileSerializer
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        serializer = DoctorProfileSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.accounts.models import DoctorProfile
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        name = doctor.user.full_name
        doctor.delete()
        return Response({'message': f'Doctor profile for Dr. {name} removed.'})


# ── APPOINTMENT MANAGEMENT ────────────────────────────────────

class AdminAppointmentListView(APIView):
    """
    GET  /api/v1/admin/appointments/    — List ALL appointments with filters
    POST /api/v1/admin/appointments/    — Create appointment (admin override)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.appointments.models import Appointment
        from apps.appointments.serializers import AppointmentSerializer

        qs = Appointment.objects.select_related('patient', 'doctor__user').order_by('-scheduled_at')
        status_filter = request.query_params.get('status', '')
        date_filter   = request.query_params.get('date', '')
        doctor_filter = request.query_params.get('doctor_id', '')
        patient_filter= request.query_params.get('patient_id', '')

        if status_filter:  qs = qs.filter(status=status_filter)
        if date_filter:    qs = qs.filter(scheduled_at__date=date_filter)
        if doctor_filter:  qs = qs.filter(doctor_id=doctor_filter)
        if patient_filter: qs = qs.filter(patient_id=patient_filter)

        return Response({'count': qs.count(), 'results': AppointmentSerializer(qs[:500], many=True).data})

    def post(self, request):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.appointments.serializers import AppointmentCreateSerializer
        serializer = AppointmentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            appt = serializer.save()
            return Response({'message': 'Appointment created.', 'appointment_id': appt.id}, status=201)
        return Response(serializer.errors, status=400)


class AdminAppointmentDetailView(APIView):
    """
    GET    /api/v1/admin/appointments/{id}/    — Get appointment details
    PATCH  /api/v1/admin/appointments/{id}/    — Update status/reschedule
    DELETE /api/v1/admin/appointments/{id}/    — Cancel and delete
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.appointments.models import Appointment
        from apps.appointments.serializers import AppointmentSerializer
        appt = get_object_or_404(Appointment, pk=pk)
        return Response(AppointmentSerializer(appt).data)

    def patch(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.appointments.models import Appointment
        appt = get_object_or_404(Appointment, pk=pk)
        allowed = ['status', 'scheduled_at', 'duration_mins', 'doctor_notes', 'reason']
        for field in allowed:
            if field in request.data:
                setattr(appt, field, request.data[field])
        appt.save()
        return Response({'message': f'Appointment #{pk} updated.'})

    def delete(self, request, pk):
        if not admin_only(request): return Response({'message': 'Admin only.'}, status=403)
        from apps.appointments.models import Appointment
        appt = get_object_or_404(Appointment, pk=pk)
        appt.status = 'cancelled'
        appt.save(update_fields=['status'])
        return Response({'message': f'Appointment #{pk} cancelled.'})


# ── REPORTS ───────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_reports(request):
    """
    GET /api/v1/admin/reports/?type=appointments&from=2026-01-01&to=2026-12-31
    Generate exportable reports on system activity.
    """
    if not admin_only(request):
        return Response({'message': 'Admin only.'}, status=403)

    report_type = request.query_params.get('type', 'summary')
    date_from   = request.query_params.get('from', (timezone.now() - timedelta(days=30)).date().isoformat())
    date_to     = request.query_params.get('to', timezone.now().date().isoformat())

    from apps.appointments.models import Appointment
    from apps.prescriptions.models import Prescription

    base_appts = Appointment.objects.filter(scheduled_at__date__gte=date_from, scheduled_at__date__lte=date_to)
    base_rxs   = Prescription.objects.filter(issued_at__date__gte=date_from, issued_at__date__lte=date_to)

    if report_type == 'appointments':
        data = {
            'period': {'from': date_from, 'to': date_to},
            'total':       base_appts.count(),
            'completed':   base_appts.filter(status='completed').count(),
            'cancelled':   base_appts.filter(status='cancelled').count(),
            'no_show':     base_appts.filter(status='no_show').count(),
            'pending':     base_appts.filter(status='pending').count(),
            'no_show_rate_pct': round(
                base_appts.filter(status='no_show').count() /
                max(base_appts.filter(status__in=['completed','no_show']).count(), 1) * 100, 2
            ),
            'by_doctor': list(
                base_appts.values('doctor__user__full_name', 'doctor__speciality')
                .annotate(count=Count('id'), completed=Count('id', filter=Q(status='completed')))
                .order_by('-count')[:10]
            ),
        }
    elif report_type == 'users':
        data = {
            'period': {'from': date_from, 'to': date_to},
            'new_patients':      User.objects.filter(role='patient', date_joined__date__gte=date_from).count(),
            'new_doctors':       User.objects.filter(role='doctor', date_joined__date__gte=date_from).count(),
            'total_patients':    User.objects.filter(role='patient').count(),
            'total_doctors':     User.objects.filter(role='doctor').count(),
            'total_pharmacists': User.objects.filter(role='pharmacist').count(),
            'total_receptionists': User.objects.filter(role='receptionist').count(),
            'suspended_users':   User.objects.filter(is_active=False).count(),
        }
    elif report_type == 'prescriptions':
        data = {
            'period': {'from': date_from, 'to': date_to},
            'issued':    base_rxs.count(),
            'dispensed': base_rxs.filter(status='dispensed').count(),
            'expired':   base_rxs.filter(status='expired').count(),
            'pending':   base_rxs.filter(status='issued').count(),
            'by_medication': list(
                base_rxs.values('medication')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
        }
    else:
        # Summary report
        data = {
            'period': {'from': date_from, 'to': date_to},
            'appointments': {
                'total': base_appts.count(),
                'completed': base_appts.filter(status='completed').count(),
                'no_show_rate_pct': round(
                    base_appts.filter(status='no_show').count() /
                    max(base_appts.filter(status__in=['completed','no_show']).count(), 1) * 100, 2
                ),
            },
            'users': {
                'total':    User.objects.count(),
                'active':   User.objects.filter(is_active=True).count(),
                'new_this_period': User.objects.filter(date_joined__date__gte=date_from).count(),
            },
            'prescriptions': {
                'issued':    base_rxs.count(),
                'dispensed': base_rxs.filter(status='dispensed').count(),
            },
        }

    return Response(data)
