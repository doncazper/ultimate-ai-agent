# FCC-ACTION-001 Approval-Bound Local Authority Capability

Status: Implemented for the existing `local_task_create` AuthorityLease-gated
local capability; blocked for any additional Action Inbox execution capability
until a separate exact scoped mode/domain/lease gate is accepted.
Baseline: v0.104.0 / 0.104.0.
Primary surface: `/actions`.

## Current Truth

`local_task_create` is the only current rank 5 Action Inbox local write
authority capability in the operational maturity manifest. It requires active
`workspace/write` AuthorityLease scope plus exact approval before it can commit
one approved Action Inbox item into local task state through:

```text
POST /control-center/actions/{action_id}/local-task/commit
scripts/dev/uaa_founder_loop.py commit-local-task
```

The capability is exact-scoped, approval-bound, idempotent, receipt-backed,
evidence-backed, redaction-bound, audit-bound, and safe-disable aware. It records
`receipt:founder-loop-local-task:*` receipts and
`evidence-event-type:local_task_created` history. It keeps
`rollback_execution` blocked; rollback posture is represented by
`rollback-not-applicable:local-task-safe-disable` and
`safe-disable:founder-loop:local-task-create-scorecard`.

## Repeatability Gate

The active repeatability gate is `FCC-ACTION-002`. It proves that the Control
Center does not mint local task authority in React state, that mock/degraded
data cannot expose committed state, and that the UI refreshes from the
backend-owned read model before treating a local task as committed.

The current rank stays honest:

- Action Inbox module: rank 3 overall.
- `local_task_create` authority capability: rank 5 local write authority with
  active `workspace/write` lease, exact approval, receipt, and evidence.
- All other Action Inbox capabilities: proposal, decision receipt, or blocked
  posture only.

## Safety Boundary

This capability adds no generic action execution, no connector writes, no
shell/subprocess execution, no browser automation, no provider/model authority,
no memory writes, no context injection, no external side effects, no rollback
execution, no public beta, no public distribution, no production-readiness
claim, and no production authority.

Future local follow-up completion, opportunity update, connector write, memory
write, shell, or rollback capabilities must define their own authority domain,
capability, required mode, lease scope, exact approval, receipt, evidence,
idempotency, redaction, safe-disable, CLI/API/core parity, and verifier gates.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_action_001_approval_bound_local_micro_lanes.py -q
.venv/bin/python scripts/verify_fcc_action_001_approval_bound_local_micro_lanes.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py tests/test_founder_loop_storage_actions.py tests/test_control_center_api_routes.py tests/test_fcc_v1_003_founder_loop_vertical_slice.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```
