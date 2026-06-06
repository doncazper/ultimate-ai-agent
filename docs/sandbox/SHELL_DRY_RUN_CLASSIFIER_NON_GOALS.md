# Shell Dry-Run Classifier Non-Goals

M83 is not command execution and not shell execution.

Non-goals:

- no dry-run execution
- no shell string
- no command execution
- no subprocess execution
- no shell execution
- no process spawn
- no filesystem mutation
- no network access
- no tool execution
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

M83 is classifier-only, review-only, deterministic, and local-only over an M82
command proposal. It may classify safe metadata for review. That metadata is
not authority and cannot be promoted into execution by this milestone.

Evaluator boundaries revalidate safety-critical fields.

M84 remains future.
