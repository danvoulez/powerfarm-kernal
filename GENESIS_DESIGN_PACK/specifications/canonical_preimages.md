# Canonical Preimages — the frozen four

**Status: FROZEN (R-26). Free before `GenesisClosed`, impossible after.**

These four change content hashes. They are not implementation TODOs that can be sequenced behind
Phase 0 — they are shape decisions on content identity, and content identity is the one thing
Genesis makes permanent. Ratify them alongside `genesis.yaml`, not after it.

---

## 1. `Relation.relation_type` → `relation_type_hash`

**Today:** [kernel/types.py:134-143](../../kernel/types.py) hashes the relation type as a **string**:

```python
object_hash("relation", {"from": …, "payload": …, "relation_type": self.relation_type, "to": …})
```

**Required:** the Relation binds its exact registered `relation_type` definition by content hash.

**Why it matters (R-15R):** this is what makes provenance semantics immutable without freezing
provenance *vocabulary*. A later `simulated_from.v2` cannot retroactively alter what a historical
Relation meant, because the old Relation points at the old definition hash. Freezing relation
*names* instead would be a whitelist that is incomplete by construction — spec §24 already names
five lineage relations, two of which (`mutated_from`, `spliced_from`) are not even seeded.

**Already specified:** `02_Powerfarm_Micro_Specs_v1.1.md:243-273` requires `relation_type_hash`,
states that `display_relation_type` never determines meaning, and derives `"lineage": true` from the
registered definition. The implementation has not caught up.

---

## 2. `Context.types` → definition hashes, not names

**Today:** [kernel/types.py:74](../../kernel/types.py) is `types: Mapping[str, str]`, and the
service supplies each key's own name as its type. [kernel/commit.py:90-94](../../kernel/commit.py)
validates by calling `registered("context_type", key, registry_cut)` — a **name** lookup, and
`registered()` is boolean-any-version.

`Context.canonical_value()` includes `types`, so this is inside the Context hash and therefore
inside every Act hash.

**Required (R-18R):** every context key a Rule reads is bound at the Rule's birth to the exact
`context_type` definition hash and schema it was type-checked against, and the admitted Context
records that hash.

**Why it matters:** without it, a later context-type version can reinterpret a historical Rule
evaluation. It is the same disease as (1), one layer up — and the same medicine: pin semantics, do
not freeze names. It also means an *ordinary* context type may evolve freely without changing what
an immutable constitutional Rule saw.

---

## 3. Act preimage gains `validity_rule_hash` and `validity_disposition`

**Today:** the preimage is `act_type`, `auth_chain`, `claimed_when`, `command_hash`, `context_hash`,
`decision_cut`, `identity_hash`, `parents`, `payload_hash`, `registry_cut`, `rule_hashes`.

**Required (R-22):** two additional fields, because authorization and decision-validity are
**distinct typed domains**:

```
authorization disposition     : allow | deny | require_review
decision-validity disposition : VALID | REAUTHORIZE | COMMIT_REGARDLESS
```

`declared-decision-cut` produces the latter and must never be smuggled through the former.
`rule_hashes` stays purely authorization; the validity decision gets its own attribution.

**Why it matters:** without it, either CR-1's decision is unattributable (the present state — a
constant decides, and nothing records that it did), or `deny` is overloaded to mean "reauthorize",
which conflates two different questions and will break when survival rung 1 arrives.

---

## 4. `created_at` → `claimed_when` where it is a hashed content assertion

**Required (R-13), qualified — three clocks, not one rename:**

| Clock | Meaning | Hashed? | Causal evidence? |
|---|---|---|---|
| `claimed_when` | content assertion — what the object claims | **yes** | no |
| causal ancestry | constitutional ordering (§10.2) | via parents | **yes** |
| `created_at` / `materialized_at` | operational DB/projection timestamp | no | **never** |

Research Scheme §27's field sits inside the canonical hashed payload, which makes it a content
assertion — therefore `claimed_when`. Projection rows in `proj_nodes` keep `created_at`, explicitly
operational.

**Why it matters:** §10.3 requires the Kernel to name claimed time `claimed_when` precisely because
*"a bare `when` invites reading it as causal order or as provable knowledge time"* — the two ideas
that section exists to keep apart.

---

## What does *not* require a preimage change

Confirmed during the ADK 2.7 absorption: **execution provenance needs no universal Act field.**

`engine_definition_hash`, `execution_plan_hash`, evidence hashes and the rest are **payload
content**, already bound by `payload_hash`. And where execution provenance should be *structurally
required* rather than conventional, the companion contract (R-24) is the right mechanism — it
enforces at the registry cut without touching content identity.

This is what keeps the universal Act format able to govern Google ADK, mistral-rs, an A2A remote
agent, a human procedure and a laboratory robot **without changing Act physics**.
