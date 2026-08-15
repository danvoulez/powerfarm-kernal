import hashlib
import json
from pathlib import Path

import pytest

from kernel.canon import CanonicalizationError, canonicalize, object_hash

VECTORS = Path(__file__).resolve().parent.parent / "conformance" / "golden-vectors"
MANIFEST = json.loads((VECTORS / "manifest.json").read_text(encoding="utf-8"))


def test_rfc8785_golden_vectors_byte_exact() -> None:
    """PF-22: every vector must canonicalize byte-exactly and hash correctly."""
    assert len(MANIFEST["vectors"]) == 6
    for vector in MANIFEST["vectors"]:
        data = json.loads((VECTORS / vector["input"]).read_text(encoding="utf-8"))
        expected = bytes.fromhex(
            (VECTORS / vector["expected_hex"]).read_text().replace("\n", " ")
        )
        canon = canonicalize(data)
        assert canon == expected, f"{vector['name']}: canonical bytes diverged"
        assert (
            hashlib.sha256(canon).hexdigest() == vector["canonical_utf8_sha256"]
        ), f"{vector['name']}: untagged hash diverged"
        assert (
            hashlib.sha256(b"powerfarm:test:v1" + canon).hexdigest()
            == vector["domain_tagged_example"]
        ), f"{vector['name']}: domain-tagged hash diverged"


def test_canon_is_deterministic_and_domain_separated() -> None:
    assert canonicalize({"b": 1, "a": 2}) == canonicalize({"a": 2, "b": 1})
    assert object_hash("test", {"a": 1}) == object_hash("test", {"a": 1})
    assert object_hash("test", {}) != object_hash("other", {})


def test_unsupported_values_fail_loud() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        object_hash("bad:tag", {})
