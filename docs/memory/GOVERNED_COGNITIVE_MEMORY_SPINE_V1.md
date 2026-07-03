# Governed Cognitive Memory Spine V1

Status: active architecture contract, Phase 6.1 internal Action proposal hook implemented.
Baseline: v0.104.0 / 0.104.0.

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

## Feature-Mine Design References

FCC-MEM-022 records Honcho, Hindsight, and Holographic as design references
only. UAA may borrow safe product ideas such as perspective-aware recall
inspection, feedback receipts, contradiction previews, and an explicit future
path for algebraic vector-like retrieval. UAA does not add an external memory
provider runtime, cloud memory sync, automatic retain/recall, model extraction,
semantic/vector search, HRR retrieval, hidden context injection, connector
writes, or memory-derived execution from those references.

HRR/algebraic retrieval remains disabled with
`hrr_enabled=false`, `algebraic_retrieval_enabled=false`, and
`required_milestone_ref=milestone-ref:fcc-mem-hrr-001-explicit-authority`.
Future HRR work must be explicitly approved as its own milestone and still use
safe-summary/ref-token inputs only.

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

FCC-MEM-022 extends L1 read models with optional `safe_query` support. The raw
query is never echoed; only `safe_query_ref`, `query_mode`,
`retrieval_strategy_refs`, `score_components`, and `search_index_status` are
returned.

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

FCC-MEM-022 extends L3 representation items with perspective fields:
`observer_ref`, `observed_ref`, `perspective_scope`, `peer_card_ref`,
`session_summary_ref`, and `representation_scope_ref`. These are inspection refs
only and do not grant truth, identity, approval, context, CRM/account, or action
authority.

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

## Context Injection Prerequisite Contract

The next authority candidate after the reviewed recall-write lane is
`context_injection`, but only as a prerequisite contract. The exact future
scope under consideration is
`exact-scope-ref:context-injection:context-pack-preview-materialization`, which
means a backend-owned, safe-ref-only context-pack preview or materialization
artifact for operator review. It does not mean a prompt, provider request,
connector payload, browser session, shell command, or runtime consumer receives
context.

Allowed source refs for that future preview/materialization lane are limited to
reviewed and inspection-only Memory refs:

- `memory-record-ref:*`
- `reviewed-recall-ref:*`
- `l1-preview-ref:*`
- `l2-projection-ref:*`
- `l3-representation-ref:*`
- `context-pack-ref:*`
- `context-manifest-ref:*`
- `evidence-ref:*`
- `receipt:*`

Allowed destination or consumer refs are limited to review artifacts:

- `context-pack-preview-ref:*`
- `context-materialization-preview-ref:*`
- `proof-ref:*`
- `evidence-ref:*`
- `receipt:context-pack-preview:*`
- `repo-local-command:founder-loop-memory-context-manifest`

The approval binding for any later micro-lane must validate exact
`LocalApprovalAuthority` scope before materialization. Idempotency must bind the
context-pack ref, context-manifest ref, source refs, allowed destination ref,
redaction posture, reviewer ref, payload fingerprint ref, and approval ref.
Receipts must include source refs, destination/consumer refs, evidence refs,
audit refs, proof refs where available, redaction state, blocked runtime refs,
and next safe action. Rollback and safe-disable posture must include
`rollback-ref:context-injection:suppress-context-preview-materialization` and
`safe-disable-ref:context-injection:context-pack-preview-materialization`.

CLI/repo-local inspection for the prerequisite contract is
`scripts/dev/uaa_founder_loop.py memory-context-manifest`. That command returns
safe refs and manifest posture only. It must not print raw prompt text, raw
memory text, raw provider payloads, raw source bodies, raw local paths,
credentials, account identifiers, contacts, or file contents.

Still blocked until a separate exact micro-lane is proposed, reviewed,
implemented, and verified:

- runtime prompt context injection
- live model or provider context injection
- automatic memory inclusion
- connector-derived context injection
- browser or web-derived context injection
- shell, subprocess, or file-derived context injection
- hidden prompt context
- raw payload persistence
- public beta, public release, production readiness, or production authority

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

## Current Phase 6.1

Governed Cognitive Memory Spine Phase 6.1 is implemented as the first narrow
slice:

- `POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal`

A reviewed context-pack proposal may create a backend-owned internal Action
proposal/envelope receipt after exact approval scope and idempotency are
validated. This scope is internal Action proposal creation only. It does not
execute the action.

Phase 6.1 requires exact approval scope, idempotency, append-first durable
receipts, rollback or safe-disable posture, and Evidence Timeline proof before
the internal proposal is recorded. The broad Phase 6 execution-hook contract
remains blocked for external side effects, connector writes, CRM/account sync,
shell/browser behavior, provider/model calls, hidden context injection, and
production authority.

## Current Phase 6.2

FCC-MEM-022 adds ranked retrieval and recall tuning:

- `POST /control-center/memory/feedback`
- `GET /control-center/memory/observation-candidates`
- `GET /control-center/memory/probe`
- `GET /control-center/memory/contradictions`

Feedback is local, approval-bound, and idempotent. It can update trust,
stale, or conflict posture for reviewed recall records only. It cannot create
recall records, delete/export memory, write connectors, inject context, execute
actions, call providers/models, sync cloud memory, or grant production
authority.

Observation candidates, probe results, and contradiction previews are read-only
inspection models. They are not truth, automatic opinions, context packs ready
for prompt injection, merge/forget actions, or authority to operate on external
systems.

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
