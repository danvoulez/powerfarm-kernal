# External Representation — Powerfarm in the World

Design document. Specifies the External Authority concept and the precise amendments it makes to
the Genesis Constitution draft 0.1.

No code, migrations, or commits.

---

## 1. The primitive test — and the answer is no

Powerfarm's discipline is that a new constitutional primitive is a halt condition. So before
designing anything: **does institutional representation require one?**

It does not. The specification already contains the machinery, built for a different example.

**§11.2 External Effects Protocol** was written about sending money and opening valves:

```
Requested → Authorized → Dispatched → Observed/Confirmed → Committed-as-external-fact
```

Signing a research agreement is exactly this shape. So is making a public commitment at a
conference, hiring a maintainer, or issuing a responsible disclosure. Each is an intent that
becomes an authorization, then an act in the world, then an observation with evidence, then — only
then — an institutional fact.

And the governing sentence of §11.2 is precisely the discipline institutional accountability needs:

> A database commit MUST NEVER claim that external reality also committed.

Applied here: **Powerfarm must never record "we have an agreement" at the moment it authorizes
signing.** Authorized-to-sign, signed, and in-force are three different facts with three different
Acts. An institution that collapses them is lying in exactly the way §11 forbids — and would be
lying about its own obligations, which is the worst possible place to start.

The runtime already anticipates this. `powerfarm.observation.admit` exists today, and its own
description reads: *"Admit a provenance-bearing observation without conflating dispatch,
observation, or external commitment"* ([protocol/mcp/tools.py:90-95](../../protocol/mcp/tools.py:90)).
`ObservationAdmitted` is registered vocabulary. The phase Act types (`Dispatched`, `Observed`,
`DispatchFailed`, `EffectRetried`) are not yet registered — ordinary vocabulary, Part VIII work.

**Conclusion: External Representation is a mandate scope plus the External Effects Protocol. No
new primitive. No halt.**

---

## 2. The missing structural piece: Powerfarm needs its own Identity

This is the one genuinely new structural requirement, and it is not a primitive — it is an
application of one.

**The legal entity must hold its own Powerfarm Identity, of kind `organization`, distinct from
Dan's.** §5 already lists `organization` among identity kinds, and `identities.kind` carries no
CHECK constraint, so this needs no schema change.

Why it matters, concretely: if agreements bind *Dan's* Identity, then succession breaks every
contract. A new Director would inherit an office whose external commitments were made by a person
who no longer holds it. The counterparty's agreement is with Powerfarm, not with Dan.

So the correct shape is:

```
Powerfarm Ltd  (organization Identity)   ← the party to every agreement
      ▲
      │ represented_by  (scoped by mandate, at a cut)
      │
Dan's Identity (human)  ── holds ──►  powerfarm.director
```

Dan **represents**; the organization **is party**. Succession replaces the representative and
leaves every obligation intact. This also gives the accountability chain its final arrow a real
target: the delivered product relates to the organization Identity, not to a person and not to a
model.

---

## 3. Internal authority vs external authority

Your distinction, formalized.

| | Internal authority | External authority |
|---|---|---|
| Question | May this Identity cause this Powerfarm Act? | May this human legally bind Powerfarm in this domain? |
| Source | Powerfarm Rules at a cut | Company law, corporate mandates, banking authority, shareholder arrangements |
| Powerfarm's role | **decides** it | **records evidence of** it |
| Failure to hold | the Act does not commit | the effect must not pass `Dispatched` |

The critical asymmetry: **Powerfarm decides the first and can only witness the second.** A ledger
cannot confer signing authority that company law withholds, and it must never appear to.

### The dual-authority principle

> **CR-7 (proposed).** An externally consequential Act must reference both (a) its Powerfarm
> authorization chain, and (b) evidence satisfying the external-authority predicate declared for
> that domain and threshold in the mandate in force at the declared cut. Where the external
> predicate is unsatisfied or unevidenced, the effect may not advance beyond `Dispatched`, and no
> Act may assert that the commitment is in force.

The predicate itself is **ordinary mandate detail**, not constitutional — so it can track real
corporate arrangements as they change:

```
research_collaboration,  any value        → Director alone
commercial,              ≤ threshold T    → Director alone
commercial,              > threshold T    → Director + second officer, evidence required
financial commitment,    any              → per banking mandate, evidence required
public institutional     commitment       → Director alone, ratified into history
```

This is what lets Powerfarm's constitution and ordinary law meet without either pretending the
other does not exist.

---

## 4. The commitment lifecycle

An institutional commitment, in full:

```
  Requested        someone proposes Powerfarm enter an agreement
       ↓
  Authorized       Rules decide; review where the mandate requires it
       ↓           Act records: authorization chain, mandate hash, rule hashes,
       ↓                        external-authority predicate that must be met
  Dispatched       Dan signs in the world  (system-internal fact: "we handed this out")
       ↓
  Observed         countersigned instrument observed, with evidence:
       ↓                        document content hash, counterparty, external-authority
       ↓                        evidence (board resolution, second signature)
       ↓           observation carries its observer Identity (§11.1)
       ↓
  In force         Committed-as-external-fact
       ↓
  Obligations      typed Relations from the agreement object to what Powerfarm now owes
```

`DispatchFailed` and `EffectRetried` are first-class (§11.2) — a negotiation that collapses after
signature leaves a complete trajectory, not a gap.

What Powerfarm then knows, and can explain:

```
Agreement (content hash)
  ├─ party:              Powerfarm Ltd  (organization Identity)
  ├─ represented by:     Dan, as Director at cut C
  ├─ authorized under:   director.mandate boundary + policy version
  ├─ internal chain:     Command → Rules → Decision → Act
  ├─ external evidence:  what corporate authority was required and how it was met
  ├─ approvals:          review Acts, if the mandate required them
  └─ obligations:        typed Relations to deliverables and commitments
```

**The ledger is not replacing contract law.** It is making the institution able to answer *why it
entered this, who had authority, and what it undertook* — which is a question most companies
cannot answer at all, and which no PDF archive answers.

---

## 5. Standing behind the work

The accountability chain, with its last arrow given a real target:

```
institutional intent → authorized Command → Rules/Decision → Act
     → execution → evidence/provenance → delivered product → organization Identity
```

Three design consequences.

**5.1 Acceptance is an Act.** Acknowledging a failure, issuing a responsible disclosure, accepting
an obligation arising from harm — these are ordinary Acts against the organization Identity, with
the Director as performer. Registered vocabulary, not a new primitive.

**5.2 Append-only means acceptance is irrevocable.** SL-1 does real work here: an accepted
obligation cannot be quietly withdrawn. A later correction is a *new* Act that remains beside the
original, never a replacement for it. This is what makes the promise credible rather than
decorative — the institution cannot un-say what it said.

**5.3 The provenance chain must not be severable.** The delivered artifact relates to the Acts that
produced it and to the organization that stands behind it. If the chain can be broken by deleting a
projection, the promise is only as strong as an index. It cannot be: projections are disposable,
history is not (§14). The relation from artifact to organization must be an **admitted Relation**,
which is precisely why Phase 0a's `relations.admitted_act` matters more than it looked.

---

## 6. Root gains a prohibition

Your formulation is sharper than what draft 0.1 says, and I'd write it in:

> Root constitutes. Director represents. Powerfarm records what its authorized representatives and
> systems actually did.

So CR-3 gains an explicit clause: **Root holds no external representation capacity whatsoever, at
any time, including before `GenesisClosed`.** Root cannot sit at a table, sign anything, or speak
for the institution. This is not merely "Root is spent after Genesis" — Root never had this power
to spend.

After Genesis, the world encounters Powerfarm and its Director. Root is a founding fact, not a
counterparty.

---

## 7. What I would flag honestly

Three things a careful colleague raises before you build this, not after.

**7.1 The ledger creates evidence against Powerfarm too.** An institution that records "we
authorized this, here is who decided, here is what we knew at the time" has built a discovery
target. When something goes wrong, the same chain that proves diligence also proves what was known
and when. That is the actual price of the promise. It is worth paying — an institution unwilling to
be held to its own record is not making the promise at all — but it should be a conscious choice
ratified with counsel, not a property discovered during litigation.

**7.2 "Accepting consequences" needs capital behind it.** The philosophical claim is only as real as
the entity's ability to bear the obligation: insurance, reserves, contractual limitation of
liability, and the corporate form itself. Powerfarm can *represent* accountability perfectly and
still be unable to *honour* it. That is a legal and financial design problem, not a ledger design
problem, and it needs actual professional advice — I can design how Powerfarm records the
arrangement, not what the arrangement should be.

**7.3 Do not let the ledger overclaim.** The single most damaging failure mode here would be a
Powerfarm Act that reads as though it establishes legal validity. Every externally consequential
Act should be phrased so that it asserts only what Powerfarm can know: *we authorized this, this
representative acted, this evidence was observed.* Never *this agreement is valid.* Validity is the
world's judgment, not Powerfarm's. §11.1's "observations with provenance, not infallible truth"
covers this exactly — apply it strictly to institutional facts, not just sensor readings.

---

## 8. Amendments to Genesis Constitution draft 0.1

Precise diffs. Everything below is additive; nothing already drafted is overturned.

| Part | Change |
|---|---|
| **New Part XI — External Representation** | §§3–5 of this document: the internal/external distinction, CR-7 dual authority, the commitment lifecycle, standing behind the work |
| **Part III** | Add **CR-7 dual-authority** (§3). Amend **CR-3** with the Root external-capacity prohibition (§6) |
| **Part IV.2** | Root mandate gains explicit exclusion: no external representation, ever |
| **Part V.2** | Director mandate gains **External Representation** as a power category: sign agreements; represent Powerfarm to universities, laboratories, governments, standards bodies; attend events as Director; hire and contract; enter collaborations; make public commitments; commission work; acknowledge failure; sign disclosures; accept obligations |
| **Part V.3** | Mandate *detail* gains the external-authority predicate table (domain × threshold → required external authority) |
| **Part V.4** | Delegation: external representation is delegable **only** by explicit domain and threshold, never wholesale. "Represent Powerfarm" is not a grantable unit |
| **Part VIII** | Register: `organization` identity usage; `represented_by` relation type; external-effect phase Act types (`Dispatched`, `Observed`, `DispatchFailed`, `EffectRetried`, `CommittedAsExternalFact`); commitment/obligation vocabulary; acceptance Act types |
| **Part IX** | Bind a **second Genesis Identity: Powerfarm the organization** (kind `organization`), alongside Root and Dan-as-Director |
| **Part X** | Clarify: external-authority predicates and commitment vocabulary are ordinary, not constitutional — they must track real corporate arrangements |

### New open decisions

| ID | Decision | Notes |
|---|---|---|
| **A-9** | Is the organization Identity Genesis-born, or created by the first Director act? | Genesis-born is symmetric with Root and Director, and avoids a window where Powerfarm can act but not be a party. Recommend Genesis-born |
| **A-10** | Does the legal entity exist yet, and under which jurisdiction? | Determines what the external-authority predicates can reference. Currently unknown — **halt** |
| **A-11** | Are public commitments ratified into history by default, or by explicit act? | Recommend explicit: not every statement at a conference should become an institutional obligation |
| **A-12** | Does Powerfarm publish any part of this chain to counterparties? | A counterparty-verifiable authorization proof is a genuine product differentiator, and a disclosure-profile question (Phase 8) |

---

## 9. Why this belongs near the heart

The Director office in draft 0.1 was justified functionally: someone must operate the institution
after Root is spent. That is true and thin.

The real justification is the one you gave. An institution that produces consequential work must be
able to stand in the world and say *that was ours, we authorized it, here is the evidence, here is
who represented us, and we accept what follows.* The constitutional machinery — Identity, Rules,
Acts, provenance, append-only history — exists to make each clause of that sentence checkable
rather than rhetorical.

Which means the Director is not an administrator the software happens to need. **The Director is
the point at which Powerfarm becomes answerable.** Every other part of the constitution is
infrastructure for that sentence being true.

I would put §§3–6 of this document at Part V, immediately after the office is established, rather
than at Part XI. The external dimension is not an extension of the office. It is what the office is
for.
