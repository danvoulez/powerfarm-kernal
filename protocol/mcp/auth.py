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
    clients: frozenset[str]


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
            # A client identity is presented or it is absent; it is never
            # derived. The previous fallback manufactured one from `aud`, so a
            # token carrying no client at all arrived wearing the audience as
            # its name, and every such token looked like the same caller.
            client_id = claims.get("client_id") or claims.get("azp")
            if not isinstance(client_id, str) or not client_id:
                return None
            if self._settings.clients and client_id not in self._settings.clients:
                return None
            return AccessToken(
                token=token,
                client_id=client_id,
                # OAuth scope is not Powerfarm authority and never was: Supabase
                # issues only openid/email/profile/phone, and authority is a Rule
                # decision over requester, performer and Context. Nothing here
                # reads a scope, so nothing can quietly start trusting one.
                scopes=[],
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
    return RequestPrincipal(issuer, token.subject, token.client_id)


def auth_from_env() -> tuple[AuthSettings | None, TokenVerifier | None, bool]:
    required = _enabled(os.environ.get("POWERFARM_AUTH_REQUIRED"))
    if not required:
        return None, None, False
    issuer = os.environ.get("POWERFARM_OAUTH_ISSUER")
    resource = os.environ.get("POWERFARM_MCP_RESOURCE_URL")
    if not issuer or not resource:
        raise RuntimeError(
            "POWERFARM_OAUTH_ISSUER and POWERFARM_MCP_RESOURCE_URL are required "
            "when OAuth is enabled"
        )
    # The audience is the resource this token was minted for, so a token issued
    # for one Kernel cannot be replayed against another. Supabase mints `aud:
    # authenticated` by default; a Custom Access Token Hook narrows it to the
    # resource, which is why this defaults to the resource rather than a name.
    audience = os.environ.get("POWERFARM_OAUTH_AUDIENCE", resource)
    jwks_url = os.environ.get(
        "POWERFARM_OAUTH_JWKS_URL", f"{issuer.rstrip('/')}/.well-known/jwks.json"
    )
    algorithms = tuple(
        item.strip()
        for item in os.environ.get("POWERFARM_OAUTH_ALGORITHMS", "ES256,RS256").split(",")
        if item.strip()
    )
    clients = frozenset(
        item.strip()
        for item in os.environ.get("POWERFARM_OAUTH_CLIENTS", "").split(",")
        if item.strip()
    )
    auth = AuthSettings(
        issuer_url=AnyHttpUrl(issuer),
        resource_server_url=AnyHttpUrl(resource),
        required_scopes=[],
    )
    verifier = SupabaseJWTVerifier(
        JWTSettings(issuer, audience, jwks_url, algorithms, resource, clients)
    )
    return auth, verifier, True
