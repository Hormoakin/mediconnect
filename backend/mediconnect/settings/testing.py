# ══════════════════════════════════════════════════════════════
# backend/mediconnect/settings/testing.py
# ══════════════════════════════════════════════════════════════
from .base import *

DEBUG = True

# Use an in-memory SQLite DB for tests (no Postgres needed in CI)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable Celery — use synchronous execution in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use dummy cache (no Redis needed in CI)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable throttling in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# Use console email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Dummy secrets (never used in real calls during tests — mocked)
TWILIO_ACCOUNT_SID  = 'ACtest'
TWILIO_AUTH_TOKEN   = 'test_token'
TWILIO_PHONE_NUMBER = '+13464894281'   # Twilio test magic number
SENDGRID_API_KEY    = 'SG.test'
OPENAI_API_KEY      = 'sk-test'
SECRET_KEY          = 'test-secret-key-for-testing-only'
MONGODB_URI         = 'mongodb://localhost:27017/mediconnect_test'

CORS_ALLOW_ALL_ORIGINS = True
