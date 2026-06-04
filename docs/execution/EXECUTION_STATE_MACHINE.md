# Execution State Machine

Status: active M30 source-of-truth documentation.

The M30 execution state machine is deterministic, local, and no-effect only.
It accepts explicit `ExecutionRun` and `ExecutionTransitionRequest` objects and
returns an `ExecutionTransitionDecision`.

Supported state changes:

- `planned` to `running_no_effect` for safe no-effect step completion.
- `pending` or `ready` to `completed_no_effect` when dependencies are complete.
- `paused`, `blocked`, or `waiting_for_dependency` as decision-only states.

The state machine does not execute tasks, actions, tools, files, memory,
network calls, model/provider calls, browser/mobile/remote/plugin/shell
actions, scheduler jobs, background workers, autonomous loops, or context
injection.

Replay keys are required. A reused replay key is denied with
`EXECUTION_REPLAY_DENIED`.

Evaluator boundaries revalidate current object fields before allowing a
transition. Constructor validation alone is not trusted.

M31-M40 remain planned/provisional.
