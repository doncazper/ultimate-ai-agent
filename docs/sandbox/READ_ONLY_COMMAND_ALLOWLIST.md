# M85 Read-Only Command Allowlist

M85 implements the Read-Only Command Allowlist as contract-only, review-only,
deterministic, and local-only governance metadata.

The allowlist is evaluated over an exact M84 sandboxed echo/no-op command
decision. M85 requires exact M84 binding for the sandboxed command ref,
sandboxed echo/no-op decision ref, shell dry-run decision ref, command proposal
ref, sandbox spec ref, and actor ref. Evaluator boundaries revalidate those
safety-critical fields.

The result is safe refs only and safe summary only. M85 records that a command
ref was reviewed against a read-only command allowlist; it does not authorize or
perform the command.

M85 adds no shell string, no raw command, no raw output, no command execution,
no subprocess execution, no shell execution, no process spawn, no filesystem
mutation, no network access, no tool execution, no browser automation, no
plugin execution, no remote execution, no model call, no memory write, no
context injection, no background worker, no backend route, no Control Center
control, no dependency, and no production authority.

M86 remains future.
