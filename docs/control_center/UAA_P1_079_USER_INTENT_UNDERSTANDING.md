# UAA-P1-079 User Intent Understanding V1

Status: Implemented.

UAA-P1-079 adds a reviewable user-intent-understanding contract for the
Founder Command Center loop. It proposes intent metadata with confidence,
source refs, evidence refs, ambiguity posture, and ask/act/defer routing.

This milestone grants no new authority. Intent understanding is not hidden
authority, not approval, not memory truth, not context injection, not tool
execution, not action execution, not Code apply, not connector authority, not
provider/model authority, not public beta, and not production authority.
Short form: not hidden authority; No context injection.

## Contract

Contract ref: `contract-ref:user-intent-understanding:v1`.

The contract defines reviewable intent proposals with these required fields:

- `proposal_ref`
- `source_surface`
- `intent_label`
- `confidence_score`
- `confidence_band`
- `ambiguity_posture`
- `routing_decision`
- `source_refs`
- `evidence_refs`
- `dependency_refs`
- `required_contract_refs`
- `conflict_refs`
- `ask_user_question_ref`
- `next_safe_action`

Routing vocabulary:

- `ask`: ask the user before routing.
- `act`: route only to reviewable Action envelope metadata; it does not execute.
- `defer`: defer until memory, evidence, or source refs are reviewed.

Low-confidence or conflicting intent asks the user. It cannot route to act.

## Dependencies

User intent understanding depends on the reviewed loop, not raw model output:

- `contract-ref:memory-to-loop-binding:v1`
- `contract-ref:evidence-history-grammar:v1`
- `contract-ref:plans-action-envelope:v1`
- `contract-ref:chat-local-operator-surface:v1`
- `contract-ref:governed-code-workbench:v1`

The intent contract is visible in Today, Actions, Evidence, and Memory-facing
review surfaces through safe refs only.

## Authority Boundary

Required blocked refs:

- `blocked-state:no-hidden-intent-authority`
- `blocked-state:low-confidence-must-ask-user`
- `blocked-state:conflicting-intent-must-ask-user`
- `blocked-state:no-action-execution`
- `blocked-state:no-approval-grant-capture`
- `blocked-state:no-memory-write`
- `blocked-state:no-automatic-memory-write`
- `blocked-state:no-context-injection`
- `blocked-state:no-tool-execution`
- `blocked-state:no-provider-model-authority`
- `blocked-state:no-connector-write`
- `blocked-state:no-shell-subprocess-execution`
- `blocked-state:no-code-apply-execution`
- `blocked-state:no-broad-autonomy`
- `blocked-state:no-public-beta`
- `blocked-state:no-production-authority`

No action execution is authorized. No memory write is authorized. No context
injection is authorized. No provider/model authority is authorized.

## Surfaces

Today now shows:

- contract ref
- proposal count
- ask/act/defer routing vocabulary
- low-confidence and conflict ask-user posture
- hidden-authority and action-execution blockers
- proposal confidence and ambiguity posture
- dependency refs

Actions now shows:

- intent action gate
- proposal count
- low-confidence asks-user posture
- action execution blocked state
- blocked refs

Evidence Timeline now records user intent as history:

- what was proposed
- what was approved
- what happened
- what changed
- what can be undone
- what is stale
- what remains blocked

## Artifacts

- `src/ultimate_ai_agent/core/intent/user_intent.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `docs/schemas/user_intent_understanding.schema.json`
- `scripts/verify_uaa_p1_079_user_intent_understanding.py`
- `tests/test_uaa_p1_079_user_intent_understanding.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts`
- `apps/control-center/src/App.test.tsx`

## Verification

Required verification:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_079_user_intent_understanding.py tests/test_founder_loop_storage.py tests/test_control_center_founder_loop_api.py -q`
- `.venv/bin/python scripts/verify_uaa_p1_079_user_intent_understanding.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `make frontend-check`

## Next

The UAA-P1-067 through UAA-P1-079 Today-spine conveyor is complete after this
milestone is committed, pushed, and verified.

Next planned lane: UAA-P1-080 API Route Classification And Public/Protected
Inventory. That lane remains planned/queued until separately scoped and does
not grant middleware, auth, route authority, runtime authority, or production
authority by this document.
