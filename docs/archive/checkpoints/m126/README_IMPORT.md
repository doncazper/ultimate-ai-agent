# Checkpoint M126 Import Notes

Checkpoint M126 implements Connector Approval Capture contracts only. It
captures exact-bound review-only approvals and denials over M125 Connector
Read-Only Runtime records.

It records safe refs only: approval ref, connector read-only runtime ref, source
messages connector contract review ref, baseline ref, actor-bound ref,
user-bound ref, workspace-bound ref, connector scope refs, connector allowlist
refs, operation allowlist refs, redacted metadata preview refs, audit ref,
replay ref, idempotency key, and no-effect receipt plan ref.

It adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write, no connector send, no connector delete, no connector export,
no attachment download, no model call, no memory write, no context injection,
no execution, no backend route, no Control Center control, no dependency, no
M127 work, no beta release, and no production authority.

Approval refs remain identifiers, not authority. `approval_test_` refs are
denied. M150 remains the planned v1.0.0-alpha target.
