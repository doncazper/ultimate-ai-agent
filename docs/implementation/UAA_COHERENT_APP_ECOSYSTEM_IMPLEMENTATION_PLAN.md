# UAA Coherent App Ecosystem Implementation Plan

Status: active full-vision implementation plan; planning-only authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-07-13
Subordinate to:
`docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md` and
`docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
Related product plans:
`docs/implementation/UAA_FIRST_CLASS_BOARDS_IMPLEMENTATION_PLAN.md`,
`docs/implementation/UAA_FIRST_CLASS_CRM_IMPLEMENTATION_PLAN.md`,
`docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md` and
`docs/strategy/DELEGATED_LIFE_OS_NORTH_STAR.md`

## Executive Decision

UAA will become a coherent local-first application ecosystem in which Calendar,
Tasks, Boards, CRM, Inbox, Social, Finance & Compliance, Today, Memory, and
Evidence are individually excellent products and materially better when used
together.

The product target is not a set of shallow dashboard widgets. Each primary app
must be standalone-worthy: it has a complete domain model, durable local data,
first-run experience, search, import/export, polished desktop and narrow
layouts, keyboard and accessibility support, failure recovery, API and CLI
parity, tests, performance evidence, and truthful product language.

The apps share one Python Agent Core, one local identity model, one governance
system, and typed cross-app links. They do not share ownership by duplicating
records. Calendar owns events. Tasks owns tasks. CRM owns relationships and
opportunities. Boards owns board membership, layout, and ordering while
projecting canonical domain records. Inbox owns source artifacts. Evidence owns
redacted decisions and receipts. Finance owns books, source observations,
balanced postings, reconciliations, tax-readiness state, and sourced compliance
obligations. Memory remains reviewed recall, not truth or authority.

The target experience is:

```text
Sources and manual input
        |
        v
People, events, tasks, relationships, opportunities, books, obligations,
projects and lists
        |
        v
Today, Calendar, Tasks, Boards, CRM and Finance
        |
        v
Proposal -> Review -> Exact change set -> Receipts -> Evidence -> Memory review
```

This plan shows the complete destination and the implementation sequence. It
does not itself add routes, storage, dependencies, connector runtime, account
sync, sends, calendar writes, provider/model calls, browser automation,
background autonomy, multi-user authority, native distribution, public beta,
public release, or production authority.

## Product Thesis

UAA should feel like one calm operating environment for personal and
professional life:

- Calendar understands commitments, tasks, people, travel, preparation, and
  follow-up.
- Tasks understands Today, projects, deadlines, recurrence, waiting states,
  people, boards, and calendar placement.
- Boards provides beautiful flexible visual organization for general work,
  plans, sales, real estate, and other domain workflows.
- CRM understands people, organizations, relationships, communications,
  activities, sales, real estate, professional networks, friends, and private
  relationships.
- Inbox turns selected email, message, meeting, form, file, and connector
  artifacts into reviewable proposals rather than silently changing product
  state.
- Social turns authorized performance, audience, campaign, cadence, and
  conversation observations into source-linked creator intelligence, then
  routes context to the canonical owning application.
- Finance & Compliance keeps local books continuously reviewable, reconciled,
  evidence-backed, accountant-ready, and connected to sourced obligations
  without treating feeds, suggestions, estimates, or Memory as truth.
- Today and Briefing assemble the operator's actual commitments, priorities,
  follow-ups, events, risks, and evidence gaps across every app.
- Evidence and Memory make the ecosystem trustworthy, correctable, and
  personal without allowing recall or generated output to become authority.

The integrated advantage is not merely that records link to one another. It is
that one source can produce a coherent, selectively approved multi-app update:

```text
Selected message
-> identify a relationship
-> propose a calendar event
-> propose a preparation task
-> link a CRM opportunity
-> place the task on a board
-> show the commitment in Today
-> record one review envelope and per-action receipts
```

## Current Baseline And Gap

The repository already contains partial foundations:

- Founder Loop Today, Action Inbox, Plans, Briefing, Evidence, and Memory
  contracts.
- A backend-owned Work Board with durable ordering, local card/task creation,
  approval, idempotency, receipts, and rollback or safe-disable posture.
- A local-task commit lane, but not yet a canonical standalone Tasks product.
- Calendar and email metadata contracts with connector runtime and account
  access still blocked.
- CRM M2 relationships, follow-ups, timelines, pipelines, smart lists,
  reports, local storage posture, CLI/API reads, and exact local mutation
  receipts.
- Shared PolicyEngine, LocalApprovalAuthority, AuthorityLease, OpenAPI,
  `/api/manifest`, evidence, redaction, and Foundation Gate boundaries.
- North-star renders for the Founder Loop and a partial CRM/source/calendar
  direction.

The principal architecture gap is canonical ownership. Task-like, event-like,
activity-like, commitment-like, and board-card-like records exist in several
lanes without a suite-wide contract naming which record is truth and which is a
projection or link. That must be resolved before the CRM private repository or
a standalone Calendar store is implemented.

## Non-Negotiable Product Bar

### Standalone-worthy

An app is standalone-worthy only when an operator can open it directly,
complete its primary workflows without another UAA app, understand its empty
and degraded states, import and export data, recover from errors, and trust its
local persistence. Integration is an advantage, not a crutch for missing core
functionality.

### One source of truth per object

The same event, task, person, or opportunity may appear in multiple views but
must have one canonical owner and stable ref. A board card that represents a
task is a task projection, not a copied task. A CRM meeting links to a Calendar
event. A Calendar time block may link to a Task without cloning it.

### Full workflows, not screenshots

Every visible control must map to backend-owned read or mutation behavior, or
be clearly labeled presentation-only, planned, proposal-only, or blocked. A
render is a target; it is not feature evidence. No app is complete because its
home screen looks convincing.

### Polish is a release gate

Accessibility, responsive behavior, keyboard workflows, latency, empty states,
conflict resolution, migration, backup, restore, undo, error recovery, and
visual consistency are part of implementation milestones, not a cleanup phase
that may be skipped.

### Local-first and private by default

Private product values live in a protected local data plane. Logs, evidence,
tests, docs, screenshots, metrics, and CLI output use safe refs and synthetic
data. Personal and Dating workspaces remain isolated from professional
briefings, exports, search, and model context unless explicitly enabled.

### Governed integration

Read-only is not automatically low risk. Source sensitivity, fields, time
range, workspace, retention, and purpose determine the authority required.
External writes, sends, deletes, cancellations, and account mutations are
separate exact capabilities.

## Application Portfolio

### UAA Today

Today is the ecosystem home, not another database. It assembles owned records
from Calendar, Tasks, CRM, Plans, Boards, Inbox proposals, and reviewed Memory.
It shows priorities, scheduled commitments, overdue work, waiting items,
relationship follow-ups, opportunity risks, source gaps, and approved recent
changes with reasons and evidence.

### UAA Calendar

Calendar must be useful as a complete personal and professional scheduling app:

- Day, week, month, multi-day, agenda, timeline, and schedule views.
- Multiple calendars and calendar sets with colors, visibility, and privacy.
- Events, all-day events, recurring series, exceptions, reminders, time zones,
  participants, availability, locations, travel buffers, preparation, and
  follow-up.
- Fast event creation, duplicate, reschedule, cancel, restore, and conflict
  handling.
- Task time-blocking without turning every task into an event.
- Availability and scheduling-link proposals, with external creation later
  governed separately.
- Meeting preparation and outcome review linked to CRM relationships, source
  artifacts, tasks, and Evidence.
- Personal organizer layouts for routines and household schedules later.
- Desktop, narrow, full-screen, and wallboard/display modes.

Calendar does not need CRM to function. CRM context enriches an event when a
relationship is linked.

### UAA Tasks

Tasks must be a full task-management product:

- Inbox, Today, Upcoming, Scheduled, Anytime, Someday, Waiting, Flagged, and
  Completed views.
- Projects, areas, sections, subtasks, checklists, priorities, tags, contexts,
  estimates, start dates, due dates, recurrence, reminders, dependencies, and
  waiting-on relationships.
- Quick capture, batch edit, snooze, reschedule, complete, reopen, archive,
  restore, and exact delete.
- Recurrence that distinguishes a recurring rule from generated occurrences.
- Calendar time blocking and board placement through links.
- Task provenance: manual, source-derived proposal, CRM follow-up, plan step,
  routine, or delegated action.
- Review views for daily, weekly, overdue, stalled, and unplanned work.

The current local-task lane becomes a migration input and governed mutation
foundation, not the final Tasks data model.

### UAA Boards

Boards follows
`docs/implementation/UAA_FIRST_CLASS_BOARDS_IMPLEMENTATION_PLAN.md`. That
subordinate plan defines local Trello/kan.bn capability parity, the clean-room
reference boundary, rich-card and deep-link behavior, exact mutation and drag
semantics, Work Board compatibility migration, offline import/export, phased
PR sequence, and first-class acceptance gate without granting runtime
authority.

Boards must be a beautiful general-purpose Kanban and visual-work product:

- Multiple boards, templates, lanes, swimlanes, card types, ordering, WIP
  limits, grouping, filters, saved views, search, and board analytics.
- Board, list, compact, table, timeline, and calendar-linked views where the
  domain supports them.
- Configurable cards with consistent density, badges, dates, people, progress,
  blockers, evidence, and custom fields.
- Mouse, touch, and full keyboard movement with accessible announcements.
- Drag preview, persisted-change review, optimistic concurrency, conflict
  handling, undo, receipt history, and responsive layouts.
- Standalone board items for general visual work.
- Projections for canonical Tasks, Plan steps, CRM Opportunities, Real Estate
  Transactions, Closing Milestones, and governed Playbook steps.

Boards owns board presentation, membership, layout, grouping, and ordering. The
subject domain owns the record's canonical lifecycle fields. A mapped lane move
creates a proposed domain transition; drag alone does not mint authority.

### UAA CRM

CRM follows
`docs/implementation/UAA_FIRST_CLASS_CRM_IMPLEMENTATION_PLAN.md` and includes
first-class presets for:

- Sales.
- Real Estate.
- Professional Network.
- Personal Network.
- Private Relationships, including Dating with stronger isolation.

CRM incorporates people-centered follow-up discipline, smart lists, intake and
action-plan vocabulary, flexible pipelines, custom fields and views, forecasts,
reports, import/export, identity review, meeting candidates, and source-backed
field update proposals. It uses UAA Boards for visual pipelines rather than
shipping a second Kanban engine.

CRM owns relationships, workspace context, organization roles, relationship
follow-ups, opportunities, CRM pipelines, properties, offers, transactions,
and relationship timelines. It links canonical Events and Tasks instead of
creating incompatible duplicates.

### UAA Inbox And Communications

Inbox becomes the governed source and communication workbench:

- Source accounts and connection state.
- Email, message, meeting, form, file, and other source-artifact metadata.
- Threads, participants, attachments, classification, archive state, and
  source provenance where separately authorized.
- Triage, link-to-person/project/opportunity, draft, defer, archive proposal,
  task proposal, event proposal, CRM update proposal, and board placement.
- Draft comparison, recipients, channel, consent, send risk, and exact send
  receipt for later authorized lanes.
- Newsletters, bulletins, receipts, personal correspondence, transactional
  messages, and lead intake as distinct categories.

Inbox owns source artifacts and communication drafts. It does not own the Task,
Event, or CRM record created from an approved proposal.

### UAA Social Media Intelligence

Social is the creator-focused intelligence and coordination surface defined in
`docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md`.

- Overview ranks a bounded daily social briefing over performance changes,
  audience intent, campaign drift, cadence variance, important conversations,
  and source gaps.
- Performance explains cross-channel and post-level trends with freshness,
  missing coverage, uncertainty, and evidence refs.
- Audience groups authorized observations about growth, returning engagement,
  repeated questions, and relationship candidates without silently creating or
  enriching CRM records.
- Campaigns connects observed outcomes to canonical Calendar slots, Work Board
  production, Communications threads, CRM relationships, Studio assets, and
  Evidence refs.
- Sources makes configuration, authority, field scope, freshness, retention,
  stale, partial, and blocked posture explicit.

Social owns interpretation and derived creator-intelligence projections.
Calendar owns time, Work Board owns production, Communications owns
conversations, CRM owns relationships, Studio owns assets, and Evidence owns
proof. The initial milestone is read-only and adds no account authentication,
live connector read, background sync, publishing, reply, delete, moderation,
provider/model call, or external account authority.

### UAA Finance & Compliance

Finance is the continuous bookkeeping, spending intelligence, tax-readiness,
accountant-handoff, and sourced obligation product defined in
`docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md` and sequenced by
`docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`.

- A protected local double-entry core separates immutable source observations,
  normalized candidates, suggestions, and reviewed balanced postings.
- A dedicated review queue learns through explicit deterministic rules and
  repeated corrections while abstaining on uncertain or high-consequence work.
- Receipts, statements, business purpose, allocations, questions, and
  reconciliation proofs remain linked to exact financial objects.
- Tax readiness produces a clear checklist and reproducible accountant packet;
  it does not claim professional approval or filing.
- Compliance obligations carry entity, jurisdiction, applicability, official
  source, effective/freshness dates, review state, evidence, and Calendar
  projections.

Finance owns books, accounts, observations, candidates, journal entries,
postings, classifications, reconciliations, readiness state, obligations, and
filing instances. Action Inbox owns pending decisions, Calendar owns time,
Boards/Plans own multi-step work, Evidence owns protected proof or safe refs,
and Today owns priority. The initial implementation is manual/file-import and
local-first; live financial aggregation, maintained compliance feeds,
accountant access, payment, filing, and professional services remain exact
later lanes.

### UAA Lists, Routines, And Personal Organizer

Lists and routines provide the Skylight-like personal organization layer
without forcing every item to become a project task:

- Custom lists, checklist-style lists, grocery, packing, wish, reference, and
  household lists.
- Routines, chores, recurring responsibilities, assignments, completion
  history, and optional reward posture later.
- Meal-plan and household-schedule profiles as optional modules rather than
  universal founder UI.
- Calendar and Today projections for scheduled routines.
- Task conversion when a list item becomes accountable work.

The initial product remains single-user founder/operator focused. Household
sharing, child profiles, team assignment, and rewards require later identity,
permission, consent, and collaboration milestones; they are not implied by a
layout.

### UAA Evidence, Memory, Trust, And Settings

These remain shared control planes rather than standalone copies in each app:

- Evidence shows proposals, approvals, receipts, corrections, partial
  outcomes, rollbacks, conflicts, blocked work, and source provenance.
- Memory offers reviewed recall for preferences, relationships, projects,
  routines, and outcomes; it never authorizes an action.
- Trust shows active exact scopes, source bindings, privacy, retention,
  revocation, safe-disable, and kill-switch posture.
- Settings configures apps, workspaces, presets, fields, calendars, boards,
  imports, exports, backups, connectors, notifications, accessibility, and
  appearance without becoming a broad authority toggle.

## Canonical Object Ownership

| Owner | Canonical records | Other-app relationship |
|---|---|---|
| Identity | `Person`, `Organization`, `Household`, `Workspace`, `ContactPoint`, `IdentityAlias`, `IdentityMatchCandidate` | All apps link by stable identity refs; workspace-private context remains scoped. |
| Calendar | `Calendar`, `CalendarSet`, `Event`, `EventSeries`, `EventOccurrence`, `EventParticipant`, `AvailabilityBlock`, `Reminder` | CRM links meetings; Tasks links time blocks; Today projects occurrences. |
| Tasks | `Task`, `TaskOccurrence`, `Checklist`, `Subtask`, `TaskDependency`, `TaskRecurrence`, `Commitment` | Boards projects tasks; Calendar schedules time; CRM links follow-ups. |
| Plans | `Project`, `Plan`, `Milestone`, `PlanStep`, `PlanDependency` | Tasks may implement steps; Boards projects plan state; Today shows current milestones. |
| Boards | `Board`, `BoardView`, `Lane`, `Swimlane`, `BoardMembership`, `CardProjection`, `CardOrdering`, `BoardTemplate` | Canonical subject remains in Tasks, Plans, CRM, or standalone `BoardItem`. |
| CRM | `Relationship`, `WorkspaceContext`, `OrganizationMembership`, `Role`, `Circle`, `FollowUp`, `Opportunity`, `Pipeline`, `PipelineStage`, `Property`, `Showing`, `Offer`, `Transaction`, `ClosingMilestone` | Links Events, Tasks, Sources, Plans, Boards, Evidence, and Memory. |
| Inbox/Communications | `SourceBinding`, `SourceArtifact`, `ConversationThread`, `CommunicationItem`, `AttachmentRef`, `CommunicationDraft` | Produces proposals for Tasks, Events, CRM, Lists, and Boards. |
| Social intelligence | Planned `SocialMetricSnapshot`, `SocialSignal`, `SocialCadenceAssessment`, `SocialAudienceObservation`, `SocialCampaignProjection`, and `SocialBriefingItem` nouns pending a later ADR/schema milestone | Interprets source-linked observations and opens typed projections in Calendar, Work Board, Communications, CRM, Studio, Evidence, and Memory review without copying their records. |
| Organizer | `List`, `ListItem`, `Routine`, `RoutineOccurrence`, `MealPlan`, `HouseholdResponsibility` | Calendar and Today project scheduled items; Tasks receives promoted accountable work. |
| Integration catalog | `CatalogEntry`, `CapabilityDefinition`, `SourceBindingProposal`, `CapabilityProposal`, `ConnectorCursor`, `SyncConflict` | Describes available and configured capabilities without granting authority. |
| Governance | `ChangeSet`, `ChangeOperation`, `ApprovalRecord`, `MutationReceipt`, `RollbackRef`, `EvidenceRef`, `PolicyDecision` | Every mutating app uses the same consequence and receipt grammar. |
| Memory | `MemoryCandidate`, `ReviewedMemory`, `MemoryProvenance`, `CorrectionRecord` | Apps may cite reviewed recall but never treat it as canonical object truth. |

### Projection rule

A projection contains display and placement data plus the canonical subject
ref. It cannot silently fork domain state. A CRM opportunity card may store its
board ref, lane mapping, order, collapsed state, and visible-field selection;
the CRM opportunity remains the owner of value, status, stage history, and
close posture.

### Cross-app link rule

Typed `EntityLink` records connect canonical refs with relationship kind,
workspace, visibility, provenance, timestamps, and deletion posture. Links are
not hidden context injection. Private links remain excluded from disallowed
search, briefings, exports, and model context.

### Activity and timeline rule

Each app owns its domain changes. A shared timeline service projects safe event
summaries and related refs. It does not copy raw private content into Evidence.
CRM may show an Event or Task in a relationship timeline through links while
Calendar and Tasks remain canonical.

## Local Data Platform

The ecosystem requires a common local application-data platform rather than a
different JSON store for every app.

Target posture:

- SQLite-backed repositories with module-owned schemas, explicit migrations,
  foreign-key and ref-integrity checks, transaction boundaries, and versioned
  projections.
- A shared unit-of-work layer for atomic local multi-app change sets.
- Encryption-at-rest and macOS-first key lifecycle for private product values.
- Workspace and field sensitivity metadata.
- Full backup, incremental backup, restore preview, recovery, integrity check,
  repair posture, and migration rollback or recovery guidance.
- Archive-first lifecycle, retention controls, per-workspace export, private
  encrypted export, redacted support export, and exact permanent deletion.
- Offline-first reads and local mutations. Connector sync is an optional
  governed source, not a dependency for app usability.
- Search indexes scoped by workspace and privacy, with rebuild and corruption
  recovery.
- Safe-ref event and receipt projection separated from private application
  values.

Existing Founder Loop SQLite, Work Board JSON, CRM snapshot/JSONL, and local
task receipts require an explicit migration inventory. No store is silently
deleted or reinterpreted. Compatibility readers, previewed migrations,
idempotency, backups, and cutover receipts are required.

## Governed Cross-App Change Sets

Integrated workflows need one understandable review without weakening exact
authority.

A `ChangeSet` contains ordered operations, dependencies, source refs, affected
apps and workspaces, field-level diffs, risk, approvals, idempotency, conflict
preconditions, rollback or compensation posture, expiry, and predicted result.

Local operations sharing one database transaction may commit atomically.
External operations cannot pretend to be atomic. They execute through separate
capabilities and record per-operation outcomes:

- `not_started`
- `applied`
- `replayed`
- `skipped`
- `denied`
- `conflicted`
- `failed`
- `compensated`
- `compensation_failed`

The product must explain partial completion and offer the next safe action.
One approval screen may cover a bounded set, but every operation is still
validated against its exact resource, source binding, capability, and scope.

## Capability Catalog And Connector Architecture

The ecosystem uses two layers:

1. A curated catalog describing pinned adapters, versions, hashes, supported
   capabilities, risk, sensitivity, review state, and proof requirements.
2. Workflow vocabulary for calendar commitments, CRM lifecycle, meeting
   evidence, intake, enrichment, communication segments, tasks, and lists.

The catalog must distinguish:

```text
Available in catalog
Configured for a source
Source binding reviewed
Capability proposed
Authority accepted
Operation executed
Receipt verified
```

No earlier state implies a later state.

Connector graduation order:

1. Contract and catalog metadata only.
2. Manual file import preview.
3. Exact selected-source metadata reads.
4. Exact bounded content reads.
5. Refresh and incremental sync with cursors, provenance, conflict review,
   revocation, retention, and safe-disable.
6. Draft proposals.
7. Exact writes one resource/action kind at a time.
8. Bounded recurring rules only after separate background-worker and standing
   approval evidence.

Email read, message read, transcript read, event create, event update, event
cancel, CRM update, archive, delete, label, send, and notification delivery are
different capabilities. Transcript access is high-sensitivity and later than
selected summary or metadata reads. Dating and other private workspaces exclude
transcripts and enrichment by default.

## Presets And Custom Layouts

Presets are versioned product configurations, not alternate databases or
hard-coded apps. They can define:

- App modules and navigation emphasis.
- Vocabulary and labels.
- Record types, roles, fields, validation, and inspectors.
- Default calendars, task views, boards, pipelines, stages, lists, routines,
  smart lists, reports, and dashboard modules.
- Card templates and visible fields.
- Privacy, search, briefing, export, connector, and model-context policy.
- Onboarding and sample-data posture.

Initial ecosystem profiles include:

- Founder/Operator.
- Sales.
- Real Estate.
- Professional Network.
- Personal Network.
- Private Relationships.
- Personal/Household Organizer later.

Operators can show, hide, reorder, and resize approved modules; configure
fields, filters, views, stages, cards, calendars, colors, and routines; and save
layouts per device class. These preferences remain backend-owned when durable.
Changing a preset produces a non-destructive diff and migration preview. It
must not silently delete fields, stages, views, or records.

## Experience Architecture

### Shared shell

The current Control Center shell remains the first product container. App-local
navigation lives inside the route workspace. Direct deep links, command-palette
entry, recent items, global search, notifications, privacy state, connection
state, and review status are consistent across apps.

Planned primary destinations after accepted route work:

```text
Today
Inbox
Social
Calendar
Tasks
Boards
Plans
CRM
Action Inbox
Memory
Evidence
Settings
```

This route plan is not implemented by this document and must be reconciled with
the accepted static shell and route manifest before changes.

### Standalone launch quality

Each primary app supports direct launch into its own home, app-specific
onboarding, app settings, search, quick capture, import/export, and complete
core workflows. Initially this may remain within one Control Center bundle.
Separate native binaries, public app distribution, and mobile apps are later
packaging decisions, not requirements for domain independence.

### Unified search and command

Search respects workspace isolation and field sensitivity. Results identify
record type, owner app, workspace, why shown, provenance, and allowed actions.
Commands create drafts or proposals and never bypass an owning app's mutation
contract.

### Notifications

Notifications are derived from canonical Events, Tasks, source activity,
follow-ups, approvals, and sync failures. Notification delivery, scheduling,
channels, quiet hours, batching, snooze, and action buttons require their own
contracts and receipts. A badge count is not an execution system.

### Display modes

- Desktop standard: full app workflows.
- Compact/narrow: capture, Today, agenda, tasks, people, follow-ups, and board
  inspection without hiding risk or destructive controls.
- Focus mode: one meeting, task session, board, or CRM workflow.
- Wallboard/household display: large schedule, routines, lists, and Today state
  with privacy-aware content; later gated for shared identities.
- Print/export: human-readable schedules, plans, lists, and reports with
  explicit private/redacted modes.

## Golden Integrated Workflows

### Message to commitment

```text
Selected message -> person match candidate -> event candidate -> task candidate
-> CRM link candidate -> review -> exact local change set -> Today projection
```

### Sales meeting loop

```text
Opportunity -> meeting prep -> Calendar event -> meeting artifact
-> decision/commitment candidates -> field update proposals
-> follow-up Task -> pipeline Board -> forecast and Evidence
```

### Real Estate transaction loop

```text
Lead intake -> identity review -> client relationship -> property/search context
-> showing events -> offer/transaction Board -> closing Tasks and milestones
-> calendar commitments -> post-close follow-up
```

### Personal relationship loop

```text
Person -> important date or commitment -> optional Calendar event
-> private reminder -> follow-up -> reflection -> reviewed Memory candidate
```

### Daily planning loop

```text
Calendar occurrences + due Tasks + CRM follow-ups + Plan milestones
-> Today review -> time-block proposals -> Board focus -> completion receipts
-> end-of-day carry forward -> Weekly Review
```

### Creator social loop

```text
Authorized social observations -> performance and audience signals
-> Social briefing -> Calendar publishing context / Work Board content work
-> Communications Social Media thread / CRM relationship context
-> Studio asset link -> observed result -> Evidence and reviewed learning
```

The read-only Social milestone routes context only. It does not publish, reply,
change schedules, create contacts, modify external accounts, or run recurring
sync.

### Household organizer loop

```text
Shared schedule + routines + chores + lists + meal plan
-> daily display -> completion/update proposals -> reminders -> review history
```

Household sharing remains future-scoped until identity, permission, consent,
notification, and multi-user conflict contracts are accepted.

## Automation And AI

### Automation

Automation is expressed as versioned governed playbooks with triggers,
conditions, steps, waits, stop conditions, workspace scope, rate/time limits,
consent, dry-run, preview, enrollment, version pinning, receipts, revocation,
safe-disable, and compensation posture.

Segment membership, saved views, playbook enrollment, recurring rules, and
standing approvals remain separate concepts.

Early playbooks create local proposals and tasks. External sends and writes are
not implied. Editing a playbook version must not silently rewrite active
enrollments without a reviewed migration.

### AI assistance

AI may later assist with:

- Email/message classification and summaries.
- Event, task, relationship, commitment, and field-update candidates.
- Meeting preparation and meeting-outcome proposals.
- Schedule optimization and time-block suggestions.
- Task decomposition and priority explanations.
- CRM follow-up suggestions and pipeline-risk explanations.
- Board setup and layout proposals.
- Social performance explanations, audience-signal clustering, cadence
  observations, campaign lessons, and conversation prioritization.
- Finance category, transfer, split, recurring-pattern, missing-evidence, and
  exception suggestions after deterministic rules, evaluation, and abstention
  gates; no generated tax, accounting, or compliance conclusion is authority.
- Briefings, weekly reviews, and missing-evidence detection.

Every generated result carries source citations, workspace scope, privacy
policy, uncertainty, cost posture, model/provider refs, and review state.
Generated output is not a fact, approval, memory truth, or execution authority.
Private-context use must be explicitly eligible. Provider calls remain blocked
until accepted exact lanes exist.

## North-Star Design And Render Program

The whole ecosystem needs a coherent visual program before broad
implementation. Existing Founder Loop renders remain inputs, not sufficient
proof.

### Global set

- Ecosystem Today home.
- App launcher and direct-app launch.
- Unified search and command palette.
- Cross-app change-set review.
- Partial failure and compensation.
- Evidence and rollback history.
- Privacy/source/authority settings.
- First-run and migration readiness.

### Calendar set

- Day, week, month, agenda, multi-calendar, event editor, recurrence editor,
  conflict review, scheduling proposal, meeting prep/outcome, task time block,
  narrow agenda, and wallboard schedule.

### Tasks set

- Inbox, Today, Upcoming, project detail, recurring task, task inspector,
  waiting/dependency review, daily planning, weekly review, bulk edit, narrow
  capture, and completion/undo.

### Boards set

- General board, task board, plan board, sales pipeline, real-estate
  transaction board, closing milestone board, list/table variant, card
  customization, filters/swimlanes, drag preview, conflict, receipt/undo,
  empty board, dense board, and narrow board.

### CRM set

- CRM Home, People, person detail, Sales, Real Estate, Professional Network,
  Personal Network, Private Relationships, follow-up queues, smart lists,
  pipeline/list, import/dedupe, reports, and change-set review.

### Inbox and organizer set

- Source triage, thread detail, linked-context inspector, multi-app proposals,
  draft comparison, selected-source permission, sync conflict, custom lists,
  routines/chores, meal-plan concept, and household wallboard.

### Finance and compliance set

- Finance Command View, Source & Statement Inbox, extraction/reconciliation
  workbench, transfer and balance-sheet review, ranked Review Batches,
  transaction review, transaction/evidence inspector, books and reconciliation,
  spending/report views, tax readiness and accountant packet, sourced
  compliance obligations, Finance Calendar saved view, and Today/Action
  Inbox/Work Board projections as specified in
  `docs/design/control_center_north_star/renders/finance-compliance-v1/README.md`.

Every set requires desktop, compact, and the relevant narrow or wallboard
variants plus loading, empty, first-run, locked, offline, stale, conflict,
blocked, partial, error, success, undo, and privacy-restricted states.

Render acceptance requires realistic data density, complete primary controls,
keyboard and screen-reader intent, no raw JSON as primary UX, no fake controls,
state and authority truth, and a traceable implementation/state matrix. Each
app milestone may begin only after its relevant render and interaction set is
accepted; render acceptance does not claim implementation.

## Full Implementation Program

### `ECO-000` Suite contract, ownership ADR, and experience acceptance

Acceptance status: accepted on 2026-07-12 for contract, architecture,
migration, threat-model, product-acceptance, route-planning, render-draft, and
quality-target scope. The additive Python contracts live in
`src/ultimate_ai_agent/core/ecosystem/`; ADR-0054 through ADR-0061 record the
decisions. This accepts no app implementation, storage dependency, route,
connector, account sync, external operation, model/provider call, background
work, packaging, or authority. ECO-001 remains a separate threat-reviewed
milestone.

- Ratify canonical object ownership, `EntityLink`, projection, timeline, and
  cross-app change-set vocabulary.
- Inventory overlapping current task/event/activity/card stores and contracts.
- Write ownership, private-data, migration, and multi-app transaction ADRs.
- Define complete route and app navigation targets without adding routes.
- Produce the global ecosystem render/storyboard set and detailed per-app
  render briefs.
- Define measurable performance, accessibility, reliability, and visual
  fidelity budgets.

Gate: CRM-FC-000 and any new Calendar/Tasks repository work cannot finalize
shared Event or Task contracts until ECO-000 ownership is accepted.

### `ECO-001` Shared local application-data platform

- Implement module repositories, migrations, unit of work, private/safe-ref
  planes, encryption/key posture, backup/restore, integrity, search indexing,
  retention, archive/delete, and migration preview.
- Add compatibility readers and cutover plans for existing Founder Loop, Work
  Board, local-task, and CRM state.

Gate: recovery, isolation, crash consistency, migration, backup, restore,
redaction, and performance tests pass before app cutovers.

### `ECO-002` Standalone Tasks V1

- Deliver the canonical Task model, repository, API/CLI, complete local CRUD,
  recurrence, projects, core views, quick capture, reminders posture,
  import/export, browser-tested UI, and migration from current local tasks.

Gate: Tasks works without Calendar, Boards, or CRM and meets standalone quality
criteria.

### `ECO-003` Reusable Boards V1

- Execute the accepted
  `docs/implementation/UAA_FIRST_CLASS_BOARDS_IMPLEMENTATION_PLAN.md` through
  its separately gated product-contract, repository, CRUD, UI, portability,
  projection, advanced-organization, and hardening milestones.
- Refactor the current Work Board into reusable board contracts, multiple
  boards, projections, ordering, templates, card configuration, filters,
  keyboard/touch interactions, conflict/undo, and task projection.
- The standalone Boards product contract may be accepted before `ECO-001`;
  repository, local CRUD, desktop UI, and portability milestones require the
  accepted `ECO-001` shared data platform. Canonical Task projections remain
  separately blocked until `ECO-002` is accepted. This split permits local
  standalone Boards without copying or anticipating Task truth.

Gate: Core V1 local parity is evidenced, general standalone boards and
canonical Task boards work without copied task truth, the current Work Board
migrates through an accepted compatibility path, and cloud/collaboration
capabilities remain explicitly excluded or separately gated.

### `ECO-004` Standalone Calendar V1

- Deliver calendars, sets, events, recurrence, occurrences, participants,
  reminders posture, time zones, conflict handling, core views, quick create,
  task time blocking, import/export, and full local CRUD with receipts and undo.

Gate: Calendar works fully with manual/local data before any account sync and
passes recurrence, time-zone, DST, conflict, accessibility, and performance
tests.

### `ECO-005` First-Class CRM program

- Execute the CRM-FC milestones using canonical Identity, Event, Task, Board,
  Source, ChangeSet, and Evidence contracts.
- Deliver Sales, Real Estate, Professional Network, Personal Network, and
  Private Relationships presets.

Gate: CRM remains standalone-worthy and uses shared Boards without a second
Kanban engine.

### `ECO-006` Today and Briefing ecosystem home

- Accepted bounded projection core on 2026-08-21: deterministic backend-owned
  projections of canonical Events, Tasks, Plan milestones, CRM follow-ups,
  source proposals, blockers, and recent receipts.
- Accepted: explicit why-shown and ordering factors, per-surface CRM privacy,
  current/stale/missing/blocked source posture, evidence posture, and
  proposal-only carry-forward. Existing Founder Loop Today/Briefing remains the
  compatibility product surface.
- Deferred: route/CLI/UI cutover, source refresh, notifications, time-block or
  daily-plan mutation, connectors, and all external/background runtime.

Gate: every Today item traces to an owner app and canonical ref.

### `ECO-007` Inbox and source-artifact workbench

- Accepted bounded local repository on 2026-08-21: encrypted manual/synthetic
  source bindings, source artifacts and threads; content-free import plans;
  exact approval/replay; triage, same-workspace links, blind-index search,
  archive/retention posture, and reviewed downstream proposals.
- Accepted: Inbox retains canonical ownership of source artifacts and
  communication drafts while Tasks, Calendar, CRM, and Boards retain their
  target records. Reviewed proposals may feed ECO-006 but perform no target
  write and grant no mutation authority.
- Deferred: live connector/account reads, file picker/read UX, route/CLI/UI
  integration, source sync, notifications, cross-app execution, and all
  provider/model/browser/background runtime.

Gate: manual/synthetic artifacts can drive reviewed proposals without raw
content leaking to evidence or unrelated workspaces.

### `ECO-008` Cross-app link and ChangeSet engine

- Accepted bounded local Python Core on 2026-08-22: encrypted typed-link
  persistence, content-free field diffs, dependency-ordered updates to existing
  Task/Board/Calendar aggregates, exact approval and replay, one-unit-of-work
  commits, conflict preconditions, encrypted rollback ledgers, separately
  approved rollback, and non-executing external outcome/compensation
  projections.
- Deferred: unified review UX, route/CLI integration, create/delete/lifecycle
  ChangeSets, CRM/Inbox mutation adapters, external execution and compensation,
  connector/provider/browser/model/background runtime, and product cutover.

Gate: the bounded golden local workflow updates multiple apps coherently and
recovers from conflict or failure without duplicated truth. No external
atomicity or standing authority is claimed.

### `FIN-001` through `FIN-008` and `COMP-001` Local Finance & Compliance program

- Execute the protected local books, manual/file import, review/rules/learning,
  evidence, reconciliation, cross-surface integration, reports, tax readiness,
  accountant packet, and manual sourced-obligation milestones in
  `docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`.
- Prove the privacy-safe statement-cleanup and accountant-readiness golden path
  in `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md` with synthetic data.
- Preserve the queue placement in
  `docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md`: first-class
  Boards/Kanban, Calendar, Today, Action Inbox, and shared ChangeSets precede
  runtime implementation; contract/threat-model/render work may proceed earlier.

Gate: the local product works without live accounts or maintained compliance
feeds; bookkeeping invariants, protected-data controls, review and correction,
reconciliation, export, cross-surface ownership, recovery, and CLI/API/UI parity
are evidenced. This gate grants no connector, accountant-access, payment,
filing, provider/model, or professional authority.

### `ECO-009` Exact read-only connector program

- Accepted first lane: one exact, local, caller-supplied or synthetic calendar
  metadata snapshot adapter implements field/time/page bounds, expiring cursors,
  provenance, retention, request replay binding, revocation, safe-disable, rate
  limits, and truthful failure posture. The repo-local inspection CLI exposes
  its registered-snapshot posture. Source Readiness UI reuses the existing
  backend calendar and metadata-contract failure truth instead of adding a
  second Founder Loop read-model field.
- Graduate selected calendar, email, message, CRM, meeting, form, and other
  provider-backed sources one capability at a time; none is accepted by the
  first snapshot lane.
- Add source selection, field/time bounds, sync cursors, provenance, conflict,
  retention, revocation, safe-disable, rate limits, and failure UI.
- Finance and compliance sources enter only as separately named
  `FIN-CONN-001` and `COMP-CONN-001` adapter milestones after their local-domain,
  license/provider, threat-model, and exact-capability gates.

Gate: connector-specific proof exists; no broad read or account-sync flag. The
accepted snapshot adapter performs no external read, account auth, network I/O,
background sync, raw-content ingestion, or connector write.

### `ECO-010` Proposal intelligence and meeting workflows

- Accepted first lane: deterministic extraction maps already-normalized,
  redacted, source-revision-bound facts into cited event, task, person,
  commitment, and meeting candidates with canonical owner, privacy,
  confidence, ambiguity, missing-evidence, and stale-source posture. Python
  Core, a validation-only API, and the repo-local inspection CLI share the same
  contract.
- Deferred: source-specific prose normalization, durable proposal review UX,
  target-app bridges, ChangeSet creation, CRM-update/meeting-decision/follow-up
  expansion, and separately accepted model-assisted candidate generation.

Gate: candidates remain cited, uncertain, reviewable, private-scope aware, and
non-authoritative. The first lane creates no target record, approval, ChangeSet,
or direct commit.

### `ECO-011` Exact external write program

- Graduate event create/update/cancel, CRM update, email/message send,
  archive/label/move/delete, notification delivery, and other writes as
  separate capabilities.

Gate: exact approval, idempotency, receipts, conflict, revocation,
safe-disable, compensation, and test-account evidence for every capability.

### `ECO-012` Playbooks, recurring rules, and bounded automation

- Deliver versioned playbooks, enrollment, triggers, dry-run, proposal-first
  steps, stop conditions, rate/time limits, quiet hours, review queues,
  revocation, and migration.
- Background execution and standing authority remain separately gated.

Gate: automation cannot exceed its exact source, workspace, record, action,
time, rate, spend, or consent scope.

### `ECO-013` Personal and household organizer

- Deliver Lists, Routines, optional meal planning, household schedule layouts,
  wallboard mode, and personal organizer presets over the shared platform.
- Keep initial operation single-user unless ECO-014 is accepted.

Gate: personal/private information is display-safe and workspace isolated.

### `ECO-014` Collaboration and shared spaces

- Add user/household/team identities, invitations, roles, visibility,
  assignment, shared calendars/lists/boards, conflict, notification, consent,
  offboarding, export, and deletion.

Gate: sharing a view never broadens record visibility or action authority.

### `ECO-015` App launch modes, native packaging, and device continuity

- Support direct-app launch, deep links, window restoration, desktop widgets or
  menu integrations where separately accepted, offline continuity, and device
  layout preferences.
- Separate native binaries, mobile apps, app-store distribution, signing, and
  notarization remain their own release milestones.

Gate: packaging cannot claim public distribution before signing, security,
privacy, update, rollback, and release evidence exists.

### `ECO-016` Whole-ecosystem polish, hardening, and dogfood

- Run complete golden paths, private trials, accessibility, performance,
  visual fidelity, migration, recovery, backup/restore, long-duration,
  conflict, offline, connector failure, privacy, security, and redaction tests.
- Remove fake, duplicate, misleading, or dead controls and reconcile product
  language across every surface.

Gate: each app meets standalone criteria and integrated workflows demonstrate
measurable value without authority or privacy regressions.

## Verification And Quality Program

Each milestone adds focused core, storage, API, CLI, frontend, browser,
accessibility, visual, migration, privacy, redaction, authority, replay,
rollback, and performance coverage. Relevant baseline verification includes:

```bash
make doctor
make test
make verify
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
git diff --check
```

Required quality disciplines:

- Synthetic and private trial data only; never actual contacts or raw source
  content in durable test evidence.
- WCAG 2.2 AA target, complete keyboard operation, focus management, reduced
  motion, screen-reader announcements, contrast, zoom, and text overflow.
- Measured local dataset tiers for small, medium, and large usage.
- Performance budgets for launch, navigation, search, filtering, board drag,
  calendar layout, large lists, sync, and change-set review ratified in
  ECO-000. Targets are not claims until measured.
- Time-zone, DST, locale, recurrence, all-day, and clock-change matrices for
  Calendar.
- Optimistic concurrency, stale versions, duplicate submission, replay,
  partial failure, compensation, backup, restore, migration interruption, and
  corruption recovery.
- Desktop, compact, narrow, wallboard, print/export, loading, empty, locked,
  offline, degraded, stale, conflict, blocked, partial, error, success, and undo
  visual states.
- No route or visible action without stable operation ID, side-effect class,
  API manifest truth, CLI inspection, safe evidence, and focused tests.

## Program Dependencies And Critical Path

```text
ECO-000 ownership and experience contract
        |
        v
ECO-001 shared local data platform
        |
        +--> ECO-003A-E standalone Boards
        |
        +--> ECO-002 Tasks --> ECO-003F Task projections
        |
        +--> ECO-004 Calendar
        |
        +--> ECO-005 CRM
        |
        v
ECO-006 Today + ECO-007 Inbox
        |
        v
ECO-008 cross-app ChangeSets
        |
        v
FIN-001..FIN-008 local Finance + COMP-001 manual obligations
        |
        v
ECO-009 reads -> exact FIN/COMP read adapters -> ECO-010 intelligence
        |
        v
ECO-011 writes
        |
        v
ECO-012 automation -> ECO-013 organizer -> ECO-014 collaboration
        |
        v
ECO-015 launch/packaging -> ECO-016 whole-system hardening
```

Tasks, Calendar, and CRM may proceed as separately staffed workstreams after
ECO-001, but they cannot invent conflicting shared contracts. Boards V1 depends
on canonical Task projection decisions. Connector and intelligence work must
not become a substitute for complete local apps.

## Definition Of Done

The coherent ecosystem vision is complete only when Calendar, Tasks, Boards,
CRM, Inbox, and the accepted local Finance & Compliance scope each satisfy their
standalone product contract; Today assembles canonical cross-app truth; shared
identity, links, search, privacy, storage, backup, migration, ChangeSets,
Evidence, and Memory are consistent; the golden integrated workflows are
polished and recovery-safe; presets support work, sales, real estate,
professional, personal, private, finance, compliance, and organizer contexts;
approved connectors and writes are exact-scoped and receipt-backed; automation
is bounded and revocable; desktop, narrow, focus, and applicable wallboard
experiences pass quality gates; and all unimplemented connector, provider,
browser, background, collaboration, accountant-access, payment, filing,
professional-service, packaging, public-release, and production authority
states remain truthfully labeled.
