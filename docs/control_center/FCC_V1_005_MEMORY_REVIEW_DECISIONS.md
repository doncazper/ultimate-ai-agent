# FCC-V1-005 Memory Review Decisions

Status: implemented for backend-owned Memory Review decision receipts.
Baseline: v0.104.0 / 0.104.0.

FCC-V1-005 originally made Memory Review accept, correct, and reject decisions
real backend-owned receipt state. FCC-MEM-001 expands that lifecycle with
defer, merge, supersede, and forget-request receipts while preserving the same
authority boundary. Memory remains recall, not truth or authority.
Accept/correct decisions create reviewed recall-only `LocalMemoryStore` records
with safe summaries and refs only after exact approval plus active
`memory/write` AuthorityLease evaluation. Defer/merge/supersede/forget-request
are posture and receipt states when no recall projection exists. When a prior
reviewed recall projection exists, their separate exact lifecycle-suppression
lane may fail-closed suppress that projection without deleting audit history.
These decisions do not automatically write memory beyond reviewed recall-only
accept/correct records, delete/export
memory, inject context, sync CRM/accounts, write connectors, execute actions,
call providers, or grant public beta or production authority.

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
- `POST /control-center/memory/review/{candidate_ref}/expire`
- `POST /control-center/memory/review/{candidate_ref}/forget-request`
- `POST /control-center/memory/review/manual-candidate`

Every mutating decision route requires `X-UAA-Idempotency-Key` or
`X-UAA-Idempotency-Ref`. The same key with the same safe payload returns the
same stored receipt payload. The same key with a different safe payload returns
a conflict.

## Reviewed Recall-Write Authority

The reviewed recall-write capability is implemented only for accept/correct
Memory Review decisions. Its exact approval scope is
`exact-scope-ref:memory-review:accept-correct-reviewed-recall-write`.
Decisions that do not alter recall state use
`exact-scope-ref:memory-review:receipt-state-no-recall-write`. Reject, merge,
supersede, expire, and forget-request use the separate exact
`exact-scope-ref:memory-review:lifecycle-suppression-write` scope only when an
existing reviewed recall record must be suppressed.
The Python Core captures and validates a backend-owned exact
`LocalApprovalAuthority` grant for that scope, candidate ref, decision kind,
payload fingerprint, source/evidence refs, idempotency ref, and reviewer ref
before authority evaluation. It then evaluates the active AuthorityLease store
for `Ask before changes` or stronger with domain `memory` and capability
`write` before a reviewed recall-only `LocalMemoryStore` record is written.
That record is first persisted in a non-retrievable prepared posture. Only
after the decision/replay receipt settles and approval, lease, and safe-disable
posture are freshly revalidated is it activated for recall. A crash before
settlement therefore cannot expose an orphan recall record. Lifecycle
suppression occurs before the terminal projection is reported, so an
interrupted terminal decision cannot leave an active record behind a durable
rejected or expired projection.
Missing or insufficient lease scope returns a readable authority denial with
`blocked-state:memory-review-authority-lease-required`, required mode, domain,
and capability refs, and no recall record write.

Safe-disable and rollback posture are explicit:

- `safe-disable-ref:memory-review:accept-correct-reviewed-recall-write`
- `rollback-ref:memory-review:suppress-reviewed-recall-record`
- `blocked-state:memory-review-rollback-execution-blocked`

Rollback execution is not implemented. Terminal reject, merge, supersede, and
forget-request decisions suppress reviewed recall projection without deleting
audit history. The repo-local CLI parity path is
`scripts/dev/uaa_founder_loop.py record-memory-decision`, with inspection
through `scripts/dev/uaa_founder_loop.py memory-receipts`.

## Receipt

`MemoryReviewDecisionReceipt` records safe refs only:

- `candidate_ref`
- `decision_ref`
- `receipt_ref`
- `idempotency_key_ref`
- `payload_fingerprint_ref`
- `evidence_timeline_event_ref`
- `approval_ref`
- `approval_scope_ref`
- `approval_status`
- `approval_reason_refs`
- `authority_decision_ref` for accept/correct only
- `authority_decision_outcome` for accept/correct only
- `authority_lease_ref` for accept/correct only
- `authority_domain_ref`
- `authority_capability_ref`
- `safe_disable_ref`
- `rollback_ref`
- `safe_disable_posture_ref`
- `rollback_blocker_refs`
- `reviewed_recall_record_ref` for accept/correct only
- `reviewed_recall_write_performed` for accept/correct only
- `corrected_summary_ref` plus a content fingerprint for correct only; the
  bounded corrected safe summary is retained in the governed recall record,
  never in the decision receipt
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
authorize context injection. Correct stores corrected_summary_ref; correction
receipts remain content-free, while the governed recall-only record retains the
bounded corrected safe summary;
raw corrected content is not stored. Reject preserves the candidate as rejected
review state so stale candidates do not silently return as fresh and does not
create a recall record. Defer, merge, supersede, expire, and forget-request preserve
auditable posture without deleting, exporting, or silently rewriting memory.
Reject/merge/supersede/expire/forget-request suppress prior recall projections by
marking local recall records inactive; the records remain inspectable audit
state and are not deleted. That suppression revalidates the exact lifecycle
lane, LocalApprovalAuthority scope, AuthorityLease, safe-disable posture, and
bound record refs immediately before mutation. Expiry marks retention expired
and cannot reactivate recall.
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
receipt shape, AuthorityLease denial/proof behavior, rejected-candidate
preservation, Evidence Timeline visibility, release-surface truth, route-status
truth, milestone truth, no unsafe UI labels, and no product overclaims.
