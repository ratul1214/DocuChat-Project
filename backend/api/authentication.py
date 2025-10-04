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
