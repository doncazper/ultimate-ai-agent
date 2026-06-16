# Connector Write Dry-Run Planner Receipt Plan

The M127 receipt plan is a no-effect receipt plan for review-only connector
write dry-run planning. It stores safe refs only:

- dry-run plan ref
- approval ref
- connector read-only runtime ref
- source messages connector contract review ref
- actor ref
- user ref
- workspace ref
- connector scope refs
- connector allowlist refs
- source operation allowlist refs
- dry-run operation allowlist refs
- safe write target refs
- safe payload summary refs
- redaction refs
- audit ref
- replay ref
- idempotency key
- no-effect receipt plan ref

The receipt plan stores no raw connector content, no full content read, no
credential material, no connector write result, no connector send result, no
connector delete result, no connector export, no attachment download, no context
injection, no memory write, no execution result, no model output, no provider
payload, no backend route state, no Control Center state, and no production
authority.

Approval refs remain identifiers, not authority. The receipt is exact-bound,
actor-bound, user-bound, workspace-bound, replay-safe, revocable, dry-run-only,
and safe refs only.
