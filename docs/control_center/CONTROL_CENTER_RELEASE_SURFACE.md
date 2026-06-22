# Control Center Release Surface

Status: FCC-V1-000 implemented as release-surface truth and verifier coverage.
This document and `docs/control_center/release_surface_manifest.json` add no
backend route, runtime authority, connector write, memory write, action
execution, provider/model call, browser automation, public distribution, or
production authority.

The release surface manifest is the promotion gate for every visible Control
Center route. It records what the route can truthfully claim today and what
proof is required before the route can be promoted.

## Status Vocabulary

The status vocabulary is exactly:

- `ship`: route behavior is backend-owned, tested, evidence-backed, not
  React-only, and no required product behavior remains blocked for that route.
- `partial`: useful backend or proof exists, but the route is not a complete
  product workflow.
- `blocked`: the visible route is present, but required backend contracts,
  proof lanes, or authority boundaries are missing.
- `experimental`: mock, preview, packet, scaffold, local UI state, or
  proof-of-shape only. This status is not release proof.

At FCC-V1-000, no route was promoted to `ship`. FCC-V1-007 later proofed only
the `/actions`, `/chat`, `/memory`, and `/evidence` route surfaces for their
exact backend-owned behavior. Other routes remain partial, blocked, or
experimental until a later scoped milestone supplies the missing
receipt-bearing workflow proof.

## Promotion Rules

A visible route cannot be promoted to `ship` unless all of these are true:

- Product behavior is owned by the Python Agent Core/API contract, not only by
  React state.
- The route has backend route refs or an explicitly documented no-backend proof
  rationale accepted by a later scoped milestone.
- Relevant proof lanes are present and run cleanly.
- Evidence uses safe refs, redacted summaries, bounded previews, and explicit
  blocked states only.
- Mutating behavior is exact-scoped, idempotent, approval-bound where required,
  receipt-backed, rollback-aware or safe-disable-aware, and tested.
- The manifest has no blocked capability that is required for the route's
  claimed product behavior.
- The route does not imply public distribution, production readiness,
  production authority, broad runtime execution, connector writes, memory
  writes, or model/provider authority.

Promotion must update both `apps/control-center/src/routes.tsx` and
`docs/control_center/release_surface_manifest.json`. The verifier fails if the
UI route release status and manifest status drift.

## Current Scope

FCC-V1-000 makes route truth reviewable and durable. It does not complete full
UAA-P1-087.2 manual UI testing and does not answer the UAA-P1-087.2c manual
review scaffold. Those answers remain pending until a later local/manual
review milestone records accepted or revised findings.

FCC-V1-001 API Perimeter For Real Mutations is complete as contract/verifier
coverage. Duplicate replay runtime remains blocked until route-owner receipt
storage exists outside routes that implement their own receipt-backed replay.
FCC-V1-002 Action Inbox Backend State Machine is complete for decision state
and receipt refs without action execution. FCC-V1-003 Founder Loop V1 Vertical
Slice is complete for the first Today-to-Action envelope receipt loop,
Evidence Timeline update, and CLI inspection path without action execution.
FCC-V1-004 Chat Durable Receipt And Handoff is complete for safe Chat turn
receipts and reviewable Actions/Plans handoff receipts without action
execution, memory writes, model-output authority, connector writes, or
provider calls. FCC-V1-005 Memory Review Decisions is complete for
backend-owned accept/correct/reject receipts. FCC-V1-006 Evidence Timeline
Productization is complete for the backend-owned timeline index. FCC-V1-007
Promotion And Proof Lane is complete for proofing only `/actions`, `/chat`,
`/memory`, and `/evidence`; `/today`, `/inbox`, `/settings`, model lifecycle,
product-readiness claims, public beta, public distribution, and production
authority remain outside this release-surface proof.
