# ECO-000 Implementation-Ready Render Briefs

These briefs cover the remaining ecosystem render program. Status is
`brief-only`; no corresponding asset or implementation acceptance is claimed.

## Shared brief requirements

Every frame uses the accepted shell or an ADR-0061-labeled future variant,
synthetic tiered data, complete primary controls, canonical owner/provenance,
privacy and authority state, keyboard order, screen-reader announcements,
blocked/partial truth, and no raw JSON. Each set must cover empty, loading,
locked, offline, stale, conflict, blocked, partial, error, success, undo, and
privacy-restricted states at desktop and applicable compact/narrow/focus/
wallboard/print modes.

## Calendar set

| Brief IDs | Required composition and interaction proof |
|---|---|
| CAL-DAY, CAL-WEEK, CAL-MONTH, CAL-AGENDA, CAL-MULTI | Time-zone label, calendar visibility, current-time marker, overlap/all-day handling, keyboard navigation, privacy-filtered titles. |
| CAL-EVENT-EDIT, CAL-RECURRENCE | Field-level dirty state, version precondition, recurrence summary/exceptions, save proposal, discard, undo, no account-write claim. |
| CAL-CONFLICT, CAL-SCHEDULING | Conflicting canonical refs, why conflict, safe alternatives, exact proposal diff, no automatic move. |
| CAL-MEETING-PREP, CAL-MEETING-OUTCOME, CAL-TASK-BLOCK | Linked CRM/Task owner refs, source/evidence refs, reviewed candidates, no transcript or model truth. |
| CAL-NARROW, CAL-WALLBOARD, CAL-PRINT | Agenda-first navigation; view-only/private-hidden wallboard; explicit private/redacted print. |

## Tasks set

| Brief IDs | Required composition and interaction proof |
|---|---|
| TASK-INBOX, TASK-TODAY, TASK-UPCOMING, TASK-PROJECT | Quick capture, clarify, due/recurrence, project/dependency, source and canonical refs, deterministic sort. |
| TASK-RECURRING, TASK-INSPECTOR, TASK-WAITING | Series/occurrence separation, version/history, dependency/wait reason, conflict and undo. |
| TASK-DAILY, TASK-WEEKLY, TASK-BULK | Review progress, carry-forward proposals, bulk exact diff and approval boundary. |
| TASK-NARROW-CAPTURE, TASK-COMPLETE-UNDO | Large touch targets, offline capture posture, receipt-backed complete and bounded undo. |

## Boards set

| Brief IDs | Required composition and interaction proof |
|---|---|
| BOARD-GENERAL, BOARD-TASK, BOARD-PLAN | Subject owner badge, lane/order/view-only fields, keyboard move, no copied domain status. |
| BOARD-SALES, BOARD-REAL-ESTATE, BOARD-CLOSING | Shared engine with preset-specific fields; CRM remains canonical. |
| BOARD-TABLE, BOARD-CARD-CUSTOM, BOARD-FILTER | View configuration diff, field sensitivity, saved-filter scope. |
| BOARD-DRAG, BOARD-CONFLICT, BOARD-UNDO | Preview before commit, stale order conflict, receipt, exact undo availability. |
| BOARD-EMPTY, BOARD-DENSE, BOARD-NARROW | Onboarding, 5,000-card synthetic performance intent, narrow inspector and move alternative. |

## CRM set

| Brief IDs | Required composition and interaction proof |
|---|---|
| CRM-HOME, CRM-PEOPLE, CRM-PERSON | Workspace/preset, relationship context, follow-up, linked Events/Tasks, provenance and privacy. |
| CRM-SALES, CRM-REAL-ESTATE | Shared Boards pipeline/transaction views, canonical Opportunity/Transaction, exact local edit proposals. |
| CRM-PROFESSIONAL, CRM-PERSONAL, CRM-PRIVATE | Increasing privacy floor; Private excludes transcript, enrichment, wallboard detail, shared search, and cloud context. |
| CRM-FOLLOWUPS, CRM-SMART-LISTS, CRM-REPORTS | Why-in-list, staleness, source refs, aggregate privacy and export posture. |
| CRM-IMPORT-DEDUPE, CRM-CHANGESET | Untrusted import preview, no silent merge/contact creation, field diff, partial/rollback truth. |

## Inbox and organizer sets

| Brief IDs | Required composition and interaction proof |
|---|---|
| INBOX-TRIAGE, INBOX-THREAD, INBOX-CONTEXT | Source trust label, retention, exclusions, linked owner refs, raw content isolated from Evidence. |
| INBOX-PROPOSALS, INBOX-DRAFT-COMPARE | Per-app candidate boundaries, citations, exact diffs, no send or automatic truth. |
| INBOX-PERMISSION, INBOX-SYNC-CONFLICT | Selected-source scope, configuration versus authority, conflict and safe-disable. |
| ORG-LISTS, ORG-ROUTINES, ORG-MEAL | Local/manual complete workflows, recurrence, completion/undo, private values. |
| ORG-WALLBOARD, ORG-NARROW, ORG-PRINT | View-only locked display, privacy-reduced titles, single-user posture, redacted/private print choice. |
