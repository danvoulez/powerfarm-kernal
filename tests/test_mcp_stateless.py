import base64
from dataclasses import dataclass

import anyio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from starlette.testclient import TestClient

from kernel.canon import canonicalize, object_hash
from kernel.rules import RuleResult
from kernel.types import Act, Context, DecisionKind, Identity
from ledger.memory import MemoryLedger
from protocol.mcp.models import ActionInput
from protocol.mcp.server import MCP_PROTOCOL_VERSION, create_server
from service.authority import AuthorityService, ConfiguredRuleResolver
from service.explain import ExplainService
from service.lifecycle import LifecycleService
from service.observation import ObservationService
from service.review import ReviewService
from service.runtime import KernelRuntime


@dataclass(frozen=True, slots=True)
class AllowRule:
    hash: str
    context_keys: frozenset[str] = frozenset({"request.origin"})

    def evaluate(
        self,
        identity: Identity,
        command: object,
        context: Context,
        history_cut: frozenset[str],
    ) -> RuleResult:
        del identity, command, context, history_cut
        return RuleResult(DecisionKind.ALLOW, "test Rule allows this action")


def setup_runtime() -> tuple[KernelRuntime, Ed25519PrivateKey, str, str]:
    ledger = MemoryLedger()
    genesis = "0" * 64
    ledger.acts[genesis] = Act(
        genesis,
        "GenesisClosed",
        genesis,
        (),
        frozenset(),
        "genesis-command",
        (),
        frozenset(),
        (),
        genesis,
        genesis,
    )
    ledger.command_index["genesis-command"] = genesis
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    identity_hash = object_hash(
        "identity", base64.urlsafe_b64encode(public_key).decode("ascii")
    )
    ledger.seed_identity(Identity(identity_hash, "human", public_key))
    ledger.register("command_type", "CreateThing", genesis)
    ledger.register("act_type", "ThingCreated", genesis)
    ledger.register("context_type", "request.origin", genesis)
    rule_hash = object_hash("rule", {"name": "test.allow", "version": 1})
    rule = AllowRule(rule_hash)
    ledger.register("rule", "test.allow", genesis, entry_hash=rule_hash)
    resolver = ConfiguredRuleResolver(
        ledger,
        rule_names=("test.allow",),
        static_rules={"test.allow": rule},
    )
    authority = AuthorityService(ledger, resolver, allow_signed_without_oauth=True)
    runtime = KernelRuntime(
        ledger,
        authority,
        ReviewService(authority),
        ObservationService(authority),
        LifecycleService(ledger),
        ExplainService(ledger),
    )
    return runtime, private_key, identity_hash, genesis


def signed_action(
    private_key: Ed25519PrivateKey, identity_hash: str, genesis: str
) -> ActionInput:
    payload = {"name": "one"}
    payload_hash = object_hash("payload", payload)
    unsigned = {
        "command_type": "CreateThing",
        "identity_hash": identity_hash,
        "nonce": "mcp-test-1",
        "parents": [genesis],
        "payload_hash": payload_hash,
    }
    signature = base64.urlsafe_b64encode(
        private_key.sign(canonicalize(unsigned))
    ).rstrip(b"=").decode("ascii")
    return ActionInput.model_validate(
        {
            "command": {**unsigned, "signature": signature},
            "context": {
                "values": {"request.origin": "test"},
                "types": {"request.origin": "origin-v1"},
            },
            "act_type": "ThingCreated",
            "payload": payload,
        }
    )


def test_semantic_tools_evaluate_commit_and_replay_idempotently() -> None:
    runtime, private_key, identity_hash, genesis = setup_runtime()
    server = create_server(runtime, auth_required=False)
    action = signed_action(private_key, identity_hash, genesis)

    async def scenario() -> None:
        arguments = {"action": action.model_dump(mode="json")}
        evaluated = await server.call_tool("powerfarm.action.evaluate", arguments)
        assert evaluated.is_error is False
        assert evaluated.structured_content["decision"]["outcome"] == "allow"
        first = await server.call_tool("powerfarm.action.commit", arguments)
        second = await server.call_tool("powerfarm.action.commit", arguments)
        assert first.is_error is False
        assert first.structured_content["act"]["hash"] == second.structured_content["act"]["hash"]
        assert second.structured_content["evaluation"]["decision"]["reason"] == (
            "idempotent replay of existing Act"
        )

    anyio.run(scenario)


def test_catalog_matches_the_context_dump_boundary() -> None:
    runtime, _, _, _ = setup_runtime()
    server = create_server(runtime, auth_required=False)

    async def inspect_catalog() -> None:
        tools = {tool.name for tool in await server.list_tools()}
        templates = {item.uri_template for item in await server.list_resource_templates()}
        resources = {str(item.uri) for item in await server.list_resources()}
        assert {
            "powerfarm.action.evaluate",
            "powerfarm.action.commit",
            "powerfarm.review.submit",
            "powerfarm.observation.admit",
            "powerfarm.action.explain",
        } <= tools
        assert "pf://acts/{act_hash}" in templates
        assert "pf://commands/{command_hash}" in templates
        assert "pf://estate/identities/{identity_hash}" in templates
        assert {"pf://registry/current", "pf://rules/current", "pf://estate/current"} <= resources

    anyio.run(inspect_catalog)


def test_two_http_requests_need_no_handshake_or_session() -> None:
    runtime, _, _, _ = setup_runtime()
    server = create_server(runtime, auth_required=False)
    app = server.streamable_http_app(
        stateless_http=True, json_response=True, host="testserver"
    )
    headers = {
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        "Mcp-Method": "tools/list",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    metadata = {
        "io.modelcontextprotocol/protocolVersion": MCP_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": "powerfarm-test", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {"_meta": metadata},
    }
    with TestClient(app) as client:
        first = client.post("/mcp", headers=headers, json=body)
        body["id"] = 2
        second = client.post("/mcp", headers=headers, json=body)
    assert first.status_code == second.status_code == 200
    assert "Mcp-Session-Id" not in first.headers
    assert "Mcp-Session-Id" not in second.headers
    assert first.json()["result"]["resultType"] == "complete"
    assert second.json()["result"]["resultType"] == "complete"
