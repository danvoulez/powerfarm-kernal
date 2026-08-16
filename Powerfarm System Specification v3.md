# Powerfarm System Specification — v3.2

**Status:** Revision 3.2 — ratifies the first supported operational profile: one macOS LAB running direct launchd agents, Supabase Cloud as managed Postgres/Auth/Storage, and a dedicated outbound-only Cloudflare Tunnel for `powerfarm.app`. Docker, Compose, containers, and Google Cloud services are outside this profile. Installation, update, and removal are governed by a versioned, idempotent, receipt-producing pack with hosted CI and attested releases. Revision 3.1 switched canonicalization from CBOR to **JCS (RFC 8785)** with a Genesis-bound golden vector suite. Revision 3 hardened causal ordering, authorization cuts, external-effect phases, constitutional change, domain-separated hashing, and temporal honesty. Revision 2 formalized Context, Command lifecycle Acts, reference-by-hash, Identity authentication and key rotation, versioned governance, review semantics, deterministic projectors, confidentiality, external observations, and the constitutional core.

## 0. Definition

Powerfarm System is a graph-native, identity-governed, append-only system for representing intention, authority, occurrence, history, and current state.

Its constitutional premise is:

- Everything has identity.
- Every change begins as intent.
- Every intent is governed by rules.
- Every accepted change becomes an immutable fact.
- Current state is a projection of those facts.
- Nothing may depend on something that has not yet been born.

Powerfarm does not treat database state as reality.

It treats history as primary and state as derived.

---

## 1. Genesis Order

The Powerfarm System is born in a strict dependency order:

```
Genesis
  ↓
Registry
  ↓
Identity
  ↓
Command
  ↓
Rules
  ↓
Act
  ↓
State
```

Each layer answers one fundamental question:

| Layer | Question |
|---|---|
| Genesis | What are the primitive laws of this system? |
| Registry | What kinds of things may exist? |
| Identity | Who or what exists and may act? |
| Command | What change is being intended? |
| Rules | Is this intention allowed to proceed? |
| Act | What was actually admitted as having happened? |
| State | What does the world look like at this cut of history? |

This ordering is constitutional.

If `A → B` means that B depends on A, then the Genesis dependency graph MUST be acyclic.

---

## 2. Fundamental Transition

Every governed change follows:

```
Identity
   +
Command
   +
Context
   ↓
Rules
   ↓
Authorization
   ↓
Act
   ↓
State'
```

Formally:

```
d = authorize(I, C, X, G_{≤c}, R_c)
```

where:

- I = Identity
- C = Command
- X = Context
- G_{≤c} = the history graph up to the **declared cut c** the decision examined
- R_c = the Rules valid at cut c
- d = authorization decision

The decision MUST record the cut `c` it was made against. If history has advanced to `c' > c` before commit, the kernel MUST decide by Rule whether the decision remains valid, must be reauthorized against `c'`, or may be committed regardless. A silent default is forbidden: authorizing a world that no longer existed when the Act was born is a constitutional TOCTOU violation (PF-13).

The authorization decision is one of:

```
allow
deny
require_review
```

If `d = allow`, then the intended transformation may be committed as an Act:

```
A = commit(C, d, X)
```

and:

```
State_{n+1} = apply(State_n, A)
```

If no corresponding Act exists, the intended governed change did not occur.

**No Act, no change.**

### 2.1 Context

`X` is a finite map of named, typed values. Every context key MUST be drawn from a context type registered in the Registry. Typical registered context families include:

- time (as declared by the commit sequence, §10.2 — never wall-clock trust alone)
- request metadata
- network origin
- prior Review Acts
- the delegation graph at the relevant cut

Every Rule MUST statically declare which context keys it reads. Evaluation of a Rule over a Context that lacks a declared key is a rule-evaluation failure — fail loud, never an implicit default.

Contexts are content-addressed. An Act records the hash of the exact Context under which it was authorized, so the authorization is fully reconstructible.

---

## 3. Powerfarm Is Graph-Native

The semantic structure of Powerfarm is a graph. Tables, indexes, KV stores and filesystems are storage representations.

The conceptual system is:

```
G = (V, E)
```

where:

- V contains immutable content-addressed objects;
- E contains typed relations between those objects.

A Powerfarm history is therefore not fundamentally a set of rows. It is an evolving graph.

```
Objects + Typed Relations
          ↓
        History
          ↓
      Projections
          ↓
         State
```

---

## 4. Registry

The Registry defines the vocabulary of the Powerfarm universe. It contains versioned definitions for things such as:

```
types            rules
schemas          resources
commands         services
act types        capabilities
relation types   versions
context types    projectors
```

Nothing becomes a first-class Powerfarm object merely because an application emitted JSON with an unfamiliar field. Its type must be recognized under a Registry definition valid at the relevant cut.

After Genesis, the Registry governs itself through the same Command → Rules → Act mechanism as everything else.

### 4.1 Registry Versioning

Every Registry definition is versioned and content-addressed. Every Act MUST reference, by content hash, the exact Registry and Rule versions under which it was validated. Historical reconstruction MUST NOT retroactively reinterpret old Acts under new definitions: an Act validated under Rule version `r_k` remains governed by `r_k` forever.

### 4.2 Constitutional Core and Constitutional Change

Genesis MAY declare a subset of Rules and Registry definitions as **constitutional**. Constitutional definitions cannot be changed by any post-Genesis Command, including Commands issued under Root authority.

Changing the constitution itself has exactly two legitimate exits:

1. **Amendment protocol** — Genesis may pre-declare a constitutional Rule that defines how the constitution amends itself (e.g. N-of-M constitutional reviewers plus a delay window). Such a protocol must itself be born at Genesis; it cannot be invented later.
2. **Fork / new Genesis** — a new universe with its own `genesis_root_hash`, linked to the old one by a `forked_from` relation. History is preserved; continuity of authority is not claimed.

**No third administrative door exists.** Any out-of-band edit of constitutional definitions invalidates the universe's conformance claim.

---

## 5. Identity

Every entity capable of participating as an actor has a Powerfarm Identity:

```
powerfarm_id
```

Examples include:

```
human, organization, service, machine, application, workflow,
agent, model, scheduler, integration, device, reviewer
```

Identity answers: *Who or what is this?*

Identity does not imply authority:

```
Identity ≠ Authority
```

Authentication establishes that a principal can presently prove control of an Identity. Authorization determines whether that Identity may perform a particular governed action.

### 5.1 Authentication and Key Management

An Identity is a stable, content-addressed object that binds:

- the identity type;
- an initial set of authentication keys (public keys or verifiable-credential references);
- a reference to the Act that created it.

Proof of control is represented as a cryptographic signature over the Command's canonical form. A Command without a verifiable signature from a key valid for the signing Identity at the relevant cut is invalid by construction.

**Key rotation does not create a new Identity.** Rotation is itself a governed change:

```
RotateKey → Rules → KeyRotated Act
```

The `KeyRotated` Act supersedes prior keys (optionally with a grace window declared in the Act) and adds new ones. The set of currently valid keys is a projection over the Identity's key history. Thus authentication remains reconstructible at any historical cut, and Identity remains stable across rotation.

In the ratified operational profile (§19), interactive human authentication
MUST use managed Supabase Auth with passkeys for the WebAuthn relying party
`powerfarm.app`. Supabase MAY issue browser sessions and OAuth 2.1 grants, but a
platform session is only authentication evidence. It MUST be linked to a stable
Powerfarm Identity and MUST NOT itself confer authority to commit an Act.
Authorization remains a cut-aware Kernel decision over Identity, Rules,
Context, and explicit proofs. OAuth clients are declared and dynamic client
registration is disabled in the first profile.

---

## 6. Command

A Command represents intention:

> An identified actor proposes that a change occur.

Example:

```
ChangeFarmOwner {
    farm: ...
    new_owner: ...
}
```

not:

```
UPDATE farms SET owner = ...
```

Commands are not Acts:

```
Command ≠ Occurrence
```

### 6.1 Command Lifecycle as Acts

A Command is a durable content-addressed object. Its lifecycle is **entirely represented as Acts that reference it** — there is no second mutable state channel outside history. The lifecycle Acts are:

```
CommandSubmitted      — the Command entered the system
CommandValidated      — type, signature, and schema checks passed
CommandRejected       — structural validation failed (invalid)
AuthorizationRequested — entered rule evaluation
CommandDenied         — authorization returned deny
ReviewRequested       — authorization returned require_review
AuthorizationReviewed — the Reviewer's Review Act (§8)
AuthorizationResolved — final allow/deny after review
CommandSuperseded     — replaced by a later Command
CommandExpired        — its validity window elapsed
```

The consequential Act (e.g. `OwnerChanged`) MUST reference the full authorization chain: `AuthorizationRequested → [AuthorizationReviewed] → AuthorizationResolved`.

A Command's current status is a projection over these lifecycle Acts. Merely existing never implies that its intended change occurred.

---

## 7. Rules

Rules determine whether an intended graph transformation may proceed:

```
Can(identity, command, resource, context)?
```

The basic decision domain is:

```
allow
deny
require_review
```

Rules may depend on identity, authority, resource, current history cut, risk, prior Acts, delegations, time, organization, requested consequence, reviews, and context — but only through dependencies that are already legitimate under the Genesis ordering.

Rules themselves are versioned, content-addressed system objects (§4.1). Rules are pure functions of `(I, C, X, S, R)`: for the same inputs and versions, a Rule MUST return the same decision. Changing a Rule after Genesis requires:

```
Command → existing Rules → (optional Auth Review) → Act → Rule history
```

No privileged configuration edit exists outside this mechanism. Constitutional Rules (§4.2) cannot be changed at all after Genesis.

---

## 8. Auth Reviewer

The Auth Reviewer is an explicit Powerfarm System component — not a constitutional primitive separate from the Kernel. It is a composition of:

```
Identity + Authority + Rules + Command + Act
```

Its purpose is to independently review an authorization decision when the applicable Rules require more than direct authorization.

### 8.1 Review Flow (Act-complete)

```
Identity → Command → Rules → require_review
    ↓
ReviewRequested Act            (Command is now pending)
    ↓
Reviewer Identity → Review Command → Rules → AuthorizationReviewed Act
    ↓
Rules reevaluate with the Review Act as governed Context
    ↓
AuthorizationResolved Act (allow / deny)
    ↓
Consequential Act
```

While review is pending, the Command is **blocked**: it cannot produce a consequential Act, it can expire (producing `CommandExpired`), and it can be superseded (producing `CommandSuperseded`). Authorization decisions themselves are never mutated: the `require_review` outcome is permanently recorded by `ReviewRequested`, and the later `AuthorizationResolved` is a new Act, not an edit. Every consequential Act references this complete chain.

### 8.2 Reviewer Invariants

An Auth Reviewer MUST:

- possess an Identity;
- possess explicitly derivable review authority;
- operate within a declared scope;
- leave an immutable Review Act;
- never silently mutate State;
- never create its own authority;
- never bypass applicable Rules;
- never transform `require_review` directly into consequence.

The reviewer produces new governed context. Rules decide what that context permits:

```
Reviewer → Review Act → Rules → Consequential Act
```

not:

```
Reviewer → Consequential Act
```

---

## 9. Separation of Powers

Rules may impose review structures such as:

```
requester != reviewer
N-of-M reviewers
reviewer.organization != requester.organization
reviewer must possess capability X
```

This allows Powerfarm to implement four-eyes review, human approval, quorum, segregation of duties, agent oversight, cross-organization review, and risk gates — without adding new Kernel primitives.

---

## 10. Act

An Act is an immutable fact of the Powerfarm history: something the system has admitted as having occurred under a particular semantic type.

Examples:

```
FarmCreated            OwnerChanged           AuthorityGranted
PaymentAuthorized      PaymentDispatched      PaymentCommitted
AuthorizationReviewed  RuleRegistered         AgentDelegated
```

Acts MUST be: **typed, immutable, append-only, attributable, content-addressed.**

An Act's identity is derived from canonical content:

```
ActID = H(Canonical(Act))
```

An implementation MUST NOT rely on a client-supplied arbitrary identifier as proof of content identity.

### 10.1 Canonicalization and Reference Discipline

Canonicalization is versioned and bound at Genesis (`canonicalization_version`, `hash_algorithm`), and MUST be enforced identically everywhere.

**The canonical form is JCS — RFC 8785 JSON Canonicalization Scheme.** Consequences:

- JCS is the sole canonical encoding for Powerfarm objects in this specification. CBOR / RFC 8949, MessagePack, ordinary `json.dumps(sort_keys=True)`, and ad hoc "stable JSON" are not interchangeable and are non-conforming for object identity.
- Field ordering is locale-independent lexicographic by UTF-16 code unit; number formatting follows the ECMAScript `Number::toString` algorithm; Unicode is preserved exactly as provided (no normalization — the `unicode` vector is constitutional proof).
- Any conforming JSON tooling — including every browser's `JSON.stringify` plus a JCS shim — can verify a Powerfarm hash without a codec dependency. The verifier needs only UTF-8 and SHA-256.
- Binary payloads are carried as base64url strings inside JSON; they are hashed as their encoded form, never as raw bytes.
- Floats are legal but treacherous: implementations MUST pass the `values` golden vector (which covers `333333333.33333329`, `1E30`, `4.50`, `2e-3`, `1e-27`). Money and other exact quantities SHOULD use integer minor units or strings.

All object references MUST be **by content hash, never by embedded value**. Embedding by value is forbidden. This guarantees that content addressing is acyclic at the object level even when the typed relation graph contains cycles (§13.3), and makes every object's hash well-founded.

**Domain separation.** Hashes MUST be computed over a domain-tagged preimage:

```
SHA-256( "powerfarm:act:v1"      || utf8( JCS(act) ) )
SHA-256( "powerfarm:relation:v1" || utf8( JCS(relation) ) )
```

so that identity encodes *which species of object* is being identified, not merely identical bytes. The tag namespace and version are bound at Genesis. The conformance suite MUST include the golden canonicalization/hash vector suite (`values`, `arrays`, `unicode`, `french`, `weird`, `structures` — each with input JSON, expected canonical UTF-8 hex, and expected plain and domain-tagged SHA-256) and every implementation MUST pass all vectors byte-exactly before it may participate in a universe (PF-22).

**Occurrence identity.** An Act's hash is its unique historical identity: the same content-addressed Act appears at most once in a universe's history (enforced by uniqueness on `acts.hash`). Re-submitting identical content is idempotent — it returns the existing Act, it never creates a second placement. Semantic identity and historical placement are therefore the same thing for Acts; anything needing a *new* occurrence must differ in content (e.g. a distinct `when` or causal parent).

### 10.2 Causal Order Is Constitutional; Linearization Is Operational

The fundamental ordering structure of history is the **ancestry DAG**: every Act declares its causal parents by hash, and ancestry MUST be acyclic (PF-10).

Commit sequence numbers (e.g. a Postgres identity column) are **an operational cursor, not constitutional order**. Allocation order is not commit order: sequences hand out values atomically but non-transactionally — aborted transactions consume values, and concurrent transactions may obtain `seq=10` and `seq=11` and commit in the reverse order. Therefore:

- `seq` MUST NOT be used as proof of causal or constitutional ordering;
- `seq` MAY have gaps; it is a monotonic cursor for pagination, projection checkpoints, and replication;
- deterministic projection (§14) is defined over the **ancestry DAG plus content**, not over `seq`;
- where a global linearization is genuinely needed (e.g. a ledger view), it is a **projection** — a registered projector producing a deterministic topological ordering of the DAG.

A *history cut* `c` is therefore defined as a **set of Act hashes closed under ancestry**, not as a log prefix.

### 10.3 Three Notions of Time

Powerfarm distinguishes at least three temporal ideas, which MUST NOT be conflated:

1. **`act.claimed_when`** (`act.when` conceptually) — the time claimed inside the Act's content (part of its hash; an assertion, not a proof). Implementations MUST name this field `claimed_when` in code, APIs, and schema: a bare `when` invites reading it as causal order or as provable knowledge time, which are the two ideas this section exists to keep apart.
2. **Causal order** — ancestry position; what the Act could have known about (§10.2).
3. **Provable knowledge time** — when the system can *prove* an object already existed. CAS proves content identity but, alone, cannot prove that content existed at a given date.

Genesis MUST reserve the hook for **external temporal anchoring** (e.g. RFC 3161 timestamping, a transparency log, or an anchoring Act referencing an external notarization), recorded as typed relations such as `anchored_at` / `notarized_by`. Implementation may be deferred; the slot in the ontology may not be. This is what will let a future claim like "this synthetic trajectory already existed in 2026" be provable rather than asserted.

---

## 11. Acts Do Not Lie

> Commands may fail. Acts do not lie.

This means something precise. It does not mean every proposition inside an Act is universally true. It means Powerfarm MUST NOT collapse semantically distinct occurrences:

```
PaymentRequested ≠ PaymentAuthorized ≠ PaymentDispatched ≠ PaymentCommitted
```

A dispatch cannot masquerade as commitment. A simulation cannot masquerade as observed execution. A review cannot masquerade as consequence. Act types preserve these distinctions.

### 11.1 Internal Facts and External Observations

Act types belong to one of two layers:

- **System-internal facts** — e.g. `CommandAccepted`, `RuleEvaluated`, `AuthorizationReviewed`, `KeyRotated`. These are undeniably true within the system by construction.
- **Observed external events** — e.g. `PaymentDispatched`, `SensorReadingReceived`. These are *observations with provenance*, not infallible truth. An observation Act MUST carry its observer Identity and evidence references, and MUST NOT claim more than "this observer reported this at this cut."

Reality may later contradict an observation; the correction is a new Act, never an edit.

### 11.2 External Effects Protocol

"No Act, no change" governs the internal universe perfectly — but sending money, opening a valve, dispatching an email, or executing a trade does not happen atomically with `INSERT INTO acts`. External effects therefore follow a mandatory phase protocol, each phase a distinct Act:

```
Requested
   ↓
Authorized
   ↓
Dispatched            (the system handed the effect to the outside world)
   ↓
Observed / Confirmed  (an observer Identity reports reality, with evidence)
   ↓
Committed-as-external-fact
```

Rules:

- A database commit MUST NEVER claim that external reality also committed. `Dispatched` is a system-internal fact; `Observed` is an external observation (§11.1); conflation violates "Acts do not lie."
- Failure, timeout, and retry are first-class phases with their own Acts (`DispatchFailed`, `EffectRetried`), preserving the full trajectory.
- This protocol composes with the Auth Reviewer exactly like HITL: the Reviewer produces governed context and Rules reevaluate — review may gate `Dispatched`, or gate `Committed-as-external-fact`, as Rules declare.

---

## 12. Relations

Powerfarm objects are connected by immutable typed Relations. Examples:

```
parent_of, caused_by, cites, supports, contradicts, supersedes,
authorized_by, reviewed_by, delegated_from, derived_from,
simulated_from, crafted_from, forked_from, matched_to
```

Conceptually:

```
Relation {
    from           // content hash
    to             // content hash
    relation_type  // registered type
    payload        // typed, registered schema
}
```

Relations themselves MUST be content-addressed. Powerfarm MUST NOT collapse all relation semantics into an untyped `parents[]` structure.

---

## 13. Graph Classes

Powerfarm maintains several overlapping semantic graphs.

**13.1 Genesis Graph** — defines constitutional dependency. MUST be acyclic.

**13.2 Ancestry Graph** — represents historical continuation. MUST be acyclic.

```
A1
 │
 ├→ A2
 │   └→ A4
 │
 └→ A3
     └→ A5
```

**13.3 Relation Graph** — contains all typed relations. It need not be acyclic; e.g. `A contradicts B` and `B contradicts A` may both be valid.

**13.4 Identity and Authority Graph** — represents grants, delegations and institutional relationships:

```
Root
 │
 ├─delegates→ Organization
 │               │
 │               ├─delegates→ Human
 │               └─delegates→ Agent
 │
 └─appoints→ Reviewer
```

Authority is derived from valid graph paths plus applicable Rules. It is not equivalent to a mutable boolean such as `is_admin = true`.

---

## 14. State

State is a projection:

```
State_t = P(G_{≤t})
```

where `G_{≤t}` is the history graph up to ancestry-closed cut `t` (§10.2) and `P` is a declared projector.

State is consequence, not original truth. Materialized State may exist for performance:

```
farms_current, balances_current, active_grants, open_jobs
```

but it is disposable.

Given the same history and projector, `P(G) = P(G)` must produce the same result whenever deterministic reconstruction is claimed. Projectors MUST therefore be deterministic functions of history: no wall-clock reads, no ambient randomness, no unversioned external lookups.

Deleting State MUST NOT delete history.

---

## 15. Projections

Different projections may coexist over the same history:

```
Operational State, Audit State, Billing State, Authorization State,
Trajectory View, Search Index, Attention View
```

A projection does not acquire authority merely because it is convenient or fast. The source of reconstructible authority remains the governed history plus the Rules and Registry definitions necessary to interpret it.

### 15.1 Projector Registration and Invalidation

A Projector is a registered Registry type binding:

- content-addressed projector code (or a content-addressed build of it);
- a declared input schema (the Act and Relation types it consumes);
- a declared output schema.

Every materialized projection MUST store:

```
projector_hash
history_cut        // ancestry-closed cut (root hash(es)) it reflects
```

A materialization is valid only if both match the requested projector and cut; otherwise it is stale and MUST be rebuilt or advanced. Invalidation is therefore deterministic, not heuristic.

---

## 16. Genesis Ceremony

The first system birth is the only exceptional transition. A minimal Genesis Ceremony produces:

```
GenesisCreated
      ↓
RegistryCreated
      ↓
RootIdentityCreated
      ↓
RootAuthorityGranted
      ↓
GenesisClosed
```

Genesis MUST bind at least:

- Genesis specification
- canonicalization version
- hash algorithm and domain-tag namespace (§10.1)
- commit mechanism (single-writer `commit()` gate)
- temporal anchoring hook reservation (§10.3)
- initial Registry definitions
- constitutional core declarations (§4.2)
- Root Identity and its initial keys
- initial Rules / authority

The resulting universe has a stable `genesis_root_hash`. After `GenesisClosed`, there are no architectural backdoors.

---

## 17. Self-Government

After Genesis, Powerfarm uses the same mechanism to modify itself that applications use to modify domain state:

```
Register a Command:     RegisterCommand → Rules → CommandRegistered → Registry projection
Change a Rule:          ChangeRule → Rules → optional Auth Review → RuleChanged
Grant authority:        GrantAuthority → Rules → Auth Reviewer if required → AuthorityGranted
Appoint a reviewer:     AppointReviewer → Rules → ReviewerAppointed
Rotate identity keys:   RotateKey → Rules → KeyRotated
```

Constitutional Rules and definitions (§4.2) are excluded from amendment by any path. The system cannot govern users by one mechanism and govern itself by an invisible second mechanism.

---

## 18. Powerfarm Kernel

```
┌───────────────────────────────────────┐
│           POWERFARM KERNEL            │
│                                       │
│ Genesis                               │
│ Registry                              │
│ Identity                              │
│ Command                               │
│ Rules                                 │
│ Act                                   │
│ State                                 │
│                                       │
│ Structural laws:                      │
│ CAS (reference-by-hash, domain-tagged)│
│ Typed Relations                       │
│ Append-only History, Causal DAG       │
│ Acyclic Constitutional Dependency     │
└───────────────────────────────────────┘
```

Genesis defines the birth. The six post-Genesis primitives are Registry, Identity, Command, Rules, Act, State.

### 18.1 Stateless MCP Boundary

The first Kernel service boundary uses MCP specification `2026-07-28` over
stateless Streamable HTTP. MCP is an adapter, not a constitutional primitive:

```text
MCP -> protocol/mcp -> service -> kernel -> ledger adapter
```

No authorization or correctness claim may depend on an MCP handshake, transport
session, session identifier, or process-local continuity. Every governed request
must carry or resolve the exact inputs needed to read an ancestry-closed cut,
evaluate Rules, and commit through the narrow transactional Ledger interface.
Protocol Tools expose Powerfarm semantics rather than raw database or CommitGate
operations. The Tasks extension remains outside the Kernel until task continuity
is represented by explicit durable Platform handles.

---

## 19. Powerfarm Platform

Everything else is composed over the Kernel:

```
Auth, Auth Reviewer, Organizations, Relations, Delegation, Secrets,
Files, Jobs, Scheduler, Notifications, Search, Workflows, Approvals,
Integrations, Agents, Billing, IoT, Trajectory Engine, Simulation
```

Examples:

```
Workflow     = Commands + Rules + Acts + State
Agent        = Identity + Capabilities + Commands + Rules
Approval     = Command + ReviewRule + ReviewerIdentity + ReviewAct
Audit        = Acts + Relations + Identity + Rules
Organization = Identity + Relations + Rules
Scheduler    = Identity + Time + Command
```

### 19.1 Ratified Operational Profile

The first supported Powerfarm deployment profile is fixed as:

```
Clients / Agents
      ↓ HTTPS
Cloudflare DNS + dedicated Tunnel
      ↓ outbound-only connector
one macOS LAB
      ↓ private Postgres connection
Supabase Cloud
```

This profile is an implementation and operations decision, not a new Genesis
primitive. Moving the runtime later does not fork the Powerfarm universe as long
as content identity, the single commit gate, history, and all conformance laws
remain intact.

For this profile:

- compute MUST run directly on macOS in a Python virtual environment;
- the worker MUST run as the `com.powerfarm.worker` launchd user agent;
- `cloudflared` MUST run as the independent `com.powerfarm.tunnel` launchd user
  agent;
- stable release discovery MUST run as the independent
  `com.powerfarm.updater` launchd user agent;
- Docker, Docker Compose, containers, container images, and container
  orchestrators MUST NOT be required or shipped;
- Google open-source software MAY be used, but Google Cloud services MUST NOT be
  required;
- Supabase Cloud Postgres is the durable store for Objects, Acts, Relations,
  Registry, Identities, keys, and rebuildable projection substrates;
- Cloudflare owns authoritative DNS ingress for `powerfarm.app`; the LAB uses one
  dedicated named Tunnel, makes only outbound connections, and opens no inbound
  router port;
- `api.powerfarm.app` is the public commit/API hostname; additional hostnames are
  explicit routes and MUST fail closed when no ingress rule matches.

### 19.2 Database and Credential Boundary

Only the Mac LAB worker may receive the private Postgres connection string used
for runtime ledger access. Agents, browsers, public clients, and Cloudflare MUST
NOT receive database credentials or a direct write capability over Kernel tables.

Consequential writes MUST pass through the worker's Commit Gate and one atomic
database transaction. Supabase Auth, Data API, Realtime, and Storage are platform
surfaces around the Kernel; none is an alternative Act write path.

Kernel tables MUST use explicit least-privilege Postgres grants and RLS as
defense in depth. `anon` and `authenticated` MUST have no direct write privilege
over Objects, Acts, Relations, Registry, Identities, or identity keys. The Data
API SHOULD omit Kernel-internal tables from its exposed schemas. A Supabase
secret or service-role credential MUST never appear in a public client.
Backend credentials, the GitHub App private key, and webhook secrets MUST be
stored in the macOS Keychain or an equivalently protected local secret store;
they MUST NOT be embedded in the versioned pack or its environment example.

### 19.3 Versioned Idempotent Operational Pack

The supported deployment artifact is a versioned macOS pack containing at least:

```
install  update  uninstall  doctor  smoke  check-update
```

The pack is a convergence mechanism. Given the same pack version, source commit,
declared configuration, and supported toolchain, repeating `install` or `update`
MUST converge to the same operational configuration without duplicating tunnels,
DNS routes, launchd jobs, schema objects, or ledger facts.

The lifecycle contract is:

- `install` creates or reuses the LAB directories and Python environment, applies
  database migrations, creates or reuses the dedicated Tunnel and DNS routes,
  installs/reloads the worker, tunnel, and updater launchd agents, verifies
  health, and writes a receipt;
- `update` performs the same convergence for a declared version transition and
  is safe to repeat after interruption;
- `uninstall` stops and removes generated local services and configuration while
  preserving database history, LAB data, and receipts by default;
- destructive purge requires an explicit option, an exact validated target, and
  MUST NOT affect Supabase history or Cloudflare resources unless separately and
  explicitly requested;
- `doctor` validates prerequisites and installed state without changing them;
- `smoke` verifies the local worker plus the declared Tunnel ingress without
  creating a governed fact.

Every successful install, update, or uninstall MUST write a receipt containing
at least the pack version, source commit, action, hostname, and timestamp. A
receipt MUST NOT contain secrets. A failed or partial convergence MUST NOT write
a success receipt; rerunning the same operation must either complete convergence
or fail loud with the unmet invariant.

Dependencies and toolchain assumptions MUST be versioned or pinned sufficiently
to reproduce an installed build. Secrets belong in a private installed env file
or managed secret store, never in source control, Acts, logs, or receipts.

An update package MUST be content-addressed, carry a canonical manifest, and be
published with a checksum and verifiable build provenance. The LAB MUST verify
both checksum and provenance before extraction. Activation MUST use a versioned
release directory and an atomic current-version pointer. A durable copy MAY be
mirrored to private Supabase Storage, but package availability never grants the
package authority over the ledger.

### 19.4 Migration Contract

Database migrations are versioned operational artifacts. Install and update MUST
apply them in deterministic filename order with fail-fast transaction semantics.
Every shipped migration MUST be safe to re-run against the state it declares,
must preserve existing ledger history, and MUST NOT require a database reset.

Schema convergence does not authorize semantic history edits. Migrations may add
constraints, indexes, projections, functions, permissions, and new registered
vocabulary, but MUST NOT rewrite or delete existing Acts. Applied migration state
and pack version SHOULD be queryable remotely as well as recorded in local
receipts.

### 19.5 CI/CD and Integration Identity

For the ratified solo-developer profile, pull requests and `main` MUST be checked
by hosted CI before a release. Required checks MUST cover Kernel conformance,
JCS golden vectors, typing/linting, SQL parsing, immutable migration history,
two consecutive migration applications on a clean supported PostgreSQL,
database privilege invariants, shell validation, and byte-identical package
reproduction.

The LAB MUST NOT execute untrusted pull-request builds. A release is eligible
for automatic LAB convergence only when its tag resolves to `main`, all declared
version fields agree, its artifact checksum matches, and its build attestation
verifies. Updating is pull-based and repeatable; a webhook is an optimization,
not a source of release authority.

Repository automation MUST use a narrowly permissioned GitHub App. Its webhook
MUST be authenticated, bounded in size, event-allowlisted, and deduplicated
before entering an operational inbox. GitHub identity and Supabase OAuth client
identity are distinct integration boundaries. Neither a GitHub webhook nor a
GitHub App credential is a Powerfarm authorization decision or a second ledger
write path.

---

## 20. Confidentiality and History

Append-only, hash-chained history cannot be redacted without breaking integrity. Powerfarm therefore separates **commitment from content**:

- Acts may carry encrypted payloads, or commitments to ciphertext stored elsewhere.
- The Act hash commits to the ciphertext (or to the commitment), never requiring plaintext to verify the chain.
- Disclosure, re-encryption, and plaintext erasure happen outside history and never mutate it. Revocation of access is a change in key distribution, not in history.

An implementation MUST NOT store secrets as plaintext inside Acts, because Acts are permanent.

---

## 21. Trajectory

A Trajectory is not a Genesis primitive. It is constructed over the historical graph:

```
T = Select(G, purpose, cut)
```

A trajectory can preserve ancestry, causal ordering, branching, citations, evidence, review, doubt, failure, retry, correction, and consequence:

```
A1 → A2 → A3
          ├→ A4
          │    ↓
          │   A6
          └→ A5
               ↓
              A6
```

Branches share ancestry but never introduce cycles into the ancestry graph (§13.2); convergence is expressed through typed relations, not through ancestry. The global history is not itself necessarily one trajectory; multiple trajectories may be projected from the same graph.

*Formal Trajectory and Fold semantics are defined in a separate higher-order projection specification; the Kernel spec only guarantees the graph properties they rely on.*

### 21.1 Native Act Orientation

Where an Act uses the LogLine form:

```
who, did, this, when, confirmed_by, if_ok, if_doubt, if_not, status
```

its internal structure already supplies local orientation:

```
v_A = f(who, did, this, when)
```

while `if_ok / if_doubt / if_not` describe possible outward continuation directions. Typed hash relations provide long-range coupling among Acts. A Powerfarm trajectory is thus not merely a sequence — it is a path through a field of locally oriented, relationally coupled objects.

---

## 22. Fold

Fold is a derived property of a Trajectory — not current State, and not proof of authenticity. It is the higher-order structure acquired by a trajectory through its interaction with time, branching, evidence, doubt, contradiction, retry, correction, consequence, environment, and reality:

```
Trajectory × Reality → Fold
```

Fold analysis MAY use ActState, PairState, typed relations, temporal relations, causal polarity, branch topology, evidence topology, and consequence topology. Different Fold models may analyze the same immutable trajectory without changing it. Fold models are themselves registered projectors (§15.1).

---

## 23. Observed, Simulated and Crafted Trajectories

Powerfarm may represent trajectories produced under different regimes:

```
observed, simulated, crafted
```

These classes may share the same structural representation but MUST NOT lose their provenance. A simulated history may be structurally indistinguishable from an observed history while remaining historically distinct:

```
StructuralSimilarity ≠ HistoricalOccurrence
```

Simulation may generate history objects. It may not fabricate prior occurrence in reality.

---

## 24. Lineage

Simulated and crafted trajectories SHOULD preserve derivation relations:

```
simulated_from, mutated_from, crafted_from, spliced_from, forked_from
```

A lineage may look like:

```
                 T-real
                    │
            ┌───────┼───────┐
            ▼       ▼       ▼
           S1      S2      S3
          ╱  ╲              │
        S4   S5             S6
```

Because all relevant objects are content-addressed, lineage can be reconstructed without relying on mutable process memory.

---

## 25. Authorization Review Graph

The Auth Reviewer remains visible in the historical graph:

```
Identity I
    ▼
Command C
    ▼
Rule Evaluation R1
    ▼
require_review  →  ReviewRequested Act
    ▼
Reviewer Identity
    ▼
AuthorizationReviewed Act RA
    ▼
Rule Evaluation R2  (with RA as Context)
    ▼
allow  →  AuthorizationResolved Act
    ▼
Consequential Act A
```

The graph preserves not merely the outcome but the full authorization trajectory that produced it.

---

## 26. Conformance Laws

A conforming Powerfarm System MUST satisfy at least:

- **PF-01 Identity Required** — No consequential Command without a valid Identity and a verifiable proof of control.
- **PF-02 Registry Closure** — Governed objects require registered types, valid at the relevant cut.
- **PF-03 Intent Before Change** — Governed changes originate through Commands.
- **PF-04 Rule Governance** — Consequential Acts require applicable authorization.
- **PF-05 Reviewer Is Governed** — Auth Reviewers act only under derived authority.
- **PF-06 Review Is History** — Reviews relied upon for authorization are represented immutably as Acts.
- **PF-07 Immutable Acts** — Existing Acts are never edited in place; corrections are new Acts.
- **PF-08 CAS Integrity** — `H(Canonical(O)) = O.id` for all content-addressed objects.
- **PF-09 Typed Relations** — Relation semantics cannot be silently collapsed.
- **PF-10 Acyclic Ancestry** — Historical ancestry contains no cycles.
- **PF-11 Reference Discipline** — Objects reference other objects by content hash only; embedding by value is forbidden.
- **PF-12 Causal Order Constitutional** — Historical truth is the ancestry DAG; commit sequence numbers are operational cursors with gaps, never proof of order. Linearizations are projections.
- **PF-13 Declared Decision Cut** — Every authorization decision records the graph cut `c` it examined; commit against an advanced cut requires reauthorization or an explicit Rule permitting it. No silent TOCTOU.
- **PF-14 Context Typing** — All Context keys are registered and typed; every Rule declares the keys it reads; the authorizing Context hash is recorded in the Act.
- **PF-15 Lifecycle Completeness** — Every Command's lifecycle is reconstructible solely from Acts; no mutable out-of-band state channel exists.
- **PF-16 Deterministic Projection** — For registered projector P and cut t, `P(G_{≤t})` is reproducible bit-for-bit; every materialization records `projector_hash` and `history_cut`.
- **PF-17 Observation Provenance** — External-event Acts carry observer identity and evidence, and claim observation, not universal truth.
- **PF-18 No Plaintext Secrets in History** — Acts commit to ciphertext or commitments only.
- **PF-19 Acyclic Genesis** — The constitutional dependency graph contains no cycles.
- **PF-20 Self-Government** — All post-Genesis changes to Rules, Registry, authority, and keys occur exclusively through the Command → Rules → Act mechanism.
- **PF-21 Versioned Governance** — Every Act references the exact Registry and Rule versions under which it was validated; governed definitions are amendable only via §17.
- **PF-22 Domain-Separated Hashing** — All content hashes are computed over domain-tagged preimages (`powerfarm:<kind>:<version> || canonical bytes`); golden canonicalization vectors ship with the conformance suite.
- **PF-23 Unique Occurrence** — An Act's hash appears at most once in a universe's history; resubmission of identical content is idempotent.
- **PF-24 External Effects Phasing** — No Act may collapse Requested / Authorized / Dispatched / Observed / Committed-as-external-fact; a DB commit never claims external reality committed.
- **PF-25 Constitutional Change Discipline** — The constitution changes only via a Genesis-born amendment protocol or via fork/new Genesis. No third administrative door.
- **PF-26 Temporal Honesty** — `act.when`, causal order, and provable knowledge time are represented distinctly; external temporal anchoring uses the Genesis-reserved hook.

---

## 27. Changelog from v2 to v3 (incl. 3.2)

### Revision 3.2

1. **Operational profile ratified** — one direct macOS LAB, Supabase Cloud Postgres, and a dedicated outbound-only Cloudflare Tunnel serving `powerfarm.app`; Docker, Compose, containers, and Google Cloud services are excluded (§19.1).
2. **Database boundary fixed** — only the worker receives Postgres credentials; agents and public clients have no direct Kernel write path; explicit grants and RLS provide defense in depth (§19.2).
3. **Reproducible operations defined** — versioned idempotent install/update/uninstall plus doctor/smoke, receipts without secrets, data-preserving uninstall, explicit purge, and fail-loud convergence (§19.3).
4. **Migration contract defined** — deterministic, re-runnable, non-resetting migrations preserve immutable history and record applied operational state (§19.4).
5. **Human authentication profile fixed** — Supabase-managed passkeys and OAuth 2.1 authenticate platform principals without replacing stable Powerfarm Identity or Kernel authorization (§5.1).
6. **Delivery and integration identity fixed** — hosted conformance CI, reproducible attested releases, pull-based LAB updates, and a narrowly permissioned GitHub App form one automated path without becoming a second ledger writer (§19.5).

### Revision 3.1

1. **Canonicalization switched to JCS / RFC 8785** — golden vectors (`values`, `arrays`, `unicode`, `french`, `weird`, `structures`) bound at Genesis; browsers become first-class verifiers; binary payloads base64url; exact quantities avoid floats.

### Revision 3.0

1. **Commit order made honest (review point 1).** Ancestry DAG is constitutional; `seq` demoted to operational cursor with gaps; linearization is a projection. PF-12 rewritten.
2. **Referential and occurrence integrity (point 2).** `acts.hash` unique; Act hash = unique historical identity; resubmission idempotent (PF-23).
3. **TOCTOU closed (point 3).** `authorize(I, C, X, G_{≤c}, R_c)` declares its cut; drift triggers reauthorization or explicit Rule (PF-13).
4. **External effects protocol (point 4).** Five-phase pipeline with failure/retry Acts; DB commit never impersonates external reality (PF-24).
5. **Constitutional change defined (point 5).** Amendment-protocol-born-at-Genesis or fork; no third door (§4.2, PF-25).
6. **Domain-separated hashing (point 6).** `powerfarm:<kind>:<version>` tags; golden vectors required (§10.1, PF-22).
7. **Three notions of time (point 7).** `act.when` vs causal order vs provable knowledge time; Genesis-reserved temporal-anchoring hook (§10.3, PF-26).

## 28. Changelog from v1 to v2

1. Context `X` formally defined as a registered, typed map; Rules declare read keys (§2.1, PF-14).
2. Command lifecycle fully represented as Acts; pending/expired/superseded semantics defined (§6.1, §8.1, PF-15).
3. Embedding by value forbidden; references by hash only; canonicalization versioned and Genesis-bound (§10.1, PF-11).
4. Total commit order introduced via sequencer/consensus; history cuts defined over it (§10.2, PF-12) — **superseded by v3 item 1**.
5. Identity authentication and key rotation specified; rotation preserves stable Identity (§5.1).
6. Registry and Rule definitions versioned and referenced by Acts; constitutional core introduced (§4.1–4.2, PF-13 → renumbered PF-21 in v3).
7. `require_review` made Act-complete: `ReviewRequested`, `AuthorizationReviewed`, `AuthorizationResolved`; decisions never mutated (§8.1).
8. Projectors registered with content-addressed code; materializations carry `projector_hash` + `history_cut` (§15.1, PF-16).
9. Confidentiality separated from history via ciphertext/commitment discipline (§20, PF-18).
10. Acts split into internal facts and observed external events with provenance (§11.1, PF-17).
11. Trajectory and Fold scoped to a higher-order projection spec, with Kernel guarantees stated (§21–22).
