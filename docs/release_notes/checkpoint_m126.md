# Checkpoint M126 - Connector Approval Capture

Checkpoint M126 adds deterministic local connector approval capture contracts.
The capture is review-only, exact-bound, safe refs only, actor-bound,
user-bound, workspace-bound, replay-safe, revocable, and bound to M125 Connector
Read-Only Runtime records.

The product baseline remains v1.7.2. M126 uses the checkpoint label
`checkpoint-m126`; M150 remains the planned v1.0.0-alpha product target.

M126 denies `approval_test_` refs, expired approvals, revoked approvals,
replayed approval nonces, actor mismatch, user mismatch, workspace mismatch,
runtime ref mismatch, source review ref mismatch, allowlist mismatch, operation
mismatch, and metadata preview mismatch. Approval refs remain identifiers, not
authority.

M126 adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write, no connector send, no connector delete, no connector export,
no connector bulk export, no attachment download, no model call, no memory
write, no context injection, no execution, no backend routes, no Control Center
controls, no dependencies, no M127 work, no beta release, and no production
authority.
