# Decision Memo — Transaction Architecture and PF-13

For decisions 1 and 2 of the audit fork. No code written, no repo files modified.

These two constrain Phases 0a, 0b, 1 and 5. Everything below is grounded in the spec sections
that govern the change and in recomputed source evidence, not recall.

---

## 0. A finding that reframes both questions

While tracing the two decisions I hit the same pattern three times, and it changes what both
decisions are actually about.

**`genesis/genesis.yaml` declares four constitutional rules by name:**

```yaml
constitutional_rules:
  - append-only-acts
  - reference-by-hash
  - declared-decision-cut      # <- this is PF-13
  - amendment-or-fork
```

**None of the four exists in the Registry.** The seed manifest registers exactly one Rule,
`genesis.root_authority`. The ceremony (`genesis/ceremony.py`) binds `genesis.yaml` into
`config_hash` and emits five Acts carrying only that hash — so the four rules are
cryptographically committed at Genesis, but never materialized as content-addressed Registry
entries that an Act could cite.

**And the Registry has no writer at all.** Nothing in any migration inserts into
`public.registry`. `registry_seed_manifest` is a declaration table with no promoter. Combined
with `commit_act`'s requirement that command and act types be *registered at the declared
registry cut*, this means:

> **No consequential Act can currently commit through the Postgres path.** The 63 passing tests
> all run against `MemoryLedger`, which has its own `register()`.

That is the same defect the pack found in `relations`, and the same one your last commit fixed
for `principal_bindings`: **a table that is read but has no governed writer.** It is now
confirmed in three places. The pack treats these as separate phase items; they are one shape.

So the reframing:

- **Decision 2 is not "should PF-13 be an invariant or policy."** Genesis already answered —
  it is constitutional. The question is how to *materialize an already-declared constitutional
  Rule* so Acts can cite it.
- **Decision 1 is not only about relations and registry rows.** It is about the general shape of
  "authoritative row admitted alongside its Act," which now has at least four instances.

---

## 1. Transaction architecture

### What the spec requires

§18.1 — governed requests must "commit through the **narrow transactional Ledger interface**."
§14 — State is a disposable projection; deleting it must not delete history.
§4.2 — "No third administrative door exists."
Halt condition 7 — stop rather than create a second hidden mechanism.

### What exists today

`CommitGate.commit` ([kernel/commit.py:99-105](../../kernel/commit.py:99)) makes three `Store` calls:

```
put_object(command)  ->  put_object(context)  ->  commit_act(act)
```

Under `PostgresStore` each opens its own pooled connection, so the commit path is **already
three transactions**. This is fine and deliberate: `commit_act` verifies both objects exist in
CAS before proceeding, and an orphaned CAS object is harmless candidate content (spec: objects
may exist without Acts; authority may not). The pack's own Phase 0a gate says the same.

This gives a clean line, and it is the key to the whole decision:

> **Content-addressed objects may precede the gate. Authoritative rows may not.**
> Only rows in `acts`, `registry`, `relations` and their kin must be inside `commit_act`'s
> transaction, which holds the advisory lock `powerfarm:commit-gate:v1`.

### The grants have already decided more than half of this

`20260815123245_rls_grants_final.sql:29` grants `powerfarm_worker` **select only** on
`objects`, `acts`, `relations`, `registry`. Insert is not granted. The only write door is a
`security definer` function — today, `powerfarm_internal.commit_act`, explicitly granted at
line 50.

So a Python-side transaction cannot write these rows *at all*, regardless of design taste. That
eliminates one option outright.

### Options

**A — Widen `commit_act` with typed admission parameters.**
Add optional `p_relations jsonb`, `p_registry_entry jsonb`; insert them after the Act insert in
the same transaction. New migration, `create or replace function`.
*For:* one gate, one lock, one transaction; structurally impossible to write an authoritative
row without an Act; trivially mirrored in `MemoryLedger`.
*Against:* the function already takes 14 parameters and grows one per admission kind; every new
authoritative side effect reopens the most carefully audited function in the system.

**B — Generic side-effect envelope.**
One `p_effects jsonb` array of `{kind, rows}`, dispatched inside `commit_act`.
*For:* signature stops growing.
*Against:* an untyped envelope at the exact point where the system is otherwise most typed;
validation moves from the signature into hand-written dispatch. This is a second hidden
mechanism wearing a typed hat — it is what halt condition 7 is about.

**C — Caller-controlled transaction (unit of work) in Python.**
*Ruled out by the grants above.* `powerfarm_worker` cannot insert into these tables from any
connection. Pursuing it would require granting direct insert, which dismantles the single-door
property. Not viable.

**D — Per-admission wrapper RPCs.**
`commit_act_with_relations(...)`, `commit_definition(...)` — each a `security definer` function
that calls `powerfarm_internal.commit_act(...)` and then inserts its own rows. One function call
is one transaction, so atomicity is automatic.
*For:* `commit_act` is never reopened — it stays exactly as audited, and every wrapper must go
through it, so the lock and all constitutional checks still run once and in one place. Each
wrapper is small, typed to its use case, and arrives as a new migration file, which fits the
sealed-migrations rule. The grant posture extends naturally: grant execute on the wrapper, never
insert on the table.
*Against:* N functions to keep coherent; a wrapper could botch its own row insert (though not
the constitutional checks, which it cannot bypass).

### Recommendation — D, with A as the named fallback

D preserves the single gate while keeping the constitutional function closed to further edits,
and it is the only option that composes with the existing grant lockdown rather than fighting it.
The bypass risk that normally argues against wrappers does not apply here, because the tables
are select-only: **a wrapper that forgets to call `commit_act` cannot insert anything.** The
invariant is enforced by grants, not by discipline.

Adopt A instead if wrapper count passes roughly four to five and the row-insert logic starts
repeating; at that point one typed signature is cheaper than five near-identical functions.

Two conditions on D either way:

1. Keep `relations`/`registry` select-only for `powerfarm_worker`, forever. That grant *is* the
   invariant.
2. Mirror each wrapper in `MemoryLedger` in the same change, or the memory and Postgres ledgers
   drift and the 63 tests stop meaning what they appear to mean.

---

## 2. PF-13 — declared decision cut

### What the spec requires

§2 (line 97), verbatim:

> The decision MUST record the cut `c` it was made against. If history has advanced to `c' > c`
> before commit, the kernel MUST decide by Rule whether the decision remains valid, must be
> reauthorized against `c'`, or may be committed regardless. A silent default is forbidden.

§4.1 — every Act must reference by content hash the exact Registry and Rule versions under which
it was validated.
§7 / §4.2 — constitutional Rules cannot be changed after Genesis.

### What exists today — three layers, all hardcoded

| Layer | Location | Behaviour |
|---|---|---|
| Service | [service/authority.py:189](../../service/authority.py:189) | `ConflictError` on any drift |
| Kernel | [kernel/commit.py:77](../../kernel/commit.py:77) | `CommitError` on any drift |
| Database | `commit_act` RPC | `raise exception` on any drift |

All three compare **whole-history equality**: `history_cut()` is `select hash from public.acts` —
*every* Act in existence. Any new Act anywhere invalidates every in-flight decision.

### The violation is subtler than "too strict"

The current behaviour is not a *permissive* silent default — it is fail-closed, which is the safe
direction. The conformance problem is different, and it is about attribution:

**No Rule hash in any Act attests to the drift decision.** An Act's `rule_hashes` record the
*authorization* Rules. Nothing records which Rule decided that its cut was acceptable, because no
Rule did — a constant did. So the decision is unreconstructible from history, which is what §4.1
requires and what "a silent default is forbidden" is protecting.

And per §0 above, the Rule that should be doing this **already exists constitutionally**:
`declared-decision-cut`, named in `genesis.yaml`, bound into `config_hash`, never materialized.

### The second problem: global serialization

Whole-history equality means two entirely unrelated commands in flight always conflict. The
system is effectively globally serialized at the authorization boundary. Phase 5's gate — "500
valid candidates → one Act **and one global-cut contention event**" — is written as though this
is understood, but nothing in Phases 4, 6 or 8 accounts for it. This is a throughput wall, not a
correctness bug, and it is worth deciding deliberately rather than discovering under load.

### Options

**1 — Materialize `declared-decision-cut` as a registered constitutional Rule.**
Give it a definition object and Registry entry; require its hash in `rule_hashes` for every
consequential Act. Behaviour unchanged; the three checks become that Rule's implementation
rather than anonymous constants.
*For:* zero behavioural change, zero new risk, fail-closed preserved. Restores conformance with
§2 and §4.1. Genesis already made this decision — this executes it rather than reopening it.
Unblocks Phase 1 immediately.
*Against:* requires the Registry writer (Phase 0b) to exist first, or a Genesis-cut seeding path.
Sequencing, not obstacle.

**2 — Rule-decided drift, per command type, including "commit regardless".**
*For:* the fullest reading of §2's three-way choice.
*Against:* "commit regardless" is the one option that can genuinely reintroduce TOCTOU, which is
the exact thing PF-13 exists to prevent. It also needs the Rule DSL (Phase 1) to exist — and
Phase 1 is blocked on PF-13 — so it is circular as a first step.
**Recommend declining** unless executable evidence forces it.

**3 — Narrow the invariant from whole-history equality to causal relevance.**
A decision survives drift that cannot affect it. This is where the throughput lives.
*For:* §10.2 already establishes causal order as constitutional and `seq` as merely operational,
so the spec supports it. And §2.1 already requires that "every Rule MUST statically declare which
context keys it reads" — which is precisely the read-set machinery needed to decide relevance
soundly, and precisely what Phase 1 builds.
*Against:* soundness is genuinely hard. A Rule reading `budget.remaining` *is* affected by an
unrelated budget Act. Getting the read-set wrong reopens TOCTOU quietly, which is the worst
failure mode available.

### Recommendation — 1 now; 3 co-designed with Phase 1; decline 2

Option 1 is small, safe, restores conformance, and unblocks Phase 1 without touching behaviour.
Do it as part of Phase 0b, since it needs the same Registry writer.

Option 3 should **not** be sequenced after Phase 1 — it should be designed alongside it, because
Phase 1's static context-key extraction is its prerequisite. Building Phase 1's read-set analysis
without knowing it will later carry drift-relevance is how you get an analysis that almost works.

Option 2 is the only one that can make the system less safe. Leave it closed.

---

## 3. What the two decisions jointly imply

They converge on one piece of work, which is why deciding them together is worth it:

**Phase 0b is larger and more central than the runbook says.** It is not "add a
`RegisterDefinition` runtime." It is *the Registry has never had a writer*, and:

- the Postgres commit path is inert until it does (§0);
- PF-13's materialization needs it (Decision 2, option 1);
- the schema-shell problem (audit §4.5, your fork item 3) is the same writer;
- Phases 1, 4, 5 and 8 all register vocabulary through it.

**Suggested order, revised from the audit:**

1. Decide the wrapper shape (Decision 1 → D). Small design note, no code.
2. **Phase 0b first, not 0a** — Registry writer, with `commit_definition` as the first wrapper
   built under D. This is the load-bearing phase, and the pack's ordering understates it.
3. Materialize the four Genesis constitutional Rules, `declared-decision-cut` among them
   (Decision 2 → option 1), and re-register constitutional vocabulary at v2 *with schemas*,
   which clears fork item 3 in the same pass.
4. Phase 0a — relations, now a second instance of an established pattern rather than a novel one.
5. Phase 1, with drift-relevance (option 3) in the read-set design from the start.

Swapping 0a and 0b is a deviation from the runbook. The runbook says not to reorder "unless a
compile-time dependency forces it and the reason is recorded" — the empty Registry blocking all
Postgres commits is that dependency, and this memo is the record.

---

## 4. What I could not resolve

- **Whether `registry_seed_manifest` was ever intended to have a promoter, or whether Genesis
  seeding is meant to happen through the Registry writer itself.** No code path exists either
  way. This changes how step 3 above is built, and it is a question about intent, not evidence —
  yours to answer.
- **Whether the four Genesis constitutional rules were deliberately left unmaterialized** (as
  structural laws implemented in code) **or whether materialization was always planned.** §18's
  "Structural laws" box lists CAS, typed Relations, append-only history and acyclic dependency —
  which overlaps the four names but does not match them exactly. If they are meant to stay as
  code-level structural laws, Decision 2 option 1 needs rethinking, because then the absence of a
  Rule hash is intentional and §2's "decide by Rule" is satisfied differently.

That second one is the only place where I think the constitutional intent is genuinely
ambiguous, and it is upstream of Decision 2. Worth settling before step 3.
