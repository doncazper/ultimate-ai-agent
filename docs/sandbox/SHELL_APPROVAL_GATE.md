# Shell Approval Gate v1

M86 adds Shell Approval Gate v1 as a contract-only, review-only, deterministic,
local-only decision over an exact M85 Read-Only Command Allowlist decision and
an exact scoped approval bundle.

The shell approval gate records whether an identifier-only approval ref is valid
for review for the exact allowlisted command ref, actor ref, sandbox spec ref,
and approval bundle refs. Approval refs are identifiers only and are not runtime
authority.

M86 stores safe refs only and safe summary only. It records no shell string, no
raw command, and no raw output. Evaluator boundaries revalidate safety-critical
fields, including model-copy-mutated allowlist decisions, approval bundles,
execution flags, raw-content flags, and receipt plans.

M86 adds no command execution, no subprocess execution, no shell execution, no
process spawn, no filesystem mutation, no network access, no tool execution, no
browser automation, no plugin execution, no remote execution, no model call, no
memory write, no context injection, no background worker, no backend route, no
Control Center control, no dependency, and no production authority.

M87 remains future.
