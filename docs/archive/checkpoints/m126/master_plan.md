# Checkpoint M126 Master Plan

Goal: add deterministic, local, review-only Connector Approval Capture
contracts bound to M125 Connector Read-Only Runtime records.

Scope:

- connector approval capture request, record, decision, and no-effect receipt
  plan contracts
- exact M125 runtime binding
- actor-bound, user-bound, workspace-bound approval capture
- replay-safe, revocable, expiry-aware denial behavior
- `approval_test_` denial
- safe refs only
- tests, static verification, documentation integrity, and Foundation Gate

Non-goals: live connector runtime, account auth, network access, credential
handling, raw connector content, full content read, connector write, connector
send, connector delete, connector export, connector bulk export, attachment
download, model call, memory write, context injection, execution, backend route,
Control Center control, dependency, M127 work, beta release, or production
authority.
