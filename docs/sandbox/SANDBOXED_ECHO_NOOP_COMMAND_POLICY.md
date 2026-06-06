# Sandboxed Echo/No-Op Command Policy

The M84 policy allows only an in-process sandboxed echo/no-op command over an M83
shell dry-run classifier no-effect decision. The policy is deterministic,
local-only, and safe summary only.

Policy flags deny shell strings, raw commands, raw output, command execution,
subprocess execution, shell execution, process spawn, filesystem mutation,
network access, tool execution, browser automation, plugin execution, remote
execution, model call, memory write, context injection, background worker,
backend route, Control Center control, dependency, and production authority.

Policy metadata must be safe and secret-free. Evaluator boundaries revalidate
policy and request fields before a review result is accepted. M85 remains
future.
