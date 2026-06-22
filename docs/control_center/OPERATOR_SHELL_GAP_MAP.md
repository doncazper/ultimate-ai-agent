# Control Center Operator Shell Gap Map

Status: active UAA-P0-007 operator-shell gap map
Baseline: v0.103.0 / 0.103.0
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M172
API boundary: current FastAPI manifest has 127 OpenAPI paths

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
behavior, UAA-P1-082 explicit loopback CORS allowlist, UAA-P1-083 fail-closed
local protected-route bearer gate with an explicit local-dev bypass, and idempotency concepts in durable
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
| Today | `/today` renders the storage-backed first-loop summary plus UAA-P1-068 Today Product Spine Contract fields, UAA-P1-069 Evidence History Grammar fields, UAA-P1-073 Plans Action envelope posture, UAA-P1-074 Chat local operator truth, UAA-P1-075 Governed Code Workbench metadata, UAA-P1-076 Cross-Surface Memory Intake proposal refs, UAA-P1-077 Memory-To-Loop Binding refs, UAA-P1-078 Private Beta-Readiness Gate refs, UAA-P1-079 User Intent Understanding refs, FCC-V1-003 Today-to-Action envelope creation, FCC-V1-004 Chat receipt/handoff refs, FCC-V1-005 Memory Review decision receipt refs, FCC-V1-006 productized Evidence Timeline event groups, and FCC-V1-007 proofed route-surface refs for Actions, Chat, Memory, and Evidence. | `GET /control-center/today/summary`, `POST /control-center/today/action-envelope`, `GET /control-center/memory/review`, `GET /control-center/evidence/timeline`, `POST /control-center/memory/review/{candidate_ref}/accept`, `POST /control-center/memory/review/{candidate_ref}/correct`, `POST /control-center/memory/review/{candidate_ref}/reject`, `GET /control-center/storage/status`. | Email/calendar read-only contracts, notification contract, private beta rehearsal receipts, and post-P1-086 exact workflow evidence. | Founder Loop storage summaries and review-only Action envelope creation; loop visibility is necessary but not sufficient for completion; evidence history, Action envelopes, Chat local operator truth, durable Chat receipt/handoff refs, governed Code workbench metadata, cross-surface memory intake proposal refs, memory-to-loop refs, private beta-readiness refs, user intent refs, and backend-owned Memory Review decision receipt refs and productized Evidence Timeline events are safe-ref posture; no action execution, apply execution, handoff execution, connector writes, CRM/account sync, provider calls, email/calendar reads, notification delivery, rollback execution, reusable approval grant authority, memory write, context injection, public beta, distribution, or production authority. | `local_dev_workspace_only`. | None for read-only summary; Today-to-Action envelope creation, Chat receipt/handoff recording, Memory Review decision receipt recording, and any later mutation require exact LocalApprovalAuthority posture where applicable, idempotency, rollback/audit posture, and receipt refs. | SQLite state refs, JSONL log refs, Today-to-Action envelope receipt refs, Chat turn receipt refs, Chat handoff receipt refs, Memory Review decision receipt refs, safe evidence refs, bounded summaries, blocked states, backup manifest refs, UAA-P1-068 through UAA-P1-086 and FCC-V1-003/FCC-V1-005/FCC-V1-006/FCC-V1-007 contract/schema/verifier/test refs, checked-in visual baselines, route classification refs, and local loopback packaging proof refs. | Partial: UAA-P1-068, UAA-P1-069, UAA-P1-073, UAA-P1-074, UAA-P1-075, UAA-P1-076, UAA-P1-077, UAA-P1-078, UAA-P1-079, UAA-P1-080 through UAA-P1-086 perimeter contracts, FCC-V1-003 first vertical slice, FCC-V1-004 Chat receipt/handoff, FCC-V1-005 Memory Review decisions, FCC-V1-006 Evidence Timeline productization, and FCC-V1-007 proofed route-surface promotion for Actions, Chat, Memory, and Evidence are implemented; product-readiness claims remain blocked. | Integration contracts, notification contracts, memory write policy binding, private beta rehearsal receipts, and full API/Foundation Gate extraction remain future work. |
| Inbox | `/inbox` renders a blocked/planned Founder Command Center communication triage posture. It is visible in the primary loop but does not bind to live email, calendar, account, draft UI, or connector runtime behavior. | None. | Inbox source status route, draft-only proposal UI binding, connector/account readiness route. | Presentation-only route posture; no connector runtime, connector reads/writes, account auth, credential handling, message send/archive/delete/label/move, raw message/calendar metadata display, memory writes, context injection, model/provider calls, background fetch, notification delivery, or production authority. FCC-P1-007, FCC-P1-008, and FCC-P1-009 are contract-only Python-core metadata/proposal envelopes. | `/inbox` is local UI state only. Future connector metadata routes must declare read-only/validation-only side-effect classes before UI controls appear. | No approval for the blocked posture page. Future triage, draft proposal, or connector actions require exact scope, LocalApprovalAuthority boundary, idempotency, rollback/safe-disable posture, audit, and receipt refs. | Product spec and gap-map refs plus contract-only calendar/email/draft proposal test evidence; no connector receipts, account proofs, raw source evidence, sent draft, or completion evidence. | Missing/blocked. | Draft UI binding, connector/account readiness route, and frontend tests proving no send/write authority remain future scoped. |
| Action Inbox | `/actions` renders review-ready action proposal summaries from local Founder Loop storage with UAA-P1-073 Action envelope contract posture, FCC-V1-003 Today-to-Action envelope receipts, backend-owned decision controls, exact scope refs, side-effect/risk/approval posture, idempotency, expiry, expected receipt refs, rollback/safe-disable posture, blocked authority refs, receipt/audit refs when available, and next safe action labels. | `GET /control-center/actions/inbox`; `POST /control-center/today/action-envelope`; `POST /control-center/actions/{action_id}/approve`; `POST /control-center/actions/{action_id}/edit`; `POST /control-center/actions/{action_id}/reject`; `POST /control-center/actions/{action_id}/defer`; `GET /control-center/actions/{action_id}/receipt`. | Action execution contract. | Backend decision state only; Today-to-Action creation and approve/edit/reject/defer produce local receipt refs but do not send, run, install, dispatch, write memory, perform connector writes, execute shell/subprocess work, call model/provider runtime, or grant production authority. | `local_dev_workspace_only`. | Read-only inbox and receipt inspection need no approval. Today-to-Action creation requires idempotency and exact approval posture; approve validates exact LocalApprovalAuthority scope; edit, reject, and defer require idempotency, audit, and receipt refs. Approval refs remain identifiers until exact scope is validated. | Action proposal refs, Today-to-Action envelope receipt refs, UAA-P1-073 Action envelope contract refs, side-effect class, risk class, blocked-state labels, backend decision receipt refs, receipt/audit/idempotency/rollback refs, expected receipt refs, and evidence refs only. | Proofed route surface: reviewable Action envelope metadata, Today-to-Action envelope creation, backend-owned decision state, receipt refs, Evidence Timeline visibility, and CLI inspection parity are implemented for the exact `/actions` behavior; action execution remains pending. | Action execution and broader vertical-loop hardening remain future work. |
| Morning Briefing | `/briefing` renders bounded local briefing summaries with source-readiness posture, priorities, blockers, stale-state posture, evidence gaps, missing source-contract refs, and next safe action labels. | `GET /control-center/morning-briefing/summary`. | Email/calendar read-only contracts, briefing refresh contract, notification contract. | Local briefing skeleton only; no email/calendar access, connector reads/writes/runtime, account auth, background refresh, notification delivery, model/provider output authority, memory writes, or production authority. | `local_dev_workspace_only`. | None for read-only briefing summaries. Source reads, refresh, notifications, connector access, and memory writes remain unscoped. | Briefing refs, safe summaries, source-readiness labels, missing email/calendar/notification contract refs, stale-state posture, evidence-gap summaries, evidence refs, and blocked states only. | Partial. | Integration contracts, redacted source evidence binding, notification delivery contract, and visual baseline capture remain future work. |
| Memory Review | `/memory` renders the storage-backed Founder Loop memory review queue with candidate provenance/source/evidence refs, UAA-P1-071 review-only decision metadata, UAA-P1-072 business-memory candidate/quality metadata, UAA-P1-076 cross-surface intake proposals, UAA-P1-077 memory-to-loop refs, and FCC-V1-005 backend-owned accept/correct/reject decision receipts. FCC-P1-010 adds a contract-only relationship/follow-up candidate schema for future review workflows. | `GET /control-center/today/summary`, `GET /control-center/memory/review`, `GET /control-center/memory/review/{candidate_ref}/receipt`, `GET /control-center/evidence/timeline`, `POST /control-center/memory/review/{candidate_ref}/accept`, `POST /control-center/memory/review/{candidate_ref}/correct`, `POST /control-center/memory/review/{candidate_ref}/reject`. | Memory write policy binding, retention/delete/export execution contract, external CRM write/account-sync contract, connector write contract, and context-injection contract. | Backend-owned Memory Review decisions record receipt refs; accept/correct create reviewed recall-only `LocalMemoryStore` records with safe refs, correct stores `corrected_summary_ref` only, and reject preserves stale candidates as rejected review state without creating recall records. No automatic memory writes, source/memory truth authority, context injection, model/provider authority, connector writes, raw transcript/prompt/source display, background sync, memory delete/export execution, external CRM writes, account sync, action execution, public beta, or production authority. | `local_dev_workspace_only`. | None for read-only review queue inspection. Accept, correct, and reject require idempotency and backend receipt refs; retain, automatic write, delete, export, CRM sync, context-injection, quality-control actions, approval capture, action execution, and loop-binding mutation require later exact scoped memory contracts. | Memory candidate refs, safe summaries, provenance refs, source refs, evidence refs, review state, UAA-P1-071 decision refs, UAA-P1-072 business quality refs, UAA-P1-076 intake refs, UAA-P1-077 loop/action/weekly-review refs, FCC-V1-005 decision receipt refs, idempotency refs, replay/conflict posture, Evidence Timeline refs, authority boundary, blocked states, and next safe action labels only. | Proofed route surface: UAA-P1-071, UAA-P1-072, UAA-P1-076, UAA-P1-077, FCC-V1-005 decision receipts, and FCC-V1-007 proof evidence are implemented for the exact `/memory` behavior; memory write/context policies remain missing. | Write policy binding, retention/delete/export semantics, external CRM write/account sync, connector writes, context-injection policy, and broader CLI inspection polish remain future work. |
| Setup Assistant | `/setup` shows the macOS-first setup preview using the read-only backend summary when available and the existing mock fallback otherwise. | `GET /control-center/setup-assistant/summary`. | Setup approval grant capture route, rollback status route, native SwiftUI shell. | Existing macOS Setup Assistant dry-run approval-envelope contract only; no installer authority, signed installer readiness, shell/subprocess execution, model download, LaunchAgent installation/load/start, background-service installation/load/start, provider/model call, credential handling, receipt/audit persistence, rollback execution, public distribution, production readiness, or production authority. | `validation_only`; `/setup` remains an inspection UI. | Dry-run envelopes may name exact future approval scope refs for review only; approval refs remain identifiers and grant no setup mutation authority in this slice. | Dry-run setup plan/envelope with bounded previews, safe approval scope refs, receipt refs, audit ref, latency ref, rollback refs, idempotency refs, stale-state handling, and denied side-effect flags only. | Partial. | Rollback rehearsal, bounded real setup-log source, native macOS visual QA, signed/distribution proof, and any scoped setup mutation authority remain future work. |
| Chat Local Operator | `/chat` probes a redacted local turn through the governed local chat gateway, records a durable safe Chat receipt, and records reviewable Actions/Plans handoff receipts while showing contract ref, route, model/runtime/auth/tool-denial truth, safe evidence refs, blocked states, and denied authority posture. OpenWebUI remains the separate local/dev shell. | `GET /v1/models`, `POST /v1/chat/completions`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `GET /control-center/today/summary`, `POST /control-center/chat/turns`, `GET /control-center/chat/turns/{turn_ref}/receipt`, `POST /control-center/chat/turns/{turn_ref}/handoff`. | Auth setup/status route, tools/functions/streaming denial summary route, Memory Review decision binding, and later governed execution workflow routes. | UAA-P1-074 local operator truth and FCC-V1-004 durable receipt/handoff refs only; model output is not truth, memory, approval evidence, or execution authority. Handoffs create reviewable proposals only. OpenWebUI and Control Center output are not authority, and OpenWebUI state is not product state. | `/v1/*` and Founder Loop Chat receipt routes are `local_dev_workspace_only`; runtime routes are `validation_only`; `/chat` uses local UI state plus backend-owned receipt refs. | Local gateway must be explicitly enabled and bearer-authorized; Chat receipt and handoff routes require idempotency; no approval grant converts model output into authority or execution. | UAA-P1-074 contract/schema/verifier/test refs, FCC-V1-004 receipt/verifier/test refs, safe turn evidence refs, tool-denial refs, handoff receipt refs, P0-005 smoke harness refs, M167 evidence matrix refs, P0-015 checklist evidence refs, API gateway tests, and latency report refs. | Proofed route surface: first-party Chat local operator truth, durable Chat receipts, reviewable handoff receipts, and FCC-V1-007 proof evidence are implemented for the exact `/chat` behavior; handoff execution, memory writes, and product-readiness claims remain blocked. | Reviewed local model evidence, tools/functions/streaming denial summary route, Memory Review decision binding, and later Code/loop integration. |
| Plans | `/operator-loop` exposes the UAA-P1-011 readable proof chain for task decomposition, one safe capability approval path, and receipt/audit/latency/rollback inspection. `/plans` remains accessible loading/error/empty/blocked/denied state copy only, while the Today spine now exposes UAA-P1-073 reviewable Action envelope metadata and UAA-P1-074 Chat proposal handoff refs for plan summaries. | `GET /task-decomposition/status`, `GET /task-decomposition/catalog`, `POST /task-decomposition/classify`, `POST /task-decomposition/decompose`, `POST /task-decomposition/plans/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `POST /task-decomposition/plans/execute`, `POST /task-decomposition/run`, `GET /control-center/today/summary`. | DAG/status summary route, durable run binding route, pause/resume/cancel status route, replay summary route, and broader product Plans workflow binding. | Local task-decomposition API plus LocalApprovalAuthority for safe registered capabilities only; UAA-P1-073 envelope metadata and UAA-P1-074 Chat handoff refs are read-only and do not grant plan execution or approval capture. | `local_dev_workspace_only`; `/plans` and `/operator-loop` are local UI state only. | Exact approval grant for each safe registered capability; no unscoped approval ref authority. UAA-P1-073 approval refs and UAA-P1-074 handoff refs remain identifiers only. | Task audit summaries, metrics, approval queue, safe task decomposition result envelopes, UAA-P1-073 envelope refs, UAA-P1-074 Chat handoff refs, exact scope refs, expected receipt refs, rollback/safe-disable refs, and blocked authority refs. | Partial: UAA-P1-011 readable loop, UAA-P1-073 Action envelope posture, and UAA-P1-074 Chat handoff posture are surfaced; broader Plans product loop remains partial. | Broader product Plans workflow binding, UAA-P1-030 route status manifest, and future Founder Command Center IA work. |
| Models | `/models` now exposes accessible loading/error/empty/blocked/denied state copy only. Runtime panels still carry the implemented readiness/capability summaries. UAA-P1-064 adds read-only Python Agent Core inventory and CLI inspection only. UAA-P1-066 is queued support for strictly read-only Control Center inventory/status; Control Center still has no activation control from either milestone. | `GET /v1/models`, `POST /models/route/preview`, `POST /model-runtime/manifests/validate`, `POST /model-runtime/requests/validate`, `POST /model-runtime/responses/validate`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`; CLI-only `uaa local-model status/list/inspect` for UAA-P1-064 inventory. | Installed GGUF status route, current loaded-model status route, memory-fit planner route, GGUF selection/approval/readiness route, llama.cpp lifecycle status route, dry-run switch planner, approval-bound switch execution route, one-big-model guard status, identity-update receipt route, tuning recommendation route, rollback status route, read-only Control Center inventory table. | M160-M167 local model lane only; model/provider output is not production authority. UAA-P1-064 adds read-only inventory and CLI inspection only; UAA-P1-066 may only render read-only backend-owned inventory/status state. Lifecycle, switch receipts, identity updates, safe-disable, and rollback remain future Python Agent Core authority. Control Center and OpenWebUI render state and request governed actions only. | `/v1/*` is `local_dev_workspace_only`; model-runtime and model-route validation routes are `validation_only`; `/models` is local UI state only unless UAA-P1-066 later adds a read-only backend route with side-effect classification and OpenAPI/API manifest tests. UAA-P1-064 has no route or OpenAPI authority. | Approved GGUF/model refs and reviewed local runtime settings are required before live local use. Exact approval is required for any start, stop, switch, identity update, or lifecycle mutation. | M167 evidence matrix, local E2E smoke harness, P0-015 checklist evidence refs, P0-016 tuning hardening test refs, P0-017 operational runbook refs, UAA-P1-062 scope doc, UAA-P1-064 read-only inventory scope doc, UAA-P1-066 read-only Control Center status scope doc, UAA-P1-064 core/CLI test refs, route preview decisions, latency results, and future backend receipts for status, fit plans, lifecycle actions, identity updates, redacted logs/status, safe-disable, and rollback. | Partial: CLI inventory only; UAA-P1-066 is queued as the read-only Control Center status support milestone behind the UAA-P1-068 Today Product Spine Contract lane. | Reviewed local operational recovery evidence, reviewed hardware evidence, UAA-P1-066 read-only UI scope, later backend contracts, one-big-model enforcement, redacted lifecycle receipts, and switch rollback proof. |
| Approvals | `/approvals` uses `ApprovalQueuePanel` with read-only/preview-only mock or summary data. | `GET /control-center/approvals/summary`, `POST /approvals/requests/validate`, `POST /approvals/grants/validate`, `POST /approvals/validate`, `POST /approvals/receipts/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`. | CCC live approval capture/revoke UI routes, approval evidence summary route, approval expiry and replay status route. | Python Agent Core and LocalApprovalAuthority remain the only approval authority; approval refs are identifiers only. | Control Center and `/approvals/*` routes are `validation_only`; task-decomposition approval routes are `local_dev_workspace_only`. | Exact-scope grant capture or revoke through the approved backend contract. | Approval summary, validation decisions, task approval queue, grant/revoke records, audit summaries. | Partial. | UAA-P1-011 operator loop and UAA-P1-030 route status manifest. |
| Files | `/files` shows safe file refs. `/files/review` shows review packets; its review-only buttons update local UI state and are not product completion evidence. | `POST /files/refs/validate`, `POST /files/review/approvals/capture`, `POST /files/tree/preview`, `POST /files/read/preview`, `POST /files/write/propose`, `POST /files/diff/preview`. | Patch apply route, rollback receipt route, file operation status route, CCC binding to approval capture route. | Safe-root refs and server-owned file refs only; no raw file browsing or shell execution. | `local_dev_workspace_only`. | Mutating file work must be exact-approved, idempotent, audited, rollback-aware, and tested. | Safe tree refs, redacted preview result, review approval capture decision, write proposal decision, diff summary, future rollback receipt. | Partial. | M173 atomic apply/rollback gates and CCC binding to approval capture route. |
| Runtime | `/runtime`, `/runtime/local`, `/runtime/manual-smoke`, `/storage`, dashboard summaries, Foundation Gate panel, and API route inventory. | `GET /health`, `GET /version`, `GET /api/manifest`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `POST /runtime/smoke-reports/validate`, `GET /control-center/status`, `GET /control-center/runtime-readiness/summary`, `GET /control-center/foundation-gate/summary`, `GET /control-center/storage/status`, `GET /control-center/routes`. | Local model readiness aggregate route, latency report route, queue status route, installed/current model status route, memory-fit status route, loopback llama.cpp reviewed-settings lifecycle status route, redacted lifecycle log/status route. | Read-only/validation-only runtime status until a scoped milestone grants exact local lifecycle authority. UAA-P1-062 shaped status and planning first, but start/stop/switch remains blocked until exact backend authority, approvals, receipts, and rollback are accepted. | `/health`, `/version`, and `/api/manifest` are `none`; runtime and Control Center summary routes are `validation_only`; Founder Loop storage status is `local_dev_workspace_only`. | No approval for read-only status. Any lifecycle launch, stop, switch, or identity update must be separately scoped and approved. | Runtime readiness report, capability matrix, Foundation Gate summary, Founder Loop storage refs, P0-015 checklist evidence refs, performance report refs, UAA-P1-062 scope doc, and future status/fit/lifecycle receipt refs. | Partial. | Reviewed local llama.cpp lifecycle prerequisite evidence, UAA-P1-013 verification lanes, UAA-P1-030 route status manifest, later CLI parity, and redacted local model manager receipts. |
| Evidence | `/evidence` starts with the storage-backed UAA-P1-069 Evidence History Grammar timeline, including UAA-P1-074 Chat local operator, UAA-P1-075 governed Code proposal history, UAA-P1-076 cross-surface memory intake proposal history, UAA-P1-077 memory-to-loop binding history, UAA-P1-078 private beta-readiness gate history, and UAA-P1-079 user intent proposal history, then keeps the existing evidence viewer. `/receipts`, `/events`, `/events/timeline`, `/foundation-gate`, and `/api-routes` show redacted summaries and refs. | `GET /control-center/today/summary`, `POST /receipts/preview`, `POST /events/validate`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `GET /observability/session-events`, `POST /observability/client-errors`, `GET /control-center/foundation-gate/summary`, `GET /control-center/routes`, `GET /web-evidence/status`, `POST /web-evidence/request`. | Release evidence index route, latency report summary route, rollback status route, run receipt trace route backed by durable records, governed evidence display binding. | Evidence is read-only review material; safe refs and redacted summaries only. Timeline refs are identifiers and do not grant approval, perform rollback, enable connector runtime, apply code changes, write memory, inject context, execute memory-derived actions, execute intent, open beta access, or confer production authority. | Ledger and Control Center evidence routes are `validation_only`; task-decomposition audit/metrics, observability summaries, and Founder Loop timeline summaries are `local_dev_workspace_only`; governed web evidence request is `governed_network_read_only`. | No approval for read-only evidence inspection; mutating evidence generation must follow its owner route. | Evidence Timeline entries show readable history answers, receipt, audit, replay, rollback posture, latency, Foundation Gate, source-readiness, governed Code validation/receipt posture, cross-surface memory intake proposal posture, memory-to-loop binding posture, private beta-readiness criteria, user intent confidence/ambiguity/routing posture, redaction, stale-state, missing-evidence, blocker, and next-safe-action posture; existing evidence views remain redacted summaries and refs. | Proofed route surface: UAA-P1-069 grammar, UAA-P1-074 Chat evidence, UAA-P1-075 governed Code evidence, UAA-P1-076 memory intake evidence, UAA-P1-077 memory-to-loop evidence, UAA-P1-078 private beta-readiness evidence, UAA-P1-079 user intent evidence, FCC-V1-006 Evidence Timeline productization, and FCC-V1-007 proof evidence are implemented for the exact `/evidence` behavior; richer release evidence and durable trace bindings remain pending. | UAA-P1-010 durable run spine, dedicated evidence index routes, richer observability dashboard work, and route status manifest follow-up bindings. |
| Settings | `/settings` now exposes accessible loading/error/empty/blocked/denied state copy only. Local backend base policy remains code/config only, and FCC-P1-011 adds the Settings kill-switch/feature-flag spec foundation. | No dedicated settings route. Related status comes from `/control-center/status`, `/runtime/readiness`, and `/api/manifest`. | Settings manifest route, loopback auth-token setup/status route, feature-flag route, kill-switch status route, reviewed local llama.cpp settings route, local model identity/alias status route, local model lifecycle safe-disable route. | Settings must remain disabled-by-default, redacted, local-only, revocable, and policy-gated. Feature-flag, kill-switch, permission-mode, model identity, and lifecycle names are posture vocabulary only until separate scoped authority exists. | `/settings` is local UI state only. Future settings routes must declare `validation_only` or exact scoped `local_dev_workspace_only`. | Exact approval is required for any setting that enables runtime authority, persistence, local lifecycle behavior, model identity mutation, or other mutation. | FCC-P1-011 spec refs in `docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md`, UAA-P1-062 scope doc, plus existing status summaries and docs; future local model manager receipts must use redacted refs only. | Spec foundation ready; implementation missing. | UAA-P1-030 route status manifest, UAA-P1-014 local runtime packaging, later local model manager contracts, and later scoped settings milestone. |

## Visible Action Map

Current visible actions expose UAA-P1-011 as inspection evidence only:

| Visible action | Current behavior | Route authority and side-effect class | Product-readiness result |
|---|---|---|---|
| Navigate/select a card or row | Local UI state only. | No backend route. | Safe for review, not completion evidence. |
| Preview action | Calls `POST /control-center/actions/preview`. | `validation_only`; execution remains denied. | Safe preview only. |
| Record Action Inbox decision | Calls `POST /control-center/actions/{action_id}/approve`, `/edit`, `/reject`, or `/defer`, then reads `GET /control-center/actions/{action_id}/receipt`. | `local_dev_workspace_only`; decision state is backend-owned and mutating routes require local auth, exact approval where required, idempotency, and receipts. | Records decision receipt refs only; action execution remains denied. |
| Approve review-only / Deny review-only on File Review | Updates local component state for review-only display. | No backend route call in CCC Web. | Not product completion evidence; must not be described as a real approval. |
| Load dashboard/runtime/routes summaries | Reads local summary endpoints. | `none` or `validation_only`. | Safe status evidence only. |

No visible CCC action currently sends a chat message, launches llama.cpp,
selects a GGUF model, creates a broader product Plans loop, executes an
approved Action Inbox decision, executes a
capability outside the existing approval-bound backend path, applies a file
patch, rolls back a mutation, changes Settings, or grants broad authority.

Future visible actions for Today, Inbox, Plans, Actions, Memory, Evidence, and
Settings must document the backing Python core/API contract, side-effect class,
approval requirement, command-line or repo-local script inspection path, tests,
and redacted evidence before they can be treated as operator-relevant product
behavior. A React-only implementation is local presentation state, not product
workflow completion evidence.

The bounded FCC-V1 conveyor in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md` is complete through
FCC-V1-007 for converting posture into one receipt-bearing Founder loop.
`/actions`, `/chat`, `/memory`, and `/evidence` are proofed only for their
exact backend-owned route-surface behavior; `/today`, `/inbox`, `/settings`,
model lifecycle, action execution, connector workflows, and product-readiness
claims remain partial, blocked, or future-scoped.

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
9. Keep the completed FCC-V1 Founder Loop V1 conveyor honest: FCC-V1-000 through
   FCC-V1-007 are complete for release-surface truth, API perimeter posture,
   Action decisions, first Today-to-Action receipt loop, Chat durable receipts
   and handoffs, Memory Review decisions, Evidence Timeline productization, and
   exact proofed route-surface promotion of `/actions`, `/chat`, `/memory`, and
   `/evidence`; broader product readiness remains blocked until later evidence.

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
