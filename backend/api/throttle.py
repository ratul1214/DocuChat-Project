# backend/api/throttle.py
from rest_framework.throttling import SimpleRateThrottle

def _tenant_key_from_request(request) -> str:
    return getattr(request, "tenant_key", None) or request.headers.get("X-Tenant") or "default"

def _sub_from_request(request) -> str:
    # mock/dev-friendly
    if isinstance(getattr(request, "auth", None), dict):
        return request.auth.get("sub") or "mock-user"
    return getattr(getattr(request, "user", None), "oidc_sub", None) or "mock-user"

class _BaseTenantThrottle(SimpleRateThrottle):
    scope = "base"

    def get_cache_key(self, request, view):
        tenant = _tenant_key_from_request(request)
        sub = _sub_from_request(request)
        if not tenant or not sub:
            return None
        # per-tenant-per-user throttle bucket
        ident = f"{tenant}:{sub}"
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request) + ":" + ident,
        }

class BurstTenantThrottle(_BaseTenantThrottle):
    scope = "burst"

class SustainedTenantThrottle(_BaseTenantThrottle):
    scope = "sustained"
