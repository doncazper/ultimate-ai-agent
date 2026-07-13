# ADR-0057: Existing Store Migration And Compatibility

Status: Accepted migration policy; no cutover authorized by ECO-000.

## Decision

Founder Loop SQLite, Work Board JSON, local-task receipts, CRM snapshot/JSONL,
memory stores, planning records, and connector metadata remain historical truth
in their current contracts. ECO-001 and app milestones must use versioned,
read-only compatibility readers and previewed idempotent migrations.

Every cutover requires: source fingerprint, record counts, duplicate/conflict
report, backup ref, destination version, dry-run diff, operator decision ref,
idempotency ref, cutover receipt, rollback/recovery posture, and post-cutover
integrity evidence. Unsupported or corrupt input fails closed. No source store
is deleted or reinterpreted automatically.

## Consequences

Current Work Board cards become projection or standalone BoardItem candidates;
local-task records become Task migration candidates; CRM M2 records remain
compatibility inputs; calendar connector contracts remain metadata evidence,
not Event data.

## Rejected

In-place schema reinterpretation, import-on-read, silent deduplication, and
deleting a source store immediately after migration were rejected.
