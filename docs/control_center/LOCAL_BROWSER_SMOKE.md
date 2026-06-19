# Local Browser Smoke Readiness

Status: active UAA-P1-032 browser smoke readiness
Baseline: v2.0.0 / 2.0.0

This document defines local browser smoke readiness for the Web Control Center
shell. It is local-only, optional, non-authoritative, and never a source of
runtime authority, public distribution claims, or production readiness claims.
UAA-P1-032 adds first product loop readiness coverage using safe mocked or
local-only fixtures where prerequisites are unavailable.

Allowed targets:

- local frontend dev server on `localhost`, `127.0.0.1`, or `::1`.
- local frontend preview server on `localhost`, `127.0.0.1`, or `::1`.
- local backend API on `localhost`, `127.0.0.1`, or `::1`.
- static build output served by a local preview command.

Required safety boundaries:

- no authenticated browser profile.
- no Chrome authenticated profile control.
- no Computer Use.
- no external sites.
- no production backend.
- no screenshots with secrets.
- no plugin enablement.
- no native/mobile workflow.
- no model, provider, runtime, remote worker, or mobile sensor execution.
- no production Control Center authority.

Manual local browser smoke checklist:

- dashboard loads.
- runtime readiness panel loads.
- Foundation Gate panel loads.
- API route inventory loads.
- approvals summary loads.
- evidence viewer loads.
- file reference viewer loads.
- memory viewer loads.
- remote worker boundary loads.
- mobile planning summary loads.
- plugin governance summary loads.
- action preview form is labeled preview-only.
- risk level input is visible and still preview-only.
- no execute button.
- no plugin enable button.
- no mobile sensor button.
- no remote dispatch button.
- mock data marked mock when backend data is unavailable.
- backend connection state is visible as online, degraded, or mock fallback.
- API base display remains local-only and does not include secret-like values.
- blocked preview results remain non-authoritative and show no action was executed.

## UAA-P1-032 First Product Loop Readiness

State meanings for browser smoke reports:

- `real`: local UI and local backend evidence are both available for the exact
  step under test.
- `mocked`: the UI renders safe mock or summary fixtures and marks them as
  non-authoritative.
- `skipped`: a local prerequisite is unavailable and the report says so.
- `blocked`: required route, authority binding, evidence output, or reviewed
  local prerequisite is missing.

| Product loop step | Browser smoke state | UI or route evidence | Blocker or skip condition |
|---|---|---|---|
| Open Control Center | mocked/local-only | `/dashboard` renders Dashboard overview, backend state, local API base, and mock fallback copy when reads fail. | None for mock fallback smoke; local backend availability can be skipped. |
| Inspect runtime health and model readiness | mocked/local-only | `/runtime` and `/runtime/local` show Runtime readiness, local runtime status, claim/evidence wording, and no runtime execution controls. | Reviewed live model evidence remains a separate M167 prerequisite. |
| Select or approve local GGUF model | blocked | `/models` shows accessible blocked/denied state copy; route status manifest records missing GGUF selection, approved GGUF readiness, llama.cpp settings, and rollback routes. | Dedicated model selection/approval UI and reviewed GGUF evidence are not implemented. |
| Use chat shell through UAA `/v1` | blocked | `/chat` shows accessible blocked/denied state copy; `/runtime/manual-smoke` shows safe manual smoke report summaries; OpenWebUI remains the current local shell. | Dedicated CCC chat composer, auth status, receipt summary, and tools/functions/streaming denial UI are missing. |
| Create a task decomposition plan | blocked/partial | `/plans` shows accessible blocked/denied state copy; `/action-preview` can preview policy only; task decomposition backend routes exist but no product Plans loop is present. | Dedicated Plans DAG/status summary, durable run lifecycle summary, and replay summary routes are missing. |
| Approve one safe registered capability | mocked/partial | `/approvals` shows read-only/preview-only approval summaries and no approval grant from the UI. | Product approval capture/revoke UI and evidence binding remain scoped to later M172 work. |
| Inspect receipt/audit/latency/rollback status | mocked/partial | `/receipts`, `/events/timeline`, `/evidence`, `/foundation-gate`, and `/api-routes` show redacted summary evidence. | Release evidence index, latency report summary, rollback status, and run receipt trace routes are incomplete. |

The first product loop is therefore not claimed complete by browser smoke. The
smoke lane proves that the shell loads, visible controls are readable and safe,
mocked/local-only states are labeled, and blocked prerequisites are not hidden.
Operator-critical flows must use human-readable panels, safe refs, and explicit
blocked/skipped/partial states; raw JSON must not be the primary UI.

Automated readiness coverage:

```bash
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_browser_smoke_readiness.py
```

The Vitest browser-smoke readiness case in `apps/control-center/src/App.test.tsx`
covers the mocked/local-only happy path and asserts the blocked prerequisites
remain visible and non-authoritative.

Use `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md` for the safe local browser smoke report format. Reports must be local-only, non-authoritative, and free of secrets, raw prompts, file content, memory content, credentials, cookies, screenshots with secrets, browser traces, and generated artifacts.

The browser smoke procedure may use Browser plus Build Web Apps only when a future release prompt explicitly asks for local UI verification. Chrome authenticated profile control, Computer Use automation, iOS/macOS build plugins, external SaaS browser services, hosted preview services, production deployments, and screenshots containing secrets remain off-limits.

Design governance references for future visual QA:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`
- `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`
