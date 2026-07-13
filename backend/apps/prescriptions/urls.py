# ══════════════════════════════════════════════════════════════
# apps/prescriptions/urls.py
# ══════════════════════════════════════════════════════════════

from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.PrescriptionListCreateView.as_view(), name='prescription-list-create'),
    path('<int:pk>/dispense/', views.dispense_prescription, name='prescription-dispense'),
]

