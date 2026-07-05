# UAA GoatCitadel Runtime Staged Orchestration Engine

Status: implemented as Phase 04 of the UAA GoatCitadel runtime parity pack.

This lane adapts GoatCitadel's staged orchestration shape into a UAA-native
Python Agent Core read model. It does not copy GoatCitadel code or import
GoatCitadel packages. It does not add runtime authority.

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
refs, and effectful modes remain blocked.

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

## Boundaries Preserved

Control Center cannot mint authority. This lane is a backend-owned read model
and validation surface only. It adds no autonomous worker, hidden model call,
unrestricted command execution, browser automation, connector write,
production authority, or raw payload persistence.

All durable output uses safe refs, redacted summaries, bounded status fields,
checkpoint refs, receipt refs, evidence refs, rollback refs, and blocked
authority refs.

## Promotion Path

Future execution-capable orchestration requires a separate exact lane for each
step class, including approval binding, idempotency, audit receipt, rollback or
safe-disable posture, redaction, route side-effect classification, CLI/API/Core
parity, and focused verifier coverage.
