# UAA Runtime Capability Foundation Durable Orchestration

Status: Phase 03 implemented as backend-owned read-model hardening, plus the
first exact approved-runtime-command step bound to the existing approved focused
pytest RuntimeGateway lane.

## Full-Strength Version

UAA should make durable work legible across the whole operator loop: every run
has lifecycle state, current phase, current step, checkpoints, retry/recovery
posture, approval waits, cancellation and dead-letter posture, redacted error
summaries, evidence refs, and proof refs. Future execution capabilities may use
those refs, but only after exact AuthorityLease mode/domain/capability scope,
policy decision, approval binding, receipts, and tests are in place.

## Repo-Safe Version

Phase 03 hardens the existing Run Observability contract:

- Core:
  `src/ultimate_ai_agent/core/execution/run_observability.py`
- Agent Loop posture:
  `GET /control-center/agent-loop/thread#high_maturity_spine_readiness.durable_orchestration_posture`
  / `contract-ref:durable-orchestration-posture:v1`
- API:
  `GET /control-center/runs/observability`
- CLI:
  `python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run-observability`
- Control Center:
  Evidence renders current phase/step, checkpoints, approval wait,
  retry/recovery posture, cancellation/dead-letter posture, and redacted error
  summaries.

All fields are derived from existing append-first durable run state, progress
events, run-attached approvals, coworker metadata, connector delivery metadata,
receipts, and evidence refs. The route remains read-only and safe-ref-only.

The first execution-capable orchestration slice is deliberately narrower than
generic run control: `StagedOrchestrationPlan` may include an
`approved_runtime_command` step only when it carries exact RuntimeGateway
invocation, Action Inbox approval envelope, approval, payload fingerprint,
policy decision, safe-disable, and rollback refs for the promoted
`focused_pytest` command intent. Execution delegates to
`RuntimeGateway.execute_approved_command(...)` and records a redacted runtime
receipt result; the staged orchestration read model still does not execute work
by itself.

## Blocked / Needs Authority

These remain blocked:

- cancel, resume, retry, recovery, or dead-letter execution
- live streaming runtime
- background workers or schedulers
- provider/model calls
- tool execution
- unapproved or unpromoted runtime command steps
- connector writes or sends
- browser automation
- unrestricted shell/subprocess execution
- public release or production authority
- raw prompt, response, provider payload, log, local path, or credential
  persistence

## Exact Promotion Path

Any future run-control capability must add exact AuthorityLease scope, approval
binding, idempotency, receipt/proof refs, rollback or safe-disable posture,
redaction, CLI/API/Core parity, route classification, focused tests, and
Control Center truth labels. Run Observability may display receipts from
AuthorityLease-gated capabilities, but it must not itself execute, resume,
cancel, retry, schedule, stream, or approve work.

## Authority Mission Failure-Management Truth

The newer AuthorityLease mission worker is a separate backend-owned runtime
from this legacy Run Observability projection. Python Core now implements
durable approval waits, exact typed retries for explicitly idempotent adapters,
immutable dead letters, append-first cancellation fences, and API operator
intent for approval decisions and dead-letter recovery. Those capabilities do
not make the existing Control Center Run Observability controls executable.

Approval decisions are durable operator intent, never authority. A resumed
worker must freshly validate exact `LocalApprovalAuthority` scope, policy,
mission lease, budget, kill switch, adapter, target, deadline, idempotency, and
safe-disable posture before execution. The macOS-first Settings surface now
renders the backend-owned AuthorityLease worker projection as read-only safe
refs, durable statuses, blocked reasons, evidence refs, kill-switch posture,
and explicit Linux/Windows render placeholders. Mission mutation controls
remain blocked rather than inferred from either Control Center panel.
