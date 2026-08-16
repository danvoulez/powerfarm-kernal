# Start Here

One document to execute from. Everything else in this pack is reference for a step below.

This phase designed a universe and deliberately did not start it. Your job is the work between
here and the ceremony — and knowing exactly which parts are not yours.

---

## 0. State on arrival

Recomputed against the working tree, not remembered.

| | |
|---|---|
| Commit | `b3de7c7` — *Admit principal bindings through Acts, not by hand* |
| Branch | `identity/principal-binding-acts`, 1 ahead of local `main` |
| Tests | 128 passed, 5 skipped · ruff clean · mypy clean on 40 files |
| SQL conformance | 19 assertions in the **migrations** CI job (not pytest) |
| Migrations | 16, sealed — only additions |
| Law coverage | 21 IMPLEMENTED · 0 ENFORCED_UNPROVEN · 5 DESIGN_ONLY |
| Genesis | **never performed.** The pre-Genesis window is open |
| Uncommitted | 8 paths — the B1–B5 conformance work plus this pack |

Full detail: [`../conformance/CURRENT_BASELINE.md`](../conformance/CURRENT_BASELINE.md).
What the pack was built against, with hashes: [`../evidence/SOURCES.md`](../evidence/SOURCES.md).

## 0.1 Read these three first, in this order

1. [`../decisions/DECISION_REGISTER.md`](../decisions/DECISION_REGISTER.md) — every ID and its
   status. **If a specification disagrees with the register, the register wins and the
   specification is stale.**
2. [`../decisions/OPEN_DECISIONS.md`](../decisions/OPEN_DECISIONS.md) — what is genuinely
   undecided, and what each open item blocks.
3. §1 and §2 of this file — halt conditions before work, and the ordering.

Do not read the whole pack before starting. Each work item below names the one or two documents
that govern it.

---

## 1. Halt conditions

`H-1`…`H-3` are **checks to run before the work they gate**. `H-4`…`H-8` are **invariants**: if one
is ever violated, stop and escalate rather than repair forward. These are not decision IDs; they do
not appear in the register. Where an item corresponds to a numbered halt in the Fresh Agent
Execution Pack, that number is given.

### Checks before work

**H-1 — Has a Genesis ceremony already run anywhere?**
Not verifiable from this machine. If a ceremony ran in any environment not visible here, the
pre-Genesis window is already closed, every `R-26` preimage change becomes impossible, and fork is
the only remedy. **Check before W-2.** Cheapest check: any admitted Act at all, in any live
database.

**H-2 — Are there legacy `relations` rows without provable admission?** *(pack halt 2)*
The table has never had a writer, so a clean database is empty — but a live Supabase project could
hold hand-inserted rows. If any exist, the Phase 0a migration adding `admitted_act` may not be
written as designed, because those rows cannot be given an admitting Act retroactively.
**Check before W-6.**

**H-3 — Is there durable Cloudflare OS state keyed by email or username?** *(pack halt 5)*
`server.ts` has **four** `idFromName` call sites — `:681` (`split[0]`), `:697` (`email`), `:726`
and `:753` (`username`) — not one. Re-keying only the email path leaves three live addressing routes
into the same Durable Object namespace, and the Phase 3 gate would pass while they remain.
**Produce a migration inventory before Phase 3**, not during it.

### Invariants

**H-4 — A second authoritative write path beside the gate.** *(pack halt 7 — the real risk)*
Every authoritative row lands in the same transaction as its admitting Act, through one door.
CAS objects may precede the gate; authoritative rows may not. A Python unit-of-work is **illegal,
not merely inadvisable** — `powerfarm_worker` holds `select` only (D-Txn-01). The failure mode is
quiet: two mechanisms, both working, only one governed.

**H-5 — Any canonical preimage change attempted after `GenesisClosed`.**
The four changes in [`../specifications/canonical_preimages.md`](../specifications/canonical_preimages.md)
alter content identity. Content identity is the one thing Genesis makes permanent. After the
ceremony there is no amendment path for them — only fork.

**H-6 — Genesis ratified while `amendment-or-fork` is still a name with no content.**
§4.2 forbids inventing the substance later: *such a protocol must itself be born at Genesis.* This
universe would then have no in-universe constitutional amendment mechanism, permanently, for every
future constitutional definition. That may be ratified **consciously** (D-Genesis-04) — it may
never happen by default.

**H-7 — Constitutional registration attempted post-Genesis outside the amendment protocol.**
Including by Root. `constitutional=true` after `GenesisClosed` → reject (D-Genesis-02). This
contradicts the execution pack's Phase 0b, which is wrong on this point.

**H-8 — Golden Bridge (Phase 7) treated as verified.** *(pack halt 6)*
`danvoulez/lab-mistral-rs-gateway` is private and absent from every supplied archive. Its
strict-routing invariants and the staleness of its `docs/GOLDEN_BRIDGE.md` are **unverified**, not
verified-clean. Every Phase 7 claim in the execution pack is unchecked.

---

## 2. Ordered work list

Three tracks. Track A is the whole of what can be built before the ceremony; Track B is the
ceremony; Track C is what the execution pack calls Phases 1–9.

**The property that matters: W-1 through W-9 are executable now, without a single open decision
being answered.** Only the offices-and-mandates subset of W-8, and all of W-10, wait on Dan.
Nothing else below stalls behind a question.

### Track A — pre-Genesis, repository only

| | Work | Governed by | Gate |
|---|---|---|---|
| **W-1** | Commit the B1–B5 conformance work | — | 8 uncommitted paths; tests already green |
| **W-2** | The four canonical preimage changes | [`canonical_preimages.md`](../specifications/canonical_preimages.md) (R-26) | **H-1 first** |
| **W-3** | The `admit` function and the companion contract | [`admission_architecture.md`](../specifications/admission_architecture.md) §F | D-Txn-01, R-24, R-25, R-27 |
| **W-4** | The Genesis promoter — seed manifest rows admitted as authoritative Registry entries | admission architecture §F | a declaration against W-3 |
| **W-5** | Registry writer (pack Phase 0b) | admission architecture §F.2 | W-3, W-4 |
| **W-6** | Relations governed door (pack Phase 0a) | admission architecture §F | **H-2 first** |
| **W-7** | CR-1 `declared-decision-cut` as a registered Rule | [`cr1_declared_decision_cut.md`](../specifications/cr1_declared_decision_cut.md) | needs W-2's third preimage change |
| **W-8** | Canonical schemas for the 55 retained definitions, and the Part VIII delta to 99 | [`initial_registry_manifest.md`](../vocabulary/initial_registry_manifest.md) | largest item; worst late-failure mode |
| **W-9** | The Google ADK 2.7 capability profile | [`engine_protocol.md`](../specifications/engine_protocol.md) Part 4 | **the one unwritten design artifact** |
| **W-10** | `genesis.yaml` binding canonical content, and key generation | [constitution](../constitution/01_Genesis_Constitution_0.2.md) Part XI | blocked — see Track B |

**W-2 first, and not for tidiness.** The four preimage changes are the only work in this project
with a deadline that is not of our choosing. They are small, they are decided, and after
`GenesisClosed` they are impossible. Everything else can be reordered on evidence; this cannot.

Note what each preimage change actually costs. Changes 1 and 2 are **Kernel shape** — they land in
`kernel/types.py` and `kernel/commit.py` without needing the Registry writer, because
`PostgresStore.registered` already matches `(name = %s or hash = %s)`. But change 2's full
enforcement — binding a Rule's context keys at its birth to the exact `context_type` definition hash
(R-18R) — needs the Rule engine, which is Track C. **Land the shape now; the enforcement follows.**
Do not defer the shape because the enforcement is far away; the shape is what Genesis freezes.

**W-3 before W-4, W-5 and W-6, always.** Phases 0a, 0b and 5 all need authoritative rows inside the
admitting transaction. If they are built first they will each invent their own seam, and that is H-4
arriving quietly. `commit_act` is declared `create or replace function`, so a new migration file can
replace it without editing a sealed one — the sealed-migrations rule permits this. After W-3, each
of W-4, W-5 and W-6 is a declaration against an existing mechanism rather than a new seam. That is
the whole point of doing it first.

**W-8 is the item that will be underestimated.** All 45 currently seeded definitions are name and
version shells: `{"kind":…,"name":…,"version":…}` and nothing more. No `payload_schema`, no
`value_schema`. The Genesis seed manifest must carry canonical schemas for all of them plus the 46
new definitions. The subset in manifest §8 — offices, mandates, projectors — waits on A-1, A-2,
A-4 and A-10; the other ninety-odd do not.

**W-9 is design, not code, and it is also a test.** The absorption matrix supplies every mapping and
the protocol supplies every slot, so writing it is mechanical. Its value is the contamination check:
if any requirement in P-1…P-10 turns out to have no engine-neutral expression and can only be stated
in ADK's vocabulary, the protocol has been contaminated and that requirement needs rewriting. Run
that check before treating the Engine Protocol as settled.

### Track B — the ceremony

Irreversible. Everything before this point was recoverable; nothing after it is.

1. **Answer the four blocking decisions.** D-Director-08 first — everything about Root/Director
   disjointness rests on it. Then D-Genesis-04 (H-6), D-Director-03, and A-8's quorum sizes,
   windows and reviewer Identities. Reasoning in `decisions/OPEN_DECISIONS.md`; **the answers are
   Dan's, and this pack deliberately does not make them.**
2. **Generate key material.** Real Ed25519 keypairs for Root, Dan-as-Director, and every
   constitutional reviewer. This pack cannot supply them and must not pretend to — generating them
   is an act with custody consequences.
3. **Ratify** V.7 with counsel, not with engineering. Symmetric accountability means the record is
   discoverable when things go wrong; that is the price of the promise and should be accepted
   knowingly.
4. **Run Genesis** — five Acts, per constitution Part XI. `genesis_root_hash` then commits the whole
   constitution rather than a 19-line summary of it.
5. `GenesisClosed`. H-5 and H-7 become live from this moment.

### Track C — post-Genesis

The execution pack's Phases 1–9, in its own dependency order, with three corrections this pack
found:

- **Phase 1 (Rules as data) should follow Genesis, not precede it.** Typed Rules require statically
  type-checked payload access, and typed registration must fail until the effective definition
  supplies a canonical schema. Built pre-Genesis, Phase 1 stalls on a v2 re-registration of the
  entire constitutional vocabulary by root authority. Built after, W-8's schemas are already there
  and the whole re-registration pass disappears. The execution pack does not call this dependency
  out; as written it would stall.
- **Phase 3** re-keys **all four** `idFromName` sites (H-3), not the email one.
- **Phase 7** is unverified, not verified (H-8).

Phases 2, 4, 5, 6, 8 and 9 stand as the execution pack describes them. Phase 5's `AdmitBatch` leans
on `acts_one_consequence_per_command_idx`, which now has a behavioural test (B3) rather than only
the Python gate.

---

## 3. What this phase deliberately did not close

Stating it so the boundary is real rather than aspirational.

- Genesis is **not** performed. The window stays open.
- No key material is generated.
- The admission architecture is designed, not implemented.
- A-1…A-12 and the D-`*` open items remain open, and they are Dan's, not the phase's.
- Whether the institution can bear what it accepts — insurance, reserves, corporate form. Powerfarm
  can represent accountability perfectly and still be unable to honour it. That is a legal and
  financial design problem, not a ledger one.

There is no clock on any of this except the one created by ratifying early.

---

## 4. Conventions that will bite you

Concrete, recomputed, and each one already cost time once.

**Entry rule.** Before editing `kernel/` or `supabase/migrations/`: read the section of the
specification that governs what you are changing, and cite it. Do not write constitutional code from
memory. Migrations are sealed — only new files.

**`MemoryStore.registered(kind, name, cut)` takes a *name*, and `CommitGate` passes the **rule
hash** into that slot.** `PostgresStore.registered` matches `(name = %s or hash = %s)`, so both work
today — but the two stores model rules differently, and that will matter the moment the Registry
writer lands.

**PF-13's drift check runs *before* the registry checks in `CommitGate`.** A test that advances
history to set up a registry-cut scenario will refuse for the wrong reason and look like a passing
failure. Declare the current history cut and an older *registry* cut instead; `registry_cut` need
only be an ancestry-closed subset.

**SQL conformance is not in pytest.** It runs in the migrations CI job. Locally it needs
PostgreSQL 15+ (`security_invoker`) and `LC_ALL=C` on macOS, or the postmaster dies with
*"became multithreaded during startup"*.

**`conformance/test_kernel.py` carries pre-existing mypy errors** and is outside the CI mypy scope.
Adding it is its own cleanup, not part of B4.

**`registry.kind` has no CHECK constraint.** All ten Phase 0b kinds — including `node_species`,
`effect_phase`, `machinery_class`, `disclosure_profile` — are registrable with no DDL change. The
"small constitution, extensible universe" claim is structurally real here, not aspirational.

**One provenance wrinkle.** The execution pack labels the kernel snapshot `3fc601c` and calls it a
merge commit. Locally that content is `b3de7c7`, one commit ahead of `main`, and
`git branch -a --contains` lists only this branch and its remote — not `origin/main`. The content
matches byte for byte; the commit identity describes a merge the local refs do not show. `git fetch`
before treating `3fc601c` as an addressable base.
