# Phase 02: Pair-Run Contracts And State Machine

Goal: create the UAA-owned contract and state model for bounded paired-agent
relay runs.

## Required Work

1. Add Python core contracts for pair run, agent slot, turn packet,
   inbound/outbound artifact ref, stop condition, run state, receipt ref,
   evidence ref, and blocked authority ref.
2. Model states: created, pending_approval, approved, agent_a_running,
   waiting_agent_a, agent_b_running, waiting_agent_b, approval_required,
   user_stopped, max_turns_reached, timed_out, blocked, failed, completed.
3. Enforce max turns, wall-clock timeout, per-turn output byte limit,
   workspace/repo scope, exact agent slot ids, and stop/sentinel rules.
4. Reject raw credential-like material, raw local paths in durable evidence,
   arbitrary command strings, unapproved scope expansion, unbounded turn count,
   and background dispatch.
5. Add deterministic builders for preview/readiness mode.
6. Add tests for valid contract, invalid limits, unsafe refs, duplicate slots,
   state transition rejection, and blocked authority posture.

## Acceptance Criteria

- Pair-run contracts are backend-owned and safe-ref oriented.
- No local agent process starts in this phase.
- The state machine fails closed on invalid transitions.
- The contract can represent both no-execution preview and future foreground
  execution.

## Verification

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_coding_cockpit_read_model.py -q
```

