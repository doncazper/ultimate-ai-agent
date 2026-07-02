# Durable Run Lifecycle Event Log

Status: active foundation for read-only durable run lifecycle inspection

This document defines the current durable run lifecycle and event-log
foundation. It is backend/core-owned state visibility only. It does not add a
scheduler, background worker, provider/model runtime, tool dispatch, connector
delivery, streaming provider runtime, public beta, production authority, or
broad autonomy.

`running` is a recorded lifecycle state, not proof that work is executing.
Approval refs, receipt refs, replay refs, durable records, and event refs are
evidence only. They do not authorize work without a later exact approval-bound
runtime lane.

## Scope

This foundation adds:

- canonical lifecycle vocabulary for future run inspection surfaces
- a read-only lifecycle projection over existing append-first durable run
  storage
- ordered event summaries derived from durable run records and receipt-summary
  entries
- safe run, receipt, replay, rollback, audit, evidence, cost-posture, redaction,
  and authority-boundary refs
- idempotency-ref visibility without treating idempotency as exactly-once
  execution
- a protected local read API for task-decomposition durable run lifecycle
  inspection
- repo-local CLI inspection parity for the same backend-owned state

The implementation reuses
`src/ultimate_ai_agent/core/execution/durable_runs.py` and
`src/ultimate_ai_agent/core/execution/run_storage.py`. It does not introduce a
parallel event ledger or a competing run-truth source.

## Canonical States

The canonical read-model states are:

- `created`
- `queued`
- `waiting_for_approval`
- `ready`
- `running`
- `paused`
- `cancel_requested`
- `canceled`
- `failed`
- `succeeded`
- `expired`
- `blocked`
- `replaying`

Existing durable-run storage states are mapped into this vocabulary for
inspection. For example, `retry_pending` is shown as `queued`, `cancelled` is
shown as `canceled`, and `dead_lettered` is shown as `failed` with safe refs
left available for review.

## Canonical Event Types

The canonical event types are:

- `run_created`
- `run_queued`
- `approval_required`
- `approval_attached`
- `approval_denied`
- `step_started`
- `step_progress`
- `step_blocked`
- `step_completed`
- `receipt_recorded`
- `evidence_ref_attached`
- `cost_posture_recorded`
- `redaction_applied`
- `pause_requested`
- `resume_requested`
- `cancel_requested`
- `run_canceled`
- `run_failed`
- `run_succeeded`
- `run_expired`
- `replay_started`
- `replay_event_emitted`
- `replay_completed`

The current projection derives event summaries from durable storage entries. It
does not claim that every future event type is emitted by current runtime
surfaces.

## Storage Guarantees

The read model is backed by the existing append-first durable run storage:

- entries are ordered by durable run ref and per-run sequence
- duplicate per-run idempotency keys are denied by storage
- entry hash refs and previous-entry hash refs preserve tamper-detection
  posture
- receipt summaries are hashed as redacted safe-ref summaries only
- replay validation refs are inspection refs only
- raw prompt, response, provider payload, tool payload, local path, log,
  environment, credential, username, hostname, and secret-like values are not
  part of the read model

Timestamp capture is intentionally not claimed in this foundation. The read
model reports timestamp recording as a planned storage extension until a later
scoped migration adds it.

## API And CLI Surfaces

The current API surface is:

- `GET /task-decomposition/runs/{run_id}/lifecycle`

The route is protected by the existing task-decomposition local authority gate,
uses the local task-decomposition rate-limit group, returns a `ResultEnvelope`,
and exposes safe refs plus bounded lifecycle event summaries only.

The repo-local CLI surface is:

- `python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run RUN_ID`

The CLI reads the same backend-owned durable storage and emits safe refs only.
It does not create, resume, cancel, replay, schedule, or execute a run.

## Blocked And Planned Authority

The following remain blocked until later accepted scoped milestones define exact
authority, approval, idempotency, receipt, audit, replay, and safe-disable
posture:

- background execution
- scheduler registration
- cancel/resume mutation controls
- streaming provider runtime
- provider/model calls
- A2A, MCP, or browser runtime dispatch
- connector writes
- CRM writes, email/calendar sends, account sync, or live source ingestion
- shell or subprocess execution
- public beta, public release, production readiness, or broad autonomy claims

## Future Promotion Gates

Before this foundation can support callable runtime work, a later milestone must
prove:

- exact approval binding to the run, task, handoff, and expiry
- mutation routes with idempotency, audit, receipt, rollback, and route
  classification coverage
- queue inspection before work starts
- safe cancel and revocation posture
- replay/audit evidence that does not expose raw payloads
- red-team checks for hidden prompt or payload injection
- UI/CLI parity for blocked, approved, cost-blocked, failed, canceled, and
  succeeded states
- safe-disable and rollback posture

## Verification

Focused verification for this foundation includes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_durable_run_lifecycle_read_model.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_task_decomposition_production_api.py tests/test_task_decomposition_live_local.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
