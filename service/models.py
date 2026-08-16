"""Value-only inputs and outputs for Kernel service operations."""

from __future__ import annotations

import base64
import re
from collections.abc import Mapping
from dataclasses import dataclass

from kernel.canon import CanonValue
from kernel.types import Act, Command, Context, Decision, Identity

from .errors import ValidationError

HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Context keys the service resolves and the caller may never assert.
#
# Authentication says who is presenting the request; the Command signature says
# which institutional participant is proposing the transition. Those are two
# different questions, and separating them is what lets one participant act *on
# request of* another. Rules then decide whether that relation carries authority
# -- a difference between requester and performer must be authorized, not merely
# tolerated.
REQUESTED_BY = "request.requested_by"
PERFORMED_BY = "request.performed_by"
REQUESTER_KIND = "request.requester_kind"
OAUTH_CLIENT = "request.oauth_client"
DERIVED_CONTEXT_KEYS = frozenset({REQUESTED_BY, PERFORMED_BY, REQUESTER_KIND, OAUTH_CLIENT})


def require_hash(value: str, field: str) -> str:
    if not HASH_PATTERN.fullmatch(value):
        raise ValidationError(f"{field} must be a lowercase SHA-256 hash")
    return value


def decode_signature(value: str) -> bytes:
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError) as error:
        raise ValidationError("signature must be base64url") from error
    if len(decoded) != 64:
        raise ValidationError("Ed25519 signature must be 64 bytes")
    return decoded


@dataclass(frozen=True, slots=True)
class RequestPrincipal:
    """Who is presenting this request to the Platform.

    No scopes. An OAuth scope never carried Powerfarm authority: the issuer
    offers only openid/email/profile/phone, and authority is decided by Rules
    over requester, performer and Context. Keeping a scope field here would
    invite someone to consult it one day.
    """

    issuer: str
    subject: str
    client_id: str


@dataclass(frozen=True, slots=True)
class ActionRequest:
    command_type: str
    identity_hash: str
    payload_hash: str
    parents: tuple[str, ...]
    nonce: str
    signature: str
    context_values: Mapping[str, CanonValue]
    context_types: Mapping[str, str]
    act_type: str
    payload: CanonValue | None = None
    history_cut: frozenset[str] | None = None
    registry_cut: frozenset[str] | None = None
    auth_chain: tuple[str, ...] = ()
    # The time claimed inside the Act; part of its content and its hash
    # (section 10.3). Named `claimed_when` rather than `when` so it can never be
    # read as causal order or as provable knowledge time.
    claimed_when: str | None = None

    def command(self) -> Command:
        require_hash(self.identity_hash, "identity_hash")
        require_hash(self.payload_hash, "payload_hash")
        for index, parent in enumerate(self.parents):
            require_hash(parent, f"parents[{index}]")
        return Command(
            command_type=self.command_type,
            identity_hash=self.identity_hash,
            payload_hash=self.payload_hash,
            parents=self.parents,
            nonce=self.nonce,
            signature=decode_signature(self.signature),
        )

    def context(self, derived: Mapping[str, str] | None = None) -> Context:
        """Client Context, with the Kernel-derived keys layered on top.

        The derived keys are not merged politely -- a request that supplies one
        is refused outright. `requested_by` is worth nothing if a caller can
        assert it, so the only way it enters history is by being resolved from a
        verified token through `principal_bindings`.
        """
        if derived is None:
            return Context(self.context_values, self.context_types)
        supplied = DERIVED_CONTEXT_KEYS & self.context_values.keys()
        if supplied:
            raise ValidationError(
                "Kernel-derived Context keys may not be supplied by the caller: "
                + ", ".join(sorted(supplied))
            )
        return Context(
            {**self.context_values, **derived},
            {**self.context_types, **{key: key for key in derived}},
        )


@dataclass(frozen=True, slots=True)
class EvaluatedAction:
    identity: Identity
    command: Command
    context: Context
    decision: Decision
    act_type: str
    auth_chain: tuple[str, ...]
    payload: CanonValue | None

    def as_dict(self) -> dict[str, object]:
        return {
            "act_type": self.act_type,
            "command_hash": self.command.hash,
            "context_hash": self.context.hash,
            "decision": {
                "outcome": self.decision.outcome.value,
                "reason": self.decision.reason,
                "history_cut": sorted(self.decision.cut),
                "registry_cut": sorted(self.decision.registry_cut),
                "rule_hashes": list(self.decision.rule_hashes),
            },
            "identity_hash": self.identity.hash,
            "payload_hash": self.command.payload_hash,
        }


def act_to_dict(act: Act) -> dict[str, object]:
    return {
        "hash": act.hash,
        "act_type": act.act_type,
        "identity_hash": act.identity_hash,
        "parents": list(act.parents),
        "decision_cut": sorted(act.decision_cut),
        "command_hash": act.command_hash,
        "auth_chain": list(act.auth_chain),
        "registry_cut": sorted(act.registry_cut),
        "rule_hashes": list(act.rule_hashes),
        "context_hash": act.context_hash,
        "payload_hash": act.payload_hash,
        "claimed_when": act.claimed_when,
    }
