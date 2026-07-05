# Phase 02: Productized Agent Loop Spine

Goal: make UAA's operator loop visibly coherent: input -> intent summary ->
plan proposal -> action proposal -> approval posture -> result/blocked state ->
evidence -> memory review candidate.

This phase should strengthen UAA's Founder Command Center spine without adding
new high-authority runtime behavior.

## Required Work

1. Inspect existing Founder Loop, Today, Inbox, Plans, Actions, Chat handoff,
   Evidence, Memory, and Settings read models, routes, CLI scripts, tests, and
   Control Center components.
2. Define a backend-owned `AgentLoopThread` or equivalent read model that can
   represent:
   - operator input or work request safe ref;
   - intent classification and ambiguity posture;
   - facts, assumptions, and unknowns;
   - plan steps and revision state;
   - proposed actions and required approvals;
   - current blocked/degraded/partial status;
   - evidence refs;
   - memory-review candidate refs;
   - next safe operator decision.
3. Bind existing surfaces to the read model instead of duplicating truth in UI
   state.
4. Add CLI/API inspection for the same loop state.
5. Render the loop in Control Center using operator-readable language, not raw
   JSON.
6. Update docs and product truth with exact implemented and blocked states.

## Safe Implementation Shape

Prefer a read-only or proposal-first vertical slice first:

- Python core owns loop state assembly.
- API exposes typed read-only routes unless an exact approved mutation lane
  already exists.
- CLI prints the same fields in redacted summary form.
- UI renders status, plan, actions, evidence, and memory-review candidates.
- No model output is treated as truth or authority.

## Acceptance Criteria

- A user can inspect where a work item is in the agent loop.
- Ambiguity, assumptions, unknowns, and blocked states are explicit.
- The UI cannot approve or execute anything without backend-owned approval
  posture.
- Existing Action Inbox and Evidence routes remain the authority source for
  their domains.
- No new runtime model call or action execution is introduced by this phase.

## Verification

Run focused tests for changed core/API/CLI/UI files plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_product_truth.py
make frontend-check
```

Skip frontend checks only if no frontend files changed.

