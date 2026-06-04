# File Review Approval Persistence

Status: active M37 persistence documentation.
Release: v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence.

M37 introduces narrow review-only persistence for file review approvals and
denials. The persisted record contains safe refs, reviewer actor ref, decision
kind, status, idempotency key, safe reason, receipt plan ref, metadata refs, and
safe metadata only.

Persistence is intentionally not a memory write and not context injection. It
does not persist raw file content, full-file content, unredacted preview, raw
absolute paths, private local paths, exported files, model/provider payloads,
credentials, cookies, or secret-like values.

The store enforces idempotency by key. Replaying the same safe record is
idempotent. Replaying the key with changed binding refs is denied as a replay
mismatch.

M37 persistence is not production authority. M38 remains planned/provisional.
