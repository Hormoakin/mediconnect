# ══════════════════════════════════════════════════════════════
# apps/notifications/message_views.py
# ══════════════════════════════════════════════════════════════
from rest_framework import generics, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Message
from .message_serializers import MessageSerializer
 
User = get_user_model()
 
 
class ConversationHistoryView(generics.ListAPIView):
    '''
    GET /api/v1/messages/{user_id}/
    Returns the full conversation history between the current user
    and the specified user_id (FR-05.4). Also marks messages as read.
    Real-time delivery happens via Socket.io; this REST endpoint
    provides the initial history load and search/audit access.
    '''
    serializer_class   = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        me    = self.request.user
        other = get_object_or_404(User, pk=self.kwargs['user_id'])
 
        qs = Message.objects.filter(
            Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
        ).select_related('sender', 'recipient').order_by('sent_at')
 
        # Mark incoming messages as read
        Message.objects.filter(
            sender=other, recipient=me, is_read=False
        ).update(is_read=True, read_at=timezone.now())
 
        return qs
 
 
class ConversationListView(generics.ListAPIView):
    '''
    GET /api/v1/messages/
    Lists distinct conversation threads for the current user,
    most recent message first — used to populate the chat sidebar.
    '''
    serializer_class   = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        me = self.request.user
        return Message.objects.filter(
            Q(sender=me) | Q(recipient=me)
        ).select_related('sender', 'recipient').order_by('-sent_at')

