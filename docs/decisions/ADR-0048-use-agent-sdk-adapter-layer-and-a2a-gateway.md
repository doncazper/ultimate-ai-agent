# ADR-0048-use-agent-sdk-adapter-layer-and-a2a-gateway: Use Agent SDK Adapter Layer and A2A Gateway

## Status
Accepted in v0.5.5.

## Context

The Ultimate AI Agent needs to use local runtimes, cloud runtimes, vendor SDKs, and agent interoperability without surrendering its own safety, memory, event, consent, rollback, and verification architecture.

## Decision

Support OpenAI Agents SDK, Claude Agent SDK, MCP, A2A, and local runtimes through explicit adapters while preserving our Agent Core boundaries.

## Consequences

- Adds a small amount of foundation schema work before M0/M1 implementation.
- Prevents long-running local sessions from relying on fragile transcript compaction.
- Keeps external SDKs and A2A as adapters rather than core authorities.
- Improves future portability across local, cloud, and vendor-managed agent runtimes.

## Related

- docs/canonical/53_structured_world_state.md
- docs/canonical/54_context_budget_and_session_survival.md
- docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md
- docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md
