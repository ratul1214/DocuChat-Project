from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import BasePermission, SAFE_METHODS
class IsAuthenticatedOrOptions(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == "OPTIONS":
            return True
        return super().has_permission(request, view)
# backend/api/permissions.py (reuse from Step-1 and tighten)
class RequiresRole(BasePermission):
    required = {"user"}  # override per-view
    message = "Forbidden: missing required role."
    def has_permission(self, request, view):
        if os.getenv("OIDC_VERIFY","mock") == "mock":   # keep reviewers unblocked
            return True
        roles = _collect_roles(request.user, request.auth)  # as before
        return bool(self.required & roles)

# backend/api/permissions.py


ADMIN_ROLE_NAMES = {"admin", "tenant_admin", "docus-admin"}

def _extract_roles_from_token(auth):
    """
    Try common Keycloak layouts; fall back to simple 'roles' array.
    Supports mock tokens too.
    """
    roles = set()
    if not isinstance(auth, dict):
        return roles

    # Keycloak realm roles
    realm = auth.get("realm_access", {})
    roles.update(realm.get("roles", []) or [])

    # Keycloak client roles (optional)
    resource = auth.get("resource_access", {})
    for client, data in resource.items():
        roles.update(data.get("roles", []) or [])

    # Simple roles claim (mock-friendly)
    roles.update(auth.get("roles", []) or [])

    # Normalize
    return {str(r).strip().lower() for r in roles if r}

def _extract_roles_from_db(request):
    """
    If you persist roles on AppUser, read them when available.
    """
    try:
        user = getattr(request, "app_user", None) or getattr(request, "user", None)
        if user and hasattr(user, "roles") and isinstance(user.roles, (list, tuple)):
            return {str(r).strip().lower() for r in user.roles if r}
    except Exception:
        pass
    return set()

class IsTenantAdmin(BasePermission):
    """
    Allows access only to users with an admin-like role in the current tenant.
    """

    message = "Admin role required for this action."

    def has_permission(self, request, view):
        # Always allow safe methods if you prefer read-only for everyone:
        # if request.method in SAFE_METHODS: return True

        roles = set()
        roles |= _extract_roles_from_token(getattr(request, "auth", None))
        roles |= _extract_roles_from_db(request)

        # Also allow explicit override via header in dev/mock
        dev_role = request.headers.get("X-Role-Dev")
        if dev_role:
            roles.add(dev_role.lower())

        return len(ADMIN_ROLE_NAMES & roles) > 0
