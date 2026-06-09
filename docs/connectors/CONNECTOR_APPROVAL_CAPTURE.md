# Connector Approval Capture

Checkpoint M126 adds Connector Approval Capture contracts. It is deterministic,
local, review-only, exact-bound, replay-safe, revocable, and safe refs only. It
captures a connector approval or denial over an already-reviewed M125 Connector
Read-Only Runtime record.

The capture record is exact-bound to the M125 connector read-only runtime ref,
source messages connector contract review ref, baseline ref, actor-bound ref,
user-bound ref, workspace-bound ref, connector scope refs, connector allowlist
refs, operation allowlist refs, redacted metadata preview refs, audit ref,
replay ref, idempotency key, and no-effect receipt plan.

Approval refs remain identifiers, not authority. `approval_test_` refs are never
runtime authority and are denied. Expired approvals, revoked approvals, replayed
approval nonces, actor mismatch, user mismatch, workspace mismatch, runtime ref
mismatch, source review ref mismatch, allowlist mismatch, operation mismatch,
and metadata preview mismatch fail closed.

M126 adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write, no connector send, no connector delete, no connector export,
no connector bulk export, no attachment download, no model call, no memory
write, no context injection, no execution, no backend route, no Control Center
control, no dependency, no M127 work, no beta release, and no production
authority.

M127 remains future. M150 remains the planned v1.0.0-alpha target.
