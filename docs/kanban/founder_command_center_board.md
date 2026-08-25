# Founder Command Center Kanban Board

Status: planning and execution board
Parent board: `docs/kanban/current_board.md`
Parent plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`

This board is a product-loop planning board. It does not replace Operator
Runtime Excellence and does not grant runtime authority. UAA-P1-011 is the
readable-loop baseline; the next product slice starts from its proof chain and
does not broaden runtime authority.

FCC-MAC-001, FCC-P0-002, FCC-P0-004, FCC-P0-003, FCC-P0-005, FCC-P1-007,
FCC-P1-008, FCC-P1-006, FCC-P1-009, FCC-P1-010, FCC-P1-011, and FCC-P1-012
have scoped implementation slices ready for review. UAA-P1-065 completed the
Founder Command Center review/cleanup pass and promoted exactly one later FCC
candidate: FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core
Surfaces.

UAA-P1-067 completed the Today-spine, memory-first beta-readiness
planning/currentness path. UAA-P1-068 completed the Today Product Spine
Contract. UAA-P1-069 completed the Evidence History Grammar contract.
UAA-P1-070 completed the Memory Source And Provenance Model. UAA-P1-071
completed Memory Review Decision Capture. UAA-P1-072 completed Business Memory
And Memory Quality Controls. UAA-P1-073 completed Plans To Reviewable Action
Envelopes. UAA-P1-074 completed Chat Local Operator Surface. UAA-P1-075
completed Governed Code Workbench V1. UAA-P1-076 completed Cross-Surface
Memory Intake. UAA-P1-077 completed Memory-To-Loop Binding. UAA-P1-078
completed the Private Beta-Readiness Gate. UAA-P1-079 completed User Intent
Understanding V1.
UAA-P1-066 is implemented as a strictly read-only Local Model Manager support
lane through `GET /control-center/local-models/status` and does not add
lifecycle, switching, activation, download, model pull, runtime adapter, model
call, provider/model authority, or production authority. It now names the
Optional Local Model Stack: Docker, llama.cpp, OpenWebUI, Ollama, MLX-LM, with
Ollama and MLX-LM as read-only readiness and inventory evidence surfaces only.

UAA-P1-091 v0.105.0 Governed Runtime Pilot is a completed scoped internal
runtime-authority lane on the Operator Runtime Excellence board, recorded by
annotated tag `v0.105.0-governed-runtime-pilot`. It is relevant
to the Founder Command Center only as backend-owned Action Inbox/runtime receipt
truth: configured loopback local-model receipts, one exact read-only status
command, and exact Action Inbox approved focused pytest, repo-verifier,
frontend-check, and repo-doctor execution through
RuntimeGateway. Its Action Inbox surface calls the exact backend local-model,
command-request, approval/deny, execute, refresh, and safe-disable APIs without
minting an AuthorityLease or enabling broad action execution. It does not grant browser automation, connector writes, plugin
import, remote execution, arbitrary shell/subprocess work outside exact
approved lanes, public beta, public release,
production authority, or broad autonomy.

The `context_injection` prerequisite contract is contract-ready for future gate
review only. It is not selected as an authority capability, adds no runtime
prompt/context injection route or Control Center control, and keeps runtime
prompt/context injection blocked.

FCC-V1-000 Control Center Release Surface Manifest is complete. FCC-V1-001 API
Perimeter For Real Mutations is complete as contract/verifier coverage with
duplicate replay runtime still blocked until route-owner receipt storage exists outside routes that implement their own receipt-backed replay.
The Founder Loop V1 conveyor is `FCC-V1-000` through `FCC-V1-007`. It is the
productization spine for completed release surface truth, API perimeter for
real mutations, backend-owned Action decisions, the first Today-to-Action
receipt loop, Chat receipts and handoff, Memory Review accept/correct/reject
backend decisions, Evidence Timeline productization, and proof-lane promotion.
The detailed milestone goals, routes, fields, storage semantics, UI outcomes,
and authority boundaries live in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`.

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

## Next Development Phase Map

Source guide: `docs/uaa_founder_command_center_next_phases_report.md`.

This phase map is the working implementation order from the current repo
baseline. It is subordinate to this board, the current Operator Runtime
Excellence board, the product truth packet, and the Founder Loop V1
proofed-route conveyor. It does not grant connector writes, email send,
calendar writes, action execution, automatic memory truth, context injection,
model/provider authority, public beta, public distribution, production
readiness, or new runtime authority.

The report's product sequence is directionally right: product truth, trust,
professional memory, Morning Briefing, Action Inbox, source readiness,
CRM-lite, self-healing recommendations, Weekly Review, dogfood, micro-actions,
and native polish. From the current implementation baseline, the next lane
should pull local setup hardening and loop readability forward because the
memory, action, evidence, and route-proof foundations already have completed
contract/read-only slices.

Operational maturity is a promotion gate, not a prose status. The canonical
scorecard is `docs/control_center/operational_maturity_manifest.json`, the
ladder is `docs/control_center/OPERATIONALIZATION_LADDER.md`, and the enforcing
check is `scripts/verify_operational_maturity.py`. No module may move from
planned, proposal, partial, or proofed-review posture to operational behavior
without a manifest rank change, verifier pass, backend-owned receipts, route
metadata, CLI/core/API parity, focused tests, and redacted evidence.
Rank 2+ backend-owned status routes must also declare `ui_status_binding`
evidence in the manifest: the Control Center endpoint/client/type/component/test
refs that surface the status, or a documented backend-only reason and blocker.
Candidate next capabilities must stay scoped to that maturity scorecard and may
not claim operational status without the same manifest and verifier proof.
The future-authority gate is the AuthorityLease capability conveyor anchored in
`docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`, with the
legacy-stable conveyor path `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`
and the canonical authority candidate scorecard at
`docs/control_center/authority_candidate_scorecard.json`. The fixed first web
implementation capability is `read_only_real_world_web_fetch` through
`WebAccessGateway`; connector writes, memory writes, shell/subprocess local
maintenance, browser automation, provider/model authority, and context
injection are ranked there only as follow-on candidates and are not selected
for implemented authority. The current follow-on authority capability decision
is no-go; Action Inbox `local_task_create` remains the only rank 5 local write
authority capability. That rank 5 capability depends on explicit
safe-disable/rollback posture refs and backend denial when the capability is
disabled; it is not a rank 6 rollback execution or broader action-execution
promotion.

Long-term "life OS" delegation, including purchases, bookings, subscriptions,
account work, and credential/payment-handle use, is parked in
`docs/strategy/DELEGATED_LIFE_OS_NORTH_STAR.md`. It is not a current lane and
does not change the WIP limit or authority-changing-card rule.

Implementation note: a bounded daily-loop product behavior slice now deepens
the existing read routes without adding authority. Morning Briefing and Today
surface backend-owned daily command-loop summaries, source-readiness states,
CRM-lite follow-ups, memory "why shown" rows, review queue groups, Weekly
Review narrative refs, and private dogfood capture refs. This advances the
readability, briefing, source-readiness, CRM-lite, review, and dogfood phases
as safe-ref UI/API behavior only; it does not complete the full phase map,
execute actions, connect external accounts, write connectors, call providers,
or grant production/public beta authority.

| Phase | Working milestone | Primary outcome | Gate before next phase |
|---:|---|---|---|
| 0 | `FCC-PRODUCT-000` Product Identity And Truth Alignment | README/front-door language presents Founder Command Center as the canonical local-first professional command center while preserving no-authority truth. | Product language and product truth packet remain aligned with current implementation. |
| 0.5 | `FCC-TRUTH-001` Currentness And Verification Repair | Verification, route counts, proof lanes, and report-only labels are consistent and boringly trustworthy. | `make verify` path and route/product truth checks either pass or report explicit blockers. |
| 1 | `FCC-SETUP-001` macOS-first Setup Assistant Hardening | Local setup preview, dry-run scope, rollback refs, blocked states, and safe prerequisite visibility are clear enough to trust. | No setup mutation, installer, LaunchAgent, credential, download, shell execution, or production claim is introduced. |
| 2 | `FCC-LOOP-001` First Product Loop Readability | Today, Inbox, Plans, Actions, Memory, Evidence, and Settings read as one product loop instead of scattered inspection panels. | Existing route truth, CLI/core inspection parity, and blocked states remain visible and tested. |
| 3 | `FCC-INBOX-001` Action Inbox And Approval Envelope UX | Reviewable envelopes are easy to scan by kind, scope, risk, authority, expiry, evidence, idempotency, and rollback posture. | Decisions remain backend-owned; approve/edit/reject/defer creates receipts without executing actions. |
| 4 | `FCC-BRIEFING-001` Morning Briefing And Today Plan V1 | Morning Briefing becomes the daily starting surface over priorities, commitments, memory hints, blocked sources, review queue state, and next safe actions. | Every item has source/evidence/memory refs or an explicit missing-source/blocked posture. |
| 5 | `FCC-SOURCES-001` Source Readiness And Draft-only Inputs | Inbox, calendar, tasks, CRM notes, manual notes, repo, and local-file readiness become visible with metadata-only/manual-import paths. | No account auth, background polling, raw body ingestion, send/write/archive/delete/label/move, or connector runtime claim. |
| 6 | `FCC-MEMORY-CRM-001` Professional Memory And CRM-lite Binding | Reviewed professional memory feeds people, organizations, opportunities, commitments, stale follow-ups, draft opportunities, and relationship health. | Memory remains recall, not truth or authority; every use has provenance and a visible "why shown." |
| 7 | `FCC-REVIEW-001` Evidence Narrative And Weekly CEO Review | Evidence reads like history and Weekly Review summarizes decisions, memory changes, CRM movement, drafts, blockers, and next-week priorities. | Weekly summaries distinguish completed, deferred, rejected, blocked, stale, planned, and missing-source states. |
| 8 | `FCC-HEALTH-001` Self-Healing Recommendations To Inbox | Verifier, docs-currentness, UI friction, blocked-state, and source-readiness issues become reviewable recommendations. | Recommendations can become tasks or patch proposals only after review; nothing auto-codes or auto-applies. |
| 9 | `FCC-DOGFOOD-001` Fourteen-Day Private Dogfood Harness | Daily-use metrics, friction notes, useful/irrelevant briefing signals, Action Inbox decisions, and memory decisions are captured as safe refs. | Accepted/revised private findings exist before beta-readiness or execution claims change. |
| 10 | `FCC-ACTION-001` Approval-bound Local Authority Capability | Add the first exact-scope local action capability, starting with `FCC-ACTION-001a` local task creation. Later local follow-up completion or opportunity update capabilities must define separate AuthorityLease scope. | Each capability has approval, receipt, evidence, idempotency, rollback/safe-disable posture, blocked external authority, and an operational maturity manifest authority capability record. |
| 11 | `FCC-POLISH-001` Native And Apple-grade UX Layer | Launcher, setup, notifications, blocked states, visual hierarchy, and product copy make the proven loop feel calm and professional. | Normal daily use no longer requires Terminal, but technical route/authority details remain inspectable. |

### Expanded Phase Cards

The table above is a quick index. The cards below preserve the report's fuller
intent so each milestone can be picked up as a scoped implementation lane
without rereading the full report.

#### Phase 0 - `FCC-PRODUCT-000` Product Identity And Truth Alignment

**Intent:** Make the repo's front door describe UAA first as the Founder Command
Center: a local-first professional command center for Morning Briefing, Today
Plan, Action Inbox, Evidence, Memory Review, and Weekly CEO Review.

**What This Means:** The safety/runtime foundation should remain visible, but it
should read as the trust layer under the product promise. Canonical language
should make Founder Command Center the user-facing product cockpit and keep
Control Center, Operator Shell, and Founder Loop as implementation or historical
terms where appropriate.

**Deliverables:** README/front-door copy, canonical product terminology, the
Morning -> Decide -> Draft -> Approve -> Follow up -> Remember -> Review spine,
and the smallest product truth packet alignment needed to keep claims current.

**Done Gate:** A new reader can understand within a short scan that UAA is a
professional personal AI command center while still seeing the current local,
non-production, no-broad-autonomy posture.

**Authority Boundary:** No new shipped feature claims, production claims, public
beta claims, connector authority, runtime authority, or broader autonomy are
introduced.

#### Phase 0.5 - `FCC-TRUTH-001` Trust And Currentness Repair

**Intent:** Protect product trust by making verification paths, route counts,
manifest truth, product status language, and report-only proof labels
boringly correct.

**What This Means:** Before more product surface is added, advertised checks
need to map to real verification paths, route/product counts need to agree
across docs and manifests, and report-only modes need to be unmistakable.

**Deliverables:** Verification-path audit, route/product truth consistency
checks, report-only wording cleanup, and product-truth drift guards for claims
such as production readiness, public beta, live connectors, action execution,
automatic memory writes, or context injection.

**Done Gate:** `make verify` and documented verification commands either run
meaningful checks or fail with clear blockers, and route/product truth
inconsistencies are caught by repo-local verification.

**Authority Boundary:** Verification work only. This phase adds no route
authority, product-surface expansion, connector runtime, action execution, or
production claim.

#### Phase 1 - `FCC-SETUP-001` macOS-first Setup Assistant Hardening

**Intent:** Make local setup feel trustworthy before the broader daily loop
depends on it.

**What This Means:** The Setup Assistant should make dry-run scope, safe local
prerequisite status, blocked states, rollback refs, redacted summaries, and
next safe actions clear enough that a user can tell what would happen without
granting setup authority.

**Deliverables:** Clearer setup preview, bounded status language,
evidence/rollback posture, safer blocked states, and focused frontend/docs
tests for the read-only setup surface.

**Done Gate:** Setup preview explains what is ready, missing, blocked, and safe
to inspect, while preserving route truth and no-mutation posture.

**Authority Boundary:** No installer mutation, LaunchAgent install/load/start,
background service install/start, credential handling, downloads, shell
execution, rollback execution, public distribution, production setup claim, or
setup mutation authority.

#### Phase 2 - `FCC-LOOP-001` First Product Loop Readability

**Intent:** Make Today, Inbox, Plans, Actions, Memory, Evidence, and Settings
read as one daily product loop rather than scattered inspection panels.

**What This Means:** The primary Control Center experience should organize the
existing proofed and partial surfaces around the user's day: what matters,
what needs review, what is remembered, what happened, and what remains blocked.
Legacy or technical surfaces should stay reachable but become supporting detail.

**Deliverables:** UI navigation/readability pass, grouped legacy surfaces,
clearer blocked/partial/planned states, and product copy that uses plain
operator language while preserving technical inspection paths.

**Done Gate:** The first product loop is scannable without hiding existing
route truth, CLI/core inspection parity, or blocked authority labels.

**Current Implementation:** Implemented as a frontend composition/readability
lane over existing backend summaries. The primary Founder Loop routes show a
shared daily-loop spine for Today, Inbox, Plans, Actions, Memory, Evidence, and
Settings, including blocked states and the exact Action Inbox `local_task_create`
authority posture. No backend route, storage contract, API manifest entry, or
operational maturity rank changed for this lane.

**Authority Boundary:** No backend route changes unless separately scoped, no
React-owned product truth, no new mutation controls, and no authority expansion.

#### Phase 3 - `FCC-INBOX-001` Action Inbox And Approval Envelope UX

**Intent:** Give every reviewable item a shared review grammar that lowers
cognitive load.

**What This Means:** Action Inbox should make envelope kind, exact scope, risk,
authority required, side-effect class, expiry, evidence, idempotency, receipt
state, and rollback/safe-disable posture visible before any decision.

**Deliverables:** Richer Action Inbox grouping/filtering, exact approval
envelope presentation, receipt visibility, blocked-authority labels, and UI
tests that decisions stay backend-owned.

**Current Slice:** Queue organization is implemented as backend-classified
Action Inbox lanes for ready decisions, approved local-task items,
authority-blocked items, expired/stale items, recorded receipts, and
proposal-only/no-execution items. This adds scanability only; it does not add
generic execution, connector writes, shell/subprocess execution, provider/model
authority, memory writes, context injection, or production authority.
FCC-INBOX-001 now adds consistent backend-owned Approval Envelope and Receipt
Visibility cards/read models for each `/actions` item. The cards improve review
quality by using one safe grammar for action kind, exact scope, risk,
side-effect class, approval requirement, expiry/staleness, idempotency,
expected receipts, rollback/safe-disable posture, blockers, evidence refs,
decision receipt refs, local task refs, local task commit receipt refs,
Evidence Timeline refs, replay posture, and conflict posture. It does not
change operational maturity rank or add authority. Mock/degraded `/actions`
fallback data stays non-authoritative. Milestone truth is recorded in
`docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`.
The backend-owned Action Inbox work queue now also carries exact-scope refs,
idempotency refs, and expiry/staleness posture into the Control Center queue
cards so reviewability does not depend on raw envelope inspection.
Fallback data is explicitly non-authoritative: it may render unavailable
envelope/receipt cards for shape, but it cannot claim Python-core read-model
ownership, backend eligibility, or local task commit readiness.
FCC-ACTION-002 keeps the active `/actions` lane filters/drilldowns as
presentation-only state and reconciles from `GET /control-center/actions/inbox`
after a local task commit before moving the item into the receipt-recorded
lane. The maturity verifier now requires backend receipt reconciliation,
frontend refresh tests, CLI parity, and mock/degraded committed-state guards for
the existing exact local-task lane.

**Done Gate:** A user can compare action proposals, memory candidates, drafts,
CRM updates, recommendations, and patch proposals through one review language,
with decision receipts visible where existing backend contracts support them.

**Authority Boundary:** Approve/edit/reject/defer may record decisions only
where already supported. This phase does not execute actions, send connector
writes, grant approval shortcuts, or store product behavior only in React state.

#### Phase 4 - `FCC-BRIEFING-001` Morning Briefing And Today Plan V1

**Intent:** Make Morning Briefing the daily home for the Founder Command Center.

**What This Means:** Morning Briefing and Today Plan should compose priorities,
commitments, memory hints, missing sources, blockers, draft opportunities,
system health, and review queue state into one readable start-of-day surface.

**Deliverables:** Briefing card model, Today Plan generation from existing safe
refs, memory/source/evidence display reasons, and review-item creation paths
where existing contracts allow them.

**Done Gate:** Every briefing item has source/evidence/memory refs or an
explicit missing-source/blocked posture, and the normal morning scan does not
require the terminal.

**Current Slice:** `/briefing` includes a read-only source readiness metadata
card over existing backend fields: route refs, missing email/calendar/
notification contracts, refresh/notification blockers, blocked source states,
and explicit `ready`, `blocked`, `missing`, `metadata_only`, `unavailable`, and
`not_configured` source-readiness labels. No connector runtime or source
refresh authority is added. Milestone truth is recorded in
`docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md`.

**Authority Boundary:** Do not fake live email, calendar, or task access. No
send/write/delete authority, account auth, background polling, raw source
ingestion, hidden context injection, or new action execution is introduced.

#### Phase 5 - `FCC-SOURCES-001` Source Readiness And Draft-only Inputs

**Intent:** Make inbox, calendar, tasks, CRM notes, manual notes, repo context,
and local-file context visible before connector authority exists.

**What This Means:** Source awareness starts with readiness states,
metadata-only records, manual imports, and draft-only proposals. Missing
sources should be useful blocked states, not dead ends or implied integrations.

**Deliverables:** Source readiness model, manual source summaries,
metadata-only source records, draft proposal contracts/UI binding, and Settings
or Setup copy for next safe source actions.

**Done Gate:** Morning Briefing and Today can show inbox/calendar/task source
readiness, manual or metadata-only source summaries can feed reviewable
objects, and missing sources explain the next safe action.

**Current Slice:** Today, Morning Briefing, `/inbox`, and `/actions` now bind
to a dedicated backend-owned Source Readiness route,
`GET /control-center/sources/readiness`, for inbox, calendar, tasks,
CRM-lite/manual notes, repo, and local files. The read model exposes draft-only
proposal candidates for email metadata contract, calendar metadata contract,
and account-auth boundary work, and Action Inbox classifies those candidates as
`proposal_only_no_execution_path`. The same route now carries backend-owned
email/calendar read-only metadata contract refs under
`read_only_metadata_contracts`. This moves the unit to rank-2 proposal review
in the operational maturity manifest without granting connector runtime,
account auth, source ingestion, or writes. Milestone truth is
recorded in
`docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`.

**Authority Boundary:** No account auth, background polling, raw body
ingestion, email send, calendar write, external task write, archive, delete,
label, move behavior, credential storage claim, or connector runtime claim.

#### Phase 6 - `FCC-MEMORY-CRM-001` Professional Memory And CRM-lite Binding

**Intent:** Turn memory into professional context for people, organizations,
projects, opportunities, commitments, preferences, interactions, follow-ups,
beliefs, and corrections.

**What This Means:** Reviewed memory should explain why it appears, identify
source and evidence refs, surface stale/conflict posture, and support local
relationship, opportunity, commitment, and follow-up workflows without becoming
truth or authority.

**Deliverables:** Visible "why shown" memory use, stale/conflict warnings,
relationship and follow-up cards, CRM-lite local objects, memory-derived
review items, and evidence-linked correction posture.

**Done Gate:** Professional memory can influence briefing/follow-up proposals
as reviewed recall only, and every visible memory use has provenance plus a
display reason.

**Current Slice:** Today, Morning Briefing, Action Inbox, and Memory now expose
backend-owned `crm_lite_followups` and `memory_why_shown_items` with
relationship refs, opportunity refs, follow-up refs, review envelope refs,
memory/source/evidence refs, stale/conflict posture, missing evidence refs,
and explicit "why shown" explanations. Milestone truth is recorded in
`docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`.

**Authority Boundary:** No automatic memory truth, hidden context injection,
model-output authority, CRM/account sync, connector writes, external CRM
updates, or action execution.

**CRM + Communications Spine M0 Bridge:** The broader CRM product-line
contract now lives in `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`,
`src/ultimate_ai_agent/core/crm/contracts.py`, and
`scripts/verify_crm_communications_spine_m0.py`. It preserves the locked
Global Identity -> Workspace Context -> Pipeline Object -> Communications
Spine -> Work Queue / Proposal -> Action Inbox / Evidence / Memory shape and
links source readiness plus professional memory to future CRM/Communications
milestones. This bridge adds no /crm UI, no backend endpoints, no connector
runtime, no connector writes, no sends, no calendar writes, no account sync, no
silent merges, no silent contact creation, no provider/model calls, no live web,
no browser runtime, no public beta, and no production authority.

#### Phase 7 - `FCC-REVIEW-001` Evidence Narrative And Weekly CEO Review

**Intent:** Make Evidence read like history and close the professional loop
with a Weekly CEO Review.

**What This Means:** Evidence should answer what was proposed, why, what was
approved/edited/rejected/deferred, what changed, what remains blocked, and what
should carry forward. Weekly Review should summarize decisions, CRM movement,
memory changes, drafts, blockers, and next-week priorities from safe refs.

**Deliverables:** Weekly summary contract/UI, Evidence narrative grouping,
status-preserving rollups, and Action Inbox handoff for follow-ups, memory
corrections, or next-week priorities.

**Done Gate:** Weekly Review distinguishes completed, deferred, rejected,
blocked, stale, planned, and missing-source states and links claims to
source/evidence refs.

**Current Slice:** Evidence Timeline remains a backend-owned safe-ref history
surface, and Weekly Review now exposes explicit `completed_refs`,
`deferred_refs`, `rejected_refs`, `blocked_refs`, `stale_refs`, `planned_refs`,
and `missing_source_refs` on Today, Morning Briefing, and Action Inbox.
Milestone truth is recorded in
`docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md`.

**Authority Boundary:** No invented truth, no hidden summarization authority,
no context injection, no connector reads/writes, and no production-readiness
claim.

#### Phase 8 - `FCC-HEALTH-001` Self-Healing Recommendations To Inbox

**Intent:** Let system and product issues improve the daily loop without making
self-healing the product's center of gravity.

**What This Means:** Verifier failures, docs drift, route mismatches, UI
friction, blocked-state issues, source-readiness gaps, private feedback, and
memory quality problems should become reviewable recommendations in Action
Inbox.

**Deliverables:** RecommendationCandidate model, `self_heal_recommendation`
Action Inbox envelope kind, Evidence Timeline events, validation-plan refs,
rollback/safe-disable refs, and conversion paths to product tasks or patch
proposals after review.

**Current Slice:** Implemented for the first backend-owned recommendation
read-model and Action Inbox projection. Source-readiness gaps, documentation
currentness drift, operational maturity proof gaps, and optional private
friction refs can become review-only `self_heal_recommendation` items with
blocked-authority refs and no execution path. Recommendation review receipts,
Evidence lifecycle events, CLI queue inspection, and conversion paths remain
planned or blocked until separately scoped.

**Implementation Task Spec:** Detailed prerequisites, contract fields, signal
adapters, queue/storage tasks, Action Inbox binding, Evidence events, UI work,
CLI parity, tests, verifiers, and done gates are tracked in
`docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`.

**Done Gate:** Recommendations can be created from verifier/doc/UI/friction
signals, reviewed in Action Inbox, and recorded in Evidence without changing
code automatically.

**Authority Boundary:** No autonomous coding, auto-apply patches, broad shell
execution, connector writes, action execution, or hidden repair authority.

#### Phase 9 - `FCC-DOGFOOD-001` Fourteen-Day Private Operator Harness

**Intent:** Test whether UAA is useful as a daily professional assistant, not
whether roadmap surfaces merely exist.

**What This Means:** The private rehearsal should track Morning Briefing opens,
useful items, false positives, memory decisions, follow-ups caught, draft
creation, Action Inbox decisions, self-heal recommendations, terminal-needed
moments, and UI friction.

**Deliverables:** Safe-ref-only dogfood artifacts, Product Friction Inbox,
daily-use metrics, review decision stats, stale follow-up stats, draft
usefulness stats, and accepted/revised private findings after the trial.

**Current Slice:** Implemented as a local/private safe-ref-only 14-day harness
contract and repo-local artifact in
`docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md` and
`docs/macos/private_operator_14_day_dogfood_harness_v1.json`. The harness
defines explicit `not_run`, skipped, blocked, missing-source, and
`pending_operator_review` states. Accepted/revised findings remain empty until
manual review; no telemetry upload, raw private content, connector write,
provider/model call, route, beta claim, or production authority is added.

**Done Gate:** The trial produces accepted or revised findings with measurable
usefulness signals and concrete friction recommendations.

**Authority Boundary:** Private dogfood does not imply public beta, production
readiness, distribution authority, connector authority, or expanded runtime
authority.

#### Phase 10 - `FCC-ACTION-001` Approval-bound Local Authority Capability

**Intent:** Add small local execution abilities only after the daily loop has
proved useful.

**What This Means:** Start with low-risk local lanes such as local task
creation and local follow-up completion or opportunity update. Every lane needs
exact scope, source refs, approval, receipt, evidence, idempotency, and
rollback/safe-disable posture.

**Deliverables:** `local_task_create` as the first exact-scope local action
authority capability, plus decision receipts, Evidence Timeline events, safe
retry behavior, and visible blocked external authority. Additional capabilities
require separate mode/domain/lease gates.

**Current Slice:** Implemented for the existing `local_task_create` authority
capability and recorded in
`docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_AUTHORITY_CAPABILITY.md`.
Action Inbox remains rank 3 overall; `local_task_create` is the only current
rank 5 local write authority capability. The capability has active
`workspace/write` AuthorityLease scope, exact approval, receipt, evidence,
idempotency, safe-disable posture, CLI/API/core parity, and `FCC-ACTION-002`
repeatability refs. No additional authority capability is implemented by this
pass.

**Done Gate:** Each implemented authority capability can be approved, recorded,
inspected, and safely reasoned about without granting broader authority.

**Authority Boundary:** No email send, external calendar write, external CRM or
task write, background sync, broad shell execution, reusable autonomy, or
unrestricted patch apply.

**Patch Workbench Phase A note:** Patch apply remains apply-blocked until the
exact apply route, CLI/API/core parity, durable receipt/evidence, rollback or
safe-disable, and redacted secret-like diff gates are implemented and verified.

#### Phase 11 - `FCC-POLISH-001` Native And Apple-grade UX Layer

**Intent:** Make the proven loop feel calm, professional, and local-first in
daily use.

**What This Means:** Polish follows proof. The launcher, setup wizard, morning
notification, blocked states, visual hierarchy, and product copy should make
normal use understandable without burying the route/authority details that keep
UAA trustworthy.

**Deliverables:** Calmer boot/setup flow, no-terminal normal daily loop,
helpful blocked states, local morning notification posture, refined product
copy, and inspectable technical detail for route/authority status.

**Current Slice:** Implemented as a verified Control Center polish baseline in
`docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md`, backed by
`docs/control_center/visual_regression_manifest.json` and the Playwright visual
spec. The current slice verifies redacted desktop/mobile baselines and
dry-run setup/blocked-state truth over existing backend-owned state. It does
not implement native runtime authority, notifications, packaging, signing,
installer mutation, or production readiness.

**Done Gate:** A user can start and use the daily loop without Terminal while
still being able to inspect what UAA can and cannot do.

**Authority Boundary:** No public installer, public distribution, production
readiness, native OS authority, notification background polling, or connector
authority is claimed unless separately scoped and proven.

Memory remains a cross-cutting lane across phases 2 through 7. The current
contract/read-only memory baseline should be used early for visible recall,
source/provenance, review decisions, conflicts, stale posture, and "why shown"
copy; deeper CRM-lite expansion should wait until the daily loop can display
and route those objects cleanly.

Self-healing remains deliberately later than Morning Briefing, Action Inbox,
source readiness, and CRM-lite. It should enter the product as one source of
reviewable recommendations, not as the product's center of gravity.

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

## Classification Summary

```text
Implemented / ready for review:
FCC-MAC-001, FCC-P0-002, FCC-P0-004, FCC-P0-003, FCC-P0-005,
FCC-P1-007, FCC-P1-008, FCC-P1-006, FCC-P1-009, FCC-P1-010,
FCC-P1-011, FCC-P1-012, UAA-P1-067, UAA-P1-068, UAA-P1-069,
UAA-P1-070, UAA-P1-071, UAA-P1-072, UAA-P1-073, UAA-P1-074,
UAA-P1-075, UAA-P1-076, UAA-P1-077, UAA-P1-078, UAA-P1-079,
UAA-P1-080, UAA-P1-081, UAA-P1-082, UAA-P1-083, UAA-P1-084,
UAA-P1-085, UAA-P1-086, UAA-P1-087.1, UAA-P1-087.2a,
UAA-P1-087.2b, UAA-P1-087.2c, FCC-V1-000, FCC-V1-001,
FCC-V1-002, FCC-V1-003, FCC-V1-004, FCC-V1-005, FCC-V1-006,
FCC-V1-007.

Parked candidate-next:
FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core Surfaces.

Blocked / future:
UAA-P1-087.2, UAA-P1-087.3,
FCC-P1-014, FCC-P1-016, FCC-P1-015, FCC-P2-016, FCC-BLOCK-001,
FCC-BLOCK-002, FCC-BLOCK-003.
```

## Completed Conveyor

### FCC-V1-000 through FCC-V1-007 - Founder Loop V1 Productization Conveyor

Status: Complete through FCC-V1-007 for the bounded Founder Loop V1 conveyor.

Epic: Product/UX, Safety/Permissions, Memory/Knowledge, Business Cofounder
Workflows

Promoted by: Founder Loop V1 planning update.

Type: staged full-stack productization with docs/test/manifest gates first.

Description: Carry the product loop from truthful route status to one real
receipt-bearing Founder loop: Today item to Action envelope, exact approval,
durable receipt, and Evidence Timeline update. The conveyor also makes Control
Center Chat produce durable receipts and handoff refs, makes Action Inbox
approve/edit/reject/defer decisions backend-owned, makes Memory Review
accept/correct/reject backend-owned, productizes Evidence Timeline events, and
promotes only routes that pass proof lanes.

Milestone order:

- `FCC-V1-000` Control Center Release Surface Manifest: implemented.
- `FCC-V1-001` API Perimeter For Real Mutations: implemented as
  contract/verifier coverage; duplicate replay runtime remains blocked until
  route-owner receipt storage exists.
- `FCC-V1-002` Action Inbox Backend State Machine: implemented for
  backend-owned approve/edit/reject/defer decision state and receipt refs
  without action execution.
- `FCC-V1-003` Founder Loop V1 Vertical Slice: implemented for the first
  Today-to-Action envelope receipt loop with exact approval/edit/reject/defer
  receipts, Evidence Timeline update, and CLI inspection parity; action
  execution remains blocked.
- `FCC-V1-004` Control Center Chat Durable Receipt And Handoff: implemented
  for durable safe Chat turn receipts and reviewable Actions/Plans handoff
  receipts; model output, action/plan execution, memory writes, connector
  writes, provider calls, public beta authority, and production authority
  remain blocked.
- `FCC-V1-005` Memory Review Decisions: implemented for backend-owned
  accept/correct/reject receipts, idempotency replay/conflict behavior,
  preserved rejected candidates, corrected-summary refs only, and Evidence
  Timeline visibility without memory truth authority, context injection,
  CRM/account sync, connector writes, action execution, public beta, or
  production authority.
- Governed Cognitive Memory Spine Phase 2: implemented as a read-only L1 hot
  local memory index over reviewed recall-only `LocalMemoryStore` records at
  `GET /control-center/memory/l1-index`; Phase 3 L2 factual/graph/temporal
  indexing is implemented as read-only deterministic ref projection at
  `GET /control-center/memory/l2-index`; Phase 4 L3 identity/session/preference
  modeling is implemented as read-only representation proposals at
  `GET /control-center/memory/l3-index`; Phase 5 context-pack proposals are
  implemented as read-only proposal-only inspection envelopes at
  `GET /control-center/memory/context-packs`; Phase 6 narrow execution hooks
  remain future blocked.
- `FCC-V1-006` Evidence Timeline Productization: implemented for a
  backend-owned Evidence Timeline index with productized events grouped by
  Today item, Action, Chat turn, and Memory candidate; safe refs, receipts,
  approval identifiers, idempotency refs, blocked states, and rollback posture
  are visible without approval, rollback execution, action execution, context
  injection, connector writes, public beta, or production authority.
- `FCC-V1-007` Promotion And Proof Lane: implemented for `founder_loop_v1_proofed` route-surface promotion of `/actions`, `/chat`, `/memory`, and `/evidence` only.
- `FCC-MEM-001` Memory Workbench V1: implemented as a backend-owned Memory
  Review workbench/search/manual-intake hardening pass with expanded lifecycle
  receipts, deterministic quality grouping, Control Center workbench cards,
  CLI parity, and stored execution prompts. Accept/correct remain the only
  reviewed recall-only record writers; delete/export execution,
  semantic/vector search, connector writes, context injection, public beta, and
  production authority remain blocked.
- `FCC-MEM-015` Memory Impact Graph And Follow-Up Queue: implemented as a
  backend-owned impact graph, proposal-only follow-up queue, Recall Health V2,
  merge/supersede comparison UI, context-pack preview surface, CLI commands,
  focused tests, and verifier. It connects memory refs to Today, Actions,
  Briefing, Evidence, and context-pack previews without action execution,
  memory writes, context injection, CRM/account sync, semantic/vector search,
  provider/model calls, public beta, or production authority.
- `FCC-MEM-016` through `FCC-MEM-020` Memory Diagnostics And Context Manifest:
  implemented as backend-owned retrieval diagnostics, citation integrity,
  feedback quality issues, proposal-only maintenance runs, context manifest
  proposals, CLI commands, stored execution prompts, focused tests, and
  verifier. Feedback records quality signal receipts only. It adds no
  automatic memory writes, auto-merge, auto-forget, delete/export execution,
  hidden context injection, provider/model calls, connector writes, action
  execution, public beta, or production authority.
- `FCC-MEM-021` Memory Read Models UI + Proposal Bridge: implemented as
  Control Center API client/types, Memory UI sections for MEM-016 through
  MEM-020, bounded feedback controls, and a proposal-only Action Inbox bridge
  that reuses `self_heal_recommendation` for memory quality/maintenance refs.
  Action Inbox decisions record review receipts only and do not merge,
  supersede, forget, write memory, run maintenance, inject context, call
  providers, perform connector writes, execute shell/subprocess work, or grant
  production authority.

Acceptance criteria: Each milestone's detailed goal, tasks, expected routes,
model fields, storage behavior, UI result, proof lane, and authority boundary
are recorded in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`. The scoped Founder Loop
V1 behavior now has route truth, idempotency, backend-owned decisions, durable
receipts, Evidence Timeline updates, CLI/repo-local inspection parity,
frontend rendering, and raw-content leak checks for the bounded proofed route
surfaces.

Required tests/verifiers: release surface verifier, OpenAPI/API manifest
checks, focused Action lifecycle tests, Chat receipt/handoff tests, Memory
decision tests, Evidence Timeline tests, Control Center route/render tests,
documentation integrity, and
`scripts/verify_founder_loop_v1.py`, implemented for the bounded route-surface
proof lane.

Safety notes: The completed conveyor does not add runtime model calls,
connector writes, shell/subprocess execution, browser automation, automatic
memory writes, context injection, CRM sync, action execution, public beta,
public distribution, or production authority.

### UAA-P1-077 - Memory-To-Loop Binding

Status: Implemented / ready for review.

Epic: Memory/Knowledge, Product/UX

Promoted by: UAA-P1-076

Type: full-stack read-only loop binding

Description: Make Today, Action Inbox, Evidence Timeline, and Weekly CEO Review
show memory candidates, accepted recall refs, corrections, rejected items,
follow-up commitments, stale-state posture, and missing-evidence blockers.

Acceptance criteria: Memory is visible as part of the daily operating loop,
not a hidden background store. Every memory-derived action proposal names its
source refs, evidence refs, side-effect class, and approval posture.

Required tests/verifiers: Control Center render tests, Founder Loop storage/API
tests if route payloads change, frontend safety verifier, and documentation
integrity.

Safety notes: Memory-derived UI does not grant approval, execute work, inject
context, write memory automatically, mutate external systems, claim production
authority, or treat recall as truth.

### FCC-P0-002 Follow-Up - Collapse/Organize Control Center Around Core Surfaces

Epic: Product/UX

Promoted by: UAA-P1-065

Type: frontend read-only product-surface organization

Description: Collapse and organize Control Center around Today, Inbox, Plans,
Actions, Memory, Evidence, and Settings as the primary product workflow while
keeping legacy review surfaces reachable as supporting detail.

Acceptance criteria: Today, Inbox, Plans, Actions, Memory, Evidence, and
Settings remain the primary loop; legacy review surfaces are grouped as
supporting detail; route truth, authority boundaries, blocked states, and
existing route coverage remain visible and tested.

Required tests/verifiers: `apps/control-center/src/App.test.tsx`,
`make frontend-check`, `.venv/bin/python scripts/verify_control_center_frontend.py`,
and `.venv/bin/python scripts/verify_documentation_integrity.py`.

Safety notes: No backend route, no OpenAPI change, approval grant capture,
frontend mutation control, connector runtime, model/provider call,
shell/subprocess behavior, public distribution, production authority, or
React-owned product truth. This task is not implemented by UAA-P1-065.

## Implemented / Ready For Review

### UAA-P1-067 - Today-Spine Founder Command Center Beta-Readiness Path

Epic: Memory/Knowledge, Business Cofounder Workflows, Product/UX

Implemented by: Documented-milestone conveyor execution

Description: Completed the planning/currentness pass that makes Today the
product spine, robust reviewed memory the product differentiator, and
UAA-P1-068 the next Today Product Spine Contract before broader product or
authority expansion.

Acceptance evidence: Active docs, roadmap, current board, product truth, MVP
spec, phase tasks, and Codex prompt library identify UAA-P1-067 as complete,
UAA-P1-068 as complete, UAA-P1-069 as complete, UAA-P1-070 as complete,
UAA-P1-071 as complete, UAA-P1-072 as complete, UAA-P1-073 as complete,
UAA-P1-074 as complete, UAA-P1-075 as complete, UAA-P1-076 as complete,
UAA-P1-077 as complete, UAA-P1-078 as complete, UAA-P1-079 as complete, and
UAA-P1-066 as read-only local model support, including Ollama and MLX-LM
readiness posture without runtime support.

Safety notes: Planning/currentness only. No backend route, OpenAPI operation,
Control Center implementation, connector runtime, provider/model call,
automatic memory write, context injection, public beta, public distribution,
production claim, or runtime authority.

### UAA-P1-068 - Today Product Spine Contract

Epic: Product/UX, Safety/Permissions

Implemented by: Documented-milestone conveyor execution

Description: Completed the shared Today spine contract over the existing
`GET /control-center/today/summary` route so modules feed Today, Actions,
Evidence, and Memory before completion can be claimed.

Acceptance evidence: `docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md`,
`docs/schemas/today_product_spine_contract.schema.json`,
`scripts/verify_uaa_p1_068_today_product_spine_contract.py`,
`tests/test_uaa_p1_068_today_product_spine_contract.py`,
`tests/test_founder_loop_storage.py`, `tests/test_control_center_founder_loop_api.py`,
and `apps/control-center/src/App.test.tsx` bind the contract. The Today panel
renders the contract read-only.

Safety notes: No new route, OpenAPI operation, side-effect class, backend
mutation, frontend mutation control, connector runtime, account auth,
automatic refresh, model/provider authority, automatic memory write, context
injection, raw private evidence, public beta, public distribution, production
readiness, or production authority.

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

### FCC-P0-004 - P0 - Action Inbox Contract And UI Skeleton

Epic: Product/UX, Safety/Permissions

Description: Define action proposal fields and an Action Inbox display for
approval-envelope posture, state-change readiness, receipt/audit/idempotency
refs, expiry posture, rollback/safe-disable posture, and next safe action
labels.

Repo areas likely touched: `src/ultimate_ai_agent/core/storage/`,
`apps/control-center/src/components/`, `apps/control-center/src/api/types.ts`,
`apps/control-center/src/mocks/controlCenterData.ts`, `tests/`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`.

Acceptance criteria: Action cards require safe refs, side-effect class, risk,
authority boundary, approval requirement, evidence refs, idempotency, expiry,
rollback/safe-disable posture, receipt/audit refs where available or explicit
missing-ref blockers, and no action execution controls.

Required tests/verifiers: focused schema tests, `make frontend-check`,
`.venv/bin/python scripts/verify_documentation_integrity.py`.

Safety notes: No execution path and no broad approval. Approve controls stay
disabled or absent until exact backend binding is scoped.

Blockers/dependencies: Builds on completed FCC-P0-001 baseline.

### FCC-P0-003 - P0 - Morning Briefing Workflow Skeleton

Epic: Product/UX, Business Cofounder Workflows

Description: Add a Today/Morning Briefing skeleton over existing status,
route, plan, evidence, source-readiness, stale-state, evidence-gap, missing
contract, and blocked-state summaries.

Repo areas likely touched: `apps/control-center/src/components/`,
`apps/control-center/src/mocks/controlCenterData.ts`,
`apps/control-center/src/api/types.ts`, `apps/control-center/src/App.test.tsx`,
`src/ultimate_ai_agent/core/storage/founder_loop.py`, and focused storage/API
tests.

Acceptance criteria: Briefing shows priorities, blockers, next safe actions,
evidence gaps, source-readiness posture, stale-state posture, explicit missing
email/calendar/notification contract refs, and memory-review count using
existing or mock-safe summaries.

Required tests/verifiers: `make frontend-check`,
`.venv/bin/python scripts/verify_control_center_frontend.py`.

Safety notes: No background generation, connector access, raw private content,
email/calendar access, source refresh, notification delivery, model/provider
call, or memory write.

Blockers/dependencies: FCC-P0-002 and FCC-P0-004.

### FCC-P0-005 - P0 - Memory Review Inbox Contract And UI Skeleton

Epic: Memory/Knowledge, Business Cofounder Workflows

Description: Harden `/memory` as the storage-backed Founder Loop Memory Review
surface using the existing read-only Today summary contract.

Repo areas likely touched: `src/ultimate_ai_agent/core/storage/`,
`apps/control-center/src/components/`, `apps/control-center/src/api/types.ts`,
`apps/control-center/src/mocks/controlCenterData.ts`,
`apps/control-center/src/App.test.tsx`, focused Founder Loop storage/API tests,
and Control Center route-status docs.

Acceptance criteria: Memory candidates show provenance refs, source refs,
evidence refs, review state, correction/rejection posture, retention/delete
posture, confidence posture, stale-state posture, authority boundary, blocked
states, and next safe action. Route paths, operation IDs, and side-effect
classes remain unchanged.

Required tests/verifiers: focused Founder Loop storage/API tests,
`make frontend-check`, `.venv/bin/python scripts/verify_control_center_frontend.py`,
OpenAPI/API manifest checks if contracts change, docs integrity, browser smoke
for `/memory`, and `git diff --check`.

Safety notes: Memory remains recall, not truth or authority. No automatic
memory writes, context injection, model/provider authority, connector writes,
raw transcript/prompt/source display, background sync, delete execution, or
production authority.

Blockers/dependencies: Decision application/persistence, write policy binding,
retention/delete contract, context-injection contract, CLI inspection path, and
durable receipt binding remain future scoped work. UAA-P1-071 covers
review-only decision metadata, not memory mutation.

### FCC-P1-007 - P1 - Calendar Read-Only Integration Contract

Epic: Tools/Integrations, Business Cofounder Workflows

Description: Defines contract-only calendar event metadata envelopes for
meeting prep without account auth or runtime fetch.

Repo areas touched: `src/ultimate_ai_agent/core/connectors/`,
`docs/connectors/`, `tests/`.

Acceptance criteria: Contracts use safe refs for attendee/account identities,
event refs, time-window refs, source readiness, evidence, audit/replay, and
meeting-prep summaries while denying calendar writes, account auth, raw invite
bodies, event titles, meeting links, locations, background collection, and
connector runtime.

Required tests/verifiers: focused contract tests and documentation integrity.

Safety notes: Read-only metadata contract only. No live calendar integration,
backend route, Control Center control, raw private calendar metadata, or
production authority.

Blockers/dependencies: Exact connector runtime milestone required before live
source access.

### FCC-P1-008 - P1 - Email Metadata Read-Only Contract

Epic: Tools/Integrations, Business Cofounder Workflows

Description: Defines safe email metadata envelopes for triage fixtures and
future read-only connector review.

Repo areas touched: `src/ultimate_ai_agent/core/connectors/`,
`docs/connectors/`, `tests/`.

Acceptance criteria: Contracts allow safe sender/thread/time/label summary
refs, source-readiness refs, evidence refs, audit/replay refs, and redacted
inbox/follow-up summaries while denying raw bodies, subject text, participants,
attachment names/downloads, account auth, fetch, send, delete, archive, label
write, and connector runtime.

Required tests/verifiers: focused contract tests, redaction tests, and
documentation integrity.

Safety notes: Metadata-only planning. No email connector runtime, backend
route, Control Center control, connector write, or production authority.

Blockers/dependencies: Future connector runtime milestone.

### FCC-P1-006 - P1 - Human-Readable Evidence Timeline

Epic: Product/UX, Safety/Permissions

Description: Convert receipt, event, audit, latency, Foundation Gate, and
rollback refs into a readable timeline.

Repo areas touched: `src/ultimate_ai_agent/core/storage/founder_loop.py`,
`apps/control-center/src/components/FounderLoopPanels.tsx`,
`apps/control-center/src/api/types.ts`, `apps/control-center/src/routes.tsx`,
`apps/control-center/src/mocks/controlCenterData.ts`, and focused tests.

Acceptance criteria: Evidence appears as human summaries first, with safe refs
and redaction status visible. Developer details never become the primary
operator UI. The current slice uses `GET /control-center/today/summary` and
does not add a route, operation ID, side-effect class, or runtime authority.

Required tests/verifiers: frontend tests, redaction tests,
`.venv/bin/python scripts/verify_control_center_frontend.py`.

Safety notes: No raw prompt, response, provider payload, path, log, environment
dump, credential material, or secret-like value.

Blockers/dependencies: Builds on completed FCC-P0-001 baseline and current
observability summaries.

### FCC-P1-009 - P1 - Draft-Only Email Response Proposal Contract

Epic: Tools/Integrations, Safety/Permissions

Description: Define draft response proposals that can be edited or rejected
but cannot send or mutate an account.

Repo areas touched: `src/ultimate_ai_agent/core/connectors/`,
`docs/connectors/`, `tests/`, and Founder Command Center board/task docs.

Acceptance criteria: Proposal includes safe summary, intent, recipient refs,
evidence refs, and blocked send/write fields. The current slice is
contract/test/docs only; it adds no connector runtime, route, Control Center
control, model call, memory write, context injection, or account authority.

Required tests/verifiers: contract tests proving send/write/delete/archive
fields are denied.

Safety notes: Draft-only. No connector writes.

Blockers/dependencies: FCC-P1-008.

### FCC-P1-010 - P1 - Relationship And Follow-Up Memory Schema

Epic: Memory/Knowledge, Business Cofounder Workflows

Description: Add reviewed memory schema for profile, project, relationship,
episodic, business, semantic-local knowledge, people, organizations, projects,
deals, promises, and follow-ups.

Repo areas touched: `src/ultimate_ai_agent/core/memory/`, focused tests, and
Founder Command Center currentness docs.

Acceptance criteria: Records require source/evidence refs, review state,
confidence, correction path, retention/delete/export posture, and no model-output
authority. The current slice is contract/test/docs only; it adds no automatic
memory write, delete execution, export execution, context injection, connector
runtime/write, route, UI control, model/provider authority, or production
authority.

Required tests/verifiers: memory tests and redaction tests.

Safety notes: Memory remains recall, not truth or authority. No automatic
capture, no automatic memory writes, and no hidden context injection.

Blockers/dependencies: FCC-P0-005.

### FCC-P1-011 - P1 - Settings Kill-Switch And Feature-Flag Spec

Epic: Safety/Permissions, Product/UX

Description: Specifies the Settings summary posture, safe defaults,
feature-flag posture, kill-switch posture, scoped permission-mode vocabulary,
disabled authority boundaries, and future Settings contract requirements.

Repo areas touched: `docs/control_center/`,
`docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`,
`docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`,
`docs/kanban/current_board.md`,
`docs/kanban/founder_command_center_board.md`, and
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`.

Acceptance criteria: Spec names local-only setup, redaction, feature-flag
posture, kill-switch posture, revocation refs, approval needs, audit refs,
receipt refs, rollback/safe-disable refs, blocked authority boundaries, and next
safe actions for any future setting. Planning labels do not grant authority.

Required tests/verifiers: documentation integrity and `git diff --check`.
Frontend/API tests are required only when frontend or route contracts are
implemented.

Safety notes: No authority toggle, credential collection, Settings mutation,
feature-flag write, kill-switch execution, revocation execution, route,
Control Center control, connector runtime/write, model/provider authority,
memory write, context injection, background job, shell/subprocess execution,
public distribution, or production authority is added by this spec.

Blockers/dependencies: Future Settings implementation requires a separate
scoped milestone with PolicyEngine, LocalApprovalAuthority, route manifest,
OpenAPI/API manifest, redaction, receipt/audit/revocation, rollback, and test
evidence.

### FCC-P1-012 - P1 - FastAPI Service-Module Extraction Plan

Epic: Core Agent Runtime, Infrastructure/Deployment

Description: Aligns Founder Command Center product-loop surfaces to the
accepted UAA-P1-052 service-module extraction plan without route drift or route
movement.

Repo areas touched: `docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md`,
`docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`,
`docs/kanban/current_board.md`,
`docs/kanban/founder_command_center_board.md`, and
`docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`.

Acceptance criteria: Plan covers system, runtime, planning, approval, memory,
file, evidence, integration, settings, and workflow surfaces using accepted
UAA-P1-052 module names. OpenAPI operation IDs, route count, auth posture,
side-effect classes, API manifest truth, route-status truth, and Foundation Gate
coverage remain stable.

Required tests/verifiers: documentation integrity, OpenAPI contract, API
manifest and Control Center route tests, Foundation Gate report-only, and
`git diff --check`.

Safety notes: Docs/plan-only. No route movement, backend route, APIRouter
module, operation ID change, side-effect class change, auth change, schema
change, dependency, Control Center UI, runtime authority, connector
runtime/write, model/provider call, memory write, context injection,
shell/subprocess execution, public distribution, or production authority.

Blockers/dependencies: UAA-P1-058 remains blocked unless UAA-P1-020,
UAA-P1-021, UAA-P1-052, Foundation Gate, OpenAPI, `/api/manifest`, and
route-status checks are green on the target branch.

## Backlog

### FCC-TODAY-RENDER-001 - P0 - Restore Accepted Today Render Fidelity

Epic: Product/UX, Today Spine, Visual Regression

Status: queued follow-up; begin after the current Social documentation/render
package is closed.

Description: Determine whether the reported Today image is an actual current
Control Center capture or a stale/mock/fallback artifact, then restore the
accepted Today composition and product language. The reported image with a
mock-fallback warning, technical route-state copy, and dense diagnostic table
is not the accepted Today design.

Acceptance criteria: Reproduce and identify the source of the mismatched Today
screen; compare it against the accepted current Today render and shell contract;
fix the actual UI, fixture, screenshot, or documentation source as appropriate;
add or update focused visual/product-language coverage; and save a verified
current capture without overstating backend authority.

Required tests/verifiers: focused Today frontend tests, applicable browser
smoke/visual checks, product-language verification, documentation integrity,
and `git diff --check`.

Safety notes: A visual correction does not grant connector, execution,
provider/model, public-release, or production authority. Preserve truthful
empty, partial, blocked, and fallback states while removing developer-facing
diagnostic treatment from the primary operator experience.

### FCC-LOOP-003 - P0 - Review-Stage Readability Refinement

Epic: Product/UX Safety

Status: proposed. Dependent on `FCC-TODAY-RENDER-001`; this refines the
accepted `FCC-LOOP-001` product loop rather than creating a parallel workflow.

Description: Make the existing Plans, Action Inbox, Today, and Evidence
surfaces read as one review journey: proposed, exact review required, decision
recorded, then receipt or explicit block. Use only existing governed read
models and redacted references.

Implementation plan:
[`FCC_LOOP_003_REVIEW_STAGE_READABILITY_IMPLEMENTATION_PLAN.md`](../implementation/FCC_LOOP_003_REVIEW_STAGE_READABILITY_IMPLEMENTATION_PLAN.md)

Acceptance criteria:

- Plan/action cards prioritize stage and safe next review step over diagnostic
  detail.
- Degraded, preview, stale, blocked, and missing state is explicit; it never
  implies a decision, receipt, or executed mutation.
- Existing scope, risk, approval, expiry, rollback, receipt, and evidence
  references remain inspectable through progressive disclosure.
- Existing approval controls, route guards, and post-decision reconciliation
  remain unchanged in behavior.

Required tests:

- Focused component/application coverage for stage mapping, degraded states,
  references, and retained decision guards.
- Desktop and narrow-width review after the Today rendering restoration.
- `make frontend-check`, `scripts/verify_control_center_frontend.py`,
  documentation integrity verification, and `git diff --check`.

Safety notes:

- No backend/API/OpenAPI changes, React-owned workflow truth, approval or grant
  issuance, action execution, plugin/connector runtime, tool/shell/browser
  authority, model/provider calls, memory retrieval, raw context/evidence
  display, telemetry upload, or dependencies.
- Do not promote preview or read-model data into authority; retain the current
  Python-core contract and existing route classifications.

### UAA-P1-070 - Memory Source And Provenance Model

Epic: Memory/Knowledge, Safety/Permissions

Status: implemented / ready for review.

Description: Defines safe source refs for manual notes, external assistant
review summaries, local chat, local coding summaries, task plans, action
proposals, evidence timeline refs, read-only calendar/email metadata refs, and
CRM-lite business records.

Acceptance criteria: Memory candidates identify where they came from
without storing raw prompts, raw responses, raw provider payloads, raw local
paths, raw logs, account identifiers, usernames, hostnames, credentials, or raw
private content.

Required tests/verifiers: focused memory/source schema tests and documentation
integrity. Bound by
`scripts/verify_uaa_p1_070_memory_source_provenance_model.py`.

Safety notes: No provider calls, browser import, connector runtime, account
auth, automatic memory write, context injection, or production authority.

### UAA-P1-071 - Memory Review Decision Capture

Epic: Memory/Knowledge, Safety/Permissions

Status: implemented / ready for review.

Description: Define accept, correct, reject, defer, merge, supersede, and
forget-request review states before any candidate becomes reviewed recall.

Acceptance criteria: Decisions carry actor refs, source refs, evidence refs,
stale-state posture, retention posture, audit refs, receipt refs, and blocked
states for unimplemented write/delete/export behavior.

Required tests/verifiers: focused Memory Review decision tests, Founder Loop
storage/API tests, frontend render checks, and documentation integrity. Bound by
`scripts/verify_uaa_p1_071_memory_review_decision_capture.py`.

Safety notes: Review decisions do not create automatic context injection,
connector writes, model/provider authority, or hidden memory writes.

### UAA-P1-072 - Business Memory And Memory Quality Controls

Epic: Memory/Knowledge, Business Cofounder Workflows

Status: implemented / ready for review.

Description: Shape reviewed candidate kinds for profile, project,
relationship, organization, deal/opportunity, promise, follow-up, preference,
decision, and commitment memory, plus dedupe, conflict, stale/expired,
low-confidence, source-missing, and evidence-missing posture.

Acceptance criteria: Business memory shows provenance, review state,
correction path, stale-state posture, retention/delete/export posture, quality
posture, and evidence refs. It feeds Today, Action Inbox, Evidence Timeline,
and Weekly CEO Review without external CRM writes or account sync.

Required tests/verifiers: memory schema tests, raw-content denial tests,
memory quality tests, frontend render tests, and documentation integrity. Bound
by `scripts/verify_uaa_p1_072_business_memory_quality_controls.py`.

Safety notes: Local CRM-lite only. No connector writes, hidden sync, account
auth, external CRM writes, account sync, raw private-content display, or
production authority.

### UAA-P1-073 - Plans To Reviewable Action Envelopes

Epic: Plans/Actions, Safety/Permissions

Status: implemented / ready for review.

Description: Plans must produce approve/edit/reject/defer-ready Action
envelopes with exact scope, side-effect class, risk, approval requirement,
idempotency, expiry, evidence refs, expected receipt refs, rollback or
safe-disable posture, and blocked-state reasons.

Acceptance criteria: Classification and decomposition alone are not enough.
The user can review an Action envelope, edit its scope, reject it, defer it, or
approve it only through exact scoped authority when such authority exists.

Required tests/verifiers: plan/action envelope contract tests, storage/API
tests, frontend read-only render tests, raw-content denial tests, and
documentation integrity. Bound by
`scripts/verify_uaa_p1_073_plans_action_envelopes.py`.

Safety notes: No action execution, approval grant capture, reusable approval
ref authority, shell/subprocess execution, connector writes, broad autonomy, or
production authority.

### UAA-P1-074 - Chat Local Operator Surface

Epic: Chat, Local Model, Product/UX

Status: Done.

Description: Chat sends a local turn, shows model/runtime/auth/tool-denial
truth, produces safe evidence refs, and hands off to Plans or Actions as
proposals only.

Acceptance criteria: A user can see whether local model runtime, auth, route
availability, and tool/function denial are true. Model output is not treated as
truth, memory, approval evidence, or execution authority.

Required tests/verifiers: `tests/test_uaa_p1_074_chat_local_operator_surface.py`,
`tests/test_founder_loop_storage.py`,
`tests/test_control_center_founder_loop_api.py`,
`apps/control-center/src/App.test.tsx`,
`scripts/verify_uaa_p1_074_chat_local_operator_surface.py`, and
`docs/schemas/chat_local_operator_surface.schema.json`.

Safety notes: No provider SDK calls, web fetching, tool execution, automatic
memory write, hidden context injection, connector write, shell/subprocess
execution, action execution, approval grant capture, public beta, public
distribution, or production authority.

### UAA-P1-075 - Governed Code Workbench V1

Epic: Code/Workspace, Evidence/Receipts, Safety/Permissions

Description: Build a narrow, better-governed code path before chasing broad
coding-agent autonomy: repo-local safe diff summary refs, validation proof
refs, exact approval requirement refs, expected apply and rollback receipt
refs, and evidence timeline binding.

Acceptance criteria: Code proposals show scope, safe diff summary ref,
validation plan, validation result refs, approval requirement, expected apply
receipt, expected rollback receipt, and Evidence history entries.

Required tests/verifiers: file/diff/apply/rollback tests, redaction tests,
frontend render tests when surfaced, OpenAPI/API manifest tests if routes
change, and documentation integrity.

Safety notes: No unrestricted shell, remote execution, broad coding-agent
autonomy, raw path evidence, or unapproved mutation.

### UAA-P1-076 - Cross-Surface Memory Intake

Epic: Memory/Knowledge, Product/UX

Description: Bind memory proposals from Today, Chat, Plans, Actions, Evidence,
local coding summaries, and manual external-assistant review imports.

Acceptance criteria: Each intake path produces bounded safe summaries,
source/evidence refs, missing-evidence posture, confidence posture, and next
safe action labels. External assistant output is treated as untrusted review
input, not truth or authority.

Required tests/verifiers: cross-surface fixture tests and Control Center
render tests for proposed candidates.

Safety notes: No automatic import from ChatGPT, browser state, local shell
history, provider payloads, account content, or raw files.

### UAA-P1-077 - Memory-To-Loop Binding

Epic: Product/UX, Memory/Knowledge

Status: Done.

Description: Today, Action Inbox, Evidence Timeline, Memory Review, and Weekly
CEO Review show memory candidates, accepted recall display-only refs,
corrections, rejected items, follow-up commitments, stale-state posture,
memory-derived Action proposals, and missing-evidence blockers.

Acceptance criteria: Memory is visible as part of the daily operating loop,
not a hidden background store. Every memory-derived action proposal names its
source refs, evidence refs, side-effect class, and approval posture.

Proof: `docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md`,
`docs/schemas/memory_to_loop_binding.schema.json`,
`scripts/verify_uaa_p1_077_memory_to_loop_binding.py`,
`tests/test_uaa_p1_077_memory_to_loop_binding.py`, Founder Loop storage/API
tests, and Control Center render tests.

Safety notes: Memory-derived UI does not grant approval, execute work, inject
context, or mutate external systems.

### UAA-P1-078 - Private Beta-Readiness Gate

Status: Implemented / ready for review.

Epic: Testing/Evals, Product/UX, Safety/Permissions

Description: Define the local/private beta-test acceptance gate for Start Here,
Setup Assistant, Today, Morning Briefing, Action Inbox, Proof Detail, Memory
Review, Evidence Timeline, Trust Authority Map, safe local Chat/Plans handoff,
governed Code proposal refs, CRM-lite follow-ups, and Dogfood Live Loop.

Acceptance criteria: Beta-readiness evidence distinguishes pass, fail, skipped,
blocked, partial, mock-only, and accepted-failure states; no public beta,
public distribution, production readiness, broad autonomy, connector write, or
provider/model authority is claimed.

Proof: `docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md`,
`docs/schemas/private_beta_readiness_gate.schema.json`,
`scripts/verify_uaa_p1_078_private_beta_readiness_gate.py`,
`tests/test_uaa_p1_078_private_beta_readiness_gate.py`, Founder Loop
storage/API tests, and Control Center render tests.

Safety notes: Private local beta-test readiness is not public beta or
production authority.

### UAA-P1-079 - User Intent Understanding V1

Epic: Intent/Planning, Product/UX, Safety/Permissions

Status: Implemented / ready for review.

Description: After the loop has reviewed memory, evidence history, Action
envelopes, Chat receipts, and Code receipts, UAA-P1-079 shapes a reviewable
intent classifier as safe-ref proposal metadata.

Acceptance criteria: Intent proposals include confidence, source refs,
ambiguity posture, ask/act/defer routing, and evidence refs. Low-confidence or
conflicting intent asks the user rather than acting.

Proof: `docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md`,
`docs/schemas/user_intent_understanding.schema.json`,
`scripts/verify_uaa_p1_079_user_intent_understanding.py`,
`tests/test_uaa_p1_079_user_intent_understanding.py`, Founder Loop
storage/API tests, and Control Center render tests.

Safety notes: Intent classification is not hidden authority, approval, memory
truth, action execution, context injection, Code apply, provider/model
authority, connector authority, public beta, production authority, or broad
autonomy.

### UAA-P1-080 - API Route Classification And Public/Protected Inventory

Status: Implemented / ready for review.

Epic: API Boundary, Security/Permissions

Description: Classify every FastAPI route as `public_metadata`,
`local_readonly`, `local_sensitive`, or `mutating_requires_authority` and map
public/protected posture before new runtime authority is claimed.

Acceptance criteria: Route inventory, OpenAPI/API manifest contract, and Control
Center route posture distinguish harmless metadata from sensitive state and
mutating authority paths without adding routes or authority.

Proof: `docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md`,
`docs/schemas/api_route_classification.schema.json`,
`tests/fixtures/api_route_inventory_133.json`,
`scripts/verify_uaa_p1_080_api_route_classification.py`,
`tests/test_api_manifest.py`, `tests/test_api_route_inventory_fixture.py`,
`tests/test_control_center_api_routes.py`, and Control Center API Routes render
tests.

Safety notes: Classification does not grant auth, approval, runtime behavior,
middleware, headers, CORS, idempotency enforcement, rate limits, public beta,
distribution, or production authority.

### UAA-P1-081 - Centralized FastAPI Security Headers

Status: Implemented / ready for review.

Epic: API Boundary, Browser-Facing Control Center

Description: Adds centralized response security headers:
`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` or strict
equivalent, `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'`,
Permissions-Policy denying unused browser capabilities, `Content-Security-Policy`
with strict posture and documented local dev loopback connect exceptions, and
HSTS only for actual HTTPS requests.

Acceptance criteria: Security-header posture is centralized, tested, and
documented before browser-facing production-readiness claims.

Proof: `docs/api/UAA_P1_081_CENTRALIZED_FASTAPI_SECURITY_HEADERS.md`,
`docs/schemas/api_security_headers.schema.json`,
`scripts/verify_uaa_p1_081_fastapi_security_headers.py`,
`tests/test_api_security_headers.py`, and `tests/test_api_manifest.py`.

Safety notes: Security headers are browser hardening only. They do not grant
auth, sessions, CORS, idempotency enforcement, rate limits, route authority,
runtime authority, public beta, distribution, or production authority.

### UAA-P1-082 - Explicit Loopback CORS Allowlist

Status: Implemented / ready for review.

Epic: API Boundary, Browser-Facing Control Center

Description: Adds a server-side CORS policy that allows only explicit local
Control Center origins: `http://localhost:5173`, `http://127.0.0.1:5173`,
`http://[::1]:5173`, `http://localhost:4173`, `http://127.0.0.1:4173`, and
`http://[::1]:4173`.

Acceptance criteria: Broad wildcard CORS is denied, configured local origins are
documented, CORS credentials are disabled, blocked origins receive no allow
headers, and CORS is labeled browser hardening rather than authentication.

Proof: `docs/api/UAA_P1_082_EXPLICIT_LOOPBACK_CORS_ALLOWLIST.md`,
`docs/schemas/api_loopback_cors.schema.json`,
`scripts/verify_uaa_p1_082_loopback_cors.py`, `tests/test_api_cors.py`, and
`tests/test_api_manifest.py`.

Safety notes: CORS is browser hardening only. It does not grant auth, sessions,
route authority, runtime authority, connector writes, provider/model calls,
idempotency enforcement, rate limits, public beta, distribution, or production
authority.

### UAA-P1-083 - Local Bearer Or Session Gate For Sensitive Routes

Epic: API Boundary, Security/Permissions

Status: Implemented.

Description: Adds a configured local-first bearer gate for protected route
classifications that expose logs or observability events, task runs, approvals,
memory, file previews or write proposals, model gateway behavior, action
previews, or sensitive runtime state.

Acceptance criteria: Public routes are limited to harmless metadata such as
health/version and possibly safe manifest data; sensitive routes require the
local gate before authority claims.

Required tests/verifiers: `tests/test_api_local_auth_gate.py`,
`tests/test_api_manifest.py`, `tests/test_api_cors.py`,
`scripts/verify_uaa_p1_083_local_auth_gate.py`, OpenAPI/API manifest checks,
and docs integrity.

Safety notes: No enterprise auth, multi-user auth, OAuth, roles, password flow,
rate limit, idempotency enforcement, public beta, distribution, production
readiness, or production authority is added by this implementation.

### UAA-P1-084 - Mutating Route Idempotency Enforcement Audit

Status: Implemented / ready for review.

Epic: API Boundary, Durability/Safety

Description: Audit every mutating route and require an idempotency key or scoped
idempotency ref aligned with UAA's durable run and action-envelope safety model.

Acceptance criteria: Mutating routes cannot claim authority without
idempotency, audit, approval, receipt, and rollback/safe-disable posture.

Required tests/verifiers: `tests/test_api_idempotency_audit.py`,
`tests/test_api_manifest.py`, `tests/test_api_route_inventory_fixture.py`,
`tests/test_api_cors.py`,
`scripts/verify_uaa_p1_084_mutating_route_idempotency.py`, OpenAPI/API
manifest checks, and docs integrity.

Safety notes: Implemented as a runtime idempotency header gate before mutating
handler execution only. It does not add durable dedupe, exactly-once execution,
replay execution, rate limits, mutation authority, public beta, distribution,
production readiness, or production authority.

### UAA-P1-085 - Targeted Rate Limits For Expensive And Sensitive Routes

Status: Implemented.

Epic: API Boundary, Performance/Safety

Description: Added targeted local fixed-window rate limits to likely abuse or
heavy paths first: model/chat endpoints, task decomposition endpoints, action
preview/proposal endpoints, and routes that trigger expensive validation or
local model behavior.

Acceptance criteria: Rate limits are targeted and evidence-based; manifest and
route inventory expose rate-limit posture and 429 responses include safe
policy/group/retry metadata.

Required tests/verifiers: `tests/test_api_rate_limits.py`,
`tests/test_api_manifest.py`, `tests/test_api_route_inventory_fixture.py`,
`tests/test_api_cors.py`,
`scripts/verify_uaa_p1_085_targeted_rate_limits.py`, OpenAPI/API manifest
checks, and docs integrity.

Safety notes: Implemented as process-local in-memory fixed-window protection
for targeted routes only. It is not auth, a distributed quota store, a durable
rate-limit store, billing quota, tenant quota, broad production authority,
public beta, distribution, or production readiness.

### UAA-P1-086 - API Boundary Enforcement Tests

Status: Implemented.

Epic: API Boundary, Tests/Verification

Description: Added OpenAPI, `/api/manifest`, and route inventory checks that
enforce route classification, protected-route auth posture, approval posture,
mutating idempotency posture, security headers, CORS policy, and targeted
rate-limit posture where scoped.

Acceptance criteria: Sensitive and mutating routes cannot silently drift outside
their declared local auth, approval, idempotency, redaction, and browser-hardening
posture.

Required tests/verifiers:
`tests/test_api_boundary_enforcement.py`,
`scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py`, the combined
API verifier lane, OpenAPI/API manifest checks, route inventory fixture checks,
and documentation integrity.

Safety notes: Enforcement tests do not grant runtime authority; they make missing
perimeter work visible.

### UAA-P1-087 - Private Operator Trial And UI Functional Tuning

Epic: Product/UX, Private Beta Readiness

Description: After UAA-P1-080 through UAA-P1-086, run local/in-person founder
testing and tune Today, Actions, Memory, Evidence, Chat handoff, blocked-state
language, and CRM-lite follow-up flow before moving to P2/provider, packaging,
public distribution, or commercialization shaping.

Sub-milestone order:

- `UAA-P1-087.1` Local Launcher Dual-Surface Boot Readiness: implemented. The
  existing launcher and macOS `.command` path start Control Center first and
  OpenWebUI as the secondary shell with truthful readiness, stop, safe log-ref,
  and blocked states.
- `UAA-P1-087.2a` Private Trial Packet And UI Tuning Surface: implemented. The
  safe-ref-only packet and read-only `/private-trial` surface collect manual
  smoke checklist refs, friction refs, UI/copy task refs, core-loop gap refs,
  and blocked authority refs for the full private trial.
- `UAA-P1-087.2b` Private Trial Findings Capture And Acceptance Ledger:
  implemented. The safe-ref-only acceptance ledger and read-only
  `/private-trial` visibility collect manual smoke step refs, pending surface
  review refs, acceptance question refs, tuning decision refs, and blocked
  authority refs before accepted/revised findings exist.
- `UAA-P1-087.2c` Private Trial Manual Review Intake Scaffold: implemented.
  The safe-ref-only scaffold and read-only `/private-trial` visibility collect
  unanswered pending answer refs, missing implementation refs, deferred
  decision refs, and blocked authority refs before accepted/revised findings
  exist.
- `UAA-P1-087.2` In-Person Private Operator UI Functional Tuning: deferred
  until more Founder Loop implementation exists; later, run founder testing
  through the proven boot path and capture manual smoke evidence, friction
  notes, copy/UI tasks, and core loop gaps.
- `UAA-P1-087.3` Native SwiftUI Boot Cockpit Planning And Source-Only Scaffold:
  only after full UAA-P1-087.2 evidence is accepted, plan/source-scaffold the
  native macOS boot cockpit over the same fixed launcher contracts.

Acceptance criteria: Trial produces a manual smoke checklist, usability/friction
findings, UI/copy tuning tasks, and beta-readiness evidence refs. It proves the
core loop is functional enough to test with the founder/operator and keeps
authority boundaries visible.

Required tests/verifiers: future frontend checks, manual smoke evidence,
documentation integrity, and product-language checks.

Safety notes: Local/private trial only. No public beta, public distribution,
connector writes, action execution, memory writes, provider/model authority,
Code apply, hidden automation, arbitrary shell execution, Docker installation,
LaunchAgent, daemon, signing, notarization, OpenWebUI plugin/admin mutation, or
production authority.

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

## Deferred Future Product Lanes

### FCC-SOCIAL-001 - P2 - Social Media Intelligence Read-Only

Epic: Product/UX, Creator Operations, Governed Read Models

Description: Build the accepted creator-focused Social command view and typed
projections into Calendar, Work Board, Communications, CRM, Studio, Evidence,
and Memory. The first milestone remains read-only and preserves canonical app
ownership.

Activation gate: Work Board, CRM, and Communications must pass
`contract-ref:social-read-only-foundation-profile:v1`. The profile is currently
partial: Communications now has a backend-owned reviewed local projection with
API/CLI parity and a real Control Center view; Work Board now has a strict
backend-owned read-only `Social Content` saved projection and Control Center
filter. The founder accepted the displayed Social direction for private
dogfooding, so cosmetic iteration no longer blocks gap closure. The CRM Social
relationship projection and strict independent-promotion profile
ledger/verifier remain missing. The profile does not mark any owner product
globally complete.

Board posture: Deferred. This card is not current WIP and is not eligible as
"what's next" while the profile lacks accepted evidence. Passing the profile
makes it eligible for prioritization; it does not automatically
outrank current P0/P1 work.

Execution prompt:
`docs/prompts/implement_social_media_intelligence_after_foundation_gates.prompt.md`.

Design and product refs:
`docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md` and
`docs/design/control_center_north_star/renders/social-media-v1/README.md`.

Safety notes: No live source access, OAuth, publishing, replies, deletes,
moderation, external scheduling, provider/model calls, browser scraping,
background sync, broad automation, public release, or production authority.
This card grants no runtime capability.

### FCC-FINANCE-001 - P2 - Finance & Compliance Local-First Program

Epic: Product/UX, Founder Operations, Books, Tax Readiness, Compliance

Description: Build a first-party UAA Finance application that keeps books
continuously organized rather than reconstructed at period end. The complete
vision includes local double-entry truth, manual/file import, a review-and-learn
transaction inbox, receipt and business-context capture, reconciliation,
spending intelligence, tax-readiness/accountant packets, and sourced
entity/jurisdiction obligations. Finance projects exact work into Today,
Morning Briefing, Action Inbox, Calendar, Work Board, Evidence, News, Memory,
and Chat without duplicating canonical truth.

Activation gates: FIN-000 planning and synthetic render acceptance may proceed
now. Runtime begins only after ECO-001, first-class Boards/Kanban, Calendar,
Today, Action Inbox, and ECO-008 ChangeSets are accepted. The local product
precedes live bank or compliance connections; every adapter, accountant-access
lane, payment, and filing handoff requires separate promotion.

Board posture: Blocked pending activation-record merge and explicit coordinator
unblock. The
separately bounded `dev-task:finance-fin001-synthetic-kernel` reserves the next
`product_surface` slot, but is not In Progress until a fresh lane-vacancy check
and coordinator claim receipt exist. The checklist and claim procedure are in
`docs/product/UAA_FINANCE_FIN001_ACTIVATION_RECORD.md`. The broader Queue V2 Q26
program task and later Finance milestones remain blocked/deferred.

Planning refs: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`,
`docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`,
`docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`,
`docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md`,
`docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`, and
`docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md`.

FIN-000 review readiness: The exact sixteen-image candidate manifest is locked,
and the independent review packet, gallery, state/accessibility matrix, pending
role ledger, and verifier are implemented. Product/design, accounting-domain,
privacy/security, accessibility, and implementation decisions remain pending;
this is review readiness, not render acceptance or runtime promotion.

Safety notes: No financial-account connection, aggregation provider, raw
credential storage, maintained compliance feed, tax/legal/accounting advice,
accountant invitation, payment, transfer, signature, filing, external write,
provider/model call, browser automation, background sync, broad automation,
public release, or production authority. This card grants no runtime capability.

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
