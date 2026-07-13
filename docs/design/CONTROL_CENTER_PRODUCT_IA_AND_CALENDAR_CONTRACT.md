# Control Center Product IA And Integrated Calendar Contract

Status: canonical target design contract, documentation and renders only

Contract ID: `CC-IA-CALENDAR-2026-07-11`

Revised: 2026-07-13 for the accepted News & Signals front-page target

Parent specification: `CONTROL_CENTER_UI_UX_SPEC.md`

Repository baseline: `v0.104.0` / package `0.104.0`

This contract locks the target product information architecture and the
governed calendar integration loop for future Control Center renders and
implementation. It does not add routes, connector reads or writes, runtime
behavior, provider/model calls, external calendar authority, or production
readiness. Current implementation truth remains authoritative until each lane
is separately implemented, tested, and promoted.

## Product Navigation

The default left rail is ordered by the founder's daily work, not by the
system's internal architecture.

### Primary workspaces

1. **Today** — the default landing surface and daily rundown.
2. **Communications** — unified email, messages, follow-ups, drafts, and items
   waiting on other people.
3. **Messenger** — an immersive Element-familiar Matrix client for direct
   messages, rooms, Spaces, threads, files, people, and governed UAA assistance.
4. **Work Board** — kanban, list, timeline, plans, and completed work.
5. **CRM** — people, organizations, opportunities, pipeline, follow-ups, and
   relationship activity.
6. **Calendar** — day, week, month, and agenda views combining commitments,
   proposed events, deadlines, focus blocks, and linked work.
7. **News & Signals** — personalized outside context grouped by familiar news
   categories and explicit source feeds, with bounded Morning Brief candidates.
8. **Studio** — one familiar immersive chat and coding workbench for asking, planning,
   editing, reviewing changes, running allowed checks, and inspecting proof.

### Supporting workspaces

- **Knowledge** combines durable memory, files, reviewed context, and source
  provenance without presenting recalled material as truth.
- **Activity & Trust** combines receipts, evidence, proof, event history,
  approvals, and authority inspection. It is easy to reach but does not
  displace daily work in the primary rail.

### Bottom utilities

- **Customize** changes rail order, visibility, groups, and density only.
- **Settings** remains fixed near the bottom and uses UAA as search.
- **Developer Tools** is collapsed and hidden by default for ordinary users.
  Runtime, models, storage, API routes, Foundation Gate, plugin governance,
  and other technical diagnostics live here.

Today is fixed first and Settings remains fixed near the bottom. The operator
may reorder or hide the middle primary and supporting workspaces without
disabling capabilities. `Start Here` is an onboarding state; after setup it
moves into Settings and does not remain permanent primary navigation.

Action Inbox is a global decision utility rather than a permanent primary
workspace. When decisions exist, the shell shows `Review N decisions` with the
real workload. When none exist, the control is demoted or omitted. The same
queue remains reachable from command search, attention items, and Activity &
Trust.

## Current-To-Target Surface Mapping

This mapping guides renders and later consolidation. It does not create,
rename, or remove current routes.

| Current surface or concept | Target home |
|---|---|
| Today and Briefing | Today |
| Source Inbox, email, messages, drafts, follow-ups | Communications |
| Matrix direct messages, rooms, Spaces, and threads | Messenger |
| Plans and Work Board | Work Board, as views of shared work |
| CRM | CRM |
| Calendar connector contracts and future schedule UI | Calendar |
| Today News module and future sourced brief views | News & Signals |
| Chat and Coding | Studio, with Chat and Code modes |
| Memory and Files | Knowledge |
| Receipts, Evidence, Proof, Trust, Events, Approvals | Activity & Trust |
| Runtime, Models, Storage, API Routes, Foundation Gate, Plugins, Setup diagnostics | Developer Tools |
| Settings | Settings |

No consolidation may duplicate durable truth in React state. Target views use
shared backend-owned refs and contracts; the same commitment can appear in
Communications, Calendar, CRM, Today, and Work Board without becoming five
independent records.

## Workspace Contracts

### Communications

Communications provides Unified, Email, Messages, Follow-ups, Drafts, and
Waiting views. The default desktop layout is a compact queue, readable detail,
and contextual inspector. Contextual actions include `Summarize`, `Draft
reply`, `Add follow-up`, `Link CRM`, `Propose event`, `Add to Day Plan`, and
`Ask UAA`. Any send, external write, or connector mutation remains separately
governed and truthfully labeled.

### Work Board

Work Board provides Board, List, Timeline, Plans, and Completed views. A task
can be linked to a calendar time block, deadline, communication, relationship,
or evidence ref. Scheduling a task changes its schedule relationship; it does
not create an unrelated copy of the task.

### CRM

CRM provides People, Organizations, Opportunities, Pipeline, Follow-ups, and
Reports. It is the canonical relationship context for meetings and follow-ups.
Calendar entries link to CRM refs and show the relationship context needed for
preparation without copying raw correspondence.

CRM exposes a governed `Call` action with an availability-backed method chooser
for system/iPhone, FaceTime Audio, WhatsApp, Telegram, Google Voice, and future
approved adapters. Launch and call outcome are distinct states; no dialer launch
marks a relationship follow-up complete. The full exact-call, recording, and
truth-state contract is defined by `CONTROL_CENTER_RENDER_REVIEW_REVISION_02.md`.

The current CRM render remains a general placeholder. Specialty CRM profiles
remain open until their earlier reference variants are reviewed.

### Calendar

Calendar provides Day, Week, Month, and Agenda views, color-coded calendars,
events, commitments, deadlines, focus blocks, routines, preparation/travel
time, and linked Work Board tasks. It reduces schedule-entry friction in the
spirit of a smart family calendar while remaining a distinct UAA product and
visual system.

Every event or proposal accounts for start, end, timezone, all-day state,
recurrence, participants, location, source, linked CRM/work refs, duplicate
risk, and conflicts. UAA can help the operator find time, propose a meeting,
time-block work, or revise a proposal. It cannot silently claim that an event
was created or externally synchronized.

### Studio

Studio combines Chat and Code in an immersive workbench patterned after the
established coding-agent interaction model. It replaces the ordinary product
rail with a Studio identity, visible back command, project/thread rail, dominant
central task/transcript/editor, optional context/changes/checks drawers, one
bottom composer, bottom Settings, and governed Terminal access. It may propose
governed actions and hand work into the same decision, receipt, and evidence
loop as every other surface; it is not a second authority system.

### Messenger

Messenger is a separate primary workspace from Communications. Communications
retains the accepted unified email, message-source, follow-up, draft, and
waiting-on-others hub. Messenger is the full Matrix client.

Like Studio, Messenger is an immersive shell exception. It replaces the normal
rail with a Messenger identity, visible Back to Control Center command, Home /
All Messages, exactly two primary Spaces (Founder HQ and Personal Circle), room
and direct-message lists, and account/security access. The conversation timeline
is dominant. Room details or UAA intelligence may occupy a collapsible right
inspector. The human message composer and Ask-UAA field remain separate.

### News & Signals

News & Signals provides For You, Categories, Source Feeds, Saved, and Sources.
The default front page groups outside context by familiar categories such as
AI, Technology, Business, Politics, World, Sports, Science, and Culture while
allowing later user-configured additions.

Source Feeds preserves the identity of each authorized intake path. Reddit
findings, watched public X posts, email newsletter bulletins, Discord channels,
RSS feeds, official blogs, YouTube channels, podcasts, and later exact adapters
must remain individually inspectable rather than being flattened into an
unsourced cluster. The product taxonomy does not grant adapter authority.

Each item keeps category, source, freshness, content type, source count, and
selection rationale visible. Curated ranking may later use explicit interests,
CRM/business watchlists, reviewed settings, and authorized read-only bulletins,
but never hides provenance or grants live web fetching. A bounded Morning Brief
queue projects selected candidates into the canonical Morning Briefing without
duplicating the full pool. News & Signals is not an attention queue and is not
completable work.

## Source-To-Calendar Proposal Loop

### Inputs

A calendar candidate may originate from:

- a read-only email or message signal;
- a CRM meeting, follow-up, or relationship commitment;
- a Work Board deadline or time-block request;
- a Today priority;
- a reviewed memory commitment;
- an existing calendar conflict or open slot; or
- an explicit operator request to UAA.

The source produces a **candidate**, not an event. Raw message and email bodies
are not copied into durable calendar state. The proposal uses bounded redacted
summaries, safe refs, and explicit provenance.

### Candidate envelope

The review surface shows:

- source safe refs and bounded source summary;
- proposed title, start, end, timezone, all-day state, and recurrence;
- participant and location safe refs;
- linked CRM, Work Board, project, and communication refs;
- confidence, duplicate check, schedule conflicts, and stale-source state;
- proposed action, exact write scope, authority mode, and expiry; and
- expected receipt, rollback or corrective path, and external-sync posture.

### Governed sequence

1. A read-only source signal creates a source-backed candidate.
2. UAA drafts a calendar proposal and explains why it inferred the commitment.
3. The core validates duplicates, conflicts, timezone, participant identity,
   recurrence, freshness, and the exact requested scope.
4. Action Inbox lets the operator edit, approve, reject, or defer the exact
   proposal. Approval of one event grants no standing calendar authority.
5. If an implemented local-only calendar lane is authorized, the app records
   the local schedule item. External connector writes remain blocked until an
   exact connector lane is separately promoted.
6. A successful exact mutation produces a receipt/evidence ref. A blocked,
   failed, or expired request remains visibly unresolved.
7. Calendar, Today, CRM, Communications, Messenger, Work Board, and Activity &
   Trust update from shared refs and receipts rather than duplicated UI truth.

Rescheduling, cancellation, participant changes, and external synchronization
use the same exact-scope sequence. Default posture is ask-first. Any future
narrow auto-approval policy requires a separately accepted authority
graduation with safe-disable, idempotency, rollback readiness, tests, and proof.

## Truth-Safe State Grammar

The interface must distinguish:

- `Candidate` — inferred but not yet submitted for decision;
- `Awaiting approval` — exact proposal queued for review;
- `Scheduled locally` — receipt-backed local schedule item;
- `Synced externally` — receipt-backed external connector write only;
- `Conflict` — proposed time overlaps or violates a scheduling rule;
- `Stale` — source or proposal needs revalidation;
- `Failed` — attempted exact lane did not complete;
- `Cancelled` — receipt-backed cancellation; and
- `Blocked` — policy, authority, connector, or implementation does not permit
  the requested action.

`Complete`, `scheduled`, `sent`, and `synced` are never inferred from a button
press or optimistic UI. They require backend-owned result state and the
applicable receipt. Rejected and deferred proposals stay auditable without
appearing on the committed calendar.

## Locked First Render Set

The complete target V1 default render set consists of:

1. `TARGET-NAV-01` — Today with the locked product rail, six panels, receipt
   activity rail, workload-aware decision CTA, weather, and UAA composer.
2. `CAL-01` — Calendar week view with approved events, linked work, a visibly
   provisional source-backed candidate, conflicts/duplicate posture, and its
   contextual inspector.
3. `DECISIONS-01` — Action Inbox review of the exact calendar proposal, including
   source, time, participants, links, conflict result, authority, and outcomes.
4. `COMM-01` — Communications detail with the `Propose event` handoff and CRM
   relationship context.
5. `STUDIO-01` — combined Chat/Code workbench.
6. `ACTIVITY-01` — consolidated Activity & Trust workspace.
7. `BOARD-01` — Work Board with shared task, plan, CRM, calendar, and receipt
   context.
8. `CRM-01` — relationship activity, commitments, pipeline context, and next
   best action.
9. `KNOWLEDGE-01` — reviewed memory, files, context, provenance, and correction.
10. `CUSTOMIZE-01` — presentation-only navigation arrangement and preview.
11. `SETTINGS-01` — search-first preferences and readable governed posture.
12. `DEVTOOLS-01` — consolidated advanced diagnostics and exact local lanes.
13. `ONBOARDING-01` — first-run local readiness and safety defaults.
14. `UAA-SIDECAR-01` — cross-surface explanation and proposal handoff.

The one-at-a-time review gallery is the approval ledger for these draft visual
targets. Current implementation routes remain separately covered by the full
route matrix and legacy composites until consolidation is implemented.
