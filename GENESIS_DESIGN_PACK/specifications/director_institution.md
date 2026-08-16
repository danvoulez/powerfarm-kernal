# Powerfarm Director — Institutional Design

Design document, pre-Genesis. Not implementation. No code, migrations, or database mutations.

Frame: **we are designing the universe, not auditing a finished one.** Findings are classified as
design decision / implementation TODO / design contradiction / post-Genesis hazard.

---

## 0. Reclassification of prior findings

| Finding | Old label | Correct label |
|---|---|---|
| Genesis not materialized | constitutional blocker | **Implementation TODO** |
| Registry empty, no promoter | constitutional blocker | **Implementation TODO** |
| `CreateIdentity` / `RegisterDefinition` no runtime | implementation defect | **Implementation TODO** |
| §17 authority vocabulary unregistered | implementation defect | **Implementation TODO** |
| Dan absent from history | executive finding | **Implementation TODO** (history does not exist yet) |
| `relations` / `identity_links` no writer | implementation defect | **Implementation TODO** |
| Bootstrap recursion (`RegisterDefinition` needs Registry) | constitutional blocker | **Design decision** — it forces Genesis to be the unique membrane, which is a property to design around, not a defect |
| Retired `genesis.yaml` omitted §16 bindings | constitutional blocker | **Resolved in form** — the content-bound Genesis manifest carries the bindings; real values remain subject to ratification |
| `amendment-or-fork` has no content | constitutional blocker, urgent | **Design decision** — no ticking clock except one created by ratifying prematurely |
| `declared-decision-cut` unmaterialized, enforcement hardcoded | implementation defect | **Implementation TODO**, with a **design decision** on attribution shape |
| `POWERFARM_ROOT_IDENTITY_HASH` determines authority | constitutional blocker | **Post-Genesis hazard** — fine as ceremony input; unacceptable if it still determines authority after `GenesisClosed` |
| Whole-history `history_cut` serialization | implementation defect | **Design decision** (drift-relevance semantics) |
| Golden Bridge unverifiable | missing evidence | unchanged — **missing evidence** |

The sharper test you named, applied: *does mutable configuration remain authoritative after
Genesis?* Today, structurally yes — `ConfiguredRuleResolver` rebuilds
`RootAuthorityRule(entry.hash, self._root_identity_hash)` from the environment on **every**
resolve, at any cut ([service/authority.py:104-107](../../service/authority.py)). So changing the
variable changes authority for all future decisions. That is the actual hazard, and it is a
statement about the *post-Genesis* reading path, not about the existence of an env var.

**Design requirement (not a defect report):** after `GenesisClosed`, Root identity must be read
from admitted history — the Genesis Act that binds it — never from configuration. The environment
variable is legitimate ceremony input and must become inert at the moment Genesis closes.

---

## 1. What the office is for

Powerfarm needs two institutions, and the cleanest design makes their mandates **disjoint rather
than nested**:

> **Root constitutes. Director operates. Neither is a superset of the other.**

Root's mandate is exhausted by the act of founding: bind the constitution, seed initial
vocabulary, establish the offices, install the initial holders. Director's mandate is everything
ongoing: grow the universe, appoint operational authority, direct trajectories, approve
publication.

This is the design choice that makes Director a real institution rather than a delegation. If
Root retains a general power to appoint and remove Directors at will, then Director is revocable
convenience and Root is a permanent throne — and Powerfarm has a sovereign who never has to
justify anything. Disjoint mandates avoid that by construction: after Genesis, **Root has no
operational powers to exercise, and Director has no constitutive powers to abuse.**

A consequence worth stating early, because it drives several later answers:

> **If succession requires Root, Root must remain alive forever.** Making succession
> self-governing is what allows Root to be spent.

---

## 2. Powers

### 2.1 Intrinsic to the office (exercised by the holder personally)

- Register **ordinary** vocabulary: command types, act types, relation types, context types, node
  species, disclosure profiles, projectors
- Register and version **ordinary** Rules
- Create Identities (human, service, agent, machine) — creation is not authorization (§5)
- Grant, scope and revoke **operational** authority to other Identities
- Appoint **ordinary** reviewers
- Approve budget ceilings and publication policy
- Nominate a successor Director

### 2.2 Delegable

- Operational execution: running trajectories, admitting batches, spending within an approved
  ceiling
- Registering ordinary vocabulary within a declared namespace
- Provisioning Identities (the pack's provisioner: may propose `CreateIdentity` and `LinkPrincipal`,
  may never grant authority)
- Reviewing ordinary authorizations

### 2.3 Reserved — non-delegable

- **Enlarging the Director mandate.** The single most important constraint. An office that can
  extend its own powers is unbounded in one step.
- **Granting the power to grant.** Delegation depth is a mandate parameter, default `0`. Without
  this, authority fans out uncontrollably and revocation becomes unprovable.
- Nominating a successor
- Revoking another Director's grant
- Selecting, suppressing, or rewriting the required Constitutional Advisor record

### 2.4 Forbidden to the office entirely

- Amending or reinterpreting constitutional definitions
- Altering Genesis or claiming Root authority
- Rewriting, deleting, or reordering history
- Acting outside the mandate in force at the declared cut

### 2.5 The self-extension invariant

> **D-Director-01.** No exercise of Director authority may increase the powers of the Director
> office, extend delegation depth beyond the mandate's declared maximum, or control a required
> advisory record about its own actions. Any Command whose effect is to enlarge the mandate must
> route through the constitutional amendment protocol, where proposal is distinct from the single
> accountable human's ratification.

The permanent Constitutional Advisor supplies mandatory, attributable analysis and no vote. The
exact premium frontier model is selected by policy and pinned per opinion; the human decision
remains the authorization.

---

## 3. Mandate: constitutional in structure, ordinary in detail

Resolving the freeze problem properly. Three layers, governed differently:

| Layer | Example | Governance | Changeable how |
|---|---|---|---|
| **Office existence** | "There is an office, Director" | Constitutional, Genesis-born | Amendment or fork |
| **Mandate boundary** | "Director may register ordinary vocabulary, appoint operational authority, approve budgets; may not amend the constitution, grant Root, or self-extend" | Constitutional, Genesis-born | Amendment or fork |
| **Mandate detail** | which namespaces, which ceilings, delegation depth, operational review policy | Ordinary registered Rules + a versioned policy object | Governed Act, no fork |
| **Holder** | Dan | Governed history (Genesis-born initial holder, then succession Acts) | Ordinary succession |

So `DirectorMandate.v1` splits: the **boundary** is constitutional and stable; the **policy** it
points at is ordinary and versions freely. The office cannot outgrow its constitutional envelope,
but it can be tuned without touching the constitution.

This is the ordinary shape of a constitution: powers enumerated at the constitutional layer,
details legislated below it.

---

## 4. Appointment — Dan is Genesis-born

**Recommendation: Genesis binds the office, the mandate boundary, the succession rule, and Dan as
initial holder.**

The argument is the same bootstrap recursion you already identified for the Registry, and it
generalizes:

> An ordinary appointment Act requires registered `GrantAuthority` vocabulary, a registered Rule
> to authorize it, and an Identity already holding authority to grant. Pre-Genesis, none of these
> exist. So the *first* appointment cannot be an ordinary Act, for exactly the reason
> `RegisterDefinition` cannot register itself.

Genesis is the unique membrane for both. Trying to make the first appointment ordinary produces
one of two bad outcomes: the universe boots headless and needs Root alive to fix it (resurrecting
the permanent throne), or Root's mandate must include a general appointment power (defeating
disjointness).

Binding Dan at Genesis is also *symmetric with what Genesis already must do*: §16 requires Genesis
to bind Root Identity and its initial keys. Binding Director Identity and the initial office
holder is the same kind of act, no more exotic.

**What is Genesis-born is "Dan is the initial holder," not "Dan is Director forever."** From the
first succession onward, the holder is governed history. That is precisely the distinction I
collapsed earlier.

---

## 5. Succession, cardinality, continuity

### 5.1 Cardinality

The mandate declares `min_holders` and `max_holders`. Recommendation: `min = 1`, `max = 2`.

- **Zero is forbidden.** A headless universe cannot appoint its way out if succession requires a
  sitting Director — that is a deadlock, not a state.
- **Two is permitted specifically to make handover safe.** Overlap means succession never passes
  through zero: the successor is admitted, both hold briefly, the predecessor's grant is revoked.
- Beyond two, "which Director authorized this" is still attributable per Act, so higher `max` is a
  policy question, not a structural one.

### 5.2 Succession mechanism

A Genesis-born constitutional Rule, **not** dependent on Root:

```
Sitting Director nominates            -> DirectorNominated
   + permanent Constitutional Advisor opinion is admitted
   + the accountable human ratifies
   + declared delay window elapses
   -> AuthorityGranted (successor admitted, overlap begins)
   -> AuthorityRevoked (predecessor's grant closed)
```

The delay window, one-human ratification and required non-binding advisory record are
constitutional. Model, provider and infrastructure profiles are governed replaceable instruments.

### 5.3 The loss case — the one genuinely hard problem

If all Directors lose their keys simultaneously, nomination is impossible. Three candidate designs,
and this is a real decision rather than a detail:

| Option | Mechanism | Cost |
|---|---|---|
| **R1** Root retained as recovery office | Root's mandate keeps exactly one power: admit a replacement Director after long delay and advisory opinion | Root never fully spent; a dormant superuser exists forever |
| **R2** Separately constituted recovery design | Real independent authority may admit a replacement under explicit Genesis-born rules | Requires actual additional humans or a lawful institution; none exists today |
| **R3** Fork | Total loss is terminal; recovery is a new Genesis linked by `forked_from` | Brutally honest, spec-legitimate (§4.2), preserves history but not continuity |

**Current candidate: R3.** It refuses to manufacture absent people. An operational key plus a cold
rotation key mitigates loss without pretending that an LLM is an independent constitutional
authority. R1 or R2 may still be chosen before Genesis.

### 5.4 Key rotation

Already solved by §5.1: `RotateKey → KeyRotated`, Identity stable across rotation, valid keys a
projection over key history. The grant references `identity_hash` and **never key material**, so
rotation cannot disturb the office. The only design obligation is negative: *do not let any grant,
relation, or rule reference a public key.*

---

## 6. Root × Director interaction

| Question | Answer |
|---|---|
| Can Root remove a Director? | **No**, post-Genesis. Removal is succession or the recovery path |
| Can Root appoint a Director? | Only the initial holder, at Genesis (and under R1, recovery) |
| Can Root exercise Director powers? | **No** — disjoint mandates. Root has no operational powers |
| Can Director claim Root authority? | **No** — forbidden by mandate boundary |
| Can Director amend the constitution? | May **propose**; never sufficient to **enact** |
| What can Director do that Root cannot? | Everything ongoing: grow vocabulary, appoint operational authority, direct trajectories, approve publication |
| What can Root do that Director cannot? | Nothing, after `GenesisClosed` — Root's mandate is spent |

> **D-Director-02 (Root/Director invariant).** Root and Director hold disjoint mandates. Root's
> mandate is exhausted at `GenesisClosed` except for any explicitly Genesis-born recovery power.
> After Genesis, Root identity is read from admitted history, never from configuration, and no
> Director power may enlarge itself or reach into the constitutive layer.

---

## 7. Advice, oversight and capture

There is one accountable human. Ordinary operational review remains ordinary policy; it must not
be misrepresented as a constitutional body. Constitutional amendment and succession instead
require a record from the permanent `powerfarm.constitutional_advisor` office.

The chair uses the current premium frontier model selected by governed capability policy. It is
mandatory, attributable and non-binding. The Director cannot select, suppress or rewrite the
required record; equally, the model and its operator cannot authorize, vote or veto. Bootstrap
infrastructure remains effective until an explicit transfer Act places routing, monitoring,
availability, receipts, security and cost under Powerfarm's internal inference-infrastructure
function.

---

## 8. Proving directorship at a historical cut

The question a later Powerfarm node must answer: *was Dan Director at cut C?*

The proof is a replay, not a lookup:

1. The admitting fact — the Genesis binding, or an `AuthorityGranted` Act — present in the
   ancestry-closed cut ≤ C, naming `grantee_identity_hash`, `office_hash`, `mandate_hash`
2. The `holds_office` Relation admitted by that Act
3. **No superseding `AuthorityRevoked` Act** anywhere in the cut ≤ C
4. The mandate definition in force at C, resolved by hash at the registry cut
5. For any specific action: the Act's own `rule_hashes` naming the Rule that evaluated the mandate

Point 3 is the load-bearing one and drives two structural requirements:

- **Revocation must be an Act, never a delete** — otherwise absence of revocation is unprovable.
  (This is the same reasoning already applied to `principal_bindings` in `20260816160000`.)
- **The cut must be ancestry-closed** (§10.2), or "no revocation exists" is a claim about an
  incomplete world.

`active_grants` is an accelerator for this replay and never the source of truth — consistent with
§14 and with the no-canonical-table ruling.

---

## 9. What Genesis must therefore bind

Derived from the institution above rather than from a checklist.

**Constitutive:**
- Root Identity + initial keys, and the rule that Root becomes inert at `GenesisClosed`
- Initial Registry definitions (canonical content, not names)
- The four declared constitutional Rules, materialized
- The amendment protocol — real content, or a conscious fork-only ratification

**Institutional:**
- The office `powerfarm.director` exists
- The mandate **boundary** (enumerated powers and prohibitions, including the self-extension
  invariant)
- `min_holders` / `max_holders`
- The succession rule (nomination + advisory opinion + one-human ratification + delay), independent of Root
- The recovery design (R1/R2/R3)
- The permanent Constitutional Advisor office, non-authority Rule, selection class and infrastructure-transfer boundary
- **Dan's Identity + keys, as initial Director**

**Deliberately left ordinary:** mandate detail and policy, all operational vocabulary, ordinary
reviewers, every subsequent holder.

---

## 10. Open design decisions

Genuinely open — competing readings, not gaps.

| ID | Decision | Competing readings |
|---|---|---|
| **D-Director-03** | Recovery from total Director loss | R1 dormant Root / **R2 constitutional quorum** / R3 fork |
| **D-Director-04** | `max_holders` | 1 (no overlap, riskier handover) / **2** (safe overlap) / N (collегial directorate) |
| **D-Director-05** | Does Director sit in the amendment quorum at all? | Propose-only *(recommended)* / propose + one vote among N / excluded entirely |
| **D-Director-06** | Is the mandate boundary one constitutional object or several? | Single `director.mandate.boundary.v1` / decomposed per power class (finer amendment granularity, larger Genesis) |
| **D-Director-07** | Delegation depth default | **0** *(recommended)* / 1 with expiry / mandate-parameterised |
| **D-Director-08** | Does Dan hold any office other than Director at Genesis? | Director only *(recommended — keeps Root/Director disjointness real)* / Dan is also Root Identity |

**D-Director-08 deserves attention.** If Dan's Identity is *also* the Root Identity, then
disjointness is nominal — the same keys hold both mandates, and "Root is spent" is a promise rather
than a structure. Binding a separate Root key, held differently (cold, or split), is what makes the
separation physical rather than declarative.

---

## 11. Next artifact

**The Genesis Constitution document** — a single design document specifying, in Powerfarm's own
vocabulary, what Genesis binds: Root, the Director office, the mandate boundary, succession,
recovery, the amendment protocol, and the initial holders.

That document is the constitutional content consumed by the Genesis material generator, expressed
as design before it is expressed as a binding. It resolves D-Director-03 through D-Director-08 and D-Genesis-03/04, and everything
downstream — the promoter, the wrapper RPC, the Registry writer, the Rule engine — becomes
implementation of a decided institution rather than scaffolding awaiting one.

Dan is the reason the document exists, so he belongs in it from the first line, not at step ten.
