# UAA-P1-090 Task Decomposition Proposal Engine

Status: implemented as a deterministic proposal/read-model lane.

`UAA-P1-090` turns bounded safe operator request refs into reviewable task
decomposition proposals for the Founder Loop. It deliberately stays separate
from the older execution-capable task decomposition runtime.

## Contract Models

The proposal engine lives in
`src/ultimate_ai_agent/core/task_decomposition/proposals.py` and defines:

- `TaskDecompositionRequest`
- `TaskDecompositionProposal`
- `TaskDecompositionStep`
- `TaskDecompositionRisk`
- `TaskDecompositionReviewEnvelope`
- `TaskDecompositionBlockedState`

Each proposal includes the original request safe summary/ref, proposed steps,
dependencies, ambiguity refs, missing evidence refs, risk class, suggested
Action Inbox proposal refs, required approvals, blocked authorities,
`why_proposed`, and `what_this_affects`.

## Founder Loop Bridge

The Founder Loop storage read model projects decomposition data into:

- Plans: `task_decomposition_*` fields render proposed steps, dependencies,
  risks, missing-evidence refs, approval refs, and blocked authorities.
- Action Inbox: generated `task_decomposition_proposal` items are proposal-only
  review artifacts in the proposal-only lane.
- CLI: `scripts/dev/uaa_founder_loop.py inspect` exposes the same bounded refs.

Action Inbox items record no state change contract, expose no local task commit
eligibility, and do not create approval grants. Any future executable work must
come from a separate exact-scoped milestone.

## Safety Boundaries

This lane is proposal-only and review-only.

It preserves:

- no runtime model calls
- no provider calls
- no tool execution
- no action execution
- no workflow execution
- no memory writes
- no context injection
- no shell/subprocess execution
- no browser/network access
- no connector writes
- no autonomous planning authority
- no production authority

The UI renders these refs as inspection data only. It adds no apply/use button,
no hidden context path, no provider call, no workflow dispatch, no memory write,
and no connector write.

## Verification

Focused checks:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_uaa_p1_090_task_decomposition_proposal_engine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_090_task_decomposition_proposal_engine.py -q
```
