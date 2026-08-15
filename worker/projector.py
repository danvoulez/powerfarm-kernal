"""Projection rebuild utilities; no wall clock, randomness, or network access."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from kernel.project import Projector, project
from kernel.types import Act

T = TypeVar("T")


@dataclass(frozen=True)
class Materialization(Generic[T]):
    state: T
    projector_hash: str
    history_cut: frozenset[str]


def rebuild(acts: tuple[Act, ...], projector: Projector[T],
            history_cut: frozenset[str]) -> Materialization[T]:
    return Materialization(project(acts, projector), projector.hash, history_cut)

