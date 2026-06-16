# Connector Audit + Revocation Hardening Authority Boundary

M129 is review-only, hardening-only, local-only, safe-ref-only, and exact-bound
to M128 connector write execution results.

Allowed authority:

- validate exact M128 decision and result refs
- record a safe audit ledger entry with safe refs only and safe summaries only
- record a revocation readiness record for governed review
- bind audit refs, replay refs, revocation refs, kill-switch refs, retention
  policy refs, and redaction refs
- preserve M130 as future Connector Safety Freeze work

Denied authority:

- no live connector runtime
- no account auth
- no network access
- no credential handling
- no raw connector content
- no full content read
- no connector write execution
- no connector send execution
- no connector delete execution
- no connector export
- no connector bulk export
- no attachment download
- no audit export
- no revocation execution
- no kill-switch execution
- no approval revocation execution
- no connector session stop
- no model call
- no memory write
- no context injection
- no backend route
- no Control Center control
- no dependency
- no production authority

Revocation refs remain identifiers, not authority. Kill-switch refs remain
identifiers, not execution.
