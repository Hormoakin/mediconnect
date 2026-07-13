# ══════════════════════════════════════════════════════════════
# apps/admin_panel/urls.py
# ══════════════════════════════════════════════════════════════
from django.urls import path
from . import views
 
urlpatterns = [
    path('stats/', views.admin_stats, name='admin-stats'),
    path('users/', views.admin_user_list, name='admin-user-list'),
    path('users/<int:pk>/toggle-active/', views.admin_user_toggle_active, name='admin-user-toggle'),
]

