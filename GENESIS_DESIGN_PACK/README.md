# Genesis Design Pack

The complete pre-Genesis design of Powerfarm as an institution: what the universe will be, what
Genesis must bind, and what remains genuinely undecided.

Assembled 2026-08-16 against commit `b3de7c7`. Genesis has never been performed. **Nothing in this
pack starts it.**

The symmetry is worth noticing. This phase began with someone handing us a Fresh Agent Execution
Pack for the *platform*. It ends by producing the equivalent for the *constitution*.

---

## Start here

→ **[`handoff/START_HERE.md`](handoff/START_HERE.md)** — halt conditions, the ordered work list, and
what is deliberately not closed. One document to execute from.

Two rules govern everything else:

1. **The register wins.** If a specification disagrees with
   [`decisions/DECISION_REGISTER.md`](decisions/DECISION_REGISTER.md), the register is right and the
   specification is stale. IDs scattered across seven documents drift — the `R-28` collision proved
   the failure mode, and `R-28` is now permanently reserved and never assigned.
2. **Design documents describe the design, not the code.** For what the implementation actually does
   today, [`conformance/CURRENT_BASELINE.md`](conformance/CURRENT_BASELINE.md) — recomputed, and it
   says plainly where the base is thin.

---

## The pack

| | |
|---|---|
| **handoff/** | |
| [`START_HERE.md`](handoff/START_HERE.md) | halt conditions, ordered work list, gotchas |
| **decisions/** | |
| [`DECISION_REGISTER.md`](decisions/DECISION_REGISTER.md) | every ID and its status — the single source |
| [`OPEN_DECISIONS.md`](decisions/OPEN_DECISIONS.md) | what is undecided, why, and what it blocks |
| **constitution/** | |
| [`01_Genesis_Constitution_0.2.md`](constitution/01_Genesis_Constitution_0.2.md) | Parts I–XII: universe identity, structural laws, constitutional Rules, Root, the Director office and Powerfarm's presence in the world, succession, amendment, initial Registry, initial holders |
| **specifications/** | |
| [`canonical_preimages.md`](specifications/canonical_preimages.md) | the frozen four — free before `GenesisClosed`, impossible after |
| [`admission_architecture.md`](specifications/admission_architecture.md) | the transaction seam and the declarative companion contract |
| [`cr1_declared_decision_cut.md`](specifications/cr1_declared_decision_cut.md) | PF-13 as a registered constitutional Rule, with the survival ladder |
| [`director_institution.md`](specifications/director_institution.md) | the office: powers, mandate, appointment, succession, capture |
| [`external_representation.md`](specifications/external_representation.md) | how Powerfarm becomes a party to things in the world |
| [`engine_protocol.md`](specifications/engine_protocol.md) | P-1…P-10, engine-neutral, plus capability profiles |
| [`adk_2_7_absorption.md`](specifications/adk_2_7_absorption.md) | what Google ADK 2.7 already decides, and where Powerfarm adds what ADK declines to promise |
| **vocabulary/** | |
| [`initial_registry_manifest.md`](vocabulary/initial_registry_manifest.md) | Part VIII: 55 → 99 definitions, enumeration-complete |
| [`research_vocabulary_pass.md`](vocabulary/research_vocabulary_pass.md) | the research institution, and why almost none of it is constitutional |
| [`research_scheme_reconciliation.md`](vocabulary/research_scheme_reconciliation.md) | the Research Scheme **is** the Compass (R-10) |
| **conformance/** | |
| [`CURRENT_BASELINE.md`](conformance/CURRENT_BASELINE.md) | what the code does today, and where it is thin |
| **evidence/** | |
| [`SOURCES.md`](evidence/SOURCES.md) | exactly what this pack was designed against, with hashes |
| **background/** | superseded drafts and the audits the design came out of — kept so no conclusion is unattributable, not required reading |

The law→test map is **not** copied here. It lives at `conformance/LAW_TEST_MAP.toml` in the
repository so there is one source, and `conformance/test_law_coverage.py` checks it against the
specification — adding a law to the constitution fails CI until someone classifies it.

---

## The result worth stating first

Working through external representation produced a **smaller** constitutional surface than expected,
not a larger one.

Signing an agreement, hiring a maintainer, entering a research collaboration, making a public
commitment, accepting an obligation, acknowledging a failure, issuing a responsible disclosure — all
of these are the same thing: an external effect passing through the §11.2 phases. They differ only
in `effect_kind`, which is ordinary vocabulary. So the constitution needs one generic external-effect
protocol, not one vocabulary per kind of institutional act.

The same held for research. A rich research civilization grows above the constitution and adds zero
constitutional definitions to it.

Node species, disclosure profiles, machinery classes, budget vocabulary, `AdmitBatch`, publication
vocabulary, engine vocabulary, `effect_kind` definitions and every ordinary Rule are all registrable
post-Genesis without amendment. **That is the test of whether this constitution is the right size —
if any of them turns out to need Genesis, the boundary was drawn wrong.**

---

## How this phase was closed

Three exit criteria, all met:

- **E1** — every design claim about current behaviour has a test or an explicit waiver. Roughly
  forty claims were verified by reading; reading does not survive refactoring. B1–B5 converted the
  load-bearing ones into properties the repository enforces, so implementation cannot silently
  invalidate the design it is implementing. 63 → 128 tests, plus 19 SQL assertions that provoke the
  database into refusing rather than reading migration text and hoping.
- **E2** — the decision register is complete, unambiguous and single-sourced, including the
  constitution's inline `A-*` markers.
- **E3** — this pack.

The phase ends with a universe fully designed and deliberately unborn. That is the right place to
stop, because the next phase's first act is irreversible in a way nothing in this one was.
