# ADR-0040: Use Custom Event Ledger + Deterministic State Machine First

Status: Accepted for foundation v0.5.3

## Context

The project needs durable execution, replay, receipts, and run-state recovery. The review correctly noted that freezing run/event schemas before choosing a runtime risks coupling the foundation to an implicit substrate.

## Decision

For the foundation, use a custom append-only Event Ledger plus deterministic run-state machine. Treat Temporal, LangGraph, and other durable workflow runtimes as future adapters, not initial dependencies.

## Consequences

- Keeps the Minimum Lovable Kernel small and inspectable.
- Lets contracts evolve through v0/provisional before adopting a heavier runtime.
- Requires explicit state transition tests and replay harness.
- Future adoption of Temporal/LangGraph must preserve existing Event Ledger receipts or define a migration ADR.
