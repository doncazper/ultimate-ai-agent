# Low-Risk Tool Autonomy Single-Session Policy

The M92 policy is review-only, low-risk only, single-session only,
deterministic, local-only, and safe refs only. It requires exact M91 binding,
exact low-risk autonomous dry run binding, and approval refs as identifiers
only.

The policy denies low-risk tool autonomy enablement as runtime authority. It
also denies real tool execution, autonomous execution, execution, session start,
additional session, background worker, multi-tool execution, command execution,
shell execution, subprocess execution, filesystem mutation, network access,
browser automation, plugin execution, remote execution, model call, memory
write, context injection, backend route, Control Center control, dependency,
and production authority flags.

Requests must not contain raw tool payload, raw provider payload, raw prompt, or
secret-like content. Evaluator boundaries revalidate the current object fields
instead of trusting constructor validation.

M93 remains future.
