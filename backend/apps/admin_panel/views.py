# ══════════════════════════════════════════════════════════════
# apps/admin_panel/views.py
# ══════════════════════════════════════════════════════════════

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from apps.accounts.permissions import IsAdminRole
from apps.appointments.models import Appointment
from apps.prescriptions.models import Prescription
 
User = get_user_model()
 
 
@api_view(['GET'])
@permission_classes([IsAdminRole])
def admin_stats(request):
    '''
    GET /api/v1/admin/stats/
    System-wide statistics dashboard (FR-07.1).
    '''
    now       = timezone.now()
    today     = now.date()
    last_30d  = now - timedelta(days=30)
 
    stats = {
        'users': {
            'total':       User.objects.count(),
            'patients':    User.objects.filter(role='patient').count(),
            'doctors':     User.objects.filter(role='doctor').count(),
            'pharmacists': User.objects.filter(role='pharmacist').count(),
            'new_last_30d': User.objects.filter(date_joined__gte=last_30d).count(),
        },
        'appointments': {
            'total_today':     Appointment.objects.filter(scheduled_at__date=today).count(),
            'pending':         Appointment.objects.filter(status='pending').count(),
            'confirmed':       Appointment.objects.filter(status='confirmed').count(),
            'completed_30d':   Appointment.objects.filter(
                                   status='completed', updated_at__gte=last_30d
                               ).count(),
            'no_show_rate_30d': _no_show_rate(last_30d),
        },
        'prescriptions': {
            'issued_30d':    Prescription.objects.filter(issued_at__gte=last_30d).count(),
            'dispensed_30d': Prescription.objects.filter(
                                  status='dispensed', dispensed_at__gte=last_30d
                              ).count(),
            'pending':       Prescription.objects.filter(status='issued').count(),
        },
        'system': {
            'status':     'healthy',
            'timestamp':  now.isoformat(),
        },
    }
    return Response(stats)
 
 
def _no_show_rate(since):
    total = Appointment.objects.filter(
        scheduled_at__gte=since, status__in=['completed', 'no_show']
    ).count()
    if total == 0:
        return 0.0
    no_shows = Appointment.objects.filter(scheduled_at__gte=since, status='no_show').count()
    return round((no_shows / total) * 100, 2)
 
 
@api_view(['GET'])
@permission_classes([IsAdminRole])
def admin_user_list(request):
    '''
    GET /api/v1/admin/users/
    List all users with management options (FR-07.2).
    '''
    from apps.accounts.serializers import UserProfileSerializer
    users = User.objects.all().order_by('-date_joined')[:200]
    return Response(UserProfileSerializer(users, many=True).data)
 
 
@api_view(['PATCH'])
@permission_classes([IsAdminRole])
def admin_user_toggle_active(request, pk):
    '''
    PATCH /api/v1/admin/users/{id}/toggle-active/
    Suspend or reactivate a user account (FR-07.2).
    '''
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return Response({'id': user.id, 'is_active': user.is_active})

