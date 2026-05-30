# ADR-0047-use-local-runtime-registry-and-resource-governor: Use Local Runtime Registry and Resource Governor

## Status
Accepted in v0.5.5.

## Context

The Ultimate AI Agent needs to use local runtimes, cloud runtimes, vendor SDKs, and agent interoperability without surrendering its own safety, memory, event, consent, rollback, and verification architecture.

## Decision

Treat local runtimes as first-class runtime providers with health, capability, context, resource, and privacy metadata.

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
