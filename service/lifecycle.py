"""Command lifecycle projection over immutable Acts."""

from __future__ import annotations

from kernel.types import LIFECYCLE_ACT_TYPES, Act
from ledger.base import Ledger

_TERMINAL = {"CommandRejected", "CommandDenied", "CommandSuperseded", "CommandExpired"}


class LifecycleService:
    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def status(self, command_hash: str) -> dict[str, object]:
        acts = self._ledger.get_acts_for_command(command_hash)
        stages = [act for act in acts if act.act_type in LIFECYCLE_ACT_TYPES]
        consequential = [act for act in acts if act.act_type not in LIFECYCLE_ACT_TYPES]
        recorded = {act.act_type for act in stages}
        return {
            "command_hash": command_hash,
            "lifecycle": [
                {"act_type": act.act_type, "act": act.hash, "claimed_when": act.claimed_when}
                for act in stages
            ],
            "consequential_act": consequential[0].hash if consequential else None,
            "status": self._status(recorded, bool(consequential)),
        }

    def trajectory(self, command_hash: str) -> dict[str, object]:
        """The factual authorization trajectory of a Command.

        `get_acts_for_command` answers *ownership*: the Acts this Command
        produced. This answers *participation*, which is a different question --
        the Reviewer's `AuthorizationReviewed` belongs to their own Review
        Command and merely takes part here, reached through the `auth_chain` of
        the resolution rather than by owning the Command (sections 8.1, 25).

        Reconstruction only. It confers no authority and decides nothing.
        """
        owned = self._ledger.get_acts_for_command(command_hash)
        participating: dict[str, Act] = {}
        for act in owned:
            for link in act.auth_chain:
                if any(link == other.hash for other in owned):
                    continue
                linked = self._ledger.get_act(link)
                if linked is not None:
                    participating[linked.hash] = linked
        return {
            "command_hash": command_hash,
            "owned": [self._node(act) for act in owned],
            "participating": [
                self._node(act) | {"owned_by_command": act.command_hash}
                for act in participating.values()
            ],
            "status": self.status(command_hash)["status"],
        }

    @staticmethod
    def _node(act: Act) -> dict[str, object]:
        return {"act": act.hash, "act_type": act.act_type, "claimed_when": act.claimed_when}

    @staticmethod
    def _status(recorded: set[str], committed: bool) -> str:
        """Merely existing never implies the intended change occurred (6.1)."""
        if committed:
            return "committed"
        if recorded & _TERMINAL:
            return min(recorded & _TERMINAL)
        # ReviewRequested blocks the Command until AuthorizationResolved (8.1).
        if "ReviewRequested" in recorded and "AuthorizationResolved" not in recorded:
            return "pending_review"
        if recorded:
            return "pending"
        return "not_submitted"
