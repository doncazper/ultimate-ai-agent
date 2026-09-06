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
| `credential_broker_ref` | The exact credential broker or not-applicable ref. |
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
- `ExecutorFenceRequest` also carries the exact `LocalApprovalAuthority`
  validation request, approval ref, validation scope ref, validation receipt
  ref, and validation status ref. Matching strings alone are not enough:
  `evaluate_executor_fence` must receive a `LocalApprovalAuthority` that can
  validate the exact approval request before the fence can pass.
- `evaluate_executor_fence` returns an `ExecutorFenceDecision`.
- The fence performs no execution. It is a validation contract any future
  side-effect lane must pass before execution can be considered.

Fence validation:

| Check | Requirement |
|---|---|
| Approval | Policy must be `execute_approved_action` with `already_approved_exact_scope`. |
| Local approval | LocalApprovalAuthority must validate the exact approval ref, subject, actor, action, risk, data classification, and all policy resource refs. |
| Validation receipt | Validation receipt ref must bind to the exact approval ref and approval-scope ref. |
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
- `build_chat_turn_harness_binding` binds the same no-effect router metadata to
  the local `/v1/chat/completions` path after chat request validation and before
  the local response builder returns.
- Local chat responses expose the binding only under `uaa_safety` as safe
  metadata; prompt text is not used in persisted refs.
- Durable Chat receipts store a receipt-safe binding projection with selected
  contract, memory/tool, approval, blocked-authority, and no-effect fields. The
  no-effect scope is explicitly `turn_harness_binding_compilation_only`, so it
  describes router binding construction and not the whole local chat response
  lifecycle. The projection omits `raw_*` storage keys while preserving false
  body-persistence proof fields.
- The read model exposes safe summaries, reason refs, evidence refs, risk
  flags, memory/tool/state posture, approval posture, and no-effect proof
  flags.
- The read model does not persist raw request text, raw response text, raw
  memory bodies, local paths, credentials, or secret-like values.
- The read model does not retrieve memory content or execute tools.
- The binding does not make Chat output authoritative and does not grant memory
  reads, memory writes, tool execution, action execution, shell/subprocess
  execution, browser/network authority, connector writes, or provider/model
  authority.

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

## Phase 06 Quality, Latency, And Product Language

Answer-preservation checks:

- Normal informational prompts must stay in `answer_directly` unless a higher
  priority safety, memory, current-info, or approval boundary applies.
- Direct/base answer bindings must report no memory touch, no tools, no
  planner, no durable state, and no approval requirement.
- Direct answers must use `plain_answer`, not approval-envelope language.
- `base_answer` remains a low-ceremony answer path and does not bypass
  payment, credential, account, send, delete, booking, or purchase boundaries.

Latency posture:

- The classifier is deterministic and precompiled.
- The focused guard expects low-millisecond classification.
- The guard uses no provider calls, LLM calls, memory retrieval, network
  access, browser action, connector write, or shell/subprocess execution.

Product-language posture:

- This contract does not claim public release, production readiness, broad
  autonomy, purchase execution, booking execution, send execution, credential
  handling, account mutation, or connector writes.
- Purchase, booking, send, credential, and account actions remain blocked until
  an exact future authority lane implements approval, fence, execution,
  receipt, rollback/safe-disable, redaction, and proof.
- The Phase 00 naming lock remains binding: this router uses `base_answer` and
  `answer_profile_hint` language for UAA turn contracts.

## Phase 07 Cheap Parallel Preflight

Status: contract and no-effect engine implemented. No product runtime
authority, provider/model call, tool execution, memory content retrieval,
context injection, shell/subprocess behavior, browser/network action, connector
write, public beta, public release, production readiness, or standing autonomy is
implemented by this section.

Prompt 01 productization adds typed parallel preflight contracts in
`src/ultimate_ai_agent/core/decision_router/parallel_preflight.py` without
adding the engine. The contracts are safe-ref-only, no-effect Pydantic models
for lane results, bundles, arbitration input, and arbitration result. They make
lane outputs inspectable while preserving the core invariant:

```text
Parallelize sensing. Centralize authority. Serialize execution.
```

Contract truth:

- A preflight lane cannot grant authority.
- A preflight lane cannot permit execution.
- A preflight lane or arbitration result cannot select `execute_approved_action`;
  that contract remains available only through exact approved scope,
  `InvocationPolicy`, and `ExecutorFence` validation.
- A preflight lane cannot retrieve raw memory content.
- A preflight lane cannot call a model, provider, browser, connector, shell,
  subprocess, or tool.
- A preflight lane cannot run workflows or inject context.
- A preflight lane cannot persist raw prompt, response, memory, tool, log,
  credential, or local-path content.
- `direct_answer_draft` lane output is never user-visible unless central
  arbitration explicitly clears a direct/base answer posture in a later phase.
- No product runtime authority is implemented by the preflight layer. Prompt
  02 adds the no-effect engine and keeps execution authority blocked.

Prompt 02 productization adds `run_parallel_turn_preflight` and
`run_parallel_turn_preflight_async`. The engine runs deterministic no-effect
lanes with `asyncio.gather`, centralizes arbitration, compiles exactly one
`InvocationPolicy`, and returns safe refs plus bounded latency buckets. Failing
lanes fail closed to approval posture. A risk/action lane veto can escalate a
low-ceremony intent to approval-required, but no lane can increase authority,
execute work, expose tools for direct answers, retrieve memory bodies, or make
`direct_answer_draft` user-visible before central arbitration.

Prompt 03 productization adds the backend-owned no-effect preview read model
and inspection surfaces: `POST /control-center/turn-router/preview` and
`scripts/dev/uaa_turn_router.py`. These surfaces can classify protected samples
or ephemeral request text for immediate operator diagnostics, but they return
safe refs, selected contract, policy posture, no-effect proof flags, and
redaction refs only. They do not persist raw request text, wire chat runtime,
call providers/models, execute tools/actions, retrieve memory bodies, inject
context, run shell/browser work, or write connectors.

Prompt 04 productization exposes that same preview contract in the Control
Center Chat surface as Router Diagnostics. The panel calls the backend-owned
preview route for protected samples, labels fallback previews as
non-authoritative mock data, and renders selected contract, reason refs,
memory/tool/state/approval posture, blocked authority refs, and no-effect proof
without making raw JSON the primary UI. The optional free-form preview input is
ephemeral UI state only; it is cleared after submission, rejects secret-like
input locally, and does not save raw text to fixtures, logs, local storage, or
durable evidence. The panel adds no chat runtime routing, provider/model call,
tool/action execution, memory retrieval/write, shell/browser work, connector
write, public release, or production authority.

Prompt 05 productization binds the selected turn contract into the local Chat
harness metadata before downstream response handling. The binding is a
safe-ref-only read model under `uaa_safety` and a receipt-safe projection in
the durable Chat receipt. It controls memory/tool/state/approval posture for
the turn, but it still performs no tool/action execution, memory write,
context injection, provider SDK call, browser/network work, connector write,
or production authority.

Prompt 06 productization adds a repeatable local browser smoke harness:

```bash
make frontend-turn-router-smoke
```

The harness runs Playwright against the local Control Center dev server and
fixtures only the safe backend read models needed by `/chat`. It verifies that
Router Diagnostics loads, protected sample prompts keep their expected
contracts, DIY desk/table stay lightweight, approval boundaries are visible
for order/card prompts, Chat displays the no-effect harness binding receipt,
raw JSON is not the primary UI, console errors stay clean, and unsupported
authority claims are absent on desktop and mobile viewports. The smoke harness
is implementation-time QA only; it does not grant UAA product runtime browser
automation, browser observe/action authority, web fetch, connector write,
provider/model authority, or standing autonomous operation.

Prompt 07 hardening adds the final productization regression sweep: broader
approval-boundary classifier coverage for memory writes, calendar/task/reply/
delete/reorder wording, required complete preflight lane bundles, hashed chat
harness route/model refs, LocalApprovalAuthority-backed executor fence
validation, bound approval-validation receipt refs, fail-closed Control Center
preview fallback, stricter preview payload validation, unexpected-route smoke
assertions, route-boundary normalization, and Foundation Gate hygiene.

## How To Smoke Test Turn Contract Router

Run the local browser smoke harness:

```bash
make frontend-turn-router-smoke
```

Expected result:

- `/chat` loads Router Diagnostics from the backend-owned preview route fixture.
- Protected sample buttons preserve the expected contracts for DIY desk,
  office memory, shopping list, current lumber prices, order materials, card
  and pickup, and base-answer bypass.
- The ephemeral preview input omits raw text and a failed free-form preview
  falls closed to a non-authoritative approval-boundary fallback instead of
  reusing stale sample truth.
- Chat displays the no-effect harness binding receipt and does not expose raw
  prompt/response JSON as the primary UI.
- Unsupported authority claims, unexpected API routes, console errors, raw
  JSON primary UI, provider/model authority, browser automation, connector
  writes, shell/subprocess execution, and action execution are absent.

For the broader local product check, run:

```bash
make frontend-check
make frontend-visual-check
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
```

Preflight lanes:

| Lane | Runs when | May read memory content? | May execute tools? | User-visible? | Output |
|---|---|---|---|---|---|
| `intent_lane` | Every turn | No | No | No | Candidate turn contract and confidence. |
| `risk_action_lane` | Every turn | No | No | No | Risk flags and veto/escalation signal. |
| `memory_trigger_lane` | Every turn | No | No | No | Whether memory relevance is allowed. |
| `memory_relevance_lane` | Only after memory trigger | Reviewed/scoped refs only | No | No | Candidate memory refs, not injected content. |
| `tool_manifest_lane` | Every turn | No | No | No | Read-only or side-effect tool category candidates. |
| `answer_profile_lane` | Optional | No | No | No | `answer_profile_hint` within the selected contract. |
| `direct_answer_draft` | Future low-risk turns only | No | No | No, until gates clear | Cancelable direct-answer draft. |

Preflight rules:

- Parallelize sensing.
- Centralize authority.
- Serialize execution.
- Do not execute side effects during preflight.
- Do not retrieve memory content unless `memory_trigger_lane` permits the
  later scoped memory lane.
- Do not expose any `direct_answer_draft` to the user until risk and
  side-effect gates clear.
- Treat every lane output as proposal/read-only evidence for the central turn
  contract, not as execution authority.

Explicit non-goals:

- No live provider/model call
- No tool execution
- No memory content retrieval
- No context injection
- No workflow execution
- No browser/network action
- No shell/subprocess execution
- No connector write
