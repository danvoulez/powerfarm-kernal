# MCP 2026-07-28 stateless boundary

The project context dump dated 2026-08-15 identifies MCP **2026-07-28** as the
external boundary for Kernel Compute and gives this separation:

```text
MCP -> protocol/mcp -> service -> kernel -> ledger adapter
```

This repository implements that separation. MCP does not redefine Powerfarm's
constitutional objects. It only transports typed requests to protocol-neutral
services; the services invoke the existing pure Kernel and the ledger arbitrates
concurrent commits.

The implementation pins the official Python SDK at `mcp==2.0.0`, the first stable
v2 release for the [2026-07-28 specification](https://modelcontextprotocol.io/specification/2026-07-28).
The server uses Streamable HTTP at `/mcp` with `stateless_http=True` and
`json_response=True`.

## 2026-07-28 properties used

- no `initialize`/`initialized` handshake and no `Mcp-Session-Id`;
- every request is self-contained and carries its protocol version and capabilities;
- `Mcp-Method` and `Mcp-Name` headers are handled by the official SDK;
- tool and resource catalogs return cache hints;
- OAuth protected-resource metadata and bearer-token verification are enabled in
  production;
- Tasks are not advertised because Kernel operations are short deterministic calls.
  Long-running Platform/ADK work must use explicit durable handles before the Tasks
  extension is enabled.

## Semantic Tools

| Tool | Contract |
|---|---|
| `powerfarm.action.evaluate` | Validate signature, types, exact cuts, Context and Rules; no write |
| `powerfarm.action.commit` | Re-evaluate and admit one idempotent Act through the atomic gate |
| `powerfarm.review.submit` | Admit a governed `AuthorizationReviewed` Act |
| `powerfarm.observation.admit` | Admit a provenance-bearing external observation |
| `powerfarm.action.explain` | Resolve Act, Command, Context and payload by hash |
| `powerfarm.command.status` | Project whether a Command already produced a consequential Act |

The protocol never exposes raw `CommitGate` or database operations.

## Resources

```text
pf://registry/current
pf://rules/current
pf://estate/current
pf://estate/identities/{identity_hash}
pf://acts/{act_hash}
pf://commands/{command_hash}
```

## Stateless request flow

```text
request
 -> verify OAuth token and institutional Identity binding
 -> read an exact ancestry-closed Registry/Rules/Estate cut
 -> verify signed Command and typed Context
 -> evaluate registered Rules
 -> atomic ledger RPC on allow
 -> return
 -> process may disappear
```

Two instances may evaluate the same cut. The PostgreSQL commit RPC holds the narrow
transactional lock and rejects the second commit if history moved, forcing
reauthorization. No correctness depends on MCP transport sessions or process memory.
