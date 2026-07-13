# ══════════════════════════════════════════════════════════════
# mediconnect/settings/production.py
# ══════════════════════════════════════════════════════════════
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'mediconnect.salman-aak.com',
    'api.mediconnect.salman-aak.com',
    'ws.mediconnect.salman-aak.com',
]

# ── Security Headers ──────────────────────────────────────────
SECURE_SSL_REDIRECT             = True
SECURE_HSTS_SECONDS             = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
SECURE_HSTS_PRELOAD             = True
SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE           = True
CSRF_COOKIE_SECURE              = True
SECURE_BROWSER_XSS_FILTER       = True
SECURE_CONTENT_TYPE_NOSNIFF     = True
X_FRAME_OPTIONS                 = 'DENY'

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'https://mediconnect.salman-aak.com',
]

# ── Static files served via S3 ────────────────────────────────
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ── SendGrid real email in production ────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.sendgrid.net'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY', '')

