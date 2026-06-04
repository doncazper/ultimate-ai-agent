# Tool Runtime Adapter

Status: active M31 documentation.
Current active baseline: **v0.35.0**

M31 implements the first governed Tool Runtime Adapter path. The adapter is
real in the narrow sense that the Python Agent Core can evaluate and complete
one deterministic no-op invocation through a runtime adapter and receive a
typed result envelope.

M31 is no-op-only. It is not arbitrary tool execution.

Allowed in M31:

- `tool:no_op.v1` with `tool_name=“noop”`.
- deterministic no-op invocation.
- no-op result envelope.
- no-op receipt plan.
- replay-key protection.
- evaluator revalidation of safety-critical fields.
- static verifier and Foundation Gate coverage.

Blocked in M31:

- arbitrary tool execution.
- dynamic dispatch or user-selected callables.
- plugins.
- shell/subprocess execution.
- file tools or file mutation.
- memory-write tools.
- network tools.
- model/provider tools.
- browser, mobile, remote, or plugin tools.
- backend public execute routes.
- Control Center execute controls.
- production authority.

Approval refs, approval decisions, tool intents, task plans, execution state
transitions, context packs, memory refs, model output, runtime output, and
arbitrary strings are not authority for arbitrary tools.

M32-M40 remain planned/provisional.
