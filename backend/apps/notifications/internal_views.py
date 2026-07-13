# ══════════════════════════════════════════════════════════════
# apps/notifications/internal_views.py
#
# Internal-only endpoint called by the WebSocket service
# (NOT exposed to the public API surface in the same way as
# user-facing endpoints — protected by a shared service token
# rather than a user JWT, since the caller is another backend
# service, not an authenticated end user).
# Implements FR-05.5: SMS notification when a new message is
# received and the recipient is not currently online.
# ══════════════════════════════════════════════════════════════
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(['POST'])
@authentication_classes([])   # No JWT — uses internal service token instead
@permission_classes([AllowAny])
def notify_offline_message(request):
    """
    POST /api/v1/internal/notify-offline-message/
    Header: X-Internal-Service-Token: <shared secret>
    Body:   {recipient_id, sender_name, preview}
    """
    token = request.headers.get('X-Internal-Service-Token', '')
    expected = getattr(settings, 'INTERNAL_SERVICE_TOKEN', '')

    if not expected or token != expected:
        return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    recipient_id = request.data.get('recipient_id')
    sender_name  = request.data.get('sender_name', 'A user')
    preview      = request.data.get('preview', '')

    try:
        recipient = User.objects.get(pk=recipient_id, is_active=True)
    except User.DoesNotExist:
        return Response({'message': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

    if recipient.phone:
        from .services import SMSService
        from .models import Notification
        sms = SMSService()
        sms.send(
            to_phone=recipient.phone,
            message=f"MediConnect: New message from {sender_name}: \"{preview[:60]}\". Open the app to reply.",
            user=recipient,
            notif_type=Notification.NotifType.NEW_MESSAGE,
        )

    return Response({'status': 'notified'})


# ── Add to apps/notifications/message_urls.py: ──────────────────
# from .internal_views import notify_offline_message
# urlpatterns += [
#     path('../internal/notify-offline-message/', notify_offline_message),
# ]
#
# ── Better: add directly to mediconnect/urls.py: ────────────────
# path('api/v1/internal/notify-offline-message/',
#      include('apps.notifications.internal_urls')),
#
# ── And add to settings/base.py: ─────────────────────────────────
# INTERNAL_SERVICE_TOKEN = env('INTERNAL_SERVICE_TOKEN', default='')
# (seal this as a Kubernetes secret alongside the other API secrets,
#  shared between the backend Deployment and the websocket Deployment
#  as the env var INTERNAL_SERVICE_TOKEN)
