"""What a presented token must prove before any Powerfarm question is asked."""

import time
from typing import Any

import anyio
import jwt
from cryptography.hazmat.primitives.asymmetric import ec

from protocol.mcp.auth import JWTSettings, SupabaseJWTVerifier
from service.models import RequestPrincipal

ISSUER = "https://wcguhgyiaphigiduyjpx.supabase.co/auth/v1"
RESOURCE = "https://api.powerfarm.app/mcp"
CLIENT = "santo-andre-os"
SUBJECT = "9f1c0b3e-1d4a-4d8b-8f2a-6c5e7a9b0d31"

SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())


class StubJWKS:
    """Stands in for the issuer's published keys; the signature check is real."""

    def __init__(self, key: Any) -> None:
        self.key = key

    def get_signing_key_from_jwt(self, token: str) -> "StubJWKS":
        del token
        return self


def verifier(*, clients: frozenset[str] = frozenset({CLIENT}),
             audience: str = RESOURCE) -> SupabaseJWTVerifier:
    settings = JWTSettings(ISSUER, audience, "https://unused.invalid/jwks.json",
                           ("ES256",), RESOURCE, clients)
    built = SupabaseJWTVerifier.__new__(SupabaseJWTVerifier)
    built._settings = settings
    built._jwks = StubJWKS(SIGNING_KEY.public_key())
    return built


def token(**overrides: Any) -> str:
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "sub": SUBJECT,
        "aud": RESOURCE,
        "client_id": CLIENT,
        "exp": int(time.time()) + 300,
    }
    claims.update(overrides)
    for key, value in list(claims.items()):
        if value is None:
            del claims[key]
    return jwt.encode(claims, SIGNING_KEY, algorithm="ES256")


def verify(built: SupabaseJWTVerifier, raw: str) -> Any:
    return anyio.run(built.verify_token, raw)


def test_a_well_formed_token_is_accepted() -> None:
    accepted = verify(verifier(), token())
    assert accepted is not None
    assert accepted.subject == SUBJECT
    assert accepted.client_id == CLIENT
    assert accepted.scopes == [], "no scope is read, so none can be trusted"


def test_a_wrong_issuer_is_refused() -> None:
    assert verify(verifier(), token(iss="https://attacker.example.com/auth/v1")) is None


def test_a_wrong_audience_is_refused() -> None:
    """A token minted for another resource cannot be replayed against this one."""
    assert verify(verifier(), token(aud="https://api.other-kernel.app/mcp")) is None


def test_an_expired_token_is_refused() -> None:
    assert verify(verifier(), token(exp=int(time.time()) - 1)) is None


def test_a_token_signed_by_another_key_is_refused() -> None:
    stranger = jwt.encode(
        {"iss": ISSUER, "sub": SUBJECT, "aud": RESOURCE, "client_id": CLIENT,
         "exp": int(time.time()) + 300},
        ec.generate_private_key(ec.SECP256R1()), algorithm="ES256")
    assert verify(verifier(), stranger) is None


def test_a_token_without_a_client_is_refused_not_invented() -> None:
    """The regression this replaces: a missing client_id was filled in from `aud`.

    Every such token then arrived wearing the audience as its name, so tokens
    from unrelated callers were indistinguishable from one another.
    """
    assert verify(verifier(), token(client_id=None)) is None


def test_an_undeclared_client_is_refused() -> None:
    assert verify(verifier(), token(client_id="some-other-app")) is None


def test_azp_is_accepted_as_the_client_claim() -> None:
    accepted = verify(verifier(), token(client_id=None, azp=CLIENT))
    assert accepted is not None and accepted.client_id == CLIENT


def test_an_empty_client_allowlist_accepts_any_presented_client() -> None:
    """Development default. Production declares its clients; absence still fails."""
    open_verifier = verifier(clients=frozenset())
    assert verify(open_verifier, token(client_id="anything")) is not None
    assert verify(open_verifier, token(client_id=None)) is None


def test_the_principal_carries_no_scopes() -> None:
    assert not hasattr(RequestPrincipal(ISSUER, SUBJECT, CLIENT), "scopes")


def test_a_missing_subject_is_refused() -> None:
    """`sub` is required at decode, so its absence never reaches the binding lookup."""
    assert verify(verifier(), token(sub=None)) is None
