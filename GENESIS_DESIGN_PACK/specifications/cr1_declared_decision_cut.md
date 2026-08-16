# Part VIII Freeze + CR-1 `declared-decision-cut`

Design document. No code, migrations, or commits.

---

## Part A — Part VIII frozen

### A.1 R-15R accepted, and the evidence is stronger than stated

Your three claims verified against source:

| Claim | Verdict |
|---|---|
| Micro-Spec already binds relations by definition hash | **Confirmed** — `02_Powerfarm_Micro_Specs_v1.1.md:243-273`: `relation_type_hash`, and *"`display_relation_type` never determines meaning"*; `"lineage": true` comes from the registered definition |
| `kernel/types.py` has not caught up | **Confirmed** — [kernel/types.py:134-143](../../kernel/types.py:134): `relation_type: str`, and the hash preimage carries `"relation_type": self.relation_type`. Implementation TODO against the Micro-Spec |
| A four-name whitelist is visibly incomplete | **Confirmed, and worse than stated** — spec §24 names **five** lineage relations: `simulated_from, mutated_from, crafted_from, spliced_from, forked_from`. **`mutated_from` and `spliced_from` are not seeded at all.** My whitelist omitted two the specification already requires |

The last point settles it independently of the argument: a whitelist that is already missing two spec-named members is not a boundary, it is an accident of what happened to be seeded.

**R-15R adopted as stated.** The constitutional property is semantic — relations bind their exact registered definition by hash; relation definitions declare lineage/provenance semantics; synthetic and crafted ancestry is preserved through admitted lineage; and no synthetic history may be admitted or represented as prior external observation by changing vocabulary, projection, approval, or relation version.

And your §11.1 point is the harder boundary, so I want it recorded explicitly: **synthetic material can contribute to reasoning, but it cannot manufacture `ObservationAdmitted`** — that Act requires an observer Identity and evidence references, and may claim only what that observer reported. Freezing a relation name never protected that; the observation requirements always did.

Same reasoning applied to `projects_as`: it stays ordinary. The constitutional property is that a public projection does not rewrite or erase its private source history and disclosure does not convert private ancestry into public ancestry. The `projects_as` Relation pins its definition hash and the publication Act pins the disclosure profile hash, so historical disclosure stays interpretable regardless of how the publication ontology evolves.

### A.2 R-13 qualified as you specified

Three clocks, not one rename:

| Clock | Meaning | Hashed? | Causal evidence? |
|---|---|---|---|
| `claimed_when` | content assertion — what the object claims | **yes** | no |
| causal ancestry | constitutional ordering (§10.2) | via parents | **yes** |
| `created_at` / `materialized_at` | operational DB/projection timestamp | no | **never** |

So: Research Scheme §27's field is inside the **canonical hashed payload**, which makes it a content assertion — therefore `claimed_when`. Projection rows in `proj_nodes` keep `created_at`/`materialized_at`, explicitly operational, never used as causal evidence. No mechanical rename.

### A.3 Frozen state

R-10 closed (Research Scheme = founding Research Compass, `ResearchCompass` its root object; no parallel ontology). Zero new constitutional research definitions. Research species remain ordinary. `proj_nodes`/`proj_node_edges` disposable; `research_jobs` disposable metabolism. Canonical Relations carry definition hashes, not semantic names. `authority.grants` caller-supplied forbidden. `supersedes` added. R-2 `ExternalFactClaimed`, R-3 `root-mandate`, R-6 one lifecycle source. R-15R replaces R-15. R-13 qualified.

**Genesis total: 100 definitions**, plus one new context family for CR-1 (§B.5) — see the revised count in §B.9.

---

## Part B — CR-1 `declared-decision-cut`

### B.1 The constitutional meaning that must survive every amendment

This is the sentence an amendment may never weaken:

> **Whenever the history cut has advanced between authorization and commit, the disposition of that
> advance is decided by CR-1 and recorded in the resulting Act's `rule_hashes`. No Act commits
> against an advanced cut without CR-1 having evaluated that advance. The disposition is never a
> default, never implicit, and never decided by code outside the Rule.**

Note what this does *not* fix: it does not fix the **criterion**. v1 is strict; a later version may admit causally irrelevant advances. Both satisfy the invariant, because the invariant is about *attribution and non-silence*, not about strictness. That is exactly what §2:97 requires — *"the kernel MUST decide by Rule… A silent default is forbidden."*

The current implementation is fail-closed and correct in behaviour. What it lacks is the second half: nothing in any Act records that a drift decision was made, because a constant made it.

### B.2 Decision domain mapping

PF-13 names three dispositions; Powerfarm Rules return three outcomes. They are not the same three.

| PF-13 disposition | Rule outcome | Lifecycle result |
|---|---|---|
| decision remains valid | `allow` | commit proceeds |
| may be committed regardless | `allow` (distinct reason) | commit proceeds — **v1 never returns this** |
| must be reauthorized against `c'` | `deny` | `CommandDenied` with a drift reason |

Two consequences worth being explicit about:

**Reauthorization is denial-then-re-evaluation, and that is correct.** Denying the stale attempt and re-evaluating at the current cut *is* reauthorization. The Command is not dead: `CommandDenied` is a lifecycle Act, and per PF-15 a Command's lifecycle is many Acts. The same Command content re-evaluated at cut `c'` yields a **different Act** — `decision_cut` is in the Act preimage — so it can legitimately reach consequence later. The stale denial stays in history as the record that drift occurred.

**`require_review` is deliberately unused by v1.** Drift needs re-evaluation, not human judgment. It remains available to a future version (e.g. "the advance is large or touches contested state — ask a reviewer"), which is a reason to leave the outcome domain untouched rather than narrowed.

### B.3 What may make a decision survive an advanced cut

Your direct question. A ladder, from sound to dangerous:

| Rung | Criterion | v1 | Notes |
|---|---|---|---|
| 0 | **No advance.** `c' = c` | **admitted** | Trivially survives; the only rung v1 admits |
| 1 | **Causally irrelevant advance.** No Act in `Δ = c' \ c` can change any value the decision's Rules read | not admitted | The intended v2. Sound *iff* the read-set derivation is complete — §B.4 |
| 2 | **Monotone-safe advance.** `Δ` only strengthens the justification (e.g. additional approvals) | not admitted | Requires reasoning about direction of effect; a Rule that is "more satisfied" may still be differently satisfied |
| 3 | **Commutative/idempotent command.** The command's effect does not depend on what else happened | not admitted | Hard to establish soundly; needs executable evidence |
| 4 | **Unconditional commit-regardless** | not admitted | The TOCTOU permit. §2 allows a Rule to return it; CR-1 never does |

**Genesis behaviour: rung 0 only.** Any advance whatsoever → `deny` → reauthorize.

Rung 1 is the one worth building toward, because rungs 2–4 trade soundness for throughput while rung 1 does not: a genuinely irrelevant advance changes nothing the decision depended on, so allowing it is not a weakening at all — it is a correction of an over-approximation. The current whole-history-equality test treats *every* concurrent Act as relevant, which is why the system is globally serialized at the authorization boundary.

**Proposed protection (R-17):** add to the eternity clauses that **CR-1 may not be amended to permit unconditional commit-regardless (rung 4)**. §2 permits that disposition in general; this universe declines it permanently. Rungs 1–3 remain amendable on evidence.

### B.4 The read-set derivation — what makes rung 1 decidable

The chain already exists in the design; nothing new is required except connecting it.

```
applicable Rules
     │ each statically declares its context keys        (§2.1 — already mandatory)
     ▼
context keys read by this decision
     │ each context type declares its producing projector
     ▼
projectors
     │ each declares the act types it consumes          (Part VIII §8.3 `inputs`)
     ▼
consumed act types
```

Then:

> An advance `Δ` is **causally irrelevant** to a decision iff no Act in `Δ` has a type consumed by
> any projector producing any context key read by any Rule applicable to that decision.

Three properties make this safe to build toward:

- **It is over-approximating in the right direction.** If the derivation is incomplete, it will find *more* relevance than exists, and reauthorize unnecessarily. Failure is toward strictness.
- **It is decidable statically.** No evaluation, no history traversal beyond `Δ`'s act types.
- **Every input is already mandatory** for other reasons — §2.1 requires context-key declaration, and projector `inputs` is needed for projection rebuild regardless.

**The one soundness hazard**, stated plainly: a Rule that reads a context value whose projector is under-declared. If a projector consumes an act type it does not list, relevance is missed and TOCTOU reopens *silently*. So rung 1 must not be admitted until projector input declarations are verified — mechanically, not by review. That is the same class of requirement as R-6's single lifecycle source.

### B.5 Declared context inputs — the schema that must exist from Genesis

This is the part that makes a later amendment change **only the Rule body**, never the surrounding machinery.

CR-1 v1 declares three context keys and reads all three. It *uses* two.

| Context type | `value_schema` | v1 use |
|---|---|---|
| `cut.declared` | `{cut: [hash]}` | the cut the decision examined |
| `cut.advance` | `{advanced: bool, delta: [hash], delta_act_types: [hash]}` | **decides on `advanced`** |
| `decision.read_set` | `{resolved: bool, context_keys: [string], projector_hashes: [hash], consumed_act_types: [hash]}` | **declared and supplied; ignored by v1** |

Declaring `decision.read_set` from Genesis is deliberate. It means the service computes and supplies
it from day one, the plumbing is exercised long before it is trusted, and the amendment to v2 is a
change to the Rule's body alone — not to the Context vocabulary, not to the Act preimage, not to the
projector metadata contract. §2.1's rule that a missing declared key is a **loud** evaluation failure
means the plumbing cannot quietly rot while unused.

`resolved: false` means the read-set could not be computed at this cut. **v1 ignores it. v2 must
deny when it is false** — fail closed, never "assume irrelevant."

All three are **constitutional** context types, which follows from:

> **Proposed general invariant (R-18): a constitutional Rule may read only constitutional context
> types.**

Otherwise ordinary governance could redefine what a constitutional Rule sees, and the Rule's meaning
becomes amendable by ordinary means — the same laundering shape as R-15, one level up. This
invariant is already implicitly respected: every seeded context type is `constitutional = true`
except `request.metadata`, which is exactly the one R-4 says no Rule may read.

### B.6 CR-1 definition schema

```
kind:            rule
name:            declared-decision-cut
version:         1
constitutional:  true

context_keys:    [cut.declared, cut.advance, decision.read_set]

applicability:   [every constitutional command type hash]
                 frozen at registration; growth requires amendment

body:            if not cut.advance.advanced  -> allow  ("declared cut intact")
                 else                          -> deny   ("history advanced after
                                                          authorization; reauthorization
                                                          required")

parameters:      survival_rungs_admitted: [0]
```

`survival_rungs_admitted` is the amendment surface. v2 would be `[0, 1]` with a body that consults
`decision.read_set`. Making it an explicit parameter rather than implicit in the body means an
amendment diff shows the policy change on one line, and the enacted definition states its own
strictness rather than requiring someone to read code.

### B.7 Relationship to the three hardcoded checks

The existing checks — [service/authority.py:189](../../service/authority.py:189),
[kernel/commit.py:77](../../kernel/commit.py:77), and the `commit_act` RPC — **remain**, as CR-1's
enforcement machinery. Two rules govern them:

1. **They may never be stricter than CR-1.** If they were, the Rule would be decorative and the
   real decision would again be made by a constant.
2. **They move with CR-1's version by construction.** CR-1 is constitutional, so changing it
   requires the amendment protocol; the checks are its implementation and are amended in the same
   act. They cannot drift apart the way two hand-maintained lists can — which is the same failure
   mode R-6 addresses, and deserves the same treatment: **one normative source for the drift
   criterion, from which all three layers are derived or mechanically verified.**

At Genesis both are trivially satisfied: CR-1 v1 and all three checks implement rung 0.

### B.8 What must accompany CR-1 to make it meaningful

Attribution is the whole point, so:

- Every consequential Act must carry CR-1's hash in `rule_hashes`. The gate already requires
  `rule_hashes` to be non-empty and every entry registered at the declared registry cut — so this is
  enforcement that already exists, applied to a Rule that does not yet exist.
- `explain(act_hash)` (`powerfarm.action.explain`, already in the MCP surface) should surface the
  drift disposition, so "why did this commit against that cut" is answerable without reading SQL.

### B.9 Revised Genesis count

| Kind | before | after | change |
|---|---|---|---|
| `context_type` | 12 | **15** | +3 (`cut.declared`, `cut.advance`, `decision.read_set`) |
| all others | — | — | — |
| **Total** | **100** | **103** | **+3** |

CR-1 itself was already counted among the eight Rules.

### B.10 Rulings

| ID | Question | Recommendation |
|---|---|---|
| **R-17** | Add to eternity clauses: CR-1 may not be amended to permit unconditional commit-regardless | **Yes.** §2 permits the disposition generally; this universe declines it permanently. Rungs 1–3 stay amendable on evidence |
| **R-18** | A constitutional Rule may read only constitutional context types | **Yes.** Already implicitly true of every seeded key except `request.metadata`, which R-4 already excludes from Rule reads |
| **R-19** | Drift rejection produces `CommandDenied` — or should a distinct disposition exist? | **`CommandDenied` with a drift reason.** A new lifecycle type would need Genesis and buys only vocabulary. Flagged because "denied" reads oddly for a stale authorization |
| **R-20** | Is `survival_rungs_admitted` an explicit definition parameter? | **Yes.** Makes the amendment diff one line and the definition self-describing |
| **R-21** | Must projector `inputs` be mechanically verified before rung 1 is admitted? | **Yes** — under-declared projector inputs reopen TOCTOU silently. Same class as R-6 |

---

## Next

Transaction seam (D-Txn-01), per your sequence. That work is now better specified than when we last
touched it: the wrapper RPCs must carry CR-1's hash through to `rule_hashes` like any other Rule,
and the "one normative source" requirement from R-6 and §B.7 shapes how the SQL-side drift check is
generated rather than hand-written.
