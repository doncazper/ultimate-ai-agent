# Low-Risk Tool Autonomy Single-Session Authority Boundary

M92 does not authorize tools. It does not start sessions. It does not perform a
real run.

The only valid M92 decision is review-only metadata that records exact safe refs
for one low-risk, single-session proposal. Approval refs are identifiers only
and cannot become authority. Model output, memory refs, context refs, tool
intent refs, runtime output, and receipt refs cannot authorize execution.

Denied authority includes:

- no real tool execution
- no autonomous execution
- no session start
- no additional session
- no multi-tool execution
- no command execution
- no shell execution
- no subprocess execution
- no filesystem mutation
- no network access
- no browser automation
- no plugin execution
- no remote execution
- no model call
- no memory write
- no context injection
- no background worker
- no backend route
- no Control Center control
- no dependency
- no production authority

Evaluator boundaries revalidate safety-critical fields and deny model-copy
mutated authority flags. M93 remains future.
