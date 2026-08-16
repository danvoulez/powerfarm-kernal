"""Reconstruct the exact content references behind a committed Act."""

from __future__ import annotations

import json
from typing import cast

from ledger.base import Ledger, ObjectRecord

from .errors import NotFoundError
from .models import act_to_dict


def _decode(record: ObjectRecord | None) -> object | None:
    if record is None:
        return None
    try:
        return cast(object, json.loads(record.canon.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"hash": record.hash, "kind": record.kind, "binary": True}


class ExplainService:
    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def action(self, act_hash: str) -> dict[str, object]:
        act = self._ledger.get_act(act_hash)
        if act is None:
            raise NotFoundError("Act not found")
        return {
            "act": act_to_dict(act),
            "command": _decode(self._ledger.get_object(act.command_hash)),
            "context": _decode(self._ledger.get_object(act.context_hash)),
            "payload": _decode(self._ledger.get_object(act.payload_hash)),
        }
