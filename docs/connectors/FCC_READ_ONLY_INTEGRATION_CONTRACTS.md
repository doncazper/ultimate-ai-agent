# FCC Read-Only Integration Contracts

Status: contract-only implementation support for FCC-P1-007, FCC-P1-008, and
FCC-P1-009
Baseline: v0.103.0 / 0.103.0

FCC-P1-007 and FCC-P1-008 define paired Founder Command Center source-readiness
contracts for calendar and email metadata. FCC-P1-009 adds a draft-only email
response proposal contract for future inbox/follow-up review. They are
Python-core-owned contract models under
`src/ultimate_ai_agent/core/connectors/` and do not add connector runtime,
account authorization, network access, backend routes, Control Center controls,
dependencies, public distribution, or production authority.

These contracts are product-loop contracts, not live M121/M122 connector
runtime. M121 and M122 remain historical connector refresh precedents; this FCC
pair and the draft-only proposal contract use the same contract-only posture for
the Founder Command Center morning briefing, inbox, meeting-prep, and follow-up
lanes.

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
- `FCC_DRAFT_ONLY_EMAIL_PROPOSAL_CONTRACT`,
  `FCC_DRAFT_PROPOSAL_SAFE_REFS_ONLY`,
  `FCC_DRAFT_PROPOSAL_NO_SEND_WRITE_OR_ACCOUNT_AUTH`, and
  `FCC_DRAFT_PROPOSAL_CONNECTOR_RUNTIME_MISSING` for draft-only proposal
  posture.

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

## Draft-Only Email Response Proposal Contract

`FCCDraftEmailResponseProposalEnvelope` supports safe proposal, source email
metadata, thread, sender identity, recipient identity, account identity,
time-window, follow-up, draft summary, response outline, evidence,
source-readiness, audit, and replay refs. It includes purpose, intent, tone,
style, stale-state, missing-evidence, approval posture, blocked send/write
state refs, and next safe action text.

Denied:

- raw email body
- raw draft body
- subject text
- participant identifiers
- attachment names/downloads
- account authorization
- account write
- email fetch/search runtime
- reply/forward/send
- delete/archive/label write/move
- connector runtime
- model calls
- memory writes
- context injection
- backend routes
- Control Center controls
- background sync/refresh
- notification delivery
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
