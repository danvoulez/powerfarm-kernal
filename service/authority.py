"""Exact-cut validation, Rule evaluation, and consequential admission."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from kernel.canon import canonicalize, object_hash
from kernel.commit import CommitGate
from kernel.rules import Rule, RuleResult, authorize
from kernel.types import (
    CONSEQUENTIAL_OUTCOMES,
    LIFECYCLE_ACT_TYPES,
    PERMITTED_OUTCOMES,
    Act,
    Command,
    Context,
    Decision,
    DecisionKind,
    Identity,
)
from ledger.base import Ledger

from .errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from .identity import IdentityService
from .models import ActionRequest, EvaluatedAction, RequestPrincipal


class RuleResolver(Protocol):
    def resolve(
        self,
        command: Command,
        context: Context,
        history_cut: frozenset[str],
        registry_cut: frozenset[str],
    ) -> tuple[Rule, ...]: ...


@dataclass(frozen=True, slots=True)
class RootAuthorityRule:
    hash: str
    root_identity_hash: str
    context_keys: frozenset[str] = frozenset()

    def evaluate(
        self,
        identity: Identity,
        command: Command,
        context: Context,
        history_cut: frozenset[str],
    ) -> RuleResult:
        del command, context, history_cut
        if identity.hash == self.root_identity_hash:
            return RuleResult(DecisionKind.ALLOW, "Genesis root authority applies")
        return RuleResult(DecisionKind.DENY, "Identity does not hold Genesis root authority")


class ConfiguredRuleResolver:
    """Resolve a closed, explicitly configured set of built-in Rules at a cut."""

    def __init__(
        self,
        ledger: Ledger,
        *,
        root_identity_hash: str | None = None,
        rule_names: tuple[str, ...] = ("genesis.root_authority",),
        static_rules: Mapping[str, Rule] | None = None,
    ) -> None:
        self._ledger = ledger
        self._root_identity_hash = root_identity_hash
        self._rule_names = rule_names
        self._static_rules = dict(static_rules or {})

    def resolve(
        self,
        command: Command,
        context: Context,
        history_cut: frozenset[str],
        registry_cut: frozenset[str],
    ) -> tuple[Rule, ...]:
        del command, context, history_cut
        entries = {entry.name: entry for entry in self._ledger.registry_entries("rule", registry_cut)}
        resolved: list[Rule] = []
        for name in self._rule_names:
            entry = entries.get(name)
            static = self._static_rules.get(name)
            if static is not None:
                if entry is None or static.hash != entry.hash:
                    raise ValidationError(f"configured Rule {name!r} is not registered at cut")
                resolved.append(static)
                continue
            if name == "genesis.root_authority" and entry is not None:
                if self._root_identity_hash is None:
                    raise AuthorizationError("POWERFARM_ROOT_IDENTITY_HASH is required")
                resolved.append(RootAuthorityRule(entry.hash, self._root_identity_hash))
                continue
            raise ValidationError(f"no executable implementation for registered Rule {name!r}")
        return tuple(resolved)


class AuthorityService:
    def __init__(
        self,
        ledger: Ledger,
        rules: RuleResolver,
        *,
        allow_signed_without_oauth: bool = False,
    ) -> None:
        self._ledger = ledger
        self._rules = rules
        self._identities = IdentityService(
            ledger, allow_signed_without_oauth=allow_signed_without_oauth
        )

    def evaluate(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> EvaluatedAction:
        command = request.command()
        context = request.context()
        current_cut = self._ledger.history_cut()
        history_cut = request.history_cut if request.history_cut is not None else current_cut
        registry_cut = request.registry_cut if request.registry_cut is not None else history_cut
        if not self._ledger.is_closed_cut(history_cut):
            raise ValidationError("history_cut is unknown or not closed under ancestry")
        if not self._ledger.is_closed_cut(registry_cut) or not registry_cut <= history_cut:
            raise ValidationError("registry_cut must be an ancestry-closed subset of history_cut")
        self._identities.require_binding(command.identity_hash, principal)
        identity = self._ledger.get_identity(command.identity_hash, history_cut)
        if identity is None:
            raise NotFoundError("Identity or valid signing key not found at declared cut")
        self._verify_signature(identity, command)
        self._validate_payload(request)
        self._validate_registry(request, context, registry_cut)
        rules = self._rules.resolve(command, context, history_cut, registry_cut)
        if not rules:
            raise AuthorizationError("no applicable Rules; authorization fails closed")
        for rule in rules:
            if not self._ledger.registered("rule", rule.hash, registry_cut):
                raise ValidationError("Rule is not registered at declared Registry cut")
        decision = authorize(identity, command, context, history_cut, registry_cut, rules)
        return EvaluatedAction(
            identity=identity,
            command=command,
            context=context,
            decision=decision,
            act_type=request.act_type,
            auth_chain=request.auth_chain,
            payload=request.payload,
        )

    def commit(
        self, request: ActionRequest, principal: RequestPrincipal | None = None
    ) -> tuple[EvaluatedAction, Act]:
        evaluated = self.evaluate(request, principal)
        # Which outcome may produce this Act is Kernel law (kernel.types); the
        # service only restates it to keep the protocol's typed error surface.
        permitted = PERMITTED_OUTCOMES.get(evaluated.act_type, CONSEQUENTIAL_OUTCOMES)
        if evaluated.decision.outcome not in permitted:
            raise AuthorizationError(
                f"{evaluated.act_type} requires {'/'.join(sorted(permitted))}, "
                f"got {evaluated.decision.outcome.value}"
            )
        if evaluated.act_type not in LIFECYCLE_ACT_TYPES:
            settled = self._settled_consequence(evaluated)
            if settled is not None:
                return settled
        cut_before = self._ledger.history_cut()
        if evaluated.decision.cut != cut_before:
            raise ConflictError("history advanced after evaluation; reauthorization required")
        if request.payload is not None:
            self._ledger.put_object(
                request.payload_hash, canonicalize(request.payload), "payload"
            )
        act = CommitGate(self._ledger).commit(
            evaluated.identity,
            evaluated.command,
            evaluated.decision,
            evaluated.context,
            act_type=evaluated.act_type,
            auth_chain=evaluated.auth_chain,
            claimed_when=request.claimed_when,
        )
        if act.hash in cut_before:
            # The Gate returned an occurrence that already held its place: a
            # replay of identical content, not a second placement (PF-23).
            replay = Decision(
                evaluated.decision.outcome,
                act.decision_cut,
                act.rule_hashes,
                act.registry_cut,
                "idempotent replay of existing Act",
            )
            return replace(evaluated, decision=replay), act
        return evaluated, act

    def _settled_consequence(
        self, evaluated: EvaluatedAction
    ) -> tuple[EvaluatedAction, Act] | None:
        """The consequential Act this Command already produced, if any.

        A re-submission at a later cut is not a new purchase of the same change.
        The Gate refuses it outright; the protocol is friendlier and replays the
        settled occurrence, which is what an idempotent client expects.
        """
        for act in self._ledger.get_acts_for_command(evaluated.command.hash):
            if act.act_type in LIFECYCLE_ACT_TYPES:
                continue
            if (
                act.act_type != evaluated.act_type
                or act.identity_hash != evaluated.identity.hash
                or act.parents != evaluated.command.parents
                or act.context_hash != evaluated.context.hash
                or act.payload_hash != evaluated.command.payload_hash
            ):
                raise ConflictError("Command already committed with different consequential inputs")
            replay = Decision(
                DecisionKind.ALLOW,
                act.decision_cut,
                act.rule_hashes,
                act.registry_cut,
                "idempotent replay of existing Act",
            )
            return replace(evaluated, decision=replay), act
        return None

    def _validate_payload(self, request: ActionRequest) -> None:
        if request.payload is not None:
            actual = object_hash("payload", request.payload)
            if actual != request.payload_hash:
                raise ValidationError("payload does not match payload_hash")
        elif not self._ledger.has_object(request.payload_hash):
            raise NotFoundError("payload_hash is not present in CAS and no payload was supplied")

    def _validate_registry(
        self, request: ActionRequest, context: Context, registry_cut: frozenset[str]
    ) -> None:
        if not self._ledger.registered("command_type", request.command_type, registry_cut):
            raise ValidationError("unregistered command type")
        if not self._ledger.registered("act_type", request.act_type, registry_cut):
            raise ValidationError("unregistered Act type")
        for key in context.values:
            if not self._ledger.registered("context_type", key, registry_cut):
                raise ValidationError(f"unregistered Context type: {key}")

    @staticmethod
    def _verify_signature(identity: Identity, command: Command) -> None:
        try:
            Ed25519PublicKey.from_public_bytes(identity.public_key).verify(
                command.signature, canonicalize(command.signing_value())
            )
        except (InvalidSignature, ValueError) as error:
            raise AuthorizationError("invalid Command signature at declared cut") from error
