# FCC Read-Only Integration Contracts

Status: contract-only implementation support for FCC-P1-007 and FCC-P1-008
Baseline: v0.102.3 / 0.102.3

FCC-P1-007 and FCC-P1-008 define paired Founder Command Center source-readiness
contracts for calendar and email metadata. They are Python-core-owned contract
models under `src/ultimate_ai_agent/core/connectors/` and do not add connector
runtime, account authorization, network access, backend routes, Control Center
controls, dependencies, public distribution, or production authority.

These contracts are product-loop contracts, not live M121/M122 connector
runtime. M121 and M122 remain historical connector refresh precedents; this FCC
pair uses the same contract-only posture for the Founder Command Center morning
briefing, inbox, meeting-prep, and follow-up lanes.

## Shared Vocabulary

Both contracts use:

- `source-readiness-ref:*` for missing/manual/fixture-only source posture.
- `evidence-ref:*` for bounded evidence summaries.
- `audit-ref:*` and `replay-ref:*` for inspectable audit/replay posture.
- `missing-runtime-ref:*` and `blocked-runtime-ref:*` for future connector
  milestone dependency.
- `FCC_READ_ONLY_METADATA_CONTRACT_ONLY`, `FCC_SAFE_REFS_ONLY`,
  `FCC_CONNECTOR_RUNTIME_MISSING`, and
  `FCC_NO_AUTH_FETCH_WRITE_OR_BACKGROUND_COLLECTION` as shared reason codes.

## Calendar Contract

`FCCCalendarEventMetadataEnvelope` supports safe refs for event, time window,
attendee identity, account identity, source readiness, evidence, audit/replay,
and meeting-prep summary posture.

Denied:

- account authorization
- network fetch
- calendar read/search runtime
- event create/update/delete
- invite send
- meeting-link exposure
- location exposure
- event title/body storage
- raw invite body
- background collection
- attachment download
- connector runtime
- model calls
- memory writes
- context injection
- backend routes
- Control Center controls
- dependencies
- beta/public/production claims

## Email Contract

`FCCEmailMetadataEnvelope` supports safe sender, thread, time-window, label
summary, source readiness, evidence, audit/replay, inbox summary, and follow-up
summary refs.

Denied:

- raw body
- subject text
- participant identifiers
- attachment names/downloads
- account authorization
- email fetch/search runtime
- send/delete/archive/label write
- connector runtime
- model calls
- memory writes
- context injection
- backend routes
- Control Center controls
- dependencies
- beta/public/production claims

## Runtime Dependency

The pair is intentionally blocked from live source access until a later exact
connector runtime milestone defines account authorization, source allowlists,
data minimization, redaction, audit/replay, approval posture, rollback or
safe-disable posture, and focused verifiers.

Current safe next action: use these contracts only to validate metadata-only
fixtures and source-readiness posture for the Founder Command Center product
loop.
