# Phase 03: Turn, Run, And Approval State Model

Goal: close the durable runtime integration gap by making UAA's canonical loop
explicit: Turn -> Durable Run -> Approval -> Result/Evidence/Recovery.

Reference pattern: GoatCitadel's canonical runtime state model defines Turn,
Durable Run, approval linkage, retry/resume/wait behavior, and ownership rules.
Borrow the state semantics, not the code.

## Required Work

1. Inspect UAA's existing durable run, execution state machine, approvals,
   evidence, Action Inbox, storage, CLI, and Control Center surfaces.
2. Define or harden UAA-native contracts for:
   - `TurnRef`;
   - `DurableRunRef`;
   - `ApprovalRef`;
   - `CheckpointRef`;
   - `ReceiptRef`;
   - `RouteDecisionBindingRef`.
3. Ensure state transitions cover:
   - created;
   - routed;
   - planning;
   - waiting_for_approval;
   - approved;
   - running;
   - retry_scheduled;
   - paused;
   - resumed;
   - cancelled;
   - failed;
   - blocked;
   - completed.
4. Make transitions exact-scoped, append-only or replayable, redacted, and
   evidence-backed.
5. Add retry/recovery posture without adding background autonomy unless already
   authorized by existing UAA policy.
6. Add CLI/API read models for inspecting a turn/run/approval chain.
7. Update product truth and route manifest docs for any exposed routes.

## Acceptance Criteria

- A durable run cannot exist without a safe turn or operator/task ref.
- An approval cannot resume or execute a changed run scope.
- Retry/resume/cancel states are inspectable and tested.
- Blocked states explain the missing authority or failed validation.
- No raw prompt, response, provider payload, path, or log content is persisted.
- CLI/API parity exists for the new durable state.

## Verification

Run focused durable run/approval tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
```
