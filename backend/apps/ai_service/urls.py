from django.urls import path
from .views import (
    symptom_check,
    recommend_doctor,
    ai_triage,
)

urlpatterns = [
    path('symptom-check/',   symptom_check,   name='symptom-check'),
    path('recommend-doctor/', recommend_doctor, name='recommend-doctor'),
    path('triage/',          ai_triage,        name='ai-triage'),
]
