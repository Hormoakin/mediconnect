# ══════════════════════════════════════════════════════════════
# apps/accounts/user_urls.py
# ══════════════════════════════════════════════════════════════
from django.urls import path
from . import views
 
urlpatterns = [
    path('me/', views.UserMeView.as_view(), name='user-me'),
    path('me/change-password/', views.change_password, name='user-change-password'),
]
