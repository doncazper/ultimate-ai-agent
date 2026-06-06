# Shell Approval Gate Policy

Shell Approval Gate v1 is contract-only, review-only, deterministic,
local-only, read-only only, and safe-ref-only.

Policy requirements:

- exact M85 binding is required.
- exact scoped approval bundle binding is required.
- approval refs are identifiers only.
- approval refs cannot authorize command execution.
- approval refs cannot authorize shell execution.
- approval_test_ refs are denied.
- revoked, expired, or replay-used approval bundles are denied.
- evaluator boundaries revalidate safety-critical fields.

Denied capabilities:

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

M87 remains future.
