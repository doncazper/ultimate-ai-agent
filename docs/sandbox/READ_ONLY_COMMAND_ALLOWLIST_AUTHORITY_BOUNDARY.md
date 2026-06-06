# M85 Read-Only Command Allowlist Authority Boundary

The M85 read-only command allowlist is not authority to execute anything.

An allowlist match is a review-only decision. It may explain that a command ref
is present in reviewed metadata, but it cannot grant command execution,
subprocess execution, shell execution, process spawn, filesystem mutation,
network access, tool execution, browser automation, plugin execution, remote
execution, model call, memory write, context injection, background worker,
backend route, Control Center control, dependency, or production authority.

M85 requires exact M84 binding and evaluator boundaries revalidate the current
object fields. Model output, runtime output, memory refs, context refs, task
plans, tool intents, approval refs, and approval_test_* refs cannot authorize
execution.

M85 stores safe refs only and safe summary only. It stores no shell string, no
raw command, and no raw output.

M86 remains future.
