# Powerfarm Kernel

This repository implements the constitutional core described by **Powerfarm System
Specification v3** and the accompanying implementation plan. The current foundation includes:

- deterministic RFC 8949 CBOR and SHA-256 domain-separated content identities;
- frozen Identity, Command, Context, Decision, Act, and Relation values;
- pure, fail-closed rule evaluation with declared context inputs;
- one signature-verifying, cut-aware, idempotent Act commit gate;
- deterministic projector contracts and disposable materializations;
- a PostgreSQL genesis schema with an append-only database backstop;
- a reproducible Genesis ceremony and agent-side signed Command proposals; and
- executable conformance coverage for the kernel invariants implemented here.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
python -m genesis.ceremony
```

Agent tools must return Command proposals. They must not connect to the database. Production
database adapters must expose the narrow `kernel.commit.Store` contract and make
`put_object` plus `append_act` one transaction; `CommitGate` remains the only history writer.

## Deliberate boundaries

The ADK runtime, Supabase Edge transport, external-effect dispatcher, and deployment manifests
remain integrations over this kernel. They must be added phase-by-phase without introducing a
second write path. The included in-memory adapter is for ceremony/conformance work, not a source
of production truth.
