# Control Center Frontend Routes

Status: Active route-inventory currentness for the local Control Center shell.
Historical milestone sections below preserve their original route-count claims as
audit context; current API truth lives in `docs/api/README.md`.

The frontend shell is served by Vite during local development. It is not mounted by the Python API and does not add OpenAPI paths.

Implemented frontend pages:

- `/`
- `/start`
- `/today`
- `/messenger`
- `/inbox`
- `/plans`
- `/work-board`
- `/actions`
- `/proof`
- `/trust`
- `/coding`
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
- `/capabilities`
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

Current IA note: the primary Founder Loop inside Control Center is Today,
Inbox, Plans, Actions, Memory, Evidence, and Settings. Supporting review,
runtime, evidence, and system surfaces remain reachable but do not visually
displace the daily loop. FCC-LOOP-001 adds a shared daily-loop spine to the
primary routes
using existing backend-backed Today, Action Inbox, Evidence Timeline, source
readiness, review queue, memory why-shown, weekly review, and dogfood capture
summaries. The spine is composition only: it adds no route, OpenAPI operation,
storage mutation, maturity promotion, or React-owned product truth. `/inbox` is
a blocked/planned frontend posture surface only; it has embedded read-only
connector draft proposal refs from `GET /control-center/sources/readiness`,
but no standalone or mutating draft proposal route, backend email/calendar
connector route, account auth, send/write/archive/delete authority, or
connector runtime.
`/messenger` is a desktop-only synthetic fixture route for the accepted
Messenger Matrix renders and deterministic failure states. It bypasses backend
data hooks and has no Matrix dependency, account, network, sync, encryption,
cache, message read/send, room mutation, media, calling, credential, model,
memory, public release, or production authority. Fixture navigation is local
presentation state and Python Agent Core remains product truth.
`/actions` renders backend-classified Action Inbox queue states from
`GET /control-center/actions/inbox` so ready, approved local-task,
authority-blocked, expired/stale, receipt-recorded, and proposal-only items are
visibly distinct. The grouping is read-only metadata from Python core storage;
it adds no generic execute button, connector write, shell/subprocess execution,
provider/model authority, memory write, context injection, or production
authority.
`/work-board` renders the backend-owned Work Board Kanban read model from
`GET /control-center/work-board`, persists exact approved local reorder through
`POST /control-center/work-board/reorder`, and exposes exact approved local
card create through `POST /control-center/work-board/cards`. It shows card,
column, proof, evidence, blocker, promotion-path, drag/drop posture, reorder
and local-card-create receipt posture, and CLI inspection refs with local
drag/drop and keyboard preview. It does not archive or assign cards, create
tasks, sync issue trackers, call providers, run shell/browser work, write
connectors, launch background autonomy, or grant production authority.
`/crm` renders the backend-owned CRM Local Command Center M2 read model from
`GET /control-center/crm/summary` and companion CRM read routes. It shows
relationship refs, follow-up refs, timeline refs, pipeline refs, smart-list
refs, report refs, local storage posture, redacted import/export preview
posture, deterministic proposal refs, `contacts/write`-gated exact local
mutation receipt posture, and blocked authority refs. It does not add connector
runtime, external CRM writes, account sync, contact import commit, sends,
calendar writes, provider/model calls, live web, browser automation, public
beta, public release, production readiness, or production authority.
`/start`, `/proof`, and `/trust` are backend-owned Founder Loop support
surfaces. `/start` renders `GET /control-center/start-here/summary`, `/proof`
renders `GET /control-center/proof/index`, and `/trust` renders
`GET /control-center/trust-authority/matrix`. Beta 07 Trust authority map
hardens `/trust` with CLI inspection refs, safe-disable refs, rollback refs,
promotion-path refs, and fail-closed frontend validation through
`scripts/verify_beta_07_trust_authority_map.py`. No broad runtime authority is
added.
`/coding` renders the repo-safe Coding Cockpit shell from
`GET /control-center/coding/session` and the read-only context-pack preview from
`GET /control-center/coding/context`. Prompt 01 exposes a backend-owned
read-only session seed with workspace/context refs, task refs, diff/proof
placeholders, terminal/Git/test/live-preview posture, authority modes, proof
refs, redaction refs, and blocked authority refs only. Prompt 02 adds
backend-owned safe context refs, excluded refs, comparison refs, context budget
posture, and CLI inspection parity. Prompt 03 adds
`GET /control-center/coding/patch-proposal` with proposal-only patch file refs,
hunk refs, bounded diff summaries, and CLI inspection parity. Prompt 04 adds
`GET /control-center/coding/patch-apply-readiness` with blocked apply
prerequisite, expected receipt, rollback, proof, blocker, promotion-path, and
unblock-prompt refs. Prompt 05 adds
`GET /control-center/coding/test-command-readiness` with allowlist and expected
receipt refs only. Prompt 06 adds `GET /control-center/coding/git-review` with
Git status, diff, changed-file, commit proposal, and PR description refs only.
Prompt 07 adds `GET /control-center/coding/live-preview` with dev-server
status, preview URL, screenshot, console, visual-proof, route-checklist, and
viewport refs only. Prompt 08 adds
`GET /control-center/coding/multi-agent-review` with Codex implementer, Claude
reviewer, local verifier, security reviewer, UX reviewer, test fixer, merge
captain, plan, review, diff-comparison, disagreement, and handoff refs only. It
does not write files, apply patches, read or persist raw file content, run
shell/subprocess commands, execute commands, mutate Git state, start or inspect
dev servers, persist raw URLs, capture screenshots, read console output, call
providers or models, call provider SDKs, dispatch local agents, inject context,
persist raw prompts or responses, automate browsers, write connectors, launch
background agents, persist raw paths or raw content, or grant production
authority.
FCC-V1-000 adds `releaseStatus` route metadata and
`docs/control_center/release_surface_manifest.json`; the sidebar and command
palette render conservative route-state labels. `ship` is intentionally
translated to `exact route proof` in the UI to avoid release overclaiming;
`partial`, `blocked`, and `experimental` remain visible as readiness posture.
Older descriptive route badges remain metadata for keywords and audit context.
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
- `GET /control-center/capabilities/surface`
- `GET /control-center/approvals/summary`
- `GET /control-center/runtime-readiness/summary`
- `GET /control-center/foundation-gate/summary`
- `GET /control-center/setup-assistant/summary`
- `GET /control-center/coding/context`
- `GET /control-center/coding/git-review`
- `GET /control-center/coding/live-preview`
- `GET /control-center/coding/multi-agent-review`
- `GET /control-center/coding/patch-apply-readiness`
- `GET /control-center/coding/patch-proposal`
- `GET /control-center/coding/session`
- `GET /control-center/coding/test-command-readiness`
- `GET /control-center/start-here/summary`
- `GET /control-center/today/summary`
- `GET /control-center/actions/inbox`
- `GET /control-center/actions/{action_id}/receipt`
- `POST /control-center/actions/{action_id}/approve`
- `POST /control-center/actions/{action_id}/edit`
- `POST /control-center/actions/{action_id}/reject`
- `POST /control-center/actions/{action_id}/defer`
- `POST /control-center/actions/{action_id}/local-task/commit`
- `GET /control-center/proof/index`
- `GET /control-center/proof/{proof_ref}`
- `POST /control-center/web-evidence/attach` for the Beta 08 Web Evidence beta
  slice only: active Browser/read AuthorityLease, configured host allowlist
  HTTPS GET through WebAccessGateway, transient bounded redacted preview to the
  requester, durable safe refs, authority decision refs, and redacted audit
  summary only.
- `GET /control-center/trust-authority/matrix`
- `GET /control-center/morning-briefing/summary`
- `GET /control-center/storage/status`
- `GET /control-center/work-board`
- `GET /runtime/readiness`
- `GET /runtime/capability-matrix`
- `GET /v1/models`
- `POST /v1/chat/completions` for the scoped redacted local readiness exchange
  only when local gateway prerequisites are already configured. The response may
  include `uaa_safety.turn_harness_binding`, which the Chat surface can pass into
  the durable chat receipt as backend-owned router metadata. The binding is
  displayed as contract/proof posture only with
  `turn_harness_binding_compilation_only` no-effect scope; it does not expose
  raw prompts, raw responses, memory content, execution tools, action execution,
  or approval authority.
- `POST /runtime/smoke-reports/validate`
- `POST /control-center/actions/preview`
- `POST /control-center/turn-router/preview` for the Chat Router Diagnostics
  no-effect preview only. The surface renders selected contract, policy
  posture, blocked authority, and no-effect proof; it does not persist raw
  turn text, execute actions/tools, retrieve memory bodies, call
  providers/models, automate browsers, write connectors, or grant authority.

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

Beta 08 Web Evidence beta slice keeps `/proof` as the Control Center surface for
one configured host allowlist WebAccessGateway preview receipt. Full-strength
Web Evidence remains future real-world evidence plus separately gated
browser/web workflows; the repo-safe version is request-ref idempotent,
safe-disable aware, durable safe-ref-only, and verified by
`scripts/verify_beta_08_web_evidence_product_slice.py`. Blocked/needs-authority
remains browser action, auth/cookies, download/upload, POST-style mutation, raw
URL/body/header persistence, context injection, memory write, provider/model
call, connector write, public release, and production authority. Exact
promotion needs a later scoped PR with approval binding where mutation appears,
redaction, rollback/safe-disable, CLI/API parity, receipts/proof, tests, and
docs. No broad runtime authority is added.

Beta 09 Provider Draft/Summarize preview keeps `/proof` and `/trust` as
inspection-only Control Center surfaces for the exact core/CLI provider draft
capability. `/proof` can show `proof-ref:provider-draft-summarize:exact` as
backend-owned safe-ref proof and `/trust` can show the capability posture, CLI
refs, safe-disable refs, rollback refs, blocked authority refs, and maturity
refs.
The frontend must not expose a provider-draft API route, provider-call button,
default live provider network, provider SDK call, durable draft preview
persistence, connector write, memory/context injection, action execution,
background provider call, public release, or production authority.

Beta 10 Connector Draft-Only keeps `/inbox`, `/proof`, and `/trust` as
inspection-only Control Center surfaces for embedded connector draft proposal
refs. Full-strength connector drafting remains a later approved connector
runtime, send, write, and sync workflow. The repo-safe current version renders
backend-owned safe refs from
`GET /control-center/sources/readiness#connector_draft_proposals`,
`proof-ref:connector-draft-only-proposals:v1`, and
`trust-lane:connector-draft-only`; it adds no standalone connector draft route,
send/write/sync/OAuth control, account connection, auth-material collection,
delivery worker, provider/model call, memory/context injection, background
runtime, public release, or production authority. Verification:
`scripts/verify_beta_10_connector_draft_only.py`. No broad runtime authority is
added.

Beta 11 Operator Workspace Spine keeps Today, `/proof`, and `/trust` as
inspection-only Control Center surfaces for the backend-owned workspace spine
read model. The current repo-safe version renders safe refs from
`GET /control-center/today/summary#operator_workspace_spine`,
`proof-ref:operator-workspace-spine:read-model`, and
`trust-lane:operator-workspace-spine`; it shows workspace status, Git posture,
preview status, run-log posture, and coworker handoff metadata without adding
file editor controls, terminal controls, patch apply, Git mutation,
shell/subprocess execution, browser automation, dev-server lifecycle control,
provider/model calls, connector writes, coworker dispatch, background autonomy,
raw path/log persistence, public release, or production authority.
Verification: `scripts/verify_beta_11_operator_workspace_spine.py`.

OpenAPI remains a backend contract. The current backend path count is `275`
with `276` manifest route operations; earlier milestone counts in the
historical sections below are audit context, not current route inventory.

## v0.18.0 M14 Connection Stabilization

v0.18.0 adds no frontend routes and no backend API paths. It stabilizes local backend connection behavior:

```text
M14 — Web Control Center Local Backend Connection Stabilization, implemented
M15 — Approval Queue + Receipt/Event Viewer UI, future
```

M14 clarifies local backend connection states and mock-to-live transitions, but it does not add execute/run/send/deploy/enable/approve controls. The frontend POST surface remains bounded to reviewed no-effect preview routes such as `/control-center/actions/preview` and `/control-center/turn-router/preview`. M15 may add read-only/preview-only approval, receipt, and event views only after a reviewed milestone prompt.

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

## Provider Credential Readiness + Cost Binding Visibility

Setup, Settings, Models, and Action Inbox may render provider credential
readiness, CostGovernor posture, and exact provider capability posture from
`GET /control-center/dashboard`.
Setup, Settings, and Models may also render provider catalog/cost-literacy
metadata from `GET /control-center/providers/setup-guide`. This is reference
posture only: provider manifest refs, provider auth ref status, consent refs,
policy refs, revocation refs, approval refs, blocker codes, vault adapter
readiness, validation readiness, invocation readiness, readiness status,
unknown paid-cost approval posture, cost estimate refs, budget decision refs,
max-approved USD refs, future receipt refs, and CostGovernor decision/posture
refs. The exact credential validation capability route
`POST /control-center/providers/credentials/validate` is active
`provider_model_calls/execute` AuthorityLease, exact-approval, policy,
idempotency, revocation/safe-disable, and redacted-receipt scoped for one
provider credential check only. Missing active lease must show an
authority-required blocker before approval or adapter execution. It does not
authorize invocation, model calls, provider SDKs, fallback, billing, raw
credential display, or provider payload persistence. The exact provider capability route
`POST /control-center/providers/exact-approved-lanes/tiny` is disabled by
default; the API route blocks without exact approval, and the Python core
evaluator reaches approved-no-execution only when exact approval and cost gates
are injected for inspection while callable provider authority still requires a
later scoped adapter enablement milestone. It does not add a provider setup
form, read environment values, collect raw keys, store credential material, run
a vault/keychain adapter, perform broad provider validation, invoke provider
SDKs, run autonomous/background model calls, grant spend authority, bypass
unknown paid-cost approval, bypass receipts, or enable provider calls.

The future gates are separate:

- Provider Credential Vault Adapter v1 remains blocked until a scoped milestone
  defines adapter storage backend, consent, policy, approval, revocation,
  audit, redaction, and rollback behavior.
- Broad Provider Credential Validation remains blocked outside the
  AuthorityLease-gated exact-approved one-provider capability with redacted
  validation receipts.
- Tiny Exact-Approved Provider Capability remains disabled by default until a scoped
  adapter enablement milestone defines provider SDK/network authority. The
  current route requires exact approval, CostGovernor posture, idempotency,
  redacted receipt refs, safe-disable behavior, and complete provider/model/
  credential/cost refs before it can reach approved-no-execution posture.
