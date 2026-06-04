# Tool Runtime Non-Goals

Status: active M31 documentation.
Current active baseline: **v0.35.1**

M31 intentionally does not implement:

- arbitrary tool execution.
- no arbitrary tool execution.
- side-effecting tools.
- dynamic dispatch.
- plugins.
- no plugins.
- shell/subprocess execution.
- file reads, file writes, or file deletes.
- memory writes.
- network calls or web search.
- model/provider calls or local LLM calls.
- browser automation or Computer Use.
- mobile/device access.
- remote execution.
- schedulers, background workers, daemons, or autonomous loops.
- context injection runtime.
- backend public execute routes.
- Control Center execute controls.
- no Control Center execute control.
- dependencies.
- production authority.

M31 proves only that a governed adapter can complete exactly one deterministic
no-op tool invocation and produce a redacted result envelope.

M32-M40 remain planned/provisional.
