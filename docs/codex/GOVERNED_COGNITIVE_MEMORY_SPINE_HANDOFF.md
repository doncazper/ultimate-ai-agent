# Governed Cognitive Memory Spine V1 — Codex Handoff

Status: Codex prompt pack and implementation contract

Use this document as the primary Codex entrypoint for the Governed Cognitive Memory Spine V1. It intentionally defines the term in repo-local language so Codex does not interpret the assignment as a vague instruction to "build better memory."

## One-sentence definition

The **Governed Cognitive Memory Spine** is UAA's local-first, review-gated memory pipeline that converts safe, provenance-linked memory candidates into reviewed recall records, indexes those records across hot/local, factual/temporal/graph, and identity/session layers, and returns explainable recall previews or context-pack proposals without treating memory as truth, approval, execution authority, or hidden prompt context.

## Current repo context Codex must preserve

Before editing, inspect and preserve the contracts in these files:

```text
README.md
pyproject.toml
docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md
docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md
docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md
docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md
docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md
docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md
src/ultimate_ai_agent/core/memory/__init__.py
src/ultimate_ai_agent/core/memory/provider.py
src/ultimate_ai_agent/core/memory/local_store.py
src/ultimate_ai_agent/core/memory/store.py
src/ultimate_ai_agent/core/memory/retrieval.py
src/ultimate_ai_agent/core/memory/manifests.py
src/ultimate_ai_agent/core/storage.py
```

The existing repo already has source/provenance envelopes, review decision metadata, business memory quality states, cross-surface intake, memory-to-loop binding, provider abstractions, local memory store, keyword retrieval, redaction, and manifest posture. The spine should extend those contracts; it should not bypass them.

## Design source synthesis

This spine combines three memory ideas in a UAA-native way:

- **Holographic-like L1 hot memory:** local, fast, private, read-your-writes recall over reviewed safe summaries and structured triples.
- **Hindsight-like L2 factual memory:** entity/relation/time normalization, graph/temporal retrieval, conflict/stale/missing-evidence handling, and multi-lane fusion.
- **Honcho-like L3 identity memory:** workspace/peer/session representations, preferences, commitments, communication style, relationship context, and session summaries.

Do **not** import or vendor Hindsight, Honcho, or Holographic in V1. Use their ideas, not their code. Keep UAA's safety model stronger than any external project.

## Non-negotiable boundaries

- Memory is recall, not authority.
- Accepted memory is reviewed recall, not truth, not approval, not automatic context injection.
- No raw prompt, raw response, raw provider payload, raw transcript, raw file body, raw local path, raw log, username, hostname, credential, token, or secret-like value in durable state.
- No automatic writes in V1.
- No provider/model calls in V1.
- No connector writes, account sync, CRM sync, shell execution, browser import, or production/public beta/distribution claims.
- Required runtime dependencies should not change in the first implementation slices.
- All mutations must be backend-owned, idempotent, append-first, auditable, receipt-backed, and evidence-visible.

## Spine pipeline

```text
Surface event or user note
  -> safe summary + source/provenance/evidence refs
  -> cross-surface memory intake proposal
  -> Memory Review accept/correct/reject decision
  -> durable decision receipt + Evidence Timeline event
  -> reviewed local recall record
  -> L1 hot local index
  -> L2 factual / graph / temporal indexes
  -> L3 identity / session representation candidates
  -> retrieval router + fusion scorer
  -> recall preview or context-pack proposal
  -> Today / Actions / Evidence / Weekly Review surfaces
```

## Implementation order

Implement in the following order. Stop after each phase with focused tests and verifier evidence.

### Phase 1 — FCC-V1-005 Memory Review Decisions

Make Memory Review accept/correct/reject real backend-owned behavior:

```text
GET  /control-center/memory/review
POST /control-center/memory/review/{candidate_ref}/accept
POST /control-center/memory/review/{candidate_ref}/correct
POST /control-center/memory/review/{candidate_ref}/reject
GET  /control-center/memory/review/{candidate_ref}/receipt
```

Accept/correct should create reviewed local recall records through `LocalMemoryStore` or the repo's current provider boundary. Reject should preserve a durable rejection decision and block promotion. All decisions need receipts, idempotency, safe refs, evidence events, and tests.

#### Phase 1 route requirements

All mutating POST routes must require idempotency using the repo's established idempotency header/body/ref pattern. Duplicate requests with the same idempotency key must return the prior receipt/result. Conflicting duplicate payloads with the same idempotency key must be rejected.

Suggested models, adapted to repo conventions:

```text
MemoryReviewDecisionRuntime
MemoryReviewDecisionReceipt
MemoryReviewDecisionRequest
MemoryReviewDecisionResult
MemoryReviewDecisionEvent
```

Required fields:

```text
candidate_ref
decision: accept | correct | reject
corrected_safe_summary_ref or corrected_safe_summary, only for correct
source_refs
provenance_refs
evidence_refs
reviewer_ref
receipt_ref
idempotency_ref
blocked_state_refs
created_at
safe_summary_ref or safe_summary
review_state
quality_state_refs
stale_state
```

Bind payloads back to existing contracts when available:

```text
contract-ref:memory-source-provenance:v1
contract-ref:memory-review-decision:v1
contract-ref:business-memory-quality-controls:v1
contract-ref:cross-surface-memory-intake:v1
```

#### Phase 1 storage behavior

Use existing storage patterns. Prefer extending `FounderLoopRepository` or existing local state repositories instead of creating orphan state.

Required behavior:

- append a decision event for every accept/correct/reject;
- generate a receipt ref for every decision;
- store idempotency replay markers;
- accepted/corrected memory is written through existing `LocalMemoryStore` or the memory provider abstraction as reviewed recall only;
- rejected candidate remains durable and excluded from promotion;
- all stored content is safe-summary/safe-ref only.

When accepting, the provider write request should resemble this shape:

```text
MemoryProviderWriteRequest(
  request_id=...,
  provider_ref="local_dev_memory",
  memory_kind=...,
  safe_summary=...,
  source_refs=...,
  evidence_refs=...,
  receipt_refs=[receipt_ref],
  user_reviewed=True,
  automatic_write=False,
  context_pack_eligible=False,
)
```

When correcting, store the corrected safe summary as the reviewed recall record, preserve source/evidence/provenance refs, record correction refs and receipt refs, and never store raw correction/source text beyond safe summary constraints.

When rejecting, do not write a recall record. Preserve the decision receipt and update review queue state so the candidate cannot silently reappear as pending unless explicitly re-proposed.

#### Phase 1 evidence behavior

Add Evidence Timeline events or extend the existing evidence history mechanism with:

```text
memory_review_decision_recorded
```

Evidence should answer:

- what candidate was reviewed;
- what decision was recorded;
- which source/evidence/provenance refs were used;
- which receipt was created;
- what changed;
- what did not change;
- what remains blocked.

### Phase 2 — L1 Hot Local Memory Index

Add a local hot-memory index over reviewed recall records only. Use safe summaries, refs, recency, access counters, and optional SQLite FTS5 with visible fallback. No embeddings dependency in V1.

Suggested files:

```text
src/ultimate_ai_agent/core/memory/hot_index.py
tests/test_memory_hot_index.py
```

Suggested tables if SQLite is used:

```text
memory_hot_entries(memory_id, safe_summary, memory_kind, trust_score, confidence_score, created_at, updated_at, last_seen_at, access_count, refs_json)
memory_hot_fts(memory_id, safe_summary)
```

If FTS5 is unavailable, the system must degrade visibly and use deterministic keyword scoring.

### Phase 3 — L2 Graph / Temporal / Triple Index

Add deterministic entity/triple/temporal indexing from reviewed safe summaries and metadata refs. Every derived triple/fact must carry source memory/evidence/receipt refs. Conflicts and stale facts must be surfaced, not silently resolved.

Suggested files:

```text
src/ultimate_ai_agent/core/memory/triples.py
src/ultimate_ai_agent/core/memory/temporal.py
tests/test_memory_triples.py
tests/test_memory_temporal_facts.py
```

Suggested outputs:

```text
MemoryEntityRef
MemoryTripleRef
MemoryTemporalFactRef
MemoryConflictRef
```

No LLM extraction/model calls in this phase. Use deterministic rules and explicit refs only.

### Phase 4 — Retrieval Router and Fusion

Replace or extend keyword-only recall with an explainable router that can query hot, keyword, graph, temporal, and identity/session lanes. Return retrieval traces and reason codes. Do not inject into prompts.

Suggested files:

```text
src/ultimate_ai_agent/core/memory/retrieval_router.py
src/ultimate_ai_agent/core/memory/fusion.py
tests/test_memory_retrieval_router.py
tests/test_memory_fusion.py
```

Fusion should consider:

```text
keyword_score
hot_score
graph_score
temporal_score
identity_score
recency_score
trust_score
confidence_score
review_state_bonus
stale_penalty
conflict_penalty
missing_evidence_penalty
```

Return safe recall previews only, plus retrieval traces explaining why each result appeared.

### Phase 5 — L3 Identity / Session Representations

Add UAA-native workspace/peer/session representation candidates inspired by Honcho. No Honcho code import. Representations are reviewable candidates or reviewed recall records, not automatic truth.

Suggested files:

```text
src/ultimate_ai_agent/core/memory/identity.py
src/ultimate_ai_agent/core/memory/sessions.py
src/ultimate_ai_agent/core/memory/representations.py
tests/test_memory_identity_representations.py
```

Suggested models:

```text
MemoryWorkspaceRef
MemoryPeerRef
MemorySessionRef
MemoryMessageRef
PeerRepresentationCandidate
SessionSummaryCandidate
ProjectRepresentationCandidate
RelationshipRepresentationCandidate
ConclusionCandidate
```

Representation candidates must carry source/evidence/provenance refs, review-required posture, stale/conflict posture, and blocked-state refs.

### Phase 6 — Context-Pack Proposals

Add context-pack proposal generation as a safe preview: why these memories were selected, what they would help with, source/evidence refs, risk/stale/conflict posture, and blocked-state refs. Do not implement automatic context injection.

Suggested files:

```text
src/ultimate_ai_agent/core/memory/context_pack.py
tests/test_memory_context_pack_proposals.py
```

A context pack proposal can say:

```text
These reviewed recall records may be useful for this user-visible task.
```

It cannot silently insert the records into a prompt, call a model, execute an action, sync an account, write a connector, or claim authority.

## Chained Codex prompts

Use these as separate Codex sessions or sequential tasks. Do not ask Codex to implement every phase in one patch unless you intentionally want a large branch.

### Prompt 0 — Currentness and plan alignment

```text
Read docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md, docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md, docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md, and docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md. Do not implement code yet. Produce a concise implementation plan for Governed Cognitive Memory Spine V1 as defined in these docs. Confirm which existing memory contracts/models/routes/storage patterns should be reused. Identify exact files to modify for Phase 1 only. Do not add dependencies or expand authority.
```

### Prompt 1 — Implement Phase 1

```text
Implement Phase 1 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md exactly. Stop after tests/verifiers for Phase 1 pass. Preserve all blocked states. Accept/correct must create reviewed recall records only; reject must preserve rejection and block promotion. No context injection.
```

### Prompt 2 — Hardening pass for Phase 1

```text
Review the Phase 1 implementation for authority creep, raw/private content leaks, idempotency gaps, route metadata drift, missing evidence events, missing receipt refs, and React-only state. Add tests and verifier coverage for any gap. Do not start Phase 2.
```

### Prompt 3 — Implement Phase 2

```text
Implement Phase 2 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md. Use stdlib SQLite/FTS5 where available and a visible fallback where not. Index reviewed safe summaries only. Integrate with Phase 1 accept/correct. No embeddings dependency. No raw content. No context injection.
```

### Prompt 4 — Implement Phase 3

```text
Implement Phase 3 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md. Add deterministic entity/triple/temporal indexing from reviewed memory only. Every derived fact must carry source memory, evidence, and receipt refs. No LLM/model calls. Surface stale/conflict/missing-evidence posture.
```

### Prompt 5 — Implement Phase 4

```text
Implement Phase 4 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md. Add deterministic query classification, lane fan-out, explainable fusion scoring, retrieval traces, and safe recall previews. Reuse existing keyword scoring as one lane. No prompt/context injection.
```

### Prompt 6 — Implement Phase 5

```text
Implement Phase 5 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md. Add UAA-native workspace/peer/session representation candidates. Do not add Honcho as a dependency or copy AGPL code. Representations remain review-required and cannot be injected automatically.
```

### Prompt 7 — Implement Phase 6

```text
Implement Phase 6 from docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md. Add safe context-pack proposal previews with source/evidence/receipt refs and retrieval traces. Do not add inject/apply/send-to-model behavior. No hidden prompt context.
```

### Prompt 8 — Final proof lane

```text
Add or update scripts/verify_governed_cognitive_memory_spine_v1.py so it verifies the whole spine: Phase 1 decisions, L1 hot index, L2 triples/temporal facts, retrieval router/fusion, L3 representation candidates, context-pack proposals, no raw/private leaks, no automatic context injection, no new unapproved dependencies, and docs/schema/currentness. Run focused tests and foundation checks. Report remaining blocked capabilities explicitly.
```

## Required proof commands

At minimum, add or update focused tests and verifiers. Prefer commands like:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_v1_005_memory_review_decisions.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_memory_hot_index.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_memory_retrieval_router.py
PYTHONPATH=src .venv/bin/python scripts/verify_governed_cognitive_memory_spine_v1.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
```

Use actual repo test conventions if names differ.

## Final response expectations for Codex

When done with a phase, Codex should report:

- files changed;
- routes/models/storage added;
- authority boundaries preserved;
- tests/verifiers run;
- what remains blocked;
- next safe phase.

## PR description template

```markdown
## Summary

Adds/implements the scoped Governed Cognitive Memory Spine V1 slice for [phase].

## Scope

- [ ] Phase 1: Memory Review accept/correct/reject decisions
- [ ] Phase 2: L1 hot local memory index
- [ ] Phase 3: L2 graph/temporal/triple index
- [ ] Phase 4: retrieval router/fusion
- [ ] Phase 5: identity/session representations
- [ ] Phase 6: context-pack proposals

## Authority boundaries preserved

- No automatic memory writes unless explicitly reviewed in Phase 1 accept/correct.
- No hidden context injection.
- No source truth authority.
- No connector/account/CRM writes.
- No provider/model calls.
- No raw/private durable content.
- No production/public beta/distribution claim.

## Tests / proof

- [ ] Focused pytest lane
- [ ] Memory spine verifier
- [ ] OpenAPI/manifest checks where routes changed
- [ ] Documentation integrity

## Remaining blocked capabilities

List all blocked capabilities explicitly.
```
