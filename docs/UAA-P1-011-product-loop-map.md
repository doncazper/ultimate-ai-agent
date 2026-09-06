# UAA-P1-011 Product Loop Map

This map focuses only on the first full product loop for UAA-P1-011:
runtime health, local model readiness, chat through UAA `/v1`, task
decomposition, one safe capability approval, receipt/audit logging, latency
inspection, and rollback inspection.

The current implementation is best described as local backend/API backed. The
Control Center exposes read-only inspection panels and a redacted readiness
probe, but it does not grant approvals, execute task plans, manage model
credentials, or become the authority for the loop.

## Request Flow

| Step | Route or surface | Request contract | Response contract | Primary owner | State change |
| --- | --- | --- | --- | --- | --- |
| 1. Runtime health | `GET /health` | none | `HealthResponse` with `status` and `version` | `src/ultimate_ai_agent/api/app.py::get_health` | no |
| 1. Runtime readiness | `GET /runtime/readiness` | none | `ResultEnvelope[RuntimeReadinessReport]` | `app.py::get_runtime_readiness`, `core/runtime_readiness/reports.py::build_readiness_report` | no |
| 1. Capability matrix | `GET /runtime/capability-matrix` | none | `ResultEnvelope[RuntimeCapabilityMatrix]` | `app.py::get_runtime_capability_matrix`, `core/runtime_readiness/matrix.py::build_matrix` | no |
| 2. Local model readiness | `GET /v1/models` | bearer header required when a local gateway is enabled | OpenAI-compatible model list plus `uaa_safety` | `app.py::get_v1_models`; M151/M164 gateway helpers | no |
| 3. Chat through UAA `/v1` | `POST /v1/chat/completions` | `V1ChatCompletionAPIRequest`; no streaming/tools/functions | OpenAI-compatible chat completion plus `uaa_safety` receipt | `app.py::post_v1_chat_completions`; M151 or M164 response builders | no durable task state |
| 4. Task plan | `POST /task-decomposition/decompose` | `TaskDecompositionRequest` with local bearer | `TaskDecompositionRunResult` with `TaskPlan`, `PlanValidationResult`, `TaskDecompositionDurableBinding` | `TaskDecompositionService.decompose` | yes |
| 5. Approval request | `POST /task-decomposition/approval-requests` | `TaskCapabilityApprovalRequestPayload` | `ApprovalRequest` | `TaskDecompositionService.build_approval_request` | yes |
| 5. Approval grant | `POST /task-decomposition/approvals/grants/capture` | `TaskDecompositionApprovalGrantRequest` | `ApprovalGrant` | `TaskDecompositionService.grant_approval`, `LocalApprovalAuthority.grant` | yes |
| 5. Approved safe execution | `POST /task-decomposition/plans/execute` | `TaskPlanExecutionRequest` | `DAGExecutionResult` with durable binding | `TaskDecompositionService.execute_plan`, `DAGExecutor.execute` | yes |
| 6. Audit inspection | `GET /task-decomposition/audit` | optional `limit`, local bearer | bounded audit event list | `TaskDecompositionService.audit_events` | no |
| 7. Latency inspection | `GET /task-decomposition/metrics` | local bearer | capability outcome metrics and reflection summaries | `TaskDecompositionService.metrics`, `CapabilityRegistry.metrics` | no |
| 8. Rollback inspection | returned in `durable_binding.rollback_refs`; partly visible through audit receipts | no dedicated rollback route | safe rollback refs and receipt summaries | `TaskDecompositionDurableBinding`, `AppendFirstRunStorage` | no |

The executable test spine is `tests/test_operator_loop_p1_011.py`. It exercises
`/health`, `/runtime/readiness`, `/control-center/dashboard`, `/v1/models`,
`/v1/chat/completions`, task decomposition example init, plan decomposition,
capability registration, approval request/grant capture, approved plan
execution, audit inspection, and metrics inspection.

## Key Files

| Area | Files |
| --- | --- |
| API routes | `src/ultimate_ai_agent/api/app.py` |
| API route manifest and safety flags | `src/ultimate_ai_agent/api/manifest.py` |
| Runtime readiness | `src/ultimate_ai_agent/core/runtime_readiness/reports.py`, `src/ultimate_ai_agent/core/runtime_readiness/matrix.py` |
| M151 local OpenWebUI test gateway | `src/ultimate_ai_agent/core/openwebui_bridge/local_test_shell.py` |
| M164 llama.cpp loopback gateway | `src/ultimate_ai_agent/core/local_model_management/gateway.py` |
| Task decomposition service | `src/ultimate_ai_agent/core/task_decomposition/runtime.py` |
| Task contracts | `src/ultimate_ai_agent/core/task_decomposition/contracts.py` |
| Plan execution | `src/ultimate_ai_agent/core/task_decomposition/executor.py` |
| Capability registry and latency metrics | `src/ultimate_ai_agent/core/task_decomposition/registry.py` |
| Approval authority | `src/ultimate_ai_agent/core/approvals/authority.py`, `src/ultimate_ai_agent/core/approvals/requests.py`, `src/ultimate_ai_agent/core/approvals/grants.py`, `src/ultimate_ai_agent/core/approvals/decisions.py` |
| Durable run state and receipt storage | `src/ultimate_ai_agent/core/execution/durable_runs.py`, `src/ultimate_ai_agent/core/execution/run_storage.py` |
| API/session observability | `src/ultimate_ai_agent/api/app.py`, `src/ultimate_ai_agent/core/observability` |
| Control Center data loading | `apps/control-center/src/api/client.ts`, `apps/control-center/src/api/endpoints.ts` |
| Control Center loop UI | `apps/control-center/src/components/OperatorLoopPanel.tsx`, `apps/control-center/src/components/OperatorFlowPanels.tsx`, `apps/control-center/src/routes.tsx` |
| Focused coverage | `tests/test_operator_loop_p1_011.py`, `tests/test_task_decomposition_production_api.py`, `tests/test_task_decomposition_live_local.py` |

## Key Functions, Classes, and Components

### Runtime and Readiness

- `app.py::get_health` returns the shallow local API health response.
- `app.py::get_runtime_readiness` wraps `build_readiness_report()` in a
  `ResultEnvelope`.
- `app.py::get_runtime_capability_matrix` wraps `build_matrix()` in a
  `ResultEnvelope`.
- `RuntimeReadinessReport` reports readiness posture without claiming production
  readiness or model-output authority.
- `RuntimeCapabilityMatrix` lists supported, simulated-only, manual-only,
  dry-run-only, planned-disabled, and blocked runtime surfaces.

### UAA `/v1` Model and Chat Routes

- `app.py::get_v1_models` selects M164 llama.cpp gateway when
  `UAA_LLAMA_CPP_GATEWAY_ENABLED` is enabled; otherwise it falls back to the
  M151 local OpenWebUI test gateway.
- `app.py::post_v1_chat_completions` validates `V1ChatCompletionAPIRequest`,
  routes to M164 or M151, and denies unsafe shape through the gateway contracts.
- `OpenWebUILocalChatCompletionRequest` denies streaming, tools, function calls,
  and non-test model IDs for the M151 deterministic local test gateway.
- `OpenWebUILocalGatewayReceipt` records that no provider calls, tools, memory
  writes, context injection, external network calls, raw prompt logging, or
  production authority occurred.
- `M164ChatCompletionRequest` denies streaming, tools, and functions for the
  llama.cpp loopback route.
- `M164GatewayReceipt` records loopback forwarding and safety flags for the
  M164 local gateway.

### Task Decomposition and Approval

- `TaskDecompositionService.from_env` builds the default service with
  `UAA_TASK_DECOMPOSITION_REGISTRY` or `.uaa/task_decomposition_registry.json`.
- `TaskDecompositionService.decompose` classifies, selects capabilities,
  creates a `TaskPlan`, validates it, creates or transitions a durable run, and
  records a `plan_decomposed` audit event.
- `TaskDecompositionService.build_approval_request` creates an
  `ApprovalRequest`, persists approval state, attaches approval request refs to
  the durable run, and records an `approval_requested` audit event.
- `TaskDecompositionService.grant_approval` delegates to
  `LocalApprovalAuthority.grant`, persists approval state, attaches approval refs
  to the durable run, and records an `approval_granted` audit event.
- `TaskDecompositionService.execute_plan` validates idempotency, prepares the
  durable run, records a redacted session event for execution start, runs
  `DAGExecutor.execute`, finishes the durable run, records node session events,
  and records a `plan_executed` audit event.
- `DAGExecutor.execute` evaluates dependencies, approval availability, capability
  validation, retry behavior, and node status.
- `CapabilityRegistry.validate_call` checks capability registration, allowed
  execution modes, risk ceilings, required permissions, approval refs, data
  sensitivity, and input schema.
- `CapabilityRegistry.invoke` measures handler latency and records capability
  outcomes.
- `LocalApprovalAuthority.validate` checks grant existence, revocation, expiry,
  run, subject, actor, action, resource refs, risk, and data classification.

### Control Center

- `build_control_center_dashboard` includes `operator_loop_summary` and
  provider credential readiness in the dashboard snapshot.
- `build_operator_loop_summary` maps the UAA-P1-011 loop to six UI summary
  steps: runtime health, local model readiness, chat, plan, approval, and
  receipt/audit/latency/rollback.
- `OperatorLoopPanel` renders the route/evidence/authority summary and keeps
  frontend authority disabled.
- `ChatOperatorPanel` calls `inspectLocalModelsRoute()` and can call
  `requestRedactedLocalChatProbe()` only after model readiness appears ready.
- `ModelsOperatorPanel`, `PlansOperatorPanel`, `EvidenceOperatorPanel`, and
  `SettingsOperatorPanel` expose inspection states, route refs, and blocked
  authority boundaries.

## Input and Output Contracts

| Contract | Direction | Purpose |
| --- | --- | --- |
| `HealthResponse` | output | shallow API liveness and version |
| `RuntimeReadinessReport` | output | readiness posture, guardrails, capability matrix ref |
| `RuntimeCapabilityMatrix` | output | capability surface status and blocked actions |
| `V1ChatCompletionAPIRequest` | input | OpenAI-compatible chat shape at UAA `/v1` |
| `OpenWebUILocalChatCompletionRequest` | input | M151 deterministic local test gateway request |
| `OpenWebUILocalGatewayReceipt` | output | M151 no-authority chat receipt flags |
| `M164ChatCompletionRequest` | input | M164 llama.cpp loopback request |
| `M164GatewayReceipt` | output | M164 loopback safety receipt flags |
| `TaskDecompositionRequest` | input | raw task request, context, idempotency key |
| `TaskPlan` and `TaskNode` | input/output | structured plan and selected capability graph |
| `PlanValidationResult` | output | valid/blocked status and approval-required nodes |
| `CapabilityContract` | input | registered capability card, schemas, permissions, handler ref |
| `TaskCapabilityApprovalRequestPayload` | input | capability ID, run ID, actor ID |
| `ApprovalRequest` | output | exact approval request for one capability |
| `TaskDecompositionApprovalGrantRequest` | input | approval request ID, approving actor, expiry/scope |
| `ApprovalGrant` | output | exact scoped approval ref |
| `CapabilityCallContext` | input | actor, risk/data ceilings, approval refs, dry-run flag |
| `TaskPlanExecutionRequest` | input | plan, call context, idempotency, reflection persistence |
| `DAGExecutionResult` | output | node records, status, outputs, durable binding |
| `TaskDecompositionDurableBinding` | output | safe refs for durable run, audit, receipt, replay, rollback, approval, handler, restart |
| `TaskDecompositionAuditEvent` | output | append-only-ish audit document event record |
| `CapabilityOutcomeMetrics` | output | total/success/failure counts and average latency |

## Where State Changes Happen

- Capability registry persistence:
  `CapabilityRegistryStore.save()` writes `.uaa/task_decomposition_registry.json`
  by default. Registration can be non-persistent with `persist: false`.
- Approval state:
  `TaskDecompositionService._approval_requests` and
  `LocalApprovalAuthority._grants` hold in-process state, while
  `CapabilityRegistryStore.save_approval_state()` writes
  `.uaa/task_decomposition_registry.approvals.json` by default.
- Audit state:
  `CapabilityRegistryStore.append_audit_event()` writes
  `.uaa/task_decomposition_registry.audit.json` by default.
- Durable run state:
  `AppendFirstRunStorage` writes `.uaa/task_decomposition_registry.runs.jsonl`
  by default.
- Reflection/metrics state:
  `ReflectionStore` records execution reflections in memory for the current
  service instance. `CapabilityRegistry` stores outcome records in memory and
  exposes aggregate metrics. Capability latency is therefore not durable unless
  another layer records a separate session event or receipt summary.
- API/session observability:
  `session_log_api_middleware` records redacted request lifecycle events through
  `record_session_event`; these are inspectable through
  `GET /observability/session-events`.

## Where Audit and Receipt Events Are Created

- API request lifecycle events:
  `app.py::session_log_api_middleware` measures each request and calls
  `_record_api_session_event`, which records route pattern, method, status code,
  duration, and redaction metadata without body/header/query values.
- Task audit events:
  `TaskDecompositionService.record_audit_event()` is called by registration,
  example init, classify, decompose, plan validation, approval request, approval
  grant, approval revoke, and plan execution.
- Durable receipt refs:
  `_ensure_durable_run`, `_transition_durable_run`, and
  `_append_durable_attachment` create safe `receipt:*`, `audit:*`, `replay:*`,
  `rollback:*`, and `evidence:*` refs.
- Receipt summaries:
  `_append_durable_snapshot()` calls
  `AppendFirstRunStorage.append_receipt_summary()` with a redacted receipt
  summary containing run ID, state, audit ref, receipt ref, replay ref,
  rollback ref, safe summary, `no_runtime_authority`, and `safe_ref_only`.
- Chat safety receipts:
  M151 and M164 chat responses include `uaa_safety` receipt objects, but those
  are response-local safety metadata and are not currently appended into the
  task-decomposition durable run.

## Where Latency Is Measured

- API request latency:
  `session_log_api_middleware` uses `time.perf_counter()` and records
  `duration_ms` in a redacted session event.
- Capability invocation latency:
  `CapabilityRegistry.invoke()` uses `time.perf_counter()` around the handler
  call and records a `CapabilityOutcomeRecord.latency_ms`.
- Metrics inspection:
  `TaskDecompositionService.metrics()` exposes `CapabilityOutcomeMetrics`,
  including `average_latency_ms`, through `GET /task-decomposition/metrics`.
- Control Center chat readiness latency:
  `requestRedactedLocalChatProbe()` measures frontend fetch duration with
  `performance.now()` or `Date.now()` and stores it in
  `RedactedLocalChatProbeStatus.durationMs`.
- Node execution timing:
  `DAGExecutor._run_node()` records `started_at` and `completed_at` on
  `NodeExecutionRecord`, but it does not currently expose a normalized per-node
  duration field.

## Where Rollback Information Is Recorded or Inspected

- Durable transition requests include `rollback_ref`.
- `DurableRunRecord.rollback_refs` accumulates rollback refs as state changes or
  attachments are recorded.
- `TaskDecompositionDurableBinding.rollback_refs` returns rollback refs from
  plan decomposition and execution responses.
- `TaskDecompositionAuditEvent.rollback_ref` records the latest rollback ref for
  major audit events.
- `AppendFirstRunStorage.append_run_record()` and `append_receipt_summary()`
  both store the rollback ref with each append-first storage entry.
- There is no dedicated UAA-P1-011 rollback inspection endpoint yet. Operators
  inspect rollback refs indirectly through `durable_binding`, task audit events,
  receipt summaries, or future storage inspection utilities.
- `TaskDecompositionService.validate_replay()` and
  `AppendFirstRunStorage.validate_receipt_replay()` can validate replay/receipt
  integrity internally, but the task decomposition API does not currently expose
  a read-only replay validation route for UAA-P1-011.

## Gaps or Unclear Boundaries

- Control Center model/chat calls do not currently provide a local bearer. When
  `/v1` gateways are correctly bearer-gated, the browser inspection path can
  report denied/blocked states, but the full happy path remains API/test/CLI
  driven.
- Control Center plan and approval panels are inspection-only. They list task
  decomposition routes and authority boundaries but do not submit task text,
  create approval requests, capture approval grants, or execute plans.
- `/health` is shallow liveness only. Runtime readiness and capability posture
  are separate routes, so product readiness should not be inferred from
  `/health`.
- M151 `/v1` chat is deterministic test-gateway behavior. M164 is the real
  loopback path, but it still remains local, bearer-gated, allowlisted, and
  non-authoritative.
- Chat safety receipts are not joined to task-decomposition durable receipt
  storage. The chat route emits `uaa_safety` in the response and API session
  events via middleware, while task execution emits durable receipt refs.
- Latency has multiple homes: API session events, frontend chat probe state,
  capability outcome metrics, and node timestamps. There is no single
  UAA-P1-011 loop latency summary contract.
- Capability latency metrics are in memory on `CapabilityRegistry`; they are
  inspectable through `/task-decomposition/metrics` during the service lifetime
  but are not append-first durable state.
- Rollback is safe-ref based and recorded in durable bindings/storage, but there
  is no dedicated rollback inspection view or endpoint for one run.
- Receipt summaries and replay validation exist in durable storage, but
  `/task-decomposition/audit` and `/task-decomposition/metrics` do not expose
  `AppendFirstRunStorage.list_receipt_summaries()` or
  `validate_receipt_replay()`.
- Approval state is split between `LocalApprovalAuthority` in memory and the
  task decomposition approval-state file. The service reload path is responsible
  for reconciling persisted approvals into the authority.
- Approval-state persistence is JSON rewrite based, unlike the append-first,
  hash-linked durable run storage.
- Approval grant/revoke mutation responses return grant payloads directly; the
  read inspection routes apply stronger safe-read projection with
  `redact_read_refs=True`.
- The Control Center dashboard summary is derived from environment/configuration
  posture. It does not inspect live `TaskDecompositionService.audit_events()` or
  `TaskDecompositionService.metrics()`.
- `TaskDecompositionService` currently owns API-adjacent orchestration,
  persistence, approval binding, audit writing, durable state transitions,
  receipt summaries, metrics, and execution. That makes the loop inspectable but
  harder to test or roll back in isolated slices.

## Safest Extraction Candidates

These are documentation-level extraction candidates only; no source refactor is
recommended before the UAA-P1-011 loop contract is accepted.

| Candidate | Current owner | Suggested module | Why it is safe |
| --- | --- | --- | --- |
| Product loop route map | `build_operator_loop_summary` plus docs/tests | `core/operator_loop/product_loop.py` | Pure summary logic; can stay read-only and backend-authority-only |
| Task durable binding helpers | `TaskDecompositionService` private methods | `core/task_decomposition/durable_binding.py` | Mostly safe-ref construction and durable storage attachment |
| Task audit writer | `TaskDecompositionService.record_audit_event` and store calls | `core/task_decomposition/audit.py` | Isolates append/write policy without changing route behavior |
| Task approval adapter | `build_approval_request`, `grant_approval`, `revoke_approval` | `core/task_decomposition/approval_flow.py` | Keeps LocalApprovalAuthority boundary explicit |
| UAA `/v1` gateway selection | `app.py::get_v1_models`, `post_v1_chat_completions` | `api/v1_gateway.py` | Narrows route handlers while preserving existing M151/M164 contracts |
| Read-only loop evidence facade | `audit_events`, `metrics`, `durable_binding`, `validate_replay` | new safe-ref-only projection module | Would centralize inspection without adding mutation or rollback execution |
| Approval persistence adapter | `_load_persisted_approval_state`, `_save_persisted_approval_state` | `core/task_decomposition/approval_persistence.py` | Lets approval durability be tested independently from grant policy |
| Metrics snapshot DTO | `CapabilityRegistry.metrics`, `ReflectionStore` | new read-only metrics projection | Makes latency inspection explicit before making it durable |
| Loop latency summary | API middleware, capability metrics, frontend probe | new contract before code extraction | Needs a contract first because latency is currently distributed |
| Rollback inspection projection | durable binding plus storage entries | new read-only projection contract | Should remain safe-ref-only and not execute rollback |

## Validation Anchors

- Focused full-loop test: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operator_loop_p1_011.py -q`
- Related API route tests: `tests/test_task_decomposition_production_api.py`,
  `tests/test_local_loopback_api_routes.py`,
  `tests/test_runtime_readiness_api_routes.py`,
  `tests/test_control_center_api_routes.py`
- Frontend safety verifier:
  `PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py`
- Foundation/UAA safety guard:
  `.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only`
