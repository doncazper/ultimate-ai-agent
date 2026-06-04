# Execution State Machine

Status: active M30 source-of-truth documentation.

The M30 execution state machine is deterministic, local, and no-effect only.
It accepts explicit `ExecutionRun` and `ExecutionTransitionRequest` objects and
returns an `ExecutionTransitionDecision`.

Supported state changes:

- `pending` to `ready` when dependencies are complete.
- `ready` to `completed_no_effect` for safe no-effect step completion.
- completed runs to `completed_no_effect` only after all steps are completed or
  skipped.
- `paused`, `blocked`, or `waiting_for_dependency` as decision-only states.

Blocked runs and blocked steps cannot resume or complete without an explicit
safe transition. Pending steps cannot complete directly, completed steps cannot
complete twice, and runs cannot finalize while pending, blocked, or
future-real-execution steps remain.

The state machine does not execute tasks, actions, tools, files, memory,
network calls, model/provider calls, browser/mobile/remote/plugin/shell
actions, scheduler jobs, background workers, autonomous loops, or context
injection.

Replay keys are required. A reused replay key is denied with
`EXECUTION_REPLAY_DENIED`. Transition IDs are also required for evaluator
decisions, and a reused transition ID is denied with
`EXECUTION_TRANSITION_REPLAY_DENIED`.

Evaluator boundaries revalidate current object fields before allowing a
transition. Constructor validation alone is not trusted. Evaluator revalidation
also denies hidden side-effect metadata, side-effect execution flags, raw
content flags, secret-like metadata, execution requests, auto-run requests,
scheduler requests, and background-worker requests.

M31-M40 remain planned/provisional.
