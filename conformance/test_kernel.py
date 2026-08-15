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
from kernel.types import Act, Context, DecisionKind, Identity


@dataclass(frozen=True)
class Allow:
    hash: str = "rule-v1"
    context_keys: frozenset[str] = frozenset({"request.origin"})

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        return RuleResult(DecisionKind.ALLOW, "test authority grants this command")


def setup_case() -> tuple[MemoryStore, Identity, object, Context, object]:
    store = MemoryStore()
    genesis = "0" * 64
    store.acts[genesis] = Act(genesis, "GenesisClosed", genesis, (), frozenset(), "genesis-command",
                              (), frozenset(), genesis, genesis)
    store.register("command_type", "CreateThing", genesis)
    store.register("act_type", "ThingCreated", genesis)
    payload = {"name": "one"}
    payload_hash = object_hash("payload", payload)
    store.put_object(payload_hash, canonicalize(payload), "payload")
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    identity = Identity(object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public)
    command = propose_command("CreateThing", identity.hash, payload_hash, (genesis,), "n-1", private)
    context = Context({"request.origin": "test"}, {"request.origin": "origin-v1"})
    decision = authorize(identity, command, context, store.history_cut(), frozenset({genesis}), (Allow(),))
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
