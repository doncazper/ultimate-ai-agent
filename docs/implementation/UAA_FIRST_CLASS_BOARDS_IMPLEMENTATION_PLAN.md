# UAA First-Class Local Boards Implementation Plan

Status: proposed implementation plan; planning-only authority; acceptance pending
Baseline: v0.104.0 / 0.104.0
Date: 2026-07-13
Program milestone: `ECO-003` Reusable Boards V1
Subordinate to:
`docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`
Accepted ownership contracts:
`docs/decisions/ADR-0054-canonical-application-object-ownership.md`,
`docs/decisions/ADR-0055-entity-links-and-projections.md`, and
`docs/decisions/ADR-0057-existing-store-migration-and-compatibility.md`

## Decision Summary

UAA Boards will become a first-class local visual-work product: simple enough
to use like a focused Kanban tool, complete enough for everyday Trello-style
workflows, and structurally better suited to UAA than either benchmark.

The product target is:

```text
kan.bn-grade focus and interaction clarity
+ Trello-class local board fundamentals
+ UAA canonical projections, governance, privacy, recovery, and integration
```

This is feature parity for the useful single-operator local workflow, not
literal parity with cloud collaboration platforms. The first-class target
includes multiple boards, rich cards, templates, archive/restore, fast capture,
deep links, filters, search, keyboard workflows, deterministic drag/reorder,
history and undo, import/export, backup/restore, responsive layouts, and tested
failure recovery. It excludes hosted workspaces, invitations, presence,
real-time multi-user editing, cloud file storage, public sharing, billing,
webhooks, marketplace power-ups, OAuth import, email notifications, and
connector runtime from the local V1.

UAA must not ship a generic board clone. Its durable advantage is that one
board can hold standalone visual-work items and projections of canonical
Tasks, Plan steps, CRM Opportunities, Real Estate Transactions, Closing
Milestones, and governed Playbook steps without copying their truth. Board
changes remain exact-scoped, approval-bound, idempotent, auditable,
rollback-aware, redacted, and available through the same Python core/API/CLI
contracts as the Control Center.

This document refines `ECO-003`; it does not create a competing roadmap. It
does not itself add routes, storage, dependencies, runtime behavior, model or
provider calls, web access, browser automation, connectors, collaboration,
public distribution, or production authority.

## What First-Class Means

A UAA app is first-class only when it has all of the following:

- a typed Python-core domain and application-service boundary;
- durable local storage, versioned migrations, backup, restore, and recovery;
- complete local CRUD for its canonical records;
- stable local API contracts and redacted human-readable CLI parity;
- a polished primary UI with deep links, keyboard access, narrow layouts, and
  complete loading, empty, locked, conflict, error, success, and undo states;
- deterministic search, filtering, saved views, archive, import, and export;
- explicit canonical ownership for every visible mutable field;
- exact approval, idempotency, optimistic concurrency, receipts, and undo or
  compensation posture for every mutation;
- protected private content separated from content-free evidence and logs;
- focused unit, integration, browser, accessibility, performance, migration,
  corruption, crash, low-disk, replay, and recovery verification; and
- truthful labels for implemented, partial, planned, blocked, and missing
  behavior.

A visually convincing React board, a fixed delivery board, raw JSON as the
primary inspector, or drag state that has not been durably committed does not
meet this bar.

## Current Baseline And Material Gaps

The existing `/work-board` is a valuable governed prototype, not the target
Boards product. It already proves a backend-owned read model, fixed lanes,
safe-ref cards, board/list/proof views, filters, drag preview, durable ordering,
approval preview, idempotency, receipts, and rollback or safe-disable posture.
Those contracts should be migrated, not discarded.

The present gap is larger than visual polish:

| Area | Current truth | First-class requirement |
|---|---|---|
| Scope | One Founder Loop Work Board | Multiple user-created boards, templates, favorites, archive, and recent boards |
| Card model | Title, safe summary, priority, authority, owner, tags, and refs | Private description/notes, labels, due posture, checklist, attachment refs, custom fields, provenance, and typed subject ownership |
| Mutation loop | Core/API require exact approval metadata; the current Control Center create/reorder calls do not complete the approval-preview handshake | One coherent preview, confirm, commit, receipt, conflict, and undo interaction across UI/API/CLI |
| Editing | Create/reorder/task-record lanes only | Create, inspect, edit, duplicate, move, archive, restore, exact delete, batch edit, and history |
| Navigation | `/work-board` fixed surface | `/boards`, board deep links, card deep links, compatibility redirect/reader, and restorable filters/scroll |
| Views | Board, list, proof | Board, list, table, saved views, inspector/detail, then applicable timeline/calendar-linked views |
| Storage | Current Work Board safe-ref JSON/read contracts | Shared SQLite application-data platform with protected content, migrations, versions, backup, restore, and integrity checks |
| Ordering | Proven local ordering contract for one board | Per-board/lane versioned ordering, transactional rebalance, stale-write conflicts, crash consistency, and dense-board proof |
| Portability | No complete end-user import/export loop | Offline file preview, deterministic mapping, exact commit, source fingerprint, warnings, rollback, private export, and restore |
| Product hierarchy | Proof/governance competes with primary work | Cards and lanes dominate; status, receipts, proof, and authority remain one action away in an inspector/history surface |

The first implementation milestone must close the existing frontend/backend
approval-handshake gap before describing card creation or drag as a complete
end-user mutation loop.

Repository evidence for this baseline is concentrated in
`src/ultimate_ai_agent/core/control_center/work_board.py` (requests, read model,
approval previews, validation, receipts, and store),
`src/ultimate_ai_agent/api/control_center.py` (read and mutation routes), and
`apps/control-center/src/components/WorkBoardPanel.tsx` (current draft, create,
reorder, and proof interaction). The component submits create/reorder payloads
without the approval/scope/envelope refs that the core models and routes
validate, so its success copy must not be treated as end-to-end evidence.

## Reference Review And Clean-Room Boundary

### Primary reference inspected

The plan was reviewed against the public source and product structure of
[`kanbn/kan`](https://github.com/kanbn/kan) at commit
`9ec4bedd9ad004faad6054cdeec9491b07585a85` dated 2026-07-08. The inspected
areas included board/list/card schemas, checklists, labels, imports, activity
types, board and card-detail views, filters, context actions, templates,
optimistic drag behavior, skeletons, empty states, responsive renders, and
keyboard/command surfaces.

The repository declares GNU AGPL v3. This plan uses public behavior and
high-level product/architecture observations as research only. UAA must not
copy kan source, schemas, components, CSS, icons, assets, text, or visual
composition wholesale, and must not add kan as a dependency. Any later PR that
adapts source rather than independently implementing a product concept requires
an explicit dependency/license decision outside this plan. This is an
engineering provenance boundary, not legal advice.

The primary inspection ledger is:

- `packages/db/src/schema/boards.ts`, `lists.ts`, `cards.ts`, `checklists.ts`,
  `labels.ts`, and `imports.ts` for domain structure;
- `apps/web/src/views/board/index.tsx` and its `List`, `Card`, `Filters`,
  `NewCardForm`, and `CardContextMenu` components for board interaction; and
- `apps/web/src/views/card/index.tsx` and its checklist, attachment, due-date,
  label, activity, and comment components for card-detail structure.

### Concepts worth carrying forward

- Clear `Board -> Lane -> Card` hierarchy with cards as the dominant surface.
- A compact board header, contained horizontal/vertical scrolling, and low
  visual noise.
- Inline board, lane, and card creation with purposeful empty states.
- Deep-linked card detail with editable content and visible related metadata.
- Context actions for move, duplicate, labels, due posture, copy link, archive,
  and delete.
- URL-backed filters and restorable board/scroll state.
- Optimistic drag feedback with rollback and canonical revalidation.
- Templates, archive, favorites, import provenance, skeletons, and narrow
  layouts.
- Normalized records with stable public references and soft deletion.

### Concepts UAA should deliberately improve

- Add explicit record versions, expected-version preconditions, board
  revisions, idempotency, deterministic conflict UX, and transaction-safe
  order compaction rather than relying on implicit integer positions.
- Keep raw titles, descriptions, notes, comments, imported values, paths, and
  before/after content out of durable evidence, logs, reports, fixtures, and
  support exports. Activity evidence uses refs and state labels only.
- Store attachments in a governed local content store; do not require S3 or
  fetch remote attachment URLs during import.
- Import Trello data from a user-selected local export file with preview and
  rollback; do not add OAuth or live network import in V1.
- Treat canonical Tasks, Plans, and CRM records as projections rather than
  copied card state.
- Add WIP policy, swimlanes, typed custom fields, saved views, ChangeSet
  previews, receipts, why-shown/provenance, and Action Inbox proposals.
- Keep cloud membership, billing, webhooks, integrations, notifications, and
  live multi-user collaboration out of the single-operator local milestone.

Trello is a capability benchmark for familiar board fundamentals. It is not a
source-code or pixel-copy reference, and cloud-only behavior is explicitly out
of the local parity definition.

## Product Principles

### Work first, trust available

The normal board should feel like a work surface, not an audit console. Board
name, view, filter, search, add-card, and lane controls occupy the primary
chrome. Receipts, source refs, versions, authority state, conflicts, and
rollback posture remain inspectable from card detail, history, or a secondary
trust inspector.

### Useful with every external capability disabled

Board creation, card work, search, import from local files, export, backup,
restore, and projection inspection must work without network access, provider
calls, connectors, a model, browser automation, cloud storage, or another UAA
app.

### One mutable field, one canonical owner

Boards owns board configuration, membership, lane/swimlane placement, ordering,
board-local display metadata, and standalone `BoardItem` records. Tasks owns
Task lifecycle and Task fields. Plans owns Plan-step lifecycle. CRM owns
Opportunity and Transaction lifecycle. A projection shows canonical values and
routes edits to the owning service; it never forks mutable truth.

### Manual actions are exact without being needlessly repetitive

The operator's Save, Drop, Archive, Restore, or Confirm action is the visible
intent boundary, but the Control Center cannot mint authority. The Python core
must prepare and validate the exact scope, bind it through
`LocalApprovalAuthority` and any required `AuthorityLease`, apply idempotently,
and return a receipt. Simple local board-only moves may use an already prepared
exact preview so Drop confirms the mutation. Cross-domain or higher-consequence
moves always show a diff/ChangeSet confirmation.

### Fast feedback is not fabricated success

Optimistic UI may render a pending ghost or tentative position. It becomes
canonical only after the backend receipt. Denial, conflict, timeout, or write
failure restores the prior render and explains the next safe action.

### Archive first, exact delete last

Boards, lanes, cards, checklists, and attachments use archive/restore where
possible. Permanent deletion is a separately confirmed exact operation with
link handling, attachment-reference handling, and an explicit irreversible or
compensation posture.

### Every visible control is real

Buttons perform immediate actions, links navigate, selectors choose state,
toggles change settings, and status chips report state. Planned or blocked
actions are labeled and cannot masquerade as enabled controls.

## Primary Operator Loops

### Standalone board loop

```text
Boards home
-> create from blank or local template
-> name lanes
-> quick-capture cards
-> enrich one card
-> move or reorder
-> filter/focus
-> archive/restore
-> inspect receipt or undo
```

### Projection loop

```text
Open task/plan/CRM board
-> inspect canonical projection
-> move to an unmapped lane: commit board placement only
-> move to a mapped lane: preview owning-domain transition
-> confirm exact ChangeSet
-> receive per-operation receipts
-> refresh from canonical owner
```

### Agent-proposed loop

```text
Agent or source proposes board/card change
-> Action Inbox envelope
-> inspect reason, sources, scope, diff, risk, and rollback posture
-> approve/edit/reject/defer
-> exact backend commit if approved
-> board refresh plus receipt/history
```

Agent proposals never silently rearrange a board, create cards, or transition a
canonical subject.

### Offline import loop

```text
Choose local export file
-> parse as untrusted input
-> preview board/list/card/label/checklist mapping
-> review omissions, duplicates, attachment posture, and counts
-> commit exact import transaction
-> verify fingerprint and counts
-> retain rollback/archive posture
```

## Information Architecture

Planned route intent, subject to the route-contract milestone:

| Route | Purpose |
|---|---|
| `/boards` | Recent, favorite, template, and archived boards; local import and new-board entry |
| `/boards/:board_ref` | Default board view with URL-backed filters and restorable scroll/focus |
| `/boards/:board_ref/list` | Accessible list view and bulk work |
| `/boards/:board_ref/table` | Configurable fields, sorting, grouping, and bulk selection |
| `/boards/:board_ref/cards/:card_ref` | Deep-linked card detail that remains usable on narrow layouts |
| `/boards/:board_ref/settings` | Lanes, mapped transitions, WIP policy, fields, templates, export, and archive |
| `/work-board` | Versioned compatibility route/redirect until migration and cutover evidence is accepted |

The primary desktop board uses the common app rail, a compact board header,
fixed-width readable lanes, independently scrolling lane bodies, and a
deep-linked detail surface or optional inspector. The board must preserve
filter, focus, and scroll state on card-detail return. Narrow mode uses a lane
selector or one-lane-at-a-time flow; it must not squeeze desktop columns into
unreadable cards.

The default card shows only decision-useful metadata: title, labels, due
posture, checklist progress, assignee/relationship projection when applicable,
blocker/progress indicators, and an explicit pending/conflict state. Priority,
authority, proof, and provenance appear when relevant rather than on every card
by default.

## Canonical Domain And Ownership

The accepted ECO-000 records remain the foundation:

| Record | Board-owned responsibility |
|---|---|
| `Board` | Name, description ref, type, archive state, revisions, settings, and stable public ref |
| `BoardView` | View kind, field layout, filters, grouping, sort, density, and visibility preferences |
| `Lane` | Board-scoped label, order, WIP policy, archive state, and optional mapped transition ref |
| `Swimlane` | Optional grouping definition, order, collapse state, and WIP policy |
| `BoardMembership` | Link between a board and one canonical subject, plus lane/swimlane placement and board-local presentation metadata |
| `CardProjection` | Computed read model with subject ref, owner kind, field provenance, privacy posture, and freshness; no copied mutable truth |
| `CardOrdering` | Opaque sortable order key, lane/board revision, expected version, and compaction posture |
| `BoardTemplate` | Versioned board/view/lane/field configuration with provenance and no live source coupling |
| `BoardItem` | Boards-owned canonical subject for general visual work that is not a Task, Plan step, CRM object, or other domain record |

The schema milestone should ratify additive board-owned records or value
objects for:

- private `BoardItemContent` with description and local notes;
- `BoardLabel` and board-local label membership;
- `BoardChecklist` and ordered `BoardChecklistItem` for standalone items;
- typed `BoardFieldDefinition` and `BoardFieldValue` with no executable custom
  code;
- local `AttachmentRef` metadata and content-store ownership;
- `BoardImport`, source fingerprint, mapping decision, warning, and rollback
  refs;
- content-free `BoardEvent`, `BoardMutationReceipt`, and `BoardUndoRecord`;
- mapped lane-transition policy and canonical owner command refs; and
- favorite/recent state as local presentation preference, not product truth.

For a standalone `BoardItem`, Boards owns title, private description/notes,
board checklist, dates, and status. For a Task projection, Tasks owns title,
notes, checklist, dates, completion, recurrence, and dependencies. For a CRM
projection, CRM owns opportunity/transaction fields and lifecycle. The card
detail must label the owner and route edits to that owner instead of offering a
board-local shadow field.

### Private content and evidence separation

Private titles, descriptions, notes, checklists, custom-field values, imported
content, attachment names, and local paths belong to the protected application
data plane. Durable evidence records only safe refs, operation kind, state
labels, decision, timestamps, versions, counts, fingerprints, idempotency ref,
receipt ref, source refs, and rollback posture.

Undo may require protected before-state deltas. Those deltas remain encrypted
or equivalently protected with the product data, are retention-bounded, and do
not enter evidence JSONL, logs, docs, fixtures, support exports, or default CLI
output.

## Local Parity And Differentiation Contract

`Core V1` is required before UAA calls Boards first-class. `Advanced` deepens
the product after the core gate. `Excluded V1` is intentionally outside local
parity and requires a separate accepted milestone.

| Capability | Target | Acceptance note |
|---|---|---|
| Multiple boards; recent/favorite/archive | Core V1 | Create, rename, duplicate, archive, restore, and deep-link locally |
| Blank and versioned templates | Core V1 | Create board from template and save a board configuration as a private template |
| Lane CRUD and reorder | Core V1 | Create, rename, reorder, archive, restore, WIP posture, version conflict, and undo |
| Rich card CRUD | Core V1 | Create, inspect, edit, duplicate, move, archive, restore, exact delete, and history |
| Stable card refs and copy link | Core V1 | Human-readable short identifier plus stable deep link without exposing storage IDs |
| Descriptions and local notes | Core V1 | Protected content; notes are single-operator notes, not fake collaboration comments |
| Labels and board fields | Core V1 | Typed, filterable, accessible, and board-scoped; projected fields show canonical ownership |
| Due posture and checklist | Core V1 | Board-owned for standalone items; canonical-owner projection otherwise |
| Local attachments | Core V1 | Add/remove local refs with size, integrity, missing-file, backup, and delete posture |
| Drag/reorder and keyboard alternative | Core V1 | Optimistic pending state, exact commit, stale-write conflict, rollback, live announcement |
| Search/filter/sort/saved views | Core V1 | URL/restoration state, protected local index, deterministic bounded results |
| Quick switcher and shortcuts | Core V1 | Open board/card, capture card, focus search, change view, and move card without pointer use |
| Context actions and bulk selection | Core V1 | Move, label, archive, restore, and safe applicable bulk edits with exact preview |
| Deep-linked card detail | Core V1 | Editable, keyboard complete, owner/provenance visible, narrow-layout usable |
| Activity, receipts, and undo | Core V1 | Human-readable private history plus content-free evidence; no raw JSON-first UX |
| Import/export/backup/restore | Core V1 | Local files, preview, exact commit, fingerprint, warnings, rollback, and recovery proof |
| Task projection board | Core V1 | Depends on `ECO-002`; no copied Task truth |
| WIP limits | Core V1 | Warning and optional exact enforcement; lane policy is explicit and testable |
| Swimlanes and advanced grouping | Advanced | Keyboard and narrow-layout behavior must be complete before release |
| Table view | Core V1 | Required for accessible bulk inspection and field configuration |
| Timeline/calendar-linked views | Advanced | Only for fields whose canonical owner supports dates; no duplicate event truth |
| Board analytics | Advanced | Deterministic local metrics with definitions and privacy-safe output |
| Plan/CRM/real-estate projections | Advanced | Follow canonical owner readiness and exact ChangeSet contracts |
| Multi-user presence/collaboration | Excluded V1 | No workspace invitations, roles, live cursors, comments, or shared authority |
| Public links and hosted boards | Excluded V1 | No cloud hosting or public distribution implied |
| Webhooks, integrations, power-ups | Excluded V1 | No connector or plugin runtime authority |
| OAuth/live Trello import | Excluded V1 | Use a user-selected local Trello export file only |
| Cloud attachment storage | Excluded V1 | Use governed local storage and explicit export/backup |

## Card Detail Design

The card detail is a durable route, not a transient modal-only form. Desktop may
offer an inspector for quick review, but Refresh, Back, Copy Link, and narrow
layouts must resolve to the same deep-linked card.

Recommended structure:

1. Header: title, owner type, board/lane, archive/conflict/pending state, and
   primary actions.
2. Overview: private description, labels, dates, typed fields, subject links,
   blocker/progress posture, and provenance.
3. Checklist: ordered items, completion, keyboard reorder, and canonical owner
   label.
4. Attachments: local metadata, missing-file state, reveal/export controls, and
   explicit remove/delete distinction.
5. Related work: Task, Plan, CRM, Today, Evidence, or source refs with privacy
   filtering.
6. History: readable operation labels, actor posture, timestamp, status,
   receipt, undo availability, and conflict/partial outcome.

The default surface does not expose raw receipt JSON, raw local paths, approval
tokens, raw import values, or private before/after text.

## Mutation And Approval Interaction Model

Every mutation follows one backend-owned state machine:

```text
idle
-> local draft or drag preview
-> backend exact-scope preview
-> operator confirm boundary
-> policy + approval + lease + version validation
-> pending optimistic render
-> atomic commit
-> receipt + canonical refresh
-> bounded undo or explicit compensation posture
```

Failure branches are first-class:

```text
denied/blocked -> prior state + reason + unblock posture
stale conflict -> latest state + diff + reapply/cancel choice
duplicate replay -> original receipt + no duplicate mutation
write failure -> prior state + retry posture
partial cross-domain ChangeSet -> per-operation outcome + recovery action
```

### Low-friction board-only changes

For a simple reorder or lane move with no mapped domain transition, the client
may request an exact preview during drag. If the preview remains current, Drop
is the explicit confirmation and the backend validates the prepared scope. The
card renders as pending until a receipt arrives. If the preview is unavailable
or stale, Drop opens a compact review instead of claiming success.

### Cross-domain moves

A lane may optionally map to a typed canonical transition such as Task status
or CRM pipeline stage. Crossing that boundary creates a ChangeSet preview with
the old/new field, owning app, side-effect class, approval requirements,
expected versions, rollback posture, and WIP outcome. The move becomes
canonical only after exact confirmation and per-operation receipts.

Lane mappings are configuration records, not broad authority. Mapping one lane
to one Task transition does not authorize other Task edits, CRM transitions,
connector writes, or future agent actions.

### Undo

Board-only ordering and metadata changes should provide bounded exact inverse
operations. Cross-domain undo is an independently validated compensation or
inverse command; the UI must not promise rollback when the canonical owner
reports an irreversible or partially applied outcome.

## Ordering, Concurrency, And Integrity

- Use an opaque sortable order key with insertion space; do not make the UI or
  public API depend on contiguous integer indexes.
- Rebalance/compact a lane transactionally, preserve relative order, increment
  the affected revision, and test interruption at every write boundary.
- Mutations include stable board/card refs, source lane, destination lane,
  neighboring refs or target position, expected board/lane/card versions,
  idempotency ref, exact scope, and action envelope.
- Stale writes fail with a typed conflict; they never silently last-write-win.
- Duplicate requests return the original compatible receipt and do not create
  a second card, movement, history row, or attachment ref.
- Startup verifies schema version, referential integrity, order-key validity,
  orphan posture, pending migrations, and recovery state before writes open.
- Low disk, locked store, corrupt attachment, unavailable key, interrupted
  migration, and read-only recovery mode have human-readable UI/CLI states.

## Local Storage, Search, And Attachments

`ECO-001` must establish the shared SQLite application-data platform before
Boards cutover. The Boards repository uses explicit transactions, versioned
migrations, a unit-of-work boundary, private/safe-ref separation, backup and
restore, integrity checks, and a reviewed encryption/key posture. This plan
does not select a new dependency.

Search indexes private content only inside the protected local boundary. The
default CLI and support export return safe refs and redacted summaries, not raw
card content. Index rebuild, locked state, stale index, deletion, workspace
privacy, and restore behavior require tests.

Attachments use content-addressed or equivalently integrity-checked local
storage behind an application service. Requirements include file-size and type
limits, filename/path redaction, duplicate-content handling, missing/corrupt
state, backup inclusion, export behavior, archive retention, reference counts,
and exact delete posture. Opening or revealing a local attachment is a distinct
operator action. No remote URL is fetched during add, import, render, or
restore.

## Offline Import, Export, And Migration

### Supported first-class import lanes

- UAA private Boards export/restore format.
- Trello JSON exported by the operator and selected from local disk.
- A documented generic CSV/JSON card import for simple boards.
- Current UAA Work Board compatibility migration under ADR-0057.

A kan.bn-specific importer should be added only after its public export format
is documented and fixtures can be independently specified. Source-code shape
alone is not an import contract.

### Import safety and UX

Treat every file as untrusted data. Enforce bounded size/depth/counts, strict
format parsing, safe filenames, no executable content, no path traversal, no
network dereference, and deterministic rejection. Preview shows:

- source kind, fingerprint, detected version, and parse posture;
- board, lane, card, label, checklist, attachment, and archived counts;
- destination and field mappings;
- unsupported fields and explicit omissions;
- duplicate/ref conflicts and deterministic resolutions;
- remote attachment URLs that will not be fetched;
- privacy/export warning and estimated local storage impact; and
- exact commit, idempotency, backup, rollback, and post-import verification
  posture.

Import commits atomically when possible. Large imports may use a staged
transaction protocol, but partial visibility is prohibited until finalization.
No source store or input file is deleted automatically.

### Export and backup

Private export is explicit, user-selected, versioned, and complete enough for
round-trip validation. Redacted support export is a separate safe-ref artifact.
Backup/restore follows the accepted ECO-000 quality gate and includes attachment
integrity, migration version, counts, and recovery instructions without
silently uploading data.

## UAA Integration Contract

| Surface | Integration rule |
|---|---|
| Tasks | Task cards are projections; board placement is Boards-owned, Task lifecycle is Tasks-owned |
| Plans | Plan steps project with owner/freshness refs; lane transition uses a Plan ChangeSet if mapped |
| CRM | Opportunities and transactions use the shared Boards engine; CRM must not ship a second Kanban store |
| Today | May show due/blocked/recent board items through backend-owned projections with why-shown and privacy posture |
| Action Inbox | Holds agent/source-proposed board changes and cross-domain ChangeSets until decided |
| Evidence | Stores content-free decisions, receipts, versions, refs, and rollback posture |
| Memory | May recall reviewed context but cannot become board truth or mutation authority |
| Search | Resolves deep links under owner/privacy scope; private content is never copied into evidence search |

## Accessibility, Responsive Design, And Interaction Quality

- Every pointer drag has Move to lane, Move before/after, Move to top/bottom,
  and cancel keyboard commands with live announcements.
- Focus remains predictable after create, edit, move, archive, undo, conflict,
  navigation, and card-detail return.
- Editors expose dirty state, validation, Cancel, Save, and close/navigation
  warning behavior; a discarded React draft never presents as persisted truth.
- Cards, lanes, menus, checklists, filters, field editors, dialogs, and pending
  states expose correct names, roles, state, errors, and shortcuts.
- A non-drag list/table workflow supports the complete primary loop.
- 200% zoom and 320 CSS-pixel reflow preserve titles, actions, conflicts,
  privacy, and approval state without two-dimensional page scrolling.
- Reduced motion removes nonessential transforms and preserves clear pending,
  success, conflict, and rollback transitions.
- Truncation never hides the only indication of a due, blocked, privacy,
  conflict, or pending state; full values remain accessible.
- Dense desktop mode increases information density without shrinking target
  sizes or suppressing keyboard focus.

## Measurable Quality Gates

The accepted `docs/quality/ECO_000_QUALITY_BUDGETS.md` remains canonical.
Boards must report evidence against its synthetic tiers: small is 5 boards/250
cards, medium is 25 boards/5,000 cards, and large is 100 boards/25,000 cards.

Required targets include:

- warm read-model response p95 at or below 150 ms and visible navigation at or
  below 250 ms;
- search p95 at or below 200 ms small, 500 ms medium, and 1.5 s large;
- 60 fps board/drag target, input-to-preview p95 at or below 100 ms, and commit
  UI feedback at or below 250 ms;
- 100% stale-write conflicts, zero duplicate commits, and deterministic restart
  truth;
- complete local/manual CRUD with network disabled;
- WCAG 2.2 AA target, zero automated violations at the milestone gate,
  complete keyboard path, VoiceOver review, visible focus, contrast, 200% zoom,
  320 CSS-pixel reflow, and reduced-motion proof; and
- reviewed desktop 1440x960, compact 1100x800, narrow 390x844, and applicable
  wallboard 1920x1080 states with no unreviewed clipping or hidden controls.

Targets are not implementation claims. Results require a recorded machine
profile, deterministic synthetic dataset, method, run count, p50/p95 where
applicable, artifact refs, and regression comparison.

## Implementation Sequence

Each milestone is one focused branch or tightly related PR series. No phase may
claim the next phase's behavior or authority.

### `ECO-003A` Product contract, benchmark, and render acceptance

Deliver:

- Accept this plan and the local parity/exclusion contract.
- Ratify the additive Boards schema/value objects, field ownership, protected
  content boundary, route intent, mutation state machine, and manual approval
  semantics.
- Produce independently designed desktop, compact, narrow, empty, dense,
  card-detail, import-preview, conflict, blocked, and recovery renders.
- Record the kan/Trello behavior-reference provenance and clean-room boundary.
- Add a state/control ledger proving every rendered control's intended contract.

Gate: no new Boards storage or route until the contract, security review,
render acceptance, and `ECO-001` dependency are accepted.

### `ECO-003B` Repository, migrations, and Work Board compatibility

Depends on: `ECO-001`.

Deliver:

- Implement typed repository interfaces, schema v1, transactions, versions,
  order keys, integrity checks, protected content, and safe-ref event projection.
- Implement a read-only current Work Board compatibility reader and idempotent
  preview migration to `BoardItem` or typed projection candidates.
- Add backup, restore preview, corruption-safe startup, locked/read-only mode,
  low-disk handling, and attachment-store foundation.

Gate: migration round trips, source fingerprints, counts, ordering, crash
consistency, corruption, low disk, privacy, backup/restore, and redaction tests
pass; the source Work Board remains intact.

### `ECO-003C` Exact local CRUD, ordering, API, and CLI

Deliver:

- Board, view, lane, BoardItem, label, checklist, field, attachment-ref,
  archive/restore, duplicate, move, reorder, and exact-delete application
  services.
- Complete the backend approval-preview/confirm handshake with exact scope,
  policy, lease, expected version, idempotency, receipt, and undo posture.
- Add stable classified API routes, `/api/manifest` metadata, OpenAPI operation
  IDs, and redacted human-readable CLI inspection/mutation commands.
- Add replay, conflict, rollback/compensation, and safe-disable tests.

Gate: every mutation has Python/API/CLI parity, route classification, focused
tests, content-free evidence, deterministic duplicate behavior, and undo or
explicit non-reversible posture.

### `ECO-003D` Boards home, board surface, and card detail

Deliver:

- Boards home, blank/template creation, favorites, recent, archive/restore, and
  compatibility navigation.
- Polished board/list/table views, lane controls, inline quick capture, card
  detail, context actions, filters, search, saved views, scroll restoration,
  keyboard movement, narrow layouts, and all required states.
- Optimistic pending UI with backend receipt refresh, conflict reconciliation,
  retry, and undo.

Gate: browser tests prove every visible control, the complete standalone loop,
desktop/compact/narrow behavior, accessibility, no private-data leakage, and no
React-only product truth.

### `ECO-003E` Portability, templates, and recovery

Deliver:

- Trello local JSON and generic CSV/JSON preview import.
- Versioned UAA private export, redacted support export, round-trip proof,
  template create/version/instantiate, and full backup/restore UX.
- Import mapping, deterministic warnings, staged/atomic commit, idempotency,
  rollback/archive, attachment omission, and post-import verification.

Gate: malformed/untrusted input, duplicate import, interrupted import, large
fixture, export round trip, backup/restore, missing attachment, and no-network
tests pass.

### `ECO-003F` Canonical Task projections

Depends on: `ECO-002`.

Deliver:

- Task BoardMembership/CardProjection, freshness and owner labels, deep links,
  field provenance, unmapped placement, mapped transition ChangeSet, and
  per-operation receipts.
- Migration of any existing work-card/task links without copying Task truth.

Gate: Tasks works without Boards; Boards refreshes canonical Task truth;
conflicts, deletion, privacy, undo/compensation, and stale projection tests pass.

### `ECO-003G` Advanced organization and domain projections

Deliver:

- Swimlanes, WIP enforcement modes, advanced grouping, typed custom fields,
  applicable timeline/calendar-linked views, deterministic local analytics,
  and Plan/CRM/real-estate/Playbook projections as their owners become ready.
- Multi-operation ChangeSet review with dependency and partial-outcome UX.

Gate: no second Kanban engine, no copied domain truth, no hidden cross-domain
mutation, and every advanced view meets keyboard/narrow/performance/privacy
gates.

### `ECO-003H` Hardening and first-class acceptance

Deliver:

- Full synthetic-tier performance evidence, 30-minute soak, visual fidelity
  pack, accessibility ledger, migration/corruption/recovery drill, threat-model
  review, product-language audit, Foundation Gate report, and dogfood findings.
- Close or explicitly defer every parity row and state/control ledger item.

Gate: the accepted matrix is fully evidenced before product truth changes from
planned/partial to first-class implemented. No public release, cloud
collaboration, connector, model/provider, browser, or production-authority claim
is implied.

## Suggested PR Slicing

The milestones above should remain reviewable through narrower PRs:

1. This planning contract and index/board alignment only.
2. Schema/ADR/threat amendments and deterministic fixtures only.
3. Repository/migrations/compatibility reader and tests.
4. Core CRUD/order/approval services and CLI.
5. API/OpenAPI/manifest routes and tests.
6. Boards home and read-only board/card UI.
7. UI mutations, pending/conflict/undo, and browser tests.
8. Import/export/templates/backup/restore.
9. Task projection and ChangeSet integration.
10. Advanced views/projections, then hardening evidence.

Do not combine the plan PR with runtime implementation, dependency changes,
unrelated UI refactors, or existing Work Board deletion.

## Verification Matrix

| Layer | Required proof |
|---|---|
| Contracts | Pydantic/value-object validation, stable refs, ownership, privacy, schema/version, and serialization tests |
| Repository | transaction, order compaction, referential integrity, archive/delete, attachment refcount, index, crash, corrupt, low-disk, and lock tests |
| Mutation | preview/scope binding, denial, expiry, stale version, replay, idempotency, receipt, undo/compensation, partial ChangeSet, and safe-disable tests |
| API | OpenAPI, unique operation IDs, route side-effect class, `/api/manifest`, no-store/private response, error shape, and backward compatibility |
| CLI | human-readable safe inspection, exact mutation parity, blocked/private defaults, deterministic exit status, and no raw path/content in CI output |
| Frontend | component/state tests for every control, draft/pending/success/conflict/blocked/error/undo, refresh truth, and no UI-only mutation state |
| Browser | standalone golden loop, deep links, refresh/back, scroll restoration, drag and keyboard move, import, archive/restore, conflict, offline, narrow, and recovery |
| Accessibility | axe, keyboard scripts, VoiceOver, live announcements, focus, contrast, zoom/reflow, overflow, reduced motion, and non-drag workflow |
| Performance | ECO-000 synthetic tiers, backend timings, browser traces, drag latency/fps, search, memory, soak, migration, backup, and restore |
| Security/privacy | protected/safe-ref separation, import fuzzing, no path traversal/network dereference, attachment handling, support export, log/evidence/fixture redaction |
| Product truth | docs/index/board/current status, accepted renders, state/control ledger, no fake control, no cloud/runtime claim, and Foundation Gate report |

Focused commands must follow the repository's final implementation files. At
minimum, each behavior PR should run its focused pytest/frontend/browser lanes,
documentation integrity, OpenAPI/API manifest verification for route changes,
and the report-only Foundation Gate. Missing dependencies or environment
limitations are reported as blockers, never converted into passing claims.

## Risks And Chosen Responses

| Risk | Response |
|---|---|
| Feature-checklist sprawl delays a useful board | Gate Core V1 around the standalone loop; sequence advanced views and projections later |
| Governance overwhelms the work surface | Keep receipts/proof secondary while preserving exact backend boundaries |
| Drag becomes slow because approval is bolted on afterward | Prepare exact board-only previews during interaction; require explicit diff only for stale/cross-domain/high-consequence moves |
| Projected cards fork owner state | Enforce ADR-0055, field provenance, owner-routed edits, and no mutable projection copies |
| Rich content leaks into evidence or tests | Separate private content and safe-ref planes; synthetic fixtures and redaction tests are release gates |
| Ordering corrupts under dense or concurrent moves | Opaque order keys, expected versions, transactional compaction, idempotency, crash and replay tests |
| Import creates hidden network or data-loss behavior | Local files only, no dereference, preview/fingerprint/warnings, exact commit, rollback, and source preservation |
| Open-source research becomes accidental copying | Record commit/provenance; independently implement concepts; copy no source/assets/text/styles; review any dependency separately |
| Existing `/work-board` users lose history | Versioned compatibility reader, previewed migration, backup, no automatic source deletion, and delayed redirect/cutover |
| Local attachments make backup/recovery fragile | Governed content store, integrity/refcount model, missing-file states, size limits, and round-trip recovery tests |

## Explicit Non-Goals For This Plan And Core V1

- No kan source, assets, styles, text, or dependency adoption.
- No exact visual clone of kan.bn or Trello.
- No hosted service, public board, account system, billing, or cloud sync.
- No multi-user workspace, invitation, role, presence, or live collaboration.
- No OAuth, live Trello API, background import, webhook, power-up, or connector.
- No remote attachment retrieval or cloud object store.
- No comments presented as collaboration; use private local notes until a
  separately accepted collaboration model exists.
- No automatic agent board changes, silent domain transitions, broad write
  toggle, or UI-minted approval.
- No new model/provider calls, web fetch, browser automation, unrestricted
  shell/subprocess execution, plugin runtime, public distribution, or
  production authority.
- No deletion of the existing Work Board store or route before accepted
  migration, compatibility, rollback, and cutover evidence.

## First-Class Acceptance Checklist

UAA Boards may be called first-class only when all of the following are true:

- Core V1 parity rows are implemented or explicitly re-accepted as deferred.
- A new operator can create a board, capture and enrich a card, move it, find
  it, undo it, archive/restore it, export it, and recover it entirely offline.
- The same primary workflow is complete with keyboard and non-drag controls.
- Current Work Board data migrates once with preview, counts, fingerprints,
  backup, source preservation, receipt, and recovery evidence.
- Standalone `BoardItem` and canonical Task projection loops both pass without
  copied Task truth.
- Every mutation has Python/core/API/CLI parity, stable route contracts, exact
  scope, policy/approval validation, idempotency, versions, receipts, and undo
  or explicit compensation posture.
- Private content never appears in durable evidence, logs, docs, reports,
  fixtures, screenshots, or default CLI output.
- Empty, loading, locked, offline, stale, conflict, blocked, partial, error,
  success, and undo states are human-readable and browser-tested.
- ECO-000 accessibility, responsive, performance, reliability, migration,
  backup/restore, and visual-fidelity targets have measured evidence.
- Every visible control is real, correctly typed, and covered by the control
  ledger and tests.
- Product truth remains explicit about every advanced, excluded, blocked, or
  not-yet-authorized capability.

At that point Boards is not merely a first-class Kanban. It is UAA's shared
visual-work engine: locally excellent on its own, consistent with familiar
board tools, and uniquely capable of governing cross-app work without
duplicating truth or hiding authority.
