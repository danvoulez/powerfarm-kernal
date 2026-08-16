# Open Decisions

What remains genuinely undecided. These are **not** gaps in the design — they are choices that
belong to Dan, and the design deliberately stops short of making them.

Meanings live in `DECISION_REGISTER.md`. This file records only *why each is still open* and *what
it blocks*.

---

## Blocking Genesis — must be answered before the ceremony is admitted

### D-Director-08 — Is Dan's Identity also the Root Identity?

**Settle this first.** Everything about Root/Director disjointness rests on it. If one keypair holds
both mandates, "Root is spent at `GenesisClosed`" is a promise only Dan can verify rather than a
structure anyone can check. A separate Root key, held differently — cold, or split — is what makes
the separation physical instead of declarative.

*Blocks:* D-Genesis-03 (what `genesis.yaml` binds), key generation, Part IX of the constitution.

### D-Genesis-04 — Does this universe get an amendment protocol?

`amendment-or-fork` is currently a **name with no content**. §4.2 forbids inventing the substance
later: *"Such a protocol must itself be born at Genesis; it cannot be invented later."*

If Genesis is ratified as it stands, this universe has **no usable in-universe constitutional
amendment mechanism**, and fork/new Genesis becomes the only exit — permanently, for every future
constitutional definition.

*Blocks:* Part VII of the constitution; every later constitutional change.

### D-Director-03 — Recovery from total loss of Director keys

Three designs, each with a real cost:

| Option | Cost |
|---|---|
| Genesis-born constitutional quorum *(recommended)* | requires designating those Identities at Genesis |
| dormant Root retained for recovery | leaves a permanent superuser, which the whole design exists to avoid |
| fork-only | honest and spec-legitimate (§4.2), but unforgiving |

*Blocks:* Part VI.3; who else needs keys at Genesis.

### A-9 — Is the organization Identity Genesis-born?

Recommended yes, symmetric with Root and Director. It blocks the ceremony because the alternative —
created by the first Director act — opens a window in which Powerfarm can act internally but cannot
be a party to anything external. Which legal entity, in which jurisdiction, is a **separate**
question and does *not* block Genesis: A-10 makes the external-authority interface constitutional
and its jurisdiction-specific instances ordinary.

*Blocks:* Part IX; whether a fourth Identity needs key material.

### Key material

Real Ed25519 keypairs for Root, Dan-as-Director, and any constitutional reviewers. **This pack
cannot supply them and must not pretend to.** Generating them is an act with custody consequences
and belongs to Dan.

*Blocks:* the ceremony itself.

### Quorum sizes and windows (carried as A-8)

Amendment quorum, succession quorum, delay windows, and **who the constitutional reviewers are**.
The recommended defaults (2-of-3, 30 days) are placeholders chosen for concreteness, not analysis.

---

## Not blocking Genesis — decidable later without a fork

| ID | Question | Recommendation |
|---|---|---|
| **A-11** | public commitments ratified by default or by explicit act | explicit act |
| **A-12** | does Powerfarm publish the authorization chain to counterparties | disclosure-profile question, Phase 8 |
| **D-Director-04** | `max_holders` | 2, so handover never passes through zero |
| **D-Director-05** | Director's role in amendment | propose-only |
| **D-Director-06** | mandate boundary: single object or decomposed | single |
| **D-Director-07** | delegation depth default | 0 |
| **R-1** | drop `SubmitCommand` | drop |
| **R-4** | `request.metadata` open shape | keep open, forbid Rule reads |
| **R-5** | seed `effect_kind` at Genesis | no |
| **R-9** | `Tension` as species *and* relation | keep both |
| **R-11** | `ResearchCompass` as node species | yes |
| **R-12** | CR-8 scope | all Rules |
| **R-14** | `competes_with`, `breaks`, `qualified_by` | catalogue, defer |
| **R-17** | eternity clause on CR-1 rung 4 | adopt |
| **R-19** | drift rejection Act type | `CommandDenied` with a drift reason |
| **R-20** | `survival_rungs_admitted` as a parameter | yes |

---

## External evidence still missing

Facts that could not be established from the supplied material and would be unsafe to assume.

| Unknown | Why it matters |
|---|---|
| Legacy `relations` rows in any live database | Determines whether the Phase 0a migration may add `admitted_act` at all. **Check before writing it.** |
| Durable Cloudflare OS state keyed by email | Determines whether re-keying needs a migration inventory first |
| Golden Bridge strict-routing invariants | The repository is private and absent from every supplied archive; all Phase 7 claims are unverifiable |
| Whether a Genesis ceremony has run in any environment not visible here | If yes, the pre-Genesis window is already closed and fork is the only remedy |
| Which entity, in which jurisdiction, is the first organization Identity | External-authority predicates cannot be instantiated without it (interface is constitutional; instances are ordinary — so this does **not** block Genesis) |

---

## Two things worth ratifying with counsel, not with engineering

**Symmetric accountability** (Constitution V.7) means the record is discoverable when things go
wrong. The same chain that demonstrates diligence records what the institution knew and when. That
is the price of the promise and should be accepted knowingly.

**The institution must be able to bear what it accepts.** Powerfarm can represent accountability
perfectly and still be unable to honour it — insurance, reserves, corporate form. That is a legal
and financial design problem, not a ledger one.
