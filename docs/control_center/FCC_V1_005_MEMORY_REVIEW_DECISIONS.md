# FCC-V1-005 Memory Review Decisions

Status: implemented for backend-owned Memory Review decision receipts.
Baseline: v0.104.0 / 0.104.0.

FCC-V1-005 originally made Memory Review accept, correct, and reject decisions
real backend-owned receipt state. FCC-MEM-001 expands that lifecycle with
defer, merge, supersede, and forget-request receipts while preserving the same
authority boundary. Memory remains recall, not truth or authority.
Accept/correct decisions create reviewed recall-only `LocalMemoryStore` records
with safe summaries and refs. Defer/merge/supersede/forget-request are posture
and receipt states only. These decisions do not automatically write memory
beyond reviewed recall-only accept/correct records, delete/export memory,
inject context, sync CRM/accounts, write connectors, execute actions, call
providers, or grant public beta or production authority.

## Contract

The Memory Review decision contract is
`contract-ref:fcc-v1-005-memory-review-decisions:v1`.

Implemented routes:

- `GET /control-center/memory/review`
- `GET /control-center/memory/review/{candidate_ref}/receipt`
- `POST /control-center/memory/review/{candidate_ref}/accept`
- `POST /control-center/memory/review/{candidate_ref}/correct`
- `POST /control-center/memory/review/{candidate_ref}/reject`
- `POST /control-center/memory/review/{candidate_ref}/defer`
- `POST /control-center/memory/review/{candidate_ref}/merge`
- `POST /control-center/memory/review/{candidate_ref}/supersede`
- `POST /control-center/memory/review/{candidate_ref}/forget-request`
- `POST /control-center/memory/review/manual-candidate`

Every mutating decision route requires `X-UAA-Idempotency-Key` or
`X-UAA-Idempotency-Ref`. The same key with the same safe payload returns the
same stored receipt payload. The same key with a different safe payload returns
a conflict.

## Receipt

`MemoryReviewDecisionReceipt` records safe refs only:

- `candidate_ref`
- `decision_ref`
- `receipt_ref`
- `idempotency_key_ref`
- `payload_fingerprint_ref`
- `evidence_timeline_event_ref`
- `approval_ref`
- `approval_status`
- `approval_reason_refs`
- `reviewed_recall_record_ref` for accept/correct only
- `corrected_summary_ref` and bounded `corrected_safe_summary` for correct only
- `defer_ref`, `merge_ref`, `supersede_ref`, or `forget_request_ref` when
  those posture receipts are recorded
- `suppressed_recall_record_refs` when a terminal decision suppresses prior
  recall projection without deleting/exporting memory
- `reviewer_ref`
- `source_refs`
- `evidence_refs`
- `blocked_state_refs`
- `created_at`

Accept records reviewed recall only; it is not truth authority and does not
authorize context injection. Correct stores corrected_summary_ref and bounded
corrected_safe_summary, then writes a reviewed recall-only safe-summary record;
raw corrected content is not stored. Reject preserves the candidate as rejected
review state so stale candidates do not silently return as fresh and does not
create a recall record. Defer, merge, supersede, and forget-request preserve
auditable posture without deleting, exporting, or silently rewriting memory.
Reject/merge/supersede/forget-request suppress prior recall projections by
marking local recall records inactive; the records remain inspectable audit
state and are not deleted.
The Memory Workbench `lifecycle_posture` read model and
`scripts/inspect_memory_merge_supersede_posture.py` expose duplicate,
stale/recheck, conflict, corrected, merged, superseded, and forget-request
posture as safe refs and receipt refs only.

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

Receipts, audit refs, and reviewed recall record refs are durable inspection
refs, not truth authority, hidden context, connector authority, or execution
authority.

## Proof

Primary proof lanes:

- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `tests/test_fcc_mem_001_memory_workbench.py`
- `scripts/inspect_memory_merge_supersede_posture.py`
- `tests/test_fcc_v1_005_memory_review_decisions.py`
- `tests/test_governed_memory_l2_factual_graph_temporal_index.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`

The verifier checks route metadata, idempotency replay/conflict behavior,
receipt shape, rejected-candidate preservation, Evidence Timeline visibility,
release-surface truth, route-status truth, milestone truth, no unsafe UI labels,
and no product overclaims.
