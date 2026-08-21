# UAA First-Class CRM Implementation Plan

Status: active implementation plan; planning-only authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-07-12
Builds on: `docs/control_center/UAA_CRM_LOCAL_COMMAND_CENTER_PLAN.md`
Current implementation truth: `docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md`
and `docs/architecture/ECO_005_FIRST_CLASS_PRIVATE_CRM.md`
Suite ownership plan:
`docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`

## Decision Summary

ECO-000 was accepted on 2026-07-12 for shared ownership and planning contracts.
The bounded ECO-005 core was accepted on 2026-08-21: encrypted private CRM
portfolio persistence, strict workspace context, exact local mutations, and
live Board-owned pipeline projections now exist. This does not accept product
cutover, M2 migration, API/CLI/UI parity, production key/path backends, or any
connector/provider/browser/background authority; those plan phases remain open.

UAA CRM will become a first-class local relationship operating system, not a
sales-only database and not a collection of unrelated vertical skins. The
shared foundation will support five initial operator workspaces:

1. Personal Network for friends, family, communities, important dates,
   commitments, and intentional follow-ups.
2. Private Relationships, including Dating as a separately isolated workspace
   for connections, dates, preferences, boundaries, reflections, and
   follow-ups.
3. Sales for people, organizations, leads, opportunities, activities,
   pipelines, forecasts, and account follow-ups.
4. Real Estate for buyers, sellers, agents, lenders, properties, showings,
   offers, transactions, closings, and post-close relationships.
5. Professional Network for partners, investors, advisors, vendors,
   candidates, collaborators, introductions, and non-sales business follow-up.

The canonical product loop is:

```text
Capture or import -> Review identity -> Add workspace context -> See what needs
attention -> Review the evidence -> Commit an exact local change -> Record a
receipt -> Feed Today, Briefing, Memory, and Weekly Review
```

The current M2 safe-ref read model, CLI, API, pipeline preview, follow-up queue,
smart lists, local mutation receipts, and `/crm` shell are the starting point.
They are not discarded. First-class CRM work promotes them into a durable
private product data plane, richer domain model, and complete operator UX while
preserving the Python Agent Core, policy, approval, redaction, evidence, and
CLI/API parity boundaries.

This plan does not itself grant connector runtime, account sync, sends,
calendar writes, external CRM writes, model/provider calls, browser runtime,
background autonomy, public distribution, or production authority.

## Product Position

UAA should compete on the complete relationship loop rather than on a generic
feature checklist alone:

- Pipedrive-class fundamentals: people, organizations, leads, opportunities,
  activities, pipelines, stages, custom fields, filters, views, search,
  reporting, import/export, and duplicate review.
- Personal relationship depth: friends, dating, circles, commitments,
  important dates, reflections, and intentional follow-up without treating
  people as deals.
- Real-estate depth: people and organization roles plus property, showing,
  offer, transaction, and closing context.
- UAA-native advantage: Today, Action Inbox, Plans, Memory, Evidence, Briefing,
  Weekly Review, approval envelopes, safe refs, receipts, rollback awareness,
  and cross-system proposals.

"First-class" means a capability has a typed Python-core model, durable local
storage, migrations, API and CLI parity, a polished primary UI, search and
keyboard access, import/export, observable failure states, redacted evidence,
focused tests, and truthful product language. A renamed generic table or a
React-only mock does not qualify.

## Product Principles

### Relationship-first, workspace-specific

Global identity answers "who is this?" Workspace context answers "what is this
relationship here?" A single person may be a friend, buyer, investor, or
customer without sharing all context between those workspaces.

### Private by default

Personal Network and Dating data are excluded from professional briefings,
reports, exports, cross-workspace search, and model context by default. Dating
has the strongest default isolation and must be deliberately opted into any
cross-surface use.

### Facts, notes, memory, and inference are different

The UI and contracts must distinguish operator-entered facts, private notes,
source-backed observations, recalled memory, and generated or deterministic
suggestions. Memory is recall, not truth. Suggestions do not become CRM state
until reviewed and committed through an exact mutation path.

### People are not scores

Personal and Dating workspaces must not rank human worth, generate manipulative
compatibility scores, infer protected or sensitive traits, scrape private
information, or automate interpersonal communication. The system may help the
operator remember, reflect, prepare, and follow through.

### Useful local capability before external authority

Manual capture, local CRUD, local search, follow-ups, pipelines, import review,
and reporting should become excellent before live account sync or outbound
automation is promoted.

### Approval without needless friction

The editor may hold presentation-only drafts. A Save action commits one exact
reviewable change set, not a stream of hidden autosaves. Closely related local
edits may be grouped into a bounded change set with an exact approval scope,
idempotency key, receipt, and rollback record. No broad "CRM write" toggle may
authorize unrelated workspaces or mutations.

## Architecture

```text
Control Center CRM workspace
        |
        | typed local API; no UI-minted authority
        v
Python CRM application services
        |
        +---- PolicyEngine / LocalApprovalAuthority / AuthorityLease
        |
        +---- Private CRM data plane
        |       identities, contact points, workspace context, private notes,
        |       activities, pipeline objects, custom fields, saved views
        |
        +---- Governance and evidence plane
                safe refs, redacted summaries, proposals, approvals,
                receipts, provenance, rollback refs, blocked states
```

### Private CRM data plane

The current safe-ref-only snapshot is not sufficient for a usable personal
CRM. A new local repository layer must store the private product record while
keeping it out of durable evidence, logs, fixtures, reports, and verifier
output.

Required posture:

- SQLite-backed local repository with explicit schema migrations and
  transaction boundaries.
- Encryption-at-rest design reviewed before Personal Network or Dating stores
  sensitive notes. The implementation milestone must select and document the
  key lifecycle, recovery posture, lock behavior, and macOS-first storage
  protections; this plan does not select or add a dependency.
- Raw names, email addresses, phone numbers, physical addresses, notes, and
  private event details never enter evidence JSONL, logs, test fixtures,
  documentation, analytics, crash reports, or CLI output by default.
- Private-data API responses are allowed only on the local authenticated
  Control Center boundary, with route classification, workspace scope, field
  projection, and no-store behavior. Safe-ref inspection remains the CLI and
  evidence default.
- Backups and exports are explicit, encrypted where private content is
  included, user-selected, and never silently uploaded.
- Every mutation has a reversible event or an explicit compensation posture.
  Archive is preferred over destructive deletion; permanent deletion is a
  separately confirmed exact lane.

### Governance and evidence plane

The current M2 safe-ref model remains the durable audit representation. It
records the record ref, workspace ref, mutation kind, decision, timestamp,
idempotency ref, receipt ref, evidence refs, before/after state labels, and
rollback posture without copying private field values.

## Canonical Domain Model

| Domain | Core records | Ownership rule |
|---|---|---|
| Identity | `Person`, `Organization`, `ContactPoint`, `IdentityAlias`, `IdentityMatchCandidate` | Minimal private identity may be shared; merges are always reviewed. |
| Workspace | `Workspace`, `WorkspaceMembership`, `WorkspaceContext`, `PresetVersion`, `PrivacyPolicy` | Context and sensitive fields belong to exactly one workspace. |
| Relationship | `Relationship`, `Role`, `Circle`, `RelationshipState`, `ImportantDate`, `Commitment` | Language and lifecycle are defined by the active workspace preset. |
| Work | `FollowUp`, `Activity`, `Interaction`, `TaskLink`, `EventLink`, `TimelineEvent` | CRM owns relationship follow-up and activity context; canonical Tasks and Calendar Events remain owned by their suite apps and are linked rather than copied. |
| Pipeline | `Pipeline`, `PipelineStage`, `PipelineObject`, `StageTransition` | Generic pipeline mechanics with typed preset-specific objects. |
| Sales | `LeadContext`, `Opportunity`, `AccountContext`, `ForecastValue` | Sales-only; never shown in Personal or Dating terminology. |
| Real estate | `Property`, `PropertyRole`, `Showing`, `Offer`, `Transaction`, `ClosingMilestone` | Typed real-estate fields supplement, not replace, shared relationship records. |
| Personal | `PersonalCircle`, `SharedInterest`, `PersonalCommitment`, `Reflection` | Private by default and excluded from professional surfaces. |
| Dating | `ConnectionContext`, `DateEvent`, `Preference`, `BoundaryNote`, `Reflection` | Highest isolation; no scoring, covert enrichment, or automated outreach. |
| Configuration | `CustomFieldDefinition`, `CustomFieldValue`, `Tag`, `SavedView`, `FilterDefinition` | Versioned and workspace-scoped; no executable custom code. |
| Governance | `Proposal`, `ApprovalRecord`, `MutationReceipt`, `EvidenceRef`, `MemoryProvenance`, `RollbackRef` | Safe-ref-only durable representation. |

The existing `CrmPerson`, `CrmOrganization`, `CrmWorkspace`,
`CrmWorkspaceContext`, `CrmRelationship`, `CrmPipelineObject`, `CrmActivity`,
`CrmCommunicationItem`, `CrmProposal`, and M2 read models should be evolved by
additive versioned contracts. Do not overload `Opportunity` for properties,
friendships, or dating relationships.

## Initial Workspace Presets

### Personal Network

Primary views: People, Circles, Important Dates, Commitments, Recent Context,
and Keep in Touch.

Default relationship language: friend, family, community, acquaintance,
mentor, collaborator, and custom. The primary attention signal is a reviewed
follow-up or commitment, not a numeric relationship-health score.

### Private Relationships And Dating

Primary views: Connections, Upcoming Dates, Follow-ups, Reflections, and
Private Archive.

Default lifecycle language should be respectful and editable: new connection,
getting to know, planning a date, dating, paused, ended, and archived. These are
personal organization labels, not judgments about another person. Dating data
is excluded from global briefings, professional Today views, general exports,
and model context unless the operator enables an exact use.

### Sales

Primary views: Leads, People and Accounts, Follow-ups, Pipeline, Activities,
Forecast, and Insights.

Default pipeline: New, Qualified, Discovery, Proposal, Negotiation, Won, and
Lost. Pipelines, stages, probabilities, values, close dates, loss reasons, and
saved views are configurable per workspace.

### Real Estate

Primary views: Contacts, Active Clients, Properties, Showings, Offers,
Transactions, Follow-ups, and Closings.

Start with two configurable pipelines rather than one overloaded board:

- Relationship pipeline: New lead, Contacted, Nurturing, Active client,
  Past client, and Sphere.
- Transaction pipeline: Search or prepare, Showing or listed, Offer,
  Under contract, Closing, Closed, and Lost or paused.

Roles include buyer, seller, tenant, landlord, agent, lender, inspector,
attorney, title or escrow, contractor, and custom. One person may hold several
roles across different transactions.

### Professional Network

Primary views: People, Organizations, Circles, Introductions, Commitments,
Follow-ups, Opportunities to Help, and Relationship History.

Default roles include partner, investor, advisor, vendor, candidate,
collaborator, referral partner, press, community, and custom. Professional
Network does not force every relationship into a sales opportunity or revenue
forecast.

## Information Architecture

Keep CRM as one primary Control Center destination with an internal workspace
switcher and nested views:

| Route | Operator purpose |
|---|---|
| `/crm` | Attention-first home: due follow-ups, recent changes, pipeline movement, missing evidence, and quick capture. |
| `/crm/people` | Searchable people and organizations directory with saved views, filters, bulk review, and duplicate candidates. |
| `/crm/people/{ref}` | Relationship record with overview, workspace contexts, timeline, follow-ups, notes, pipeline links, provenance, and privacy controls. |
| `/crm/follow-ups` | Due, upcoming, stale, completed, blocked, and proposed follow-ups. |
| `/crm/pipelines` | Workspace pipeline/list switcher with stage definitions, filters, totals, and exact stage-move changes. |
| `/crm/activities` | Calls, meetings, dates, showings, tasks, reminders, and manually recorded interactions. |
| `/crm/insights` | Workspace-appropriate reporting; sales forecast is never shown as a personal relationship metric. |
| `/crm/import` | File selection, mapping, validation, duplicate review, commit preview, batch receipt, and rollback readiness. |
| `/crm/settings` | Workspaces, presets, fields, stages, privacy, export, retention, and authority posture. |

The current all-in-one `CrmM1FixtureShellPanel` should become a composed CRM
shell. Authority and connector diagnostics remain accessible, but they should
move out of the primary relationship workflow into a compact status drawer or
CRM Settings so the default screen prioritizes the operator's work.

## North-Star Render Revision Pack

The existing Source Inbox / CRM / Briefing render remains useful for the
cross-system loop, but it is not sufficient evidence for a first-class CRM.
Before broad frontend implementation, produce and accept desktop plus narrow
layouts for:

1. CRM Home in Sales with attention queue and quick capture.
2. People directory with workspace switcher, saved views, filters, and search.
3. Person detail showing shared identity and strictly separated workspace
   contexts.
4. Sales pipeline board and list view.
5. Real Estate relationship and transaction workspace.
6. Personal Network keep-in-touch view.
7. Private Relationships workspace with Dating isolation and respectful language.
8. Import mapping and duplicate-review flow.
9. Exact change-set approval and rollback receipt.
10. Empty, first-run, loading, error, locked, blocked, partial, and success
    states for the primary views.

Render acceptance requires legible primary actions, keyboard and screen-reader
intent, realistic density, no raw JSON as primary UX, no fake controls, clear
workspace and privacy state, and product-language review against current repo
authority.

## Implementation Sequence

Each milestone should be one focused branch or tightly related PR series. A
milestone is not complete until its Python contract, storage behavior, API,
CLI, UI where applicable, tests, documentation, and safe-disable or rollback
posture agree.

### `CRM-FC-000` Product contract and render acceptance

Deliver:

- Add Personal Network, Private Relationships/Dating, Sales, Real Estate, and
  Professional Network to a versioned workspace/preset contract.
- Ratify suite ownership so CRM links canonical Events and Tasks and uses the
  shared Boards engine; do not create duplicate CRM-owned event, task, or
  Kanban truth.
- Freeze the v1 domain nouns, workspace isolation rules, private-data versus
  evidence-plane boundary, and route map.
- Produce the render revision pack and record accepted variants.
- Write an ADR for private CRM storage, encryption, keys, backup, recovery,
  and local API exposure.

Gate: no private-data persistence or new mutation routes until the ADR and
threat model are accepted. This is the immediate next milestone.

### `CRM-FC-001` Private local repository and migrations

Deliver:

- Add the SQLite repository interface, schema v1, migration runner,
  transaction tests, lock/unlock posture, backup/restore contract, and
  corruption-safe startup behavior.
- Keep existing M2 snapshot support as a compatibility/read-only migration
  source until cutover proof is accepted.
- Add workspace isolation and field-level sensitivity metadata.
- Add safe-ref event projection without private-value logging.

Gate: migration round trips, crash consistency, workspace isolation, redaction,
backup/restore, and key lifecycle tests pass. Dating storage remains unavailable
until the selected encryption posture is implemented and verified.

### `CRM-FC-002` Exact local CRUD and rollback

Deliver:

- Create, edit, archive, restore, and exact-delete lanes for people,
  organizations, workspace contexts, follow-ups, notes, activities, and
  pipeline objects.
- Add bounded change-set drafts, diff previews, exact approval requests,
  idempotency, receipts, optimistic concurrency, and compensating rollback.
- Extend `scripts/dev/uaa_crm.py` with safe inspection and exact mutation
  commands. Private values require an explicit local-private display flag and
  must never be emitted in CI or durable reports.

Gate: every mutation has Python/API/CLI parity, route side-effect
classification, approval-scope tests, replay/conflict tests, receipt tests, and
rollback or explicit non-reversible posture.

### `CRM-FC-003` First-class shell, People, and relationship record

Deliver:

- Replace the M2 cockpit layout with the accepted CRM shell and nested views.
- Implement workspace switcher, CRM Home, People directory, quick capture,
  person/organization detail, workspace-context tabs, privacy badges, timeline,
  empty states, and keyboard navigation.
- Preserve backend-owned truth; React state remains drafts, selection, filters,
  expansion, and layout preferences only.

Gate: browser tests prove every visible control, responsive layouts, focus
order, accessible names, loading/empty/error/locked states, and no
cross-workspace leakage.

### `CRM-FC-004` Activities, commitments, and follow-up loop

Deliver:

- Implement due/upcoming/stale/completed/blocked follow-up views, recurring
  local reminders, important dates, commitments, activity history, and manual
  interaction logging.
- Feed reviewed CRM follow-ups into Today, Action Inbox, Morning Briefing, and
  Weekly Review using safe refs and workspace privacy policy.
- Support snooze, reschedule, complete, reopen, and undo as exact local lanes.

Gate: a contact can be captured, given a follow-up, surfaced on Today,
completed through an approved change set, and shown in Evidence without private
content entering the evidence record.

### `CRM-FC-005` Pipelines for Sales and Real Estate

Deliver:

- Implement configurable pipelines, stages, stage order, probability, status,
  values, expected dates, roles, loss or pause reasons, board/list views, and
  stage histories.
- Implement typed Sales Opportunity, Property, Showing, Offer, Transaction,
  and Closing Milestone records.
- Support drag as a presentation gesture that opens an exact persisted-change
  preview; a drag alone does not mint authority.

Gate: sales and real-estate golden paths work through Python/API/CLI/UI,
including undo and history, without using sales language in personal
workspaces.

### `CRM-FC-006` Professional, Personal, and Private Relationship workspaces

Deliver:

- Implement Personal Network circles, important dates, commitments,
  keep-in-touch views, reflections, and private archive.
- Implement Professional Network roles, circles, introductions, commitments,
  opportunities to help, and non-sales follow-up views.
- Implement Dating lifecycle, date events, preferences, boundary notes,
  reflections, follow-ups, archive, and private export/delete controls.
- Add explicit cross-workspace linking and sharing review. Default to no Dating
  results in global search, Today, Briefing, Memory context, or professional
  reports.

Gate: privacy tests prove default exclusion, no protected-trait inference, no
compatibility scoring, no automated outreach, and no personal-context leakage
into professional views or evidence.

### `CRM-FC-007` Search, customization, import/export, and identity hygiene

Deliver:

- Add fast local full-text search with workspace and privacy filters.
- Add typed custom fields, tags, saved views, advanced filters, column
  selection, sorting, and controlled preset versioning.
- Implement CSV import mapping, validation, duplicate candidates, merge
  preview, exact batch commit, import receipt, and batch rollback.
- Implement private encrypted export and redacted support export as separate
  lanes.

Gate: no silent merge, no silent contact creation, no hidden field loss,
deterministic import preview, reversible batch commit, and measured search/UI
performance against representative local datasets.

### `CRM-FC-008` Insights and review

Deliver:

- Sales: pipeline totals, conversion, activity, aging, forecast, won,
  lost, and follow-up reporting.
- Real Estate: lead source, active clients, showing/offer/transaction movement,
  closing milestones, and relationship follow-up reporting.
- Personal Network and Dating: descriptive workload and history views only;
  avoid reductive relationship scoring.
- Feed safe movement summaries into Weekly Review.

Gate: every chart is traceable to records, respects workspace isolation and
visibility, has an accessible table form, and distinguishes missing or stale
data from zero.

### `CRM-FC-009` Exact read-only connector lanes

Deliver only after separate authority acceptance:

- Promote one connector/source at a time, beginning with read-only contact,
  email metadata, or calendar metadata through approved connector boundaries.
- Add account selection, field projection, consent, sync status, conflict
  review, source provenance, safe-disable, refresh receipts, and disconnect.
- Treat raw message or calendar bodies as a separate authority decision from
  metadata reads.

Gate: connector-specific policy, approval, redaction, revocation, rate-limit,
failure, and no-write tests pass. There is no broad account-sync flag.

### `CRM-FC-010` Draft, send, and calendar-write lanes

Remain blocked until each exact capability is separately graduated. Draft
creation, email send, message send, calendar create/update/cancel, and external
CRM writeback are different capabilities with different previews, approvals,
idempotency, receipts, safe-disable, compensation, and tests. No workspace or
connector receives standing outbound authority.

### `CRM-FC-011` Governed AI assistance

Deterministic proposals may improve before runtime model authority. Later
accepted provider/model lanes may add summary drafts, follow-up suggestions,
meeting preparation, duplicate explanations, and next-action proposals only
with explicit source citations, uncertainty, workspace scope, private-context
policy, cost posture, and review. Model output remains proposal material, not
CRM truth or execution authority.

## API And CLI Contract Direction

Read routes should be resource-oriented and field-projected rather than
returning one increasingly large summary payload. Proposed route families are
planning targets, not implemented routes:

```text
GET  /control-center/crm/workspaces
GET  /control-center/crm/people
GET  /control-center/crm/people/{ref}
GET  /control-center/crm/follow-ups
GET  /control-center/crm/pipelines
GET  /control-center/crm/pipelines/{ref}
GET  /control-center/crm/activities
GET  /control-center/crm/insights
POST /control-center/crm/change-sets/preview
POST /control-center/crm/change-sets/commit
POST /control-center/crm/change-sets/{ref}/rollback
POST /control-center/crm/imports/preview
POST /control-center/crm/imports/{ref}/commit
```

Every route change must preserve stable unique operation IDs, update OpenAPI,
API manifest tests, route side-effect documentation, release-surface truth,
CLI inspection or mutation parity, redaction tests, and Foundation Gate checks.

## Verification Strategy

Every implementation milestone runs its focused tests plus the relevant
baseline checks:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_communications_spine_contracts.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_local_command_center.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_local_command_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_crm_local_command_center.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
git diff --check
```

Add milestone-specific coverage for repository migrations, encryption/key
lifecycle, backup/restore, workspace isolation, private API projection,
optimistic concurrency, change-set approval, idempotency, rollback, import
mapping, duplicate review, search performance, accessibility, responsive UI,
browser interaction, and visual regression.

Tests, fixtures, screenshots, and reports must use synthetic data and safe
refs. They must not contain actual operator contacts, notes, addresses,
messages, dates, usernames, hostnames, or local paths.

## Product Quality Gates

Before calling the CRM first-class, prove all of the following with synthetic
or private local trial evidence:

- A new operator can create a workspace and first person without reading
  documentation.
- Quick capture, search, person detail, follow-up completion, and stage movement
  are fast and keyboard accessible.
- Empty, loading, error, locked, offline, migration-required, conflict, blocked,
  partial, and success states are understandable.
- Imports are previewable, duplicate-aware, bounded, and reversible.
- Private workspaces never appear in disallowed surfaces or exports.
- Every persistent UI action maps to Python Core, API, CLI inspection, and a
  receipt or read contract.
- Mobile-width workflows cover capture, search, follow-up, person detail, and
  pipeline inspection; native mobile apps are not claimed.
- The first-use experience provides useful presets without locking the operator
  into one vocabulary or schema.
- Performance budgets are set from measured representative datasets during
  `CRM-FC-007`; no unsupported speed claim is made before evidence exists.

## Prioritized Delivery

### Now

1. `CRM-FC-000` contract, privacy architecture, and render acceptance.
2. `CRM-FC-001` private repository and migrations.
3. `CRM-FC-002` exact local CRUD, receipts, and rollback.
4. `CRM-FC-003` CRM Home, People, and relationship record.
5. `CRM-FC-004` follow-up loop integrated with Today and Evidence.

This creates the first genuinely useful local relationship CRM loop.

### Next

6. `CRM-FC-005` Sales and Real Estate pipelines.
7. `CRM-FC-006` Professional, Personal, and Private Relationship workspaces.
8. `CRM-FC-007` search, customization, import/export, and identity hygiene.
9. `CRM-FC-008` insights and Weekly Review integration.

### Later and separately gated

10. `CRM-FC-009` exact read-only connector lanes.
11. `CRM-FC-010` exact draft/send/calendar-write lanes.
12. `CRM-FC-011` governed model-assisted proposals.

## Definition Of Done

The first-class CRM program is complete only when the five initial workspaces
are usable through durable local records; the primary capture, find, review,
follow-up, pipeline, import/export, and reporting loops are polished; private
workspace isolation is proven; mutations are exact-scoped, approval-bound,
idempotent, auditable, and rollback-aware; Python/API/CLI/UI contracts agree;
focused and foundation checks pass; current product truth is updated; and all
external connector, send, calendar-write, provider/model, browser, background,
public-release, and production-authority states remain accurately represented.
