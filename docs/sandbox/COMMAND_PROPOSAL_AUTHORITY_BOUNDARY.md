# Command Proposal Authority Boundary

M82 Command Proposal Contracts are proposal-only and review-only.

A command proposal may describe a structured argv preview and safe purpose for
human review. It cannot authorize command execution, subprocess execution, shell
execution, process spawn, filesystem mutation, network access, tool execution,
browser automation, plugin execution, remote execution, model call, memory
write, context injection, background worker, backend route, Control Center
control, dependency, or production authority.

Approval refs, task refs, tool intent refs, context refs, memory refs, model
output refs, runtime output refs, OpenWebUI refs, review refs, and command refs
are identifiers only. They are not authority.

The receipt plan stores safe summary only metadata. It must store no raw command
and no shell string.

Evaluator boundaries revalidate safety-critical fields and reject unsafe
model-copy mutations.

M83 remains future.
