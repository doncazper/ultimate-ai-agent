# Autonomous Tool Execution Contract Policy

M91 policy enables only review of autonomous tool execution contract metadata.
The policy requires contract-only, review-only, deterministic, local-only, safe
refs only, exact M90 binding, approval refs as identifiers only, and dry-run plan
only semantics.

The policy denies real tool execution, autonomous execution, execution,
autonomous session start, background worker start, command execution, shell
execution, subprocess execution, filesystem mutation, network access, browser
automation, plugin execution, remote execution, model call, memory write,
context injection, backend route, Control Center control, dependency change, and
production authority.

Raw tool payloads, raw provider payloads, raw prompts, and secret-like content
are denied. Evaluator boundaries revalidate policy, request, decision, and
receipt fields. M92 remains future.
