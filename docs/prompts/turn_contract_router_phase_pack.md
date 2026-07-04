# UAA Turn Contract Router Phase Pack

Status: operator-run phased prompt pack
Scope: Turn Contract Router / Answer Preservation Router
Source artifacts:
- `docs/strategy/AGENT_HARNESS_ROUTING_DISCUSSION.md`
- `artifact-ref:turn-contract-router-capability-tables`

This pack is implementation guidance for future Codex runs. It is not product
truth by itself and grants no runtime authority. Each phase must preserve UAA's
existing no-broad-authority posture and must finish with review, fix, harden,
merge readiness, commit, and push steps before the next phase starts.

## Global Product Invariant

UAA should feel like a normal smart LLM until the user asks for personal memory,
current information, tools, planning, approval, or consequential action. Then
UAA should become a governed operator.

The Turn Contract Router is not a backend selector. ModelRouter can remain a
separate project for backend/provider selection. UAA's router decides product
mode, risk, memory policy, tool policy, state policy, approval posture, output
contract, and prompt/profile shape.

Use answer/contract language:

| Old or confusing name | Use instead | Reason |
|---|---|---|
| `raw_model` | `base_answer` | The escape hatch is low-ceremony answer behavior, not raw backend exposure. |
| `base_model` | `base_answer` | UAA chooses an answer contract, not a backend route. |
| `raw_answer_draft` | `direct_answer_draft` | A speculative draft is a normal direct answer draft with no memory, tools, private files, or side effects. |
| `model_route_hint` | `answer_profile_hint` | The hint chooses answer/prompt profile within the current contract. |
| `model_route_lane` | `answer_profile_lane` | Optional preflight signal for answer/profile shape; it grants no authority. |
| `ModelRouter inside UAA` | `TurnContractRouter` | UAA decides product mode, risk, memory policy, tool policy, state policy, and approval posture. |
| `model/backend routing` | `invocation_policy_selection` | The compiler selects allowed capabilities. Backend choice can stay outside this contract. |
| `raw/base model request` | `base_answer request` | The user asks for a minimal UAA wrapper; safety and approval boundaries still apply. |

Recommended turn contract values:

```text
answer_directly
base_answer
answer_with_reviewed_memory
draft_or_plan
prepare_tool_or_action
approval_required
execute_approved_action
ask_clarifying_question
blocked_unsafe
```

## Layer Boundaries

| Layer | Responsibility | Must not do |
|---|---|---|
| `TurnContractRouter` | Classifies the user turn into a product contract: direct answer, memory answer, plan, read-only tool prep, approval, execution, clarification, or block. | Must not call the LLM, execute tools, read unapproved memory, or choose broad authority. |
| `InvocationPolicyCompiler` | Converts the selected contract into hard harness constraints: memory scope, tools, state, approval posture, output contract, and prompt profile. | Must not treat router output as a soft hint. The policy must physically limit capabilities. |
| `AgentHarness` | Calls the LLM with only the context, memory refs, tools, and output contract allowed for the turn. | Must not expose all tools or memory and hope the LLM ignores them. |
| `ExecutorFence` | Revalidates every proposed side effect against the exact approval envelope and invocation policy. | Must not execute send/order/book/delete/pay/account changes without exact approval. |

Core invariant:

```text
A later layer may reduce permissions, but it may never increase permissions beyond the TurnContractRouter's selected capability gate.
```

## Turn Contract / Capability Gate Table

This is the user-experience contract. The default is lightweight. UAA escalates
only when the request needs memory, planning, current information, tools,
approval, or execution.

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

## Stricter Capability Firewall - Authority And Context

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

Protected direct-answer rule:

```text
For answer_directly and base_answer:
memory_scope=none, tools=[], tool_choice=none, planner=false, durable_state=false, approval_required=false.
```

## Stricter Capability Firewall - Tools, State, And Side Effects

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

## Parallel Preflight Policy

Phase 2+ can parallelize sensing, but not authority. Use these lane names to
avoid backend-routing confusion.

| Lane | Runs when | May read memory content? | May execute tools? | User-visible? | Output |
|---|---|---|---|---|---|
| `intent_lane` | Every turn | No | No | No | Candidate turn contract and confidence |
| `risk_action_lane` | Every turn | No | No | No | Risk flags and veto/escalation signal |
| `memory_trigger_lane` | Every turn | No | No | No | Whether memory relevance is allowed |
| `memory_relevance_lane` | Only after memory trigger | Reviewed/scoped refs only | No | No | Candidate memory refs, not injected yet |
| `tool_manifest_lane` | Every turn | No | No | No | Read-only or side-effect tool category candidates |
| `answer_profile_lane` | Optional | No | No | No | Prompt/profile hint within the contract |
| `direct_answer_draft` | Later phase; likely low-risk turns | No | No | Not until gates clear | Cancelable draft for direct answer |

Parallel preflight rule:

```text
Parallelize sensing. Centralize authority. Serialize execution.
Speculative drafts may be internal, but not user-visible until risk and side-effect gates clear.
```

## Golden Tests

These fixtures protect both answer quality and safety boundaries. The DIY table
and Home Depot prompts define the product line.

| Prompt | Expected contract | Required policy |
|---|---|---|
| How do I build a DIY table? | `answer_directly` | No memory, no tools, no planner, no state, no approval, normal useful answer. |
| Ask the base answer path: how do I build a DIY table? | `base_answer` | Minimal UAA wrapper; no memory/tools/planner/state; safety still applies. |
| Build me a React table component. | `answer_directly` | Code-style answer is fine. Do not route to operator/action mode. |
| Design one for my office using what you know. | `answer_with_reviewed_memory` | Reviewed relevant memory only; say "I do not know" when absent. |
| Remember that I prefer walnut. | memory write proposal/review path | No silent durable memory write unless product policy explicitly allows it. |
| Make me a shopping list for this table. | `draft_or_plan` | No purchase tools, no checkout, no external side effect. |
| Find current lumber prices near me. | `prepare_tool_or_action` | Read-only tools only; ask for location if unavailable. |
| Order the materials. | `approval_required` | Action envelope required; no execution tools until approval. |
| Use my card and book pickup at Home Depot. | `approval_required` | High purchase + credential + booking risk; strong approval and brokered credential refs. |
| Send this to Alex. | `approval_required` | External communication boundary; no send before exact approval. |
| Delete these files. | `approval_required` | Destructive action boundary; no delete before exact approval. |
| Ask the base answer path: use my card and order this. | `approval_required` | `base_answer` must not bypass payment, credential, or action safety. |

Acceptance criterion:

```text
If a normal informational question feels worse than the loaded LLM, the router failed.
If a consequential action avoids approval, the router failed.
```

## Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate

Every phase below must end with this exact process:

1. Review the implementation against this prompt pack, `AGENTS.md`, product
   language rules, and the relevant existing UAA contracts.
2. Fix defects, naming drift, authority creep, missing tests, brittle
   classifications, raw-data leakage, and docs mismatch.
3. Harden with adversarial tests for false positive escalation and false
   negative consequence detection.
4. Run focused tests and verifiers for the files changed. Run broader checks
   only when the touched surface justifies it.
5. Inspect `git status` and `git diff`. Stage only files changed for this
   phase. Do not stage unrelated user work.
6. If working on a feature branch, merge only after verification is green. If a
   merge commit is needed, create it intentionally. If already on the target
   branch, skip merge and commit the verified phase directly.
7. Commit with a scoped phase message.
8. Push the current branch. Never force-push and never mutate historical tags.
9. If merge or push is blocked, report the exact blocker and stop instead of
   broadening scope.
10. After push succeeds, proceed to the next phase only if the wrapper prompt
    asked for end-to-end execution.

## Phase 00 - Baseline Review And Scope Lock

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Prepare Phase 00 for the UAA Turn Contract Router.

Read first:
- AGENTS.md
- docs/prompts/turn_contract_router_phase_pack.md
- docs/strategy/AGENT_HARNESS_ROUTING_DISCUSSION.md
- docs/control_center/PRODUCT_LANGUAGE_RULES.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- src/ultimate_ai_agent/core/decision_router/contracts.py
- tests around `decision_router`

Goal:
Confirm the correct implementation home and produce only the smallest planning
or doc adjustment needed before code starts. Prefer evolving
`src/ultimate_ai_agent/core/decision_router/` unless repo inspection proves a
separate module is cleaner.

Required output:
- Identify existing contracts that should be reused.
- Identify focused test files to add/update.
- Identify docs to update.
- Confirm `base_answer` replaces `base_model`/`raw_model` naming.
- Confirm Phase 1 implementation boundaries.

Do not add runtime model calls, provider calls, tool execution, memory
retrieval, memory writes, connector writes, browser/network authority, shell
execution, or API routes.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 01 - Contracts And Capability Firewall

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 01 of the Turn Contract Router: typed contracts and
capability firewall only.

Implement:
- Turn contract enum values:
  - answer_directly
  - base_answer
  - answer_with_reviewed_memory
  - draft_or_plan
  - prepare_tool_or_action
  - approval_required
  - execute_approved_action
  - ask_clarifying_question
  - blocked_unsafe
- Policy enums or typed values for:
  - memory policy
  - tool policy
  - state policy
  - approval policy
  - prompt/profile policy
  - output contract
  - risk flags
- A typed `TurnDecision` or equivalent result.
- A typed `InvocationPolicy` or equivalent compiled constraints object.
- Validation that `answer_directly` and `base_answer` physically compile to:
  `memory_scope=none`, `tools=[]`, `tool_choice=none`,
  `planner=false`, `durable_state=false`, and
  `approval_required=false`.

Do not implement classifier rules yet beyond trivial construction helpers.
Do not call the LLM. Do not execute tools. Do not read memory.

Tests:
- Contract construction and serialization.
- Validation blocks permission expansion for `answer_directly` and
  `base_answer`.
- `execute_approved_action` cannot exist without an approval/action scope ref,
  or record it as not executable if the existing architecture has no exact
  approved execution lane yet.

Docs:
- Create or update `docs/architecture/TURN_CONTRACT_ROUTER.md`.
- Include the Turn Contract / Capability Gate table and both stricter
  capability firewall tables from this prompt pack.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 02 - Deterministic Serial Classifier

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 02 of the Turn Contract Router: deterministic serial
classification.

Build a no-effect classifier:
- precompiled regex/table/rule based
- no LLM call
- no provider call
- no tool call
- no memory retrieval
- no side effects
- confidence and reason codes

Priority:
1. blocked_unsafe
2. high-risk external side effect
3. credential/payment/account/privacy boundary
4. external side-effecting action
5. explicit memory/personal-context request
6. current/read-only tool or research need
7. draft/plan request
8. explicit `base_answer` request unless it conflicts with safety/action
   boundaries
9. ask clarification only when necessary
10. answer_directly

Signals:
- High-risk: buy, order, pay, checkout, use my card, book, reserve, cancel,
  send, email, message, post, share, upload, delete, remove, overwrite,
  transfer, withdraw, sign, submit, grant access, change password, use
  credentials, merchant, account, money, identity, destructive operation.
- Memory: using what you know, my office, my preferences, my home, my files,
  my calendar, last time, what did I tell you, remember this, save this, based
  on my previous, from my account.
- Fresh/current: latest, current, today, this week, near me, search, look up,
  cite sources, current price, availability, inventory.
- Draft/plan: make a plan, shopping list, itinerary, proposal, compare options,
  break into tasks, draft, outline, checklist.
- Physical DIY terms are not code/operator signals by themselves: build, make,
  construct, DIY, wood, table, chair, shelf.
- Software terms can make a code-style direct answer appropriate: React,
  Python, SQL, API, component, function, class, package, repo, code, compile,
  test.

Tests:
- Add the full Golden Tests table from this prompt pack.
- Include specific false-positive and false-negative regressions:
  - "How do I build a DIY table?" -> answer_directly.
  - "Use my card and book pickup at Home Depot." -> approval_required.
  - "Ask the base answer path: use my card and order this." ->
    approval_required or blocked_unsafe, not base_answer.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 03 - Invocation Policy Compiler

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 03 of the Turn Contract Router: invocation policy
compiler.

Goal:
Convert every `TurnDecision` into hard harness constraints. The result must be
enforceable data, not a soft instruction to the LLM.

Compiler requirements:
- `answer_directly`:
  - memory_scope=none
  - tools=[]
  - tool_choice=none
  - side_effects_allowed=false
  - durable_state_allowed=false
  - approval_required=false
  - prompt_profile=minimal_answer
  - output_contract=plain_answer
- `base_answer`:
  - no UAA memory
  - no UAA tools
  - no planner
  - no durable state
  - minimal wrapper
  - no safety/action bypass
- `answer_with_reviewed_memory`:
  - memory_scope=reviewed_relevant_only
  - tools=[] by default
  - side_effects_allowed=false
  - durable_state_allowed=false unless an explicit memory-review flow exists
- `draft_or_plan`:
  - draft/proposal only
  - no side effects
  - draft state at most
- `prepare_tool_or_action`:
  - read-only/proposal/envelope-building tools only, if already safe
  - no side effects
- `approval_required`:
  - no side-effect execution tools exposed
  - action envelope required
  - exact approval required before future execution
- `execute_approved_action`:
  - exact approved tool only
  - exact approved scope only
  - receipt/action log required
  - no expansion

Tests:
- Prove `answer_directly` and `base_answer` compile to no tools, no memory, no
  planner, no durable state, no approval.
- Prove `approval_required` exposes envelope/read-only posture only.
- Prove `execute_approved_action` cannot broaden approved merchant, recipient,
  account, cost, tool name, or arguments.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 04 - ExecutorFence Contract

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 04 of the Turn Contract Router: ExecutorFence contract
and validation tests.

Scope:
Implement no runtime execution. Add the contract and validators that any future
execution lane must pass before a side effect can occur.

ExecutorFence must revalidate:
- approved action id
- selected turn contract is `execute_approved_action`
- current invocation policy allows the exact tool
- tool name matches approved envelope
- arguments match approved envelope
- merchant, recipient, account, cost, credential broker refs, and risk class
  match approved envelope
- no unapproved expansion occurred

Tests:
- Reject execution when approval is missing.
- Reject execution when action id mismatches.
- Reject execution when tool name or args differ.
- Reject payment/booking/order expansion.
- Reject recipient/account expansion.
- Require receipt/action-log posture for approved execution.

Do not add a live execution route, side-effecting tool call, connector write,
email send, payment action, booking action, shell execution, browser action, or
provider call.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 05 - Harness Binding Read Model

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 05 of the Turn Contract Router: safe harness binding
read model.

Goal:
Expose, through existing internal/API/CLI inspection patterns if appropriate,
what UAA would give the harness for a turn without executing tools or reading
private memory on ordinary prompts.

Requirements:
- `answer_directly` and `base_answer` must report:
  - memory_touched=false
  - tools_exposed_count=0
  - planner=false
  - durable_state=false
  - approval_required=false
- Memory content must not be retrieved for ordinary prompts.
- Read model must use safe summaries and reason codes only.
- No raw prompt, raw response, raw memory body, raw local path, credential, or
  secret-like value in durable outputs.

Tests:
- Harness binding for DIY table shows no tools/memory/state.
- Harness binding for office/memory prompt allows reviewed memory refs but not
  silent memory write.
- Harness binding for Home Depot/card prompt requires approval envelope and no
  execution tools.

Docs:
- Update `docs/architecture/TURN_CONTRACT_ROUTER.md` with the binding shape.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 06 - Quality, Latency, And Product-Language Hardening

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Implement Phase 06 of the Turn Contract Router: quality, latency, and
product-language hardening.

Add answer-preservation checks:
- Normal informational prompts must not route to planner/action/evidence
  ceremony.
- Direct answers must not include unnecessary approval-envelope language.
- `answer_directly` and `base_answer` must not touch memory or tools.

Add latency/performance guard if practical:
- Classifier should run in microseconds or low milliseconds.
- The guard should not require LLM calls, provider calls, memory retrieval, or
  network access.

Add product-language checks/docs:
- No production/public beta/broad autonomy claims.
- No claim that purchase, booking, send, credential, or account execution
  exists unless an exact future lane implements it.
- Use `base_answer`, not `base_model` or `raw_model`.
- Use `answer_profile_hint`, not `model_route_hint`, unless explicitly
  discussing an external backend router.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```

## Phase 07 - Phase 2 Cheap Parallel Preflight Plan Only

Prompt:

```text
You are Codex working in `doncazper/ultimate-ai-agent`.

Task: Create the Phase 2 cheap parallel preflight plan, without implementing
parallel runtime behavior yet.

Document:
- `intent_lane`
- `risk_action_lane`
- `memory_trigger_lane`
- `memory_relevance_lane`
- `tool_manifest_lane`
- `answer_profile_lane`
- future `direct_answer_draft`

Rules:
- Parallelize sensing.
- Centralize authority.
- Serialize execution.
- No side-effecting execution during preflight.
- No memory content retrieval unless memory trigger permits it.
- No user-visible direct answer draft until risk and side-effect gates clear.

Tests/docs:
- Add planning-only docs and any static validation that preserves lane names
  and authority boundaries.

Finish with the Per-Phase Review, Fix, Harden, Merge, Commit, Push Gate.
```
