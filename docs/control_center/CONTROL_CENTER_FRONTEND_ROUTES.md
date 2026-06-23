# Control Center Frontend Routes

Status: Active route-inventory currentness for the local Control Center shell.
Historical milestone sections below preserve their original route-count claims as
audit context; current API truth lives in `docs/api/README.md`.

The frontend shell is served by Vite during local development. It is not mounted by the Python API and does not add OpenAPI paths.

Implemented frontend pages:

- `/`
- `/today`
- `/inbox`
- `/plans`
- `/actions`
- `/memory`
- `/evidence`
- `/settings`
- `/dashboard`
- `/operator-loop`
- `/chat`
- `/models`
- `/briefing`
- `/runtime`
- `/storage`
- `/foundation-gate`
- `/api-routes`
- `/approvals`
- `/receipts`
- `/events`
- `/events/timeline`
- `/files`
- `/files/review`
- `/context/proposals`
- `/runtime/local`
- `/runtime/manual-smoke`
- `/remote-workers`
- `/mobile-planning`
- `/plugin-governance`
- `/setup`
- `/action-preview`
- `/private-trial`

Current IA note: the primary Founder Command Center loop is Today, Inbox,
Plans, Actions, Memory, Evidence, and Settings. Supporting review, runtime,
evidence, and system surfaces remain reachable but do not visually displace the
daily loop. FCC-LOOP-001 adds a shared daily-loop spine to the primary routes
using existing backend-backed Today, Action Inbox, Evidence Timeline, source
readiness, review queue, memory why-shown, weekly review, and dogfood capture
summaries. The spine is composition only: it adds no route, OpenAPI operation,
storage mutation, maturity promotion, or React-owned product truth. `/inbox` is
a blocked/planned frontend posture surface only; it has no backend
email/calendar connector route, account auth, draft proposal route,
send/write/archive/delete authority, or connector runtime.
`/actions` renders backend-classified Action Inbox queue lanes from
`GET /control-center/actions/inbox` so ready, approved local-task,
authority-blocked, expired/stale, receipt-recorded, and proposal-only items are
visibly distinct. The grouping is read-only metadata from Python core storage;
it adds no generic execute button, connector write, shell/subprocess execution,
provider/model authority, memory write, context injection, or production
authority.
FCC-V1-000 adds `releaseStatus` route metadata and
`docs/control_center/release_surface_manifest.json`; the sidebar and command
palette render the conservative `ship`/`partial`/`blocked`/`experimental`
release status, while older descriptive route badges remain metadata for
keywords and audit context.
`/private-trial` is the UAA-P1-087.2a/087.2b/087.2c read-only packet,
acceptance ledger, and unanswered manual-review scaffold surface only. It
renders safe refs from
`docs/macos/private_operator_trial_packet_v1.json` and
`docs/macos/private_operator_trial_acceptance_ledger_v1.json` plus the
unanswered `docs/macos/private_operator_trial_manual_review_scaffold_v1.json`
and adds no backend route, OpenAPI path, connector write, memory write, action
execution, provider/model authority, shell/subprocess behavior, browser
automation, public beta claim, or production authority. Full UAA-P1-087.2 is
deferred until more Founder Loop implementation exists and accepted or revised
local/private findings are recorded later.

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
- `GET /control-center/setup-assistant/summary`
- `GET /control-center/today/summary`
- `GET /control-center/actions/inbox`
- `GET /control-center/actions/{action_id}/receipt`
- `POST /control-center/actions/{action_id}/approve`
- `POST /control-center/actions/{action_id}/edit`
- `POST /control-center/actions/{action_id}/reject`
- `POST /control-center/actions/{action_id}/defer`
- `POST /control-center/actions/{action_id}/local-task/commit`
- `GET /control-center/morning-briefing/summary`
- `GET /control-center/storage/status`
- `GET /runtime/readiness`
- `GET /runtime/capability-matrix`
- `GET /v1/models`
- `POST /v1/chat/completions` for the scoped redacted local readiness exchange
  only when local gateway prerequisites are already configured.
- `POST /runtime/smoke-reports/validate`
- `POST /control-center/actions/preview`

Forbidden frontend route/API targets:

- Control Center action run endpoints.
- plugin enablement endpoints.
- runtime/model/provider invocation endpoints.
- provider credential collection, storage, validation-call, or invocation
  endpoints.
- remote worker dispatch endpoints.
- mobile sensor endpoints.
- native/mobile build endpoints.
- Chrome profile, Computer Use, iOS, macOS, keychain, signing, or App Store workflows.

v0.17.4 keeps the frontend route set unchanged and adds local browser smoke UX polish plus safe reporting documentation. `scripts/verify_control_center_frontend.py` rejects forbidden execute, plugin enablement, runtime execution, remote dispatch, mobile sensor endpoint strings, analytics/SaaS SDK markers, sensitive browser APIs, and unsafe fixtures in frontend implementation files. `scripts/verify_control_center_browser_smoke_readiness.py` verifies that browser smoke readiness and reporting remain manual local-only documentation.

OpenAPI remains a backend contract. The current backend path count is `108` with
unique operation IDs; earlier milestone counts in the historical sections below
are audit context, not current route inventory.

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

v0.18.3 clarifies that the existing route set belongs to CCC Web, the current
TypeScript web Control Center. CCC iOS, CCC Android, and CCC macOS are future
native clients only. Current product direction keeps Control Center / Founder
Command Center as the first-party product UI and keeps OpenWebUI as a separate
supported local/dev conversational shell.

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

v0.40.1 hardens `/files/review` with safe-ref-only display checks, private/raw
path drift checks, local read-only packet selection/expansion guarantees, and
no-mutating-request checks. It adds no frontend route and no backend API path.

## v0.43.0 M39 CCC Context Proposal Surface

v0.43.0 adds one frontend route and no backend API paths:

- `/context/proposals`: read-only CCC context proposal surface for M38 safe
  context proposal objects.

The route uses safe mock fallback data, proposal-only status, approved-review
provenance, exact binding refs, redaction verification, safe proposal sections,
review-only decision status, approval-gate contract status, and receipt-plan
metadata. It does not add context handoff approval, context injection,
OpenWebUI handoff, OpenWebUI runtime integration, model/provider calls, memory
writes, export/download/copy-raw controls, execution/tool controls, approval
mutation controls, backend routes, raw file reads, raw file display/storage,
full-file display, unredacted preview display, raw absolute paths, file picker,
browser, upload, root selector, dependencies, or production Control Center
authority.

M40 remains future.

## Provider Credential Readiness Visibility

The Settings surface may render provider credential readiness from
`GET /control-center/dashboard`. This is reference posture only: provider
manifest refs, provider auth ref status, consent refs, policy refs, revocation
refs, approval refs, blocker codes, vault adapter readiness, validation
readiness, invocation readiness, and readiness status. It does not add a
provider setup form, read environment values, collect raw keys, store
credential material, run a vault/keychain adapter, validate credentials against
an external provider, or enable provider calls.

The future gates are separate:

- Provider Credential Vault Adapter v1 remains blocked until a scoped milestone
  defines adapter storage backend, consent, policy, approval, revocation,
  audit, redaction, and rollback behavior.
- Provider Credential Validation v1 remains blocked until a scoped milestone
  defines redacted validation receipts and external-call authority.
- Governed Provider Invocation v1 remains blocked until a scoped milestone
  defines PolicyEngine checks, LocalApprovalAuthority or successor approval,
  provider allowlists, provider auth references, redacted request/response summaries,
  receipt/audit refs, safe-disable behavior, and rate/budget boundaries.
