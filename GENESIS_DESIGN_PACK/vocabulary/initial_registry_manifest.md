# Part VIII — Initial Registry Definitions

Complete enumeration with canonical schemas, for Genesis Constitution draft 0.2.

Design document. No code, migrations, or commits.

**Baseline recomputed:** 55 definitions currently in `registry_seed_manifest` — 21 `act_type`,
12 `relation_type`, 9 `context_type`, 8 `command_type`, 4 `projector`, 1 `rule`. **All are
name/version shells** carrying only `{"kind","name","version"}`. None has a schema.

Because Genesis has never run, nothing here is a re-issue. Every definition is born at `v1`, with
its schema, once.

---

## 1. Conventions

**Schema language.** JSON Schema draft 2020-12, restricted to a decidable subset: `type`,
`properties`, `required`, `additionalProperties: false`, `enum`, `pattern`, `minimum`/`maximum`,
`items`. No `$ref` to external documents, no `oneOf` chains deeper than one level. The Rule engine's
static type checker must be able to decide `(payload "/json/pointer")` types without evaluation.

**Hash pattern.** `^[0-9a-f]{64}$` throughout. Every cross-reference between definitions is by
content hash, never by name (SL-2).

**Definition object shape.** Beyond `{kind, name, version}`, each definition carries:

```
command_type   →  payload_schema
context_type   →  value_schema
act_type       →  payload_schema  (the shape the resulting Act's payload must satisfy)
relation_type  →  payload_schema (nullable), lineage: bool, endpoint_kinds
rule           →  context_keys[], applicability[] (definition hashes), body or procedural marker
office         →  mandate_kinds[], min_holders, max_holders
mandate        →  powers[], delegation_depth, external_predicates_ref
projector      →  inputs[], deterministic: true
```

**`additionalProperties: false` everywhere.** A payload with unexpected fields must fail
registration-time validation, not pass silently. This is the cheapest defence against vocabulary
drift.

**Naming.** `PascalCase` for command and act types; `snake_case` for relation types; dotted
lowercase for context types, rules and projectors.

---

## 2. The design result worth stating first

Working through external representation produced a **smaller** constitutional surface than
expected, not a larger one.

Signing an agreement, hiring a maintainer, entering a research collaboration, making a public
commitment, accepting an obligation, acknowledging a failure, issuing a responsible disclosure —
**all of these are the same thing**: an external effect passing through the §11.2 phases. They
differ only in `effect_kind`, which is *ordinary* vocabulary.

So the constitution needs **one** generic external-effect protocol, not one vocabulary per kind of
institutional act. Four commands and six act types cover every external commitment Powerfarm will
ever make. Everything domain-specific stays ordinary and registrable without amendment.

This is the "small constitution, huge universe" vector doing real work.

---

## 3. Constitutional Rules — `kind=rule` (7)

| Name | Context keys read | Applies to |
|---|---|---|
| `declared-decision-cut` | `delegation.cut`, `time.claimed` | every consequential command type |
| `amendment-or-fork` | `authority.grants` | every command touching a constitutional definition |
| `root-mandate` | `authority.grants`, `request.performed_by` | every command type |
| `director-mandate-boundary` | `authority.grants`, `request.performed_by`, `request.requested_by` | every command type |
| `director-succession` | `authority.grants`, `review.acts` | `NominateDirector`, `GrantAuthority`, `RevokeAuthority` |
| `no-self-extension` | `authority.grants` | `GrantAuthority`, `RegisterDefinition`, `ProposeAmendment` |
| `dual-authority` | `authority.grants`, `external.authority_evidence` | `DispatchExternalEffect`, `ClaimExternalFact` |

**Applicability is by definition hash, frozen at registration** — future vocabulary does not
silently enter an old Rule's applicability set. `declared-decision-cut`, `root-mandate` and
`director-mandate-boundary` apply to *every* command type, so their applicability sets enumerate
every constitutional command hash and must be re-frozen by amendment if the set grows.

`genesis.root_authority` (currently the only seeded rule) is **superseded** by `root-mandate`,
which does the same job with an explicit exhaustion clause. Do not seed both.

---

## 4. Constitutional command types — `kind=command_type`

### 4.1 Retained from current seed (7 of 8, with schemas)

| Name | `payload_schema` |
|---|---|
| `RegisterDefinition` | `{kind: enum[...], name: string, version: int≥1, constitutional: bool, definition_hash: hash, schema_hash: hash∣null}` |
| `CreateIdentity` | `{identity_kind: enum[human,organization,service,machine,application,workflow,agent,model,scheduler,integration,device,reviewer], public_keys: [string], attributes_hash: hash∣null}` |
| `RotateKey` | `{identity_hash: hash, add_keys: [string], retire_keys: [string], grace_until_act: hash∣null}` |
| `ReviewAuthorization` | `{reviewed_command_hash: hash, verdict: enum[approve,reject], reason: string}` |
| `LinkPrincipal` | `{issuer: string, subject: string, identity_hash: hash}` |
| `RevokePrincipal` | `{issuer: string, subject: string, reason: string}` |
| `AdmitObservation` | `{observed_effect_hash: hash, observer_identity_hash: hash, evidence_hashes: [hash] (min 1), observation_hash: hash, reported_at: string}` |

**`SubmitCommand` is dropped.** It is a protocol verb, not a governed command type — the MCP
boundary already carries submission, and registering it invites the reading that submission is
itself a governed change. Flagged for your ruling (§10, R-1).

### 4.2 Authority and office (4 new)

| Name | `payload_schema` |
|---|---|
| `GrantAuthority` | `{grantee_identity_hash: hash, office_hash: hash, mandate_hash: hash, on_behalf_of: hash∣null, powers: [string]∣null, delegation_depth: int≥0, expires_at_act: hash∣null, reason: string}` |
| `RevokeAuthority` | `{grant_act_hash: hash, reason: enum[succession,delegation_ended,misconduct,expired,voluntary], effective_immediately: bool}` |
| `AppointReviewer` | `{reviewer_identity_hash: hash, remit: [hash], quorum_role: enum[ordinary,constitutional], expires_at_act: hash∣null}` |
| `NominateDirector` | `{nominee_identity_hash: hash, mandate_hash: hash, statement: string}` |

Three design points:

- **`on_behalf_of` is what makes representation a grant rather than a new concept.** When null, the
  grant confers internal Powerfarm authority. When it names an organization Identity, the grant is a
  representation mandate. One command type covers both.
- **`powers` null means "the full mandate"**; a non-null list must be a strict subset, verified by
  `no-self-extension` against the grantor's own grant at the cut.
- **`delegation_depth` on the grant, not the mandate**, so a Director can issue a depth-0 delegation
  from a depth-1 mandate but never the reverse.

### 4.3 Amendment (3 new)

| Name | `payload_schema` |
|---|---|
| `ProposeAmendment` | `{target_definition_hash: hash, replacement_definition_hash: hash, rationale: string, eternity_clause_check: bool}` |
| `ObjectToAmendment` | `{proposal_act_hash: hash, grounds: string}` |
| `EnactAmendment` | `{proposal_act_hash: hash, approval_act_hashes: [hash], delay_satisfied_at_cut: [hash]}` |

`eternity_clause_check` is not a permission flag — it is the proposer asserting they have checked
the target is amendable. `amendment-or-fork` verifies it independently and denies regardless of what
the flag says. It exists so that a proposal against an eternity clause is a *recorded refusal*
rather than a silent rejection.

### 4.4 External effects (4 new)

Generic over `effect_kind`. This is the whole external surface.

| Name | `payload_schema` |
|---|---|
| `ProposeExternalEffect` | `{effect_kind_hash: hash, on_behalf_of: hash, subject_hash: hash, domain: string, threshold_value: string∣null, threshold_unit: string∣null, counterparty_ref: string∣null, summary: string}` |
| `DispatchExternalEffect` | `{effect_request_act_hash: hash, performed_by_identity_hash: hash, external_authority_evidence: [hash], dispatched_content_hash: hash}` |
| `ClaimExternalFact` | `{effect_request_act_hash: hash, observation_act_hashes: [hash] (min 1), claimed_content_hash: hash, obligations: [hash], claim_statement: string}` |
| `AdmitObservation` | (§4.1 — serves the Observed phase) |

`threshold_value` is a **string**, not a number: §10.1 warns that floats are treacherous and that
money should use integer minor units or strings. A contract value must never lose precision in
canonicalization.

`external_authority_evidence` is required by `dual-authority` (CR-7) and may be an empty array only
when the applicable predicate declares none is required.

---

## 5. Constitutional act types — `kind=act_type`

### 5.1 Retained (21, with schemas)

Genesis (5): `GenesisCreated`, `RegistryCreated`, `RootIdentityCreated`, `RootAuthorityGranted`,
`GenesisClosed` — payload `{config_hash: hash}`.

Command lifecycle (10): `CommandSubmitted`, `CommandValidated`, `CommandRejected`,
`AuthorizationRequested`, `CommandDenied`, `ReviewRequested`, `AuthorizationReviewed`,
`AuthorizationResolved`, `CommandSuperseded`, `CommandExpired` — payload
`{command_hash: hash, reason: string}`. **These ten are exactly the set excluded from
`acts_one_consequence_per_command_idx`**; the enumeration and the index must not drift apart.

Consequential (6): `DefinitionRegistered`, `IdentityCreated`, `KeyRotated`, `PrincipalLinked`,
`PrincipalRevoked`, `ObservationAdmitted` — payload mirrors the originating command.

### 5.2 New (9)

| Name | Phase / role |
|---|---|
| `AuthorityGranted` | consequence of `GrantAuthority` |
| `AuthorityRevoked` | consequence of `RevokeAuthority` |
| `ReviewerAppointed` | consequence of `AppointReviewer` |
| `DirectorNominated` | succession step |
| `AmendmentProposed` | amendment step |
| `AmendmentObjected` | amendment step |
| `AmendmentEnacted` | consequence; births a new constitutional definition version |
| `ExternalEffectRequested` | §11.2 **Requested** |
| `ExternalEffectAuthorized` | §11.2 **Authorized** |
| `ExternalEffectDispatched` | §11.2 **Dispatched** — system-internal fact |
| `ExternalEffectDispatchFailed` | §11.2 failure phase |
| `ExternalEffectRetried` | §11.2 retry phase |
| `ExternalFactClaimed` | §11.2 final phase, claimed semantics (§10 R-2) |

(That is 13 rows; `ObservationAdmitted` already exists and serves the **Observed** phase, so the
five-phase protocol needs six *new* types plus two failure types.)

**Succession needs no dedicated act types beyond `DirectorNominated`** — it completes through
`AuthorityGranted` and `AuthorityRevoked`. **Acceptance, disclosure and failure acknowledgement need
none at all** — they are external effects with distinct `effect_kind`.

---

## 6. Constitutional relation types — `kind=relation_type`

### 6.1 Retained (12)

`caused_by`, `authorized_by`, `reviewed_by`, `derived_from`, `forked_from`, `simulated_from`,
`crafted_from`, `supports`, `contradicts`, `matched_to`, `anchored_at`, `notarized_by`.

Each gains `lineage: bool` (per the pack's AdmitBatch step 8) and `endpoint_kinds`. `derived_from`,
`forked_from`, `simulated_from`, `crafted_from` are `lineage: true`; the rest false.

### 6.2 New (6)

| Name | From → To | `lineage` | Purpose |
|---|---|---|---|
| `holds_office` | identity → office | false | office tenancy, admitted by the grant Act |
| `represented_by` | organization → identity | false | who may act for this legal person |
| `delegated_from` | grant → grant | true | delegation provenance; §12 names it |
| `supersedes` | object → object | true | §12 names it and it is **not currently seeded**; corrections-by-new-Act need it |
| `evidenced_by` | act → object | false | binds a claimed fact to its evidence |
| `stands_behind` | organization → object | false | **the last arrow of the accountability chain** |

`stands_behind` is the relation that makes V.7 checkable. Without it, "Powerfarm stands behind this
result" is a sentence in a document rather than an admitted fact in history. It is also why Phase
0a's `relations.admitted_act` matters more than it appeared: an unadmitted relation cannot carry an
institutional commitment.

---

## 7. Constitutional context types — `kind=context_type`

### 7.1 Retained (9, with `value_schema`)

| Name | `value_schema` |
|---|---|
| `request.origin` | `{type: string, address: string∣null}` |
| `request.metadata` | `{object, additionalProperties: true}` — the one deliberate exception |
| `review.acts` | `{acts: [hash]}` |
| `delegation.cut` | `{cut: [hash]}` |
| `time.claimed` | `{claimed_when: string (RFC 3339)}` |
| `request.requested_by` | `{identity_hash: hash}` |
| `request.performed_by` | `{identity_hash: hash}` |
| `request.requester_kind` | `{kind: enum[human,service,agent,...]}` |
| `request.oauth_client` | `{client_id: string}` |

### 7.2 New (3)

| Name | `value_schema` | Read by |
|---|---|---|
| `authority.grants` | `{grants: [{grant_act: hash, grantee: hash, office: hash, mandate: hash, on_behalf_of: hash∣null, powers: [string]∣null, depth: int}]}` | every mandate Rule |
| `external.authority_evidence` | `{predicate_ref: string, evidence: [{hash: hash, kind: string, described_as: string}], satisfied: bool}` | `dual-authority` |
| `amendment.state` | `{proposal_act: hash, approvals: [hash], objections: [hash], proposed_at_cut: [hash]}` | `amendment-or-fork` |

`authority.grants` is resolved by the service from admitted history and **must be refused when a
caller supplies it** — the same discipline `20260816150000` applied to `request.requested_by`. A
body claiming its own grants is the most obvious privilege-escalation path in the whole design.

---

## 8. Offices, mandates, projectors

### 8.1 `kind=office` (1)

`powerfarm.director` — `{mandate_kinds: [hash], min_holders: 1, max_holders: 2, succession_rule: hash, recovery_rule: hash∣null}` `[A-2]` `[A-1]`

### 8.2 `kind=mandate` (2)

- `director.mandate.boundary.v1` — constitutional. `{powers: [...], prohibitions: [...], delegation_depth_max: int, policy_ref: hash}` `[A-4]`
- `root.mandate.v1` — constitutional, exhaustive, with the exhaustion clause and the
  no-external-representation-authority clause (IV.4).

The mandate **policy** object that `policy_ref` points at is **ordinary** and is not seeded at
Genesis beyond an initial version — this is what lets external-authority predicates arrive after
incorporation. `[A-10]`

### 8.3 `kind=projector` (4 retained + 3 new)

Retained: `causal.topological`, `registry.current`, `identity_keys.at_cut`, `trajectory.graph`.

New: `authority.active_grants`, `office.holders`, `external.commitments` — each
`{inputs: [act_type hashes], deterministic: true}`.

All projections are disposable and rebuildable (§14). None is authoritative.

---

## 9. Delta summary

| Kind | Now | Genesis | Change |
|---|---|---|---|
| `command_type` | 8 | 18 | +11 new, −1 (`SubmitCommand`) |
| `act_type` | 21 | 34 | +13 |
| `relation_type` | 12 | 18 | +6 |
| `context_type` | 9 | 12 | +3 |
| `rule` | 1 | 7 | +7, −1 (`genesis.root_authority` superseded) |
| `office` | 0 | 1 | +1 |
| `mandate` | 0 | 2 | +2 |
| `projector` | 4 | 7 | +3 |
| **Total** | **55** | **99** | **+46, −2** |

Plus **all 55 existing definitions gain canonical schemas**, which is the larger part of the work
and the part with the worst late-failure mode.

---

## 10. Rulings needed

| ID | Question | Recommendation |
|---|---|---|
| **R-1** | Drop `SubmitCommand`? | **Drop.** A protocol verb, not a governed change |
| **R-2** | Final external phase Act type name | **`ExternalFactClaimed`.** Keep PF-24's phase taxonomy for conformance; name the vocabulary honestly so it cannot be read as asserting validity |
| **R-3** | Supersede `genesis.root_authority` with `root-mandate`? | **Yes.** Same job, explicit exhaustion. Seeding both creates two root paths |
| **R-4** | Is `request.metadata` genuinely open (`additionalProperties: true`)? | **Yes, but never Rule-readable.** An open-shaped context key a Rule can read defeats static type checking |
| **R-5** | Should `effect_kind` definitions be seeded at Genesis? | **No.** Ordinary. Seed only the generic protocol; seeding kinds now freezes what Powerfarm can commit to |
| **R-6** | Do the ten lifecycle act types need to match the partial index literally? | **Yes** — and the enumeration should be generated from one source, or they will drift |
| **R-7** | `authority.grants` refused when caller-supplied? | **Yes**, same as `request.requested_by` |

---

## 11. What is deliberately not seeded

Node species; disclosure profiles; machinery classes; budget vocabulary; `AdmitBatch` and batch
manifests; publication vocabulary; ADK/Engine vocabulary; `effect_kind` definitions; additional
organization Identities; external-authority predicate instances; every ordinary Rule.

All are registrable post-Genesis through `RegisterDefinition` under the Director mandate, without
amendment. **That is the test of whether this constitution is the right size** — if any of the above
turns out to need Genesis, the boundary was drawn wrong.

---

## 12. Open dependencies

1. **R-1 … R-7** above.
2. Schema bodies for the 55 retained definitions — this document gives shapes for the ones that
   Rules will read; the remainder need a line-by-line pass.
3. `[A-1]`, `[A-2]`, `[A-4]`, `[A-10]` feed directly into §8.
4. The lifecycle-act-type list must be reconciled with
   `acts_one_consequence_per_command_idx` (R-6) before either is frozen.
