# Constitutional Decision Record — Genesis Materialization

Recorded 2026-08-16, cut `b3de7c7`. No code written, no repo files modified.

Supersedes the open question in the Decision Memo §4 ("whether the four Genesis constitutional
rules were deliberately left unmaterialized"). That question is now closed.

---

## Evidence check on the ruling

Every citation verified against source. All hold verbatim.

| Claim | Verdict |
|---|---|
| Rules are versioned, content-addressed system objects; constitutional Rules the immutable subset | **Confirmed** — spec §7:324-330, §4.2:191 |
| §16 imposes *three distinct* Genesis obligations | **Confirmed** — "initial Registry definitions", "constitutional core declarations (§4.2)", "initial Rules / authority" are separate bullets at spec:660-663 |
| §18 structural laws are a different list from `genesis.yaml` | **Confirmed** — CAS/reference-by-hash, typed Relations, append-only causal DAG, acyclic constitutional dependency. Overlaps conceptually, matches nothing exactly |
| PF-25 forbids a third administrative door | **Confirmed** — spec:1055, verbatim |
| The manifest comment says rows are ceremony *inputs* | **Confirmed** — `20260815123236_registry_seed.sql:1-3`, verbatim: "operational inputs to the Genesis ceremony; they do not become authoritative Registry entries until admitted with a born_at reference to GenesisClosed" |
| `ceremony.py` never consumes the manifest | **Confirmed** — `genesis/ceremony.py:15-25` hashes the YAML, emits five Acts carrying only `config_hash` |

The conclusion follows. "Structural law" and "constitutional Rule" are not aliases, the database
comment states the intended promotion path in its own words, and the promoter was never written.
**Incomplete implementation, not an intentional exception.**

---

## D-Genesis-01 — Genesis-declared Rules are materialized constitutional Registry objects

> Every name in `genesis.yaml.constitutional_rules` must resolve to a content-addressed
> `kind=rule` definition whose authoritative Registry entry is born at Genesis. Kernel
> enforcement of a corresponding structural invariant does not substitute for that Rule's
> historical identity where the specification requires Rule attribution.

**Consequence for PF-13.** The three hardcoded checks
([service/authority.py:189](../../service/authority.py:189), [kernel/commit.py:77](../../kernel/commit.py:77),
`commit_act` RPC) are acceptable as fail-closed enforcement machinery. They are not sufficient
constitutional representation. The authorizing/reauthorizing decision needs the registered Rule
identity in the trajectory — i.e. `declared-decision-cut`'s hash present in `rule_hashes`.

## D-Genesis-02 — Constitutional registration is sealed at GenesisClosed

Replaces Phase 0b's "`constitutional=true` requires root authority", which is too permissive:
Root authority alone would be exactly the third door §4.2 and PF-25 prohibit.

```
constitutional = false
    -> ordinary governed RegistryService path

constitutional = true, before GenesisClosed
    -> Genesis ceremony only

constitutional = true, after GenesisClosed
    -> only via an already-Genesis-born amendment protocol, if one exists
    -> otherwise reject, including Root
```

**This is a pack discrepancy.** `03_Implementation_Runbook.md` Phase 0b line 64 states
`constitutional=true` requires root authority. Recorded as a deviation with the reason above;
the runbook is wrong on this point and the spec governs.

---

## Three further cracks this conclusion exposes

Following D-Genesis-02 to its consequences surfaced problems beyond the missing promoter.

### C-1 — `genesis.yaml` does not bind everything §16 requires

Checking the file against §16's nine mandatory bindings:

| §16 requirement | In `genesis.yaml`? |
|---|---|
| Genesis specification | yes — `powerfarm-system-v3.2` |
| canonicalization version | yes — `rfc8785-jcs-v1` |
| hash algorithm + domain namespace | yes — `sha256`, `powerfarm` |
| commit mechanism | yes — `kernel.commit.CommitGate` |
| temporal anchoring hook reservation | yes — `anchored_at`, `notarized_by` |
| **initial Registry definitions** | **no** — the manifest lives in SQL, outside `config_hash` |
| constitutional core declarations | yes — four names |
| **Root Identity and its initial keys** | **no** — absent entirely |
| initial Rules / authority | names only, no content |

`genesis_root_hash` is `object_hash("genesis_config", <genesis.yaml bytes>)`. So the universe's
root hash **does not commit the initial Registry definitions**. A migration can alter the seed
manifest without changing `genesis_root_hash` — and three migrations already have
(`20260816120000`, `20260816150000`, `20260816160000`).

### C-2 — Root Identity is an environment variable, not a Genesis binding

```
service/runtime.py:42    root_identity_hash=os.environ.get("POWERFARM_ROOT_IDENTITY_HASH")
protocol/mcp/server.py:87  "genesis_root_hash": os.environ.get("POWERFARM_GENESIS_ROOT", "unset")
```

§16 requires Genesis to bind "Root Identity and its initial keys." It does not. Who holds root
authority is runtime configuration, and `genesis_root_hash` is a separately-supplied env var
defaulting to the literal string `"unset"`.

Changing `POWERFARM_ROOT_IDENTITY_HASH` silently changes who root is, with no Act, no Registry
change, and no change to `genesis_root_hash`. Under §17 and PF-20 that is a privileged
configuration edit outside the Command → Rules → Act mechanism.

This is a more serious instance of the same defect as PF-13: authority asserted by a constant
rather than by attributable history.

### C-3 — the amendment protocol is a name with no content

`amendment-or-fork` appears in `constitutional_rules`, so the *name* is bound into
`config_hash`. Its substance is nowhere — not in the YAML, not in the manifest, not in code.

§4.2 is explicit: such a protocol "must itself be born at Genesis; it cannot be invented later."
Only the name was born. Writing the procedure now (N-of-M reviewers, delay window, whatever it
turns out to be) would be inventing substance later while claiming Genesis birth.

**Consequence, stated plainly:** if Genesis is ratified as `genesis.yaml` currently stands, this
universe has **no usable amendment protocol**, and D-Genesis-02's middle branch is empty. Fork /
new Genesis becomes the only constitutional exit, permanently. Every future constitutional
definition — every new `constitutional=true` command type, act type or Rule — would be
unreachable.

---

## The window is open, and it closes on first Genesis

The recovering fact: **Genesis has never been materialized anywhere.**

- No code path writes Genesis Acts to a database. `ceremony.py` is a pure function that prints
  JSON to stdout.
- `public.registry` has no writer and is empty; nothing has a `born_at`.
- Only tests fabricate a `GenesisClosed` Act, in `MemoryLedger`.

So C-1, C-2 and C-3 are all still fixable by amending `genesis.yaml` and the manifest **before**
the ceremony is first admitted. After `GenesisClosed` is committed against a real database, §16's
"no architectural backdoors" takes effect and every one of them requires a fork to correct.

This reorders the urgency. The missing promoter is not merely "the first implementation defect."
It is the last moment at which the Genesis binding itself can still be made correct.

---

## Revised Phase 0-bootstrap

Your five steps, with the new findings folded in. Steps 0 and 1 are additions.

| # | Step | Why |
|---|---|---|
| **0** | **Amend `genesis.yaml` to bind everything §16 requires** — initial Registry definitions (or their manifest hash), Root Identity and initial keys | C-1, C-2. Must precede the ceremony; impossible afterward |
| **1** | **Decide `amendment-or-fork`: give it real content at Genesis, or accept fork-only** | C-3. A deliberate choice, not a default. Cannot be deferred |
| 2 | Complete Genesis materialization from the seed manifest | the missing promoter |
| 3 | Materialize the four declared constitutional Rules, `declared-decision-cut` among them | D-Genesis-01 |
| 4 | Ensure `genesis.root_authority` and all bootstrap vocabulary receive real `registry.born_at` history | closes C-2's env-var authority |
| 5 | Close the post-Genesis constitutional-registration loophole | D-Genesis-02 |
| 6 | Only then build ordinary runtime `RegistryService` | Phase 0b proper |

The bootstrap paradox you identified is confirmed and is what forces this shape:
`RegisterDefinition` is itself a `command_type` that `commit_act` requires to be registered at
the declared registry cut, so `RegisterDefinition` cannot register itself. Genesis is necessarily
the unique bootstrap membrane. After `GenesisClosed`, it seals.

---

## Pack discrepancies recorded

1. **Phase 0b `constitutional=true` rule is wrong** — per D-Genesis-02 above. Root authority
   alone cannot mint constitutional definitions post-Genesis.
2. **The runbook has no Genesis materialization phase.** It opens at Phase 0a assuming a
   functioning Registry. No Registry exists, and the pack's own source map lists
   `RegisterDefinition` as merely "seeded but lacking runtime implementation" — understating a
   missing Genesis promoter as a missing service method.
3. **The pack's phase ordering is unreachable as written.** Phases 0a and 0b both require
   committing Acts through Postgres; no Act can commit until the Registry is populated; the
   Registry cannot be populated except at Genesis.

---

## Status

Decisions D-Genesis-01 and D-Genesis-02 recorded as ruled. C-1, C-2 and C-3 raised as new
findings requiring your decision — C-3 in particular is a fork-or-not choice that cannot be
deferred past first Genesis.

No code touched. Awaiting instruction.
