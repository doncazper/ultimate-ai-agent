# FCC-MEM-015 Memory Impact Graph And Follow-Up Queue

Repository: this repository.

Goal: advance the governed Memory module from a review workbench into an
operator-grade reconciliation cockpit. Build a backend-owned, safe-ref-only
Memory Impact Graph and proposal-only Follow-Up Queue that show what reviewed
memory affects across Today, Actions, Morning Briefing, Evidence, Memory
Review, and context-pack proposals. Preserve every existing safety boundary:
memory remains governed recall, not truth, authority, execution, connector
state, or hidden prompt context.

This prompt extends FCC-MEM-001. It must not replace or weaken the completed
Memory Workbench, lifecycle receipts, quality grouping, search/filter, manual
intake, CLI parity, or verifier coverage.

## Required First Audit

Before editing code, inspect:

- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`
- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `tests/test_fcc_mem_001_memory_workbench.py`
- `tests/test_uaa_p1_077_memory_to_loop_binding.py`
- `tests/test_governed_memory_context_pack_proposals.py`

Then write or update a scoped spec:

`docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`

The spec must distinguish implemented, partial, planned, blocked, and
out-of-scope states. It must explicitly reconcile the current correction-text
contract tension: if bounded `corrected_safe_summary` is stored in receipts,
docs must say so consistently; if only `corrected_summary_ref` is authoritative,
docs and UI must not imply corrected text is durable product truth.

## Implementation Scope

### 1. Merge / Supersede Multi-Select UX

Backend merge and supersede receipts already exist. Add the operator UX that is
still missing:

- A safe candidate picker in `/memory` for selecting two or more local
  candidates or reviewed recall projections.
- Side-by-side duplicate/conflict comparison cards.
- Visible source refs, evidence refs, quality refs, stale/conflict posture,
  receipt refs, and blocked-state refs for every selected peer.
- Merge and supersede controls that call existing backend lifecycle routes only.
- Receipt display after merge/supersede, including which refs were suppressed
  or marked superseded.

Constraints:

- React selection state is presentation only.
- Backend receipts remain the source of truth.
- No silent deletion.
- No memory export/delete execution.
- No raw content display.

### 2. Memory Impact Graph Read Model

Build a backend-owned read model, likely exposed as:

`GET /control-center/memory/impact-graph`

The read model must map safe refs like:

`memory_ref -> Today items -> Action proposals -> Briefing refs -> Evidence events`

Minimum contract fields:

- `schema_version`
- `contract_ref`
- `route_ref`
- `generated_at`
- `safe_refs_only`
- `memory_ref`
- `review_ref`
- `review_state`
- `candidate_kind`
- `relationship_refs`
- `commitment_refs`
- `promise_refs`
- `source_refs`
- `provenance_refs`
- `evidence_refs`
- `today_item_refs`
- `action_proposal_refs`
- `briefing_refs`
- `evidence_event_refs`
- `context_pack_refs`
- `why_shown_refs`
- `what_this_affects_refs`
- `stale_state_refs`
- `quality_state_refs`
- `blocked_state_refs`
- `next_safe_action`

The graph may derive refs from existing Today, Actions, Briefing, Evidence,
Memory Workbench, L1/L2/L3, memory-to-loop binding, and context-pack proposal
read models. It must not inspect raw content or invent hidden relationships.

### 3. Recall Health Dashboard V2

Extend the Memory Workbench health summary or add a nested V2 health section.
It must include:

- reviewed recall count
- pending review count
- stale pressure
- duplicate pressure
- conflict pressure
- missing evidence pressure
- defer aging
- forget-request aging
- merge/supersede suppression count
- top memories driving the current loop
- top relationship refs needing attention
- top commitment or stale-promise refs needing attention

All pressure scores must be deterministic, ref-based, and explainable with
`health_reason_refs`. No model/provider scoring, embeddings, semantic search, or
private source inspection.

### 4. Evidence Timeline Memory Polish

Every memory lifecycle event must answer:

- What changed?
- What was suppressed?
- What stayed blocked?
- Which surfaces are affected?

This must be especially clear for:

- `correct`
- `merge`
- `supersede`
- `forget_request`
- `defer`

Use safe refs and redacted summaries only. Evidence Timeline events must not
claim memory truth, delete/export execution, context injection, CRM sync, or
Action execution.

### 5. Memory-Derived Follow-Up Queue

Create a sharper proposal-only queue for reviewed-memory follow-ups. This may
be nested in the impact graph or exposed as:

`GET /control-center/memory/follow-ups`

Group candidates by:

- relationship
- commitment
- stale promise
- missing evidence
- recently corrected preference
- deferred review
- forget-request follow-up

Each follow-up candidate must include:

- `follow_up_ref`
- `source_memory_refs`
- `relationship_refs`
- `commitment_refs`
- `action_proposal_ref` or `action_candidate_ref`
- `why_shown_refs`
- `what_this_affects_refs`
- `proposal_only`
- `approval_required_before_action`
- `action_execution_authorized=false`
- `connector_write_authorized=false`
- `memory_write_authorized=false`
- `context_injection_authorized=false`
- `production_authority_enabled=false`

The queue can create or surface Action Inbox proposal refs only. It must not
execute, schedule, send, sync, or mutate external systems. Any later Action
must go through the existing Action Inbox approval envelope path.

### 6. Manual Memory Intake Ergonomics

The backend manual candidate route already exists:

`POST /control-center/memory/review/manual-candidate`

Improve the `/memory` UI around it:

- Quick-add panel.
- Missing-evidence reason selector.
- Source ref picker or controlled input.
- Provenance ref picker or controlled input.
- Tag refs.
- Entity refs for person/org/deal/project/relationship/commitment.
- Review-later posture.
- Safe preview before submit.
- Receipt and replay/conflict display after submit.

All inputs must be safe refs or bounded safe summaries accepted by existing
backend validators. No raw note storage.

### 7. Memory CRM-Lite / Relationship Layer

Add a tighter relationship/follow-up schema lane without CRM/account sync.
Represent safe refs for:

- people
- organizations
- deals/opportunities
- projects
- relationships
- commitments
- promises
- follow-ups
- stale relationship posture
- "you said you would" loop refs

This can be a read-model schema or contract helper used by the impact graph and
follow-up queue. It must remain local, safe-ref-only, reviewable, and
proposal-only. It must not write to external CRM systems, contacts, accounts,
email, calendar, messages, or connectors.

### 8. Context-Pack Preview Handoff

Keep context injection blocked, but make context packs inspectable and
comparable as proposal artifacts.

Add UI/read-model support for:

- context-pack preview cards
- included memory refs
- excluded memory refs
- inclusion reason refs
- exclusion reason refs
- stale/conflict posture
- evidence refs
- affected Today/Action/Briefing/Evidence refs
- exact approval posture for the existing internal Action proposal hook

The operator should be able to understand: "Here is the pack I would use, here
is why, here is what it excludes." Actual prompt/context injection remains
blocked and requires a separate accepted milestone with exact approval,
idempotency, receipt refs, rollback/safe-disable posture, and Evidence proof.

## Explicitly Blocked / Out Of Scope

Do not add:

- memory delete execution
- memory export execution
- semantic search
- vector DB
- embeddings
- model/provider extraction or scoring
- connector reads or writes
- CRM/account/contact sync
- email/calendar/message send, archive, delete, label, move, or draft execution
- hidden or automatic context injection
- action execution
- scheduling/background automation
- browser automation
- shell/subprocess execution
- public beta, public distribution, production readiness, or production
  authority

Semantic/vector search is intentionally out of scope for FCC-MEM-015. If it is
desired later, create a separate milestone for embeddings/vector-store/provider
boundaries and safety proof.

## Backend Tasks

Implement backend-owned contracts/read models for:

- Memory Impact Graph.
- Recall Health Dashboard V2.
- Memory-derived Follow-Up Queue.
- Relationship/commitment/follow-up safe-ref helpers.
- Context-pack preview/handoff posture.

Use existing storage/read-model sources where possible:

- Memory Workbench items.
- Memory Review queue and receipts.
- Reviewed recall-only records.
- L1/L2/L3 indexes.
- Context-pack proposals.
- Today summary.
- Actions Inbox.
- Morning Briefing summary.
- Evidence Timeline.
- Memory-to-loop binding.

Update route classification, OpenAPI/API manifest, route status manifest,
release surface manifest, and type definitions for any new route.

## Frontend Tasks

Update `/memory` so it becomes an operator-grade reconciliation cockpit:

- Multi-select merge/supersede picker.
- Duplicate/conflict comparison cards.
- Impact graph section.
- Recall health V2 section.
- Follow-up queue section.
- Manual intake quick-add section.
- Relationship/commitment ref chips.
- Context-pack preview comparison cards.
- Receipt/replay/conflict states after decisions.

Do not use raw JSON as the primary UI for operator-critical flows. Fallback/mock
data must be labeled non-authoritative and must not expose mutation controls.

## CLI Tasks

Add repo-local CLI parity in `scripts/dev/uaa_founder_loop.py` for:

- inspect memory impact graph
- inspect memory follow-up queue
- inspect recall health V2
- inspect context-pack preview refs

CLI output must be safe-ref-only, omit raw paths, and provide blocked states.

## Tests

Add or extend focused tests for:

- impact graph maps memory refs to Today, Actions, Briefing, and Evidence refs
  without raw content
- recall health V2 counts and pressure reason refs
- merge/supersede multi-select UI and receipt display
- duplicate/conflict side-by-side comparison UI
- memory-derived follow-up queue is proposal-only and cannot execute
- manual intake quick-add uses safe refs and preserves replay/conflict behavior
- relationship/commitment/stale-promise grouping
- context-pack preview inclusion/exclusion refs and no context injection
- Evidence Timeline memory events answer changed/suppressed/blocked/affected
  questions
- OpenAPI/API manifest route coverage for new endpoints
- frontend fallback does not expose authoritative mutation controls

## Verification Commands

Run focused checks first:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_mem_001_memory_workbench.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_077_memory_to_loop_binding.py tests/test_governed_memory_context_pack_proposals.py -q
.venv/bin/python scripts/verify_fcc_mem_001_memory_workbench.py
.venv/bin/python scripts/verify_fcc_v1_005_memory_review_decisions.py
.venv/bin/python scripts/verify_uaa_p1_077_memory_to_loop_binding.py
```

Then add and run a new verifier:

```bash
.venv/bin/python scripts/verify_fcc_mem_015_memory_impact_graph_followup_queue.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_mem_015_memory_impact_graph_followup_queue.py -q
```

Run adjacent checks after route/UI changes:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```

If a command is blocked by the local environment, report the blocker and do not
claim success.

## Documentation Updates

Update the smallest relevant docs:

- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md` if correction semantics
  need reconciliation
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/kanban/current_board.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/DOCUMENTATION_INDEX.md`
- `docs/README.md`
- route/release/manifest docs touched by new routes

Product language must say local functional/review/proposal behavior only. Do
not claim production readiness, automatic truth, context injection, connector
authority, semantic search, delete/export execution, or action execution.

## Definition Of Done

- FCC-MEM-015 has a documented contract and read model.
- Merge/supersede UX supports multi-select and comparison over safe refs.
- Impact graph shows what reviewed memory affects across Today, Actions,
  Briefing, and Evidence.
- Recall Health V2 exposes deterministic pressure and aging refs.
- Evidence Timeline memory events answer changed/suppressed/blocked/affected.
- Follow-up queue surfaces ranked proposal-only candidates.
- Manual intake UI is ergonomic but still backend-owned and safe-ref-only.
- Relationship/CRM-lite refs are local review posture only.
- Context-pack previews explain inclusions/exclusions without injection.
- Focused tests, verifiers, docs, OpenAPI/API manifest, CLI parity, and frontend
  checks pass or blockers are reported.
- No blocked authority is enabled.
