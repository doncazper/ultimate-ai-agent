# Local Browser Smoke Reporting

Status: Active for v0.21.1; local browser smoke reporting was added in v0.17.4.

This document defines the safe local browser smoke report format for the Web Control Center shell. A local browser smoke report is local-only, optional, non-authoritative, and never a substitute for tests, static verifiers, OpenAPI verification, or Foundation Gate.

v0.21.1 browser smoke reviewability includes `/evidence`, `/files`, and `/memory`: each route should show visibly mock, non-authoritative, redacted summary-only data, allow selecting alternate safe metadata cards, expose selected-card state, and show no mutation, raw-content, filesystem browsing, execution, auth, cookie, analytics, or production authority controls.

Allowed report scope:

- local frontend dev or preview URL on `localhost`, `127.0.0.1`, or `::1`.
- local backend API on `localhost`, `127.0.0.1`, or `::1` when the release prompt explicitly asks for it.
- Web Control Center routes already documented in `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`.
- mock fallback state when the local backend is unavailable.
- preview-only action form behavior, including the visible “no action was executed” result text.

Required safety boundaries:

- no authenticated browser profile.
- no Chrome authenticated profile control.
- no Computer Use.
- no external sites.
- no production backend.
- no screenshots with secrets.
- no screenshots, logs, URLs, route names, field values, or copied text containing credentials, tokens, cookies, API keys, private keys, personal data, prompts, file content, memory content, provider payloads, or approval secrets.
- do not include secrets.
- do not commit generated screenshots.
- do not commit browser traces, videos, reports, coverage, local logs, `.env` files, or build output.

Suggested report fields:

```text
baseline_version:
frontend_package_version:
local_url:
backend_mode: mock_fallback | local_backend
browser_tool: Browser
authenticated_profile_used: no
computer_use_used: no
external_site_used: no
screenshots_captured: no | sanitized_local_only
dashboard_loaded: pass | fail
runtime_readiness_loaded: pass | fail
foundation_gate_loaded: pass | fail
api_routes_loaded: pass | fail
approvals_loaded: pass | fail
remote_worker_boundary_loaded: pass | fail
mobile_planning_loaded: pass | fail
plugin_governance_loaded: pass | fail
action_preview_preview_only: pass | fail
mock_fallback_marked_mock: pass | fail | not_applicable
backend_connection_state_visible: pass | fail
api_base_local_only: pass | fail
forbidden_controls_absent: pass | fail
no_action_was_executed_visible: pass | fail
notes:
blockers:
```

Forbidden report claims:

- do not claim production readiness from browser smoke.
- do not claim model output, mock data, simulated data, or local browser observations as truth authority.
- do not claim runtime/model/provider execution.
- do not claim remote dispatch, mesh connection, mobile sensor access, plugin enablement, native build capability, Chrome authenticated profile control, or Computer Use automation.

If a local browser smoke run finds a failure, the report should describe the visible symptom and route only. It must not include raw secret-like input, raw backend validation payloads, user prompt content, file content, memory content, local filesystem paths outside this repository, credential refs, cookies, or screenshots with secrets.

Design governance references:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`
- `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`
