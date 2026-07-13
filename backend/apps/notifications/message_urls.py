# ══════════════════════════════════════════════════════════════
# apps/notifications/message_urls.py
# ══════════════════════════════════════════════════════════════

from django.urls import path
from . import message_views as views
 
urlpatterns = [
    path('', views.ConversationListView.as_view(), name='conversation-list'),
    path('<int:user_id>/', views.ConversationHistoryView.as_view(), name='conversation-history'),
]

