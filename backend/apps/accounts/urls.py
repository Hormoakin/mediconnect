"""
apps/accounts/urls.py — Authentication routes
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# ── /api/v1/auth/ ─────────────────────────────────────────────
urlpatterns = [
    path('login/',          views.LoginView.as_view(),           name='auth-login'),
    path('register/',       views.RegisterView.as_view(),        name='auth-register'),
    path('logout/',         views.logout_view,                   name='auth-logout'),
    path('token/refresh/',  TokenRefreshView.as_view(),          name='auth-token-refresh'),
    path('password-reset/', views.password_reset_request,        name='auth-password-reset'),
]

