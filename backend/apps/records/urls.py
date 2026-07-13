# ══════════════════════════════════════════════════════════════
# apps/records/urls.py
# ══════════════════════════════════════════════════════════════
from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.ClinicalRecordListCreateView.as_view(), name='record-list-create'),
    path('<int:pk>/', views.ClinicalRecordDetailView.as_view(), name='record-detail'),
    path('documents/', views.MedicalDocumentListCreateView.as_view(), name='document-list-create'),
]

