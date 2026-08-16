# Powerfarm Kernel

Powerfarm Kernel is the constitutional computation core of Powerfarm. It admits
content-addressed history under exact Registry, Rule, Identity, and causal cuts.
It does not deploy agents, operate a web application, or own a machine-specific
runtime.

The repository is deliberately narrow:

```text
powerfarm-kernel/
├── SPECIFICATION.md          constitutional system and PF-01…PF-26
├── GENESIS_DESIGN_PACK/      draft Constitution, decisions, contracts, evidence
├── genesis/                  reproducible M2 candidate material
├── kernel/                   canonical values, Rules, admission, projection
├── service/                  protocol-neutral governed operations
├── ledger/                   memory and PostgreSQL adapters
├── protocol/mcp/             stateless MCP boundary
├── agent/                    signed Command proposal helper
├── conformance/              law map, golden vectors, SQL refusal tests
├── tests/                    executable component contracts
├── supabase/migrations/      sealed physical history substrate
└── scripts/ci/               migration and SQL verification
```

This is an institutional boundary, not a monorepo. Platform hosting, Cloudflare
Workers, ADK execution, product surfaces, machine installers, release updaters,
and webhook ingestion belong to their own components. Historical implementations
of those concerns were removed from this repository; Git history remains the
archive.

## Authority

When documents disagree, read them in this order:

1. [`GENESIS_DESIGN_PACK/decisions/DECISION_REGISTER.md`](GENESIS_DESIGN_PACK/decisions/DECISION_REGISTER.md)
2. [`SPECIFICATION.md`](SPECIFICATION.md)
3. [`GENESIS_DESIGN_PACK/constitution/01_Genesis_Constitution_0.2.md`](GENESIS_DESIGN_PACK/constitution/01_Genesis_Constitution_0.2.md)
4. focused contracts under `GENESIS_DESIGN_PACK/specifications/`
5. evidence and research reconciliation material

The Constitution is still a draft. M2 material is a deterministic candidate,
not admitted Genesis. `genesis/material-input.candidate.json` records the real
unsettled decisions and missing public-key custody inputs; no synthetic ceremony
may cross that boundary.

## Development

```bash
uv sync --extra dev --locked
uv run ruff check .
uv run mypy kernel agent genesis ledger service protocol
uv run pytest -q
uv run python -m genesis.material --check
uv run python scripts/ci/check_sql.py
```

PostgreSQL conformance additionally runs:

```bash
scripts/ci/test_migrations.sh
```

The MCP adapter exposes stateless Streamable HTTP at `POST /mcp` and health at
`GET /health`. Production authentication is configured through environment
variables consumed by `protocol/mcp/auth.py`; authentication proves a principal,
while Powerfarm authority still comes only from admitted history and Rules.

## Non-negotiable boundaries

- canonical identity is RFC 8785 JCS plus SHA-256 domain separation;
- an admitted Act names the exact decision, Registry, Rule, Context, and causal cuts;
- one database admission function owns every authoritative companion write;
- protocol state, model output, external runtime state, and projections confer no authority;
- sealed migrations and admitted history are never rewritten;
- candidates, simulations, and observations remain distinct provenance domains.

The complete law catalogue and component contract are in
[`SPECIFICATION.md`](SPECIFICATION.md). The current Genesis blockers are in
[`GENESIS_DESIGN_PACK/decisions/OPEN_DECISIONS.md`](GENESIS_DESIGN_PACK/decisions/OPEN_DECISIONS.md).
