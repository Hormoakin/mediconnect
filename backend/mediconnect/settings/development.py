# ══════════════════════════════════════════════════════════════
# mediconnect/settings/development.py
# ══════════════════════════════════════════════════════════════
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use console email backend in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable throttling in dev
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# Show SQL queries in dev
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

# CORS allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

