"""Composition root for one disposable Kernel process."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ledger.base import Ledger
from ledger.memory import MemoryLedger
from ledger.postgres import PostgresStore

from .authority import AuthorityService, ConfiguredRuleResolver
from .explain import ExplainService
from .lifecycle import LifecycleService
from .observation import ObservationService
from .review import ReviewService


@dataclass(slots=True)
class KernelRuntime:
    ledger: Ledger
    authority: AuthorityService
    review: ReviewService
    observation: ObservationService
    lifecycle: LifecycleService
    explain: ExplainService

    def close(self) -> None:
        self.ledger.close()


def build_runtime_from_env(*, auth_required: bool) -> KernelRuntime:
    database_url = os.environ.get("DATABASE_URL")
    ledger: Ledger = PostgresStore(database_url) if database_url else MemoryLedger()
    rule_names = tuple(
        name.strip()
        for name in os.environ.get("POWERFARM_RULES", "genesis.root_authority").split(",")
        if name.strip()
    )
    resolver = ConfiguredRuleResolver(
        ledger,
        root_identity_hash=os.environ.get("POWERFARM_ROOT_IDENTITY_HASH"),
        rule_names=rule_names,
    )
    authority = AuthorityService(
        ledger,
        resolver,
        allow_signed_without_oauth=not auth_required,
    )
    return KernelRuntime(
        ledger=ledger,
        authority=authority,
        review=ReviewService(authority),
        observation=ObservationService(authority),
        lifecycle=LifecycleService(ledger),
        explain=ExplainService(ledger),
    )
