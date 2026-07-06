# Control Center UI Wiring Report

Status: scoped wiring inventory and hardening report.

This report inventories the visible Control Center route registry in
`apps/control-center/src/routes.tsx`, the release surface truth in
`docs/control_center/release_surface_manifest.json`, and the local backend/API
contracts used by the TypeScript shell. It does not grant runtime authority.
Python Agent Core remains the product truth boundary.

## Summary

What was wired in this pass:

- `loadControlCenterData()` now reads the dedicated Control Center summary
  routes for approvals, runtime readiness, and Foundation Gate posture:
  `/control-center/approvals/summary`,
  `/control-center/runtime-readiness/summary`, and
  `/control-center/foundation-gate/summary`.
- The visible dashboard state now prefers those dedicated read summaries over
  the embedded dashboard copies when the dedicated routes are available.
- The `/approvals` surface now displays the backend-owned approval summary
  while keeping detailed approval queue cards as preview-only M15 review data.

What was already wired and left intact:

- FCC primary surfaces already consume backend read models for Today, Source
  Inbox readiness, Action Inbox, Memory, Evidence Timeline, Settings, Morning
  Briefing, local model status, provider setup guide, setup assistant summary,
  storage status, runtime readiness, capability matrix, dashboard, status, and
  route inventory.
- Exact-scoped mutation lanes already present in the UI, such as Action Inbox
  decision receipts and Chat receipt/handoff receipts, remain behind existing
  backend contracts. No new mutation lane was added here.

What was intentionally not wired:

- M15 review details, M16 event timeline trace, M17 file/evidence/memory viewer,
  M18 local runtime/manual smoke surfaces, M36 file review packets, and M39
  context proposals still use non-authoritative mock bundles where no safe
  read-model route exists.
- Validation-only POST routes such as receipt preview, event validation, and
  file validation were not used as product-state read models.
- Provider calls, connector runtime, credential collection, browser/web
  fetching, shell/subprocess execution, background execution, scheduler
  runtime, billing authority, memory writes, context injection, and production
  authority remain blocked.

Highest-risk gaps:

- Several visible route-registry pages still render mock milestone bundles that
  look richer than the backend read contracts currently available.
- `/api-routes` is backed by `/control-center/routes`, but the frontend does
  not yet have a typed `/api/manifest` client model even though the release
  surface manifest lists `/api/manifest` as part of that route contract.
- `/receipts`, `/events`, `/events/timeline`, `/files`, `/files/review`, and
  `/context/proposals` need backend-owned read summaries before the UI should
  retire their mock bundles.

## Naming / Alias Map

Control Center:

- The actual frontend app shell and route registry under
  `apps/control-center`.
- It is a presentation and inspection shell, not an authority boundary.

Founder Command Center / FCC:

- The founder/operator product surfaces inside Control Center: Today, Source
  Inbox, Plans, Action Inbox, Memory, Evidence, Settings, Morning Briefing,
  Chat, Models, and closely related review surfaces.
- FCC copy must keep implemented, partial, blocked, planned, mock-only, and
  unsafe-authority states explicit.

Command Center alias usage:

- "Command Center" alone is ambiguous because it can refer to the frontend
  shell or the founder/operator product surfaces.
- Use "Control Center" for app-shell and route-contract work.
- Use "FCC" or "Founder Command Center" for product-loop surfaces.

Ambiguous routes/pages:

- `/operator-loop`, `/dashboard`, `/differentiators`, `/approvals`,
  `/receipts`, and `/events` are Control Center support surfaces that also
  explain FCC product posture. Reports should name both context and authority
  posture when discussing them.

## Wiring Matrix

| Surface | Product alias | UI control/action | Backend/API/core contract | Current status | Reason | Next recommended action |
|---|---|---|---|---|---|---|
| `/today` Today | FCC | Daily loop command deck, Today-to-Action envelope proposal | `GET /control-center/today/summary`; `POST /control-center/today/action-envelope`; CLI: `scripts/inspect_today_loop.py`, `scripts/dev/uaa_founder_loop.py` | partially wired | Backend summary is used; Action envelope promotion stays exact-scoped and does not execute work. | Add a dedicated Today wiring verifier that proves every visible subcard comes from the read model or a blocked state. |
| `/inbox` Source Inbox | FCC | Source readiness cards plus connector draft-only proposal refs | `GET /control-center/sources/readiness`; CLI: `scripts/inspect_connector_draft_proposals.py` | partially wired | Readiness is backend-owned and now includes email-response and calendar-hold draft proposal refs; live email/calendar reads, account auth, source ingestion, connector runtime, sends, and writes remain blocked. | Add read-only email/calendar source contracts and test-account metadata proof before richer inbox cards or any send/write controls. |
| `/plans` Plans | FCC | Plan status, Plans-to-Actions proposal posture | `GET /control-center/today/summary`; core read-model slices; CLI: `scripts/inspect_plans_to_actions_bridge.py` | partially wired | Plans data is currently carried through Today/bridge read models, not a dedicated Plans route. | Add `GET /control-center/plans/summary` with CLI parity before adding richer controls. |
| `/actions` Action Inbox | FCC | Action rows, approve/edit/reject/defer receipts, local-task commit lane, queue scope/idempotency/staleness posture | `GET /control-center/actions/inbox`; decision and receipt routes under `/control-center/actions/{action_id}`; CLI: `scripts/inspect_action_inbox_decision_lanes.py`, `scripts/dev/uaa_founder_loop.py` | wired with authority limits | Backend owns state, receipts, and review refs; UI decisions require existing exact-scoped backend contracts and still do not execute external actions. | Keep adding receipt visibility tests; do not add action execution without a separate scoped milestone. |
| `/memory` Memory | FCC | Memory Review, workbench, context packs, review decisions | `GET /control-center/memory/review`; `GET /control-center/memory/workbench`; `GET /control-center/memory/context-packs`; decision/receipt routes; CLI: `scripts/inspect_memory_merge_supersede_posture.py` | partially wired | Backend read models and review receipts are used; memory truth authority, delete/export execution, semantic search, and context injection stay blocked. | Add a single CLI inspection path for the complete Memory route surface. |
| `/evidence` Evidence | FCC | Evidence timeline, evidence operator cards, legacy evidence viewer | `GET /control-center/evidence/timeline`; CLI: `scripts/inspect_evidence_timeline_narrative.py` | partially wired | Evidence Timeline is backend-owned; the legacy evidence/file viewer still reads M17 mock data. | Replace M17 viewer inputs with safe backend read summaries or mark the legacy viewer as mock-only in the route. |
| `/settings` Settings | FCC | Authority posture, kill-switch posture, feature flags, provider/readiness cards | `GET /control-center/settings/status`; `GET /control-center/providers/setup-guide`; `GET /control-center/local-models/status`; CLI: `scripts/inspect_settings_authority_posture.py` | wired read-only | Backend owns status labels; mutation toggles are not exposed. | Keep UI/CLI parity for kill-switch inspection; do not add settings writes yet. |
| `/briefing` Briefing | FCC | Morning Briefing summary and shared loop spine | `GET /control-center/morning-briefing/summary`; CLI: `scripts/inspect_morning_briefing_v1.py` | partially wired | Backend summary is used; live source ingestion and calendar/email contracts are missing. | Add source-specific readiness refs to the briefing read model before richer source claims. |
| `/private-trial` Trial Packet | FCC support | Local/private trial checklist and evidence refs | Static packet/docs; CLI: `scripts/inspect_product_loop_trial_script.py` | partially wired static | It is a safe-ref manual review artifact, not a backend live state route. | Add a read-only backend summary only if the route remains visible in normal nav. |
| `/operator-loop` Operator Loop | Control Center support | Operator loop readiness summary | `GET /control-center/dashboard` operator loop summary | wired read-only | Dashboard summary is backend-owned and describes blocked authority. | Add a focused CLI inspection path for the operator-loop summary. |
| `/setup` Setup | Control Center support | macOS Setup Assistant summary | `GET /control-center/setup-assistant/summary` | wired read-only | Backend returns a safe plan; installer side effects and credential capture remain blocked. | Add setup receipt/rollback inspection before enabling any setup mutation. |
| `/chat` Chat | FCC | Local model route probe, redacted local chat probe, chat receipt, handoff receipts | `GET /v1/models`; `POST /v1/chat/completions`; chat receipt/handoff routes; CLI: `scripts/inspect_chat_to_loop_handoff.py` | partially wired | Existing UI can request a redacted local probe and record receipts; output is not displayed or treated as authority. | Add a CLI-equivalent redacted chat probe receipt path before expanding Chat controls. |
| `/models` Models | FCC | Local model inventory/status, provider catalog/readiness cards | `GET /v1/models`; `GET /control-center/local-models/status`; `GET /control-center/providers/setup-guide`; CLI: `scripts/inspect_provider_setup_guide.py`, `scripts/inspect_provider_credential_readiness.py` | partially wired | Read-only inventory and provider readiness are backend-owned; lifecycle actions and provider invocation remain blocked. | Add dedicated local model lifecycle status refs before any start/stop/switch UI. |
| `/approvals` Approvals | FCC support | Backend approval summary plus M15 preview queue details | `GET /control-center/approvals/summary`; M15 mock detail bundle | partially wired | Summary is now backend-owned; detailed queue rows still lack a safe backend read list. | Add `GET /control-center/approvals/queue` with redacted rows and CLI inspection. |
| `/files` Files | Control Center support | File refs/evidence viewer | Validation POST routes exist; UI uses M17 mock bundle | mock-only for visible list | There is no safe GET read model for file ref inventory visible to this panel. | Add a redacted file-ref inventory route before replacing mock data. |
| `/files/review` File Review | Control Center support | File review packets and receipt plan posture | `POST /files/review/approvals/capture` exists; UI uses M36 mock bundle | blocked / mock-only | Existing backend route is mutating and authority-scoped; it is not a read model for visible packet state. | Add `GET /control-center/files/review/summary` before wiring the panel. |
| `/context/proposals` Context Proposals | Control Center support | Context proposal review cards | No backend route | missing backend | The panel is M39 mock-only; context injection is not scoped. | Add a safe proposal-read route with explicit no-context-injection posture. |
| `/action-preview` Action Preview | Control Center support | Preview-only action validation form | `POST /control-center/actions/preview` | wired validation-only | Backend returns preview decisions without executing actions. | Keep as validation-only; add CLI parity if operators need non-UI inspection. |
| `/runtime` Runtime | Control Center support | Runtime readiness and capability matrix | `GET /runtime/readiness`; `GET /runtime/capability-matrix`; `GET /control-center/runtime-readiness/summary` | wired read-only | Runtime flags are status only; no runtime activation is exposed. | Keep direct summary and matrix tests aligned. |
| `/storage` Storage | FCC support | Founder Loop storage status | `GET /control-center/storage/status` | wired read-only | Storage posture is backend-owned; storage mutation controls are not exposed. | Add storage CLI inspection if storage becomes operator-critical. |
| `/runtime/local` Local Runtime | Control Center support | Local runtime status cards | `GET /runtime/readiness`; `GET /runtime/capability-matrix`; M18 mock details | partially wired | Core runtime state is backend-owned; detailed M18 surfaces still come from mock data. | Replace M18 local runtime surfaces with a backend summary route. |
| `/runtime/manual-smoke` Manual Smoke | Control Center support | Manual smoke report summaries | `POST /runtime/smoke-reports/validate`; M18 mock reports | mock-only for visible reports | Validation exists, but no safe report list/read model is consumed by the UI. | Add `GET /runtime/smoke-reports/summary` before retiring M18 mock reports. |
| `/remote-workers` Remote Workers | Control Center support | Remote worker planning summary | `GET /control-center/dashboard` remote worker summary | wired read-only | Dashboard states dry-run/planned posture; dispatch remains blocked. | Keep dispatch blocked until a scoped authority lane exists. |
| `/mobile-planning` Mobile Planning | Control Center support | Mobile planning summary | `GET /control-center/dashboard` mobile planning summary | wired read-only | Dashboard states planned/disabled posture; sensor/control runtime remains blocked. | Keep as planning/readiness only. |
| `/plugin-governance` Plugin Governance | Control Center support | Plugin governance summary | `GET /control-center/dashboard` plugin governance summary | wired read-only | Dashboard states planned/disabled posture; plugin runtime import remains blocked. | Add plugin catalog read model before any enablement UI. |
| `/foundation-gate` Foundation Gate | Control Center support | Foundation Gate summary | `GET /control-center/foundation-gate/summary` | wired read-only | Dedicated summary route is now preferred in client data. | Add last-run report refs only through redacted backend evidence. |
| `/receipts` Receipts | Control Center support | Receipt viewer cards | `POST /receipts/preview` exists; UI uses M15 mock receipts | mock-only for visible list | Preview validation is not a receipt ledger read model. | Add `GET /control-center/receipts/summary` with redacted receipt rows. |
| `/events` Events | Control Center support | Event viewer cards | `POST /events/validate` exists; UI uses M15 mock events | mock-only for visible list | Event validation is not an event ledger read model. | Add `GET /control-center/events/summary` with redacted event rows. |
| `/events/timeline` Timeline | Control Center support | Timeline trace and selected detail | No backend route; M16 mock trace | mock-only | No safe event timeline summary/read model exists for this page. | Add an event timeline read model with selected-detail evidence refs. |
| `/` Overview | Control Center shell | Overview dashboard | `GET /control-center/dashboard`; `GET /control-center/manifest`; `GET /control-center/status` | wired read-only | The app shell uses backend dashboard/status and manifest data. | Keep as the default shell route. |
| `/dashboard` Dashboard | Control Center shell | Dashboard summary cards | `GET /control-center/dashboard` plus dedicated summary routes | wired read-only | Dedicated approval/runtime/foundation summaries are now preferred when available. | Add tests whenever new dashboard cards are added. |
| `/api-routes` API Routes | Control Center shell | API route inventory table | `GET /control-center/routes`; release manifest also lists `GET /api/manifest` | partially wired | Control Center routes are typed and displayed; full API manifest is not typed in the frontend client. | Add a typed `ApiManifest` client model and render a bounded full-manifest summary. |
| `/differentiators` Differentiators | Control Center shell | Operator-proof comparison cards | Mixed: dashboard/routes/runtime plus M15/M16/M17/M18/M36 mock bundles | partially wired / demo-only | It aggregates real summaries and mock milestone bundles; it should not be treated as product truth. | Replace mock-fed cards with backend proof refs or mark each card's data source inline. |

## Unwired Items

Missing backend route:

- Redacted approval queue rows for `/approvals`.
- Redacted receipt list/read model for `/receipts`.
- Redacted event list and event timeline read models for `/events` and
  `/events/timeline`.
- Redacted file-ref inventory for `/files`.
- File Review read summary for `/files/review`.
- Context proposal read summary for `/context/proposals`.
- Local runtime surface and manual smoke report summaries for M18 panels.
- Typed full API manifest model for `/api-routes`.

Missing Python core contract:

- Calendar/email read-only contracts for Source Inbox and Morning Briefing.
- Durable Plans summary that is not carried indirectly through Today.
- Full Memory workbench CLI parity for all visible Memory cards.
- Operator Loop CLI inspection for dashboard-owned loop summary.
- Chat redacted probe receipt CLI parity.

Missing CLI or script inspection path:

- `/approvals` backend summary has no dedicated inspect script.
- `/receipts`, `/events`, `/events/timeline`, `/files`, `/files/review`, and
  `/context/proposals` do not have matching read-model CLI inspection because
  their safe read models do not exist yet.
- `/api-routes` has backend and verifier coverage, but no frontend typed full
  manifest client yet.

Unsafe authority not yet granted:

- Provider/model calls beyond existing scoped local loopback probe behavior.
- Connector reads/writes, email/calendar writes, browser/web fetching,
  shell/subprocess execution, plugin runtime import, mobile control/sensors,
  background/autonomous execution, scheduler runtime, billing authority,
  memory writes, context injection, and production authority.

Mock-only or demo-only data still visible:

- `m15Review` details for approval queue, receipts, and events.
- `m16Trace` for event timeline trace.
- `m17Knowledge` for legacy evidence/file/memory viewer data.
- `m18Runtime` for local runtime and manual smoke detail cards.
- `m36FileReview` for file review packets.
- `m39ContextProposals` for context proposal cards.

Product-language or verifier blockers:

- Any page using mock data must keep mock/preview/degraded status visible.
- Do not use "Command Center" alone when a report means either Control Center
  shell or FCC product surface.
- Do not describe validation-only POST routes as product-state read models.
- Do not imply approval grants, action execution, provider authority, file
  mutation, connector writes, context injection, or runtime activation from UI
  visibility.

## Recommendations

Smallest safe next backend contracts:

- `GET /control-center/approvals/queue` with redacted approval rows, receipt
  refs, expiry, risk, and explicit identifier-only approval posture.
- `GET /control-center/receipts/summary` and
  `GET /control-center/events/summary` for redacted evidence lists.
- `GET /control-center/events/timeline` for M16 replacement with selected-detail
  evidence refs.
- `GET /control-center/files/refs` and
  `GET /control-center/files/review/summary` for file panels.
- `GET /control-center/context/proposals` with no-context-injection fields.
- `GET /control-center/plans/summary` so Plans is not dependent on Today
  summary shape.
- A typed frontend `ApiManifest` model limited to route counts,
  classifications, side-effect classes, and operation IDs.

UI states to improve:

- Add inline data-source badges for mixed real/mock surfaces, especially
  `/differentiators`, `/evidence`, `/runtime/local`, and `/runtime/manual-smoke`.
- Convert mock-only panels to empty/degraded states when backend routes are
  available but return no rows.
- Keep proposal-only and blocked-authority copy on all mutation-like controls.

Tests/verifiers to add:

- Frontend test that every route in `navItems` has a row in this report or the
  release surface manifest.
- API client tests for the future typed `/api/manifest` model.
- Product-language verifier expectation that mock-only route panels disclose
  mock/preview/degraded state.
- Backend tests for each new read-model route before any UI replaces mock data.

Authority lanes that must stay blocked:

- Provider invocation, background/autonomous provider calls, scheduler runtime,
  billing authority, connector writes, email/calendar writes, browser/web
  fetching, unrestricted shell/subprocess execution, plugin runtime import,
  memory writes, context injection, and production authority.

Naming cleanup suggestions:

- In reports, prefer "Control Center shell" or "FCC surface" instead of
  "Command Center".
- In UI copy, keep "Founder Command Center" only where it means the product
  surface, not the technical app shell.
- In route docs, mark support surfaces such as Approvals, Receipts, Events,
  Runtime, API Routes, and Differentiators as Control Center support unless the
  route is directly part of the FCC product spine.

## Verification

Commands run for this pass:

- `npm run test -- --run src/api/client.summaryEndpoints.test.ts src/components/ApprovalQueuePanel.test.tsx`:
  passed, 2 test files, 3 tests.
- `npm run test -- --run`: passed, 4 test files, 108 tests.
- `npm run typecheck --if-present`: passed.
- `git diff --check`: passed.
- `.venv/bin/python scripts/verify_control_center_frontend.py`: passed.
- `.venv/bin/python scripts/verify_documentation_integrity.py`: passed.
- `.venv/bin/python scripts/verify_product_truth.py --root .`: passed.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_release_surface_manifest.py tests/test_control_center_route_status_manifest.py`:
  passed, 11 tests.
- `make verify`: passed. The run included `scripts/verify_all.py`, 7,547
  pytest tests passed with 3 skipped, gate architecture passed, and Foundation
  Gate report-only status passed with 627 passed, 0 failed, 0 warnings, and
  0 blocked.

Skipped checks and reasons:

- None.
