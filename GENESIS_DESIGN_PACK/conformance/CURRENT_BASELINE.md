# Current Baseline

What the implementation actually does today, recomputed rather than remembered.

**Commit:** `b3de7c7fb83b7848f9f7b53ffe85c966d4556c9f` — *"Admit principal bindings through Acts,
not by hand"*
**Date:** 2026-08-16 · **Migrations:** 16 · **Genesis:** never performed

---

## Test state

```
pytest      128 passed, 5 skipped
ruff        clean
mypy        clean — kernel worker agent genesis ledger service protocol (40 files)
shellcheck  clean — deploy/macos, scripts/ci, .claude/scene
SQL         19 assertions in the migrations job (7 + 12)
```

The SQL conformance runs in the **migrations** CI job, not pytest. Locally it needs PostgreSQL 15+
(`security_invoker`) and `LC_ALL=C` on macOS, or the postmaster dies with *"became multithreaded
during startup"*.

## Law coverage

The authoritative map is `conformance/LAW_TEST_MAP.toml` in the repository — **not copied here**, so
there is one source. `conformance/test_law_coverage.py` checks it against the specification: it
greps `PF-\d{2}` out of `Powerfarm System Specification v3.md`, so adding a law to the constitution
fails CI until someone classifies it.

| Status | Count | Laws |
|---|---|---|
| IMPLEMENTED | 21 | — |
| ENFORCED_UNPROVEN | 0 | — |
| DESIGN_ONLY | 5 | PF-09, PF-16, PF-18, PF-24, PF-25 |

All five are genuinely unbuilt: relations have no writer, no projector exists, no Act type carries
secret material, no effect-phase vocabulary is registered, no amendment protocol exists.

## What is strong

**Canonicalization (PF-22).** Six golden vectors — `values`, `arrays`, `unicode`, `french`, `weird`,
`structures` — each asserting byte-exact canonical output, the untagged SHA-256, **and** the
domain-tagged SHA-256. Every hash-pinning decision in this pack depends on it.

**The review lifecycle.** Ten conformance tests covering the ways a reviewer could cheat, not just
the happy path: a review of another Command cannot resolve this one; a consequence cannot step over
a pending review; resolution requires both the request and the review.

**Fail-closed is consistent, not incidental.** No applicable Rules → raise. Missing declared context
key → raise. Unregistered command/act/rule/context type at the cut → raise. Empty `rule_hashes` →
raise. Invalid signature → raise. Cut drift → raise.

**Database refusals are now proved by provocation**, not by reading migration text. A dropped
trigger and a working one look identical to a code-reading audit.

## What is thin, honestly

**The Rule engine is sound; the Rule population is one car.** `kernel/rules.py` is 53 lines and
fail-closed in four independent places. But there is exactly **one** production Rule —
`RootAuthorityRule` — and it declares `context_keys = frozenset()` and does
`del command, context, history_cut`. **No shipped Rule declares a context key.** The machinery that
CR-1 survival rung 1 depends on is exercised only by the conformance suite's test doubles.

**The Postgres commit path is inert.** `public.registry` has no writer and is empty; `commit_act`
requires command and act types registered at the declared registry cut. All 128 tests run against
`MemoryLedger`. This is expected pre-Genesis, not a defect.

**Four tables are read but have no governed writer:** `registry`, `relations`, `identity_links`,
`identities`. The companion contract (R-24) closes all four with one mechanism.

## Standing gotchas

- `MemoryStore.registered(kind, name, cut)` takes a *name*, and `CommitGate` passes the **rule hash**
  into that slot. `PostgresStore.registered` matches `(name = %s or hash = %s)`, so both work — but
  the two stores model rules differently and that will matter when the Registry writer lands.
- PF-13's drift check runs **before** the registry checks in `CommitGate`. A test that advances
  history to set up a registry-cut scenario will refuse for the wrong reason. Declare the current
  history cut and an older *registry* cut instead — `registry_cut` need only be an ancestry-closed
  subset.
- `conformance/test_kernel.py` carries pre-existing mypy errors and is outside the CI mypy scope.
  Adding it is a separate cleanup from B4.
