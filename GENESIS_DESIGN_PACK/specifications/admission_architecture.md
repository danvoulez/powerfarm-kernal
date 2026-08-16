# Admission Architecture — the Transaction Seam

Closes D-Txn-01. Incorporates R-18R, R-21, R-22.

Design document. No code, migrations, or commits.

---

## A. R-18R accepted — verified

| Claim | Verdict |
|---|---|
| `Context.types` is still name-based | **Confirmed** — [kernel/types.py:74](../../kernel/types.py:74): `types: Mapping[str, str]` |
| Derived keys become `"request.requested_by" → "request.requested_by"` | **Confirmed** — the service supplies the key name as its own type |
| `commit.py` checks the key *name* against the registry | **Confirmed** — [kernel/commit.py:90-94](../../kernel/commit.py:90) calls `registered("context_type", key, registry_cut)`, which is boolean-any-version |

So Context has exactly the Relation disease: meaning carried by a name, validated by name, with no version pinning. **R-18R adopted as stated** — Rule context semantics are hash-pinned; every context key a Rule reads is bound at the Rule's birth to the exact `context_type` definition hash and schema it was type-checked against, and the admitted Context records that hash. Later context-type versions cannot reinterpret a historical Rule evaluation.

Consequence I want explicit: this **replaces** my R-18. An ordinary context type may evolve freely without changing what an immutable constitutional Rule saw, because the Rule's dependency is pinned to the version it was born against. `request.metadata` stays ordinary and stays Rule-forbidden under R-4, which is a separate concern about open-shaped values defeating static type checking — not an ontological claim.

---

## B. R-21 accepted as strengthened — the dependency function

Your generalization is the right object. Formally:

```
D(K) = the set of historical inputs capable of changing the value of context key K
```

| Key class | `D(K)` |
|---|---|
| projector-derived (`budget.remaining`) | the act types the producing projector consumes |
| request-derived (`request.requested_by`) | ∅ for intervening history — resolved from the verified principal, not from `Δ` |
| cut-derived (`cut.advance`) | the advance itself; never eligible for irrelevance |

```
READ_SET = ⋃ D(K)  for every K read by every applicable Rule

Δ is irrelevant  ⟺  types(Δ) ∩ READ_SET = ∅
```

with conservative fallback to reauthorize whenever dependency completeness cannot be proven.

**And your enforcement point is the one that matters.** Linting declarations and trusting them is not a bridge to rung 1 — it is a bridge to a silent TOCTOU hole. A projector that reads an act type it did not declare produces a `READ_SET` that is too small, and too-small is the unsafe direction.

Two viable enforcement shapes, in preference order:

1. **Capability-style: the producer receives only its declared inputs.** A registered projector is invoked with a history slice restricted to its declared act types. An undeclared read is then not "detected" — it is *impossible*, because the data was never in scope. This is the stronger construction and it composes with §14's determinism requirement (a projector that cannot see undeclared input cannot depend on it).
2. **Instrumented: historical accesses are recorded and rejected when they exceed the declaration.** Weaker — it catches violations at runtime rather than preventing them — but viable where restriction is impractical.

**R-21 as ratified:** causal relevance requires mechanically complete dependency declarations. No Rule may treat an advanced cut as irrelevant unless every history-sensitive producer contributing to its read context has a mechanically enforced dependency set. Unknown or unverifiable dependency means reauthorization.

This is the gate on rung 1, and it should be stated as a precondition in CR-1's amendment, not as a project convention.

---

## C. `decision.read_set` — derived proof, never assertion

Agreed, and your stronger form is correct. It joins `authority.grants` and `request.requested_by` in the **kernel-derived, caller-forbidden** category, and beyond that it must be *recomputable* rather than trusted:

```
decision.rule_hashes
      ↓ registered Rule definitions at the registry cut
static context accesses
      ↓ exact context_type definition hashes          (R-18R)
registered producers / projectors
      ↓ their exact dependency declarations           (R-21)
READ_SET
```

Every link is already pinned by hash, so the value is a **derived proof object carrying no new authority**. If a supplied or reconstructed value disagrees with recomputation, fail closed.

Two consequences:

- It is verifiable by any party who can read the Registry at that cut — including a future auditor with no access to the service that produced it.
- It cannot be used to *grant* anything. It only ever narrows what counts as relevant, and narrowing wrongly fails toward reauthorization.

**And your point on the count is taken.** 103 was inventory, not architecture. Under R-18R and this derivation, `decision.read_set` is recomputable rather than supplied, so it need not be a stored context type at all — it is a *function of things already pinned*. That removes one of the three I proposed:

| Proposed | Status |
|---|---|
| `cut.declared` | **keep** — CR-1 must read the declared cut as context |
| `cut.advance` | **keep** — the advance is the subject of the decision |
| `decision.read_set` | **drop as a context type** — derived on demand from `rule_hashes`; adding it as vocabulary would invite treating it as an input rather than a proof |

Genesis returns to **102 definitions** (+2, not +3). The plumbing argument still holds — the *derivation* must exist and be exercised from day one — but it is a service capability, not a vocabulary item.

---

## D. R-22 accepted — and its price, which must be paid now

The domains are genuinely distinct:

```
authorization disposition   :  allow | deny | require_review
decision-validity disposition:  VALID | REAUTHORIZE | COMMIT_REGARDLESS
```

CR-1 is a **decision-validity Rule**, not another authorization vote. It must not be folded into `authorize()`'s `DENY > REQUIRE_REVIEW > ALLOW` collapse ([kernel/rules.py:45-50](../../kernel/rules.py:45)), and `deny` must never be made to stand in for `REAUTHORIZE`.

v1:

```
current_cut == decision_cut   →  VALID
current_cut != decision_cut   →  REAUTHORIZE
COMMIT_REGARDLESS             →  unreachable (R-17)
```

**The price:** the Act must attest CR-1's hash and the validity disposition that permitted admission, and `rule_hashes` must stay purely authorization. That means two new fields in the Act preimage:

```
validity_rule_hash
validity_disposition
```

Which changes every Act hash. Free now. Impossible later.

---

## E. The preimage window — four changes, one deadline

These have accumulated across the design and they share a property worth stating together, because it is the highest-stakes pre-Genesis fact we have:

| # | Change | Source | Changes |
|---|---|---|---|
| 1 | `Relation.relation_type` → `relation_type_hash` | R-15R / Micro-Spec :243-273 | relation hashes |
| 2 | `Context.types` → definition hashes | R-18R | context hashes → act hashes |
| 3 | Act preimage `+ validity_rule_hash, validity_disposition` | R-22 | every act hash |
| 4 | research node `created_at` → `claimed_when` | R-13 | research node hashes |

**All four are free before `GenesisClosed` and require amendment or fork afterwards.** They are not implementation TODOs that can be sequenced comfortably behind Phase 0 — they are shape decisions on content identity, and content identity is the one thing Genesis makes permanent.

Recommend treating these as a single ratification item alongside `genesis.yaml`.

---

## F. The admission architecture

### F.1 The question

> How do we make "Act admitted without its required canonical consequences" impossible, while keeping
> policy evaluation in Rules rather than slowly rebuilding a second Rule engine in SQL?

### F.2 The answer: a declarative companion contract, resolved from the Registry

The act type declares what must accompany it. The gate resolves that declaration **at the Act's own registry cut** and enforces it structurally.

```json
{
  "kind": "act_type",
  "name": "DefinitionRegistered",
  "version": 1,
  "companion": { "writer": "registry", "cardinality": "exactly_one" }
}
```

`cardinality ∈ {none, exactly_one, one_or_more}`. `writer` names one of a small fixed set of internal companion writers, one per authoritative table.

The gate then enforces, in one transaction:

- act type declares no companion → supplied companions must be empty;
- act type declares a companion → companions must be present, target that writer, and satisfy cardinality;
- rows are written by the named internal writer **before the function returns**;
- any failure aborts everything.

**Why this is not a second Rule engine.** The gate performs *resolution and structural enforcement* — a registry lookup, a writer dispatch, and a count. It never decides whether the Act *should* be admitted; that remains entirely upstream in Rules. The distinction is exact:

| | enforces | does not enforce |
|---|---|---|
| **SQL gate** | indivisibility: no Act of a companion-declaring type exists without its rows | whether the Act was authorized, whether the rows are semantically right |
| **Kernel** | correctness: rows well-formed against the schema, values right, semantics hold | atomicity |

Neither duplicates the other, and the boundary is the same one the system already draws everywhere else: structure in the database, meaning in the Kernel.

**Why resolving at the registry cut matters.** A historical Act is judged by the companion contract in force when it was admitted — PF-21 semantics applied to companion requirements. If `DefinitionRegistered.v2` later adds a requirement, `v1` Acts remain valid under `v1`'s contract. No retroactive reinterpretation, which is exactly §4.1.

**Extensibility, honestly bounded.** New act types reuse existing writers with no SQL change. A genuinely new authoritative *table* requires DDL anyway, so requiring a gate amendment at that moment is honest rather than limiting — and it is rare by construction, since the whole architecture pushes new meaning into vocabulary rather than new tables.

**This closes six holes with one mechanism**, not one: `registry`, `relations`, `principal_bindings`, `identity_links`, `identities` and `identity_keys` are all currently read-but-unwritten. They stop being six separate wrapper problems and become six declarations.

### F.3 One door

```
revoke execute on powerfarm_internal.commit_act(...) from powerfarm_worker
grant  execute on powerfarm_internal.begin_admission()  to powerfarm_worker
grant  execute on powerfarm_internal.admit(...)         to powerfarm_worker
```

Authoritative tables remain `select`-only. Bare `commit_act` is not merely discouraged — it becomes **unreachable**, folded into `admit` as an internal step. There is no alternative route to revoke because there is no alternative route.

This is the same enforcement posture that already makes the wrapper design safe: the invariant lives in grants, not in discipline.

### F.4 The admission sequence

Preserving your shape, with the CR-1 round-trip inside the lock:

```
BEGIN                                     -- connection C, one transaction
  cut ← begin_admission()                 -- pg_advisory_xact_lock('powerfarm:commit-gate:v1')
                                          -- returns the authoritative current cut,
                                          -- atomically with taking the lock
  ── Python ──────────────────────────────
  disposition ← CR-1(declared_cut, cut, READ_SET)
  if disposition = REAUTHORIZE:  ROLLBACK; return conflict
  ────────────────────────────────────────
  act ← admit(act…, validity_rule_hash, disposition, companions[])
        -- asserts the lock is held
        -- re-reads the cut and asserts it still equals `cut`
        -- constitutional checks (as today)
        -- resolves the companion contract at p_registry_cut
        -- inserts the Act
        -- dispatches companion rows to the declared writer
COMMIT
```

The lock is `pg_advisory_xact_lock` — transaction-scoped, released on COMMIT or ROLLBACK. Because only the gate writes Acts and the gate requires the lock, the lock **is** the serialization point. The re-read inside `admit` cannot fail while the lock is held; asserting it anyway converts an assumption into a check, which is cheap and is the difference between "nothing can interleave" and "nothing did."

Business Rules evaluate **before** `BEGIN`. CR-1 is the final gate against the actual admission cut. That is the ordering your race analysis requires, and it is the only ordering that closes it: fixing PF-13 in Python and then reopening it between Python and Postgres is precisely what a single-connection, lock-held round-trip prevents.

### F.5 Costs, stated plainly

**A transaction stays open across a Python round-trip.** That extends how long the global admission lock is held. Three honest notes:

- The round-trip is small: CR-1 v1 is a set comparison; rung 1 is a set intersection over act types.
- It does not *add* serialization — admission is already globally serialized by the advisory lock. It lengthens the critical section.
- **Rung 1 does not increase admission parallelism.** The lock still serializes commits. Its benefit is that a decision whose cut drifted need not **re-run authorization** — which may be expensive (LLM-driven Rule evaluation, review chains, budget projection). That is the real saving, and it is substantial for this system. I would not want it sold as throughput.

**Connection affinity becomes a requirement.** `PostgresStore`'s connection-per-method design ([ledger/postgres.py](../../ledger/postgres.py)) cannot express this. The Ledger needs an explicit admission scope that pins one connection for the sequence. This is a narrowing of the persistence contract, not a widening — and the pack already says the `Store` method count is not an invariant.

**CAS writes stay outside.** `put_object` for command, context and payload continues to precede the admission transaction. Orphans remain harmless candidate content, and `admit` continues to verify presence. Nothing about the companion contract changes that boundary.

### F.6 What this makes Phase 0

Not a collection of wrappers. A single admission function with a declarative contract, where:

- adding a governed writer is **a definition**, not a migration;
- omitting a canonical consequence is **structurally impossible**, not a review finding;
- the constitutional checks live in one place and run once;
- policy stays entirely in Rules.

The six read-but-unwritten tables were never six bugs. They were one missing mechanism.

---

## G. Rulings

| ID | Question | Recommendation |
|---|---|---|
| **R-18R** | Hash-pinned Rule context semantics | **Adopted as stated.** Replaces my R-18 |
| **R-21** | Mechanically enforced dependency declarations | **Adopted as stated**, with capability-style restriction preferred over instrumentation |
| **R-22** | Distinct typed dispositions | **Adopted.** Requires two new Act preimage fields — §D |
| **R-23** | Drop `decision.read_set` as a context type; derive it | **Yes** — it is a proof, not an input. Genesis returns to 102 |
| **R-24** | Companion contract declared in the act_type definition | **Yes** — the core of §F.2 |
| **R-25** | Revoke `commit_act`; fold it into `admit` | **Yes** — one door, enforced by grants |
| **R-26** | Ratify the four preimage changes as one pre-Genesis item | **Yes** — §E. Highest-stakes deadline in the project |
| **R-27** | Ledger gains an explicit admission scope pinning one connection | **Yes** — required by §F.4; narrows the contract rather than widening it |

---

## H. Next

The four preimage changes (§E) are the item I would put in front of everything else now. They are
small, they are decided, and they are the only work in this project with a hard deadline that is not
of our choosing.

After that, Phase 0 in dependency order: the admission function and companion contract, then the
Genesis promoter that uses it, then the Registry writer, then relations — each one now a declaration
against an existing mechanism rather than a new seam.
