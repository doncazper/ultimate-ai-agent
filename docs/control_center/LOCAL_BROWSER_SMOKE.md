# Local Browser Smoke Readiness

Status: Active for v0.19.0; local browser smoke guidance was added/polished in v0.17.4.

This document defines manual local browser smoke readiness for the Web Control Center shell. It is local-only, optional, non-authoritative, and never part of CI or Foundation Gate browser execution.

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
