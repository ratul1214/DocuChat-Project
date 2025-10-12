import os
from pathlib import Path
from datetime import timedelta

from corsheaders.defaults import default_headers  # ✅ correct import


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-not-for-prod')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')



INSTALLED_APPS = [
    'corsheaders',
    "pgvector.django",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    "api.apps.ApiConfig",



]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React dev server
    "http://127.0.0.1:3000",
    "https://localhost",
    "https://127.0.0.1",
]
MIDDLEWARE = [
    "api.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # must be high up
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "api.middleware.TenantMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# add near top
import sys

# ...
TESTING = os.getenv("TESTING", "0") == "1" or "pytest" in sys.modules or "test" in sys.argv

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'docuchat'),
        'USER': os.getenv('POSTGRES_USER', 'docu'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'docu'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': int(os.getenv('POSTGRES_PORT', 5432)),
    }
}

# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [(os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', 6379)))],
#         },
#     },
# }

# --- Redis cache ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
        "TIMEOUT": 60,  # default TTL; you can override per-set
    }
}

# --- DRF throttling ---
# REST_FRAMEWORK = {
#     "DEFAULT_THROTTLE_CLASSES": [
#         "api.throttle.BurstTenantThrottle",
#         "api.throttle.SustainedTenantThrottle",
#     ],
#     "DEFAULT_THROTTLE_RATES": {
#         # tweak to taste
#         "burst": os.getenv("THROTTLE_BURST", "20/min"),
#         "sustained": os.getenv("THROTTLE_SUSTAINED", "200/day"),
#     },
# }

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.MockBearerAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "api.throttle.BurstTenantThrottle",
        "api.throttle.SustainedTenantThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "burst": "20/min",
        "sustained": "200/day",
    },
}
#
# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": (
#         "api.authentication.KeycloakOIDCAuthentication",  # ✅ uses mock if OIDC_VERIFY=mock
#     ),
#     "DEFAULT_PERMISSION_CLASSES": (
#         "rest_framework.permissions.IsAuthenticated",
#     ),
#     # Default throttle settings
#     "DEFAULT_THROTTLE_CLASSES": [
#         "rest_framework.throttling.UserRateThrottle",
#         "rest_framework.throttling.AnonRateThrottle",
#     ],
#     "DEFAULT_THROTTLE_RATES": {
#         "user": "20/min",   # Authenticated users: 20 requests per minute
#         "anon": "10/min",   # Unauthenticated users: 10 requests per minute
#     },
# }
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("redis", 6379)]},
    },
}



LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# RAG/LLM
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # for ADR docs

# OIDC/Keycloak
OIDC_ISSUER = os.getenv('OIDC_ISSUER', '')  # e.g., https://keycloak:8443/realms/docu
OIDC_AUDIENCE = os.getenv('OIDC_AUDIENCE', 'docuchat-client')
OIDC_VERIFY = os.getenv('OIDC_VERIFY', 'mock')  # 'on' | 'mock'

MAX_UPLOAD_FILES = int(os.getenv('MAX_UPLOAD_FILES', '20'))
MAX_CHUNK_TOKENS = int(os.getenv('MAX_CHUNK_TOKENS', '600'))
CHUNK_OVERLAP_TOKENS = int(os.getenv('CHUNK_OVERLAP_TOKENS', '80'))
TOP_K = int(os.getenv('TOP_K', '5'))
# CORS (dev)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization"]
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "x-tenant",
    "content-type",
]
APPEND_SLASH = True

