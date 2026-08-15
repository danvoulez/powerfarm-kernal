"""Deterministic projection contracts."""

from typing import Protocol

from .types import Act


class Projector[StateT](Protocol):
    hash: str

    def initial(self) -> StateT: ...
    def apply(self, state: StateT, act: Act) -> StateT: ...


def project[StateT](acts: tuple[Act, ...], projector: Projector[StateT]) -> StateT:
    """Fold an explicitly deterministic causal linearization supplied by the caller."""
    state = projector.initial()
    for act in acts:
        state = projector.apply(state, act)
    return state
