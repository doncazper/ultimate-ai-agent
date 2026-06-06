# Runtime Sandbox Spec Authority Boundary

M81 Runtime Sandbox Spec output is not authority.

The spec may describe local-only sandbox boundaries, boundary refs, threat
model refs, and audit requirement refs. It cannot authorize runtime sandbox
execution, command proposal, command execution, subprocess execution, shell
execution, process spawn, filesystem mutation, network access, tool execution,
browser automation, plugin execution, remote execution, model call, memory
write, context injection, background worker, backend route, Control Center
control, dependency, or production authority.

Approval refs, task refs, tool intent refs, context refs, memory refs, model
output refs, runtime output refs, OpenWebUI refs, and review refs are
identifiers only. They are not runtime sandbox authority and cannot authorize
execution.

Evaluator boundaries revalidate safety-critical fields and reject unsafe
model-copy mutations.

M82 remains future.
