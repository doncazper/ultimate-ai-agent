# v0.41.0 README Import

Status: historical release packet after acceptance.
Release: **v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence**.

v0.41.0 adds review-only approval capture for exact redacted file review
packets. The release persists safe refs only, supports review-only approval and
denial records, enforces idempotency/replay protection, exposes exactly one
capture route, and keeps all raw/context/memory/export/execution authority
blocked.

## Boundaries

- review-only approval capture.
- safe-ref-only persistence.
- exact packet binding required.
- no raw file access.
- no raw content storage.
- no full-file read.
- no unredacted preview.
- no context proposal.
- no context injection.
- no memory write.
- no export.
- no execution.
- no dependencies.

M38 remains planned/provisional.
