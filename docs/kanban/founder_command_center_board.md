# Founder Command Center Kanban Board

Status: planning and execution board
Parent board: `docs/kanban/current_board.md`
Parent plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`

This board is a product-loop planning board. It does not replace Operator
Runtime Excellence and does not grant runtime authority. UAA-P1-011 is the
readable-loop baseline; the next product slice starts from its proof chain and
does not broaden runtime authority.

The active implementation sequence is:

1. FCC-MAC-001 macOS Setup Assistant hardening.
2. FCC-P0-002 first product-loop readability.
3. FCC-P0-004 Action Inbox approval envelopes.
4. FCC-P0-003 Morning Briefing skeleton.
5. Read-only email/calendar contracts later.

Mattermost, plugin ecosystem, packaging/distribution, additional integrations,
and new runtime authority lanes are not allowed to displace this sequence
without a separate scoped dependency, safety boundary, tests, and verifier plan.

## WIP Limits

```text
Now: max 2 cards
Frontend product-surface cards: max 2 cards
Backend route-contract cards: max 1 card unless docs/test-only
Authority-changing cards: 0 unless a separate scoped milestone is accepted
```

## Epics

1. Product/UX
2. Core Agent Runtime
3. Memory/Knowledge
4. Tools/Integrations
5. Business Cofounder Workflows
6. Safety/Permissions
7. Testing/Evals
8. Infrastructure/Deployment
9. Growth/Commercialization

## Now

### FCC-MAC-001 - P0 - macOS Setup Assistant Hardening

Epic: Product/UX, Infrastructure/Deployment, Safety/Permissions

Description: Harden the macOS-first Setup Assistant foundation around the
existing dry-run/read-only route, bounded previews, approval-envelope posture,
rollback refs, and truthful blocked states.

Repo areas likely touched: `docs/macos/UAA-setup-assistant-plan.md`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`apps/control-center/src/components/MacOSSetupAssistantPanel.tsx`,
`apps/control-center/src/App.test.tsx`, and focused setup assistant tests if the
slice changes contracts.

Acceptance criteria: The setup surface stays dry-run only, model choices remain
recommendation classes, approval-required setup steps show dry-run
approval-envelope refs, dry-run receipt refs, rollback refs, redacted bounded
terminal/log previews, and no setup mutation authority is implied.

Required tests/verifiers: focused setup assistant tests,
`make frontend-check`, `.venv/bin/python scripts/verify_control_center_frontend.py`,
and OpenAPI verification only if the route contract changes.

Safety notes: No installer execution, model download, LaunchAgent install/load,
background-service install/load, bridge enablement, credential handling,
shell/subprocess execution, signed installer readiness, public distribution, or
production authority.

Blockers/dependencies: Existing dry-run setup contract and read-only summary
route.

### FCC-P0-002 - P0 - First Product Loop Readability And Information Architecture

Epic: Product/UX

Description: Shape Control Center navigation and product hierarchy around
Today, Inbox, Plans, Actions, Memory, Evidence, and Settings without removing
existing route access needed for operator review.

Repo areas likely touched: `apps/control-center/src/routes.tsx`,
`apps/control-center/src/App.test.tsx`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

Acceptance criteria: The IA shows fewer primary surfaces while existing
operator routes remain reachable or clearly grouped. Every visible action keeps
authority and side-effect truth visible.

Required tests/verifiers: `make frontend-check`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py`,
`.venv/bin/python scripts/verify_documentation_integrity.py`.

Safety notes: Frontend-only grouping must not imply completed backend flows.

Blockers/dependencies: FCC-P0-001 defines the readable baseline; FCC-MAC-001
keeps first-run/setup posture truthful.

## Ready

### FCC-P0-004 - P0 - Action Inbox Contract And UI Skeleton

Epic: Product/UX, Safety/Permissions

Description: Define action proposal fields and an Action Inbox display for
approve/edit/reject/defer review states.

Repo areas likely touched: `src/ultimate_ai_agent/core/`,
`apps/control-center/src/components/`, `tests/`,
`docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`.

Acceptance criteria: Action cards require safe refs, side-effect class, risk,
authority boundary, approval requirement, evidence refs, idempotency, expiry,
and rollback/safe-disable posture.

Required tests/verifiers: focused schema tests, `make frontend-check`,
`.venv/bin/python scripts/verify_documentation_integrity.py`.

Safety notes: No execution path and no broad approval. Approve controls stay
disabled or absent until exact backend binding is scoped.

Blockers/dependencies: Builds on completed FCC-P0-001 baseline.

### FCC-P0-003 - P0 - Morning Briefing Workflow Skeleton

Epic: Product/UX, Business Cofounder Workflows

Description: Add a Today/Morning Briefing skeleton over existing status,
route, plan, evidence, and blocked-state summaries.

Repo areas likely touched: `apps/control-center/src/components/`,
`apps/control-center/src/mocks/controlCenterData.ts`,
`apps/control-center/src/api/types.ts`, `apps/control-center/src/App.test.tsx`.

Acceptance criteria: Briefing shows priorities, blockers, next safe actions,
evidence gaps, and memory-review count using existing or mock-safe summaries.

Required tests/verifiers: `make frontend-check`,
`.venv/bin/python scripts/verify_control_center_frontend.py`.

Safety notes: No background generation, connector access, raw private content,
or memory write.

Blockers/dependencies: FCC-P0-002 and FCC-P0-004.

### FCC-P0-005 - P0 - Memory Review Inbox Contract And UI Skeleton

Epic: Memory/Knowledge, Business Cofounder Workflows

Description: Add reviewed memory candidate shape for people, projects, deals,
promises, corrections, and rejections.

Repo areas likely touched: `src/ultimate_ai_agent/core/memory/`,
`apps/control-center/src/components/`, `tests/test_memory*.py`,
`apps/control-center/src/App.test.tsx`.

Acceptance criteria: Memory candidates require provenance, source refs,
evidence refs, review state, correction state, retention/delete posture, and
safe summaries.

Required tests/verifiers: memory contract tests, redaction tests,
`make frontend-check`.

Safety notes: Memory remains recall, not truth or authority. No automatic
memory writes or context injection.

Blockers/dependencies: Existing LocalMemoryStore policies.

### FCC-P1-006 - P1 - Human-Readable Evidence Timeline

Epic: Product/UX, Safety/Permissions

Description: Convert receipt, event, audit, latency, Foundation Gate, and
rollback refs into a readable timeline.

Repo areas likely touched: `apps/control-center/src/components/`,
`src/ultimate_ai_agent/core/execution/`, `src/ultimate_ai_agent/core/observability/`,
`tests/`.

Acceptance criteria: Evidence appears as human summaries first, with safe refs
and redaction status visible. Developer details never become the primary
operator UI.

Required tests/verifiers: frontend tests, redaction tests,
`.venv/bin/python scripts/verify_control_center_frontend.py`.

Safety notes: No raw prompt, response, provider payload, path, log, environment
dump, credential material, or secret-like value.

Blockers/dependencies: Builds on completed FCC-P0-001 baseline and current
observability summaries.

## Shaping

### FCC-P1-007 - P1 - Calendar Read-Only Integration Contract

Epic: Tools/Integrations, Business Cofounder Workflows

Description: Define read-only calendar event metadata contracts for meeting
prep without account auth or runtime fetch.

Repo areas likely touched: `src/ultimate_ai_agent/core/`, `docs/connectors/`,
`tests/`.

Acceptance criteria: Contracts use safe refs for attendee/account identities and
deny calendar writes, account auth, raw invite bodies, event titles, meeting
links, locations, background collection, and connector runtime.

Required tests/verifiers: contract tests and documentation integrity.

Safety notes: Read-only contract only. No live calendar integration or raw
private calendar metadata in durable evidence.

Blockers/dependencies: Exact connector milestone required before runtime.

### FCC-P1-008 - P1 - Email Metadata Read-Only Contract

Epic: Tools/Integrations, Business Cofounder Workflows

Description: Define safe email metadata envelopes for triage fixtures and
future read-only connector review.

Repo areas likely touched: `src/ultimate_ai_agent/core/`, `docs/connectors/`,
`tests/`.

Acceptance criteria: Contracts allow safe sender/thread/time/label refs and
summaries and deny raw bodies, subjects, participants, addresses, attachments,
account identifiers, account auth, fetch, send, delete, move, and write.

Required tests/verifiers: contract tests, redaction tests, documentation
integrity.

Safety notes: Metadata-only planning. No email connector runtime.

Blockers/dependencies: Future connector milestone.

### FCC-P1-009 - P1 - Draft-Only Reply Proposal Contract

Epic: Tools/Integrations, Safety/Permissions

Description: Define draft response proposals that can be edited or rejected
but cannot send or mutate an account.

Repo areas likely touched: `src/ultimate_ai_agent/core/`, `tests/`,
`docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`.

Acceptance criteria: Proposal includes safe summary, intent, recipient refs,
evidence refs, and blocked send/write fields.

Required tests/verifiers: contract tests proving send/write/delete/archive
fields are denied.

Safety notes: Draft-only. No connector writes.

Blockers/dependencies: FCC-P1-008.

### FCC-P1-010 - P1 - Relationship And Follow-Up Memory Schema

Epic: Memory/Knowledge, Business Cofounder Workflows

Description: Add reviewed memory schema for profile, project, relationship,
episodic, business, semantic-local knowledge, people, organizations, projects,
deals, promises, and follow-ups.

Repo areas likely touched: `src/ultimate_ai_agent/core/memory/`, `docs/memory/`,
`tests/`.

Acceptance criteria: Records require source/evidence refs, review state,
confidence, correction path, retention/delete/export posture, and no model-output
authority.

Required tests/verifiers: memory tests and redaction tests.

Safety notes: Memory remains recall, not truth or authority. No automatic
capture, no automatic memory writes, and no hidden context injection.

Blockers/dependencies: FCC-P0-005.

### FCC-P1-011 - P1 - Settings Kill-Switch And Feature-Flag Spec

Epic: Safety/Permissions, Product/UX

Description: Specify Settings summary, safe defaults, feature flag posture,
kill-switch posture, and disabled authority boundaries.

Repo areas likely touched: `docs/control_center/`, `docs/strategy/`,
`apps/control-center/src/components/Settings*`, tests after implementation.

Acceptance criteria: Spec names local-only setup, redaction, revocation,
approval, audit, receipt, and rollback requirements for any future setting.

Required tests/verifiers: docs integrity now; frontend/API tests when
implemented.

Safety notes: No authority toggle and no credential collection in this task.

Blockers/dependencies: None for docs-only shaping.

### FCC-P1-012 - P1 - FastAPI Service-Module Extraction Plan

Epic: Core Agent Runtime, Infrastructure/Deployment

Description: Plan route grouping into service modules without route drift.

Repo areas likely touched: `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`,
`src/ultimate_ai_agent/api/app.py`, `src/ultimate_ai_agent/api/manifest.py`,
`tests/test_api_manifest.py` after implementation.

Acceptance criteria: Plan covers system, runtime, planning, approval, memory,
file, evidence, integration, settings, and workflow services. OpenAPI operation
IDs and side-effect classes remain stable.

Required tests/verifiers: OpenAPI contract, API manifest tests, Foundation Gate
after implementation.

Safety notes: Refactor-only until scoped implementation.

Blockers/dependencies: UAA-P1-052 on parent board.

## Backlog

### FCC-P1-014 - P1 - Lead And Follow-Up Tracker Spec

Epic: Business Cofounder Workflows

Description: Define CRM-lite local founder workflow for lead, opportunity,
contact, promise, due window, and next safe action tracking.

Repo areas likely touched: `docs/strategy/`, `docs/memory/`,
`src/ultimate_ai_agent/core/memory/` after implementation.

Acceptance criteria: Tracker uses reviewed local metadata and memory refs; no
connector writes or hidden account sync.

Required tests/verifiers: docs integrity now; memory tests later.

Safety notes: Planning/spec only.

Blockers/dependencies: FCC-P1-010.

### FCC-P1-016 - P1 - First-Party Integration Direction Spec

Epic: Tools/Integrations, Business Cofounder Workflows

Description: Align first-party integration lanes for future contacts lookup
contract planning, task creation proposals, governed article/evidence capture,
GitHub read-only project status, and CRM-lite local lead/follow-up store.

Repo areas likely touched: `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`,
`docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`,
`docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, and `docs/connectors/`.

Acceptance criteria: Each lane stays contract-first with safe refs, redacted
summaries, evidence refs, explicit consent/approval posture where relevant, and
blocked runtime/write states.

Required tests/verifiers: docs integrity now; contract tests only when later
schemas are implemented.

Safety notes: No account auth, connector runtime, contacts read/search/lookup
runtime, connector writes, browser automation, plugin execution, hidden sync, or
production authority.

Blockers/dependencies: Read-only/draft-only MVP proof and separate scoped
connector milestones.

### FCC-P1-015 - P1 - Weekly CEO Review Workflow Spec

Epic: Business Cofounder Workflows, Product/UX

Description: Specify weekly review summary over outcomes, decisions,
follow-ups, blockers, memory corrections, and evidence gaps.

Repo areas likely touched: `docs/strategy/`, `apps/control-center/src/components/`
after implementation.

Acceptance criteria: Review makes no unsupported claims and links to receipts,
evidence refs, and memory review state.

Required tests/verifiers: docs integrity now; frontend tests later.

Safety notes: Summary only. No background automation.

Blockers/dependencies: Morning Briefing and Action Inbox.

### FCC-P2-016 - P2 - Growth And Commercialization Gate

Epic: Growth/Commercialization

Description: Define when UAA can discuss pricing, packaging, public docs, or
external distribution claims.

Repo areas likely touched: `docs/productization/`, `docs/roadmap/`,
`docs/strategy/`.

Acceptance criteria: Gate requires MVP proof, security posture, release
evidence, support expectations, rollback, and no unsafe public claims.

Required tests/verifiers: documentation integrity and release-truth checks.

Safety notes: No commercialization claim by itself.

Blockers/dependencies: Founder Command Center MVP proof.

## Review

No Founder Command Center cards are in Review yet.

## Done

### FCC-P0-001 - P0 - UAA-P1-011 Readable Operator-Loop Baseline

Epic: Core Agent Runtime, Product/UX

Description: Establish the first readable operator-loop proof chain already
named by the parent board: runtime health, local model readiness, UAA `/v1`
chat readiness, plan creation, one safe capability approval path, and
receipt/audit/latency/rollback inspection. This is a baseline for Founder
Command Center work, not completion of the full daily founder loop.

Repo areas likely touched: `apps/control-center/src/components/`,
`apps/control-center/src/App.test.tsx`,
`tests/test_operator_loop_p1_011.py`.

Acceptance criteria: The loop is usable through readable UI states, not raw
JSON. It distinguishes real, mock, skipped, blocked, partial, denied, and
missing prerequisites. No hidden authority is added.

Required tests/verifiers: `make frontend-check`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/test_operator_loop_p1_011.py`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py`,
`PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`,
`.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`.

Safety notes: UI changes remain inspection-only. Backend authority remains
Python Agent Core plus LocalApprovalAuthority through existing routes.

Blockers/dependencies: Broader Founder Command Center IA, real Today/Inbox
surfaces, and deeper product Plans workflows remain separately scoped.

### FCC-DOC-001 - P0 - Founder Command Center Planning Packet

Epic: Product/UX, Testing/Evals

Description: Create the master plan, product principles, MVP spec, Kanban
board, phase 0/1 task list, target architecture, metrics, Codex prompts, and
root AGENTS guidance.

Repo areas likely touched: `docs/strategy/`, `docs/kanban/`,
`docs/implementation/`, `docs/architecture/`, `docs/metrics/`, `docs/codex/`,
`AGENTS.md`, `docs/README.md`, `docs/DOCUMENTATION_INDEX.md`.

Acceptance criteria: Docs are linked from the docs entrypoints and do not
contradict the parent Operator Runtime Excellence board.

Required tests/verifiers: documentation integrity, OpenAPI contract, focused
API tests, Foundation Gate report-only as feasible.

Safety notes: Docs-only. No authority granted.

Blockers/dependencies: None.

## Blocked

### FCC-BLOCK-001 - P0 - Live Email Or Calendar Runtime

Epic: Tools/Integrations

Description: Runtime account access for email/calendar.

Repo areas likely touched: none until scoped.

Acceptance criteria: Requires separate milestone with consent, credential
boundary, account auth posture, read/write scope, redaction, approval,
revocation, audit, tests, and rollback/safe-disable plan.

Required tests/verifiers: not applicable until scoped.

Safety notes: Blocked by design.

Blockers/dependencies: Connector milestone not accepted.

### FCC-BLOCK-002 - P0 - Connector Writes

Epic: Tools/Integrations, Safety/Permissions

Description: Sending email, editing calendar, updating CRM, or writing to an
external account.

Repo areas likely touched: none until scoped.

Acceptance criteria: Requires exact approval, abuse-case tests, revocation,
receipts, idempotency, rollback/safe-disable, and connector-specific policy.

Required tests/verifiers: not applicable until scoped.

Safety notes: Blocked by design.

Blockers/dependencies: Read-only/draft-only MVP proof first.

### FCC-BLOCK-003 - P0 - Broad Shell, Browser, Plugin, Mobile, Or Background Autonomy

Epic: Safety/Permissions

Description: Any unrestricted execution, automation, plugin runtime import,
mobile sensor/control, or autonomous background session.

Repo areas likely touched: none until scoped.

Acceptance criteria: Requires separate scoped milestone and explicit approval
model.

Required tests/verifiers: not applicable until scoped.

Safety notes: Blocked by current repository invariants.

Blockers/dependencies: Not part of Founder Command Center MVP.
