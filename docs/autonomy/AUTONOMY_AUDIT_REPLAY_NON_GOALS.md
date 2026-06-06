# Autonomy Audit Replay Non-Goals

M65 is not an autonomy runtime milestone. It adds an autonomy audit + replay
viewer contract only.

M65 explicitly does not add:

- policy activation
- session start
- autonomous actions
- background worker or scheduler behavior
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
- model/provider authority or model/provider calls
- backend route
- Control Center control
- dependency
- production authority
- scoped approval bundles

The replay viewer is review-only and replay-view-only. It can describe a
deterministic simulated step sequence from M64, but it cannot replay by
executing, cannot start an autonomy session, cannot export raw replay payloads,
and cannot treat approval refs as authority.

M66 remains future.
