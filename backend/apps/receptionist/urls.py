from django.urls import path
from . import views

urlpatterns = [
    path('stats/',              views.receptionist_dashboard_stats, name='receptionist-stats'),
    path('patients/search/',    views.search_patients,              name='receptionist-patient-search'),
    path('patients/create/',    views.create_walk_in_patient,       name='receptionist-patient-create'),
    path('appointments/book/',  views.book_appointment_on_behalf,   name='receptionist-book'),
    path('schedule/today/',     views.today_schedule,               name='receptionist-schedule'),
    path('doctors/available/',  views.available_doctors,            name='receptionist-doctors'),
]
