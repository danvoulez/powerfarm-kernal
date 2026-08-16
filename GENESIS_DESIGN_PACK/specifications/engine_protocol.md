# Powerfarm Engine Protocol + Consolidated Decision Register

Covers steps 1–3 of the revised order: preimage freeze, ADK rulings recorded, generic Engine
Protocol defined.

Design document. No code, migrations, or commits.

---

# PART 1 — Corrections adopted

## 1.1 External-effect semantics — my claim was too strong

I wrote *"at-least-once execution must produce at-most-once effect."* Powerfarm cannot guarantee
at-most-once **reality**. Where the external system offers no idempotency key and no queryable
transaction identity, a dispatch whose response is lost is genuinely ambiguous, and no amount of
local discipline resolves it.

**And the ordering error matters more than the phrasing.** I wrote that the dispatch record is
written *"before the external call returns."* That leaves the classic duplicate window: crash after
external execution, before local persistence, and Powerfarm has no record that it ever dispatched.

Corrected ordering:

```
EffectRequested / Authorized
        ↓
durably establish effect_id + dispatch intent      ← BEFORE dispatch begins
        ↓
dispatch, using effect_id as idempotency key where the protocol supports it
        ↓
record observation / receipt
        ↓
ambiguous outcome → reconciliation state, never blind retry
```

## 1.2 Identifier phrasing — sharpened

My *"none enters Powerfarm canonical identity"* was right in intent and loose in wording. Correct
form:

> Runtime identifiers may be **canonically preserved as claims/correlation data inside an evidence
> object**, which then receives its own Powerfarm content hash. They never substitute for Powerfarm
> content identity.

```json
{ "engine": "google.adk", "invocation_id": "…", "event_id": "…",
  "node_path": "…", "captured_content_hash": "…", "captured_when": "…" }
```

That whole object is hashed. The identifiers are inside the canonical content — preserved, not
promoted.

## 1.3 Protocol and profile are two layers

Adopted. Otherwise the first engine silently defines the generic interface.

```
POWERFARM ENGINE PROTOCOL          ← stable architectural interface (Part 3)
        ↑ satisfied/described by
ExecutionEngine definition         ← ordinary Registry object
  family: google.adk
  version: 2.7.0
  capability profile: …
```

---

# PART 2 — Consolidated decision register

Canonical list. Supersedes scattered numbering in earlier documents.

## 2.1 Frozen — canonical preimages

| ID | Decision | State |
|---|---|---|
| **R-23** | `decision.read_set` is derived, not a context type | **frozen** |
| **R-24** | Companion contract declared in the act_type definition, resolved at the registry cut | **frozen** |
| **R-25** | Revoke bare `commit_act`; fold into `admit`; one door enforced by grants | **frozen** |
| **R-26** | Ratify the four preimage changes as one pre-Genesis item | **frozen** |
| **R-27** | Ledger gains an explicit admission scope pinning one connection | **frozen** |

**The four preimage changes, now frozen (R-26):**

1. `Relation.relation_type` → `relation_type_hash`
2. `Context.types` → definition hashes, not names
3. Act preimage `+ validity_rule_hash, validity_disposition`
4. research node `created_at` → `claimed_when` where it is a hashed content assertion

ADK adds none. Execution provenance lives under `payload_hash`, so the universal Act format never
needs to know what Google ADK is — which is what keeps Powerfarm able to govern ADK, mistral-rs,
A2A remote agents, human procedures, laboratory robots and future engines without changing Act
physics.

*R-28 is unused in this register and left **reserved** rather than assigned a retrospective meaning.*

## 2.2 ADK / execution rulings

| ID | Ruling |
|---|---|
| **R-29** | **ADK evidence capture is copy-by-content, never reference-by-runtime-coordinate.** Rewind or deletion in an execution engine may change the engine's live view, but may never retroactively alter evidence already admitted by Powerfarm |
| **R-30** | **External-effect retry semantics.** An engine may provide at-least-once unit execution. Powerfarm provides stable logical effect identity, durable pre-dispatch intent, idempotency where the external protocol supports it, and reconciliation rather than blind retry where outcome is ambiguous |
| **R-31** | Engine-side rewind/undo constructs are never mirrored into Powerfarm history |
| **R-32** | Constitutional enforcement never lives in an engine plugin/callback. Plugins are sensors; the governed capability wrapper is the gate |
| **R-33** | An engine confirmation flag is never authorization. Authority is the admitted review chain, verified by the governed capability |
| **R-34** | Runtime identifiers are canonical *content* of evidence objects, never Powerfarm object identity |
| **R-35** | Engine registries are execution discovery, never the Powerfarm Registry |
| **R-36** | Three falsifiable compatibility tests — Part 5 |
| **R-37** | Engine Protocol and engine capability profile are separate layers |

## 2.3 Carried, still open

R-1 (drop `SubmitCommand`), R-4 (`request.metadata` open shape, Rule-forbidden), R-5 (no
`effect_kind` at Genesis), R-7 (`authority.grants` caller-refused), R-9, R-11, R-12, R-14, R-17,
R-19, R-20, R-21, R-22.

Constitutional decisions unchanged: D-Genesis-01(refined)…05, D-Authority-01…04, D-Director-01…08,
D-Txn-01, D-PF13-01/02, R-15R, R-18R.

---

# PART 3 — The Powerfarm Engine Protocol

## 3.0 The membrane

> **Authorization going down. Immutable evidence coming up.**

The protocol is deliberately thin and deliberately serious. It states what Powerfarm requires of
*any* execution engine, in terms no engine's vocabulary appears in.

| Direction | Crosses | Never crosses |
|---|---|---|
| **down** | execution request, authorization envelope, plan reference, correlation identity, budget ceiling, required evidence classes | Powerfarm authority as a value the engine may edit or widen |
| **up** | evidence, observations, receipts, artifacts, candidates, disposition | anything that becomes an Act without admission; anything Powerfarm must trust to remain available |

## 3.1 P-1 Execution request

Powerfarm hands down a request pinning, by hash: the execution plan, the engine profile, the
authorization envelope, the budget ceiling reference, the correlation identity, and the evidence
classes required back.

**The envelope is a capability grant, not configuration.** The engine may narrow what it uses; it
may never widen it. An engine that can edit its own envelope has become an authority.

## 3.2 P-2 Correlation

Powerfarm mints a correlation identity; the engine echoes it in every evidence object it returns.
The engine's own identifiers are recorded as claims *inside* evidence (R-34). Neither substitutes
for the other, and the correlation identity is opaque to the engine — it carries no authority and
decodes to nothing.

## 3.3 P-3 Evidence capture

- Evidence is captured **by copy of content**, hashed at capture (R-29).
- Runtime coordinates travel as correlation claims inside the evidence object.
- Every evidence object declares its **capturing observer Identity** and may claim only what that
  observer reported (§11.1).
- The engine's live view may change afterwards; admitted evidence may not.

## 3.4 P-4 Artifact capture

Same rule, applied to large or binary output. Content hash is identity; engine coordinates
(filename, version, URI) are locators recorded as claims. **An artifact must be copied into
Powerfarm-controlled content-addressed storage before any admitted object references it.**

## 3.5 P-5 Interruption and review

The engine must be able to suspend a unit, surface a request, and resume it.

```
Powerfarm REQUIRE_REVIEW
      ↓ review requirement, reviewed Command pinned
engine suspends, surfaces the ask
      ↓ human responds
Powerfarm admits the review / resolution Acts
      ↓ resumption carries a *reference* to the admitted resolution
governed capability verifies the admitted authorization chain
      ↓
execution resumes
```

**The resumption payload is never the authority** (R-33). An actor setting a confirmation flag,
replaying an old confirmation, or reaching the capability by another path must not create authority.
The governed capability verifies the chain itself, every time.

## 3.6 P-6 External effects

The protocol's most demanding requirement, and the one engines legitimately decline to provide.

- Every authorized external effect has **one stable logical effect identity**, minted by Powerfarm.
- **Dispatch intent is durable before dispatch begins** (§1.1).
- All retries reuse the same effect identity; the idempotency key is that identity wherever the
  external protocol supports one.
- **Powerfarm never knowingly originates a second logical effect because execution resumed.**
- Where the external system cannot prove idempotent or reconcilable execution, an ambiguous outcome
  is a **reconciliation state**, not an automatic retry.
- No engine may originate an external effect outside a governed capability.

## 3.7 P-7 Resumability semantics

The engine **declares** its guarantee: `none | at-least-once | exactly-once`, and whether it can
express **per-unit rerun semantics**.

This produces a capability gradient rather than a binary:

| Engine can express per-unit non-rerun? | May host |
|---|---|
| yes | consequential external effects |
| no | pure computation and evidence production only |

An engine that cannot mark a unit as non-rerunnable is not disqualified — it is qualified for less.
Rules then require a minimum profile for a given class of work.

## 3.8 P-8 Cancellation

Powerfarm may request cancellation. The engine must report **actual** disposition truthfully —
including "too late, already dispatched," which is itself evidence and must not be reported as
cancelled. Cancellation is a request, never a guarantee.

## 3.9 P-9 Final disposition

Every execution terminates in exactly one declared disposition:

```
completed · failed · cancelled · abandoned · awaiting-review
```

**"Unknown" is not a disposition** — it is a reconciliation state. This is what lets budget
settlement close honestly (`reason = abandoned | failed | cancelled`) rather than inventing an
outcome.

## 3.10 P-10 Provenance

Every evidence object traces to: the execution request, the engine profile in force, the capability
that produced it, and the observer that captured it. An evidence object that cannot answer all four
is not admissible.

## 3.11 What the protocol forbids any engine

Writing Powerfarm history directly; conferring identity or authority; making its own registries
authoritative; producing institutional facts without admission; serving as the durable home of
evidence; widening its own authorization envelope.

---

# PART 4 — Capability profiles

An `ExecutionEngine` definition is an **ordinary Registry object** declaring which protocol
requirements the engine satisfies and how:

```
ExecutionEngine
  family:                google.adk
  version:               2.7.0
  satisfies:             P-1 … P-10, each with a mapping note
  resumability:          at-least-once, per-unit rerun expressible
  external_effects:      via governed capability wrapper only
  evidence_capture:      copy-by-content at capture
  interruption:          suspend/resume with reference-carrying resumption
```

Rules then require a minimum profile for a class of work — *"consequential external effects require
an engine profile satisfying P-6 and P-7 with per-unit non-rerun expressible."* Because profiles are
ordinary registered objects pinned by hash, an Act records exactly which profile was in force, and a
later engine version is a new profile rather than a silent reinterpretation.

This is what keeps ADK from becoming synonymous with the protocol: **the protocol states
requirements, the profile states satisfaction, and Rules state what is required for what work.**

---

# PART 5 — Compatibility tests (R-36)

All three falsifiable, all three failing loudly.

1. **A Powerfarm-governed ADK App remains deployable on Google Agent Engine without forking ADK.**
   Forbids subclassing internals, depending on private paths (`tools/_node_tool.py` is the known
   private surface), patching the Runner, or assuming a local-only session/artifact backend.
2. **A normal ADK App that does not use Powerfarm remains a normal ADK App.** Integration is through
   public extension surfaces only; no global mutation of ADK semantics, no import-time monkey-patching,
   no behaviour change for apps that never opted in.
3. **Powerfarm institutional history remains valid when the corresponding ADK Session, Events or
   Artifacts are rewound or deleted after evidence capture.** This directly exercises R-29 and is the
   test that fails if the trajectory adapter ever links instead of copies.

Test 3 is the one I would build first. It is the cheapest to write and it protects the boundary
whose violation cannot be repaired retrospectively.

---

# PART 6 — Engine-neutrality check

The protocol claims to be engine-neutral. Testing that claim against engines with nothing in common
with ADK:

| Engine | P-1 request | P-3 evidence | P-6 effects | P-7 resumability | P-9 disposition |
|---|---|---|---|---|---|
| **Google ADK 2.7** | plan + envelope → App/Workflow | Events copied, hashed | governed tool wrapper | at-least-once, per-unit expressible | node status → disposition |
| **Human procedure** | a work order | signed forms scanned and hashed | the human performs; dispatch intent recorded first | none declared → effects need explicit per-step records | declared by the operator |
| **Laboratory robot** | a run specification | instrument output hashed at capture | actuation via governed capability | typically none | reported by the controller |
| **A2A remote agent** | plan + envelope over the wire | converted events, copied and hashed | governed capability at the boundary | per remote declaration | reported disposition |
| **Future engine** | — | — | — | declared | declared |

The protocol holds. Nothing in P-1…P-10 mentions agents, models, workflows, sessions or tools —
which is the property that was at risk if ADK had been allowed to define the interface implicitly.

The human-procedure column is the useful stress test: an engine with *no* resumability guarantee is
still governable, it simply cannot host effects that rely on rerun safety. That is the gradient in
P-7 doing its job.

---

# PART 7 — Next

Per your order, remaining: **the Google ADK 2.7 compatibility profile** (step 4), then the admission
architecture (step 5).

The profile is now a mechanical exercise — the absorption matrix supplies every mapping, and the
protocol supplies every slot. Writing it is also the real test of Part 3: if any P-requirement turns
out to have no engine-neutral expression and can only be stated in ADK's vocabulary, the protocol
has been contaminated and that requirement needs rewriting.

That is the check I would run before treating Part 3 as settled.
