# Governed Cognitive Memory Spine Roadmap

Status: active phased roadmap.
Baseline: v0.103.0 / 0.103.0.

This roadmap adapts the PR #36 governed memory spine direction onto current
main. It starts from the implemented FCC-V1-005 Memory Review decision lane and
keeps every future phase local-first, review-gated, receipt-backed, and
evidence-visible.

## Phase Order

| Phase | Scope | Current status | Authority boundary |
|---|---|---|---|
| Phase 1 | Memory Review decisions and recall-only record creation | Implemented/hardened through FCC-V1-005 | Accept/correct write reviewed recall-only records; reject writes no recall record |
| Phase 2 | L1 hot local memory index | Next safe phase after Phase 1 is merged and stable | Recall preview only; no hidden context injection |
| Phase 3 | L2 factual, graph, and temporal indexing | Planned | Explainable retrieval fusion only; no truth authority |
| Phase 4 | L3 identity, session, preference, and commitment modeling | Planned | Representation proposals only; no account sync or CRM writes |
| Phase 5 | Context-pack proposals | Planned | Proposal-only envelopes; exact user review required |
| Phase 6 | Narrow low-risk execution hooks | Future blocked | Requires separate accepted milestone, exact approval, receipt, rollback, and Evidence Timeline proof |

## Phase 1 Done Criteria

Phase 1 is complete only when:

- `GET /control-center/memory/review/{candidate_ref}/receipt` returns the latest
  safe receipt or a redacted 404.
- Accept/correct create reviewed recall-only `LocalMemoryStore` records and set
  `reviewed_recall_record_ref`.
- Correct stores corrected-summary ref posture only.
- Reject preserves the rejected candidate and creates no recall record.
- Decision routes require idempotency and preserve replay/conflict behavior.
- Evidence Timeline events record what changed and what remains blocked.
- Route inventory, OpenAPI, release surface, route status, docs, and verifiers
  agree on the 127-route boundary.

## Phase 2 Guardrails

Phase 2 L1 Hot Local Memory Index may add an L1 hot local index only after
Phase 1 is stable. It must remain local, private, safe-summary-only, and
user-reviewable.

Phase 2 must not add:

- embeddings or vector dependencies unless separately accepted
- provider/model calls
- hidden prompt/context injection
- automatic memory writes
- raw transcript or raw source storage
- connector writes or CRM/account sync
- action execution
- production authority

The first Phase 2 deliverable should be a recall preview and index inspection
contract, not automatic context use.

## Future Phases

L2 and L3 should synthesize factual, temporal, graph, identity, session,
preference, commitment, relationship, and representation models through
UAA-native contracts. Capability should be negotiated through manifests and
receipts, not hardcoded driver or provider assumptions.

Context packs, when scoped, must be proposed as reviewable envelopes with safe
refs, sources, provenance, evidence, risk, stale/conflict posture, and explicit
blocked states. They must never become hidden prompt context.
