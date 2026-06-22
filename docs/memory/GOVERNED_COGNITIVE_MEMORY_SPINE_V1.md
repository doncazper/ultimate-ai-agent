# Governed Cognitive Memory Spine V1

Status: proposed implementation spine

## Purpose

The Governed Cognitive Memory Spine V1 turns the existing UAA memory contracts into a real, receipt-backed, local-first memory capability while preserving UAA's core rule: **memory is recall, not authority**.

The spine is not a single database and it is not a vague "better memory" feature. In UAA, the spine means this governed pipeline:

```text
safe memory candidate
  -> source/provenance/evidence envelope
  -> Memory Review decision
  -> durable receipt + Evidence Timeline event
  -> reviewed local recall record
  -> hot / factual / identity indexes
  -> retrieval trace
  -> recall preview or context-pack proposal
```

## Design synthesis

The spine borrows ideas from three memory systems without importing them as required dependencies in V1:

- Holographic-like L1: local, fast, private hot-memory recall over reviewed safe summaries and structured triples.
- Hindsight-like L2: entity/relation/time indexing, factual recall, graph/temporal retrieval, and explainable fusion.
- Honcho-like L3: workspace/peer/session representations, preferences, commitments, relationship context, and session summaries.

The important implementation rule is that UAA should use these ideas through UAA-native contracts, not by copying external systems into the runtime.

## V1 authority boundary

Allowed:

- review memory candidates;
- accept/correct/reject with receipts;
- store accepted/corrected safe summaries as reviewed local recall;
- index reviewed memories;
- retrieve explainable recall previews;
- propose context packs for review;
- surface stale/conflict/missing-evidence posture;
- bind memory refs into Today, Action Inbox, Evidence Timeline, and Weekly Review.

Denied:

- automatic memory writes;
- hidden context injection;
- source truth authority;
- approval/execution authority;
- connector/CRM/account writes;
- provider/model calls;
- raw prompt/response/provider payload/transcript/source body/path/log storage;
- production/public beta/distribution claims.

## Phases

1. FCC-V1-005 Memory Review Decisions.
2. L1 Hot Local Memory Index.
3. L2 Graph / Temporal / Triple Index.
4. Retrieval Router and Fusion.
5. L3 Identity / Session Representations.
6. Context-Pack Proposals, not injection.

Each phase must land as a scoped, test-backed, verifier-backed slice. Do not implement all phases in one patch unless a maintainer intentionally asks for a large branch.

## First implementation bridge

The first real implementation target is **FCC-V1-005 Memory Review Decisions**.

That means Memory Review accept/correct/reject becomes backend-owned, idempotent, append-first, receipt-backed, and Evidence-visible. Accept/correct may create reviewed local recall records through the existing memory provider or `LocalMemoryStore`; reject must preserve the rejection and block promotion.

Accepted memory remains reviewed recall only. It is not truth, approval, execution authority, connector authority, or automatic prompt context.

## Output types to converge on

Suggested UAA-native outputs:

```text
MemoryReviewDecisionReceipt
ReviewedRecallRecord
HotMemoryIndexEntry
MemoryTripleRef
MemoryTemporalFactRef
MemoryRetrievalTrace
MemoryContextPackProposal
MemoryDerivedActionProposal
MemoryEvidenceEvent
```

Names may be adapted to existing repo conventions, but the authority boundary may not be weakened.
