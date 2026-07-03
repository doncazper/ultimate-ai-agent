# Background Worker / Scheduler Limited Automation Blocker

Status: blocked, no background worker or scheduler runtime promoted
Lane: Background Worker / Scheduler
Attempted promotion: Level 4 limited automation for one exact proven action
Date: 2026-07-03

## Existing Verified Posture

UAA already has metadata-only background/coworker contracts:

- doc: `docs/architecture/BACKGROUND_COWORKER_WORKER_CONTRACT.md`
- core: `src/ultimate_ai_agent/core/execution/background_coworker.py`
- CLI:
  `PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-coworker-workers`
- tests:
  - `tests/test_background_coworker_worker_contract.py`
  - `tests/test_run_observability_surface.py`

The contracts represent worker identity refs, handoff envelopes, lease and
heartbeat metadata, cancel/resume request metadata, parent/child run trees, and
read-only worker status models. They do not start workers, consume queues,
dispatch work, schedule jobs, call providers, execute tools, write connectors,
run shell commands, or persist raw context.

## Why This Was Not Unblocked

The requested promotion requires one exact foreground action that is already
proven, plus explicit operator setup, pause/cancel/revoke controls, approval
renewal/expiry posture, run observability, and receipts for each scheduled run.

That promotion was not safe in this run because:

- the Action Execution lane remains limited to `local_task_create`;
- promotion of an additional exact Action kind is blocked;
- no scheduler contract binds a proven action to a future run window;
- no approval renewal/expiry contract exists for scheduled execution;
- no pause/cancel/revoke runtime control exists;
- no per-run receipt schema exists for scheduled attempts;
- no queue consumer, worker process, dispatch route, or scheduler route is
  allowed by current contracts.

## Missing Contract / Test / Evidence

- exact already-proven foreground action selected for scheduling;
- schedule window and cadence contract;
- operator setup receipt;
- approval renewal and expiry posture;
- pause/cancel/revoke contract and safe-disable refs;
- per-run receipt/evidence/proof refs;
- run observability binding for scheduled attempts;
- denial paths for stale approval, revoked approval, disabled worker,
  overlapping run, unsafe action, provider/model call, connector write, shell
  execution, and background loop attempts;
- CLI/API/Core parity for read-only inspection and any later mutation routes.

## Smallest Next Safe Action

Run a dedicated scheduler prerequisite PR only after a second exact foreground
Action kind or another level-3 foreground lane has merged. The prerequisite PR
should define schedule metadata, approval renewal, pause/cancel/revoke, and
per-run receipt contracts without starting a worker or scheduler.

## Authority Still Blocked

- background execution
- scheduler runtime
- queue consumers
- worker processes, daemons, or pools
- autonomous model/provider calls
- provider SDK calls
- tool execution expansion
- connector writes/sends
- live web, browser, or shell/local-command execution
- hidden loops or self-selected tasks
- memory writes or context injection
- public beta, public release, or production authority
