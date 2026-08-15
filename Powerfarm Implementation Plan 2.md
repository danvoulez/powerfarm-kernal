# Powerfarm — Implementation Plan
### Small code, constitutional core, Google open-source parts, self-hosted

**Guiding constraints**
- Use Google *open-source software* (ADK 2.0, protobuf, etc.), **no Google Cloud services** — nothing that requires a GCP account.
- Code must be small: the Kernel is the only thing that must be perfect; everything else is a projection or an integration and can be rewritten.
- Solo dev: everything automated from day 1; nothing deploys by hand; anything done twice goes into CI.
- Deployment decided now, not later: **Supabase Cloud + one VPS**.

---

## 1. Architecture at a Glance

```
┌────────────────────────────────────────────────────────────┐
│ CLIENT (later — pure projection consumer, hash routes)     │
└────────────────────────────────────────────────────────────┘
              │ HTTPS (REST + Realtime)
┌─────────────┴───────────────┐   ┌─────────────────────────┐
│  VPS (Docker Compose)       │   │  SUPABASE CLOUD         │
│  ┌───────────────────────┐  │   │  = THE KERNEL'S HOME    │
│  │ pf-agent (ADK 2.0)    │  │   │  Postgres:              │
│  │  agent orchestration  │──┼──▶│   • objects (CAS)       │
│  │  proposes Commands    │  │   │   • acts (append-only   │
│  └───────────────────────┘  │   │     causal DAG)         │
│  ┌───────────────────────┐  │   │   • relations, registry │
│  │ pf-worker             │  │   │   • identities, keys    │
│  │  projectors, jobs     │──┼──▶│  Edge Functions:        │
│  └───────────────────────┘  │   │   pf-api (Command intake│
│  ┌───────────────────────┐  │   │   + auth verify)        │
│  │ Caddy (TLS, reverse   │  │   │  Realtime: projection   │
│  │  proxy, automatic)    │  │   │   streams to clients    │
│  └───────────────────────┘  │   │  Storage: encrypted     │
└─────────────────────────────┘   │   payload blobs (§20)   │
                                  └─────────────────────────┘
        ▲ git push to main
┌───────┴────────┐
│ GitHub Actions │  test → conformance → migrate → deploy → smoke
└────────────────┘
```

**The constitutional split:** agents *propose*, Postgres *disposes*. One single-writer commit gate lives inside Postgres. Agent containers are stateless and disposable; history is not.

**Honesty note (from review 2):** a Postgres identity column gives *allocation* order, not *commit* order — concurrent transactions can grab `seq=10`/`seq=11` and commit in reverse. So the causal ancestry DAG is constitutional truth, `seq` is an operational cursor (gaps allowed), and any global linearization is a deterministic projection. We do not buy a fake total order with a sequence.

---

## 2. Stack Decisions (and why)

| Layer | Choice | Why |
|---|---|---|
| Agent runtime | **Google ADK 2.0 (Python)** | Orchestration, tools, HITL pause/resume, `adk eval` — maps directly onto Trajectory/Review concepts; open source, runs anywhere |
| Model access | `google-genai` SDK, **Gemini API key** (or any OpenAI-compatible endpoint) | An API key is not infrastructure lock-in; the kernel never cares which model proposed a Command |
| Canonical form + hashing | **JCS (RFC 8785) + SHA-256, domain-separated** — `SHA-256("powerfarm:<kind>:v1" ‖ utf8(JCS(value)))` | Golden vectors exist and are Genesis-bound (`conformance/golden-vectors/`); every browser can verify hashes with zero codec deps; the tag makes object *species* part of identity (PF-22). Binary payloads ride as base64url strings; exact quantities use integer minor units, never floats |
| Kernel storage | **Supabase Postgres** | Insert-only Acts with causal parents; `seq` is a cursor, not order (PF-12); RLS as coarse isolation under Rules; Realtime ships projection updates with zero code |
| API edge | **Supabase Edge Functions** (Deno, ~200 lines) | Command intake, signature verification, idempotency; nothing stateful lives here |
| Long-running work | **`pf-worker`** container (Python) on the VPS | Projectors, scheduler ticks, review notifications — Edge Functions are RAM/CPU-capped, so no agent or projector code runs there |
| Deployment target | **1 VPS (Hetzner CX22-class) + Caddy + Docker Compose** | One file defines the whole self-hosted side; TLS automatic |
| CI/CD | **GitHub Actions** | Free for the scale; `adk eval` and conformance tests run as gates |
| Frontend (later) | A projection consumer only — hash-routed SPA; pick when needed | Not a day-1 concern |

**Deliberately rejected:** Vertex AI Agent Engine, Cloud Run, GKE, Pub/Sub, Cloud SQL, managed session/memory services — all are services. ADK's `DatabaseSessionService` is also rejected as a source of truth: ADK sessions are a *projection*; the Act log is truth (PF-15).

---

## 3. Repository Layout (monorepo, deliberately tiny)

```
powerfarm/
├── kernel/                  # THE CONSTITUTION — small, zero-warning, 100% tested
│   ├── canon.py             # RFC 8785 JCS encode; domain-tagged hash = object id
│   ├── types.py             # Identity, Act, Relation, Command, Context (frozen dataclasses)
│   ├── rules.py             # authorize(I,C,X,G≤c,R_c) — pure function, declared context keys
│   ├── commit.py            # the ONLY writer of acts; runs inside one DB transaction
│   └── project.py           # deterministic projector protocol P(G_≤t)
├── genesis/
│   ├── genesis.yaml         # spec hash, canon version, hash algo, constitutional rules
│   └── ceremony.py          # GenesisCreated → … → GenesisClosed; prints genesis_root_hash
├── migrations/              # Supabase SQL migrations — the schema IS history
│   └── 0001_genesis.sql     # objects, acts (append-only), relations, registry, identities
├── agent/                   # pf-agent: ADK 2.0 wiring
│   ├── main.py              # agents, tools, graph workflow
│   ├── tools.py             # every tool call ends as a Command proposal, never a write
│   └── evals/               # adk eval suites → simulated trajectories (simulated_from)
├── worker/                  # pf-worker: projectors + scheduler + notifications
├── edge/pf-api/             # Supabase Edge Function: intake + verify (Deno)
├── conformance/             # PF-01…PF-26 executable tests + golden-vectors/
├── docker-compose.yml       # caddy + pf-agent + pf-worker
├── Caddyfile
└── .github/workflows/ci.yml
```

**Size discipline:** `kernel/` should stay under ~1,500 lines. If a feature can't be expressed as Commands + Rules + Acts + a projector, it doesn't go in the kernel.

---

## 4. Database Schema — the constitutional minimum

Six tables. Everything else is a projection.

```sql
-- CAS object store (PF-08, PF-11)
objects(hash text primary key, canon bytea not null, kind text not null);

-- Append-only history (PF-07). seq = operational cursor ONLY (PF-12):
-- gaps allowed, never used as proof of order. Causal truth is parents[].
acts(seq bigint generated always as identity primary key,
     hash text not null unique references objects(hash),  -- PF-23: unique occurrence,
                                                          -- resubmission idempotent
     act_type text not null,                 -- registered type only (PF-02)
     identity_hash text not null,
     parents jsonb not null,                 -- causal parents by hash (ancestry DAG)
     decision_cut jsonb not null,            -- cut c the authorization saw (PF-13, TOCTOU)
     command_hash text, auth_chain jsonb,    -- AuthorizationRequested→…→Resolved (PF-15)
     registry_cut jsonb not null,            -- exact rule/registry versions (PF-21)
     context_hash text not null);            -- authorizing context (PF-14)
-- anchor hook reserved from Genesis (PF-26): temporal anchors arrive later as
-- anchored_at / notarized_by relations, never as edits to acts.

-- No UPDATE, no DELETE, ever:
revoke update, delete on acts from public;
-- enforced again by trigger that raises on any mutation attempt

relations(hash text primary key references objects(hash),
          from_hash text not null, to_hash text not null,
          relation_type text not null, payload_hash text references objects(hash));

registry(hash text primary key, kind text not null,     -- type/rule/projector/context…
         version bigint not null, constitutional boolean not null default false);

identities(hash text primary key, kind text not null,   -- human/agent/service/…
           created_act text not null references acts(hash));

identity_keys(identity_hash text, pubkey text, valid_from_act text, valid_until_act text);
-- current keys = projection over this table (§5.1)
```

Materialized projections live in separate `proj_*` tables, each row stamped with `(projector_hash, history_cut)` — stale rows are detected, never trusted (PF-16).

---

## 5. The Only Write Path

There is exactly one function that can create history:

```python
def commit(conn, command, decision, context) -> Act:
    # 1. verify signature → identity + key valid at this cut         (PF-01)
    # 2. types registered at registry cut                            (PF-02)
    # 3. decision ∈ {allow} — deny/review paths emit lifecycle acts  (PF-03..06)
    # 4. TOCTOU: if history advanced past decision.cut c → reauthorize
    #    unless an explicit Rule permits commit against c' > c       (PF-13)
    # 5. canon + domain-tagged hash → object; UNIQUE(hash) makes
    #    resubmission idempotent, never a second placement   (PF-08/22/23)
    # 6. INSERT act with causal parents; seq is just a cursor        (PF-12)
    # 7. ONE transaction per commit; concurrency resolved by the
    #    single-writer gate, not by pretending seq is commit order
```

**External effects never shortcut this gate.** Effects on the outside world follow the phase protocol `Requested → Authorized → Dispatched → Observed → Committed-as-external-fact`, each phase its own Act; a DB commit never claims external reality committed (PF-24). The dispatcher (in `pf-worker`) is the only component that talks to the outside, and it writes `Dispatched`/`DispatchFailed` Acts, not "done" flags.

Agents, Edge Functions, the worker, future UIs — **all** propose Commands; none touch `acts`. This is the "small and powerful" trick: power comes from one narrow gate, not from many features.

---

## 6. ADK 2.0 Integration Contract

| ADK surface | Powerfarm rule |
|---|---|
| Tool call wanting real effect | Returns a **Command object**; `pf-api` submits it; the tool's "result" is the Command hash. The consequential Act arrives asynchronously |
| HITL pause | Emits `ReviewRequested`; resume webhook feeds the Reviewer's `AuthorizationReviewed` Act back into Rules reevaluation |
| `adk eval` runs | Written as **simulated** Acts with `simulated_from` lineage — never mixed into observed history (§23) |
| Session state | Kept in ADK's own store as a *disposable projection*; reconstructible from Acts on demand |
| Agent identity | Each ADK agent gets a Powerfarm Identity + keypair at provisioning; every Command signed (PF-01) |

---

## 7. CI/CD Pipeline (`.github/workflows/ci.yml`)

```yaml
on: [pull_request]               # gate 1: correctness
  - ruff + mypy (zero warnings)  # kernel must be warning-free
  - pytest kernel/ conformance/  # PF-01..PF-26 against ephemeral Supabase branch
  - golden canonicalization/hash vectors  # PF-22: byte-exact, cross-implementation
  - adk eval agent/evals/        # agent regression suite
  - supabase db lint

on: push: branches: [main]       # gate 2: ship
  - supabase db push             # migrations from git, reviewed as PR diffs
  - supabase functions deploy pf-api
  - build & push images → ghcr.io
  - ssh vps 'docker compose pull && docker compose up -d'
  - smoke test: replay genesis + golden Command→Act chain; fail loud, rollback alert
```

Solo-dev economics: **a PR is your staging environment** (Supabase branch), **merge is your deploy**, and the smoke test is your pager. No dashboards to babysit.

---

## 8. Phased Build Order (Genesis order, of course)

Each phase ends green in CI before the next begins.

| Phase | Deliverable | Exit test |
|---|---|---|
| **0. Genesis** | `migrations/0001`, `genesis.yaml`, ceremony script | Genesis closes; `genesis_root_hash` stable across replays |
| **1. Registry + Identity** | schema + `kernel/types.py`, key rotation path | Register a type via Command→Act; rotate a key via Act |
| **2. Command + Rules + Act** | `canon.py`, `rules.py`, `commit.py`, `pf-api` | Signed Command → allow → Act → hash verifies; tampered Command fails loud |
| **3. Reviewer** | HITL loop end-to-end | `require_review` blocks; Review Act unblocks; chain visible in graph |
| **4. Projections** | `pf-worker`, `proj_*` tables, Realtime stream | Delete all `proj_*`; rebuild bit-identical (PF-16) |
| **5. Agent** | ADK 2.0 wired through Command contract | Agent proposes; only authorized intents become Acts |
| **6. Self-government** | Rule/Registry change flows | Change a governed Rule via Command; attempt on a constitutional Rule fails loud; constitution changes only via Genesis-born amendment protocol or fork with new `genesis_root_hash` (PF-25) |
| **7. Platform pieces** | scheduler, files, notifications… as compositions | each is Commands+Rules+Acts+projector, nothing kernel-new |

---

## 9. Non-negotiables (merge checklist)

- Zero warnings (lint + types). "Seems to work" is not done — conformance green is done.
- Every new Act type lands with: registry migration + conformance test + projector handling.
- No writes outside `commit()`. Any PR adding one is rejected by review *and* by a CI check (static scan for `INSERT INTO acts` outside `kernel/commit.py`).
- Fail loud: missing context key, unknown type, stale projection stamp, authorization against a moved cut → hard error, never a default.
- Canonicalization is pinned by the six golden JCS vectors in CI — every implementation passes all of them byte-exactly, or nothing merges.
- `seq` is a cursor, never an argument in a correctness proof; causal claims cite parents.
- Determinism: projectors never read wall-clock, randomness, or the network.
- Secrets in GitHub Secrets / Supabase Vault only; plaintext never enters an Act (PF-18).

---

## 10. What This Buys You

- **~2,500 lines of code you actually own**; the rest is Postgres, ADK, and generated plumbing.
- **Deployment from day 1** that the final architecture still uses — no migration cliff.
- **Agents with constitutional supervision**: ADK gives you orchestration power, Powerfarm guarantees no model output becomes fact without `Command → Rules → Act`.
- **An audit trail you can defend**: every state reconstructible, every authorization chain inspectable, `genesis_root_hash` as your universe's fingerprint.
