# ══════════════════════════════════════════════════════════════
# apps/accounts/middleware.py — Audit Log Middleware
# ══════════════════════════════════════════════════════════════
import logging
from .models import AuditLog

logger = logging.getLogger(__name__)

# Endpoints that require audit logging (write operations on sensitive data)
AUDIT_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
AUDIT_PATHS   = ['/api/v1/records/', '/api/v1/prescriptions/', '/api/v1/appointments/']


class AuditLogMiddleware:
    """
    Middleware that logs all write operations on sensitive resources.
    Implements FR-03.5: immutable audit log of all record modifications.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log write operations on sensitive endpoints
        if (request.method in AUDIT_METHODS and
                any(request.path.startswith(p) for p in AUDIT_PATHS) and
                hasattr(request, 'user') and
                request.user.is_authenticated):
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action=request.method.lower().replace(
                        'delete', 'delete'
                    ).replace('post', 'create').replace(
                        'put', 'update'
                    ).replace('patch', 'update'),
                    resource_type=request.path.split('/')[3],
                    resource_id=request.path.split('/')[-2] if request.path.split('/')[-2].isdigit() else '',
                    description=f"{request.method} {request.path} → {response.status_code}",
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
            except Exception as e:
                logger.error(f"Audit log creation failed: {e}")

        return response


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
