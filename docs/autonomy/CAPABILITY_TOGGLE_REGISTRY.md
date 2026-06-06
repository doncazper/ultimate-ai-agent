# Capability Toggle Registry

Status: M61 / v0.65.0 implemented-released contract.

M61 adds capability-toggle registry contracts only. A capability toggle is a
safe record describing what future authority would need before any risky
capability could be considered.

## Required Bindings

Each toggle contract requires:

- a stable toggle ref
- a capability ref
- an actor ref
- a scope ref
- resource binding
- duration when a future non-off mode is requested
- a risk class
- a revocation ref
- an audit/replay ref
- an approval record only where a future milestone explicitly allows one

Approval refs are identifiers, not authority. approval_test_* refs are never
runtime authority and are denied by M61 validators. A consent ref alone is not
authority.

## M61 Denials

M61 toggles are disabled by default and dry-run first. They cannot enable Mode
1, Mode 2, Mode 3, Mode 4, Mode 5, or Mode 6. They add no global autonomy
switch, no execution, no tool execution, no browser automation, no shell
execution, no network tools, no background worker, no autonomous session, no
memory write, no context injection, no model/provider authority, no plugin
execution, no mobile sensor access, no remote execution, no backend route, no
dependency, and no production authority.

M62 remains future.
