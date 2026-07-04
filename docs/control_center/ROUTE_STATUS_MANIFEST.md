# Control Center Route Status Manifest

Status: active UAA-P1-030 route status manifest

The route status manifest is the route-status truth index for visible Control
Center actions. It records the owner, auth posture, side-effect class,
UAA-P1-080 route classification, risk class, OpenAPI operation id, release
status, UI surface, approval requirement, and evidence/audit output for each
visible action and required operator shell surface.

Machine-checkable source:

```text
docs/control_center/route_status_manifest.json
```

Source map:

```text
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
```

Product language contract:

```text
docs/control_center/PRODUCT_LANGUAGE_RULES.md
```

Operator readiness taxonomy:

```text
docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md
```

This manifest does not add runtime authority, backend routes, frontend
controls, shell/subprocess behavior, unrestricted network or browser automation,
connector writes, plugin runtime import, mobile control, autonomous background
execution, public distribution, or production readiness claims.

Route classifications are inventory posture only. `public_metadata`,
`local_readonly`, `local_sensitive`, and `mutating_requires_authority` describe
how a visible route should be treated by later API perimeter work; they do not
implement auth, middleware, headers, CORS, idempotency, rate limits, or new
runtime authority.

## Release Status Values

| Status | Meaning |
|---|---|
| `status_available_not_completion` | The visible action can display local status or route inventory, but it is not completion evidence. |
| `preview_available_not_execution` | The visible action can request a policy preview, but it cannot execute, grant, dispatch, or enable anything. |
| `partial_backend_not_product_ready` | Some backend routes exist, but the product loop or UI binding is incomplete. |
| `founder_loop_v1_proofed` | The exact Founder Loop V1 route behavior is backend-owned, receipt-backed, evidence-visible, and proofed; this is not public release or production readiness. |
| `mock_only_not_product_ready` | The visible surface is backed by mock or planning data only. |
| `local_ui_state_only_not_evidence` | The visible action changes local UI state only and does not create release evidence. |
| `blocked_missing_backend` | Required backend route(s), authority binding, or evidence output are missing. |

These manifest values map to the canonical operator-readiness statuses in
`docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`: `status_only`,
`preview_only`, `partial`, `shipped`, `mock_only`, `local_ui_state_only`, and
`blocked`.

No status in this manifest means public release readiness, broad autonomy,
production runtime authority, model/provider authority, shell authority,
connector write authority, plugin runtime authority, or mobile authority.

## Required Surfaces

The JSON manifest covers these UAA-P0-007 surfaces:

- Setup Assistant
- Today
- Inbox
- Action Inbox
- Morning Briefing
- CRM
- Memory Review
- Chat Local Operator
- Plans
- Models
- Approvals
- Files
- Runtime
- Evidence
- Settings

Each surface has explicit current backend routes, missing backend route refs,
authority posture, approval requirement, evidence/audit output, and release
status. Unimplemented or unsafe surfaces are marked as blocked, partial,
mock-only, or local-UI-state-only.

## Visible Actions

The JSON manifest covers the current visible Control Center routes and actions:

- Setup Assistant, Overview, Dashboard, and Operator Loop navigation
- Today, Inbox, Actions, Briefing, CRM, Chat Local Operator, Plans, Models, Runtime,
  Foundation Gate, API Routes, Approvals,
  Receipts, Events, Timeline, Evidence, Files, File Review, Context Proposals,
  Memory, Local Runtime, Manual Smoke, Remote Workers, Mobile Planning, Plugin
  Governance, Settings, and Differentiators navigation
- Action Preview submission
- Action Inbox approval-envelope/state-change posture inspection
- Morning Briefing source-readiness and missing-contract posture inspection
- CRM M1 fixture-only shell inspection with backend CRM routes, backend CRM
  read models, connector runtime, writes, sends, calendar writes, provider/model
  calls, live web, browser automation, public release, and production authority
  blocked
- Memory Review candidate provenance/source/evidence posture inspection
- Local detail-card selection
- File Review approve/deny review-only local state

Visible actions that do not call a backend route are explicitly marked as local
UI state, mock-only, or missing backend. Visible actions that map to backend
routes list the exact OpenAPI operation id and side-effect class.

## Verification

Required verification lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
```

The pytest lane compares manifest route entries with OpenAPI operation ids and
API manifest side-effect classes. The frontend verifier confirms that current
Control Center routes have manifest entries and that unsafe or unimplemented
actions are not marked as ready.

## Rollback

Rollback is to remove this document, remove
`docs/control_center/route_status_manifest.json`, remove the tests/verifier
rules that require it, and move UAA-P1-030 out of Done on the Kanban board. No
runtime state, route, authority, migration, or persistent user data is changed.
