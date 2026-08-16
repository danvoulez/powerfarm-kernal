# Powerfarm Director & Genesis Authority — Decision Memo

Audit cut `b3de7c7`, 2026-08-16. No code, migrations, commits, or database mutations.
Verified against source and normative specification; pack claims and prior analysis re-tested
rather than assumed.

---

## 1. Executive finding

**Dan cannot currently exist in Powerfarm at all — as Director or as anything else.** This is not
a gap in the Director design. It is the absence of every substrate the Director design would
stand on:

- `CreateIdentity` has **no runtime**. No Identity can be created through the system.
- `public.registry` has **no writer**. It is empty.
- `commit_act` requires command and act types to be registered at the declared registry cut, so
  with an empty Registry **no consequential Act can commit through Postgres at all**.
- Genesis has **never been materialized**. `ceremony.py` prints JSON; nothing admits it.
- There is **no authority substrate**: no grant table, and none of §17's self-government
  vocabulary (`GrantAuthority`, `AuthorityGranted`, `AppointReviewer`, `ReviewerAppointed`,
  `AgentDelegated`, `RegisterCommand`, `ChangeRule`) is registered anywhere.

Today, authority in Powerfarm is exactly one branch: `identity.hash == root_identity_hash →
ALLOW`, everything else `DENY` ([service/authority.py:65-67](../../service/authority.py:65)). And
`root_identity_hash` is `os.environ.get("POWERFARM_ROOT_IDENTITY_HASH")`
([service/runtime.py:42](../../service/runtime.py:42)).

**So the honest answer to "what does 'Dan is Powerfarm's Director' mean inside Powerfarm's own
authority model" is: nothing yet, and the thing blocking it is not Director design — it is that
authority itself is currently a mutable environment variable rather than governed history.**

Your hypothesis is correct and the specification supports it: **Director should be a governed
institutional office held by Dan's Identity, not an alias for Root.** §17 already names the
mechanism (`GrantAuthority → Rules → AuthorityGranted`), §14 already names the projection
(`active_grants`), §5.1 already guarantees Identity survives key rotation, and §9 already
provides delegation and separation-of-duties through Rules without new primitives. The
architecture wants this shape. Nothing needs to be invented.

But there is a prerequisite that dominates everything else:

> **Director is decorative until Root is bound at Genesis.** If `POWERFARM_ROOT_IDENTITY_HASH`
> remains an environment variable, then whoever controls deployment is silently omnipotent, and
> a governed Director office sits on top of an ungoverned one. Making Dan Director without
> fixing this would produce exactly the hidden administrative authority you asked to avoid.

The most important prerequisite decisions, in order: bind Root and the Registry seed into
`genesis_root_hash` (they currently are not); decide the amendment protocol before first Genesis
(it is currently a name with no content); and constrain Root's post-Genesis powers by a
Genesis-born constitutional Rule, so that Root is a bootstrap membrane rather than a permanent
throne.

---

## 2. Evidence table

| Claim | Evidence | File/location | Confidence |
|---|---|---|---|
| Four attachments are one pack; three are byte-identical duplicates of its `sources/` | SHA-256 compared | `c90e1dc6…`, `63f67b39…`, `3a8518e7…` match bundled zips | Certain |
| Pack integrity manifest validates | `shasum -c` | `SHA256SUMS.txt`, 19/19 OK | Certain |
| Pinned kernel snapshot is the live working tree | `diff -r`, zero tracked differences | snapshot vs repo | Certain |
| Normative spec is v3.2; pack docs are implementation notes | Authority order + content | `Powerfarm System Specification v3.md:1` | High |
| Genesis never materialized | No writer; ceremony is a pure printer | [genesis/ceremony.py:15-30](../../genesis/ceremony.py:15) | Certain |
| Registry has no writer | No `insert into public.registry` in any migration | `supabase/migrations/*` | Certain |
| Seed manifest is declarative only | Comment states it | `20260815123236_registry_seed.sql:1-3` | Certain |
| Bootstrap recursion is real | `RegisterDefinition` is a `command_type`; `commit_act` requires registered command type | `20260816130000…sql` (commit_act body); seed:22 | Certain |
| Root identity is an env var | `os.environ.get` | [service/runtime.py:42](../../service/runtime.py:42) | Certain |
| `genesis_root_hash` is an env var defaulting to `"unset"` | `os.environ.get(..., "unset")` | [protocol/mcp/server.py:87](../../protocol/mcp/server.py:87) | Certain |
| `genesis.yaml` omits initial Registry definitions and Root Identity/keys | File is 19 lines; both absent | [genesis/genesis.yaml](../../genesis/genesis.yaml) vs spec:653-663 | Certain |
| §16 requires nine bindings incl. those two | Enumerated list | `spec:653-663` | Certain |
| `amendment-or-fork` is a name with no content | Appears only in the YAML list | `genesis.yaml:10` | Certain |
| Amendment protocol must be Genesis-born, not invented later | "must itself be born at Genesis; it cannot be invented later" | `spec §4.2:195` | Certain |
| PF-25 forbids a third administrative door | Verbatim | `spec:1055` | Certain |
| §17 names the authority vocabulary | `GrantAuthority → Rules → AuthorityGranted` | `spec:676` | Certain |
| None of §17's vocabulary is registered | Checked each name against migrations | all absent | Certain |
| No authority/grant table exists | Full table enumeration (29 tables) | `supabase/migrations/*` | Certain |
| §14 anticipates `active_grants` as a projection | Named as example materialized State | `spec:596` | High |
| §5.1 separates Identity from key material | "Key rotation does not create a new Identity" | `spec:237-243` | Certain |
| PF-13 declared at Genesis as `declared-decision-cut` | Named in constitutional_rules | `genesis.yaml:9` | Certain |
| PF-13 enforced by three hardcoded checks, no Rule attribution | Three sites | [service/authority.py:189](../../service/authority.py:189), [kernel/commit.py:77](../../kernel/commit.py:77), `commit_act` RPC | Certain |
| `history_cut` is whole-history equality | `select hash from public.acts` | [ledger/postgres.py:65-68](../../ledger/postgres.py:65) | Certain |
| Decision records all resolved Rule hashes | `tuple(rule.hash for rule in rules)` | [kernel/rules.py:51](../../kernel/rules.py:51) | Certain |
| Rules statically declare context keys; missing key fails loud | `rule.context_keys - context.values.keys()` | [kernel/rules.py:39-41](../../kernel/rules.py:39) | Certain |
| Authorization combines fail-closed (DENY > REVIEW > ALLOW) | Outcome folding | [kernel/rules.py:45-50](../../kernel/rules.py:45) | Certain |
| `powerfarm_worker` has select-only on registry/relations | grant statement | `20260815123245_rls_grants_final.sql:29` | Certain |
| `commit_act` is the sole granted write door | grant execute | same file:50 | Certain |
| `commit_act` holds an advisory lock | `pg_advisory_xact_lock('powerfarm:commit-gate:v1')` | `20260816130000…sql` | Certain |
| `CreateIdentity` has no runtime | No Python references | repo-wide grep | Certain |
| `identity_links` has no writer | No Python references | repo-wide grep | Certain |
| MCP surface is generic (`action.commit` etc.), not per-command | Six tools | [protocol/mcp/tools.py:22-138](../../protocol/mcp/tools.py:22) | Certain |
| Golden Bridge absent from this repo entirely | Zero references to gateway/mistral | repo-wide grep | Certain |
| Cloudflare OS keys DO from email; four `idFromName` sites | grep | `packages/workshop-backend/src/server.ts:681,697,726,753` | High |
| ADK 2.7 public seams exist; `NodeTool` private | wheel `__all__` inspection | `google/adk/{workflow,plugins,events}/__init__.py`; `tools/_node_tool.py` | Certain |

---

## 3. Current constitutional state

What Powerfarm actually has, as distinct from what the pack says it has.

**Materialized and working.** A stateless MCP boundary (§18.1) with six generic tools. A Kernel
whose CommitGate performs signature verification, outcome/act-type matching, one-consequence-per-
Command, structural review-chain proof, cut checks, registration checks and CAS preconditions
([kernel/commit.py](../../kernel/commit.py)). RFC 8785 JCS canonicalization with domain separation.
A Postgres `commit_act` RPC that re-performs the constitutional checks under an advisory lock.
A grant posture that makes authoritative tables select-only. 63 passing tests — all against
`MemoryLedger`.

**Declared but not materialized.** Genesis (five Acts, never admitted). Four constitutional Rules
(names only). The entire Registry (seed manifest, no promoter). `RegisterDefinition`,
`CreateIdentity`, `RotateKey` (vocabulary shells, no runtime).

**Absent entirely.** Any authority model beyond the Root env-var comparison. All of §17's
self-government vocabulary. `relations` writer and `admitted_act`. `proj_nodes`/`proj_node_edges`.
Budget, AdmitBatch, Engine, publication. Golden Bridge.

**The dominant structural fact.** Four tables are read but have no governed writer:
`registry`, `relations`, `identity_links`, and — until commit `b3de7c7` — `principal_bindings`.
That commit's message ("Admit principal bindings through Acts, not by hand") diagnosed the
pattern correctly and fixed one of four instances. The execution pack treats the remainder as
unrelated phase items; they are one defect with one shape.

**Consequence for authority.** Powerfarm currently has one bit of authority state, held outside
history, in process environment. Everything the specification says about attribution,
reconstruction and self-government is presently unexercised.

---

## 4. Genesis defects and gaps

| ID | Finding | Class |
|---|---|---|
| G-1 | No Genesis promoter: no path writes Genesis Acts, Registry births, constitutional Rules, Root Identity or Root keys | **Constitutional blocker** |
| G-2 | `genesis.yaml` does not bind initial Registry definitions (§16) — the seed lives in SQL, outside `config_hash`; three migrations have already altered it without changing `genesis_root_hash` | **Constitutional blocker** |
| G-3 | `genesis.yaml` does not bind Root Identity or its initial keys (§16); Root is `POWERFARM_ROOT_IDENTITY_HASH` | **Constitutional blocker** |
| G-4 | `amendment-or-fork` is a symbolic name with no content-addressed protocol | **Constitutional blocker** |
| G-5 | Bootstrap recursion: `RegisterDefinition` is itself a `command_type` requiring prior Registry closure, so ordinary `RegistryService` logic cannot bootstrap an empty Registry | **Constitutional blocker** (structural; forces Genesis to be the unique membrane) |
| G-6 | `declared-decision-cut` declared constitutional but unmaterialized; enforcement hardcoded at three layers with no Rule attribution in Acts | **Implementation defect** (safe: fail-closed) |
| G-7 | `registry`, `relations`, `identity_links` read but have no governed writer | **Implementation defect** |
| G-8 | No authority substrate; §17's vocabulary entirely unregistered | **Implementation defect** |
| G-9 | Pack Phase 0b: "`constitutional=true` requires root authority" contradicts §4.2/PF-25 | **Runbook discrepancy** |
| G-10 | Pack has no Genesis materialization phase and opens at 0a assuming a working Registry | **Runbook discrepancy** |
| G-11 | Pack names one `idFromName` site; there are four | **Runbook discrepancy** |
| G-12 | Whether legacy `relations` rows exist in any live database | **Missing evidence** |
| G-13 | Whether email-keyed durable state exists in Cloudflare OS | **Missing evidence** |
| G-14 | Golden Bridge routing invariants; repo absent from all supplied material | **Missing evidence** |
| G-15 | Whether `3fc601c` exists as a merge on `origin/main` | **Missing evidence** (non-blocking) |
| G-16 | `Store` method count as an invariant | **Non-issue** (pack says so explicitly; correct) |
| G-17 | Whole-history `history_cut` causing global serialization | **Implementation defect** (correctness-safe, throughput-limiting) |

**On G-1 through G-5: the window.** All are correctable *only* until the ceremony is first
admitted. After `GenesisClosed` commits against a real database, §16's "no architectural
backdoors" takes effect and each requires a fork to correct. Since Genesis has never run, the
window is open now.

**On G-4, stated plainly:** if the current Genesis were ratified exactly as written, this universe
would possess **no usable in-universe constitutional amendment mechanism**. Only the name
`amendment-or-fork` is bound into `config_hash`; its substance is nowhere, and §4.2 forbids
inventing it later. The consequence is permanent fork/new-Genesis-only for every future
constitutional definition.

---

## 5. Director model

Derived from existing primitives. **No new Kernel primitive is required**, which is the test the
pack's own halt condition 1 sets. The MCP surface is generic (`powerfarm.action.commit`), so no
new protocol tool is required either.

### 5.1 What encodes the office

| Concern | Encoding | Why this and not something else |
|---|---|---|
| The office exists | Registry definition, `kind=office`, name `powerfarm.director` | Meaning must be referenced by immutable hash (§4.1). `registry.kind` has no CHECK constraint, so a new kind needs no DDL |
| What the office may do | Registry definition, `kind=mandate`, name `director.mandate`, versioned | Powers are **data**, not code. New version = new hash = governed Act. Satisfies "constrained" |
| Dan holds it | `AuthorityGranted` Act (§17) whose payload names `office_hash`, `mandate_hash`, `grantee_identity_hash` | §17 already names `GrantAuthority → AuthorityGranted`. Using it adds no vocabulary the spec lacks |
| Current holders | `active_grants` projection over grant/revoke Acts | §14 names `active_grants` explicitly as materialized State. Disposable, rebuildable, never canonical |
| Structural link | admitted `holds_office` Relation, Identity → office | §12: typed, content-addressed, admitted Relations. Requires Phase 0a |
| Whether a given act is permitted | Registered Rule `director.mandate.v1` | §7. Reads the grant projection and mandate at the cut; returns allow/deny/require_review |

**Deliberately not used:** a canonical `directors` table (would repeat the `research_nodes`
mistake the pack correctly forbids); a new Identity kind (Dan's Identity is `human`; office is
not identity); a Kernel-level Director class (would grow the constitution for one feature).

### 5.2 Lifecycle

**Appointment.** Root issues `GrantAuthority`, payload naming office hash, mandate hash, grantee.
Rules evaluate; `AuthorityGranted` Act commits; `holds_office` Relation admitted in the same
transaction. Attribution is complete: the Act carries `rule_hashes`, `registry_cut`,
`decision_cut`, and the granting Identity.

**Exercise.** Dan signs a Command. `director.mandate.v1` resolves, reads `active_grants` at the
declared cut and the mandate definition by hash, and decides whether *this specific power* covers
*this command type*. The resulting Act names that Rule hash. "Dan did this as Director" is then a
provable historical fact, not a configuration claim.

**Delegation.** A scoped `GrantAuthority` whose payload names a **subset** of the delegator's
mandate powers, plus an expiry. The Rule must verify subset containment against the delegator's
own grant at the cut — this is what prevents accidental transfer of the whole office. The context
keys `request.requested_by` / `request.performed_by` / `request.requester_kind` already exist and
are constitutional (`20260816150000_delegation_context.sql`), so "who asked" and "who signed" are
already separable without new vocabulary. §9's separation-of-powers structures compose here
without Kernel changes.

**Revocation.** `AuthorityRevoked` Act; the projection carries `revoked_act`. Same shape as
`PrincipalRevoked` in `20260816160000`. Deleting the projection loses nothing.

**Succession.** Revoke Dan's grant; grant to the successor. Two ordinary Acts. No Root change, no
environment variable, no Genesis mutation, no history rewrite, and no pretence that two people
share an Identity.

**Key rotation.** Already solved by §5.1: `RotateKey → KeyRotated`, Identity stable across
rotation, valid keys a projection over key history (`identity_keys.valid_from_act` /
`valid_until_act` already model this). The grant references `identity_hash`, never key material,
so rotation cannot disturb the office. **This requires nothing new — only that the grant never
reference a key.**

### 5.3 Authority graph

```
  Genesis
     │ binds (must, currently does not)
     ▼
  Root Identity ──── constrained by ────► genesis.root_powers   [constitutional, Genesis-born]
     │
     │ GrantAuthority ──► AuthorityGranted Act    (one-time bootstrap appointment)
     ▼
  Dan's Identity ──── holds_office (Relation) ───► powerfarm.director   [Registry: kind=office]
     │                                                    │
     │                                          governed by
     │                                                    ▼
     │                                        director.mandate.v1  [Registry: kind=mandate]
     │                                          enumerated powers, versioned
     │
     ├── signs Command ──► director.mandate.v1 Rule ──► Decision ──► Act (rule_hashes = attribution)
     │
     └── GrantAuthority (subset ⊆ own mandate, expiring) ──► delegate Identity
                                                                  │
                                              AuthorityRevoked ◄──┘

  projection: active_grants  ──  derived from grant/revoke Acts, disposable, never canonical
```

---

## 6. Root / Director separation

> **Invariant (D-Authority-01).** Root is a bootstrap membrane, not an operating role. Director is
> a governed office with an enumerated, versioned mandate. Every power the Director exercises must
> be traceable to a mandate definition hash and an unrevoked grant Act at the declared cut. Root
> must never be a fallback path for a Director power, and no Director power may grant Root
> authority or amend a constitutional definition.

**Which powers genuinely belong to Root/Genesis.** Registering constitutional definitions
(Genesis only, per D-Genesis-02); creating the initial Identities; the one-time appointment of the
initial Director. That is the complete legitimate list.

**Which belong to the Director office.** Everything operational: registering ordinary vocabulary,
appointing reviewers, granting and revoking scoped operational authority, approving budget
ceilings, authorizing publication — as enumerated in the mandate, and nowhere else.

**How Director authority becomes historically governed after Root appoints it.** The appointment
Act is itself in history with full attribution. From that Act forward, every Director action
resolves through `director.mandate.v1` against `active_grants` — Root is not consulted. Root's
role ends at the appointment. To make that structural rather than conventional, Genesis should
bind a constitutional Rule constraining Root's post-Genesis powers to the list above. Without it,
Root can silently re-appoint or override, and the Director office is decorative.

**The threat to this invariant is G-3, not the Director design.** While Root is
`POWERFARM_ROOT_IDENTITY_HASH`, anyone with deploy access is Root, and therefore can appoint
themselves Director. Fixing G-3 is what makes the separation real.

### What must be Genesis-born — smallest sufficient surface

| Element | Genesis-born? | Reason |
|---|---|---|
| Root Identity + initial keys | **Yes** | §16 requires it; G-3 |
| Initial Registry definitions (or their manifest hash) | **Yes** | §16 requires it; G-2 |
| Amendment protocol content | **Yes, or accept fork-only** | §4.2: cannot be invented later; G-4 |
| Constitutional Rule constraining Root's post-Genesis powers | **Yes** | Otherwise the Root/Director boundary is convention, not law |
| The four declared constitutional Rules, materialized | **Yes** | D-Genesis-01 |
| Existence of the Director office | **No** | Ordinary Registry definition, registrable post-Genesis |
| The Director mandate | **No** | Ordinary; must be versionable without a fork |
| The appointment mechanism (`GrantAuthority`/`AuthorityGranted`) | **No** | §17 self-government path; ordinary vocabulary |
| The initial office holder (Dan) | **No** | An ordinary Act under Root's bootstrap power |

The office deliberately stays **ordinary**. Making Director constitutional would freeze the mandate
against amendment for the life of the universe — and given G-4, that could mean permanently.

---

## 7. Required decisions

Preserved from the prior record where evidence still supports them; one restated more precisely.

| ID | Decision | Status |
|---|---|---|
| **D-Genesis-01** | Every name in `genesis.yaml.constitutional_rules` must resolve to a content-addressed `kind=rule` definition whose Registry entry is born at Genesis. Kernel enforcement of a structural invariant does not substitute for Rule attribution | **Upheld** — evidence re-verified (§7:324-330, §16:660-663, §18 structural-law list differs, manifest comment, `ceremony.py`) |
| **D-Genesis-02** | Constitutional registration seals at `GenesisClosed`. `constitutional=false` → ordinary governed path; `constitutional=true` pre-Genesis → ceremony only; post-Genesis → Genesis-born amendment protocol only, otherwise reject **including Root** | **Upheld** — §4.2:193-198, PF-25:1055 |
| **D-Genesis-03** | `genesis.yaml` must cryptographically bind the *canonical content* of every §16 item, specifically the initial Registry definitions and Root Identity + initial keys — not merely their names | **New** — G-2, G-3 |
| **D-Genesis-04** | Decide `amendment-or-fork`: give it real content-addressed substance at Genesis, or consciously ratify a fork-only universe. No third option exists after `GenesisClosed` | **New, urgent** — G-4 |
| **D-Genesis-05** | Genesis must bind a constitutional Rule constraining Root's post-Genesis powers to: registering constitutional definitions at Genesis, creating initial Identities, and appointing the initial Director | **New** — makes D-Authority-01 structural |
| **D-Authority-01** | Root is a bootstrap membrane, not an operating role; Director is a governed office with enumerated mandate (full text §6 above) | **New** |
| **D-Authority-02** | The Director office, its mandate, the appointment vocabulary and the initial appointment are **ordinary** governed objects, not constitutional ones | **New** — smallest surface; keeps the mandate amendable |
| **D-Authority-03** | Authority state is Acts + admitted Relations projected into `active_grants`. No canonical authority table | **New** — §14:596, consistent with the no-`research_nodes` ruling |
| **D-Authority-04** | Delegated grants must name a strict subset of the delegator's mandate powers, verified by Rule against the delegator's own grant at the declared cut | **New** — prevents whole-office transfer |
| **D-Txn-01** | The single correct transaction seam is a `security definer` wrapper RPC that calls `powerfarm_internal.commit_act` and inserts its authoritative rows in the same transaction. CAS objects may precede the gate; authoritative rows may not | **Upheld, strengthened** — see §7.1 |
| **D-PF13-01** | Materialize `declared-decision-cut` as a registered constitutional Rule; keep the hardcoded checks as its enforcement machinery; require its hash in `rule_hashes` | **Upheld** |
| **D-PF13-02** | Do not weaken TOCTOU. Causal/context-scoped reauthorization (G-17) is co-designed with the Rule engine's static read-set analysis, never as a shortcut | **New** |

### 7.1 The transaction seam — answer

**A Python unit-of-work is not merely inadvisable; it is illegal.** `powerfarm_worker` holds
`select` only on `objects`, `acts`, `relations`, `registry`
(`20260815123245_rls_grants_final.sql:29`) and `execute` on `commit_act` (same file:50). No
connection held by the worker can insert those rows. Option eliminated by permission, not taste.

The correct seam is therefore a `security definer` wrapper per admission kind
(`commit_definition`, `commit_act_with_relations`), each calling `commit_act` — which holds
`pg_advisory_xact_lock('powerfarm:commit-gate:v1')` and performs every constitutional check — and
then inserting its rows before returning. One function call is one transaction, so atomicity is
structural.

The usual objection to wrappers (someone forgets the gate) does not apply here: **the tables are
select-only, so a wrapper that skips `commit_act` cannot insert anything.** The invariant is
enforced by grants, not discipline. Widening `commit_act`'s signature is the fallback if wrappers
exceed roughly five; the untyped-envelope variant should be rejected as a second hidden mechanism.

Each wrapper must be mirrored in `MemoryLedger` in the same change, or the 63 tests stop meaning
what they appear to mean.

---

## 8. Correct Phase 0 ordering

Derived from dependencies. The supplied runbook opens at Phase 0a, which is unreachable: 0a and
0b both require committing Acts through Postgres; no Act can commit until the Registry is
populated; the Registry cannot be populated except at Genesis (G-5).

**Must happen before first Genesis — cannot be deferred:**

| # | Step | Decisions |
|---|---|---|
| 0 | Amend `genesis.yaml` to bind canonical content of all §16 items: initial Registry definitions, Root Identity + initial keys, authority configuration | D-Genesis-03 |
| 1 | Resolve the amendment protocol — real content, or ratified fork-only | D-Genesis-04 |
| 2 | Author the constitutional Rule constraining Root's post-Genesis powers | D-Genesis-05 |
| 3 | Author the four declared constitutional Rules as content-addressed definitions | D-Genesis-01 |

**After Genesis is correctly specified:**

| # | Step | Decisions |
|---|---|---|
| 4 | Decide and build the wrapper-RPC seam (`commit_definition` first) | D-Txn-01 |
| 5 | Build the Genesis promoter: manifest → Registry births with `born_at` = `GenesisClosed`; Root Identity and keys admitted | G-1 |
| 6 | Close the post-Genesis constitutional-registration loophole | D-Genesis-02 |
| 7 | Ordinary runtime `RegistryService` (`RegisterDefinition` → `DefinitionRegistered`) | Phase 0b proper |
| 8 | Register §17 authority vocabulary + office/mandate definitions as ordinary | D-Authority-02 |
| 9 | Phase 0a — relations writer + `admitted_act`, second instance of the established wrapper pattern | — |
| 10 | Appoint Dan Director: `GrantAuthority` → `AuthorityGranted` + `holds_office` Relation | D-Authority-01 |
| 11 | `active_grants` projection; `director.mandate.v1` Rule | D-Authority-03 |
| 12 | Rule engine (Phase 1), with drift-relevance in the read-set design from the start | D-PF13-02 |

Note the inversion: **Dan becomes Director at step 10, not step 1.** Every earlier step is what
makes step 10 mean something Powerfarm can prove.

---

## 9. Halt conditions

Facts not establishable from the supplied material; unsafe to assume.

| ID | Unknown | Why it matters |
|---|---|---|
| H-1 | Whether any live database holds `relations` rows without provable admission | Pack halt condition 2. Determines whether the 0a migration may add `admitted_act` at all. **Check before writing it** |
| H-2 | Whether Cloudflare OS holds durable state keyed by email | Pack halt condition 5. Determines whether re-keying needs a migration inventory first |
| H-3 | Golden Bridge routing invariants — repo absent from every supplied archive | Pack halt condition 6. All Phase 7 claims unverifiable |
| H-4 | Whether Golden Bridge derives any privilege from gateway configuration | Cannot inspect. See §9.1 |
| H-5 | Whether a Genesis ceremony has been run in any environment not visible here | If yes, G-1..G-5 are already sealed and fork is the only remedy |
| H-6 | Whether `POWERFARM_ROOT_IDENTITY_HASH` is currently set anywhere, and to whose key | Determines who holds root authority today |
| H-7 | Whether Dan possesses an Ed25519 keypair intended as the Director signing key | Required before any appointment Act |
| H-8 | Intended semantics of `registry_seed_manifest` promotion (ceremony-consumed vs. writer-consumed) | Changes how step 5 is built |
| H-9 | Whether `3fc601c` exists as a merge on `origin/main` | Provenance only; non-blocking |

### 9.1 Golden Bridge boundary — normative position, pending H-3/H-4

The gateway is **entirely absent** from this repository — zero references to a gateway, Golden
Bridge, or Mistral in any `.py`, `.sql` or `.md`. So the boundary can be stated normatively but
not verified.

From §11.2 and PF-24, inference is an **external effect**. Therefore:

- The gateway may decide **routing and execution only**: which certified machinery runs, and what
  it returned. It may decide nothing about identity, authority, or admission.
- `Requested / Authorized / Dispatched / Observed / Committed-as-external-fact` must not collapse.
  A returned completion is `Dispatched` plus an `Observed` report — never an admitted fact.
- A receipt is an **observation with provenance** (§11.1): it must carry its observer Identity and
  evidence references, and must not claim more than "this observer reported this at this cut."
- Changing model or provider changes the **machinery receipt**, never the actor Identity.
- Gateway configuration must confer no privilege. Any request reaching the gateway without prior
  Powerfarm admission, or any post-admission mutation of routing parameters, would constitute a
  second authority path and is prohibited.

**Explicitly: Director authority must not be inferred from ownership of the gateway, the GitHub
repositories, the Cloudflare account, or the servers.** Those establish operational control, not
Powerfarm authority — the same category error as OAuth scope, already ruled on.

---

## 10. Recommended next artifact

**Design the amended `genesis.yaml` and its binding schema — the complete Genesis input document,
with the amendment protocol resolved.**

Not the Genesis promoter, not the Director objects, not the wrapper RPC. Those are all
implementable later and are correctable if wrong. The Genesis binding is the only artifact here
that becomes permanently immutable the first time it is admitted, and it currently fails four of
§16's requirements.

That single document forces the decisions that everything else inherits: what Root is and what it
may do after Genesis (D-Genesis-03, D-Genesis-05), whether this universe can ever amend its own
constitution (D-Genesis-04), and what the four constitutional Rules actually say (D-Genesis-01).
Until it exists, every downstream design — including Dan's Directorship — rests on an
environment variable.

Design it. Do not admit it until you are willing to live inside it.
