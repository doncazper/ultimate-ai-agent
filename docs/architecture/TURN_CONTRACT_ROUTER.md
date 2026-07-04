# Turn Contract Router

Status: phase-01 contracts added; planning/contract surface only
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

## Phase 01 Contracts And Capability Firewall

Implemented contract surface:

- `TurnContractKind` enumerates the user-facing turn contracts.
- `TurnDecision` stores the safe-ref-only router result and no-effect proof
  flags.
- `InvocationPolicy` stores compiled capability constraints.
- `compile_invocation_policy` maps a typed decision into hard constraints
  without classifier rules, model/provider calls, tools, memory reads, shell,
  browser/network, connector writes, or API routes.

Protected direct-answer rule:

```text
For answer_directly and base_answer:
memory_scope=none, tools=[], tool_choice=none, planner=false, durable_state=false, approval_required=false.
```

Core invariant:

```text
A later layer may reduce permissions, but it may never increase permissions beyond the TurnContractRouter's selected capability gate.
```

### Turn Contract / Capability Gate Table

This is the user-experience contract. The default is lightweight. UAA
escalates only when the request needs memory, planning, current information,
tools, approval, or execution.

| Turn contract | Example prompt | Memory | Tools | State | Approval | Expected feel |
|---|---|---|---|---|---|---|
| `answer_directly` | How do I build a DIY table? | No | No | Ephemeral only | No | Normal helpful LLM answer. No ceremony. |
| `base_answer` | Answer this with the base answer path. | No | No | Ephemeral only | No | Minimal UAA wrapper. Useful for comparison or low-ceremony work. |
| `answer_with_reviewed_memory` | Design one for my office using what you know. | Reviewed relevant only | Usually no | No durable state by default | No | Personalized answer, with memory refs or "I do not know." |
| `draft_or_plan` | Make me a shopping list for this table. | Optional if triggered | Maybe draft/proposal tools | Draft state only | No execution | Helpful plan, list, proposal, or checklist. No external effects. |
| `prepare_tool_or_action` | Find current lumber prices near me. | Optional/relevant only | Read-only tools only | Maybe proposal state | No side effects | Research or action prep. Side-effect tools still blocked. |
| `approval_required` | Order the materials. | Scoped/relevant only | Read-only/envelope prep only | Action envelope | Required | Consequence boundary: "approve this exact action?" |
| `execute_approved_action` | Yes, place that exact order. | Scoped to approval | Exact approved tool only | Receipt/action log | Already approved | Execution-only and exact-scope. No expansion. |
| `ask_clarifying_question` | Handle that thing for me. | No unless needed | No | No | No | Clarify only when direct answer would be wrong or unsafe. |
| `blocked_unsafe` | Unsafe or disallowed request. | No | No | No | N/A | Safe refusal or safe alternative. |

### Stricter Capability Firewall - Authority And Context

If the router chooses `answer_directly` or `base_answer`, UAA memory and tools
are physically absent.

| Capability | `answer_directly` | `base_answer` | `answer_with_reviewed_memory` | `draft_or_plan` | `prepare_tool_or_action` | `approval_required` | `execute_approved_action` |
|---|---|---|---|---|---|---|---|
| Plain LLM reasoning | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| UAA memory read | No | No | Reviewed relevant only | Only if triggered | Only if triggered | Scoped/relevant only | Scoped to approval |
| UAA memory write | No | No | No by default | No by default | No | Proposal/review only | Only if approved |
| Private file/context injection | No | No | Only if requested/relevant | Optional, scoped | Optional, scoped | Scoped | Scoped to approval |
| Personalization disclosure | No | No | Yes, disclose refs used | If memory used | If memory used | Yes if used in envelope | Receipt if relevant |
| Clarifying question | Rare | Rare | If memory gap matters | If plan scope unclear | If tool inputs missing | If approval scope unclear | If approved scope mismatches |

### Stricter Capability Firewall - Tools, State, And Side Effects

Side-effecting execution only appears in the exact approved execution contract.
An LLM suggestion is never authority by itself.

| Capability | `answer_directly` | `base_answer` | `answer_with_reviewed_memory` | `draft_or_plan` | `prepare_tool_or_action` | `approval_required` | `execute_approved_action` |
|---|---|---|---|---|---|---|---|
| Read-only tools | No | No | Usually no | Maybe | Yes | Maybe for envelope | Maybe, if approved |
| Side-effecting tools | No | No | No | No | No | No execution | Exact approved tool only |
| Planner loop | No | No | No | Lightweight only | Maybe | Yes, for envelope | Execution-only |
| Durable task state | No | No | No | Draft state only | Maybe proposal state | Action envelope | Receipt/action log |
| External send/order/book/delete | No | No | No | No | No | Proposed only | Exact approved scope |
| Credentials/payment handles | No | No | No | No | No | Broker refs only | Brokered and scoped |
| Approval envelope | No | No | No | No | Maybe proposal | Required | Already approved |
| Evidence/citations | No by default | No by default | Memory refs if used | Optional | Sources if used | Required for scope | Receipt required |

Execution fence:

```text
Before any side effect, revalidate approved action id, tool name, arguments, merchant, recipient, account, cost, credential broker refs, and risk class. Reject any unapproved expansion.
```
