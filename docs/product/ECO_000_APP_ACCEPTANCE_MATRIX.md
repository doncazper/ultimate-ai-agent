# ECO-000 Standalone Application Acceptance Matrix

Status: product contracts accepted for implementation planning. Every app is
`planned`; none is accepted as implemented by ECO-000. The machine-readable
contract is `docs/product/eco_000_app_acceptance.json`.

## Shared release bar

Every app below must pass all shared dimensions before it can be called
standalone-worthy:

| Dimension | Required acceptance |
|---|---|
| Local/manual usefulness | Complete primary workflow works while all external connectors are disabled. |
| Canonical truth | Every record resolves to the ADR-0054 owner and version; projections never fork state. |
| CRUD | Create, inspect, edit, archive/delete posture, conflict, replay, undo/history, and recovery are complete for local records. |
| Capture/search/views | Quick capture, scoped search, filtering, saved views, recent items, and direct deep links are keyboard operable. |
| Portability | Import preview, exact commit, private export, redacted support export, backup, restore preview, and recovery are tested. |
| States | Empty, loading, locked, offline, stale, conflict, blocked, partial, error, success, and undo have readable, non-JSON-first UX. |
| Modes | Desktop, compact, narrow, focus, print/export, and applicable wallboard intent preserve privacy and authority state. |
| Accessibility | WCAG 2.2 AA target, complete keyboard path, visible focus, announcements, zoom/reflow, reduced motion, contrast, and overflow. |
| API/CLI parity | Any operator mutation uses the same Python contract; inspection is human-readable and redacted; stable routes are classified. |
| Evidence/privacy | Mutation receipts are content-free; private values remain in the protected plane; why-shown/provenance is inspectable. |
| Reliability | Optimistic concurrency, duplicate submission, crash, replay, low disk, corrupt state, backup, and restore are tested. |
| Product truth | Planned, blocked, partial, and implemented states are explicit; no fake control or connector claim is allowed. |

## App-specific matrix

| App | Canonical records | Complete primary workflows | Required views and capture | Integration that improves but is not required | Standalone-worthiness proof |
|---|---|---|---|---|---|
| Calendar | Calendar, CalendarSet, Event, EventSeries, EventOccurrence, EventParticipant, AvailabilityBlock, Reminder | Local calendar setup; quick event; edit/cancel; recurrence and exception; day/week/month/agenda; availability/conflict; task time-block link; import/export; backup/restore | Day, week, month, agenda, multi-calendar, event/recurrence editor, conflict inspector, meeting prep/outcome projection, narrow agenda, wallboard schedule | Account sync, invitations, conferencing, email, CRM meeting link, model-assisted scheduling | Fully useful with manual/local events; time-zone, locale, DST, recurrence, all-day, conflict, undo, and restore matrices pass |
| Tasks | Task, TaskOccurrence, Subtask, Checklist, TaskDependency, TaskRecurrence, Commitment | Inbox capture; clarify/schedule; project grouping; recurrence; dependencies/waiting; Today/Upcoming; complete/undo; bulk edit; daily/weekly review; import/export | Inbox, Today, Upcoming, project, recurring task, inspector, dependency review, daily planning, weekly review, narrow capture | Calendar time blocks, CRM follow-ups, Plans steps, Boards projections, notifications | Current local-task sources migrate once; Tasks works without Calendar/Boards/CRM and passes large-list/replay/conflict proof |
| Boards | Board, BoardView, Lane, Swimlane, BoardMembership, CardProjection, CardOrdering, BoardTemplate, BoardItem | Create board/template; configure lanes/views; add standalone item or link subject; filter/swimlane; reorder/drag preview; conflict; receipt/undo; archive/export | General, task, plan, sales, real-estate transaction, closing milestone, table/list, card inspector, dense/empty/narrow board | Canonical Task/Plan/CRM projections and ChangeSets | No copied Task/CRM state; deterministic ordering, keyboard drag alternative, dense-board performance, undo/recovery pass |
| CRM | Relationship, WorkspaceContext, OrganizationMembership, Role, Circle, FollowUp, Opportunity, Pipeline, PipelineStage, Property, Showing, Offer, Transaction, ClosingMilestone | Relationship capture/review; organization/person linking; follow-up; pipeline; opportunity/transaction; meeting linkage; dedupe proposal; reports; import preview; exact local edit/undo/export | Home, People/person detail, Sales, Real Estate, Professional Network, Personal Network, Private Relationships, smart lists, follow-up queues, pipeline/list, reports, import/dedupe | Calendar Events, Tasks, shared Boards, Inbox sources, approved connector reads/writes | All five presets pass; uses shared Boards; private workspaces isolate; no silent merge/contact creation; local/manual CRM useful |
| Inbox | SourceBinding, SourceArtifact, ConversationThread, CommunicationItem, AttachmentRef, CommunicationDraft | Manual/synthetic ingest; source triage; thread inspect; link candidates; multi-app proposals; draft compare; retention/exclusion; search; conflict; export/delete posture | Inbox/source list, thread detail, linked-context inspector, proposal composer, selected-source permission, sync-conflict and draft comparison | Exact connector reads, sends, Calendar/Task/CRM proposals, model classification | Manual local artifacts drive reviewable proposals; content remains untrusted; no connector or send required |
| Organizer | List, ListItem, Routine, RoutineOccurrence, MealPlan, HouseholdResponsibility | Create/list/check; routine schedule/complete; meal-plan concept; household responsibility planning; daily display; undo/history; import/export | Lists, routine/chores, schedule, meal plan, focused list, narrow capture, wallboard | Calendar projections, Tasks promotion, notifications, future shared spaces | Single-user local/manual organizer is useful; wallboard privacy and private-data handling pass; collaboration remains blocked |
| Today | Projection only across Events, Tasks, Plan milestones, CRM follow-ups, source proposals, approvals, receipts | Morning review; inspect why shown/sources; prioritize; propose time blocks; open owner app; carry forward; completion/receipt refresh; end-of-day and weekly review | Today home, briefing, attention, agenda, focus, recent proof, stale/blocked/private placeholders, narrow Today | Every owner app, Action Inbox, Evidence, Memory review | No Today-owned domain records; every item has owner/canonical ref, workspace/privacy, why shown, freshness, and evidence posture |

## CRM preset acceptance

| Preset | Required objects and views | Privacy/authority floor |
|---|---|---|
| Sales | Organizations, people, opportunities, pipeline, meetings, follow-ups, forecast/report | No external CRM write or send without its own exact capability. |
| Real Estate | Clients, properties, showings, offers, transactions, closing milestones, transaction board | Property/client workspaces isolate; no portal, MLS, email, or calendar mutation implied. |
| Professional Network | People, organizations, roles, relationship strength, commitments, follow-ups | Reviewed recall only; no enrichment or automatic contact creation. |
| Personal Network | People, circles, important dates, commitments, private reminders | Excluded from workspaces unless explicitly linked; local/manual useful. |
| Private Relationships | Private people/context, dates, commitments, reflections | No transcript, enrichment, shared search, wallboard detail, cloud context, or cross-workspace link by default. |

## Acceptance status

ECO-000 accepts the ownership, workflow, state, mode, accessibility, privacy,
and verification requirements. It does not accept any app as implemented.
Implementation status remains `planned` until its milestone supplies code,
tests, measured quality evidence, CLI/API parity, and operator-visible proof.
