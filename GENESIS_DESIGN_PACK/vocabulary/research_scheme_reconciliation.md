# Research Scheme ↔ Constitution Reconciliation

Closes R-10. Finalises the Part VIII research vocabulary against the actual source.

Design document. No code, migrations, or commits.

---

## 1. R-10 resolved: the Research Scheme *is* the Compass

Plan v2 cites "Compass §N" throughout. Every citation resolves against this document.

| Plan v2 citation | Research Scheme section | Match |
|---|---|---|
| §6 "introduce new node types later without rebuilding the database" | §6 *"The Registry can introduce new node types later without rebuilding the database."* | **exact** |
| §9 "a Campaign can return unused budget" | §9 `ResearchCampaign{budget}` / §21 same sentence verbatim | exact (sentence in §21) |
| §14 "Rules decide when a human is necessary" | §14 *"Powerfarm Rules decide when a human is necessary."* | **exact** |
| §15 continuation policies that terminate on spend | §15 `budget_ceiling`, `termination_conditions` | match |
| §16 autonomous metabolism volume | §16 "Nodes can wake each other" | match |
| §17 AdversarialEngineer, non-optional | §17 "Automated skepticism" | match |
| §21 research economy | §21 "Research economy" | **exact** |
| §22 "outputs remain candidates until admitted" | §22 *"Outputs remain candidates until admitted."* | **exact** |
| **§29.9** "a simulation never launders itself into observational evidence" | **§29 rule 9** *"Synthetic work never launders itself into observational evidence."* | **exact — and the numbering decides it** |

Nine of nine. `§29.9` meaning *section 29, rule 9* is not a coincidence available to any other document.

**Naming, resolved.** The document is the **Research Scheme**; `ResearchCompass` is its root object
(§2). Plan v2 referred to the whole document loosely as "the Compass." There is no collision — my
earlier reading 1 was correct. Recommend citing it as *Research Scheme §N* going forward, reserving
"Compass" for the node species.

---

## 2. How the two documents layer

They are not competitors, and neither is a draft of the other.

| | Constitution | Research Scheme |
|---|---|---|
| Question | what kind of institution are we, under what laws may we act | what are we trying to discover, and how |
| Status | constitutional, Genesis-born, amendment-or-fork | **ordinary governed object**, versioned |
| Changes | rarely, by protocol | as research learns |
| Confers | authority | direction — **and no authority** |

The Scheme's own §2 says the Compass *"changes rarely"* — rarely, not never. That is exactly the
right status for an ordinary versioned object, and it confirms the placement: **the Research Scheme
must not be constitutional, or research direction could only change by constitutional amendment.**

CR-8 (`compass-confers-no-authority`) and the V.9 clause stand unchanged.

---

## 3. The one real conflict: §25's canonical tables

Research Scheme §25 proposes:

> The canonical research layer can begin with essentially two tables: `research_nodes`,
> `research_edges`.

This is **superseded**, by two independent authorities:

- **The execution pack's standing rulings:** *"No canonical `research_nodes` table. Node = Object +
  admission Act + Relations."* and *"Generic `proj_nodes` / `proj_node_edges`, not research-specific
  canonical storage."* The pack (2026-08-16) is later than Scheme v0.1.
- **The normative specification, which outranks both.** §3: *"The semantic structure of Powerfarm is
  a graph. Tables, indexes, KV stores and filesystems are storage representations."* §14: State is a
  projection and is disposable. §15: *"A projection does not acquire authority merely because it is
  convenient or fast."*

**But almost nothing is lost.** The Scheme's instinct — small, two tables, `body jsonb`, large
artifacts in CAS by hash — is right. What changes is their *status*:

| Scheme §25 | Becomes |
|---|---|
| `research_nodes` (canonical) | `proj_nodes` — projection, disposable, rebuildable |
| `research_edges` (canonical) | `proj_node_edges` — projection over admitted Relations |
| `hash` as identity | unchanged — canonical identity stays in CAS |
| `body jsonb` | unchanged as projection payload |
| `research_jobs` (non-canonical) | **unchanged — the Scheme already got this exactly right** |

The Scheme's §26 boundary — *"`research_nodes` + `research_edges` = durable research knowledge;
`research_jobs` = disposable metabolism"* — survives with one correction: durable research knowledge
lives in **Objects + Acts + Relations**, and all three tables are downstream of it. Deleting every
one of them must lose nothing.

That is a strictly stronger version of the Scheme's own "beautiful boundary."

---

## 4. Where the Scheme and the Kernel already agree

Worth recording, because these needed no reconciliation at all:

- **§27 hashing** — `H("powerfarm:research-node:v1" || JCS(payload))` matches §10.1's domain
  separation and JCS requirement exactly, including a separate domain tag for edges.
- **§4 visibility** — two states, inheritance, `PRIVATE ⇒ PRIVATE` for children, never flip,
  publication as a new node with `projects_as`. Identical to the standing publication ruling and to
  Phase 8's `projects_as` lineage requirement.
- **§26 runtime/canonical boundary** — matches §14's disposable-State model.
- **§22 dream cycle** — *"Outputs remain candidates until admitted"* is precisely the candidate/
  admission membrane.
- **§28 north as graph reachability** — no denormalised `compass_hash` in every node; semantic truth
  in the graph, cache as projection. This is §3 and §14 applied correctly, and it is a better design
  than the alternative.

**One naming nit.** §27's canonical payload has `created_at`. §10.3 requires the Kernel to name
claimed time `claimed_when` precisely because *"a bare `when` invites reading it as causal order or
as provable knowledge time."* `created_at` invites the same misreading. Recommend `claimed_when` for
consistency (R-13).

---

## 5. Species and relations — corrected to Scheme names

My earlier pass proposed `Campaign`, `Experiment`, `Question`, `Method`. **The Scheme already names
them**, and its names win.

### 5.1 Node species — Research Scheme §6 (16)

```
ResearchScheme      ResearchCompass     ResearchFrontier
ResearchQuestion    Hypothesis          ResearchCampaign
ResearchMethod      Experiment          Culture
TrajectorySet       Finding             Counterexample
ResearchDebt        Tension             PublicProjection
ResearchAsset
```

Corrections to my earlier draft: `ResearchQuestion` not `Question`; `ResearchCampaign` not
`Campaign`; `ResearchMethod` not `Method`. And four species I had not accounted for —
`TrajectorySet`, `Counterexample`, `PublicProjection`, `ResearchAsset` — plus `ResearchScheme`
itself as the root species.

`Counterexample` as a distinct species (rather than a Finding subtype) is a deliberate epistemic
choice and worth keeping: §17 pairs every productive operator with an antagonist, and a
first-class Counterexample is what makes `breaks` a real relation rather than a note.

**R-8 answered by the source:** `Culture` stays — §8 gives it a substantive role
(`Culture_hypothesis`, `Culture_method`, `Culture_research-program`).

### 5.2 Relations — Research Scheme §25 (17)

```
advances   tests        supports      contradicts   refines
supersedes opens        closes        depends_on    derived_from
uses_method uses_machinery calibrated_by projects_as reproduces
damages    revives
```

Already seeded: `supports`, `contradicts`, `derived_from`. New from the Scheme: 14, including
`supersedes` (which I had proposed independently) and `projects_as` (required by Phase 8's
publication lineage).

Also referenced in the Scheme body but not in its §25 list: `competes_with` (§7), `breaks` (§7),
`qualified_by` (§11). Plan v2 lists `competes_with` and `qualified_by` among the deferred set. Worth
adding to the catalogue (R-14).

### 5.3 Timing — unchanged

All of it remains **ordinary, registered post-Genesis**, per Plan v2's *"registering vocabulary
nobody uses is how an ontology becomes furniture"* and per §6's own promise that the Registry can
introduce node types later. The Scheme's existence does not move any of it into Genesis.

---

## 6. Scheme §29's ten rules, mapped

The Scheme calls these "minimal constitutional rules." Against the actual Constitution, they
partition three ways.

| # | Rule | Status |
|---|---|---|
| 1 | admitted research objects immutable and hashed | **already constitutional** — SL-1, SL-2 |
| 2 | every meaningful experiment has a path to a Research Compass | **ordinary** research Rule |
| 3 | the Compass is PUBLIC | **ordinary** — a property of the object, not of the universe |
| 4 | Frontiers are PUBLIC or PRIVATE | **ordinary** — visibility model |
| 5 | PRIVATE ancestry cannot silently produce PUBLIC descendants | **candidate constitutional** — see §7 |
| 6 | publication is a new projection node, never mutation | **candidate constitutional** — see §7 |
| 7 | automation default where Rules/authority/budgets permit | **ordinary** policy |
| 8 | LLM activity producing research knowledge is trajectory provenance | **ordinary** |
| 9 | **synthetic work never launders itself into observational evidence** | **should be constitutional** — see §7 |
| 10 | Findings modify future interpretation, never rewrite the past | **already constitutional** — SL-1 |

Rules 1 and 10 are already covered; 2, 3, 4, 7, 8 are ordinary. Rules 5, 6 and 9 are the ones that
need a decision, and they share a single underlying problem.

---

## 7. A finding: the provenance relations are not constitutional, and probably should be

Scheme §29.9 and spec §23 make the same demand:

> §23: *"Simulation may generate history objects. It may not fabricate prior occurrence in
> reality."* — `StructuralSimilarity ≠ HistoricalOccurrence`

That invariant is carried entirely by **which relation marks the provenance**. And in the current
seed:

```
('relation_type', 'derived_from',   1, false, ...)
('relation_type', 'simulated_from', 1, false, ...)
('relation_type', 'crafted_from',   1, false, ...)
('relation_type', 'forked_from',    1, true,  ...)   ← the only one marked constitutional
```

`simulated_from` and `crafted_from` are **`constitutional = false`**. Post-Genesis, ordinary
governance could redefine or retire them. The relation that marks synthetic origin would be
amendable by the same authority that runs the research.

That is the laundering path §29.9 exists to close — not through fraud, but through vocabulary drift:
redefine `simulated_from`, and prior synthetic ancestry silently changes meaning while every
`rule_hashes` reference still validates.

The same argument applies to rules 5 and 6: PRIVATE→PUBLIC inheritance and publication-as-new-node
are enforced by `projects_as` and lineage semantics. If those relation definitions are ordinary, the
disclosure guarantee is ordinary too.

**Recommendation (R-15): mark the provenance-and-disclosure relations constitutional at Genesis** —
`derived_from`, `simulated_from`, `crafted_from`, `projects_as`, plus `forked_from` which already is.
Their *meaning* becomes unamendable; new research relations remain freely registrable. This costs
four definitions and closes the epistemic-integrity hole that Scheme §29.9, spec §23, and the
publication ruling all depend on.

Note this does **not** contradict §5.3. These are not research vocabulary — they are provenance
vocabulary that research happens to use. `advances`, `tests`, `refines` and the rest stay ordinary.

---

## 8. Revised Part VIII delta

| Kind | prior | now | change |
|---|---|---|---|
| `rule` | 8 | 8 | — (CR-8 stands) |
| `relation_type` | 18 | 18 | — count unchanged; **4 change `constitutional` false→true** (R-15) |
| all others | — | — | — |
| **Total** | **100** | **100** | **0 new definitions** |

The Research Scheme adds **zero** definitions to Genesis and changes four flags. An entire research
civilisation — 16 species, 17+ relations, campaigns, enzymes, dream cycles, a research economy —
composes on top of a constitution it does not enlarge.

Registered post-Genesis as ordinary: 16 node species, ~14 new relations, the founding
`ResearchCompass` object and its seven initial Frontiers (§30), the
`research.current_experiments` projector, `proj_nodes`/`proj_node_edges`, and the research
lifecycle Acts.

---

## 9. Rulings

| ID | Question | Recommendation |
|---|---|---|
| **R-10** | Compass identity | **Resolved** — the Research Scheme is it. Cite as *Research Scheme §N* |
| **R-13** | `created_at` in the canonical node payload | Rename **`claimed_when`** per §10.3 |
| **R-14** | `competes_with`, `breaks`, `qualified_by` — in the catalogue? | **Yes**, ordinary, deferred until used |
| **R-15** | Make `derived_from`, `simulated_from`, `crafted_from`, `projects_as` constitutional | **Yes** — §7 above. The single highest-value change in this pass |
| **R-16** | Scheme §25 canonical tables → projections | **Yes**, superseded by spec §3/§14 and the standing ruling. Schema survives as `proj_nodes`/`proj_node_edges` |
| **R-8** | `Culture` | **Keep** — answered by Scheme §8 |

Still open from earlier: R-1, R-4, R-5, R-7, R-9, R-11, R-12.

---

## 10. Where this leaves us

Part VIII is **enumeration-complete**. R-10 is closed, the species and relation names come from the
source rather than from me, and the only substantive change the Research Scheme forces on Genesis is
R-15 — four constitutional flags, protecting the invariant the Scheme itself calls rule 9.

The Scheme's §30 initial graph — seven Frontiers under the Compass, with the Golden Bridge
Capability Atlas beneath the private machinery branch — is exactly the "something real to eat on day
one" that makes the institution non-hypothetical. It is also entirely ordinary: registrable the day
after Genesis, under the Director mandate, without amendment.

Next per your sequence: **`declared-decision-cut`**, then the transaction seam.
