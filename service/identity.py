"""Credential-principal to institutional-Identity binding."""

from __future__ import annotations

from kernel.types import Identity
from ledger.base import Ledger

from .errors import AuthorizationError
from .models import RequestPrincipal


class IdentityService:
    def __init__(self, ledger: Ledger, *, allow_signed_without_oauth: bool = False) -> None:
        self._ledger = ledger
        self._allow_signed_without_oauth = allow_signed_without_oauth

    def resolve_requester(
        self, performer: Identity, principal: RequestPrincipal | None, cut: frozenset[str]
    ) -> tuple[str, str]:
        """Who asked, and of what kind -- resolved, never asserted.

        A principal proves that someone authenticated to the Platform; it does
        not say they may act. It also does not have to be a person: an
        autonomous service asks on its own behalf, and then requester and
        performer are the same Identity. Whether *this* performer may act on
        *this* requester's behalf is a Rule question, decided over the Context
        these values enter (section 5.1).
        """
        if principal is None:
            if not self._allow_signed_without_oauth:
                raise AuthorizationError("OAuth principal is required")
            return performer.hash, performer.kind
        requester_hash = self._ledger.resolve_principal(principal.issuer, principal.subject)
        if requester_hash is None:
            raise AuthorizationError("authenticated principal is not linked to Powerfarm Identity")
        if requester_hash == performer.hash:
            return requester_hash, performer.kind
        requester = self._ledger.get_identity(requester_hash, cut)
        if requester is None:
            raise AuthorizationError("requester Identity is unknown at the declared cut")
        return requester_hash, requester.kind
