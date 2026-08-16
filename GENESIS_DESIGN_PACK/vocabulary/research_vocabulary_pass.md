# Part VIII — Research Institution Pass

Second pass over the vocabulary enumeration, incorporating the Research Compass / Frontiers /
Campaigns / Experiments layer. Supersedes §§9–11 of Part VIII 0.1; §§1–8 stand.

Design document. No code, migrations, or commits.

---

## 1. The vocabulary already exists — do not re-coin it

You asked me to use existing names. Nearly all of them exist, and the project has already ruled on
how they enter.

**`00_Context_and_North.md:148-160` contains your loop almost verbatim:**

```
Compass / Frontier
 -> Question / Hypotheses
 -> Campaign / Experiment
 -> Engine
 -> Golden Bridge + tools/world
 -> Trajectories
 -> Adversarial review / reproduction
 -> Findings / Debt / Tensions
 -> new Nodes and next work
```

**`01_Powerfarm_Platform_Plan_v2.md:299-301` names the species:**

> **Node species are not registry kinds.** `ResearchFrontier`, `Hypothesis`, `Finding`,
> `ResearchDebt`, `Tension`, `Culture` are the `node_type` field inside a node payload, validated
> against a **species schema that is itself a registered object**.

So the canonical existing names are **`ResearchFrontier`, `Hypothesis`, `Finding`, `ResearchDebt`,
`Tension`, `Culture`**. Note `Culture` — an existing species you did not list, which you may or may
not still want. `Campaign`, `Experiment`, `Question` and `Method` appear in the loop but have no
declared species name yet; they should follow the same naming style.

**And Plan v2 already ruled on timing**, in the passage immediately above (`:295-298`), about
research relations:

> `uses_machinery`, `calibrated_by`, `reproduces`, `damages`, `revives`, `competes_with`,
> `qualified_by` — enters later, at runtime, when something actually needs it. **Registering
> vocabulary nobody uses is how an ontology becomes furniture.**

That sentence answers most of your question directly.

---

## 2. Answer: almost none of it belongs in the initial Registry

**Recommendation: the initial Registry should contain canonical schemas for none of Research
Compass, ResearchFrontier, Campaign, Experiment, Question, Hypothesis, Finding, Tension,
ResearchDebt, or Method.**

Four independent lines of evidence converge:

1. **The normative spec contains none of it.** Zero occurrences of Frontier, Finding, Campaign,
   Experiment, Hypothesis, Tension, Method or Compass in `Powerfarm System Specification v3.md`.
   Only `Trajectory` (8) and `Fold` (6) are spec-level concepts. The research layer is not
   constitutional in the specification's own judgment.
2. **Plan v2 explicitly defers it** — vocabulary enters at runtime when something needs it.
3. **Your own placement instinct** — Draft 0.2 should carry the constitutional *interface*, not
   today's research agenda.
4. **The size test from Part VIII 0.1 §11.** If research vocabulary needs Genesis, the boundary was
   drawn wrong. Species are registrable through `RegisterDefinition` under the Director mandate,
   with no amendment and no deploy — that is precisely the capability Phase 0b exists to deliver.

Seeding them at Genesis would also freeze them: post-Genesis, a constitutional definition changes
only by amendment or fork. **A research vocabulary that cannot evolve without a constitutional
amendment is the opposite of a research institution.**

### What the research layer *does* need from Genesis

Exactly one new constitutional Rule, plus one relation already proposed in 0.1.

**CR-8 `compass-confers-no-authority`** — constitutional.

Your invariant, made enforceable: *the Compass directs research but confers no authority by itself.*

Expressed as a Rule over `RegisterDefinition` where `kind=rule`: **deny registration of any Rule
whose declared `context_keys` include a Compass-derived key.** Since §2.1 already requires every
Rule to statically declare the context keys it reads, this is decidable at registration time and
needs no runtime evaluation.

This is the right shape because the danger is not a Compass that misbehaves — it is a *Rule* that
quietly treats a research priority as authorization. Blocking it at registration means the failure
cannot be introduced at all, rather than being caught per-decision.

It must be constitutional. If CR-8 were ordinary, a later Rule could repeal it and then read Compass
priorities as grants.

**`supersedes`** — already proposed in 0.1 §6.2, and now doubly justified: `ResearchCompass.v1 →
supersedes → ResearchCompass.v2` is exactly the versioning you described, and §12 names the relation
while the current seed omits it.

---

## 3. Constitutional text for Draft 0.2

Proposed clause, to sit in Part V after the mandate (research is something the institution *does*,
under the Director's mandate):

> **V.9 Research.** Powerfarm maintains a governed, versioned Research Compass expressing its
> current research direction. Research Frontiers, Campaigns, Experiments, Findings and related
> research objects may advance under that Compass subject to Powerfarm authority, evidence,
> disclosure and accountability requirements. **The Research Compass directs research but does not
> itself confer authority** (CR-8): no research priority authorizes spending, an external effect, or
> an experiment. Those require mandate, Rules and Acts as any other governed change does.
>
> The Compass, its Frontiers and their vocabulary are ordinary governed objects. Their content is
> not constitutional and must remain amendable without fork.

That is the whole constitutional footprint. Everything else is ordinary.

---

## 4. Vocabulary catalogue — ordinary, registered post-Genesis

Recorded here so the enumeration is complete and the names are fixed, **not** because any of it is
Genesis-born.

### 4.1 Node species (`kind=node_species`)

| Species | Status | Meaning |
|---|---|---|
| `ResearchFrontier` | **existing name** | a bounded territory Powerfarm recognises as an important unresolved frontier — not a subject tag |
| `Hypothesis` | **existing name** | |
| `Finding` | **existing name** | |
| `ResearchDebt` | **existing name** | known deficit the institution owes itself |
| `Tension` | **existing name** | recognised contradiction between admitted results |
| `Culture` | **existing name** | present in Plan v2; unlisted by you — see R-8 |
| `ResearchCompass` | **new** | the governed, versioned direction-setting object |
| `Campaign` | **new** | coordinated attempt to advance part of a Frontier: objective, resources, horizon |
| `Experiment` | **new** | an individual falsifiable or executable research intervention |
| `Question` | **new** | in the loop, no species name yet |
| `Method` | **new** | Plan v2: "Research methods are Nodes, not Kernel code" |

**Campaign and Experiment stay distinct**, as you specified. A Frontier is an enduring unknown; a
Campaign is a bounded coordinated attempt; an Experiment is a single intervention. The distinction
earns its keep the moment agents generate work autonomously — without it, "what is Powerfarm doing"
collapses into an undifferentiated queue.

### 4.2 Visibility

**No `PublicResearchFrontier` / `PrivateResearchFrontier` species.** A Frontier is PRIVATE or PUBLIC
under the existing visibility model, and a private Frontier produces a **new public projection**
without mutating or exposing its private ancestry — which is the standing ruling ("PUBLIC publication
creates a new projection hash. Never flip PRIVATE to PUBLIC in place") applied unchanged.

This is what serves confidential client science, embargoed partnerships, unreleased technology,
sensitive datasets and competitive work — while public Frontiers become Powerfarm's actual
scientific presence.

### 4.3 Research relations

Existing seeded relations already cover much of the ecology: `supports`, `contradicts`,
`derived_from`, `matched_to`, `crafted_from`, `simulated_from`.

Deferred per Plan v2 `:295-298`, to be registered when something needs them: `opens`, `advances`,
`refines`, `uses_machinery`, `calibrated_by`, `reproduces`, `damages`, `revives`, `competes_with`,
`qualified_by`.

`Tension` is interesting: it exists both as a **node species** (a recognised institutional
contradiction, with its own lifecycle) and as the **`contradicts` relation** (a structural link
between two objects). Both are legitimate and they are not duplicates — the relation states that A
contradicts B; the species states that Powerfarm has recognised this contradiction as something it
owes itself resolution on. Worth keeping distinct deliberately (R-9).

### 4.4 Research lifecycle Acts

**None needed beyond what exists.** Experiments, Campaigns and Frontiers are Nodes; Nodes are
admitted by `AdmitBatch`/`BatchAdmitted` and connected by admitted Relations. Their state
transitions are ordinary Acts registered when the lifecycle is designed.

Resist minting `ExperimentStarted`, `ExperimentCompleted`, `FrontierOpened` at Genesis. Each would
freeze a lifecycle nobody has run yet.

---

## 5. "Current Experiments" is a projection — confirmed

Your instinct matches the architecture, and the evidence supports it without qualification.

- §14: *State is a projection… Materialized State may exist for performance… but it is disposable.*
- §15: *A projection does not acquire authority merely because it is convenient or fast.*
- The pack's standing ruling against canonical research tables (no `research_nodes`), which a
  `CurrentExperiment` object would reintroduce in miniature.

So: **`Experiment` is canonical; "current" is derived.** A `current=true` field would be exactly the
mutable authoritative state the whole design refuses — and it would be unreconstructible, since you
could never ask *what was running at cut C* after the flag moved.

New projector, ordinary: **`research.current_experiments`**, deriving at a cut:

```
RUNNING · AWAITING REVIEW · SCHEDULED · BLOCKED · COMPLETED RECENTLY
```

surfacing Experiment, Frontier, Campaign, responsible Agent or human, start, budget envelope,
current phase, latest observation, review status — every field derived from admitted Acts.

History records transitions; the projection reports what is current. Delete it, rebuild it, get the
same answer (§14's determinism requirement).

---

## 6. A naming collision to resolve

**"Compass" is already taken in this project, and it refers to a document I do not have.**

`01_Powerfarm_Platform_Plan_v2.md` cites it by section throughout — Compass §6, §9, §14, §15, §16,
§17, §21, §22, §29.9 — quoting things like *"introduce new node types later without rebuilding the
database"* (§6), *"a Campaign can return unused budget"* (§9), *"Rules decide when a human is
necessary"* (§14), and *"a simulation never launders itself into observational evidence"* (§29.9).

So a Powerfarm Compass document with at least 29 sections exists and was normative for Plan v2. It
is **not** in the execution pack — not in `authoritative/`, not in `background/` — and not in this
repository.

Two readings, and I cannot distinguish them from the supplied material:

1. **Same artifact.** The existing Compass *is* the direction-setting document you are describing,
   and "Research Compass" is its governed, versioned form. Then this pass is formalising something
   that already exists in prose, and its §§6/9/14/21/22 content should be reconciled with the
   Constitution rather than re-derived.
2. **Different artifacts.** The existing Compass is a *design* document (closer to the spec), and
   Research Compass is a new *institutional* object about research direction. Then the name collides
   and one should be renamed.

**This is a halt for this pass.** If reading 1 holds, drafting a Research Compass without reading
the existing one risks contradicting a document Plan v2 treats as normative — including on budget
semantics (§9, §21) and simulation discipline (§29.9), both of which touch the Constitution.

Requested: the Compass document, or confirmation that it is superseded.

---

## 7. Revised Part VIII delta

Change from 0.1: **+1 constitutional Rule. Nothing else.**

| Kind | 0.1 Genesis | 0.2 Genesis | Change |
|---|---|---|---|
| `rule` | 7 | **8** | +CR-8 `compass-confers-no-authority` |
| `command_type` | 18 | 18 | — |
| `act_type` | 34 | 34 | — |
| `relation_type` | 18 | 18 | — (`supersedes` already included) |
| `context_type` | 12 | 12 | — |
| `office` / `mandate` / `projector` | 1 / 2 / 7 | 1 / 2 / 7 | — |
| **Total** | **99** | **100** | **+1** |

The research institution added **one** definition to Genesis. That is the strongest available
evidence that the constitutional boundary is drawn in the right place: an entire institutional layer
composed on top without enlarging the constitution.

Registered post-Genesis as ordinary vocabulary: 11 node species, ~10 research relations, the
`research.current_experiments` projector, the founding Research Compass object, and every research
lifecycle Act — all under the Director mandate, no amendment, no deploy.

---

## 8. Rulings needed

| ID | Question | Recommendation |
|---|---|---|
| **R-8** | Keep `Culture` as a node species? | Your call — it exists in Plan v2 and you did not list it. Keeping it costs nothing (ordinary, registered when needed) |
| **R-9** | `Tension` as both species and `contradicts` relation? | **Keep both.** The relation is structural; the species is institutional recognition. Not duplicates |
| **R-10** | Does the founding Research Compass reconcile with the existing Compass document? | **Blocked** — §6 above |
| **R-11** | Is `ResearchCompass` a node species, or its own registry kind? | **Node species.** It is a governed object in the graph, not a category of definition. Keeps the kind list short |
| **R-12** | Should CR-8 also block *ordinary* Rules reading Compass context, or only constitutional ones? | **All Rules.** A priority must never authorize anything, whoever registered the Rule |

Carried from 0.1 and still open: R-1 (drop `SubmitCommand`), R-4 (`request.metadata` open shape),
R-5 (no `effect_kind` at Genesis), R-7 (`authority.grants` caller-refused).

---

## 9. Where this leaves the sequence

Part VIII is enumeration-complete **except** for R-10. The Compass question does not block the
Constitution — CR-8 and the V.9 clause stand regardless of which reading is correct, because both
readings agree the Compass confers no authority.

So: **Part VIII can freeze on R-8/R-9/R-11/R-12, with R-10 tracked against the founding Compass
artifact rather than against Genesis.** Then `declared-decision-cut`, then the transaction seam.

The four layers you named, now with their homes:

| Layer | Question | Where it lives |
|---|---|---|
| Constitution | what kind of institution are we, under what laws may we act | Genesis, immutable but for amendment |
| Research Compass | what are we trying to discover, and why does it matter | ordinary governed object, versioned |
| Research Frontiers | where are the important boundaries of what we do not know | ordinary Nodes, PUBLIC or PRIVATE |
| Current Experiments | what are we actually doing about those unknowns right now | **projection over admitted history at a cut** |

Only the first is constitutional. The last is not even an object.
