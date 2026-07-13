# ══════════════════════════════════════════════════════════════
# apps/accounts/doctor_urls.py
# ══════════════════════════════════════════════════════════════

from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:pk>/slots/', views.doctor_available_slots, name='doctor-slots'),
    path('<int:pk>/availability/', views.DoctorAvailabilityView.as_view(), name='doctor-availability'),
]

