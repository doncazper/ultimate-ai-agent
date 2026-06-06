# v0.90.0 Master Plan

M86 Shell Approval Gate v1 adds review-only shell approval gate contracts.

Scope:

- Add shell approval gate policy, request, decision, and receipt plan contracts.
- Bind decisions exactly to M85 Read-Only Command Allowlist decisions.
- Bind approvals exactly to scoped approval bundles.
- Keep approval refs as identifiers only.
- Revalidate model-copy-mutated allowlist decisions, approval bundles,
  execution flags, raw-content flags, and receipt plans.
- Add docs, tests, static verifier coverage, documentation-integrity coverage,
  and Foundation Gate criteria.

Non-goals:

- no shell string
- no raw command
- no raw output
- no command execution
- no subprocess execution
- no shell execution
- no process spawn
- no filesystem mutation
- no network access
- no tool execution
- no browser automation
- no plugin execution
- no remote execution
- no model call
- no memory write
- no context injection
- no background worker
- no backend route
- no Control Center control
- no dependency
- no M87 work
- no production authority
