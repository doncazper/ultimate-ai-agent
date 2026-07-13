# ECO-000 Existing State And Migration Inventory

Status: accepted inventory for planning. This document authorizes no migration,
storage change, route, connector, or runtime capability.

## Classification vocabulary

- `canonical candidate`: may become the source record after an explicit app
  milestone and migration proof.
- `compatibility-only`: remains readable under its historical contract.
- `projection`: display/placement state pointing to a canonical subject.
- `link`: typed relationship between canonical refs.
- `migration source`: input to a previewed, idempotent later migration.
- `historical evidence`: immutable receipt/audit truth, never reinterpreted.
- `deprecated later`: removable only after retention, cutover, restore, and
  rollback gates pass.

## Current overlap matrix

| Record family and current record | Current module/store and contract | Current inspection surface | Current authority/side effect | ECO owner and disposition | Required compatibility/migration | Principal risks | Cutover proof required |
|---|---|---|---|---|---|---|---|
| Founder Loop action item / `FounderLoopActionRecord` | `core/storage/founder_loop.py`; Founder Loop SQLite; `founder_loop_storage.v1` plus per-lane contract refs | Action Inbox API, founder-loop CLI, Control Center | Backend-owned read; exact approval decisions; selected exact mutations only | Governance/Action Inbox; compatibility-only plus link source | Preserve IDs and receipts; map approved proposals to canonical targets, never to Tasks automatically | Double action, lost approval scope, false completion | Record-count/fingerprint reconciliation; approval/receipt binding tests; replay test |
| Founder Loop plan / `FounderLoopPlanRecord` | `core/storage/founder_loop.py`; Founder Loop SQLite; `founder_loop_storage.v1` | Plans/Today read models and CLI | Read/proposal posture; no generic execution | Plans; migration source for canonical Plan/PlanStep | Versioned reader; preview decomposition and dependency map | Reordered steps, changed plan identity, duplicate Plan | Immutable fingerprint comparison; dependency and terminal receipt proof |
| Founder Loop briefing/attention items | `FounderLoopBriefingRecord`, Today summary in Founder Loop SQLite | Today, Morning Briefing, CLI | Projection/read-only | Today; projection only | Replace copied summary fields with owner refs and why-shown metadata | Stale copied truth, private item leakage | Owner-ref coverage, staleness, privacy, and no-orphan tests |
| Local task commit receipt / local task read model | `core/control_center/local_tasks.py`; append-first receipt through Founder Loop state; `contract-ref:founder-loop-local-task-commit:v1` | Exact local-task commit route, Action Inbox, CLI | Reversible local mutation only with exact approval and AuthorityLease; no external side effect | Tasks; migration source and historical evidence | Convert each committed local-task ref once; retain original receipt link | Duplicate Task on replay, title leakage, missing rollback | Idempotent import, receipt chain, safe-ref/redaction, repeated-cutover test |
| Work Board card / `WorkBoardCardReadModel` | `core/control_center/work_board.py`; bounded `uaa-work-board-state.v1` JSON; read model `uaa-work-board-read-model.v1` / `contract-ref:work-board-kanban-shell:v1` | Work Board API and Control Center | Backend-owned local card create/reorder under exact approval | Boards; projection when subject is Task/Plan/CRM, otherwise BoardItem candidate | Classify subject; preserve board/lane/order as projection state | Copied task/CRM status, orphan subject, reorder conflict | Subject ownership test, ordering/version test, compatibility reader |
| Work Board local task / `WorkBoardLocalTaskReadModel` | Work Board bounded JSON plus local-task linkage | Work Board read model and task-create route | Exact local mutation; no connector write | Tasks owns Task; Boards stores membership/projection | Resolve canonical Task by receipt/idempotency refs; do not create a second task | Duplicate local-task truth, lost action receipt | One-to-one mapping, replay, missing-subject fail-closed tests |
| Work Board columns/drag posture | Work Board JSON and `WorkBoardColumnReadModel` | Work Board API/UI | Local ordering mutation with approval/safe-disable | Boards; canonical Lane/CardOrdering candidate | Versioned board migration after shared store exists | Lost ordering, concurrent drag overwrite | Optimistic-version conflict, undo, dense-board order checks |
| CRM M0 domain records | `core/crm/contracts.py`; contract-only safe refs; `contract-ref:crm-communications-spine-m0:v1` | Verifier/tests only | No CRM runtime granted | CRM/Identity/Inbox/Governance according to ADR-0054; historical contract | Preserve contract refs; provide adapters into ECO vocabulary | Breaking historical evidence, treating proposals as truth | Import compatibility test and unchanged verifier |
| CRM M1 fixture records | `core/crm/fixtures.py`; synthetic fixture map; `contract-ref:crm-m1-fixture-only-vertical-shell:v1` | Fixture shell/tests | Fixture-only, no source runtime | Historical test evidence; not production migration input | Keep fixture version and use only synthetic render/test data | Fixture mistaken for user data or live capability | Fixture marker and product-language tests |
| CRM M2 relationship/workspace records | `core/crm/local_command_center.py`; safe-ref JSON snapshot and JSONL events/receipts; `crm-local-command-center.v1` | CRM summary, relationships, timeline, follow-ups, pipelines, smart lists, CLI | Partial local read plus exact local mutation; connector reads/writes blocked | CRM canonical candidate; Identity refs remain separate | Previewed adapter preserving workspace, version, events, idempotency, receipts | Silent merge, lost history, scope collapse | Snapshot/event replay, workspace isolation, receipt reconciliation |
| CRM M2 follow-up | CRM snapshot/event ledger | CRM follow-ups, Today/Action projections | Local proposal/mutation posture | CRM owns FollowUp until promoted; accountable Task is a typed link to Tasks | Explicit operator-reviewed promotion mapping | Two competing due/status fields, duplicate Task | Promotion idempotency, source link, no silent Task creation |
| CRM M2 timeline item/activity | CRM event ledger/read model | CRM timeline API/UI/CLI | Read-only safe summary projection | Originating app owns change; CRM timeline is projection | Preserve source/evidence refs; do not copy raw values to Evidence | Timeline becomes second activity truth, raw note leakage | Owner-ref, safe-summary, ordering, deletion-posture tests |
| Planning `TaskPlan`, `TaskStep`, `TaskDependency` | `core/planning/`; Pydantic contract records (`extra=forbid`), no shared app-store schema | Planning APIs/CLI/tests | Review/planning only unless separately dispatched | Plans owns Plan/PlanStep; not a canonical Task repository | Adapter can reference plan contracts; app migration must not reinterpret run plans as personal Tasks | Runtime plan conflated with product plan, changed dependency graph | Contract-kind marker, immutable fingerprint, no automatic conversion |
| Durable mission/action receipts | execution/orchestration ledgers | CLI/API evidence and receipts | Historical execution evidence, not app truth | Governance historical evidence | Link by safe refs only | Rewriting evidence during migration, result-to-truth promotion | Hash/receipt verification and immutable source test |
| Evidence timeline entries | Founder Loop evidence records/SQLite | Evidence API/CLI/UI | Read-only content-free evidence | Governance/Evidence; projection and historical evidence | Keep exact receipt/evidence refs; app timeline links to it | Raw private values copied into evidence, duplicated event history | Redaction scan, provenance and no-domain-owner test |
| Memory candidates/review decisions | `core/memory/` and Founder Loop memory review storage | Memory APIs/CLI/UI | Recall/review only; exact memory writes separately governed | Memory; never canonical app truth | Preserve source refs, correction, supersession, expiry, review state | Recall promoted to contact/event/task truth | Canonical-truth denial test, source deletion/exclusion test |
| Email/calendar connector contract records | `core/connectors/email_connector_contract_refresh.py` M121 and `calendar_connector_contract_refresh.py` M122 contract records | Verifiers/tests and source-readiness surfaces | Contract/metadata only; live reads and writes blocked unless exact later lane | Integration catalog and Inbox source-binding proposals; not Events or messages | Preserve as configuration/readiness evidence | Configuration mistaken for synced data or authority | Catalog-versus-authority and no-route/runtime tests |
| Founder Loop source-readiness items | `core/connectors/founder_loop_read_only_integration_contracts.py` | Source readiness API/CLI/UI | Backend-owned readiness/proposal truth, not external data | Integration catalog projection | Map status/reason refs; no source content import | "ready" mistaken for callable/read authority | Availability/readiness separation and product-language tests |
| Communication delivery envelopes | `core/execution/connector_delivery.py` | CLI/task-decomposition inspection | Contract-only; sends blocked | Governance/Inbox historical plan evidence | Link future drafts/sends by exact refs; no raw body | Draft mistaken for sent; replay without provider truth | Delivery-state vocabulary, no-send and raw-content tests |

## Cutover ordering and compatibility policy

1. ECO-001 proves storage, encryption, migration, recovery, and compatibility
   reader facilities without cutting over an app.
2. Tasks migrates local-task and Work Board task candidates before Boards uses
   Task projections.
3. Boards migrates board structure and classifies every card subject.
4. CRM adopts canonical Identity/Event/Task/Board links without migrating
   connector metadata into app records.
5. Today and cross-app timelines switch only after every item resolves to a
   canonical owner ref or an explicit historical-evidence ref.

No cutover deletes its source. A later retention milestone may deprecate a
compatibility reader only after two successful restore drills, deterministic
replay, export/delete reconciliation, and an operator-visible rollback window.

## Unresolved evidence before ECO-001

- Exact Founder Loop SQLite schema version and migration API boundary.
- Stable version/fingerprint adapter for Work Board JSON.
- CRM M2 snapshot/event compaction and interrupted-write recovery proof.
- Key lifecycle and encrypted backup selection.
- Search-index rebuild and deletion semantics across workspaces.
- Quantified source record counts and migration duration on synthetic tiers.
