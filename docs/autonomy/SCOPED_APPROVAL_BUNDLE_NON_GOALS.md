# Scoped Approval Bundle Non-Goals

M66 does not implement runtime approval authority. Scoped approval bundles remain
contract-only and review-only.

M66 does not add:

- policy activation
- session start
- autonomous actions
- background worker
- execution
- tool execution
- shell execution
- network tools
- browser automation
- plugin execution
- mobile sensor access
- remote execution
- memory write
- context injection
- model/provider authority
- backend routes
- Control Center controls
- approval-bundle persistence service
- approval-bundle activation endpoint
- approval-bundle execution endpoint
- dependencies
- production authority

Approval refs are identifiers. They are not runtime authority and cannot be
used to bypass exact-scope validation.

M67 remains future.
