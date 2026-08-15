"""Pinned JCS (RFC 8785) canonicalization and domain-separated object identities.

The canonical form is JSON Canonicalization Scheme: UTF-8 in, deterministic bytes
out.  Browsers can verify Powerfarm hashes with no codec beyond JSON + SHA-256.

Constitutional caveats (spec v3.1 section 10.1):
  * floats are legal but treacherous -- exact quantities use integer minor units;
  * binary payloads ride as base64url strings, never raw bytes;
  * every implementation MUST pass the golden vector suite byte-exactly (PF-22).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

import rfc8785

type CanonValue = (
    None | bool | int | float | str | Sequence["CanonValue"] | Mapping[str, "CanonValue"]
)


class CanonicalizationError(ValueError):
    pass


def canonicalize(value: CanonValue) -> bytes:
    """Encode *value* as RFC 8785 canonical JSON (UTF-8)."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        value = list(value)
    try:
        canon = rfc8785.dumps(value)
    except (TypeError, ValueError) as error:
        raise CanonicalizationError(str(error)) from error
    if isinstance(canon, str):
        return canon.encode("utf-8")
    if isinstance(canon, (bytes, bytearray)):
        return bytes(canon)
    raise CanonicalizationError(f"unexpected JCS encoder output: {type(canon).__name__}")


def object_hash(kind: str, value: CanonValue, version: str = "v1") -> str:
    """SHA-256 over the domain tag and the canonical UTF-8 form."""
    if not kind or ":" in kind or not version:
        raise ValueError("kind and version must form an unambiguous domain tag")
    tag = f"powerfarm:{kind}:{version}".encode()
    return hashlib.sha256(tag + canonicalize(value)).hexdigest()
