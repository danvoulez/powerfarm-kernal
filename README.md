# Powerfarm Kernel

This repository implements the constitutional core described by **Powerfarm System
Specification v3** and the accompanying implementation plan. The current foundation includes:

- deterministic JCS (RFC 8785) and SHA-256 domain-separated content identities,
  pinned byte-exact by the golden vector suite in conformance/golden-vectors/;
- frozen Identity, Command, Context, Decision, Act, and Relation values;
- pure, fail-closed rule evaluation with declared context inputs;
- one signature-verifying, cut-aware, idempotent Act commit gate;
- deterministic projector contracts and disposable materializations;
- a PostgreSQL genesis schema with an append-only database backstop;
- a reproducible Genesis ceremony and agent-side signed Command proposals; and
- executable conformance coverage for the kernel invariants implemented here.

The repository also carries the earlier institutional bootstrap package from the
Kimi workspace under `bootstrap/v0/`. That package is preserved as a one-shot
ledger bootstrap artifact: useful for LAB ceremony experiments and comparison
against the kernel genesis ceremony, but not a replacement write path for
production Acts.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
python -m genesis.ceremony
```

## macOS LAB Install

Powerfarm runs directly on the Mac LAB with launchd. Docker and Compose are not
part of the deployment contract.

```bash
cp deploy/macos/powerfarm.env.example deploy/macos/powerfarm.env
$EDITOR deploy/macos/powerfarm.env
deploy/macos/install.sh --env deploy/macos/powerfarm.env
deploy/macos/smoke.sh --env deploy/macos/powerfarm.env
```

The pack owns the local worker LaunchAgent, the dedicated Cloudflare Tunnel
LaunchAgent, Supabase migration application, Cloudflare DNS routing for
`powerfarm.app`, and versioned install receipts.

Bootstrap V0 can be exercised in a disposable LAB directory:

```bash
export POWERFARM_HOME=/tmp/powerfarm-lab
mkdir -p "$POWERFARM_HOME"
python bootstrap/v0/generate_test_keys.py --home "$POWERFARM_HOME" --write-manifest
python bootstrap/v0/bootstrap.py bootstrap --home "$POWERFARM_HOME"
```

Agent tools must return Command proposals. They must not connect to the database. Production
database adapters must expose the narrow `kernel.commit.Store` contract and make
`put_object` plus `append_act` one transaction; `CommitGate` remains the only history writer.

## Deliberate boundaries

The ADK runtime, Supabase Edge transport, external-effect dispatcher, and deployment manifests
remain integrations over this kernel. They must be added phase-by-phase without introducing a
second write path. The included in-memory adapter is for ceremony/conformance work, not a source
of production truth.
