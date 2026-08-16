# The Powerfarm Genesis Constitution — Draft 0.2

Integrated draft. Supersedes 0.1 and the External Representation addendum.

Design document: what `genesis.yaml` and the Genesis definition objects must *say*, expressed as
design before it is expressed as a binding.

**Status: draft for reaction. Not for ratification.** Nothing here has been admitted, and nothing
should be until the decisions in Part XII are settled deliberately.

No code, migrations, commits, or database mutations.

---

## 0.1 What this document is

Genesis is the only exceptional transition in Powerfarm (§16). Everything after it is governed by
the machinery Genesis installs; nothing before it is governed at all. This document must:

1. satisfy every mandatory binding in §16;
2. establish the Director institution and Powerfarm's presence in the world;
3. bind nothing that ought to remain amendable.

It is written to be read by a person deciding whether to live inside it.

## 0.2 Changes from 0.1

| Change | Reason |
|---|---|
| External representation moved from an appendix into **Part V** | It is not an extension of the office; it is what the office is for |
| Root clause sharpened to *"the Root role confers no external representation authority"* | 0.1 said Root "has no external capacity," which was Powerfarm asserting something about a human's legal standing — the exact overclaiming this constitution forbids |
| Organization Identity is **not** constitutionally singular | Subsidiaries, foundations, research entities, regional companies and joint ventures may each be real-world embodiments within one institutional architecture |
| A-10 (jurisdiction) demoted from **halt** to **deferred instantiation** | The external-authority *interface* is constitutional; the jurisdiction-specific *predicate* is ordinary and awaits incorporation and counsel |
| Symmetric accountability stated as a constitutional clause (V.7) | It is the claim that makes the responsibility promise real, not a side effect of the design |
| Final external phase carries **claimed** semantics | Powerfarm cannot cryptographically manufacture legal validity |

## 0.3 Assumptions carried

Recommendations carried forward so the draft is concrete. **Each is a decision not yet made.**
Marked `[A-n]` where they bite.

| ID | Assumption | Alternative |
|---|---|---|
| A-1 | Recovery from total Director loss is a Genesis-born constitutional quorum | dormant Root; fork-only |
| A-2 | `max_holders = 2`, `min_holders = 1` | 1; N |
| A-3 | Director may propose amendments, never enact alone | one vote among N; excluded |
| A-4 | Mandate boundary is a single constitutional object | decomposed per power class |
| A-5 | Delegation depth default 0 | 1 with expiry; parameterised |
| A-6 | **Dan's Identity is Director only; Root is a separate Identity, separately-held keys** | Dan is both |
| A-7 | Structural laws and constitutional Rules separately enumerated | keep all four as Rules |
| A-8 | Amendment delay 30 days; constitutional quorum 2-of-3 | any N-of-M + window |
| A-9 | The organization Identity is Genesis-born | created by first Director act |
| A-10 | External-authority **interface** is constitutional; **instances** are ordinary and deferred | bind a jurisdiction now |
| A-11 | Public commitments enter history by explicit act, not by default | automatic ratification |
| A-12 | Counterparty-verifiable authorization proof is a disclosure-profile question (Phase 8) | constitutional now |

**A-6 remains the one to settle first.** If Dan holds both Identities, Root/Director disjointness
is a promise rather than a structure.

## 0.4 A refinement to D-Genesis-01

A Powerfarm Rule decides a Command: `evaluate(identity, command, context, cut) → allow | deny |
require_review`. Two of the four originally declared names fit; two do not.

- `declared-decision-cut` — decides whether a Command may commit given cut drift ✓
- `amendment-or-fork` — decides Commands touching constitutional definitions ✓
- `append-only-acts` — no Command is authorized by it; a storage property ✗
- `reference-by-hash` — a canonicalization discipline, not a decision ✗

§18 already separates these as *Structural laws*. The current `genesis.yaml` collapses the
categories by filing all four under `constitutional_rules`; the fix is to un-collapse them.

> **D-Genesis-01 (refined).** Every name declared a *constitutional Rule* must resolve to a
> content-addressed `kind=rule` definition born at Genesis and citable in `rule_hashes`. Structural
> laws are separately enumerated, bound at Genesis as part of the universe's identity, and enforced
> by construction rather than evaluation. Neither list may contain a member of the other.

---

# PART I — Universe identity

Satisfies §16 bindings 1–5 and §10.1.

| Binding | Value |
|---|---|
| Specification | `powerfarm-system-v3.2` |
| Canonicalization | `rfc8785-jcs-v1` — JCS is the *sole* canonical encoding; CBOR, MessagePack and sorted-key JSON are non-conforming (§10.1:430-432) |
| Hash algorithm | `sha256` |
| Domain tag namespace | `powerfarm`, tag version `v1` (`powerfarm:act:v1`, `powerfarm:relation:v1`, …) (§10.1:440-447, PF-22) |
| Golden vector suite | `values`, `arrays`, `unicode`, `french`, `weird`, `structures` — passed byte-exactly before any implementation may participate |
| Commit mechanism | single-writer commit gate; no authoritative Act enters history by any other path |
| Temporal anchoring hook | reserved: `anchored_at`, `notarized_by`. Implementation deferred; the ontology slot is not (§10.3:472) |
| Genesis order | `GenesisCreated → RegistryCreated → RootIdentityCreated → RootAuthorityGranted → GenesisClosed` |

**Binding discipline.** Genesis binds the *canonical content* of everything below, not its name. A
name whose content lives outside `genesis_root_hash` is mentioned, not bound.

---

# PART II — Structural laws

Enforced by construction. Not evaluable, not citable in `rule_hashes`, not amendable short of
fork. `[A-7]`

| Law | Statement |
|---|---|
| **SL-1 Append-only history** | Acts are immutable and append-only. Existing records are corrected by new Acts, never edited or deleted |
| **SL-2 Reference by hash** | All object references are by content hash; embedding by value is forbidden. Hashes are computed over domain-tagged preimages |
| **SL-3 Causal acyclicity** | Ancestry is a DAG. `seq` is an operational cursor, never constitutional order. A history cut is a set of Act hashes closed under ancestry |
| **SL-4 Acyclic constitutional dependency** | The Genesis graph defining constitutional dependency is acyclic |
| **SL-5 Typed relations** | Objects are connected by immutable typed Relations; relation semantics are never collapsed into an untyped parents array |

These are eternity clauses. A universe violating one is not a different Powerfarm — it is not
Powerfarm.

---

# PART III — Constitutional Rules

Materialized as content-addressed `kind=rule` definitions, born at Genesis, citable in
`rule_hashes`. Amendable only through Part VII.

### CR-1 `declared-decision-cut`

Every authorization decision records the cut it examined. When history advances before commit, this
Rule decides whether the decision stands, must be reauthorized, or may proceed.

- **Genesis behaviour: strict.** Any advance of the declared cut requires reauthorization.
- Fail-closed. Its hash appears in `rule_hashes` of every consequential Act, making the drift
  decision attributable rather than anonymous.
- The existing hardcoded checks become this Rule's *enforcement machinery* — they remain and are
  correct; what changes is that history records which Rule decided.
- **Deliberately amendable** so causal/context-scoped relevance can replace whole-history equality
  once the Rule engine's static read-set analysis exists to make it sound. Amendment must never
  weaken it to "commit regardless" by default.

### CR-2 `amendment-or-fork`

Decides any Command whose effect would create, alter, or reinterpret a constitutional definition.
Denies all such Commands except those routed through Part VII — **including when the requester
holds Root or Director authority.** This is what makes PF-25 executable rather than aspirational.

### CR-3 `root-mandate`

- Before `GenesisClosed`: Root may constitute (Part IV).
- After `GenesisClosed`: Root holds no operational authority. Every Command from the Root Identity
  that is not an explicitly Genesis-born recovery action is denied.
- Root identity resolves **from admitted Genesis history**, never from configuration.
- **The Root role confers no external representation authority**, at any time. See IV.4.

### CR-4 `director-mandate-boundary`

The enumerated powers and prohibitions of Part V. `[A-4]`

### CR-5 `director-succession`

Part VI. **Does not reference Root** — which is what allows Root to be spent.

### CR-6 `no-self-extension`

> No exercise of any office's authority may increase that office's powers, extend delegation depth
> beyond the declared maximum, or appoint the reviewers of its own actions.

Stated generally, so it binds every office Powerfarm ever creates.

### CR-7 `dual-authority`

> An externally consequential Act must reference both (a) its Powerfarm authorization chain, and
> (b) evidence satisfying the applicable external-authority predicate declared for that domain and
> threshold in the mandate in force at the declared cut. Where the predicate is unsatisfied or
> unevidenced, the effect may not advance beyond `Dispatched`, and no Act may assert the commitment
> is in force.

The **interface** is constitutional. The **predicate instances** — which jurisdiction, which
thresholds, which corporate instrument — are ordinary mandate detail and may be unresolved at
Genesis without weakening the Rule. `[A-10]`

---

# PART IV — Root

### IV.1 Identity

Genesis binds Root Identity's canonical content and initial public keys, not a reference to them.
`[A-6]` Root is a distinct Identity from the Director's, with separately held key material.

### IV.2 Mandate — exhaustive

Root may, and only before `GenesisClosed`:

1. bind the constitution;
2. seed initial Registry definitions;
3. establish offices and their mandate boundaries;
4. create the initial Identities;
5. install the initial office holders.

### IV.3 Exhaustion

At `GenesisClosed`, Root's mandate is spent. Root cannot appoint, remove, operate, register, grant,
or amend. `[A-1]` Under the recovery-quorum design Root holds no recovery power either. Root keys
should thereafter be treated as archival evidence, not an operating credential.

> **The environment variable ceases to determine anything at `GenesisClosed`.** It is legitimate
> ceremony input — the ceremony must learn the root public key from somewhere. It is illegitimate as
> a continuing source of authority. Any post-Genesis code path resolving root authority from
> configuration rather than admitted history is non-conforming.

### IV.4 Root and the world

> **The Root role confers no external representation authority.**

This constrains what Powerfarm may infer, not what any person may do. The human who participates as
Root during the ceremony may independently be a company director, shareholder, lawyer or signatory
under ordinary law — Powerfarm simply must never derive that authority from Root status, nor
represent Root as speaking for the institution.

Root constitutes. Director represents. Powerfarm records what its authorized representatives and
systems actually did.

---

# PART V — The Director office and Powerfarm's presence in the world

### V.1 Why the office exists

An institution that produces consequential work must be able to stand in the world and say: *that
was ours, we authorized it, here is the evidence, here is who represented us, and we accept what
follows.*

The Director is the office through which Powerfarm obtains **accountable human presence**. Every
other part of this constitution is infrastructure for that sentence being checkable rather than
rhetorical.

The office is not an administrator the software needs. It is the point at which Powerfarm becomes
answerable.

### V.2 Four elements

| Element | Role |
|---|---|
| **Director office** (`powerfarm.director`) | the office through which Powerfarm obtains accountable human presence |
| **Organization Identity** (kind `organization`) | identifies the legal person bearing external rights and obligations |
| **Representation mandate** | explains why this human may act for that organization, in which domains, to which thresholds |
| **External Effects Protocol** (§11.2) | prevents Powerfarm confusing authorization, signature/action, observation, and legal effectiveness |

**Existence.** There exists an office `powerfarm.director`. Its existence is constitutional; its
holder is governed history.

**Plurality.** Powerfarm's constitutional institution is embodied in law by one or more
organization Identities. `[A-9]` The constitution does **not** assert that Powerfarm has exactly one
legal entity — subsidiaries, foundations, research entities, regional companies and joint ventures
may each be real-world embodiments participating in the same institutional architecture. Each is a
distinct organization Identity; each may have its own representation mandates.

**Why the organization holds its own Identity.** If agreements bound the *Director's* Identity,
succession would break every contract — a new Director would inherit an office whose commitments
were made by someone no longer holding it. The counterparty's agreement is with the organization.
So the organization **is party**; the Director **represents**.

```
Powerfarm Organization Identity
        │
        ├── represented_by ──► Dan Identity
        │                          │ holds
        │                          ▼
        │                    powerfarm.director
        │                          │ governed by
        │                          ▼
        │                    DirectorMandate.v1
        ▼
External commitment
        │
    Requested
        ↓
    Authorized                 (Powerfarm decides)
        ↓
    Dispatched / performed     (system-internal fact: we handed this out)
        ↓
    Observed with provenance   (evidence, observer Identity, content hashes)
        ↓
    Recorded as claimed external fact
```

### V.3 Mandate boundary — constitutional

**Internal powers.** Register ordinary vocabulary; register and version ordinary Rules; create
Identities of any kind; grant, scope and revoke operational authority; appoint ordinary reviewers;
approve budget ceilings and publication policy; nominate a successor; propose constitutional
amendments.

**External representation.** Within declared domains and thresholds, and subject to CR-7: sign
client and partnership agreements; represent Powerfarm before universities, laboratories,
governments and standards bodies; attend scientific and commercial events as Director; hire and
contract maintainers and researchers; enter research collaborations; make public institutional
commitments; commission work and purchase services; acknowledge failures; sign responsible
disclosures; accept contractual obligations; and accept consequences on behalf of the organization
when Powerfarm's products cause harm or fail their commitments.

**May not.** Enact a constitutional amendment alone `[A-3]`; create, alter or reinterpret any
constitutional definition; claim Root authority or act in the constitutive layer; rewrite, delete or
reorder history; enlarge the Director mandate (CR-6); extend delegation depth beyond the declared
maximum; appoint the reviewers of Director actions; assert legal validity on Powerfarm's behalf
(V.5); act outside the mandate in force at the declared cut.

### V.4 Mandate detail — ordinary

Namespaces, ceilings, quorum sizes, delegation depth, expiry defaults, and the **external-authority
predicate table** live in a versioned ordinary policy object the boundary points at:

```
research_collaboration,  any value       → Director alone
commercial,              ≤ threshold T   → Director alone
commercial,              > threshold T   → Director + second officer, evidence required
financial commitment,    any             → per applicable banking mandate, evidence required
public institutional commitment          → Director alone, ratified by explicit act  [A-11]
```

These change by governed Act, no fork. This is what lets the office track real corporate
arrangements as they evolve, and what allows Genesis to precede incorporation. `[A-10]`

### V.5 Internal authority is decided; external authority is witnessed

| | Internal authority | External authority |
|---|---|---|
| Question | May this Identity cause this Powerfarm Act? | May this human legally bind this organization in this domain? |
| Source | Powerfarm Rules at a cut | company law, corporate mandates, banking authority, shareholder arrangements |
| Powerfarm's role | **decides** it | **records evidence of** it |
| If it fails | the Act does not commit | the effect must not advance beyond `Dispatched` |

Powerfarm cannot confer signing authority that company law withholds, and must never appear to.

**The word *claimed* is load-bearing.** Powerfarm can prove what it authorized, what evidence it
received, what its representatives did, and what it subsequently treated as an obligation. It cannot
cryptographically manufacture the legal validity of a contract. Every externally consequential Act
asserts only what Powerfarm can know — *we authorized this, this representative acted, this evidence
was observed, we treat this as binding upon us* — never *this agreement is valid.* Validity is the
world's judgment.

This is §11.1 applied strictly to institutional facts: observations with provenance, not infallible
truth.

### V.6 Delegation

- Delegated grants name a **strict subset** of the delegator's mandate powers, verified by Rule
  against the delegator's own grant at the declared cut.
- **Delegation depth defaults to 0** `[A-5]`: delegates may not re-delegate. Otherwise authority
  fans out and revocation becomes unprovable.
- Delegations carry expiry. An unexpiring delegation is a transfer in disguise.
- **External representation is delegable only by explicit domain and threshold, never wholesale.**
  "Represent Powerfarm" is not a grantable unit.

### V.7 Symmetric accountability

> **The provenance system preserves evidence against Powerfarm as faithfully as it preserves
> evidence for Powerfarm.**

The same chain that demonstrates diligence records what the institution knew, when it knew it, what
it authorized, what it declined to act on, and what it undertook. Append-only history (SL-1) means
an accepted obligation cannot be quietly withdrawn: a later correction is a new Act standing beside
the original, never a replacement for it.

This is not a side effect of the design. **It is what makes the responsibility claim real.** An
institution unwilling to be held to its own record is not making the claim at all.

Much of the surrounding industry runs an asymmetry — *we built it* when it works, *the model
produced it* when it fails. Powerfarm's counter-claim is narrower and more defensible than
infallibility: an intelligent system may perform the work, but an accountable institution stands
behind the work, and machine intelligence is not a mechanism for evaporating institutional
responsibility.

### V.8 Cardinality

`min_holders = 1`, `max_holders = 2` `[A-2]`. Zero is **forbidden**: if succession requires a
sitting Director to nominate, zero is a deadlock rather than a state. Two exists precisely so
handover never passes through zero.

---

# PART VI — Succession, revocation, recovery

### VI.1 Succession

```
sitting Director nominates                    -> DirectorNominated
  + N-of-M constitutional reviewers approve   (requester != reviewer, §9)
  + declared delay window elapses
  -> AuthorityGranted    (successor admitted; overlap begins)
  -> AuthorityRevoked    (predecessor's grant closed)
```

Quorum and window are constitutional `[A-8]`; who the reviewers are is ordinary. **Root appears
nowhere** — deliberately.

Representation mandates follow the office, not the person: the successor represents the same
organization Identities, and existing obligations are undisturbed.

### VI.2 Revocation

Revocation is always an **Act**, never a deletion. Proving "Dan was Director at cut C" requires
proving *no revocation exists* in the ancestry-closed cut, and absence is only provable when
revocations are discoverable objects.

### VI.3 Recovery — total loss of Director keys `[A-1]`

A Genesis-born **constitutional recovery quorum**: named Identities, not Directors, who may admit a
replacement Director under quorum plus extended delay. They hold no operational power and cannot
direct the system — only repopulate the office.

Three mandates, none a superset of another: *constitute*, *operate*, *restore*.

Fallback if you prefer not to designate this body: total loss is terminal and recovery is a fork
under `forked_from` — spec-legitimate (§4.2), honest, unforgiving.

### VI.4 Key rotation

Solved by §5.1: `RotateKey → KeyRotated`, Identity stable across rotation, valid keys a projection
over key history. Grants reference `identity_hash` and **never key material**. The only design
obligation is negative: no grant, relation or rule may reference a public key.

---

# PART VII — Amendment protocol

Without this, the universe is fork-only forever.

```
proposal by any mandate-holding Identity      -> AmendmentProposed
  + 2-of-3 constitutional reviewers approve, proposer excluded   [A-8]
  + 30-day delay window
  + no successful objection Act within the window
  -> AmendmentEnacted    (new constitutional definition version born)
```

**Unamendable (eternity clauses):** Part II structural laws; the prohibition on rewriting history;
CR-6 self-extension; V.7 symmetric accountability; and the requirement that this protocol cannot be
amended to remove review or delay.

**The Director may propose but never enact** `[A-3]`. With CR-6, this closes the path whereby an
office grows itself by amendment.

---

# PART VIII — Initial Registry definitions

Bound by canonical content. **Categories below; the complete enumeration with canonical schemas is
the next artifact.**

- Constitutional command and act types: Genesis vocabulary; Command lifecycle (all ten);
  constitutional change
- §17 self-government vocabulary: `GrantAuthority`/`AuthorityGranted`,
  `AppointReviewer`/`ReviewerAppointed`, `RegisterDefinition`/`DefinitionRegistered`,
  `RotateKey`/`KeyRotated` — all currently absent and required for the office to function
- Office and mandate kinds: `office`, `mandate` (registry `kind` has no CHECK, so no schema change)
- Representation vocabulary: `represented_by` relation type; representation mandate objects
- External effects phases: `Dispatched`, `Observed`, `DispatchFailed`, `EffectRetried`, and the
  claimed-external-fact type (V.5)
- Commitment and obligation vocabulary; acceptance and disclosure act types
- Constitutional context types: delegation and request-provenance keys
- Constitutional Rules CR-1 … CR-7

> **Every definition inspected by a typed Rule must carry its canonical schema from birth**
> (`payload_schema` for commands, `value_schema` for context keys). Seeding name/version shells and
> retrofitting later means typed Rules cannot register until constitutional vocabulary is
> re-versioned — which, post-Genesis, requires the amendment protocol.

**Design note for the enumeration.** PF-24 names the final external phase
`Committed-as-external-fact`. V.5 requires claimed semantics. Recommendation: keep the spec's phase
taxonomy for conformance, and name the registered Act type honestly (e.g. `ExternalFactClaimed`) so
the vocabulary cannot be misread as asserting validity. Flagged for your ruling rather than decided.

---

# PART IX — Initial holders

| Office / role | Holder | Bound at Genesis |
|---|---|---|
| Root | Root Identity | canonical content + initial public keys `[A-6]` |
| Director | **Dan Voulez's Identity** | canonical content + initial public keys |
| Legal person | **Powerfarm organization Identity** | canonical content `[A-9]` |
| Constitutional reviewers | named Identities | canonical content + initial public keys `[A-1]` `[A-8]` |

**Dan is Genesis-born Director.** The first appointment cannot be an ordinary Act for the same
reason `RegisterDefinition` cannot register itself: it would require registered vocabulary, a Rule,
and a granting authority — none of which exist before Genesis. Genesis is the unique membrane for
both.

What is bound is *"Dan is the initial holder,"* not *"Dan is Director forever."* From the first
succession onward the holder is governed history, by a path that does not run through Root.

> **Required before ratification:** real Ed25519 key material for Root, Dan-as-Director, and each
> constitutional reviewer. This draft cannot supply them and must not pretend to.

---

# PART X — Deliberately not constitutional

Stated explicitly, because omission is otherwise indistinguishable from oversight.

Mandate detail and policy; **external-authority predicate instances and their jurisdictions**
`[A-10]`; all operational vocabulary; ordinary Rules; ordinary reviewers; every holder after the
first; additional organization Identities beyond the first; projections including `active_grants`;
budget ceilings; disclosure profiles; node species; the Engine, the OS, and the inference gateway.

**None of the Director machinery beyond the boundary is constitutional.** The office is durable; its
instruments are not.

---

# PART XI — What this becomes

| This document | Artifact |
|---|---|
| Parts I, II | `genesis.yaml` scalar bindings + `structural_laws` list `[A-7]` |
| Part III | seven `kind=rule` definition objects, hashes bound into `genesis.yaml` |
| Parts IV–VII | `office`/`mandate` objects, CR-3/4/5/7, amendment protocol object |
| Part VIII | seed manifest with canonical schemas, content hash bound into `genesis.yaml` |
| Part IX | Identity objects + initial key material, bound by canonical content |

The ceremony then admits these as the five Genesis Acts, and `genesis_root_hash` finally commits the
whole constitution rather than a 19-line summary of it.

---

# PART XII — Open before ratification

1. **A-6** — is Dan's Identity also Root? Everything about disjointness turns on it.
2. **A-1** — recovery: quorum, dormant Root, or fork-only.
3. **A-8** — quorum sizes, delay windows, and who the constitutional reviewers are.
4. **Key material** for every Genesis-born holder.
5. **A-9** — is the organization Identity Genesis-born, and which entity is the first one?
6. **A-2, A-3, A-4, A-5, A-7, A-11, A-12** — carried defaults, each defensible, none settled.
7. The Part VIII enumeration, and the claimed-external-fact naming ruling.
8. **V.7 ratified with counsel.** Symmetric accountability means the record is discoverable when
   things go wrong. That is the price of the promise and should be accepted knowingly.
9. Whether the institution can bear what it accepts — insurance, reserves, corporate form. Powerfarm
   can represent accountability perfectly and still be unable to honour it. That is a legal and
   financial design problem, not a ledger one.

There is no clock on any of this except the one created by ratifying early.
