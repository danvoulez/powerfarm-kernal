"""Content-addressed MCP Resources over Registry, Rules, Estate, Acts and Commands."""

from __future__ import annotations

import base64
import json

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError

from ledger.base import RegistryEntry
from service.models import act_to_dict
from service.runtime import KernelRuntime


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _entry(entry: RegistryEntry) -> dict[str, object]:
    return {
        "hash": entry.hash,
        "kind": entry.kind,
        "name": entry.name,
        "version": entry.version,
        "born_at": entry.born_at,
        "constitutional": entry.constitutional,
        "definition": entry.definition,
    }


def install_resources(server: MCPServer[object], runtime: KernelRuntime) -> None:
    @server.resource(
        "pf://registry/current",
        name="powerfarm-registry-current",
        title="Current Powerfarm Registry",
        description="Registered definitions valid at the current exact Estate cut.",
        mime_type="application/json",
    )
    def registry_current() -> str:
        cut = runtime.ledger.history_cut()
        return _json(
            {"cut": sorted(cut), "entries": [_entry(item) for item in runtime.ledger.registry_entries(None, cut)]}
        )

    @server.resource(
        "pf://rules/current",
        name="powerfarm-rules-current",
        title="Current Powerfarm Rules",
        description="Rule definitions valid at the current exact Estate cut.",
        mime_type="application/json",
    )
    def rules_current() -> str:
        cut = runtime.ledger.history_cut()
        return _json(
            {"cut": sorted(cut), "rules": [_entry(item) for item in runtime.ledger.registry_entries("rule", cut)]}
        )

    @server.resource(
        "pf://estate/current",
        name="powerfarm-estate-current",
        title="Current Powerfarm Estate cut",
        description="The exact ancestry-closed set of Acts currently known to the ledger.",
        mime_type="application/json",
    )
    def estate_current() -> str:
        cut = runtime.ledger.history_cut()
        return _json({"cut": sorted(cut), "act_count": len(cut)})

    @server.resource(
        "pf://acts/{act_hash}",
        name="powerfarm-act",
        title="Powerfarm Act",
        description="One immutable Act addressed by its constitutional content hash.",
        mime_type="application/json",
    )
    def act_by_hash(act_hash: str) -> str:
        act = runtime.ledger.get_act(act_hash)
        if act is None:
            raise ResourceNotFoundError(f"Act {act_hash} not found")
        return _json(act_to_dict(act))

    @server.resource(
        "pf://commands/{command_hash}",
        name="powerfarm-command",
        title="Powerfarm Command",
        description="One canonical unsigned Command value addressed by content hash.",
        mime_type="application/json",
    )
    def command_by_hash(command_hash: str) -> str:
        record = runtime.ledger.get_object(command_hash)
        if record is None or record.kind != "command":
            raise ResourceNotFoundError(f"Command {command_hash} not found")
        return record.canon.decode("utf-8")

    @server.resource(
        "pf://estate/identities/{identity_hash}",
        name="powerfarm-identity",
        title="Powerfarm Identity",
        description="Institutional Identity and signing key valid at the current Estate cut.",
        mime_type="application/json",
    )
    def identity_by_hash(identity_hash: str) -> str:
        cut = runtime.ledger.history_cut()
        identity = runtime.ledger.get_identity(identity_hash, cut)
        if identity is None:
            raise ResourceNotFoundError(f"Identity {identity_hash} not found")
        key = base64.urlsafe_b64encode(identity.public_key).rstrip(b"=").decode("ascii")
        return _json(
            {"hash": identity.hash, "kind": identity.kind, "public_key": key, "cut": sorted(cut)}
        )
