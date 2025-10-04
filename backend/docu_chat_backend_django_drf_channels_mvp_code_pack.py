# ─────────────────────────────────────────────────────────────────────────────
# backend/PROJECT STRUCTURE (MVP)
# ─────────────────────────────────────────────────────────────────────────────
# backend/
# ├── manage.py
# ├── pyproject.toml                   # or requirements.txt (both provided below)
# ├── requirements.txt
# ├── .env.sample
# ├── backend/                         # Django project package
# │   ├── __init__.py
# │   ├── asgi.py
# │   ├── settings.py
# │   ├── urls.py
# │   └── routing.py
# └── api/                             # App for auth, uploads, chat, RAG
#     ├── __init__.py
#     ├── admin.py
#     ├── apps.py
#     ├── authentication.py
#     ├── consumers.py
#     ├── embeddings.py
#     ├── indexing.py
#     ├── migrations/
#     │   └── 0001_initial.py
#     ├── models.py
#     ├── rag.py
#     ├── serializers.py
#     ├── urls.py
#     └── views.py
#
# Notes:
# • Real-time indexing progress is delivered via WebSocket groups using Channels.
# • JWT (Keycloak) validation via OIDC discovery + JWKS (configurable). For Step 1
#   you can set OIDC_VERIFY="mock" to bypass live verification (document in ADR).
# • Embeddings via OpenAI-compatible API (set EMBEDDING_MODEL + OPENAI_API_KEY) or
#   use "mock" mode for offline/local testing.
# • Simple cosine search over embeddings stored in Postgres (JSONB) for MVP.
#
# ─────────────────────────────────────────────────────────────────────────────

# =====================================
# manage.py
# =====================================
from pathlib import Path
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

# =====================================
# backend/__init__.py
# =====================================
# empty

# =====================================
# backend/asgi.py
# =====================================
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf import settings
import api.routing as api_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(api_routing.websocket_urlpatterns)
    ),
})

# =====================================
# backend/routing.py
# =====================================
# (not used; app-level routing below)

# =====================================
# backend/urls.py
# =====================================
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# =====================================
# backend/settings.py
# =====================================
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-not-for-prod')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.KeycloakOIDCAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
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

# =====================================
# backend/wsgi.py (optional for completeness)
# =====================================
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
application = get_wsgi_application()

# =====================================
# api/apps.py
# =====================================
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

# =====================================
# api/models.py
# =====================================
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

class Document(models.Model):
    owner_sub = models.CharField(max_length=255)  # OIDC subject
    filename = models.CharField(max_length=512)
    content_type = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    owner_sub = models.CharField(max_length=255)
    idx = models.IntegerField()
    text = models.TextField()
    embedding = models.JSONField()  # list[float]

class ChatSession(models.Model):
    owner_sub = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255, blank=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20)  # 'user' | 'assistant' | 'system'
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

# =====================================
# api/migrations/0001_initial.py
# =====================================
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_sub', models.CharField(max_length=255)),
                ('filename', models.CharField(max_length=512)),
                ('content_type', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_sub', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('title', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Chunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_sub', models.CharField(max_length=255)),
                ('idx', models.IntegerField()),
                ('text', models.TextField()),
                ('embedding', models.JSONField()),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='api.document')),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=20)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='api.chatsession')),
            ],
        ),
    ]

# =====================================
# api/authentication.py (Keycloak OIDC JWT)
# =====================================
import json
import time
import requests
from jose import jwt
from rest_framework import authentication, exceptions
from django.conf import settings

class KeycloakOIDCAuthentication(authentication.BaseAuthentication):
    """Validate incoming Authorization: Bearer <JWT> from Keycloak.
    If settings.OIDC_VERIFY == 'mock', accept any token and set request.user as AnonymousUser
    but with a .oidc_sub attribute via SimpleUser wrapper.
    """
    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).decode('utf-8')
        if not auth or not auth.lower().startswith('bearer '):
            return None
        token = auth.split(' ')[1]

        if settings.OIDC_VERIFY == 'mock':
            sub = 'mock-user'
            user = SimpleUser(sub)
            return (user, None)

        try:
            unverified = jwt.get_unverified_header(token)
            jwks = _fetch_jwks(settings.OIDC_ISSUER)
            key = None
            for k in jwks['keys']:
                if k['kid'] == unverified['kid']:
                    key = k
                    break
            if not key:
                raise exceptions.AuthenticationFailed('JWKS key not found')
            payload = jwt.decode(
                token,
                key,
                audience=settings.OIDC_AUDIENCE,
                issuer=settings.OIDC_ISSUER,
                options={'verify_at_hash': False},
            )
            sub = payload['sub']
            user = SimpleUser(sub)
            return (user, None)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {e}')

class SimpleUser:
    is_authenticated = True
    def __init__(self, sub: str):
        self.oidc_sub = sub
        self.username = sub


def _fetch_jwks(issuer: str):
    r = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=5)
    r.raise_for_status()
    jwks_uri = r.json()['jwks_uri']
    jwks = requests.get(jwks_uri, timeout=5).json()
    return jwks

# =====================================
# api/serializers.py
# =====================================
from rest_framework import serializers
from .models import Document, Chunk

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'filename', 'content_type', 'created_at']

class AskSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False)
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False)

# =====================================
# api/embeddings.py
# =====================================
import os
import numpy as np
from typing import List

class Embedder:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.mode = 'mock' if not self.api_key else 'openai'

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.mode == 'mock':
            # Deterministic pseudo-embedding: hash → vector (MVP/testing)
            return [self._mock_embedding(t) for t in texts]
        else:
            # OpenAI-compatible embeddings API
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.embeddings.create(model=self.model, input=texts)
            return [d.embedding for d in resp.data]

    def _mock_embedding(self, text: str, dim: int = 256) -> List[float]:
        import hashlib, random
        h = hashlib.sha256(text.encode('utf-8')).digest()
        rng = random.Random(h)
        return [rng.uniform(-1, 1) for _ in range(dim)]

# =====================================
# api/rag.py
# =====================================
import numpy as np
from typing import List, Tuple
from django.conf import settings
from .models import Chunk


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def search(owner_sub: str, query_embedding: List[float], top_k: int) -> List[Tuple[Chunk, float]]:
    q = np.array(query_embedding, dtype=float)
    results = []
    for ch in Chunk.objects.filter(owner_sub=owner_sub).select_related('document'):
        e = np.array(ch.embedding, dtype=float)
        sim = _cosine(q, e)
        results.append((ch, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# =====================================
# api/indexing.py (file parsing, chunking, progress events)
# =====================================
import io
import threading
from typing import List
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Document, Chunk
from .embeddings import Embedder

EMBEDDER = Embedder()


def _send_progress(sub: str, payload: dict):
    group = f"progress.{sub}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(group, {"type": "progress.message", "payload": payload})


def _extract_text(filename: str, content: bytes, content_type: str) -> str:
    if content_type in ('text/plain',) or filename.lower().endswith('.txt'):
        return content.decode('utf-8', errors='ignore')
    if content_type in ('text/markdown',) or filename.lower().endswith('.md'):
        return content.decode('utf-8', errors='ignore')
    if content_type in ('application/pdf',) or filename.lower().endswith('.pdf'):
        from pdfminer.high_level import extract_text
        with io.BytesIO(content) as f:
            return extract_text(f)
    # Fallback: treat as text
    return content.decode('utf-8', errors='ignore')


def _chunk_text(text: str, max_tokens: int, overlap: int) -> List[str]:
    # Token-agnostic MVP: split by ~max_tokens words
    words = text.split()
    chunks = []
    i = 0
    step = max_tokens - overlap
    if step <= 0:
        step = max_tokens
    while i < len(words):
        chunk_words = words[i:i + max_tokens]
        chunks.append(' '.join(chunk_words))
        i += step
    return chunks


def index_file(owner_sub: str, filename: str, content: bytes, content_type: str):
    _send_progress(owner_sub, {"stage": "received", "filename": filename})
    text = _extract_text(filename, content, content_type)
    doc = Document.objects.create(owner_sub=owner_sub, filename=filename, content_type=content_type, text=text)

    _send_progress(owner_sub, {"stage": "chunking", "filename": filename})
    chunks = _chunk_text(text, settings.MAX_CHUNK_TOKENS, settings.CHUNK_OVERLAP_TOKENS)

    _send_progress(owner_sub, {"stage": "embedding", "filename": filename, "chunks": len(chunks)})
    vectors = EMBEDDER.embed(chunks)

    objs = [Chunk(document=doc, owner_sub=owner_sub, idx=i, text=ch, embedding=vectors[i]) for i, ch in enumerate(chunks)]
    Chunk.objects.bulk_create(objs, batch_size=100)

    _send_progress(owner_sub, {"stage": "done", "filename": filename, "chunks": len(chunks)})


def index_file_async(owner_sub: str, filename: str, content: bytes, content_type: str):
    # Lightweight background thread for MVP (no Celery in Step 1)
    threading.Thread(target=index_file, args=(owner_sub, filename, content, content_type), daemon=True).start()

# =====================================
# api/consumers.py (WebSocket progress)
# =====================================
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ProgressConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Expect querystring like ?sub=<subject>
        self.sub = self.scope['query_string'].decode().split('sub=')[-1] or 'mock-user'
        self.group_name = f"progress.{self.sub}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def progress_message(self, event):
        await self.send_json(event['payload'])

# =====================================
# api/routing.py
# =====================================
from django.urls import re_path
from .consumers import ProgressConsumer

websocket_urlpatterns = [
    re_path(r"ws/progress$", ProgressConsumer.as_asgi()),
]

# =====================================
# api/urls.py (HTTP endpoints)
# =====================================
from django.urls import path
from .views import UploadView, AskView, MeView, ListDocumentsView

urlpatterns = [
    path('me', MeView.as_view(), name='me'),
    path('documents', ListDocumentsView.as_view(), name='documents'),
    path('upload', UploadView.as_view(), name='upload'),
    path('chat/ask', AskView.as_view(), name='chat-ask'),
]

# =====================================
# api/views.py
# =====================================
from typing import List
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from .serializers import DocumentSerializer, AskSerializer
from .models import Document
from .indexing import index_file_async
from .embeddings import Embedder
from .rag import search

EMBEDDER = Embedder()

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        return Response({"sub": sub})

class ListDocumentsView(APIView):
    def get(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        docs = Document.objects.filter(owner_sub=sub).order_by('-created_at')
        return Response(DocumentSerializer(docs, many=True).data)

class UploadView(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        files = request.FILES.getlist('files')
        if not files:
            return Response({"detail": "No files uploaded"}, status=400)
        if len(files) > settings.MAX_UPLOAD_FILES:
            return Response({"detail": f"Max {settings.MAX_UPLOAD_FILES} files"}, status=400)

        for f in files:
            content = f.read()
            index_file_async(sub, f.name, content, f.content_type or 'application/octet-stream')
        return Response({"status": "queued", "count": len(files)})

class AskView(APIView):
    def post(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', settings.TOP_K)

        qvec = EMBEDDER.embed([question])[0]
        results = search(sub, qvec, top_k)

        # Build prompt with citations
        context_blocks = []
        citations = []
        for i, (chunk, score) in enumerate(results, start=1):
            context_blocks.append(f"[Doc {i}] {chunk.text}")
            citations.append({
                'index': i,
                'document_id': chunk.document.id,
                'filename': chunk.document.filename,
                'score': round(float(score), 4),
            })
        prompt = (
            "Answer the question using only the context. Cite sources using [Doc i].\n\n" +
            "\n\n".join(context_blocks) +
            f"\n\nQuestion: {question}\nAnswer:"
        )

        answer = _call_llm(prompt)
        return Response({"answer": answer, "citations": citations})


def _call_llm(prompt: str) -> str:
    # Minimal: use OpenAI if key present else return deterministic mock
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return "[MOCK ANSWER] This is a placeholder answer generated without external LLM."
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    chat = client.chat.completions.create(
        model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
        messages=[{"role": "system", "content": "You are a helpful RAG assistant."}, {"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return chat.choices[0].message.content.strip()

# =====================================
# requirements.txt (MVP)
# =====================================
# Django & REST
Django==5.0.6
psycopg[binary]==3.2.1
djangorestframework==3.15.2

# WebSockets
channels==4.1.0
channels-redis==4.2.0
asgiref==3.8.1

# Auth / JWT
python-jose[cryptography]==3.3.0
requests==2.32.3

# PDFs
pdfminer.six==20240706

# OpenAI (optional)
openai==1.40.2

# Utilities
numpy==2.1.0

# =====================================
# pyproject.toml (optional alternative to requirements.txt)
# =====================================
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "docuchat-backend"
version = "0.1.0"
dependencies = [
  "Django==5.0.6",
  "psycopg[binary]==3.2.1",
  "djangorestframework==3.15.2",
  "channels==4.1.0",
  "channels-redis==4.2.0",
  "asgiref==3.8.1",
  "python-jose[cryptography]==3.3.0",
  "requests==2.32.3",
  "pdfminer.six==20240706",
  "openai==1.40.2",
  "numpy==2.1.0",
]

# =====================================
# .env.sample
# =====================================
# Django
DJANGO_SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (docker-compose should provide these)
POSTGRES_DB=docuchat
POSTGRES_USER=docu
POSTGRES_PASSWORD=docu
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis (for Channels)
REDIS_HOST=redis
REDIS_PORT=6379

# Keycloak (Step 1: set OIDC_VERIFY=mock; Step 2: configure real values)
OIDC_ISSUER=https://keycloak:8443/realms/docu
OIDC_AUDIENCE=docuchat-client
OIDC_VERIFY=mock

# RAG
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
TOP_K=5
MAX_UPLOAD_FILES=20
MAX_CHUNK_TOKENS=600
CHUNK_OVERLAP_TOKENS=80

# =====================================
# api/admin.py (optional)
# =====================================
from django.contrib import admin
from .models import Document, Chunk, ChatSession, ChatMessage
admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
