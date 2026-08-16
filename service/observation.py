"""Admission rules for provenance-bearing external observations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from kernel.canon import CanonValue
from kernel.types import Act

from .authority import AuthorityService
from .effects import validate_effect_phase
from .errors import ValidationError
from .models import ActionRequest, EvaluatedAction, RequestPrincipal


class ObservationService:
    def __init__(self, authority: AuthorityService) -> None:
        self._authority = authority

    def admit(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> tuple[EvaluatedAction, Act]:
        if request.command_type != "AdmitObservation":
            raise ValidationError("observation admission requires AdmitObservation command type")
        if request.act_type != "ObservationAdmitted":
            raise ValidationError("observation admission must produce ObservationAdmitted")
        payload = request.payload
        if not isinstance(payload, Mapping):
            raise ValidationError("observation payload must be an object")
        self._validate_payload(payload, request.identity_hash)
        return self._authority.commit(request, principal)

    @staticmethod
    def _validate_payload(payload: Mapping[str, CanonValue], identity_hash: str) -> None:
        if payload.get("observer_identity_hash") != identity_hash:
            raise ValidationError("observer_identity_hash must match the signing Identity")
        evidence = payload.get("evidence_hashes")
        if (
            not isinstance(evidence, Sequence)
            or isinstance(evidence, str)
            or not evidence
            or any(not isinstance(item, str) or len(item) != 64 for item in evidence)
        ):
            raise ValidationError("observation requires one or more evidence_hashes")
        phase = payload.get("effect_phase")
        if not isinstance(phase, str):
            raise ValidationError("observation requires effect_phase")
        validate_effect_phase(phase)
