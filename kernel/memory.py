"""Deterministic in-memory adapter used by ceremony and conformance tests."""

from __future__ import annotations

from .types import Act


class MemoryStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.acts: dict[str, Act] = {}
        self.command_index: dict[str, str] = {}
        self.registry: set[tuple[str, str, str]] = set()

    def history_cut(self) -> frozenset[str]:
        children = {parent for act in self.acts.values() for parent in act.parents}
        return frozenset(set(self.acts) - children)

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

    def append_act(self, act: Act) -> None:
        if act.hash in self.acts or act.command_hash in self.command_index:
            raise ValueError("Act occurrence must be unique")
        self.acts[act.hash] = act
        self.command_index[act.command_hash] = act.hash

    def get_act_for_command(self, command_hash: str) -> Act | None:
        act_hash = self.command_index.get(command_hash)
        return self.acts.get(act_hash) if act_hash else None

