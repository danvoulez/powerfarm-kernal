# Powerfarm Institutional Pack

This directory contains the material that governs or justifies Powerfarm's
pre-Genesis constitutional boundary. It is intentionally not an archive of every
analysis that produced the current design; Git history performs that function.

## Authority and reading order

1. [`decisions/DECISION_REGISTER.md`](decisions/DECISION_REGISTER.md) — accepted,
   frozen, recommended, and open rulings.
2. [`../SPECIFICATION.md`](../SPECIFICATION.md) — current Kernel system contract
   and PF law catalogue.
3. [`constitution/01_Genesis_Constitution_0.2.md`](constitution/01_Genesis_Constitution_0.2.md)
   — integrated Constitution draft.
4. [`constitution/02_Research_Scheme_Compass.md`](constitution/02_Research_Scheme_Compass.md)
   — exact Powerfarm Research Scheme v0.1 source.
5. focused contracts under `specifications/`.

The Constitution is a draft and the Research Scheme is an ordinary governed
object, not constitutional authority. Research direction never authorizes an
Act, expenditure, or external effect.

## Active tree

```text
GENESIS_DESIGN_PACK/
├── constitution/
│   ├── 01_Genesis_Constitution_0.2.md
│   └── 02_Research_Scheme_Compass.md
├── decisions/
│   ├── DECISION_REGISTER.md
│   └── OPEN_DECISIONS.md
├── specifications/
│   ├── canonical_preimages.md
│   ├── admission_architecture.md
│   ├── cr1_declared_decision_cut.md
│   ├── director_institution.md
│   ├── external_representation.md
│   ├── engine_protocol.md
│   └── adk_2_7_absorption.md
├── vocabulary/
│   └── research_scheme_reconciliation.md
└── evidence/
    └── SOURCES.md
```

`genesis/registry_blueprint.py` is now the executable source for the Registry
candidate; prose enumeration was removed. `conformance/LAW_TEST_MAP.toml` is the
executable law-to-evidence index; a dated baseline snapshot was removed.

## What was deliberately removed

Superseded drafts, audit diaries, handoff notes, dated baselines, and earlier
vocabulary passes no longer occupy the active tree. Their claims either became a
decision, a focused contract, executable code, or ceased to be current. The old
macOS deployment profile and its implementation were also removed from this
Kernel repository.

Nothing here performs Genesis. The readiness gate in `genesis/material.py`
continues to refuse until the open ratifications, public keys, custody records,
and Constitution approval are real.
