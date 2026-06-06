# Runtime Sandbox Spec

v0.85.0 / M81 implements Runtime Sandbox Spec as deterministic local
spec-only and review-only contracts.

M81 defines prior milestone refs, boundary refs, threat model refs, audit
requirement refs, a runtime sandbox spec policy, a runtime sandbox spec request,
and a runtime sandbox spec report. The report is local-only and non-authoritative.
Evaluator boundaries revalidate safety-critical fields before a report can be
accepted for review.

M81 has no runtime sandbox execution, no command proposal, no command execution,
no subprocess execution, no shell execution, no process spawn, no filesystem
mutation, no network access, no tool execution, no browser automation, no plugin
execution, no remote execution, no model call, no memory write, no context
injection, no background worker, no backend route, no Control Center control, no
dependency, and no production authority.

M82 remains future.
