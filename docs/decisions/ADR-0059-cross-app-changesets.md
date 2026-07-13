# ADR-0059: Cross-App ChangeSets And Multi-Resource Transactions

Status: Planning contract accepted; execution is not authorized.

## Decision

A `ChangeSetPlan` is an immutable, fingerprinted, review-only DAG of exact
operations. Every operation binds target/version, capability, workspace,
dependencies, conflict precondition, atomicity posture, and rollback or
compensation plan. A ChangeSet plan cannot authorize or execute work.

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
