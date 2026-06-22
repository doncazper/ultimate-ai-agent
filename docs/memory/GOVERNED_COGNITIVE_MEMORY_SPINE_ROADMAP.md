# Governed Cognitive Memory Spine V1 Roadmap

Status: proposed phased roadmap

## Phase 1 — FCC-V1-005 Memory Review Decisions

Make Memory Review accept/correct/reject backend-owned, idempotent, receipt-backed, and Evidence-visible. Accept/correct create reviewed local recall records only. Reject blocks promotion.

This is the first phase because it turns the current review-only posture into real, governed recall without adding hidden context injection or broader runtime authority.

## Phase 2 — L1 Hot Local Memory Index

Index reviewed recall records in a local hot-memory store using safe summaries, recency, access counts, source/evidence/receipt refs, and optional SQLite FTS5 with visible fallback.

Do not add embeddings, vector dependencies, or external memory services in this phase.

## Phase 3 — L2 Graph / Temporal / Triple Index

Create deterministic triples, entity refs, and temporal facts from reviewed memory records. Every derived item must point back to memory, evidence, and receipt refs.

Conflicting, stale, duplicate, low-confidence, or missing-evidence facts must be surfaced, not silently resolved.

## Phase 4 — Retrieval Router and Fusion

Route memory recall through hot, keyword, graph, temporal, and identity/session lanes. Return explainable traces and safe recall previews only.

No prompt injection, no provider/model calls, and no automatic action generation.

## Phase 5 — L3 Identity / Session Representations

Create UAA-native workspace/peer/session representation candidates for preferences, commitments, session summaries, project context, relationship state, and communication style.

Do not add Honcho as a dependency and do not copy AGPL code. Representations remain review-required and cannot be injected automatically.

## Phase 6 — Context-Pack Proposals

Generate reviewable context-pack proposals with selection reasons, source/evidence/receipt refs, stale/conflict posture, missing-evidence posture, and blocked states.

A context pack proposal is a preview. It is not hidden prompt context and it is not an apply/send-to-model operation.

## Proof lane

Add and evolve `scripts/verify_governed_cognitive_memory_spine_v1.py` to verify:

- route metadata and side-effect classification;
- idempotency posture for memory review mutations;
- decision receipts and Evidence Timeline events;
- no raw/private durable leaks;
- no automatic writes or hidden context injection;
- docs/schema/currentness alignment;
- focused tests for each implemented phase.
