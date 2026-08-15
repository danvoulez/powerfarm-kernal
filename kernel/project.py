"""Deterministic projection contracts."""

from typing import Protocol, TypeVar

from .types import Act

StateT = TypeVar("StateT")


class Projector(Protocol[StateT]):
    hash: str

    def initial(self) -> StateT: ...
    def apply(self, state: StateT, act: Act) -> StateT: ...


def project(acts: tuple[Act, ...], projector: Projector[StateT]) -> StateT:
    """Fold an explicitly deterministic causal linearization supplied by the caller."""
    state = projector.initial()
    for act in acts:
        state = projector.apply(state, act)
    return state
