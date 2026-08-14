# FCC-LOOP-003 Review-Stage Readability Implementation Plan

Status: proposed planning-only refinement

Parent board: `docs/kanban/founder_command_center_board.md`

Dependencies:

- `FCC-TODAY-RENDER-001` must first establish the accepted Today composition
  and product language.
- The existing Today, Plans-to-Actions, Action Inbox, receipt, Evidence
  Timeline, and route-state read models remain the only product-data sources.

Research basis: comparative review of the open Grok Build harness and TUI. The
useful input is its readable review-stage ergonomics; this plan does not copy
Grok Build source, prompts, runtime, policies, extensions, telemetry, or model
assets.

## Objective

Make the current Founder Command Center loop easier to scan as one review
journey:

```text
proposal -> exact review required -> recorded decision -> receipt or explicit block
```

The primary operator should be able to see why an item is present, its exact
scope and risk, what evidence or approval is missing, and the next safe action
before opening technical detail. Existing route, receipt, evidence, and
authority inspection remains available as progressive disclosure.

## Scope

This is a frontend composition and product-language pass over existing
backend-owned safe-ref read models. It may extract shared presentational
components and add focused frontend/visual coverage. It does not require a new
route, storage field, API schema, OpenAPI operation, or runtime capability.

If the current backend data cannot determine a displayed lifecycle state
without inference, the UI must display `unavailable` rather than derive a
state. A separately scoped, Python-owned read-model addition would be required
before continuing that portion of the work.

## Authority And Safety Boundary

`FCC-LOOP-003` grants no authority. In particular, it must not add or change:

- action, tool, workflow, shell/subprocess, browser, connector, plugin, MCP,
  remote, scheduler, or background execution;
- provider/model calls, model-output authority, local-model lifecycle, or
  cost/billing behavior;
- approval-grant capture, AuthorityLease issuance, approval shortcuts, or
  client-side eligibility/authority inference;
- memory writes, context injection, raw instruction loading, or raw evidence
  display;
- telemetry export, cloud traces, uploaded artifacts, new dependencies,
  public-beta/distribution, or production-readiness claims.

React may retain only presentation state such as the expanded card, selected
queue group, and active detail tab. Python Core remains authoritative for every
decision, lifecycle fact, route state, and receipt.

## Current Building Blocks

| Need | Existing source of truth | Planned treatment |
| --- | --- | --- |
| Plan proposal and link to Action Inbox | `FounderLoopPlansToActionsBridgeReadModel` | Condense first-read fields into a Plan Review Digest; retain complete bridge detail. |
| Exact scope, risk, side effect, approval, expiry, idempotency, cost, rollback, evidence, and blockers | `FounderLoopActionApprovalEnvelope` | Put decision-critical items before secondary implementation metadata. |
| Recorded decision, replay/conflict posture, AuthorityLease and Evidence Timeline refs | `FounderLoopActionReceiptVisibility` and receipt route | Render a post-decision proof section, never permission to act. |
| Today priority and next-safe-action context | `FounderLoopTodaySummary` | Surface compact links into existing plan/action review state. |
| Safe history | Evidence Timeline read model | Link by safe event ref; do not create client-owned history. |
| Fallback/degraded state | Existing route-state and backend-owned checks | Preserve `unavailable`, `partial`, and `blocked`; never fill gaps from mock data. |

## Experience Design

### Review-stage rail

Each authoritative Plan or Action item may show one backend-backed stage:

1. **Proposed** — a reviewable plan/action exists but has no recorded decision.
2. **Review required** — an existing decision posture is available and the
   item needs an approve/edit/reject/defer review.
3. **Decision recorded** — an existing receipt ref confirms the decision.
4. **Blocked or stale** — backend state identifies a blocker, expiry, missing
   evidence, unavailable envelope, or unavailable receipt.

This is a display grammar, not a new domain lifecycle. Stage labels must map
only to existing backend values and refs. Never derive a positive state from a
missing field, optimistic POST response, mock fixture, or browser state.

### First-read hierarchy

The default card layout should contain, in this order:

1. Plain-language safe summary and `why proposed` context.
2. Stage label and the exact next safe action.
3. Exact scope, risk class, approval requirement, and expiry/staleness.
4. Evidence/missing-evidence and rollback/safe-disable posture.
5. A link/ref to the appropriate Action Inbox, receipt, and Evidence Timeline
   detail when those backend refs exist.

Secondary items—route refs, provider/cost details, task-decomposition refs,
authority receipt fields, conflict/replay posture, and all blocker lists—move
to an expandable **Review detail** section. They remain visible and searchable;
they are not discarded or rewritten into raw JSON.

### Truthful unavailable state

When a required backend read model is absent, non-authoritative, or degraded,
the card must say which review surface is unavailable and direct the operator to
the current next-safe action. It must not show a completed stage, active
authority, receipt eligibility, or mutation control from a fallback fixture.

## Delivery Sequence

### Slice A — field inventory and reusable display primitives

Type: frontend/test; no route or contract change.

1. Inventory existing authoritative Plan, Action Envelope, and Receipt
   Visibility fields used on `/today`, `/plans`, and `/actions`.
2. Define a small, pure presentation mapper that accepts already validated
   frontend types and can return `unavailable`; it cannot inspect raw payloads
   or manufacture authority.
3. Extract shared `ReviewStageRail`, `ReviewDigest`, and `ReviewDetail`
   components from `FounderLoopPanels.tsx`, retaining authoritative guards.
4. Test the mapper and components against authoritative, blocked, stale,
   unavailable, and mock/degraded fixtures.

Likely files:

- `apps/control-center/src/components/FounderLoopPanels.tsx`
- small presentational components under `apps/control-center/src/components/`
- `apps/control-center/src/App.test.tsx`
- focused component tests adjacent to extracted components

Acceptance:

- No new API client call, endpoint, route, or persisted state.
- An unavailable/mocked envelope or receipt cannot produce a review-ready or
  decision-recorded display.
- Components expose safe labels/refs only and retain current redaction
  boundaries.

### Slice B — Plans and Action Inbox composition

Type: frontend/test; no authority change.

1. Apply the digest and review-stage rail to `/plans` and the Plan-to-Actions
   bridge.
2. Apply the same hierarchy to Action Inbox cards, showing the existing
   envelope and receipt cards as progressive detail rather than duplicating
   their backend facts in new React state.
3. Preserve all supported approve/edit/reject/defer and exact local-task
   controls exactly where existing backend-owned guards permit them. This slice
   does not add controls or change eligibility.
4. Do not move a card locally after a decision until the existing Action Inbox
   reconciliation confirms the backend-owned state.

Acceptance:

- An operator can compare scope, risk, approval, expiry, evidence, and
  rollback/safe-disable posture without opening every metadata list.
- Existing receipt, AuthorityLease, and Evidence Timeline details remain
  reachable using safe refs.
- Mock/degraded cards stay visibly non-authoritative and cannot expose local
  task commit readiness.

### Slice C — Today and Evidence wayfinding

Type: frontend/visual test; no backend aggregation.

1. On Today, add compact, non-mutating wayfinding from priority/briefing
   items to an existing plan or Action Inbox review surface when a safe ref
   already exists.
2. On Evidence, display an existing lifecycle label/ref as history context;
   do not synthesize event content or new timeline records.
3. Confirm desktop and mobile layouts retain the accepted Today fidelity
   established by `FCC-TODAY-RENDER-001`.

Acceptance:

- Today remains a calm daily starting surface, not a dense diagnostics table.
- Evidence remains redacted, safe-ref history only.
- No route link implies a source refresh, action, or approval.

## Verification Plan

Run focused checks per slice, then the appropriate full frontend/documentation
checks:

```bash
cd apps/control-center && npm test -- --run
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

Add focused assertions for:

- authoritative versus mock/degraded Plan, envelope, and receipt rendering;
- proposed, review-required, decision-recorded, blocked/stale, and unavailable
  display states;
- no new mutation control or client-owned authority state;
- visible safe next action, exact scope, risk, approval, expiry, evidence, and
  rollback/safe-disable posture;
- retained safe receipt/Evidence Timeline detail;
- desktop/mobile visual coverage after the accepted Today render is restored.

No OpenAPI or API-manifest check is required unless implementation deliberately
and separately scopes a backend contract change. If that happens, stop this
frontend plan and create a new Python Core/API plan with route side-effect,
OpenAPI, CLI-parity, redaction, and focused verifier coverage.

## Definition Of Done

- Plans and Actions are legible as a single review journey without hiding
  backend truth.
- Default cards lead with decision-critical safe facts; supporting technical
  detail is progressively disclosed.
- Backend-owned and non-authoritative states remain clearly distinct.
- Existing decision and exact local-task controls neither broaden nor become
  easier to invoke without their current backend checks.
- Tests and visual checks demonstrate the same boundary on desktop and mobile.
- Documentation identifies this as a readability pass, not a new
  action-execution or automation capability.

## Explicit Non-Goals And Deferred Ideas

The Grok Build review also surfaced future-only ideas: immutable sandbox
snapshots, typed read-only delegation roles, and extension provenance review.
They are not part of this plan. UAA already has separate profile-isolation and
inspectable-extension-catalog read models; any execution, sandbox, plugin,
MCP, or delegation promotion needs its own exact AuthorityLease, receipt,
idempotency, rollback/safe-disable, redaction, Core/API/CLI parity, and
verifier plan.
