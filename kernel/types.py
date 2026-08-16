"""Frozen, value-only types crossing the kernel boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from .canon import CanonValue, object_hash


def _freeze(values: Mapping[str, CanonValue]) -> Mapping[str, CanonValue]:
    return MappingProxyType(dict(values))


class DecisionKind(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_REVIEW = "require_review"


# Which authorization outcome may produce which Act (spec v3 sections 6.1, 8.1).
#
# A blanket "lifecycle Acts skip the allow check" would open a door where a deny
# commits anything named like a lifecycle stage. Instead each stage declares the
# outcome that is its own evidence: `require_review` is permanently recorded by
# ReviewRequested, `deny` by CommandDenied, and AuthorizationResolved carries the
# final allow *or* deny after review.
#
# Everything absent from this table -- consequential Acts, and the lifecycle
# stages produced by an ordinary authorized Command such as AuthorizationRequested
# or the Reviewer's own AuthorizationReviewed -- requires allow. An unregistered
# or unknown Act type therefore fails closed.
PERMITTED_OUTCOMES: Mapping[str, frozenset[DecisionKind]] = MappingProxyType({
    "ReviewRequested": frozenset({DecisionKind.REQUIRE_REVIEW}),
    "CommandDenied": frozenset({DecisionKind.DENY}),
    "AuthorizationResolved": frozenset({DecisionKind.ALLOW, DecisionKind.DENY}),
})
CONSEQUENTIAL_OUTCOMES: frozenset[DecisionKind] = frozenset({DecisionKind.ALLOW})


# The stages of a Command's trajectory (spec v3 section 6.1). A Command may hold
# many of these at once; what it may hold only once is a *consequential* Act.
#
# The old `unique (command_hash)` conflated two rules: idempotency, which PF-23
# places on the Act's own hash, and "one consequential occurrence per Command",
# which is real. Only the second survives, and only for Acts outside this set --
# otherwise re-submitting an intent at a later cut would buy the change twice.
LIFECYCLE_ACT_TYPES: frozenset[str] = frozenset({
    "CommandSubmitted",
    "CommandValidated",
    "CommandRejected",
    "AuthorizationRequested",
    "CommandDenied",
    "ReviewRequested",
    "AuthorizationReviewed",
    "AuthorizationResolved",
    "CommandSuperseded",
    "CommandExpired",
})


@dataclass(frozen=True, slots=True)
class Identity:
    hash: str
    kind: str
    public_key: bytes


@dataclass(frozen=True, slots=True)
class Context:
    values: Mapping[str, CanonValue]
    types: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _freeze(self.values))
        object.__setattr__(self, "types", MappingProxyType(dict(self.types)))
        if set(self.values) != set(self.types):
            raise ValueError("every context value must have exactly one registered type")

    @property
    def hash(self) -> str:
        return object_hash("context", self.canonical_value())

    def canonical_value(self) -> dict[str, CanonValue]:
        return {"types": dict(self.types), "values": dict(self.values)}


@dataclass(frozen=True, slots=True)
class Command:
    command_type: str
    identity_hash: str
    payload_hash: str
    parents: tuple[str, ...]
    nonce: str
    signature: bytes = field(repr=False, compare=False)

    def signing_value(self) -> dict[str, CanonValue]:
        return {"command_type": self.command_type, "identity_hash": self.identity_hash,
                "nonce": self.nonce, "parents": list(self.parents), "payload_hash": self.payload_hash}

    @property
    def hash(self) -> str:
        return object_hash("command", self.signing_value())


@dataclass(frozen=True, slots=True)
class Decision:
    outcome: DecisionKind
    cut: frozenset[str]
    rule_hashes: tuple[str, ...]
    registry_cut: frozenset[str]
    reason: str


@dataclass(frozen=True, slots=True)
class Act:
    hash: str
    act_type: str
    identity_hash: str
    parents: tuple[str, ...]
    decision_cut: frozenset[str]
    command_hash: str
    auth_chain: tuple[str, ...]
    registry_cut: frozenset[str]
    rule_hashes: tuple[str, ...]
    context_hash: str
    payload_hash: str
    claimed_when: str | None = None


@dataclass(frozen=True, slots=True)
class Relation:
    from_hash: str
    to_hash: str
    relation_type: str
    payload_hash: str | None = None

    @property
    def hash(self) -> str:
        return object_hash("relation", {"from": self.from_hash, "payload": self.payload_hash,
                                        "relation_type": self.relation_type, "to": self.to_hash})
