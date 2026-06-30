# Web Control Center Shell

Status: Active shell safety/currentness for the local Control Center. Historical
milestone sections below preserve their original route-count claims as audit
context; current API truth lives in `docs/api/README.md`.

M13 adds a local TypeScript React/Vite shell under `apps/control-center/` for reading existing backend Control Center and runtime readiness APIs. It is the first web UI surface for the future Control Center, but it is not a production Control Center and it has no authority to execute actions.

Implemented shell behavior:

- renders read-only dashboard, runtime readiness, Foundation Gate, API route, approval queue, receipt viewer, event viewer, event timeline trace viewer, evidence viewer, file reference viewer, memory viewer, remote worker, private mesh, mobile planning, plugin governance, setup assistant, and settings summaries.
- submits exactly one preview-only request type to `/control-center/actions/preview`.
- labels action preview as preview-only and displays blocked decisions as non-executed safety results.
- exposes the action preview risk level as policy metadata only.
- provides route-level headings and accessible loading, empty, error, and mock fallback states for local browser smoke review.
- shows provider credential readiness and CostGovernor binding posture as
  status-only safe refs in Setup, Settings, Models, and Action Inbox, including
  vault adapter, credential enrollment, validation, invocation, consent, policy,
  revocation, approval, blocker state, unknown paid-cost approval, cost
  estimate refs, budget decision refs, max-approved USD refs, future receipt
  refs, and provider/model ref posture.
- falls back to clearly marked mock data when the local backend is unavailable.
- displays unknown/checking, backend online, degraded, offline-safe, and mock fallback connection states.
- sanitizes secret-like frontend errors before display.
- uses relative API URLs by default.
- may use `VITE_UAA_API_BASE_URL` for local development with a local backend only.
- allows only relative, localhost, 127.0.0.1, and loopback IPv6 API bases.
- blocks external absolute API bases, public/private non-loopback hosts, non-loopback hostnames, URL credentials, and secret-like API base strings.

Non-goals:

- no backend mutation/execution routes and no route authority beyond separately
  scoped read/validation summaries.
- no public execution API.
- no runtime/model/provider call.
- no provider credential collection form.
- no raw provider key, token, secret, or environment-value display.
- no provider credential resolution, validation call, vault adapter runtime, or
  provider invocation.
- no provider spend authority, unknown paid-cost approval bypass, or usage/cost
  receipt bypass.
- no remote dispatch.
- no mobile/native app.
- no sensor access.
- no plugin enablement.
- no Chrome authenticated profile control.
- no Computer Use automation.
- no iOS/macOS build workflow.
- no production authority.

The shell is allowed to use local npm dependencies for React, Vite, TypeScript, Vitest, and Testing Library only. `node_modules`, `dist`, `build`, coverage output, log output, `.env` files, and native/mobile build files are not release artifacts.

v0.17.4 adds local browser smoke UX polish and safe reporting documentation only. Frontend CI still covers install, typecheck, lint, tests, and build; static verifiers cover frontend safety plus manual local browser smoke readiness/reporting; and Foundation Gate checks the CI/static/browser-readiness boundary. It does not add backend API paths, execution controls, sensitive browser storage, mobile sensor APIs, plugin enablement controls, browser automation, Chrome authenticated profile control, Computer Use automation, native build workflows, dependencies, or production Control Center authority.

## v0.18.0 M14 Connection Stabilization

v0.18.0 implements M14 local backend connection stabilization:

- API base URL policy is local-only.
- external absolute API URLs are blocked.
- secret-like API base URL strings are rejected and not displayed.
- live, degraded, and mock fallback states are visible.
- partial backend failures show degraded state and call out non-authoritative mock fallback panels.
- no backend route is added in M14.

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

v0.18.3 clarifies that this shell is CCC Web, the current TypeScript web
Control Center. CCC means Control Center Clients and also includes future CCC
iOS, CCC Android, and CCC macOS planning. Current product direction keeps
Control Center / Founder Command Center as the first-party product UI and keeps
OpenWebUI as a supported local/dev conversational shell, while Open Design
governs custom CCC surfaces and does not replace OpenWebUI.

This shell remains read-only/preview-only and is not the agent brain. v0.18.3 adds no frontend feature, backend API route, OpenWebUI integration, native CCC implementation, Android app, iOS app, macOS app, mobile sensor access, native build workflow, OS permission integration, or production authority.

## v0.19.0 M15 Approval Receipt Event Viewer

v0.19.0 adds read-only/preview-only CCC Web inspection panels:

- Approval Queue: approval request summaries and selected details.
- Receipt Viewer: redacted summary-only receipt records and selected details.
- Event Viewer: redacted event summaries and selected details.

The M15 panels use visibly mock, non-authoritative fallback data until a future reviewed backend contract adds safe live summaries. They add no backend routes and no authority to approve, reject, execute, send, write, run, deploy, enable, or mutate.

## v0.19.1 M15 Approval Receipt UI Safety Hardening

v0.19.1 hardens those M15 panels with explicit approval authority-boundary copy, approval-ref identifier-only copy, Python Agent Core approval authority copy, and redacted receipt/event detail copy. It adds no M16 timeline view, backend route, approval execution, approve/deny mutation, runtime execution, remote execution, plugin enablement, dependency, or production authority.

## v0.20.0 M16 Event Timeline Trace Viewer

v0.20.0 adds a read-only `/events/timeline` CCC Web route:

- Event Timeline: redacted event summaries with safe event, run, correlation, receipt, and evidence refs.
- Trace detail: selected run/receipt trace summary metadata only.
- Relation refs: parent/child and receipt/evidence relationship summaries.
- Foundation Gate evidence summary: safe criterion/evidence refs and statuses.

The M16 route uses visibly mock, non-authoritative fallback data until a future reviewed backend contract adds safe live summaries. It adds no backend route, no execution control, no approval mutation, no trace export, no external telemetry, no raw payload display, and no production authority.

## v0.20.1 M16 Trace Redaction Safety Hardening

v0.20.1 hardens M16 without adding a new surface. The timeline route keeps selection local to the visible UI: clicking a second `View trace` control changes selected trace detail and selected-card state only.

Foundation Gate now checks that backend timeline, trace, raw event, and
telemetry export routes remain absent. Release review builds should prefer
temporary Vite output paths, and generated frontend build/log artifacts must
remain ignored and untracked.

## v0.21.0 M17 Evidence File Memory Viewer

v0.21.0 adds read-only CCC Web routes for `/evidence`, `/files`, and `/memory`.

The M17 routes use visibly mock, non-authoritative fallback data until a future reviewed backend contract adds safe live summaries. They show safe refs, redacted summary metadata, data classification labels, provenance summaries, stale/conflict indicators, and relation refs only. Memory is recall, not authority; canonical files and governed source systems outrank memory.

M17 adds no backend route, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, raw prompt display, raw secret display, raw file display, raw memory display, raw evidence payload display, raw credential display, raw provider payload display, embeddings, vector DB, memory provider implementation, execution control, dependency, native build workflow, or production authority.

## v0.21.1 M17 Evidence File Memory Viewer Safety Hardening

v0.21.1 hardens the existing M17 routes with alternate safe mock refs, accessible selected-card reviewability, frontend tests, static verifier checks, docs, browser smoke reviewability, and Foundation Gate criteria.

## v0.22.0 M18 Local Runtime Status Manual Smoke Surface

M18 adds `/runtime/local` and `/runtime/manual-smoke` to the Web Control Center shell. The routes are frontend-only and use existing runtime readiness/validation contracts.

`/runtime/local` displays read-only readiness and capability matrix summaries.
`/runtime/manual-smoke` displays validation-only manual smoke report metadata.
Neither route starts, stops, connects, launches, executes, calls models,
performs manual smoke, dispatches remote work, enables plugins, accesses
sensors, exposes raw reports, or adds backend routes.

`/evidence`, `/files`, and `/memory` remain frontend-only, read-only, visibly
mock, non-authoritative, and redacted summary-only. No backend API route is
added in that milestone.
## M19 Mobile Companion Boundary

v0.23.0 / M19 adds Mobile Companion Contract/API Planning only and does not add
CCC Web behavior. The Web Control Center remains read-only/preview-only. M19
adds no backend API route, no frontend route, no mobile app, no Android app, no
iOS app, no native build workflow, no OS permission integration, no mobile
sensor access, and no production Control Center authority.
