"""Governed review submission; review creates history, never hidden session state."""

from __future__ import annotations

from collections.abc import Mapping

from kernel.canon import CanonValue
from kernel.types import Act

from .authority import AuthorityService
from .errors import ValidationError
from .models import ActionRequest, EvaluatedAction, RequestPrincipal


class ReviewService:
    def __init__(self, authority: AuthorityService) -> None:
        self._authority = authority

    def submit(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> tuple[EvaluatedAction, Act]:
        if request.command_type != "ReviewAuthorization":
            raise ValidationError("review submission requires ReviewAuthorization command type")
        if request.act_type != "AuthorizationReviewed":
            raise ValidationError("review submission must produce AuthorizationReviewed")
        payload = request.payload
        if not isinstance(payload, Mapping):
            raise ValidationError("review payload must be an object")
        self._validate_payload(payload)
        return self._authority.commit(request, principal)

    @staticmethod
    def _validate_payload(payload: Mapping[str, CanonValue]) -> None:
        target = payload.get("reviewed_command_hash")
        outcome = payload.get("outcome")
        if not isinstance(target, str) or len(target) != 64:
            raise ValidationError("reviewed_command_hash is required")
        if outcome not in ("allow", "deny"):
            raise ValidationError("review outcome must be allow or deny")
