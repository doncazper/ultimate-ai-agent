# ADR-0020: Use a Consent and Permissions Ledger

Status: Accepted; expanded in v0.4.8

## Context

The agent will access personal/project data, scan communications, monitor sources, write memory, use cloud/local models, and execute actions. Action-level approval is not enough; the system needs durable, inspectable consent boundaries.

## Decision

Use a Consent and Permissions Ledger to record active grants, denied scopes, content boundaries, model routing restrictions, expirations, revocations, and approval requirements. The Orchestrator, Context Pack Builder, Model Router, Tool Broker, Memory Service, File Manager, and scanner modules must consult it.

## Consequences

Positive:
- User remains in control.
- Sensitive data can be scoped by source, account, content category, and purpose.
- Revocation can stop future access and trigger cleanup.
- Enables companion behavior without uncontrolled surveillance.

Tradeoffs:
- Requires policy evaluation and UI surface.
- Some convenience is gated until consent is explicit.
