"""Pinned canonical CBOR encoding and domain-separated object identities.

Only the deliberately small data model accepted by the kernel is encoded.  Rejecting
floats and implicit object conversion avoids language-dependent identities.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import TypeAlias

CanonValue: TypeAlias = None | bool | int | bytes | str | Sequence["CanonValue"] | Mapping[str, "CanonValue"]


class CanonicalizationError(ValueError):
    pass


def _head(major: int, value: int) -> bytes:
    if value < 0:
        raise CanonicalizationError("CBOR length cannot be negative")
    if value < 24:
        return bytes([(major << 5) | value])
    for marker, width in ((24, 1), (25, 2), (26, 4), (27, 8)):
        if value < 1 << (width * 8):
            return bytes([(major << 5) | marker]) + value.to_bytes(width, "big")
    raise CanonicalizationError("integer exceeds the supported 64-bit CBOR range")


def canonicalize(value: CanonValue) -> bytes:
    """Encode *value* using RFC 8949 deterministic (preferred) serialization."""
    if value is None:
        return b"\xf6"
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if isinstance(value, int):
        return _head(0, value) if value >= 0 else _head(1, -1 - value)
    if isinstance(value, bytes):
        return _head(2, len(value)) + value
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return _head(3, len(encoded)) + encoded
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("map keys must be strings")
        pairs = [(canonicalize(key), canonicalize(item)) for key, item in value.items()]
        pairs.sort(key=lambda pair: (len(pair[0]), pair[0]))
        return _head(5, len(pairs)) + b"".join(key + item for key, item in pairs)
    if isinstance(value, Sequence):
        values = [canonicalize(item) for item in value]
        return _head(4, len(values)) + b"".join(values)
    raise CanonicalizationError(f"unsupported canonical value: {type(value).__name__}")


def object_hash(kind: str, value: CanonValue, version: str = "v1") -> str:
    if not kind or ":" in kind or not version:
        raise ValueError("kind and version must form an unambiguous domain tag")
    tag = f"powerfarm:{kind}:{version}".encode()
    return hashlib.sha256(tag + canonicalize(value)).hexdigest()

