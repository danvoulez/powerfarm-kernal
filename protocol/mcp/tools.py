"""Semantic MCP Tools. Raw CommitGate operations are intentionally not exposed."""

from __future__ import annotations

from mcp.server import MCPServer
from mcp_types import ToolAnnotations

from service.models import EvaluatedAction, act_to_dict
from service.runtime import KernelRuntime

from .auth import current_principal
from .errors import call_service
from .models import (
    ActionInput,
    CommitOutput,
    EvaluationOutput,
    ExplainOutput,
    LifecycleOutput,
)


def install_tools(server: MCPServer[object], runtime: KernelRuntime) -> None:
    @server.tool(
        name="powerfarm.action.evaluate",
        title="Evaluate governed action",
        description=(
            "Validate a signed Command and evaluate registered Rules at an explicit, "
            "ancestry-closed ledger cut. This tool does not write history."
        ),
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    def evaluate(action: ActionInput) -> EvaluationOutput:
        evaluated = call_service(
            lambda: runtime.authority.evaluate(action.to_service(), current_principal())
        )
        return EvaluationOutput.model_validate(evaluated.as_dict())

    @server.tool(
        name="powerfarm.action.commit",
        title="Commit governed action",
        description=(
            "Re-evaluate a signed Command at its declared cut and, only on allow, admit one "
            "idempotent consequential Act through the atomic ledger gate."
        ),
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    def commit(action: ActionInput) -> CommitOutput:
        evaluated, act = call_service(
            lambda: runtime.authority.commit(action.to_service(), current_principal())
        )
        assert isinstance(evaluated, EvaluatedAction)
        return CommitOutput.model_validate(
            {"evaluation": evaluated.as_dict(), "act": act_to_dict(act)}
        )

    @server.tool(
        name="powerfarm.review.submit",
        title="Submit governed authorization review",
        description=(
            "Admit an independently signed AuthorizationReviewed Act. Review is immutable "
            "history and never hidden MCP or workflow state."
        ),
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    def submit_review(action: ActionInput) -> CommitOutput:
        evaluated, act = call_service(
            lambda: runtime.review.submit(action.to_service(), current_principal())
        )
        assert isinstance(evaluated, EvaluatedAction)
        return CommitOutput.model_validate(
            {"evaluation": evaluated.as_dict(), "act": act_to_dict(act)}
        )

    @server.tool(
        name="powerfarm.observation.admit",
        title="Admit external observation",
        description=(
            "Admit a provenance-bearing observation without conflating dispatch, observation, "
            "or external commitment."
        ),
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
    )
    def admit_observation(action: ActionInput) -> CommitOutput:
        evaluated, act = call_service(
            lambda: runtime.observation.admit(action.to_service(), current_principal())
        )
        assert isinstance(evaluated, EvaluatedAction)
        return CommitOutput.model_validate(
            {"evaluation": evaluated.as_dict(), "act": act_to_dict(act)}
        )

    @server.tool(
        name="powerfarm.action.explain",
        title="Explain committed action",
        description="Resolve an Act and the exact Command, Context and payload objects it cites.",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    def explain(act_hash: str) -> ExplainOutput:
        result = call_service(lambda: runtime.explain.action(act_hash))
        return ExplainOutput.model_validate(result)

    @server.tool(
        name="powerfarm.command.status",
        title="Read Command status",
        description="Project whether a Command already produced a consequential Act.",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    def command_status(command_hash: str) -> LifecycleOutput:
        result = call_service(lambda: runtime.lifecycle.status(command_hash))
        return LifecycleOutput.model_validate(result)
