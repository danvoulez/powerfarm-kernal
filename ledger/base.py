"""Read and commit ports used by the stateless Kernel service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kernel.canon import CanonValue
from kernel.commit import Store
from kernel.types import Act, Identity


@dataclass(frozen=True, slots=True)
class ObjectRecord:
    hash: str
    canon: bytes
    kind: str


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    hash: str
    kind: str
    name: str
    version: int
    born_at: str
    constitutional: bool
    definition: CanonValue


class BindingProjection(Protocol):
    """Writes for the principal-binding projection (section 14, disposable)."""

    def link_principal(self, *, issuer: str, subject: str, identity_hash: str,
                       linked_act: str) -> None: ...
    def revoke_principal(self, *, issuer: str, subject: str, unlinked_act: str) -> None: ...


class Ledger(Store, BindingProjection, Protocol):
    """Narrow persistence contract; the Kernel itself remains stateless."""

    def get_object(self, object_hash: str) -> ObjectRecord | None: ...
    def is_closed_cut(self, cut: frozenset[str]) -> bool: ...
    def get_act(self, act_hash: str) -> Act | None: ...
    def get_identity(self, identity_hash: str, cut: frozenset[str]) -> Identity | None: ...
    def registry_entries(
        self, kind: str | None, cut: frozenset[str]
    ) -> tuple[RegistryEntry, ...]: ...
    def list_acts(self, limit: int = 100) -> tuple[Act, ...]: ...
    def resolve_principal(self, issuer: str, subject: str) -> str | None: ...
    def close(self) -> None: ...
