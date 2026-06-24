# FCC-INBOX-001 Action Inbox And Approval Envelope UX

Status: Implemented
Baseline: v0.104.0 / 0.104.0
Primary surface: `/actions` Action Inbox
Related surface: `/inbox` source-readiness and communication triage posture

## Purpose

FCC-INBOX-001 makes Action Inbox items easier to review before any decision by
using one backend-owned grammar for approval envelopes and receipt visibility.
It is a product-readability lane over existing Founder Loop storage/API
contracts, not a new action-execution lane.

The implemented path is `/actions`. The `/inbox` route remains the
source-readiness and communication triage posture surface; the application
chrome may describe both routes under the broader Action Inbox loop, but
backend truth for reviewable Action envelopes is `GET /control-center/actions/inbox`.

## Implementation Evidence

- Backend read model:
  `src/ultimate_ai_agent/core/storage/founder_loop.py::_action_approval_envelope_read_model`
  and
  `src/ultimate_ai_agent/core/storage/founder_loop.py::_action_receipt_visibility_read_model`.
- API/read route: `GET /control-center/actions/inbox`.
- Decision routes stay backend-owned and receipt-backed:
  `POST /control-center/actions/{action_id}/approve`,
  `POST /control-center/actions/{action_id}/edit`,
  `POST /control-center/actions/{action_id}/reject`,
  `POST /control-center/actions/{action_id}/defer`, and
  `GET /control-center/actions/{action_id}/receipt`.
- The exact local micro-lane remains separately bounded:
  `POST /control-center/actions/{action_id}/local-task/commit`.
- Frontend types:
  `apps/control-center/src/api/types.ts::FounderLoopActionApprovalEnvelope`
  and
  `apps/control-center/src/api/types.ts::FounderLoopActionReceiptVisibility`.
- Frontend cards:
  `apps/control-center/src/components/FounderLoopPanels.tsx::ApprovalEnvelopeCard`
  and
  `apps/control-center/src/components/FounderLoopPanels.tsx::ReceiptVisibilityCard`.
- Verification:
  `scripts/verify_fcc_inbox_001_approval_envelope_ux.py`,
  `scripts/verify_operational_maturity.py`,
  `tests/test_fcc_inbox_001_approval_envelope_ux.py`,
  `tests/test_founder_loop_storage_actions.py`,
  `tests/test_founder_loop_storage_crud.py`,
  `tests/test_control_center_api_routes.py`, and
  `apps/control-center/src/App.test.tsx`.

## Current Truth

Action Inbox now renders backend-classified lanes for ready decisions, approved
local-task items, authority-blocked items, expired/stale items, receipt-recorded
items, and proposal-only/no-execution items.

Each backend-owned Action Inbox item can expose:

- action kind
- exact scope
- risk class
- side-effect class
- approval requirement
- expiry/staleness
- idempotency ref
- expected receipt refs
- rollback/safe-disable posture
- blocked authority refs
- evidence refs
- decision receipt ref
- local task ref
- local task commit receipt ref
- Evidence Timeline event ref
- replay posture
- conflict posture
- missing-field states

The read-model source must be `python_core_action_inbox_read_model` and
`backend_owned` must be true before the UI treats the envelope and receipt
visibility as authoritative. Missing or degraded data falls back to
`mock_fallback_non_authoritative`, marks the cards unavailable, and does not
expose local task commit controls.

## Authority Boundary

FCC-INBOX-001 does not add generic action execution, connector writes,
shell/subprocess execution, provider/model authority, memory writes, context
injection, browser automation, plugin runtime import, remote execution, public
beta, public distribution, production authority, or operational maturity rank
promotion.

Action Inbox remains rank 3 overall in
`docs/control_center/operational_maturity_manifest.json`. The existing
`local_task_create` lane remains the only rank 5 local micro-lane, and it is
still exact-scope, approval-bound, idempotent, receipt-backed, evidence-backed,
and safe-disable/rollback-posture guarded.

## Verification Commands

```bash
.venv/bin/python scripts/verify_fcc_inbox_001_approval_envelope_ux.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_inbox_001_approval_envelope_ux.py tests/test_founder_loop_storage_actions.py tests/test_founder_loop_storage_crud.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```
