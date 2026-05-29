# ADR-0039: Use a Stable Agent API Boundary

Status: Accepted

## Context

The Ultimate AI Agent will have multiple clients and surfaces: OpenWebUI, a TypeScript Control Center, CLI scripts, workers, future mobile/browser surfaces, and possibly external agent protocols.

Without a stable API boundary, clients may bypass policy or couple to internal implementation details.

## Decision

Expose the Agent Core through a stable API boundary. All clients must enter through this boundary.

The API boundary must enforce:

```text
Execution Contract rules
Context Pack rules
Consent Ledger checks
Tool Broker path for actions
Event Ledger logging
Model Router policy
Cost policy
redaction policy
receipt generation
```

## Consequences

Benefits:

```text
Clients remain replaceable.
OpenWebUI can be swapped or supplemented later.
Control Center can evolve independently.
Contracts become testable.
Foundation changes are less likely to topple higher layers.
```

Costs:

```text
Need OpenAPI/JSON Schema discipline.
Need contract tests.
Need versioning once external clients exist.
```

## Guardrail

No client may directly access Postgres, object storage, canonical files, memory writes, or tool execution in production paths.
