# Control Center Operator Shell Gap Map

Status: active UAA-P0-007 operator-shell gap map
Baseline: v0.102.3 / 0.102.3
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M172
API boundary: current FastAPI manifest has 112 OpenAPI paths

This map is production-readiness scaffolding for the Control Center operator
shell. It does not add runtime authority, backend routes, frontend controls,
shell/subprocess execution, browser automation, connector writes, plugin runtime
import, mobile control, autonomous background execution, or public distribution.

Control Center and OpenWebUI remain shells. Python Agent Core, PolicyEngine,
LocalApprovalAuthority, route side-effect classification, OpenAPI checks, and
Foundation Gate checks remain the authority boundaries.

UI surface direction: Control Center / Founder Command Center is the
first-party product cockpit for Today, Inbox, Plans, Actions, Memory, Evidence,
Settings, Models, and future first-party Chat. OpenWebUI remains a supported
local/dev conversational shell and compatibility surface for governed `/v1`
smoke, llama.cpp shell testing, and developer chat. OpenWebUI must not become
the source of product state or the destination for wiring every UAA workflow.
`/private-trial` is the UAA-P1-087.2a/087.2b/087.2c read-only packet,
acceptance ledger, and unanswered manual-review scaffold surface only; it
records safe manual smoke checklist refs, manual smoke step refs, pending
surface review refs, acceptance question refs, tuning decision refs, unanswered
pending answer refs, missing implementation refs, friction refs, UI/copy task
refs, core-loop gap refs, and blocked authority refs without backend routes or
runtime authority. Full UAA-P1-087.2 private UI tuning is deferred until more
Founder Loop implementation exists and accepted or revised local/private
findings are recorded later.

API boundary hardening gap: because Control Center is browser-facing,
UAA-P1-080 now makes public/protected route posture explicit before
authority-heavy product claims. Existing partial coverage includes OpenAPI/API
manifest metadata, route side-effect classes, route-status auth posture,
P1-080 route classification as `public_metadata`, `local_readonly`,
`local_sensitive`, or `mutating_requires_authority`, UAA-P1-081 centralized
response security headers, disabled-by-default bearer-gated local `/v1`
behavior, UAA-P1-082 explicit loopback CORS allowlist, UAA-P1-083 configured
local protected-route bearer gate, and idempotency concepts in durable
run/action planning. UAA-P1-084 now adds a mutating-route idempotency header
gate without durable dedupe, exactly-once execution, replay execution, rate
limits, mutation authority, or production authority. UAA-P1-085 now adds
targeted local fixed-window rate limits without auth, distributed quota,
dependencies, billing, or production authority. UAA-P1-086 now adds OpenAPI/
API manifest/route inventory enforcement tests without route, middleware, or
runtime authority changes. CORS is browser hardening, not auth.

CLI is a first-class operator surface. The Control Center may expose a workflow
only as a shell over the same Python core/API contract that can be inspected or
operated from a command-line or repo-local script path. Product behavior must not
live only in React state; UI-only state is limited to presentation concerns such
as filters, expanded panels, selected tabs, and layout preferences.

Evidence sources for this map:

- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/api/endpoints.ts`
- `src/ultimate_ai_agent/api/app.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `tests/test_control_center_api_routes.py`
- `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`
- `docs/control_center/ROUTE_STATUS_MANIFEST.md`
- `docs/control_center/route_status_manifest.json`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`
- `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`
- `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`
- `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`

## Route Classes

The current API manifest classifies route side effects as:

| Class | Meaning for operator shell mapping |
|---|---|
| `none` | System metadata such as `/health`, `/version`, `/api/manifest`, and governed capability status. |
| `validation_only` | Review, preview, validation, and summary routes that do not execute production work. |
| `local_dev_workspace_only` | Local-only workspace or local gateway routes. These are not broad production authority. |
| `governed_network_read_only` | UAA-P1-063 allowlisted HTTPS GET evidence route with bounded redacted preview and receipt refs only. |

## Surface Matrix

| Surface | Current frontend component/page | Current backend route(s) | Missing backend route(s) | Authority boundary | Side-effect class | Approval requirement | Evidence/audit output | Readiness status | Production-readiness blocker |
|---|---|---|---|---|---|---|---|---|---|
| Today | `/today` renders the storage-backed first-loop summary plus UAA-P1-068 Today Product Spine Contract fields, UAA-P1-069 Evidence History Grammar fields, UAA-P1-073 Plans Action envelope posture, UAA-P1-074 Chat local operator truth, UAA-P1-075 Governed Code Workbench metadata, UAA-P1-076 Cross-Surface Memory Intake proposal refs, UAA-P1-077 Memory-To-Loop Binding refs, UAA-P1-078 Private Beta-Readiness Gate refs, and UAA-P1-079 User Intent Understanding refs. | `GET /control-center/today/summary`, `GET /control-center/storage/status`. | Today action mutation contract, email/calendar read-only contracts, notification contract, private beta rehearsal receipts, and post-P1-086 exact workflow evidence. | Founder Loop storage summaries only; loop visibility is necessary but not sufficient for completion; evidence history, Action envelopes, Chat local operator truth, governed Code workbench metadata, cross-surface memory intake proposal refs, memory-to-loop refs, private beta-readiness refs, and user intent refs are read-only posture; no action execution, apply execution, approval grant capture, connector writes, provider calls, email/calendar reads, notification delivery, rollback execution, approval grant, memory write, context injection, public beta, distribution, or production authority. | `local_dev_workspace_only`. | None for read-only summary; any mutation requires exact LocalApprovalAuthority scope, idempotency, rollback, audit, and receipt refs. | SQLite state refs, JSONL log refs, safe evidence refs, bounded summaries, blocked states, backup manifest refs, UAA-P1-068 through UAA-P1-086 contract/schema/verifier/test refs, checked-in visual baselines, route classification refs, and local loopback packaging proof refs. | Partial: UAA-P1-068, UAA-P1-069, UAA-P1-073, UAA-P1-074, UAA-P1-075, UAA-P1-076, UAA-P1-077, UAA-P1-078, UAA-P1-079, and UAA-P1-080 through UAA-P1-086 perimeter contracts are implemented; product-readiness claims remain blocked. | Scoped mutation contracts, integration contracts, notification contracts, memory write policy binding, private beta rehearsal receipts, exact workflow evidence, and full API/Foundation Gate extraction remain future work. |
| Inbox | `/inbox` renders a blocked/planned Founder Command Center communication triage posture. It is visible in the primary loop but does not bind to live email, calendar, account, draft UI, or connector runtime behavior. | None. | Inbox source status route, draft-only proposal UI binding, connector/account readiness route. | Presentation-only route posture; no connector runtime, connector reads/writes, account auth, credential handling, message send/archive/delete/label/move, raw message/calendar metadata display, memory writes, context injection, model/provider calls, background fetch, notification delivery, or production authority. FCC-P1-007, FCC-P1-008, and FCC-P1-009 are contract-only Python-core metadata/proposal envelopes. | `/inbox` is local UI state only. Future connector metadata routes must declare read-only/validation-only side-effect classes before UI controls appear. | No approval for the blocked posture page. Future triage, draft proposal, or connector actions require exact scope, LocalApprovalAuthority boundary, idempotency, rollback/safe-disable posture, audit, and receipt refs. | Product spec and gap-map refs plus contract-only calendar/email/draft proposal test evidence; no connector receipts, account proofs, raw source evidence, sent draft, or completion evidence. | Missing/blocked. | Draft UI binding, connector/account readiness route, and frontend tests proving no send/write authority remain future scoped. |
| Action Inbox | `/actions` renders review-ready action proposal summaries from local Founder Loop storage with UAA-P1-073 Action envelope contract posture, state-change readiness, exact scope refs, side-effect/risk/approval posture, review actions, idempotency, expiry, expected receipt refs, rollback/safe-disable posture, blocked authority refs, receipt/audit refs when available, and next safe action labels. | `GET /control-center/actions/inbox`. | Action inbox state-change contract, approval-envelope capture contract, replay summary. | Review queue only; no grant capture, denial, send, run, install, dispatch, connector write, shell/subprocess execution, or model/provider authority. | `local_dev_workspace_only`. | Read-only inspection needs no approval; state changes require exact approval scope, idempotency, rollback, audit, and receipt refs. Approval refs are identifiers only until exact LocalApprovalAuthority scope is validated by a later accepted milestone. | Action proposal refs, UAA-P1-073 Action envelope contract refs, side-effect class, risk class, blocked-state labels, receipt/audit/idempotency/rollback refs, expected receipt refs, and evidence refs only. | Partial: reviewable Action envelope metadata is implemented; action state changes remain pending. | State-change contract, approval grant capture, denial capture, CLI inspection path, and durable receipt binding remain future work. |
| Morning Briefing | `/briefing` renders bounded local briefing summaries with source-readiness posture, priorities, blockers, stale-state posture, evidence gaps, missing source-contract refs, and next safe action labels. | `GET /control-center/morning-briefing/summary`. | Email/calendar read-only contracts, briefing refresh contract, notification contract. | Local briefing skeleton only; no email/calendar access, connector reads/writes/runtime, account auth, background refresh, notification delivery, model/provider output authority, memory writes, or production authority. | `local_dev_workspace_only`. | None for read-only briefing summaries. Source reads, refresh, notifications, connector access, and memory writes remain unscoped. | Briefing refs, safe summaries, source-readiness labels, missing email/calendar/notification contract refs, stale-state posture, evidence-gap summaries, evidence refs, and blocked states only. | Partial. | Integration contracts, redacted source evidence binding, notification delivery contract, and visual baseline capture remain future work. |
| Memory Review | `/memory` renders the storage-backed Founder Loop memory review queue with candidate provenance/source/evidence refs, UAA-P1-071 review-only decision metadata, UAA-P1-072 business-memory candidate/quality metadata, UAA-P1-076 cross-surface intake proposals, and UAA-P1-077 memory-to-loop refs. FCC-P1-010 adds a contract-only relationship/follow-up candidate schema for future review workflows. | `GET /control-center/today/summary`. | Memory write policy binding, retention/delete/export execution contract, external CRM write/account-sync contract, and context-injection contract. | Review-only memory candidates, review-only decision metadata, review-only business quality metadata, review-only intake proposals, and read-only loop-binding refs; no automatic memory writes, context injection, model/provider authority, connector writes, raw transcript/prompt/source display, background sync, memory delete/export execution, external CRM writes, account sync, or production authority. | `local_dev_workspace_only`. | None for read-only review queue inspection. Accept, correct, reject, retain, delete, export, write, CRM sync, context-injection, quality-control actions, approval capture, action execution, and loop-binding mutation require later exact scoped memory contracts. | Memory candidate refs, safe summaries, provenance refs, source refs, evidence refs, review state, UAA-P1-071 decision refs, UAA-P1-072 business quality refs, UAA-P1-076 intake refs, UAA-P1-077 loop/action/weekly-review refs, authority boundary, blocked states, and next safe action labels only. | Partial: UAA-P1-071, UAA-P1-072, UAA-P1-076, and UAA-P1-077 contracts are implemented; memory mutation policies remain missing. | Write policy binding, retention/delete/export semantics, external CRM write/account sync, context-injection policy, CLI inspection path, and durable receipt binding remain future work. |
| Setup Assistant | `/setup` shows the macOS-first setup preview using the read-only backend summary when available and the existing mock fallback otherwise. | `GET /control-center/setup-assistant/summary`. | Setup approval grant capture route, rollback status route, native SwiftUI shell. | Existing macOS Setup Assistant dry-run approval-envelope contract only; no installer authority, signed installer readiness, shell/subprocess execution, model download, LaunchAgent installation/load/start, background-service installation/load/start, provider/model call, credential handling, receipt/audit persistence, rollback execution, public distribution, production readiness, or production authority. | `validation_only`; `/setup` remains an inspection UI. | Dry-run envelopes may name exact future approval scope refs for review only; approval refs remain identifiers and grant no setup mutation authority in this slice. | Dry-run setup plan/envelope with bounded previews, safe approval scope refs, receipt refs, audit ref, latency ref, rollback refs, idempotency refs, stale-state handling, and denied side-effect flags only. | Partial. | Rollback rehearsal, bounded real setup-log source, native macOS visual QA, signed/distribution proof, and any scoped setup mutation authority remain future work. |
| Chat Local Operator | `/chat` sends a redacted local turn through the governed local chat gateway and shows contract ref, route, model/runtime/auth/tool-denial truth, safe evidence refs, proposal handoff refs, blocked states, and denied authority posture. OpenWebUI remains the separate local/dev shell. | `GET /v1/models`, `POST /v1/chat/completions`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `POST /control-center/actions/preview`, `GET /control-center/today/summary`. | Dedicated chat receipt summary route, auth setup/status route, tools/functions/streaming denial summary route, governed Chat-to-Plans/Actions workflow route. | UAA-P1-074 local operator truth only; model output is not truth, memory, approval evidence, or execution authority. OpenWebUI and Control Center output are not authority, and OpenWebUI state is not product state. | `/v1/*` is `local_dev_workspace_only`; runtime and Control Center preview routes are `validation_only`; `/chat` uses local UI state plus Today safe refs. | Local gateway must be explicitly enabled and bearer-authorized; no approval grant converts model output into authority. | UAA-P1-074 contract/schema/verifier/test refs, safe turn evidence refs, tool-denial refs, handoff refs, P0-005 smoke harness refs, M167 evidence matrix refs, P0-015 checklist evidence refs, API gateway tests, and latency report refs. | Partial: first-party Chat local operator truth is implemented; durable chat receipts and governed handoff execution remain pending. | Reviewed local model evidence, durable chat receipt route, governed handoff workflow binding, and later Code/loop integration. |
| Plans | `/operator-loop` exposes the UAA-P1-011 readable proof chain for task decomposition, one safe capability approval path, and receipt/audit/latency/rollback inspection. `/plans` remains accessible loading/error/empty/blocked/denied state copy only, while the Today spine now exposes UAA-P1-073 reviewable Action envelope metadata and UAA-P1-074 Chat proposal handoff refs for plan summaries. | `GET /task-decomposition/status`, `GET /task-decomposition/catalog`, `POST /task-decomposition/classify`, `POST /task-decomposition/decompose`, `POST /task-decomposition/plans/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `POST /task-decomposition/plans/execute`, `POST /task-decomposition/run`, `GET /control-center/today/summary`. | DAG/status summary route, durable run binding route, pause/resume/cancel status route, replay summary route, and broader product Plans workflow binding. | Local task-decomposition API plus LocalApprovalAuthority for safe registered capabilities only; UAA-P1-073 envelope metadata and UAA-P1-074 Chat handoff refs are read-only and do not grant plan execution or approval capture. | `local_dev_workspace_only`; `/plans` and `/operator-loop` are local UI state only. | Exact approval grant for each safe registered capability; no unscoped approval ref authority. UAA-P1-073 approval refs and UAA-P1-074 handoff refs remain identifiers only. | Task audit summaries, metrics, approval queue, safe task decomposition result envelopes, UAA-P1-073 envelope refs, UAA-P1-074 Chat handoff refs, exact scope refs, expected receipt refs, rollback/safe-disable refs, and blocked authority refs. | Partial: UAA-P1-011 readable loop, UAA-P1-073 Action envelope posture, and UAA-P1-074 Chat handoff posture are surfaced; broader Plans product loop remains partial. | Broader product Plans workflow binding, UAA-P1-030 route status manifest, and future Founder Command Center IA work. |
| Models | `/models` now exposes accessible loading/error/empty/blocked/denied state copy only. Runtime panels still carry the implemented readiness/capability summaries. UAA-P1-064 adds read-only Python Agent Core inventory and CLI inspection only. UAA-P1-066 is queued support for strictly read-only Control Center inventory/status; Control Center still has no activation control from either milestone. | `GET /v1/models`, `POST /models/route/preview`, `POST /model-runtime/manifests/validate`, `POST /model-runtime/requests/validate`, `POST /model-runtime/responses/validate`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`; CLI-only `uaa local-model status/list/inspect` for UAA-P1-064 inventory. | Installed GGUF status route, current loaded-model status route, memory-fit planner route, GGUF selection/approval/readiness route, llama.cpp lifecycle status route, dry-run switch planner, approval-bound switch execution route, one-big-model guard status, identity-update receipt route, tuning recommendation route, rollback status route, read-only Control Center inventory table. | M160-M167 local model lane only; model/provider output is not production authority. UAA-P1-064 adds read-only inventory and CLI inspection only; UAA-P1-066 may only render read-only backend-owned inventory/status state. Lifecycle, switch receipts, identity updates, safe-disable, and rollback remain future Python Agent Core authority. Control Center and OpenWebUI render state and request governed actions only. | `/v1/*` is `local_dev_workspace_only`; model-runtime and model-route validation routes are `validation_only`; `/models` is local UI state only unless UAA-P1-066 later adds a read-only backend route with side-effect classification and OpenAPI/API manifest tests. UAA-P1-064 has no route or OpenAPI authority. | Approved GGUF/model refs and reviewed local runtime settings are required before live local use. Exact approval is required for any start, stop, switch, identity update, or lifecycle mutation. | M167 evidence matrix, local E2E smoke harness, P0-015 checklist evidence refs, P0-016 tuning hardening test refs, P0-017 operational runbook refs, UAA-P1-062 scope doc, UAA-P1-064 read-only inventory scope doc, UAA-P1-066 read-only Control Center status scope doc, UAA-P1-064 core/CLI test refs, route preview decisions, latency results, and future backend receipts for status, fit plans, lifecycle actions, identity updates, redacted logs/status, safe-disable, and rollback. | Partial: CLI inventory only; UAA-P1-066 is queued as the read-only Control Center status support milestone behind the UAA-P1-068 Today Product Spine Contract lane. | Reviewed local operational recovery evidence, reviewed hardware evidence, UAA-P1-066 read-only UI scope, later backend contracts, one-big-model enforcement, redacted lifecycle receipts, and switch rollback proof. |
| Approvals | `/approvals` uses `ApprovalQueuePanel` with read-only/preview-only mock or summary data. | `GET /control-center/approvals/summary`, `POST /approvals/requests/validate`, `POST /approvals/grants/validate`, `POST /approvals/validate`, `POST /approvals/receipts/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`. | CCC live approval capture/revoke UI routes, approval evidence summary route, approval expiry and replay status route. | Python Agent Core and LocalApprovalAuthority remain the only approval authority; approval refs are identifiers only. | Control Center and `/approvals/*` routes are `validation_only`; task-decomposition approval routes are `local_dev_workspace_only`. | Exact-scope grant capture or revoke through the approved backend contract. | Approval summary, validation decisions, task approval queue, grant/revoke records, audit summaries. | Partial. | UAA-P1-011 operator loop and UAA-P1-030 route status manifest. |
| Files | `/files` shows safe file refs. `/files/review` shows review packets; its review-only buttons update local UI state and are not product completion evidence. | `POST /files/refs/validate`, `POST /files/review/approvals/capture`, `POST /files/tree/preview`, `POST /files/read/preview`, `POST /files/write/propose`, `POST /files/diff/preview`. | Patch apply route, rollback receipt route, file operation status route, CCC binding to approval capture route. | Safe-root refs and server-owned file refs only; no raw file browsing or shell execution. | `local_dev_workspace_only`. | Mutating file work must be exact-approved, idempotent, audited, rollback-aware, and tested. | Safe tree refs, redacted preview result, review approval capture decision, write proposal decision, diff summary, future rollback receipt. | Partial. | M173 atomic apply/rollback gates and CCC binding to approval capture route. |
| Runtime | `/runtime`, `/runtime/local`, `/runtime/manual-smoke`, `/storage`, dashboard summaries, Foundation Gate panel, and API route inventory. | `GET /health`, `GET /version`, `GET /api/manifest`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `POST /runtime/smoke-reports/validate`, `GET /control-center/status`, `GET /control-center/runtime-readiness/summary`, `GET /control-center/foundation-gate/summary`, `GET /control-center/storage/status`, `GET /control-center/routes`. | Local model readiness aggregate route, latency report route, queue status route, installed/current model status route, memory-fit status route, loopback llama.cpp reviewed-settings lifecycle status route, redacted lifecycle log/status route. | Read-only/validation-only runtime status until a scoped milestone grants exact local lifecycle authority. UAA-P1-062 shaped status and planning first, but start/stop/switch remains blocked until exact backend authority, approvals, receipts, and rollback are accepted. | `/health`, `/version`, and `/api/manifest` are `none`; runtime and Control Center summary routes are `validation_only`; Founder Loop storage status is `local_dev_workspace_only`. | No approval for read-only status. Any lifecycle launch, stop, switch, or identity update must be separately scoped and approved. | Runtime readiness report, capability matrix, Foundation Gate summary, Founder Loop storage refs, P0-015 checklist evidence refs, performance report refs, UAA-P1-062 scope doc, and future status/fit/lifecycle receipt refs. | Partial. | Reviewed local llama.cpp lifecycle prerequisite evidence, UAA-P1-013 verification lanes, UAA-P1-030 route status manifest, later CLI parity, and redacted local model manager receipts. |
| Evidence | `/evidence` starts with the storage-backed UAA-P1-069 Evidence History Grammar timeline, including UAA-P1-074 Chat local operator, UAA-P1-075 governed Code proposal history, UAA-P1-076 cross-surface memory intake proposal history, UAA-P1-077 memory-to-loop binding history, UAA-P1-078 private beta-readiness gate history, and UAA-P1-079 user intent proposal history, then keeps the existing evidence viewer. `/receipts`, `/events`, `/events/timeline`, `/foundation-gate`, and `/api-routes` show redacted summaries and refs. | `GET /control-center/today/summary`, `POST /receipts/preview`, `POST /events/validate`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `GET /observability/session-events`, `POST /observability/client-errors`, `GET /control-center/foundation-gate/summary`, `GET /control-center/routes`, `GET /web-evidence/status`, `POST /web-evidence/request`. | Release evidence index route, latency report summary route, rollback status route, run receipt trace route backed by durable records, governed evidence display binding. | Evidence is read-only review material; safe refs and redacted summaries only. Timeline refs are identifiers and do not grant approval, perform rollback, enable connector runtime, apply code changes, write memory, inject context, execute memory-derived actions, execute intent, open beta access, or confer production authority. | Ledger and Control Center evidence routes are `validation_only`; task-decomposition audit/metrics, observability summaries, and Founder Loop timeline summaries are `local_dev_workspace_only`; governed web evidence request is `governed_network_read_only`. | No approval for read-only evidence inspection; mutating evidence generation must follow its owner route. | Evidence Timeline entries show readable history answers, receipt, audit, replay, rollback posture, latency, Foundation Gate, source-readiness, governed Code validation/receipt posture, cross-surface memory intake proposal posture, memory-to-loop binding posture, private beta-readiness criteria, user intent confidence/ambiguity/routing posture, redaction, stale-state, missing-evidence, blocker, and next-safe-action posture; existing evidence views remain redacted summaries and refs. | Partial: UAA-P1-069 grammar, UAA-P1-074 Chat evidence, UAA-P1-075 governed Code evidence, UAA-P1-076 memory intake evidence, UAA-P1-077 memory-to-loop evidence, UAA-P1-078 private beta-readiness evidence, and UAA-P1-079 user intent evidence are implemented; richer evidence index and durable trace bindings remain pending. | UAA-P1-010 durable run spine, dedicated evidence index routes, richer observability dashboard work, and route status manifest follow-up bindings. |
| Settings | `/settings` now exposes accessible loading/error/empty/blocked/denied state copy only. Local backend base policy remains code/config only, and FCC-P1-011 adds the Settings kill-switch/feature-flag spec foundation. | No dedicated settings route. Related status comes from `/control-center/status`, `/runtime/readiness`, and `/api/manifest`. | Settings manifest route, loopback auth-token setup/status route, feature-flag route, kill-switch status route, reviewed local llama.cpp settings route, local model identity/alias status route, local model lifecycle safe-disable route. | Settings must remain disabled-by-default, redacted, local-only, revocable, and policy-gated. Feature-flag, kill-switch, permission-mode, model identity, and lifecycle names are posture vocabulary only until separate scoped authority exists. | `/settings` is local UI state only. Future settings routes must declare `validation_only` or exact scoped `local_dev_workspace_only`. | Exact approval is required for any setting that enables runtime authority, persistence, local lifecycle behavior, model identity mutation, or other mutation. | FCC-P1-011 spec refs in `docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md`, UAA-P1-062 scope doc, plus existing status summaries and docs; future local model manager receipts must use redacted refs only. | Spec foundation ready; implementation missing. | UAA-P1-030 route status manifest, UAA-P1-014 local runtime packaging, later local model manager contracts, and later scoped settings milestone. |

## Visible Action Map

Current visible actions expose UAA-P1-011 as inspection evidence only:

| Visible action | Current behavior | Route authority and side-effect class | Product-readiness result |
|---|---|---|---|
| Navigate/select a card or row | Local UI state only. | No backend route. | Safe for review, not completion evidence. |
| Preview action | Calls `POST /control-center/actions/preview`. | `validation_only`; execution remains denied. | Safe preview only. |
| Approve review-only / Deny review-only on File Review | Updates local component state for review-only display. | No backend route call in CCC Web. | Not product completion evidence; must not be described as a real approval. |
| Load dashboard/runtime/routes summaries | Reads local summary endpoints. | `none` or `validation_only`. | Safe status evidence only. |

No visible CCC action currently sends a chat message, launches llama.cpp,
selects a GGUF model, creates a broader product Plans loop, executes a
capability outside the existing approval-bound backend path, applies a file
patch, rolls back a mutation, changes Settings, or grants broad authority.

Future visible actions for Today, Inbox, Plans, Actions, Memory, Evidence, and
Settings must document the backing Python core/API contract, side-effect class,
approval requirement, command-line or repo-local script inspection path, tests,
and redacted evidence before they can be treated as operator-relevant product
behavior. A React-only implementation is local presentation state, not product
workflow completion evidence.

The planned FCC-V1 conveyor in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md` is the active gap-closure
path for converting posture into one receipt-bearing Founder loop. Until those
milestones land, `/actions`, `/chat`, `/memory`, and `/evidence` remain partial
for real backend-owned decisions, durable receipts, handoff refs, and actual
Evidence Timeline updates.

## First Product Loop Gaps

UAA-P1-011 now has a readable Control Center proof chain for runtime health,
local model readiness, UAA `/v1` chat readiness, task plan creation, one safe
capability approval path, and receipt/audit/latency/rollback inspection. The
remaining gaps before broader product-readiness claims are:

1. Implement the UAA-P1-065 promoted FCC-P0-002 Follow-Up Collapse/Organize
   Control Center Around Core Surfaces only under a later exact UI milestone,
   keeping Today, Inbox, Plans, Actions, Memory, Evidence, and Settings as the
   primary loop while route authority and blocked states stay visible.
2. Use the UAA-P1-030 route status manifest as release evidence for visible
   action owners, auth posture, side-effect class, risk class, release status,
   OpenAPI operation ids, approval requirements, and evidence refs.
3. Add installed GGUF, current loaded-model, and reviewed GGUF
   selection/approval/readiness routes using safe refs only.
4. Add reviewed loopback llama.cpp settings, lifecycle status, redacted
   logs/status, and UAA-P1-062 memory-fit/switch planning before any lifecycle
   execute controls.
5. Extend the CCC Chat Local Operator that uses UAA `/v1` with local bearer status, auth
   failure handling, safe failure handling, and visible tools/functions/
   streaming denial into durable receipt and governed handoff workflows.
6. Add a CCC Plans surface over classify, decompose, approval request, grant
   capture, safe registered capability execution, audit, and metrics.
7. Continue expanding Evidence views beyond the FCC-P1-006 timeline only after
   durable run, evidence-index, rollback-status, and latency-report contracts
   are scoped.
8. Treat UAA-P1-086 as the completed API boundary enforcement-test checkpoint
   before any authority-heavy Plans, Chat, Code, loop-binding, or private
   beta-readiness claims can advance on later workflow evidence.
9. Complete the FCC-V1 Founder Loop V1 conveyor before promoting the first
   product loop to `ship`: release surface manifest, API perimeter for real
   mutations, Action Inbox approve/edit/reject/defer backend decisions, Today
   item to Action envelope to exact approval to durable receipt to Evidence
   update, Chat durable receipt and handoff, Memory Review accept/correct/
   reject backend decisions, Evidence Timeline productization, and proof-lane
   promotion.

These remaining gaps are release blockers for M172 product-readiness claims.

## Rollback

Rollback refs are inspection evidence only in this map. Any future Control
Center rollback action must name the exact backend route, approval boundary,
receipt ref, audit ref, idempotency key, and no-raw-content evidence before it
can be presented as a product-ready recovery path.

## Product Language Rules

The canonical enforceable UAA-P1-031 rules live in
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

- No hidden authority: visible Control Center actions must name their backend
  authority boundary and side-effect class.
- No frontend-only product behavior: visible operator workflows must preserve a
  CLI/core/API path and cannot exist only in React state.
- No fake completion: preview-only or blocked flows must not be described as
  completed product work.
- No raw JSON as primary UI for operator-critical flows: operator surfaces need
  readable summaries, states, and evidence refs before claiming readiness.
