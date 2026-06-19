# Connector Write Dry-Run Planner

Checkpoint M127 adds Connector Write Dry-Run Planner contracts. It is
deterministic, local, review-only, dry-run-only, exact-bound, actor-bound,
user-bound, workspace-bound, replay-safe, revocable, and safe refs only.

The dry-run plan is bound to an already-captured M126 connector approval capture
decision and its M125 Connector Read-Only Runtime record. Approval refs remain
identifiers, not authority. The planner may record a proposed connector write
intent for governed review using safe write target refs, safe payload summary
refs, dry-run operation allowlist refs, redaction refs, audit refs, replay refs,
and idempotency keys.

M127 denies approval_test_ refs, denied M126 approvals, rejected M126 approvals,
missing approval records, expired dry-run requests, revoked dry-run requests,
replayed dry-run nonces, actor mismatch, user mismatch, workspace mismatch,
runtime ref mismatch, source review ref mismatch, source operation mismatch,
allowlist mismatch, metadata preview mismatch, unsafe write target refs, unsafe
payload summary refs, and unallowlisted dry-run operation refs.

M127 adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write execution, no connector send execution, no connector delete
execution, no connector export, no connector bulk export, no attachment
download, no model call, no memory write, no context injection, no execution,
no backend route, no Control Center control, no dependency, no M128 work, no
broad autonomy, no beta release, and no production authority.

M128 remains future. M150 remains the planned v1.2.0-alpha target.
