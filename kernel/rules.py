"""Pure, fail-closed authorization rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .types import Command, Context, Decision, DecisionKind, Identity


class RuleError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuleResult:
    outcome: DecisionKind
    reason: str


class Rule(Protocol):
    hash: str
    context_keys: frozenset[str]

    def evaluate(self, identity: Identity, command: Command, context: Context,
                 history_cut: frozenset[str]) -> RuleResult: ...


def authorize(identity: Identity, command: Command, context: Context,
              history_cut: frozenset[str], registry_cut: frozenset[str],
              rules: tuple[Rule, ...]) -> Decision:
    if identity.hash != command.identity_hash:
        raise RuleError("command identity does not match authenticated identity")
    outcomes: list[RuleResult] = []
    for rule in rules:
        missing = rule.context_keys - context.values.keys()
        if missing:
            raise RuleError(f"rule {rule.hash} requires missing context keys: {sorted(missing)}")
        outcomes.append(rule.evaluate(identity, command, context, history_cut))
    if not outcomes:
        raise RuleError("no applicable rules; authorization fails closed")
    if any(item.outcome is DecisionKind.DENY for item in outcomes):
        outcome = DecisionKind.DENY
    elif any(item.outcome is DecisionKind.REQUIRE_REVIEW for item in outcomes):
        outcome = DecisionKind.REQUIRE_REVIEW
    else:
        outcome = DecisionKind.ALLOW
    return Decision(outcome, history_cut, tuple(rule.hash for rule in rules), registry_cut,
                    "; ".join(item.reason for item in outcomes))

