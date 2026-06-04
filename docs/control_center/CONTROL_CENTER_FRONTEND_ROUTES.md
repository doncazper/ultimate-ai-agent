# Control Center Frontend Routes

Status: Active for M18 Local Runtime Status + Manual Smoke Control Surface as of v0.22.0.

The frontend shell is served by Vite during local development. It is not mounted by the Python API and does not add OpenAPI paths.

Implemented frontend pages:

- `/`
- `/dashboard`
- `/runtime`
- `/foundation-gate`
- `/api-routes`
- `/approvals`
- `/receipts`
- `/events`
- `/events/timeline`
- `/evidence`
- `/files`
- `/files/review`
- `/memory`
- `/runtime/local`
- `/runtime/manual-smoke`
- `/remote-workers`
- `/mobile-planning`
- `/plugin-governance`
- `/action-preview`

Backend API endpoints consumed:

- `GET /health`
- `GET /version`
- `GET /api/manifest`
- `GET /control-center/manifest`
- `GET /control-center/dashboard`
- `GET /control-center/status`
- `GET /control-center/routes`
- `GET /control-center/approvals/summary`
- `GET /control-center/runtime-readiness/summary`
- `GET /control-center/foundation-gate/summary`
- `GET /runtime/readiness`
- `GET /runtime/capability-matrix`
- `POST /runtime/smoke-reports/validate`
- `POST /control-center/actions/preview`

Forbidden frontend route/API targets:

- Control Center action run endpoints.
- plugin enablement endpoints.
- runtime/model/provider invocation endpoints.
- remote worker dispatch endpoints.
- mobile sensor endpoints.
- native/mobile build endpoints.
- Chrome profile, Computer Use, iOS, macOS, keychain, signing, or App Store workflows.

v0.17.4 keeps the frontend route set unchanged and adds local browser smoke UX polish plus safe reporting documentation. `scripts/verify_control_center_frontend.py` rejects forbidden execute, plugin enablement, runtime execution, remote dispatch, mobile sensor endpoint strings, analytics/SaaS SDK markers, sensitive browser APIs, and unsafe fixtures in frontend implementation files. `scripts/verify_control_center_browser_smoke_readiness.py` verifies that browser smoke readiness and reporting remain manual local-only documentation.

OpenAPI remains a backend contract. v0.22.0 changes only `info.version` to `0.22.0`; backend path count remains `74` with unique operation IDs.

## v0.18.0 M14 Connection Stabilization

v0.18.0 adds no frontend routes and no backend API paths. It stabilizes local backend connection behavior:

```text
M14 — Web Control Center Local Backend Connection Stabilization, implemented
M15 — Approval Queue + Receipt/Event Viewer UI, future
```

M14 clarifies local backend connection states and mock-to-live transitions, but it does not add execute/run/send/deploy/enable/approve controls or any POST target beyond `/control-center/actions/preview`. M15 may add read-only/preview-only approval, receipt, and event views only after a reviewed milestone prompt.

## v0.18.1 M14 Connection Safety Hardening

v0.18.1 adds no frontend routes and no backend API paths. It hardens the existing M14 route behavior by rejecting unsafe API base forms and making unknown/checking connection states explicit.

## v0.18.2 Design Governance

v0.18.2 adds no frontend routes and no backend API paths. It documents the design rules future route implementations must follow:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

M15 is implemented in v0.19.0 as read-only/preview-only frontend route panels for `/approvals`, `/receipts`, and `/events`.

## v0.18.3 CCC Web Route Boundary

v0.18.3 clarifies that the existing route set belongs to CCC Web, the current TypeScript web Control Center. CCC iOS, CCC Android, and CCC macOS are future native clients only. OpenWebUI remains a separate preferred conversational web shell.

No frontend route, backend API path, OpenWebUI integration, native client route, mobile sensor route, OS permission route, native build workflow, or production authority is added.

## v0.19.0 M15 Approval Receipt Event Viewer

v0.19.0 adds three frontend routes and no backend API paths:

- `/approvals`: Approval Queue list and selected detail panel.
- `/receipts`: Receipt Viewer list and selected detail panel.
- `/events`: Event Viewer list and selected detail panel.

These routes use safe mock fallback data and selected item detail panels because the current route framework is a simple path switch. They do not add dynamic backend detail routes, execute approvals, grant/reject approvals, mutate receipts/events, expose raw event data, or change OpenAPI path count.

v0.19.1 keeps the same frontend route set and hardens M15 authority/redaction safety checks. It adds no M16 timeline route, backend API path, approval execution route, approve/deny mutation route, receipt mutation route, event mutation route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, dependency, external API host, or production authority.

## v0.20.0 M16 Event Timeline Trace Viewer

v0.20.0 adds one frontend route and no backend API paths:

- `/events/timeline`: Event Timeline + Run/Receipt Trace Viewer with redacted event summaries, selected trace detail, event relation refs, and Foundation Gate evidence summaries.

This route uses safe mock fallback data, safe refs, and redacted summary-only copy. It does not add dynamic backend trace routes, approval execution, tool execution, trace export, external telemetry, OpenTelemetry export, cloud traces, raw prompt display, raw secret display, raw file display, raw memory display, raw credential display, raw provider payload display, raw event payload dumps, or OpenAPI path count changes.

v0.20.1 hardens this route with second-trace selection coverage and Foundation Gate checks that reject backend timeline/raw/export route expansion. Selecting `View trace` changes visible selection only.

## v0.21.0 M17 Evidence File Memory Viewer

v0.21.0 adds three frontend routes and no backend API paths:

- `/evidence`: Evidence Viewer with redacted evidence ref summaries.
- `/files`: File Reference Viewer with safe file ref metadata summaries.
- `/memory`: Memory Viewer with recall-only memory ref summaries.

These routes use safe mock fallback data, safe refs, redacted summary-only copy, and visible non-authoritative markers. They do not add dynamic backend evidence, file, or memory detail routes; file mutation; memory mutation; filesystem browsing; raw prompt display; raw secret display; raw file display; raw memory display; raw evidence payload display; raw credential display; raw provider payload display; embeddings; vector DB; memory provider implementation; execution controls; or OpenAPI path count changes.

## v0.21.1 M17 Evidence File Memory Viewer Safety Hardening

v0.21.1 keeps the same frontend routes and no backend API paths:

- `/evidence`
- `/files`
- `/memory`

The hardening patch adds alternate safe mock refs, selected-card reviewability, tests, verifier checks, docs, and Foundation Gate criteria only.

## v0.22.0 M18 Local Runtime Status Manual Smoke Surface

v0.22.0 adds two frontend routes and no backend API paths:

- `/runtime/local`: read-only local runtime readiness and capability matrix status.
- `/runtime/manual-smoke`: validation-only manual smoke report summary surface.

These routes use safe mock fallback data and existing runtime readiness/validation contracts. They do not add local runtime execution, manual smoke execution, backend routes, provider calls, remote dispatch, mobile sensor access, plugin enablement, OpenWebUI integration, raw smoke report display, raw prompts, raw response bodies, credentials, provider payloads, dependencies, or production Control Center authority.

## v0.40.0 M36 CCC File Review Surface

v0.40.0 adds one frontend route and no backend API paths:

- `/files/review`: review-only CCC file review surface for redacted review
  packets.

The route uses safe mock fallback data, redacted previews, redaction summaries,
exact binding refs, review-only decision status, approval gate contract status,
and receipt plan metadata. It does not add approval capture, approval
persistence, backend review routes, raw file reads, raw file display, raw file
storage, full-file reads, file picker/browser/upload/root selector,
export/download/copy-raw controls, context proposal, context injection, memory
writes, execution/tool controls, dependencies, or production Control Center
authority.
