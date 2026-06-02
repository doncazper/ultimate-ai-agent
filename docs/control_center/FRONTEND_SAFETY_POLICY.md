# Frontend Safety Policy

Status: Active for v0.20.0 / M16 Event Timeline + Run/Receipt Trace Viewer.

The Web Control Center shell is a display and preview surface. The Python Agent Core remains the brain and source of policy enforcement.

Frontend safety rules:

- UI controls may read status, route inventory, readiness reports, and summaries.
- The only POST from the frontend is `/control-center/actions/preview`.
- Action preview must never be treated as execution, approval, credential resolution, remote dispatch, model invocation, plugin enablement, or sensor access.
- Mock fixtures must be visibly marked mock and non-authoritative.
- Approval, receipt, and event viewer fixtures must be redacted summary-only and must not show raw secrets, prompt bodies, file bodies, memory contents, or provider payloads.
- Event timeline and run/receipt trace fixtures must be redacted summary-only and must show safe refs and safe messages only.
- API base URLs must be local-only: relative path, localhost, 127.0.0.1, or loopback IPv6.
- External absolute API URLs, public/private non-loopback hosts, URL credentials, and secret-like API base strings must be blocked or rejected.
- Unknown/checking, live, degraded, offline-safe, and mock fallback connection states must be visible and safe.
- Secret-like user input and backend errors must be sanitized before display.
- The frontend must not read cookies, local storage, session storage, credentials, keychains, files, mobile sensors, camera, microphone, location, browser profiles, or OS signing material.
- The frontend must not use browser credential APIs, service workers, IndexedDB, CacheStorage, notification/push APIs, or clipboard writes.
- The frontend must not include analytics, auth SDKs, payment SDKs, SaaS SDKs, model/provider SDKs, browser automation, native build tooling, mobile project files, or background services.
- `scripts/verify_control_center_frontend.py` is the canonical static frontend safety verifier and is run by `scripts/verify_all.py` and Foundation Gate.
- `scripts/verify_control_center_browser_smoke_readiness.py` verifies that local browser smoke readiness and reporting remain documented, static, manual, local-only, and non-authoritative.

Allowed local tooling:

- npm package management inside `apps/control-center`.
- Vite dev server on localhost.
- React rendering.
- TypeScript typechecking.
- Vitest and Testing Library.
- Browser verification against local dev targets when explicitly approved by the milestone prompt.
- CI frontend checks inside `apps/control-center`: `npm ci`, typecheck, lint, tests, and build.

Local browser smoke readiness:

- manual local browser smoke only.
- local-only targets: `localhost`, `127.0.0.1`, and `::1`.
- no authenticated browser profile.
- no Chrome authenticated profile control.
- no Computer Use.
- no external sites.
- no production backend.
- no screenshots with secrets.
- non-authoritative verification only.

Off-limits in M14/v0.18.1:

- Chrome authenticated profile control.
- Computer Use automation.
- Build iOS Apps and Build macOS Apps plugins.
- App Store Connect, signing identities, keychains, provisioning profiles, and entitlements.
- MCP/A2A runtime delegation.
- external network services.
- external API hosts.
- auth, credentials, cookies, Authorization headers, or API keys.
- analytics/SaaS SDKs.
- production persistence.

## v0.18.0 M14 Connection Safety

v0.18.0 implements local backend connection stabilization only:

- relative API bases are allowed.
- localhost, 127.0.0.1, and loopback IPv6 API bases are allowed.
- external absolute API bases are unsupported.
- secret-like query strings or credentials in an API base are rejected.
- mock fallback remains non-authoritative.
- partial backend failures show degraded state.
- OpenAPI path count remains `74`.

## v0.18.1 M14 Connection Safety Hardening

v0.18.1 strengthens the same M14 boundary:

- public IPs, private LAN IPs, and non-loopback hostnames are blocked as API bases.
- URL credentials in API bases are rejected.
- broad secret-like query parameter names are rejected.
- Vite proxy targets and env examples are statically checked for unsafe API base values.
- unknown/checking connection states are explicit.

M15 Approval Queue + Receipt/Event Viewer UI is implemented in v0.19.0 and preserves these safety boundaries:

- no execution.
- no approval authority bypass.
- no plugin enablement.
- no mobile sensor control.
- no remote dispatch.
- no model/provider invocation.
- no sensitive browser storage, cookies, credential APIs, camera, microphone, location, notification, push, service worker, IndexedDB, CacheStorage, or clipboard-write APIs.
- no raw receipt/event/prompt/file/memory display.
- no receipt or event mutation endpoints.

## v0.18.2 Design Governance Boundary

Control Center UI changes must follow:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

Design governance does not add frontend behavior, dependencies, Tailwind, shadcn, design system packages, icon packs, analytics, auth, payment SDKs, design tool integration, Chrome authenticated profile control, Computer Use, plugin enablement, mobile sensor access, remote dispatch, model/provider calls, or production authority.

## v0.18.3 CCC Web Boundary

v0.18.3 clarifies CCC Web as the current TypeScript web Control Center and CCC as the broader Control Center Clients family. OpenWebUI is the preferred conversational web shell and Open Design does not replace OpenWebUI.

The frontend safety boundary is unchanged: no OpenWebUI integration, deployment config, new frontend feature, backend route, native CCC implementation, Android app, iOS app, macOS app, mobile sensor access, OS permission integration, native build workflow, signing/store workflow, or production authority is added.

## v0.19.0 M15 Approval Receipt Event Viewer Safety

M15 adds frontend-only `/approvals`, `/receipts`, and `/events` routes. These routes are read-only and preview-only. `scripts/verify_control_center_frontend.py` rejects dangerous M15 mutation endpoints, active approval/action button labels, sensitive browser APIs, unsafe dependencies, secret-like fixtures, and generated artifacts. Foundation Gate criterion `m15_approval_receipt_event_ui_safe` verifies the same boundary.

## v0.19.1 M15 Approval Receipt UI Safety Hardening

v0.19.1 keeps M15 frontend-only and adds no backend API route or OpenAPI path count change. It hardens the same boundary by requiring approval authority copy, identifier-only approval-ref copy, Python Agent Core approval authority copy, redacted receipt detail copy, redacted event detail copy, raw M15 review field rejection, credential-like review field rejection, and Foundation Gate coverage for authority-bypass and raw-sensitive-field drift.

## v0.20.0 M16 Event Timeline Trace Viewer Safety

M16 adds frontend-only `/events/timeline`. The route is read-only and summary-only. It may show event refs, run refs, correlation refs, receipt refs, evidence refs, relation refs, status, timestamps, actor summaries, source summaries, redaction status, and safe messages.

It must not show raw prompts, raw secrets, raw file contents, raw memory contents, raw credentials, raw provider payloads, raw event payload dumps, raw receipt payload dumps, or unreviewed tool arguments. It must not add execution controls, approval execution, tool execution, trace export, production telemetry export, external observability integration, OpenTelemetry export, cloud traces, backend routes, or production Control Center authority.
