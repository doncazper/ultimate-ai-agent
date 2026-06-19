# Durable Run Spine

Status: active UAA-P1-010 contract

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

Append-first local storage, atomic persistence, backup minimum set, offline
restore operation, and task-decomposition binding remain scoped to later P1
items.

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
refs as applicable. Repeating a prior idempotency key or replay ref is denied.

## Persistence Expectations

The UAA-P1-010 persistence model is a contract, not the final storage engine:

- append-first ledger binding is required
- atomic writes are required when storage is added
- offline restore is required before live restore is claimed
- snapshots include a schema version and SHA-256 ref over the run record
- restore rejects mismatched snapshot hashes as corruption
- evidence remains safe-ref and redacted-summary only

## Non-Goals

UAA-P1-010 does not add:

- broad autonomy or autonomous background sessions
- task, tool, action, file, memory, network, browser, mobile, remote, plugin, or
  model/provider execution authority
- live scheduler or worker behavior
- production persistence implementation
- new backend routes or Control Center controls
- public release, public beta, signed installer, or distribution claims

## Verification

Required verification lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_execution_state_machine_safety.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_ledger_append_only.py
```
