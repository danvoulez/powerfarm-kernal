"""Projection rebuild utilities; no wall clock, randomness, or network access."""

from dataclasses import dataclass

from kernel.project import Projector, project
from kernel.types import Act


@dataclass(frozen=True)
class Materialization[T]:
    state: T
    projector_hash: str
    history_cut: frozenset[str]


def rebuild[T](acts: tuple[Act, ...], projector: Projector[T],
               history_cut: frozenset[str]) -> Materialization[T]:
    return Materialization(project(acts, projector), projector.hash, history_cut)
