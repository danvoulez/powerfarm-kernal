# Powerfarm - Implementation Plan
### Small code, constitutional core, macOS LAB, Supabase, Cloudflare

**Guiding constraints**

- Use Google open-source software where useful, but no Google Cloud services.
- Code stays small: the Kernel is the only thing that must be perfect.
- Solo dev: anything done twice becomes a script or CI check.
- Deployment target is fixed: **Supabase Cloud + one macOS LAB + Cloudflare DNS/Tunnel**.
- No Docker, no Compose, no containers. Runtime processes are direct macOS launchd agents.

---

## 1. Architecture at a Glance

```
CLIENTS / AGENTS
       |
       | HTTPS
       v
CLOUDFLARE DNS + DEDICATED TUNNEL
       |
       | outbound-only connector
       v
macOS LAB
  - com.powerfarm.worker  (launchd)
  - com.powerfarm.tunnel  (launchd)
  - com.powerfarm.updater (launchd)
  - Python venv under POWERFARM_HOME
  - versioned install receipts
       |
       | DATABASE_URL
       v
SUPABASE CLOUD
  - Postgres: objects, acts, relations, registry, identities, keys
  - Auth: passkeys, sessions, OAuth 2.1 authorization server
  - private Storage: remote ledger and durable update packages
  - projection, ADK, and trajectory query substrates
```

**The constitutional split:** agents propose, the local worker exposes the commit
surface, and Supabase Postgres persists truth. launchd processes are disposable;
history is not.

`seq` remains an operational cursor, never proof of constitutional ordering.
Causal ancestry is the source of truth.

---

## 2. Stack Decisions

| Layer | Choice | Why |
|---|---|---|
| Canonical form + hashing | JCS (RFC 8785) + SHA-256, domain-separated | Browser-verifiable, byte-exact golden vectors, Genesis-bound tag namespace |
| Kernel storage | Supabase Postgres | Append-only Acts, CAS objects, Registry, Identity, auth boundary |
| Local runtime | macOS launchd | Native Mac LAB operation with automatic restart and no container layer |
| Public ingress | Cloudflare DNS + dedicated locally-managed Tunnel | No inbound router ports; `api.powerfarm.app` reaches local `pf-worker` |
| Install/update | `deploy/macos` scripts | Idempotent convergence, versioned receipts, smoke/doctor checks |
| Human authentication | Supabase Auth passkeys | Managed WebAuthn for RP ID `powerfarm.app`; platform authentication remains separate from Kernel authorization |
| Automation identity | GitHub App | Narrow webhook and repository permissions without a long-lived personal token on the LAB |
| CI/CD | GitHub Actions + artifact attestations | Hosted checks/builds; the LAB only pulls, verifies, and converges signed releases |
| Agent runtime | Google ADK later | Agent proposes Commands only; no database write path |

Deliberately rejected: Docker, Docker Compose, Caddy, VPS container deployment,
Google Cloud services, and ADK session state as a source of truth.

---

## 3. Repository Layout

```
powerfarm-kernel/
├── kernel/                  # constitutional kernel
│   ├── canon.py             # RFC 8785 JCS encode; domain-tagged hash
│   ├── types.py             # frozen Identity, Act, Relation, Command, Context
│   ├── rules.py             # pure authorization
│   ├── commit.py            # single commit gate abstraction
│   └── project.py           # deterministic projector protocol
├── genesis/
│   ├── genesis.yaml
│   └── ceremony.py
├── supabase/migrations/     # idempotent schema package
├── agent/                   # Command proposal helpers now; ADK later
├── worker/                  # launchd-run local worker
├── conformance/             # golden vectors + kernel invariants
├── deploy/macos/            # lifecycle, updater, Auth, Keychain, GitHub App
├── .github/workflows/       # hosted CI and attested release pipeline
├── .github/rulesets/        # versioned main protection contract
├── scripts/ci/              # SQL, migration, and package checks
└── tests/
```

`genesis/genesis.yaml` and `genesis/ceremony.py` define the only Genesis path.
There is no alternate bootstrap ledger or legacy canonicalization path.

---

## 4. Database Schema

Six constitutional tables remain the minimum:

- `objects`
- `acts`
- `relations`
- `registry`
- `identities`
- `identity_keys`

Auth boundary/projection tables live beside them:

- `identity_links`
- `oauth_applications`
- `authorization_proofs`

All schema changes are committed under `supabase/migrations/` and applied by the
macOS pack using `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f <migration>`.
Migrations must remain idempotent so install and update can converge safely.

---

## 5. Local macOS Pack Contract

`deploy/macos` owns the operating lifecycle.

| Script | Contract |
|---|---|
| `install.sh` | Create/reuse LAB dirs, Python venv, Supabase schema, Cloudflare tunnel/DNS, launchd plists, receipt |
| `update.sh` | Converge an already verified versioned package; safe to repeat |
| `uninstall.sh` | Stop launchd jobs and remove generated config; preserve data unless `--purge` |
| `doctor.sh` | Check required local tools and installed files |
| `smoke.sh` | Verify local worker health and Cloudflare ingress rules |
| `check-update.sh` | Poll latest stable release, verify checksum and attestation, then invoke `update.sh` |
| `configure-auth.sh` | Converge managed Supabase Auth settings from `supabase/config.toml` |
| `ensure-oauth-clients.sh` | Create/update declared OAuth clients by stable client name |
| `configure-github.sh` | Converge the protected-main ruleset and repository security settings |
| `register-github-app.sh` | Create a GitHub App through the Manifest flow and store its credentials in Keychain |

Receipts are written under `POWERFARM_HOME/receipts` with pack version, git
commit, action, hostname, and timestamp. Secrets are never written to receipts.

---

## 6. Cloudflare Boundary

Cloudflare owns public ingress for `powerfarm.app`.

The pack uses a dedicated locally-managed tunnel:

- tunnel name: `powerfarm-lab` by default;
- API hostname: `api.powerfarm.app`;
- optional app hostname: `app.powerfarm.app`;
- local service: `http://localhost:$POWERFARM_PORT`;
- launchd label: `com.powerfarm.tunnel`.

The tunnel is outbound-only from the Mac LAB. DNS routes are created with
`cloudflared tunnel route dns`, which creates the CNAME to the tunnel target.

---

## 7. Supabase Boundary

Supabase owns managed Postgres and related platform services.

The pack requires `DATABASE_URL` and applies migrations directly. It does not
store a service role key in public clients and does not grant direct browser
write access to kernel tables. RLS remains defense in depth; consequential writes
must pass through the commit gate.

Supabase Auth is configured from `supabase/config.toml`: passkeys are enabled for
RP ID `powerfarm.app`, allowed origins are explicit, the OAuth 2.1 authorization
server is enabled, and dynamic client registration is disabled. OAuth clients
are declarative in `supabase/oauth-clients.json`. Management tokens, backend
secret keys, GitHub App credentials, and webhook secrets live in the macOS
Keychain. Supabase user/session identity is linked to a Powerfarm Identity at the
boundary and never substitutes for a cut-aware authorization decision.

---

## 8. Phased Build Order

| Phase | Deliverable | Exit test |
|---|---|---|
| 0. Genesis | migrations, `genesis.yaml`, ceremony script | stable `genesis_root_hash` |
| 1. macOS Pack | launchd worker/tunnel, install/update/uninstall | repeated install/update converges |
| 2. Registry + Identity | complete registry bootstrap and key rotation | register type and rotate key via Act |
| 3. Command + Rules + Act | Postgres Store adapter for `CommitGate` | signed Command -> Act; tamper fails loud |
| 4. Lifecycle + Review | command lifecycle Acts and reviewer flow | require_review blocks, review unblocks |
| 5. Projections | projector tables and rebuild path | delete projections, rebuild bit-identical |
| 6. Agent | ADK wired through Command contract | agent proposes; only authorized intents become Acts |
| 7. Self-government | rule/registry/authority flows | constitutional edits fail except amendment/fork |

---

## 9. Non-negotiables

- No Docker artifacts or Compose paths.
- Zero warnings: `ruff`, `mypy`, `pytest`.
- Every new Act type lands with registry migration, conformance test, and projector handling.
- No writes outside the commit gate.
- Missing context key, unknown type, stale projection, or moved cut fails loud.
- Golden JCS vectors stay byte-exact.
- Install/update/uninstall are idempotent and receipt-producing.
- Secrets stay in env files or managed secret stores, never in Acts or receipts.

---

## 10. Ledger and Database Adapter Plan

This section is the practical ledger plan. It intentionally avoids inventing a
large governance universe before the kernel can write one real Act.

### 10.1 Ledger Definition

For the first operational pack, "ledger" means the persisted Postgres history
surface made from:

- `objects`: content-addressed canonical bytes;
- `acts`: append-only accepted occurrences;
- `relations`: typed edges between content-addressed objects;
- `registry`: versioned vocabulary for command types, act types, relation types,
  context types, rules, and projectors;
- `identities` and `identity_keys`: actor identity and key history;
- auth boundary/projection tables such as `identity_links`, `oauth_applications`,
  and `authorization_proofs`.

The Postgres ledger above is the sole persisted history surface.

### 10.2 Migrations Already Present

| Migration | Status | Purpose |
|---|---|---|
| `20260815060311_powerfarm_baseline.sql` | present | Clean idempotent baseline embedding the schema already present in the live database: six constitutional tables, auth boundary tables, indexes, append-only trigger, RLS enables, and baseline revokes |

This baseline is idempotent and is applied by `deploy/macos/install.sh` and
`deploy/macos/update.sh` through `psql "$DATABASE_URL" -v ON_ERROR_STOP=1`.
It is a psql-pack baseline, not a remote database reset. If the project later
switches to Supabase CLI migration history as the deploy source of truth, first
reconcile remote history with `supabase migration squash` / `repair`.

### 10.3 Packaged Migrations After the Baseline

These files are present and must execute in timestamp order. Each file is one
transaction and the complete sequence has been verified by applying it twice to
a fresh PostgreSQL 15 database. The target Supabase project runs PostgreSQL 17.

| Migration | Status | Purpose |
|---|---|---|
| `20260815123236_registry_seed.sql` | implemented | Operational Genesis manifest for command, Act, relation, context, rule, and projector definitions; entries become authoritative only when admitted into the Registry by Acts |
| `20260815123237_identity_key_lookup.sql` | implemented | Cut-aware identity-key lookup and open-key projection view |
| `20260815123238_ledger_integrity_checks.sql` | implemented | Hash-array validation, Act insert checks, immutable ledger triggers, indexes, and deferred legacy constraints |
| `20260815123239_commit_gate_rpc.sql` | implemented | Private atomic CAS-plus-Act commit function with replay, history-cut, Registry, parent, identity, Context, and Rule checks |
| `20260815123240_projection_metadata.sql` | implemented | Projection runs/checkpoints plus generic materialized graph nodes and edges |
| `20260815123241_adk_integration_substrate.sql` | implemented | Non-authoritative ADK event, workflow-node, tool-call, and artifact staging |
| `20260815123243_trajectory_projection_substrate.sql` | implemented | Selector, run, node, edge, feature, and annotation projections for trajectory engineering |
| `20260815123244_storage_artifacts.sql` | implemented | Content-addressed metadata for remote ledger segments and durable update packages; no direct writes to `storage.*` |
| `20260815123245_rls_grants_final.sql` | implemented | Deny-by-default Data API grants and worker-only RLS policies/capabilities |
| `20260815123246_migration_receipts.sql` | implemented | Immutable remote receipts for install, update, and uninstall convergence |

The SQL files are the normative physical schema. The logical sketches below
explain intent and may omit operational columns, checks, and indexes.

Do not add domain ledgers such as farms, billing, jobs, or notifications until
the generic commit path is live. Those are projections or later Acts.

### 10.4 Communication With Supabase Postgres

The Mac LAB worker talks to Supabase Postgres directly with `DATABASE_URL` from
the private installed env file at `POWERFARM_HOME/powerfarm.env`.

Rules:

- only `com.powerfarm.worker` receives `DATABASE_URL`;
- agents, browser clients, and Cloudflare do not receive database credentials;
- migrations use `psql` from install/update only;
- runtime writes use the Python Postgres adapter only;
- every write uses one transaction;
- failed transactions leave no partial CAS object without its Act;
- `statement_timeout` and `lock_timeout` should be set per connection once the
  adapter lands;
- the worker should use pooled Supabase Postgres for normal runtime and direct
  Postgres only when a migration requires it.

The first Python dependency for the adapter should be `psycopg[binary,pool]`
unless a later benchmark or deployment constraint says otherwise. The adapter is
small enough to keep under `worker/postgres_store.py`.

### 10.5 Postgres Store Adapter Contract

`PostgresStore` implements the existing `kernel.commit.Store` protocol:

```python
class PostgresStore:
    def history_cut(self) -> frozenset[str]: ...
    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool: ...
    def has_object(self, object_hash: str) -> bool: ...
    def has_act(self, act_hash: str) -> bool: ...
    def put_object(self, object_hash: str, canon: bytes, kind: str) -> None: ...
    def append_act(self, act: Act) -> None: ...
    def get_act_for_command(self, command_hash: str) -> Act | None: ...
```

Implementation rules:

- `CommitGate.commit()` remains the only Python caller that creates
  consequential Acts;
- `put_object()` and `append_act()` are executed inside one transaction owned by
  `PostgresStore.commit_transaction(...)` or an equivalent context manager;
- duplicate `command_hash` returns the existing Act, not an error;
- duplicate object hash with different bytes/kind is a hard collision error;
- parent references must exist in `acts`;
- payload references must exist in `objects`;
- registry checks read the exact `registry_cut` supplied by the authorization
  decision;
- the adapter returns frozen kernel dataclasses, not raw SQL rows.

### 10.6 `/commit` Worker Contract

The first real `/commit` endpoint is local-worker HTTP over the Cloudflare
Tunnel. It accepts a signed Command envelope and either returns an existing Act
or creates one.

Minimal request shape:

```json
{
  "identity": {
    "hash": "<identity hash>",
    "kind": "human|agent|service",
    "public_key": "<base64url raw ed25519 public key>"
  },
  "command": {
    "command_type": "<registered command type>",
    "identity_hash": "<identity hash>",
    "payload_hash": "<object hash>",
    "parents": ["<act hash>"],
    "nonce": "<unique nonce>",
    "signature": "<base64url raw ed25519 signature>"
  },
  "context": {
    "values": {},
    "types": {}
  },
  "act_type": "<registered act type>"
}
```

Response codes:

- `200`: idempotent replay; existing Act returned;
- `201`: new Act committed;
- `400`: malformed request or unknown canonical value;
- `401`: signature or identity proof failure;
- `409`: moved history cut, missing parent, missing payload, registry mismatch,
  or uniqueness collision;
- `422`: rules deny or require review;
- `500`: unexpected adapter/database failure.

The endpoint may initially run only on localhost and through
`api.powerfarm.app`; it must not expose a direct database capability to clients.

### 10.7 Projection Substrate

Projections are vital and need their own storage substrate. They are not a
second source of truth; they are queryable, rebuildable graph views over the
ledger.

Minimum generic tables for `projection_metadata.sql`:

```sql
projection_runs(
  run_hash text primary key,
  projector_hash text not null,
  input_cut jsonb not null,
  input_cut_hash text not null,
  status text not null check (status in ('running','complete','failed')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error jsonb
);

projection_checkpoints(
  projector_hash text primary key,
  input_cut jsonb not null,
  input_cut_hash text not null,
  high_water_seq bigint,
  run_hash text not null references projection_runs(run_hash),
  updated_at timestamptz not null default now()
);

proj_graph_nodes(
  projector_hash text not null,
  input_cut_hash text not null,
  node_hash text not null,
  node_kind text not null,
  labels jsonb not null default '[]'::jsonb,
  properties jsonb not null default '{}'::jsonb,
  primary key (projector_hash, input_cut_hash, node_hash)
);

proj_graph_edges(
  projector_hash text not null,
  input_cut_hash text not null,
  edge_hash text not null,
  from_hash text not null,
  to_hash text not null,
  edge_type text not null,
  properties jsonb not null default '{}'::jsonb,
  primary key (projector_hash, input_cut_hash, edge_hash)
);
```

Rules:

- `input_cut_hash` is the canonical hash of the ancestry-closed Act set used by
  the projector;
- `high_water_seq` is an optimization cursor only;
- graph nodes/edges must always be reconstructible from `objects`, `acts`,
  `relations`, and the registered projector version;
- failed projection runs keep their error payload for debugging but confer no
  authority;
- deleting every `proj_*` table must not delete history.

### 10.8 ADK Integration Preparation

ADK 2.0 is graph-oriented: agents, tools, and functions execute as nodes in a
workflow graph; Events carry workflow metadata such as `node_info` and `output`;
callbacks are the safe capture points; long-running tools model pause/resume and
HITL; MCP/A2A expose external tool and agent boundaries.

Powerfarm should prepare for ADK without depending on ADK as truth. The
implemented schema uses `(workflow_hash, node_id)` as the stable workflow-node
identity and links tool calls and artifacts to that pair.

Minimum tables for `adk_integration_substrate.sql`:

```sql
adk_event_envelopes(
  event_hash text primary key,
  adk_app text not null,
  adk_session_id text not null,
  invocation_id text,
  author text,
  node_info jsonb,
  output jsonb,
  actions jsonb,
  event_json jsonb not null,
  observed_at timestamptz not null default now(),
  linked_act text references acts(hash)
);

adk_workflow_nodes(
  node_hash text primary key,
  workflow_hash text not null,
  node_name text not null,
  node_kind text not null,
  adk_node_info jsonb not null default '{}'::jsonb
);

adk_tool_calls(
  tool_call_hash text primary key,
  event_hash text not null references adk_event_envelopes(event_hash),
  tool_name text not null,
  args_hash text,
  result_hash text,
  command_hash text,
  status text not null check (status in ('proposed','submitted','committed','failed'))
);

adk_artifact_refs(
  artifact_ref_hash text primary key,
  event_hash text references adk_event_envelopes(event_hash),
  artifact_name text not null,
  artifact_version text,
  mime_type text,
  object_hash text references objects(hash),
  storage_uri text
);
```

Rules:

- ADK envelopes are observations/staging records until linked to Acts;
- tools that want consequences return or submit Powerfarm Commands;
- ADK session state can be imported as context, but not as authoritative state;
- ADK artifacts become Powerfarm objects or storage commitments before they are
  relied upon by Rules;
- callbacks should capture telemetry and proposed Commands, not mutate the
  ledger directly;
- long-running tools map naturally to `ReviewRequested`, `AuthorizationReviewed`,
  external-effect phases, and trajectory pause/resume projections.

### 10.9 Trajectory Engineering Substrate

Trajectory engineering needs a first-class projection substrate because it asks
questions over paths, branches, evidence, retries, alternatives, simulations,
and outcomes. It should operate over the graph without mutating history.

The implemented schema gives every run an immutable selector and input-cut
stamp, orders nodes explicitly, constrains edge endpoints to nodes in the same
run, and versions computed features.

Minimum tables for `trajectory_projection_substrate.sql`:

```sql
trajectory_selectors(
  selector_hash text primary key,
  name text not null,
  purpose text not null,
  selector_json jsonb not null,
  projector_hash text not null
);

trajectory_runs(
  run_hash text primary key,
  selector_hash text not null references trajectory_selectors(selector_hash),
  input_cut jsonb not null,
  input_cut_hash text not null,
  status text not null check (status in ('running','complete','failed')),
  created_at timestamptz not null default now(),
  error jsonb
);

trajectory_nodes(
  run_hash text not null references trajectory_runs(run_hash),
  node_hash text not null,
  node_role text not null,
  depth integer,
  branch_key text,
  properties jsonb not null default '{}'::jsonb,
  primary key (run_hash, node_hash, node_role)
);

trajectory_edges(
  run_hash text not null references trajectory_runs(run_hash),
  edge_hash text not null,
  from_hash text not null,
  to_hash text not null,
  edge_role text not null,
  polarity text check (polarity in ('supports','blocks','contradicts','continues','forks','joins')),
  properties jsonb not null default '{}'::jsonb,
  primary key (run_hash, edge_hash)
);

trajectory_features(
  run_hash text not null references trajectory_runs(run_hash),
  subject_hash text not null,
  feature_kind text not null,
  value jsonb not null,
  primary key (run_hash, subject_hash, feature_kind)
);

trajectory_annotations(
  annotation_hash text primary key,
  run_hash text not null references trajectory_runs(run_hash),
  subject_hash text not null,
  annotation_type text not null,
  payload jsonb not null,
  author_identity text references identities(hash),
  source_act text references acts(hash)
);
```

Initial trajectory roles:

- `observed`: built from accepted real Acts;
- `simulated`: built from simulated Acts or ADK eval traces;
- `crafted`: built from human/agent edited trajectory objects;
- `candidate`: proposed path not yet accepted as occurrence;
- `counterfactual`: intentionally non-occurring branch for analysis.

Rules:

- trajectory tables are projections unless an annotation is explicitly committed
  as an Act;
- `simulated_from`, `crafted_from`, `forked_from`, `supports`, `contradicts`,
  and `matched_to` remain typed relations in the canonical graph;
- trajectory features are replaceable analysis outputs, not facts;
- a trajectory run is valid only for its selector, projector, and input cut;
- fold/score/risk models should write to `trajectory_features`, not mutate Acts.

This gives us the substrate for trajectory engineering without needing a full
domain ontology on day one.

### 10.10 Supabase Storage Contract

Postgres remains the transactional source of truth. Supabase Storage supplies
two private, durable object surfaces:

- `powerfarm-ledger`: content-addressed remote ledger segments and snapshots;
- `powerfarm-packages`: signed/versioned macOS update packages and manifests.

The installer creates or reuses both buckets through the Supabase Storage API.
SQL never inserts into or mutates `storage.*`. Postgres stores checksums, paths,
sizes, cuts, versions, and source Acts in `remote_ledger_segments` and
`update_packages`. Runtime upload/download uses a backend-only Supabase secret;
browser clients receive neither that secret nor direct kernel-table grants.

### 10.11 Immediate Implementation Order

1. **Implemented:** installer checksums and records each SQL file in
   `powerfarm_schema_migrations`, skipping identical versions and rejecting a
   changed checksum.
2. **Implemented:** install/update create or reuse the two private Storage buckets through
   the Storage API and emit a local plus remote pack receipt.
3. **Next:** add `worker/postgres_store.py` as the sole runtime adapter and call the
   private database commit gate through a pooled connection.
4. Replace `/commit` 501 with parsing, JCS verification, authorization, and the
   `PostgresStore` commit path.
5. Add an end-to-end smoke path that repeats the same signed Command and proves
   idempotent replay of the same Act.
6. Implement projection rebuild/checkpoint workers before domain query APIs.
7. Add ADK ingestion and trajectory scoring only through their non-authoritative
   staging/projection tables.

This is enough to make the ledger real without founding a religion around every
future domain.

### 10.12 CI/CD, Release, and Integration Identity

The delivery path is deliberately asymmetric:

```
pull request -> hosted GitHub CI -> protected main -> v* tag
             -> deterministic package + GitHub attestation + Release
             -> com.powerfarm.updater polls -> verifies -> converges LAB
```

The Mac LAB is not a self-hosted build runner and does not rebuild arbitrary
pushes. GitHub-hosted CI checks untrusted changes; only a tagged package whose
commit belongs to `main`, whose SHA-256 matches, and whose GitHub artifact
attestation verifies may reach `update.sh`. The updater stages versions under
`POWERFARM_HOME/releases/<version>` and atomically changes the `current`
symlink only after verification. The package is then mirrored by content hash
to private `powerfarm-packages` Storage and recorded in `update_packages`.

Required CI contexts are:

- `quality`: ruff, mypy, pytest, JCS/conformance and SQL static checks;
- `migrations`: PostgreSQL 17 applies all migrations twice, exercises the
  installer's checksum ledger, and verifies database-role invariants;
- `package`: shellcheck plus two byte-identical macOS package builds.

Existing migration files are sealed. A pull request may add a later migration,
but may not edit, delete, or reorder an already shipped SQL filename. Release
tags must match `deploy/macos/VERSION`, `pyproject.toml`, and
`deploy/macos/manifest.json`.

The GitHub integration is a GitHub App, not a personal access token and not a
Powerfarm human OAuth client. The terminal starts GitHub's Manifest flow, the
user performs the required consent, and credentials are placed in Keychain.
Webhook HMAC, event allowlisting, delivery deduplication, and payload limits are
verified before an event enters the operational inbox. A webhook may request
work, but it cannot write an Act or access Postgres; governed effects still
require an authenticated Powerfarm Identity, Rules, and the Commit Gate.
