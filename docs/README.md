# Ultimate AI Agent Docs

This is the active documentation entrypoint. Start with UAA as the
Founder Command Center product path: a local-first professional AI command
center for Today, Inbox, Plans, Actions, Memory, Evidence, and Settings. The
front-door product story lives in `README.md`; the strategic narrative lives in
`docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`; the implementation
truth and blocked states live in
`docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.

The Control Center is the technical web shell, Founder Command Center is the
user-facing product name, and the Founder Loop is the bounded product spine.
Python Agent Core, PolicyEngine, LocalApprovalAuthority, route classification,
OpenAPI checks, and Foundation Gate checks remain the authority boundaries.

Status: active
Current through: v0.104.0 plus accepted checkpoint-m169, completed
UAA-P1-065 Founder Command Center review cleanup, completed UAA-P1-067
Today-Spine Founder Command Center beta-readiness planning/currentness work,
completed UAA-P1-068 Today Product Spine Contract work, completed UAA-P1-069
Evidence History Grammar work, completed UAA-P1-070 Memory Source And
Provenance Model work, completed UAA-P1-071 Memory Review Decision Capture
work, completed UAA-P1-072 Business Memory And Memory Quality Controls work,
completed UAA-P1-073 Plans To Reviewable Action Envelopes work, completed
UAA-P1-074 Chat Local Operator Surface work, completed UAA-P1-075 Governed
Code Workbench V1 work, completed UAA-P1-076 Cross-Surface Memory Intake work,
completed UAA-P1-077 Memory-To-Loop Binding work, completed UAA-P1-078
Private Beta-Readiness Gate work, and completed UAA-P1-079 User Intent
Understanding V1 work, completed UAA-P1-080 API Route Classification And
Public/Protected Inventory work, completed UAA-P1-081 Centralized FastAPI
Security Headers work, and completed UAA-P1-082 Explicit Loopback CORS
Allowlist work, and completed UAA-P1-083 Local Bearer Or Session Gate For
Sensitive Routes work, and completed UAA-P1-084 Mutating Route Idempotency
Enforcement Audit work, completed UAA-P1-085 Targeted Rate Limits For
Expensive And Sensitive Routes work, completed UAA-P1-086 API Boundary
Enforcement Tests work, completed UAA-P1-087.1 Local Launcher Dual-Surface
Boot Readiness work, completed UAA-P1-087.2a Private Trial Packet And UI
Tuning Surface work, and completed UAA-P1-087.2b Private Trial Findings Capture
And Acceptance Ledger work, and completed UAA-P1-087.2c Private Trial Manual
Review Scaffold work. Full UAA-P1-087.2 in-person private UI functional tuning
remains planned but deferred until more Founder Loop implementation exists and
accepted or revised local/private findings can be recorded later.
UAA-P1-087.3 native SwiftUI boot cockpit planning/source-only scaffold stays
deferred behind full UAA-P1-087.2. FCC-V1-000 Control Center Release Surface
Manifest work is complete with release-status truth, manifest/schema, verifier,
and focused tests. FCC-V1-001 API Perimeter For Real Mutations is complete as
contract/verifier coverage with duplicate replay runtime still blocked until
route-owner receipt storage exists outside routes that implement their own
receipt-backed replay. FCC-V1-002 Action Inbox Backend State Machine is
complete for backend-owned approve/edit/reject/defer decision state, local
receipt refs, and Control Center receipt visibility without action execution or
new external authority. FCC-V1-003 Founder Loop V1 Vertical Slice is complete
for Today-to-Action envelope creation, exact decision receipts, Evidence
Timeline update, and CLI inspection parity without action execution or new
external authority. FCC-V1-004 Control Center Chat Durable Receipt And Handoff
is complete for durable safe Chat turn receipts and reviewable Actions/Plans
handoff receipts without action execution, memory writes, model-output
authority, connector writes, provider calls, or new external authority.
FCC-V1-005 Memory Review Decisions is complete for backend-owned
accept/correct/reject receipts without memory truth authority, context
injection, CRM/account sync, connector writes, action execution, public beta, or
production authority. FCC-V1-006 Evidence Timeline Productization is complete
for a backend-owned safe-ref Evidence Timeline index without approval authority,
rollback execution, action execution, context injection, connector writes, public
beta, or production authority. FCC-V1-007 Promotion And Proof Lane is complete
for `founder_loop_v1_proofed` promotion of `/actions`, `/chat`, `/memory`, and
`/evidence` route surfaces only, with `/today` partial and `/inbox`, `/settings`,
and `/models` still blocked or partial; it adds no action execution, context
injection, connector writes, public beta, public release, or production
authority. The
sequence is tracked in
`docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md`.
The completed bounded Founder Loop V1 productization conveyor is tracked in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md` for `FCC-V1-000` through
`FCC-V1-007`: release surface manifest, API perimeter, Action Inbox backend
decisions, Today-to-Action vertical loop, Chat durable receipts and handoff,
Memory Review accept/correct/reject decisions, Evidence Timeline
productization, and proofed route-surface promotion.

This is the human-facing entrypoint for active documentation. The full catalog
lives in `docs/DOCUMENTATION_INDEX.md`; historical releases, checkpoint imports,
and older roadmap snapshots stay under `docs/archive/` as audit artifacts, not
current implementation claims.

Portfolio reviewers should start with `README.md`,
`docs/portfolio/CURRENT_STATUS.md`, `docs/portfolio/PRODUCT_NORTH_STAR.md`,
`docs/portfolio/SCREENSHOTS.md`, `docs/portfolio/GOLDEN_PATH_DEMO.md`, and
`docs/portfolio/CASE_STUDY.md` before opening the deeper roadmap and
product-truth ledgers.

## Start Here

| Need | Start with |
|---|---|
| Portfolio demo path | `README.md`, `docs/portfolio/CURRENT_STATUS.md`, `docs/portfolio/PRODUCT_NORTH_STAR.md`, `docs/portfolio/SCREENSHOTS.md`, `docs/portfolio/GOLDEN_PATH_DEMO.md`, `docs/portfolio/CASE_STUDY.md` |
| Portfolio overview and case study | `README.md`, `docs/portfolio/CURRENT_STATUS.md`, `docs/portfolio/PRODUCT_NORTH_STAR.md`, `docs/portfolio/CASE_STUDY.md` |
| Product story and current repository truth | `README.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` |
| Active roadmap and board | `docs/canonical/09_roadmap.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`, `docs/kanban/current_board.md` |
| Founder Command Center planning | `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, `docs/kanban/founder_command_center_board.md` |
| Operational maturity and authority ramp | `docs/control_center/OPERATIONALIZATION_LADDER.md`, `docs/control_center/operational_maturity_manifest.json`, `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`, `docs/control_center/authority_candidate_scorecard.json` |
| Version and checkpoint currentness | `VERSION.md`, `docs/release_notes/v0_104_0.md`, `docs/release_notes/checkpoint_m169.md` |
| Tag history and future tag convention | `docs/releases/TAG_CATALOG.md`, `docs/maintenance/RELEASE_PROCESS.md`, `docs/maintenance/SEMVER_POLICY.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| Product claims and gaps | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` |
| Canonical navigation | `docs/DOCUMENTATION_INDEX.md`, `docs/canonical/CANONICAL_DOC_MAP.md` |
| API boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md` |
| Verification maintainability | `docs/verification/milestone_status_manifest.json`, `docs/verification/verification_maintainability_policy.json` |
| Computer Use / CUA contract lane | `docs/cua/COMPUTER_USE_CUA_CONTRACT.md`, `docs/cua/cua_release_surface_manifest.json` |
| Security posture | `SECURITY.md`, `docs/security/SECURITY_TRIAGE_RUNBOOK.md` |
| Documentation policy | `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md` |

## Current Baseline Packet

The product/package baseline is `v0.104.0` / `0.104.0`. The latest accepted
repository checkpoint tag is `checkpoint-m169`. The latest accepted local model
lane checkpoint tags remain `checkpoint-m166` and `checkpoint-m167`.

Current release and checkpoint refs:

```text
docs/archive/releases/v0_104_0/README_IMPORT.md
docs/archive/releases/v0_104_0/master_plan.md
docs/release_notes/v0_104_0.md
docs/implementation/foundation_gate_implementation_plan_v0_104_0.md
docs/release_notes/checkpoint_m169.md
docs/release_notes/checkpoint_m166.md
docs/release_notes/checkpoint_m167.md
```

The active Operator Runtime Excellence sequence now points from completed
UAA-P1-065 Founder Command Center review cleanup, completed UAA-P1-067
Today-spine beta-readiness planning/currentness, completed UAA-P1-068 Today
Product Spine Contract, completed UAA-P1-069 Evidence History Grammar,
completed UAA-P1-070 Memory Source And Provenance Model, completed
UAA-P1-071 Memory Review Decision Capture, completed UAA-P1-072 Business
Memory And Memory Quality Controls, and completed UAA-P1-073 Plans To
Reviewable Action Envelopes, and completed UAA-P1-074 Chat Local Operator
Surface, completed UAA-P1-075 Governed Code Workbench V1, and completed
UAA-P1-076 Cross-Surface Memory Intake, and completed UAA-P1-077
Memory-To-Loop Binding, and completed UAA-P1-078 Private Beta-Readiness Gate
to completed UAA-P1-079 User Intent Understanding V1, and completed UAA-P1-080
API Route Classification And Public/Protected Inventory, and completed
UAA-P1-081 Centralized FastAPI Security Headers, and completed UAA-P1-082
Explicit Loopback CORS Allowlist, and completed UAA-P1-083 Local Bearer Or
Session Gate For Sensitive Routes, and completed UAA-P1-084 Mutating Route
Idempotency Enforcement Audit, completed UAA-P1-085 Targeted Rate Limits
For Expensive And Sensitive Routes, completed UAA-P1-086 API Boundary
Enforcement Tests, completed UAA-P1-087.1 Local Launcher Dual-Surface Boot
Readiness, completed UAA-P1-087.2a Private Trial Packet And UI Tuning Surface,
and completed UAA-P1-087.2b Private Trial Findings Capture And Acceptance
Ledger, completed UAA-P1-087.2c Private Trial Manual Review Scaffold, and
completed FCC-V1-000 Control Center Release Surface Manifest, FCC-V1-001
API Perimeter For Real Mutations, and FCC-V1-002 Action Inbox Backend State
Machine, completed FCC-V1-003 Founder Loop V1 Vertical Slice, completed
FCC-V1-004 Chat Durable Receipt And Handoff, completed FCC-V1-005 Memory
Review Decisions, completed FCC-V1-006 Evidence Timeline Productization, and
completed FCC-V1-007 Promotion And Proof Lane.
Full UAA-P1-087.2
local/private UI tuning and UAA-P1-087.3 private UI trial/native boot planning
are deferred until the Founder Loop has more real implementation to test. No
active FCC-V1 conveyor milestone remains. UAA-P1-066 is implemented as a
strictly read-only Local Model Control Center inventory/status support lane at
`GET /control-center/local-models/status`.
`FCC-V1-000` through `FCC-V1-007` are the Founder Loop V1 productization
conveyor after the private-trial sequencing: completed release surface truth,
real mutation perimeter contract/verifier coverage, and backend-owned
Action decisions, then completed Today item to Action envelope to exact
approval/edit/reject/defer receipt, completed Chat receipt/handoff, Memory Review decision receipts, Evidence
Timeline productization, and proof-lane promotion.
This sequence makes Today the product spine and keeps memory,
Evidence, Plans, Chat, Code, and Actions bound to safe refs, review decisions,
receipts, and rollback posture. It adds no production authority, public beta,
public distribution, broad autonomy, shell/subprocess authority, unrestricted
network/browser automation, connector writes, plugin runtime import, mobile
control, model/provider authority, raw prompt export, raw response export, raw
provider payload export, or no-secret-output regression.

## Active Program Areas

| Area | Current docs |
|---|---|
| Operator Runtime Excellence | `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` |
| Founder Command Center product-loop planning | `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, `docs/kanban/founder_command_center_board.md`, `docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`, `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`, `docs/metrics/NORTH_STAR_METRICS.md`, `docs/codex/CODEX_EXECUTION_PROMPTS.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| Product truth packet | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md` |
| Control Center readiness | `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/control_center/ROUTE_STATUS_MANIFEST.md`, `docs/control_center/route_status_manifest.json`, `docs/control_center/release_surface_manifest.json`, `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`, `docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`, `docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`, `docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md`, `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`, `docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`, `docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md`, `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`, `docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md`, `docs/macos/private_operator_14_day_dogfood_harness_v1.json`, `docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md`, `docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md`, `docs/control_center/visual_regression_manifest.json`, `docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md`, `docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md`, `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`, `docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`, `docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`, `docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md`, `docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md`, `docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md`, `docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md`, `docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md`, `docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md`, `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md`, `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`, `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`, `docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md`, `docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md`, `docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md`, `docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md` |
| Local model production-readiness lane | `docs/production/M166_PRODUCTION_AUTHORITY_GATE.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Local model operations | `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md`, `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`, `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md` |
| Release verification and evidence | `docs/production/RELEASE_VERIFICATION_LANES.md`, `docs/production/RELEASE_EVIDENCE_PACKET.md`, `docs/production/BACKUP_RESTORE_VERIFICATION.md`, `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`, `docs/production/LOCAL_RUNTIME_PACKAGING.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Verification maintainability | `docs/verification/milestone_status_manifest.json`, `docs/verification/verification_maintainability_policy.json` |
| Computer Use / CUA contract lane | `docs/cua/COMPUTER_USE_CUA_CONTRACT.md`, `docs/cua/cua_release_surface_manifest.json` |
| Performance and API cache | `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `docs/api/SAFE_STATIC_MANIFEST_CACHING.md` |
| Redacted observability | `docs/observability/SESSION_LOGGING_M167.md` |
| Plugin/skill ecosystem boundary | `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`, `docs/schemas/plugin_skill_trust_manifest.schema.json`, `docs/schemas/inspectable_extension_catalog.schema.json`, `docs/schemas/extension_activation_grant.schema.json` |

The Founder Command Center docs are planning and execution artifacts for the
next product loop. They do not grant production authority, public distribution,
broad autonomy, runtime connector writes, unrestricted shell/browser/network
authority, plugin runtime import, provider/model authority, mobile runtime, or
new backend/Control Center behavior by themselves.

## Verification Commands

Use these before release-facing claims or milestone status changes:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_verifier_maintainability.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

The named release lanes are described in
`docs/production/RELEASE_VERIFICATION_LANES.md`. Release evidence packets are
defined in `docs/production/RELEASE_EVIDENCE_PACKET.md`.

## Historical Docs

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

Historical notes such as v0.29.5 documentation policy polish, v0.38.0 M34
file capability review, v0.41.0 M37 review approval capture, and M57-M60
planning remain available under `docs/archive/` and the full documentation
index. They are not current release or production-readiness claims.
