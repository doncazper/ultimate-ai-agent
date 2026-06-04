# Execution Step Contracts

Status: active M30 source-of-truth documentation.

`ExecutionStep` records are safe summaries and refs only. They carry a stable
step ref, a no-effect mode, a status, optional dependency refs, and an input
boundary.

Allowed M30 step modes:

- `no_effect`
- `validation_only`
- `receipt_plan_only`

Blocked M30 step modes:

- task execution.
- action execution.
- tool execution.
- file mutation.
- memory write.
- Event Ledger mutation.
- network call.
- model/provider call.
- browser/mobile/remote/plugin/shell action.
- scheduler or background worker.
- unknown step mode.

Blocked step modes are denied before any state transition. M30 step contracts
are reviewable state-machine records, not execution instructions.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
