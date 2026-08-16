# The Powerfarm Genesis Constitution — Draft 0.1

Design document. This is what `genesis.yaml` and the Genesis definition objects must *say*,
expressed as design before it is expressed as a binding.

**Status: draft for reaction. Not for ratification.** Nothing here has been admitted, and nothing
should be until every assumption in §0.2 is settled deliberately.

No code, migrations, commits, or database mutations were made in producing this.

---

## 0.1 What this document is

Genesis is the only exceptional transition in Powerfarm (§16). Everything after it is governed by
the machinery Genesis installs; nothing before it is governed at all. So this document has to do
three things at once:

1. satisfy every mandatory binding in §16;
2. install the Director institution as designed;
3. avoid binding anything that ought to remain amendable.

It is written to be *read by a person deciding whether to live inside it*, not by a parser.

## 0.2 Assumptions carried (open decisions, defaulted for concreteness)

These are my recommendations from the institutional design, carried forward so this draft is
concrete. **Each is a decision you have not yet made.** Where one bites, it is marked `[A-n]`.

| ID | Assumption | Alternative |
|---|---|---|
| A-1 | Recovery from total Director loss is a Genesis-born **constitutional recovery quorum** (D-Director-03 → R2) | dormant Root (R1); fork-only (R3) |
| A-2 | `max_holders = 2`, `min_holders = 1` (D-Director-04) | 1 (no overlap); N (collegial) |
| A-3 | Director may **propose** amendments, never enact alone (D-Director-05) | one vote among N; excluded |
| A-4 | Mandate boundary is a **single** constitutional object (D-Director-06) | decomposed per power class |
| A-5 | Delegation depth default **0** (D-Director-07) | 1 with expiry; parameterised |
| A-6 | **Dan's Identity is Director only; Root is a separate Identity with separately-held keys** (D-Director-08) | Dan is both |
| A-7 | Structural laws and constitutional Rules are **separately enumerated** (refinement to D-Genesis-01, see §0.3) | keep all four as Rules |
| A-8 | Amendment delay window = 30 days; constitutional quorum = 2-of-3 | any other N-of-M + window |

**A-6 is the one I would settle first.** If Dan holds both Identities, Root/Director disjointness
is a promise rather than a structure — the same keys hold both mandates, and "Root is spent"
cannot be verified by anyone but Dan.

## 0.3 A refinement to D-Genesis-01

Drafting Part III forced a distinction I want to put in front of you rather than resolve silently.

D-Genesis-01 ruled that every name in `genesis.yaml.constitutional_rules` must resolve to a
content-addressed `kind=rule` definition. Applying that literally to the current four names breaks
on two of them, because a Powerfarm Rule has a specific shape — it decides a Command:

```
evaluate(identity, command, context, history_cut) -> allow | deny | require_review
```

- `declared-decision-cut` fits. Given cut drift, it decides whether this Command may commit.
- `amendment-or-fork` fits. Given a Command touching constitutional definitions, it decides.
- `append-only-acts` does **not** fit. No Command is authorized or refused by it; it is a property
  of storage, enforced by construction (`reject_act_mutation` triggers).
- `reference-by-hash` does **not** fit. It is a canonicalization discipline enforced in
  `kernel/canon.py`, not a decision about anyone's intent.

§18 already separates these as *Structural laws*, and your own instruction was not to collapse the
two categories unless the specification does. The current `genesis.yaml` collapses them by filing
all four under `constitutional_rules`. **The fix is to un-collapse them, which is consistent with
D-Genesis-01's purpose:** the rule existed to stop a declared Rule from hiding as a hardcoded
constant. A structural law is not hiding — it is a different category the spec itself names.

So D-Genesis-01 is refined, not overturned:

> **D-Genesis-01 (refined).** Every name declared as a *constitutional Rule* must resolve to a
> content-addressed `kind=rule` definition born at Genesis and citable in `rule_hashes`. Structural
> laws are separately enumerated, bound at Genesis as part of the universe's identity, and enforced
> by construction rather than by evaluation. Neither list may contain a member of the other.

---

# PART I — Universe identity

Satisfies §16 bindings 1–5 and §10.1.

| Binding | Value | Source |
|---|---|---|
| Specification | `powerfarm-system-v3.2` | §16 |
| Canonicalization | `rfc8785-jcs-v1` — JCS is the *sole* canonical encoding; CBOR, MessagePack and sorted-key JSON are non-conforming | §10.1:430-432 |
| Hash algorithm | `sha256` | §10.1 |
| Domain tag namespace | `powerfarm`, tag version `v1` (`powerfarm:act:v1`, `powerfarm:relation:v1`, …) | §10.1:440-447, PF-22 |
| Golden vector suite | `values`, `arrays`, `unicode`, `french`, `weird`, `structures` — every implementation must pass byte-exactly before participating | PF-22 |
| Commit mechanism | single-writer commit gate; no authoritative Act enters history by any other path | §16, §2 |
| Temporal anchoring hook | reserved: `anchored_at`, `notarized_by` relation types. Implementation deferred; the ontology slot is not | §10.3:472 |
| Genesis order | `GenesisCreated → RegistryCreated → RootIdentityCreated → RootAuthorityGranted → GenesisClosed` | §16 |

**Binding discipline.** Genesis binds the *canonical content* of everything below, not its name.
A name whose content lives outside `genesis_root_hash` is not bound — it is merely mentioned.

---

# PART II — Structural laws

Enforced by construction. Not evaluable, not citable in `rule_hashes`, not amendable by any
mechanism short of fork. `[A-7]`

| Law | Statement | Enforced where |
|---|---|---|
| **SL-1 Append-only history** | Acts are immutable and append-only. Existing rows are corrected by new Acts, never edited or deleted | storage triggers; Kernel has no update path |
| **SL-2 Reference by hash** | All object references are by content hash; embedding by value is forbidden. Hashes are computed over domain-tagged preimages | canonicalization layer |
| **SL-3 Causal acyclicity** | Ancestry is a DAG. `seq` is an operational cursor, never constitutional order. A history cut is a set of Act hashes closed under ancestry | Kernel + storage |
| **SL-4 Acyclic constitutional dependency** | The Genesis graph defining constitutional dependency is acyclic | ceremony construction |
| **SL-5 Typed relations** | Objects are connected by immutable typed Relations; relation semantics are never collapsed into an untyped parents array | Kernel types |

These are eternity clauses. A universe that violates one is not a different Powerfarm — it is not
Powerfarm.

---

# PART III — Constitutional Rules

Materialized as content-addressed `kind=rule` definitions, born at Genesis, citable in
`rule_hashes`. Amendable only through Part VII.

### CR-1 `declared-decision-cut` — the PF-13 Rule

Every authorization decision records the cut it examined. When history has advanced before commit,
this Rule decides whether the decision stands, must be reauthorized, or may proceed.

- **Genesis behaviour: strict.** Any advance of the declared cut requires reauthorization.
- Fail-closed. Its hash appears in `rule_hashes` of every consequential Act, so the drift decision
  is attributable rather than anonymous.
- The existing hardcoded checks at three layers become this Rule's *enforcement machinery* — they
  remain, and are correct; what changes is that history now records which Rule decided.
- **Deliberately left amendable** so that causal/context-scoped relevance (replacing whole-history
  equality) can be adopted later without a fork, once the Rule engine's static read-set analysis
  exists to make it sound. Amendment must never weaken it to "commit regardless" by default.

### CR-2 `amendment-or-fork` — constitutional change discipline

Decides any Command whose effect would create, alter, or reinterpret a constitutional definition.

- Denies all such Commands except those routed through the Part VII protocol.
- Denies them **including when the requester holds Root or Director authority**.
- This is the Rule that makes PF-25 executable rather than aspirational.

### CR-3 `root-mandate` — what Root may do, and when it stops

- Before `GenesisClosed`: Root may constitute (Part IV).
- After `GenesisClosed`: Root holds **no operational authority**. Every Command from the Root
  Identity that is not an explicitly Genesis-born recovery action is denied.
- Root identity is resolved **from admitted Genesis history**, never from configuration.

### CR-4 `director-mandate-boundary` — the office's constitutional envelope

The enumerated powers and prohibitions of Part V. `[A-4]`

### CR-5 `director-succession` — how the office changes hands

Part VI. Notably **does not reference Root**, which is what allows Root to be spent.

### CR-6 `no-self-extension` — the invariant that bounds every office

> No exercise of any office's authority may increase that office's powers, extend delegation depth
> beyond the declared maximum, or appoint the reviewers of its own actions.

Stated generally rather than for Director specifically, so it binds every office Powerfarm ever
creates.

---

# PART IV — Root

### IV.1 Identity

Genesis binds Root Identity's **canonical content and initial public keys**, not a reference to
them. `[A-6]` Root is a distinct Identity from the Director's, with separately held key material.

> **The environment variable ceases to determine anything at `GenesisClosed`.** It is legitimate
> ceremony input — the ceremony must learn the root public key from somewhere. It is illegitimate
> as a continuing source of authority. After Genesis, any code path resolving root authority from
> configuration rather than from admitted history is non-conforming.

### IV.2 Mandate — exhaustive

Root may, and only before `GenesisClosed`:

1. bind the constitution (this document);
2. seed initial Registry definitions;
3. establish offices and their mandate boundaries;
4. create the initial Identities;
5. install the initial office holders.

### IV.3 Exhaustion

At `GenesisClosed`, Root's mandate is spent. Root cannot appoint, remove, operate, register, grant,
or amend. `[A-1]` Under the recovery quorum design, Root holds no recovery power either — recovery
belongs to the body in Part VI.3.

Root's keys should thereafter be treated as archival evidence, not as an operating credential.

---

# PART V — The Director office

### V.1 Existence

There exists an office: **`powerfarm.director`**. Its existence is constitutional; its holder is
governed history.

### V.2 Mandate boundary — constitutional

**May:**
- register ordinary vocabulary (command/act/relation/context types, node species, disclosure
  profiles, projectors);
- register and version ordinary Rules;
- create Identities of any kind;
- grant, scope and revoke **operational** authority;
- appoint ordinary reviewers;
- approve budget ceilings and publication policy;
- nominate a successor;
- propose constitutional amendments.

**May not:**
- enact a constitutional amendment alone `[A-3]`;
- create, alter or reinterpret any constitutional definition;
- claim Root authority or act in the constitutive layer;
- rewrite, delete or reorder history;
- enlarge the Director mandate (CR-6);
- extend delegation depth beyond the declared maximum;
- appoint the reviewers of Director actions;
- act outside the mandate in force at the declared cut.

### V.3 Mandate detail — ordinary

Namespaces, ceilings, quorum sizes, delegation depth, expiry defaults live in a versioned ordinary
policy object the boundary points at. These change by governed Act, no fork required. **This is
what keeps the office durable without freezing it.**

### V.4 Delegation

- Delegated grants must name a **strict subset** of the delegator's mandate powers, verified by
  Rule against the delegator's own grant at the declared cut.
- **Delegation depth defaults to 0** `[A-5]`: delegates may not re-delegate. Without this,
  authority fans out and revocation becomes unprovable.
- Delegations carry expiry. An unexpiring delegation is a transfer wearing a disguise.

### V.5 Cardinality

`min_holders = 1`, `max_holders = 2` `[A-2]`.

Zero is **forbidden**: if succession requires a sitting Director to nominate, zero is a deadlock
rather than a state. Two exists precisely so handover never passes through zero.

---

# PART VI — Succession, revocation, recovery

### VI.1 Succession

```
sitting Director nominates              -> DirectorNominated
  + N-of-M constitutional reviewers approve   (requester != reviewer, §9)
  + declared delay window elapses
  -> AuthorityGranted    (successor admitted; overlap begins)
  -> AuthorityRevoked    (predecessor's grant closed)
```

Quorum and window are constitutional `[A-8]`; who the reviewers are is ordinary. **Root appears
nowhere in this flow** — deliberately.

### VI.2 Revocation

Revocation is always an **Act**, never a deletion. This is structural, not stylistic: proving
"Dan was Director at cut C" requires proving *no revocation exists* in the ancestry-closed cut,
and absence is only provable when revocations are discoverable objects. The same reasoning already
applied to `principal_bindings`.

### VI.3 Recovery — total loss of Director keys `[A-1]`

A Genesis-born **constitutional recovery quorum**: named Identities, not Directors, who may admit
a replacement Director under quorum plus an extended delay. They hold no operational power and
cannot direct the system — only repopulate the office.

This preserves disjointness in a third direction: *constitute*, *operate*, *restore* are three
mandates, none a superset of another.

If you prefer not to designate this body at Genesis, the fallback is R3 — total loss is terminal
and recovery is a fork under `forked_from`. That is spec-legitimate (§4.2) and honest, but
unforgiving.

---

# PART VII — Amendment protocol

Resolves G-4. Without this, the universe is fork-only forever.

```
proposal by any mandate-holding Identity   -> AmendmentProposed
  + 2-of-3 constitutional reviewers approve, proposer excluded   [A-8]
  + 30-day delay window
  + no successful objection Act within the window
  -> AmendmentEnacted   (new constitutional definition version born)
```

**Unamendable (eternity clauses):** Part II structural laws; the prohibition on rewriting history;
CR-6 self-extension; and the requirement that the amendment protocol itself cannot be amended to
remove review or delay. Everything else in Parts III–VI is amendable by this protocol.

**The Director may propose but never enact** `[A-3]`. Combined with CR-6, this closes the path
whereby an office grows itself by amendment.

---

# PART VIII — Initial Registry definitions

Bound by canonical content. Categories, not an exhaustive list — the enumeration belongs in the
ratification draft.

- **Constitutional command types:** the Genesis and constitutional-change vocabulary
- **Constitutional act types:** Genesis Acts, Command lifecycle (all ten), authority grant/revoke,
  amendment
- **§17 self-government vocabulary:** `GrantAuthority`/`AuthorityGranted`,
  `AppointReviewer`/`ReviewerAppointed`, `RegisterDefinition`/`DefinitionRegistered`,
  `RotateKey`/`KeyRotated` — currently absent and required for the office to function
- **Office and mandate kinds:** `office`, `mandate` (the Registry has no CHECK on `kind`, so new
  kinds need no schema change)
- **Constitutional context types:** delegation and request-provenance keys
- **Constitutional Rules:** CR-1 … CR-6

**Every definition inspected by a typed Rule must carry its canonical schema from birth**
(`payload_schema` for commands, `value_schema` for context keys). Seeding name/version shells and
retrofitting schemas later means typed Rules cannot register until constitutional vocabulary is
re-versioned — which, post-Genesis, needs the amendment protocol. This is the cheapest thing to
get right now and among the most expensive to get wrong.

---

# PART IX — Initial holders

| Office | Holder | Bound at Genesis |
|---|---|---|
| Root | Root Identity | canonical content + initial public keys `[A-6]` |
| Director | **Dan Voulez's Identity** | canonical content + initial public keys |
| Constitutional reviewers | named Identities | canonical content + initial public keys `[A-1]` `[A-8]` |

**Dan is Genesis-born Director.** The first appointment cannot be an ordinary Act for the same
reason `RegisterDefinition` cannot register itself: it would require registered vocabulary, a Rule,
and a granting authority — none of which exist before Genesis. Genesis is the unique membrane for
both.

What is bound is *"Dan is the initial holder,"* not *"Dan is Director forever."* From the first
succession onward the holder is governed history, and Part VI gives that history a path that does
not run through Root.

> **Required before ratification:** real Ed25519 key material for Root, Dan-as-Director, and each
> constitutional reviewer. This draft cannot supply them and must not pretend to. (Halt H-7.)

---

# PART X — Deliberately not constitutional

Stated explicitly, because omission is otherwise indistinguishable from oversight.

Mandate detail and policy; all operational vocabulary; ordinary Rules; ordinary reviewers; every
holder after the first; projections including `active_grants`; budget ceilings; disclosure
profiles; node species; the Engine, the OS, and the inference gateway.

**None of the Director machinery beyond the boundary is constitutional.** The office is durable;
its instruments are not.

---

# What this becomes

| This document | Artifact |
|---|---|
| Parts I, II | `genesis.yaml` scalar bindings + `structural_laws` list `[A-7]` |
| Part III | six `kind=rule` definition objects, hashes bound into `genesis.yaml` |
| Parts IV, V, VI, VII | `office`/`mandate` definition objects + CR-3/4/5 + the amendment protocol object |
| Part VIII | the seed manifest, with canonical schemas, its content hash bound into `genesis.yaml` |
| Part IX | Identity objects + initial key material, bound by canonical content |

The ceremony then admits these as the five Genesis Acts, and `genesis_root_hash` finally commits
the whole constitution rather than a 19-line summary of it.

---

# Open before ratification

1. **A-6** — is Dan's Identity also Root? Everything about disjointness turns on this.
2. **A-1** — recovery: quorum, dormant Root, or fork-only.
3. **A-8** — quorum sizes and delay windows; who the constitutional reviewers are.
4. **A-2, A-3, A-4, A-5, A-7** — carried defaults, each defensible, none settled.
5. **H-7** — real key material for every Genesis-born holder.
6. Whether Part VIII's enumeration is complete — it needs a line-by-line pass before ratification.

Nothing here should be admitted until 1, 2, 3 and 5 are answered deliberately. There is no clock
on this except the one created by ratifying early.
