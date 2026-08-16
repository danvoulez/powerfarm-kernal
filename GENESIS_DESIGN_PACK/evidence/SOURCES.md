# Evidence and provenance

This file records the sources still needed to reproduce or audit the active
institutional material. Historical reasoning remains available through Git; the
active tree keeps only evidence with a current claim to support.

## Current repository

| Item | Value |
|---|---|
| Branch at consolidation | `identity/principal-binding-acts` |
| Migrations | 18 SQL files, sealed; additions only |
| Registry candidate | 112 definitions, generated from executable content |
| Genesis state | candidate only; readiness gate blocked |

## Institutional documents

| Artifact | SHA-256 / status |
|---|---|
| `constitution/02_Research_Scheme_Compass.md` | `cf22899d069f1fcabd7c1a0232364e99f5f0bd1caa0c9a26c1194a98627d9db3` |
| Original supplied filename | `Untitled document.md`; byte-identical to the promoted source |
| Previous system specification v3.2 | `0082daf671fcac1727900460b1a7b5d040e7af3d4118f8c3e02fef606bb8b9f8`; removed from the active tree after consolidation into `SPECIFICATION.md` |
| Previous implementation plan v2 | `7e9ed4dfd215f40897bb194f8f9b16d3df1ff885679287878b3bce0e37327c34`; removed as the superseded macOS/Supabase deployment profile |

The Research Scheme hash is now canonical for the supplied v0.1 bytes. The
reconciliation in `vocabulary/research_scheme_reconciliation.md` can therefore
be checked directly against its source rather than against an absent transcription.

## Supplied implementation sources

| Artifact | SHA-256 |
|---|---|
| `powerfarm-kernal-main_3fc601c.zip` | `c90e1dc6d7732c19d828cb76f2294e8d63e82210f9ced34d9d4b1eeb29c08799` |
| `cloudflare-os-main_ba4036b.zip` | `63f67b39d927105bf723521a08dea616837be8d25cd9c64b8d9fa01049fedbfa` |
| `google-adk-2.7.0-offline.zip` | `3a8518e73a11f6395b319c9bb38bb7afd9229b8db3b3347a2cb1ad4c2dd5c530` |

The ADK compatibility contracts were derived from the offline wheel, including
event identity, rewind, workflow state, plugin callbacks, confirmation, session
state, artifacts, A2A conversion, registries, and Agent Engine services.

## External evidence not present

| Unknown | Consequence |
|---|---|
| Any admitted Genesis in an environment outside this repository | If one exists, the pre-Genesis change window is closed |
| Any live Powerfarm database | Legacy data and deployed migration state cannot be inferred |
| Live Cloudflare durable state | Re-keying and platform migration need a separate inventory |
| Golden Bridge private source and strict-routing invariants | M5 inference-gateway conformance remains externally unverified |
| Legal entity, jurisdiction, reviewers, public keys, and custody records | Genesis readiness correctly remains blocked |

Absence is recorded as absence. It is not filled with fixtures, placeholder keys,
or a synthetic ceremony.
