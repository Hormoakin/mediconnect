# ══════════════════════════════════════════════════════════════
# apps/appointments/urls.py
# ══════════════════════════════════════════════════════════════

from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('<int:pk>/review/', views.DoctorReviewCreateView.as_view(), name='appointment-review'),
]

