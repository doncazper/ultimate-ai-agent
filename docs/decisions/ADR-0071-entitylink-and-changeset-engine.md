# ADR-0071: EntityLink Persistence And Local ChangeSet Execution

Status: Accepted for the bounded ECO-008 local core.

## Decision

Persist typed `EntityLink` records on the encrypted ECO-001 data plane and
execute exact updates to existing Task, Board, and Calendar aggregates through
one shared local transaction. A prepared ChangeSet is immutable,
dependency-ordered, content-free at review surfaces, exact-version and keyed-
fingerprint bound, approval-required, idempotent, and paired with an encrypted
rollback ledger.

The engine reuses each owning repository's domain validation and protected undo
semantics immediately before commit. The special local-atomic data-plane action
admits only `PutRecord` updates to existing allowlisted aggregate kinds plus
the ChangeSet ledger; it cannot create/delete/archive arbitrary domain records
or admit CRM/Inbox mutations.

Rollback is never automatic. It is a separately prepared, exact-approved local
transaction whose scope binds every current target version and encrypted
replacement fingerprint. External operation results and compensation remain
non-executing projections.

## Consequences

Local multi-app updates can commit or fail as one SQLite transaction without a
second database or UI-only state. Typed links remain relationship metadata and
never copy mutable domain truth. Partial external outcomes are explainable
without claiming distributed atomicity.

Routes, CLI/UI integration, create/delete/lifecycle ChangeSets, CRM/Inbox
mutation adapters, external capabilities, product cutover, and production
key/path backends require later separately accepted scopes.

## Rejected

Raw field values in review receipts, unkeyed private-value hashes, generic
cross-module writes, mutable operation membership, best-effort fan-out, hidden
link context injection, automatic rollback, distributed-transaction claims,
and approval booleans were rejected.
