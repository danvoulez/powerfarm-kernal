import copy
import json
from collections import Counter
from pathlib import Path
from typing import cast

import pytest

from genesis.material import (
    DEFAULT_INPUT,
    GENESIS_OUTPUT,
    RATIFICATIONS,
    REGISTRY_OUTPUT,
    MaterialError,
    build_genesis_manifest,
    build_registry_manifest,
    generate,
    material_blockers,
)
from kernel.canon import CanonValue, object_hash


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def test_candidate_registry_is_explicit_hashed_and_reproducible() -> None:
    registry = load(REGISTRY_OUTPUT)
    definitions = cast(list[dict[str, object]], registry["definitions"])

    assert registry["definition_count"] == len(definitions) == 102
    assert registry["counts_by_kind"] == {
        "act_type": 34,
        "command_type": 18,
        "context_type": 14,
        "mandate": 2,
        "office": 1,
        "projector": 7,
        "relation_type": 18,
        "rule": 8,
    }
    assert Counter(str(item["definition_hash"]) for item in definitions).most_common(1)[0][1] == 1
    for entry in definitions:
        definition = cast(dict[str, CanonValue], entry["definition"])
        assert entry["definition_hash"] == object_hash("registry", definition)
        assert len(definition) > 3, "M2 may not regress to a kind/name/version shell"

    without_hash = cast(dict[str, CanonValue], dict(registry))
    manifest_hash = without_hash.pop("manifest_hash")
    assert manifest_hash == object_hash("registry_manifest", without_hash)
    assert generate() == (REGISTRY_OUTPUT.read_bytes(), GENESIS_OUTPUT.read_bytes())


def test_frozen_registry_corrections_are_present() -> None:
    registry = load(REGISTRY_OUTPUT)
    entries = cast(list[dict[str, object]], registry["definitions"])
    by_key = {
        (entry["definition"]["kind"], entry["definition"]["name"]): entry["definition"]
        for entry in entries
    }

    assert ("rule", "genesis.root_authority") not in by_key
    assert ("rule", "root-mandate") in by_key
    assert ("context_type", "cut.declared") in by_key
    assert ("context_type", "cut.advance") in by_key
    assert ("context_type", "decision.read_set") not in by_key
    assert by_key[("act_type", "PrincipalLinked")]["companion"] == {
        "cardinality": "exactly_one",
        "writer": "principal_bindings",
    }


def test_every_registry_cross_reference_resolves_inside_the_candidate() -> None:
    registry = load(REGISTRY_OUTPUT)
    entries = cast(list[dict[str, object]], registry["definitions"])
    hashes = {str(entry["definition_hash"]) for entry in entries}
    for entry in entries:
        definition = cast(dict[str, object], entry["definition"])
        kind = definition["kind"]
        if kind == "rule":
            for context_ref in cast(list[dict[str, str]], definition["context_keys"]):
                assert context_ref["definition_hash"] in hashes
            assert set(cast(list[str], definition["applicability"])) <= hashes
        elif kind == "projector":
            assert set(cast(list[str], definition["inputs"])) <= hashes
        elif kind == "office":
            assert set(cast(list[str], definition["mandate_kinds"])) <= hashes
            assert definition["succession_rule"] in hashes
            recovery = definition["recovery_rule"]
            assert recovery is None or recovery in hashes


def test_genesis_manifest_binds_registry_and_its_own_exact_content() -> None:
    registry = load(REGISTRY_OUTPUT)
    genesis = load(GENESIS_OUTPUT)

    assert genesis["registry_manifest_hash"] == registry["manifest_hash"]
    without_hash = cast(dict[str, CanonValue], dict(genesis))
    manifest_hash = without_hash.pop("manifest_hash")
    assert manifest_hash == object_hash("genesis_manifest", without_hash)


def test_candidate_is_loudly_blocked_not_mislabeled_final() -> None:
    source = load(DEFAULT_INPUT)
    blockers = material_blockers(source)
    genesis = build_genesis_manifest(source, build_registry_manifest(source))

    assert genesis["ratification_status"] == "blocked"
    assert tuple(genesis["blockers"]) == blockers
    assert "D-Genesis-04 is not RATIFIED" in blockers
    assert "Identity root is absent" in blockers
    assert "Identity director is absent" in blockers


def test_ready_gate_requires_ratification_real_public_keys_and_custody() -> None:
    source = copy.deepcopy(load(DEFAULT_INPUT))
    source["constitution_ratified"] = True
    source["ratifications"] = {decision: "RATIFIED" for decision in RATIFICATIONS}
    identities: dict[str, object] = {}
    for number, name in enumerate((
        "root", "director", "organization", "constitutional_reviewer_1",
        "constitutional_reviewer_2", "constitutional_reviewer_3",
    ), start=1):
        # Valid, distinct 32-byte public material. Tests never create private keys.
        import base64

        key = base64.urlsafe_b64encode(bytes([number]) * 32).decode().rstrip("=")
        identities[name] = {
            "kind": "organization" if name == "organization" else "human",
            "public_keys": [key],
            "custody": {"method": "test fixture; not ceremony custody"},
        }
    source["identities"] = identities

    assert material_blockers(source) == ()
    genesis = build_genesis_manifest(source, build_registry_manifest(source))
    assert genesis["ratification_status"] == "ready"
    assert genesis["blockers"] == []


def test_private_key_material_is_rejected() -> None:
    source = copy.deepcopy(load(DEFAULT_INPUT))
    source["identities"] = {
        "root": {"public_keys": ["x"], "custody": {"method": "x"}, "seed": "secret"}
    }
    with pytest.raises(MaterialError, match="private key material is forbidden"):
        material_blockers(source)
