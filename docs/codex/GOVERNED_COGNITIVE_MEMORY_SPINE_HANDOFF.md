# Governed Cognitive Memory Spine Codex Handoff

Status: active implementation handoff.
Baseline: v0.103.0 / 0.103.0.

This handoff adapts PR #36 onto current main. Do not merge the branch blindly:
the PR docs were conceptually aligned but behind current repo truth, and main
already contains FCC-V1-005 Memory Review decisions.

## Current Files

Primary runtime/storage files:

- `src/ultimate_ai_agent/core/memory/review_decisions.py`
- `src/ultimate_ai_agent/core/memory/l1_index.py`
- `src/ultimate_ai_agent/core/memory/l2_index.py`
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
- `tests/test_governed_memory_l1_hot_index.py`
- `tests/test_governed_memory_l2_factual_graph_temporal_index.py`

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

## Phase 2 Scope

Implemented/hardened route:

- `GET /control-center/memory/l1-index`

The L1 hot local memory index is a backend-backed, read-only derived preview
over reviewed recall-only `LocalMemoryStore` records created by Phase 1
accept/correct decisions. It returns safe summaries, match reasons, source refs,
evidence refs, receipt refs, event refs, metadata refs, tag refs, and blocked
state refs. It skips unreviewed, rejected, raw/private, context-pack-eligible,
or authority-bearing records.

Phase 2 does not add embeddings, vector DB, semantic search, background
indexing, automatic memory writes, hidden context injection, provider/model
calls, connector writes, CRM/account sync, action execution, public beta, or
production authority.

## Phase 3 Scope

Implemented/hardened route:

- `GET /control-center/memory/l2-index`

The L2 factual/graph/temporal index is a backend-backed, read-only derived
preview over Phase 2 L1 hot local memory previews. It returns deterministic
safe-ref projections for factual, relationship, and temporal inspection with
source refs, evidence refs, receipt refs, memory record refs, reviewed recall
refs where available, derivation reasons, stale/conflict posture, and blocked
state refs.

Phase 3 does not add truth authority, hidden context injection, embeddings,
vector DB, semantic search, LLM/entity extraction, background indexing,
automatic memory writes, context-pack injection, provider/model calls,
connector writes, CRM/account sync, action execution, public beta, or
production authority.

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
- embeddings, vector DB, semantic search, or LLM/entity extraction
- browser automation
- shell/subprocess behavior
- delete/export execution
- public beta, public distribution, or production authority

## Next Safe Prompt

After Phase 3 is merged and stable, the next safe phase is Phase 4 L3 Identity /
Session / Preference / Commitment Modeling.

Prompt shape:

```text
Read AGENTS.md, docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md,
docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md,
docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md, and the current
memory provider/store files.

Implement Phase 4 L3 Identity / Session / Preference / Commitment Modeling
only. Build proposal-only identity/session/preference/commitment contracts from
reviewed L2 inspection refs. Do not add account sync, CRM writes, truth
authority, hidden context injection, automatic writes, provider/model calls,
connector writes, action execution, public beta, or production authority.
```
