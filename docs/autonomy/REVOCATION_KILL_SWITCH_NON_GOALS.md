# M67 Revocation + Kill Switch Non-Goals

M67 is contract-only and review-only. It does not implement runtime revocation,
runtime kill switches, process management, execution, or production authority.

M67 explicitly does not add:

- revocation action
- kill-switch activation
- session stop
- process kill
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
- backend route
- Control Center control
- dependency
- production authority

Approval refs are identifiers only. `approval_test_` refs are never runtime
authority. A Revocation + Kill Switch record may explain why a future operator
should revoke or stop something, but M67 itself performs no revocation action,
does no kill-switch activation, and does no session stop.

M68 remains future.
