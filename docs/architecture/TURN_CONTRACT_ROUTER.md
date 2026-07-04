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

## Phase 02 Deterministic Serial Classifier

Implemented classifier surface:

- `classify_turn_contract` accepts ephemeral turn text and returns a
  safe-ref-only `TurnDecision`.
- The classifier stores reason refs, risk flags, confidence, and safe
  summaries, not raw request text.
- The classifier is precompiled regex/rule based.
- It performs no LLM call, provider call, tool call, memory retrieval, durable
  write, shell/subprocess execution, browser/network access, connector write,
  or side effect.

Serial priority order:

1. `blocked_unsafe`
2. High-risk external side effect
3. Credential, payment, account, or privacy boundary
4. External side-effecting action
5. Explicit memory or personal-context request
6. Current, read-only tool, or research need
7. Draft or plan request
8. Explicit `base_answer` request unless it conflicts with safety/action
   boundaries
9. Clarifying question only when necessary
10. `answer_directly`

Signal policy:

| Signal group | Examples | Selected contract |
|---|---|---|
| Unsafe | phishing, malware, unauthorized access | `blocked_unsafe` |
| High-risk external side effect | buy, order, pay, checkout, book, reserve, submit | `approval_required` |
| Credential/payment/account/privacy | card, credentials, account, money, identity | `approval_required` |
| External or destructive action | send, email, message, upload, delete, overwrite | `approval_required` |
| Memory write request | remember this, save this | `approval_required` as the repo-safe review boundary |
| Memory read request | using what you know, my preferences, my office, last time | `answer_with_reviewed_memory` |
| Current/research need | latest, current, today, near me, search, cite sources | `prepare_tool_or_action` |
| Draft/plan | shopping list, proposal, outline, checklist | `draft_or_plan` |
| Explicit base answer | base answer path | `base_answer` unless a higher priority safety/action boundary applies |
| Ambiguous delegation | handle that thing, do the thing | `ask_clarifying_question` |
| Informational/software/DIY | DIY table, React component, Python function | `answer_directly` |

Golden regression table:

| Prompt | Expected contract | Required policy |
|---|---|---|
| How do I build a DIY table? | `answer_directly` | No memory, no tools, no planner, no state, no approval, normal useful answer. |
| Ask the base answer path: how do I build a DIY table? | `base_answer` | Minimal UAA wrapper; no memory/tools/planner/state; safety still applies. |
| Build me a React table component. | `answer_directly` | Code-style answer is fine. Do not route to operator/action mode. |
| Design one for my office using what you know. | `answer_with_reviewed_memory` | Reviewed relevant memory only; say "I do not know" when absent. |
| Remember that I prefer walnut. | `approval_required` | Repo-safe memory review boundary; no silent durable memory write. |
| Make me a shopping list for this table. | `draft_or_plan` | No purchase tools, no checkout, no external side effect. |
| Find current lumber prices near me. | `prepare_tool_or_action` | Read-only tools only; ask for location if unavailable. |
| Order the materials. | `approval_required` | Action envelope required; no execution tools until approval. |
| Use my card and book pickup at Home Depot. | `approval_required` | High purchase plus credential and booking risk; strong approval and brokered credential refs. |
| Send this to Alex. | `approval_required` | External communication boundary; no send before exact approval. |
| Delete these files. | `approval_required` | Destructive action boundary; no delete before exact approval. |
| Ask the base answer path: use my card and order this. | `approval_required` | `base_answer` must not bypass payment, credential, or action safety. |

## Phase 03 Invocation Policy Compiler

Implemented compiler surface:

- `compile_invocation_policy` converts every `TurnDecision` into an
  `InvocationPolicy` with hard constraints.
- `answer_directly` and `base_answer` compile to no memory, no tools,
  `tool_choice=none`, no planner, no durable state, no side effects, and no
  approval requirement.
- `answer_with_reviewed_memory` carries `memory_scope=reviewed_relevant_only`
  and keeps tools, side effects, and durable state disabled.
- `draft_or_plan` is draft/proposal only and side-effect free.
- `prepare_tool_or_action` exposes read-only/proposal posture only.
- `approval_required` exposes an envelope-building posture only and requires
  exact approval before any later execution.
- `execute_approved_action` carries exact approved scope refs and requires a
  receipt/action log posture.

Exact approved execution scope:

| Scope field | Purpose |
|---|---|
| `approval_scope_ref` | The exact approval boundary. |
| `action_scope_ref` | The exact action boundary. |
| `tool_ref` | The exact approved tool ref. |
| `arguments_ref` | The exact approved arguments ref. |
| `merchant_ref` | The exact merchant or not-applicable ref. |
| `recipient_ref` | The exact recipient or not-applicable ref. |
| `account_ref` | The exact account or broker ref. |
| `cost_ref` | The exact cost or not-applicable ref. |
| `risk_ref` | The exact reviewed risk-class ref. |

Compiler no-broadening rule:

```text
For execute_approved_action, every allowed_* ref in InvocationPolicy must match the embedded ApprovedExecutionScope. Any widened merchant, recipient, account, cost, tool, argument, or risk ref is invalid before execution.
```

## Phase 04 ExecutorFence Contract

Implemented fence surface:

- `ExecutorFenceRequest` carries a current `InvocationPolicy` plus the exact
  requested approval, action, tool, arguments, merchant, recipient, account,
  cost, credential broker, and risk refs.
- `evaluate_executor_fence` returns an `ExecutorFenceDecision`.
- The fence performs no execution. It is a validation contract any future
  side-effect lane must pass before execution can be considered.

Fence validation:

| Check | Requirement |
|---|---|
| Approval | Policy must be `execute_approved_action` with `already_approved_exact_scope`. |
| Action id | Requested action scope must match the approved action scope. |
| Tool | Requested tool must match the exact approved tool and policy tool list. |
| Arguments | Requested arguments must match the exact approved arguments ref. |
| Merchant/cost | Merchant and cost refs must match the approved envelope. |
| Recipient/account | Recipient and account refs must match the approved envelope. |
| Credential broker | Credential broker ref must match the approved envelope. |
| Risk | Risk-class ref must match the approved envelope. |
| Receipt posture | Receipt and action-log posture are required for a fence pass. |

Still blocked:

- Live execution route
- Side-effecting tool call
- Connector write
- Email send
- Payment action
- Booking action
- Shell/subprocess execution
- Browser action
- Provider/model call

## Phase 05 Harness Binding Read Model

Implemented binding surface:

- `build_turn_harness_binding` classifies a turn, compiles the invocation
  policy, and returns a `TurnHarnessBindingReadModel`.
- The read model exposes safe summaries, reason refs, evidence refs, risk
  flags, memory/tool/state posture, approval posture, and no-effect proof
  flags.
- The read model does not persist raw request text, raw response text, raw
  memory bodies, local paths, credentials, or secret-like values.
- The read model does not retrieve memory content or execute tools.

Binding shape:

| Field | Meaning |
|---|---|
| `turn_contract` | Selected contract from the deterministic classifier. |
| `memory_touched` | Whether memory content was actually accessed; false in this repo-safe binding. |
| `reviewed_memory_refs_allowed` | Whether reviewed/scoped memory refs may be considered by a later approved lane. |
| `tools_exposed_count` | Count of non-executing refs exposed by policy. |
| `execution_tools_exposed_count` | Count of execution-capable tools exposed; zero except exact approved execution. |
| `planner` | Whether a planner posture is allowed by the policy. |
| `durable_state` | Whether the policy allows durable state posture. |
| `approval_required` | Whether an approval envelope is required before a future action. |
| `approval_envelope_required` | Whether the output contract is an approval envelope. |
| `side_effects_allowed` | Whether the policy has exact approved side-effect posture. |
| `execution_ready` | Whether the policy is ready for an ExecutorFence check. |

Required current behavior:

| Prompt class | Binding result |
|---|---|
| Direct/base answer | `memory_touched=false`, `tools_exposed_count=0`, `planner=false`, `durable_state=false`, `approval_required=false`. |
| Reviewed-memory answer | Reviewed memory refs may be allowed, but memory content is not retrieved and no silent memory write occurs. |
| Approval boundary | Approval envelope posture is visible and execution tools remain absent. |
