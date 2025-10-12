# backend/api/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

import re

class TenantMiddleware:
    def __init__(self, get_response): self.get_response = get_response

    def __call__(self, request):
        # tenant
        tenant_key = request.headers.get("X-Tenant") or "default"

        # sub from (in order) DRF claims -> bearer mock token -> header -> default
        sub = None
        # DRF may set request.auth later; don't rely on it here unless already dict
        claims = getattr(request, "auth", None)
        if isinstance(claims, dict):
            sub = claims.get("sub")
        if not sub:
            auth = request.headers.get("Authorization", "")
            m = re.match(r"Bearer\s+mock::(.+)$", auth)
            if m: sub = m.group(1)
        if not sub:
            sub = request.headers.get("X-Sub")
        if not sub:
            sub = "mock-user"

        request.sub = sub
        request.tenant_key = tenant_key
        return self.get_response(request)

import uuid
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class RequestIDMiddleware(MiddlewareMixin):
    """
    Injects a unique X-Request-ID into every request and log record.
    """
    def process_request(self, request):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.id = rid
        request.META["X-Request-ID"] = rid
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        rid = getattr(request, "id", None)
        if rid:
            response["X-Request-ID"] = rid
        duration = (time.time() - getattr(request, "_start_time", time.time())) * 1000
        logger.info(f"[RID={rid}] {request.method} {request.path} "
                    f"{response.status_code} ({duration:.1f}ms)")
        return response
