import base64
from dataclasses import dataclass

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agent.tools import propose_command
from kernel.canon import canonicalize, object_hash
from kernel.commit import CommitError, CommitGate
from kernel.memory import MemoryStore
from kernel.rules import RuleResult, authorize
from kernel.types import LIFECYCLE_ACT_TYPES, Act, Context, DecisionKind, Identity


@dataclass(frozen=True)
class Allow:
    hash: str = "rule-v1"
    context_keys: frozenset[str] = frozenset({"request.origin"})

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        return RuleResult(DecisionKind.ALLOW, "test authority grants this command")


@dataclass(frozen=True)
class Outcome:
    """A Rule that returns whatever outcome the scenario needs to exercise."""

    result: DecisionKind
    hash: str = "rule-outcome-v1"
    context_keys: frozenset[str] = frozenset({"request.origin"})

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        return RuleResult(self.result, f"test authority returns {self.result}")


def setup_case() -> tuple[MemoryStore, Identity, object, Context, object]:
    store = MemoryStore()
    genesis = "0" * 64
    store.acts[genesis] = Act(genesis, "GenesisClosed", genesis, (), frozenset(), "genesis-command",
                              (), frozenset(), (), genesis, genesis)
    store.register("command_type", "CreateThing", genesis)
    store.register("act_type", "ThingCreated", genesis)
    for lifecycle_type in LIFECYCLE_ACT_TYPES:
        store.register("act_type", lifecycle_type, genesis)
    store.register("context_type", "request.origin", genesis)
    payload = {"name": "one"}
    payload_hash = object_hash("payload", payload)
    store.put_object(payload_hash, canonicalize(payload), "payload")
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    identity = Identity(object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public)
    command = propose_command("CreateThing", identity.hash, payload_hash, (genesis,), "n-1", private)
    context = Context({"request.origin": "test"}, {"request.origin": "origin-v1"})
    rule = Allow(hash=object_hash("rule", {"name": "test.allow", "version": 1}))
    store.register("rule", rule.hash, genesis)
    decision = authorize(identity, command, context, store.history_cut(), frozenset({genesis}), (rule,))
    return store, identity, command, context, decision


def test_pf01_pf02_pf03_pf04_pf08_pf11_pf13_pf14_pf23() -> None:
    store, identity, command, context, decision = setup_case()
    gate = CommitGate(store)
    act = gate.commit(identity, command, decision, context, act_type="ThingCreated")
    assert gate.commit(identity, command, decision, context, act_type="ThingCreated") == act
    assert store.objects[act.hash][0]
    assert act.context_hash == context.hash
    assert act.decision_cut == decision.cut


def test_tampering_and_cut_drift_fail_loud() -> None:
    store, identity, command, context, decision = setup_case()
    bad = command.__class__(command.command_type, command.identity_hash, command.payload_hash,
                            command.parents, "tampered", command.signature)
    with pytest.raises(CommitError, match="signature"):
        CommitGate(store).commit(identity, bad, decision, context, act_type="ThingCreated")
    store.acts["1" * 64] = store.acts["0" * 64]
    with pytest.raises(CommitError, match="advanced"):
        CommitGate(store).commit(identity, command, decision, context, act_type="ThingCreated")


GENESIS = "0" * 64


def decide(store: MemoryStore, identity: Identity, command: object, context: Context,
           outcome: DecisionKind) -> object:
    """Authorize at the current cut with a Rule that returns *outcome*."""
    rule = Outcome(outcome, hash=object_hash("rule", {"name": "test.allow", "version": 1}))
    return authorize(identity, command, context, store.history_cut(),
                     frozenset({GENESIS}), (rule,))


def test_allow_commits_the_consequential_act() -> None:
    store, identity, command, context, decision = setup_case()
    act = CommitGate(store).commit(identity, command, decision, context, act_type="ThingCreated")
    assert act.act_type == "ThingCreated"
    assert store.get_act(act.hash) == act


def test_deny_records_commanddenied_but_refuses_consequence() -> None:
    store, identity, command, context, _ = setup_case()
    gate = CommitGate(store)
    denied = decide(store, identity, command, context, DecisionKind.DENY)
    recorded = gate.commit(identity, command, denied, context, act_type="CommandDenied")
    assert recorded.hash in store.acts, "refusing to authorize is itself a fact of history"
    again = decide(store, identity, command, context, DecisionKind.DENY)
    with pytest.raises(CommitError, match="requires allow"):
        gate.commit(identity, command, again, context, act_type="ThingCreated")


def test_require_review_records_reviewrequested_but_refuses_consequence() -> None:
    store, identity, command, context, _ = setup_case()
    gate = CommitGate(store)
    deferred = decide(store, identity, command, context, DecisionKind.REQUIRE_REVIEW)
    requested = gate.commit(identity, command, deferred, context, act_type="ReviewRequested")
    assert requested.hash in store.acts
    again = decide(store, identity, command, context, DecisionKind.REQUIRE_REVIEW)
    with pytest.raises(CommitError, match="requires allow"):
        gate.commit(identity, command, again, context, act_type="ThingCreated")


def test_deny_cannot_smuggle_an_arbitrary_lifecycle_act() -> None:
    """The outcome table is not a door: deny admits CommandDenied, nothing else."""
    store, identity, command, context, _ = setup_case()
    denied = decide(store, identity, command, context, DecisionKind.DENY)
    with pytest.raises(CommitError, match="requires allow"):
        CommitGate(store).commit(identity, command, denied, context,
                                 act_type="AuthorizationReviewed")


def test_full_review_lifecycle_then_consequence() -> None:
    """Spec 8.1: require_review blocks, the Review Act unblocks, consequence follows."""
    store, identity, command, context, _ = setup_case()
    gate = CommitGate(store)
    chain: list[str] = []

    deferred = decide(store, identity, command, context, DecisionKind.REQUIRE_REVIEW)
    chain.append(gate.commit(identity, command, deferred, context,
                             act_type="ReviewRequested").hash)
    reviewed = decide(store, identity, command, context, DecisionKind.ALLOW)
    chain.append(gate.commit(identity, command, reviewed, context,
                             act_type="AuthorizationReviewed", auth_chain=tuple(chain)).hash)
    resolved = decide(store, identity, command, context, DecisionKind.ALLOW)
    chain.append(gate.commit(identity, command, resolved, context,
                             act_type="AuthorizationResolved", auth_chain=tuple(chain)).hash)
    final = decide(store, identity, command, context, DecisionKind.ALLOW)
    act = gate.commit(identity, command, final, context,
                      act_type="ThingCreated", auth_chain=tuple(chain))

    assert act.auth_chain == tuple(chain)
    assert len(store.get_acts_for_command(command.hash)) == 4


def test_authorizationresolved_may_carry_a_deny() -> None:
    store, identity, command, context, _ = setup_case()
    gate = CommitGate(store)
    deferred = decide(store, identity, command, context, DecisionKind.REQUIRE_REVIEW)
    gate.commit(identity, command, deferred, context, act_type="ReviewRequested")
    refused = decide(store, identity, command, context, DecisionKind.DENY)
    resolved = gate.commit(identity, command, refused, context, act_type="AuthorizationResolved")
    assert resolved.hash in store.acts


def test_pf23_same_act_submitted_twice_returns_the_same_act() -> None:
    store, identity, command, context, decision = setup_case()
    gate = CommitGate(store)
    first = gate.commit(identity, command, decision, context, act_type="ThingCreated")
    assert gate.commit(identity, command, decision, context, act_type="ThingCreated") == first


def test_pf15_same_command_different_lifecycle_acts_both_exist() -> None:
    store, identity, command, context, _ = setup_case()
    gate = CommitGate(store)
    first = gate.commit(identity, command,
                        decide(store, identity, command, context, DecisionKind.REQUIRE_REVIEW),
                        context, act_type="ReviewRequested")
    second = gate.commit(identity, command,
                         decide(store, identity, command, context, DecisionKind.ALLOW),
                         context, act_type="AuthorizationReviewed")
    assert first.hash != second.hash
    assert {act.hash for act in store.get_acts_for_command(command.hash)} == {
        first.hash, second.hash}


def test_a_command_buys_its_change_only_once() -> None:
    store, identity, command, context, decision = setup_case()
    gate = CommitGate(store)
    gate.commit(identity, command, decision, context, act_type="ThingCreated")
    later = decide(store, identity, command, context, DecisionKind.ALLOW)
    with pytest.raises(CommitError, match="already produced a consequential Act"):
        gate.commit(identity, command, later, context, act_type="ThingCreated")


def test_claimed_when_is_part_of_the_act_identity() -> None:
    """Section 10.3: the time claimed inside an Act is part of its hash.

    Isolated on the preimage, because committing twice would advance the cut and
    change the hash for an unrelated reason. Here everything is held identical
    except `claimed_when`.
    """
    store, identity, command, context, decision = setup_case()
    canonical = CommitGate._canonical_value
    bare = canonical(identity, command, decision, context, "ThingCreated", (), None)
    at_nine = canonical(identity, command, decision, context, "ThingCreated", (),
                        "2026-08-16T09:00:00Z")
    at_ten = canonical(identity, command, decision, context, "ThingCreated", (),
                       "2026-08-16T10:00:00Z")

    assert "claimed_when" in bare, "the field must be inside the hashed content, not beside it"
    assert len({object_hash("act", value) for value in (bare, at_nine, at_ten)}) == 3

    committed = CommitGate(store).commit(identity, command, decision, context,
                                         act_type="ThingCreated",
                                         claimed_when="2026-08-16T09:00:00Z")
    assert committed.claimed_when == "2026-08-16T09:00:00Z"
    assert committed.hash == object_hash("act", at_nine), "one representation, end to end"
