# Emergency Stop + Process Kill Safety Non-Goals

M89 does not implement a process killer or emergency stop runtime.

Non-goals:

- no emergency stop execution
- no process kill
- no process signal
- no PID handling
- no raw PID
- no raw signal
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

M89 is contract-only, review-only, deterministic, local-only, and safe refs
only. M90 remains future.
