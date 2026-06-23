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
| Phase 2 | L1 hot local memory index | Implemented read-only derived preview | Recall preview and index inspection only; no hidden context injection |
| Phase 3 | L2 factual, graph, and temporal indexing | Next planned safe phase | Explainable retrieval fusion only; no truth authority |
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
  agree on the 128-route boundary after Phase 2.

## Phase 2 Done Criteria

Phase 2 L1 Hot Local Memory Index is implemented as a derived, read-only
inspection lane over Phase 1 reviewed recall-only `LocalMemoryStore` records.
It remains local, private, safe-summary-only, and user-reviewable.

Phase 2 is complete only when:

- `GET /control-center/memory/l1-index` returns safe recall previews and index
  inspection metadata for reviewed recall-only records.
- Every preview explains why it matched and includes source, evidence, receipt,
  event, metadata, tag, and memory record refs where available.
- Unreviewed, rejected, raw/private, context-pack-eligible, or authority-bearing
  records are skipped.
- Route inventory, OpenAPI, release surface, route status, docs, tests, and
  verifiers agree that the route is read-only, local-sensitive, and not
  idempotency-required.

Phase 2 does not add:

- embeddings or vector dependencies unless separately accepted
- provider/model calls
- hidden prompt/context injection
- automatic memory writes
- raw transcript or raw source storage
- semantic search
- background indexing
- connector writes or CRM/account sync
- action execution
- production authority

## Phase 3 Guardrails

Phase 3 L2 Factual / Graph / Temporal Indexing remains planned. It must not
turn memory into truth authority, add hidden context injection, or introduce
provider/model calls, connector writes, action execution, public beta, or
production authority.

## Future Phases

L2 and L3 should synthesize factual, temporal, graph, identity, session,
preference, commitment, relationship, and representation models through
UAA-native contracts. Capability should be negotiated through manifests and
receipts, not hardcoded driver or provider assumptions.

Context packs, when scoped, must be proposed as reviewable envelopes with safe
refs, sources, provenance, evidence, risk, stale/conflict posture, and explicit
blocked states. They must never become hidden prompt context.
