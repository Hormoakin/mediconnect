from django.urls import path
from .views import admin_stats                          # existing admin_stats view
from . import enhanced_views as ev                     # new CRUD views

urlpatterns = [
    # Existing
    path('stats/',                          admin_stats,                           name='admin-stats'),
    # New enhanced CRUD
    path('reports/',                        ev.admin_reports,                      name='admin-reports'),
    path('users/',                          ev.AdminUserListCreateView.as_view(),   name='admin-user-list'),
    path('users/<int:pk>/',                 ev.AdminUserDetailView.as_view(),       name='admin-user-detail'),
    path('users/<int:pk>/toggle-active/',   ev.admin_toggle_user_active,           name='admin-user-toggle'),
    path('users/<int:pk>/reset-password/',  ev.admin_reset_password,               name='admin-user-reset-pwd'),
    path('doctors/',                        ev.AdminDoctorListView.as_view(),       name='admin-doctor-list'),
    path('doctors/<int:pk>/',               ev.AdminDoctorDetailView.as_view(),     name='admin-doctor-detail'),
    path('appointments/',                   ev.AdminAppointmentListView.as_view(),  name='admin-appt-list'),
    path('appointments/<int:pk>/',          ev.AdminAppointmentDetailView.as_view(),name='admin-appt-detail'),
]
