# Powerfarm Kernel

This repository implements the constitutional core described by **Powerfarm System
Specification v3.2** and the accompanying implementation plan. The current foundation includes:

- deterministic JCS (RFC 8785) and SHA-256 domain-separated content identities,
  pinned byte-exact by the golden vector suite in conformance/golden-vectors/;
- frozen Identity, Command, Context, Decision, Act, and Relation values;
- pure, fail-closed rule evaluation with declared context inputs;
- one signature-verifying, cut-aware, idempotent Act commit gate;
- deterministic projector contracts and disposable materializations;
- a PostgreSQL genesis schema with an append-only database backstop;
- a reproducible Genesis ceremony and agent-side signed Command proposals; and
- executable conformance coverage for the kernel invariants implemented here.

There is one Genesis implementation: the version-bound configuration in
`genesis/genesis.yaml` and the deterministic ceremony in `genesis/ceremony.py`.
It uses the JCS/domain-separated Kernel identity model.

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
deploy/macos/secrets.sh set supabase-access-token
deploy/macos/secrets.sh set supabase-secret-key
deploy/macos/install.sh --env deploy/macos/powerfarm.env --dry-run
deploy/macos/install.sh --env deploy/macos/powerfarm.env
deploy/macos/smoke.sh --env deploy/macos/powerfarm.env
```

The pack owns the local worker LaunchAgent, the dedicated Cloudflare Tunnel
LaunchAgent, the release updater LaunchAgent, Supabase migration and Auth
convergence, two private Storage buckets, Cloudflare DNS routing for
`powerfarm.app`, and local plus remote versioned receipts. Secrets are read from
the macOS Keychain; the env file is a private fallback.

Human authentication uses Supabase Auth passkeys for RP ID `powerfarm.app`.
Supabase also acts as the OAuth 2.1 authorization server for declared clients in
`supabase/oauth-clients.json`. A Supabase session proves authentication at the
platform boundary; Powerfarm authorization still requires a linked Identity,
the applicable Rules, and the Commit Gate.

## CI and Releases

Pull requests run kernel conformance, JCS golden vectors, static typing, SQL
parsing, immutable migration-history checks, migrations twice on temporary
PostgreSQL 17 without Docker, privilege invariants, shell checks, and a byte-for-byte
package reproducibility check. `main` is protected by the versioned ruleset in
`.github/rulesets/main.json`.

A `v*` tag on `main` builds one deterministic macOS arm64 package, creates a
GitHub artifact attestation, and publishes an immutable GitHub Release. The LAB
does not compile on every push. `com.powerfarm.updater` polls the latest stable
release, verifies SHA-256 and the GitHub attestation, stages it under a versioned
release directory, runs the idempotent updater, switches the `current` symlink
atomically, and mirrors the durable package to private Supabase Storage.

```bash
deploy/macos/configure-github.sh --dry-run
deploy/macos/configure-github.sh
deploy/macos/register-github-app.sh
deploy/macos/package.sh --output dist
```

The GitHub App registration is terminal-driven except for GitHub's required
creation and installation consent pages. Its signed webhook only enters the
operational inbox; it has no database credential and no Act write authority.

Agent tools must return Command proposals. They must not connect to the database. Production
database adapters must expose the narrow `kernel.commit.Store` contract and make
`put_object` plus `append_act` one transaction; `CommitGate` remains the only history writer.

## Deliberate boundaries

The ADK runtime, Supabase Edge transport, external-effect dispatcher, and deployment manifests
remain integrations over this kernel. They must be added phase-by-phase without introducing a
second write path. The included in-memory adapter is for ceremony/conformance work, not a source
of production truth.
