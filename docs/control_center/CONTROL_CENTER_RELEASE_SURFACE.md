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
Slice is complete for the first active `workspace/draft` AuthorityLease-gated
Today-to-Action envelope receipt loop, Evidence Timeline update, and CLI
inspection path without action execution.
FCC-V1-004 Chat Durable Receipt And Handoff is complete for safe Chat turn
receipts and reviewable Actions/Plans handoff receipts without action
execution, memory writes, model-output authority, connector writes, or
provider calls. FCC-V1-005 Memory Review Decisions is complete for
backend-owned accept/correct/reject receipts. FCC-V1-006 Evidence Timeline
Productization is complete for the backend-owned timeline index. FCC-V1-007
Promotion And Proof Lane is complete for proofing only `/actions`, `/chat`,
`/memory`, and `/evidence`; `/today`, `/inbox`, `/settings`, model lifecycle,
and product-readiness claims remain outside this release-surface proof. CRM
Local Command Center M2 makes `/crm` a partial backend-owned local CRM surface
over Python-core read routes, CLI inspection, local storage posture, redacted
import/export preview, deterministic proposal refs, and one exact local
mutation receipt lane. Connector runtime, external CRM writes, account sync,
sends, calendar writes, provider/model calls, live web, browser automation,
public beta, public distribution, production readiness, and production
authority remain outside this release-surface proof.

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

Beta 08 Web Evidence beta slice hardens the Proof Web Evidence path as a real
Tier 1 lane without widening authority. Full-strength Web Evidence should
eventually support useful real-world evidence, richer source review, and later
browser/web workflows under separate gates. The repo-safe current version uses
`POST /control-center/web-evidence/attach` and
`scripts/dev/uaa_founder_loop.py attach-web-evidence` for one configured host
allowlist HTTPS GET through WebAccessGateway after an active Browser/read
AuthorityLease decision; the redacted preview is returned transiently to the
requester, while durable Today/Evidence/Proof/CLI surfaces store safe refs,
authority decision refs, request-ref idempotency posture, rollback/safe-disable
refs, and a redacted WebAccessGateway audit summary only.
Blocked/needs-authority remains browser actions, auth/cookies,
downloads/uploads, POST-style mutation, raw URL/body/header persistence,
context injection, memory writes, provider/model calls, connector writes,
public release, and production authority. Exact promotion requires a later
verifier-backed PR with exact
scope, configured policy, approval binding if mutation appears, redaction,
receipt/proof evidence, safe-disable, rollback, CLI/API parity, docs, and
tests. Verification:
`scripts/verify_beta_08_web_evidence_product_slice.py`. No broad runtime
authority is added.

Beta 09 Provider Draft/Summarize preview keeps `/proof` and `/trust` as
inspection surfaces for the exact core/CLI provider draft lane. Full-strength
provider drafting remains a later approved live-credential workflow. The
repo-safe current version exposes proof refs, CLI refs, safe-disable refs,
blocked-authority refs, and fixture-proven posture only; it adds no provider
draft API route, Control Center provider-call button, default live provider
network, durable draft preview persistence, provider SDK call, raw
prompt/response/provider exchange persistence, memory/context injection,
connector write, action execution, background provider call, public release, or
production authority. Verification:
`scripts/verify_beta_09_provider_draft_preview.py`. No broad runtime authority
is added.

Beta 10 Connector Draft-Only keeps `/inbox`, `/proof`, and `/trust` as
inspection surfaces for embedded backend-owned connector draft proposal refs.
Full-strength connector drafting remains a later approved connector runtime,
send/write/sync workflow with exact account and target scope. The repo-safe
current version exposes Source Readiness refs, Proof refs, Trust refs, CLI
refs, safe-disable refs, rollback refs, blocked-authority refs, and
metadata-only draft posture only; it adds no standalone connector draft route,
connector send/write/sync/OAuth control, account connection, auth-material
collection, delivery worker, provider/model call, memory/context injection,
background runtime, public release, or production authority. The older M128
low-risk connector write contract remains outside this beta-10 release surface
and is not wired to the draft-only lane. Verification:
`scripts/verify_beta_10_connector_draft_only.py`. No broad runtime authority is
added, and no connector send/write is exposed by beta-10.

Beta 11 Operator Workspace Spine keeps Today, Proof, and Trust as
inspection surfaces for a backend-owned workspace spine read model. The
full-strength version should become a useful operator cockpit for workspace
status, Git posture, preview status, run logs, and coworker handoff state. The
repo-safe current version exposes only safe refs from
`GET /control-center/today/summary#operator_workspace_spine`,
`proof-ref:operator-workspace-spine:read-model`,
`trust-lane:operator-workspace-spine`, and
`python scripts/inspect_operator_workspace_spine.py`; it adds no editor,
terminal, file write, patch apply, no Git mutation, shell/subprocess
execution, browser automation, dev-server lifecycle control, provider/model
call, connector write, coworker dispatch, background autonomy, raw path/log
persistence, public release, or production authority. Verification:
`scripts/verify_beta_11_operator_workspace_spine.py`. No broad runtime
authority is added.

Beta 12 Backend Modularization/API Contract hardening keeps the Control Center
release surface contract intact while moving the app-owned shell/status API
block into `ultimate_ai_agent.api.control_center`. Full-strength modularization
should separate every route family into service-owned modules with no OpenAPI,
API manifest, route-status, release-surface, proof, or authority drift. The
repo-safe current version preserves the then-current 169-route API boundary, stable
operation IDs, side-effect classes, route classifications, response envelopes,
redactions, task-decomposition service compatibility, and release-surface
metadata. It adds no provider/model calls, connector writes, web fetching,
browser automation, shell/subprocess execution, Git/file mutation, background
autonomy, public release, or production authority. Promotion remains one route
group at a time through UAA-P1-052 with OpenAPI/API manifest/route-status
checks, module ownership assertions, docs, focused tests, and Foundation Gate.
Verification: `scripts/verify_beta_12_backend_modularization_api.py`.

Usable Authority PR 04 hardens `/actions` as a backend-owned Action Inbox work
queue with safe lane counts, next-item posture, proof/receipt/evidence refs,
CLI inspection, and the exact `local_task_create` local task record lane. It
does not grant generic action execution, provider/model calls, connector
writes/sends, browser or shell execution, memory writes, context injection,
external side effects, rollback execution, public release, or production
authority.

Beta 05 hardens the same Action Inbox lane as a real work queue surface:
`action_inbox_work_queue_read_model.work_items[]` now carries exact safe work
items, approval posture, receipt posture, mutation-control posture, proof refs,
expected/recorded receipt refs, rollback/safe-disable refs, blocked-authority
refs, explicit unsafe-ref omission posture, and no-fake-mutation-control flags.
Control Center renders those backend-owned work items only after the frontend
guard validates the Python Core source, lane/ref parity, no denied authority
flags, and decision-lane visibility-before-approval posture. The route remains
limited to read/proof inspection and separately scoped decision/local-task
receipt lanes; no broad execution authority is added.

Usable Authority PR 05 binds Evidence and Memory into the daily loop through a
backend-owned Evidence/Memory loop binding read model exposed from Today,
Memory Review, Evidence Timeline, and
`scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding`. The binding
uses safe refs to explain why memory appeared, which evidence supports it, and
which action/run/proof refs connect the loop. Proof Detail resolves the
binding's universal Proof refs without becoming the binding read-model surface.
It does not make memory truth,
inject context, write memory automatically, delete or export memory, execute
actions, call providers/models, write/send connectors, run browser or shell
work, start background autonomy, or grant production authority.

Beta 06 hardens that Evidence/Memory binding by making the shared
loop/run/action/proof refs, reviewed-memory-write exact scope, broad-memory-
write blocked posture, safe-disable/rollback refs, and promotion-path refs
first-class in the Python Core read model and Control Center guard. The
universal Proof spine now resolves the binding's advertised Proof refs.
`scripts/verify_beta_06_evidence_memory_binding.py` verifies the repo-safe
slice. This adds no memory truth authority, runtime context injection,
automatic memory write, memory delete/export, connector write/send,
provider/model calls, shell/browser execution, background autonomy, public
release, or production authority.

Usable Authority PR 06 adds `/trust` as a partial Trust authority map backed by
`GET /control-center/trust-authority/matrix` and
`scripts/dev/uaa_founder_loop.py inspect-trust-authority`. It explains the
current usable authority tiers, approval posture, proof refs, verifier refs,
and blocked capability refs from Python Core/API truth. It does not grant
connector writes/sends, provider/model calls, browser or shell execution,
runtime context injection, standing authority, background autonomy, public
release, or production authority.

Beta 07 Trust authority map hardens `/trust` from a blocker wall into an
operator authority map. Full-strength Trust should eventually let the operator
choose exact authority modes, inspect enabled lanes, pause or disable lanes,
understand rollback posture, and see authority readiness for future provider,
connector, shell, browser, and background authority. The repo-safe version
remains backend-owned and read-only: it exposes enabled, review-only,
approval-required, planned, and blocked lanes with CLI inspection refs,
safe-disable refs, rollback refs, authority readiness refs, compatibility
promotion-path refs, proof refs, verifier refs, and fail-closed Control Center
validation. Blocked/needs-authority lanes
remain visible for connector writes/sends, provider/model calls,
shell/subprocess execution, browser automation, runtime context injection,
standing authority, background autonomy, public release, and production
authority. Each later authority-ready lane still requires a verifier-backed PR
with exact scope, approval binding, safe-disable, rollback, redaction,
receipt/proof coverage, CLI parity, and route/product-language updates.
Verification:
`scripts/verify_beta_07_trust_authority_map.py`. No broad runtime authority is
added.

Usable Authority PR 12 hardens the release surface by requiring checked-in
redacted desktop/mobile visual baselines for primary Control Center routes:
`/start`, `/today`, `/inbox`, `/plans`, `/actions`, `/proof`, `/trust`,
`/memory`, `/evidence`, and `/settings`. It also records dev-only auth bypass
and unsafe local `/v1` runtime posture as release blockers for the relevant
Chat, Models, Settings, and Setup surfaces. This is evidence hardening only; it
does not grant public distribution, production authority, broader model
runtime authority, browser execution, connector writes, or background
autonomy.

Beta 13 frontend route states and visual proof hardens the Control Center shell
state grammar. Full-strength: every route should have polished loading, empty,
error, blocked, partial, and success states backed by route-specific read-model
truth, operator proof, and visual regression evidence. Repo-safe: Control
Center now renders a route-state strip from release surface metadata plus
frontend-client route read-state provenance; route-specific state labels remain
presentation-only and do not create durable workflow truth. Checked-in visual
baselines cover the primary routes plus dedicated state scenarios for loading,
empty, error, blocked, partial, and success. Blocked / needs authority:
frontend route states do not grant action execution, provider/model calls,
connector sends or writes, browser automation, shell/subprocess execution,
Git mutation, background autonomy, public release, or production authority.
Exact promotion path: promote each missing route state with a backend-owned
read model or proof contract, CLI inspection, redacted receipt/evidence refs,
visual baseline update, product-language guard, and focused frontend/verifier
tests before claiming readiness.

Beta 14 adds the local beta QA gate. Full-strength: Beta 14 aims for a
high-ambition local founder/operator QA gate where setup, the daily loop,
Action Inbox, evidence, memory, proof, Trust, and private trial review read as
one coherent beta-quality product loop. Repo-safe: `make verify-beta-local`
runs a backend-owned, local/private, safe-ref-only verifier bundle across docs,
security/redaction, product truth, operational maturity, OpenAPI, the API
perimeter, release lanes, release evidence packets, release surface, dogfood
loop evidence, private beta/private-trial readiness, WebAccessGateway authority
guards, frontend safety, checked-in visual proof, every beta lane verifier, and
Foundation Gate report-only mode. `make verify-beta-local-visual` runs that
default bundle plus the explicit live Playwright visual comparison lane and is
required when the beta PR changes primary UI output or visual manifests.
Blocked / needs authority: public beta, public distribution, production
readiness, production authority, connector writes, provider/model calls,
browser/shell execution, account sync,
background autonomy, broad memory writes, context injection, Code apply,
rollback execution, and generic action execution remain blocked. Exact
promotion path: promotion requires a later scoped PR with accepted
local/private findings, backend/core/API or CLI parity, redacted evidence,
product-language checks, verifier updates, focused tests, route/OpenAPI/
manifest updates where applicable, and rollback/safe-disable posture for any
mutation.

Beta 02 hardens `/setup` by binding the dry-run Setup Assistant read model to
first-run daily-loop refs and local package proof refs. The route can truthfully
show local loopback runtime packaging proof and local unsigned `.app` artifact
proof, but the `.app` verifier does not launch the app and this surface still
does not grant signing, notarization, installer side effects, LaunchAgent or
daemon changes, model downloads, provider/model calls, browser automation,
public distribution, production readiness, or production authority.

Dogfood Live Loop Acceptance adds a deterministic repo-local fixture, CLI
inspection command, verifier, and frontend coherence test proving one local
daily loop across `/start`, `/today`, `/actions`, `/proof`, `/memory`,
`/evidence`, and `/trust`. Start, Today, Actions, Proof, and the combined
Evidence/Memory binding share deterministic backend-owned run, action, receipt,
proof, evidence, and memory refs; Trust contributes the matching approval and
blocked-authority posture. It reuses the exact `local_task_create` local task
commit lane and adds no broader execution, external mutation, hidden context
injection, public distribution, or production authority.

Beta 03 productizes the repo-safe daily loop across `/start`, `/today`,
`/actions`, `/proof`, `/evidence`, `/memory`, `/trust`, and `/settings` by
using one backend-owned loop spine from
`founder_loop_v1_product_proof_read_model`, Action Inbox work queue refs,
Universal Proof refs, Evidence/Memory binding refs, and Settings status refs.
Source Inbox remains visible in primary navigation for route reachability and
visual-baseline continuity, but it is a supporting source-readiness surface.
This is read-model, CLI, UI, and verifier hardening only; it adds no
provider/model call, connector send/write, browser automation,
shell/subprocess execution, broad memory write, runtime context injection,
public distribution, or production authority.

Beta 04 hardens the Universal Proof and Run Detail spine across the same
repo-safe daily loop. Full-strength target: every action, approval, evidence
event, memory decision, local task commit, setup/package event, and future
coding/operator run opens one coherent Proof and Run Detail view. Repo-safe
version: each backend-owned proof record carries a
`control-center-proof-run-detail.v1` safe-ref snapshot with route refs, receipt
refs, evidence refs, audit refs, rollback or safe-disable refs, blocked
authority refs, and exact promotion-path refs; Control Center renders those
refs as inspection-only route, receipt, evidence, audit, memory, blocked, and
promotion-path groups while CLI output exposes the complete proof records.
Blocked / needs authority: provider/model calls, connector writes or sends,
browser automation, shell/subprocess execution, background autonomy, public
release claims, and production authority remain blocked. Exact capability path:
implement one AuthorityLease-gated capability at a time with exact scope,
approval binding, idempotency, redacted receipts, rollback or safe-disable
posture, CLI parity, frontend truth labels, and focused tests/verifiers.
