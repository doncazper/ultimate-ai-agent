# FCC-MEM-015 Memory Impact Graph And Follow-Up Queue

Status: implemented safe read-model slice.

FCC-MEM-015 advances Memory Review from an isolated reconciliation queue into a
backend-owned operator surface that shows how a memory candidate connects to the
Founder Loop. The slice is read-only except for already-existing Memory Review
receipt decisions and manual candidate intake.

## Implemented Contracts

- `GET /control-center/memory/impact-graph`
  - Contract ref: `contract-ref:fcc-mem-015-memory-impact-graph:v1`
  - Builds `memory_ref -> Today refs -> Action proposal refs -> Briefing refs -> Evidence event refs -> context-pack preview refs`.
  - Includes `changed_refs`, `suppressed_refs`, `stayed_blocked_refs`, and `affected_surface_refs` for lifecycle clarity.
- `GET /control-center/memory/follow-ups`
  - Contract ref: `contract-ref:fcc-mem-015-memory-follow-up-queue:v1`
  - Returns ranked memory-derived follow-up candidates grouped by relationship, commitment, stale promise, missing evidence, correction, defer, and forget-request posture.
  - Candidates are proposal-only and require separate Action Inbox approval before any future action lane.
- `GET /control-center/memory/recall-health`
  - Returns Recall Health Dashboard V2 counts: reviewed recall, stale pressure, duplicate pressure, conflict pressure, missing evidence, defer aging, forget-request aging, suppression count, and top memories driving the current loop.

## Backend Read Model

The Python core builds FCC-MEM-015 from existing local read models:

- Memory Workbench items and decision receipts.
- Today memory-to-loop bindings and memory-derived action proposals.
- Actions Inbox memory-derived proposal refs.
- Morning Briefing memory refs and section refs.
- Evidence Timeline lifecycle events.
- Context-pack proposals.

The read model is safe-ref-only and does not perform semantic search,
embeddings, provider/model calls, web fetching, connector IO, CRM/account sync,
context injection, action execution, memory writes, deletes, or exports.

## Control Center UI

Memory Review now includes:

- Recall Health V2 pressure metrics and top current-loop memory refs.
- Impact Graph rows showing what each memory affects across Today, Actions,
  Briefing, Evidence, and context-pack previews.
- Merge / Supersede multi-select comparison over duplicate and conflict peers.
- Proposal-only follow-up queue inspection.
- Context-pack preview inspection with context injection blocked.
- Manual candidate intake remains review-queue-only.

UI state is presentation-only. Product behavior comes from Python core routes and
typed API contracts.

## CLI Parity

Repo-local inspection commands:

- `scripts/dev/uaa_founder_loop.py memory-impact-graph`
- `scripts/dev/uaa_founder_loop.py memory-follow-ups`
- `scripts/dev/uaa_founder_loop.py memory-recall-health`

The commands omit raw paths/content and return safe-ref JSON projections.

## Safety Boundaries

FCC-MEM-015 explicitly blocks:

- Auto-code, auto-apply, shell/subprocess execution, browser automation, and
  provider/model authority.
- Context injection and hidden prompt stuffing.
- Memory writes, deletes, exports, and automatic recall-as-truth behavior.
- Connector writes, CRM/account sync, scheduling, and action execution.
- Semantic/vector search, embeddings, vector DB, and background indexing.
- Public beta, public distribution, and production authority claims.

Memory remains recall and operator-reviewed state, not truth or authority.

## Remaining Future Lanes

- Deeper Evidence Timeline polish for richer lifecycle answer rows.
- Relationship schema expansion for CRM-lite refs beyond safe relationship,
  org, person, deal, commitment, and promise refs.
- Exact accepted milestone for context injection, if ever allowed, with approval,
  rollback/safe-disable, receipts, and Evidence proof.
- Separate accepted milestone for semantic/vector search and provider boundaries.
