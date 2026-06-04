# Frontend Safety Policy

Status: Active for M18 Local Runtime Status + Manual Smoke Control Surface as of v0.22.0.

The Web Control Center shell is a display and preview surface. The Python Agent Core remains the brain and source of policy enforcement.

Frontend safety rules:

- UI controls may read status, route inventory, readiness reports, and summaries.
- The only action preview POST from the frontend is `/control-center/actions/preview`.
- M18 may reference the existing validation-only `POST /runtime/smoke-reports/validate` route for safe manual smoke report metadata validation.
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

## v0.20.1 M16 Trace Redaction Safety Hardening

v0.20.1 keeps M16 frontend-only and read-only. Selecting `View trace` may change visible selected trace detail and the selected-card marker only. It must not mutate data, execute actions, export traces, call telemetry systems, or bypass Python Agent Core authority.

Release review builds should prefer temporary Vite output paths such as `npm run build -- --outDir /tmp/uaa-control-center-review-dist` where practical. Generated frontend `dist`, `build`, `coverage`, `logs`, dependency, native, and cache artifacts must remain ignored and untracked.

## v0.21.0 M17 Evidence File Memory Viewer Safety

M17 adds frontend-only `/evidence`, `/files`, and `/memory` routes. These routes are read-only and summary-only. They may show evidence refs, file refs, memory refs, event refs, receipt refs, data classification labels, confidence status, staleness, conflict indicators, provenance summaries, redaction status, and safe messages.

They must not show raw prompts, raw secrets, raw file contents, raw memory contents, raw evidence payloads, raw credentials, raw provider payloads, or unreviewed tool arguments. They must not add file mutation, memory mutation, filesystem browsing, execution controls, approval execution, tool execution, backend routes, embeddings, vector DB, memory provider implementation, or production Control Center authority.

Memory is recall, not authority. Canonical files and governed source systems outrank memory.

## v0.21.1 M17 Evidence File Memory Viewer Safety Hardening

v0.21.1 hardens M17 only. Alternate mock evidence, file ref, and memory ref entries must remain visibly mock, non-authoritative, redacted summary-only, and safe-ref based. Selected cards must expose accessible selected-state reviewability for browser smoke and tests.

This patch adds no M18 surface, backend API route, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, raw secret/prompt/file/memory/evidence/credential/provider payload display, embeddings, vector DB, memory provider implementation, runtime execution, model/provider calls, remote execution, mobile sensor access, plugin enablement, dependencies, auth, cookies, analytics, SaaS SDKs, native build workflow, or production Control Center authority.

## v0.22.0 M18 Runtime Smoke UI Safety

M18 adds frontend-only `/runtime/local` and `/runtime/manual-smoke` routes. `/runtime/local` is read-only local runtime status. `/runtime/manual-smoke` is validation-only manual smoke report summary display.

These routes may show readiness status, capability matrix summaries, manual smoke report refs, fixed prompt hash values, validation reason codes, redaction status, and non-authoritative warnings.

They must not add backend routes, runtime execution, manual smoke execution, model/provider calls, local runtime provider integrations, remote execution, mobile sensor access, plugin enablement, OpenWebUI integration, raw smoke report display, raw prompts, raw response bodies, credentials, provider payloads, dependencies, or production Control Center authority.

## v0.40.0 M36 File Review Surface Safety

M36 adds frontend-only `/files/review`. The route is review-only and may show
redacted review packets, redacted previews, redaction summaries, exact binding
refs, review-only decision status, approval gate contract status, and receipt
plan metadata.

The surface must show mock fallback data as mock and non-authoritative. It must
not include approve, deny, submit, save, mark-reviewed, export, download,
copy-raw, file picker, browse, upload, root selector, raw file open, context
proposal, context injection, memory write, execute, run, tool, or model-call
controls.

M36 adds no approval capture, approval persistence, backend routes, raw file
display, raw file storage, full-file reads, context proposal, context
injection, memory writes, export, execution, dependencies, or production
Control Center authority. M37 remains planned/provisional. M38 remains
planned/provisional.

## v0.40.1 M36 File Review Surface Hardening

v0.40.1 keeps `/files/review` frontend-only and review-only. It requires safe
refs only, rejects private path-shaped refs, raw path-shaped labels, and
traversal fragments in M36 static checks, and requires that packet selection or
expansion make no mutating request.

The surface still adds no approval capture, approval persistence, backend
routes, raw file display, context proposal, context injection, memory writes,
export/download/copy-raw controls, execution controls, dependencies, or
production Control Center authority. M37 remains planned/provisional.

## M19 Mobile Safety Boundary

Frontend code must not add mobile sensor APIs, native mobile endpoints, Android
or iOS app scaffolding, OS permission prompts, background services, notification
permission requests, or mobile approval execution. M19 is Mobile Companion
Contract/API Planning only. Device Capability Broker is required before sensors,
capture cannot silently become memory, and phone/mobile is not the agent brain.
