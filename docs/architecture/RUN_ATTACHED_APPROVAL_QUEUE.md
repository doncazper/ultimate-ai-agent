# Run-Attached Approval Queue

Status: implemented as a read-only contract/read-model foundation.

This lane makes approval request, grant, denial, expiry, revocation, and scope
mismatch posture inspectable through durable run state. It does not grant new
approval authority, execution authority, provider/model calls, connector writes,
background workers, schedulers, browser/web/shell execution, billing authority,
public beta claims, or production authority.

## Contract

The Python Agent Core owns the queue in
`src/ultimate_ai_agent/core/execution/approval_queue.py`.

The read model exposes:

- `RunAttachedApprovalQueueReadModel`
- `RunAttachedApprovalQueueItemReadModel`
- `RunAttachedApprovalQueueSummaryReadModel`
- `RunAttachedApprovalRunBucketReadModel`

Supported approval states are:

- `requested`
- `approved`
- `denied`
- `expired`
- `revoked`
- `scope_mismatch_blocked`
- `blocked`

Supported durable run event names are:

- `approval_required`
- `approval_attached`
- `approval_denied`
- `approval_expired`
- `approval_revoked`
- `approval_scope_mismatch_blocked`

Approval refs are identifiers only. They do not authorize execution unless a
later exact `LocalApprovalAuthority` scope validates inside a separately scoped
mutation lane.

## Inspection Surfaces

Read-only API routes:

- `GET /control-center/approvals/queue`
- `GET /task-decomposition/runs/{run_id}/approvals`

CLI inspection:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-approvals
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-approvals task-decomposition-run:example
```

The Control Center `/approvals` route displays the backend-owned queue first and
keeps legacy preview approval cards clearly labeled as mock/non-authoritative.

## Non-Goals

- No approve/deny/revoke UI controls.
- No POST attach route.
- No run resume/start/cancel behavior.
- No provider/model calls.
- No tool execution expansion.
- No connector writes.
- No scheduler or background worker.
- No raw payload persistence.

## Promotion Blockers

Future approval mutation work must prove:

- exact `LocalApprovalAuthority` scope validation;
- idempotent receipt mutation;
- route side-effect classification as mutating authority;
- CLI parity;
- redacted Evidence Timeline refs;
- replay/audit posture;
- expiry and revocation handling;
- frontend tests proving mock/degraded data cannot expose controls.
