# Founder Command Center Phase 0/1 Tasks

Status: planning and task-breakdown artifact
Parent board: `docs/kanban/founder_command_center_board.md`

These tasks are designed for future scoped Codex branches/PRs. This document
does not implement workflows, add runtime authority, change the API boundary,
or add dependencies. Most tasks should land as small PRs with tests before
product claims change.

## Task 1 - FCC-P0-001 Capture UAA-P1-011 Readable Baseline

Type: full-stack

Current status: baseline implemented as a readable Operator Loop proof chain.
Future work should extend from this baseline instead of treating UAA-P1-011 as
the complete Founder Command Center daily loop.

New authority: no broad authority. Any safe capability action must use existing
scoped PolicyEngine and LocalApprovalAuthority boundaries.

Acceptance criteria:

- Control Center exposes the UAA-P1-011 loop as readable product flow.
- Runtime health, local model readiness, UAA `/v1` chat readiness, plan
  creation, safe capability approval, and receipt/audit/latency/rollback
  inspection are visible.
- Real, mock, skipped, blocked, denied, partial, and missing states remain
  distinct.
- No raw JSON is the primary UI.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `tests/test_operator_loop_p1_011.py`
- `tests/test_control_center_api_routes.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`

Likely files touched:

- `apps/control-center/src/components/OperatorLoopPanel.tsx`
- `apps/control-center/src/components/OperatorFlowPanels.tsx`
- `apps/control-center/src/api/client.ts`
- `apps/control-center/src/api/types.ts`
- `src/ultimate_ai_agent/core/task_decomposition/`
- `src/ultimate_ai_agent/api/app.py`

PR size: one PR if it binds existing routes only; split backend aggregation and
frontend UI if new route contracts are required.

## Task 2 - FCC-P0-002 Create Founder Command Center IA

Type: frontend/docs

New authority: no.

Acceptance criteria:

- Primary navigation or grouped route model is shaped around Today, Inbox,
  Plans, Actions, Memory, Evidence, and Settings.
- Existing operator/review routes remain reachable.
- Surface copy names readiness and blocked states accurately.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `scripts/verify_control_center_frontend.py` if product-language checks need
  new expected routes.

Likely files touched:

- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/App.tsx`
- `apps/control-center/src/App.test.tsx`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`

PR size: one frontend PR.

## Task 3 - FCC-P0-003 Collapse/Organize Control Center Around Core Surfaces

Type: frontend

New authority: no.

Acceptance criteria:

- Today, Inbox, Plans, Actions, Memory, Evidence, and Settings appear as the
  primary product workflow.
- Legacy review surfaces are grouped as supporting detail rather than
  first-order product loop steps.
- No existing route tests lose coverage.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/components/*Navigation*`
- `apps/control-center/src/styles.css`

PR size: one frontend PR after Task 2.

## Task 4 - FCC-P0-004 Implement Morning Briefing Workflow Skeleton

Type: frontend with possible backend aggregation later

New authority: no.

Acceptance criteria:

- Today/Morning Briefing shows priorities, blockers, next safe actions,
  evidence gaps, and review counts.
- It uses existing summaries or safe mock fixtures.
- It does not fetch email/calendar or generate background content.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/components/MorningBriefingPanel.tsx`
- `apps/control-center/src/components/TodaySurfacePanel.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts`
- `apps/control-center/src/api/types.ts`

PR size: one frontend PR. Add backend aggregation only in a later scoped PR.

## Task 5 - FCC-P1-007 Add Calendar Read-Only Integration Contract

Type: backend contract/test/docs

New authority: no.

Acceptance criteria:

- Calendar event metadata contract exists with safe refs and redacted summary
  fields only.
- Contract denies account auth, network fetch, calendar write, background
  collection, raw event body storage, and connector runtime.
- Docs say this is contract-only.

Tests to add/update:

- New focused contract tests under `tests/`.
- `.venv/bin/python scripts/verify_documentation_integrity.py`

Likely files touched:

- `src/ultimate_ai_agent/core/` new connector/planning module or existing
  connector package if present.
- `docs/connectors/`
- `tests/`

PR size: one backend contract PR.

## Task 6 - FCC-P1-008 Add Email Metadata Read-Only Integration Contract

Type: backend contract/test/docs

New authority: no.

Acceptance criteria:

- Email metadata envelope supports safe sender/thread/time/label summary refs.
- Contract denies raw body, attachment download, account auth, email fetch,
  send, delete, archive, label write, and connector runtime.

Tests to add/update:

- New focused contract tests under `tests/`.
- Redaction regression tests for unsafe body-like fields.

Likely files touched:

- `src/ultimate_ai_agent/core/`
- `docs/connectors/`
- `tests/`

PR size: one backend contract PR.

## Task 7 - FCC-P1-009 Add Draft-Only Email Response Proposal Contract

Type: backend contract/test/docs

New authority: no.

Acceptance criteria:

- Draft proposal includes safe recipient refs, purpose, evidence refs, draft
  summary ref, review state, expiry, and rejection/edit state.
- Send/write/delete/archive fields are denied.
- Proposal output cannot authorize connector writes.

Tests to add/update:

- Contract tests for allowed draft proposal.
- Denial tests for send/write/delete/archive fields.

Likely files touched:

- `src/ultimate_ai_agent/core/`
- `tests/`
- `docs/connectors/`

PR size: one backend contract PR after Task 6.

## Task 8 - FCC-P0-004 Add Action Inbox Schema And UI

Type: full-stack if schema lands in Python; frontend-only if using mock-safe
fixtures first

New authority: no.

Acceptance criteria:

- Action cards show title, safe summary, route refs, side-effect class, risk,
  approval requirement, evidence refs, idempotency, expiry, and rollback or
  safe-disable posture.
- Approve/edit/reject controls are clearly review-only unless exact backend
  grant binding exists.

Tests to add/update:

- Python schema tests if contract is added.
- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `src/ultimate_ai_agent/core/`
- `apps/control-center/src/components/ActionInboxPanel.tsx`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/mocks/controlCenterData.ts`

PR size: split into contract PR and UI PR if Python schema is added.

## Task 9 - FCC-P0-005 Add Memory Review Inbox Schema And UI

Type: full-stack

New authority: no automatic memory write.

Acceptance criteria:

- Memory candidates include provenance, source refs, evidence refs, review
  state, correction state, confidence, retention/delete posture, and safe
  summary.
- Accept/correct/reject states are review states until existing memory write
  policy is explicitly bound.

Tests to add/update:

- Memory contract tests.
- `apps/control-center/src/App.test.tsx`
- Redaction/export tests if memory output changes.

Likely files touched:

- `src/ultimate_ai_agent/core/memory/`
- `apps/control-center/src/components/MemoryReviewInboxPanel.tsx`
- `apps/control-center/src/api/types.ts`
- `tests/test_memory*.py`

PR size: split contract and UI if needed.

## Task 10 - FCC-P0-003 Add Product E2E Test For Morning Briefing

Type: test-only

New authority: no.

Acceptance criteria:

- Test proves Morning Briefing renders priorities, blockers, next safe action,
  evidence gap, and review count.
- Test proves no send/run/approve/mutate button is exposed by the briefing.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/App.test.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts` if fixtures are needed.

PR size: one test PR or bundled with Task 4.

## Task 11 - FCC-P1-009 Add Product E2E Test For Draft-Only Email Flow

Type: test-only

New authority: no.

Acceptance criteria:

- Test proves draft-only flow renders safe metadata and draft proposal state.
- Test proves no send/archive/delete/account-write button exists.
- Test proves blocked connector-runtime state is visible.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- Contract tests from Tasks 6 and 7 if backend contracts exist.

Likely files touched:

- `apps/control-center/src/App.test.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts`

PR size: one test PR after draft-only UI exists.

## Task 12 - FCC-P1-012 Plan FastAPI Service-Module Extraction

Type: docs-only first

New authority: no.

Acceptance criteria:

- Plan maps routes to `system_service`, `runtime_service`,
  `planning_service`, `approval_service`, `memory_service`, `file_service`,
  `evidence_service`, `integration_service`, `settings_service`, and
  `workflow_service`.
- Plan requires no route drift, stable operation IDs, side-effect class
  preservation, API manifest truth, and Foundation Gate coverage.

Tests to add/update:

- None for docs-only beyond documentation integrity.

Likely files touched:

- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- Possibly `docs/api/README.md`

PR size: one docs PR.

## Task 13 - FCC-P1-006 Build Human-Readable Evidence Timeline

Type: frontend first; backend aggregation later if scoped

New authority: no.

Acceptance criteria:

- Timeline displays receipts, audits, task events, latency, Foundation Gate,
  and rollback status as readable safe summaries.
- Raw evidence is not displayed as the primary UI.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- Redaction tests if new backend records are added.

Likely files touched:

- `apps/control-center/src/components/EvidenceTimelinePanel.tsx`
- `apps/control-center/src/components/EventTimelineTracePanel.tsx`
- `apps/control-center/src/api/types.ts`

PR size: one frontend PR.

## Task 14 - FCC-P1-013 Add Local Setup/Onboarding Wizard Spec

Type: docs-only first

New authority: no.

Acceptance criteria:

- Spec covers prerequisite checks, loopback API, Control Center, local model
  readiness, OpenWebUI shell configuration, safe evidence, blocked states, and
  rollback/safe-disable guidance.
- Spec denies installer, signing, background agent, credential collection, and
  public distribution claims.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/developer/`
- `docs/macos/`
- `docs/strategy/`

PR size: one docs PR.

## Task 15 - FCC-P1-011 Add Settings Surface Spec With Kill Switch And Feature Flags

Type: docs-only first

New authority: no.

Acceptance criteria:

- Spec names feature flag state, kill-switch state, disabled boundaries, audit
  refs, revocation refs, rollback/safe-disable refs, and approval needs.
- Spec says no credential collection and no authority toggle in current UI.

Tests to add/update:

- Documentation integrity.
- Frontend tests when implemented.

Likely files touched:

- `docs/control_center/`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`

PR size: one docs PR.

## Task 16 - FCC-P1-011 Define Scoped Permission Modes

Type: docs/backend contract later

New authority: no. This task may document planning labels and future contract
requirements only. It must not create approval refs, standing grants, enabled UI
controls, backend routes, mutating settings, runtime sessions, connector writes,
background jobs, revocation actions, or kill-switch actions.

Acceptance criteria:

- Modes distinguish inspect-only, draft-only, approval-required local mutation,
  governed read-only evidence, and blocked high-risk scopes.
- Planning names are explicit and shared by product surfaces: Observe, Draft,
  Propose, Approve once, Approve rule, Autopilot micro-scope, and Kill switch.
- Modes bind to PolicyEngine, LocalApprovalAuthority, side-effect class, audit,
  receipt, revocation, and rollback requirements.
- Naming a mode does not grant runtime authority.
- Approval-like mode names do not create approval refs, standing grants,
  background sessions, connector writes, execution rights, revocation actions, or
  kill-switch actions.
- Definitions must stay aligned with the MVP spec, target architecture, and
  Codex prompt vocabulary.

Tests to add/update:

- Docs integrity for planning.
- Policy/approval tests only if contracts are implemented.

Likely files touched:

- `docs/approvals/`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- `docs/codex/CODEX_EXECUTION_PROMPTS.md`
- `docs/control_center/`
- `src/ultimate_ai_agent/core/approvals/` in a later contract PR.

PR size: docs PR first; backend contract PR later.

## Task 17 - FCC-P1-010 Add Relationship/Follow-Up Memory Schema

Type: backend contract/test

New authority: no automatic memory write.

Acceptance criteria:

- Schema covers person, organization, project, deal, promise, due window,
  follow-up state, source refs, evidence refs, correction state, retention
  posture, and confidence.
- Model/provider output cannot authorize memory truth.

Tests to add/update:

- New memory schema tests.
- Redaction tests for unsafe names or secret-like values if applicable.

Likely files touched:

- `src/ultimate_ai_agent/core/memory/`
- `tests/test_memory*.py`
- `docs/memory/`

PR size: one backend contract PR.

## Task 18 - FCC-P1-014 Add Lead/Follow-Up Tracker Spec

Type: docs-only first

New authority: no.

Acceptance criteria:

- Spec maps lead/opportunity/follow-up states to reviewed memory and action
  proposals.
- Spec denies connector writes, CRM writes, and hidden sync.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/strategy/`
- `docs/memory/`
- `docs/connectors/`

PR size: one docs PR.

## Task 19 - FCC-P1-013 Add One-Command Local Launcher Task

Type: infrastructure/docs, possible dev-script hardening

New authority: no production or broad runtime authority.

Acceptance criteria:

- Existing local launcher guidance has one clear command path for loopback-only
  API and Control Center dev startup.
- Generated local state remains under ignored `.uaa/` paths.
- Docs distinguish local dev launcher from installer or public distribution.

Tests to add/update:

- `make doctor`
- Existing launcher tests if scripts change.
- Documentation integrity.

Likely files touched:

- `docs/developer/LOCAL_LAUNCHER.md`
- `scripts/dev/README.md`
- `Makefile` if adding a wrapper target
- `tests/test_dev_launcher.py` if script behavior changes.

PR size: one small infra/docs PR.

## Task 20 - FCC-DOC-002 Add 3-Minute Product Demo Script/Checklist

Type: docs-only

New authority: no.

Acceptance criteria:

- Checklist demonstrates the current safe product loop without unsupported
  claims.
- It names prerequisites, expected blocked states, safe evidence refs, tests to
  run, and rollback/safe-disable review.
- It does not claim public distribution, public beta, broad autonomy, or
  unrestricted authority.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/strategy/`
- `docs/control_center/`
- `docs/testing/`

PR size: one docs PR, ideally after Tasks 1-4.
