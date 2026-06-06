# M85 to M86 Boundary

M85 implements only the read-only command allowlist contract. It is
contract-only, review-only, deterministic, local-only, exact-bound to an M84
sandboxed echo/no-op command decision, and safe refs only.

M85 adds no shell string, no raw command, no raw output, no command execution,
no subprocess execution, no shell execution, no process spawn, no filesystem
mutation, no network access, no tool execution, no browser automation, no
plugin execution, no remote execution, no model call, no memory write, no
context injection, no background worker, no backend route, no Control Center
control, no dependency, and no production authority.

M86 remains future and is the first place a Shell Approval Gate v1 may be
reviewed. M85 does not implement M86.
