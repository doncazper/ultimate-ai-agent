# Ultimate AI Agent Master Plan v0.31.0

Status: active release packet
Current through: v0.31.0
Purpose: Master-plan summary for M27 Tool Broker v2 + Safe Tool Intent Contracts.

## Implemented

- Tool Broker v2 contract package under `src/ultimate_ai_agent/core/tools/v2/`.
- Safe tool intent, target, input boundary, catalog, decision, manifest, and
  receipt-plan models.
- Validation-only `evaluate_tool_intent` for metadata-only safe previews.
- Denial reason codes for unknown tools, target mismatches, side effects,
  approval refs as authority, context packs as authority, risk downgrades, and
  hidden side effects.
- Foundation Gate, static verifier, documentation-integrity, and regression
  test coverage.

## Boundaries

v0.31.0 adds no real tool execution, shell execution, file mutation, memory
write, Event Ledger mutation, backend execution route, frontend execution
control, external network call, web search, browser automation, Computer Use,
plugin enablement, model/provider call, local LLM call, retrieval/RAG/vector
behavior, context injection runtime, dependency, M28 work, or production
authority.

M28-M40 remain planned/provisional.
