# UAA CRM Local Command Center Plan

Status: implemented as M2 local-first CRM command center
Contract ref: `contract-ref:crm-local-command-center:m2:v1`
Verifier: `scripts/verify_crm_local_command_center.py`

## Scope

UAA CRM is a backend-owned local relationship command center for the single-user
Founder Loop. It makes relationship context, follow-ups, opportunities,
pipelines, communication drafts, proposal refs, reports, storage posture,
import/export previews, and authority blockers readable from Python core,
FastAPI, CLI, and Control Center.

This work is inspired by public CRM category patterns such as relationship
records, follow-up queues, pipelines, smart lists, reports, draft review, and
import/export workflows. No proprietary code, UI, copy, templates,
screenshots, data, branding, or private behavior is copied. No live web
fetching was used to implement this lane.

## Implemented

- Python core read model in `ultimate_ai_agent.core.crm.local_command_center`.
- Read-only FastAPI routes:
  - `GET /control-center/crm/summary`
  - `GET /control-center/crm/relationships`
  - `GET /control-center/crm/timeline`
  - `GET /control-center/crm/follow-ups`
  - `GET /control-center/crm/pipelines`
  - `GET /control-center/crm/smart-lists`
- Exact local mutation route:
  - `POST /control-center/crm/local-mutations`
- Repo-local CLI parity through `scripts/dev/uaa_crm.py`.
- Local JSON snapshot and JSONL receipt/event posture, with safe refs only in
  API/CLI/read-model output.
- Control Center `/crm` cockpit bound to backend-owned CRM summary data, with a
  visible non-authoritative fallback state when the backend is unavailable.
- Focused backend, API, frontend, product-language, route-manifest, and verifier
  coverage.

## Authority

The implemented local mutation lane is exact-scoped, idempotent,
approval-bound, auditable, safe-ref-only, and local-state-only. It can record
bounded local CRM state changes such as follow-up completion, follow-up status
changes, stage moves, and safe note summary refs after exact
`LocalApprovalAuthority` validation.

The Control Center does not mint authority. UI state is limited to presentation
concerns such as selected relationship, filters, and expanded sections.

## Explicitly Blocked

- Connector runtime.
- Connector writes.
- External CRM writes.
- Account sync.
- Contact import commit.
- Message sends.
- Calendar writes.
- Provider/model calls.
- Live web fetching.
- Browser automation.
- Background autonomy.
- Hidden context injection.
- Public beta, public distribution, production readiness, and production
  authority.

## Phase Mapping

| Prompt phase | Result |
|---|---|
| 01 product truth / feature map | Implemented as generic category pattern map with no proprietary copying or live web fetching. |
| 02 backend read model | Implemented in Python core with safe refs and blocked authority posture. |
| 03 Control Center cockpit | Implemented as `/crm` cockpit over backend-owned summary data. |
| 04 local storage seed | Implemented with local JSON snapshot and JSONL event/receipt posture. |
| 05 relationship timeline | Implemented as safe timeline refs. |
| 06 follow-up queue | Implemented as backend-owned queue refs and counts. |
| 07 smart lists | Implemented as safe smart-list definitions. |
| 08 pipeline board | Implemented as local pipeline/opportunity stage refs. |
| 09 exact local mutations | Implemented as `contacts/write` AuthorityLease plus approval/idempotency-bound local mutation receipts. |
| 10 communication drafts | Implemented as draft refs only; no sends. |
| 11 AI proposal layer | Implemented as deterministic proposal refs only; no model/provider calls. |
| 12 import/export | Implemented as redacted export and import preview only; no commit without later exact authority. |
| 13 reporting | Implemented as safe report refs and counts. |
| 14 connector read lanes | Blocked with authority report and unblock prompt. |
| 15 sends/writes plan | Blocked with authority report and unblock prompt. |
| 16 QA gate | Covered by `scripts/verify_crm_local_command_center.py`, focused pytest, OpenAPI verification, and frontend checks. |

## Inspection

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_crm.py inspect-summary --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_crm.py inspect-follow-ups --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_crm.py inspect-pipelines --pretty
PYTHONPATH=src .venv/bin/python scripts/verify_crm_local_command_center.py
```
