"""External-effect phase vocabulary; database admission never claims outside reality."""

from __future__ import annotations

from .errors import ValidationError

EFFECT_PHASES = (
    "requested",
    "authorized",
    "dispatched",
    "observed",
    "committed_as_external_fact",
    "dispatch_failed",
    "retried",
)


def validate_effect_phase(phase: str) -> str:
    if phase not in EFFECT_PHASES:
        raise ValidationError(f"effect phase must be one of {', '.join(EFFECT_PHASES)}")
    return phase
