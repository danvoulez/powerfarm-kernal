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
  - Python venv under POWERFARM_HOME
  - versioned install receipts
       |
       | DATABASE_URL
       v
SUPABASE CLOUD
  - Postgres: objects, acts, relations, registry, identities, keys
  - Auth boundary tables
  - Realtime / Storage later as projections and blob surfaces
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
├── bootstrap/v0/            # Kimi institutional bootstrap artifact
├── conformance/             # golden vectors + kernel invariants
├── deploy/macos/            # install/update/uninstall/doctor/smoke
└── tests/
```

The Kimi `bootstrap/v0` package is preserved as a ceremony artifact. It is not
the production Act write path and does not replace the JCS/domain-tagged kernel.

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
| `update.sh` | Re-run convergence after git pull; safe to repeat |
| `uninstall.sh` | Stop launchd jobs and remove generated config; preserve data unless `--purge` |
| `doctor.sh` | Check required local tools and installed files |
| `smoke.sh` | Verify local worker health and Cloudflare ingress rules |

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
