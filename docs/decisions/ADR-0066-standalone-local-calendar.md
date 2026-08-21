# ADR-0066: Standalone Local Calendar

Status: Accepted for the bounded ECO-004 core; route, UI, notification delivery,
account adapters, migration, and product cutover remain deferred.

## Decision

`core.ecosystem.calendar` owns local Calendar Sets, calendars, events,
recurrence, occurrences, participants, reminder intent, time-zone semantics,
overlap facts, views, and typed portability. Each Calendar Set is one encrypted
ECO-001 aggregate with a monotonic optimistic version. Mutations use the exact
repository-only `ecosystem.calendar.apply` approval action and encrypted
request-context replay.

Task time blocks store only scheduling fields and a canonical Task ref. They
resolve current truth through `TaskRepository` and cannot store a copied Task
title or description. Tasks remains the sole owner of Task truth and continues
to work without Calendar.

Recurring events preserve local wall time in their IANA recurrence zone.
Nonexistent spring-forward times normalize forward; query horizons and result
counts are bounded. Conflict detection reports deterministic overlap facts and
does not silently mutate schedules. Reminder records are `intent_only`; they
grant no scheduler or notification authority.

Every successful mutation retains the prior private aggregate snapshot in an
undo stack bounded by both 20 entries and the ECO-001 encrypted plaintext
limit. Oldest snapshots are trimmed first. Explicit undo restores one retained
snapshot at a new version. No private before-state is emitted to the evidence
plane.

## Explicitly deferred

- API, OpenAPI, CLI, Control Center, accessibility, and approval-preview UX;
- existing-calendar migration, compatibility cutover, and production key/path
  backends;
- OS notification delivery, background scheduling, free-text parsing, and
  autonomous planning;
- Google, Apple, Microsoft, CalDAV, account, sync, invitation, RSVP, and
  external calendar write adapters;
- cross-domain ChangeSets, external runtime, public distribution, and
  production authority.

Those require separately scoped route, interaction, migration, recovery,
adapter-authority, and acceptance evidence.
