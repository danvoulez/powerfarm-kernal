"""The conformance map is checked against the constitution, not against itself.

A law with no test and a law with a test look identical from the outside. This
module makes the difference machine-readable: it reads the normative PF-NN list
out of the specification, requires every one of them to carry a classified
status, and requires each status to carry the evidence that status implies.

The status that earns its keep is ENFORCED_UNPROVEN -- "the mechanism exists but
nothing tries to violate it". Without it, an honest map has only two moves:
claim coverage that does not exist, or pretend the law is unbuilt. Both hide the
same risk, which is the one worth seeing.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = REPO / "Powerfarm System Specification v3.md"
MAP = Path(__file__).with_name("LAW_TEST_MAP.toml")

REQUIRED_EVIDENCE = {
    "IMPLEMENTED": "tests",
    "ENFORCED_UNPROVEN": "enforced_by",
    "DESIGN_ONLY": "blocked_by",
    "NOT_APPLICABLE": "reason",
    "EXTERNAL_CONFORMANCE": "profile",
}


def load_map() -> dict[str, Any]:
    return tomllib.loads(MAP.read_text(encoding="utf-8"))


def normative_laws() -> set[str]:
    """The laws the specification actually declares (section 26)."""
    return set(re.findall(r"\bPF-\d{2}\b", SPEC.read_text(encoding="utf-8")))


def law_entries() -> dict[str, dict[str, Any]]:
    return {key: value for key, value in load_map().items() if isinstance(value, dict)}


def test_every_normative_law_is_classified() -> None:
    """Adding a law to the constitution must force a decision here."""
    unclassified = normative_laws() - set(law_entries())
    assert not unclassified, (
        f"laws in the specification with no conformance status: {sorted(unclassified)}. "
        "Classify them in LAW_TEST_MAP.toml -- silence is not a status."
    )


def test_no_invented_laws() -> None:
    """The map may not classify a law the constitution does not declare."""
    invented = set(law_entries()) - normative_laws()
    assert not invented, f"LAW_TEST_MAP.toml classifies unknown laws: {sorted(invented)}"


@pytest.mark.parametrize("law", sorted(law_entries()))
def test_status_is_recognised_and_carries_its_evidence(law: str) -> None:
    entry = law_entries()[law]
    status = entry.get("status")
    assert status in REQUIRED_EVIDENCE, f"{law}: unknown status {status!r}"
    required = REQUIRED_EVIDENCE[str(status)]
    assert entry.get(required), f"{law}: status {status} requires a non-empty {required!r}"
    if status == "ENFORCED_UNPROVEN":
        assert entry.get("tracked_by"), (
            f"{law}: an unproven law must name the work that will prove it, "
            "or it becomes the trapdoor this map exists to prevent"
        )


@pytest.mark.parametrize("law", sorted(law_entries()))
def test_implemented_laws_cite_tests_that_exist(law: str) -> None:
    """An IMPLEMENTED law whose test was renamed away is worse than an honest gap."""
    entry = law_entries()[law]
    if entry.get("status") != "IMPLEMENTED":
        pytest.skip("only IMPLEMENTED laws must cite executable tests")
    for reference in entry["tests"]:
        path_part, _, test_name = str(reference).partition("::")
        path = REPO / path_part
        assert path.exists(), f"{law}: cites missing test file {path_part}"
        if test_name:
            assert test_name in path.read_text(encoding="utf-8"), (
                f"{law}: {path_part} no longer defines {test_name}"
            )


def test_the_unproven_set_is_frozen() -> None:
    """Both directions matter: a new gap must be deliberate, and closing one
    must update the map rather than leaving a stale claim behind."""
    declared = set(load_map()["frozen_enforced_unproven"])
    actual = {law for law, entry in law_entries().items()
              if entry.get("status") == "ENFORCED_UNPROVEN"}
    assert actual == declared, (
        f"ENFORCED_UNPROVEN drifted. declared={sorted(declared)} actual={sorted(actual)}. "
        "Proving a law means removing it from frozen_enforced_unproven in the same change."
    )
