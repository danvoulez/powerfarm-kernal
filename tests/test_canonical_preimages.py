"""R-26 golden vectors for the pre-Genesis content-identity corrections."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kernel.canon import object_hash
from kernel.types import Context, DecisionValidityDisposition, Relation
from kernel.validity import evaluate_declared_decision_cut

VECTORS = json.loads(
    (
        Path(__file__).resolve().parent.parent
        / "conformance"
        / "golden-vectors"
        / "preimages.json"
    ).read_text(encoding="utf-8")
)


def test_r26_preimage_hashes_are_frozen() -> None:
    for name, tag in (("context", "context"), ("relation", "relation"), ("act", "act")):
        vector = VECTORS[name]
        assert object_hash(tag, vector["value"]) == vector["hash"]
        assert vector["hash"] != vector["legacy_hash"]


def test_relation_identity_binds_the_definition_hash() -> None:
    value = VECTORS["relation"]["value"]
    relation = Relation(
        value["from"], value["to"], value["relation_type_hash"], value["payload"]
    )
    assert relation.hash == VECTORS["relation"]["hash"]


def test_context_type_names_are_no_longer_valid_preimage_content() -> None:
    with pytest.raises(ValueError, match="definition hashes"):
        Context({"request.origin": "test"}, {"request.origin": "request.origin"})


def test_cr1_v1_has_a_distinct_typed_domain() -> None:
    rule_hash = VECTORS["act"]["value"]["validity_rule_hash"]
    declared = frozenset({"0" * 64})
    intact = evaluate_declared_decision_cut(rule_hash, declared, declared)
    advanced = evaluate_declared_decision_cut(
        rule_hash, declared, frozenset({"0" * 64, "1" * 64})
    )

    assert intact.disposition is DecisionValidityDisposition.VALID
    assert advanced.disposition is DecisionValidityDisposition.REAUTHORIZE
    assert DecisionValidityDisposition.COMMIT_REGARDLESS not in {
        intact.disposition,
        advanced.disposition,
    }
