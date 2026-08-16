"""Deterministic in-memory adapter used by ceremony and conformance tests."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from .canon import CanonValue, object_hash
from .types import Act, Companion


class MemoryStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.acts: dict[str, Act] = {}
        # A Command's lifecycle is many Acts (spec v3 section 6.1), so this index
        # is one-to-many. It is a trajectory index, not an identity: the Command
        # is the subject whose trajectory we reconstruct, never the occurrence.
        self.command_index: dict[str, list[str]] = {}
        self.registry: set[tuple[str, str, int, str, str]] = set()
        self.registry_definitions: dict[str, CanonValue] = {}

    def history_cut(self) -> frozenset[str]:
        # A cut is closed under ancestry (spec v3 section 10.2): the full known
        # history is trivially closed, unlike the old frontier-only computation.
        return frozenset(self.acts)

    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool:
        return any(
            k == kind and (n == name or definition_hash == name) and born in cut
            for k, n, _version, definition_hash, born in self.registry
        )

    def definition_registered(
        self, kind: str, name: str, definition_hash: str, cut: frozenset[str]
    ) -> bool:
        return any(
            k == kind and n == name and h == definition_hash and born in cut
            for k, n, _version, h, born in self.registry
        )

    def latest_definition_hash(
        self, kind: str, name: str, cut: frozenset[str]
    ) -> str | None:
        candidates = (
            (version, definition_hash)
            for k, n, version, definition_hash, born in self.registry
            if k == kind and n == name and born in cut
        )
        latest = max(candidates, default=None)
        return latest[1] if latest is not None else None

    def register(
        self,
        kind: str,
        name: str,
        born_at: str,
        *,
        version: int = 1,
        entry_hash: str | None = None,
        definition: CanonValue | None = None,
    ) -> str:
        definition_hash = entry_hash or (
            name
            if len(name) == 64 and all(character in "0123456789abcdef" for character in name)
            else object_hash("registry", {"kind": kind, "name": name, "version": version})
        )
        self.registry.add((kind, name, version, definition_hash, born_at))
        self.registry_definitions[definition_hash] = definition or {
            "kind": kind, "name": name, "version": version
        }
        return definition_hash

    @contextmanager
    def admission_scope(self) -> Iterator[_MemoryAdmission]:
        snapshot = (
            self.objects.copy(),
            self.acts.copy(),
            {key: list(value) for key, value in self.command_index.items()},
            self._companion_snapshot(),
        )
        admission = _MemoryAdmission(self, self.history_cut())
        try:
            yield admission
        except Exception:
            self.objects, self.acts, self.command_index, companion_state = snapshot
            self._restore_companion_snapshot(companion_state)
            raise
        finally:
            admission.close()

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

    def _admit(
        self,
        admission_cut: frozenset[str],
        act: Act,
        canon: bytes,
        command_type: str,
        companions: tuple[Companion, ...],
    ) -> Act:
        del command_type
        if self.history_cut() != admission_cut:
            raise ValueError("admission cut changed while scope was open")
        self._validate_companions(act, companions)
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
        self._apply_companions(act, companions)
        return act

    def _validate_companions(self, act: Act, companions: tuple[Companion, ...]) -> None:
        definition_hash = self.latest_definition_hash(
            "act_type", act.act_type, act.registry_cut
        )
        definition = self.registry_definitions.get(definition_hash or "")
        contract = definition.get("companion") if isinstance(definition, Mapping) else None
        if contract is None:
            if companions:
                raise ValueError("Act type declares no companion")
            return
        if not isinstance(contract, Mapping):
            raise TypeError("invalid companion contract")
        writer = contract.get("writer")
        cardinality = contract.get("cardinality")
        if cardinality == "exactly_one" and len(companions) != 1:
            raise ValueError("companion contract requires exactly one row")
        if cardinality == "one_or_more" and not companions:
            raise ValueError("companion contract requires one or more rows")
        if cardinality not in {"exactly_one", "one_or_more"}:
            raise ValueError("unsupported companion cardinality")
        if any(companion.writer.value != writer for companion in companions):
            raise ValueError("companion writer does not match Act type contract")

    def _apply_companions(self, act: Act, companions: tuple[Companion, ...]) -> None:
        del act
        if companions:
            raise ValueError("companion writer is not implemented by this store")

    def _companion_snapshot(self) -> object:
        return None

    def _restore_companion_snapshot(self, snapshot: object) -> None:
        del snapshot

    def get_act(self, act_hash: str) -> Act | None:
        return self.acts.get(act_hash)

    def get_acts_for_command(self, command_hash: str) -> tuple[Act, ...]:
        """Every Act referencing this Command -- its whole lifecycle (PF-15)."""
        return tuple(self.acts[h] for h in self.command_index.get(command_hash, ()))


class _MemoryAdmission:
    def __init__(self, store: MemoryStore, cut: frozenset[str]) -> None:
        self._store = store
        self.cut = cut
        self._active = True

    def close(self) -> None:
        self._active = False

    def admit(
        self,
        act: Act,
        canon: bytes,
        command_type: str,
        companions: tuple[Companion, ...],
    ) -> Act:
        if not self._active:
            raise RuntimeError("admission scope is closed")
        return self._store._admit(self.cut, act, canon, command_type, companions)
