# UAA GoatCitadel Runtime Staged Orchestration Engine

Status: implemented as Phase 04 of the UAA GoatCitadel runtime parity pack.

This lane adapts GoatCitadel's staged orchestration shape into a UAA-native
Python Agent Core orchestration contract. It does not copy GoatCitadel code or
import GoatCitadel packages. The base read model remains non-mutating, and the
first execution-capable slice is limited to one approved-runtime-command step
that can consume existing exact Action Inbox approved RuntimeGateway utility
command lanes: `focused_pytest`, `repo_verifier`, `frontend_check`, and
`repo_doctor`.

## Implemented Repo-Safe Slice

Python Agent Core owns `StagedOrchestrationReadModel` and related contracts for:

- orchestration plan
- stage
- step
- dependency
- deterministic no-effect callback ref
- checkpoint
- degraded handoff
- blocked authority
- approved runtime command binding/result refs for the exact promoted utility
  command lanes: `focused_pytest`, `repo_verifier`, `frontend_check`, and
  `repo_doctor`

The staged progress statuses are:

- `pending`
- `running`
- `waiting`
- `degraded`
- `skipped`
- `blocked`
- `failed`
- `completed`

Dependency validation rejects missing dependencies, cycles, same-stage
dependencies, future-stage dependencies, degraded steps without handoff refs,
and downstream work that is not skipped, blocked, or degraded after a failed or
blocked dependency. Execution-ready steps require policy and approval posture
refs. Effectful modes remain blocked except the exact
`approved_runtime_command` mode, which requires a runtime invocation ref, Action
Inbox approval envelope ref, exact scope ref, expected payload fingerprint ref,
expected policy decision ref, safe-disable ref, rollback ref, and the promoted
`focused_pytest`, `repo_verifier`, `frontend_check`, or `repo_doctor` command
intent.

Checkpoint replay is safe-ref and fingerprint based. Replays are inspectable as
idempotent matches or conflicts; replay does not perform execution.

The CLI inspection path is:

```bash
.venv/bin/python scripts/dev/uaa_runtime.py inspect-staged-orchestration --json
```

The API inspection path is:

```text
GET /api/runtime/staged-orchestration
```

## Approved Runtime Command Step

`execute_approved_runtime_command_step(...)` runs only after
`validate_staged_orchestration_plan(...)` accepts a plan with
`approved_runtime_command_execution_enabled=True`. It then delegates execution to
`RuntimeGateway.execute_approved_command(...)`, so the same idempotency,
approval binding, allowlist, redaction, receipt, and safe-disable rules apply.

The result contract records step/ref status, command intent, receipt ref,
evidence refs, redacted output-summary availability, replay posture, and whether
RuntimeGateway performed command execution. It does not persist raw command
output or raw payloads and does not enable unrestricted command execution.

## Boundaries Preserved

Control Center cannot mint authority. The read model remains inspection-only.
The execution-capable path is backend-owned, exact-scope, approval-bound, and
limited to the existing promoted focused pytest, repo-verifier, frontend-check,
and repo-doctor RuntimeGateway lanes. It does not add runtime authority outside
exact approved utility lanes, and it adds no autonomous worker, hidden model call,
unrestricted command execution, browser automation, connector write,
production authority, or raw payload persistence.
This does not add runtime authority beyond exact approved utility lanes;
browser automation remains blocked.

All durable output uses safe refs, redacted summaries, bounded status fields,
checkpoint refs, receipt refs, evidence refs, rollback refs, and blocked
authority refs.

## Promotion Path

Future execution-capable orchestration still requires a separate exact lane for
each additional step class, including approval binding, idempotency, audit
receipt, rollback or safe-disable posture, redaction, route side-effect
classification, CLI/API/Core parity, and focused verifier coverage.
