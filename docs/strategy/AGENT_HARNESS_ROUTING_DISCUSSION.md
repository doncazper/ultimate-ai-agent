# Agent Harness Routing Discussion

Status: side-conversation share packet
Purpose: summarize the full discussion so it can be shared with ChatGPT or
another design reviewer.

This is not an implementation plan, product truth packet, or authority grant.
It is a design note about how UAA should answer normal questions, when it
should behave like an agent, and how it could use fast routing, tool policy,
memory, and speculative preflight without adding unwanted latency or ceremony.

## 1. Starting Point

The discussion began from an article describing the AI product everyone keeps
circling:

- an executive super-assistant
- deep memory
- one continuous history
- enough trust to handle email, credit cards, bookings, passwords, and
  subscriptions
- judgment to interrupt only when a human is actually needed

The immediate reaction was that this sounds like UAA: not just a chatbot, but a
trusted operator layer with memory, inbox, plans, actions, evidence, approvals,
and judgment.

The matching UAA product spine is:

- Today / Morning Briefing
- Inbox / Action Inbox
- Plans
- Actions
- Memory
- Evidence
- Settings / Policy

The distinction is governance. UAA should not become "give an agent your
passwords and hope." It should become a delegated operator whose authority is
explicit, scoped, inspectable, revocable, and evidence-backed.

## 2. Delegated Authority North Star

The long-term UAA thesis was refined as:

> A governed executive super-assistant with deep reviewed memory, continuous
> evidence-backed history, delegated authority, brokered credentials, and
> judgment about when human approval is actually needed.

Important pieces:

- Deep memory: preferences, people, projects, commitments, vendors, habits,
  subscriptions, decisions.
- Continuous history: Today, Plans, Actions, Evidence, Memory, and Weekly
  Review feed one loop.
- Trust layer: approval envelopes, receipts, audit refs, rollback or
  safe-disable posture, revocation.
- Credential/payment broker: UAA can use a stored credential or payment handle,
  but should not know, expose, or leak raw passwords or card data.
- Delegated authority: "you may order my usual pizza under this limit from this
  merchant" is different from "do anything online."
- Interruption judgment: draft quietly, ask before consequences, escalate when
  cost, risk, ambiguity, or evidence gaps appear.

An internal phrase for the product direction:

> UAA is the governed life-and-work OS for delegated personal operations.

## 3. Concern: Agent Harness Should Not Make Every Answer Weird

The core concern:

> If I ask the raw model "how do I build a DIY table?", will the agent harness
> answer differently in an annoying way?

That concern is valid. The harness should not treat every normal question like
an operator workflow.

A raw model answer to:

```text
How do I build a DIY table?
```

should probably be a normal helpful answer: tools, materials, dimensions,
steps, safety notes, and maybe a simple cut list.

UAA should only shift modes when the user intent becomes personal, stateful,
tool-bearing, or consequence-bearing.

Suggested behavior:

| User asks | UAA behavior |
|---|---|
| "How do I build a DIY table?" | Normal answer mode. No memory, no plans, no approvals, no evidence ceremony. |
| "Help me design a table for my office using what you know about my space." | Memory-assisted answer, with reviewed memory refs or a clear "I do not know." |
| "Make me a shopping list for this table." | Draft/proposal mode. |
| "Order the materials." | Action envelope and approval. |
| "Use my card and book pickup at Home Depot." | High-authority delegated action with exact approval and credential broker. |

The agent harness should be a router and governance layer around the LLM, not a
replacement personality that turns every prompt into process.

## 4. Proposed Modes

The product needs explicit turn modes:

1. `answer_directly`
   - Plain LLM response.
   - Minimal harness.
   - No durable state unless explicitly requested.

2. `answer_with_reviewed_memory`
   - Use reviewed memory only when relevant.
   - Cite or name the memory refs used.
   - Never treat memory as authority.

3. `draft_or_plan`
   - Create editable drafts, lists, plans, carts, booking holds, or proposals.
   - No external side effect.

4. `prepare_tool_or_action`
   - Build a scoped action envelope.
   - Include risk, scope, refs, expiry, idempotency, receipt posture, and
     rollback or safe-disable posture.

5. `approval_required`
   - Consequence boundary.
   - Used for send, order, book, pay, subscribe, cancel, delete, deploy, push,
     account change, credential use, or similar external mutation.

6. `ask_clarifying_question`
   - Used for ambiguous or conflicting intent.

7. `base_answer`
   - Explicit escape hatch for low-ceremony answer behavior.
   - Useful for comparison and low-ceremony work.

## 5. Best Implementation Shape

The best path is a fast deterministic turn router in front of the agent
harness.

Architecture:

```text
user message
-> deterministic turn classifier
-> mode + risk + confidence + tool policy
-> answer/prompt profile selection
-> harness exposes only allowed context/tools
-> model answers or proposes a tool/action
-> executor validates again before any side effect
```

The key rule:

> The model can suggest a tool call. The harness decides whether that tool was
> even available, whether the arguments validate, whether approval is required,
> and whether execution is allowed.

This avoids relying on the LLM to self-regulate.

## 6. Tool Exposure Policy

Do not expose all tools to the model by default.

Instead, the turn router should produce a tool policy:

| Mode | Tool policy |
|---|---|
| `answer_directly` | no tools |
| `answer_with_reviewed_memory` | memory-read only, if relevant |
| `draft_or_plan` | proposal/draft tools only, if needed |
| `prepare_tool_or_action` | envelope-building tools only |
| `approval_required` | no execution tools until approval exists |
| `base_answer` | no UAA tools |

Online docs reviewed:

- OpenAI function calling describes tools as application-provided
  functionality, supports constraining callable tools with `tool_choice`, and
  recommends strict schemas for reliable arguments:
  https://developers.openai.com/api/docs/guides/function-calling
- OpenAI Agents SDK docs frame agents as applications that plan, call tools,
  keep state, and use the SDK when the application owns orchestration, tool
  execution, approvals, and state:
  https://developers.openai.com/api/docs/guides/agents
- Anthropic tool-use docs distinguish client tools from server tools. For
  client tools, the model returns a structured tool-use request and the
  application executes it:
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- LangChain human-in-the-loop docs describe interrupting risky tool calls for
  approve/edit/reject/respond decisions:
  https://docs.langchain.com/oss/python/langchain/human-in-the-loop

The design lesson: models can request tools, but product code should control
which tools are visible, validate schemas, and gate execution.

## 7. ModelRouter Review

The `model-router` repo already has the right instinct:

- deterministic `route_fast(...)` hot path
- richer `route(...)` receipts for diagnostics
- risk signals for destructive, send, purchase, and external actions
- `supports_tools` metadata on engines
- explicit boundary that ModelRouter is not the agent harness

Relevant repo references:

- `README.md` says ModelRouter is routing/control, not the agent harness, and
  the host agent owns task execution, context management, delegation, and final
  review.
- `hermes/plugins/model_router/scorer.py` has useful signal extraction for
  destructive, send, purchase, high-impact external, freshness, tool, and
  modality intent.
- `hermes/plugins/model_router/policy.py` has `route(...)` and `route_fast(...)`
  separation. `route_fast(...)` is explicitly for latency-sensitive callers and
  sends obvious high-risk lexical actions to `human_confirm`.
- `docs/product-boundaries.md` says host agents own planning, tool calls,
  context, supervision, synthesis, and final answers.

What to borrow:

- the hot-path architecture
- precompiled lexical signals
- explicit risk flags
- latency checks
- receipt-rich diagnostic path
- separation between model routing and agent orchestration

What not to borrow unchanged:

- exact prompt classification rules, because UAA needs a personal-operations
  turn router, not only a model/backend router.

Quick sanity examples from the current router behavior:

| Prompt | Observed route | Note |
|---|---|---|
| "How do I build a DIY table?" | `code_agent` | Misclassified because `build` is treated as coding intent. |
| "Help me design a table for my office using what you know about my space." | `reasoning_local` | Reasonable, but UAA should also consider reviewed memory. |
| "Make me a shopping list for this table." | `balanced_local` | Reasonable draft/list behavior. |
| "Order the materials for this table." | `human_confirm` | Correctly treated as purchase/high-risk. |
| "Use my card and book pickup at Home Depot." | `balanced_local` | Missed payment/booking risk; UAA should catch this. |

This is useful evidence. It means UAA should not simply call ModelRouter and
interpret the selected model as the product mode. UAA needs a preflight turn
router first, then ModelRouter can choose the best model/backend for the chosen
mode.

## 8. UAA Home For This

UAA already has a natural conceptual home:

```text
src/ultimate_ai_agent/core/decision_router/
```

The existing top-level decision router contract already models outcomes like:

- `answer_directly`
- `use_reviewed_memory`
- `propose_action_inbox_item`
- `ask_human`
- `escalate_to_review`
- `defer`
- `blocked_unsafe`
- `insufficient_evidence`

That should evolve into the preflight turn router.

Suggested boundary:

```text
UAA Turn Router:
  decides product mode, memory relevance, risk, action posture, and tool policy

ModelRouter:
  chooses model/backend under provider/runtime policy

Agent Harness:
  builds prompt/context/tools for the selected mode

Executor:
  validates approvals and executes only allowed side effects
```

## 9. Latency Strategy

The turn router should be cheap:

- regex/table/rule based
- precompiled patterns
- no model call
- no tool call
- no memory retrieval on the lowest-risk path unless needed

Expected behavior:

```text
normal question
-> fast classifier
-> no memory/tools/actions
-> one model call
```

The result should feel raw-model fast for normal questions.

The slower paths should only activate when the turn actually needs them:

- memory relevance
- current/fresh information
- tool/action preparation
- approval envelope
- clarification
- high-risk policy review

## 10. Parallel Or Speculative Preflight

The user asked whether more than one logic path could run at the same time until
one is clearly better.

Answer: yes. This is probably the advanced version.

Call it speculative routing or parallel preflight:

```text
user turn
-> fast deterministic router starts immediately
-> cheap memory relevance check starts in parallel
-> tool/action risk scan starts in parallel
-> model route choice starts in parallel
-> optional raw-answer draft starts only if risk looks low
-> arbiter chooses mode
-> final answer or action envelope
```

Important rule:

> Multiple thinking, classification, retrieval, and planning paths can run in
> parallel. Multiple side-effecting execution paths must not.

Examples:

### Normal DIY Question

```text
"How do I build a DIY table?"

direct-answer lane -> normal explanation
memory lane -> no reviewed memory needed
tool lane -> no tool needed
risk lane -> low risk
arbiter -> answer_directly
```

The user gets a normal answer.

### High-Risk Delegated Action

```text
"Use my card and book pickup at Home Depot."

direct-answer lane -> maybe starts, but must be cancellable
risk lane -> payment + booking + merchant action
memory lane -> maybe address/preferences refs
tool lane -> action tools blocked until approval
arbiter -> approval_required
```

No tool executes until an approval envelope is approved.

## 11. Arbiter Rules

"Clearly better" should be deterministic, not model vibes.

Suggested priority rules:

1. High-risk external action beats direct answer.
2. Explicit credential, payment, booking, account, send, delete, deploy,
   subscribe, cancel, refund, or purchase language enters approval/envelope
   mode.
3. Explicit "use what you know about me" enables reviewed memory.
4. "Latest", "current", "today", "search", "look up", or "cite sources" enables
   research/freshness mode.
5. Tool verbs like "run", "open", "edit", "write file", "commit", "push",
   "schedule", "send", "order", or "book" require tool policy review.
6. Low confidence asks a clarifying question.
7. No special signal within the latency budget means stream or return direct
   answer.

An example preflight result:

```json
{
  "mode": "answer_directly",
  "risk": "low",
  "confidence": 0.92,
  "memory_policy": "none",
  "tool_policy": "none",
  "approval_required": false,
  "answer_profile_hint": "balanced"
}
```

For a high-risk action:

```json
{
  "mode": "approval_required",
  "risk": "high",
  "confidence": 0.95,
  "memory_policy": "reviewed_refs_only",
  "tool_policy": "envelope_only_no_execution",
  "approval_required": true,
  "blocked_authority_refs": [
    "payment_handle_use",
    "merchant_order_submission",
    "external_account_mutation"
  ]
}
```

## 12. Proposed Implementation Path

Suggested incremental path:

1. Add or extend a `TurnPreflight` contract.
   - mode
   - risk class
   - confidence
   - memory policy
   - tool policy
   - approval posture
   - source/evidence refs
   - blocked authority refs

2. Implement deterministic classifiers first.
   - Borrow ModelRouter's precompiled regex approach.
   - Add UAA-specific personal-operations signals:
     - credential
     - card/payment
     - booking
     - pickup/delivery
     - purchase/order
     - send/reply/post
     - calendar schedule/reschedule
     - subscription/renew/cancel
     - account settings/login/password

3. Add golden tests.
   - DIY table -> `answer_directly`
   - use what you know -> `answer_with_reviewed_memory`
   - make shopping list -> `draft_or_plan`
   - order materials -> `approval_required`
   - use my card and book pickup -> `approval_required`
   - latest/research -> freshness/research mode
   - base answer request -> `base_answer`

4. Add a latency guard.
   - Similar to `scripts/check_route_fast_latency.py` in ModelRouter.
   - The default preflight should be cheap enough that normal chat does not
     feel delayed.

5. Wire tool exposure to mode.
   - `answer_directly`: no tools.
   - `answer_with_reviewed_memory`: memory read refs only.
   - `draft_or_plan`: proposal tools only.
   - `approval_required`: envelope tools only.
   - Execution tools appear only after exact approval exists.

6. Add speculative preflight later.
   - Start with parallel cheap lanes only.
   - Defer parallel model generations until there is evidence they improve UX.

## 13. Core Product Principle

The simplest statement of the design:

> UAA should feel like a normal smart model until the user asks for personal
> memory, current information, tool use, or a consequential action. Then it
> should become a governed operator.

The harness should be invisible on ordinary questions and very visible at
consequence boundaries.

That is the line that prevents UAA from becoming bureaucratic while preserving
the trust layer needed for email, cards, bookings, passwords, subscriptions,
and delegated action.
