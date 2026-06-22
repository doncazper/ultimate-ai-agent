# Governed Cognitive Memory Spine V1

Status: active architecture contract, Phase 1 hardened through FCC-V1-005.
Baseline: v0.103.0 / 0.103.0.

The Governed Cognitive Memory Spine is UAA's local-first, review-gated memory
pipeline that converts safe, provenance-linked memory candidates into reviewed
recall records and, in later phases, indexes those records across hot/local,
factual/temporal/graph, and identity/session layers for explainable recall
previews or context-pack proposals without treating memory as truth, approval,
execution authority, connector authority, or hidden prompt context.

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
- provider/model calls
- shell/subprocess behavior
- browser automation
- delete/export execution
- public beta, public distribution, or production authority

No durable state may store raw prompt, raw response, raw provider payload, raw
transcript, raw source body, raw file content, raw local path, raw log,
username, hostname, credential, token, or secret-like value.

## Evidence Contract

Every accepted, corrected, or rejected candidate must be inspectable as history:

- what candidate was reviewed
- what decision was recorded
- what source/provenance/evidence refs were used
- what receipt was created
- what changed
- what did not change
- what remains blocked

Evidence, receipts, and recall refs are durable inspection refs. They do not
grant hidden context, truth, connector, or execution authority.
