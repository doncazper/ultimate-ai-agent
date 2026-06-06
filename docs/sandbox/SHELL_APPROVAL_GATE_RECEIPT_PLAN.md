# Shell Approval Gate Receipt Plan

M86 receipt plans store safe refs only:

- shell approval gate ref
- M85 read-only command allowlist decision ref
- scoped approval bundle ref
- approval ref
- allowlist ref
- command ref
- sandbox spec ref

Receipt plans are safe summary only. They store no shell string, no raw command,
no raw output, no raw prompt, no secret, and no provider payload.

Receipt plans record no command execution, no subprocess execution, no shell
execution, no process spawn, no filesystem mutation, no network access, no tool
execution, no browser automation, no plugin execution, no remote execution, no
model call, no memory write, no context injection, no background worker, no
backend route, no Control Center control, no dependency, and no production
authority.

Evaluator boundaries revalidate receipt bindings and safety-critical fields.
M87 remains future.
