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
| Phase 3 | L2 factual, graph, and temporal indexing | Implemented read-only derived preview | Deterministic ref projection only; no truth authority |
| Phase 4 | L3 identity, session, preference, and commitment modeling | Implemented read-only representation proposals | Representation proposals only; no account sync, CRM writes, or context injection |
| Phase 5 | Context-pack proposals | Implemented read-only proposal envelopes | Proposal-only envelopes; exact user review required before any future use |
| Phase 6 | Narrow low-risk execution hooks | Future blocked; contract/proof lane only | Requires separate accepted milestone, exact approval, receipt, rollback, and Evidence Timeline proof |
| Phase 6.1 | Context-pack to internal Action proposal hook | Accepted for implementation | Internal Action proposal creation only; no action execution or external side effects |

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
  agree on the current route boundary after Phase 5.

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

## Phase 3 Done Criteria

Phase 3 L2 Factual / Graph / Temporal Indexing is implemented as a derived,
read-only deterministic ref projection over Phase 2 L1 hot local memory
previews. It remains local, private, safe-ref-only, and inspection-only.

Phase 3 is complete only when:

- `GET /control-center/memory/l2-index` returns factual, graph, and temporal
  inspection items derived from reviewed L1 previews only.
- Every L2 item includes memory record refs, source refs, evidence refs,
  receipt refs, derivation reasons, stale/conflict posture, and blocked states.
- Rejected, unreviewed, raw/private, context-pack-eligible, or
  authority-bearing records remain filtered out by the L1 source lane.
- Route inventory, OpenAPI, release surface, route status, docs, tests, and
  verifiers agree that the route is read-only, local-sensitive, and not
  idempotency-required.

Phase 3 does not add:

- truth authority
- hidden prompt/context injection
- embeddings or vector dependencies
- provider/model calls
- LLM/entity extraction
- semantic search
- background indexing
- automatic memory writes
- context-pack injection
- connector writes or CRM/account sync
- action execution
- production authority

## Phase 4 Done Criteria

Phase 4 L3 Identity / Session / Preference / Commitment Modeling is
implemented as a derived, read-only representation proposal layer over Phase 3
L2 safe-ref inspection items. It remains local, private, safe-ref-only,
review-required, and inspection-only.

Phase 4 is complete only when:

- `GET /control-center/memory/l3-index` returns identity, session, preference,
  commitment, relationship, workspace, peer, or representation proposal items
  derived from reviewed L2 refs only.
- Every L3 item includes supporting memory record refs, L1 preview refs, L2
  item refs, source refs, evidence refs, receipt refs, derivation reason refs,
  stale/conflict posture, blocked states, and `review_required=true`.
- Rejected, unreviewed, raw/private, context-pack-eligible, or
  authority-bearing records remain filtered out by the L1/L2 source lanes.
- Route inventory, OpenAPI, release surface, route status, docs, tests, and
  verifiers agree that the route is read-only, local-sensitive, and not
  idempotency-required.

Phase 4 does not add:

- truth authority or CRM truth authority
- hidden prompt/context injection
- embeddings or vector dependencies
- provider/model calls
- LLM/entity extraction or semantic extraction
- semantic search
- background indexing
- automatic memory writes
- context-pack injection
- connector writes or CRM/account sync
- action execution
- production authority

## Phase 5 Done Criteria

Phase 5 Context-Pack Proposals is implemented as a derived, read-only proposal
envelope layer over reviewed L1/L2/L3 memory outputs. It remains local,
private, safe-ref-only, review-required, and inspection-only.

Phase 5 is complete only when:

- `GET /control-center/memory/context-packs` returns proposal-only context
  packs derived from reviewed L1 previews, L2 projections, and L3
  representation proposals.
- Every proposal includes source memory record refs, L1 preview refs, L2
  projection refs, L3 representation refs, included summary refs,
  inclusion/exclusion reasons, source refs, evidence refs, receipt refs,
  stale/conflict posture, approval requirement refs, and blocked states.
- Rejected, unreviewed, raw/private, or authority-bearing records remain
  filtered out by the source lanes.
- Route inventory, OpenAPI, release surface, route status, docs, tests, and
  verifiers agree that the route is read-only, local-sensitive, and not
  idempotency-required.

Phase 5 does not add:

- hidden prompt/context injection
- prompt context writing
- provider/model calls
- embeddings or vector dependencies
- semantic search
- background indexing
- automatic memory writes
- connector writes or CRM/account sync
- action execution
- public beta or production authority

## Future Phases

Phase 6 remains future blocked. `MemoryExecutionHookContract`,
`MemoryExecutionHookProposal`, and `MemoryExecutionHookBlockedState` define the
contract/proof lane only. Any narrow low-risk execution hook still requires a
separate accepted milestone with exact approval, idempotency, receipt, rollback
or safe-disable posture, and Evidence Timeline proof.

Phase 6.1 is the accepted first implementation slice. It may create an
internal Action proposal/envelope receipt from a reviewed context-pack proposal
after exact approval scope and idempotency are validated. Phase 6.1 does not
execute actions, write connectors, sync CRM/accounts, call providers/models,
run shell/browser behavior, inject prompt context, or grant production
authority.

Phase 6 currently adds no:

- memory-derived execution route
- context-pack action execution
- connector write
- CRM or account sync
- shell/subprocess or browser automation
- provider/model call
- hidden or automatic context injection
- background agent or automatic scheduling
- public beta or production authority
