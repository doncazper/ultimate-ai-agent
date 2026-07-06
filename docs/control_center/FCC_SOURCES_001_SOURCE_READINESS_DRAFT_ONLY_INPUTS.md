# FCC-SOURCES-001 Source Readiness And Draft-Only Inputs

Status: Implemented
Baseline: v0.104.0 / 0.104.0
Primary surfaces: `/inbox`, `/today`, `/briefing`, and `/actions`

## Purpose

FCC-SOURCES-001 makes source readiness visible before connector authority
exists. Inbox, calendar, tasks, CRM-lite/manual notes, repo context, and
local-file context appear as backend-owned readiness states with safe refs,
missing contracts, blocked authorities, and draft-only proposal candidates.

This is a readability and proposal lane. It is not account auth, connector
runtime, background polling, raw source ingestion, send/write/archive/delete,
provider/model, memory-write, context-injection, shell/browser, or production
authority work.

## Implementation Evidence

- Backend route: `GET /control-center/sources/readiness`.
- Embedded surfaces: `GET /control-center/today/summary`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/actions/inbox`.
- Storage/source: `src/ultimate_ai_agent/core/storage/founder_loop.py`.
- API route owner: `src/ultimate_ai_agent/api/founder_loop.py`.
- Frontend binding:
  `apps/control-center/src/components/FounderLoopPanels.tsx::SourceReadinessCards`
  and `/inbox`.
- Frontend type:
  `apps/control-center/src/api/types.ts::FounderLoopSourceReadiness`.
- Verification:
  `scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py`,
  `tests/test_fcc_sources_001_source_readiness_draft_only_inputs.py`,
  `tests/test_control_center_api_routes.py`,
  `tests/test_founder_loop_storage_briefing.py`, and
  `apps/control-center/src/App.test.tsx`.

## Current Truth

Source Readiness exposes:

- `source_readiness_items` for inbox/email, calendar, tasks, CRM-lite/manual
  notes, repo context, and local-file context.
- Supported states: `ready`, `blocked`, `missing`, `metadata_only`,
  `unavailable`, and `not_configured`.
- `source_readiness_posture` with backend ownership, source counts, missing
  contract refs, blocked state refs, and blocked authority refs.
- `read_only_metadata_contracts` for backend-owned email/calendar metadata
  contract refs, metadata refs, evidence refs, audit/replay refs, and blocked
  runtime refs.
  Current contract refs are
  `fcc-email-metadata-read-only-contract:fcc-p1-008` and
  `fcc-calendar-read-only-contract:fcc-p1-007`.
- `source_readiness_proposal_candidates` for email read-only metadata contract,
  calendar read-only metadata contract, and account-auth boundary work.
- `connector_draft_proposals` for backend-owned email-response and
  calendar-hold draft proposal refs, with sends/writes/runtime blocked.
- Action Inbox projection of those candidates as
  `proposal_only_no_execution_path`.

All source proposal candidates are draft-only proposal/readability records.
Connector draft proposals are local safe-ref review artifacts. They are not
connector writes, live account states, external source reads, sent drafts, or
evidence that source access has been completed.
Read-only metadata contracts are contract evidence only. They are not live
email/calendar fetches, source ingestion, account auth, connector runtime,
message sends, archive/delete/label/move operations, calendar writes, or
test-account proofs.

## Authority Boundary

FCC-SOURCES-001 does not add account auth, background polling, raw body
ingestion, attachment download, send/write/archive/delete/label/move, calendar
write, connector runtime/write, provider/model calls, memory writes, hidden
context injection, shell/subprocess execution, browser automation, public beta,
public distribution, production readiness, or production authority.

React must not invent source readiness, connector state, account state, source
evidence, or operational maturity rank. The UI may display backend-owned
readiness/proposal state and local presentation filters only.

## Verification Commands

```bash
.venv/bin/python scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_sources_001_source_readiness_draft_only_inputs.py tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```
