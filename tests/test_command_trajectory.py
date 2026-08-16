"""Ownership and participation are different questions about the same history."""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agent.tools import propose_command
from kernel.canon import canonicalize, object_hash
from kernel.commit import CommitGate
from kernel.rules import RuleResult, authorize
from kernel.types import Act, Context, DecisionKind, Identity
from ledger.memory import MemoryLedger
from service.lifecycle import LifecycleService
from service.models import DERIVED_CONTEXT_KEYS

GENESIS = "0" * 64


class Rule:
    hash = object_hash("rule", {"name": "test.rule", "version": 1})
    context_keys = frozenset({"request.origin"})

    def __init__(self, outcome: DecisionKind) -> None:
        self.outcome = outcome

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        return RuleResult(self.outcome, "test")


def build() -> tuple[MemoryLedger, Identity, Context, Ed25519PrivateKey]:
    ledger = MemoryLedger()
    ledger.acts[GENESIS] = Act(GENESIS, "GenesisClosed", GENESIS, (), frozenset(),
                               "genesis-command", (), frozenset(), (), GENESIS, GENESIS)
    ledger.command_index["genesis-command"] = [GENESIS]
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    identity = Identity(
        object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public)
    ledger.seed_identity(identity)
    for name in ("CreateThing", "ReviewAuthorization"):
        ledger.register("command_type", name, GENESIS)
    for name in ("ThingCreated", "ReviewRequested", "AuthorizationReviewed",
                 "AuthorizationResolved"):
        ledger.register("act_type", name, GENESIS)
    ledger.register("context_type", "request.origin", GENESIS)
    for derived in DERIVED_CONTEXT_KEYS:
        ledger.register("context_type", derived, GENESIS)
    ledger.register("rule", "test.rule", GENESIS, entry_hash=Rule.hash)
    context = Context({"request.origin": "test"}, {"request.origin": "origin-v1"})
    return ledger, identity, context, private


def payload_command(ledger: MemoryLedger, identity: Identity, private: Ed25519PrivateKey,
                    command_type: str, payload: dict[str, object], nonce: str) -> object:
    payload_hash = object_hash("payload", payload)
    ledger.put_object(payload_hash, canonicalize(payload), "payload")
    return propose_command(command_type, identity.hash, payload_hash, (GENESIS,), nonce, private)


def test_review_act_participates_without_being_owned() -> None:
    ledger, identity, context, private = build()
    gate = CommitGate(ledger)

    def decide(command: object, outcome: DecisionKind) -> object:
        return authorize(identity, command, context, ledger.history_cut(),
                         frozenset({GENESIS}), (Rule(outcome),))

    target = payload_command(ledger, identity, private, "CreateThing", {"name": "one"}, "n-1")
    requested = gate.commit(identity, target, decide(target, DecisionKind.REQUIRE_REVIEW),
                            context, act_type="ReviewRequested")
    lifecycle = LifecycleService(ledger)
    assert lifecycle.status(target.hash)["status"] == "pending_review", (
        "while review is pending the Command is blocked (section 8.1)")

    review = payload_command(ledger, identity, private, "ReviewAuthorization",
                             {"outcome": "allow", "reviewed_command_hash": target.hash}, "r-1")
    reviewed = gate.commit(identity, review, decide(review, DecisionKind.ALLOW), context,
                           act_type="AuthorizationReviewed")
    gate.commit(identity, target, decide(target, DecisionKind.ALLOW), context,
                act_type="AuthorizationResolved", auth_chain=(requested.hash, reviewed.hash))

    trajectory = lifecycle.trajectory(target.hash)
    owned = {node["act"] for node in trajectory["owned"]}
    participating = {node["act"] for node in trajectory["participating"]}

    assert requested.hash in owned
    assert reviewed.hash not in owned, "the Review Act belongs to the Reviewer's Command"
    assert reviewed.hash in participating, "but it takes part in this Command's trajectory"
    assert trajectory["participating"][0]["owned_by_command"] == review.hash
    assert trajectory["status"] == "pending", "resolved, but consequence has not occurred"

    # The narrower question stays narrow.
    assert reviewed.hash not in {act.hash for act in ledger.get_acts_for_command(target.hash)}
    assert ledger.get_acts_for_command(review.hash) == (reviewed,)
