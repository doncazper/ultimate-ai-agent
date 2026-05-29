# ADR-0037: Use Python Agent Core and TypeScript Control Center

Status: Accepted

## Context

The Ultimate AI Agent needs a scalable runtime for orchestration, contracts, model routing, memory, files, tools, evals, event logging, and sandbox workflows. It also needs a durable user-facing control surface for approvals, memory editing, permissions, scanners, watchlists, costs, and receipts.

A single-language architecture would be simpler, but it would force one ecosystem to do jobs where another is stronger.

## Decision

Use Python for the Agent Core and TypeScript for the custom Control Center.

Python owns:

```text
Orchestrator
Execution Contract
Context Pack
Model Router
Event Ledger
Consent Ledger
Tool Broker
Memory Service
File Manager
QA/Evals
Workers
Foundation Gate tests
```

TypeScript owns:

```text
User Control Center
Approvals Queue
Memory/Permission UI
Watchlist/Scanner UI
Notification and Cost Dashboards
Typed API client
Browser extension later
```

## Consequences

Benefits:

```text
Agent runtime uses the strongest AI/tooling ecosystem.
Frontend/control surfaces get type-safe maintainability.
The project can scale without forcing UI concerns into the agent brain.
API contracts become the seam between runtime and UI.
```

Costs:

```text
Two-language repo management.
Need generated/shared contracts.
Need discipline around API boundaries.
```

## Guardrail

The TypeScript Control Center must call Agent Core APIs. It may not write directly to memory, files, consent, event ledger, or tools.
