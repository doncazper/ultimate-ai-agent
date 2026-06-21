# UAA-P1-069 Evidence History Grammar

Status: implemented contract/test/docs slice

UAA-P1-069 makes the Founder Loop Evidence Timeline read like history. It
extends the existing `GET /control-center/today/summary` payload and does not
add a new route, operation ID, backend mutation, frontend mutation control,
approval grant, rollback execution, connector runtime, model/provider call,
memory write, context injection, public beta, public distribution, production
readiness, or production authority.

## Contract

The evidence history grammar is identified by:

```text
contract-ref:evidence-history-grammar:v1
```

Every timeline item must answer the same seven questions:

- What was proposed?
- What was approved?
- What happened?
- What changed?
- What can be undone?
- What is stale?
- What remains blocked?

The approved and undoable answers are posture, not authority. Approval refs are
identifiers only. A later exact LocalApprovalAuthority scope must validate any
future approval. Rollback refs describe undo posture only and do not execute
rollback.

Rule: Approval refs are identifiers only.
Rule: Rollback refs describe undo posture only and do not execute rollback.

## Surface Bindings

Actions, Plans, Memory, Chat, and Code must all use this grammar for receipts,
audits, stale states, rollback posture, and blocked states.

- Actions currently bind the grammar through receipt, audit, replay, rollback,
  stale, and blocker refs.
- Plans remain partial until UAA-P1-073 Action envelopes.
- Memory uses the grammar as review metadata only; recall is not truth,
  approval, write authority, or context injection.
- Chat remains blocked until UAA-P1-074 local operator evidence exists.
- Code remains blocked until UAA-P1-075 governed diff and validation evidence
  exists.

## Safety

Evidence history uses safe refs and redacted summaries only. Durable evidence,
fixtures, docs, tests, and UI copy must not contain raw prompts, raw responses,
provider payloads, raw paths, raw logs, usernames, hostnames, account IDs,
credential material, or secret-like values.

Every evidence timeline item must keep these authority booleans false:

- `approval_ref_authority`
- `rollback_execution_enabled`
- `memory_truth_authority`
- `context_injection_authorized`
- `raw_evidence_included`

The `/evidence` surface remains read-only. It may show history answers, safe
refs, redacted summaries, route refs, and blockers, but it must not show
approve, run, write, send, sync, rollback, reveal-raw, or show-raw controls.

## Evidence

- Backend payload: `src/ultimate_ai_agent/core/storage/founder_loop.py`
- API route: `src/ultimate_ai_agent/api/founder_loop.py`
- Frontend type/render path: `apps/control-center/src/api/types.ts` and
  `apps/control-center/src/components/FounderLoopPanels.tsx`
- Route-status manifest: `docs/control_center/route_status_manifest.json`
- Schema: `docs/schemas/evidence_history_grammar.schema.json`
- Tests: `tests/test_founder_loop_storage.py`,
  `tests/test_control_center_founder_loop_api.py`,
  `tests/test_control_center_api_routes.py`, and
  `apps/control-center/src/App.test.tsx`
- Verifier: `scripts/verify_uaa_p1_069_evidence_history_grammar.py`
