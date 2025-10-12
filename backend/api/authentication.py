import json
import time
import requests
from jose import jwt
from rest_framework import authentication, exceptions
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

class MockBearerAuthentication(BaseAuthentication):
    """
    Accepts Authorization: Bearer <token>
    Token format we mint in login: mock:<tenant>:<sub>
    """
    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None  # let other authenticators run (or anonymous)

        token = auth.split(" ", 1)[1].strip()
        parts = token.split(":", 2)
        if len(parts) != 3 or parts[0] != "mock":
            raise exceptions.AuthenticationFailed("Invalid token")

        tenant_key, sub = parts[1], parts[2]

        # Attach a very light “user” with .oidc_sub
        class _U: pass
        u = _U()
        u.is_authenticated = True
        u.oidc_sub = sub

        # Attach claims-like dict for middleware-aware code
        request.auth = {"tenant": tenant_key, "sub": sub}
        return (u, request.auth)
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
