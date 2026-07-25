from django.urls import path

from .views import (
    symptom_check,
    recommend_doctor,
)

urlpatterns = [
    path(
        "symptom-check/",
        symptom_check,
        name="symptom-check",
    ),
    path(
        "recommend-doctor/",
        recommend_doctor,
        name="recommend-doctor",
    ),
]
