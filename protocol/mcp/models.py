"""Typed MCP tool schemas; service types remain protocol-neutral."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from service.models import ActionRequest


class CommandInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_type: str = Field(min_length=1)
    identity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    parents: list[str] = Field(default_factory=list)
    nonce: str = Field(min_length=1)
    signature: str = Field(description="Ed25519 signature encoded as unpadded base64url")


class ContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: dict[str, JsonValue]
    types: dict[str, str]


class ActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: CommandInput
    context: ContextInput
    act_type: str = Field(min_length=1)
    payload: JsonValue | None = None
    history_cut: list[str] | None = None
    registry_cut: list[str] | None = None
    auth_chain: list[str] = Field(default_factory=list)

    def to_service(self) -> ActionRequest:
        return ActionRequest(
            command_type=self.command.command_type,
            identity_hash=self.command.identity_hash,
            payload_hash=self.command.payload_hash,
            parents=tuple(self.command.parents),
            nonce=self.command.nonce,
            signature=self.command.signature,
            context_values=self.context.values,
            context_types=self.context.types,
            act_type=self.act_type,
            payload=self.payload,
            history_cut=(
                frozenset(self.history_cut) if self.history_cut is not None else None
            ),
            registry_cut=(
                frozenset(self.registry_cut) if self.registry_cut is not None else None
            ),
            auth_chain=tuple(self.auth_chain),
        )


class DecisionOutput(BaseModel):
    outcome: str
    reason: str
    history_cut: list[str]
    registry_cut: list[str]
    rule_hashes: list[str]


class EvaluationOutput(BaseModel):
    act_type: str
    command_hash: str
    context_hash: str
    decision: DecisionOutput
    identity_hash: str
    payload_hash: str


class ActOutput(BaseModel):
    hash: str
    act_type: str
    identity_hash: str
    parents: list[str]
    decision_cut: list[str]
    command_hash: str
    auth_chain: list[str]
    registry_cut: list[str]
    rule_hashes: list[str]
    context_hash: str
    payload_hash: str
    claimed_when: str | None


class CommitOutput(BaseModel):
    evaluation: EvaluationOutput
    act: ActOutput


class ExplainOutput(BaseModel):
    act: dict[str, JsonValue]
    command: JsonValue | None
    context: JsonValue | None
    payload: JsonValue | None


class LifecycleOutput(BaseModel):
    command_hash: str
    consequential_act: str | None
    status: str
