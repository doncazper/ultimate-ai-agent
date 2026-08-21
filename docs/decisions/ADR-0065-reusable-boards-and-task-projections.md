# ADR-0065: Reusable Boards And Canonical Task Projections

Status: Accepted for the bounded ECO-003 core; route, UI, migration, and product
cutover remain deferred.

## Decision

`core.ecosystem.boards` owns reusable Board configuration, lanes, board-local
placement and ordering, filters, templates, standalone board-item content, and
protected undo state. Each Board is one encrypted ECO-001 aggregate with a
monotonic optimistic version. Mutations use the exact repository-only
`ecosystem.boards.apply` approval action and encrypted request-context replay.

Canonical Task cards store only their card/placement metadata and Task ref.
They resolve current truth through `TaskRepository`; Boards cannot store a Task
title or description. Tasks therefore remains the sole owner of Task truth and
continues to work without Boards.

Board order is represented as validated contiguous lane-local positions. Each
successful mutation retains the prior protected snapshot in a stack bounded by
both 20 entries and the ECO-001 encrypted plaintext limit; oldest snapshots are
trimmed first so an accepted Board remains mutable. Explicit undo restores one
retained snapshot at a new version. No private before-state is emitted to the
evidence plane.

## Explicitly deferred

- API, OpenAPI, CLI, Control Center, drag/drop, and approval-preview surfaces;
- Work Board migration or compatibility cutover;
- production key/path backends, attachments, portability, and recovery UX;
- mapped Task lifecycle changes or cross-domain ChangeSets;
- cloud collaboration, connectors, background work, external runtime, public
  distribution, and production authority.

Those require separately scoped route, migration, recovery, interaction, and
acceptance evidence.
