# ══════════════════════════════════════════════════════════════
# mediconnect/exceptions.py — Custom Exception Handler
# ══════════════════════════════════════════════════════════════
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON error responses.
    All errors follow the format:
    {
        "error": true,
        "message": "Human-readable error message",
        "code": "error_code",
        "details": { ... }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': True,
            'message': _extract_message(response.data),
            'code': _extract_code(response.data),
            'status_code': response.status_code,
        }
        response.data = error_data

    else:
        # Unhandled exception — log and return 500
        logger.exception(f"Unhandled exception in {context.get('view')}: {exc}")
        response = Response({
            'error': True,
            'message': 'An unexpected error occurred. Please try again.',
            'code': 'internal_server_error',
            'status_code': 500,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response


def _extract_message(data):
    if isinstance(data, dict):
        for key in ('detail', 'message', 'non_field_errors'):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        # Return first field error
        for key, val in data.items():
            return f"{key}: {val[0] if isinstance(val, list) else val}"
    if isinstance(data, list):
        return str(data[0])
    return str(data)


def _extract_code(data):
    if isinstance(data, dict) and 'code' in data:
        return data['code']
    if isinstance(data, dict) and 'detail' in data:
        detail = data['detail']
        if hasattr(detail, 'code'):
            return detail.code
    return 'error'

