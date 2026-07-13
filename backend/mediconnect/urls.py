# ══════════════════════════════════════════════════════════════
# mediconnect/urls.py  — Root URL Configuration
# ══════════════════════════════════════════════════════════════
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'MediConnect API', 'version': '1.0.0'})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check (no auth required — used by K8s probes + CI/CD)
    path('api/v1/health/', health_check, name='health-check'),

    # API v1 routes
    path('api/v1/auth/',          include('apps.accounts.urls')),
    path('api/v1/users/',         include('apps.accounts.user_urls')),
    path('api/v1/doctors/',       include('apps.accounts.doctor_urls')),
    path('api/v1/appointments/',  include('apps.appointments.urls')),
    path('api/v1/records/',       include('apps.records.urls')),
    path('api/v1/prescriptions/', include('apps.prescriptions.urls')),
    path('api/v1/messages/',      include('apps.notifications.message_urls')),
    path('api/v1/ai/',            include('apps.ai_service.urls')),
    path('api/v1/admin/',         include('apps.admin_panel.urls')),

    # Prometheus metrics (scraped by Prometheus every 15s)
    path('', include('django_prometheus.urls')),
]

