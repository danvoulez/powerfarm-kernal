import pytest

from kernel.canon import CanonicalizationError, canonicalize, object_hash


def test_rfc8949_vectors_and_map_order() -> None:
    assert canonicalize(0) == bytes.fromhex("00")
    assert canonicalize(-1) == bytes.fromhex("20")
    assert canonicalize({"b": 1, "a": 2}) == bytes.fromhex("a2616102616201")
    assert object_hash("test", {"a": 1}) == object_hash("test", {"a": 1})
    assert object_hash("test", {}) != object_hash("other", {})


def test_unsupported_values_fail_loud() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize(1.5)  # type: ignore[arg-type]

