# ADK 2.7 Absorption / Engine Contract

Design document. Inspected against the bundled `google_adk-2.7.0-py3-none-any.whl` (675 modules),
not against documentation or summary. No code, migrations, or commits.

---

## 1. The finding that most changes the design

**ADK's event history is rewindable. Powerfarm's is not.**

`EventActions.rewind_before_invocation_id` ([events/event_actions.py:192]) plus
`events/_rewind_events.py`, whose docstring says it is *"the single source of truth for 'which
events are live' after rewinds"* — iterating backward, dropping the rewinding event together with
every event back to the earliest event of the target invocation.

And artifacts are **deletable**: `BaseArtifactService.delete_artifact()`
([artifacts/base_artifact_service.py:171]), with identity `(filename, version:int, canonical_uri)` —
a monotonic counter and a storage location, not content.

So both of ADK's evidence surfaces are **mutable views**. An ADK event or artifact that supported a
Powerfarm admission can later be rewound out of the live set or deleted outright, while the
Powerfarm Act stands forever.

> **Consequence (the sharpest one in this pass): evidence must be content-addressed into Powerfarm
> CAS at capture time. Powerfarm must never reference an ADK `event.id`, artifact coordinate or
> `canonical_uri` as its evidence identity.** Those may travel *inside* a hashed evidence payload as
> correlation data — never as the evidence itself.

This is not a defect in ADK. Rewind and artifact deletion are sensible for an execution runtime.
It is precisely why the trajectory adapter must *copy* rather than *link*, and it validates the
Act ≠ Event boundary far more strongly than the volume argument does.

---

## 2. Absorption matrix

Verdicts: **adopt** (use ADK's mechanism as-is) · **wrap** (use behind a Powerfarm-governed
boundary) · **map** (translate into Powerfarm objects) · **keep separate** (both exist, never
merged) · **reject** (must not enter Powerfarm).

| ADK concept | Powerfarm analogue | Verdict | Rationale |
|---|---|---|---|
| `App` | execution application definition | **map** | Registry object pinning app + root agent/workflow + toolset + model config + semantic plugins |
| `Runner` | engine runtime | **adopt** | ADK-owned; Powerfarm never reimplements the loop |
| `InvocationContext` | — | **keep separate** | Holds mutable services, session, live queues, `end_invocation`. Never Powerfarm Context |
| `Session` | runtime conversation/state | **keep separate** | Operational. Deleting the session store must not touch institutional history |
| `Session.state` + `app:`/`user:`/`temp:` scopes | — | **keep separate** | Engine memory. A `state_delta` may reach authorization **only** through a registered projector with declared dependencies (R-21) |
| `Event` | trajectory event | **map** | Evidence, never an Act. Content-addressed on capture (§1) |
| `EventActions` (`state_delta`, `artifact_delta`, `transfer_to_agent`, `escalate`, …) | execution deltas | **map** | Projection input and evidence |
| `EventActions.rewind_before_invocation_id` | — | **reject** | Powerfarm history has no rewind. Never mirrored into Acts |
| `Workflow` | execution graph | **adopt** | Do not build a competing workflow engine |
| `BaseNode` / `Node` / `FunctionNode` / `JoinNode` | execution unit | **adopt** | |
| `input_schema` / `output_schema` / `state_schema` | typed node contracts | **adopt design, map authority** | ADK validates at runtime; the Powerfarm-registered schema is authoritative at admission |
| `NodeStatus` (INACTIVE/PENDING/RUNNING/COMPLETED/WAITING/FAILED) | execution status | **adopt** | Feeds `research.current_experiments` — a projection, never canonical |
| `NodeState` (`attempt_count`, `interrupts`, `resume_inputs`, `run_id`) | execution-local state | **keep separate** | Operational |
| `sequence_barrier` (deterministic replay) | — | **adopt** | ADK's own determinism machinery; Powerfarm benefits, owns nothing |
| `max_concurrency`, `retry_config`, `timeout` | execution policy | **adopt** | Ordinary execution-plan parameters |
| dynamic node scheduling | dynamically created work | **map** | Powerfarm preserves *scientific meaning*: why created, under which Experiment, by which Agent, under which authorization envelope |
| `rerun_on_resume` | idempotency declaration | **wrap** | The seam where §11.2 attaches — §4 |
| resumability (best-effort, at-least-once) | — | **wrap** | Powerfarm supplies effect identity + idempotency key + dispatch record |
| `ArtifactService` | artifact runtime | **wrap** | CAS bridge; content hash is Powerfarm identity, ADK coords are locators |
| `MemoryService` | engine memory | **keep separate** | Not canonical State |
| `CredentialService` | credential runtime | **keep separate** | Authentication material, never authority |
| `Plugin` (15 callbacks) | lifecycle sensor | **adopt for observation, reject as gate** | Plugins short-circuit — §3 |
| `Tool` / `BaseTool` | executable capability | **wrap when consequential** | The real authority boundary — §3 |
| `LongRunningFunctionTool` | async effect | **wrap** | Natural fit for Dispatched→Observed |
| `ToolConfirmation` (`hint`, `confirmed`, `payload`) | HITL mechanics | **map** | Bridge from `REQUIRE_REVIEW` — §5 |
| interruption / WAITING / resume | runtime HITL | **adopt mechanics, map meaning** | Powerfarm owns the authority of the review |
| `A2A` (+ event converters) | remote execution | **map** | Identity attaches to the actor/endpoint, not the deployment topology |
| ADK registries (models, tools/api, auth providers, features, skills, `integrations/agent_registry`, `integrations/skill_registry`) | execution discovery | **keep separate** | ~8 registries, all execution-scoped. **None is the Powerfarm Registry.** May be *referenced* by pinned identity; confer no authority |
| `Telemetry` | operational observability | **keep separate** | Not evidence unless admitted |
| `Evaluation` | engine evaluation | **keep separate** | Powerfarm's evaluators are Nodes (Research Scheme §6) |
| Agent Engine (`vertex_ai_session_service`, `vertex_ai_memory_bank_service`) | managed deployment | **adopt** | Confirmed present; see the compatibility test in §8 |

---

## 3. Plugins are sensors; tools are the gate

Verified from source, `plugins/base_plugin.py`: fifteen callbacks
(`on_user_message`, `before_run`, `on_event`, `after_run`, `before_agent`, `after_agent`,
`before_model`, `after_model`, `on_model_error`, `before_tool`, `after_tool`, `on_tool_error`,
`on_agent_error`, `on_run_error`, `close`).

And the short-circuit semantics are explicit in the docstrings:

> *"plugin returns a value, it will short circuit all remaining plugins and … to be skipped"*
> *"If a value is returned, it will bypass …"*
> *"`LlmResponse`, which would skip the actual model call."*

Two independent reasons a plugin cannot be the constitutional gate:

1. **Order-dependent bypass.** Execution is registration order, and an earlier plugin returning a
   value short-circuits the rest — including a Powerfarm plugin registered after it.
2. **Registration is App configuration, not a constitutional guarantee.** An App deployed without
   the Powerfarm plugin still runs. Nothing in ADK requires it to be present.

So: **plugins are excellent sensors** — trajectory capture, model request/response provenance,
tool-call observation, usage and cost, artifact registration, failure evidence — and the authority
boundary lives in the **governed tool wrapper**, which an agent cannot invoke around because it *is*
the capability being invoked.

```
ADK agent wants a consequential capability
        ↓
Powerfarm governed tool  ← the only route to the effect
        ↓  authorize / present existing authorization
        ↓  dispatch external effect (§4)
        ↓  return result to ADK
plugins observe throughout
```

---

## 4. Resumability × External Effects — where Powerfarm adds what ADK declines to promise

Verified verbatim, `apps/_configs.py:30-44`:

> *"ADK resumes the invocation in a best-effort manner: 1. Tool call to resume needs to be
> idempotent because we only guarantee an at-least-once behavior once resumed. 2. Any temporary /
> in-memory state will be lost upon resumption."*

This is an honest contract, and it is exactly the gap §11.2 exists to fill.

```
ADK        "resume safely if your tools are idempotent"
Powerfarm  "prove which effect was authorized, whether it was dispatched,
            and what was observed"
```

The attachment point is per-node: `BaseNode.rerun_on_resume: bool`
([workflow/_base_node.py:54]). So the mapping is structural rather than advisory:

| Requirement | Mechanism |
|---|---|
| effect identity | Powerfarm effect request Act hash — stable across resumes |
| idempotency key | derived from that Act hash, passed to the external system |
| dispatch record | `ExternalEffectDispatched` — written **before** the external call returns |
| observation | `ObservationAdmitted` with observer Identity + evidence |
| reconciliation | `ExternalEffectDispatchFailed` / `EffectRetried`; unresolved dispatch is a reconciler's job |
| node declaration | a node wrapping a consequential tool must set `rerun_on_resume = False` |

**The invariant:** at-least-once execution must produce at-most-once *effect*. ADK guarantees the
former; Powerfarm must supply the latter, and the dispatch record written before the call is what
makes an orphaned dispatch detectable rather than invisible.

---

## 5. `REQUIRE_REVIEW` ↔ ADK interruption

ADK already has the mechanics: `NodeStatus.WAITING`, `NodeState.interrupts` and `resume_inputs`,
`RequestInput`, `ToolConfirmation{hint, confirmed, payload}`, and resume semantics. Powerfarm should
not invent an interaction protocol.

```
Powerfarm Rule → REQUIRE_REVIEW
      ↓ review requirement, with the reviewed Command pinned
ADK node → WAITING, interrupt raised, ToolConfirmation.hint carries the ask
      ↓ human responds
Powerfarm ReviewAuthorization Command → AuthorizationReviewed → AuthorizationResolved
      ↓ resume_inputs carries the resolution *reference*, not the authority
ADK invocation resumes
```

**The critical direction:** `ToolConfirmation.confirmed = true` is **not** authorization. It is a
UI-level assertion that a human clicked. Authority comes only from the admitted review Acts, and the
governed tool must verify the resolved authorization chain — never trust `confirmed`. Powerfarm owns
the meaning; ADK owns the pause and resume.

---

## 6. Identifier classification

You asked for this explicitly. Every ADK identifier, classified:

| Identifier | Class | May enter Powerfarm canonical identity? |
|---|---|---|
| `session.id` | execution-local | no |
| `invocation_id` | **correlation identifier** — the natural trajectory correlation key | no; travels inside hashed evidence |
| `event.id` | execution-local (UUID via `Event.new_id()`, not content) | **no** |
| `event.timestamp` (float) | operational metadata | no — never causal order, never `claimed_when` |
| `node_path` / `NodeInfo.path` | execution-local structural locator | no |
| `run_id` / `parent_run_id` | execution-local | no |
| function call id | execution-local correlation | no |
| `branch` / `isolation_scope` | execution-local scoping | no |
| `attempt_count` / `run_counter` | operational metadata | no |
| artifact `(filename, version)` | **evidence locator** — mutable, deletable | no |
| artifact `canonical_uri` | evidence locator / storage identity | no |
| ADK `app_name`, `user_id` | execution-local | no — `user_id` especially: identity is a Powerfarm principal binding |

> **None of them enters Powerfarm canonical object identity.** Content hash remains the sole
> canonical identity. Several become correlation fields *inside* evidence payloads, which are
> themselves content-addressed — so the correlation is preserved and hashed without ever becoming
> identity.

---

## 7. Does this change the preimage decisions? — No, and here is why

You paused the freeze pending this pass. The pass says the freeze is **not blocked**.

You speculated about `engine_definition_hash`, `application_definition_hash`,
`execution_definition_hash`. Working it through: these are **payload content**, not Act preimage
fields. The Act preimage is deliberately generic — `act_type`, `command_hash`, `context_hash`,
`payload_hash`, `parents`, `decision_cut`, `registry_cut`, `rule_hashes`, `claimed_when`. Execution
provenance lives in the payload, which is already bound by `payload_hash`.

And if execution provenance should be **structurally required** on execution Acts rather than a
payload convention, the mechanism already exists: the **companion contract** (R-24). An act type
declares what must accompany it; the gate enforces it at the registry cut. That absorbs the
requirement without touching content identity at all.

So:

| Preimage change | Affected by ADK? |
|---|---|
| `Relation.relation_type` → `relation_type_hash` | no |
| `Context.types` → definition hashes | no — ADK Context never becomes Powerfarm Context |
| Act preimage `+ validity_rule_hash, validity_disposition` | no |
| research `created_at` → `claimed_when` | no |
| **ADK-driven additions** | **none** |

**Recommendation: the four preimage changes can be ratified.** ADK absorption adds nothing to them,
and the companion contract is the right home for execution provenance. This is good news rather than
a contradiction of your caution — the caution was correct to check.

---

## 8. The Engine Contract, derived rather than invented

What Powerfarm requires of any execution engine, stated as capabilities ADK demonstrably has:

1. **Observable execution** — an event stream rich enough to reconstruct a trajectory (ADK: `Event` + `EventActions`).
2. **Interceptable capability invocation** — consequential capability calls can be routed through a governed wrapper (ADK: tools).
3. **Typed units with declared schemas** (ADK: `input_schema`/`output_schema`/`state_schema`).
4. **Suspend and resume with declared rerun semantics** (ADK: WAITING, interrupts, `rerun_on_resume`).
5. **Deterministic replay ordering** (ADK: `sequence_barrier`).
6. **Bounded concurrency and failure policy** (ADK: `max_concurrency`, `retry_config`, `timeout`).
7. **Dynamic scheduling** without requiring pre-declared canonical rows (ADK: dynamic nodes).
8. **Disposable runtime state** separable from institutional history (ADK: Session/Memory services).

And what the contract forbids any engine from doing: writing Powerfarm history directly; conferring
identity or authority; making its own registries authoritative; producing results that become
institutional facts without admission; and — from §1 — serving as the durable home of evidence.

```
ResearchCampaign / Experiment   (institutional meaning, admitted)
        │ selects
        ▼
ExecutionPlan                    (ordinary Registry object; pins engine + app + schemas by hash)
        │ implemented by
        ▼
ADK Workflow                     (execution)
        │
Powerfarm Trajectory Adapter     (content-addresses evidence at capture)
        │
        ▼
candidates → admission Rules → Acts
```

A `ResearchCampaign` is **not** an ADK Workflow. An admitted Campaign or Experiment *selects* an
execution plan that an ADK Workflow implements. That boundary keeps scientific meaning in Powerfarm
and execution mechanics in the engine.

---

## 9. Compatibility test

Agent Engine support is real: `sessions/vertex_ai_session_service.py` and
`memory/vertex_ai_memory_bank_service.py`.

> **A Powerfarm-governed ADK App must remain deployable on Google Agent Engine without forking ADK.**

This is a good test because it is falsifiable and it fails loudly. It forbids: subclassing ADK
internals, depending on private module paths (`tools/_node_tool.py` remains the known private
surface), requiring a patched Runner, or assuming a local-only session/artifact backend.

---

## 10. Rulings

| ID | Question | Recommendation |
|---|---|---|
| **R-28** | Evidence captured from ADK must be content-addressed into CAS at capture time; never referenced by ADK event id or artifact coordinate | **Yes** — §1. Both are mutable views |
| **R-29** | `rewind_before_invocation_id` is never mirrored into Powerfarm | **Yes** — Powerfarm history has no rewind |
| **R-30** | Constitutional enforcement must not live in an ADK plugin | **Yes** — §3. Governed tool wrapper is the gate; plugins are sensors |
| **R-31** | A node wrapping a consequential tool must declare `rerun_on_resume = False`, and effect idempotency comes from the Powerfarm effect Act hash | **Yes** — §4 |
| **R-32** | `ToolConfirmation.confirmed` is never authorization | **Yes** — §5. Authority is the admitted review chain |
| **R-33** | No ADK identifier enters Powerfarm canonical identity | **Yes** — §6 |
| **R-34** | ADK registries are execution discovery, never the Powerfarm Registry | **Yes** |
| **R-35** | Ratify the four preimage changes; ADK adds none | **Yes** — §7 |
| **R-36** | Adopt the Agent Engine deployability test | **Yes** — §9 |

---

## 11. Where this leaves the order

The absorption did not change the constitution and did not change the preimages. It changed where
several boundaries sit, and it supplied the Engine Contract from evidence rather than from
imagination — which is what you wanted from treating ADK as an architectural input.

Suggested order now:

1. **Ratify the four preimage changes** (unblocked by §7).
2. **Admission architecture** — the companion contract, which now also carries execution provenance.
3. **Genesis promoter**, then Registry writer, then relations.
4. **Engine contract as an ordinary Registry object** — `ExecutionEngine{family: google.adk, version: 2.7.0, compatibility_profile}` and `ExecutionPlan`, both post-Genesis, both amendable without fork.

The one thing I would not defer is R-28. It is cheap now and expensive later: if the trajectory
adapter is built to link rather than copy, every piece of evidence captured before the fix is
permanently unreliable, and no amount of later correctness repairs it.
