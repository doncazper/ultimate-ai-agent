# Target Product Architecture

Status: target architecture planning artifact

This document describes the desired Founder Command Center architecture. It
does not implement service modules, move routes, add runtime authority, add
dependencies, or change OpenAPI. Future implementation must preserve current
route behavior unless an accepted scoped task says otherwise.

## Architecture Summary

```text
Founder / Operator
        |
        v
Control Center app shell
        |
        v
FastAPI service boundary and /api/manifest
        |
        v
Python Agent Core
        |
        +-- PolicyEngine
        +-- LocalApprovalAuthority
        +-- ToolBroker
        +-- Task decomposition
        +-- Durable runs
        +-- Memory layers
        +-- Evidence, receipts, audit, replay, rollback
        +-- Integration contracts and governed adapters
```

Control Center and OpenWebUI are shells. The Python Agent Core remains the
brain and authority boundary.

## Core Components

### Python Agent Core

The Python core owns policy, approvals, contracts, task decomposition, memory,
tool governance, durable runs, evidence, receipts, redaction, and Foundation
Gate integration.

It must not delegate authority to Control Center, OpenWebUI, model output, raw
provider output, memory recall, or plugin metadata.

### FastAPI Service Boundary

FastAPI remains the typed local API boundary. `/api/manifest` and OpenAPI are
public contract surfaces for route metadata, route count, operation IDs,
declared capabilities, blocked capabilities, and side-effect classes.

Routes may validate, preview, summarize, or expose metadata. Runtime authority
requires an accepted scoped milestone, explicit approval model, side-effect
class, tests, and verifier updates.

Because Control Center is browser-facing, the FastAPI boundary now includes the
UAA-P1-080 through UAA-P1-086 local-first API perimeter: every route is
classified as `public_metadata`, `local_readonly`, `local_sensitive`, or
`mutating_requires_authority`; centralized security headers are present;
loopback Control Center CORS origins are explicit; sensitive routes have a
local bearer/session gate; mutating routes require idempotency keys or scoped
idempotency refs; targeted local rate limits cover selected expensive/sensitive
paths; and OpenAPI, `/api/manifest`, and route inventory tests enforce the
posture. These controls do not grant broader runtime authority.

### Control Center App Shell

Control Center should become the Founder Command Center shell organized around
Today, Inbox, Plans, Actions, Memory, Evidence, and Settings. It should show
human-readable state before developer detail and must follow
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

Control Center does not become the authority layer.

### Coherent Application Ecosystem

The full application-suite target is subordinate to this architecture in
`docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`.
Calendar, Tasks, Boards, CRM, Inbox, Today, Organizer, Evidence, and Memory must
share the Python Agent Core and governance boundaries while keeping one
canonical owner for each event, task, relationship, opportunity, source
artifact, board projection, and receipt. This planning target adds no routes,
stores, connectors, controls, dependencies, packaging, or authority by itself.
ECO-000 accepts the additive ownership/link/projection/ChangeSet vocabulary,
ADRs 0054-0061, migration inventory, privacy threat model, app acceptance bar,
planned navigation, reviewed design drafts, and unmeasured quality targets.
Implementation begins only through a separately accepted ECO-001 milestone.

### OpenWebUI Optional Shell

OpenWebUI remains an optional local shell into UAA-managed local model behavior.
It is not the agent brain, not a tool authority, not a memory authority, and
not a connector authority.

### Workflow Engine

The target workflow layer coordinates user-visible loops:

- Morning Briefing
- Prioritized Plan
- Action Inbox
- Draft-only reply proposals
- Memory Review Inbox
- Evidence Timeline
- Weekly CEO Review

The workflow layer should compose existing contracts before adding routes. It
must keep planned, partial, blocked, skipped, mock-only, and implemented states
distinct.

The first workflow promoted from posture to backend-owned product behavior is
the completed bounded FCC-V1 conveyor in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`. One Today item can become
an Action envelope, receive an exact approve/edit/reject/defer decision,
produce a durable receipt, and update Evidence Timeline through backend-owned
state with CLI/core/API inspection parity. Chat receipt/handoff and Memory
Review accept/correct/reject decisions follow the same receipt/evidence
boundary. FCC-V1-007 promotes only `/actions`, `/chat`, `/memory`, and
`/evidence`; `/today` and the broader product loop remain partial until later
scoped work.

### Task Decomposition

Task decomposition remains the planning and safe capability orchestration
spine. It can classify, decompose, validate, bind approvals, expose audit, bind
durable run records, and report metrics.

Plan creation must not imply execution.

### Durable Runs

Durable runs provide local run truth: state transitions, idempotency, restart
visibility, replay refs, receipt refs, audit refs, and rollback refs.

Durable runs must not store raw prompts, raw responses, raw provider payloads,
raw private paths, raw logs, environment dumps, credentials, or secret-like
values.

### ToolBroker

ToolBroker evaluates capability registry entries, execution contracts, context
boundaries, credentials, firewall, consent, idempotency, approval, dry-run, and
Foundation Gate blockers.

It remains the path for governed tool runtime adapters. It must not become an
arbitrary plugin, shell, browser, connector, or remote execution dispatcher
without a future scoped milestone.

### AuthorityDispatcher

`AuthorityDispatcher` is the durable Python Core execution seam for exact
adapters promoted under AuthorityLease. Its V1 implementation binds current
lease policy, exact approval where required, operation/cost reservation,
pre-start proof, adapter invocation, settlement/release, pre-start
cancellation, recovery posture, and safe evidence refs.

Only explicitly injected safe tool-runtime adapters are routed through it now.
It is not a dynamic plugin registry and does not grant generic tool, shell,
browser, provider, connector, background, or production authority. Legacy
execution paths remain partial until separately migrated with CLI/API/UI parity
and focused proof.

### PolicyEngine

PolicyEngine remains the required policy boundary for authority decisions.
Future service modules must route relevant decisions through it instead of
adding parallel shortcuts.

### LocalApprovalAuthority

LocalApprovalAuthority remains the exact-scope approval boundary. Approval refs
are identifiers only. Exact actor, resource, capability, risk, scope,
expiration, revocation, replay, audit, and receipt bindings must be preserved.

### Planning-Only Permission Modes

Founder Command Center surfaces should share a planning vocabulary for authority
posture:

- Observe: safe refs, metadata, and redacted summaries only.
- Draft: editable output that cannot send, write, execute, or persist as truth.
- Propose: a scoped action envelope with evidence, risk, side-effect class,
  expiry, idempotency, receipt refs, and rollback/safe-disable posture.
- Approve once: future exact-scope grant for one reviewed action.
- Approve rule: future bounded rule approval with expiry, revocation, audit, and
  receipt requirements.
- Autopilot micro-scope: future narrowly bounded repeated action class after a
  separate scoped milestone proves safety and usefulness.
- Kill switch: visible status/plan for future stop, disable, or revoke
  behavior.

These are inert planning labels, not runtime modes, API capabilities, approval
grants, UI affordances, feature flags, connector scopes, or background sessions.
Observe does not fetch, crawl, refresh, or collect account/network data. Draft
does not send, write, persist as truth, or authorize outbound side effects.
Propose does not dispatch, schedule, retry, execute, or create a durable run.
Approve once and Approve rule do not create approval refs, reusable grants, or
standing authority. Autopilot micro-scope does not start background autonomy,
polling, repeated execution, or connector writes. Kill switch is posture text
only unless a later scoped mutation path is accepted. Future implementations
must bind exact approvals, policy decisions, audit refs, receipt refs,
revocation, and rollback/safe-disable behavior through PolicyEngine and
LocalApprovalAuthority.

### Memory Layers

Memory remains recall, not truth or authority.

Target layers:

- Profile memory candidates for stable user preferences and working style.
- Project memory candidates for goals, repos, decisions, blockers, and open
  loops.
- Relationship memory candidates for people, organizations, promises,
  follow-ups, and context.
- Episodic memory candidates for reviewed events, decisions, and outcomes.
- Business memory candidates for deals, leads, customers, partnerships, and
  commitments.
- Semantic-local knowledge labels and summaries for future reviewed retrieval
  UX, without implying embeddings, vector search, RAG ingestion, or context
  injection.
- Reviewed local recall records and Memory Review Inbox state.
- Redacted export and deletion/retention posture.
- Source/evidence priority that keeps canonical evidence above memory.

No automatic memory writes or context injection are implied by this target.

### Evidence, Receipts, And Audit

Evidence should become human-readable product proof:

- Receipt summaries.
- Event and audit timeline.
- Latency summary refs.
- Rollback or safe-disable refs.
- Foundation Gate and release-lane status.
- Source/evidence refs for plans and memory candidates.

Evidence must be safe-ref and redacted-summary first.

### Integration Adapters

Target adapters should be contract-first:

- Email metadata read-only.
- Calendar read-only.
- Contacts lookup/read-only contact metadata contracts after scoped consent and
  redaction review.
- Draft-only response proposal.
- Task creation proposals that cannot write to external task systems until a
  later exact approval lane exists.
- Governed article/evidence capture proposals over allowlisted read-only
  evidence contracts.
- GitHub read-only project status summaries where repository access, redaction,
  and evidence refs are separately scoped.
- Follow-up and lead metadata.
- CRM-lite local lead/follow-up store with reviewed local metadata only.
- Document/repo/project summary refs.

Runtime connector behavior remains blocked until a later scoped milestone
defines auth, consent, read/write boundaries, redaction, approval, revocation,
audit, tests, and rollback/safe-disable.

### Settings And Kill Switch

Settings should expose safe local setup, feature flag posture, disabled
boundaries, kill-switch posture, revocation posture, and setup blockers.

Settings must not expose credential collection or broad authority toggles.

### Local/Cloud Split

Local-first remains the default:

- Local loopback API and Control Center.
- Local model shell only through reviewed local gateway lanes.
- Local durable state and redacted evidence.
- Optional cloud/server behavior only after scoped milestone and separate
  authority boundary.

## Proposed Service Modules

These are target modules for future refactor tasks. They are not implemented by
this document.

Service ownership is routing and contract ownership only. It does not grant
memory write authority, context injection, account auth, connector runtime,
connector writes, browser automation, plugin execution, background polling, or
production authority. Any future mutating or runtime adapter path must be
separately scoped, PolicyEngine-classified, LocalApprovalAuthority-bound,
idempotency-bound, redacted, auditable, revocable, receipt-backed,
rollback/safe-disable-aware, and tested.

### `system_service`

Owns health, version, API manifest, route inventory, and static metadata.

Candidate routes: `/health`, `/version`, `/api/manifest`,
`/control-center/status`, `/control-center/routes`.

### `runtime_service`

Owns runtime readiness, capability matrix, local model gateway status, local
model list/chat readiness summaries, and local smoke validation.

Candidate routes: `/runtime/*`, `/model-runtime/*`, `/v1/*`,
`/models/route/preview`.

Accepted UAA-P1-052 extraction splits this into `runtime_service` for
`/runtime/*` readiness/boundary routes and `model_runtime_service` for
`/model-*`, `/model-runtime/*`, local `/v1/*`, and OpenWebUI local test routes.

### `planning_service`

Owns task classification, decomposition, plan validation, plan run summaries,
and workflow planning envelopes.

Product-facing candidate routes: `/task-decomposition/*`.
Accepted UAA-P1-052 extraction module name for current route movement:
`task_decomposition_service`.

### `approval_service`

Owns approval request validation, grant validation, LocalApprovalAuthority
binding, approval summaries, revocation, and approval receipts.

Candidate routes: `/approvals/*`, task decomposition approval routes,
`/control-center/approvals/summary`.

### `memory_service`

Owns memory records, recall, review candidates, relationship/follow-up memory,
redacted export, retention, correction, and delete posture.

Candidate routes: `/memory/*` and future memory-review summaries.

### `file_service`

Owns safe file refs, tree preview, bounded read preview, write proposals, diff
preview, atomic apply, rollback receipts, and file review approvals.

Product-facing candidate routes: `/files/*`.
Accepted UAA-P1-052 extraction module name for current route movement:
`workspace_files_service`.

### `evidence_service`

Owns receipts, events, timeline summaries, observability summaries, Foundation
Gate summaries, latency refs, release evidence refs, and rollback status.

Candidate routes: `/receipts/*`, `/events/*`, `/observability/*`,
`/gate/*`, `/control-center/foundation-gate/summary`.

### `integration_service`

Owns integration contract shapes for possible later adapter milestones covering
email metadata, calendar read-only, future contacts lookup contract planning,
draft-only response proposals, task creation proposals, governed
article/evidence capture, GitHub read-only project status, CRM-lite local
lead/follow-up contracts, Mattermost, and governed web evidence status. Adapter
runtime remains separately scoped.

Candidate routes: `/integrations/*`, `/web-evidence/*`, future
contract-only connector routes.

Accepted UAA-P1-052 extraction module names are `integrations_service` for
Mattermost-style integration routes and `governed_web_evidence_service` for
`/web-evidence/*`.

### `settings_service`

Owns safe setup summary, feature flag posture, kill-switch posture, disabled
authority boundary summaries, and redacted local configuration status.

Candidate routes: future settings/status routes only after scope approval.
Accepted UAA-P1-052 extraction treats `settings_service` as future-scoped
because no dedicated Settings route exists yet.

### `workflow_service`

Owns Founder Command Center workflow aggregation: Today, Morning Briefing,
Action Inbox, Memory Review Inbox, Evidence Timeline, and Weekly CEO Review.

Candidate routes: future aggregation/status routes that compose existing safe
summaries before adding any new authority.

FCC-P1-012 keeps current Founder Command Center summary routes in the accepted
`control_center_service` extraction boundary until a separate scoped
`workflow_service` route contract exists.

## Migration Strategy

1. Document ownership first.
2. Add or update tests that freeze current OpenAPI operation IDs, route count,
   side-effect classes, route groups, auth posture, capability declarations,
   blocked capabilities, and API manifest fields.
3. Extract one low-risk read-only route group first, preferably system or
   Control Center summary routes.
4. Keep route paths, methods, request/response schemas, operation IDs, tags,
   and side-effect classes unchanged unless the PR explicitly scopes an API
   change.
5. Keep route side-effect classes in `src/ultimate_ai_agent/api/manifest.py`
   authoritative.
6. Keep `/api/manifest` truth and OpenAPI checks green after each extraction.
7. Keep Foundation Gate checks green.
8. Avoid dependency additions unless a scoped task proves they are necessary.

## No-Route-Drift Rules

- Do not rename existing paths during extraction.
- Do not change operation IDs accidentally.
- Do not change side-effect class by moving a route.
- Do not add backend routes for planning docs.
- Do not expose new mutating controls from Control Center without exact scope.
- Do not hide blocked, skipped, partial, or mock-only state.

## First Refactor Candidate

First candidate: system/control-center summary extraction.

Why:

- Mostly read-only or validation/status-only.
- Strong existing tests in `tests/test_api_manifest.py` and
  `tests/test_control_center_api_routes.py`.
- Low risk if operation IDs, side-effect classes, response envelopes, and route
  inventory stay unchanged.

Exit criteria:

- OpenAPI path count unchanged unless explicitly approved.
- Operation IDs unchanged.
- API manifest fields unchanged.
- Control Center route status manifest still matches OpenAPI.
- Foundation Gate report-only still passes.
