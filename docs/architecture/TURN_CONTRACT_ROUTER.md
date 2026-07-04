# Turn Contract Router

Status: phase-00 scope locked; planning/contract surface only
Scope: Turn Contract Router / Answer Preservation Router

This document defines the local UAA turn-contract boundary. It is not a
backend router, provider selector, runtime model invocation lane, or authority
grant. The Turn Contract Router decides the product contract for a user turn:
direct answer, base answer, reviewed-memory answer, draft/plan, read-only
tool/action preparation, approval boundary, exact approved execution posture,
clarification, or unsafe block.

## Phase 00 Scope Lock

Implementation home:

- Prefer `src/ultimate_ai_agent/core/decision_router/`.
- Reuse the existing no-effect top-level decision-router contract shape in
  `src/ultimate_ai_agent/core/decision_router/contracts.py`.
- Keep ModelRouter/backend/provider selection outside this UAA contract unless
  a later document explicitly discusses an external LLM/backend router.

Existing contracts to reuse:

- `DecisionRouterInput`, `DecisionRouterCandidate`,
  `DecisionRouterOutcome`, and `DecisionRouterTrace` for safe-ref-only,
  no-effect route decisions.
- `DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS` for no runtime model call,
  provider call, tool execution, action execution, workflow execution, memory
  write, context injection, shell/subprocess, browser/network, or connector
  write.
- `validate_safe_task_text`, `validate_safe_task_payload`, and
  `validate_task_ref` for redacted summaries and safe refs.
- Existing decision-router tests in
  `tests/test_uaa_p1_089_top_level_decision_router_contract.py` as the
  baseline for no-effect behavior and blocked authority preservation.

Focused test files to add or update:

- Add `tests/test_turn_contract_router_contracts.py` for typed turn contracts,
  capability firewall validation, and serialization.
- Add `tests/test_turn_contract_router_classifier.py` for the golden prompt
  table and deterministic serial classification.
- Add `tests/test_turn_contract_router_policy_compiler.py` for hard invocation
  constraints.
- Add `tests/test_turn_contract_router_executor_fence.py` for exact approved
  execution validation with no live execution.
- Add `tests/test_turn_contract_router_harness_binding.py` for safe harness
  binding read models.
- Add `tests/test_turn_contract_router_quality.py` for answer-preservation,
  latency, and product-language regressions.

Docs to update:

- Continue updating this document for phases 01 through 07.
- Keep release-facing truth in
  `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` only when the implementation
  becomes product-truth-relevant.
- Keep prompt-pack and side-discussion artifacts as planning inputs only; they
  do not grant runtime authority.

Naming lock:

- Use `base_answer`.
- Do not introduce `base_model`, `raw_model`, `raw_answer_draft`,
  `model_route_hint`, or `model_route_lane` for this UAA router.
- Use `direct_answer_draft`, `answer_profile_hint`, and
  `answer_profile_lane` when those concepts are needed.

Phase 1 implementation boundaries:

- Add typed contracts and capability firewall data only.
- Do not add classifier rules beyond construction helpers.
- Do not call an LLM, provider, or model backend.
- Do not execute tools.
- Do not read or write memory.
- Do not add connector writes, browser/network authority, shell/subprocess
  execution, API routes, public beta, public distribution, production
  readiness, or production authority.
- Prove `answer_directly` and `base_answer` compile to no memory, no tools, no
  planner, no durable state, and no approval requirement.
