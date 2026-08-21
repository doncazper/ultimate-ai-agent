# ADR-0064: Canonical Tasks And Mission Ownership

Status: Accepted for the bounded ECO-002 core; product cutover and UI remain
deferred.

## Decision

`core.ecosystem.tasks` owns canonical local task and commitment truth. Plans
continues to own projects, while the durable mission subsystem continues to own
mission execution state. A Task may retain exact safe references to one mission,
run, plan, owner, evidence, handoff, and recovery record, but it does not copy or
independently mutate mission execution state.

Canonical Tasks use the encrypted ECO-001 repository, optimistic versions, an
exact `ecosystem.tasks.apply` approval action, encrypted exact replay, and
archive-before-delete semantics. Dependencies must resolve within the
workspace and remain acyclic. One mission ref may have only one active canonical
Task owner.

Recurrence is a deterministic, explicit plan-and-materialize operation. ECO-002
does not start a scheduler, worker, or background execution loop. Existing
Founder Loop local-task rows are compatibility input only; the included reader
produces a bounded read-only safe-ref preview and cannot infer missing private
task titles.

## Explicitly deferred

- production key and trusted-path backends;
- Founder Loop cutover or deletion of historical rows;
- Tasks routes, Control Center UI, packaging, or public distribution;
- project CRUD or ownership, which remains with Plans;
- external task-provider reads or writes;
- background recurrence, reminders, collaboration, or mission execution.

These require separately scoped authority, migration, recovery, route, UI, and
acceptance evidence.
