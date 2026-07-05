# Phase 05: Chat Turn Preparation Loop

Goal: make UAA's operator input path feel like a real agent loop: a turn is
prepared, routed, bound, optionally planned, connected to durable state, and
returned with readable next actions or blocked-state explanations.

Reference pattern: GoatCitadel's chat-turn prep gathers session/runtime grants,
message state, model-router decisions, retrieval context, orchestration
eligibility, and planner fallback. Borrow the loop shape, not the code.

## Required Work

1. Inspect UAA's chat, turn router, memory recall, model router, planning,
   Action Inbox, evidence, API, and Control Center surfaces.
2. Implement or harden a UAA-native `PreparedTurn` contract containing safe
   refs for:
   - session/operator/task;
   - latest user turn;
   - turn contract decision;
   - route-decision binding;
   - memory/context readiness;
   - tool/action readiness;
   - orchestration eligibility;
   - durable run ref when created;
   - evidence refs;
   - blocked authority refs.
3. Ensure prepared turns never persist raw prompt text or raw model output.
4. Add clear branches:
   - answer directly;
   - answer with reviewed memory refs;
   - draft/plan;
   - prepare tool/action;
   - approval required;
   - execute approved exact action;
   - blocked unsafe;
   - ask clarifying question.
5. Connect one real UI/API/CLI path to display prepared-turn state without raw
   JSON as the primary operator-critical workflow.
6. Add tests for direct answer, approval required, blocked unsafe, memory-read
   readiness, tool/action readiness, and no raw persistence.

## Acceptance Criteria

- A user turn can be traced through routing, binding, run state, and evidence.
- The preparation loop is backend-owned and not only React state.
- The operator sees what the agent knows, plans, needs, and cannot do.
- Missing authority is explicit and does not degrade into silent failure.

## Verification

Run focused chat/prepared-turn tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_turn_contract_router_harness_binding.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
```

Run frontend checks only when frontend files changed.

