# ADR-0060: Local Atomicity, External Partial Completion, And Compensation

Status: Accepted semantics; external execution remains blocked.

## Decision

Only operations committed by one proven local unit of work may claim
`local_atomic`. Each such operation requires a rollback plan. External
operations use `external_compensating`, never claim atomicity, and require a
compensation plan before review.

Future execution records per-operation durable start and terminal truth.
Partial completion is an explicit product state. Compensation is a new exact
operation subject to current authority; it is neither guaranteed nor silently
performed. Unknown external execution truth becomes recovery-required and is
never retried as if nothing happened.

## Consequences

The UI must distinguish what applied, what did not start, what failed, what can
be compensated, and what needs operator investigation. A successful local
operation cannot be reported as rolled back merely because a later external
operation failed.

## Rejected

Distributed-transaction claims over connectors, automatic destructive
compensation, and "all done" summaries for partial outcomes were rejected.
