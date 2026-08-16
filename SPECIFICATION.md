# Powerfarm Kernel Specification

**Status:** current repository specification, pre-Genesis

**Authority:** subordinate to accepted decisions in the Decision Register

**Scope:** constitutional computation, admission, and ledger adapters only

## 1. Institutional boundary

Powerfarm is an append-only, graph-native institution. Objects carry immutable
content; Relations carry typed meaning; Acts record governed occurrence; State
is a disposable projection over admitted history at an explicit cut.

```text
Platform / Engine / humans
          |
          | signed Command proposals + typed Context
          v
protocol -> service -> kernel -> ledger admission
                                  |
                                  v
                     Objects + Acts + Relations + Registry
```

The Kernel decides and admits. Engines execute. Platforms schedule and expose
products. Ledgers remember. Moving or replacing an engine or platform must not
change the meaning of admitted Powerfarm history.

## 2. Authority and identity

Authentication is evidence linking an external principal to a Powerfarm
Identity. It never grants authority by itself. Authority is derived at the
declared cut from admitted mandate definitions, grants, Rules, and unrevoked
history.

Root is a bootstrap membrane. The Director is an operating office. Their
mandates are disjoint: Root constitutes; Director operates. The exact initial
holders, recovery design, amendment protocol, quorum, public keys, and custody
records must be ratified before Genesis.

## 3. Canonical model

Canonical values use RFC 8785 JCS and SHA-256 over typed, versioned domain
preimages. Identity comes from content, never a database sequence, filename,
runtime identifier, or protocol session.

The canonical graph consists of:

- **Object** — immutable canonical bytes addressed by hash;
- **Identity** — governed actor with admitted key history;
- **Command** — signed proposal with no authority until evaluated;
- **Context** — typed decision input whose definition hashes are pinned;
- **Decision** — pure Rule evaluation at exact cuts;
- **Act** — immutable admitted occurrence caused by a Command;
- **Relation** — typed edge whose exact definition is hash-bound;
- **Registry definition** — versioned semantics born through admitted history.

`seq` is an operational cursor and may contain gaps. Constitutional order is the
ancestry DAG. A valid cut is a set of Act hashes closed under ancestry.

## 4. Admission

There is one transactional admission door. It rechecks signatures, hashes,
causal closure, exact Registry and Rule dependencies, decision-cut validity,
type definitions, lifecycle uniqueness, and required companion rows. The Act
and every authoritative companion row succeed or fail in the same transaction.

CAS objects may be staged before admission because they confer no authority.
Registry, Relation, Identity, key, principal-link, and other authoritative rows
may not be written around the admission door. Database grants enforce this
boundary; caller discipline is not a security mechanism.

## 5. Genesis

M2 prepares content. M3 performs the irreversible ceremony. The deterministic
candidate is generated from `genesis/registry_blueprint.py` and
`genesis/material-input.candidate.json`. Generated manifests are review
artifacts and must reproduce byte-for-byte.

The readiness gate refuses while ratifications, Constitution approval, real
public Ed25519 keys, or custody records are missing. Private key material is
forbidden from Genesis inputs. `genesis/ceremony.py` may only use the real
admission mechanism; a synthetic hash ceremony is not Genesis.

## 6. External and research boundaries

External effects remain phased: requested, authorized, dispatched, observed,
and claimed as an external fact are different events. A dispatch attempt is not
proof of outcome. An observation is a provenance-bearing claim, not reality
manufactured by consensus.

The Research Scheme directs work and confers no authority. Research vocabulary,
frontiers, campaigns, experiments, and findings are ordinary governed graph
objects registered after Genesis. Research tables are projections, never a
parallel canonical ledger. The exact Research Scheme v0.1 source is preserved
at `GENESIS_DESIGN_PACK/constitution/02_Research_Scheme_Compass.md` and its
SHA-256 is recorded in the evidence register.

## 7. Constitutional laws

These identifiers are the normative law catalogue used by the executable
conformance map.

- **PF-01 — Identity Required.** Every Act names the Identity responsible for it.
- **PF-02 — Registry Closure.** Every governed type resolves at the declared Registry cut.
- **PF-03 — Intent Before Change.** Every consequential Act is caused by a prior Command.
- **PF-04 — Rule Governance.** Consequences require an attributable allowing Rule decision.
- **PF-05 — Reviewer Is Governed.** Reviewers act through the same Identity and Rule system.
- **PF-06 — Review Is History.** Requests, reviews, and resolutions are immutable Acts.
- **PF-07 — Immutable Acts.** Admitted history is never updated or deleted.
- **PF-08 — CAS Integrity.** Stored canonical bytes hash to the identity under which they are stored.
- **PF-09 — Typed Relations.** Canonical edges bind an exact Relation definition.
- **PF-10 — Acyclic Ancestry.** An admitted Act cannot create a causal cycle.
- **PF-11 — Reference Discipline.** Canonical references are hashes, not embedded mutable values.
- **PF-12 — Causal Order Constitutional.** Ancestry, not sequence allocation, defines order.
- **PF-13 — Declared Decision Cut.** The decision records and validates the history it examined.
- **PF-14 — Context Typing.** Every Rule input is typed and definition-hash pinned.
- **PF-15 — Lifecycle Completeness.** A Command may have many lifecycle Acts but one consequence.
- **PF-16 — Deterministic Projection.** Same projector plus same cut yields the same State.
- **PF-17 — Observation Provenance.** Observations preserve source and acquisition claims.
- **PF-18 — No Plaintext Secrets in History.** Secret material never enters canonical history.
- **PF-19 — Acyclic Genesis.** Genesis dependencies are complete and acyclic.
- **PF-20 — Self-Government.** Changes to authority enter through governed Acts.
- **PF-21 — Versioned Governance.** Acts bind exact Rule and Registry definition hashes.
- **PF-22 — Domain-Separated Hashing.** Canonical object kinds cannot collide by shared bytes.
- **PF-23 — Unique Occurrence.** Idempotency is keyed by Act identity, not Command identity.
- **PF-24 — External Effects Phasing.** Authorization, dispatch, and observation never collapse.
- **PF-25 — Constitutional Change Discipline.** Amendment follows a Genesis-born protocol or forks.
- **PF-26 — Temporal Honesty.** Claimed time is content; causal order and observation time remain distinct.

## 8. Repository obligations

- `kernel/` remains deterministic and free of network or wall-clock authority.
- `service/` composes governed operations without inventing protocol semantics.
- `ledger/` implements the narrow storage and admission contracts.
- `protocol/mcp/` transports semantic operations without session authority.
- `conformance/` maps every PF law to evidence or an explicit implementation gap.
- `supabase/migrations/` is sealed physical history: additions only.

Documents that describe superseded deployments, snapshots, audits, or handoffs
do not remain in the active tree. Git history is their archive.
