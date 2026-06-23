# Governed Cognitive Memory Spine V1

Status: active architecture contract, Phase 6.1 internal Action proposal hook accepted.
Baseline: v0.103.0 / 0.103.0.

The Governed Cognitive Memory Spine is UAA's local-first, review-gated memory
pipeline that converts safe, provenance-linked memory candidates into reviewed
recall records and indexes those records across hot/local,
factual/temporal/graph, and identity/session/preference/commitment layers for
explainable recall previews or context-pack proposals without treating memory
as truth, approval, execution authority, connector authority, or hidden prompt
context.

This is not a generic "build better memory" track. It is the governed spine for
the Founder Command Center loop: Today, Actions, Evidence, and Memory. Every
memory path must stay source-linked, user-reviewable, receipt-backed, and
evidence-visible.

## Layer Synthesis

UAA uses the concepts of three memory styles without importing, vendoring, or
depending on their systems:

- L1 hot local memory: local, fast, private, reviewed safe-summary recall.
- L2 factual, graph, and temporal memory: entity, relation, and time indexing
  with explainable retrieval fusion.
- L3 identity and session memory: workspace, peer, session, preference,
  commitment, relationship, and representation modeling.

The spine is UAA-native. `LocalMemoryStore`, source provenance contracts,
Memory Review decisions, Evidence Timeline events, and route manifests are the
current authority surfaces.

## Current Phase 1

FCC-V1-005 is implemented as backend-owned Memory Review decisions:

- `GET /control-center/memory/review`
- `GET /control-center/memory/review/{candidate_ref}/receipt`
- `POST /control-center/memory/review/{candidate_ref}/accept`
- `POST /control-center/memory/review/{candidate_ref}/correct`
- `POST /control-center/memory/review/{candidate_ref}/reject`

Accept/correct decisions require idempotency, create durable receipts, write
reviewed recall-only `LocalMemoryStore` records with safe summaries and refs,
and emit Evidence Timeline state. Reject decisions create receipts, preserve the
rejected candidate, and do not create recall records.

`MemoryReviewDecisionReceipt` includes `reviewed_recall_record_ref` for
accept/correct only. Correction stores corrected-summary ref posture only, not
raw corrected content.

## Current Phase 2

Phase 2 L1 hot local memory index status is implemented read-only derived
preview over reviewed recall-only `LocalMemoryStore` records:

- `GET /control-center/memory/l1-index`

The L1 route indexes only records produced by reviewed accept/correct Memory
Review decisions. It returns safe summaries, source refs, evidence refs,
receipt refs, event refs, metadata refs, tag refs, match reasons, and
supporting ref groups so recall previews explain why they appeared.

The L1 index status is `implemented_read_only_derived_preview`. It does not
store raw content, run background indexing, call providers/models, use
embeddings, use a vector DB, perform semantic search, write memories
automatically, inject context, sync connectors/CRM/accounts, execute actions,
or grant public beta or production authority.

## Current Phase 3

Phase 3 L2 factual, graph, and temporal index status is implemented read-only
derived preview over Phase 2 L1 hot local memory previews:

- `GET /control-center/memory/l2-index`

The L2 route derives factual, relationship, and temporal inspection items only
from reviewed L1 recall previews and safe refs. Every item carries memory
record refs, reviewed recall refs where available, source refs, evidence refs,
receipt refs, event/metadata/tag refs, derivation reasons, stale/conflict
posture, and blocked states.

The L2 index is deterministic ref projection only. It does not perform semantic
search, LLM/entity extraction, embeddings/vector indexing, background indexing,
truth scoring, context-pack injection, connector/CRM/account sync, action
execution, provider/model calls, or public beta/production authority.

## Current Phase 4

Phase 4 L3 identity, session, preference, and commitment modeling status is
implemented read-only representation proposals over Phase 3 L2 safe-ref
inspection items:

- `GET /control-center/memory/l3-index`

The L3 route derives representation proposal items only from reviewed L2 facts,
relations, and temporal anchors. Every item carries supporting memory record
refs, L1 preview refs, L2 item refs, source refs, evidence refs, receipt refs,
derivation reason refs, stale/conflict posture, and blocked states.

The L3 index is deterministic safe-ref projection only. It does not perform
semantic extraction, hidden context injection, truth scoring, CRM/account sync,
connector writes, context-pack injection, action execution, provider/model
calls, embeddings/vector indexing, semantic search, background indexing, or
public beta/production authority.

## Current Phase 5

Phase 5 context-pack proposal status is implemented as a read-only,
review-required proposal envelope layer over Phase 2 L1, Phase 3 L2, and Phase
4 L3 safe-ref outputs:

- `GET /control-center/memory/context-packs`

The context-pack route derives proposal envelopes only from reviewed memory
layers. Every proposal carries source memory record refs, L1 preview refs, L2
projection refs, L3 representation refs, included summary refs, inclusion
reason refs, excluded ref reasons, source refs, evidence refs, receipt refs,
stale/conflict posture, approval requirement refs, and blocked states.

The context-pack lane is proposal-only. It is not hidden context injection and
does not inject context into prompts, write prompt context, call
providers/models, perform semantic search, add embeddings/vector indexing,
sync CRM/accounts, write connectors, execute actions, or grant public
beta/production authority.

## Current Phase 6

Phase 6 narrow low-risk execution hooks remain future blocked. The current work
adds `MemoryExecutionHookContract`, `MemoryExecutionHookProposal`, and
`MemoryExecutionHookBlockedState` as a contract-only proof surface; current
Phase 6 status is contract/proof lane only.

The contract records the future gate sequence that must exist before any later
memory-derived execution can be considered:

- context-pack proposal refs
- Action Envelope refs
- exact LocalApprovalAuthority scope refs
- idempotency refs
- durable receipt refs
- rollback or safe-disable refs
- Evidence Timeline event refs
- blocked authority refs

There is no Phase 6 runtime route, execution driver, connector write, shell or
browser execution, provider/model call, automatic context injection, CRM/account
sync, background agent, scheduler, public beta, or production authority.

## Accepted Phase 6.1 Scope

Governed Cognitive Memory Spine Phase 6.1 is accepted for the first narrow
implementation slice: a reviewed context-pack proposal may create a
backend-owned internal Action proposal/envelope receipt. This scope is internal
Action proposal creation only. It does not execute the action.

Phase 6.1 must require exact approval scope, idempotency, append-first durable
receipts, rollback or safe-disable posture, and Evidence Timeline proof before
the internal proposal is recorded. The broad Phase 6 execution-hook contract
remains blocked for external side effects, connector writes, CRM/account sync,
shell/browser behavior, provider/model calls, hidden context injection, and
production authority.

## Authority Boundary

Memory is recall, not authority. Accepted memory is reviewed recall only.
Accepted memory is not truth authority, approval authority, execution
authority, connector/account/CRM authority, or automatic prompt/context
injection.

Still blocked:

- automatic memory writes
- hidden context injection
- source truth authority
- approval authority
- action execution
- connector writes
- CRM or account sync
- hidden prompt or context-pack injection
- provider/model calls
- shell/subprocess behavior
- browser automation
- delete/export execution
- public beta, public distribution, or production authority

No durable state may store raw prompt, raw response, raw provider payload, raw
transcript, raw source body, raw file content, raw local path, raw log,
username, hostname, credential, token, or secret-like value.

## Evidence Contract

Every accepted, corrected, rejected, or proposed context-pack candidate must be
inspectable as history:

- what candidate was reviewed
- what decision was recorded
- what source/provenance/evidence refs were used
- what receipt was created
- what changed
- what did not change
- what remains blocked
- why proposed context refs are not hidden prompt context

Evidence, receipts, and recall refs are durable inspection refs. They do not
grant hidden context, truth, connector, or execution authority.
