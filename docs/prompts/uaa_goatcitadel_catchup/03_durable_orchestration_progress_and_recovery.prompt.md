# Phase 03: Durable Orchestration, Progress, And Recovery

Goal: close the gap with GoatCitadel-style durable work visibility by making
UAA's run lifecycle, progress, checkpoints, retry/recovery posture, and blocked
states more inspectable and operator-useful.

This phase may add read models and local durable state only when they preserve
existing authority boundaries.

## Required Work

1. Inspect UAA's execution, durable run, event log, approval queue, progress,
   background coworker contract, route inventory, API manifest, and tests.
2. Define or harden a durable run lifecycle model with:
   - run id and safe refs;
   - lifecycle status;
   - current phase/step;
   - checkpoint summaries;
   - retry and recovery posture;
   - approval wait state;
   - cancellation/dead-letter state;
   - evidence refs;
   - redacted error summaries.
3. Add or improve CLI/API/Control Center inspection for active, completed,
   blocked, failed, and recovered runs.
4. Add tests for resume/recovery truth where local fixtures can prove behavior.
5. If actual recovery execution is not implemented, label it as blocked or
   proposal-only. Do not simulate it as production behavior.

## Safe Implementation Shape

- Backend read model first.
- Durable state must be local and redacted.
- Progress events are operator signals; durable logs remain source of truth.
- Approval wait/resume must validate exact approval refs before any mutation.
- Retry must be idempotent or explicitly unavailable.

## Acceptance Criteria

- Operators can tell what a run is doing, what it is waiting for, and what can
  safely happen next.
- Failed and blocked runs have explicit reasons and next actions.
- Tests prove route/API shape and lifecycle edge cases.
- UI does not invent progress, checkpoint, retry, recovery, or cancellation
  truth.

## Verification

Run focused execution tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

