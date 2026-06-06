# M85 Read-Only Command Allowlist Policy

The read-only command allowlist policy is contract-only and review-only.

Required policy invariants:

- deterministic
- local-only
- read-only command allowlist
- exact M84 binding
- safe refs only
- safe summary only
- evaluator boundaries revalidate

Denied policy states:

- no shell string
- no raw command
- no raw output
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

M86 remains future.
