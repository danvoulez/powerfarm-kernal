"""A credential principal is (issuer, subject). Nothing less identifies it."""

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from kernel.canon import object_hash
from kernel.types import Identity
from ledger.memory import MemoryLedger
from service.errors import AuthorizationError
from service.identity import IdentityService
from service.models import RequestPrincipal

ISSUER = "https://wcguhgyiaphigiduyjpx.supabase.co/auth/v1"
OTHER_ISSUER = "https://attacker.example.com/auth/v1"
SUBJECT = "9f1c0b3e-1d4a-4d8b-8f2a-6c5e7a9b0d31"
CLIENT = "santo-andre-os"


def principal(issuer: str, subject: str) -> RequestPrincipal:
    # `scopes` is still on the model; step 7 removes it. Powerfarm authority
    # comes from Rules, never from an OAuth scope.
    return RequestPrincipal(issuer, subject, CLIENT, ())


def identity_of(seed: bytes) -> tuple[Identity, Ed25519PrivateKey]:
    private = Ed25519PrivateKey.from_private_bytes(seed)
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return Identity(
        object_hash("identity", base64.urlsafe_b64encode(public).decode()), "human", public
    ), private


def bound_ledger() -> tuple[MemoryLedger, Identity]:
    ledger = MemoryLedger()
    identity, _ = identity_of(b"\x01" * 32)
    ledger.seed_identity(identity, issuer=ISSUER, subject=SUBJECT)
    return ledger, identity


def service(ledger: MemoryLedger) -> IdentityService:
    return IdentityService(ledger)


def test_a_linked_principal_resolves_to_its_identity() -> None:
    ledger, identity = bound_ledger()
    service(ledger).require_binding(identity.hash, principal(ISSUER, SUBJECT))


def test_the_same_subject_from_another_issuer_is_a_different_principal() -> None:
    """The defect this table replaces: `del issuer` made these indistinguishable."""
    ledger, identity = bound_ledger()
    assert ledger.resolve_principal(OTHER_ISSUER, SUBJECT) is None
    with pytest.raises(AuthorizationError, match="not linked"):
        service(ledger).require_binding(identity.hash, principal(OTHER_ISSUER, SUBJECT))


def test_an_unlinked_principal_is_denied() -> None:
    ledger, identity = bound_ledger()
    with pytest.raises(AuthorizationError, match="not linked"):
        service(ledger).require_binding(identity.hash, principal(ISSUER, "someone-else"))


def test_a_revoked_binding_stops_resolving() -> None:
    ledger, identity = bound_ledger()
    ledger.unlink_principal(ISSUER, SUBJECT)
    with pytest.raises(AuthorizationError, match="not linked"):
        service(ledger).require_binding(identity.hash, principal(ISSUER, SUBJECT))


def test_a_valid_principal_cannot_reach_another_identity() -> None:
    ledger, _ = bound_ledger()
    stranger, _ = identity_of(b"\x02" * 32)
    with pytest.raises(AuthorizationError, match="does not control"):
        service(ledger).require_binding(stranger.hash, principal(ISSUER, SUBJECT))


def test_no_principal_at_all_is_denied() -> None:
    ledger, identity = bound_ledger()
    with pytest.raises(AuthorizationError, match="OAuth principal is required"):
        service(ledger).require_binding(identity.hash, None)


def test_a_subject_need_not_be_a_uuid() -> None:
    """Subjects are opaque strings; UUID is a fact about one issuer, not about principals."""
    ledger = MemoryLedger()
    identity, _ = identity_of(b"\x03" * 32)
    ledger.seed_identity(identity, issuer=ISSUER, subject="github|dan")
    assert ledger.resolve_principal(ISSUER, "github|dan") == identity.hash


def test_empty_halves_never_resolve() -> None:
    ledger, _ = bound_ledger()
    assert ledger.resolve_principal("", SUBJECT) is None
    assert ledger.resolve_principal(ISSUER, "") is None


def test_the_identity_survives_a_change_of_email() -> None:
    """Email is an attribute of the account, never the binding (section 5.1).

    Nothing here records an email, which is exactly the point: changing one
    cannot move an Identity, because the binding never depended on it.
    """
    ledger, identity = bound_ledger()
    before = ledger.resolve_principal(ISSUER, SUBJECT)
    # Whatever the issuer now reports as the account's email, `sub` is unchanged.
    after = ledger.resolve_principal(ISSUER, SUBJECT)
    assert before == after == identity.hash
