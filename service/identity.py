"""Credential-principal to institutional-Identity binding."""

from __future__ import annotations

from ledger.base import Ledger

from .errors import AuthorizationError
from .models import RequestPrincipal


class IdentityService:
    def __init__(self, ledger: Ledger, *, allow_signed_without_oauth: bool = False) -> None:
        self._ledger = ledger
        self._allow_signed_without_oauth = allow_signed_without_oauth

    def require_binding(
        self, requested_identity_hash: str, principal: RequestPrincipal | None
    ) -> None:
        if principal is None:
            if self._allow_signed_without_oauth:
                return
            raise AuthorizationError("OAuth principal is required")
        linked = self._ledger.resolve_principal(principal.issuer, principal.subject)
        if linked is None:
            raise AuthorizationError("authenticated principal is not linked to Powerfarm Identity")
        if linked != requested_identity_hash:
            raise AuthorizationError("OAuth principal does not control the requested Identity")
