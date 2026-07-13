# UAA-P1-079 User Intent Understanding V1

Status: Implemented; Runtime Capability Foundation Phase 01 hardened.

UAA-P1-079 adds a reviewable user-intent-understanding contract for the
Founder Command Center loop. It proposes intent metadata with confidence,
source refs, evidence refs, ambiguity posture, and ask/act/defer routing.

This milestone grants no new authority. Intent understanding is not hidden
authority, not approval, not memory truth, not context injection, not tool
execution, not action execution, not Code apply, not connector authority, not
provider/model authority, not public beta, and not production authority.
Short form: not hidden authority; No context injection.

## Runtime Capability Foundation Phase 01

The original V1 proposal catalog remains compatible, while current-request
reasoning now uses the separate typed
`contract-ref:intent-reasoning-truth:v1` contract. The deterministic builder:

- receives raw request text only as bounded transient input;
- persists only a safe request fingerprint and reviewed summaries/refs;
- separates facts, assumptions, unknowns, contradictions, and operator
  questions;
- derives confidence bands and rejects score/band or contradiction drift;
- marks all content, including instruction-shaped text, as untrusted data;
- uses the deterministic turn classifier with no runtime model call; and
- remains non-authoritative review truth.

The companion immutable decomposition and plan-revision binding covers ordered
membership, dependencies, targets, sources, definitions, lineage, predecessor
fingerprints, and safe revision reasons. Unchanged replay requires the exact
revision fingerprint. Changed membership, order, dependency, or target is
rejected unless represented by a new contiguous revision. A revision
invalidates old downstream authority assumptions and grants no new authority.

Operator parity reuses `GET /control-center/agent-loop/thread`, adds readable
`scripts/dev/uaa_founder_loop.py inspect-reasoning` output with optional
redacted JSON, and renders the same truth in the existing Today Agent Loop
panel. No new route, OpenAPI operation, route classification, model/provider
call, execution path, memory write, or context injection was added.
The stateless Agent Loop read projection uses content-addressed decomposition
and revision refs, so changed definitions, membership, order, dependencies, or
targets cannot reuse the same snapshot identity. It does not claim a
predecessor until a prior revision is explicitly supplied to the core
validator.

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
- `src/ultimate_ai_agent/core/intent/reasoning_truth.py`
- `src/ultimate_ai_agent/core/planning/revisions.py`
- `src/ultimate_ai_agent/core/control_center/agent_loop.py`
- `scripts/dev/uaa_founder_loop.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `docs/schemas/user_intent_understanding.schema.json`
- `scripts/verify_uaa_p1_079_user_intent_understanding.py`
- `tests/test_uaa_p1_079_user_intent_understanding.py`
- `tests/test_phase01_reasoning_truth.py`
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

The UAA-P1-067 through UAA-P1-082 conveyor is complete after UAA-P1-082 is
committed, pushed, and verified.

UAA-P1-080 API Route Classification And Public/Protected Inventory is complete.
UAA-P1-081 Centralized FastAPI Security Headers is complete. UAA-P1-082
Explicit Loopback CORS Allowlist is complete as browser hardening only. Next
planned lane: UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes.
That lane remains planned/queued until separately scoped and does not grant
enterprise auth, route authority beyond its exact sensitive-route scope,
runtime authority, rate limits, idempotency, or production authority by this
document.
