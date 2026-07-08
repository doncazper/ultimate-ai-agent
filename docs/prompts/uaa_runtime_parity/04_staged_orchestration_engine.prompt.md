# Phase 04: Staged Orchestration Engine

Goal: adapt external comparison runtime's staged orchestration pattern into a UAA-native
durable orchestration engine that can plan, stage, checkpoint, degrade, and
recover without bypassing policy or approval boundaries.

Reference pattern: external comparison runtime builds role-based plans and executes dependency
stages with concurrency, callbacks, degraded handoffs, progress, citations, and
integrity signals. Borrow the structure, not the implementation.

## Required Work

1. Inspect UAA's planning, task decomposition, execution steps, runtime,
   approvals, evidence, and Control Center progress surfaces.
2. Implement or harden orchestration contracts for:
   - orchestration plan;
   - stage;
   - step;
   - dependency;
   - callback/adaptor ref;
   - checkpoint;
   - degraded handoff;
   - blocked authority.
3. Enforce dependency validation:
   - no missing dependencies;
   - no cycles;
   - no same-stage dependencies unless explicitly supported and tested;
   - no execution-ready step without policy and approval posture.
4. Support staged progress read models:
   - pending;
   - running;
   - waiting;
   - degraded;
   - skipped;
   - blocked;
   - failed;
   - completed.
5. Permit only deterministic/no-effect callbacks unless an exact existing UAA
   authority lane already authorizes execution.
6. Add tests for pass path, dependency rejection, degraded handoff, skip
   downstream on failure, checkpoint replay, and redaction.
7. Expose a CLI/API inspection surface for orchestration plans and run traces.

## Explicit Non-Goals

- Do not create broad autonomous workers.
- Do not add hidden model calls to populate steps.
- Do not let model/provider output execute actions.
- Do not add unrestricted command execution.

## Acceptance Criteria

- The engine can represent a real operation plan with progress and recovery.
- The engine fails closed when a step needs unauthorized authority.
- The operator can see why a step is waiting, blocked, degraded, or skipped.
- Tests prove dependency validation and redacted trace behavior.

## Verification

Run focused orchestration tests plus:

```bash
git diff --check
.venv/bin/python scripts/verify_operational_maturity.py
```
