"""Binding a credential principal to an Identity, as a governed change."""

from __future__ import annotations

from collections.abc import Mapping

from kernel.canon import CanonValue
from kernel.types import Act
from ledger.base import BindingProjection

from .authority import AuthorityService
from .errors import ValidationError
from .models import ActionRequest, EvaluatedAction, RequestPrincipal

LINK = ("LinkPrincipal", "PrincipalLinked")
REVOKE = ("RevokePrincipal", "PrincipalRevoked")


class PrincipalService:
    """`principal_bindings` is a projection; these Acts are what it projects.

    The table previously had no writer, so a row could only appear by hand --
    the invisible second mechanism section 17 rules out. Here the binding enters
    the same way every other change does, and the projection follows the Act
    rather than standing beside it.
    """

    def __init__(self, authority: AuthorityService, ledger_writer: BindingProjection) -> None:
        self._authority = authority
        self._bindings = ledger_writer

    def link(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> tuple[EvaluatedAction, Act]:
        payload = self._require_payload(request, LINK)
        evaluated, act = self._authority.commit(request, principal)
        self._bindings.link_principal(
            issuer=str(payload["issuer"]),
            subject=str(payload["subject"]),
            identity_hash=str(payload["identity_hash"]),
            linked_act=act.hash,
        )
        return evaluated, act

    def revoke(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> tuple[EvaluatedAction, Act]:
        payload = self._require_payload(request, REVOKE)
        evaluated, act = self._authority.commit(request, principal)
        self._bindings.revoke_principal(
            issuer=str(payload["issuer"]),
            subject=str(payload["subject"]),
            unlinked_act=act.hash,
        )
        return evaluated, act

    @staticmethod
    def _require_payload(
        request: ActionRequest, kinds: tuple[str, str]
    ) -> Mapping[str, CanonValue]:
        command_type, act_type = kinds
        if request.command_type != command_type:
            raise ValidationError(f"this operation requires the {command_type} command type")
        if request.act_type != act_type:
            raise ValidationError(f"this operation must produce {act_type}")
        payload = request.payload
        if not isinstance(payload, Mapping):
            raise ValidationError("payload must be an object")
        required = ("issuer", "subject") if act_type == REVOKE[1] else (
            "issuer", "subject", "identity_hash")
        for field in required:
            value = payload.get(field)
            if not isinstance(value, str) or not value:
                raise ValidationError(f"{field} is required")
        return payload
