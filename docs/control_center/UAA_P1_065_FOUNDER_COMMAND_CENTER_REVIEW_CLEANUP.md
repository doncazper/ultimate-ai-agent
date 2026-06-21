# UAA-P1-065 Founder Command Center Review/Cleanup Lane

Status: Implemented
Baseline: v0.102.3
Parent lane: M172 Control Center Operator Shell v1
Predecessor: UAA-P1-064 Local Model Inventory Read-Only Backend + CLI
Decision date: 2026-06-21

## Purpose

UAA-P1-065 reconciles the Founder Command Center planning board against the
completed and review-ready slices, removes stale sequencing, and promotes one
next review-ready UI or contract task for a later exact implementation pass.

This milestone is a docs, board, and verification cleanup lane. It keeps the
Founder Command Center product spine pointed at the single-user loop without
adding runtime authority, route behavior, connector behavior, model/provider
calls, or Control Center mutation controls.

## Scope

- Reconcile `docs/kanban/founder_command_center_board.md` against the parent
  `docs/kanban/current_board.md`, the Founder Command Center MVP spec, and the
  implementation task packet.
- Remove or rewrite stale active-sequence language that points at completed
  milestones as future work.
- Classify Founder Command Center cards as implemented/ready-for-review,
  blocked/future, or candidate-next without treating planning language as
  implementation authority.
- Promote exactly one next review-ready UI or contract task for a later exact
  implementation milestone.
- Preserve the current product direction: Today, Inbox, Plans, Actions,
  Memory, Evidence, Settings, Setup Assistant, Action Inbox, Morning Briefing,
  and read-only source contracts.
- Update the smallest relevant board, roadmap, product-truth, recommendation,
  and reconciliation docs.

## Classification Output

Implemented / ready for review:

- FCC-MAC-001 macOS Setup Assistant Hardening
- FCC-P0-002 First Product Loop Readability And Information Architecture
- FCC-P0-004 Action Inbox Contract And UI Skeleton
- FCC-P0-003 Morning Briefing Workflow Skeleton
- FCC-P0-005 Memory Review Inbox Contract And UI Skeleton
- FCC-P1-007 Calendar Read-Only Integration Contract
- FCC-P1-008 Email Metadata Read-Only Contract
- FCC-P1-006 Human-Readable Evidence Timeline
- FCC-P1-009 Draft-Only Email Response Proposal Contract
- FCC-P1-010 Relationship And Follow-Up Memory Schema
- FCC-P1-011 Settings Kill-Switch And Feature-Flag Spec
- FCC-P1-012 FastAPI Service-Module Extraction Plan

Candidate-next:

- FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core Surfaces

Blocked / future:

- FCC-P1-014 Lead And Follow-Up Tracker Spec
- FCC-P1-016 First-Party Integration Direction Spec
- FCC-P1-015 Weekly CEO Review Workflow Spec
- FCC-P2-016 Growth And Commercialization Gate
- Live email or calendar runtime
- Connector writes
- Broad shell, browser, plugin, mobile, or background autonomy

## Promoted Next FCC Task

UAA-P1-065 promotes exactly one later FCC implementation candidate:

```text
FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core Surfaces
```

Task type: frontend read-only product-surface organization.

Reason: the primary Founder Command Center IA is already implemented, and this
follow-up is the smallest review-ready UI/readability task that improves the
first product loop without adding route authority or mutation behavior.

Scope for the later exact milestone:

- Today, Inbox, Plans, Actions, Memory, Evidence, and Settings remain the
  primary product workflow.
- Legacy review surfaces become supporting detail rather than first-order loop
  steps.
- Existing operator/review routes remain reachable.
- Route truth, side-effect classes, authority boundaries, and blocked states
  stay visible.

This task is not implemented by UAA-P1-065. It requires a later exact milestone
before any product code changes.

## Required Behavior

- The parent Operator Runtime Excellence board remains the authority for the
  active milestone sequence.
- The Founder Command Center board remains subordinate planning guidance.
- Every promoted future task must state whether it is docs-only, contract-only,
  frontend read-only, backend read-only, validation-only, or blocked.
- Any future task that would require routes, OpenAPI changes, persistence,
  approval capture, connector access, setup mutation, model/provider output, or
  runtime authority must explicitly stop until a later scoped milestone grants
  that work.

## Non-Goals

- No backend routes.
- No OpenAPI operation changes.
- No Control Center implementation work.
- No React-only product behavior.
- No approval grant capture, denial capture, or mutation controls.
- No setup mutation, installer execution, LaunchAgent behavior, shell or
  subprocess execution, model download, or background service control.
- No email/calendar connector runtime, account auth, source fetch, send, write,
  archive, delete, or notification delivery.
- No model/provider calls, web fetching, browser automation, plugin runtime
  import, connector writes, mobile control, remote execution, public
  distribution, or production authority.

## Verification Commands

```bash
.venv/bin/python scripts/verify_uaa_p1_065_founder_command_center_review_cleanup.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
.venv/bin/python scripts/verify_morning_reconciliation_artifact.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_065_founder_command_center_review_cleanup.py
git diff --check
```

## Stop And Ask Conditions

Pause before implementation if the work appears to require product code,
backend routes, frontend controls, source connector access, setup mutation,
model runtime behavior, shell/subprocess behavior, raw private evidence, or a
claim that any Founder Command Center workflow is complete beyond the evidence
already accepted in the docs.
