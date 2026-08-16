"""Command lifecycle projection over immutable Acts."""

from __future__ import annotations

from ledger.base import Ledger


class LifecycleService:
    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def status(self, command_hash: str) -> dict[str, object]:
        consequential = self._ledger.get_act_for_command(command_hash)
        return {
            "command_hash": command_hash,
            "consequential_act": consequential.hash if consequential is not None else None,
            "status": "committed" if consequential is not None else "not_committed",
        }
