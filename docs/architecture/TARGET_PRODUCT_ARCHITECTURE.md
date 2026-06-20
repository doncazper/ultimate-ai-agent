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

### Control Center App Shell

Control Center should become the Founder Command Center shell organized around
Today, Inbox, Plans, Actions, Memory, Evidence, and Settings. It should show
human-readable state before developer detail and must follow
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

Control Center does not become the authority layer.

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

### PolicyEngine

PolicyEngine remains the required policy boundary for authority decisions.
Future service modules must route relevant decisions through it instead of
adding parallel shortcuts.

### LocalApprovalAuthority

LocalApprovalAuthority remains the exact-scope approval boundary. Approval refs
are identifiers only. Exact actor, resource, capability, risk, scope,
expiration, revocation, replay, audit, and receipt bindings must be preserved.

### Memory Layers

Memory remains recall, not truth or authority.

Target layers:

- Reviewed local recall records.
- Business memory candidates for people, projects, deals, and promises.
- Memory Review Inbox state.
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
- Draft-only response proposal.
- Follow-up and lead metadata.
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

### `system_service`

Owns health, version, API manifest, route inventory, and static metadata.

Candidate routes: `/health`, `/version`, `/api/manifest`,
`/control-center/status`, `/control-center/routes`.

### `runtime_service`

Owns runtime readiness, capability matrix, local model gateway status, local
model list/chat readiness summaries, and local smoke validation.

Candidate routes: `/runtime/*`, `/model-runtime/*`, `/v1/*`,
`/models/route/preview`.

### `planning_service`

Owns task classification, decomposition, plan validation, plan run summaries,
and workflow planning envelopes.

Candidate routes: `/task-decomposition/*`.

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

Candidate routes: `/files/*`.

### `evidence_service`

Owns receipts, events, timeline summaries, observability summaries, Foundation
Gate summaries, latency refs, release evidence refs, and rollback status.

Candidate routes: `/receipts/*`, `/events/*`, `/observability/*`,
`/gate/*`, `/control-center/foundation-gate/summary`.

### `integration_service`

Owns integration contracts and future governed adapters for email metadata,
calendar read-only, draft-only response proposals, Mattermost, and governed
web evidence status.

Candidate routes: `/integrations/*`, `/web-evidence/*`, future
contract-only connector routes.

### `settings_service`

Owns safe setup summary, feature flag posture, kill-switch posture, disabled
authority boundary summaries, and redacted local configuration status.

Candidate routes: future settings/status routes only after scope approval.

### `workflow_service`

Owns Founder Command Center workflow aggregation: Today, Morning Briefing,
Action Inbox, Memory Review Inbox, Evidence Timeline, and Weekly CEO Review.

Candidate routes: future aggregation/status routes that compose existing safe
summaries before adding any new authority.

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
