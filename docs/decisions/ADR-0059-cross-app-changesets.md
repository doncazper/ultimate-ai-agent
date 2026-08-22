# ADR-0059: Cross-App ChangeSets And Multi-Resource Transactions

Status: Accepted. ADR-0071 implements exact local execution for existing Task,
Board, and Calendar records; external execution and other domains remain
unauthorized.

## Decision

A `ChangeSetPlan` is an immutable, fingerprinted DAG of exact
operations. Every operation binds target/version, capability, workspace,
dependencies, conflict precondition, atomicity posture, and rollback or
compensation plan. A ChangeSet plan cannot authorize work; only the bounded
ADR-0071 engine may execute its separately approved local subset.

One review may present a bounded group, but each future operation must still
pass exact request-scoped policy, approval, AuthorityLease, budget, readiness,
safe-disable, deadline, target, idempotency, and replay evaluation immediately
before start.

## Consequences

Dependencies must be unique, present, and acyclic. Stale versions conflict.
Results use the fixed vocabulary `not_started`, `applied`, `replayed`,
`skipped`, `denied`, `conflicted`, `failed`, `compensated`, and
`compensation_failed`.

## Rejected

Global approval booleans, mutable operation membership, best-effort untracked
fan-out, and UI-only transaction state were rejected.
