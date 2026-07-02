# Documentation Index

Current active baseline: **v0.104.0**

This index is the active entrypoint for documentation navigation. Historical release documents remain in the repository for audit history, but active truth starts with the current baseline files listed here.

For the front-door product narrative, read UAA as the Founder Command Center:
a local-first professional AI command center built around Morning Briefing,
Today Plan, Action Inbox, Evidence, Memory Review, and Weekly CEO Review. Use
the product truth packet beside that narrative to keep implemented, partial,
blocked, planned, and future-scoped states distinct.

## Curated Current Entry Points

| Area | Canonical entry |
|---|---|
| GitHub landing page | `README.md` |
| Portfolio demo path | `README.md`, `docs/portfolio/CURRENT_STATUS.md`, `docs/portfolio/PRODUCT_NORTH_STAR.md`, `docs/portfolio/SCREENSHOTS.md`, `docs/portfolio/GOLDEN_PATH_DEMO.md`, `docs/portfolio/CASE_STUDY.md` |
| Portfolio review | `docs/portfolio/CURRENT_STATUS.md`, `docs/portfolio/PRODUCT_NORTH_STAR.md`, `docs/portfolio/CASE_STUDY.md` |
| Version and baseline | `VERSION.md`, `docs/release_notes/v0_104_0.md`, `docs/release_notes/checkpoint_m169.md` |
| Tag history and release convention | `docs/releases/TAG_CATALOG.md`, `docs/maintenance/RELEASE_PROCESS.md`, `docs/maintenance/SEMVER_POLICY.md` |
| Product truth | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md` |
| Governed cognitive memory spine | FCC-MEM-001 Memory Workbench V1 and FCC-MEM-022 Ranked Retrieval / Recall Tuning: `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md`, `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`, `docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md`, `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`, `docs/control_center/FCC_MEM_001_MEMORY_BASELINE_AUDIT.md`, `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`, `docs/control_center/FCC_MEM_022_RANKED_RETRIEVAL_RECALL_TUNING.md` |
| Agent module maturity review | `docs/registry/agent_module_maturity_map.json`, `docs/registry/agent_module_maturity_review_v2.json`, `docs/registry/AGENT_MODULE_MATURITY_REVIEW_V2.md` |
| Top-level decision router contract | `docs/control_center/UAA_P1_089_TOP_LEVEL_DECISION_ROUTER_CONTRACT.md`, `src/ultimate_ai_agent/core/decision_router/contracts.py`, `scripts/verify_uaa_p1_089_top_level_decision_router_contract.py` |
| Task decomposition proposal engine | `docs/control_center/UAA_P1_090_TASK_DECOMPOSITION_PROPOSAL_ENGINE.md`, `src/ultimate_ai_agent/core/task_decomposition/proposals.py`, `scripts/verify_uaa_p1_090_task_decomposition_proposal_engine.py` |
| Durable run lifecycle inspection | `docs/architecture/DURABLE_RUN_LIFECYCLE_EVENT_LOG.md`, `docs/execution/DURABLE_RUN_SPINE.md`, `src/ultimate_ai_agent/core/execution/read_models.py`, `src/ultimate_ai_agent/core/execution/run_storage.py`, `tests/test_durable_run_lifecycle_read_model.py` |
| Provider and Tool Runtime Safety Contracts | `docs/architecture/PROVIDER_TOOL_RUNTIME_SAFETY_CONTRACTS.md`, `src/ultimate_ai_agent/core/execution/provider_tool_runtime_safety.py`, `tests/test_provider_tool_runtime_safety_contracts.py` |
| Agent runtime compatibility | `docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md`, `docs/codex/UAA_P2_AGENT_RUNTIME_COMPATIBILITY_PROMPTS.md`, `scripts/verify_agent_runtime_compatibility.py`, `scripts/verify_compatibility_schema_drift.py` |
| Product Loop 006 Plans to Actions bridge | `docs/control_center/PRODUCT_LOOP_006_PLANS_TO_ACTIONS.md`, `src/ultimate_ai_agent/core/control_center/plans_to_actions.py`, `scripts/inspect_plans_to_actions_bridge.py`, `scripts/verify_product_loop_006_plans_to_actions.py` |
| Product Loop 007 Morning Briefing V1 | `docs/control_center/PRODUCT_LOOP_007_MORNING_BRIEFING_V1.md`, `src/ultimate_ai_agent/core/control_center/morning_briefing.py`, `scripts/inspect_morning_briefing_v1.py`, `scripts/verify_product_loop_007_morning_briefing_v1.py` |
| Product Loop 008 Weekly CEO Review | `docs/control_center/PRODUCT_LOOP_008_WEEKLY_CEO_REVIEW.md`, `src/ultimate_ai_agent/core/control_center/weekly_ceo_review.py`, `scripts/inspect_weekly_ceo_review.py`, `scripts/verify_product_loop_008_weekly_ceo_review.py` |
| Product Loop 009 Chat to loop handoff | `docs/control_center/PRODUCT_LOOP_009_CHAT_TO_LOOP_HANDOFF.md`, `src/ultimate_ai_agent/core/control_center/chat_to_loop_handoff.py`, `scripts/inspect_chat_to_loop_handoff.py`, `scripts/verify_product_loop_009_chat_to_loop_handoff.py` |
| Product Loop 010 Evidence Timeline narrative | `docs/control_center/PRODUCT_LOOP_010_EVIDENCE_TIMELINE_NARRATIVE.md`, `src/ultimate_ai_agent/core/storage/founder_loop.py`, `scripts/inspect_evidence_timeline_narrative.py`, `scripts/verify_product_loop_010_evidence_timeline_narrative.py` |
| Product Loop 011 Settings and kill-switch clarity | `docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md`, `src/ultimate_ai_agent/core/control_center/operational_status.py`, `scripts/inspect_settings_authority_posture.py`, `scripts/verify_product_loop_011_settings_kill_switch_clarity.py` |
| Product Loop 012 Private product loop trial script | `docs/control_center/PRODUCT_LOOP_012_PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT.md`, `src/ultimate_ai_agent/core/readiness/private_operator_trial.py`, `docs/control_center/private_product_loop_trial_script_v1.json`, `scripts/inspect_product_loop_trial_script.py`, `scripts/verify_product_loop_012_private_trial_script.py` |
| Founder Loop V1 product proof pass | `docs/control_center/FOUNDER_LOOP_V1_PRODUCT_PROOF_PASS.md`, `src/ultimate_ai_agent/core/control_center/founder_loop_product_proof.py`, `scripts/inspect_founder_loop_v1_product_proof.py`, `scripts/verify_founder_loop_v1_product_proof.py`, `tests/test_founder_loop_v1_product_proof.py` |
| FCC fusion routing/delegation readability | `docs/control_center/FCC_FUSION_ROUTING_DELEGATION.md`, `src/ultimate_ai_agent/core/control_center/fusion_routing.py`, `scripts/verify_fcc_fusion_routing_delegation.py`, `tests/test_fcc_fusion_routing_delegation.py` |
| Provider Catalog + Cost Literacy | `docs/control_center/PROVIDER_CATALOG_COST_LITERACY.md`, `docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md`, `docs/control_center/PROVIDER_SETTINGS_DIAGNOSTICS.md`, `docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md`, `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`, `docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md`, `docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md`, `docs/control_center/BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md`, `docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`, `docs/control_center/PROVIDER_CREDENTIAL_VALIDATION_LANE.md`, `docs/control_center/PROVIDER_ROUTER_DRY_RUN.md`, `src/ultimate_ai_agent/core/providers/catalog.py`, `src/ultimate_ai_agent/core/providers/readiness.py`, `src/ultimate_ai_agent/core/providers/invocation.py`, `src/ultimate_ai_agent/core/providers/live_invocation_adapter.py`, `src/ultimate_ai_agent/core/providers/fallback.py`, `src/ultimate_ai_agent/core/providers/credential_validation.py`, `src/ultimate_ai_agent/core/providers/router_dry_run.py`, `src/ultimate_ai_agent/core/secrets/vault_contracts.py`, `src/ultimate_ai_agent/core/secrets/vault_backend.py`, `scripts/inspect_provider_setup_guide.py`, `scripts/inspect_provider_credential_readiness.py`, `scripts/inspect_credential_vault_contract.py`, `scripts/inspect_credential_vault_backend.py`, `scripts/inspect_tiny_provider_invocation_lane.py`, `scripts/inspect_provider_credential_validation_lane.py`, `scripts/inspect_provider_router_dry_run.py`, `scripts/inspect_exact_approved_provider_fallback.py`, `scripts/verify_provider_catalog_cost_literacy.py`, `scripts/verify_provider_credential_cost_binding.py`, `scripts/verify_credential_vault_contract_shell.py`, `scripts/verify_credential_vault_backend_v1.py`, `scripts/verify_provider_invocation_promotion_plan.py`, `scripts/verify_tiny_provider_invocation_lane.py`, `scripts/verify_provider_credential_validation_lane.py`, `scripts/verify_provider_router_dry_run.py`, `scripts/verify_background_autonomous_provider_plan.py`, `scripts/verify_provider_billing_authority_boundary.py`, `tests/test_provider_catalog_cost_literacy.py`, `tests/test_provider_credential_readiness_contracts.py`, `tests/test_credential_vault_contract_shell.py`, `tests/test_credential_vault_backend_v1.py`, `tests/test_provider_invocation_promotion_plan.py`, `tests/test_tiny_provider_invocation_lane.py`, `tests/test_provider_credential_validation_lane.py`, `tests/test_provider_router_dry_run.py`, `tests/test_exact_approved_provider_fallback.py`, `tests/test_background_autonomous_provider_plan.py`, `tests/test_provider_billing_authority_boundary.py` |
| A2A gateway foundation | `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`, `docs/schemas/a2a_agent_card_v1.schema.json`, `src/ultimate_ai_agent/core/capabilities/a2a_gateway.py`, `scripts/verify_a2a_gateway_foundation.py`, `scripts/verify_compatibility_schema_drift.py`, `tests/test_a2a_gateway_foundation.py` |
| Browser Gateway Ladder | `docs/browser/UAA_BROWSER_GATEWAY_LADDER.md`, `src/ultimate_ai_agent/core/web_access/browser_gateway_ladder.py`, `scripts/verify_browser_gateway_ladder.py`, `tests/test_browser_gateway_ladder.py` |
| Active roadmap | `docs/canonical/09_roadmap.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`, `docs/kanban/current_board.md` |
| Control Center UI wiring report | `docs/control_center/UI_WIRING_REPORT.md`, `apps/control-center/src/routes.tsx`, `apps/control-center/src/api/client.ts`, `docs/control_center/release_surface_manifest.json` |
| Founder Command Center product narrative and strategy | `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, `docs/kanban/founder_command_center_board.md`, `docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`, `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`, `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`, `docs/control_center/release_surface_manifest.json`, `docs/control_center/founder_loop_api_perimeter_manifest.json`, `docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`, `docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`, `docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md`, `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`, `docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`, `docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md`, `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`, `docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md`, `docs/macos/private_operator_14_day_dogfood_harness_v1.json`, `docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md`, `docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md`, `docs/control_center/visual_regression_manifest.json`, `docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md`, `docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md`, `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`, `docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`, `docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`, `docs/control_center/FOUNDER_LOOP_V1_PRODUCT_PROOF_PASS.md`, `docs/control_center/FCC_LOOP_002_FOUNDER_LOOP_ERGONOMICS_PASS.md`, `docs/control_center/PRODUCT_LOOP_004_FOLLOW_UP_TRACKER.md`, `docs/control_center/PRODUCT_LOOP_005_ACTION_INBOX_DECISION_LANES.md`, `docs/control_center/PRODUCT_LOOP_009_CHAT_TO_LOOP_HANDOFF.md`, `docs/control_center/PRODUCT_LOOP_010_EVIDENCE_TIMELINE_NARRATIVE.md`, `docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md`, `docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md`, `docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md`, `docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md`, `docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md`, `docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md`, `docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md`, `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md`, `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`, `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`, `docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md`, `docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md`, `docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md`, `docs/macos/UAA_P1_087_2A_PRIVATE_TRIAL_PACKET_AND_UI_TUNING_SURFACE.md`, `docs/macos/UAA_P1_087_2B_PRIVATE_TRIAL_ACCEPTANCE_LEDGER.md`, `docs/macos/UAA_P1_087_2C_PRIVATE_TRIAL_MANUAL_REVIEW_SCAFFOLD.md` |
| Next capability and product prompt pack | `docs/prompts/uaa_next_capability_product_prompts.md` |
| Public-facing portfolio/developer-preview readiness prompt | `docs/prompts/uaa_public_preview_perfection_pass.prompt.md` |
| CRM + Communications Spine M0 | `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`, `src/ultimate_ai_agent/core/crm/contracts.py`, `scripts/verify_crm_communications_spine_m0.py`, `tests/test_crm_communications_spine_contracts.py` |
| CRM M1 Fixture-Only Vertical Shell | `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`, `src/ultimate_ai_agent/core/crm/fixtures.py`, `scripts/verify_crm_m1_fixture_only_vertical_shell.py`, `tests/test_crm_m1_fixture_only_vertical_shell.py` |
| Operational maturity and authority ramp | `docs/control_center/OPERATIONALIZATION_LADDER.md`, `docs/control_center/operational_maturity_manifest.json`, `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`, `docs/control_center/authority_candidate_scorecard.json` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| API boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md`, `docs/api/FCC_V1_001_API_PERIMETER_FOR_REAL_MUTATIONS.md` |
| Verification maintainability | `docs/verification/milestone_status_manifest.json`, `docs/verification/verification_maintainability_policy.json` |
| Computer Use / CUA contract lane | `docs/cua/COMPUTER_USE_CUA_CONTRACT.md`, `docs/cua/cua_release_surface_manifest.json` |
| Security posture | `SECURITY.md`, `docs/security/SECURITY_TRIAGE_RUNBOOK.md` |
| Release evidence | `docs/production/RELEASE_VERIFICATION_LANES.md`, `docs/production/RELEASE_EVIDENCE_PACKET.md` |
| Governed web evidence and WebAccess runtime authority | `docs/truth/GOVERNED_WEB_EVIDENCE.md`, `docs/network/WEB_ACCESS_GATEWAY.md`, `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`, `docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md` |
| Local model lane | `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md`, `docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md`, `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`, `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md` |
| Redacted observability | `docs/observability/SESSION_LOGGING_M167.md` |
| Plugin/skill ecosystem | `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md` |
| Documentation policy | `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`, `docs/archive/README.md` |

Use the curated table first. The long list below is intentionally retained as
the repo-owned audit catalog for active and historical documentation refs.

Product Loop 010 Evidence Timeline narrative is safe-ref-only local history:
no live web, no public beta, and no production authority are granted by its
visibility in this index.

Product Loop 011 Settings and kill-switch clarity is backend-owned read-only posture with blocked/degraded/partial labels only: no toggles that grant authority, no provider configuration, no installer behavior, no runtime activation, no feature-flag writes, no kill-switch execution, no revocation execution, no connector runtime, no connector writes, no model calls, no provider SDK calls, no live web, no shell/browser execution, no public beta, no production readiness claims, and no production authority.

Product Loop 012 Private product loop trial script is a local/private, safe-ref-only manual operator review artifact for Boot, Today, Morning Briefing, Follow-Ups, Memory, Actions, Plans, Chat Handoff, Evidence, Weekly Review, and Settings. `scripts/inspect_product_loop_trial_script.py` provides CLI parity for the same checklist and acceptance ledger posture. It adds no public beta, no public distribution, no telemetry export, no connector runtime, no connector reads/writes, no provider/model calls, no live web, no shell/browser execution, no production readiness claims, and no production authority.

FCC fusion routing/delegation readability is backend-owned review metadata in
`docs/control_center/FCC_FUSION_ROUTING_DELEGATION.md`, backed by
`src/ultimate_ai_agent/core/control_center/fusion_routing.py`,
`scripts/verify_fcc_fusion_routing_delegation.py`, and
`tests/test_fcc_fusion_routing_delegation.py`. It adds work classification,
route visibility, future-only delegation proposals, cache/context posture, and
private dogfood safe refs without adding worker runtime, action execution,
model/provider invocation, shell/browser execution, connector writes, memory
writes, context injection, public distribution, or production authority.

CRM + Communications Spine M0 is contract-only product-line truth in
`docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`, backed by
`src/ultimate_ai_agent/core/crm/contracts.py`,
`scripts/verify_crm_communications_spine_m0.py`, and
`tests/test_crm_communications_spine_contracts.py`. It defines safe-ref
contract nouns and fixture/proposal posture for future CRM and Communications
work while adding no /crm UI, no backend endpoints, no connector runtime, no
connector writes, no sends, no calendar writes, no silent merges, no silent
contact creation, no provider/model calls, no live web, no browser runtime, no
public beta, and no production authority.

CRM M1 Fixture-Only Vertical Shell is a deterministic screen-ready fixture map
in `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`, backed by
`src/ultimate_ai_agent/core/crm/fixtures.py`,
`scripts/verify_crm_m1_fixture_only_vertical_shell.py`, and
`tests/test_crm_m1_fixture_only_vertical_shell.py`. It adds fixture_only
vertical metadata for Real Estate/Realtor, Healthcare, Finance/Insurance,
Retail/E-commerce, and Professional Services plus a fixture-only `/crm`
Control Center shell route while adding no backend endpoints, no backend CRM
read model, no connector runtime, no connector writes, no external CRM writes,
no account sync, no sends, no calendar writes, no provider/model calls, no
live web, no browser runtime, no public beta, and no production authority.

Provider Catalog + Cost Literacy is backend-owned read-only metadata in
`docs/control_center/PROVIDER_CATALOG_COST_LITERACY.md`, with Provider
Credential Readiness + Cost Governor Binding in
`docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md`,
Provider And Settings Diagnostics in
`docs/control_center/PROVIDER_SETTINGS_DIAGNOSTICS.md`, and the
Credential Vault Contract Shell in
`docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md`, Credential Vault
Backend V1 in `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`, with the
Exact-Approved Provider Invocation Promotion Plan in
`docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md` and
Exact-Approved Provider Credential Validation Lane in
`docs/control_center/PROVIDER_CREDENTIAL_VALIDATION_LANE.md`, Exact-Approved
Provider Fallback in `docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md`,
Background and Autonomous Provider Calls Promotion Plan in
`docs/control_center/BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md`,
Provider Billing Authority Boundary in
`docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`,
and Provider Router Dry-Run in `docs/control_center/PROVIDER_ROUTER_DRY_RUN.md`.
The fallback lane is limited to two named single-provider adapter scopes and
requires per-attempt exact approval, CostGovernor posture, durable receipt refs,
and complete usage/cost receipts. Background/autonomous provider calls remain
blocked until a later scoped promotion proves a scoped autonomy window, exact
provider/model refs, exact credential refs, queue inspection, kill switch,
revocation, replay/audit, red-team checks, UI/CLI parity, CostGovernor hard
blocks, incomplete-cost receipt blocking, explicit human approval boundaries,
and safe-disable/rollback posture. Provider billing authority remains blocked
until a later scoped promotion proves exact per-request or per-session max USD
approval, CostGovernor hard limits, actual usage/cost receipts,
incomplete-cost blocking, revocation, UI/CLI inspection, audit/replay posture,
safe-disable/rollback posture, and no broad spend toggle. The contracts are
backed by
`src/ultimate_ai_agent/core/providers/catalog.py`,
`src/ultimate_ai_agent/core/providers/readiness.py`,
`src/ultimate_ai_agent/core/providers/invocation.py`,
`src/ultimate_ai_agent/core/providers/fallback.py`,
`src/ultimate_ai_agent/core/providers/credential_validation.py`,
`src/ultimate_ai_agent/core/providers/router_dry_run.py`,
`src/ultimate_ai_agent/core/secrets/vault_contracts.py`,
`src/ultimate_ai_agent/core/secrets/vault_backend.py`,
`GET /control-center/providers/setup-guide`,
`POST /control-center/providers/exact-approved-lanes/tiny`,
`POST /control-center/providers/credentials/validate`,
`POST /control-center/providers/router/dry-run`,
`scripts/inspect_provider_setup_guide.py`,
`scripts/inspect_provider_credential_readiness.py`,
`scripts/inspect_credential_vault_contract.py`, and
`scripts/inspect_credential_vault_backend.py`, and
`scripts/inspect_tiny_provider_invocation_lane.py`, and
`scripts/inspect_provider_credential_validation_lane.py`, and
`scripts/inspect_provider_router_dry_run.py`, and
`scripts/inspect_exact_approved_provider_fallback.py`, with provider posture
checked by `scripts/verify_provider_invocation_promotion_plan.py` and
`scripts/verify_tiny_provider_invocation_lane.py`,
`scripts/verify_provider_credential_validation_lane.py`,
`scripts/verify_provider_router_dry_run.py`,
`scripts/verify_background_autonomous_provider_plan.py`,
`scripts/verify_provider_billing_authority_boundary.py`, plus
`scripts/verify_credential_vault_backend_v1.py`, with fallback sequencing covered
by `tests/test_exact_approved_provider_fallback.py` and planning coverage by
`tests/test_background_autonomous_provider_plan.py` and
`tests/test_provider_billing_authority_boundary.py`. It adds no secret resolution
API, no raw secret display, no provider SDK calls, no provider network call by
default, no provider network outside named exact-scoped tiny live adapters, no broad
provider router authority, no unbounded or router-dry-run fallback execution, no
autonomous model calls, no background execution, no scheduler, no runtime
activation, no automatic pricing fetch, no billing authority, no provider output
authority, no unknown paid-cost bypass, no incomplete-cost bypass, no vault
runtime authority, no invocation authority from vault presence, no new API
runtime route, and no broad callable runtime authority.
Credential validation is exact-approved, one-provider, redacted-receipt only and
does not grant provider/model runtime authority.

## Founder Command Center / Product Strategy

These docs translate the current repo state, Operator Runtime Excellence plan,
Control Center gap map, product language rules, and product truth packet into a
practical first product-loop roadmap. The front-door product narrative should
lead with Founder Command Center while the evidence language below preserves
the exact current implementation state. UAA-P1-067 completes the Today-spine,
memory-first Founder Command Center beta-readiness planning/currentness pass;
UAA-P1-068 completes the Today Product Spine Contract; UAA-P1-069 completes the
Evidence History Grammar; UAA-P1-070 completes the Memory Source And
Provenance Model; UAA-P1-071 completes Memory Review Decision Capture;
UAA-P1-072 Business Memory And Memory Quality Controls completes CRM-lite
candidate kinds and quality posture; UAA-P1-073 Plans To Reviewable Action
Envelopes completes reviewable Action envelope posture; UAA-P1-074 Chat Local
Operator Surface completes first-party local Chat operator truth; UAA-P1-075
Governed Code Workbench V1 completes repo-local governed Code proposal refs;
UAA-P1-076 Cross-Surface Memory Intake completes review-only intake proposal
refs from Today, Chat, Plans, Actions, Evidence, local coding, and manual
external-assistant review imports; UAA-P1-077 Memory-To-Loop Binding completes
read-only loop refs, memory-derived Action proposals, Evidence Timeline
history, Memory Review visibility, and Weekly CEO Review rollup metadata;
UAA-P1-078 Private Beta-Readiness Gate completes local/private beta-test
acceptance evidence states, Today/Actions/Evidence visibility, a schema,
verifier, and focused tests. UAA-P1-079 User Intent Understanding V1 completes
reviewable intent proposals with confidence, source refs, evidence refs,
ambiguity posture, and ask/act/defer routing. UAA-P1-080 API Route
Classification And Public/Protected Inventory completes typed route
classification in `/api/manifest`, the current 147-route inventory fixture,
route-status manifest alignment, and Control Center API Routes visibility.
UAA-P1-081 Centralized FastAPI Security Headers completes centralized response
headers, HTTPS-only HSTS, manifest capability posture, and focused verifier
coverage without adding CORS/auth/rate-limit authority. UAA-P1-082 Explicit
Loopback CORS Allowlist completes exact local Control Center dev/preview origin
allowlisting without wildcard CORS, CORS credentials, or auth claims.
UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes completes a
configured local bearer gate for non-public route classifications without
enterprise auth, OAuth, password flow, idempotency, rate-limit, or production
authority claims. UAA-P1-084 Mutating Route Idempotency Enforcement Audit
completes a runtime idempotency header gate for mutating route classifications
without durable dedupe, exactly-once execution, rate-limit, mutation authority,
or production authority claims. UAA-P1-085 Targeted Rate Limits For Expensive
And Sensitive Routes completes targeted local fixed-window rate limits for
model/chat, task-decomposition, action preview/proposal, and expensive
validation/local-model paths without auth, distributed quota, dependency, or
production authority claims. UAA-P1-086 API Boundary Enforcement Tests
completes OpenAPI, API manifest, route inventory fixture, route-status
manifest, protected-route, idempotency, header, CORS, and rate-limit
enforcement checks without new runtime authority. FCC-V1-001 API Perimeter For
Real Mutations completes manifest-visible auth and approval posture,
Founder Loop mutation perimeter manifest coverage, a verifier, and focused
tests while keeping duplicate replay runtime blocked until route-owner receipt
storage exists. UAA-P1-087.1 Local Launcher
Dual-Surface Boot Readiness completes the `trial-boot` launcher contract,
Control Center-first boot, secondary OpenWebUI blocked states, status/stop
coverage, and safe launcher log refs without new runtime authority. It is
followed by completed UAA-P1-087.2a Private Trial Packet And UI Tuning Surface
with a safe-ref-only packet, read-only `/private-trial` surface, manual smoke
checklist refs, friction refs, UI/copy task refs, and blocked authority refs.
UAA-P1-087.2b Private Trial Findings Capture And Acceptance Ledger completes a
safe-ref-only acceptance ledger, pending surface review refs, manual smoke step
refs, acceptance question refs, tuning decision refs, and read-only
`/private-trial` visibility. UAA-P1-087.2c Private Trial Manual Review Scaffold
completes unanswered pending answer refs, missing implementation refs, deferred
decision refs, and read-only `/private-trial` visibility without accepted or
revised manual-review answers. Full UAA-P1-087.2 remains planned and deferred
until more Founder Loop implementation exists and accepted or revised
local/private findings are recorded later, followed by UAA-P1-087.3 native
SwiftUI boot cockpit planning/source-only scaffold.
UAA-P1-088 Agent Module Maturity Review V2 completes a review/scoring/read-model
lane for the existing core agent modules, ranked improvement queue, verifier,
tests, and benchmark evidence integration without runtime model calls,
provider calls, shell/subprocess execution, network/browser authority,
connector writes, memory writes, context injection, action execution, workflow
execution, autonomous routing authority, public beta, or production authority.
UAA-P1-089 Top-Level Decision Router Contract completes a core
contract/read-model package for answer-direct, reviewed-memory, Action Inbox
proposal, ask-human, escalate, defer, blocked-unsafe, and
insufficient-evidence route outcome proposals without model/provider calls,
tool execution, action execution, workflow execution, memory writes, context
injection, shell/subprocess execution, browser/network access, connector
writes, autonomous routing authority, backend routes, public beta, or
production authority.
UAA-P1-090 Task Decomposition Proposal Engine completes a deterministic
proposal/read-model lane that turns bounded safe request refs into
review-only decomposition proposals for Plans and Action Inbox visibility,
with CLI inspection parity, no backend route, no model/provider calls, no
tool/action/workflow execution, no memory writes, no context injection, no
shell/subprocess execution, no browser/network access, no connector writes, no
autonomous planning authority, and no production authority.
FCC-V1-000 Control Center Release Surface Manifest completes release-status
truth for every visible Control Center route with
`docs/control_center/release_surface_manifest.json`,
`docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`, a schema, verifier,
and focused tests. It adds no backend route or runtime authority, and no route
is promoted beyond the manifest's conservative `partial`, `blocked`, or
`experimental` truth.
The completed `FCC-V1-000` through `FCC-V1-007` Founder Loop V1 productization
conveyor is recorded in `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`
with detailed goals, tasks, routes, model fields, storage semantics, UI
outcomes, proof lanes, and authority boundaries for release surface truth, API
perimeter, Action decisions, the implemented Today-to-Action vertical loop,
implemented Chat receipts and handoff, Memory Review accept/correct/reject decisions,
implemented Evidence Timeline productization
(`docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`), and
implemented promotion/proof lanes
(`docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`).
FCC-MEM-001 Memory Workbench V1 adds the backend-owned Memory Workbench,
search/filter route, manual safe-summary candidate intake, expanded lifecycle
receipts, deterministic quality grouping, Control Center workbench cards, CLI
parity, and `scripts/verify_fcc_mem_001_memory_workbench.py` without
delete/export execution, semantic/vector search, connector writes, context
injection, public beta, or production authority.
FCC-LOOP-002 Founder Loop Ergonomics Pass adds the Control Center daily-loop
command deck, Briefing spine entry, and grouped Action Inbox, Briefing, Memory,
and Evidence operator summaries over existing backend read models without new
backend authority.
Every module
feeds Today, Actions, Evidence, and Memory;
source provenance, reviewed business memory, Evidence-as-history,
Plans-to-Action envelopes, Chat operator truth, governed Code proposal refs,
cross-surface intake, memory quality, and loop binding proceed before broader
authority. Governed Code uses safe proposal refs and apply remains blocked
until a later exact scope exists. These are planning
artifacts and do not grant runtime authority, public distribution, public beta,
broad autonomy, unrestricted shell/browser/network authority, connector writes,
plugin runtime import, provider/model authority, mobile runtime, backend
routes, Control Center controls, or production authority.

```text
docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md
docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md
docs/kanban/founder_command_center_board.md
docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md
docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md
docs/macos/UAA_P1_087_2A_PRIVATE_TRIAL_PACKET_AND_UI_TUNING_SURFACE.md
docs/macos/UAA_P1_087_2B_PRIVATE_TRIAL_ACCEPTANCE_LEDGER.md
docs/macos/UAA_P1_087_2C_PRIVATE_TRIAL_MANUAL_REVIEW_SCAFFOLD.md
docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md
docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md
docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md
docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md
docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md
docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md
docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md
docs/control_center/FCC_LOOP_002_FOUNDER_LOOP_ERGONOMICS_PASS.md
docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md
docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md
docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md
docs/control_center/founder_loop_api_perimeter_manifest.json
docs/api/FCC_V1_001_API_PERIMETER_FOR_REAL_MUTATIONS.md
docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md
docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md
docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md
docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md
docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md
docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md
docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md
docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md
docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md
docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md
docs/api/UAA_P1_083_LOCAL_BEARER_SESSION_GATE.md
docs/api/UAA_P1_084_MUTATING_ROUTE_IDEMPOTENCY_AUDIT.md
docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md
docs/metrics/NORTH_STAR_METRICS.md
docs/codex/CODEX_EXECUTION_PROMPTS.md
docs/schemas/today_product_spine_contract.schema.json
docs/schemas/evidence_history_grammar.schema.json
docs/schemas/memory_source_provenance.schema.json
docs/schemas/chat_local_operator_surface.schema.json
docs/schemas/governed_code_workbench.schema.json
docs/schemas/cross_surface_memory_intake.schema.json
docs/schemas/memory_to_loop_binding.schema.json
docs/schemas/memory_review_decision_capture.schema.json
docs/schemas/business_memory_quality_controls.schema.json
docs/schemas/plans_action_envelopes.schema.json
docs/schemas/api_local_auth_gate.schema.json
docs/schemas/api_mutating_route_idempotency_audit.schema.json
docs/schemas/founder_loop_api_perimeter.schema.json
```

## Historical Currentness Repairs

These historical notes remain active documentation-integrity anchors:

- v0.29.4 repairs documentation archive references and confirms legacy
  historical verifiers are not current release gates; stale Ruff excludes were
  removed.
- v0.35.1 hardens M31 no-op runtime behavior by denying hidden dynamic dispatch
  and hidden side-effect paths.
- v0.37.1 hardens M33 redacted file preview safety.
- v0.37.3 repairs active roadmap label alignment.

## Start Here

```text
README.md
VERSION.md
SECURITY.md
docs/portfolio/CURRENT_STATUS.md
docs/portfolio/PRODUCT_NORTH_STAR.md
docs/portfolio/SCREENSHOTS.md
docs/portfolio/GOLDEN_PATH_DEMO.md
docs/portfolio/CASE_STUDY.md
docs/README.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/09_roadmap.md
docs/roadmap/README.md
docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md
docs/releases/TAG_CATALOG.md
docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md
docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md
docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md
docs/kanban/founder_command_center_board.md
docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md
docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md
docs/metrics/NORTH_STAR_METRICS.md
docs/codex/CODEX_EXECUTION_PROMPTS.md
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
docs/control_center/ROUTE_STATUS_MANIFEST.md
docs/control_center/route_status_manifest.json
docs/verification/milestone_status_manifest.json
docs/verification/verification_maintainability_policy.json
docs/cua/COMPUTER_USE_CUA_CONTRACT.md
docs/cua/cua_release_surface_manifest.json
docs/control_center/PRODUCT_LANGUAGE_RULES.md
docs/kanban/current_board.md
docs/security/SECURITY_TRIAGE_RUNBOOK.md
docs/archive/README.md
docs/archive/releases/v0_104_0/README_IMPORT.md
docs/archive/releases/v0_104_0/master_plan.md
docs/release_notes/v0_104_0.md
docs/implementation/foundation_gate_implementation_plan_v0_104_0.md
docs/release_notes/checkpoint_m169.md
docs/release_notes/checkpoint_m166.md
docs/release_notes/checkpoint_m167.md
docs/truth/GOVERNED_WEB_EVIDENCE.md
docs/observability/SESSION_LOGGING_M167.md
docs/developer/LOCAL_LAUNCHER.md
scripts/dev/README.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/NEXT_SEQUENCE_v0_17_5.md
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/roadmap/M61_M100_ROADMAP.md
docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md
docs/productization/MULTI_USER_PRODUCT_BOUNDARY.md
docs/productization/MULTI_USER_PRODUCT_BOUNDARY_POLICY.md
docs/productization/MULTI_USER_PRODUCT_BOUNDARY_AUTHORITY_BOUNDARY.md
docs/productization/MULTI_USER_PRODUCT_BOUNDARY_RECEIPT_PLAN.md
docs/productization/MULTI_USER_PRODUCT_BOUNDARY_NON_GOALS.md
docs/productization/M141_TO_M142_BOUNDARY.md
docs/productization/ALPHA_PRIVACY_REVIEW.md
docs/productization/ALPHA_PRIVACY_REVIEW_POLICY.md
docs/productization/ALPHA_PRIVACY_REVIEW_AUTHORITY_BOUNDARY.md
docs/productization/ALPHA_PRIVACY_REVIEW_RECEIPT_PLAN.md
docs/productization/ALPHA_PRIVACY_REVIEW_NON_GOALS.md
docs/productization/M142_TO_M143_BOUNDARY.md
docs/productization/ALPHA_UI_APP_READINESS.md
docs/productization/ALPHA_UI_APP_READINESS_POLICY.md
docs/productization/ALPHA_UI_APP_READINESS_AUTHORITY_BOUNDARY.md
docs/productization/ALPHA_UI_APP_READINESS_RECEIPT_PLAN.md
docs/productization/ALPHA_UI_APP_READINESS_NON_GOALS.md
docs/productization/M143_TO_M144_BOUNDARY.md
docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT.md
docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_POLICY.md
docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_AUTHORITY_BOUNDARY.md
docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_RECEIPT_PLAN.md
docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_NON_GOALS.md
docs/productization/M144_TO_M145_BOUNDARY.md
docs/productization/ENTERPRISE_PRO_SAFETY_MODES.md
docs/productization/ENTERPRISE_PRO_SAFETY_MODES_POLICY.md
docs/productization/ENTERPRISE_PRO_SAFETY_MODES_AUTHORITY_BOUNDARY.md
docs/productization/ENTERPRISE_PRO_SAFETY_MODES_RECEIPT_PLAN.md
docs/productization/ENTERPRISE_PRO_SAFETY_MODES_NON_GOALS.md
docs/productization/M145_TO_M146_BOUNDARY.md
docs/productization/BILLING_PLAN_BOUNDARY.md
docs/productization/BILLING_PLAN_BOUNDARY_POLICY.md
docs/productization/BILLING_PLAN_BOUNDARY_AUTHORITY_BOUNDARY.md
docs/productization/BILLING_PLAN_BOUNDARY_RECEIPT_PLAN.md
docs/productization/BILLING_PLAN_BOUNDARY_NON_GOALS.md
docs/productization/M146_TO_M147_BOUNDARY.md
docs/productization/PUBLIC_DOCS_WIKI_READINESS.md
docs/productization/PUBLIC_DOCS_WIKI_READINESS_POLICY.md
docs/productization/PUBLIC_DOCS_WIKI_READINESS_AUTHORITY_BOUNDARY.md
docs/productization/PUBLIC_DOCS_WIKI_READINESS_RECEIPT_PLAN.md
docs/productization/PUBLIC_DOCS_WIKI_READINESS_NON_GOALS.md
docs/productization/M147_TO_M148_BOUNDARY.md
docs/productization/EXTERNAL_SECURITY_REVIEW.md
docs/productization/EXTERNAL_SECURITY_REVIEW_POLICY.md
docs/productization/EXTERNAL_SECURITY_REVIEW_AUTHORITY_BOUNDARY.md
docs/productization/EXTERNAL_SECURITY_REVIEW_RECEIPT_PLAN.md
docs/productization/EXTERNAL_SECURITY_REVIEW_NON_GOALS.md
docs/productization/M148_TO_M149_BOUNDARY.md
docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE.md
docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_POLICY.md
docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_AUTHORITY_BOUNDARY.md
docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_RECEIPT_PLAN.md
docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_NON_GOALS.md
docs/productization/M149_TO_M150_BOUNDARY.md
docs/productization/ULTIMATE_AI_AGENT_ALPHA.md
docs/productization/ULTIMATE_AI_AGENT_ALPHA_POLICY.md
docs/productization/ULTIMATE_AI_AGENT_ALPHA_AUTHORITY_BOUNDARY.md
docs/productization/ULTIMATE_AI_AGENT_ALPHA_RECEIPT_PLAN.md
docs/productization/ULTIMATE_AI_AGENT_ALPHA_NON_GOALS.md
docs/productization/M150_ALPHA_TO_BETA_BOUNDARY.md
docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md
docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_AUTHORITY_BOUNDARY.md
docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_RUNBOOK.md
docs/model_management/LOCAL_MODEL_MANAGEMENT_CHARTER.md
docs/model_management/LOCAL_MODEL_MANAGEMENT_AUTHORITY_BOUNDARY.md
docs/model_management/LOCAL_MODEL_MANAGEMENT_RECEIPT_PLAN.md
docs/model_management/LOCAL_MODEL_MANAGEMENT_NON_GOALS.md
docs/model_management/M152_TO_M153_BOUNDARY.md
docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md
docs/model_management/M160_HUGGING_FACE_GGUF_SEARCH.md
docs/model_management/M161_LOCAL_SYSTEM_CAPABILITY_PROBE.md
docs/model_management/M162_GGUF_MODEL_ACQUISITION.md
docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md
docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md
docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md
docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md
docs/production/LOCAL_MODEL_PRODUCTION_READINESS_GATE.md
docs/production/LOCAL_MODEL_PRODUCTION_READINESS_BOUNDARY.md
docs/production/LOCAL_MODEL_PRODUCTION_READINESS_RECEIPT_PLAN.md
docs/production/LOCAL_MODEL_PRODUCTION_READINESS_NON_GOALS.md
docs/production/M166_PRODUCTION_AUTHORITY_GATE.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md
docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md
docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md
docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md
docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md
docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md
docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md
docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md
docs/production/RELEASE_VERIFICATION_LANES.md
docs/production/RELEASE_EVIDENCE_PACKET.md
docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md
docs/production/BACKUP_RESTORE_VERIFICATION.md
docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md
docs/production/LOCAL_RUNTIME_PACKAGING.md
docs/api/SAFE_STATIC_MANIFEST_CACHING.md
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
docs/control_center/PRODUCT_LANGUAGE_RULES.md
docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_BOUNDARY.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_NON_GOALS.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md
docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE.md
docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_POLICY.md
docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_AUTHORITY_BOUNDARY.md
docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_RECEIPT_PLAN.md
docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_NON_GOALS.md
docs/autonomy/M140_TO_M141_BOUNDARY.md
docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION.md
docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_POLICY.md
docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_AUTHORITY_BOUNDARY.md
docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_RECEIPT_PLAN.md
docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_NON_GOALS.md
docs/autonomy/M139_TO_M140_BOUNDARY.md
docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS.md
docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_POLICY.md
docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_AUTHORITY_BOUNDARY.md
docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_RECEIPT_PLAN.md
docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_NON_GOALS.md
docs/autonomy/M138_TO_M139_BOUNDARY.md
docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW.md
docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_POLICY.md
docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_AUTHORITY_BOUNDARY.md
docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_RECEIPT_PLAN.md
docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_NON_GOALS.md
docs/autonomy/M137_TO_M138_BOUNDARY.md
docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION.md
docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_POLICY.md
docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_AUTHORITY_BOUNDARY.md
docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_RECEIPT_PLAN.md
docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_NON_GOALS.md
docs/autonomy/M136_TO_M137_BOUNDARY.md
docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER.md
docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_POLICY.md
docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_AUTHORITY_BOUNDARY.md
docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_RECEIPT_PLAN.md
docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_NON_GOALS.md
docs/autonomy/M135_TO_M136_BOUNDARY.md
docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING.md
docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_POLICY.md
docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_AUTHORITY_BOUNDARY.md
docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_RECEIPT_PLAN.md
docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_NON_GOALS.md
docs/autonomy/M134_TO_M135_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW.md
docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_POLICY.md
docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_RECEIPT_PLAN.md
docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_NON_GOALS.md
docs/mobile/M101_TO_M102_BOUNDARY.md
docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT.md
docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_POLICY.md
docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_AUTHORITY_BOUNDARY.md
docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_RECEIPT_PLAN.md
docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_NON_GOALS.md
docs/mobile/M102_TO_M103_BOUNDARY.md
docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_CONTRACT.md
docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_POLICY.md
docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_AUTHORITY_BOUNDARY.md
docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_RECEIPT_PLAN.md
docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_NON_GOALS.md
docs/mobile/M103_TO_M104_BOUNDARY.md
docs/mobile/NOTIFICATION_PLANNING_NO_PUSH.md
docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_POLICY.md
docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_AUTHORITY_BOUNDARY.md
docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_RECEIPT_PLAN.md
docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_NON_GOALS.md
docs/mobile/M104_TO_M105_BOUNDARY.md
docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION.md
docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_POLICY.md
docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_AUTHORITY_BOUNDARY.md
docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_RECEIPT_PLAN.md
docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_NON_GOALS.md
docs/mobile/M105_TO_M106_BOUNDARY.md
docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC.md
docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_POLICY.md
docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_RECEIPT_PLAN.md
docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_NON_GOALS.md
docs/mobile/M106_TO_M107_BOUNDARY.md
docs/mobile/MOBILE_APPROVAL_RENEWAL_UX.md
docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_POLICY.md
docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_RECEIPT_PLAN.md
docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_NON_GOALS.md
docs/mobile/M107_TO_M108_BOUNDARY.md
docs/mobile/MOBILE_KILL_SWITCH_REVOCATION.md
docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_POLICY.md
docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_RECEIPT_PLAN.md
docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_NON_GOALS.md
docs/mobile/M108_TO_M109_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER.md
docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_POLICY.md
docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_RECEIPT_PLAN.md
docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_NON_GOALS.md
docs/mobile/M109_TO_M110_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE.md
docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_POLICY.md
docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md
docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_RECEIPT_PLAN.md
docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_NON_GOALS.md
docs/mobile/M110_TO_M111_BOUNDARY.md
docs/production/PRODUCTION_THREAT_MODEL.md
docs/production/PRODUCTION_THREAT_MODEL_POLICY.md
docs/production/PRODUCTION_THREAT_MODEL_AUTHORITY_BOUNDARY.md
docs/production/PRODUCTION_THREAT_MODEL_RECEIPT_PLAN.md
docs/production/PRODUCTION_THREAT_MODEL_NON_GOALS.md
docs/production/M111_TO_M112_BOUNDARY.md
docs/production/USER_WORKSPACE_IDENTITY_MODEL.md
docs/production/USER_WORKSPACE_IDENTITY_POLICY.md
docs/production/USER_WORKSPACE_IDENTITY_AUTHORITY_BOUNDARY.md
docs/production/USER_WORKSPACE_IDENTITY_RECEIPT_PLAN.md
docs/production/USER_WORKSPACE_IDENTITY_NON_GOALS.md
docs/production/M112_TO_M113_BOUNDARY.md
docs/production/SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT.md
docs/production/SECRETS_BOUNDARY_POLICY.md
docs/production/SECRETS_BOUNDARY_AUTHORITY_BOUNDARY.md
docs/production/SECRETS_BOUNDARY_RECEIPT_PLAN.md
docs/production/SECRETS_BOUNDARY_NON_GOALS.md
docs/production/M113_TO_M114_BOUNDARY.md
docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md
docs/production/ACCOUNT_CONNECTOR_POLICY.md
docs/production/ACCOUNT_CONNECTOR_AUTHORITY_BOUNDARY.md
docs/production/ACCOUNT_CONNECTOR_RECEIPT_PLAN.md
docs/production/ACCOUNT_CONNECTOR_NON_GOALS.md
docs/production/M114_TO_M115_BOUNDARY.md
docs/production/PRODUCTION_AUDIT_RETENTION_POLICY.md
docs/production/PRODUCTION_AUDIT_RETENTION_AUTHORITY_BOUNDARY.md
docs/production/PRODUCTION_AUDIT_RETENTION_RECEIPT_PLAN.md
docs/production/PRODUCTION_AUDIT_RETENTION_NON_GOALS.md
docs/production/M115_TO_M116_BOUNDARY.md
docs/production/ROLE_BASED_AUTHORITY_MODEL.md
docs/production/ROLE_BASED_AUTHORITY_BOUNDARY.md
docs/production/ROLE_BASED_AUTHORITY_RECEIPT_PLAN.md
docs/production/ROLE_BASED_AUTHORITY_NON_GOALS.md
docs/production/M116_TO_M117_BOUNDARY.md
docs/files/BROADER_FILE_CAPABILITY_REVIEW.md
docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md
docs/files/FILE_CAPABILITY_RISK_REGISTER.md
docs/files/FILE_CAPABILITY_DECISION_RECORD.md
docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md
docs/files/M34_TO_M35_BOUNDARY.md
docs/files/SAFE_FILE_REVIEW_WORKFLOW.md
docs/files/FILE_REVIEW_PACKET_CONTRACT.md
docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md
docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md
docs/browser/BROWSER_OBSERVE_ONLY_ADAPTER.md
docs/browser/BROWSER_OBSERVE_ONLY_POLICY.md
docs/browser/BROWSER_OBSERVE_ONLY_RESULT_CONTRACT.md
docs/browser/BROWSER_OBSERVE_ONLY_AUTHORITY_BOUNDARY.md
docs/browser/BROWSER_OBSERVE_ONLY_RECEIPT_PLAN.md
docs/browser/M74_TO_M75_BOUNDARY.md
docs/browser/BROWSER_ACTION_DRY_RUN_PLANNER.md
docs/browser/LOW_RISK_BROWSER_CLICKS.md
docs/browser/LOW_RISK_BROWSER_CLICK_POLICY.md
docs/browser/LOW_RISK_BROWSER_CLICK_AUTHORITY_BOUNDARY.md
docs/browser/LOW_RISK_BROWSER_CLICK_RECEIPT_PLAN.md
docs/browser/LOW_RISK_BROWSER_CLICK_NON_GOALS.md
docs/browser/M94_TO_M95_BOUNDARY.md
docs/browser/BROWSER_ACTION_DRY_RUN_POLICY.md
docs/browser/BROWSER_ACTION_DRY_RUN_RESULT_CONTRACT.md
docs/browser/BROWSER_ACTION_DRY_RUN_AUTHORITY_BOUNDARY.md
docs/browser/BROWSER_ACTION_DRY_RUN_RECEIPT_PLAN.md
docs/browser/M75_TO_M76_BOUNDARY.md
docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_V1.md
docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_POLICY.md
docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RESULT_CONTRACT.md
docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_AUTHORITY_BOUNDARY.md
docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RECEIPT_PLAN.md
docs/openwebui/M76_TO_M77_BOUNDARY.md
docs/openwebui/OPENWEBUI_SAFE_HANDOFF_EXECUTION.md
docs/openwebui/OPENWEBUI_SAFE_HANDOFF_POLICY.md
docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RESULT_CONTRACT.md
docs/openwebui/OPENWEBUI_SAFE_HANDOFF_AUTHORITY_BOUNDARY.md
docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RECEIPT_PLAN.md
docs/openwebui/M77_TO_M78_BOUNDARY.md
docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md
docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md
docs/tooling/PLUGIN_MANIFEST_POLICY.md
docs/tooling/PLUGIN_PERMISSION_MODEL.md
docs/tooling/PLUGIN_PROVENANCE_REVIEW.md
docs/tooling/PLUGIN_SANDBOX_TEST_PLAN.md
docs/tooling/PLUGIN_MANIFEST_AUTHORITY_BOUNDARY.md
docs/tooling/PLUGIN_MANIFEST_RECEIPT_PLAN.md
docs/tooling/M78_TO_M79_BOUNDARY.md
docs/tooling/PLUGIN_INSTALL_REVIEW.md
docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md
docs/tooling/PLUGIN_INSTALL_REVIEW_AUTHORITY_BOUNDARY.md
docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md
docs/tooling/M79_TO_M80_BOUNDARY.md
docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE.md
docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_CONTRACTS.md
docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_NON_GOALS.md
docs/hardening/M80_TO_M81_BOUNDARY.md
docs/sandbox/RUNTIME_SANDBOX_SPEC.md
docs/sandbox/RUNTIME_SANDBOX_SPEC_CONTRACTS.md
docs/sandbox/RUNTIME_SANDBOX_SPEC_AUTHORITY_BOUNDARY.md
docs/sandbox/RUNTIME_SANDBOX_SPEC_NON_GOALS.md
docs/sandbox/M81_TO_M82_BOUNDARY.md
docs/sandbox/COMMAND_PROPOSAL_CONTRACTS.md
docs/sandbox/COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md
docs/sandbox/COMMAND_PROPOSAL_RECEIPT_PLAN.md
docs/sandbox/COMMAND_PROPOSAL_NON_GOALS.md
docs/sandbox/M82_TO_M83_BOUNDARY.md
docs/sandbox/SHELL_DRY_RUN_CLASSIFIER.md
docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_POLICY.md
docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_AUTHORITY_BOUNDARY.md
docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_RECEIPT_PLAN.md
docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_NON_GOALS.md
docs/sandbox/M83_TO_M84_BOUNDARY.md
docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND.md
docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_POLICY.md
docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_AUTHORITY_BOUNDARY.md
docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_RECEIPT_PLAN.md
docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_NON_GOALS.md
docs/sandbox/M84_TO_M85_BOUNDARY.md
docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST.md
docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_POLICY.md
docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md
docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_RECEIPT_PLAN.md
docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_NON_GOALS.md
docs/sandbox/M85_TO_M86_BOUNDARY.md
docs/sandbox/SHELL_APPROVAL_GATE.md
docs/sandbox/SHELL_APPROVAL_GATE_POLICY.md
docs/sandbox/SHELL_APPROVAL_GATE_AUTHORITY_BOUNDARY.md
docs/sandbox/SHELL_APPROVAL_GATE_RECEIPT_PLAN.md
docs/sandbox/SHELL_APPROVAL_GATE_NON_GOALS.md
docs/sandbox/M86_TO_M87_BOUNDARY.md
docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY.md
docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_POLICY.md
docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_AUTHORITY_BOUNDARY.md
docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_RECEIPT_PLAN.md
docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_NON_GOALS.md
docs/sandbox/M87_TO_M88_BOUNDARY.md
docs/sandbox/MUTATING_COMMAND_PROPOSAL.md
docs/sandbox/MUTATING_COMMAND_PROPOSAL_POLICY.md
docs/sandbox/MUTATING_COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md
docs/sandbox/MUTATING_COMMAND_PROPOSAL_RECEIPT_PLAN.md
docs/sandbox/MUTATING_COMMAND_PROPOSAL_NON_GOALS.md
docs/sandbox/M88_TO_M89_BOUNDARY.md
docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY.md
docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_POLICY.md
docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_AUTHORITY_BOUNDARY.md
docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_RECEIPT_PLAN.md
docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_NON_GOALS.md
docs/sandbox/M89_TO_M90_BOUNDARY.md
docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE.md
docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md
docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md
docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_RECEIPT_PLAN.md
docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_NON_GOALS.md
docs/sandbox/M90_TO_M91_BOUNDARY.md
docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT.md
docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT_POLICY.md
docs/tools/AUTONOMOUS_TOOL_EXECUTION_AUTHORITY_BOUNDARY.md
docs/tools/AUTONOMOUS_TOOL_EXECUTION_RECEIPT_PLAN.md
docs/tools/AUTONOMOUS_TOOL_EXECUTION_NON_GOALS.md
docs/tools/M91_TO_M92_BOUNDARY.md
docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION.md
docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_POLICY.md
docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_AUTHORITY_BOUNDARY.md
docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_RECEIPT_PLAN.md
docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_NON_GOALS.md
docs/autonomy/M92_TO_M93_BOUNDARY.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md
docs/dry_run_audit/M58_TO_M59_BOUNDARY.md
docs/public_readiness/PUBLIC_GITHUB_READINESS.md
docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md
docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md
docs/public_readiness/M59_TO_M60_BOUNDARY.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md
docs/beta/POST_M60_AUTONOMY_BOUNDARY.md
docs/autonomy/AUTONOMY_MODE_CHARTER.md
docs/autonomy/AUTHORITY_LEVELS.md
docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md
docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md
docs/autonomy/M61_TO_M62_BOUNDARY.md
docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md
docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md
docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md
docs/autonomy/M62_TO_M63_BOUNDARY.md
docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md
docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md
docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md
docs/autonomy/M63_TO_M64_BOUNDARY.md
docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md
docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md
docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md
docs/autonomy/M64_TO_M65_BOUNDARY.md
docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md
docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md
docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md
docs/autonomy/M65_TO_M66_BOUNDARY.md
docs/autonomy/SCOPED_APPROVAL_BUNDLES.md
docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md
docs/autonomy/SCOPED_APPROVAL_BUNDLE_NON_GOALS.md
docs/autonomy/M66_TO_M67_BOUNDARY.md
docs/autonomy/REVOCATION_KILL_SWITCH.md
docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md
docs/autonomy/REVOCATION_KILL_SWITCH_NON_GOALS.md
docs/autonomy/M67_TO_M68_BOUNDARY.md
docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md
docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md
docs/autonomy/AUTONOMY_RISK_CLASSIFIER_NON_GOALS.md
docs/autonomy/M68_TO_M69_BOUNDARY.md
docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md
docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md
docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_NON_GOALS.md
docs/autonomy/M69_TO_M70_BOUNDARY.md
docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md
docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md
docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_NON_GOALS.md
docs/autonomy/M70_TO_M71_BOUNDARY.md
docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md
docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md
docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md
docs/network/M71_TO_M72_BOUNDARY.md
docs/network/READ_ONLY_HTTP_FETCH_TOOL.md
docs/network/READ_ONLY_HTTP_FETCH_POLICY.md
docs/network/READ_ONLY_HTTP_FETCH_AUTHORITY_BOUNDARY.md
docs/network/WEB_ACCESS_GATEWAY.md
docs/network/WEB_ACCESS_GATEWAY_CODEX_PROMPTS.md
docs/network/WEB_ACCESS_GATEWAY_DEFINITION_OF_DONE.md
docs/network/WEB_ACCESS_GATEWAY_PR_BODY.md
docs/network/WEB_ACCESS_GATEWAY_PR_SEQUENCE.md
docs/network/WEB_ACCESS_GATEWAY_SECURITY_REVIEW_CHECKLIST.md
docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md
docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md
docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION.md
docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_POLICY.md
docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md
docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_RECEIPT_PLAN.md
docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_NON_GOALS.md
docs/network/M95_TO_M96_BOUNDARY.md
docs/tooling/PLUGIN_EXECUTION_SANDBOX.md
docs/tooling/PLUGIN_EXECUTION_SANDBOX_POLICY.md
docs/tooling/PLUGIN_EXECUTION_SANDBOX_AUTHORITY_BOUNDARY.md
docs/tooling/PLUGIN_EXECUTION_SANDBOX_RECEIPT_PLAN.md
docs/tooling/PLUGIN_EXECUTION_SANDBOX_NON_GOALS.md
docs/tooling/M96_TO_M97_BOUNDARY.md
docs/network/READ_ONLY_HTTP_FETCH_RECEIPT_PLAN.md
docs/network/M72_TO_M73_BOUNDARY.md
docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW.md
docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW_POLICY.md
docs/browser/BROWSER_AUTOMATION_AUTHORITY_BOUNDARY.md
docs/browser/BROWSER_AUTOMATION_RECEIPT_PLAN.md
docs/browser/M73_TO_M74_BOUNDARY.md
docs/roadmap/M61_M100_ROADMAP.md
docs/files/FILE_REVIEW_RECEIPT_PLAN.md
docs/files/FILE_REVIEW_NON_GOALS.md
docs/files/M35_TO_M36_BOUNDARY.md
docs/control_center/FILE_REVIEW_SURFACE.md
docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md
docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md
docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md
docs/control_center/M36_TO_M37_BOUNDARY.md
docs/control_center/FILE_REVIEW_SURFACE_READINESS.md
docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md
docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md
docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md
docs/files/FILE_REVIEW_APPROVAL_API.md
docs/files/M37_TO_M38_BOUNDARY.md
docs/context/SAFE_CONTEXT_PROPOSAL_FROM_APPROVED_REVIEW.md
docs/context/CONTEXT_PROPOSAL_CONTRACT.md
docs/context/CONTEXT_PROPOSAL_AUTHORITY_BOUNDARY.md
docs/context/CONTEXT_PROPOSAL_RECEIPT_PLAN.md
docs/context/CONTEXT_PROPOSAL_NON_GOALS.md
docs/context/M38_TO_M39_BOUNDARY.md
docs/control_center/CONTEXT_PROPOSAL_SURFACE.md
docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md
docs/control_center/CONTEXT_PROPOSAL_MOCK_DATA_POLICY.md
docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md
docs/control_center/M39_TO_M40_BOUNDARY.md
docs/context/CONTEXT_HANDOFF_APPROVAL.md
docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md
docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md
docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md
docs/context/M40_TO_M41_BOUNDARY.md
docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md
docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md
docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md
docs/prototype/M41_TO_M42_BOUNDARY.md
docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md
docs/mobile/M42_TO_M43_BOUNDARY.md
docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md
docs/mobile/M43_TO_M44_BOUNDARY.md
docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md
docs/mobile/M44_TO_M45_BOUNDARY.md
docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md
docs/mobile/M45_TO_M46_BOUNDARY.md
docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md
docs/mobile/M46_TO_M47_BOUNDARY.md
docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md
docs/mobile/M47_TO_M48_BOUNDARY.md
docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md
docs/mobile/M48_TO_M49_BOUNDARY.md
docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md
docs/mobile/M49_TO_M50_BOUNDARY.md
docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md
docs/mobile/M50_TO_M51_BOUNDARY.md
docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md
docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md
docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md
docs/openwebui/M51_TO_M52_BOUNDARY.md
docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md
docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md
docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md
docs/openwebui/M52_TO_M53_BOUNDARY.md
docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md
docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md
docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md
docs/tools/M53_TO_M54_BOUNDARY.md
docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md
docs/media/SAFE_MEDIA_METADATA_POLICY.md
docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md
docs/media/M54_TO_M55_BOUNDARY.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md
docs/observability/M55_TO_M56_BOUNDARY.md
docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md
docs/evals/AGENT_EVAL_REGRESSION_POLICY.md
docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md
docs/evals/M56_TO_M57_BOUNDARY.md
docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md
docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md
docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md
docs/sandbox/M57_TO_M58_BOUNDARY.md
docs/tools/FILE_TOOL_CAPABILITY_MATRIX.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
docs/maintenance/documentation_integrity_checklist.md
docs/maintenance/codex_plugin_capability_inventory.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md
docs/ui/CLIENT_SURFACE_ROLES.md
docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md
docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md
docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md
docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md
docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md
docs/openwebui/OPENWEBUI_SECURITY_MODEL.md
docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md
docs/openwebui/OPENWEBUI_NON_GOALS.md
docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md
docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md
docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md
docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md
docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md
docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md
docs/runtime/FIRST_LOCAL_LLM_CALL.md
docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md
docs/runtime/M23_FIXED_PROMPT_POLICY.md
docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md
docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md
docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md
docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md
docs/runtime/M23_MANUAL_CLI_USAGE.md
docs/runtime/M23_TO_M24_BOUNDARY.md
docs/memory/MEMORY_PROVIDER_ABSTRACTION.md
docs/memory/LOCAL_MEMORY_STORE.md
docs/memory/MEMORY_RECORD_SCHEMA.md
docs/memory/MEMORY_WRITE_POLICY.md
docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md
docs/memory/MEMORY_SOURCE_PRIORITY.md
docs/memory/MEMORY_RECALL_PLANNING.md
docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md
docs/memory/MEMORY_CONFLICT_AND_STALENESS.md
docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md
docs/memory/MEMORY_SECURITY_MODEL.md
docs/memory/MEMORY_NON_GOALS.md
docs/memory/MEMORYOS_REVIEW_INCORPORATION.md
docs/memory/M24_TO_M25_BOUNDARY.md
docs/truth/TRUTH_SOURCE_ROUTER.md
docs/truth/EVIDENCE_CLAIM_CHECKER.md
docs/truth/TRUTH_SOURCE_PRIORITY.md
docs/truth/CLAIM_EVIDENCE_CHAIN.md
docs/truth/CLAIM_VERIFICATION_POLICY.md
docs/truth/CLAIM_CONFLICT_AND_STALENESS.md
docs/truth/MEMORY_TRUTH_BOUNDARY.md
docs/truth/TRUTH_NON_GOALS.md
docs/truth/M25_TO_M26_BOUNDARY.md
docs/recall/GROUNDED_RECALL_ROUTER.md
docs/recall/CONTEXT_PACK_BUILDER.md
docs/recall/RECALL_SOURCE_PRIORITY.md
docs/recall/RECALL_CANDIDATE_POLICY.md
docs/recall/CONTEXT_PACK_SAFETY.md
docs/recall/RECALL_NON_GOALS.md
docs/recall/M26_TO_M27_BOUNDARY.md
docs/tools/TOOL_BROKER_V2.md
docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md
docs/tools/TOOL_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_INTENT_RECEIPT_PLAN.md
docs/tools/M27_TO_M28_BOUNDARY.md
docs/tools/TOOL_RUNTIME_ADAPTER.md
docs/tools/NOOP_TOOL_RUNTIME.md
docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md
docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md
docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md
docs/tools/TOOL_RUNTIME_NON_GOALS.md
docs/tools/M31_TO_M32_BOUNDARY.md
docs/tools/FILESYSTEM_METADATA_TOOL.md
docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md
docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md
docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md
docs/tools/FILESYSTEM_METADATA_NON_GOALS.md
docs/tools/M32_TO_M33_BOUNDARY.md
docs/tools/REDACTED_FILE_PREVIEW_TOOL.md
docs/tools/REDACTED_FILE_PREVIEW_POLICY.md
docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md
docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md
docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md
docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md
docs/tools/M33_TO_M34_BOUNDARY.md
docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md
docs/files/BROADER_FILE_CAPABILITY_REVIEW.md
docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md
docs/files/FILE_CAPABILITY_RISK_REGISTER.md
docs/files/FILE_CAPABILITY_DECISION_RECORD.md
docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md
docs/files/M34_TO_M35_BOUNDARY.md
docs/approvals/APPROVAL_AUTHORITY_V2.md
docs/approvals/ACTION_POLICY.md
docs/approvals/APPROVAL_GRANT_BINDING.md
docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md
docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md
docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md
docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md
docs/approvals/APPROVAL_RECEIPT_PLAN.md
docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md
docs/approvals/M28_TO_M29_BOUNDARY.md
docs/planning/TASK_PLANNING_ENGINE.md
docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md
docs/planning/TASK_DEPENDENCY_GRAPH.md
docs/planning/TASK_INPUT_BOUNDARY.md
docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md
docs/planning/TASK_PLAN_DECISION_ENVELOPE.md
docs/planning/TASK_PLAN_RECEIPT_PLAN.md
docs/planning/TASK_PLANNING_NON_GOALS.md
docs/planning/M29_TO_M30_BOUNDARY.md
docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md
docs/execution/EXECUTION_STATE_MACHINE.md
docs/execution/EXECUTION_STEP_CONTRACTS.md
docs/execution/EXECUTION_DEPENDENCY_POLICY.md
docs/execution/EXECUTION_TRANSITION_POLICY.md
docs/execution/EXECUTION_INPUT_BOUNDARY.md
docs/execution/EXECUTION_RECEIPT_PLAN.md
docs/execution/EXECUTION_NON_GOALS.md
docs/execution/M30_TO_M31_BOUNDARY.md
docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md
docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md
docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md
docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md
docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md
docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md
docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md
docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md
docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md
docs/mobile/MOBILE_COMPANION_CONTRACT.md
docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md
docs/mobile/MOBILE_API_PLANNING.md
docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md
docs/mobile/MOBILE_SENSOR_BOUNDARY.md
docs/mobile/MOBILE_SECURITY_MODEL.md
docs/mobile/MOBILE_CAPTURE_POLICY.md
docs/mobile/CCC_IOS_ANDROID_STRATEGY.md
docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md
docs/mobile/MOBILE_COMPANION_NON_GOALS.md
docs/control_center/APPROVAL_QUEUE_UI.md
docs/control_center/RECEIPT_EVENT_VIEWER.md
docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md
docs/control_center/EVENT_TIMELINE_UI.md
docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md
docs/control_center/OPERATOR_RUN_TIMELINE.md
docs/control_center/TRACE_REDACTION_POLICY.md
docs/control_center/EVIDENCE_VIEWER.md
docs/control_center/FILE_REFERENCE_VIEWER.md
docs/control_center/MEMORY_VIEWER.md
docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md
docs/control_center/LOCAL_RUNTIME_STATUS_UI.md
docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md
docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md
```

## Active Canonical Docs

The active canonical docs live in `docs/canonical/`. Use `docs/canonical/CANONICAL_DOC_MAP.md` to map systems to canonical files.

Key active canonical groups:

- roadmap and sequencing: `docs/canonical/09_roadmap.md`, `docs/roadmap/MILESTONE_CHARTERS.md`, `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`
- user control: `docs/canonical/20_user_control_center.md`
- consent, tools, approvals, planning, execution state, and authority: `docs/canonical/21_consent_and_permissions_ledger.md`, `docs/canonical/37_tool_broker.md`, `docs/tools/TOOL_BROKER_V2.md`, `docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md`, `docs/tools/TOOL_AUTHORITY_BOUNDARY.md`, `docs/tools/TOOL_INTENT_RECEIPT_PLAN.md`, `docs/tools/M27_TO_M28_BOUNDARY.md`, `docs/tools/TOOL_RUNTIME_ADAPTER.md`, `docs/tools/NOOP_TOOL_RUNTIME.md`, `docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md`, `docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md`, `docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md`, `docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md`, `docs/tools/TOOL_RUNTIME_NON_GOALS.md`, `docs/tools/M31_TO_M32_BOUNDARY.md`, `docs/tools/FILESYSTEM_METADATA_TOOL.md`, `docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md`, `docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md`, `docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md`, `docs/tools/FILESYSTEM_METADATA_NON_GOALS.md`, `docs/tools/M32_TO_M33_BOUNDARY.md`, `docs/approvals/APPROVAL_AUTHORITY_V2.md`, `docs/approvals/ACTION_POLICY.md`, `docs/approvals/APPROVAL_GRANT_BINDING.md`, `docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md`, `docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md`, `docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md`, `docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md`, `docs/approvals/APPROVAL_RECEIPT_PLAN.md`, `docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md`, `docs/approvals/M28_TO_M29_BOUNDARY.md`, `docs/planning/TASK_PLANNING_ENGINE.md`, `docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md`, `docs/planning/TASK_DEPENDENCY_GRAPH.md`, `docs/planning/TASK_INPUT_BOUNDARY.md`, `docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md`, `docs/planning/TASK_PLAN_DECISION_ENVELOPE.md`, `docs/planning/TASK_PLAN_RECEIPT_PLAN.md`, `docs/planning/TASK_PLANNING_NON_GOALS.md`, `docs/planning/M29_TO_M30_BOUNDARY.md`, `docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md`, `docs/execution/EXECUTION_STATE_MACHINE.md`, `docs/execution/EXECUTION_STEP_CONTRACTS.md`, `docs/execution/EXECUTION_DEPENDENCY_POLICY.md`, `docs/execution/EXECUTION_TRANSITION_POLICY.md`, `docs/execution/EXECUTION_INPUT_BOUNDARY.md`, `docs/execution/EXECUTION_RECEIPT_PLAN.md`, `docs/execution/EXECUTION_NON_GOALS.md`, `docs/execution/M30_TO_M31_BOUNDARY.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md`, `docs/canonical/48_actor_authority_and_identity.md`
- truth, evidence, memory, and files: `docs/canonical/03_memory_system.md`, `docs/canonical/10_file_management.md`, `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/60_truth_source_router.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md`, `docs/truth/TRUTH_SOURCE_ROUTER.md`, `docs/truth/EVIDENCE_CLAIM_CHECKER.md`, `docs/truth/TRUTH_SOURCE_PRIORITY.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`, `docs/truth/CLAIM_VERIFICATION_POLICY.md`, `docs/truth/CLAIM_CONFLICT_AND_STALENESS.md`, `docs/truth/MEMORY_TRUTH_BOUNDARY.md`, `docs/truth/TRUTH_NON_GOALS.md`, `docs/truth/M25_TO_M26_BOUNDARY.md`
- runtime and adapters: `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md`, `docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md`, `docs/platform/PLATFORM_CAPABILITY_REGISTRY.md`
- security and privacy: `docs/canonical/23_security_threat_model.md`, `docs/canonical/24_data_lifecycle_and_privacy.md`, `docs/canonical/45_trusted_computing_base.md`, `docs/canonical/50_data_classification_policy.md`, `docs/canonical/51_redaction_and_safe_debugging.md`
- mobile/device planning: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md`, `docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md`, `docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md`, `docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md`, `docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md`, `docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md`, `docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md`, `docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md`, `docs/mobile/MOBILE_COMPANION_CONTRACT.md`, `docs/mobile/MOBILE_SENSOR_BOUNDARY.md`, `docs/mobile/MOBILE_SECURITY_MODEL.md`
- external tooling and Codex plugin governance: `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`
- UI/client strategy: `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/CLIENT_SURFACE_ROLES.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`
- OpenWebUI bridge contract: `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md`, `docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md`, `docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md`, `docs/openwebui/OPENWEBUI_SECURITY_MODEL.md`, `docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md`, `docs/openwebui/OPENWEBUI_NON_GOALS.md`, `docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md`
- memory provider and local store: `docs/memory/MEMORY_PROVIDER_ABSTRACTION.md`, `docs/memory/LOCAL_MEMORY_STORE.md`, `docs/memory/MEMORY_WRITE_POLICY.md`, `docs/memory/MEMORY_SECURITY_MODEL.md`, `docs/memory/M24_TO_M25_BOUNDARY.md`
- M25 truth source router and evidence claim checker: `docs/truth/TRUTH_SOURCE_ROUTER.md`, `docs/truth/EVIDENCE_CLAIM_CHECKER.md`, `docs/truth/TRUTH_SOURCE_PRIORITY.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`, `docs/truth/CLAIM_VERIFICATION_POLICY.md`, `docs/truth/CLAIM_CONFLICT_AND_STALENESS.md`, `docs/truth/MEMORY_TRUTH_BOUNDARY.md`, `docs/truth/TRUTH_NON_GOALS.md`, `docs/truth/M25_TO_M26_BOUNDARY.md`

## Active API Docs

```text
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
```

API docs describe implemented validation, dry-run, simulated, status, and preview-only routes. Future mobile/device routes are not implemented.

## Active Control Center Docs

```text
docs/control_center/CONTROL_CENTER_CONTRACT.md
docs/control_center/DASHBOARD_SNAPSHOT.md
docs/control_center/ACTION_PREVIEW_POLICY.md
docs/control_center/WEB_CONTROL_CENTER_SHELL.md
docs/control_center/FRONTEND_SAFETY_POLICY.md
docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
docs/control_center/ROUTE_STATUS_MANIFEST.md
docs/control_center/route_status_manifest.json
docs/control_center/UI_WIRING_REPORT.md
docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md
docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md
docs/control_center/PRODUCT_LANGUAGE_RULES.md
docs/control_center/LOCAL_BACKEND_CONNECTION.md
docs/control_center/LOCAL_BROWSER_SMOKE.md
docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md
docs/control_center/APPROVAL_QUEUE_UI.md
docs/control_center/RECEIPT_EVENT_VIEWER.md
docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md
docs/control_center/EVENT_TIMELINE_UI.md
docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md
docs/control_center/TRACE_REDACTION_POLICY.md
docs/control_center/EVIDENCE_VIEWER.md
docs/control_center/FILE_REFERENCE_VIEWER.md
docs/control_center/MEMORY_VIEWER.md
docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md
docs/control_center/LOCAL_RUNTIME_STATUS_UI.md
docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md
docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md
```

M12 Control Center docs describe backend contracts, read-only dashboard snapshots, and action preview policy only. M13 adds a local Web Control Center shell that consumes those routes, renders safe mock fallback data, and submits only preview-only action requests. v0.17.4 polishes local shell reviewability and adds safe local browser smoke reporting documentation. v0.18.0 / M14 stabilizes local backend connection behavior with local-only API base URL policy and visible live/degraded/mock fallback states. v0.18.1 hardens M14 connection safety for public/private non-loopback hosts, URL credentials, secret-like query parameters, and unknown/checking states. v0.18.2 adds Open Design governance docs for Control Center and Mobile Companion UI work. v0.19.0 / M15 adds read-only/preview-only approval queue, receipt viewer, and event viewer UI surfaces with redacted summary-only data. v0.19.1 hardens M15 approval authority and redacted-detail safety copy plus static verifier/Foundation Gate checks. v0.20.0 / M16 adds a read-only event timeline and run/receipt trace viewer with safe refs and Foundation Gate evidence summaries. v0.20.1 hardens M16 trace/redaction safety, second-trace selection coverage, generated build-output hygiene, and no-backend-route Foundation Gate checks. v0.21.0 / M17 adds read-only evidence, file ref, and memory ref summary viewers. v0.21.1 hardens M17 selected-state reviewability, alternate safe mock refs, frontend tests, static verifier coverage, docs, and Foundation Gate checks. v0.21.2 normalizes developer verification commands around `.venv/bin/python` and Makefile targets. v0.22.0 / M18 adds read-only local runtime status and validation-only manual smoke report summary surfaces. v0.23.0 / M19 adds mobile companion contract/API planning only. v0.23.1 hardens M19 roadmap status and mobile contract safety tests only. v0.24.0 / M20 adds Device Capability Broker Contract as contract-only planning and validation. v0.24.1 hardens M20 Device Capability Broker Contract safety without adding runtime authority. v0.25.0 / M21 adds OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. v0.25.1 hardens M21 OpenWebUI content-mode semantics, authority text validation, and verifier/Foundation Gate scanning without adding execution capability. v0.26.0 / M22 adds Local Model Runtime Activation Contract as contract/planning/validation only. v0.26.1 hardens M22 verifier precision and metadata key secret hygiene without adding execution capability. v0.27.0 / M23 adds manual fixed-prompt local model call contracts and CLI-only execution gating without backend routes or production authority.

## Active Design Governance Docs

```text
docs/design/OPEN_DESIGN_SYSTEM.md
docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md
docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md
docs/design/ACCESSIBILITY_BASELINE.md
docs/design/DESIGN_TOOLING_POLICY.md
docs/design/DESIGN_TOKEN_ROADMAP.md
docs/design/UI_COPY_AND_ACTION_LANGUAGE.md
docs/design/DESIGN_ARTIFACT_GOVERNANCE.md
docs/design/COMPONENT_TAXONOMY.md
docs/design/RESPONSIVE_LAYOUT_BASELINE.md
```

v0.18.2 adds Open Design System and UI Design Governance documentation only. The design source of truth is repo-owned docs, reviewed components, and future repo-owned tokens. Design tools, design SaaS, UI generators, screenshot-to-code, and design-to-code systems are not enabled and are not authority.

M15 Approval Queue + Receipt/Event Viewer UI is implemented in v0.19.0 as read-only/preview-only CCC Web summary views. v0.19.1 hardens its authority-boundary and redacted-detail safety checks. v0.20.0 adds M16 Event Timeline + Run/Receipt Trace Viewer as a read-only summary surface. v0.20.1 hardens M16 trace/redaction safety and keeps generated frontend artifacts ignored/untracked. v0.21.0 adds M17 Evidence/File/Memory Viewer as read-only, summary-only CCC Web views. v0.21.1 hardens the existing M17 views without adding approval execution, backend authority, raw data display, or backend API routes. v0.21.2 is dev tooling/docs only and changes no Control Center behavior. v0.22.0 adds M18 local runtime status and manual smoke report summary surfaces; v0.23.0 adds M19 mobile companion contract/API planning only; v0.23.1 hardens M19 roadmap and contract safety checks only.

## Active UI Client Strategy Docs

```text
docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md
docs/ui/CLIENT_SURFACE_ROLES.md
docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md
docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md
```

v0.18.3 clarifies that OpenWebUI is a supported local/dev conversational shell,
CCC means Control Center Clients, and CCC covers CCC Web, CCC iOS, CCC Android,
and CCC macOS. Current product direction keeps Control Center / Founder Command
Center as the first-party product UI. Open Design governs custom CCC surfaces
and does not replace OpenWebUI. These docs add no OpenWebUI integration,
deployment config, frontend feature, backend API route, native app, native build
workflow, mobile sensor access, OS permission integration, signing, keystore,
provisioning, App Store, or Play Store workflow.

v0.25.1 hardens M21 OpenWebUI Bridge + Chat Shell Integration Contract safety while keeping M21 contract/planning/validation only. OpenWebUI remains a supported local/dev conversational shell and is not the agent brain or first-party product cockpit. Python Agent Core remains authority. M21 allows only summary/ref/redacted-preview content modes, rejects blocked raw/future modes for refs and envelopes, permits safe negated authority-boundary text, rejects positive OpenWebUI authority claims, and scans the OpenWebUI bridge package for forbidden runtime/config fragments. M21 adds no OpenWebUI integration, deployment config, Docker config, OpenWebUI plugins/functions/pipelines/tools/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, OpenWebUI runtime execution, user-content local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority. v0.26.0 implements M22 as contract-only metadata/validation. v0.26.1 hardens M22 verifier precision and metadata key secret hygiene only. v0.27.0 implements M23 as manual fixed-prompt local call only.

## Active Post-M20 Roadmap Projection Docs

```text
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
```

v0.18.4 adds post-M20 roadmap projection and M21-M40 capability-layer charters only. M14-M20 remain frozen and unchanged. M21-M40 are planned/provisional and require dedicated future implementation and review prompts. The ecosystem and standards watchlists are watchlist-only and add no integration, plugin enablement, external network, dependency, or parity claim.

## Active Runtime Docs

```text
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/runtime/RUNTIME_READINESS.md
docs/runtime/MANUAL_SMOKE_REPORTS.md
docs/runtime/RUNTIME_CAPABILITY_MATRIX.md
docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md
docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md
docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md
docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md
docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md
docs/platform/PLATFORM_CAPABILITY_REGISTRY.md
```

Model runtime docs distinguish simulated runtime behavior, dev/manual loopback readiness, fixed-prompt manual smoke, and non-authoritative model output. They do not describe general production model execution.

The Platform Capability Registry is a metadata and readiness contract only. It
does not grant platform runtime, installer, read, write, provider, credential,
service, or production authority.

M11 runtime readiness docs describe status/report validation only. They do not describe production runtime execution. v0.15.1 clarifies local loopback policy as supported validation-only and `fake_manual_loopback_smoke` as a fake/test report origin only.

v0.26.0 / M22 adds Local Model Runtime Activation Contract docs as contract/planning/validation only. v0.27.0 / M23 adds the first bounded manual local model call path. v0.28.0 / M24 adds Memory Provider Abstraction + Local Memory Store as governed reviewed-write-only local memory foundation. v0.29.0 / M25 adds Truth Source Router + Evidence Claim Checker as deterministic local contracts over provided refs only. v0.29.5 is documentation policy polish that polishes duplicated policy wording. v0.30.0 implements M26 Grounded Recall Router + Evidence-Linked Context Pack Builder. v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts. v0.32.0 implements M28 Approval Authority v2 + Action Policy Expansion. v0.33.0 implements M29 Agent Task Planning Engine. v0.34.0 implements M30 Multi-Step Execution Framework. v0.35.0 implements M31 Real Tool Runtime Adapter, Single Safe No-Op Tool. v0.36.0 implements M32 Safe Local Filesystem Metadata Tool. v0.37.0 implements M33 First Safe Local File Read Proposal, Redacted Preview Only. v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier only. v0.39.0 implements M35 Safe File Review Workflow Contracts as contract-only, review-only logic over already-redacted preview results. v0.39.1 hardens exact file/path binding for M35 approvals. Memory is recall, not authority. Memory is not ground truth. At that historical M39.1 point, OpenAPI path count remained `74`; current API boundary count is documented in `docs/api/openapi_contract.md` and generated from FastAPI.

## Active Remote Worker and Private Mesh Docs

```text
docs/remote/REMOTE_WORKER_FOUNDATION.md
docs/remote/REMOTE_NODE_SECURITY_MODEL.md
docs/remote/REMOTE_JOB_ENVELOPE.md
docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md
docs/remote/TAILNET_TRANSPORT_POLICY.md
docs/decisions/remote_worker_tailnet_foundation.md
docs/decisions/ADR-open-source-first-private-networking.md
```

Remote workers remain foundation-only. Private mesh, Headscale, generic WireGuard, Tailscale, tailnet, and LAN entries remain planned/disabled metadata only.

## Active Mobile and Device Capability Planning Docs

```text
docs/canonical/64_mobile_companion_and_device_capability_broker.md
docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md
docs/backlog/mobile_companion_backlog.md
docs/backlog/device_capability_broker_backlog.md
docs/schemas/mobile_device_manifest.schema.todo.md
docs/schemas/mobile_sensor_permission_manifest.schema.todo.md
docs/schemas/device_capability_manifest.schema.todo.md
```

Mobile Companion and Device Capability Broker docs are planning only. No mobile app, sensor API, OS permission integration, background service, or runtime Device Capability Broker exists.

## Active Security and Privacy Docs

```text
docs/security/approval_authority.md
docs/canonical/23_security_threat_model.md
docs/canonical/24_data_lifecycle_and_privacy.md
docs/canonical/30_agent_constitution.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/50_data_classification_policy.md
docs/canonical/51_redaction_and_safe_debugging.md
```

## Backlog and Future Work

```text
docs/backlog/parking_lot.md
docs/backlog/external_agent_tooling_watchlist.md
docs/backlog/mobile_companion_backlog.md
docs/backlog/device_capability_broker_backlog.md
docs/backlog/codex_plugin_enablement_backlog.md
docs/backlog/open_design_system_backlog.md
docs/backlog/codex_recommendation_log.md
docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md
docs/backlog/reconciliation/README.md
```

Backlog files are not implementation claims.

## Roadmap Guardrails

Future prompts must check `docs/roadmap/MILESTONE_CHARTERS.md` and `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` before selecting milestone scope. Parked work, including local branches or tags, must not be merged, reactivated, or treated as accepted baseline without an explicit reintroduction prompt.

Future prompts after M20 must also read `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`, and `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md` before implementation.

## Development Tooling Inventory

```text
docs/maintenance/codex_plugin_capability_inventory.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md
docs/schemas/plugin_skill_trust_manifest.schema.json
docs/schemas/inspectable_extension_catalog.schema.json
docs/schemas/extension_activation_grant.schema.json
docs/backlog/codex_plugin_enablement_backlog.md
```

## Recurring Automation Contracts

```text
docs/automation/RECURRING_AUTOMATION_CONTRACTS.md
docs/automation/RECURRING_AUTOMATION_RENEWAL_POLICY.md
docs/automation/RECURRING_AUTOMATION_STOP_CONDITIONS.md
docs/automation/RECURRING_AUTOMATION_AUTHORITY_BOUNDARY.md
docs/automation/RECURRING_AUTOMATION_RECEIPT_PLAN.md
docs/automation/RECURRING_AUTOMATION_NON_GOALS.md
docs/automation/M97_TO_M98_BOUNDARY.md
docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION.md
docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_POLICY.md
docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_AUTHORITY_BOUNDARY.md
docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_RECEIPT_PLAN.md
docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_NON_GOALS.md
docs/automation/M98_TO_M99_BOUNDARY.md
docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE.md
docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_POLICY.md
docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md
docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_RECEIPT_PLAN.md
docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_NON_GOALS.md
docs/autonomy/M99_TO_M100_BOUNDARY.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1_POLICY.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1_CONSENT_REVOCATION.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1_PRIVACY_COPY.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1_AUDIT.md
docs/mobile/MOBILE_PERMISSION_MODEL_V1_NON_GOALS.md
docs/mobile/M100_FINAL_BOUNDARY.md
```

The Codex plugin capability inventory and risk policy record available development-assist tool classes and the approval boundaries for future UI, Mobile Companion, Desktop Companion, CI, security, and documentation milestones. They are guidance-only and do not enable plugins, activate build tools, add runtime behavior, or authorize credential-bearing workflows.

## Local Developer Launcher

```text
docs/developer/LOCAL_LAUNCHER.md
scripts/dev/README.md
```

v0.37.4 supersedes the old active M35-M40 roadmap projection and defines the
active M34-M60 sequence. v0.104.0 is the current active package baseline for the
accepted Operator Runtime Excellence currentness and production-readiness
documentation repair lane through P2 read-only ecosystem inspection,
activation-record contracts, and MCP/A2A compatibility watchlist planning.
Checkpoint M108 is implemented/released as Mobile Kill Switch + Revocation
after the Checkpoint M107 Mobile Approval Renewal UX release and post-M103
versioning repair follow-up.
M100 remains implemented/released as Mobile Permission Model v1. M101 is
implemented/released as contract-only mobile sensor governance. M102 is
implemented/released as contract-only location sensor governance with location
off by default. M103 is implemented/released as contract-only camera/photos
metadata-only governance. M104 is implemented/released as contract-only
notification planning with no push execution. M105 is implemented/released as
contract-only background task planning with no execution. M106 is
implemented/released as contract-only read-only background status sync. M107 is
implemented/released as contract-only review-only mobile approval renewal UX.
M108 is implemented/released as contract-only review-only mobile kill switch +
revocation records. M109 is implemented/released as contract-only review-only
mobile sensor audit ledger records. M110 is implemented/released as
contract-only review-only freeze-only mobile sensor hardening freeze records.
M111 is implemented/released as contract-only review-only production threat
model records. M112 is implemented/released as contract-only review-only
user/workspace identity model records. M113 is implemented/released as
contract-only review-only secrets boundary and credential vault contract
records. M114 is implemented/released as contract-only review-only account
connector contract review records. M115 is implemented/released as
contract-only review-only production audit retention policy records. M116 is
implemented/released as contract-only review-only role-based authority model
records. M117 is implemented/released as contract-only review-only remote agent
coordination contract records. M118 is implemented/released as contract-only
review-only deployment mode matrix records. M119 is implemented/released as
contract-only review-only production red-team harness records. M120 is
implemented/released as contract-only review-only production authority
readiness review records. M121 is implemented/released as contract-only
review-only email connector contract refresh records. M122 is
implemented/released as contract-only review-only calendar connector contract
refresh records. M123 is implemented/released as contract-only review-only
contacts connector contract refresh records. M124 is implemented/released as
contract-only review-only messages connector contract review records. M125 is
implemented/released as deterministic local safe-ref-only connector read-only
runtime records. M126 is implemented/released as deterministic local
review-only exact-bound connector approval capture records. M127 is
implemented/released as deterministic local review-only dry-run-only connector
write dry-run planner records. M128 is implemented/released as deterministic
local low-risk-only connector write execution records through injected safe
transport. M129 is implemented/released as deterministic local review-only
connector audit + revocation hardening records. M130 is implemented/released as
deterministic local freeze-only connector safety freeze records. M131 is
implemented/released as deterministic local review-only Autonomy Mode 4 scoped
work-session records. M132 is implemented/released as deterministic local
review-only Autonomy Mode 5 trusted recurring workflow records. M133 is
implemented/released as deterministic local review-only Long-Running Task
Supervisor records. M134 is implemented/released as deterministic local
review-only Human Checkpoint Scheduling records. M135 is implemented/released
as deterministic local review-only Autonomous Recovery Planner records. M136 is
implemented/released as deterministic local review-only Cross-Tool Dependency
Execution records. M137 is implemented/released as deterministic local
review-only Autonomous Browser + Connector Combined Workflows records.
M138 is implemented/released as deterministic local review-only Autonomous
Error Handling Guardrails records. M139 is implemented/released as
deterministic local review-only Autonomy Abuse/Loop Detection records. M140 is
implemented/released as deterministic local review-only Higher-Autonomy
Red-Team Freeze records. M141 is implemented/released as deterministic local
review-only Multi-User Product Boundary records. M142 is implemented/released as
deterministic local review-only Alpha Privacy Review records. M143 is
implemented/released as deterministic local review-only Alpha UI and App
Readiness records. M144 is implemented/released as deterministic local
review-only Plugin Marketplace Policy Draft records. M145 is
implemented/released as deterministic local review-only Enterprise/Pro Safety
Modes records. M146 is implemented/released as deterministic local review-only
Billing/Plan Boundary records. M147 is implemented/released as deterministic
local review-only Public Docs + Wiki Readiness records. M148 is implemented/released as deterministic
local review-only External Security Review records. M149 is implemented/released as deterministic
local review-only Alpha Release Candidate Freeze records. M150 is
implemented/released as deterministic local review-only Ultimate AI Agent
v1.2.0-alpha target acceptance records in
`docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md`. M150 adds no release
publication, tag creation, artifact publishing, external distribution, beta
release, or production authority. Beta begins only after alpha UI and supporting
safety/product work are reviewed and promoted. Active roadmap sources consistently mark
M34-M150 implemented/released and rely on documentation-integrity checks to
guard against superseded-roadmap drift, stale current-baseline labels, route
drift, authority-boundary drift, alpha/beta versioning drift, and beta
future-status drift.

## Release Notes Index

Current release notes: `docs/release_notes/v0_104_0.md`

Historical release notes remain under `docs/release_notes/`. Historical docs may mention old active baselines in historical context; they are not the current source of truth.

Historical release import and master-plan packets live under `docs/archive/releases/`.
Retired planning packets live under `docs/archive/retired_plans/`. Archive docs are
audit records, not current implementation guidance.
Legacy files still present under `docs/master_plans/*` are historical planning
artifacts only; their top-of-file banners govern any old "working baseline" or
compatibility wording inside those files.

Future milestone and review prompts must follow
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`, including the rule that
legacy historical verifiers are not current release gates and must not live at
root or under active `scripts/`.

## How To Verify Docs

Run:

```bash
make doctor
make verify
```

The documentation integrity verifier checks active version alignment, active release docs, active index/map/checklist docs, design governance docs, OpenWebUI/CCC strategy docs, post-M20 roadmap projection docs, mobile/private mesh doc presence, and obvious unsafe implementation claims.
