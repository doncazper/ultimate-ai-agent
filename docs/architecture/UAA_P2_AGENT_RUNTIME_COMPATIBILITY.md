# UAA-P2 Agent Runtime Compatibility

Status: contract-first compatibility architecture

This document defines the UAA-P2 Agent Runtime Compatibility lane. It does not adopt the OpenAI Agents SDK
as UAA's architecture, add provider SDK calls,
grant runtime model authority, add backend routes, add Control Center controls,
fetch the web, run browsers, execute shell/subprocess commands, write
connectors, write memory, inject context, import plugin runtimes, claim public
beta, claim public release, or claim production authority.

## Thesis

UAA should borrow agent-runtime patterns without making any SDK the kernel.
The useful ideas are portable: typed tools, explicit handoffs, trace spans,
specialists-as-capabilities, structured outputs, and clear execution loops.
The authority model is not portable. UAA owns authority.

Python Agent Core remains the brain. Control Center and OpenWebUI remain
shells. Provider runtimes, SDK-style agents, local deterministic workers, Codex
or Claude Code-like tools, MCP tools, and A2A-style agent cards are execution
targets or metadata sources only after UAA policy, approval, capability,
receipt, audit, and redaction contracts bind them.

## Current Implementation Scope

The implemented P2 compatibility slice is a contract/read-model foundation:

- `CapabilityManifest` carries UAA-owned authority metadata for tools, agents,
  workflows, reviewers, human gates, and future runtime adapters.
- `ultimate_ai_agent.core.agent_runtime` defines inert adapter request,
  decision, result, handoff, trace, receipt, and deterministic specialist
  contracts.
- Static OpenAI/MCP-shaped schema export includes UAA authority extension
  metadata and explicitly marks dispatch as unauthorized.
- A deterministic in-process specialist demo can run through the existing
  `Coordinator` as an agent-as-tool without external runtime authority.
- A static verifier checks the compatibility namespace for SDK imports,
  network/browser imports, raw-content fields, runtime routes, and unsafe
  default authority flags.

This scope is implemented-contract-only. It is not live agent runtime
execution.

## Compatibility Boundary

An `AgentRuntimeAdapter` is a future execution target boundary, not a new
authority layer. Its request, decision, and result contracts carry only safe
refs, safe summaries, blocked authority refs, trace refs, receipt refs, and
evidence refs.

Allowed adapter families as metadata or future exact-scoped adapters:

- deterministic local workers
- local model runtimes
- OpenAI Agents SDK-style runtimes
- Anthropic-style runtimes
- Gemini-style runtimes
- Codex-like tools
- Claude Code-like tools
- external agent frameworks

Adapter output is not truth, memory, approval evidence, or execution authority.
UAA may treat adapter output as an artifact or subordinate evidence only after
the Python Agent Core has validated policy, approvals, redaction, side effects,
and receipts.

## Capability Manifest As Registry Language

The capability registry remains the single registry language. Capability
manifests now describe:

- authority level
- approval posture
- deterministic behavior
- rollback support
- receipt and evidence requirements
- privacy, latency, and cost classes
- memory write, context injection, provider runtime, browser runtime, and
  connector write flags
- side effects, risk, coordination modes, health, dependencies, conflicts,
  idempotency, and output schemas

Authority flags default to false. Existing policy and approval validation still
decide whether any capability can be selected or executed.

## Execution Loop

The target loop remains UAA-owned:

```text
Intent
-> classify
-> plan
-> select capability
-> policy
-> exact approval when required
-> execute or no-effect review
-> receipt
-> evaluate
-> continue or stop
```

This loop is coordinated by UAA contracts. SDK-native planning or tracing can
be imported only as subordinate evidence after a future scoped adapter review.

## Structured Handoffs

Specialist handoffs must use a structured `HandoffEnvelope`, not freeform
agent-to-agent authority. A handoff envelope binds:

- source turn or run refs
- source and target capability refs
- objective refs and safe summaries
- allowed and blocked authority refs
- evidence and receipt refs
- expected output schema refs
- timeout, idempotency, and rollback/safe-disable refs
- human-review requirement

Handoff approval is not execution approval. The implemented envelope denies
execution, memory write, context injection, and connector write authority by
default.

## UAA-Owned Trace And Receipts

UAA trace refs are canonical. Vendor or SDK trace IDs may be stored only as
safe evidence metadata. They cannot replace:

- UAA durable run state
- UAA receipt ledger
- UAA audit records
- UAA evidence timeline
- UAA replay and rollback refs
- LocalApprovalAuthority decisions
- PolicyEngine decisions

If an adapter cannot produce UAA-safe receipt refs for meaningful work, that
work is not eligible for runtime promotion.

## Memory Boundary

Memory remains recall, not truth or authority. Agent runtime compatibility
does not add memory writes, automatic context injection, raw transcript
persistence, hidden recall, or provider-owned conversation state as system
truth.

Future memory integration must remain reviewed, provenance-bearing, redacted,
correctable, exportable/deletable where scoped, and subordinate to canonical
evidence.

## Single Orchestrator First

The default path is one UAA orchestrator using many capabilities. Specialists
should be introduced only when they reduce real complexity, improve evidence,
or make the product loop easier to review.

Good specialist candidates:

- memory review
- calendar metadata prep
- email metadata triage
- CRM-lite follow-up analysis
- code proposal review
- evidence narrative review

Specialists remain capabilities. They do not become separate authority owners.

## Non-Goals

This lane does not add:

- OpenAI Agents SDK adoption as core architecture
- provider SDK imports
- runtime model calls
- live web fetching
- browser automation
- shell/subprocess execution
- connector writes
- memory writes
- context injection
- plugin runtime import
- remote execution
- backend routes
- Control Center controls
- broad action execution
- public beta, public release, or production authority

## Promotion Requirements

A future live adapter promotion requires a separate scoped milestone with:

- reviewed `CapabilityManifest`
- exact side-effect class
- `PolicyEngine` checks
- `LocalApprovalAuthority` exact approval scope when required
- idempotency and retry posture
- UAA-owned trace and receipt refs
- safe-disable or rollback posture
- redaction tests
- OpenAPI and `/api/manifest` updates if routes are added
- CLI/core/API inspection parity
- Foundation Gate and product-truth updates

Until then, this layer remains contract-first compatibility infrastructure.
