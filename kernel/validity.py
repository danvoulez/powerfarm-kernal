"""Typed decision-validity evaluation for the declared admission cut."""

from __future__ import annotations

from dataclasses import dataclass

from .types import DecisionValidityDisposition

DECLARED_DECISION_CUT_RULE = "declared-decision-cut"


@dataclass(frozen=True, slots=True)
class DecisionValidity:
    rule_hash: str
    disposition: DecisionValidityDisposition
    reason: str


def evaluate_declared_decision_cut(
    rule_hash: str,
    declared_cut: frozenset[str],
    admission_cut: frozenset[str],
) -> DecisionValidity:
    """Evaluate CR-1 v1.

    Genesis admits survival rung 0 only: the decision remains valid exactly
    when admission sees the same history cut.  ``COMMIT_REGARDLESS`` exists in
    the typed domain but is intentionally unreachable in this implementation.
    """

    if not rule_hash:
        raise ValueError("decision-validity Rule hash is required")
    if admission_cut == declared_cut:
        return DecisionValidity(
            rule_hash,
            DecisionValidityDisposition.VALID,
            "declared decision cut is intact",
        )
    return DecisionValidity(
        rule_hash,
        DecisionValidityDisposition.REAUTHORIZE,
        "history advanced after authorization; reauthorization required",
    )
