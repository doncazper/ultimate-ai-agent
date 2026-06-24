# FCC-MEM-001 Memory Workbench V1

Status: implemented local functional memory workbench slice.
Baseline: v0.104.0 / 0.104.0 plus FCC-MEM-001.

FCC-MEM-001 makes Memory Review more usable and auditable without expanding
runtime authority. It unifies review candidates, lifecycle receipts, reviewed
recall-only records, L1/L2/L3 projection refs, context-pack proposal refs, and
quality posture into one backend-owned Memory Workbench read model.

This is local product behavior, not production authority. Memory remains
governed recall; it is not source truth, approval authority, execution
authority, or hidden prompt context.

## Implemented

- `GET /control-center/memory/workbench` returns a backend-owned safe-ref-only
  read model with groups for `needs_review`, `conflict`, `duplicate`, `stale`,
  `missing_evidence`, `reviewed`, and `rejected`.
- `GET /control-center/memory/search` performs read-only safe-ref filtering by
  kind, source ref, project/person/org/deal refs, review state, quality state,
  stale state, and conflict state.
- `POST /control-center/memory/review/manual-candidate` creates a manual
  safe-summary review candidate only; it does not create a recall record.
- Memory Review lifecycle receipts now include `accept`, `correct`, `reject`,
  `defer`, `merge`, `supersede`, and `forget_request`.
- Correction receipts record both `corrected_summary_ref` and bounded
  `corrected_safe_summary`; terminal reject/merge/supersede/forget-request
  receipts suppress prior recall projections without deleting/exporting memory.
- Deterministic quality detection flags duplicate, conflict, stale, and
  missing-evidence posture with explainable `quality_reason_refs`.
- Ranking includes `why_shown_refs` based on review state, source/evidence
  presence, recency, loop relevance, unresolved action posture, and tags.
- `/memory` surfaces workbench health, grouped items, why-shown refs, quality
  refs, and backend lifecycle controls for review-queue items.
- `scripts/dev/uaa_founder_loop.py` can inspect workbench/search/receipts and
  record manual candidates or lifecycle decisions from CLI.

## Partial / Planned UI Follow-Up

- Merge and supersede UX can submit backend-owned peer refs; an explicit
  multi-select picker over two or more local candidates remains planned. The
  backend already records merge/supersede receipts and marks referenced local
  queue records as merged/superseded posture without deletion.

## Explicitly Blocked

- No memory delete execution.
- No memory export execution.
- No semantic search, vector DB, embeddings, or provider/model extraction.
- No connector writes, CRM/account sync, or external source writes.
- No shell/subprocess execution or browser automation.
- No action execution from memory-derived proposals.
- No hidden or automatic context injection.
- No public beta, public distribution, production readiness, or production
  authority.

## Evidence And Tests

Primary proof lanes:

- `tests/test_fcc_mem_001_memory_workbench.py`
- `scripts/verify_fcc_mem_001_memory_workbench.py`
- `tests/test_fcc_v1_005_memory_review_decisions.py`
- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `scripts/dev/uaa_founder_loop.py memory-workbench`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `docs/control_center/route_status_manifest.json`
- `docs/control_center/release_surface_manifest.json`

## Operator Path

1. Inspect the queue with `memory-workbench`.
2. Filter safe refs with `memory-search`.
3. Add a manual safe-summary candidate with `memory-manual-candidate` when
   evidence or missing-evidence posture is explicit.
4. Record a lifecycle receipt with `record-memory-decision`.
5. Inspect receipts with `memory-receipts`.
6. Use `/memory`, Today, Actions, Briefing, and Evidence as readable surfaces
   over the same backend-owned refs.
