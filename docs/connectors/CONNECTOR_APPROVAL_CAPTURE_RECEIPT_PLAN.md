# Connector Approval Capture Receipt Plan

The M126 receipt plan is a no-effect receipt plan for review-only connector
approval capture. It stores safe refs only:

- approval ref
- connector read-only runtime ref
- source messages connector contract review ref
- actor ref
- user ref
- workspace ref
- audit ref
- replay ref
- idempotency key
- no-effect receipt plan ref

The receipt plan stores no raw connector content, no full content read, no
credential material, no connector export, no attachment download, no context
injection, no memory write, no execution result, no model output, no provider
payload, no backend route state, no Control Center state, and no production
authority.

Approval refs remain identifiers, not authority. The receipt is exact-bound,
actor-bound, user-bound, workspace-bound, replay-safe, revocable, and safe refs
only.
