# Governed Cognitive Memory Spine Codex Handoff

Status: active implementation handoff.
Baseline: v0.103.0 / 0.103.0.

This handoff adapts PR #36 onto current main. Do not merge the branch blindly:
the PR docs were conceptually aligned but behind current repo truth, and main
already contains FCC-V1-005 Memory Review decisions.

## Current Files

Primary runtime/storage files:

- `src/ultimate_ai_agent/core/memory/review_decisions.py`
- `src/ultimate_ai_agent/core/memory/local_store.py`
- `src/ultimate_ai_agent/core/memory/provider.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `src/ultimate_ai_agent/core/control_center/founder_loop.py`
- `src/ultimate_ai_agent/api/founder_loop.py`

Primary docs/proof files:

- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md`
- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`
- `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`
- `scripts/verify_governed_cognitive_memory_spine_v1.py`
- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `tests/test_fcc_v1_005_memory_review_decisions.py`

There is no `src/ultimate_ai_agent/core/storage.py` file. Founder Loop storage
lives under `src/ultimate_ai_agent/core/storage/founder_loop.py`.

## Phase 1 Scope

Implemented/hardened routes:

- `GET /control-center/memory/review`
- `GET /control-center/memory/review/{candidate_ref}/receipt`
- `POST /control-center/memory/review/{candidate_ref}/accept`
- `POST /control-center/memory/review/{candidate_ref}/correct`
- `POST /control-center/memory/review/{candidate_ref}/reject`

Accept/correct must:

- require idempotency
- create a durable `MemoryReviewDecisionReceipt`
- create `reviewed_recall_record_ref`
- write one reviewed recall-only `LocalMemoryStore` record with safe refs
- emit Evidence Timeline state
- keep memory as recall only

Reject must:

- require idempotency
- create a durable receipt
- preserve the rejected candidate
- create no recall record
- keep promotion and recall blocked for that candidate

## Blocked Capabilities

Keep these blocked unless a later accepted milestone grants the exact authority
with tests, receipts, rollback or safe-disable posture, and Evidence Timeline
proof:

- automatic memory writes
- hidden context injection
- truth authority
- approval authority
- action execution
- connector writes
- CRM or account sync
- provider/model calls
- browser automation
- shell/subprocess behavior
- delete/export execution
- public beta, public distribution, or production authority

## Next Safe Prompt

After Phase 1 is merged and stable, the next safe phase is Phase 2 L1 Hot Local
Memory Index.

Prompt shape:

```text
Read AGENTS.md, docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md,
docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md,
docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md, and the current
memory provider/store files.

Implement Phase 2 L1 Hot Local Memory Index only. Add recall preview/index
inspection contracts for reviewed recall-only records. Do not add hidden context
injection, automatic writes, provider/model calls, embeddings/vector
dependencies, connector writes, CRM/account sync, action execution, public beta,
or production authority.
```
