# Kanban Work Board Recovery Contract

Status: triage-ready recovery source. It does not grant external task-system or
collaboration authority.

## Outcome

Advance the local Work Board into a first-class UAA task and visual-work
surface with canonical Python-core ownership, governed mutations, recovery,
and cross-surface projections.

## In Scope

- Board, lane, card, ordering, concurrency, filter, and projection contracts.
- Approval-aware drag and mutation receipts with rollback readiness.
- Accessible desktop, narrow, and wallboard render acceptance.

## Out Of Scope

- Trello or third-party code import, cloud collaboration, connector writes,
  background autonomy, or public distribution.

## Acceptance

- Task truth remains canonical outside React presentation state.
- Concurrent ordering and stale mutations fail closed with recoverable state.
- Focused storage, API, CLI, frontend, accessibility, and visual checks pass.
