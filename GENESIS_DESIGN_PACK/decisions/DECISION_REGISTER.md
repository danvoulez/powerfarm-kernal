# Decision Register

**This file is the single source of truth for what every decision ID means.**

Every other document in this pack references IDs and must not restate their content. If a
specification and this register disagree, this register wins and the specification is stale.

Status vocabulary:

| Status | Meaning |
|---|---|
| **FROZEN** | ratified; changing it after Genesis requires amendment or fork |
| **ACCEPTED** | ruled and stable; not yet Genesis-bound |
| **RECOMMENDED** | proposed with reasoning; awaiting a ruling |
| **OPEN** | genuinely undecided; see `OPEN_DECISIONS.md` |
| **SUPERSEDED** | replaced; retained so the ID never silently changes meaning |
| **RESERVED** | never assigned; do not reuse |

Last updated 2026-08-16 against commit `b3de7c7`.

---

## Constitutional — Genesis

| ID | Decision | Status |
|---|---|---|
| **D-Genesis-01** | Every name declared a *constitutional Rule* must resolve to a content-addressed `kind=rule` definition born at Genesis and citable in `rule_hashes`. Structural laws are separately enumerated, bound at Genesis, and enforced by construction. Neither list may contain a member of the other. *(Refined from the original form, which required all four `genesis.yaml` names to become Rules; two of them — `append-only-acts`, `reference-by-hash` — are structural laws, not decisions about Commands.)* | ACCEPTED |
| **D-Genesis-02** | Constitutional registration seals at `GenesisClosed`. `constitutional=false` → ordinary governed path; `constitutional=true` pre-Genesis → ceremony only; post-Genesis → Genesis-born amendment protocol only, **otherwise reject, including Root**. Contradicts the execution pack's Phase 0b. | ACCEPTED |
| **D-Genesis-03** | `genesis.yaml` must cryptographically bind the **canonical content** of every §16 item — specifically the initial Registry definitions and Root Identity + initial keys — not merely their names. | ACCEPTED |
| **D-Genesis-04** | Resolve `amendment-or-fork`: give it real content-addressed substance at Genesis, or consciously ratify a fork-only universe. No third option exists after `GenesisClosed`. | **OPEN** |
| **D-Genesis-05** | Genesis binds a constitutional Rule constraining Root's post-Genesis powers to: registering constitutional definitions at Genesis, creating initial Identities, and installing initial office holders. | ACCEPTED |

## Constitutional — Authority

| ID | Decision | Status |
|---|---|---|
| **D-Authority-01** | Root is a bootstrap membrane, not an operating role. Every Director power must trace to a mandate definition hash and an unrevoked grant Act at the declared cut. Root is never a fallback path for a Director power; no Director power may grant Root authority. | ACCEPTED |
| **D-Authority-02** | The Director office, its mandate, the appointment vocabulary and the initial appointment are **ordinary** governed objects, not constitutional ones — except the mandate *boundary*, which is constitutional. | ACCEPTED |
| **D-Authority-03** | Authority state is Acts + admitted Relations projected into `active_grants`. No canonical authority table. | ACCEPTED |
| **D-Authority-04** | Delegated grants must name a strict subset of the delegator's mandate powers, verified by Rule against the delegator's own grant at the declared cut. | ACCEPTED |

## Constitutional — Director

| ID | Decision | Status |
|---|---|---|
| **D-Director-01** | No exercise of an office's authority may enlarge that office's powers, extend delegation depth beyond the declared maximum, or appoint the reviewers of its own actions. | ACCEPTED |
| **D-Director-02** | Root and Director hold **disjoint** mandates, not nested ones. Root constitutes; Director operates. Root's mandate is exhausted at `GenesisClosed`. After Genesis, Root identity resolves from admitted history, never from configuration. | ACCEPTED |
| **D-Director-03** | Recovery from total loss of Director keys: Genesis-born constitutional quorum *(recommended)* / dormant Root / fork-only. | **OPEN** |
| **D-Director-04** | `max_holders`: 2 *(recommended, so handover never passes through zero)* / 1 / N. `min_holders = 1`; zero is forbidden. | **OPEN** |
| **D-Director-05** | Director's role in constitutional amendment: propose-only *(recommended)* / one vote among N / excluded. | **OPEN** |
| **D-Director-06** | Mandate boundary as a single constitutional object *(recommended)* / decomposed per power class. | **OPEN** |
| **D-Director-07** | Delegation depth default: 0 *(recommended — delegates may not re-delegate)* / 1 with expiry / parameterised. | **OPEN** |
| **D-Director-08** | Is Dan's Identity also the Root Identity? Separate Identities with separately-held keys *(recommended)*. **If shared, Root/Director disjointness is a promise rather than a structure.** | **OPEN** |

## Constitution draft markers — the `A-*` crosswalk

The constitution draft carries inline `[A-n]` markers at the points its text depends on an unsettled
choice. Seven of them are the same decisions as `D-Director-*` under a different name; five have no
twin. **For those five, the `A-` form is canonical** — they are registered here so no ID in this
pack means two things.

| Marker | Same as | Decision | Status |
|---|---|---|---|
| `A-1` | D-Director-03 | recovery from total Director key loss | **OPEN** |
| `A-2` | D-Director-04 | `max_holders = 2`, `min_holders = 1` | **OPEN** |
| `A-3` | D-Director-05 | Director may propose amendments, never enact alone | **OPEN** |
| `A-4` | D-Director-06 | mandate boundary is a single constitutional object | **OPEN** |
| `A-5` | D-Director-07 | delegation depth default 0 | **OPEN** |
| `A-6` | D-Director-08 | Dan's Identity is Director only; Root is separate | **OPEN** |
| `A-7` | D-Genesis-01 | structural laws and constitutional Rules separately enumerated | ACCEPTED |
| **`A-8`** | — | amendment delay 30 days; constitutional quorum 2-of-3; **and who the reviewers are**. The numbers are placeholders chosen for concreteness, not analysis | **OPEN** |
| **`A-9`** | — | the organization Identity is Genesis-born, symmetric with Root and Director — avoiding a window in which Powerfarm can act but cannot be a party | RECOMMENDED |
| **`A-10`** | — | the external-authority **interface** is constitutional; jurisdiction-specific **instances** are ordinary and deferred until incorporation and counsel exist. *(Demoted from halt to deferred instantiation — this is why Genesis may precede incorporation.)* | ACCEPTED |
| **`A-11`** | — | public commitments enter history by explicit act, never by default. Not every statement at a conference should become an institutional obligation | RECOMMENDED |
| **`A-12`** | — | counterparty-verifiable authorization proof is a disclosure-profile question (Phase 8), not a constitutional one | RECOMMENDED |

## Transaction and admission

| ID | Decision | Status |
|---|---|---|
| **D-Txn-01** | The single correct seam is a `security definer` wrapper calling `commit_act` and inserting authoritative rows in the same transaction. CAS objects may precede the gate; authoritative rows may not. A Python unit-of-work is illegal, not merely inadvisable: `powerfarm_worker` holds `select` only. | ACCEPTED |
| **R-23** | `decision.read_set` is derived and recomputable, never a stored context type or a supplied input. | FROZEN |
| **R-24** | The companion contract is declared in the `act_type` definition and resolved at the Act's declared registry cut. Gate enforces presence, cardinality and writer routing — a lookup, not a policy engine. | FROZEN |
| **R-25** | Revoke bare `commit_act`; fold it into `admit`. One door, enforced by grants rather than discipline. | FROZEN |
| **R-26** | Ratify the four canonical preimage changes as one pre-Genesis item. See `specifications/canonical_preimages.md`. | FROZEN |
| **R-27** | The Ledger gains an explicit admission scope pinning one connection for the sequence. | FROZEN |

## PF-13 / decision validity

| ID | Decision | Status |
|---|---|---|
| **D-PF13-01** | Materialize `declared-decision-cut` as a registered constitutional Rule. The three hardcoded checks remain as its enforcement machinery; what changes is that history records which Rule decided. | ACCEPTED |
| **D-PF13-02** | Do not weaken TOCTOU. Causal/context-scoped reauthorization is co-designed with the Rule engine's static read-set analysis, never adopted as a shortcut. | ACCEPTED |
| **R-17** | CR-1 may not be amended to permit unconditional commit-regardless (survival rung 4). Rungs 1–3 remain amendable on evidence. | RECOMMENDED |
| **R-19** | Drift rejection produces `CommandDenied` with a drift reason rather than a new lifecycle type. | RECOMMENDED |
| **R-20** | `survival_rungs_admitted` is an explicit definition parameter, so an amendment diff shows the policy change on one line. | RECOMMENDED |
| **R-21** | Causal relevance requires **mechanically enforced** dependency declarations. No Rule may treat an advanced cut as irrelevant unless every history-sensitive producer has an enforced dependency set. Unknown dependency means reauthorization. Capability-style restriction preferred over instrumentation. | ACCEPTED |
| **R-22** | Authorization disposition and decision-validity disposition are **distinct typed domains**. `declared-decision-cut` produces the latter; it must never be smuggled through `allow`/`deny`/`require_review`. | ACCEPTED |

## Vocabulary and semantics

| ID | Decision | Status |
|---|---|---|
| **R-1** | Drop `SubmitCommand` — a protocol verb, not a governed command type. | RECOMMENDED |
| **R-2** | The final external-effect phase Act type is `ExternalFactClaimed`. Preserves PF-24's phase taxonomy while refusing to let Powerfarm assert external legal validity. | ACCEPTED |
| **R-3** | `root-mandate` replaces `genesis.root_authority` in the initial seed vocabulary. **This is initial-vocabulary correction, not supersession** — nothing has been admitted, so there is nothing to supersede. `supersedes` retains its strict historical meaning for after Genesis. | ACCEPTED |
| **R-4** | `request.metadata` may keep an open shape but must never be readable by an authorization Rule. | RECOMMENDED |
| **R-5** | No `effect_kind` definitions at Genesis; seeding them freezes what Powerfarm can commit to. | RECOMMENDED |
| **R-6** | One normative lifecycle vocabulary source, from which the Registry entries, runtime validation, the partial-index constraint and tests are derived or mechanically verified. The invariant is that one representation cannot evolve without forcing the others. | ACCEPTED |
| **R-7** | Caller-supplied `authority.grants` is categorically rejected. Grants are derived authority context, never a user assertion. | ACCEPTED |
| **R-8** | `Culture` is retained as a node species (Research Scheme §8 gives it a substantive role). | ACCEPTED |
| **R-9** | `Tension` exists both as a node species and as the `contradicts` relation. Not duplicates: the relation is structural, the species is institutional recognition. | RECOMMENDED |
| **R-10** | The Powerfarm Research Scheme **is** the document Plan v2 cites as "Compass". `ResearchCompass` is its root object. No parallel ontology. | RESOLVED |
| **R-11** | `ResearchCompass` is a node species, not its own registry kind. | RECOMMENDED |
| **R-12** | `compass-confers-no-authority` (CR-8) applies to **all** Rules, not only constitutional ones. | RECOMMENDED |
| **R-13** | `claimed_when` where the field is a hashed content assertion; `created_at`/`materialized_at` where it is an operational projection timestamp, never causal evidence. Three clocks, not one rename. | ACCEPTED |
| **R-14** | `competes_with`, `breaks`, `qualified_by` join the relation catalogue; ordinary, deferred until used. | RECOMMENDED |
| **R-15** | *(constitutionalize four provenance relation names)* | **SUPERSEDED by R-15R** |
| **R-15R** | **Synthetic provenance is constitutional; provenance vocabulary is not.** Relations bind their exact registered type definition by content hash; definitions declare lineage/provenance semantics; synthetic and crafted ancestry is preserved through admitted lineage; and no synthetic history may be represented as prior external observation by changing vocabulary, projection, approval, or relation version. §11.1 is the harder boundary: synthetic material may inform reasoning but cannot manufacture `ObservationAdmitted`. | ACCEPTED |
| **R-16** | Research Scheme §25's canonical `research_nodes`/`research_edges` become **projections** (`proj_nodes`/`proj_node_edges`). Superseded by spec §3 and §14. Its §26 runtime boundary was already correct. | ACCEPTED |
| **R-18** | *(constitutional Rules may read only constitutional context types)* | **SUPERSEDED by R-18R** |
| **R-18R** | **Rule context semantics are hash-pinned.** Every context key a Rule reads is bound at the Rule's birth to the exact `context_type` definition hash and schema it was type-checked against; the admitted Context records that hash. Later context-type versions cannot reinterpret a historical Rule evaluation. Constitutional Rules require immutable dependency *meaning*, not `constitutional=true` on every vocabulary item. | ACCEPTED |

## Engine and execution

| ID | Decision | Status |
|---|---|---|
| **R-28** | — | **RESERVED, never assigned. Do not reuse.** |
| **R-29** | ADK evidence capture is **copy-by-content, never reference-by-runtime-coordinate**. Rewind or deletion in an execution engine may change the engine's live view but may never retroactively alter evidence already admitted by Powerfarm. | ACCEPTED |
| **R-30** | External-effect retry semantics. An engine may provide at-least-once unit execution. Powerfarm provides stable logical effect identity, **durable pre-dispatch intent established before dispatch begins**, idempotency where the external protocol supports it, and reconciliation rather than blind retry where outcome is ambiguous. Powerfarm never *knowingly originates* a second logical effect. | ACCEPTED |
| **R-31** | Engine-side rewind/undo constructs are never mirrored into Powerfarm history. | ACCEPTED |
| **R-32** | Constitutional enforcement never lives in an engine plugin or callback. Plugins are sensors; the governed capability wrapper is the gate. | ACCEPTED |
| **R-33** | An engine confirmation flag is never authorization. Authority is the admitted review chain, verified by the governed capability every time. | ACCEPTED |
| **R-34** | Runtime identifiers may be canonically preserved as claims/correlation data **inside** an evidence object, which then receives its own Powerfarm content hash. They never substitute for Powerfarm content identity. | ACCEPTED |
| **R-35** | Engine registries are execution discovery, never the Powerfarm Registry. | ACCEPTED |
| **R-36** | Three falsifiable compatibility tests: (1) a Powerfarm-governed ADK App remains deployable on Google Agent Engine without forking ADK; (2) a normal ADK App that does not use Powerfarm remains a normal ADK App; (3) Powerfarm history remains valid when the corresponding ADK Session, Events or Artifacts are rewound or deleted after evidence capture. | ACCEPTED |
| **R-37** | The Engine **Protocol** (stable architectural interface) and an engine **capability profile** (ordinary Registry object) are separate layers, so the first engine cannot silently define the generic interface. | ACCEPTED |

## Base strengthening — completed

| ID | Work | Status |
|---|---|---|
| **B1** | PF-21 proved at both the Kernel boundary (`conformance/test_pf21.py`, 8 tests) and the real admission boundary (`conformance/sql/pf21_admission.sql`, 7 assertions through `commit_act`). | **DONE** |
| **B2** | `conformance/LAW_TEST_MAP.toml` + `conformance/test_law_coverage.py`: typed statuses, checked against the specification, `ENFORCED_UNPROVEN` set frozen against drift in both directions. | **DONE** |
| **B3** | `conformance/sql/ledger_invariants.sql`: 12 assertions that attempt forbidden mutations and require the database to refuse. Closes PF-07, PF-10, PF-12. | **DONE** |
| **B4** | CI mypy widened to `ledger service protocol`; shellcheck glob widened to `.claude/scene/*.sh`. Both were already clean. | **DONE** |
| **B5** | The nine-law bundled test split into one test per law. | **DONE** |
