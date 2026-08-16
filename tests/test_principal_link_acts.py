"""A binding enters history the way every other change does."""

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
from service.errors import ValidationError
from service.models import DERIVED_CONTEXT_KEYS, ActionRequest
from service.principals import PrincipalService

GENESIS = "0" * 64
ISSUER = "https://wcguhgyiaphigiduyjpx.supabase.co/auth/v1"
SUBJECT = "9f1c0b3e-1d4a-4d8b-8f2a-6c5e7a9b0d31"
RULE_HASH = object_hash("rule", {"name": "test.allow", "version": 1})


class AllowRule:
    hash = RULE_HASH
    context_keys: frozenset[str] = frozenset()

    def evaluate(self, identity: Identity, command: object, context: Context,
                 history_cut: frozenset[str]) -> RuleResult:
        return RuleResult(DecisionKind.ALLOW, "test authority allows this")


def build() -> tuple[PrincipalService, MemoryLedger, Identity, Ed25519PrivateKey]:
    ledger = MemoryLedger()
    ledger.acts[GENESIS] = Act(GENESIS, "GenesisClosed", GENESIS, (), frozenset(),
                               "genesis-command", (), frozenset(), (), GENESIS, GENESIS)
    ledger.command_index["genesis-command"] = [GENESIS]
    private = Ed25519PrivateKey.from_private_bytes(b"\x05" * 32)
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    steward = Identity(
        object_hash("identity", base64.urlsafe_b64encode(public).decode()), "service", public)
    ledger.seed_identity(steward)
    for name in ("LinkPrincipal", "RevokePrincipal"):
        ledger.register("command_type", name, GENESIS)
    for name in ("PrincipalLinked", "PrincipalRevoked"):
        ledger.register("act_type", name, GENESIS)
    for key in DERIVED_CONTEXT_KEYS:
        ledger.register("context_type", key, GENESIS)
    ledger.register("rule", "test.allow", GENESIS, entry_hash=RULE_HASH)
    resolver = ConfiguredRuleResolver(
        ledger, rule_names=("test.allow",), static_rules={"test.allow": AllowRule()})
    authority = AuthorityService(ledger, resolver, allow_signed_without_oauth=True)
    return PrincipalService(authority, ledger), ledger, steward, private


def request(ledger: MemoryLedger, steward: Identity, private: Ed25519PrivateKey,
            command_type: str, act_type: str, payload: dict[str, object],
            nonce: str) -> ActionRequest:
    payload_hash = object_hash("payload", payload)
    ledger.put_object(payload_hash, canonicalize(payload), "payload")
    command = propose_command(command_type, steward.hash, payload_hash, (GENESIS,), nonce, private)
    return ActionRequest(
        command_type=command_type, identity_hash=steward.hash, payload_hash=payload_hash,
        parents=(GENESIS,), nonce=nonce,
        signature=base64.urlsafe_b64encode(command.signature).decode().rstrip("="),
        context_values={}, context_types={}, act_type=act_type, payload=payload)


def test_linking_produces_an_act_and_the_projection_follows_it() -> None:
    service, ledger, steward, private = build()
    assert ledger.resolve_principal(ISSUER, SUBJECT) is None

    _, act = service.link(request(
        ledger, steward, private, "LinkPrincipal", "PrincipalLinked",
        {"issuer": ISSUER, "subject": SUBJECT, "identity_hash": steward.hash}, "link-1"))

    assert act.act_type == "PrincipalLinked"
    assert ledger.get_act(act.hash) is not None, "the binding is admitted by an Act"
    assert ledger.resolve_principal(ISSUER, SUBJECT) == steward.hash


def test_revoking_produces_its_own_act() -> None:
    service, ledger, steward, private = build()
    service.link(request(
        ledger, steward, private, "LinkPrincipal", "PrincipalLinked",
        {"issuer": ISSUER, "subject": SUBJECT, "identity_hash": steward.hash}, "link-1"))

    _, revoked = service.revoke(request(
        ledger, steward, private, "RevokePrincipal", "PrincipalRevoked",
        {"issuer": ISSUER, "subject": SUBJECT}, "revoke-1"))

    assert revoked.act_type == "PrincipalRevoked"
    assert ledger.resolve_principal(ISSUER, SUBJECT) is None
    # Revocation withdraws the binding; it never erases that it existed.
    assert len(ledger.acts) == 3


def test_the_wrong_command_type_cannot_link() -> None:
    service, ledger, steward, private = build()
    with pytest.raises(ValidationError, match="requires the LinkPrincipal command type"):
        service.link(request(
            ledger, steward, private, "RevokePrincipal", "PrincipalLinked",
            {"issuer": ISSUER, "subject": SUBJECT, "identity_hash": steward.hash}, "x-1"))


def test_an_incomplete_payload_cannot_link() -> None:
    service, ledger, steward, private = build()
    with pytest.raises(ValidationError, match="identity_hash is required"):
        service.link(request(
            ledger, steward, private, "LinkPrincipal", "PrincipalLinked",
            {"issuer": ISSUER, "subject": SUBJECT}, "x-2"))
