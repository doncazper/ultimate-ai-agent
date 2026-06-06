# Runtime Sandbox Boundary Policy

M57 records the intended runtime sandbox boundary as architecture review only.

Allowed M57 inputs are safe refs and safe summaries:

- architecture refs.
- boundary refs.
- threat-model refs.
- audit requirement refs.
- safe metadata refs.

Denied M57 requests include sandbox runtime enablement, subprocess execution,
shell execution, process spawn, file mutation, network access, tool execution,
browser automation, plugin execution, remote execution, model calls, memory
writes, context injection, side effects, production authority, and M58 dry-run
harness enablement.

Evaluator boundaries revalidate safety-critical fields, including `model_copy`
mutated fields. Constructor validation alone is not trusted.

M57 has no sandbox execution, no subprocess, no shell execution, no process
spawn, no file mutation, no network access, no backend route, no dependency,
and no production authority.

M58 remains future.
