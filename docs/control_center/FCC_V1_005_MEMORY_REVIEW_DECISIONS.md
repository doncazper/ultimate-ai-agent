# FCC-V1-005 Memory Review Decisions

Status: implemented for backend-owned Memory Review decision receipts.
Baseline: v0.102.3 / 0.102.3.

FCC-V1-005 makes Memory Review accept, correct, and reject decisions real
backend-owned receipt state. Memory remains recall, not truth or authority.
These decisions do not write memory records, inject context, sync CRM/accounts,
write connectors, execute actions, call providers, or grant public beta or
production authority.

## Contract

The Memory Review decision contract is
`contract-ref:fcc-v1-005-memory-review-decisions:v1`.

Implemented routes:

- `GET /control-center/memory/review`
- `POST /control-center/memory/review/{candidate_ref}/accept`
- `POST /control-center/memory/review/{candidate_ref}/correct`
- `POST /control-center/memory/review/{candidate_ref}/reject`

Every mutating decision route requires `X-UAA-Idempotency-Key` or
`X-UAA-Idempotency-Ref`. The same key with the same safe payload returns the
prior receipt with `replayed=true`. The same key with a different safe payload
returns a conflict.

## Receipt

`MemoryReviewDecisionReceipt` records safe refs only:

- `candidate_ref`
- `decision_ref`
- `receipt_ref`
- `idempotency_key_ref`
- `payload_fingerprint_ref`
- `evidence_timeline_event_ref`
- `reviewer_ref`
- `source_refs`
- `evidence_refs`
- `blocked_state_refs`
- `created_at`

Accept records reviewed recall only; it is not truth authority and does not
authorize context injection. Correct stores corrected_summary_ref only; raw
corrected content is not stored. Reject preserves the candidate as rejected
review state so stale candidates do not silently return as fresh.

Denied authority flags stay false: no context injection, no source truth
authority, no connector/CRM/account sync, no action execution, and no production
authority.

## Evidence

Evidence Timeline entries answer:

- what was proposed
- what was decided
- what changed
- what remains blocked
- what can be undone or why rollback is not applicable

Receipts and audit refs are durable inspection refs, not memory-write authority.

## Proof

Primary proof lanes:

- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `tests/test_fcc_v1_005_memory_review_decisions.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`

The verifier checks route metadata, idempotency replay/conflict behavior,
receipt shape, rejected-candidate preservation, Evidence Timeline visibility,
release-surface truth, route-status truth, milestone truth, no unsafe UI labels,
and no product overclaims.
