"""Disposable ledger used by conformance tests and explicit local development."""

from __future__ import annotations

import base64

from kernel.canon import CanonValue, canonicalize, object_hash
from kernel.memory import MemoryStore
from kernel.types import Act, Identity

from .base import ObjectRecord, RegistryEntry


class MemoryLedger(MemoryStore):
    def __init__(self) -> None:
        super().__init__()
        self.identities: dict[str, Identity] = {}
        self.principal_bindings: dict[tuple[str, str], str] = {}
        self._registry_metadata: dict[tuple[str, str, str], RegistryEntry] = {}

    def seed_identity(
        self, identity: Identity, *, issuer: str | None = None, subject: str | None = None
    ) -> None:
        encoded_key = base64.urlsafe_b64encode(identity.public_key).rstrip(b"=").decode("ascii")
        value = {"kind": identity.kind, "public_key": encoded_key}
        self.put_object(identity.hash, canonicalize(value), "identity")
        self.identities[identity.hash] = identity
        if issuer is not None and subject is not None:
            self.principal_bindings[(issuer, subject)] = identity.hash

    def register(
        self,
        kind: str,
        name: str,
        born_at: str,
        *,
        version: int = 1,
        constitutional: bool = False,
        entry_hash: str | None = None,
    ) -> None:
        super().register(kind, name, born_at)
        value: dict[str, CanonValue] = {"kind": kind, "name": name, "version": version}
        definition_hash = entry_hash or (
            name if kind == "rule" and len(name) == 64 else object_hash("registry", value)
        )
        self._registry_metadata[(kind, name, born_at)] = RegistryEntry(
            hash=definition_hash,
            kind=kind,
            name=name,
            version=version,
            born_at=born_at,
            constitutional=constitutional,
            definition=value,
        )

    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool:
        return any(
            entry.kind == kind
            and (entry.name == name or entry.hash == name)
            and entry.born_at in cut
            for entry in self._registry_metadata.values()
        )

    def get_object(self, object_hash_value: str) -> ObjectRecord | None:
        found = self.objects.get(object_hash_value)
        if found is None:
            return None
        canon, kind = found
        return ObjectRecord(object_hash_value, canon, kind)

    def get_act(self, act_hash: str) -> Act | None:
        return self.acts.get(act_hash)

    def is_closed_cut(self, cut: frozenset[str]) -> bool:
        return all(
            act_hash in self.acts and set(self.acts[act_hash].parents) <= cut
            for act_hash in cut
        )

    def get_identity(self, identity_hash: str, cut: frozenset[str]) -> Identity | None:
        del cut
        return self.identities.get(identity_hash)

    def registry_entries(
        self, kind: str | None, cut: frozenset[str]
    ) -> tuple[RegistryEntry, ...]:
        entries = (
            entry
            for entry in self._registry_metadata.values()
            if entry.born_at in cut and (kind is None or entry.kind == kind)
        )
        return tuple(sorted(entries, key=lambda item: (item.kind, item.name, item.version)))

    def list_acts(self, limit: int = 100) -> tuple[Act, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return tuple(self.acts.values())[-limit:]

    def resolve_principal(self, issuer: str, subject: str) -> str | None:
        if not issuer or not subject:
            return None
        return self.principal_bindings.get((issuer, subject))

    def unlink_principal(self, issuer: str, subject: str) -> None:
        """Revocation: the binding stops resolving. History keeps the Act."""
        self.principal_bindings.pop((issuer, subject), None)

    def close(self) -> None:
        return None
