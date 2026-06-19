# Durable Run Spine

Status: active UAA-P1-010 contract with UAA-P1-025 storage, UAA-P1-026 lifecycle contracts, UAA-P1-027 task decomposition binding, UAA-P1-028 offline restore planning, and UAA-P1-029 replay-safe receipt hashing

The durable run spine defines the minimum run-truth contract for local operator
work. It is a state and evidence model only. It does not add execution,
scheduling, background work, shell or subprocess behavior, network or browser
automation, connector writes, plugin runtime import, model/provider authority,
or public distribution.

## Scope

UAA-P1-010 adds:

- durable run records with schema version, generation, state, source ref, and
  safe summary
- explicit run states and transition rules
- transition requests bound to transition id, idempotency key, actor ref, audit
  ref, receipt ref, replay ref, rollback ref, and safe evidence refs
- denied transitions for invalid state moves, duplicate transition ids,
  duplicate idempotency keys, reused replay refs, terminal states, and
  unapproved authority flags
- restart recovery as a visible state with restart refs
- checksum-backed snapshot and restore validation for corruption detection

UAA-P1-025 adds append-first local storage for durable run records and receipt
summaries in `docs/execution/APPEND_FIRST_RUN_STORAGE.md` and
`src/ultimate_ai_agent/core/execution/run_storage.py`.

UAA-P1-026 adds state-only lifecycle contracts for pause, resume, cancel,
retry, dead-letter, and restart recovery. Exact repeated lifecycle requests
return an idempotent no-op replay decision; conflicting reused idempotency keys
are denied.

UAA-P1-027 binds task decomposition plan and run results to durable run records.
The binding adds safe refs for durable run state, approval evidence, registered
handler refs, receipt summaries, replay validation, restart visibility, and
explicit idempotency replay denial. It does not turn a plan, model output,
approval ref, replay ref, receipt ref, or durable record into runtime authority.

UAA-P1-028 defines the backup minimum set, verification process, and
offline/operator-run restore plan in
`docs/execution/DURABLE_RUN_BACKUP_RESTORE.md`. Live restore, backup rotation,
and automatic restoration remain scoped to later P1 items.

UAA-P1-029 adds replay-safe receipt hashing for mutating local paths in
`src/ultimate_ai_agent/core/execution/run_storage.py`. Receipt hashes are stable
over redacted receipt-summary data only, stored as safe hash refs, and bound to
replay validation refs. Receipt summaries with private-data-shaped keys are
denied before persistence.

## States

| State | Meaning | Terminal |
|---|---|---|
| `created` | Run record exists but is not ready. | no |
| `ready` | Run is validated enough to start the local operator loop. | no |
| `running` | Run is active as a state record. This is not execution authority. | no |
| `paused` | Operator or policy paused the run. | no |
| `blocked` | Run needs review, missing evidence, or a scoped blocker resolution. | no |
| `retry_pending` | A retry is approved as a future state transition only. | no |
| `restart_recovery` | Restart was observed and recovery truth is visible. | no |
| `failed` | Run failed but may be retried, cancelled, or dead-lettered. | no |
| `succeeded` | Run reached successful terminal state. | yes |
| `cancelled` | Run was cancelled and cannot advance. | yes |
| `dead_lettered` | Run was moved out of normal processing for manual review. | yes |

## Transition Rules

| From | Allowed next states |
|---|---|
| `created` | `ready`, `failed`, `cancelled` |
| `ready` | `running`, `failed`, `cancelled` |
| `running` | `paused`, `blocked`, `restart_recovery`, `succeeded`, `failed`, `cancelled` |
| `paused` | `running`, `failed`, `cancelled` |
| `blocked` | `retry_pending`, `failed`, `cancelled`, `dead_lettered` |
| `retry_pending` | `running`, `cancelled`, `dead_lettered` |
| `restart_recovery` | `running`, `failed`, `cancelled`, `dead_lettered` |
| `failed` | `retry_pending`, `cancelled`, `dead_lettered` |
| `succeeded`, `cancelled`, `dead_lettered` | none |

Each accepted transition increments the run generation and records transition,
idempotency, audit, receipt, replay, rollback, evidence, failure, and restart
refs as applicable. Repeating a prior non-lifecycle idempotency key or replay
ref is denied.

## Lifecycle Contracts

Lifecycle actions are exact state-only transitions:

| Action | Allowed from | Result |
|---|---|---|
| pause | `running` | `paused` |
| resume | `paused`, `retry_pending`, `restart_recovery` | `running` |
| cancel | `created`, `ready`, `running`, `paused`, `blocked`, `retry_pending`, `restart_recovery`, `failed` | `cancelled` |
| retry | `blocked`, `failed` | `retry_pending` |
| dead-letter | `blocked`, `retry_pending`, `restart_recovery`, `failed` | `dead_lettered` |
| restart recovery | `running` | `restart_recovery` |

Every lifecycle request requires idempotency, audit, receipt, replay, rollback,
and authority-boundary refs. Stale expected-state requests are denied.
Dead-letter requires a failure ref so the terminal state remains inspectable.
Restart recovery requires a restart ref.

Exact repeated lifecycle requests return `idempotent_replay` without changing
the run generation or hiding the current state. Reused idempotency keys with a
different request fingerprint are denied as conflicts.

## Persistence Expectations

The UAA-P1-010 persistence model is the contract. UAA-P1-025 adds the first
local implementation for run records and receipt summaries:

- append-first ledger binding is required
- append entries require idempotency key, audit ref, receipt ref, rollback ref,
  and safe summary
- accepted transitions record idempotency fingerprints for exact lifecycle
  replay detection
- atomic local writes are required and update memory only after replacement
  succeeds
- entry hash refs and previous-entry hash refs detect corruption
- receipt hash refs and replay validation refs support redacted receipt replay
  validation for mutating local paths
- duplicate per-run idempotency keys are denied before persistence and on load
- offline restore verification is defined before live restore is claimed
- snapshots include a schema version and SHA-256 ref over the run record
- restore rejects mismatched snapshot hashes as corruption
- evidence remains safe-ref and redacted-summary only

## Task Decomposition Binding

Task decomposition uses the durable run spine as a single local run-truth record:

- `/task-decomposition/decompose`, `/task-decomposition/run`, and
  `/task-decomposition/plans/execute` attach a durable binding envelope to
  successful responses.
- Plan validation records `created`, `ready`, or safe failure state without
  recording task request text.
- Plan execution advances through `running`, `blocked`, `retry_pending`, and
  `succeeded` where the state machine permits it.
- Approval request, grant, and revocation activity is bound by safe approval
  refs only; approval refs remain evidence, not authority by themselves.
- Registered handler bindings are safe handler refs only and remain limited to
  already-allowlisted local handlers.
- Explicit repeated idempotency keys are denied before durable mutation.
- Replay validation and restart visibility append safe refs without hiding the
  terminal run state.
- Durable receipt summaries store run id, state, audit ref, receipt ref, replay
  ref, rollback ref, safe summary, receipt hash ref, and replay validation ref
  only.

This binding does not add broad autonomy, background execution, shell or
subprocess behavior, browser or network automation, connector writes, plugin
runtime import, mobile control, model/provider authority, public distribution,
or new production authority.

## Non-Goals

UAA-P1-010 does not add:

- broad autonomy or autonomous background sessions
- task, tool, action, file, memory, network, browser, mobile, remote, plugin, or
  model/provider execution authority
- live scheduler or worker behavior
- live restore, automatic retry, or backup rotation claims
- new backend routes or Control Center controls
- public release, public beta, signed installer, or distribution claims

## Verification

Required verification lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_execution_state_machine_safety.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_ledger_append_only.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_atomic_writes.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_task_decomposition_production_api.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
