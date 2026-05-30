# 52 — Service Boundaries and Dependency Injection

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

The agent must be built like an onion. Lower layers expose stable contracts. Higher layers depend on interfaces and schemas, not implementation details. This prevents a foundation change from toppling the rest of the system.

## Core rule

> No foundation service may import another foundation service's internals. Services depend on interfaces, contracts, and result envelopes.

## Boundary examples

| Component | May depend on | Must not depend on |
|---|---|---|
| Orchestrator | MemoryService interface, ToolBroker interface, ModelRouter interface | Postgres tables, provider SDKs, raw filesystem writes |
| Tool Broker | ConsentService interface, SecretBroker interface, EventLedger interface | UI code, Orchestrator internals |
| File Manager | Workspace config, EventLedger interface | Model provider clients, scanner internals |
| Memory Service | Memory store interface, embedder interface, EventLedger interface | UI code, provider adapters |
| Provider Adapter | SecretBroker credential handle, Provider Registry | raw secrets, Orchestrator internals |
| OpenWebUI shell | Agent API boundary | database, tools, memory, event ledger directly |
| TypeScript Control Center | Agent API boundary | direct DB writes or tool execution |

## Dependency injection rules

1. Services receive dependencies through constructors or explicit runtime wiring.
2. Tests can inject fake services.
3. Runtime configuration is passed as typed config objects, not read ad hoc from global environment in deep modules.
4. Secret values are resolved only by Secret Broker.
5. Capability flags are checked at service boundaries.

## M0/M1 code rules

- Define interfaces before deep implementations.
- Keep adapters thin.
- Put shared schemas in one place.
- Avoid circular imports.
- No service should directly instantiate high-risk dependencies inside business logic.

## Contract testing

Every service boundary should have tests that validate:

```text
input schema
output envelope
error envelope
redaction behavior
actor context requirement
idempotency requirement for mutable actions
classification propagation
```
