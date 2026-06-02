# Web Control Center Shell

Status: Active for v0.19.0 / M15 Approval Queue + Receipt/Event Viewer UI.

M13 adds a local TypeScript React/Vite shell under `apps/control-center/` for reading existing backend Control Center and runtime readiness APIs. It is the first web UI surface for the future Control Center, but it is not a production Control Center and it has no authority to execute actions.

Implemented shell behavior:

- renders read-only dashboard, runtime readiness, Foundation Gate, API route, approval queue, receipt viewer, event viewer, remote worker, private mesh, mobile planning, and plugin governance summaries.
- submits exactly one preview-only request type to `/control-center/actions/preview`.
- labels action preview as preview-only and displays blocked decisions as non-executed safety results.
- exposes the action preview risk level as policy metadata only.
- provides route-level headings and accessible loading, empty, error, and mock fallback states for local browser smoke review.
- falls back to clearly marked mock data when the local backend is unavailable.
- displays unknown/checking, backend online, degraded, offline-safe, and mock fallback connection states.
- sanitizes secret-like frontend errors before display.
- uses relative API URLs by default.
- may use `VITE_UAA_API_BASE_URL` for local development with a local backend only.
- allows only relative, localhost, 127.0.0.1, and loopback IPv6 API bases.
- blocks external absolute API bases, public/private non-loopback hosts, non-loopback hostnames, URL credentials, and secret-like API base strings.

Non-goals:

- no backend route changes beyond version metadata.
- no public execution API.
- no runtime/model/provider call.
- no remote dispatch.
- no mobile/native app.
- no sensor access.
- no plugin enablement.
- no Chrome authenticated profile control.
- no Computer Use automation.
- no iOS/macOS build workflow.
- no production authority.

The shell is allowed to use local npm dependencies for React, Vite, TypeScript, Vitest, and Testing Library only. `node_modules`, `dist`, coverage output, `.env` files, and native/mobile build files are not release artifacts.

v0.17.4 adds local browser smoke UX polish and safe reporting documentation only. Frontend CI still covers install, typecheck, lint, tests, and build; static verifiers cover frontend safety plus manual local browser smoke readiness/reporting; and Foundation Gate checks the CI/static/browser-readiness boundary. It does not add backend API paths, execution controls, sensitive browser storage, mobile sensor APIs, plugin enablement controls, browser automation, Chrome authenticated profile control, Computer Use automation, native build workflows, dependencies, or production Control Center authority.

## v0.18.0 M14 Connection Stabilization

v0.18.0 implements M14 local backend connection stabilization:

- API base URL policy is local-only.
- external absolute API URLs are blocked.
- secret-like API base URL strings are rejected and not displayed.
- live, degraded, and mock fallback states are visible.
- partial backend failures show degraded state and call out non-authoritative mock fallback panels.
- OpenAPI path count remains `74`; no backend route is added.

M14 kept local backend connection stabilization separate from M15. M15 is implemented in v0.19.0 as read-only/preview-only frontend inspection panels and adds no backend API routes, execution, approval authority, plugin enablement, remote dispatch, mobile sensor control, model/provider calls, auth, credentials, cookies, analytics/SaaS SDKs, production persistence, external API hosts, dependencies, or production Control Center authority.

## v0.18.1 M14 Connection Safety Hardening

v0.18.1 hardens M14 without changing the route set or backend API contract:

- public IPs, private LAN IPs, and non-loopback hostnames remain unsupported API bases.
- URL credentials in API bases are rejected.
- broad secret-like query parameter names are rejected and not displayed.
- unknown/checking connection states are explicit in frontend types and loading copy.
- static verification rejects unsafe Vite proxy targets and secret-like API base env examples.

## v0.18.2 Design Governance

v0.18.2 adds design governance documentation only. Future Control Center UI work, including M15 approval, receipt, and event surfaces, must read:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

The design docs do not enable design tools, design SaaS, design-to-code, screenshot-to-code, new frontend behavior, new dependencies, backend routes, M15 UI, or production Control Center authority.

## v0.18.3 CCC Web Strategy

v0.18.3 clarifies that this shell is CCC Web, the current TypeScript web Control Center. CCC means Control Center Clients and also includes future CCC iOS, CCC Android, and CCC macOS planning. OpenWebUI remains the preferred conversational web shell, while Open Design governs custom CCC surfaces and does not replace OpenWebUI.

This shell remains read-only/preview-only and is not the agent brain. v0.18.3 adds no frontend feature, backend API route, OpenWebUI integration, native CCC implementation, Android app, iOS app, macOS app, mobile sensor access, native build workflow, OS permission integration, or production authority.

## v0.19.0 M15 Approval Receipt Event Viewer

v0.19.0 adds read-only/preview-only CCC Web inspection panels:

- Approval Queue: approval request summaries and selected details.
- Receipt Viewer: redacted summary-only receipt records and selected details.
- Event Viewer: redacted event summaries and selected details.

The M15 panels use visibly mock, non-authoritative fallback data until a future reviewed backend contract adds safe live summaries. They add no backend routes and no authority to approve, reject, execute, send, write, run, deploy, enable, or mutate.
