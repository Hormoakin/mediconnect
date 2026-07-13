"""
MediConnect — Base Django Settings
Shared across development, production, and testing environments.
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

# ── Base Directory ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environment Variables ─────────────────────────────────────
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ── Application Definition ────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'django_prometheus',
    'storages',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.appointments',
    'apps.records',
    'apps.prescriptions',
    'apps.notifications',
    'apps.admin_panel',
    'apps.ai_service',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.AuditLogMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'mediconnect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mediconnect.wsgi.application'

# ── Database ──────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     env('DATABASE_NAME', default='mediconnect'),
        'USER':     env('DATABASE_USER', default='mediconnect_user'),
        'PASSWORD': env('DATABASE_PASSWORD', default='mediconnect_dev_password'),
        'HOST':     env('DATABASE_HOST', default='localhost'),
        'PORT':     env('DATABASE_PORT', default='5432'),
        'OPTIONS':  {'connect_timeout': 10},
    }
}

# ── Custom User Model ─────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# ── Password Validation ───────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# ── Static & Media Files ──────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Django REST Framework ─────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '100/minute',
        'auth': '10/minute',
    },
    'EXCEPTION_HANDLER': 'mediconnect.exceptions.custom_exception_handler',
}

# ── JWT Settings ──────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_OBTAIN_SERIALIZER': 'apps.accounts.serializers.MediConnectTokenObtainSerializer',
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
])
CORS_ALLOW_CREDENTIALS = True

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL           = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND       = 'django-db'
CELERY_CACHE_BACKEND        = 'django-cache'
CELERY_ACCEPT_CONTENT       = ['json']
CELERY_TASK_SERIALIZER      = 'json'
CELERY_RESULT_SERIALIZER    = 'json'
CELERY_TIMEZONE             = 'Africa/Lagos'
CELERY_BEAT_SCHEDULER       = 'django_celery_beat.schedulers:DatabaseScheduler'

# ── Redis Cache ───────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

# ── MongoDB (for clinical notes and AI logs) ──────────────────
MONGODB_URI = env('MONGODB_URI', default='mongodb://mediconnect_user:mediconnect_dev_password@localhost:27017/mediconnect?authSource=admin')

# ── AWS S3 ────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID       = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY   = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='mediconnect-assets-aak')
AWS_S3_REGION_NAME      = env('AWS_S3_REGION_NAME', default='eu-north-1')
AWS_S3_FILE_OVERWRITE   = False
AWS_DEFAULT_ACL         = None
AWS_S3_ENCRYPTION       = True

# ── Twilio ────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID  = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN   = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')

# ── SendGrid ──────────────────────────────────────────────────
SENDGRID_API_KEY    = env('SENDGRID_API_KEY', default='')
DEFAULT_FROM_EMAIL  = 'noreply@mediconnect.salman-aak.com'
DEFAULT_FROM_NAME   = 'MediConnect'

# Email backend (overridden per environment)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── OpenAI ────────────────────────────────────────────────────
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_MODEL   = 'gpt-4'

# ── Logging ───────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

