# Audit — Powerfarm Fresh-Agent Execution Pack (2026-08-16)

Audit only. No code written, no repo files modified.

Scope: verify the pack's provenance and integrity, test each of its current-state
claims against the actual source, and map what stands between here and each phase gate.

Baseline recomputed, not remembered: **63 passed in 0.92s**, tree clean, HEAD `b3de7c7`.

---

## 1. Provenance and integrity

**The four attachments are one artifact.** Three are byte-identical duplicates of the
pack's own `sources/` directory:

| Attachment | SHA-256 | Identical to |
|---|---|---|
| `powerfarm-kernal-main 2.zip` | `c90e1dc6…c08799` | `sources/powerfarm-kernal-main_3fc601c.zip` |
| `cloudflare-os-main 3.zip` | `63f67b39…fedbfa` | `sources/cloudflare-os-main_ba4036b.zip` |
| `google-adk-2.7(1).0-offline` | `3a8518e7…dd5c530` | `sources/google-adk-2.7.0-offline.zip` |

`shasum -c SHA256SUMS.txt` → **19/19 OK**. The pack is internally consistent, and its
`06_Source_Map_and_Hashes.md` hashes match the files it ships.

**The pinned kernel snapshot is your working tree.** `diff -r` between the snapshot and
this repo yields zero tracked-file differences — only local cruft (`.venv`, `.mypy_cache`,
`.ruff_cache`, `build`, `.DS_Store`, and two empty dirs `tests/fixtures`,
`deploy/macos/launchd`).

One provenance wrinkle worth noting: the pack labels the snapshot `3fc601c…` and calls it a
*merge* commit. Locally, that content is `b3de7c7` sitting **1 commit ahead of `main`** on
`identity/principal-binding-acts`, and `git branch -a --contains b3de7c7` lists only that
branch and its remote — not `origin/main`. The content is what matters and it matches; but
the pack's commit identity describes a merge that your local refs don't show. Worth a
`git fetch` before anyone treats `3fc601c` as an addressable base.

---

## 2. Current-state claims — each one tested

The pack asserts specific facts about the code. All of them hold. This matters: it means the
pack was written against the real source, not from memory, so its phase design can be trusted
to be aimed at real gaps.

| Claim | Verdict | Evidence |
|---|---|---|
| `relations` has no `admitted_act` | **True** | zero hits for `admitted_act` across all `.sql`/`.py` |
| `relations` has no writer | **True** | table declared in baseline:38; no INSERT path anywhere |
| `Relation.hash` already exists | **True** | `kernel/types.py:134-143` |
| `RegisterDefinition`/`DefinitionRegistered` seeded, no runtime | **True** | appear **only** in `20260815123236_registry_seed.sql:22,42` |
| `ConfiguredRuleResolver` ignores command/context/history cut | **True** | literal `del command, context, history_cut` — `service/authority.py:93` |
| Only `genesis.root_authority` is executable | **True** | every other name raises `no executable implementation for registered Rule` — `authority.py:109` |
| `PostgresStore` methods open their own connection | **True** | every method wraps `self._pool.connection()` — `ledger/postgres.py` |
| Canonicalization is RFC 8785 JCS + SHA-256 domain separation | **True** | `kernel/canon.py` |
| ADK 2.7 public surfaces exist | **True** | `workflow.__all__` exports `BaseNode`/`Node`/`FunctionNode`/`JoinNode`/`RetryConfig`/`Workflow`; `plugins.__all__` exports `BasePlugin`; `events.__all__` exports `RequestInput` |
| `NodeTool` is on a private path | **True** | `google/adk/tools/_node_tool.py` |
| OS keys the user DO from verified email | **True** | `this.users.idFromName(email)` — `packages/workshop-backend/src/server.ts:697` |

**One correction to the pack.** It names the email seam as *the* critical change. There are
in fact **four** `idFromName` call sites in `server.ts` — `:681` (`split[0]`), `:697`
(`email`), `:726` and `:753` (`username`). Re-keying only the email path leaves three other
addressing routes into the same Durable Object namespace. Phase 3's gate ("DO key is
`identity_hash`, not email") would pass while the username paths still mint addresses
outside Powerfarm Identity.

---

## 3. Gap analysis by phase

### Phase 0a — Relations governed door
**Have:** `relations` table (`from_hash`, `to_hash`, `relation_type`, `payload_hash`),
immutability trigger (`relations_are_immutable`), three indexes, worker RLS select,
`Relation.hash` in the Kernel.
**Need:** `admitted_act` column; any writer at all; relation methods on the `Ledger`
protocol; cut-aware reads; `MemoryLedger` mirror.
**Blocked on:** the atomicity seam (§4.1).
**Unverifiable from here:** halt condition 2 (legacy `relations` rows without provable
admission). The table has never had a writer, so a clean database must be empty — but a live
Supabase project could hold hand-inserted rows. **Check before writing the migration.**

### Phase 0b — RegistryService runtime
**Have:** `registry` table, `registry_seed_manifest`, `registry_entries(kind, cut)` read path,
`RegistryEntry` dataclass carrying `definition: CanonValue`, 45 seeded definitions.
**Need:** the entire writer; `resolve_definition(kind, selector, cut)`; `constitutional=true`
root check; canonical schemas on definitions.
**Good news the pack understates:** `registry.kind` has **no CHECK constraint**. All ten
Phase 0b kinds — including `node_species`, `effect_phase`, `machinery_class`,
`disclosure_profile` — are registrable with **no DDL change**. The "small constitution,
extensible universe" claim is structurally real here, not aspirational.
**Blocked on:** the atomicity seam (§4.1).

### Phase 1 — Rules as data
**Have:** one executable Rule. `RuleResult`/`DecisionKind`. The DB already enforces
fail-closed at the gate (`commit requires at least one Rule`).
**Need:** parser, AST, static type checker, context-key extraction, typed JSON-pointer payload
access, deterministic interpreter, applicability resolver over definition hashes, explanation
output.
**Collides with PF-13** (§4.2) and **with the schema-shell problem** (§4.5).

### Phase 2 — Provisioner, generic Nodes, projections
**Have:** nothing. `proj_nodes` and `proj_node_edges` return **zero hits** across all migrations.
**Need:** both projections, `pf://nodes/{hash}` and `pf://subgraph/{hash}` resources, node
species as registered schema objects, rebuild-equivalence test.
**Depends on:** 0a + 0b.

### Phase 3 — Identity takeover of Cloudflare OS
**Further along than the pack assumes.** The kernel half largely exists: `principal_bindings`
(`20260816140000`), `LinkPrincipal`/`RevokePrincipal` → `PrincipalLinked`/`PrincipalRevoked`
vocabulary (`20260816160000`), and `resolve_principal(issuer, subject)` on the Store. The
remaining work is on the OS side.
**Need:** re-key **all four** `idFromName` sites (§2), not just the email one.
**Unverifiable from here:** halt condition 5 — whether durable OS state keyed by email already
exists. Requires the live Cloudflare account. **Produce a migration inventory first.**

### Phase 4 — Budget
**Have:** nothing. No `ReserveBudget`/`SettleBudget` vocabulary, no `budget.*` context keys.
**Depends on:** 0b, if the vocabulary is to be registered at runtime rather than by migration —
which is the whole point of 0b.

### Phase 5 — AdmitBatch
**Have:** nothing.
**Depends on:** 0a (relation admission) + 0b (species and relation definition hashes).
**Leans on** `acts_one_consequence_per_command_idx`, which has no behavioural test (§4.4).

### Phase 6 — Powerfarm Engine over ADK
**Have:** the offline pack (57 files), all required public seams verified present.
**Need:** the `powerfarm-engine` package; nothing exists yet.
**No fork needed** on current evidence — every surface the runbook names is public. Only
`NodeTool` is private, and the pack already says to avoid coupling to it.

### Phase 7 — Golden Bridge
**Not verifiable from this machine.** `danvoulez/lab-mistral-rs-gateway` is private and
deliberately not bundled. The pack pins `aaeeb87…`. Its strict-routing invariants, and halt
condition 6, cannot be checked without repo access. The pack's own warning that
`docs/GOLDEN_BRIDGE.md` carries stale sticky-route prose is itself unverified here.

### Phase 8 — Node-first OS + publication
**Have:** `projector` kind with 4 entries.
**Need:** `disclosure_profile` definitions, `PublishProjection` vocabulary, the profile
projector, `projects_as` lineage, public read surface that cannot traverse private inbound edges.

### Phase 9 — Vertical slice
Gated on everything above. 17 slice steps, ~90 acceptance checkboxes, currently 0 executable.

---

## 4. Cross-cutting risks

### 4.1 The atomicity seam is the load-bearing problem
Phases 0a, 0b and 5 **all** require inserting authoritative rows in the same transaction as
their admitting Act. Today `PostgresStore` has no cross-method transaction — every method
opens its own pooled connection. The only transactional gate is the
`powerfarm_internal.commit_act` RPC, which takes the advisory lock
(`powerfarm:commit-gate:v1`) and performs every constitutional check.

So the seam has exactly one honest shape: extend or wrap `commit_act` so relation and registry
rows land inside its transaction. Your sealed-migrations rule permits this — `commit_act` is
declared `create or replace function`, so a new migration file can replace it without editing
a sealed one.

Getting this wrong is **halt condition 7**, and the failure mode is quiet: a second hidden
write mechanism beside the gate. This is the decision I would want settled before any Phase 0
code is written, because 0a and 0b would otherwise each invent their own.

### 4.2 PF-13 fixed default vs. Rules-as-data
`commit_act` hardcodes, for every command:

> `history advanced after authorization; reauthorization required`

triggered whenever `count(acts) <> length(decision_cut)`. That is a fixed default in SQL,
beneath the Rule engine, unreachable by data. The spec (per §10.5 and your standing note)
requires this decision **per Rule** and states a silent default is forbidden.

Phase 1's entire premise is that ordinary policy moves into Rules. This constant sits
underneath it and no registered Rule can override it. **This is the collision to resolve at or
before Phase 1** — the pack does not mention it.

### 4.3 CI does not type-check the layers the pack targets
`.github/workflows/ci.yml` runs `mypy kernel worker agent genesis`. It omits **`ledger/`,
`service/`, `protocol/`** — which is precisely where Phases 0a, 0b and 1 land most of their
new code. The phases with the most new code would be the least type-checked.
`shellcheck` also globs only `deploy/macos/*.sh`, `deploy/macos/lib/*.sh`, `scripts/ci/*.sh`,
leaving `.claude/scene/compose.sh` unchecked.
Cheap to fix, and worth fixing before the code volume arrives rather than after.

### 4.4 The partial index has no behavioural test
`acts_one_consequence_per_command_idx` applies cleanly, but the rule "one consequential Act per
Command" is proven today only by the Python gate. The database's refusal is untested. Phase 5
("500 candidates → one Act") leans directly on it.

### 4.5 A sequencing gap inside the runbook itself
All 45 seeded definitions are name/version shells — `{"kind":…,"name":…,"version":…}` and
nothing more. No `payload_schema`, no `value_schema`.

Phase 1 requires *statically type-checked* payload access, and the pack states typed Rules
"must fail registration until the effective definition supplies a canonical schema." So typed
Rules over existing constitutional vocabulary require that vocabulary to first be **re-registered
at v2 with schemas, by root authority** — which is Phase 0b work.

The runbook does not call this dependency out. Phase 1 as written would stall on it. The pack
flags the fact in `06_Source_Map` but never turns it into a work item.

### 4.6 Scope spans repos not present here
Only the kernel is in this directory. Phases 3 and 8 are Cloudflare OS, Phase 7 is a private
GitHub repo, Phase 6 is a package that doesn't exist. Any "run the whole pack" plan needs those
checked out first, and Phase 7 needs credentials this machine doesn't have.

---

## 5. What the pack gets right

Worth saying plainly, because it changes how much of it to trust:

- Every current-state claim it makes is accurate.
- Its halt conditions are well chosen — condition 7 (atomicity) is exactly the real risk.
- Its refusal to grow the Kernel is structurally supported: `registry.kind` has no constraint,
  so the extensibility claim is real.
- PF-21 is already satisfied at the gate — `rule_hashes` and `registry_cut` are validated
  inside `commit_act`.
- It correctly identifies that `Store` method count is not an invariant.

## 6. What I could not verify

- Legacy `relations` rows in the live database (halt condition 2).
- Existing email-keyed durable state in Cloudflare OS (halt condition 5).
- Golden Bridge strict-routing invariants (halt condition 6) — private repo.
- Whether `3fc601c` exists as a merge on `origin/main` (local refs say no; needs a fetch).

---

## Recommended order, if this proceeds

1. **Settle the `commit_act` extension shape** (§4.1) — one decision that unblocks 0a, 0b and 5.
2. **Resolve PF-13** (§4.2) — because Phase 1 cannot be honest until it is.
3. **Widen CI** (§4.3) — cheap, and it should precede the code volume.
4. Then Phase 0a, with the live-database relation-row check done first.

Items 1 and 2 are constitutional decisions, not implementation. They are yours to make, and
the pack does not make them for you.
