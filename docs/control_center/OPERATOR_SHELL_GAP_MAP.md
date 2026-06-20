# Control Center Operator Shell Gap Map

Status: active UAA-P0-007 operator-shell gap map
Baseline: v0.102.0 / 0.102.0
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M172
API boundary: current FastAPI manifest has 97 OpenAPI paths

This map is production-readiness scaffolding for the Control Center operator
shell. It does not add runtime authority, backend routes, frontend controls,
shell/subprocess execution, browser automation, connector writes, plugin runtime
import, mobile control, autonomous background execution, or public distribution.

Control Center and OpenWebUI remain shells. Python Agent Core, PolicyEngine,
LocalApprovalAuthority, route side-effect classification, OpenAPI checks, and
Foundation Gate checks remain the authority boundaries.

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
| `none` | System metadata such as `/health`, `/version`, and `/api/manifest`. |
| `validation_only` | Review, preview, validation, and summary routes that do not execute production work. |
| `local_dev_workspace_only` | Local-only workspace or local gateway routes. These are not broad production authority. |

## Surface Matrix

| Surface | Current frontend component/page | Current backend route(s) | Missing backend route(s) | Authority boundary | Side-effect class | Approval requirement | Evidence/audit output | Readiness status | Production-readiness blocker |
|---|---|---|---|---|---|---|---|---|---|
| Chat Shell | `/chat` now exposes accessible loading/error/empty/blocked/denied state copy only. OpenWebUI remains the separate local shell; CCC chat composition is not implemented. | `GET /v1/models`, `POST /v1/chat/completions`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `POST /control-center/actions/preview`. | Dedicated CCC chat surface status route, chat receipt summary route, auth setup/status route, tools/functions/streaming denial summary route. | M151/M164/M166/M167 exact-bound local loopback gateway only; OpenWebUI and CCC output are not authority. | `/v1/*` is `local_dev_workspace_only`; runtime and Control Center preview routes are `validation_only`; `/chat` is local UI state only. | Local gateway must be explicitly enabled and bearer-authorized; no approval grant converts model output into authority. | P0-005 smoke harness refs, M167 evidence matrix refs, P0-015 checklist evidence refs, API gateway tests, latency report refs. | Blocked. | Reviewed `llama-server` packaging evidence, reviewed local model evidence, and a real Chat Shell UI with safe evidence binding. |
| Plans | `/plans` now exposes accessible loading/error/empty/blocked/denied state copy only. Action Preview can preview an action, but task decomposition is not surfaced as a completed product loop. | `GET /task-decomposition/status`, `GET /task-decomposition/catalog`, `POST /task-decomposition/classify`, `POST /task-decomposition/decompose`, `POST /task-decomposition/plans/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `POST /task-decomposition/plans/execute`, `POST /task-decomposition/run`. | DAG/status summary route, durable run binding route, pause/resume/cancel status route, replay summary route, and product Plans workflow binding. | Local task-decomposition API plus LocalApprovalAuthority for safe registered capabilities only. | `local_dev_workspace_only`; `/plans` is local UI state only. | Exact approval grant for each safe registered capability; no unscoped approval ref authority. | Task audit summaries, metrics, approval queue, safe task decomposition result envelopes. | Partial backend, blocked product loop. | UAA-P1-010 durable run spine, UAA-P1-011 task decomposition operator loop, and UAA-P1-030 route status manifest. |
| Models | `/models` now exposes accessible loading/error/empty/blocked/denied state copy only. Runtime panels still carry the implemented readiness/capability summaries. | `GET /v1/models`, `POST /models/route/preview`, `POST /model-runtime/manifests/validate`, `POST /model-runtime/requests/validate`, `POST /model-runtime/responses/validate`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`. | GGUF selection route, GGUF approval/readiness route, llama.cpp lifecycle status route, tuning recommendation route, rollback status route. | M160-M167 local model lane only; model/provider output is not production authority. | `/v1/*` is `local_dev_workspace_only`; model-runtime and model-route validation routes are `validation_only`; `/models` is local UI state only. | Approved GGUF/model refs and reviewed local runtime settings are required before live local use. | M167 evidence matrix, local E2E smoke harness, P0-015 checklist evidence refs, P0-016 tuning hardening test refs, P0-017 operational runbook refs, route preview decisions, latency results. | Blocked. | Reviewed local operational recovery evidence and reviewed hardware evidence. |
| Approvals | `/approvals` uses `ApprovalQueuePanel` with read-only/preview-only mock or summary data. | `GET /control-center/approvals/summary`, `POST /approvals/requests/validate`, `POST /approvals/grants/validate`, `POST /approvals/validate`, `POST /approvals/receipts/validate`, `POST /task-decomposition/approval-requests`, `GET /task-decomposition/approvals`, `POST /task-decomposition/approvals/grants/capture`, `POST /task-decomposition/approvals/revoke`. | CCC live approval capture/revoke UI routes, approval evidence summary route, approval expiry and replay status route. | Python Agent Core and LocalApprovalAuthority remain the only approval authority; approval refs are identifiers only. | Control Center and `/approvals/*` routes are `validation_only`; task-decomposition approval routes are `local_dev_workspace_only`. | Exact-scope grant capture or revoke through the approved backend contract. | Approval summary, validation decisions, task approval queue, grant/revoke records, audit summaries. | Partial. | UAA-P1-011 operator loop and UAA-P1-030 route status manifest. |
| Files | `/files` shows safe file refs. `/files/review` shows review packets; its review-only buttons update local UI state and are not product completion evidence. | `POST /files/refs/validate`, `POST /files/review/approvals/capture`, `POST /files/tree/preview`, `POST /files/read/preview`, `POST /files/write/propose`, `POST /files/diff/preview`. | Patch apply route, rollback receipt route, file operation status route, CCC binding to approval capture route. | Safe-root refs and server-owned file refs only; no raw file browsing or shell execution. | `local_dev_workspace_only`. | Mutating file work must be exact-approved, idempotent, audited, rollback-aware, and tested. | Safe tree refs, redacted preview result, review approval capture decision, write proposal decision, diff summary, future rollback receipt. | Partial. | M173 atomic apply/rollback gates and CCC binding to approval capture route. |
| Runtime | `/runtime`, `/runtime/local`, `/runtime/manual-smoke`, dashboard summaries, Foundation Gate panel, and API route inventory. | `GET /health`, `GET /version`, `GET /api/manifest`, `GET /runtime/readiness`, `GET /runtime/capability-matrix`, `POST /runtime/smoke-reports/validate`, `GET /control-center/status`, `GET /control-center/runtime-readiness/summary`, `GET /control-center/foundation-gate/summary`, `GET /control-center/routes`. | Local model readiness aggregate route, latency report route, storage status route, queue status route, loopback llama.cpp reviewed-settings lifecycle route. | Read-only/validation-only runtime status until a scoped milestone grants exact local lifecycle authority. | `/health`, `/version`, and `/api/manifest` are `none`; runtime and Control Center summary routes are `validation_only`. | No approval for read-only status. Any lifecycle launch/stop must be separately scoped and approved. | Runtime readiness report, capability matrix, Foundation Gate summary, P0-015 checklist evidence refs, performance report refs. | Partial. | Reviewed local llama.cpp lifecycle prerequisite evidence, UAA-P1-013 verification lanes, and UAA-P1-030 route status manifest. |
| Evidence | `/evidence`, `/receipts`, `/events`, `/events/timeline`, `/foundation-gate`, and `/api-routes` show redacted summaries and refs. | `POST /receipts/preview`, `POST /events/validate`, `GET /task-decomposition/audit`, `GET /task-decomposition/metrics`, `GET /observability/session-events`, `POST /observability/client-errors`, `GET /control-center/foundation-gate/summary`, `GET /control-center/routes`. | Release evidence index route, latency report summary route, rollback status route, run receipt trace route backed by durable records. | Evidence is read-only review material; safe refs and redacted summaries only. | Ledger and Control Center evidence routes are `validation_only`; task-decomposition audit/metrics and observability summaries are `local_dev_workspace_only`. | No approval for read-only evidence inspection; mutating evidence generation must follow its owner route. | Receipt previews, event validation results, audit summaries, redacted session summaries, client-error summaries, Foundation Gate summaries, release evidence docs. | Partial. | UAA-P1-010 durable run spine, richer observability dashboard work, and UAA-P1-030 route status manifest. |
| Settings | `/settings` now exposes accessible loading/error/empty/blocked/denied state copy only. Local backend base policy remains code/config only. | No dedicated settings route. Related status comes from `/control-center/status`, `/runtime/readiness`, and `/api/manifest`. | Settings manifest route, loopback auth-token setup/status route, feature-flag route, kill-switch status route, reviewed local llama.cpp settings route. | Settings must remain disabled-by-default, redacted, local-only, revocable, and policy-gated. | `/settings` is local UI state only. Future settings routes must declare `validation_only` or exact scoped `local_dev_workspace_only`. | Exact approval is required for any setting that enables runtime authority, persistence, local lifecycle behavior, or mutation. | None yet beyond status summaries and docs. | Missing. | UAA-P1-030 route status manifest, UAA-P1-014 local runtime packaging, and later scoped settings milestone. |

## Visible Action Map

Current visible actions do not complete the first product loop:

| Visible action | Current behavior | Route authority and side-effect class | Product-readiness result |
|---|---|---|---|
| Navigate/select a card or row | Local UI state only. | No backend route. | Safe for review, not completion evidence. |
| Preview action | Calls `POST /control-center/actions/preview`. | `validation_only`; execution remains denied. | Safe preview only. |
| Approve review-only / Deny review-only on File Review | Updates local component state for review-only display. | No backend route call in CCC Web. | Not product completion evidence; must not be described as a real approval. |
| Load dashboard/runtime/routes summaries | Reads local summary endpoints. | `none` or `validation_only`. | Safe status evidence only. |

No visible CCC action currently sends a chat message, launches llama.cpp,
selects a GGUF model, creates a product Plans loop, executes a capability,
applies a file patch, rolls back a mutation, changes Settings, or grants broad
authority.

## First Product Loop Gaps

The smallest route/product work needed to complete the first operator loop is:

1. Use the UAA-P1-030 route status manifest as release evidence for visible
   action owners, auth posture, side-effect class, risk class, release status,
   OpenAPI operation ids, approval requirements, and evidence refs.
2. Expose runtime health, local model readiness, latency, audit, and rollback
   summaries without raw prompts, raw responses, raw provider payloads, private
   filesystem paths, raw logs, environment dumps, or credential material.
3. Add reviewed GGUF selection/approval/readiness routes using safe refs only.
4. Add reviewed loopback llama.cpp settings and lifecycle status for the
   existing exact-bound local shell scope only.
5. Add a CCC Chat Shell that uses UAA `/v1` with local bearer status, auth
   failure handling, safe failure handling, and visible tools/functions/
   streaming denial.
6. Add a CCC Plans surface over classify, decompose, approval request, grant
   capture, safe registered capability execution, audit, and metrics.
7. Bind one safe registered capability approval to LocalApprovalAuthority and
   show the resulting receipt/audit summary.
8. Add Evidence views for receipt, audit, latency, and rollback refs so the
   operator can verify completion without raw API payloads.

These gaps are release blockers for M172 product-readiness claims.

## Product Language Rules

The canonical enforceable UAA-P1-031 rules live in
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

- No hidden authority: every operator-critical action must show the authority
  boundary, route, side-effect class, approval requirement, and evidence output.
- No fake completion: mock fallback, local component state, preview-only
  decisions, and validation-only responses must never be described as real
  execution, real approval, real model readiness, real persistence, or release
  completion.
- No raw JSON as primary UI for operator-critical flows: raw API payload display
  cannot be the main operator experience for chat, plans, model readiness,
  approvals, file mutation, settings, evidence, latency, or rollback. Human
  summaries, safe refs, statuses, and explicit blockers come first.
- No production/public distribution claims without evidence: release-facing
  copy must keep production and public distribution unclaimed unless an accepted
  packet proves the exact claim.
- No model/provider output as authority: model, provider, OpenWebUI, runtime,
  memory, and preview outputs may inform review but cannot authorize work.
- No completed-state language for blocked/skipped/pending work: blocked,
  skipped, pending, mock-only, local-state-only, and partial states must keep
  that state visible.

## Rollback

This task adds mapping and verifier coverage only. Rollback is to remove this
document, remove its links, remove the verifier/test assertions that require it,
and move `UAA-P0-007` back from Done to Ready Next on the Kanban board. No
runtime state, authority, migration, route, or persistent user data is changed.
