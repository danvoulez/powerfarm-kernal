"""PF-21 Versioned Governance — semantic dependencies resolve to exact definitions.

    Every semantic dependency used to validate an admitted object is resolved to
    the exact content-addressed definition/version valid at its declared cut.

Today that concretely means the Registry cut and the Rule hashes. The law is
phrased generally on purpose: as Context types and Relation types become
hash-pinned, they join this matrix rather than earning a PF-21-and-a-half.

The distinction being defended is the one section 4.1 states outright --
"an Act validated under Rule version r_k remains governed by r_k forever". A
system that resolved "the rule named X" at read time would silently regovern its
own history every time a newer version was registered.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agent.tools import propose_command
from kernel.canon import canonicalize, object_hash
from kernel.commit import CommitError, CommitGate
from kernel.memory import MemoryStore
from kernel.types import (
    LIFECYCLE_ACT_TYPES,
    Act,
    Command,
    Context,
    Decision,
    DecisionKind,
    Identity,
)

GENESIS = "0" * 64
LATER = "1" * 64


@dataclass(frozen=True)
class NamedRule:
    """A Rule whose hash is derived from (name, version), as the Registry does."""

    name: str
    version: int
    context_keys: frozenset[str] = frozenset({"request.origin"})

    @property
    def hash(self) -> str:
        return object_hash("rule", {"name": self.name, "version": self.version})

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> object:
        from kernel.rules import RuleResult
        return RuleResult(DecisionKind.ALLOW, f"{self.name}.v{self.version} allows this")


@dataclass(frozen=True)
class Fixture:
    store: MemoryStore
    identity: Identity
    command: Command
    context: Context
    private: Ed25519PrivateKey


def build(nonce: str = "n-1") -> Fixture:
    """A universe holding one closed Genesis Act and the vocabulary a commit needs."""
    store = MemoryStore()
    store.acts[GENESIS] = Act(GENESIS, "GenesisClosed", GENESIS, (), frozenset(),
                              "genesis-command", (), frozenset(), (), GENESIS, GENESIS)
    store.register("command_type", "CreateThing", GENESIS)
    store.register("act_type", "ThingCreated", GENESIS)
    for lifecycle_type in LIFECYCLE_ACT_TYPES:
        store.register("act_type", lifecycle_type, GENESIS)
    store.register("context_type", "request.origin", GENESIS)

    payload = {"name": "one"}
    payload_hash = object_hash("payload", payload)
    store.put_object(payload_hash, canonicalize(payload), "payload")

    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    identity = Identity(
        object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public)
    command = propose_command("CreateThing", identity.hash, payload_hash, (GENESIS,),
                              nonce, private)
    context = Context({"request.origin": "test"}, {"request.origin": "origin-v1"})
    return Fixture(store, identity, command, context, private)


def decision(*rule_hashes: str, registry_cut: frozenset[str] | None = None,
             history_cut: frozenset[str] | None = None) -> Decision:
    return Decision(DecisionKind.ALLOW,
                    frozenset({GENESIS}) if history_cut is None else history_cut,
                    rule_hashes,
                    frozenset({GENESIS}) if registry_cut is None else registry_cut,
                    "test")


def advance_history(store: MemoryStore) -> None:
    """Land a second Act so the Registry can grow without the decision cut moving."""
    store.acts[LATER] = Act(LATER, "ThingCreated", GENESIS, (GENESIS,), frozenset({GENESIS}),
                            "other-command", (), frozenset({GENESIS}), (), GENESIS, GENESIS)


# --- the matrix ------------------------------------------------------------


def test_exact_registry_cut_and_rule_hashes_are_admitted() -> None:
    """The baseline: the versions that authorized are the versions recorded."""
    f = build()
    rule = NamedRule("test.allow", 1)
    f.store.register("rule", rule.hash, GENESIS)

    act = CommitGate(f.store).commit(
        f.identity, f.command, decision(rule.hash), f.context, act_type="ThingCreated")

    assert act.rule_hashes == (rule.hash,)
    assert act.registry_cut == frozenset({GENESIS})


def test_a_newer_rule_version_does_not_regovern_an_older_act() -> None:
    """Section 4.1: an Act validated under r_k remains governed by r_k forever."""
    f = build()
    v1 = NamedRule("test.allow", 1)
    f.store.register("rule", v1.hash, GENESIS)
    act = CommitGate(f.store).commit(
        f.identity, f.command, decision(v1.hash), f.context, act_type="ThingCreated")

    # A newer version of the *same name* is admitted later in history.
    advance_history(f.store)
    v2 = NamedRule("test.allow", 2)
    f.store.register("rule", v2.hash, LATER)
    assert v1.hash != v2.hash, "a version bump must change the content hash"

    # The already-admitted Act still names v1, and its declared cut still excludes v2.
    stored = f.store.get_act(act.hash)
    assert stored is not None
    assert stored.rule_hashes == (v1.hash,)
    assert v2.hash not in stored.rule_hashes
    assert LATER not in stored.registry_cut


def test_rule_not_registered_at_the_declared_cut_is_refused() -> None:
    """Registered later in history is not registered at the cut that authorized.

    History is current here on purpose. PF-13's drift check runs before these
    registration checks, so declaring a stale *history* cut would refuse for the
    wrong reason and prove nothing about PF-21. The decision therefore examines
    all of history and declares the older *Registry* cut -- which the service
    permits, since `registry_cut` need only be an ancestry-closed subset.
    """
    f = build()
    rule = NamedRule("test.allow", 1)
    advance_history(f.store)
    f.store.register("rule", rule.hash, LATER)  # born after the declared Registry cut

    with pytest.raises(CommitError, match="unregistered Rule"):
        CommitGate(f.store).commit(
            f.identity, f.command,
            decision(rule.hash, registry_cut=frozenset({GENESIS}),
                     history_cut=frozenset({GENESIS, LATER})),
            f.context, act_type="ThingCreated")


def test_right_name_wrong_hash_is_refused() -> None:
    """Meaning is the hash. A Rule name is a convenience, never a credential."""
    f = build()
    real = NamedRule("test.allow", 1)
    f.store.register("rule", real.hash, GENESIS)
    impostor = NamedRule("test.allow", 99)  # same name, different content

    with pytest.raises(CommitError, match="unregistered Rule"):
        CommitGate(f.store).commit(
            f.identity, f.command, decision(impostor.hash), f.context, act_type="ThingCreated")


def test_definition_born_after_the_declared_cut_is_refused() -> None:
    """A command type that did not exist at the declared cut cannot govern it."""
    f = build()
    rule = NamedRule("test.allow", 1)
    f.store.register("rule", rule.hash, GENESIS)
    f.store.register("act_type", "LateType", LATER)
    advance_history(f.store)

    with pytest.raises(CommitError, match="unregistered act type"):
        CommitGate(f.store).commit(
            f.identity, f.command,
            decision(rule.hash, registry_cut=frozenset({GENESIS}),
                     history_cut=frozenset({GENESIS, LATER})),
            f.context, act_type="LateType")


def test_one_bad_hash_rejects_the_whole_admission() -> None:
    """No partial attribution: an Act cites every Rule that validated it, or none."""
    f = build()
    good_a = NamedRule("test.allow", 1)
    good_b = NamedRule("test.also_allow", 1)
    missing = NamedRule("test.never_registered", 1)
    f.store.register("rule", good_a.hash, GENESIS)
    f.store.register("rule", good_b.hash, GENESIS)

    with pytest.raises(CommitError, match="unregistered Rule"):
        CommitGate(f.store).commit(
            f.identity, f.command, decision(good_a.hash, good_b.hash, missing.hash),
            f.context, act_type="ThingCreated")

    assert not [act for act in f.store.acts.values() if act.act_type == "ThingCreated"], (
        "a rejected admission must leave no partially attributed Act behind")


def test_registering_another_version_cannot_alter_an_admitted_act() -> None:
    """The Act's content -- and therefore its hash -- is fixed at admission."""
    f = build()
    v1 = NamedRule("test.allow", 1)
    f.store.register("rule", v1.hash, GENESIS)
    act = CommitGate(f.store).commit(
        f.identity, f.command, decision(v1.hash), f.context, act_type="ThingCreated")
    before = (act.hash, act.rule_hashes, act.registry_cut)

    advance_history(f.store)
    for version in (2, 3, 4):
        f.store.register("rule", NamedRule("test.allow", version).hash, LATER)

    stored = f.store.get_act(act.hash)
    assert stored is not None
    assert (stored.hash, stored.rule_hashes, stored.registry_cut) == before


def test_an_empty_rule_set_cannot_buy_a_consequence() -> None:
    """Attribution is mandatory: no Act claims authority nothing granted."""
    f = build()
    with pytest.raises(CommitError, match="at least one Rule"):
        CommitGate(f.store).commit(
            f.identity, f.command, decision(), f.context, act_type="ThingCreated")
