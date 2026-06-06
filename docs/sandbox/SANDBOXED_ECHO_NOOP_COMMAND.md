# Sandboxed Echo/No-Op Command

M84 adds a sandboxed echo/no-op command contract. It is in-process only,
deterministic, local-only, and bound to an already validated M83 shell dry-run
classifier decision whose classification is `no_effect_review`.

The command may return safe echo text and safe summary only receipt metadata for
human review. It adds no shell string, no raw command, no raw output, no command
execution, no subprocess execution, no shell execution, no process spawn, no
filesystem mutation, no network access, no tool execution, no browser
automation, no plugin execution, no remote execution, no model call, no memory
write, no context injection, no background worker, no backend route, no Control
Center control, no dependency, and no production authority.

Safety phrase guard: no command execution; no browser automation; no memory write; no control center control.

Evaluator boundaries revalidate the current request, M83 decision, result, and
receipt fields. M85 remains future.
