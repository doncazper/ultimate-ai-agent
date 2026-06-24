# Memory Module Hardening And GoatCitadel Comparison

Status: review and hardening report
Date: 2026-06-24
Baseline: v0.104.0 / 0.104.0
Compared systems:

- Ultimate AI Agent, current repository: `doncazper/ultimate-ai-agent`
- GoatCitadel, local comparison repository:
  `/Users/sambehdjou/Documents/GitHub/GoatCitadel`

## Executive Verdict

GoatCitadel is stronger today as a functional memory runtime.

Ultimate AI Agent is stronger today as a governed memory reconciliation and
operator-safety system.

That distinction matters. GoatCitadel has more runtime teeth: it composes
memory context, ranks candidates with lexical, semantic-hint, recency, diversity,
and optional embedding signals, validates citations, stores context packs,
tracks QMD runs, exposes retrieval status, supports memory feedback, scans
quality issues, and runs memory maintenance. It behaves more like a working
memory engine.

Ultimate AI Agent has more disciplined governance: memory remains recall, not
truth; context injection is blocked; memory write/delete/export authority is
explicitly denied unless scoped; every lane is safe-ref oriented; review
decisions produce receipts; Memory Workbench groups duplicate, conflict, stale,
and missing-evidence states; FCC-MEM-015 connects memory refs to Today, Actions,
Briefing, Evidence, and context-pack previews without creating hidden authority.
It behaves more like a controlled memory cockpit.

For the Founder Command Center direction, Ultimate AI Agent should not copy
GoatCitadel's raw-context runtime posture wholesale. The right next step is to
import GoatCitadel's runtime maturity as inspectable, proposal-only machinery:
ranked retrieval diagnostics, citation validation, memory feedback loops,
quality scans, maintenance runs, and structured relationship/decision/learning
records, while preserving UAA's review gate, safe refs, Action Inbox approval,
Evidence Timeline proof, and no hidden context injection.

## What Was Hardened In This Pass

This review included a scoped hardening patch to Ultimate AI Agent:

- `validate_memory_record()` now validates nested `source_refs`, `provenance`,
  `recall_metadata`, and `lifecycle` objects, rather than relying on callers to
  invoke those checks separately.
- FCC-MEM-015 impact graph builders now validate direct `memory_ref`,
  `review_ref`, `review_state`, `candidate_kind`, top loop-driving memory refs,
  context-pack preview refs, proposal refs, and follow-up action proposal refs.
- New regression coverage rejects nested raw local paths in memory provenance
  and unsafe direct refs in FCC-MEM-015 derived read models.

Files changed:

- `src/ultimate_ai_agent/core/memory/validation.py`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `tests/test_memory_validation.py`
- `tests/test_fcc_mem_015_memory_impact_graph_followup_queue.py`

Validation run:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_memory_validation.py tests/test_m24_memory_provider_contracts.py tests/test_memory_records.py tests/test_fcc_mem_015_memory_impact_graph_followup_queue.py tests/test_fcc_mem_001_memory_workbench.py -q`
  - Result: 29 passed, 1 Starlette/httpx deprecation warning.
- `.venv/bin/python scripts/verify_fcc_mem_015_memory_impact_graph_followup_queue.py`
  - Result: passed.
- `.venv/bin/python scripts/verify_fcc_mem_001_memory_workbench.py`
  - Result: passed.
- `.venv/bin/python scripts/verify_governed_cognitive_memory_spine_v1.py`
  - Result: passed, 1 Starlette/httpx deprecation warning.
- `.venv/bin/python scripts/verify_documentation_integrity.py`
  - Result: passed.
- `corepack pnpm --filter @goatcitadel/memory-core test`
  - Result: 4 files passed, 30 tests passed.
- `git diff --check`
  - Result: passed.

## Methodology

The comparison used local source inspection, not web claims.

Ultimate AI Agent files inspected:

- `src/ultimate_ai_agent/core/memory/records.py`
- `src/ultimate_ai_agent/core/memory/validation.py`
- `src/ultimate_ai_agent/core/memory/local_store.py`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/memory/review_decisions.py`
- `src/ultimate_ai_agent/core/memory/context_packs.py`
- `src/ultimate_ai_agent/core/memory/l1_index.py`
- `src/ultimate_ai_agent/core/memory/l2_index.py`
- `src/ultimate_ai_agent/core/memory/l3_index.py`
- `src/ultimate_ai_agent/core/memory/fcc_relationship_memory_schema.py`
- `src/ultimate_ai_agent/core/recall/context_pack.py`
- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`
- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`

GoatCitadel files inspected:

- `AGENTS.md`
- `packages/contracts/src/memory.ts`
- `packages/contracts/src/learned-memory.ts`
- `packages/contracts/src/memory-write-gate.ts`
- `packages/memory-core/src/types.ts`
- `packages/memory-core/src/candidate-collector.ts`
- `packages/memory-core/src/candidate-ranker.ts`
- `packages/memory-core/src/context-composer.ts`
- `packages/memory-core/src/distiller.ts`
- `packages/memory-core/src/cache.ts`
- `apps/gateway/src/services/memory-context-service.ts`
- `apps/gateway/src/services/memory-lifecycle-service.ts`
- `apps/gateway/src/services/memory-lifecycle-policy.ts`
- `apps/gateway/src/services/memory-maintenance-service.ts`
- `apps/gateway/src/services/memory-write-gate-service.ts`
- `apps/gateway/src/routes/memory.ts`
- `packages/storage/src/*memory*.ts`
- `packages/mission-control-shared/src/api/memory.ts`
- `packages/mission-control-shared/src/hooks/useMemoryOperatorSnapshot.ts`
- `apps/mission-control-next/src/features/native-routes/library/MemoryRoutePage.tsx`

## Ultimate AI Agent Memory Architecture

Ultimate AI Agent's memory module is contract-first and governance-heavy.

Core structure:

- `MemoryRecord`, `MemorySourceRef`, `MemoryProvenance`,
  `MemoryRecallMetadata`, and `MemoryLifecycleMetadata` define the base record
  model.
- `LocalMemoryStore` persists reviewed recall-only records to memory or SQLite.
- `validate_memory_write_request()` denies automatic writes, model output,
  local LLM output, OpenWebUI output, mobile capture, tool output, raw prompt,
  raw model output, raw file content, raw transcript, and secret-like content.
- `MemoryReviewDecisionEnvelope` and `MemoryReviewDecisionRequest` model
  accept, correct, reject, defer, merge, supersede, and forget-request decisions.
- L1/L2/L3 indexes derive safe read-only previews over reviewed recall records.
- Context-pack proposals remain inspectable artifacts only.
- FCC-MEM-001 exposes the operator workbench: ranked candidate queue,
  duplicate/conflict/stale/missing-evidence grouping, search filters, manual
  intake, lifecycle receipts, and CLI parity.
- FCC-MEM-015 exposes the impact graph, Recall Health V2, proposal-only
  follow-up queue, merge/supersede comparison, and context-pack preview
  inspection.

UAA's strongest pattern is the "memory is not authority" discipline. The code
does not treat memory recall, previews, context packs, or model/provider output
as permission to act. This is visible across blocked-state refs, explicit false
authority flags, receipt refs, and route docs.

The major current limitation is that UAA's memory module is still mostly an
operator reconciliation spine. It explains and governs memory better than it
uses memory. It has ranked queues and read models, but it does not yet have a
full runtime retrieval loop, real citation-bearing context composition,
feedback-driven relevance tuning, or durable memory maintenance jobs comparable
to GoatCitadel.

## GoatCitadel Memory Architecture

GoatCitadel's memory module is runtime-first and deeply wired into its gateway.

Core structure:

- `packages/memory-core` owns candidate collection, ranking, citation
  validation, context composition, cache keys, token estimation, and distiller
  parsing.
- `MemoryContextService` composes context packs from transcripts, memory items,
  and files; ranks candidates; calls a distiller model when configured; falls
  back when unavailable; records QMD runs; emits realtime events; and exposes
  retrieval status.
- `MemoryLifecycleService` owns memory items, learnings, entities, relations,
  decisions, feedback, trace candidates, quality issues, recall, forget, and
  history.
- `MemoryWriteGateService` classifies writes as allowed, proposed, or blocked
  based on authority, secret-like content, external write policy, and
  contradiction hints.
- `MemoryMaintenanceService` runs policy-driven durable maintenance,
  consolidates sources, writes maintenance artifacts, tracks provenance, and
  issues recommendations.
- `apps/gateway/src/routes/memory.ts` exposes a broad API: context compose,
  context get, QMD stats, retrieval status, retrieval benchmark, recall,
  feedback, quality issues, trace candidates, item lifecycle, maintenance
  policy/runs/recommendations, learnings, entities, relations, decisions, and
  structured history.
- Mission Control renders memory as an operator surface with memory truth,
  lifecycle state, maintenance, QMD stats, quality issues, trace candidates,
  and structured records.

GoatCitadel's strongest pattern is "memory as an active runtime subsystem."
It does not stop at review cards. It can retrieve, rank, compose, cache,
benchmark, observe, and maintain memory.

The major current limitation is risk posture. GoatCitadel's memory context path
can carry raw candidate text, snippets, file chunks, transcript-derived content,
and distiller evidence into runtime context. That is useful for a working
assistant, but it is not as conservative as UAA's safe-ref-only Founder Command
Center memory surfaces. GoatCitadel has write gates, auth route access, path
jails, citation validation, and feature flags, but it is more willing to use
memory content directly.

## Head-To-Head Scorecard

| Dimension | Stronger system | Why |
|---|---|---|
| Runtime retrieval | GoatCitadel | Candidate collection from transcript, file, and memory item sources; BM25-like lexical scoring; semantic hints; optional embedding score; recency and diversity scoring. |
| Context composition | GoatCitadel | Builds actual `MemoryContextPack` records, caches them, tracks token estimates, QMD quality, citations, and expiry. |
| Citation integrity | GoatCitadel | Has `validateCitations()` and distiller citation parsing. UAA has evidence refs and receipt refs, but not a comparable runtime citation-validation loop. |
| Memory governance | Ultimate AI Agent | Stronger default denials, safe-ref-first surfaces, blocked authority flags, review receipts, and no hidden context injection. |
| Operator reconciliation UX | Ultimate AI Agent | Memory Workbench and FCC-MEM-015 are more explicit about duplicate/conflict/stale/missing-evidence grouping and "why shown" / "what this affects." |
| Structured relationship memory | GoatCitadel today, UAA directionally | GoatCitadel has entities, relations, decisions, learnings, trace candidates, feedback, and quality issues as runtime APIs. UAA has CRM-lite and relationship schemas, but they remain more proposal/read-model oriented. |
| Maintenance and self-healing | GoatCitadel | Durable memory maintenance runs, recommendations, policy patching, run provenance, and source consolidation are materially ahead. |
| Safety boundaries | Ultimate AI Agent | UAA denies model/provider calls, context injection, vector/semantic search, connector writes, CRM sync, action execution, and production authority by default. |
| CLI parity | Ultimate AI Agent | UAA explicitly treats CLI inspection as first-class for operator-relevant flows. GoatCitadel has gateway and scripts, but the memory review loop is more UI/API centered. |
| Product integration | Tie, different shape | GoatCitadel integrates memory into Chat/Cowork/Code runtime. UAA integrates memory into Today, Action Inbox, Briefing, Evidence, and Founder Command Center review. |
| Evidence and route truth | Ultimate AI Agent | UAA's route manifests, OpenAPI checks, product truth docs, and verifier culture are stricter for public claims and authority boundaries. |
| Actual usefulness today | GoatCitadel | It can actively retrieve and compose memory context. UAA mostly inspects and proposes. |
| Founder safety fit | Ultimate AI Agent | UAA's memory posture better matches a local-first governed operator cockpit. |

## Detailed Strengths: Ultimate AI Agent

### 1. Memory Is Clearly Not Truth

UAA repeats the boundary at every level:

- `authority_level` defaults to recall-only.
- `validate_memory_record()` rejects blocked authority.
- Workbench read models set `memory_truth_authority=false`.
- Context-pack proposals set `truth_authority_enabled=false`.
- FCC-MEM-015 sets `memory_truth_authority=false`,
  `context_injection_authorized=false`, `action_execution_authorized=false`,
  `connector_write_authorized=false`, and `production_authority_enabled=false`.

This is better than a memory system that quietly treats recall as evidence,
truth, or instruction.

### 2. Review Receipts Are A First-Class Primitive

UAA's memory review decisions are explicit, receipt-bearing lifecycle events.
Accept/correct can create reviewed recall-only records. Reject/defer/merge/
supersede/forget-request preserve review posture without silently mutating
runtime authority.

This is exactly the right shape for a founder cockpit: memory changes are
decisions, not background magic.

### 3. FCC-MEM-001 Is A Real Reconciliation Surface

The Memory Workbench gives memory candidates operational posture:

- ranked queue
- duplicate grouping
- conflict grouping
- stale grouping
- missing evidence grouping
- reviewed/rejected grouping
- why-shown refs
- quality reason refs
- manual candidate intake
- search/filter route
- CLI parity

GoatCitadel has more runtime memory, but UAA's memory review queue is more
governed and explainable.

### 4. FCC-MEM-015 Connects Memory To The Founder Loop

The impact graph answers the question that most memory systems dodge:

What does this memory affect?

It connects memory refs to Today, Actions, Briefing, Evidence, and context-pack
preview refs. This is powerful because it makes memory part of the operator
loop rather than a passive database.

### 5. Context Packs Are Inspectable Without Injection

UAA has context-pack proposals that show what would be included and why, while
preserving blocked states for hidden context injection. This is safer than
immediately stuffing memory into prompts.

## Detailed Weaknesses: Ultimate AI Agent

### 1. Retrieval Is Still Mostly A Governed Preview, Not A Runtime Engine

UAA has L1/L2/L3 projections and search filters, but it lacks a mature runtime
retrieval loop with:

- lexical scoring over candidate text
- semantic-hint scoring
- optional embedding scoring behind an accepted milestone
- recency/diversity scoring
- citation validation
- query/source hashes
- cache TTL
- retrieval benchmarks
- QMD stats

In short: UAA can explain memory safely, but it cannot yet compete with
GoatCitadel's practical recall mechanics.

### 2. No Memory Feedback Loop Yet

UAA has health metrics and review states, but not enough operator feedback
capture:

- useful
- stale
- missing
- irrelevant
- wrong relationship
- wrong timing
- not actionable

GoatCitadel's feedback and quality issue model would be very valuable here.

### 3. No Durable Maintenance Runner

UAA has self-healing recommendations and memory follow-up proposals, but it does
not yet have a memory maintenance runner that can:

- scan eligible sources
- produce dry-run consolidation proposals
- record source bundles
- create maintenance provenance
- recommend schedule/threshold changes
- track durable maintenance run state

UAA should implement this, but as proposal-only first.

### 4. Structured Memory Is Split Across Several Lanes

UAA has `MemoryRecord`, `FCCRelationshipMemoryCandidate`, CRM-lite bindings,
L3 representation proposals, and FCC-MEM-015 impact nodes. These are safe, but
they are not yet a single cohesive structured memory schema for:

- people
- organizations
- relationships
- deals
- commitments
- promises
- decisions
- learnings
- retrospectives
- source drift

GoatCitadel is ahead here.

### 5. Safe-Ref-Only Can Become Too Abstract

Safe refs are the right default for UAA, but operators eventually need bounded,
reviewed, redacted summaries. If every screen becomes only refs, memory is safe
but not alive. UAA needs a strict "bounded reviewed display text" lane that is
not raw content, not hidden context, and not authority.

## Detailed Strengths: GoatCitadel

### 1. Mature Candidate Pipeline

GoatCitadel collects candidates from:

- transcript events
- files
- memory items

It bounds transcript events, file candidates, memory item candidates, and chars
per candidate. Ranking combines:

- BM25-like lexical score
- semantic hint score
- optional embedding score
- recency score
- source diversity score

This is much closer to a useful retrieval engine than UAA's current safe
inspection indexes.

### 2. Context Composition Is Operational

GoatCitadel can produce a `MemoryContextPack` with:

- `contextId`
- scope
- query hash
- sources hash
- context text
- citations
- quality status
- token estimates
- creation and expiry

It also supports cache hits, fallbacks, realtime events, and QMD run stats.
That is runtime muscle UAA does not yet have.

### 3. Structured Memory Is Productive

GoatCitadel's contracts include:

- entities
- relations
- decisions
- learnings
- feedback
- trace candidates
- quality issues
- recall responses
- maintenance policies
- maintenance recommendations

This gives it an immediately useful memory ontology.

### 4. Feedback And Quality Issues Are Built In

GoatCitadel can record feedback and scan quality issues such as:

- stale low value
- near duplicate
- likely contradiction
- source drift
- retrieval gap

UAA has health and quality grouping, but GoatCitadel is ahead on feedback-driven
memory improvement.

### 5. Maintenance Has A Durable Runtime Shape

GoatCitadel's memory maintenance service can run manually, on schedule, or in
hybrid mode. It tracks policy, state, runs, provenance, sources, changes, and
recommendations. This is the clearest feature UAA should learn from.

## Detailed Weaknesses: GoatCitadel

### 1. Direct Context Use Has Higher Risk

GoatCitadel's context composer can emit fallback context lines from candidate
text and citations with snippets. It also builds distiller prompts that include
candidate text. That is appropriate for a runtime assistant, but it is not
UAA's desired safety posture yet.

For UAA, this must remain blocked until a separate accepted milestone defines:

- exact approval
- safe display text rules
- redaction proof
- rollback/safe-disable
- Evidence Timeline proof
- no hidden prompt injection

### 2. Write Gate Is Useful But Simpler Than UAA's Governance Matrix

GoatCitadel's write gate classifies allowed/proposed/blocked by authority,
secret-like content, external write policy, and contradiction hints. That is
good, but UAA's broader route, approval, evidence, redaction, and product-truth
matrix is stricter.

### 3. Operator Review Is Less Central Than Runtime Use

GoatCitadel has operator routes and UI, but the memory engine's strongest
center of gravity is runtime context composition. UAA's Memory Workbench is
more sharply designed as a reconciliation surface.

### 4. Raw Text And Snippets Are A Product Risk

A useful memory product eventually needs text, but raw or semi-raw snippets
increase the chance of leaking private content, local paths, provider payloads,
or stale assertions. UAA's instinct to force safe refs and bounded summaries is
safer for a local-first founder cockpit.

## What UAA Should Learn From GoatCitadel

### 1. Add A Retrieval Diagnostics Layer Before Semantic Search

Do not jump straight to vector search. First implement a deterministic local
retrieval diagnostics layer:

- query ref
- candidate refs
- lexical score
- recency score
- diversity score
- safe semantic-hint score from tags/aliases only
- total score
- why selected refs
- why excluded refs
- no raw candidate text
- no embeddings
- no model calls

This would give UAA practical ranking without crossing the semantic/vector
milestone boundary.

### 2. Add Citation Validation For Context-Pack Proposals

Before context packs can ever be used, UAA should validate that every proposed
summary ref, source ref, evidence ref, receipt ref, and memory ref maps to the
candidate set.

Borrow the idea of GoatCitadel's citation validator, but keep UAA safe-ref-only:

- invalid citation refs fail the proposal
- orphaned memory refs are excluded with reason refs
- context-pack proposals include citation integrity status
- Evidence Timeline records invalid citation attempts

### 3. Add Memory Feedback Records

UAA should capture operator feedback as first-class memory quality signals:

- useful
- stale
- missing
- irrelevant
- duplicate
- conflict
- wrong relationship
- wrong commitment

These feedback records should feed Recall Health V3 and Memory Workbench
ranking. They should not directly write memory.

### 4. Add Proposal-Only Memory Maintenance Runs

UAA should implement a local Memory Maintenance dry-run lane:

- manual run only at first
- no model calls
- no file writes except receipt/proposal storage
- source refs only
- proposed changes only
- Action Inbox review required before any future mutation lane
- run provenance
- changed/refreshed/suppressed proposal refs
- Evidence Timeline event

This is the biggest GoatCitadel lesson.

### 5. Consolidate Structured Memory Around Founder Workflows

UAA should create one cohesive schema for:

- person refs
- organization refs
- deal refs
- project refs
- commitment refs
- promise refs
- relationship refs
- decision refs
- learning refs
- retrospective refs
- follow-up refs

The current CRM-lite and L3 lanes are close, but the schema should become the
foundation for the next memory workbench phase.

### 6. Add Retrieval Benchmarks

GoatCitadel has a retrieval benchmark API. UAA should add a local verifier lane:

- given safe query refs and expected memory refs
- run deterministic retrieval diagnostics
- assert expected refs appear or are explicitly excluded
- record no raw text
- prove no vector/model/provider calls

This would make memory quality measurable instead of anecdotal.

## What GoatCitadel Should Learn From UAA

### 1. Make Memory Authority Flags More Visible Everywhere

UAA is relentless about explicit denied flags. GoatCitadel has governance, but
some runtime memory surfaces should more visibly state:

- memory is recall, not truth
- context pack is not approval
- citation is not canonical proof
- fallback context is lower confidence
- memory write is not execution authority

### 2. Separate Context Preview From Context Use More Strongly

GoatCitadel can compose context for actual runtime use. UAA's context-pack
proposal pattern is safer: inspectable first, approved use later.

GoatCitadel could benefit from clearer "preview only" and "used in prompt"
receipts.

### 3. Improve Redacted Evidence Posture Around Candidate Text

GoatCitadel's raw candidate text path is useful, but it should have more
UAA-style redaction proof and source-safety markers, especially for fallback
context.

### 4. Make Lifecycle Events Answer Operator Questions

UAA's FCC-MEM-015 shape asks:

- What changed?
- What was suppressed?
- What stayed blocked?
- Which surfaces are affected?

GoatCitadel could make memory changes more operator-readable by adopting those
questions across forget, supersede, maintenance, trace candidate promotion, and
quality issue resolution.

## Recommended Next Implementation Sequence For UAA

### P0: Keep The Hardening From This Pass

Status: implemented in this review.

Keep nested provenance validation and FCC-MEM-015 direct-ref validation. These
are small but important guardrails.

### P1: FCC-MEM-016 Retrieval Diagnostics Read Model

Build a read-only retrieval diagnostics endpoint:

- `GET /control-center/memory/retrieval-diagnostics`
- Inputs: `query_ref`, optional `surface_ref`, optional `limit`.
- Output: ranked candidate refs, score components, why-selected refs,
  why-excluded refs, stale/conflict/missing-evidence refs, and blocked states.
- No semantic search.
- No embeddings.
- No model/provider calls.
- No raw candidate text.
- CLI: `scripts/dev/uaa_founder_loop.py memory-retrieval-diagnostics`.
- Tests: query ref validation, deterministic ranking, no raw content, no hidden
  authority flags.

Why next: this gives UAA memory "teeth" without violating the current design
block on semantic/vector search.

### P2: FCC-MEM-017 Citation Integrity For Context-Pack Proposals

Add safe-ref citation validation over context-pack proposals:

- validate included memory refs exist in the candidate/read-model set
- validate source/evidence/receipt refs are structured safe refs
- produce invalid/missing/orphaned citation reason refs
- show citation integrity in Control Center
- record Evidence Timeline events for invalid proposals
- add verifier coverage

Why next: this is the bridge from proposal-only context packs to future
approved context use.

### P3: FCC-MEM-018 Memory Feedback And Quality Issue Queue

Add first-class memory feedback records:

- feedback kind: useful, stale, missing, irrelevant, duplicate, conflict,
  wrong-relationship, wrong-timing
- target kind: memory candidate, impact graph node, context-pack preview,
  follow-up proposal, Today item, Action proposal, Evidence event
- status: open, reviewed, dismissed
- no memory write
- no action execution
- read model folds feedback into Recall Health V3

Why next: operators need a low-friction way to teach the memory system without
granting it hidden write authority.

### P4: FCC-MEM-019 Proposal-Only Memory Maintenance Run

Add dry-run maintenance:

- manual run only
- source bundles are safe refs only
- output is proposed suppression, merge, stale, missing-evidence, and
  follow-up candidates
- all changes go to Action Inbox or Memory Review
- no direct store mutation
- durable run receipt
- Evidence Timeline proof

Why next: this imports GoatCitadel's strongest operational pattern while
preserving UAA's safety posture.

### P5: FCC-MEM-020 Structured Founder Memory Schema V1

Consolidate CRM-lite, L3, and relationship memory into a coherent schema:

- PersonMemoryRef
- OrgMemoryRef
- DealMemoryRef
- ProjectMemoryRef
- CommitmentMemoryRef
- PromiseMemoryRef
- RelationshipMemoryRef
- DecisionMemoryRef
- LearningMemoryRef
- RetrospectiveMemoryRef

Each record must include:

- safe display label
- redacted summary
- source refs
- provenance refs
- evidence refs
- receipt refs
- confidence posture
- stale posture
- review state
- lifecycle state
- suppressed/superseded refs
- affected surface refs
- blocked authority refs

Why next: this is where memory becomes real founder leverage instead of a queue.

### P6: FCC-MEM-021 Context-Pack Approval Handoff

Still do not auto-inject context. Build an approval handoff:

- context-pack preview diff
- included/excluded refs
- citation integrity status
- what surfaces would use it
- exact operator approval envelope
- safe disable
- rollback/ref invalidation
- Evidence Timeline event

Only after this milestone should UAA consider any scoped, reversible context
use. Even then, it should be exact-surface and exact-session, not global.

## Implementation Notes For FCC-MEM-016

The fastest useful implementation is a deterministic ranker over existing
Workbench items:

- lexical score is based on safe refs, tags, candidate kind, title, and bounded
  safe summary only
- recency score uses `created_at`
- quality pressure adds weight for conflict, duplicate, stale, missing evidence
- loop impact score uses FCC-MEM-015 `what_this_affects_refs`
- diversity score avoids showing ten variants of the same source/kind

Output example shape:

```json
{
  "schema_version": "fcc_mem_016_retrieval_diagnostics.v1",
  "query_ref": "query-ref:memory:founder-follow-ups",
  "ranked_candidates": [
    {
      "memory_ref": "business-memory-candidate:preference:founder-loop",
      "rank_score": 72,
      "score_refs": [
        "score-ref:lexical-kind-match",
        "score-ref:recent-capture",
        "score-ref:loop-impact",
        "score-ref:missing-evidence-pressure"
      ],
      "why_selected_refs": [],
      "why_excluded_refs": [],
      "blocked_state_refs": []
    }
  ],
  "semantic_search_enabled": false,
  "vector_db_enabled": false,
  "embedding_search_enabled": false,
  "model_provider_authority_allowed": false,
  "context_injection_authorized": false,
  "memory_write_authorized": false
}
```

## Risks To Avoid

Do not implement GoatCitadel-style raw fallback context in UAA yet.

Do not add vector search under the name "diagnostics." Semantic/vector search
needs a separate accepted milestone.

Do not let memory-derived follow-ups become Action Inbox approvals without a
separate envelope.

Do not let context-pack approval become global context injection.

Do not treat structured relationship memory as CRM truth.

Do not treat memory maintenance as permission to mutate the store.

## Final Recommendation

UAA should aim to become stronger than GoatCitadel by combining:

- GoatCitadel's practical runtime memory machinery
- UAA's governed review, evidence, and approval boundaries

The next best build is not semantic search. It is FCC-MEM-016 Retrieval
Diagnostics, followed by citation integrity, feedback/quality issue queues, and
proposal-only maintenance runs.

That sequence gives the memory module real teeth while keeping the mouth guard
in.
