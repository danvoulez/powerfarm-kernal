"""The sole gate through which consequential Acts enter history."""

from __future__ import annotations

from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .canon import canonicalize, object_hash
from .types import Act, Command, Context, Decision, DecisionKind, Identity


class CommitError(RuntimeError):
    pass


class Store(Protocol):
    def history_cut(self) -> frozenset[str]: ...
    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool: ...
    def has_object(self, object_hash: str) -> bool: ...
    def has_act(self, act_hash: str) -> bool: ...
    def put_object(self, object_hash: str, canon: bytes, kind: str) -> None: ...
    def commit_act(self, act: Act, canon: bytes, command_type: str) -> Act: ...
    def get_act_for_command(self, command_hash: str) -> Act | None: ...


class CommitGate:
    def __init__(self, store: Store) -> None:
        self._store = store

    def commit(self, identity: Identity, command: Command, decision: Decision,
               context: Context, *, act_type: str, auth_chain: tuple[str, ...] = ()) -> Act:
        if identity.hash != command.identity_hash:
            raise CommitError("identity mismatch")
        try:
            Ed25519PublicKey.from_public_bytes(identity.public_key).verify(
                command.signature, canonicalize(command.signing_value()))
        except (InvalidSignature, ValueError) as error:
            raise CommitError("invalid command signature") from error
        existing = self._store.get_act_for_command(command.hash)
        if existing is not None:
            if (
                existing.act_type != act_type
                or existing.identity_hash != identity.hash
                or existing.parents != command.parents
                or existing.context_hash != context.hash
                or existing.payload_hash != command.payload_hash
            ):
                raise CommitError("command already committed with different consequential inputs")
            return existing
        if decision.outcome is not DecisionKind.ALLOW:
            raise CommitError(f"consequential commit requires allow, got {decision.outcome}")
        current_cut = self._store.history_cut()
        if current_cut != decision.cut:
            raise CommitError("history advanced after authorization; reauthorization required")
        if not self._store.registered("command_type", command.command_type, decision.registry_cut):
            raise CommitError("unregistered command type")
        if not self._store.registered("act_type", act_type, decision.registry_cut):
            raise CommitError("unregistered act type")
        if not decision.rule_hashes:
            raise CommitError("consequential commit requires at least one Rule")
        if any(
            not self._store.registered("rule", rule_hash, decision.registry_cut)
            for rule_hash in decision.rule_hashes
        ):
            raise CommitError("unregistered Rule at declared Registry cut")
        if any(
            not self._store.registered("context_type", key, decision.registry_cut)
            for key in context.values
        ):
            raise CommitError("unregistered Context type at declared Registry cut")
        if not self._store.has_object(command.payload_hash):
            raise CommitError("payload must already exist in CAS")
        if any(not self._store.has_act(parent) for parent in command.parents):
            raise CommitError("every parent must be an existing Act")
        self._store.put_object(command.hash, canonicalize(command.signing_value()), "command")
        self._store.put_object(context.hash, canonicalize(context.canonical_value()), "context")
        value = {"act_type": act_type, "auth_chain": list(auth_chain),
                 "command_hash": command.hash, "context_hash": context.hash,
                 "decision_cut": sorted(decision.cut), "identity_hash": identity.hash,
                 "parents": list(command.parents), "payload_hash": command.payload_hash,
                 "registry_cut": sorted(decision.registry_cut),
                 "rule_hashes": list(decision.rule_hashes)}
        act_hash = object_hash("act", value)
        act = Act(act_hash, act_type, identity.hash, command.parents, decision.cut, command.hash,
                  auth_chain, decision.registry_cut, decision.rule_hashes, context.hash,
                  command.payload_hash)
        try:
            return self._store.commit_act(act, canonicalize(value), command.command_type)
        except Exception as error:
            raise CommitError("store rejected Act") from error
