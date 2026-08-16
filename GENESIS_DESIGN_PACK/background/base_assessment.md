# Base Assessment and Phase Close

What the Rule machinery actually is, where the base is thin, and a proposed end to this phase.

Recomputed, not remembered: **63 passed**, tree clean, HEAD `b3de7c7`.

---

# PART 1 — How the Rules are actually written

## 1.1 The machinery

`kernel/rules.py` is 53 lines and it is the whole authorization engine.

```python
class Rule(Protocol):
    hash: str
    context_keys: frozenset[str]
    def evaluate(identity, command, context, history_cut) -> RuleResult
```

`authorize()` ([kernel/rules.py:32-52](../../kernel/rules.py:32)) does four things:

1. refuses when the command identity ≠ authenticated identity;
2. for each Rule, computes `rule.context_keys - context.values.keys()` and **raises** on any
   missing key — §2.1's "fail loud, never an implicit default", implemented literally;
3. folds outcomes **`DENY > REQUIRE_REVIEW > ALLOW`**, so any single deny wins;
4. raises when the rule tuple is empty — fail closed.

Then it returns a `Decision` carrying `history_cut`, **all** resolved `rule_hashes`, `registry_cut`
and a joined reason string.

**This machinery is sound.** It is small, it is fail-closed in four independent places, and it
records every Rule that participated rather than only the deciding one — which is what makes
attribution possible at all.

## 1.2 The population

There is exactly **one** production Rule:

```python
@dataclass(frozen=True, slots=True)
class RootAuthorityRule:
    hash: str
    root_identity_hash: str
    context_keys: frozenset[str] = frozenset()      # ← reads nothing

    def evaluate(self, identity, command, context, history_cut):
        del command, context, history_cut           # ← ignores everything
        return ALLOW if identity.hash == self.root_identity_hash else DENY
```

And `ConfiguredRuleResolver.resolve()` does `del command, context, history_cut` — it resolves a
closed configured list, ignoring what is being asked.

> **The engine is well-built. The fleet is one car, and it drives with its eyes closed.**

That is not a criticism of the code — it is the honest state of a system that has not had Genesis.
But it has one consequence worth stating precisely: **no shipped Rule declares a context key.** The
`context_keys` machinery is exercised only by the conformance suite's test doubles (`Allow` and
`Outcome` both declare `request.origin`). The read-set chain that CR-1 rung 1 depends on has never
been exercised by production code.

---

# PART 2 — What is strong

Worth recording, because the design we have been building rests on it.

**Canonicalization (PF-22) is fully and rigorously covered.** `conformance/golden-vectors/` ships six
vectors — `values`, `arrays`, `unicode`, `french`, `weird`, `structures` — and
[tests/test_canon.py:13](../../tests/test_canon.py:13) asserts, for each: byte-exact canonical output, the
untagged SHA-256, **and** the domain-tagged SHA-256. That is stronger than most systems ever get
about their own identity function, and every hash-pinning decision in this design depends on it.

**The review lifecycle is genuinely pinned.** Ten conformance tests, and they cover the subtle
cases, not just the happy path: a review of another Command cannot resolve this one; a consequence
cannot step over a pending review; resolution requires both the request and the review;
`AuthorizationReviewed` must come from a `ReviewAuthorization` Command; `AuthorizationResolved` may
carry a deny. Those are the tests you write after you have thought about how a reviewer could cheat.

**Fail-closed is consistent, not incidental.** No applicable Rules → raise. Missing declared context
key → raise. Unregistered command/act/rule/context type at the cut → raise. Empty `rule_hashes` →
raise. Signature invalid → raise. Cut drift → raise. Every default in the system points at refusal.

**PF-23 and PF-15 are both pinned** — identical resubmission returns the same Act; one Command
carries many lifecycle Acts.

**The migration harness tests the right two things**: migrations apply **twice** cleanly
(idempotency), and grants actually bite — `service_role` is denied, `powerfarm_worker_test` is
permitted.

---

# PART 3 — Where the base is thin

## 3.1 PF-21 is asserted nowhere

```
grep -rn "registry_cut\|rule_hashes" tests/ conformance/   →   no matches
```

PF-21 — *"Every Act references the exact Registry and Rule versions under which it was validated"* —
is the law the P0 work existed to satisfy. `rule_hashes` was added to the Act preimage **for** it.
`commit_act` validates it in SQL. And **no test asserts it.**

This is the single cheapest, highest-value gap in the repository. It is also load-bearing for
everything we designed: R-18R, R-15R, the companion contract and CR-1's attribution all assume Acts
faithfully carry the versions that validated them.

## 3.2 Database-layer refusals are untested

`scripts/ci/test_migrations.sh` tests application idempotency and grants. It does **not** test that
the enforcement mechanisms refuse:

- `reject_act_mutation` / `relations_are_immutable` / `registry_is_immutable` triggers (PF-07);
- `acts_one_consequence_per_command_idx` — the standing open item from the scene.

The Python gate proves these rules today. The database's own refusal is unproven. That matters more
now than it did, because the admission architecture moves *more* enforcement into SQL, not less.

## 3.3 Law coverage: 11 of 26 referenced

Referenced in test names: PF-01, 02, 03, 04, 08, 11, 13, 14, 15, 22, 23.

The other fifteen, classified honestly:

| Status | Laws |
|---|---|
| **covered by unlabelled tests** | PF-05, PF-06 (review lifecycle), PF-17 (`ObservationService` in `test_mcp_stateless`) |
| **structurally enforced, untested** | PF-07 (triggers), PF-10 (parents must pre-exist ⇒ no cycle possible), PF-19 (genesis is a chain) |
| **enforced but unasserted** | **PF-21** (§3.1) |
| **partial** | PF-12, PF-18, PF-20 |
| **not yet implementable** | PF-09 (relations have no writer), PF-16 (no projectors), PF-24 (no effects machinery), PF-25 (no amendment protocol), PF-26 (anchoring deferred) |

So the real gap is smaller than 15 — but it is invisible, because nothing makes it visible. A law
with no test and no waiver looks exactly like a law with a test.

## 3.4 One test carries nine laws

`test_pf01_pf02_pf03_pf04_pf08_pf11_pf13_pf14_pf23` — when it fails, it does not say which law broke.
Naming tests after constitutional assertions is a good instinct; bundling nine into one undoes the
benefit.

## 3.5 CI still omits the layers that will carry the new code

`mypy kernel worker agent genesis` — `ledger/`, `service/`, `protocol/` remain outside. The admission
architecture, the Registry writer and the Rule engine all land there. Unchanged since the first
audit; still cheap; now more consequential.

---

# PART 4 — Strengthening actions, ranked by value per hour

| # | Action | Why now |
|---|---|---|
| **B1** | **Assert PF-21.** One test: an Act's `registry_cut` and `rule_hashes` are exactly the versions that validated it, and a Rule not registered at that cut is refused | Cheapest gap, load-bearing for the whole design |
| **B2** | **Law→test conformance map with a completeness check** — a machine-readable map from PF-01…PF-26 to tests, with explicit `not-yet-implementable` waivers, and a test that fails when a law has neither | Makes §3.3 permanently visible instead of rediscovered |
| **B3** | **Behavioural tests for DB refusals** — the three immutability triggers and the partial unique index | Closes the standing open item; the admission architecture depends on SQL enforcement being real |
| **B4** | **Widen CI** to `mypy ledger service protocol`, and add `.claude/scene/compose.sh` to the shellcheck glob | Cheap; precedes the code volume |
| **B5** | **Split the nine-law test** into one test per law | Makes failures diagnostic |

B1 and B2 together are the ones I would not skip. B2 is what converts "we checked coverage once, in
a conversation" into a property the repository maintains by itself.

---

# PART 5 — Proposed end of this phase

## 5.1 What this phase actually produced

Working backwards from the artifacts: a complete design of the pre-Genesis institution.

- Genesis Constitution draft 0.2 (Parts I–XII)
- Part VIII vocabulary, enumeration-complete, frozen
- CR-1 `declared-decision-cut`, designed with the survival ladder and read-set schema
- Admission architecture — the declarative companion contract
- Powerfarm Engine Protocol P-1…P-10, with the ADK 2.7 absorption matrix behind it
- A consolidated decision register: D-Genesis-01…05, D-Authority-01…04, D-Director-01…08,
  D-Txn-01, D-PF13-01/02, R-1…R-37
- Four content-preimage changes, frozen (R-26)

That is a coherent body. What it lacks is a boundary.

## 5.2 Three exit criteria

I would call the phase complete when all three hold:

**E1 — Every design claim about *current* behaviour has a test, or an explicit waiver.**
This design rests on roughly forty verified claims about the existing code. They were verified by
reading. Reading does not survive refactoring. B1 and B2 convert the load-bearing ones into
properties the repository enforces, so implementation cannot silently invalidate the design it is
implementing.

**E2 — The decision register is complete, unambiguous, and single-sourced.**
Largely done. The R-28 collision showed the failure mode: IDs scattered across seven documents drift.
One register, one file, no phantoms.

**E3 — One handoff document a fresh implementer can execute from.**
Not seven design documents plus a conversation. The symmetry is worth noticing: this phase began
with someone handing us a Fresh Agent Execution Pack for the *platform*. It should end by producing
the equivalent for the *constitution* — call it the **Genesis Design Pack**: ratified constitution,
frozen preimages, vocabulary, admission architecture, engine protocol, decision register, ordered
work list, and explicit halt conditions.

## 5.3 What closes the phase concretely

Five base actions (B1–B5), then one assembly:

```
B1  assert PF-21                          ← smallest, most load-bearing
B2  law→test map + completeness check
B3  DB refusal tests
B4  widen CI
B5  split the nine-law test
────────────────────────────────
Genesis Design Pack                        ← E3, assembled from existing artifacts
```

B1–B5 are the only work in this list that touches the repository, and all of it is tests and CI
configuration — no `kernel/` changes, no migrations, no Genesis.

## 5.4 What explicitly does *not* close in this phase

Stating this so the boundary is real rather than aspirational:

- Genesis is **not** performed. The window stays open.
- No key material is generated.
- The admission architecture is designed, not implemented.
- The ADK compatibility profile is not written (step 4 of your order).
- A-1, A-6, A-8, A-9…A-12 remain open decisions, and they are yours, not the phase's.

The phase ends with a universe fully designed and deliberately unborn. That seems like the right
place to stop, because the next phase's first act is irreversible in a way nothing in this one was.

---

# PART 6 — Recommendation

Take B1 and B2 now — they are small, they are in tests only, and they protect the design from the
code drifting underneath it. B3–B5 next. Then assemble the Genesis Design Pack and close.

If you would rather keep designing, the ADK compatibility profile is the natural continuation and it
also serves as the contamination check on the Engine Protocol. But I would not start Genesis
implementation with PF-21 unasserted — the law that every Act carries the versions that validated it
is precisely the one the entire hash-pinning design assumes.
