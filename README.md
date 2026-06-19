# Ultimate AI Agent

A local-first, safety-first AI agent architecture for building governed AI
systems around a Python Agent Core, typed contracts, preview-oriented control
surfaces, and milestone-gated safety reviews.

Ultimate AI Agent is under active development. It is designed to make powerful
agent behavior inspectable, permissioned, reversible, and testable before it is
allowed to become operational authority.

## Status

| Field | Current state |
|---|---|
| Current active baseline | **v2.0.0** |
| Current program milestone | **Operator Runtime Excellence P2 ecosystem inspection lane through UAA-P2-051** |
| Latest accepted checkpoint tag | **checkpoint-m168** |
| Development posture | Active, milestone-driven, local-first |
| Runtime posture | Contract-first, validation-first, preview-oriented |
| API boundary | FastAPI route contract with **95** OpenAPI paths |
| Production readiness | Not claimed |

The product and package baseline is **v2.0.0** / `2.0.0`. This is a fresh
currentness and production-readiness documentation baseline over the accepted
Operator Runtime Excellence P0 repair lane, scoped P1 release-evidence packet
work, and P2 read-only ecosystem inspection/activation-record/watchlist work. It does not publish a public
release, move historical tags, ship external artifacts, distribute externally,
release a beta, or grant production authority. Already-pushed tags remain
immutable historical records.

The active workstream is the **Operator Runtime Excellence Program**. The latest
accepted repository checkpoint tag is `checkpoint-m168`, which repairs
currentness and product truth across README, roadmap, board, accepted checkpoint
references, and API route-count references. The latest accepted local model lane
checkpoint tags remain `checkpoint-m166` and `checkpoint-m167`: M166 is an
exact-scope local model production-readiness gate for the M160-M165
llama.cpp/OpenWebUI layer, and M167 adds stricter live-evidence hardening
without granting new production authority beyond the accepted M166 gate.

v0.29.5 is documentation policy polish. It remains the documentation
organization cleanup baseline before the M26 and M27 implementation releases.

## Quick Links

- [Docs home](docs/README.md)
- [Security policy](SECURITY.md)
- [Security triage runbook](docs/security/SECURITY_TRIAGE_RUNBOOK.md)
- [Documentation index](docs/DOCUMENTATION_INDEX.md)
- [Canonical document map](docs/canonical/CANONICAL_DOC_MAP.md)
- [Current roadmap](docs/canonical/09_roadmap.md)
- [Operator Runtime Excellence roadmap](docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
- [Product release-truth packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md)
- [Control Center operator-shell gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md)
- [Plugin/skill ecosystem boundary](docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md)
- [Inspectable extension catalog](docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md)
- [Extension activation grants](docs/tooling/EXTENSION_ACTIVATION_GRANTS.md)
- [MCP/A2A compatibility watchlist](docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md)
- [Current Kanban board](docs/kanban/current_board.md)
- [M34-M60 roadmap supersession](docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md)
- [M61-M100 roadmap](docs/roadmap/M61_M100_ROADMAP.md)
- [M101-M150 planned roadmap](docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md)
- [M150 Ultimate AI Agent v1.2.0-alpha](docs/productization/ULTIMATE_AI_AGENT_ALPHA.md)
- [M149 Alpha Release Candidate Freeze](docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE.md)
- [M148 External Security Review](docs/productization/EXTERNAL_SECURITY_REVIEW.md)
- [M147 Public Docs + Wiki Readiness](docs/productization/PUBLIC_DOCS_WIKI_READINESS.md)
- [M146 Billing/Plan Boundary](docs/productization/BILLING_PLAN_BOUNDARY.md)
- [M145 Enterprise/Pro Safety Modes](docs/productization/ENTERPRISE_PRO_SAFETY_MODES.md)
- [M144 Plugin Marketplace Policy Draft](docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT.md)
- [M143 Alpha UI and App Readiness](docs/productization/ALPHA_UI_APP_READINESS.md)
- [M142 Alpha Privacy Review](docs/productization/ALPHA_PRIVACY_REVIEW.md)
- [M141 Multi-User Product Boundary](docs/productization/MULTI_USER_PRODUCT_BOUNDARY.md)
- [M140 Higher-Autonomy Red-Team Freeze](docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE.md)
- [M139 Autonomy Abuse/Loop Detection](docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION.md)
- [M138 Autonomous Error Handling Guardrails](docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS.md)
- [M137 Autonomous Browser + Connector Combined Workflows](docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW.md)
- [M136 Cross-Tool Dependency Execution](docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION.md)
- [M135 Autonomous Recovery Planner](docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER.md)
- [M134 Human Checkpoint Scheduling](docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING.md)
- [M133 Long-Running Task Supervisor](docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR.md)
- [M132 Autonomy Mode 5, Trusted Recurring Workflow](docs/autonomy/TRUSTED_RECURRING_WORKFLOW.md)
- [M131 Autonomy Mode 4, Scoped Work Session](docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION.md)
- [M130 Connector Safety Freeze](docs/connectors/CONNECTOR_SAFETY_FREEZE.md)
- [M129 Connector Audit + Revocation Hardening](docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING.md)
- [M128 Connector Write Execution, Low-Risk Only](docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK.md)
- [M127 Connector Write Dry-Run Planner](docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER.md)
- [M126 Connector Approval Capture](docs/connectors/CONNECTOR_APPROVAL_CAPTURE.md)
- [M125 Connector Read-Only Runtime](docs/connectors/CONNECTOR_READ_ONLY_RUNTIME.md)
- [M124 Messages Connector Contract Review](docs/connectors/MESSAGES_CONNECTOR_CONTRACT_REVIEW.md)
- [M123 Contacts Connector Contract Refresh](docs/connectors/CONTACTS_CONNECTOR_CONTRACT_REFRESH.md)
- [M122 Calendar Connector Contract Refresh](docs/connectors/CALENDAR_CONNECTOR_CONTRACT_REFRESH.md)
- [M121 Email Connector Contract Refresh](docs/connectors/EMAIL_CONNECTOR_CONTRACT_REFRESH.md)
- [M120 Production Authority Readiness Review](docs/production/PRODUCTION_AUTHORITY_READINESS_REVIEW.md)
- [M119 Production Red-Team Harness](docs/production/PRODUCTION_RED_TEAM_HARNESS.md)
- [M118 Deployment Mode Matrix](docs/production/DEPLOYMENT_MODE_MATRIX.md)
- [M117 Remote Agent Coordination Contract](docs/production/REMOTE_AGENT_COORDINATION_CONTRACT.md)
- [M116 Role-Based Authority Model](docs/production/ROLE_BASED_AUTHORITY_MODEL.md)
- [M115 Production Audit Retention Policy](docs/production/PRODUCTION_AUDIT_RETENTION_POLICY.md)
- [M114 Account Connector Contract Review](docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md)
- [M63 Autonomy Policy Engine v1](docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md)
- [M63 Autonomy Policy Rule Contracts](docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md)
- [M64 Autonomous Plan Simulator](docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md)
- [M64 Autonomous Plan Simulator Contracts](docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md)
- [M65 Autonomy Audit + Replay Viewer](docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md)
- [M65 Autonomy Audit Replay Contracts](docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md)
- [M66 Scoped Approval Bundles](docs/autonomy/SCOPED_APPROVAL_BUNDLES.md)
- [M66 Scoped Approval Bundle Contracts](docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md)
- [M67 Revocation + Kill Switch](docs/autonomy/REVOCATION_KILL_SWITCH.md)
- [M67 Revocation + Kill Switch Contracts](docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md)
- [M68 Autonomy Risk Classifier](docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md)
- [M97 Recurring Automation Contracts](docs/automation/RECURRING_AUTOMATION_CONTRACTS.md)
- [M98 Scoped Recurring Low-Risk Automation](docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION.md)
- [M99 Autonomy v1 Safety Freeze](docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE.md)
- [M100 Mobile Permission Model v1](docs/mobile/MOBILE_PERMISSION_MODEL_V1.md)
- [M101 Mobile Sensor Contract Review](docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW.md)
- [M102 Location Sensor, Off by Default](docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT.md)
- [M113 Secrets Boundary + Credential Vault Contract](docs/production/SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT.md)
- [M112 User/Workspace Identity Model](docs/production/USER_WORKSPACE_IDENTITY_MODEL.md)
- [M111 Production Threat Model](docs/production/PRODUCTION_THREAT_MODEL.md)
- [M110 Mobile Sensor Hardening Freeze](docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE.md)
- [M109 Mobile Sensor Audit Ledger](docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER.md)
- [M108 Mobile Kill Switch + Revocation](docs/mobile/MOBILE_KILL_SWITCH_REVOCATION.md)
- [M107 Mobile Approval Renewal UX](docs/mobile/MOBILE_APPROVAL_RENEWAL_UX.md)
- [M106 Mobile Background Read-Only Status Sync](docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC.md)
- [M105 Background Task Contract, No Execution](docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION.md)
- [M104 Notification Planning, No Push Execution](docs/mobile/NOTIFICATION_PLANNING_NO_PUSH.md)
- [M103 Camera/Photos Metadata-Only Contract](docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_CONTRACT.md)
- [M68 Autonomy Risk Classifier Contracts](docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md)
- [M69 Low-Risk Autonomous Dry Run](docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md)
- [M69 Low-Risk Autonomous Dry Run Contracts](docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md)
- [M70 Autonomy Foundation Freeze](docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md)
- [M70 Autonomy Foundation Freeze Contracts](docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md)
- [M71 Network Tool Contract Review](docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md)
- [M71 Network Tool Contract Review Policy](docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md)
- [M71 Network Tool Authority Boundary](docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md)
- [M72 Read-Only HTTP Fetch Tool](docs/network/READ_ONLY_HTTP_FETCH_TOOL.md)
- [M72 Read-Only HTTP Fetch Policy](docs/network/READ_ONLY_HTTP_FETCH_POLICY.md)
- [M72 Read-Only HTTP Fetch Authority Boundary](docs/network/READ_ONLY_HTTP_FETCH_AUTHORITY_BOUNDARY.md)
- [M91 Autonomous Tool Execution Contract](docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT.md)
- [M91 Autonomous Tool Execution Authority Boundary](docs/tools/AUTONOMOUS_TOOL_EXECUTION_AUTHORITY_BOUNDARY.md)
- [M92 Low-Risk Tool Autonomy, Single Session](docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION.md)
- [M92 Low-Risk Tool Autonomy Authority Boundary](docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_AUTHORITY_BOUNDARY.md)
- [M93 Multi-Tool Dry-Run Promotion](docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION.md)
- [M93 Multi-Tool Dry-Run Promotion Authority Boundary](docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_AUTHORITY_BOUNDARY.md)
- [M94 Low-Risk Browser Clicks](docs/browser/LOW_RISK_BROWSER_CLICKS.md)
- [M94 Low-Risk Browser Click Authority Boundary](docs/browser/LOW_RISK_BROWSER_CLICK_AUTHORITY_BOUNDARY.md)
- [M95 Authless Network Tool Expansion](docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION.md)
- [M95 Authless Network Tool Expansion Policy](docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_POLICY.md)
- [M95 Authless Network Authority Boundary](docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md)
- [M96 Plugin Execution Sandbox](docs/tooling/PLUGIN_EXECUTION_SANDBOX.md)
- [M96 Plugin Execution Sandbox Policy](docs/tooling/PLUGIN_EXECUTION_SANDBOX_POLICY.md)
- [M96 Plugin Execution Sandbox Authority Boundary](docs/tooling/PLUGIN_EXECUTION_SANDBOX_AUTHORITY_BOUNDARY.md)
- [M73 Browser Automation Contract Review](docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW.md)
- [M73 Browser Automation Contract Review Policy](docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW_POLICY.md)
- [M73 Browser Automation Authority Boundary](docs/browser/BROWSER_AUTOMATION_AUTHORITY_BOUNDARY.md)
- [M74 Browser Observe-Only Adapter](docs/browser/BROWSER_OBSERVE_ONLY_ADAPTER.md)
- [M74 Browser Observe-Only Policy](docs/browser/BROWSER_OBSERVE_ONLY_POLICY.md)
- [M74 Browser Observe-Only Authority Boundary](docs/browser/BROWSER_OBSERVE_ONLY_AUTHORITY_BOUNDARY.md)
- [M75 Browser Action Dry-Run Planner](docs/browser/BROWSER_ACTION_DRY_RUN_PLANNER.md)
- [M75 Browser Action Dry-Run Policy](docs/browser/BROWSER_ACTION_DRY_RUN_POLICY.md)
- [M75 Browser Action Dry-Run Authority Boundary](docs/browser/BROWSER_ACTION_DRY_RUN_AUTHORITY_BOUNDARY.md)
- [M76 OpenWebUI Runtime Bridge v1](docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_V1.md)
- [M76 OpenWebUI Runtime Bridge Policy](docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_POLICY.md)
- [M76 OpenWebUI Runtime Bridge Authority Boundary](docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_AUTHORITY_BOUNDARY.md)
- [M77 OpenWebUI Safe Handoff Execution](docs/openwebui/OPENWEBUI_SAFE_HANDOFF_EXECUTION.md)
- [M77 OpenWebUI Safe Handoff Policy](docs/openwebui/OPENWEBUI_SAFE_HANDOFF_POLICY.md)
- [M77 OpenWebUI Safe Handoff Authority Boundary](docs/openwebui/OPENWEBUI_SAFE_HANDOFF_AUTHORITY_BOUNDARY.md)
- [M151 Local OpenWebUI Test Shell](docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md)
- [M151 Local OpenWebUI Test Shell Authority Boundary](docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_AUTHORITY_BOUNDARY.md)
- [M151 Local OpenWebUI Test Shell Runbook](docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_RUNBOOK.md)
- [M153-M165 Local Model Management Progression](docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md)
- [M160-M165 Live Lane Boundary](docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md)
- [M166 Production Authority Gate](docs/production/M166_PRODUCTION_AUTHORITY_GATE.md)
- [M167 Live Model Production Hardening](docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md)
- [M167 Live Model Evidence Matrix](docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md)
- [M167 Local Model E2E Smoke Harness](docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md)
- [llama-server Packaging Provenance Checklist](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md)
- [Local Model Operational Runbook](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md)
- [Release Latency Baseline Harness](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md)
- [Release Verification Lanes](docs/production/RELEASE_VERIFICATION_LANES.md)
- [Release Evidence Packet](docs/production/RELEASE_EVIDENCE_PACKET.md)
- [Backup/Restore Verification](docs/production/BACKUP_RESTORE_VERIFICATION.md)
- [Local State Rollback Runbook](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md)
- [Local Runtime Packaging](docs/production/LOCAL_RUNTIME_PACKAGING.md)
- [Control Center Operator Shell Gap Map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md)
- [M78 Plugin Manifest Security Model](docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md)
- [M78 Plugin Manifest Policy](docs/tooling/PLUGIN_MANIFEST_POLICY.md)
- [M78 Plugin Manifest Authority Boundary](docs/tooling/PLUGIN_MANIFEST_AUTHORITY_BOUNDARY.md)
- [M79 Plugin Install Review](docs/tooling/PLUGIN_INSTALL_REVIEW.md)
- [M79 Plugin Install Review Policy](docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md)
- [M79 Plugin Install Review Authority Boundary](docs/tooling/PLUGIN_INSTALL_REVIEW_AUTHORITY_BOUNDARY.md)
- [M80 Network/Browser/OpenWebUI Hardening Freeze](docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE.md)
- [M80 Hardening Freeze Contracts](docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_CONTRACTS.md)
- [M80 Hardening Freeze Non-Goals](docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_NON_GOALS.md)
- [M81 Runtime Sandbox Spec](docs/sandbox/RUNTIME_SANDBOX_SPEC.md)
- [M81 Runtime Sandbox Spec Contracts](docs/sandbox/RUNTIME_SANDBOX_SPEC_CONTRACTS.md)
- [M81 Runtime Sandbox Spec Authority Boundary](docs/sandbox/RUNTIME_SANDBOX_SPEC_AUTHORITY_BOUNDARY.md)
- [M81 Runtime Sandbox Spec Non-Goals](docs/sandbox/RUNTIME_SANDBOX_SPEC_NON_GOALS.md)
- [M82 Command Proposal Contracts](docs/sandbox/COMMAND_PROPOSAL_CONTRACTS.md)
- [M83 Shell Dry-Run Classifier](docs/sandbox/SHELL_DRY_RUN_CLASSIFIER.md)
- [M84 Sandboxed Echo/No-Op Command](docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND.md)
- [M85 Read-Only Command Allowlist](docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST.md)
- [M86 Shell Approval Gate v1](docs/sandbox/SHELL_APPROVAL_GATE.md)
- [M34 Broader File Capability Review](docs/files/BROADER_FILE_CAPABILITY_REVIEW.md)
- [File capability boundary matrix](docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md)
- [File capability risk register](docs/files/FILE_CAPABILITY_RISK_REGISTER.md)
- [M35 file review workflow readiness](docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md)
- [M35 Safe File Review Workflow](docs/files/SAFE_FILE_REVIEW_WORKFLOW.md)
- [M35 File Review Packet Contract](docs/files/FILE_REVIEW_PACKET_CONTRACT.md)
- [M35 File Review User Approval Gate](docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md)
- [M35 File Review Authority Boundary](docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md)
- [M36 CCC File Review Surface](docs/control_center/FILE_REVIEW_SURFACE.md)
- [M36 File Review Review-Only Policy](docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md)
- [M36 File Review Mock Data Policy](docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md)
- [M36 File Review Binding Display Policy](docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md)
- [M37 File Review Approval Capture](docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md)
- [M37 File Review Approval Persistence](docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md)
- [M37 File Review Approval Authority Boundary](docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md)
- [M37 File Review Approval API](docs/files/FILE_REVIEW_APPROVAL_API.md)
- [M38 Safe Context Proposal](docs/context/SAFE_CONTEXT_PROPOSAL_FROM_APPROVED_REVIEW.md)
- [M38 Context Proposal Contract](docs/context/CONTEXT_PROPOSAL_CONTRACT.md)
- [M38 Context Proposal Authority Boundary](docs/context/CONTEXT_PROPOSAL_AUTHORITY_BOUNDARY.md)
- [M39 CCC Context Proposal Surface](docs/control_center/CONTEXT_PROPOSAL_SURFACE.md)
- [M39 Context Proposal Review-Only Policy](docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md)
- [M39 Context Proposal Binding Display Policy](docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md)
- [M40 Context Handoff Approval](docs/context/CONTEXT_HANDOFF_APPROVAL.md)
- [M40 Context Handoff Approval Boundary](docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md)
- [M40 Context Handoff No-Injection Policy](docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md)
- [M40 Context Handoff Receipt Plan](docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md)
- [M41 Local Prototype Safety Freeze](docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md)
- [M41 Local Prototype Browser Smoke Review](docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md)
- [M41 Local Prototype No-Authority Boundary](docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md)
- [M41 to M42 Boundary](docs/prototype/M41_TO_M42_BOUNDARY.md)
- [M42 Mobile Companion Product Contract Refresh](docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md)
- [M42 to M43 Boundary](docs/mobile/M42_TO_M43_BOUNDARY.md)
- [M43 Mobile API Boundary, Read-Only](docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md)
- [M43 to M44 Boundary](docs/mobile/M43_TO_M44_BOUNDARY.md)
- [M44 CCC iOS Skeleton, No Authority](docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md)
- [M44 to M45 Boundary](docs/mobile/M44_TO_M45_BOUNDARY.md)
- [M45 CCC iOS Local Read-Only Connection](docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md)
- [M45 to M46 Boundary](docs/mobile/M45_TO_M46_BOUNDARY.md)
- [M46 iOS Review/Receipt Read-Only Surfaces](docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md)
- [M46 to M47 Boundary](docs/mobile/M46_TO_M47_BOUNDARY.md)
- [M47 TestFlight Pipeline, Internal Only](docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md)
- [M47 to M48 Boundary](docs/mobile/M47_TO_M48_BOUNDARY.md)
- [M48 First Internal TestFlight Build](docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md)
- [M48 to M49 Boundary](docs/mobile/M48_TO_M49_BOUNDARY.md)
- [M49 Mobile Review Approval Capture](docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md)
- [M49 to M50 Boundary](docs/mobile/M49_TO_M50_BOUNDARY.md)
- [M50 Mobile Approval Audit Hardening](docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md)
- [M50 to M51 Boundary](docs/mobile/M50_TO_M51_BOUNDARY.md)
- [M51 OpenWebUI Bridge Adapter Pilot](docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md)
- [M51 OpenWebUI Bridge Adapter Policy](docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md)
- [M51 OpenWebUI Bridge Adapter Authority Boundary](docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md)
- [M51 to M52 Boundary](docs/openwebui/M51_TO_M52_BOUNDARY.md)
- [M52 OpenWebUI Safe Conversation Surface](docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md)
- [M52 OpenWebUI Safe Conversation Policy](docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md)
- [M52 OpenWebUI Safe Conversation Authority Boundary](docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md)
- [M52 to M53 Boundary](docs/openwebui/M52_TO_M53_BOUNDARY.md)
- [M53 Controlled Tool Expansion Review](docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md)
- [M53 Controlled Tool Expansion Policy](docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md)
- [M53 Controlled Tool Expansion Authority Boundary](docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md)
- [M53 to M54 Boundary](docs/tools/M53_TO_M54_BOUNDARY.md)
- [M54 Safe Media Metadata Inspector](docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md)
- [M54 Safe Media Metadata Policy](docs/media/SAFE_MEDIA_METADATA_POLICY.md)
- [M54 Safe Media Metadata Authority Boundary](docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md)
- [M54 to M55 Boundary](docs/media/M54_TO_M55_BOUNDARY.md)
- [M55 Redacted Observability Export](docs/observability/REDACTED_OBSERVABILITY_EXPORT.md)
- [M55 Redacted Observability Export Policy](docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md)
- [M55 Redacted Observability Export Authority Boundary](docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md)
- [M55 to M56 Boundary](docs/observability/M55_TO_M56_BOUNDARY.md)
- [M56 Agent Eval Regression Harness](docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md)
- [M56 Agent Eval Regression Policy](docs/evals/AGENT_EVAL_REGRESSION_POLICY.md)
- [M56 Agent Eval Regression Authority Boundary](docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md)
- [M56 to M57 Boundary](docs/evals/M56_TO_M57_BOUNDARY.md)
- [M57 Runtime Sandbox Architecture Review](docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md)
- [M57 Runtime Sandbox Boundary Policy](docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md)
- [M57 Runtime Sandbox Authority Boundary](docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md)
- [M57 to M58 Boundary](docs/sandbox/M57_TO_M58_BOUNDARY.md)
- [M58 Dry-Run Execution Audit Harness](docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md)
- [M58 Dry-Run Execution Audit Policy](docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md)
- [M58 Dry-Run Execution Authority Boundary](docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md)
- [M58 to M59 Boundary](docs/dry_run_audit/M58_TO_M59_BOUNDARY.md)
- [M59 Public GitHub Readiness](docs/public_readiness/PUBLIC_GITHUB_READINESS.md)
- [M59 Public GitHub Readiness Policy](docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md)
- [M59 Public GitHub Readiness Authority Boundary](docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md)
- [M59 to M60 Boundary](docs/public_readiness/M59_TO_M60_BOUNDARY.md)
- [M60 Local Developer Beta Freeze](docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md)
- [M60 Local Developer Beta Freeze Policy](docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md)
- [M60 Local Developer Beta Freeze Authority Boundary](docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md)
- [Post-M60 Autonomy Boundary](docs/beta/POST_M60_AUTONOMY_BOUNDARY.md)
- [M61 Autonomy Mode Charter](docs/autonomy/AUTONOMY_MODE_CHARTER.md)
- [M61 Authority Levels](docs/autonomy/AUTHORITY_LEVELS.md)
- [M61 Capability Toggle Registry](docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md)
- [M61 Autonomy Consent And Revocation Policy](docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md)
- [M61 to M62 Boundary](docs/autonomy/M61_TO_M62_BOUNDARY.md)
- [M62 Scoped Autonomy Session Contracts](docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md)
- [M62 Scoped Autonomy Session Scope Policy](docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md)
- [M62 Scoped Autonomy Session Non-Goals](docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md)
- [M62 to M63 Boundary](docs/autonomy/M62_TO_M63_BOUNDARY.md)
- [M63 Autonomy Policy Engine v1](docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md)
- [M63 Autonomy Policy Rule Contracts](docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md)
- [M63 Autonomy Policy Engine Non-Goals](docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md)
- [M63 to M64 Boundary](docs/autonomy/M63_TO_M64_BOUNDARY.md)
- [M64 Autonomous Plan Simulator](docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md)
- [M64 Autonomous Plan Simulator Contracts](docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md)
- [M64 Autonomous Plan Simulator Non-Goals](docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md)
- [M64 to M65 Boundary](docs/autonomy/M64_TO_M65_BOUNDARY.md)
- [M65 Autonomy Audit + Replay Viewer](docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md)
- [M65 Autonomy Audit Replay Contracts](docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md)
- [M65 Autonomy Audit Replay Non-Goals](docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md)
- [M65 to M66 Boundary](docs/autonomy/M65_TO_M66_BOUNDARY.md)
- [M38 Context Proposal Receipt Plan](docs/context/CONTEXT_PROPOSAL_RECEIPT_PLAN.md)
- [API route inventory](docs/api/route_inventory.md)
- [Documentation organization policy](docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md)
- [Control Center frontend safety policy](docs/control_center/FRONTEND_SAFETY_POLICY.md)
- [Local developer launcher](docs/developer/LOCAL_LAUNCHER.md)
- [M31 Tool Runtime Adapter](docs/tools/TOOL_RUNTIME_ADAPTER.md)
- [M31 No-Op Tool Runtime](docs/tools/NOOP_TOOL_RUNTIME.md)
- [M32 Filesystem Metadata Tool](docs/tools/FILESYSTEM_METADATA_TOOL.md)
- [M32 Filesystem Metadata Path Policy](docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md)
- [M33 Redacted File Preview Tool](docs/tools/REDACTED_FILE_PREVIEW_TOOL.md)
- [M33 Redacted File Preview Policy](docs/tools/REDACTED_FILE_PREVIEW_POLICY.md)
- [M30 Multi-Step Execution Framework](docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md)
- [M29 Agent Task Planning Engine](docs/planning/TASK_PLANNING_ENGINE.md)
- [M28 Approval Authority v2](docs/approvals/APPROVAL_AUTHORITY_V2.md)
- [M28 Action Policy](docs/approvals/ACTION_POLICY.md)
- [M27 Tool Broker v2](docs/tools/TOOL_BROKER_V2.md)
- [M26 Grounded Recall Router](docs/recall/GROUNDED_RECALL_ROUTER.md)
- [v0.60.0 release notes](docs/release_notes/v0_60_0.md)
- [v0.82.0 release packet](docs/archive/releases/v0_82_0/README_IMPORT.md)
- [v0.82.0 master plan](docs/archive/releases/v0_82_0/master_plan.md)
- [v0.83.0 release packet](docs/archive/releases/v0_83_0/README_IMPORT.md)
- [v0.83.0 master plan](docs/archive/releases/v0_83_0/master_plan.md)
- [v0.85.0 release packet](docs/archive/releases/v0_85_0/README_IMPORT.md)
- [v0.85.0 master plan](docs/archive/releases/v0_85_0/master_plan.md)
- [v0.86.0 release packet](docs/archive/releases/v0_86_0/README_IMPORT.md)
- [v0.86.0 master plan](docs/archive/releases/v0_86_0/master_plan.md)
- [v0.90.0 release packet](docs/archive/releases/v0_90_0/README_IMPORT.md)
- [v0.90.0 master plan](docs/archive/releases/v0_90_0/master_plan.md)
- [v0.91.0 release packet](docs/archive/releases/v0_91_0/README_IMPORT.md)
- [v0.91.0 master plan](docs/archive/releases/v0_91_0/master_plan.md)
- [v0.93.0 release packet](docs/archive/releases/v0_93_0/README_IMPORT.md)
- [v0.93.0 master plan](docs/archive/releases/v0_93_0/master_plan.md)
- [v0.94.0 release packet](docs/archive/releases/v0_94_0/README_IMPORT.md)
- [v0.94.0 master plan](docs/archive/releases/v0_94_0/master_plan.md)
- [v0.95.0 release packet](docs/archive/releases/v0_95_0/README_IMPORT.md)
- [v0.95.0 master plan](docs/archive/releases/v0_95_0/master_plan.md)
- [v0.96.0 release packet](docs/archive/releases/v0_96_0/README_IMPORT.md)
- [v0.96.0 master plan](docs/archive/releases/v0_96_0/master_plan.md)
- [v0.99.0 release packet](docs/archive/releases/v0_99_0/README_IMPORT.md)
- [v0.99.0 master plan](docs/archive/releases/v0_99_0/master_plan.md)
- [v1.0.0 release packet](docs/archive/releases/v1_0_0/README_IMPORT.md)
- [v1.0.0 master plan](docs/archive/releases/v1_0_0/master_plan.md)
- [v1.1.0 release packet](docs/archive/releases/v1_1_0/README_IMPORT.md)
- [v1.1.0 master plan](docs/archive/releases/v1_1_0/master_plan.md)
- [v1.2.0-alpha release packet](docs/archive/releases/v1_2_0_alpha/README_IMPORT.md)
- [v1.2.0-alpha master plan](docs/archive/releases/v1_2_0_alpha/master_plan.md)
- [v1.3.0 release packet](docs/archive/releases/v1_3_0/README_IMPORT.md)
- [v1.3.0 master plan](docs/archive/releases/v1_3_0/master_plan.md)
- [v1.4.0 release packet](docs/archive/releases/v1_4_0/README_IMPORT.md)
- [v1.4.0 master plan](docs/archive/releases/v1_4_0/master_plan.md)
- [v1.5.0 release packet](docs/archive/releases/v1_5_0/README_IMPORT.md)
- [v1.5.0 master plan](docs/archive/releases/v1_5_0/master_plan.md)
- [v1.6.0 release packet](docs/archive/releases/v1_6_0/README_IMPORT.md)
- [v1.6.0 master plan](docs/archive/releases/v1_6_0/master_plan.md)
- [v1.7.0 release packet](docs/archive/releases/v1_7_0/README_IMPORT.md)
- [v1.7.0 master plan](docs/archive/releases/v1_7_0/master_plan.md)
- [v1.7.1 release packet](docs/archive/releases/v1_7_1/README_IMPORT.md)
- [v1.7.1 master plan](docs/archive/releases/v1_7_1/master_plan.md)
- [v1.7.2 release packet](docs/archive/releases/v1_7_2/README_IMPORT.md)
- [v1.7.2 master plan](docs/archive/releases/v1_7_2/master_plan.md)
- [v2.0.0 release packet](docs/archive/releases/v2_0_0/README_IMPORT.md)
- [v2.0.0 master plan](docs/archive/releases/v2_0_0/master_plan.md)

## What This Project Is

Ultimate AI Agent is a foundation workspace for a governed AI agent system. The
repo favors typed contracts, local validation, deterministic tests, static
verifiers, and release gates over early runtime power.

Core themes:

- **Python Agent Core is the brain.** Policy, contracts, validation, approvals,
  redaction, memory governance, truth decisions, recall planning, and tool
  intent decisions belong in the core.
- **Control Center / CCC is the governance client family.** CCC Web exists as a
  local React/Vite control surface for safe summaries, status, and previews.
  Future CCC iOS, Android, and macOS clients are planned, not implemented.
- **OpenWebUI is the preferred conversational shell direction.** M151 adds a
  local-dev-only, disabled-by-default, localhost-only OpenWebUI test shell path
  for `uaa-safe-local`; OpenWebUI is still a shell, not the agent brain.
- **Memory is recall, not authority.** Memory can help plan recall context, but
  governed source refs outrank memory for truth.
- **Tool intents are contracts, not execution.** M27 validates tool intent
  metadata and can allow metadata-only preview decisions with
  `execution_performed=False`.
- **Approval decisions are policy decisions, not action execution.** M28
  validates action intent, grant, risk, and scope boundaries with
  `execution_authorized=False` and `execution_performed=False`.
- **Tool runtime is allowlist-only.** M33 permits exactly three governed runtime
  tools: deterministic no-op, safe local filesystem metadata, and bounded
  redacted file preview. The preview tool returns redacted preview output only;
  it cannot return raw content, full files, hashes, listings, or mutate files.

## What This Project Is Not

This repo is deliberately not an unrestricted autonomous executor.

It does not currently provide:

- production agent authority
- general cloud/provider model execution
- backend tool execution routes
- shell, subprocess, browser, mobile, remote, or plugin execution
- context injection into a model, runtime, OpenWebUI, tool, or agent loop
- vector search, embeddings, semantic search, or RAG ingestion
- web search or external retrieval
- unrestricted memory writes or raw prompt/file/transcript display
- implemented native iOS, Android, or macOS apps

Future milestones may expand capability, but only through reviewed, documented,
release-gated patches.

## Architecture Overview

```text
Ultimate AI Agent
  Python Agent Core
    Runtime contracts and bounded local smoke paths
    Memory: recall, not authority
    Truth/Evidence: validation over provided refs
    Recall/Context Packs: safe plans, not injection
    Tool Intent Contracts: preview/validation, not execution
    Tool Runtime Adapter: no-op, metadata-only filesystem lookup, redacted file preview
  Control Center / CCC Web
    Local governance and preview surfaces
  OpenWebUI Strategy
    Local safe smoke shell in M151; no OpenWebUI authority
  Foundation Gate + Verifiers
    Tests, docs integrity, OpenAPI checks, frontend checks, safety scans
```

The project advances by small milestones. Each milestone states what it enables,
what it blocks, which docs are active, and which tests/verifiers protect the
boundary.

## Capability Registry

`ultimate_ai_agent.core.capabilities` is the central source of truth for
agent-facing capabilities. A capability is a typed, provider-neutral record that
describes a named operation, its input and output schemas, source, tags,
metadata, risk policy, optional model instructions, examples, and an optional
internal callable binding. Model-facing adapters export only safe schema fields;
callable refs and registry metadata are never included in OpenAI or MCP tool
definitions.

For local smoke testing, use
`scripts/dev/capability_registry_smoke.py`. It resolves a deterministic
in-process capability and exports OpenAI/MCP schemas without adding backend
routes, provider calls, shell/network authority, plugin loading, or production
authority.

Register native Python capabilities explicitly:

```python
from pydantic import BaseModel

from ultimate_ai_agent.core.capabilities import (
    CapabilityPolicy,
    CapabilityRegistry,
    RiskLevel,
    tool_capability,
)

class ReadTextInput(BaseModel):
    path: str

class ReadTextOutput(BaseModel):
    text: str

registry = CapabilityRegistry()

@tool_capability(
    name="files.read_text",
    title="Read text file",
    description="Read a safe text reference from an allowed workspace.",
    input_model=ReadTextInput,
    output_model=ReadTextOutput,
    tags={"files", "read"},
    policy=CapabilityPolicy(risk=RiskLevel.READ_ONLY, required_scopes={"files:read"}),
    registry=registry,
)
async def read_text(ctx, args: ReadTextInput) -> ReadTextOutput:
    return ReadTextOutput(text="safe summary")
```

Group related capabilities with dotted namespaces such as `files.read_text` or
`github.search_issues`, then resolve a per-run tool set by agent, user scopes,
tags, and query:

```python
resolved = registry.resolve(
    agent_name="orchestrator",
    user_scopes={"files:read"},
    query="read file",
    tags={"files"},
)
```

Policy is enforced before execution: allowed agents, required scopes, approval
requirements, timeouts, retry limits, idempotency, output redaction, and sandbox
requirements are checked by the registry executor. Approval is pluggable via
`CapabilityRegistry(approval_callback=...)`. The executor treats model
arguments as untrusted, validates input and output schemas, emits redacted
observability events, and returns structured `CapabilityResult` errors that a
model can correct.

Adapters are thin and provider-neutral:

```python
from ultimate_ai_agent.core.capabilities.adapters import (
    capability_to_mcp_tool,
    capability_to_openai_tool,
    capability_to_tool_manifest,
)

openai_tool = capability_to_openai_tool(resolved[0])
mcp_tool = capability_to_mcp_tool(resolved[0])
tool_manifest = capability_to_tool_manifest(resolved[0])
```

External packages can contribute capabilities through entry points named
`ultimate_ai_agent.capabilities`. Entry points may return a `CapabilityPack`, a
list of `CapabilitySpec` or `CapabilityRegistration` objects, or a function that
receives a registry and registers capabilities. Runtime imports are disabled by
default under the current contract-first boundary; enable them only in controlled
local development or tests after review:

```python
registry.discover_entry_points(allow_runtime_imports=True)
```

This package does not add backend routes, provider SDK calls, browser
automation, shell execution, plugin enablement, or production authority. It is
an internal schema, policy, disabled-by-default discovery, adapter, and opt-in
callable layer for code that has already registered a safe in-process
capability.

## Capability Map

| Layer | Current status | Notes |
|---|---|---|
| Python Agent Core | Implemented foundation | Contract-first core under `src/ultimate_ai_agent/` |
| FastAPI backend | Implemented validation/metadata API | Includes disabled-by-default M151 local OpenWebUI test gateway |
| CCC Web Control Center | Implemented preview/read-only local shell | React/Vite app under `apps/control-center/` |
| OpenWebUI bridge | Local test shell plus contracts | M151 exposes `uaa-safe-local` for local smoke only; no provider/tool/memory/context authority |
| Local model runtime | Scoped local model lane | M160-M165 cover bounded HF metadata search, redacted system probing, exact-approved GGUF acquisition, loopback llama.cpp supervision, local `/v1` gateway, and approved tuning; M166/M167 require reviewed safe-ref evidence, P0-005 adds a local/dev E2E smoke harness with skipped or blocked states when prerequisites are unavailable, P0-015 adds the local `llama-server` packaging/provenance checklist without public distribution or broad binary-trust claims, P0-016 hardens tuning advice for lag, out-of-memory, crash loop, reload loop, slow token rate, and one-change rollback cases, and P0-017 adds safe local model operational recovery guidance |
| Performance baseline | Release latency harness and verification lanes | P0-006 measures p50/p95 for release-critical local paths; P1-013 names docs, OpenAPI, API safety, security/redaction, local model E2E, durability, frontend, and performance release lanes; P1-039 gates required local path budgets; P1-040 writes safe regression reports; P1-041 profiles task decomposition and OpenAPI build hot paths; P1-042 caches only safe static API manifest data; authority checks are not cached, skipped, or bypassed for speed |
| Memory | Implemented governed local foundation | Reviewed/source-linked recall records; no automatic writes |
| Truth/evidence | Implemented M25 contracts | Deterministic validation over provided refs; no external lookup |
| Recall/context packs | Implemented M26 contracts | Safe summaries and refs only; source_ref/source_kind consistency enforced |
| Tool Broker v2 | Implemented M27 contracts | Safe intent validation and metadata preview only; no execution |
| Approval Authority v2 | Implemented M28 contracts | Action policy decisions only; no execution authority |
| Tool Runtime Adapter | Implemented M33 allowlist-only | `tool:no_op.v1`, `tool:filesystem_metadata.v1`, and `tool:filesystem.redacted_preview.v1`; arbitrary/effectful tools blocked |
| Mobile/device clients | Planned/contract-only | Future CCC clients and device capability contracts; no native apps or sensors |
| Foundation Gate | Implemented | Release safety gate covering docs, OpenAPI, frontend, and capability boundaries |

## Safety Model

The safety posture is not a side note; it is the product architecture.

- Model output is not truth authority.
- Runtime output is not truth authority.
- Memory is recall, not authority.
- Context packs are planning artifacts, not prompt injection.
- Tool intents are not tool execution.
- M33 tool runtime is limited to deterministic no-op, safe local filesystem
  metadata, and bounded redacted file preview under server-owned safe roots.
- Redacted file previews are not raw file reads, full-file reads, or context
  injection.
- Approval decisions are not action execution.
- Approval refs are identifiers, not authority.
- `approval_test_*` refs are test-only and not runtime authority.
- Local/dev mode is not a security bypass.
- Raw prompts, raw files, raw transcripts, raw model outputs, and secret-like
  values are blocked or redacted unless a reviewed contract explicitly allows a
  safe summary/ref form.
- Foundation Gate, documentation integrity checks, OpenAPI checks, frontend
  checks, and static safety verifiers are part of the architecture.

## Getting Started Locally

Create a local Python environment and install the project with development
extras:

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -e ".[dev]"
```

Run the standard backend and repository checks:

```bash
make doctor
make test
make verify
```

The equivalent explicit commands are:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
.venv/bin/python scripts/verify_current_baseline.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_skill_package_security_rule.py
.venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_release_lanes.py
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
.venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python -m ruff check .
```

For the Control Center frontend:

```bash
cd apps/control-center
npm install
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Or from the repo root:

```bash
make frontend-check
```

## Local Developer Launcher

For day-to-day prototype testing, use the repo-local launcher:

```bash
./scripts/dev/uaa doctor
./scripts/dev/uaa start
./scripts/dev/uaa ui
./scripts/dev/uaa status
./scripts/dev/uaa logs
./scripts/dev/uaa stop
```

It starts only the local FastAPI backend on `127.0.0.1:8000` and the Control
Center Vite dev server on `127.0.0.1:5173`. PID and log files stay under
ignored `.uaa/dev/` launcher state.

Optional shell convenience:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/scripts/dev/uaa" ~/.local/bin/uaa
```

Then run `uaa doctor`, `uaa start`, and `uaa ui`.

For a clickable macOS launcher:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target repo
```

Read the full launcher guide at
[docs/developer/LOCAL_LAUNCHER.md](docs/developer/LOCAL_LAUNCHER.md).

For loopback-first Docker/local runtime packaging, use the scoped package in
[docs/production/LOCAL_RUNTIME_PACKAGING.md](docs/production/LOCAL_RUNTIME_PACKAGING.md).
It is for local release-readiness testing only and does not claim public
distribution, hosted production support, or signed installer readiness.

## Control Center

CCC Web is the current TypeScript Control Center surface. It is local,
read-only/preview-oriented, and visibly non-authoritative where mock fallback
data is used.

It may show status, route inventory, runtime readiness, approval summaries,
receipts, events, evidence refs, file refs, memory refs, local runtime status,
and safe action previews. It must not grant approvals, run tools, execute
runtimes, enable plugins, call providers, access browser profiles, use mobile
sensors, or become production authority.

Read more:

- [Control Center contract](docs/control_center/CONTROL_CENTER_CONTRACT.md)
- [Frontend safety policy](docs/control_center/FRONTEND_SAFETY_POLICY.md)
- [Control Center frontend routes](docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md)
- [Operator shell gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md)

## Roadmap Snapshot

The canonical roadmap source of truth is
[docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md). The active
post-M33 supersession is
[docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md](docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md).

| Version | Milestone | Status |
|---|---|---|
| v0.30.1 | M26 hardening - Recall Source Ref / Source Kind Consistency | Implemented/released |
| v0.31.0 | M27 - Tool Broker v2 + Safe Tool Intent Contracts | Implemented/released |
| v0.31.1 | GitHub README Polish Baseline Normalization | Implemented/released docs-only |
| v0.32.0 | M28 - Approval Authority v2 + Action Policy Expansion | Implemented/released |
| v0.32.1 | M28 hardening - Evaluator Revalidation for Raw/Secret Action Inputs | Implemented/released |
| v0.33.0 | M29 - Agent Task Planning Engine | Implemented/released |
| v0.33.1 | M29 hardening - Task Plan Dependency, Risk, and No-Execution Safety | Implemented/released |
| v0.34.0 | M30 - Multi-Step Execution Framework | Implemented/released |
| v0.34.1 | M30 hardening - Execution State Machine, Replay, and No-Side-Effect Safety | Implemented/released |
| v0.35.0 | M31 - Real Tool Runtime Adapter, Single Safe No-Op Tool | Implemented/released |
| v0.35.1 | M31 hardening - No-Op Tool Runtime Adapter Safety | Implemented/released |
| v0.36.0 | M32 - Safe Local Filesystem Metadata Tool | Implemented/released |
| v0.36.1 | M32 hardening - Filesystem Metadata Path Safety | Implemented/released |
| v0.37.0 | M33 - First Safe Local File Read Proposal, Redacted Preview Only | Implemented/released |
| v0.37.1 | M33 hardening - Redacted File Preview Safety | Implemented/released |
| v0.37.2 | Local Developer Launcher + Desktop Shortcut | Implemented/released tooling-only |
| v0.37.3 | Roadmap Label Alignment + Documentation Integrity Guard | Implemented/released docs/verifier-only |
| v0.37.4 | Roadmap Supersession Through M60 + Documentation Integrity Guard | Implemented/released docs/verifier-only |
| v0.38.0 | M34 - Broader File Capability Review | Implemented/released planning/docs/verifier-only |
| v0.38.1 | M34 hardening - File Capability Review Boundary Clarity | Pushed, reviewed Yellow; superseded by v0.38.2 |
| v0.38.2 | M34 hardening - Current Baseline Label + Documentation Integrity Repair | Implemented/released docs/verifier-only |
| v0.39.0 | M35 - Safe File Review Workflow Contracts | Implemented/released contract-only |
| v0.39.1 | M35 hardening - File Review Exact File/Path Binding | Implemented/released hardening |
| v0.40.0 | M36 - CCC File Review Surface, Review-Only | Implemented/released frontend-only |
| v0.40.1 | M36 hardening - CCC File Review Surface Read-Only Safety | Implemented/released hardening |
| v0.41.0 | M37 - Review Approval Capture, Review-Only Persistence | Implemented/released |
| v0.42.0 | M38 - Safe Context Proposal From Approved Review | Implemented/released |
| v0.43.0 | M39 - CCC Context Proposal Surface | Implemented/released frontend-only |
| v0.44.0 | M40 - Context Handoff Approval, No Injection | Implemented/released contract-only |
| v0.45.0 | M41 - Local Prototype Safety Freeze | Implemented/released safety freeze |
| v0.46.0 | M42 - Mobile Companion Product Contract Refresh | Implemented/released contract refresh |
| v0.47.0 | M43 - Mobile API Boundary, Read-Only | Implemented/released contract-only |
| v0.48.0 | M44 - CCC iOS Skeleton, No Authority | Implemented/released source-only |
| v0.48.1 | M44 hardening - CCC iOS Skeleton Verifier Allowance | Implemented/released hardening |
| v0.49.0 | M45 - CCC iOS Local Read-Only Connection | Implemented/released contract/status-only |
| v0.50.0 | M46 - iOS Review/Receipt Read-Only Surfaces | Implemented/released source-only read-only |
| v0.51.0 | M47 - TestFlight Pipeline, Internal Only | Implemented/released contract/checklist-only |
| v0.52.0 | M48 - First Internal TestFlight Build | Implemented/released reviewed-candidate-only |
| v0.53.0 | M49 - Mobile Review Approval Capture | Implemented/released safe-ref-only review capture |
| v0.54.0 | M50 - Mobile Approval Audit Hardening | Implemented/released audit hardening |
| v0.55.0 | M51 - OpenWebUI Bridge Adapter Pilot | Implemented/released adapter pilot |
| v0.56.0 | M52 - OpenWebUI Safe Conversation Surface | Implemented/released safe conversation surface |
| v0.57.0 | M53 - Controlled Tool Expansion Review | Implemented/released review-only |
| v0.58.0 | M54 - Safe Media Metadata Inspector | Implemented/released metadata-only |
| v0.59.0 | M55 - Redacted Observability Export | Implemented/released redacted-only |
| v0.60.0 | M56 - Agent Eval Regression Harness | Implemented/released contract-only |
| v0.61.0 | M57 - Runtime Sandbox Architecture Review | Implemented/released architecture-review-only |
| v0.62.0 | M58 - Dry-Run Execution Audit Harness | Implemented/released dry-run-only |
| v0.63.0 | M59 - Public GitHub Readiness | Implemented/released review-only |
| v0.64.0 | M60 - Local Developer Beta Freeze | Implemented/released freeze-only |
| v0.65.0 | M61 - Autonomy Mode Charter + Authority Levels | Implemented/released contract-only autonomy authority charter |
| v0.66.0 | M62 - Scoped Autonomy Session Contracts | Implemented/released contract-only scoped session records |
| v0.67.0 | M63 - Autonomy Policy Engine v1 | Implemented/released contract-only policy evaluation |

The roadmap intentionally separates contract planning, validation, preview,
manual local execution, and future operational authority.

## Repository Layout

```text
src/ultimate_ai_agent/     Python Agent Core contracts and validators
apps/control-center/       CCC Web React/Vite control surface
scripts/                   Verifiers, release checks, OpenAPI export, gates
scripts/dev/               Local developer launcher tooling
tests/                     Unit, contract, safety, and Foundation Gate tests
docs/                      Active docs, canonical maps, release notes, archive
VERSION.md                 Current active baseline summary
AGENTS.md                  Workspace rules and milestone safety boundaries
Makefile                   Repo-local verification commands
```

Historical release artifacts live under `docs/archive/`. The root directory is
kept minimal and current by policy.

## Verification Philosophy

Ultimate AI Agent treats verification as a first-class design surface.

Release work is expected to preserve:

- deterministic Python tests
- OpenAPI route-contract stability
- static safety scans for forbidden capability drift
- documentation integrity checks
- frontend typecheck/lint/test/build coverage
- Foundation Gate criteria for milestone boundaries
- clean version, tag, and release-packet alignment

The main verification entrypoints are:

- `make test`
- `make verify`
- `make frontend-check`
- `.venv/bin/python scripts/run_foundation_gate.py`
- `.venv/bin/python scripts/verify_openapi_contract.py`

## Documentation

The root README is an entrypoint, not the full documentation site.

- Start with [docs/README.md](docs/README.md).
- Use [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) for the full
  active documentation map.
- Use [docs/canonical/CANONICAL_DOC_MAP.md](docs/canonical/CANONICAL_DOC_MAP.md)
  to find source-of-truth documents by system.
- Use [docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md) for current
  sequencing.
- Use [docs/archive/README.md](docs/archive/README.md) for historical context.

Active docs may claim the current active baseline. Archived docs are audit
records and must not be treated as current source of truth.

## Development Posture

When changing this repo:

- keep milestone changes small and release-gated
- preserve the current safety boundary unless a prompt explicitly changes it
- add tests or verifier coverage for safety bugs
- do not commit secrets, credentials, raw private data, or generated artifacts
- keep root docs current and historical docs clearly archived
- use `.venv/bin/python`, not bare `python`, for repo verification commands

## License

License: not yet declared.
