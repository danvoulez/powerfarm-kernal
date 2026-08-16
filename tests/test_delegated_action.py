"""Authentication, agency and authority are three questions, not one."""

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agent.tools import propose_command
from kernel.canon import canonicalize, object_hash
from kernel.rules import RuleResult
from kernel.types import Act, Context, DecisionKind, Identity
from ledger.memory import MemoryLedger
from service.authority import AuthorityService, ConfiguredRuleResolver
from service.errors import AuthorizationError, ValidationError
from service.models import (
    DERIVED_CONTEXT_KEYS,
    PERFORMED_BY,
    REQUESTED_BY,
    ActionRequest,
    RequestPrincipal,
)

GENESIS = "0" * 64
ISSUER = "https://wcguhgyiaphigiduyjpx.supabase.co/auth/v1"
SUBJECT = "9f1c0b3e-1d4a-4d8b-8f2a-6c5e7a9b0d31"
RULE_HASH = object_hash("rule", {"name": "test.delegation", "version": 1})


class DelegationRule:
    """Acting for someone else is authorized, never merely tolerated."""

    hash = RULE_HASH
    context_keys = frozenset({REQUESTED_BY, PERFORMED_BY})

    def __init__(self, *, permitted: frozenset[tuple[str, str]] = frozenset()) -> None:
        self.permitted = permitted

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        requester = str(context.values[REQUESTED_BY])
        performer = str(context.values[PERFORMED_BY])
        if requester == performer:
            return RuleResult(DecisionKind.ALLOW, "acting on its own behalf")
        if (performer, requester) in self.permitted:
            return RuleResult(DecisionKind.ALLOW, "delegation is authorized")
        return RuleResult(DecisionKind.DENY, "no authority to act for this requester")


def keypair(seed: bytes) -> tuple[Identity, Ed25519PrivateKey]:
    private = Ed25519PrivateKey.from_private_bytes(seed)
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return Identity(
        object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public
    ), private


def build(*, permitted: frozenset[tuple[str, str]] = frozenset()) -> tuple[
    AuthorityService, MemoryLedger, Identity, Identity, Ed25519PrivateKey, str
]:
    ledger = MemoryLedger()
    ledger.acts[GENESIS] = Act(GENESIS, "GenesisClosed", GENESIS, (), frozenset(),
                               "genesis-command", (), frozenset(), (), GENESIS, GENESIS)
    ledger.command_index["genesis-command"] = [GENESIS]
    human, _ = keypair(b"\x01" * 32)
    raw_service, service_key = keypair(b"\x02" * 32)
    platform = Identity(raw_service.hash, "service", raw_service.public_key)
    ledger.seed_identity(human, issuer=ISSUER, subject=SUBJECT)
    ledger.seed_identity(platform)
    ledger.register("command_type", "CreateThing", GENESIS)
    ledger.register("act_type", "ThingCreated", GENESIS)
    ledger.register("context_type", "request.origin", GENESIS)
    for key in DERIVED_CONTEXT_KEYS:
        ledger.register("context_type", key, GENESIS)
    ledger.register("rule", "test.delegation", GENESIS, entry_hash=RULE_HASH)
    payload_hash = object_hash("payload", {"name": "one"})
    ledger.put_object(payload_hash, canonicalize({"name": "one"}), "payload")
    resolver = ConfiguredRuleResolver(
        ledger, rule_names=("test.delegation",),
        static_rules={"test.delegation": DelegationRule(permitted=permitted)})
    return AuthorityService(ledger, resolver), ledger, human, platform, service_key, payload_hash


def action(platform: Identity, key: Ed25519PrivateKey, payload_hash: str,
           extra: dict[str, str] | None = None) -> ActionRequest:
    command = propose_command("CreateThing", platform.hash, payload_hash, (GENESIS,), "n-1", key)
    values: dict[str, object] = {"request.origin": "test"}
    types = {"request.origin": "request.origin"}
    for name, value in (extra or {}).items():
        values[name] = value
        types[name] = name
    return ActionRequest(
        command_type="CreateThing", identity_hash=platform.hash, payload_hash=payload_hash,
        parents=(GENESIS,), nonce="n-1",
        signature=base64.urlsafe_b64encode(command.signature).decode().rstrip("="),
        context_values=values, context_types=types, act_type="ThingCreated")


def principal() -> RequestPrincipal:
    return RequestPrincipal(ISSUER, SUBJECT, "santo-andre-os")


def test_a_caller_cannot_assert_who_requested() -> None:
    """A body claiming requested_by is refused, not merged."""
    service, _, human, platform, key, payload_hash = build()
    forged = action(platform, key, payload_hash, extra={REQUESTED_BY: human.hash})
    with pytest.raises(ValidationError, match="may not be supplied by the caller"):
        service.evaluate(forged, principal())


def test_the_requester_is_resolved_from_the_token_not_the_body() -> None:
    """The body never mentions the human; the token is what puts them there."""
    service, _, human, platform, key, payload_hash = build()
    request = action(platform, key, payload_hash)
    assert REQUESTED_BY not in request.context_values

    evaluated = service.evaluate(request, principal())
    assert evaluated.context.values[REQUESTED_BY] == human.hash
    assert evaluated.context.values[PERFORMED_BY] == platform.hash


def test_an_unauthorized_delegation_cannot_reach_an_act() -> None:
    """evaluate() reports the decision; the Gate is what refuses consequence."""
    service, _, _, platform, key, payload_hash = build(permitted=frozenset())
    request = action(platform, key, payload_hash)
    assert service.evaluate(request, principal()).decision.outcome is DecisionKind.DENY
    with pytest.raises(AuthorizationError, match="requires allow"):
        service.commit(request, principal())


def test_delegation_requires_authority_not_mere_difference() -> None:
    """requester != performer is a question for Rules, never a pass from code."""
    service, _, human, platform, key, payload_hash = build()
    denied = service.evaluate(action(platform, key, payload_hash), principal())
    assert denied.decision.outcome is DecisionKind.DENY

    allowed_service, _, human2, platform2, key2, payload2 = build(
        permitted=frozenset({(platform.hash, human.hash)}))
    granted = allowed_service.evaluate(action(platform2, key2, payload2), principal())
    assert granted.decision.outcome is DecisionKind.ALLOW
    assert granted.context.values[REQUESTED_BY] == human2.hash
    assert granted.context.values[PERFORMED_BY] == platform2.hash


def test_the_act_records_both_who_asked_and_who_performed() -> None:
    service, _ledger, human, platform, key, payload_hash = build(
        permitted=frozenset({(keypair(b"\x02" * 32)[0].hash, keypair(b"\x01" * 32)[0].hash)}))
    evaluated, act = service.commit(action(platform, key, payload_hash), principal())
    assert act.identity_hash == platform.hash, "the Act attributes the signature honestly"
    assert evaluated.context.values[REQUESTED_BY] == human.hash
    # The association is content-addressed: the Context hash is in the Act hash.
    assert act.context_hash == evaluated.context.hash


def test_a_revoked_binding_denies_even_a_valid_signature() -> None:
    service, ledger, _human, platform, key, payload_hash = build(
        permitted=frozenset({(keypair(b"\x02" * 32)[0].hash, keypair(b"\x01" * 32)[0].hash)}))
    ledger.unlink_principal(ISSUER, SUBJECT)
    with pytest.raises(AuthorizationError, match="not linked"):
        service.evaluate(action(platform, key, payload_hash), principal())
