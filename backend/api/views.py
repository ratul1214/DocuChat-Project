# api/views.py
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework import status

from openai import OpenAI, OpenAIError
import threading, time
from django.utils import timezone

from .indexing import index_file_async
from .embeddings import embed_texts
from .search import hybrid_search
from .models import Tenant, AppUser, Document, Chunk, ChatTurn, Report

# ---------- Small helpers ----------
def _get_tenant(request):
    key = getattr(request, "tenant_key", None) or request.headers.get("X-Tenant") or "default"
    tenant, _ = Tenant.objects.get_or_create(key=key, defaults={"name": key})
    return tenant

# backend/api/views.py (top-level helpers)
def resolve_tenant_user(request):
    # tenant
    tenant_key = getattr(request, "tenant_key", None) or request.headers.get("X-Tenant") or "default"
    tenant, _ = Tenant.objects.get_or_create(key=tenant_key, defaults={"name": tenant_key})

    # sub (try DRF claims → request.user.oidc_sub → header → mock)
    sub = None
    claims = getattr(request, "auth", None)
    if isinstance(claims, dict):
        sub = claims.get("sub")
    sub = sub or getattr(getattr(request, "user", None), "oidc_sub", None) \
              or request.headers.get("X-Sub") \
              or "mock-user"

    user, _ = AppUser.objects.get_or_create(tenant=tenant, sub=sub)
    return tenant, user, sub

def _get_user(request, tenant):
    # mock user if OIDC not wired
    sub = getattr(getattr(request, "user", None), "oidc_sub", None) or request.headers.get("X-Sub") or "mock-user"
    user, _ = AppUser.objects.get_or_create(tenant=tenant, sub=sub, defaults={"email": f"{sub}@example.com"})
    return user

# ---------- Health ----------
class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "ok"})

# ---------- Me ----------
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tenant = _get_tenant(request)
        user = _get_user(request, tenant)
        return Response({"tenant": tenant.key, "sub": user.sub})

# ---------- Documents ----------
class DocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant, user, _ = resolve_tenant_user(request)
        scope = request.query_params.get("scope", "mine")  # mine | tenant

        qs = Document.objects.filter(tenant=tenant)
        if scope == "mine":
            qs = qs.filter(owner=user)

        docs = qs.order_by("-created_at").values("id", "filename", "content_type", "created_at")
        return Response(list(docs))

# ---------- Upload ----------

# backend/api/views.py (only the changed parts)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .indexing import index_file, index_file_async

class UploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail': 'No files uploaded'}, status=400)

        tenant, user, sub = resolve_tenant_user(request)
        tenant_key = tenant.key

        for f in files:
            content = f.read()
            content_type = f.content_type or 'application/octet-stream'
            index_file_async(
                sub=sub,
                tenant_key=tenant_key,
                filename=f.name,
                content=content,
                content_type=content_type,
            )
        return Response({'status': 'queued', 'count': len(files)})


# backend/api/views.py



import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from openai import OpenAI, OpenAIError

from .embeddings import embed_texts, _stub_vec
from .models import Tenant
from .search import hybrid_search

log = logging.getLogger(__name__)

class AskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 1) Inputs (always safe defaults)
            query = (request.data.get("query") or "Hello").strip()
            if not query:
                # DRF Response (never return None)
                return Response({"detail": "Query must not be empty."},
                                status=status.HTTP_400_BAD_REQUEST)

            top_k = int(request.data.get("top_k") or 5)

            # 2) Tenant (never 404, create if missing)
            tenant_key = getattr(request, "tenant_key", None) or request.headers.get("X-Tenant") or "default"
            tenant, _ = Tenant.objects.get_or_create(key=tenant_key, defaults={"name": tenant_key})

            # 3) Embedding (try real; fall back to stub)
            try:
                _ = embed_texts([query])
            except Exception as e:
                log.warning("embed_texts failed; using stub vec: %s", e)
                _ = [_stub_vec(query)]

            # 4) Retrieval (never crash if no docs)
            try:
                top_chunks = hybrid_search(query, tenant, top_k=top_k)
            except Exception as e:
                log.error("hybrid_search failed: %s", e, exc_info=True)
                top_chunks = []

            context = "\n\n".join(c.text for c, *_ in top_chunks) if top_chunks else ""
            prompt = (
                "You are a helpful assistant.\n"
                "Use ONLY the context to answer the user's question. "
                "If the answer is not in the context, say so clearly.\n\n"
                f"Context:\n{context}\n\nQuestion:\n{query}"
            )

            # 5) Cache + LLM (always set an answer)
            ck = "llm:" + hashlib.sha1(prompt.encode()).hexdigest()
            answer = cache.get(ck)

            if not answer:
                api_key = getattr(settings, "OPENAI_API_KEY", None)
                if not api_key:
                    answer = "[MOCK ANSWER] (missing OPENAI_API_KEY)"
                else:
                    try:
                        client = OpenAI(api_key=api_key)
                        chat = client.chat.completions.create(
                            model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant for document Q&A."},
                                {"role": "user", "content": prompt},
                            ],
                            temperature=0.2,
                        )
                        answer = (chat.choices[0].message.content or "").strip() or "[MOCK ANSWER] (empty LLM reply)"
                    except OpenAIError as e:
                        log.error("LLM error: %s", e, exc_info=True)
                        answer = f"[MOCK ANSWER] LLM error: {e}"
                    except Exception as e:
                        log.error("Unexpected LLM exception: %s", e, exc_info=True)
                        answer = "[MOCK ANSWER] (unexpected LLM error)"

                cache.set(ck, answer, timeout=300)

            # 6) Build citations
            citations = [
                {
                    "filename": c.document.filename,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "score": float(score),
                }
                for (c, score, *_rest) in top_chunks
            ]

            return Response({"answer": answer, "citations": citations}, status=200)

        except Exception as e:
            # Final guard: never let DRF see a None
            log.exception("AskView fatal error: %s", e)
            return Response({"detail": f"Ask failed: {e.__class__.__name__}"}, status=500)


# ---------- Agent (Step 2 optional / Step 4 seed) ----------
def _agent_worker(report_id: int):
    r = Report.objects.get(pk=report_id)
    r.status = "running"
    r.save(update_fields=["status"])
    try:
        # replace with real multi-step agent logic later
        time.sleep(2)
        r.title = f"Auto Report @ {timezone.now().strftime('%H:%M:%S')}"
        r.content = "## Summary\nGenerated by agent workflow.\n"
        r.status = "done"
        r.save(update_fields=["title", "content", "status"])
    except Exception as e:
        r.status = "error"
        r.content = f"Error: {e}"
        r.save(update_fields=["status", "content"])

class AgentReportStartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        tenant = _get_tenant(request)
        user = _get_user(request, tenant)
        topic = (request.data.get("topic") or request.data.get("question") or "").strip()
        if not topic:
            return Response({"detail":"topic/question required"}, status=400)

        rpt = Report.objects.create(tenant=tenant, user=user, title="(pending)", status="queued", content="")
        threading.Thread(target=_agent_worker, args=(rpt.id,), daemon=True).start()
        return Response({"report_id": rpt.id, "status": rpt.status})

class ProgressTestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        from .indexing import _send_progress
        sub = request.data.get("sub", "mock-user")
        _send_progress(sub, "test", "hello from /api/progress/test")
        return Response({"ok": True})
class ReportListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tenant = _get_tenant(request)
        user = _get_user(request, tenant)
        qs = Report.objects.filter(tenant=tenant, user=user).values("id","title","status","created_at")
        return Response(list(qs))

class ReportDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, report_id: int):
        tenant = _get_tenant(request)
        user = _get_user(request, tenant)
        rpt = get_object_or_404(Report, id=report_id, tenant=tenant, user=user)
        return Response({"id": rpt.id, "title": rpt.title, "status": rpt.status, "content": rpt.content})

# backend/api/views.py
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .models import Tenant, AppUser

# class PasswordLoginView(APIView):
#     permission_classes = [AllowAny]
#     def post(self, request):
#         username = (request.data.get("username") or "").strip()
#         password = request.data.get("password") or ""
#         tenant_key = (request.data.get("tenant") or request.headers.get("X-Tenant") or "default").strip() or "default"
#
#         if not username:
#             return Response({"detail":"username required"}, status=400)
#
#         # mock password gate for step-2
#         demo_pw = getattr(settings, "AUTH_DEMO_PASSWORD", "demo")
#         if settings.OIDC_VERIFY != "mock":
#             return Response({"detail":"Password login only available in mock mode"}, status=400)
#         if password != demo_pw:
#             return Response({"detail":"invalid credentials"}, status=401)
#
#         tenant, _ = Tenant.objects.get_or_create(key=tenant_key, defaults={"name": tenant_key})
#         user, _ = AppUser.objects.get_or_create(tenant=tenant, sub=username, defaults={"email": f"{username}@example.com"})
#
#         # Return a simple opaque token "mock::<sub>"
#         token = f"mock::{username}"
#         return Response({"token": token, "tenant": tenant.key, "sub": user.sub})

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .consumers import _sanitize_group

def _agent_group(tenant_key: str, report_id: int) -> str:
    return _sanitize_group(f"agent.{tenant_key}.{report_id}")

def agent_send(tenant_key: str, report_id: int, stage: str, message: str, extra: dict | None = None):
    ch = get_channel_layer()
    if not ch:
        return
    payload = {"stage": stage, "message": message}
    if extra: payload.update(extra)
    async_to_sync(ch.group_send)(
        _agent_group(tenant_key, report_id),
        {"type": "agent.event", "payload": payload}
    )

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Tenant, AppUser

class PasswordLoginView(APIView):
    authentication_classes = []          # <- critical
    permission_classes = [AllowAny]      # <- critical

    def post(self, request):
        tenant_key = (request.headers.get("X-Tenant") or
                      request.data.get("tenant") or "default").strip()
        username = (request.data.get("username") or "").strip()
        password = (request.data.get("password") or "").strip()

        if not username or not password:
            return Response({"detail": "username and password required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # SUPER SIMPLE CHECK (replace with real auth later)
        # e.g., allow any non-empty password; or compare to env var
        # if password != os.getenv("DEV_PASSWORD", "pass"): ...
        # For now, accept anything non-empty:
        # (You can tighten this as needed.)
        tenant, _ = Tenant.objects.get_or_create(key=tenant_key, defaults={"name": tenant_key})
        AppUser.objects.get_or_create(tenant=tenant, sub=username)

        token = f"mock:{tenant.key}:{username}"
        return Response({
            "token": token,
            "tenant": tenant.key,
            "sub": username,
        })

from rest_framework.permissions import IsAuthenticated
from .permissions import IsTenantAdmin

class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request):
        # only tenant admins can do this
        return Response({"ok": True})