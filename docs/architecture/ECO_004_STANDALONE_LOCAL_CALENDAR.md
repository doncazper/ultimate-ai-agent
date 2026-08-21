# ECO-004 Standalone Local Calendar

Status: accepted bounded core on 2026-08-21.

## Accepted implementation

ECO-004 establishes a useful manual/local Calendar aggregate on the encrypted
ECO-001 data plane. `CalendarRepository` supplies:

- multiple encrypted, versioned Calendar Sets with local calendars and events;
- private event title, description, location, participant, and reminder-intent
  records that never enter governance receipts or search terms;
- daily, multi-weekday weekly, and month-day recurrence with bounded occurrence
  expansion, IANA time zones, DST offset changes, and explicit normalization of
  nonexistent spring-forward wall times;
- day, week, month, and 30-day agenda read models with stable occurrence refs;
- deterministic overlap detection that treats adjacent events as non-conflicts;
- structured quick create through the same repository mutation as full create;
- full local event create/update/archive/restore/delete lifecycle, Calendar
  create/update/archive-and-empty delete posture, optimistic concurrency, exact
  replay, receipts, and protected undo;
- typed local export, import preview, and import into a new Calendar Set; and
- Task time blocks that retain only a canonical Task ref and resolve current
  Task truth through `TaskRepository`.

Calendar owns schedules, recurrence, occurrence windows, location,
participants, reminder intent, and calendar organization. Tasks owns Task
title, notes, lifecycle, dependencies, mission binding, and task recurrence. A
Task time block cannot persist a copied Task title or description.

## Authority, privacy, and recovery boundary

Every mutation uses one encrypted ECO-001 unit of work. The local-data plane
reserves `module-ref:calendar` for the repository-only
`ecosystem.calendar.apply` action. Generic local-data calls and raw calls
bearing the Calendar action cannot bypass schema, replay, expected-version,
Task-reference, archive/delete, or payload-boundary validation.

Prior Calendar Set snapshots are retained inside the encrypted aggregate for
at most 20 mutations and are trimmed oldest-first sooner when necessary to
remain within the ECO-001 one-mebibyte plaintext limit. Undo restores the most
recent retained snapshot at a new monotonic version. Import/export is a typed,
explicit local portability operation; exported private content is returned to
the direct caller and is never written to evidence, logs, or default CLI
output.

Reminder records have the literal `intent_only` delivery posture. There is no
timer, notification dispatcher, background scheduler, account adapter, or
external calendar write. Participant status is local operator-managed data,
not a remote RSVP claim.

## Time and conflict semantics

Events carry aware instants plus an IANA display/recurrence time zone. Recurring
events preserve local wall time across offset changes. A wall time that does
not exist during a spring-forward transition moves to the first normalized
local instant while the series continues; ambiguous fall-back times retain the
stored fold. Queries are bounded to 370 elapsed days and 25,000 occurrences.

Conflict results are read-only overlap facts for distinct events in the
requested window. They do not silently move, reject, or reschedule events.
Unbounded future-series conflict proof and automated scheduling remain outside
this core.

## Explicitly not accepted

- No Calendar API route, OpenAPI operation, CLI command, Control Center UI,
  accessibility claim, browser-tested surface, or product-completeness claim.
- No operating-system notification delivery, background reminder scheduler,
  free-text parser, model/provider call, or autonomous time blocking.
- No Google, Apple, Microsoft, CalDAV, ICS-account, or other live adapter; no
  account discovery, credential, sync, RSVP, invitation, or calendar write.
- No production Keychain/path backend, existing-store cutover, cross-domain
  ChangeSet, external runtime, public release, or production authority.

The core is sufficient for later API/CLI/UI milestones to share one governed
Calendar contract. Product cutover still requires route and CLI parity,
approval-preview UX, production key/path backends, accessibility and interaction
evidence, packaging, migration/recovery, and separately authorized adapters.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_004_calendar.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_004_calendar.py tests/test_eco_004_verifier.py
```

The focused suite covers ciphertext at rest, domain-action isolation, exact
replay, optimistic concurrency, CRUD and undo, recurrence and DST behavior,
bounded old-series queries, deterministic conflicts, ref-only Task time blocks,
and typed import/export.
