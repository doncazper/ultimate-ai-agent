# ADR-0021: Use an Agent Event Ledger

Status: Accepted; expanded in v0.4.7

## Context

The Ultimate AI Agent must be inspectable, recoverable, and safe. It will use tools, files, memory, models, scanners, notifications, and self-improving code. Without a durable event ledger, it will be impossible to debug failures, prove what happened, replay old runs, calculate costs, or maintain user trust.

## Decision

Use an append-only Event Ledger for all meaningful agent runs. The ledger records contracts, context packs, model routes, tool calls, approvals, memory writes, file changes, code execution, evals, notifications, costs, errors, rollbacks, and final delivery.

## Consequences

Positive:
- Creates receipts for users and developers.
- Enables replay/shadow testing before foundation changes.
- Supports cost governance, audit, rollback, and incident review.
- Makes tool and memory actions traceable.

Tradeoffs:
- Requires event schemas and redaction discipline.
- Adds storage and instrumentation work.

## Rule

If an action cannot be logged with a useful receipt, it should not be allowed in production.
