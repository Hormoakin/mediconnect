#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════
#  MediConnect — Dr. Ugbari Enhancement Deployment Guide
#  Three enhancements:
#    1. Receptionist / Front Desk Role
#    2. Enhanced Administrator Role (Full CRUD)
#    3. Enhanced AI Symptom Checker with Triage
#
#  Run from repo root: bash scripts/deploy-enhancements.sh
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# PART A: DATABASE MIGRATION (receptionist role + profile)
# File: backend/apps/accounts/migrations/0002_receptionist_role.py
# ─────────────────────────────────────────────────────────────

MIGRATION_CODE = '''
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add receptionist to the role choices
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('patient',      'Patient'),
                    ('doctor',       'Doctor'),
                    ('pharmacist',   'Pharmacist'),
                    ('receptionist', 'Receptionist'),
                    ('admin',        'Administrator'),
                ],
                default='patient',
                max_length=20,
            ),
        ),
        # Create ReceptionistProfile model
        migrations.CreateModel(
            name='ReceptionistProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('department',   models.CharField(blank=True, max_length=100)),
                ('staff_id',     models.CharField(blank=True, max_length=50, unique=True, null=True)),
                ('is_available', models.BooleanField(default=True)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('updated_at',   models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='receptionist_profile',
                    to='accounts.user',
                )),
            ],
            options={'db_table': 'receptionist_profiles'},
        ),
    ]
'''

# ─────────────────────────────────────────────────────────────
# PART B: URL ROUTING UPDATES
# ─────────────────────────────────────────────────────────────

RECEPTIONIST_URLS = '''
# apps/receptionist/urls.py
from django.urls import path
from apps.accounts.receptionist_views import (
    receptionist_dashboard_stats,
    search_patients,
    create_walk_in_patient,
    book_appointment_on_behalf,
    today_schedule,
    available_doctors,
)

urlpatterns = [
    path('stats/',                  receptionist_dashboard_stats,  name='receptionist-stats'),
    path('patients/search/',        search_patients,               name='receptionist-patient-search'),
    path('patients/create/',        create_walk_in_patient,        name='receptionist-patient-create'),
    path('appointments/book/',      book_appointment_on_behalf,    name='receptionist-book'),
    path('schedule/today/',         today_schedule,                name='receptionist-schedule'),
    path('doctors/available/',      available_doctors,             name='receptionist-doctors'),
]
'''

ADMIN_ENHANCED_URLS = '''
# apps/admin_panel/urls.py  (update existing file)
from django.urls import path
from apps.admin_panel import enhanced_views as ev

urlpatterns = [
    path('stats/',                          ev.admin_stats,                      name='admin-stats'),
    path('reports/',                        ev.admin_reports,                    name='admin-reports'),
    path('users/',                          ev.AdminUserListCreateView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/',                 ev.AdminUserDetailView.as_view(),     name='admin-user-detail'),
    path('users/<int:pk>/toggle-active/',   ev.admin_toggle_user_active,         name='admin-user-toggle'),
    path('users/<int:pk>/reset-password/',  ev.admin_reset_password,             name='admin-user-reset-pwd'),
    path('doctors/',                        ev.AdminDoctorListView.as_view(),     name='admin-doctor-list'),
    path('doctors/<int:pk>/',               ev.AdminDoctorDetailView.as_view(),   name='admin-doctor-detail'),
    path('appointments/',                   ev.AdminAppointmentListView.as_view(),name='admin-appt-list'),
    path('appointments/<int:pk>/',          ev.AdminAppointmentDetailView.as_view(),name='admin-appt-detail'),
]
'''

MAIN_URLS_UPDATE = '''
# mediconnect/urls.py — add these two lines to urlpatterns:
path('api/v1/receptionist/', include('apps.receptionist.urls')),
path('api/v1/admin/',        include('apps.admin_panel.urls')),   # already exists — update with new views
# ai/triage/ endpoint is in the FastAPI service, proxied via:
path('api/v1/ai/',           include('apps.ai_service.urls')),    # already exists — add triage/ route
'''

AI_SERVICE_URL_UPDATE = '''
# apps/ai_service/urls.py — add triage endpoint
from django.urls import path
from .views import symptom_check, recommend_doctor, ai_triage  # add ai_triage

urlpatterns = [
    path('symptom-check/', symptom_check,    name='ai-symptom-check'),
    path('recommend/',     recommend_doctor, name='ai-recommend'),
    path('triage/',        ai_triage,        name='ai-triage'),   # NEW
]
'''

FRONTEND_ROUTES_UPDATE = '''
// frontend/src/App.tsx — add new routes to the router

// Import new components
import ReceptionistDashboard    from './pages/receptionist/ReceptionistDashboard'
import AdminDashboardEnhanced   from './pages/admin/AdminDashboardEnhanced'
import SymptomCheckerEnhanced   from './pages/patient/SymptomCheckerEnhanced'

// Add to <Routes> (replace existing admin dashboard and symptom checker):
<Route path="/dashboard" element={
  <ProtectedRoute>
    <DashboardLayout>
      {user?.role === 'patient'      && <PatientDashboard />}
      {user?.role === 'doctor'       && <DoctorDashboard />}
      {user?.role === 'pharmacist'   && <PharmacistDashboard />}
      {user?.role === 'receptionist' && <ReceptionistDashboard />}   // NEW
      {user?.role === 'admin'        && <AdminDashboardEnhanced />}   // UPDATED
    </DashboardLayout>
  </ProtectedRoute>
} />

// Replace existing SymptomChecker route:
<Route path="/symptom-checker" element={
  <ProtectedRoute allowedRoles={['patient']}>
    <DashboardLayout>
      <SymptomCheckerEnhanced />    // UPDATED — now has full triage flow
    </DashboardLayout>
  </ProtectedRoute>
} />
'''

# ─────────────────────────────────────────────────────────────
# PART C: DEPLOYMENT STEPS
# ─────────────────────────────────────────────────────────────

DEPLOYMENT_STEPS = """
═══════════════════════════════════════════════════════════════
  MediConnect — Enhancement Deployment Steps
═══════════════════════════════════════════════════════════════

BACKEND CHANGES:
─────────────────
1. Copy receptionist-role.py content into:
   - apps/accounts/models.py        (ReceptionistProfile model + role choice)
   - apps/accounts/permissions.py   (IsReceptionist, IsReceptionistOrAdmin)
   - apps/accounts/serializers.py   (ReceptionistProfileSerializer)
   - apps/receptionist/views.py     (all receptionist views — create file)

2. Copy admin-enhanced-views.py content into:
   - apps/admin_panel/enhanced_views.py

3. Copy ai-triage-enhanced.py content into:
   - ai_service/triage.py           (TriageSymptomChecker)
   - apps/ai_service/views.py       (add ai_triage view)

4. Write the migration file (copy MIGRATION_CODE above to):
   - apps/accounts/migrations/0002_receptionist_role.py

5. Update URL files (see PART B above):
   - apps/receptionist/urls.py      (create new file)
   - apps/admin_panel/urls.py       (update with new endpoints)
   - apps/ai_service/urls.py        (add triage/ route)
   - mediconnect/urls.py            (add receptionist URL include)

6. Create receptionist app if it doesn't exist:
   python manage.py startapp receptionist
   mv receptionist apps/receptionist

7. Add 'apps.receptionist' to INSTALLED_APPS in settings/base.py

8. Run migrations:
   python manage.py migrate

FRONTEND CHANGES:
──────────────────
9. Copy frontend files to:
   - frontend/src/pages/receptionist/ReceptionistDashboard.tsx
   - frontend/src/pages/admin/AdminDashboardEnhanced.tsx
   - frontend/src/pages/patient/SymptomCheckerEnhanced.tsx

10. Update App.tsx router (see FRONTEND_ROUTES_UPDATE above)

AI SERVICE CHANGES:
────────────────────
11. Copy ai-triage-enhanced.py to:
    - ai_service/triage.py

12. Update ai_service/main.py to:
    - Import TriageSymptomChecker from triage
    - Instantiate triage_checker in lifespan
    - Add /api/v1/ai/triage POST endpoint

KUBERNETES DEPLOYMENT:
───────────────────────
13. Rebuild and push all changed Docker images:

    docker buildx build --platform linux/amd64 \\
      -t hormoakin001/mediconnect-backend:latest --push ./backend

    docker buildx build --platform linux/amd64 \\
      -t hormoakin001/mediconnect-ai:latest --push ./ai_service

    docker buildx build --platform linux/amd64 \\
      -t hormoakin001/mediconnect-frontend:latest --push ./frontend

14. Restart deployments:
    kubectl rollout restart deployment/backend   -n mediconnect
    kubectl rollout restart deployment/ai-service -n mediconnect
    kubectl rollout restart deployment/frontend   -n mediconnect

15. Run migrations inside backend pod:
    BACKEND_POD=$(kubectl get pods -n mediconnect -l app=backend \\
      --no-headers | grep Running | awk '{print $1}' | head -1)
    kubectl exec -n mediconnect $BACKEND_POD -- \\
      python manage.py migrate --noinput

16. Create a test receptionist account:
    kubectl exec -it -n mediconnect $BACKEND_POD -- python manage.py shell
    >>> from django.contrib.auth import get_user_model
    >>> from apps.accounts.models import ReceptionistProfile
    >>> User = get_user_model()
    >>> u = User(email='receptionist@mediconnect.salman-aak.com',
    ...          username='front_desk', full_name='Front Desk Officer',
    ...          phone='+2348055555555', role='receptionist', is_active=True)
    >>> u.set_password('Reception123!')
    >>> u.save()
    >>> ReceptionistProfile.objects.create(user=u, department='General Outpatient')
    >>> exit()

VERIFICATION CHECKLIST:
────────────────────────
□ Receptionist can log in at mediconnect.salman-aak.com
□ Receptionist dashboard shows stats, book tab, patient tab, schedule tab
□ Receptionist can search existing patients
□ Receptionist can create walk-in patient account
□ Receptionist can book appointment on behalf of patient
□ Patient cannot access receptionist endpoints (403)
□ Admin dashboard shows full user management table
□ Admin can create users of any role (including receptionist/pharmacist)
□ Admin can suspend/activate/reset-password/delete users
□ Admin reports endpoint returns summary/appointments/users/prescriptions
□ AI triage returns recommended_department + available_doctors
□ AI triage booking flow books appointment correctly
□ AI triage shows emergency banner for emergency-level urgency

═══════════════════════════════════════════════════════════════
"""

if __name__ == '__main__':
    print(DEPLOYMENT_STEPS)
    print("Migration code:")
    print(MIGRATION_CODE)
    print("\nReceptionist URLs:")
    print(RECEPTIONIST_URLS)
    print("\nAdmin Enhanced URLs:")
    print(ADMIN_ENHANCED_URLS)
    print("\nMain URLs update:")
    print(MAIN_URLS_UPDATE)
    print("\nFrontend routes update:")
    print(FRONTEND_ROUTES_UPDATE)
