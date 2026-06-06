# Dry-Run Execution Authority Boundary

M58 dry-run audit records are not authority.

Dry-run audit reports cannot authorize real execution, tool execution,
subprocess, shell execution, process spawn, file mutation, network access,
model/provider calls, memory write, context injection, browser automation,
plugin execution, remote execution, export, backend routes, Control Center
controls, dependencies, or production authority.

Approval refs, task plans, context packs, memory refs, model output, runtime
output, OpenWebUI output, and Control Center preview refs remain identifiers or
evidence only. They cannot authorize execution through M58.

Audit entries and receipt plans must stay safe-summary-only. They must not
store raw prompts, raw provider payloads, raw file content, secrets, credentials,
or unredacted private content.

M59 remains future.
