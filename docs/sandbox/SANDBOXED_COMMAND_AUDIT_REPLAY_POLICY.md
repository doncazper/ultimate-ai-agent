# Sandboxed Command Audit Replay Policy

M87 policy allows only contract-only, review-only, replay-view-only,
deterministic, local-only audit replay review.

Required policy invariants:

- exact M86 shell approval gate binding is required.
- exact replay step binding is required.
- safe refs only are allowed.
- safe summary only receipts are allowed.
- evaluator boundaries revalidate safety-critical fields.

Denied policy authority:

- no replay runner
- no replay execution
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

M88 remains future.
