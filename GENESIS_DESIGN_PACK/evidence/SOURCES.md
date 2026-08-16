# Evidence

Exactly what this pack was designed against. Every claim in the pack was verified against these
artifacts at these hashes; anything else is inference and is marked as such where it appears.

---

## Repository

| Item | Value |
|---|---|
| Inspected commit | `b3de7c7fb83b7848f9f7b53ffe85c966d4556c9f` |
| Commit subject | *Admit principal bindings through Acts, not by hand* |
| Branch | `identity/principal-binding-acts` (1 ahead of local `main`) |
| Migrations | 16, sealed — only additions |

## Documents

| File | SHA-256 |
|---|---|
| `Powerfarm System Specification v3.md` (v3.2, **normative**) | `0082daf671fcac1727900460b1a7b5d040e7af3d4118f8c3e02fef606bb8b9f8` |
| `Powerfarm Implementation Plan 2.md` | `7e9ed4dfd215f40897bb194f8f9b16d3df1ff885679287878b3bce0e37327c34` |
| `genesis/genesis.yaml` | `2e43a3bf4ba0a84e3fb44ce4e7aa33751e9bdbb9d4af4169cc22911840159c12` |

## Execution pack (2026-08-16) and its sources

The Fresh Agent Execution Pack self-verified: `shasum -c SHA256SUMS.txt` → **19/19 OK**.

| Artifact | SHA-256 |
|---|---|
| `powerfarm-kernal-main_3fc601c.zip` | `c90e1dc6d7732c19d828cb76f2294e8d63e82210f9ced34d9d4b1eeb29c08799` |
| `cloudflare-os-main_ba4036b.zip` | `63f67b39d927105bf723521a08dea616837be8d25cd9c64b8d9fa01049fedbfa` |
| `google-adk-2.7.0-offline.zip` | `3a8518e73a11f6395b319c9bb38bb7afd9229b8db3b3347a2cb1ad4c2dd5c530` |

The pinned kernel snapshot is **content-identical** to the inspected working tree: `diff -r` yields
zero tracked-file differences.

## Google ADK

| Item | Value |
|---|---|
| Offline pack SHA-256 | `3a8518e73a11f6395b319c9bb38bb7afd9229b8db3b3347a2cb1ad4c2dd5c530` |
| Wheel | `google_adk-2.7.0-py3-none-any.whl` |
| Modules inspected | 675 `.py` files, extracted and read directly |

Verified from source, not documentation: `Event` fields and `Event.new_id()` (UUID, not content);
`EventActions.rewind_before_invocation_id` and `events/_rewind_events.py`;
`apps/_configs.py` resumability contract; `workflow/_base_node.py` (`rerun_on_resume`, schemas);
`_node_status.py`, `_node_state.py`, `_workflow.py` (`sequence_barrier`, `max_concurrency`);
`plugins/base_plugin.py` (15 callbacks, short-circuit semantics);
`tools/tool_confirmation.py`; `sessions/session.py` and `state.py` scopes;
`artifacts/base_artifact_service.py` (versioning and `delete_artifact`);
`agents/invocation_context.py`; the A2A converters; ~8 registries;
`sessions/vertex_ai_session_service.py` and `memory/vertex_ai_memory_bank_service.py`.

## Research Scheme / Compass

Supplied by Dan on 2026-08-16 as *Powerfarm Research Scheme v0.1*. Identified (R-10) as the document
`01_Powerfarm_Platform_Plan_v2.md` cites throughout as "Compass §N" — all nine citations resolve,
and `§29.9` = section 29, rule 9 is decisive.

> **No canonical file hash exists yet.** The copy in `constitution/02_Research_Scheme_Compass.md`
> is a transcription of what was supplied. Before it is treated as normative, replace it with the
> canonical source and record its hash here.

## Not verified — absent from all supplied material

| Item | Consequence |
|---|---|
| `danvoulez/lab-mistral-rs-gateway` (Golden Bridge) | Private; zero references anywhere in the kernel repo. Every Phase 7 / strict-routing claim is unverifiable |
| Any live Powerfarm database | Legacy `relations` rows cannot be checked |
| The live Cloudflare account | Email-keyed durable state cannot be inventoried |
| Whether `3fc601c` exists as a merge on `origin/main` | Local refs say no; needs a fetch. Provenance only, non-blocking |

## Reproducing the SQL conformance locally

PostgreSQL **15+** is required (`security_invoker` is 15+; CI uses 17). On macOS, export `LC_ALL=C`
before `initdb`/`pg_ctl` or the postmaster fails with *"postmaster became multithreaded during
startup"*. Migrations additionally expect an `auth.users` table and the roles `anon`,
`authenticated`, `service_role`, `powerfarm_worker`, `supabase_admin` to exist — a Supabase project
supplies these; a bare instance does not.
