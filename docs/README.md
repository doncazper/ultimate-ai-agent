# Ultimate AI Agent Docs

This is the active documentation entrypoint. Start with UAA as the
Founder Command Center product path: a local-first professional AI command
center for Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust,
Settings, Plans, and supporting source readiness. The
front-door product story lives in `README.md`; the strategic narrative lives in
`docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`; the implementation
truth and blocked states live in
`docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.

The Control Center is the technical web shell, Founder Command Center is the
user-facing product name, and the Founder Loop is the bounded product spine.
Python Agent Core, PolicyEngine, LocalApprovalAuthority, route classification,
OpenAPI checks, and Foundation Gate checks remain the authority boundaries.
Managed portable mission-evidence signing is documented in
`docs/runtime/UAA_PORTABLE_MISSION_EVIDENCE_SIGNING.md`; it is a macOS-only,
exact dispatcher-governed Ed25519 lane and is not signer identity, notarization,
non-repudiation, an external timestamp, or execution authority.

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
Review Scaffold work, completed UAA-P1-088 Agent Module Maturity Review V2
work as a review/scoring/read-model lane only, completed UAA-P1-089
Top-Level Decision Router Contract work as a contract/read-model lane only,
and completed UAA-P1-090 Task Decomposition Proposal Engine work as a
proposal/read-model lane only.
Full UAA-P1-087.2 in-person private UI functional tuning remains planned but
deferred until more Founder Loop implementation exists and accepted or revised
local/private findings can be recorded later.
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
Founder Loop V1 product proof pass adds a backend-owned
`founder_loop_v1_product_proof_read_model` across Start Here, Today, Action
Inbox, Proof, Evidence, Memory, Trust, and Settings for one repo-safe loop. It
also preserves the seeded/demo-safe proof path from Morning Briefing to Today,
Action Inbox decision receipts, Evidence Timeline, Memory Review, and Weekly
Review, with CLI inspection parity and no provider/model calls, connector
writes, browser/live web, background autonomy, public release, or production
authority.
FCC-THREAD-001 Unified Work Thread adds a backend-owned
`unified_work_thread_read_model` and `inspect-work-thread` CLI view over the
same local loop refs so Chat handoff, Plans, Action Inbox, receipts, Evidence,
Memory Review, and Weekly Review are readable without runtime dispatch,
provider/model calls, connector read/write authority, browser/live web, memory
writes, context injection, public beta/release, or production authority.
The
sequence is tracked in
`docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md`.
The completed bounded Founder Loop V1 productization conveyor is tracked in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md` for `FCC-V1-000` through
`FCC-V1-007`: release surface manifest, API perimeter, Action Inbox backend
decisions, Today-to-Action vertical loop, Chat durable receipts and handoff,
Memory Review accept/correct/reject decisions, Evidence Timeline
productization, and proofed route-surface promotion.
FCC-LOOP-002 Founder Loop Ergonomics Pass is implemented as a UI/readability
layer over existing backend read models: Today opens with a daily-loop command
deck, Briefing joins the shared loop spine, and Action Inbox, Briefing, Memory,
and Evidence expose grouped operator summaries without new runtime authority.
FCC-MEM-001 Memory Workbench V1 is the current active memory hardening layer:
it adds the backend-owned memory workbench/search/manual-intake routes,
expanded lifecycle receipts, quality grouping, `/memory` workbench UI, and CLI
parity without memory truth authority, delete/export execution, semantic/vector
search, connector writes, context injection, public beta, or production
authority.
CRM + Communications Spine M0 is a contract-only product-line foundation in
`docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md` and
`src/ultimate_ai_agent/core/crm/contracts.py`. It defines safe-ref nouns and
fixture/proposal posture for future CRM and Communications work while adding
no /crm UI, no backend endpoints, no connector runtime, no connector writes,
no sends, no calendar writes, no silent merges, no silent contact creation, no
provider/model calls, no live web, no browser runtime, no public beta, and no
production authority.
CRM M1 Fixture-Only Vertical Shell is the historical deterministic
screen-ready fixture map
in `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`,
`src/ultimate_ai_agent/core/crm/fixtures.py`,
`scripts/verify_crm_m1_fixture_only_vertical_shell.py`, and
`tests/test_crm_m1_fixture_only_vertical_shell.py`, with a fixture-only `/crm`
Control Center shell route. It covers Real Estate/Realtor, Healthcare,
Finance/Insurance, Retail/E-commerce, and Professional Services as
fixture_only metadata only while adding no backend endpoints, no backend CRM
read model, no connector runtime, no connector writes, no external CRM writes,
no account sync, no sends, no calendar writes, no provider/model calls, no
live web, no browser runtime, no public beta, and no production authority.
CRM Local Command Center M2 is the current partial backend-owned CRM capability in
`docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md`,
`docs/control_center/UAA_CRM_LOCAL_COMMAND_CENTER_PLAN.md`,
`src/ultimate_ai_agent/core/crm/local_command_center.py`,
`scripts/dev/uaa_crm.py`, `scripts/verify_crm_local_command_center.py`,
`tests/test_crm_local_command_center.py`, and
`tests/test_crm_local_command_center_api_routes.py`. It adds local CRM read
routes, CLI inspection, local storage posture, redacted import/export preview,
deterministic proposal refs, and one exact local mutation receipt capability while
keeping connector runtime, connector writes, external CRM writes, account sync,
sends, calendar writes, provider/model calls, live web, browser runtime,
public beta, public release, production readiness, and production authority
blocked.

Connector draft-only proposals are backend-owned safe-ref review artifacts in
`docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md`,
`src/ultimate_ai_agent/core/connectors/connector_draft_proposals.py`,
`scripts/inspect_connector_draft_proposals.py`, and
`tests/test_connector_draft_proposals.py`. They make email-response and
calendar-hold draft refs visible in Source Readiness, Inbox, and Trust while
adding no connector runtime, sends, writes, account sync, source ingestion,
provider/model calls, memory writes, context injection, background work, public
beta, public release, or production authority.

Provider Catalog + Cost Literacy is a backend-owned read-only guide in
`docs/control_center/PROVIDER_CATALOG_COST_LITERACY.md`,
Provider Credential Readiness + Cost Governor Binding is documented in
`docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md`,
Provider And Settings Diagnostics is documented in
`docs/control_center/PROVIDER_SETTINGS_DIAGNOSTICS.md`, Model/Provider Control
Plane is documented in `docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md`,
with runtime capability foundation Phase 07 model/provider/research posture documented in
`docs/control_center/UAA_RUNTIME_MODEL_PROVIDER_RESEARCH.md`,
and the
Credential Vault Contract Shell is documented in
`docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md`, Credential Vault
Backend V1 is documented in
`docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`, and the
Tiny Exact-Approved Provider Invocation Lane is documented in
`docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md`;
the Exact-Approved Provider Fallback lane is documented in
`docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md`. The fallback lane is
limited to two proven single-provider adapter scopes and requires per-attempt
exact approval, CostGovernor posture, durable receipt refs, and complete
usage/cost receipts. Background and autonomous provider-call promotion
requirements are planning-only and documented in
`docs/control_center/BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md`;
background execution, scheduler runtime, autonomous model calls, provider
calls, runtime activation, billing authority, broad provider routing, and new
API runtime routes remain blocked. The contracts live in
`src/ultimate_ai_agent/core/providers/catalog.py`,
`src/ultimate_ai_agent/core/providers/readiness.py`,
`src/ultimate_ai_agent/core/providers/invocation.py`,
`src/ultimate_ai_agent/core/providers/live_invocation_adapter.py`,
`src/ultimate_ai_agent/core/providers/fallback.py`, and
`src/ultimate_ai_agent/core/providers/credential_validation.py`,
`src/ultimate_ai_agent/core/secrets/vault_contracts.py`, and
`src/ultimate_ai_agent/core/secrets/vault_backend.py`, exposed through
`GET /control-center/providers/setup-guide`,
`POST /control-center/providers/exact-approved-lanes/tiny`,
`POST /control-center/providers/credentials/validate`,
`scripts/inspect_provider_setup_guide.py`,
`scripts/inspect_provider_credential_readiness.py`, and
`scripts/inspect_credential_vault_contract.py`, and
`scripts/inspect_credential_vault_backend.py`, and
`scripts/inspect_tiny_provider_invocation_lane.py`, and
`scripts/inspect_provider_credential_validation_lane.py`, and
`scripts/inspect_exact_approved_provider_fallback.py`. Provider capability posture is
checked by `scripts/verify_provider_invocation_promotion_plan.py` and
`scripts/verify_tiny_provider_invocation_lane.py`, and
`scripts/verify_provider_credential_validation_lane.py`, with fallback sequencing
covered by `tests/test_exact_approved_provider_fallback.py`; background
promotion planning is checked by
`scripts/verify_background_autonomous_provider_plan.py` and
`tests/test_background_autonomous_provider_plan.py`; provider billing authority
requirements are planning-only and documented in
`docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`; provider billing
authority remains blocked until a later scoped promotion proves exact
per-request or per-session max USD approval, CostGovernor hard limits, actual
usage/cost receipts, incomplete-cost blocking, revocation, UI/CLI inspection,
audit/replay posture, safe-disable/rollback posture, and no broad spend toggle;
this boundary is checked by
`scripts/verify_provider_billing_authority_boundary.py` and
`tests/test_provider_billing_authority_boundary.py`; Phase 07 model/provider
research posture is checked by
`scripts/verify_uaa_runtime_model_provider_research.py` and
`tests/test_runtime_model_provider_research.py`; backend safe-ref
posture is checked by `scripts/verify_credential_vault_backend_v1.py`. They add no secret
resolution API, no raw secret display, no built-in live validation transport,
no provider SDK calls, no provider network call by default, no provider network
outside named exact-scoped tiny live adapters, no broad provider router, no
unbounded or router-dry-run fallback, no autonomous model calls, no background
execution, no automatic pricing fetch, no billing authority, no unknown
paid-cost bypass, no provider output authority, no vault runtime authority, and
no invocation authority from vault presence.
Credential validation is exact-approved, one-provider, redacted-receipt only
and does not grant provider/model runtime authority.

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
| CRM + Communications Spine M0 | `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`, `src/ultimate_ai_agent/core/crm/contracts.py`, `scripts/verify_crm_communications_spine_m0.py` |
| CRM M1 Fixture-Only Vertical Shell | `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`, `src/ultimate_ai_agent/core/crm/fixtures.py`, `scripts/verify_crm_m1_fixture_only_vertical_shell.py`, `tests/test_crm_m1_fixture_only_vertical_shell.py` |
| Provider Catalog + Cost Literacy | `docs/control_center/PROVIDER_CATALOG_COST_LITERACY.md`, `docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md`, `docs/control_center/PROVIDER_SETTINGS_DIAGNOSTICS.md`, `docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md`, `docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md`, `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`, `docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md`, `docs/control_center/PROVIDER_DRAFT_SUMMARIZE_MICRO_LANE.md`, `docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md`, `docs/control_center/BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md`, `docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`, `src/ultimate_ai_agent/core/providers/catalog.py`, `src/ultimate_ai_agent/core/providers/readiness.py`, `src/ultimate_ai_agent/core/providers/control_plane.py`, `src/ultimate_ai_agent/core/providers/invocation.py`, `src/ultimate_ai_agent/core/providers/live_invocation_adapter.py`, `src/ultimate_ai_agent/core/providers/draft_summarize.py`, `src/ultimate_ai_agent/core/providers/credential_validation.py`, `src/ultimate_ai_agent/core/secrets/vault_contracts.py`, `src/ultimate_ai_agent/core/secrets/vault_backend.py`, `scripts/inspect_provider_setup_guide.py`, `scripts/inspect_provider_credential_readiness.py`, `scripts/inspect_model_provider_control_plane.py`, `scripts/inspect_credential_vault_contract.py`, `scripts/inspect_credential_vault_backend.py`, `scripts/inspect_tiny_provider_invocation_lane.py`, `scripts/inspect_provider_draft_summarize_lane.py`, `scripts/inspect_provider_credential_validation_lane.py`, `scripts/inspect_exact_approved_provider_fallback.py`, `scripts/verify_provider_catalog_cost_literacy.py`, `scripts/verify_provider_credential_cost_binding.py`, `scripts/verify_model_provider_control_plane.py`, `scripts/verify_credential_vault_contract_shell.py`, `scripts/verify_credential_vault_backend_v1.py`, `scripts/verify_provider_invocation_promotion_plan.py`, `scripts/verify_tiny_provider_invocation_lane.py`, `scripts/verify_provider_credential_validation_lane.py`, `scripts/verify_background_autonomous_provider_plan.py`, `scripts/verify_provider_billing_authority_boundary.py` |
| Provider and Tool Runtime Safety Contracts | `docs/architecture/PROVIDER_TOOL_RUNTIME_SAFETY_CONTRACTS.md`, `src/ultimate_ai_agent/core/execution/provider_tool_runtime_safety.py`, `tests/test_provider_tool_runtime_safety_contracts.py` |
| Run-Attached Approval Queue | `docs/architecture/RUN_ATTACHED_APPROVAL_QUEUE.md`, `src/ultimate_ai_agent/core/execution/approval_queue.py`, `tests/test_run_attached_approval_queue.py` |
| Streaming and Progress Read Model | `docs/architecture/STREAMING_PROGRESS_READ_MODEL.md`, `src/ultimate_ai_agent/core/execution/read_models.py`, `tests/test_streaming_progress_read_model.py` |
| Background Coworker Worker Contract | `docs/architecture/BACKGROUND_COWORKER_WORKER_CONTRACT.md`, `src/ultimate_ai_agent/core/execution/background_coworker.py`, `tests/test_background_coworker_worker_contract.py` |
| Connector Delivery Semantics Contract | `docs/architecture/CONNECTOR_DELIVERY_SEMANTICS_CONTRACT.md`, `src/ultimate_ai_agent/core/execution/connector_delivery.py`, `tests/test_connector_delivery_semantics_contract.py` |
| MCP gateway foundation and capability promotion ladder | `docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md`, `docs/tooling/CAPABILITY_PROMOTION_LADDER.md`, `src/ultimate_ai_agent/core/capabilities/mcp_gateway.py`, `tests/test_mcp_gateway_foundation.py`, `scripts/verify_mcp_gateway_foundation.py` |
| A2A gateway foundation | `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`, `docs/tooling/CAPABILITY_PROMOTION_LADDER.md`, `docs/schemas/a2a_agent_card_v1.schema.json`, `src/ultimate_ai_agent/core/capabilities/a2a_gateway.py`, `tests/test_a2a_gateway_foundation.py`, `scripts/verify_a2a_gateway_foundation.py`, `scripts/verify_compatibility_schema_drift.py` |
| Browser Gateway Ladder | `docs/browser/UAA_BROWSER_GATEWAY_LADDER.md`, `docs/tooling/CAPABILITY_PROMOTION_LADDER.md`, `src/ultimate_ai_agent/core/web_access/browser_gateway_ladder.py`, `tests/test_browser_gateway_ladder.py`, `scripts/verify_browser_gateway_ladder.py` |
| Skill Workbench discovery and adoption charter | `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`, `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/network/WEB_ACCESS_GATEWAY.md` |
| Memory Workbench V1 and Ranked Retrieval / Recall Tuning | `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`, `docs/control_center/FCC_MEM_001_MEMORY_BASELINE_AUDIT.md`, `docs/control_center/FCC_MEM_022_RANKED_RETRIEVAL_RECALL_TUNING.md`, `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md` |
| Agent module maturity review | `docs/registry/agent_module_maturity_map.json`, `docs/registry/agent_module_maturity_review_v2.json`, `docs/registry/AGENT_MODULE_MATURITY_REVIEW_V2.md` |
| Top-level decision router contract | `docs/control_center/UAA_P1_089_TOP_LEVEL_DECISION_ROUTER_CONTRACT.md`, `src/ultimate_ai_agent/core/decision_router/contracts.py`, `scripts/verify_uaa_p1_089_top_level_decision_router_contract.py` |
| Task decomposition proposal engine | `docs/control_center/UAA_P1_090_TASK_DECOMPOSITION_PROPOSAL_ENGINE.md`, `src/ultimate_ai_agent/core/task_decomposition/proposals.py`, `scripts/verify_uaa_p1_090_task_decomposition_proposal_engine.py` |
| FCC fusion routing/delegation readability | `docs/control_center/FCC_FUSION_ROUTING_DELEGATION.md`, `src/ultimate_ai_agent/core/control_center/fusion_routing.py`, `scripts/verify_fcc_fusion_routing_delegation.py` |
| Operational maturity and authority ramp | `docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`, `docs/runtime/UAA_AUTHORITY_LEASE_BUDGET_LEDGER.md`, `docs/runtime/UAA_AUTHORITY_MISSION_WORKER_V1.md`, `docs/control_center/OPERATIONALIZATION_LADDER.md`, `docs/control_center/operational_maturity_manifest.json`, `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`, `docs/control_center/authority_candidate_scorecard.json` |
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
completed UAA-P1-088 Agent Module Maturity Review V2 as a
review/scoring/read-model lane only, completed UAA-P1-089 Top-Level Decision
Router Contract as a contract/read-model lane only, completed UAA-P1-090 Task
Decomposition Proposal Engine as a proposal/read-model lane only, and completed FCC-V1-000
Control Center Release Surface Manifest, FCC-V1-001
API Perimeter For Real Mutations, and FCC-V1-002 Action Inbox Backend State
Machine, completed FCC-V1-003 Founder Loop V1 Vertical Slice, completed
FCC-V1-004 Chat Durable Receipt And Handoff, completed FCC-V1-005 Memory
Review Decisions, completed FCC-V1-006 Evidence Timeline Productization, and
completed FCC-V1-007 Promotion And Proof Lane.
UAA-P1-091 v0.105.0 Governed Runtime Pilot is the active scoped internal
runtime-authority capability set. Phase 07 release truth keeps v0.104.0 as the active
product/package baseline while the governed runtime milestone is tag-eligible
only after green PR review and verification: configured loopback local-model
calls, one exact read-only status command, and exact Action Inbox approved
focused pytest, repo-verifier, frontend-check, and repo-doctor execution may produce
RuntimeGateway receipts only under active `workspace/execute` AuthorityLease
scope plus exact Action Inbox approval; browser
automation, connector writes, plugin import, remote execution, arbitrary
shell/subprocess work outside exact approved capabilities, public
beta, public release, production authority, and broad autonomy remain blocked.
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
| Agent runtime compatibility | `docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md`, `docs/codex/UAA_P2_AGENT_RUNTIME_COMPATIBILITY_PROMPTS.md` |
| Runtime parity baseline | `docs/runtime/UAA_RUNTIME_PARITY_SCORECARD.md`, `docs/runtime/UAA_GOATCITADEL_PARITY_MATRIX.md`, `docs/runtime/UAA_RUNTIME_ROUTE_DECISION_BINDING.md`, `docs/runtime/UAA_RUNTIME_TURN_RUN_APPROVAL_CHAIN.md`, `docs/runtime/UAA_RUNTIME_STAGED_ORCHESTRATION_ENGINE.md`, `docs/runtime/UAA_RUNTIME_PREPARED_TURN_LOOP.md`, `docs/runtime/UAA_RUNTIME_ROLE_PROVIDER_EVIDENCE.md`, `docs/runtime/UAA_RUNTIME_ACTION_SIGNED_EVIDENCE.md`, `docs/runtime/UAA_RUNTIME_PARITY_FINAL_HARDENING.md`, `docs/runtime/UAA_HERMES_RUNTIME_DELEGATION_ADAPTER.md`, `docs/runtime/UAA_HERMES_RUNTIME_CAPABILITY_DISCOVERY.md`, `docs/runtime/UAA_HERMES_RUNTIME_RUN_EVENTS.md`, `docs/runtime/UAA_HERMES_RUNTIME_APPROVAL_BRIDGE.md`, `docs/runtime/UAA_HERMES_RUNTIME_STREAMING_PROGRESS.md`, `docs/runtime/UAA_HERMES_RUNTIME_PROFILE_ISOLATION.md`, `docs/runtime/UAA_HERMES_RUNTIME_MODEL_PROVIDER_CATALOG.md`, `docs/runtime/UAA_HERMES_RUNTIME_MODEL_SLOT_POSTURE.md`, `docs/runtime/UAA_HERMES_INTERFACE_MODE.md`, `docs/prompts/uaa_runtime_parity/00_execute_runtime_parity_end_to_end.prompt.md`, `scripts/verify_uaa_runtime_parity_scorecard.py`, `scripts/verify_uaa_runtime_route_decision_binding.py`, `scripts/verify_uaa_runtime_turn_run_approval_chain.py`, `scripts/verify_uaa_runtime_staged_orchestration.py`, `scripts/verify_uaa_runtime_prepared_turn.py`, `scripts/verify_uaa_runtime_role_provider_evidence.py`, `scripts/verify_uaa_runtime_action_signed_evidence.py`, `scripts/verify_uaa_runtime_parity_final.py`, `scripts/verify_hermes_runtime_adoption_phase_01.py`, `scripts/verify_hermes_runtime_adoption_phase_02.py`, `scripts/verify_hermes_runtime_adoption_phase_03.py`, `scripts/verify_hermes_runtime_adoption_phase_04.py`, `scripts/verify_hermes_runtime_adoption_phase_05.py`, `scripts/verify_hermes_runtime_adoption_phase_06.py`, `scripts/verify_hermes_runtime_adoption_phase_07.py`, `scripts/verify_hermes_runtime_adoption_phase_08.py`, `scripts/verify_hermes_interface_mode.py` |
| Durable run lifecycle inspection | `docs/architecture/DURABLE_RUN_LIFECYCLE_EVENT_LOG.md`, `docs/execution/DURABLE_RUN_SPINE.md`, `docs/execution/APPEND_FIRST_RUN_STORAGE.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| Product truth packet | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md` |
| Governed runtime pilot | `VERSION.md`, `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, `docs/control_center/GOVERNED_PRODUCT_PILOT_AUTHORITY_PROFILE.md`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md`, `scripts/dev/uaa_runtime.py`, `scripts/verify_governed_product_pilot_authority_profile.py`, `tests/test_governed_runtime_contracts.py`, `tests/test_governed_runtime_api_routes.py`, `tests/test_governed_product_pilot_authority_profile.py` |
| Control Center readiness | `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/control_center/ROUTE_STATUS_MANIFEST.md`, `docs/control_center/route_status_manifest.json`, `docs/control_center/release_surface_manifest.json`, `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`, `docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md`, `docs/control_center/UAA_RUNTIME_CAPABILITY_FINAL_SCORECARD.md`, `docs/control_center/UAA_RUNTIME_AGENT_LOOP_SPINE.md`, `docs/control_center/UAA_RUNTIME_DURABLE_ORCHESTRATION.md`, `docs/control_center/UAA_RUNTIME_ACTION_TOOL_CODE_LANES.md`, `docs/control_center/UAA_RUNTIME_MEMORY_LEARNING.md`, `docs/control_center/UAA_RUNTIME_COCKPIT_CLI_API.md`, `docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md`, `docs/control_center/FCC_THREAD_001_UNIFIED_WORK_THREAD.md`, `docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`, `docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`, `docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md`, `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`, `docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`, `docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md`, `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`, `docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md`, `docs/macos/private_operator_14_day_dogfood_harness_v1.json`, `docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_AUTHORITY_CAPABILITY.md`, `docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md`, `docs/control_center/visual_regression_manifest.json`, `docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md`, `docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md`, `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`, `docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`, `docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`, `docs/control_center/FCC_LOOP_002_FOUNDER_LOOP_ERGONOMICS_PASS.md`, `docs/control_center/FCC_FUSION_ROUTING_DELEGATION.md`, `docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md`, `docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md`, `docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md`, `docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md`, `docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md`, `docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md`, `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md`, `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`, `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`, `docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md`, `docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md`, `docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md`, `docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md` |
| Local model production-readiness lane | `docs/production/M166_PRODUCTION_AUTHORITY_GATE.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Local model operations | `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md`, `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`, `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md` |
| Release verification and evidence | `docs/production/RELEASE_VERIFICATION_LANES.md`, `docs/production/RELEASE_EVIDENCE_PACKET.md`, `docs/production/BACKUP_RESTORE_VERIFICATION.md`, `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`, `docs/production/LOCAL_RUNTIME_PACKAGING.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Verification maintainability | `docs/verification/milestone_status_manifest.json`, `docs/verification/verification_maintainability_policy.json` |
| Computer Use / CUA contract lane | `docs/cua/COMPUTER_USE_CUA_CONTRACT.md`, `docs/cua/cua_release_surface_manifest.json` |
| Performance and API cache | `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `docs/api/SAFE_STATIC_MANIFEST_CACHING.md` |
| Redacted observability | `docs/observability/SESSION_LOGGING_M167.md` |
| Plugin/skill ecosystem boundary | `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`, `docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md`, `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`, `docs/schemas/plugin_skill_trust_manifest.schema.json`, `docs/schemas/inspectable_extension_catalog.schema.json`, `docs/schemas/extension_ecosystem_read_model.schema.json`, `docs/schemas/extension_activation_grant.schema.json` |

The Founder Command Center docs are planning and execution artifacts for the
next product loop. They do not grant production authority, public distribution,
broad autonomy, runtime connector writes, unrestricted shell/browser/network
authority, plugin runtime import, provider/model authority, mobile runtime, or
new backend/Control Center behavior by themselves.

## Verification Commands

Use these before release-facing claims or milestone status changes:

```bash
make verify
make verify-fast
make verify-dev-fast
make test-sharded
make test-sharded-profile
make verify-dev-sharded
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_verifier_maintainability.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

`make verify` is the release-grade local gate. It runs the complete pytest
inventory across timing-balanced, process-isolated shards, followed by the
static verifier, gate architecture, and a serialized report-only Foundation
Gate. `make test-serial` remains available for order-sensitive diagnostics.
`make verify-fast` uses the same complete pytest inventory without updating the
latest Foundation Gate report. `make verify-dev-fast` runs the four pre-gate
phases concurrently and then serializes Foundation Gate with
`report-only --no-write-latest`. `VERIFY_DEV_FAST_JOBS` bounds top-level phase
fanout, while `PYTEST_SHARD_WORKERS` separately bounds pytest subprocesses.
Hosted CI proves the same complete inventory through eight isolated shards and
one aggregate `pytest` check. These local lanes do not populate release evidence
packets or independently grant release readiness.

`make test` and `make test-sharded` use the canonical sharded pytest lane. The
shard runner discovers `tests/**/test_*.py`, stores logs and
isolated pytest temp dirs under ignored `/tmp` paths by default, and writes
file-level timing data only during explicit `make test-sharded-profile` runs.
The tracked repo-relative advisory seed is overlaid by a newer local profile;
missing files receive a conservative p90 estimate. Timing data schedules files
only and never caches a pass or authority result. No pytest-xdist dependency is
added. Hosted CI promotes the same default-safe partitioning as required pytest
evidence only when every one of its eight isolated shards passes.

`make verify-dev-sharded` uses `scripts/verification/run_dev_fast_gate.py` to
keep local output readable: phase output is captured to ignored `/tmp` logs,
successful phases print concise timing summaries, and failed phases print log
tails plus log paths for full diagnostics. The runner still includes static
verification, documentation integrity, product truth, OpenAPI, redaction,
authority-boundary, route-classification, gate-architecture, and Foundation
Gate report-only coverage through the same underlying commands.

The sharded lane does not broaden test authority. Shard subprocesses strip
known live/model-heavy opt-in environment variables for GGUF search,
acquisition, local model roots, llama.cpp gateways, OpenWebUI test gateways,
Web Hybrid transports and Firecrawl credential references,
and provider live-network smoke tests. Existing optional/live tests remain
env-gated and skipped by default.

No local unchanged-file cache shortcut is currently enabled. Cache shortcuts are
planned-only until deterministic invalidation can be reviewed.

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
