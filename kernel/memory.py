"""Deterministic in-memory adapter used by ceremony and conformance tests."""

from __future__ import annotations

from .types import Act


class MemoryStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.acts: dict[str, Act] = {}
        # A Command's lifecycle is many Acts (spec v3 section 6.1), so this index
        # is one-to-many. It is a trajectory index, not an identity: the Command
        # is the subject whose trajectory we reconstruct, never the occurrence.
        self.command_index: dict[str, list[str]] = {}
        self.registry: set[tuple[str, str, str]] = set()

    def history_cut(self) -> frozenset[str]:
        # A cut is closed under ancestry (spec v3 section 10.2): the full known
        # history is trivially closed, unlike the old frontier-only computation.
        return frozenset(self.acts)

    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool:
        return any(k == kind and n == name and born in cut for k, n, born in self.registry)

    def register(self, kind: str, name: str, born_at: str) -> None:
        self.registry.add((kind, name, born_at))

    def has_object(self, object_hash: str) -> bool:
        return object_hash in self.objects

    def has_act(self, act_hash: str) -> bool:
        return act_hash in self.acts

    def put_object(self, object_hash: str, canon: bytes, kind: str) -> None:
        old = self.objects.get(object_hash)
        if old is not None and old != (canon, kind):
            raise ValueError("CAS collision")
        self.objects[object_hash] = (canon, kind)

    def object_canon(self, object_hash: str) -> bytes | None:
        found = self.objects.get(object_hash)
        return found[0] if found is not None else None

    def append_act(self, act: Act) -> None:
        # Uniqueness is on the Act's own hash, never on its Command (PF-23).
        if act.hash in self.acts:
            raise ValueError("Act occurrence must be unique")
        self.acts[act.hash] = act
        self.command_index.setdefault(act.command_hash, []).append(act.hash)

    def commit_act(self, act: Act, canon: bytes, command_type: str) -> Act:
        del command_type
        existing = self.acts.get(act.hash)
        if existing is not None:
            return existing
        old = self.objects.get(act.hash)
        if old is not None and old != (canon, "act"):
            raise ValueError("CAS collision")
        self.objects[act.hash] = (canon, "act")
        try:
            self.append_act(act)
        except Exception:
            if old is None:
                self.objects.pop(act.hash, None)
            raise
        return act

    def get_act(self, act_hash: str) -> Act | None:
        return self.acts.get(act_hash)

    def get_acts_for_command(self, command_hash: str) -> tuple[Act, ...]:
        """Every Act referencing this Command -- its whole lifecycle (PF-15)."""
        return tuple(self.acts[h] for h in self.command_index.get(command_hash, ()))
