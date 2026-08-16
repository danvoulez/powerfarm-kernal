"""OAuth protected-resource verification for Supabase-issued JWTs."""

from __future__ import annotations

import os
from dataclasses import dataclass

import anyio.to_thread
import jwt
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from service.models import RequestPrincipal


def _enabled(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class JWTSettings:
    issuer: str
    audience: str
    jwks_url: str
    algorithms: tuple[str, ...]
    resource: str


class SupabaseJWTVerifier(TokenVerifier):
    def __init__(self, settings: JWTSettings) -> None:
        self._settings = settings
        self._jwks = jwt.PyJWKClient(settings.jwks_url, cache_keys=True)

    async def verify_token(self, token: str) -> AccessToken | None:
        def verify() -> AccessToken | None:
            try:
                signing_key = self._jwks.get_signing_key_from_jwt(token)
                claims = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=list(self._settings.algorithms),
                    audience=self._settings.audience,
                    issuer=self._settings.issuer,
                    options={"require": ["exp", "iss", "sub", "aud"]},
                )
            except jwt.PyJWTError:
                return None
            subject = claims.get("sub")
            if not isinstance(subject, str) or not subject:
                return None
            scope_claim = claims.get("scope", "")
            scopes = scope_claim.split() if isinstance(scope_claim, str) else []
            audience = claims.get("aud")
            fallback_client = audience if isinstance(audience, str) else "supabase-client"
            client_id = claims.get("client_id") or claims.get("azp") or fallback_client
            return AccessToken(
                token=token,
                client_id=str(client_id),
                scopes=scopes,
                expires_at=int(claims["exp"]),
                resource=self._settings.resource,
                subject=subject,
                claims=dict(claims),
            )

        return await anyio.to_thread.run_sync(verify)


def current_principal() -> RequestPrincipal | None:
    token = get_access_token()
    if token is None:
        return None
    issuer = (token.claims or {}).get("iss")
    if not isinstance(issuer, str) or token.subject is None:
        return None
    return RequestPrincipal(issuer, token.subject, token.client_id, tuple(token.scopes))


def auth_from_env() -> tuple[AuthSettings | None, TokenVerifier | None, bool]:
    required = _enabled(os.environ.get("POWERFARM_AUTH_REQUIRED"))
    if not required:
        return None, None, False
    issuer = os.environ.get("POWERFARM_OAUTH_ISSUER")
    audience = os.environ.get("POWERFARM_OAUTH_AUDIENCE")
    resource = os.environ.get("POWERFARM_MCP_RESOURCE_URL")
    if not issuer or not audience or not resource:
        raise RuntimeError(
            "POWERFARM_OAUTH_ISSUER, POWERFARM_OAUTH_AUDIENCE and "
            "POWERFARM_MCP_RESOURCE_URL are required when OAuth is enabled"
        )
    jwks_url = os.environ.get(
        "POWERFARM_OAUTH_JWKS_URL", f"{issuer.rstrip('/')}/.well-known/jwks.json"
    )
    algorithms = tuple(
        item.strip()
        for item in os.environ.get("POWERFARM_OAUTH_ALGORITHMS", "ES256,RS256").split(",")
        if item.strip()
    )
    scopes = [
        item.strip()
        for item in os.environ.get("POWERFARM_MCP_SCOPES", "powerfarm.kernel").split(",")
        if item.strip()
    ]
    auth = AuthSettings(
        issuer_url=AnyHttpUrl(issuer),
        resource_server_url=AnyHttpUrl(resource),
        required_scopes=scopes,
    )
    verifier = SupabaseJWTVerifier(JWTSettings(issuer, audience, jwks_url, algorithms, resource))
    return auth, verifier, True
