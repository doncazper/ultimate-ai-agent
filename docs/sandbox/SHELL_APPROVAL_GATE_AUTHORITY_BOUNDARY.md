# Shell Approval Gate Authority Boundary

M86 does not make shell approvals executable. It only validates a review-only
approval gate decision bound to an exact M85 Read-Only Command Allowlist
decision and exact scoped approval bundle.

Approval refs are identifiers only. A scoped approval bundle can explain review
intent, actor binding, resource binding, allowlist binding, audit refs,
revocation refs, and replay refs, but it cannot authorize command execution,
subprocess execution, shell execution, process spawn, filesystem mutation,
network access, tool execution, browser automation, plugin execution, remote
execution, model call, memory write, context injection, background worker,
backend route, Control Center control, dependency, or production authority.

M86 keeps all receipts safe summary only and safe refs only. It stores no shell
string, no raw command, no raw output, no raw prompt, and no secret. Evaluator
boundaries revalidate mutated approval bundles, mutated allowlist decisions,
raw-content flags, execution flags, and receipt plans.

M87 remains future.
