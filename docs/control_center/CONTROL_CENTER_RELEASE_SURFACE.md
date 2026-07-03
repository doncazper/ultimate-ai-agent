# Control Center Release Surface

Status: FCC-V1-000 implemented as release-surface truth and verifier coverage.
This document and `docs/control_center/release_surface_manifest.json` add no
backend route, runtime authority, connector write, memory write, action
execution, provider/model call, browser automation, public distribution, or
production authority.

The release surface manifest is the promotion gate for every visible Control
Center route. It records what the route can truthfully claim today and what
proof is required before the route can be promoted.

## Proof Chain Fields

Every visible route in `docs/control_center/release_surface_manifest.json`
must carry the full proof chain below:

- Route path, label, group, UI status, release status, and owner copied from
  the active Control Center route metadata.
- Backend route refs or an explicit `no-backend-route:*` rationale. A
  no-backend rationale is a blocked/planned posture, not a runtime permission.
- Side-effect class, route classification, and approval posture for the
  referenced backend contracts.
- Proof lanes and evidence refs that use repo-local, redacted artifacts only.
- Visual proof status, visual baseline ref, and visual rationale. Routes with
  checked-in redacted desktop/mobile baselines must match
  `docs/control_center/visual_regression_manifest.json`; routes without a
  checked-in baseline must say whether the visual gap is blocked or
  experimental.
- Blocked capabilities, promotion criteria, and product-language caveats that
  keep public distribution, release, production authority, connector writes,
  provider/model calls, browser execution, memory/context injection, and broad
  runtime claims out of route truth.

The verifier fails on missing visible routes, unknown statuses, missing proof
lanes, missing visual baseline refs or missing no-baseline rationales, backend
status drift, raw evidence fragments, unsupported release claims, and schema
drift.

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
- The route has visual proof: either a checked-in redacted baseline referenced
  by the visual regression manifest, or an explicit blocked/experimental
  no-baseline rationale.
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
and product-readiness claims remain outside this release-surface proof. CRM M1
adds `/crm` only as a fixture-only blocked shell; backend CRM read models,
backend CRM routes, connector runtime, writes, sends, calendar writes,
provider/model calls, live web, browser automation, public beta, public
distribution, and production authority remain outside this release-surface
proof.

Usable Authority PR 02 adds `/start` as a partial Start Here surface backed by
`GET /control-center/start-here/summary`. It is a local read-model entry point
for one governed daily loop and does not grant action execution, provider/model
calls, connector writes/sends, browser or shell execution, background autonomy,
public release, or production authority.

Usable Authority PR 03 adds `/proof` as a partial universal Proof Detail
surface backed by `GET /control-center/proof/index` and
`GET /control-center/proof/{proof_ref}`. It is a read-only inspection surface
for safe refs, receipts, evidence refs, approval refs, rollback/safe-disable
refs, redaction posture, and blocked authority refs only; it does not grant
approval, action execution, provider/model calls, connector writes/sends,
browser or shell execution, background autonomy, public release, or production
authority.

Usable Authority PR 04 hardens `/actions` as a backend-owned Action Inbox work
queue with safe lane counts, next-item posture, proof/receipt/evidence refs,
CLI inspection, and the exact `local_task_create` local task record lane. It
does not grant generic action execution, provider/model calls, connector
writes/sends, browser or shell execution, memory writes, context injection,
external side effects, rollback execution, public release, or production
authority.

Usable Authority PR 05 binds Evidence and Memory into the daily loop through a
backend-owned Evidence/Memory loop binding read model exposed from Today,
Memory Review, Evidence Timeline, Proof Detail, and
`scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding`. The binding
uses safe refs to explain why memory appeared, which evidence supports it, and
which action/run/proof refs connect the loop. It does not make memory truth,
inject context, write memory automatically, delete or export memory, execute
actions, call providers/models, write/send connectors, run browser or shell
work, start background autonomy, or grant production authority.
