#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


REQUIRED_M23_LOCAL_CALL_DOCS = [
    "docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md",
    "docs/runtime/FIRST_LOCAL_LLM_CALL.md",
    "docs/runtime/M23_FIXED_PROMPT_POLICY.md",
    "docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md",
    "docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md",
    "docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md",
    "docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md",
    "docs/runtime/M23_MANUAL_CLI_USAGE.md",
    "docs/runtime/M23_TO_M24_BOUNDARY.md",
]

REQUIRED_M24_MEMORY_DOCS = [
    "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
    "docs/memory/LOCAL_MEMORY_STORE.md",
    "docs/memory/MEMORY_RECORD_SCHEMA.md",
    "docs/memory/MEMORY_WRITE_POLICY.md",
    "docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md",
    "docs/memory/MEMORY_SOURCE_PRIORITY.md",
    "docs/memory/MEMORY_RECALL_PLANNING.md",
    "docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md",
    "docs/memory/MEMORY_CONFLICT_AND_STALENESS.md",
    "docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md",
    "docs/memory/MEMORY_SECURITY_MODEL.md",
    "docs/memory/MEMORY_NON_GOALS.md",
    "docs/memory/MEMORYOS_REVIEW_INCORPORATION.md",
    "docs/memory/M24_TO_M25_BOUNDARY.md",
]


REQUIRED_M25_TRUTH_DOCS = [
    "docs/truth/TRUTH_SOURCE_ROUTER.md",
    "docs/truth/EVIDENCE_CLAIM_CHECKER.md",
    "docs/truth/TRUTH_SOURCE_PRIORITY.md",
    "docs/truth/CLAIM_EVIDENCE_CHAIN.md",
    "docs/truth/CLAIM_VERIFICATION_POLICY.md",
    "docs/truth/CLAIM_CONFLICT_AND_STALENESS.md",
    "docs/truth/MEMORY_TRUTH_BOUNDARY.md",
    "docs/truth/TRUTH_NON_GOALS.md",
    "docs/truth/M25_TO_M26_BOUNDARY.md",
]


REQUIRED_M26_RECALL_DOCS = [
    "docs/recall/GROUNDED_RECALL_ROUTER.md",
    "docs/recall/CONTEXT_PACK_BUILDER.md",
    "docs/recall/RECALL_SOURCE_PRIORITY.md",
    "docs/recall/RECALL_CANDIDATE_POLICY.md",
    "docs/recall/CONTEXT_PACK_SAFETY.md",
    "docs/recall/RECALL_NON_GOALS.md",
    "docs/recall/M26_TO_M27_BOUNDARY.md",
]


REQUIRED_M27_TOOL_DOCS = [
    "docs/tools/TOOL_BROKER_V2.md",
    "docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md",
    "docs/tools/TOOL_AUTHORITY_BOUNDARY.md",
    "docs/tools/TOOL_INTENT_RECEIPT_PLAN.md",
    "docs/tools/M27_TO_M28_BOUNDARY.md",
]


REQUIRED_M28_APPROVAL_DOCS = [
    "docs/approvals/APPROVAL_AUTHORITY_V2.md",
    "docs/approvals/ACTION_POLICY.md",
    "docs/approvals/APPROVAL_GRANT_BINDING.md",
    "docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md",
    "docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md",
    "docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md",
    "docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md",
    "docs/approvals/APPROVAL_RECEIPT_PLAN.md",
    "docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md",
    "docs/approvals/M28_TO_M29_BOUNDARY.md",
]


REQUIRED_M29_PLANNING_DOCS = [
    "docs/planning/TASK_PLANNING_ENGINE.md",
    "docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md",
    "docs/planning/TASK_DEPENDENCY_GRAPH.md",
    "docs/planning/TASK_INPUT_BOUNDARY.md",
    "docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md",
    "docs/planning/TASK_PLAN_DECISION_ENVELOPE.md",
    "docs/planning/TASK_PLAN_RECEIPT_PLAN.md",
    "docs/planning/TASK_PLANNING_NON_GOALS.md",
    "docs/planning/M29_TO_M30_BOUNDARY.md",
]


REQUIRED_M30_EXECUTION_DOCS = [
    "docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md",
    "docs/execution/EXECUTION_STATE_MACHINE.md",
    "docs/execution/EXECUTION_STEP_CONTRACTS.md",
    "docs/execution/EXECUTION_DEPENDENCY_POLICY.md",
    "docs/execution/EXECUTION_TRANSITION_POLICY.md",
    "docs/execution/EXECUTION_INPUT_BOUNDARY.md",
    "docs/execution/EXECUTION_RECEIPT_PLAN.md",
    "docs/execution/EXECUTION_NON_GOALS.md",
    "docs/execution/M30_TO_M31_BOUNDARY.md",
]


REQUIRED_M31_TOOL_RUNTIME_DOCS = [
    "docs/tools/TOOL_RUNTIME_ADAPTER.md",
    "docs/tools/NOOP_TOOL_RUNTIME.md",
    "docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md",
    "docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md",
    "docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md",
    "docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md",
    "docs/tools/TOOL_RUNTIME_NON_GOALS.md",
    "docs/tools/M31_TO_M32_BOUNDARY.md",
]


REQUIRED_M32_FILESYSTEM_METADATA_DOCS = [
    "docs/tools/FILESYSTEM_METADATA_TOOL.md",
    "docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md",
    "docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md",
    "docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md",
    "docs/tools/FILESYSTEM_METADATA_NON_GOALS.md",
    "docs/tools/M32_TO_M33_BOUNDARY.md",
]


REQUIRED_M33_REDACTED_FILE_PREVIEW_DOCS = [
    "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
    "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
    "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
    "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
    "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
    "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
    "docs/tools/M33_TO_M34_BOUNDARY.md",
    "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
]


REQUIRED_M34_FILE_CAPABILITY_REVIEW_DOCS = [
    "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md",
    "docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md",
    "docs/files/FILE_CAPABILITY_RISK_REGISTER.md",
    "docs/files/FILE_CAPABILITY_DECISION_RECORD.md",
    "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
    "docs/files/M34_TO_M35_BOUNDARY.md",
]


REQUIRED_M35_FILE_REVIEW_DOCS = [
    "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
    "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
    "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
    "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/files/FILE_REVIEW_RECEIPT_PLAN.md",
    "docs/files/FILE_REVIEW_NON_GOALS.md",
    "docs/files/M35_TO_M36_BOUNDARY.md",
]

REQUIRED_M36_FILE_REVIEW_SURFACE_DOCS = [
    "docs/control_center/FILE_REVIEW_SURFACE.md",
    "docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md",
    "docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md",
    "docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md",
    "docs/control_center/M36_TO_M37_BOUNDARY.md",
]

REQUIRED_M37_REVIEW_APPROVAL_CAPTURE_DOCS = [
    "docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md",
    "docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md",
    "docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md",
    "docs/files/FILE_REVIEW_APPROVAL_API.md",
    "docs/files/M37_TO_M38_BOUNDARY.md",
]


REQUIRED_M38_SAFE_CONTEXT_PROPOSAL_DOCS = [
    "docs/context/SAFE_CONTEXT_PROPOSAL_FROM_APPROVED_REVIEW.md",
    "docs/context/CONTEXT_PROPOSAL_CONTRACT.md",
    "docs/context/CONTEXT_PROPOSAL_AUTHORITY_BOUNDARY.md",
    "docs/context/CONTEXT_PROPOSAL_RECEIPT_PLAN.md",
    "docs/context/CONTEXT_PROPOSAL_NON_GOALS.md",
    "docs/context/M38_TO_M39_BOUNDARY.md",
]


REQUIRED_ACTIVE_DOCS = [
    "docs/README.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/canonical/CANONICAL_DOC_MAP.md",
    "docs/archive/README.md",
    "docs/archive/releases/README.md",
    "docs/archive/roadmap_snapshots/README.md",
    "docs/archive/retired_plans/README.md",
    "docs/roadmap/README.md",
    "docs/roadmap/archive/README.md",
    "docs/maintenance/documentation_integrity_checklist.md",
    "docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md",
    "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
    "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
    "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
    "docs/backlog/mobile_companion_backlog.md",
    "docs/backlog/device_capability_broker_backlog.md",
    "docs/backlog/codex_plugin_enablement_backlog.md",
    "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
    "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
    "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
    "docs/remote/TAILNET_TRANSPORT_POLICY.md",
    "docs/remote/REMOTE_WORKER_FOUNDATION.md",
    "docs/runtime/RUNTIME_READINESS.md",
    "docs/runtime/MANUAL_SMOKE_REPORTS.md",
    "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
    "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
    "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
    "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
    "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
    "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
    *REQUIRED_M23_LOCAL_CALL_DOCS,
    *REQUIRED_M24_MEMORY_DOCS,
    *REQUIRED_M25_TRUTH_DOCS,
    *REQUIRED_M26_RECALL_DOCS,
    *REQUIRED_M27_TOOL_DOCS,
    *REQUIRED_M28_APPROVAL_DOCS,
    *REQUIRED_M29_PLANNING_DOCS,
    *REQUIRED_M30_EXECUTION_DOCS,
    *REQUIRED_M31_TOOL_RUNTIME_DOCS,
    *REQUIRED_M32_FILESYSTEM_METADATA_DOCS,
    *REQUIRED_M33_REDACTED_FILE_PREVIEW_DOCS,
    *REQUIRED_M34_FILE_CAPABILITY_REVIEW_DOCS,
    *REQUIRED_M35_FILE_REVIEW_DOCS,
    *REQUIRED_M36_FILE_REVIEW_SURFACE_DOCS,
    "docs/developer/LOCAL_LAUNCHER.md",
    "docs/control_center/CONTROL_CENTER_CONTRACT.md",
    "docs/control_center/DASHBOARD_SNAPSHOT.md",
    "docs/control_center/ACTION_PREVIEW_POLICY.md",
    "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
    "docs/control_center/FRONTEND_SAFETY_POLICY.md",
    "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
    "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
    "docs/control_center/APPROVAL_QUEUE_UI.md",
    "docs/control_center/RECEIPT_EVENT_VIEWER.md",
    "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
    "docs/control_center/EVENT_TIMELINE_UI.md",
    "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
    "docs/control_center/TRACE_REDACTION_POLICY.md",
    "docs/control_center/EVIDENCE_VIEWER.md",
    "docs/control_center/FILE_REFERENCE_VIEWER.md",
    "docs/control_center/MEMORY_VIEWER.md",
    "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
    "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
    "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
    "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
    "docs/design/OPEN_DESIGN_SYSTEM.md",
    "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
    "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
    "docs/design/ACCESSIBILITY_BASELINE.md",
    "docs/design/DESIGN_TOOLING_POLICY.md",
    "docs/design/DESIGN_TOKEN_ROADMAP.md",
    "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
    "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
    "docs/design/COMPONENT_TAXONOMY.md",
    "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
    "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
    "docs/ui/CLIENT_SURFACE_ROLES.md",
    "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
    "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
    "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
    "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
    "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
    "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_NON_GOALS.md",
    "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
    "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
    "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
    "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
    "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
    "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
    "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
    "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
    "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
    "docs/mobile/MOBILE_API_PLANNING.md",
    "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
    "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
    "docs/mobile/MOBILE_SECURITY_MODEL.md",
    "docs/mobile/MOBILE_CAPTURE_POLICY.md",
    "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
    "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
    "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
    "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
    "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
    "docs/roadmap/MILESTONE_CHARTERS.md",
    "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
]


EXPECTED_ACTIVE_M34_LABEL = "v0.38.0 / M34 - Broader File Capability Review"
ACTIVE_M34_LABEL_DOCS = [
    "README.md",
    "docs/canonical/09_roadmap.md",
    "docs/canonical/20_user_control_center.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/MILESTONE_CHARTERS.md",
]
CONFLICTING_ACTIVE_M34_TITLES = [
    "m34 - macos local companion contract / prototype",
    "m34 - safe file review workflow + user approval gate",
]
EXPECTED_M34_M60_LABELS = [
    ("v0.38.0", "M34", "Broader File Capability Review"),
    ("v0.39.0", "M35", "Safe File Review Workflow Contracts"),
    ("v0.40.0", "M36", "CCC File Review Surface, Review-Only"),
    ("v0.41.0", "M37", "Review Approval Capture, Review-Only Persistence"),
    ("v0.42.0", "M38", "Safe Context Proposal From Approved Review"),
    ("v0.43.0", "M39", "CCC Context Proposal Surface"),
    ("v0.44.0", "M40", "Context Handoff Approval, No Injection"),
    ("v0.45.0", "M41", "Local Prototype Safety Freeze"),
    ("v0.46.0", "M42", "Mobile Companion Product Contract Refresh"),
    ("v0.47.0", "M43", "Mobile API Boundary, Read-Only"),
    ("v0.48.0", "M44", "CCC iOS Skeleton, No Authority"),
    ("v0.49.0", "M45", "CCC iOS Local Read-Only Connection"),
    ("v0.50.0", "M46", "iOS Review/Receipt Read-Only Surfaces"),
    ("v0.51.0", "M47", "TestFlight Pipeline, Internal Only"),
    ("v0.52.0", "M48", "First Internal TestFlight Build"),
    ("v0.53.0", "M49", "Mobile Review Approval Capture"),
    ("v0.54.0", "M50", "Mobile Approval Audit Hardening"),
    ("v0.55.0", "M51", "OpenWebUI Bridge Adapter Pilot"),
    ("v0.56.0", "M52", "OpenWebUI Safe Conversation Surface"),
    ("v0.57.0", "M53", "Controlled Tool Expansion Review"),
    ("v0.58.0", "M54", "Safe Media Metadata Inspector"),
    ("v0.59.0", "M55", "Redacted Observability Export"),
    ("v0.60.0", "M56", "Agent Eval Regression Harness"),
    ("v0.61.0", "M57", "Runtime Sandbox Architecture Review"),
    ("v0.62.0", "M58", "Dry-Run Execution Audit Harness"),
    ("v0.63.0", "M59", "Public GitHub Readiness"),
    ("v0.64.0", "M60", "Local Developer Beta Freeze"),
]
ACTIVE_M34_M60_LABEL_DOCS = [
    "README.md",
    "docs/canonical/09_roadmap.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
]
SUPERSEDED_ACTIVE_M35_M40_TITLES = [
    "device capability broker implementation, no sensors",
    "mobile capture inbox, selected input only",
    "one governed sensor capability",
    "browser automation contract, no execution",
    "observability export adapters",
    "agent evaluation + regression harness",
]

REQUIRED_DESIGN_DOCS = [
    "docs/design/OPEN_DESIGN_SYSTEM.md",
    "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
    "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
    "docs/design/ACCESSIBILITY_BASELINE.md",
    "docs/design/DESIGN_TOOLING_POLICY.md",
    "docs/design/DESIGN_TOKEN_ROADMAP.md",
    "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
    "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
    "docs/design/COMPONENT_TAXONOMY.md",
    "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
]

REQUIRED_UI_STRATEGY_DOCS = [
    "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
    "docs/ui/CLIENT_SURFACE_ROLES.md",
    "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
    "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
]

REQUIRED_OPENWEBUI_BRIDGE_DOCS = [
    "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
    "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
    "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
    "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_NON_GOALS.md",
    "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
]

REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS = [
    "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
    "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
    "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
    "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
    "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
]

REQUIRED_MOBILE_DOCS = [
    "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
    "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
    "docs/mobile/MOBILE_API_PLANNING.md",
    "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
    "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
    "docs/mobile/MOBILE_SECURITY_MODEL.md",
    "docs/mobile/MOBILE_CAPTURE_POLICY.md",
    "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
    "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
    "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
]

REQUIRED_POST_M20_ROADMAP_DOCS = [
    "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
    "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
]

REQUIRED_DEVICE_CAPABILITY_DOCS = [
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
    "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
    "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
    "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
    "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
    "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
    "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
]

UNSAFE_IMPLEMENTATION_CLAIMS = [
    "tailscale integration is implemented",
    "headscale integration is implemented",
    "remote execution is supported",
    "mobile camera access is implemented",
    "microphone capture is implemented",
    "gps access is implemented",
    "skill factory is implemented",
    "scanner runtime is implemented",
    "production_ready=true",
    "real_model_runtime_ready=true",
    "remote_execution_ready=true",
    "mobile_sensor_ready=true",
    "plugin_or_native_build_ready=true",
    "production control center is implemented",
    "control center executes actions",
    "control center enables plugins",
    "control center dispatches remote workers",
    "control center calls models",
    "control center controls native builds",
    "control center accesses mobile sensors",
    "web control center has production authority",
]

ACTIVE_DOCS_TO_SCAN = [
    "README.md",
    "VERSION.md",
    "AGENTS.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/canonical/CANONICAL_DOC_MAP.md",
    "docs/canonical/09_roadmap.md",
    "docs/roadmap/MILESTONE_CHARTERS.md",
    "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
    *REQUIRED_POST_M20_ROADMAP_DOCS,
    "docs/api/README.md",
    "docs/api/openapi_contract.md",
    "docs/api/route_inventory.md",
    "docs/runtime/model_runtime_adapter_harness.md",
    "docs/runtime/local_loopback_model_runtime.md",
    "docs/runtime/RUNTIME_READINESS.md",
    "docs/runtime/MANUAL_SMOKE_REPORTS.md",
    "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
    *REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS,
    *REQUIRED_M23_LOCAL_CALL_DOCS,
    *REQUIRED_M25_TRUTH_DOCS,
    "docs/control_center/CONTROL_CENTER_CONTRACT.md",
    "docs/control_center/DASHBOARD_SNAPSHOT.md",
    "docs/control_center/ACTION_PREVIEW_POLICY.md",
    "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
    "docs/control_center/FRONTEND_SAFETY_POLICY.md",
    "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
    "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
    "docs/control_center/APPROVAL_QUEUE_UI.md",
    "docs/control_center/RECEIPT_EVENT_VIEWER.md",
    "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
    "docs/control_center/EVENT_TIMELINE_UI.md",
    "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
    "docs/control_center/TRACE_REDACTION_POLICY.md",
    "docs/control_center/EVIDENCE_VIEWER.md",
    "docs/control_center/FILE_REFERENCE_VIEWER.md",
    "docs/control_center/MEMORY_VIEWER.md",
    "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
    "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
    "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
    "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
    *REQUIRED_M36_FILE_REVIEW_SURFACE_DOCS,
    *REQUIRED_DESIGN_DOCS,
    *REQUIRED_UI_STRATEGY_DOCS,
    *REQUIRED_OPENWEBUI_BRIDGE_DOCS,
    *REQUIRED_DEVICE_CAPABILITY_DOCS,
    *REQUIRED_MOBILE_DOCS,
    *REQUIRED_M30_EXECUTION_DOCS,
    "docs/remote/REMOTE_WORKER_FOUNDATION.md",
    "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
    "docs/remote/REMOTE_JOB_ENVELOPE.md",
    "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
    "docs/remote/TAILNET_TRANSPORT_POLICY.md",
    "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
    "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
    "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
    "docs/backlog/mobile_companion_backlog.md",
    "docs/backlog/device_capability_broker_backlog.md",
    "docs/backlog/codex_plugin_enablement_backlog.md",
    "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
    "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _active_version(root: Path) -> str | None:
    match = re.search(r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*", _read(root / "VERSION.md"))
    return match.group(1) if match else None


def _version_tuple(version: str | None) -> tuple[int, int, int]:
    if not version:
        return (0, 0, 0)
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _release_packet_paths(version_key: str) -> tuple[str, str]:
    return (
        f"docs/archive/releases/v{version_key}/README_IMPORT.md",
        f"docs/archive/releases/v{version_key}/master_plan.md",
    )


def _active_baseline_label_docs(version: str) -> list[str]:
    version_key = version.replace(".", "_")
    active_import, active_master = _release_packet_paths(version_key)
    return [
        "README.md",
        "VERSION.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/canonical/09_roadmap.md",
        "docs/roadmap/README.md",
        "docs/roadmap/MILESTONE_CHARTERS.md",
        "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
        f"docs/release_notes/v{version_key}.md",
        f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
        active_import,
        active_master,
    ]


ACTIVE_BASELINE_LABEL_PATTERNS = [
    re.compile(r"current active baseline\s*(?:\||:)?\s*\*{0,2}v?(\d+\.\d+\.\d+)\*{0,2}", re.IGNORECASE),
    re.compile(r"active accepted baseline is\s+v?(\d+\.\d+\.\d+)", re.IGNORECASE),
    re.compile(
        r"status:\s*active[^\n]*(?:maintained through|source of truth through)\s+v?(\d+\.\d+\.\d+)",
        re.IGNORECASE,
    ),
    re.compile(r"current through:\s*\*{0,2}v?(\d+\.\d+\.\d+)\*{0,2}", re.IGNORECASE),
]


def _verify_active_baseline_labels(root: Path, version: str) -> list[str]:
    failures: list[str] = []
    expected = f"v{version}"
    for rel_path in _active_baseline_label_docs(version):
        path = root / rel_path
        if not path.exists():
            continue
        for line_number, line in enumerate(_read(path).splitlines(), start=1):
            for pattern in ACTIVE_BASELINE_LABEL_PATTERNS:
                for match in pattern.finditer(line):
                    actual = f"v{match.group(1)}"
                    if actual != expected:
                        failures.append(
                            f"{rel_path}:{line_number} active baseline label {actual} "
                            f"does not match expected {expected}"
                        )
    return failures


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    version = _active_version(root)
    if not version:
        return ["VERSION.md active baseline is missing or malformed"]

    version_key = version.replace(".", "_")
    pyproject = _read(root / "pyproject.toml")
    init = _read(root / "src/ultimate_ai_agent/__init__.py")
    readme = _read(root / "README.md")

    if f'version = "{version}"' not in pyproject:
        failures.append("pyproject.toml version does not match VERSION.md")
    if f'__version__ = "{version}"' not in init:
        failures.append("package __version__ does not match VERSION.md")

    active_import, active_master = _release_packet_paths(version_key)
    active_release_notes = f"docs/release_notes/v{version_key}.md"
    active_gate_plan = f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md"
    failures.extend(_verify_active_baseline_labels(root, version))
    for rel_path in [active_import, active_master, active_release_notes, active_gate_plan, *REQUIRED_ACTIVE_DOCS]:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    if active_import not in readme:
        failures.append("README.md does not point to active archived README_IMPORT")
    if active_master not in readme:
        failures.append("README.md does not point to active archived master plan")
    if "docs/DOCUMENTATION_INDEX.md" not in readme:
        failures.append("README.md does not point to documentation index")
    if "docs/canonical/CANONICAL_DOC_MAP.md" not in readme:
        failures.append("README.md does not point to canonical doc map")

    documentation_index = _read(root / "docs/DOCUMENTATION_INDEX.md")
    expected_current_notes = f"Current release notes: `{active_release_notes}`"
    if expected_current_notes not in documentation_index:
        failures.append("docs/DOCUMENTATION_INDEX.md current release notes pointer does not match active version")

    release_notes_dir = root / "docs/release_notes"
    for release_note in release_notes_dir.glob("v*.md"):
        rel_path = release_note.relative_to(root).as_posix()
        if rel_path == active_release_notes:
            continue
        lowered = _read(release_note).lower()
        if "status: current release notes" in lowered:
            failures.append(f"historical release notes claim current status: {rel_path}")

    for rel_path in ACTIVE_DOCS_TO_SCAN:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active scan target: {rel_path}")
            continue
        lowered = _read(path).lower()
        for phrase in UNSAFE_IMPLEMENTATION_CLAIMS:
            if phrase in lowered:
                failures.append(f"unsafe implemented-capability claim in {rel_path}: {phrase}")

    failures.extend(_verify_roadmap_milestone_charters(root))
    failures.extend(_verify_open_design_governance(root))
    failures.extend(_verify_openwebui_ccc_strategy(root))
    failures.extend(_verify_openwebui_bridge_contract_docs(root, version))
    failures.extend(_verify_local_runtime_activation_docs(root, version))
    failures.extend(_verify_m23_local_model_call_docs(root, version))
    failures.extend(_verify_m24_memory_docs(root, version))
    failures.extend(_verify_m25_truth_docs(root, version))
    failures.extend(_verify_mobile_companion_contract_docs(root, version))
    failures.extend(_verify_m20_device_capability_docs(root, version))
    failures.extend(_verify_post_m20_roadmap_projection(root))
    failures.extend(_verify_active_m34_label_consistency(root, version))
    failures.extend(_verify_m34_m60_roadmap_supersession(root, version))
    failures.extend(_verify_m34_file_capability_review_docs(root, version))
    failures.extend(_verify_m34_active_currentness(root, version))
    failures.extend(_verify_m35_file_review_workflow_docs(root, version))
    failures.extend(_verify_m36_file_review_surface_docs(root, version))
    failures.extend(_verify_m37_review_approval_capture_docs(root, version))
    failures.extend(_verify_m38_safe_context_proposal_docs(root, version))
    failures.extend(_verify_m19_roadmap_currentness(root, version))
    failures.extend(_verify_post_m18_roadmap_status_labels(root))

    policy_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
        ]
        if (root / rel_path).exists()
    )
    policy_expectations = {
        "iOS/macOS build plugins disabled or future-only": ["build ios apps", "build macos apps", "disabled"],
        "Computer Use disabled or approval-only": ["computer use", "disabled"],
        "Chrome authenticated profile disabled or approval-only": ["chrome authenticated", "disabled"],
        "plugin/skill installers disabled": ["plugin/skill installers", "disabled"],
        "Browser + Build Web Apps future approval": ["browser + build web apps", "approval"],
    }
    for label, required_fragments in policy_expectations.items():
        if not all(fragment in policy_text for fragment in required_fragments):
            failures.append(f"missing Codex plugin governance policy: {label}")

    return failures


def _normalize_milestone_label_text(text: str) -> str:
    normalized = text.lower().replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", normalized)


def _verify_active_m34_label_consistency(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 37, 3):
        return []

    failures: list[str] = []
    expected_fragment = "broader file capability review"
    for rel_path in ACTIVE_M34_LABEL_DOCS:
        path = root / rel_path
        if not path.exists():
            continue
        normalized = _normalize_milestone_label_text(_read(path))
        for stale_title in CONFLICTING_ACTIVE_M34_TITLES:
            if stale_title in normalized:
                failures.append(
                    f"active M34 roadmap label mismatch in {rel_path}: "
                    f"expected {EXPECTED_ACTIVE_M34_LABEL}"
                )
        if "v0.38.0" in normalized and "m34" in normalized and expected_fragment not in normalized:
            failures.append(
                f"active M34 roadmap label mismatch in {rel_path}: "
                f"expected {EXPECTED_ACTIVE_M34_LABEL}"
            )
    return failures


def _verify_m34_m60_roadmap_supersession(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 37, 4):
        return []

    failures: list[str] = []
    combined_parts: list[str] = []
    for rel_path in ACTIVE_M34_M60_LABEL_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing M34-M60 roadmap supersession doc: {rel_path}")
            continue
        normalized = _normalize_milestone_label_text(_read(path))
        combined_parts.append(normalized)
        for version_label, milestone, title in EXPECTED_M34_M60_LABELS:
            expected = _normalize_milestone_label_text(f"{version_label} / {milestone} - {title}")
            table_form = _normalize_milestone_label_text(f"{version_label} | {milestone} | {title}")
            readme_table_form = _normalize_milestone_label_text(f"{version_label} | {milestone} - {title}")
            if expected not in normalized and table_form not in normalized and readme_table_form not in normalized:
                failures.append(
                    f"active M34-M60 roadmap label mismatch in {rel_path}: "
                    f"expected {version_label} / {milestone} - {title}"
                )

    combined = "\n".join(combined_parts)
    for stale_title in SUPERSEDED_ACTIVE_M35_M40_TITLES:
        if stale_title in combined:
            failures.append(f"superseded active M35-M40 roadmap label still present: {stale_title}")

    required_fragments = {
        "M42 must be mobile planning refresh": "m42",
        "M44 must be first iOS skeleton": "first ios skeleton",
        "M47 must be TestFlight-capable pipeline": "testflight-capable pipeline",
        "M48 must be first internal TestFlight build": "first internal testflight build",
        "M49-M50 must be mobile approval capture/audit": "m49-m50",
        "Archive docs must not be active source of truth": "not the active source of truth",
    }
    if _version_tuple(version) >= (0, 42, 0):
        required_fragments.update(
            {
                "M34 must be released as planning/docs/verifier only": (
                    "m34 is implemented/released as planning/docs/verifier only"
                ),
                "M35 must be released as Safe File Review Workflow Contracts": (
                    "m35 is implemented/released"
                ),
                "M36 must be released as CCC File Review Surface": (
                    "m36 is implemented/released"
                ),
                "M37 must be released as Review Approval Capture": (
                    "m37 is implemented/released"
                ),
                "M38 must be released as Safe Context Proposal": (
                    "m38 is implemented/released"
                ),
                "M39-M60 must remain planned/provisional": "m39-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 41, 0):
        required_fragments.update(
            {
                "M34 must be released as planning/docs/verifier only": (
                    "m34 is implemented/released as planning/docs/verifier only"
                ),
                "M35 must be released as Safe File Review Workflow Contracts": (
                    "m35 is implemented/released"
                ),
                "M36 must be released as CCC File Review Surface": (
                    "m36 is implemented/released"
                ),
                "M37 must be released as Review Approval Capture": (
                    "m37 is implemented/released"
                ),
                "M38-M60 must remain planned/provisional": "m38-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 40, 0):
        required_fragments.update(
            {
                "M34 must be released as planning/docs/verifier only": (
                    "m34 is implemented/released as planning/docs/verifier only"
                ),
                "M35 must be released as Safe File Review Workflow Contracts": (
                    "m35 is implemented/released"
                ),
                "M36 must be released as CCC File Review Surface": (
                    "m36 is implemented/released"
                ),
                "M37-M60 must remain planned/provisional": "m37-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 39, 0):
        required_fragments.update(
            {
                "M34 must be released as planning/docs/verifier only": (
                    "m34 is implemented/released as planning/docs/verifier only"
                ),
                "M35 must be released as Safe File Review Workflow Contracts": (
                    "m35 is implemented/released"
                ),
                "M36-M60 must remain planned/provisional": "m36-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 38, 0):
        required_fragments.update(
            {
                "M35 must be first implementation after supersession": (
                    "m35 is the first implementation after"
                ),
                "M34 must be released as planning/docs/verifier only": (
                    "m34 is implemented/released as planning/docs/verifier only"
                ),
                "M36-M60 must remain planned/provisional": "m36-m60 remain planned/provisional",
            }
        )
    else:
        required_fragments.update(
            {
                "M34 must remain planning/docs/verifier only": "m34 is planning/docs/verifier only",
                "M34-M60 must remain planned/provisional": "m34-m60 remain planned/provisional",
            }
        )
    for failure, fragment in required_fragments.items():
        if fragment not in combined:
            failures.append(failure)

    boundary_doc = root / "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md"
    boundary_text = _normalize_milestone_label_text(_read(boundary_doc)) if boundary_doc.exists() else ""
    blocked_boundaries = [
        "arbitrary raw file browsing",
        "arbitrary caller-selected filesystem roots",
        "raw file export",
        "full-file reads",
        "arbitrary shell/subprocess",
        "unrestricted network tools",
        "provider/model calls as authority",
        "background workers",
        "mobile sensors",
        "plugin enablement",
        "production authority",
        "unreviewed memory writes",
        "automatic context injection",
        "raw prompt/provider payload exposure",
        "external saas/analytics sdks",
        "credentials/cookie handling",
        "remote execution",
        "browser automation execution",
        "approval refs as authority",
    ]
    for boundary in blocked_boundaries:
        if boundary not in boundary_text:
            failures.append(f"M34-M60 supersession missing blocked boundary: {boundary}")

    media_fragments = [
        "media color pipeline",
        "not core before m60 except for m54",
        "ocio deterministic transform preview belongs after m60",
        "ai gamut expansion is much later",
        "never truth recovery",
    ]
    for fragment in media_fragments:
        if fragment not in boundary_text:
            failures.append(f"M34-M60 supersession missing media/color positioning: {fragment}")

    return failures


def _verify_m34_file_capability_review_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 38, 0):
        return []

    failures: list[str] = []
    existing_docs: list[str] = []
    for rel_path in REQUIRED_M34_FILE_CAPABILITY_REVIEW_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M34 file capability doc: {rel_path}")
            continue
        existing_docs.append(_normalize_milestone_label_text(_read(path)))

    combined = "\n".join(existing_docs)
    required_fragments = {
        "M34 docs must say planning/review only": "planning/review only",
        "M34 docs must say no raw file reads": "no raw file reads",
        "M34 docs must say no file review UI": "no file review ui",
        "M34 docs must say no approval persistence": "no approval persistence",
        "M34 docs must say no context injection": "no context injection",
        "M34 docs must say no memory writes": "no memory writes",
        "M34 docs must say no export": "no export",
        "M34 docs must say no execution": "no execution",
        "M34 docs must keep M36 planned/provisional": "m36 remains planned/provisional",
    }
    if _version_tuple(version) < (0, 39, 0):
        required_fragments["M34 docs must keep M35 planned/provisional"] = "m35 remains planned/provisional"
    else:
        required_fragments["M34 docs must acknowledge M35 implementation"] = "v0.39.0 implements m35"
    for failure, fragment in required_fragments.items():
        if fragment not in combined:
            failures.append(failure)

    forbidden_fragments = {
        "M34 docs must not claim M35 implementation": [
            "m34 implements safe file review workflow contracts",
            "safe file review workflow is implemented",
        ],
        "M34 docs must not claim file review UI implementation": [
            "m34 implements ccc file review surface",
            "m34 implements safe file review workflow contracts and file review ui",
            "ccc file review surface is implemented",
            "file review ui is implemented",
        ],
        "M34 docs must not claim approval persistence implementation": [
            "approval persistence is implemented",
            "review approval capture is implemented",
        ],
        "M34 docs must not claim context proposal implementation": [
            "context proposal is implemented",
            "safe context proposal is implemented",
        ],
        "M34 docs must not claim context injection": [
            "context injection is implemented",
            "automatic context injection is implemented",
        ],
        "M34 docs must not claim export implementation": [
            "raw file export is implemented",
            "export is implemented",
        ],
    }
    for failure, fragments in forbidden_fragments.items():
        if any(fragment in combined for fragment in fragments):
            failures.append(failure)

    return failures


def _verify_m34_active_currentness(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 38, 0):
        return []

    failures: list[str] = []
    readme = _normalize_milestone_label_text(_read(root / "README.md"))
    stale_readme_row = (
        "v0.38.0 | m34 - broader file capability review | planned/provisional"
    )
    if stale_readme_row in readme:
        failures.append("README.md must not list v0.38.0/M34 as planned/provisional")

    stale_active_m33_docs: list[str] = []
    for rel_path in REQUIRED_M33_REDACTED_FILE_PREVIEW_DOCS:
        path = root / rel_path
        if path.exists() and "m34 remains planned/provisional" in _read(path).lower():
            stale_active_m33_docs.append(rel_path)
    if stale_active_m33_docs:
        failures.append(
            "active M33 docs must not say M34 remains planned/provisional after v0.38.0: "
            + ", ".join(stale_active_m33_docs)
        )

    return failures


def _verify_m35_file_review_workflow_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 39, 0):
        return []

    failures: list[str] = []
    existing_docs: list[str] = []
    for rel_path in REQUIRED_M35_FILE_REVIEW_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M35 file review workflow doc: {rel_path}")
            continue
        existing_docs.append(_normalize_milestone_label_text(_read(path)))

    combined = "\n".join(existing_docs)
    required_fragments = {
        "M35 docs must say redacted review packets only": "redacted review packets only",
        "M35 docs must say exact approval binding": "exact approval binding",
        "M35 docs must say exact file_ref binding": "exact file_ref binding",
        "M35 docs must say exact safe_path_ref binding": "exact safe_path_ref binding",
        "M35 docs must say review_packet_ref alone is insufficient": "review_packet_ref alone is not sufficient",
        "M35 docs must say file/path mismatches are denied": "file/path mismatches are denied",
        "M35 docs must say review-only": "review-only",
        "M35 docs must say no raw file access": "no raw file access",
        "M35 docs must say no raw content": "no raw content",
        "M35 docs must say no approval capture": "no approval capture",
        "M35 docs must say no approval persistence": "no approval persistence",
        "M35 docs must say no context proposal": "no context proposal",
        "M35 docs must say no context injection": "no context injection",
        "M35 docs must say no memory writes": "no memory writes",
        "M35 docs must say no export": "no export",
        "M35 docs must say no execution": "no execution",
        "M35 docs must keep M36 planned/provisional": "m36 remains planned/provisional",
        "M35 docs must keep M37 planned/provisional": "m37 remains planned/provisional",
        "M35 docs must keep M38 planned/provisional": "m38 remains planned/provisional",
    }
    for failure, fragment in required_fragments.items():
        if fragment not in combined:
            failures.append(failure)

    forbidden_fragments = {
        "M35 docs must not claim file review UI implementation": [
            "file review ui is implemented",
            "ccc file review surface is implemented",
        ],
        "M35 docs must not claim approval persistence implementation": [
            "approval persistence is implemented",
            "review approval capture is implemented",
        ],
        "M35 docs must not claim context proposal implementation": [
            "context proposal is implemented",
            "safe context proposal is implemented",
        ],
        "M35 docs must not claim context injection": [
            "context injection is implemented",
            "automatic context injection is implemented",
        ],
        "M35 docs must not claim raw/export/execution implementation": [
            "raw file export is implemented",
            "execution is implemented",
        ],
    }
    for failure, fragments in forbidden_fragments.items():
        if any(fragment in combined for fragment in fragments):
            failures.append(failure)

    return failures


def _verify_m36_file_review_surface_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 40, 0):
        return []

    failures: list[str] = []
    combined_parts: list[str] = []
    for rel_path in REQUIRED_M36_FILE_REVIEW_SURFACE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M36 file review surface doc: {rel_path}")
            continue
        combined_parts.append(_read(path).lower())
    text = "\n".join(combined_parts)

    required_fragments = {
        "M36 docs must say review-only": "review-only",
        "M36 docs must say mock and non-authoritative": "mock and non-authoritative",
        "M36 docs must say redacted preview": "redacted preview",
        "M36 docs must say redaction summary": "redaction summary",
        "M36 docs must say exact binding refs": "exact binding refs",
        "M36 docs must say safe refs only": "safe refs only",
        "M36 docs must say no mutating request": "no mutating request",
        "M36 docs must say review_packet_ref": "review_packet_ref",
        "M36 docs must say preview_result_ref": "preview_result_ref",
        "M36 docs must say redaction_summary_ref": "redaction_summary_ref",
        "M36 docs must say file_ref": "file_ref",
        "M36 docs must say safe_path_ref": "safe_path_ref",
        "M36 docs must say approval gate contract status": "approval gate contract status",
        "M36 docs must say receipt plan metadata": "receipt plan metadata",
        "M36 docs must say no approval capture": "no approval capture",
        "M36 docs must say no approval persistence": "no approval persistence",
        "M36 docs must say no raw file display": "no raw file display",
        "M36 docs must say no context proposal": "no context proposal",
        "M36 docs must say no context injection": "no context injection",
        "M36 docs must say no memory writes": "no memory writes",
        "M36 docs must say no export": "no export",
        "M36 docs must say no execution": "no execution",
        "M36 docs must keep M37 planned/provisional": "m37 remains planned/provisional",
        "M36 docs must keep M38 planned/provisional": "m38 remains planned/provisional",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M36 docs must not claim approval persistence": [
            "approval persistence is implemented",
            "m37 is implemented",
            "v0.41.0 implements m37",
        ],
        "M36 docs must not claim context proposal implementation": [
            "context proposal is implemented",
            "m38 is implemented",
            "v0.42.0 implements m38",
        ],
        "M36 docs must not claim context injection": ["context injection is implemented"],
    }
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")

    return failures


def _verify_m37_review_approval_capture_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 41, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M37_REVIEW_APPROVAL_CAPTURE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M37 review approval capture doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M37 docs must say review-only persistence": "review-only persistence",
        "M37 docs must say exact redacted review packet": "exact redacted review packet",
        "M37 docs must say safe refs only": "safe refs only",
        "M37 docs must say idempotency/replay protection": "idempotency",
        "M37 docs must say one backend capture route": "/files/review/approvals/capture",
        "M37 docs must deny raw file access": "no raw file access",
        "M37 docs must deny raw content": "raw content",
        "M37 docs must deny context proposal": "no context proposal",
        "M37 docs must deny context injection": "no context injection",
        "M37 docs must deny memory writes": "no memory write",
        "M37 docs must deny export": "no export",
        "M37 docs must deny execution": "no execution",
    }
    if _version_tuple(version) >= (0, 42, 0):
        required_fragments["M37 docs must acknowledge M38 implemented/released"] = "m38 is now implemented/released"
    else:
        required_fragments["M37 docs must keep M38 planned/provisional"] = "m38 remains planned/provisional"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)
    forbidden_fragments = {
        "M37 docs must not claim context injection": ["context injection is implemented"],
        "M37 docs must not claim raw file reads": ["raw file reads are implemented"],
    }
    if _version_tuple(version) < (0, 42, 0):
        forbidden_fragments["M37 docs must not claim context proposal implementation"] = [
            "context proposal is implemented",
            "v0.42.0 implements m38",
        ]
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")
    return failures


def _verify_m38_safe_context_proposal_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 42, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M38_SAFE_CONTEXT_PROPOSAL_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M38 safe context proposal doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M38 docs must say non-authoritative": "non-authoritative",
        "M38 docs must say proposal-only": "proposal-only",
        "M38 docs must say exact approved-review binding": "exact approved-review binding",
        "M38 docs must say approval_ref alone is not authority": "approval_ref alone is not authority",
        "M38 docs must deny approval_test_ refs": "approval_test_",
        "M38 docs must deny raw content": "no raw content",
        "M38 docs must deny full-file reads": "no full-file reads",
        "M38 docs must deny unredacted preview": "no unredacted preview",
        "M38 docs must say not context injection": "not context injection",
        "M38 docs must say not OpenWebUI handoff": "not openwebui handoff",
        "M38 docs must deny model calls": "no model calls",
        "M38 docs must deny memory writes": "does not write memory",
        "M38 docs must deny export": "does not export",
        "M38 docs must deny execution": "does not execute",
        "M38 docs must keep M39 planned/provisional": "m39 remains planned/provisional",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)
    forbidden_fragments = {
        "M38 docs must not claim context injection implementation": [
            "context injection is implemented",
            "automatic context injection is implemented",
        ],
        "M38 docs must not claim OpenWebUI handoff implementation": [
            "openwebui handoff is implemented",
            "send to openwebui is implemented",
        ],
        "M38 docs must not claim memory/export/execution implementation": [
            "memory writes are implemented",
            "export is implemented",
            "execution is implemented",
        ],
        "M38 docs must not claim M39/M40 implementation": [
            "m39 is implemented",
            "v0.43.0 implements m39",
            "m40 is implemented",
            "v0.44.0 implements m40",
        ],
    }
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")
    return failures


def _verify_m19_roadmap_currentness(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 23, 1):
        return failures

    canonical_path = root / "docs/canonical/09_roadmap.md"
    post_m20_path = root / "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md"
    m21_m40_path = root / "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md"
    canonical = _read(canonical_path).lower() if canonical_path.exists() else ""
    post_m20 = _read(post_m20_path).lower() if post_m20_path.exists() else ""
    m21_m40 = _read(m21_m40_path).lower() if m21_m40_path.exists() else ""
    active_roadmaps = "\n".join([canonical, post_m20, m21_m40])

    if "active accepted baseline is v0.22.1" in canonical:
        failures.append("canonical roadmap must not claim active baseline v0.22.1 after v0.23.1")
    if "maintained through v0.22.1" in active_roadmaps:
        failures.append("active roadmap docs must not be maintained only through v0.22.1 after v0.23.1")

    m19_released = re.search(
        r"v0\.23\.0\s*/\s*m19[^\n]*(implemented|released)",
        canonical,
    )
    if _version_tuple(version) >= (0, 24, 0):
        m20_current = re.search(
            r"v0\.24\.0\s*/\s*m20[^\n]*(implemented|released)",
            canonical,
        )
        if _version_tuple(version) >= (0, 27, 0):
            m21_planned = True
            m21_current = re.search(
                r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_current = re.search(
                r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_planned = True
            m23_current = re.search(
                r"(v0\.27\.0[^\n]*m23|m23[^\n]*v0\.27\.0|m23)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m23_planned = True
        elif _version_tuple(version) >= (0, 26, 0):
            m21_planned = True
            m21_current = re.search(
                r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_current = re.search(
                r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_planned = True
            m23_planned = re.search(
                r"(v0\.27\.0[^\n]*m23|m23[^\n]*v0\.27\.0|m23)[^\n]*planned/provisional",
                active_roadmaps,
            )
            m23_current = True
        elif _version_tuple(version) >= (0, 25, 0):
            m21_planned = True
            m21_current = re.search(
                r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_current = True
            m22_planned = re.search(
                r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*planned/provisional",
                active_roadmaps,
            )
            m23_planned = re.search(
                r"(v0\.27\.0[^\n]*m23|m23[^\n]*v0\.27\.0|m23)[^\n]*planned/provisional",
                active_roadmaps,
            )
            m23_current = True
        else:
            m21_planned = re.search(
                r"v0\.25\.0\s*/\s*m21[^\n]*planned/provisional",
                active_roadmaps,
            )
            m21_current = True
            m22_current = True
            m22_planned = True
            m23_planned = True
            m23_current = True
    else:
        m20_current = re.search(
            r"v0\.24\.0\s*/\s*m20[^\n]*planned/provisional",
            canonical,
        )
        m21_planned = True
        m21_current = True
        m22_current = True
        m22_planned = True
        m23_planned = True
        m23_current = True
    if not m19_released:
        failures.append("canonical roadmap must mark M19/v0.23.0 as implemented/released")
    if not m20_current:
        if _version_tuple(version) >= (0, 24, 0):
            failures.append("canonical roadmap must mark M20/v0.24.0 as implemented/released")
        else:
            failures.append("canonical roadmap must keep M20/v0.24.0 planned/provisional")
    if not m21_planned:
        failures.append("active roadmap docs must keep M21/v0.25.0 planned/provisional")
    if _version_tuple(version) >= (0, 25, 0):
        if not m21_current:
            failures.append("active roadmap docs must mark M21/v0.25.0 as implemented/released")
        if _version_tuple(version) >= (0, 26, 0):
            if not m22_current:
                failures.append("active roadmap docs must mark M22/v0.26.0 as implemented/released")
        elif not m22_planned:
            failures.append("active roadmap docs must keep M22/v0.26.0 planned/provisional")
        if _version_tuple(version) >= (0, 27, 0):
            if not m23_current:
                failures.append("active roadmap docs must mark M23/v0.27.0 as implemented/released")
        elif not m23_planned:
            failures.append("active roadmap docs must keep M23/v0.27.0 planned/provisional")
        if _version_tuple(version) >= (0, 28, 0):
            m24_current = re.search(
                r"(v0\.28\.0[^\n]*m24|m24[^\n]*v0\.28\.0|m24)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            if not m24_current:
                failures.append("active roadmap docs must mark M24/v0.28.0 as implemented/released")
            if _version_tuple(version) >= (0, 29, 0):
                m25_current = re.search(
                    r"(v0\.29\.0[^\n]*m25|m25[^\n]*v0\.29\.0|m25)[^\n]*(implemented|released)",
                    active_roadmaps,
                )
                m26_planned = re.search(
                    r"(v0\.30\.0[^\n]*m26|m26[^\n]*v0\.30\.0|m26)[^\n]*planned/provisional",
                    active_roadmaps,
                )
                m26_current = re.search(
                    r"(v0\.30\.0[^\n]*m26|m26[^\n]*v0\.30\.0|m26)[^\n]*(implemented|released)",
                    active_roadmaps,
                )
                if not m25_current:
                    failures.append("active roadmap docs must mark M25/v0.29.0 as implemented/released")
                if _version_tuple(version) >= (0, 30, 0):
                    if not m26_current:
                        failures.append("active roadmap docs must mark M26/v0.30.0 as implemented/released")
                elif not m26_planned:
                    failures.append("active roadmap docs must keep M26/v0.30.0 planned/provisional")
            else:
                m25_implemented_lines = [
                    line
                    for line in active_roadmaps.splitlines()
                    if re.search(r"(v0\.29\.0[^\n]*m25|m25[^\n]*v0\.29\.0|m25)[^\n]*(implemented|released)", line)
                    and "planned/provisional" not in line
                ]
                if m25_implemented_lines:
                    failures.append("active roadmap docs must keep M25/v0.29.0 planned/provisional")

    forbidden_claims = [
        "mobile app is implemented",
        "android app is implemented",
        "ios app is implemented",
        "mobile sensor access is implemented",
        "os permission integration is implemented",
    ]
    if _version_tuple(version) < (0, 24, 0):
        forbidden_claims.extend(
            [
                "m20 is implemented",
                "m20 has implemented",
                "device capability broker is implemented",
                "device capability broker implementation is complete",
            ]
        )
    for claim in forbidden_claims:
        if claim in active_roadmaps:
            failures.append(f"active roadmap docs must not claim future mobile capability implementation: {claim}")

    if _version_tuple(version) >= (0, 38, 0):
        if "m36-m60 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M36-M60 planned/provisional")
    elif _version_tuple(version) >= (0, 37, 4):
        if "m34-m60 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M34-M60 planned/provisional")
    elif _version_tuple(version) >= (0, 32, 0):
        if "m29-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M29-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 31, 0):
        if "m28-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M28-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 30, 0):
        if "m27-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M27-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 29, 0):
        if "m26-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M26-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 28, 0):
        if "m25-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M25-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 27, 0):
        if "m24-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M24-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 26, 0):
        if "m23-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M23-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 25, 0):
        if "m22-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M22-M40 planned/provisional")
    elif "m21-m40 remain planned/provisional" not in active_roadmaps:
        failures.append("post-M20 roadmap docs must keep M21-M40 planned/provisional")

    return failures


def _verify_open_design_governance(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_DESIGN_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    design_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_DESIGN_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "design docs must say no design tools are enabled": "no design tools are enabled",
        "design docs must say design source of truth is repo-owned": "repo-owned source of truth",
        "design docs must say screenshots/design artifacts must not contain secrets": (
            "screenshots and design artifacts must not contain secrets"
        ),
        "design docs must say no automatic design-to-code": "no automatic design-to-code",
        "design docs must say no automatic design sync": "no automatic design sync",
        "design docs must say design SaaS is not authority": "no design saas is authority",
    }
    for failure, fragment in expectations.items():
        if fragment not in design_text:
            failures.append(failure)

    control_center_text = "\n".join(
        _read(root / rel_path)
        for rel_path in [
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
            "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
        ]
        if (root / rel_path).exists()
    )
    for rel_path in [
        "docs/design/OPEN_DESIGN_SYSTEM.md",
        "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
        "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
        "docs/design/ACCESSIBILITY_BASELINE.md",
        "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
        "docs/design/COMPONENT_TAXONOMY.md",
        "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
    ]:
        if rel_path not in control_center_text:
            failures.append(f"Control Center docs missing design doc link: {rel_path}")

    roadmap_text = ""
    roadmap_path = root / "docs/canonical/09_roadmap.md"
    if roadmap_path.exists():
        roadmap_text = _read(roadmap_path).lower()
    if "v0.18.2" not in roadmap_text or "open design system" not in roadmap_text:
        failures.append("roadmap must mention v0.18.2 Open Design implementation")

    return failures


def _verify_openwebui_ccc_strategy(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_UI_STRATEGY_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    ui_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_UI_STRATEGY_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "UI strategy docs must say OpenWebUI is the preferred conversational web shell": (
            "openwebui is the preferred conversational web shell"
        ),
        "UI strategy docs must say OpenWebUI is not the agent brain": "openwebui is not the agent brain",
        "UI strategy docs must say OpenWebUI must not bypass Python Agent Core": (
            "openwebui must not bypass python agent core"
        ),
        "UI strategy docs must say no OpenWebUI integration is implemented yet": (
            "no openwebui integration is implemented"
        ),
        "UI strategy docs must say no OpenWebUI deployment config is added": (
            "no openwebui deployment config is added"
        ),
        "UI strategy docs must say CCC means Control Center Clients": "ccc means control center clients",
        "UI strategy docs must say CCC is the governance/control layer": "ccc is the governance/control layer",
        "UI strategy docs must say Open Design does not replace OpenWebUI": "open design does not replace openwebui",
        "CCC docs must define CCC Web": "ccc web is the current typescript web control center",
        "CCC docs must define CCC iOS": "ccc ios is a future native mobile control client",
        "CCC docs must define CCC Android": "ccc android is a future native mobile control client",
        "CCC docs must define CCC macOS": "ccc macos is a future desktop/local companion client",
        "CCC docs must say all clients are control surfaces": (
            "all ccc clients are control surfaces, not the agent brain"
        ),
        "CCC docs must say all clients use Python Agent Core authority": (
            "all ccc clients must use python agent core authority"
        ),
        "CCC native strategy must say no Android app is implemented": "no android app is implemented yet",
        "CCC native strategy must say no iOS app is implemented": "no ios app is implemented yet",
        "CCC native strategy must say no macOS app is implemented": "no macos app is implemented yet",
        "CCC native strategy must say no CCC native implementation is added": (
            "no ccc native implementation is added"
        ),
        "CCC native strategy must say no native build workflow is added": "no native build workflow is added",
        "CCC native strategy must say no mobile sensor access is added": "no mobile sensor access is added",
        "CCC native strategy must say no OS permission integration is added": (
            "no os permission integration is added"
        ),
        "CCC native strategy must say no signing/store workflow is added": (
            "no signing, keystore, provisioning, app store, or play store workflow is added"
        ),
    }
    for failure, fragment in expectations.items():
        if fragment not in ui_text:
            failures.append(failure)

    return failures


def _verify_openwebui_bridge_contract_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 25, 0):
        return failures

    for rel_path in REQUIRED_OPENWEBUI_BRIDGE_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    bridge_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_OPENWEBUI_BRIDGE_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M21 docs must say contract-only": "contract-only",
        "M21 docs must say OpenWebUI is preferred conversational web shell": (
            "openwebui is the preferred conversational web shell"
        ),
        "M21 docs must say OpenWebUI is not the agent brain": "openwebui is not the agent brain",
        "M21 docs must say Python Agent Core remains authority": "python agent core remains authority",
        "M21 docs must say no OpenWebUI integration is implemented": (
            "no openwebui integration is implemented"
        ),
        "M21 docs must say no deployment config is added": "no deployment config is added",
        "M21 docs must say no direct tool execution": "no direct tool execution",
        "M21 docs must say no direct memory write": "no direct memory write",
        "M21 docs must say no runtime execution": "no runtime execution",
        "M21 docs must say no provider call": "no provider call",
        "M21 docs must say no backend API route": "no backend api route",
        "M21 docs must say refs are identifiers only": "refs are identifiers only",
        "M21 docs must mention M22": "m22",
        "M21 docs must mention M23": "m23",
    }
    for failure, fragment in expectations.items():
        if fragment not in bridge_text:
            failures.append(failure)

    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "README.md",
            "VERSION.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    active_expectations = {
        "active docs must mark M21/v0.25.0 as implemented/released": "v0.25.0",
        "active docs must mark M22/v0.26.0 as implemented/released": "v0.26.0",
        "active docs must link OpenWebUI bridge docs": "docs/openwebui/openwebui_bridge_contract.md",
    }
    if _version_tuple(version) >= (0, 27, 0):
        active_expectations["active docs must mark M23/v0.27.0 as implemented/released"] = "v0.27.0"
    else:
        active_expectations["active docs must keep M23 planned/provisional"] = "m23"
    for failure, fragment in active_expectations.items():
        if fragment not in active_docs:
            failures.append(failure)

    forbidden_active_claims = [
        "openwebui integration is implemented",
        "openwebui deployment config is implemented",
        "openwebui docker config is implemented",
        "openwebui plugin is enabled",
        "openwebui tool bridge is enabled",
        "openwebui admin workflow is enabled",
    ]
    if _version_tuple(version) < (0, 27, 0):
        forbidden_active_claims.extend(["m23 is implemented", "local llm call is implemented"])
    if _version_tuple(version) < (0, 26, 0):
        forbidden_active_claims.append("m22 is implemented")
    for claim in forbidden_active_claims:
        if re.search(rf"(?<!no ){re.escape(claim)}", active_docs):
            failures.append(f"active docs must not claim M21+ runtime implementation: {claim}")

    return failures


def _verify_local_runtime_activation_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 26, 0):
        return failures

    for rel_path in REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    runtime_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M22 docs must say contract-only": "contract-only",
        "M22 docs must say no model was called": "no model was called",
        "M22 docs must say no runtime was activated": "no runtime was activated",
        "M22 docs must say no endpoint was contacted": "no endpoint was contacted",
        "M22 docs must say no backend API route": "no backend api route",
        "M22 docs must say OpenAPI path count remains 74": "openapi path count",
        "M22 docs must say no runtime execution": "no runtime execution",
        "M22 docs must say no provider call": "no provider call",
        "M22 docs must say no endpoint probe": "no endpoint probe",
        "M22 docs must say no user prompt processing": "no user prompt",
        "M22 docs must say no tool execution": "no tool",
        "M22 docs must say no memory write": "no memory",
        "M22 docs must say no dependency": "no dependency",
    }
    if _version_tuple(version) >= (0, 27, 0):
        expectations["M22 docs must mention M23 separate manual-only call"] = "m23"
        expectations["M22 docs must say M23 does not authorize runtime activation"] = "does not authorize runtime activation"
    else:
        expectations["M22 docs must say M23 remains future"] = "m23 remains future"
    for failure, fragment in expectations.items():
        if fragment not in runtime_text:
            failures.append(failure)

    version_key = version.replace(".", "_") if version else ""
    active_import, active_master = _release_packet_paths(version_key) if version_key else ("", "")
    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "README.md",
            "VERSION.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    active_expectations = {
        "active docs must mark M22/v0.26.0 as implemented/released": "v0.26.0",
        "active docs must link M22 activation docs": "docs/runtime/local_model_runtime_activation_contract.md",
    }
    if _version_tuple(version) >= (0, 27, 0):
        active_expectations["active docs must mark M23/v0.27.0 as implemented/released"] = "v0.27.0"
        active_expectations["active docs must link M23 local call docs"] = (
            "docs/runtime/first_local_llm_call_m23.md"
        )
    else:
        active_expectations["active docs must keep M23 planned/provisional"] = "m23"
    for failure, fragment in active_expectations.items():
        if fragment not in active_docs:
            failures.append(failure)

    forbidden_claims = [
        "runtime activation is implemented",
        "endpoint probe is implemented",
        "model runtime call is implemented",
    ]
    if _version_tuple(version) < (0, 27, 0):
        forbidden_claims.extend(
            [
                "m23 is implemented",
                "first real local llm call is implemented",
                "local llm call is implemented",
            ]
        )
    for claim in forbidden_claims:
        if re.search(rf"(?<!no ){re.escape(claim)}", active_docs):
            failures.append(f"active docs must not claim M23+ runtime implementation: {claim}")

    return failures


def _verify_m23_local_model_call_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 27, 1):
        return failures

    for rel_path in REQUIRED_M23_LOCAL_CALL_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    docs_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M23_LOCAL_CALL_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M23 docs must say fixed-prompt-only": "fixed-prompt-only",
        "M23 docs must name the fixed prompt id": "m23_fixed_local_model_smoke_v1",
        "M23 docs must say no arbitrary prompts": "no arbitrary prompt",
        "M23 docs must say CLI defaults dry-run": "dry-run by default",
        "M23 docs must say execution requires explicit flag": "--execute-local-call",
        "M23 docs must say execution requires approval": "validated local approval",
        "M23 docs must say no user content": "no user content",
        "M23 docs must say no memory writes": "no memory write",
        "M23 docs must say no tool execution": "no tool execution",
        "M23 docs must say raw responses are not stored": "raw responses are not stored",
        "M23 docs must say output non-authoritative": "non-authoritative",
        "M23 docs must say response capped/redacted": "capped",
        "M23 docs must say tests use fake transport": "fake transport",
        "M23 docs must say no backend execute route": "no backend api route",
        "M23 docs must say no UI execute": "no control center execution",
        "M23 docs must say no OpenWebUI runtime bridge": "no openwebui runtime bridge",
    }
    if _version_tuple(version) < (0, 28, 0):
        expectations["M23 docs must say M24 remains future"] = "m24 remains future"
    for failure, fragment in expectations.items():
        if fragment not in docs_text:
            failures.append(failure)

    if _version_tuple(version) < (0, 28, 0) and ("m24 is implemented" in docs_text or "m24 implemented" in docs_text):
        failures.append("M23 docs must not claim M24 implemented")
    return failures


def _verify_m24_memory_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 28, 0):
        return failures

    for rel_path in REQUIRED_M24_MEMORY_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    docs_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M24_MEMORY_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M24 docs must say memory is recall, not authority": "memory is recall, not authority",
        "M24 docs must say memory is not ground truth": "memory is not ground truth",
        "M24 docs must say canonical/evidence/receipt/Event Ledger/user-reviewed sources outrank memory": (
            "canonical files, evidence manifests, receipts, event ledger records, and user-reviewed sources outrank memory"
        ),
        "M24 docs must say no automatic writes": "no automatic writes",
        "M24 docs must say no model-output writes": "no model-output writes",
        "M24 docs must say no local LLM output writes": "no local llm output writes",
        "M24 docs must say no OpenWebUI chat memory writes": "no openwebui chat memory writes",
        "M24 docs must say no mobile capture writes": "no mobile capture writes",
        "M24 docs must say no tool output writes": "no tool output writes",
        "M24 docs must say no vector DB": "no vector db",
        "M24 docs must say no embeddings": "no embeddings",
        "M24 docs must say no cloud memory": "no cloud memory",
        "M24 docs must say no raw session history": "no raw session history",
        "M24 docs must say no context injection": "no context injection",
        "M24 docs must say no backend memory mutation API": "no backend memory mutation api",
    }
    if _version_tuple(version) < (0, 29, 0):
        expectations["M24 docs must say M25 remains future"] = "m25 remains future"
    else:
        expectations["M24 docs must say M25 is now separate"] = "m25 is now implemented/released"
        expectations["M24 docs must say M26 remains future"] = "m26 remains future"
    for failure, fragment in expectations.items():
        if fragment not in docs_text:
            failures.append(failure)

    if _version_tuple(version) < (0, 29, 0) and ("m25 is implemented" in docs_text or "m25 implemented" in docs_text):
        failures.append("M24 docs must not claim M25 implemented")
    return failures


def _verify_m25_truth_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 29, 0):
        return failures

    for rel_path in REQUIRED_M25_TRUTH_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    docs_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M25_TRUTH_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M25 docs must say deterministic/local": "deterministic",
        "M25 docs must say no external verification": "no external verification",
        "M25 docs must say no web search": "no web search",
        "M25 docs must say no source fetching": "no source fetching",
        "M25 docs must say no model calls": "no model calls",
        "M25 docs must say no provider calls": "no provider calls",
        "M25 docs must say no retrieval/RAG": "retrieval/rag",
        "M25 docs must say no vector DB": "vector db",
        "M25 docs must say no embeddings": "embeddings",
        "M25 docs must say no memory writes": "no memory writes",
        "M25 docs must say no evidence mutation": "no evidence mutation",
        "M25 docs must say no backend route": "no backend route",
        "M25 docs must say memory is recall, not authority": "memory is recall, not authority",
        "M25 docs must say memory is not ground truth": "memory is not ground truth",
        "M25 docs must say model output cannot verify truth": "model output",
        "M25 docs must say arbitrary refs are not authority": "arbitrary refs are not authority",
        "M25 docs must say unknown refs are denied": "unknown",
        "M25 docs must say explicit unknown source kind is denied": "truthsourcekind.unknown",
        "M25 docs must say evidence-supported requires recognized refs": "evidence-supported status requires recognized",
        "M25 docs must say OpenAPI path count remains 74": "openapi path count",
    }
    if _version_tuple(version) < (0, 30, 0):
        expectations["M25 docs must say M26 remains future"] = "m26 remains future"
    for failure, fragment in expectations.items():
        if fragment not in docs_text:
            failures.append(failure)

    version_key = version.replace(".", "_") if version else ""
    active_import, active_master = _release_packet_paths(version_key) if version_key else ("", "")
    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "README.md",
            "VERSION.md",
            "AGENTS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/testing/test_strategy_v0.md",
            active_import,
            active_master,
            f"docs/release_notes/v{version.replace('.', '_')}.md" if version else "",
            f"docs/implementation/foundation_gate_implementation_plan_v{version.replace('.', '_')}.md" if version else "",
        ]
        if rel_path and (root / rel_path).exists()
    )
    active_expectations = {
        "active docs must mark M25/v0.29.0 as implemented/released": "m25 is implemented/released",
        "active docs must link M25 truth docs": "docs/truth/truth_source_router.md",
        "active docs must say M26 grounded recall remains future": "grounded recall router",
        "active docs must say M25 has no backend route": "no backend route",
        "active docs must say M25 has no web search": "no web search",
        "active docs must say M25 has no model/provider calls": "model/provider",
    }
    if _version_tuple(version) >= (0, 30, 0):
        active_expectations["active docs must mark M26/v0.30.0 as implemented/released"] = (
            "m26 is implemented/released"
        )
        active_expectations["active docs must link M26 recall docs"] = "docs/recall/grounded_recall_router.md"
        if _version_tuple(version) >= (0, 30, 1):
            active_expectations["active docs must mention M26 source identity hardening"] = (
                "source_ref/source_kind"
            )
        if _version_tuple(version) >= (0, 31, 0):
            active_expectations["active docs must mark M27/v0.31.0 as implemented/released"] = (
                "m27 is implemented/released"
            )
            active_expectations["active docs must link M27 tool docs"] = "docs/tools/tool_broker_v2.md"
            active_expectations["active docs must mention Tool Broker v2"] = "tool broker v2"
            if _version_tuple(version) >= (0, 32, 0):
                active_expectations["active docs must mark M28/v0.32.0 as implemented/released"] = (
                    "m28 is implemented/released"
                )
                active_expectations["active docs must link M28 approval docs"] = (
                    "docs/approvals/approval_authority_v2.md"
                )
                if _version_tuple(version) >= (0, 33, 0):
                    active_expectations["active docs must mark M29/v0.33.0 as implemented/released"] = (
                        "m29 is implemented/released"
                    )
                    active_expectations["active docs must link M29 planning docs"] = (
                        "docs/planning/task_planning_engine.md"
                    )
                    if _version_tuple(version) >= (0, 34, 0):
                        active_expectations["active docs must mark M30/v0.34.0 as implemented/released"] = (
                            "m30 is implemented/released"
                        )
                        active_expectations["active docs must link M30 execution docs"] = (
                            "docs/execution/multi_step_execution_framework.md"
                        )
                        if _version_tuple(version) >= (0, 35, 0):
                            active_expectations["active docs must mark M31/v0.35.0 as implemented/released"] = (
                                "m31 is implemented/released"
                            )
                            active_expectations["active docs must link M31 tool runtime docs"] = (
                                "docs/tools/tool_runtime_adapter.md"
                            )
                            if _version_tuple(version) >= (0, 37, 0):
                                active_expectations["active docs must mark M33/v0.37.0 as implemented/released"] = (
                                    "m33 is implemented/released"
                                )
                                active_expectations["active docs must link M33 redacted preview docs"] = (
                                    "docs/tools/redacted_file_preview_tool.md"
                                )
                                if _version_tuple(version) >= (0, 38, 0):
                                    active_expectations["active docs must mark M34/v0.38.0 as implemented/released"] = (
                                        "m34 is implemented/released"
                                    )
                                    active_expectations["active docs must keep M36-M60 planned/provisional"] = (
                                        "m36-m60 remain planned/provisional"
                                    )
                                elif _version_tuple(version) >= (0, 37, 4):
                                    active_expectations["active docs must keep M34-M60 planned/provisional"] = (
                                        "m34-m60 remain planned/provisional"
                                    )
                                else:
                                    active_expectations["active docs must keep M34-M40 planned/provisional"] = (
                                        "m34-m40 remain planned/provisional"
                                    )
                                if _version_tuple(version) >= (0, 37, 1):
                                    active_expectations["active docs must mention M33/v0.37.1 hardening"] = (
                                        "v0.37.1 hardens m33"
                                    )
                                if _version_tuple(version) >= (0, 37, 2):
                                    active_expectations["active docs must mention v0.37.2 local developer launcher"] = (
                                        "v0.37.2 adds local developer launcher"
                                    )
                                    active_expectations["active docs must link local developer launcher docs"] = (
                                        "docs/developer/local_launcher.md"
                                    )
                                    active_expectations["active docs must keep launcher tooling-only"] = (
                                        "local developer launcher"
                                    )
                                if _version_tuple(version) >= (0, 37, 3):
                                    active_expectations["active docs must mention v0.37.3 roadmap label repair"] = (
                                        "v0.37.3 repairs active roadmap label alignment"
                                    )
                                if _version_tuple(version) >= (0, 37, 4):
                                    active_expectations["active docs must mention v0.37.4 roadmap supersession"] = (
                                        "v0.37.4 supersedes"
                                    )
                                    active_expectations["active docs must name planned M34 label"] = (
                                        "broader file capability review"
                                    )
                            else:
                                active_expectations["active docs must keep M32-M40 planned/provisional"] = (
                                    "m32-m40 remain planned/provisional"
                                )
                            if _version_tuple(version) >= (0, 35, 1):
                                active_expectations["active docs must mention M31/v0.35.1 no-op runtime hardening"] = (
                                    "v0.35.1 hardens m31"
                                )
                                active_expectations["active docs must mention hidden dynamic dispatch denial"] = (
                                    "hidden dynamic dispatch"
                                )
                                active_expectations["active docs must mention hidden side-effect denial"] = (
                                    "hidden side-effect"
                                )
                        else:
                            active_expectations["active docs must keep M31-M40 planned/provisional"] = (
                                "m31-m40 remain planned/provisional"
                            )
                    else:
                        active_expectations["active docs must keep M30-M40 planned/provisional"] = (
                            "m30-m40 remain planned/provisional"
                        )
                else:
                    active_expectations["active docs must keep M29-M40 planned/provisional"] = (
                        "m29-m40 remain planned/provisional"
                    )
            else:
                active_expectations["active docs must keep M28-M40 planned/provisional"] = (
                    "m28-m40 remain planned/provisional"
                )
        else:
            active_expectations["active docs must keep M27-M40 planned/provisional"] = (
                "m27-m40 remain planned/provisional"
            )
    else:
        active_expectations["active docs must keep M26-M40 planned/provisional"] = (
            "m26-m40 remain planned/provisional"
        )
    for failure, fragment in active_expectations.items():
        if fragment not in active_docs:
            failures.append(failure)

    if _version_tuple(version) >= (0, 29, 2):
        v0292_expectations = {
            "active docs must say v0.29.2 hardens local-dev API authority": "local-dev api authority",
            "active docs must say kernel task API is dry-run-only": "dry-run-only",
            "active docs must say file read preview is metadata-only": "metadata-only",
            "active docs must say raw exception echo is blocked": "raw exception",
            "active docs must say test-prefixed approval refs are not fallback authority": "approval_test",
        }
        for failure, fragment in v0292_expectations.items():
            if fragment not in active_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 29, 3):
        v0293_expectations = {
            "active docs must say v0.29.3 reorganizes documentation": "reorganizes documentation",
            "active docs must include docs archive entrypoints": "docs/archive",
            "active docs must say historical release packets are archived": "docs/archive/releases",
            "active docs must say v0.29.3 adds no runtime behavior": "no runtime behavior",
        }
        if _version_tuple(version) < (0, 30, 0):
            v0293_expectations["active docs must say M26 remains planned/provisional"] = (
                "m26 remains planned/provisional"
            )
        for failure, fragment in v0293_expectations.items():
            if fragment not in active_docs:
                failures.append(failure)

        sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
        sequence = _read(sequence_path).lower() if sequence_path.exists() else ""
        if "status: historical roadmap projection" not in sequence:
            failures.append("docs/roadmap/NEXT_SEQUENCE_v0_17_5.md must have historical roadmap banner")
        if "current roadmap: docs/canonical/09_roadmap.md" not in sequence:
            failures.append("historical roadmap snapshot must point to current roadmap")

        root_release_artifacts = [
            *root.glob("README_IMPORT_v*.md"),
            *root.glob("ultimate_ai_agent_master_plan_v*.md"),
        ]
        for artifact in root_release_artifacts:
            lowered = _read(artifact).lower()
            if "status: historical stub" not in lowered:
                failures.append(f"root release artifact must be archived or a historical stub: {artifact.name}")

    if _version_tuple(version) >= (0, 29, 4):
        version_key = version.replace(".", "_")
        v0294_expectations = {
            "active docs must say v0.29.4 repairs archive references": "repairs documentation archive references",
            "active docs must say historical verifiers are not current gates": "legacy historical verifiers are not current release gates",
            "active docs must say stale Ruff excludes were removed": "stale ruff excludes",
            "active docs must point to current archive release packet": f"docs/archive/releases/v{version_key}/readme_import.md",
        }
        if _version_tuple(version) < (0, 30, 0):
            v0294_expectations["active docs must say M26 remains future"] = "m26 remains future"
        for failure, fragment in v0294_expectations.items():
            if fragment not in active_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 29, 5):
        v0295_expectations = {
            "active docs must say v0.29.5 polishes duplicated policy wording": "duplicated policy wording",
            "active docs must say v0.29.5 is documentation policy polish": "documentation policy polish",
        }
        for failure, fragment in v0295_expectations.items():
            if fragment not in active_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 30, 0):
        for rel_path in REQUIRED_M26_RECALL_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        recall_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M26_RECALL_DOCS
            if (root / rel_path).exists()
        )
        m26_expectations = {
            "M26 docs must say deterministic/local": "deterministic",
            "M26 docs must say provided candidates only": "provided candidate",
            "M26 docs must say no context injection": "no context injection",
            "M26 docs must say no vector search": "no vector search",
            "M26 docs must say no embeddings": "no embeddings",
            "M26 docs must say no external retrieval": "no external retrieval",
            "M26 docs must say no web search": "no web search",
            "M26 docs must say no model/provider calls": "model/provider",
            "M26 docs must say no memory writes": "no memory write",
            "M26 docs must say no backend route": "no backend",
            "M26 docs must say safe summaries only": "safe summaries",
            "M26 docs must say memory is recall context only": "memory as recall context only",
            "M26 docs must say source_ref/source_kind consistency": "source_ref/source_kind",
            "M26 docs must say caller-declared source_kind cannot upgrade priority": "cannot upgrade",
        }
        if _version_tuple(version) >= (0, 35, 0):
            m26_expectations["M26 docs must say M27 is implemented/released"] = "m27 tool broker v2"
            m26_expectations["M26 docs must say M28 is implemented/released"] = "m28 approval authority v2"
            m26_expectations["M26 docs must say M29 is implemented/released"] = "m29 agent task planning engine"
            m26_expectations["M26 docs must say M30 is implemented/released"] = "m30 multi-step execution framework"
            m26_expectations["M26 docs must say M31 is implemented/released"] = "m31 is implemented/released"
            m26_expectations["M26 docs must keep M32-M40 planned/provisional"] = (
                "m32-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 34, 0):
            m26_expectations["M26 docs must say M27 is implemented/released"] = "m27 tool broker v2"
            m26_expectations["M26 docs must say M28 is implemented/released"] = "m28 approval authority v2"
            m26_expectations["M26 docs must say M29 is implemented/released"] = "m29 agent task planning engine"
            m26_expectations["M26 docs must say M30 is implemented/released"] = "m30 multi-step execution framework"
            m26_expectations["M26 docs must keep M31-M40 planned/provisional"] = (
                "m31-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 33, 0):
            m26_expectations["M26 docs must say M27 is implemented/released"] = "m27 tool broker v2"
            m26_expectations["M26 docs must say M28 is implemented/released"] = "m28 approval authority v2"
            m26_expectations["M26 docs must say M29 is implemented/released"] = "m29 agent task planning engine"
            m26_expectations["M26 docs must keep M30-M40 planned/provisional"] = (
                "m30-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 32, 0):
            m26_expectations["M26 docs must say M27 is implemented/released"] = "m27 tool broker v2"
            m26_expectations["M26 docs must say M28 is implemented/released"] = "m28 approval authority v2"
            m26_expectations["M26 docs must keep M29-M40 planned/provisional"] = (
                "m29-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 31, 0):
            m26_expectations["M26 docs must say M27 is implemented/released"] = "m27 tool broker v2"
            m26_expectations["M26 docs must keep M28-M40 planned/provisional"] = (
                "m28-m40 remain planned/provisional"
            )
        else:
            m26_expectations["M26 docs must say M27 remains planned/provisional"] = (
                "m27 remains planned/provisional"
            )
        for failure, fragment in m26_expectations.items():
            if fragment not in recall_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 31, 0):
        for rel_path in REQUIRED_M27_TOOL_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        tool_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M27_TOOL_DOCS
            if (root / rel_path).exists()
        )
        m27_expectations = {
            "M27 docs must say validation-only": "validation-only",
            "M27 docs must say preview-only": "preview-only",
            "M27 docs must say no real tool execution": "no real tool execution",
            "M27 docs must say approval_ref is not authority": "approval_ref",
            "M27 docs must say context packs are not authority": "context packs are not authority",
            "M27 docs must say no backend execution route": "no backend execution route",
            "M27 docs must say no memory writes": "no memory write",
            "M27 docs must say no Event Ledger mutation": "no event ledger mutation",
            "M27 docs must say no model/provider calls": "model/provider",
            "M27 docs must say no network calls": "no network call",
            "M27 docs must say no browser automation": "no browser automation",
            "M27 docs must say no plugin enablement": "no plugin enablement",
            "M27 docs must say no context injection": "no context injection",
        }
        if _version_tuple(version) >= (0, 35, 0):
            m27_expectations["M27 docs must say M28 is implemented/released"] = (
                "m28 implements approval authority v2"
            )
            m27_expectations["M27 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m27_expectations["M27 docs must say M30 is implemented/released"] = (
                "m30 multi-step execution framework"
            )
            m27_expectations["M27 docs must say M31 is implemented/released"] = (
                "m31 is implemented/released"
            )
            m27_expectations["M27 docs must keep M32-M40 planned/provisional"] = (
                "m32-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 34, 0):
            m27_expectations["M27 docs must say M28 is implemented/released"] = (
                "m28 implements approval authority v2"
            )
            m27_expectations["M27 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m27_expectations["M27 docs must say M30 is implemented/released"] = (
                "m30 multi-step execution framework"
            )
            m27_expectations["M27 docs must keep M31-M40 planned/provisional"] = (
                "m31-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 33, 0):
            m27_expectations["M27 docs must say M28 is implemented/released"] = (
                "m28 implements approval authority v2"
            )
            m27_expectations["M27 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m27_expectations["M27 docs must keep M30-M40 planned/provisional"] = (
                "m30-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 32, 0):
            m27_expectations["M27 docs must say M28 is implemented/released"] = (
                "m28 implements approval authority v2"
            )
            m27_expectations["M27 docs must keep M29-M40 planned/provisional"] = (
                "m29-m40 remain planned/provisional"
            )
        else:
            m27_expectations["M27 docs must keep M28-M40 planned/provisional"] = (
                "m28-m40 remain planned/provisional"
            )
        for failure, fragment in m27_expectations.items():
            if fragment not in tool_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 32, 0):
        for rel_path in REQUIRED_M28_APPROVAL_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        approval_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M28_APPROVAL_DOCS
            if (root / rel_path).exists()
        )
        m28_expectations = {
            "M28 docs must say policy-only": "policy-only",
            "M28 docs must say decision-only": "decision-only",
            "M28 docs must say no action execution": "no action execution",
            "M28 docs must say no tool execution": "no tool execution",
            "M28 docs must say no memory writes": "no memory write",
            "M28 docs must say no network calls": "network calls",
            "M28 docs must say no model/provider calls": "model/provider",
            "M28 docs must say no shell execution": "shell execution",
            "M28 docs must say no backend execution routes": "backend execution route",
            "M28 docs must say approval_ref is not authority": "approval_ref",
            "M28 docs must say approval_test_ is denied/not authority": "approval_test_",
            "M28 docs must say consent_ref alone is not authority": "consent_ref",
            "M28 docs must say wildcard approvals are denied": "wildcard",
            "M28 docs must say expired grants are denied": "expired",
            "M28 docs must say revoked grants are denied": "revoked",
            "M28 docs must say replayed grants are denied": "replayed",
            "M28 docs must say actor/action/resource/scope binding": "actor/action/resource/scope",
            "M28 docs must say raw inputs are rejected": "raw",
            "M28 docs must say receipt plans are non-authoritative": "non-authoritative",
        }
        if _version_tuple(version) >= (0, 35, 0):
            m28_expectations["M28 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m28_expectations["M28 docs must say M30 is implemented/released"] = (
                "m30 multi-step execution framework"
            )
            m28_expectations["M28 docs must say M31 is implemented/released"] = (
                "m31 is implemented/released"
            )
            m28_expectations["M28 docs must keep M32-M40 planned/provisional"] = (
                "m32-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 34, 0):
            m28_expectations["M28 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m28_expectations["M28 docs must say M30 is implemented/released"] = (
                "m30 multi-step execution framework"
            )
            m28_expectations["M28 docs must keep M31-M40 planned/provisional"] = (
                "m31-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 33, 0):
            m28_expectations["M28 docs must say M29 is implemented/released"] = (
                "m29 agent task planning engine"
            )
            m28_expectations["M28 docs must keep M30-M40 planned/provisional"] = (
                "m30-m40 remain planned/provisional"
            )
        else:
            m28_expectations["M28 docs must keep M29-M40 planned/provisional"] = (
                "m29-m40 remain planned/provisional"
            )
        if _version_tuple(version) >= (0, 32, 1):
            m28_expectations["M28 docs must say evaluator revalidation is enforced"] = (
                "evaluator-side revalidation"
            )
            m28_expectations["M28 docs must say model_copy mutation bypasses are denied"] = (
                "model_copy"
            )
        for failure, fragment in m28_expectations.items():
            if fragment not in approval_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 33, 0):
        for rel_path in REQUIRED_M29_PLANNING_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        planning_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M29_PLANNING_DOCS
            if (root / rel_path).exists()
        )
        m29_expectations = {
            "M29 docs must say deterministic": "deterministic",
            "M29 docs must say local": "local",
            "M29 docs must say review-only": "review-only",
            "M29 docs must say no task execution": "no task execution",
            "M29 docs must say no scheduler runtime": "no scheduler runtime",
            "M29 docs must say no background worker": "no background worker",
            "M29 docs must say no tool execution": "no tool execution",
            "M29 docs must say no action execution": "no action execution",
            "M29 docs must say no file mutation": "no file mutation",
            "M29 docs must say no memory writes": "no memory write",
            "M29 docs must say no network calls": "no network call",
            "M29 docs must say no model/provider calls": "model/provider",
            "M29 docs must say no backend route": "backend task/plan execution routes",
            "M29 docs must say no context injection": "no context injection",
            "M29 docs must say dependency graph": "dependency graph",
            "M29 docs must say receipt plans are non-authoritative": "non-authoritative",
        }
        if _version_tuple(version) >= (0, 35, 0):
            m29_expectations["M29 docs must say M30 is implemented/released"] = (
                "m30 is implemented/released"
            )
            m29_expectations["M29 docs must say M31 is implemented/released"] = (
                "m31 is implemented/released"
            )
            m29_expectations["M29 docs must keep M32-M40 planned/provisional"] = (
                "m32-m40 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 34, 0):
            m29_expectations["M29 docs must say M30 is implemented/released"] = (
                "m30 is implemented/released"
            )
            m29_expectations["M29 docs must keep M31-M40 planned/provisional"] = (
                "m31-m40 remain planned/provisional"
            )
        else:
            m29_expectations["M29 docs must keep M30-M40 planned/provisional"] = (
                "m30-m40 remain planned/provisional"
            )
        if _version_tuple(version) >= (0, 33, 1):
            m29_expectations.update(
                {
                    "M29 docs must say dependency graph must be acyclic": "acyclic",
                    "M29 docs must say duplicate step IDs are denied": "duplicate",
                    "M29 docs must say missing step IDs are denied": "missing",
                    "M29 docs must say self dependencies are denied": "self-dependencies",
                    "M29 docs must say indirect cycles are denied": "indirect dependency cycles",
                    "M29 docs must say risk downgrade is denied": "risk downgrade",
                    "M29 docs must say derived risk wins": "derived risk wins",
                    "M29 docs must say side effects cannot be hidden": "side effects cannot be hidden",
                    "M29 docs must say hidden side effects are denied": "hidden side effects",
                    "M29 docs must say authority refs cannot authorize execution": "cannot authorize execution",
                    "M29 docs must say evaluator revalidation exists": "evaluator revalidates",
                    "M29 docs must say model_copy mutations remain denied": "model_copy",
                    "M29 docs must say execution_performed remains false": "execution_performed=false",
                }
            )
        for failure, fragment in m29_expectations.items():
            if fragment not in planning_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 34, 0):
        for rel_path in REQUIRED_M30_EXECUTION_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        execution_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M30_EXECUTION_DOCS
            if (root / rel_path).exists()
        )
        m30_expectations = {
            "M30 docs must say deterministic": "deterministic",
            "M30 docs must say local": "local",
            "M30 docs must say state-machine-only": "state-machine-only",
            "M30 docs must say side-effect-safe": "side-effect-safe",
            "M30 docs must say no real task execution": "no real task execution",
            "M30 docs must say no action execution": "action execution",
            "M30 docs must say no tool execution": "tool execution",
            "M30 docs must say no file mutation": "file mutation",
            "M30 docs must say no memory writes": "memory writes",
            "M30 docs must say no Event Ledger mutation": "event ledger mutation",
            "M30 docs must say no network calls": "network calls",
            "M30 docs must say no model/provider calls": "model/provider calls",
            "M30 docs must say no scheduler/background worker": "scheduler/background worker",
            "M30 docs must say no autonomous loop": "autonomous loop",
            "M30 docs must say no context injection": "context injection",
            "M30 docs must say no backend execution routes": "backend execution routes",
            "M30 docs must say dependency-aware progression": "dependency-aware",
            "M30 docs must say dependency graph must be acyclic": "acyclic",
            "M30 docs must say replay protection": "replay protection",
            "M30 docs must say transition ID replay protection": "transition id",
            "M30 docs must say ready-only completion": "ready",
            "M30 docs must say incomplete finalize denied": "finalize",
            "M30 docs must say hidden side effects denied": "hidden side-effect",
            "M30 docs must say evaluator revalidation exists": "evaluator revalidation",
            "M30 docs must say receipt plans are non-authoritative": "non-authoritative",
            "M30 docs must keep execution_performed false": "execution_performed=false",
        }
        if _version_tuple(version) >= (0, 35, 0):
            m30_expectations["M30 docs must say M31 is implemented/released"] = "m31 is implemented/released"
            m30_expectations["M30 docs must keep M32-M40 planned/provisional"] = "m32-m40 remain planned/provisional"
        else:
            m30_expectations["M30 docs must keep M31-M40 planned/provisional"] = "m31-m40 remain planned/provisional"
        for failure, fragment in m30_expectations.items():
            if fragment not in execution_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 35, 0):
        for rel_path in REQUIRED_M31_TOOL_RUNTIME_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        runtime_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M31_TOOL_RUNTIME_DOCS
            if (root / rel_path).exists()
        )
        m31_expectations = {
            "M31 docs must say first real tool runtime adapter": "first governed tool runtime adapter",
            "M31 docs must say no arbitrary tool execution": "arbitrary tool execution",
            "M31 docs must say no dynamic dispatch": "dynamic dispatch",
            "M31 docs must say no plugins": "plugins",
            "M31 docs must say no shell/subprocess execution": "shell/subprocess",
            "M31 docs must say no memory/network/model/browser/mobile/remote tools": "network, model, browser, mobile, remote, or plugin",
            "M31 docs must say no backend execute route": "no backend execute route",
            "M31 docs must say no Control Center execute controls": "no control center execute control",
            "M31 docs must say approval refs cannot authorize": "approval refs",
            "M31 docs must say approval_test_ is denied": "approval_test_",
            "M31 docs must say no-op result does not echo raw input": "does not echo raw input",
            "M31 docs must say evaluator revalidation exists": "evaluator revalidation",
            "M31 docs must say replay protection exists": "replay-key protection",
            "M31 docs must say side effects are empty": "side_effects_performed=[]",
        }
        if _version_tuple(version) < (0, 36, 0):
            m31_expectations["M31 docs must say only no-op tool is enabled"] = "only the deterministic no-op tool"
            m31_expectations["M31 docs must keep M32-M40 planned/provisional"] = "m32-m40 remain planned/provisional"
        elif _version_tuple(version) >= (0, 37, 4):
            m31_expectations["M31 docs must say no-op remains enabled"] = "tool:no_op.v1"
            m31_expectations["M31 docs must acknowledge M32 filesystem metadata"] = "tool:filesystem_metadata.v1"
            m31_expectations["M31 docs must keep M34-M60 planned/provisional"] = "m34-m60 remain planned/provisional"
        else:
            m31_expectations["M31 docs must say no-op remains enabled"] = "tool:no_op.v1"
            m31_expectations["M31 docs must acknowledge M32 filesystem metadata"] = "tool:filesystem_metadata.v1"
            m31_expectations["M31 docs must keep M33-M40 planned/provisional"] = "m33-m40 remain planned/provisional"
        for failure, fragment in m31_expectations.items():
            if fragment not in runtime_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 36, 0):
        for rel_path in REQUIRED_M32_FILESYSTEM_METADATA_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        m32_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M32_FILESYSTEM_METADATA_DOCS
            if (root / rel_path).exists()
        )
        m32_expectations = {
            "M32 docs must say safe local filesystem metadata": "safe local filesystem metadata",
            "M32 docs must name filesystem metadata tool ref": "tool:filesystem_metadata.v1",
            "M32 docs must say metadata-only": "metadata-only",
            "M32 docs must say server-owned safe roots": "server-owned safe roots",
            "M32 docs must deny raw file content": "raw file content",
            "M32 docs must deny text previews": "text previews",
            "M32 docs must deny content hashes": "content hashes",
            "M32 docs must deny directory listing": "directory listing",
            "M32 docs must deny recursive traversal": "recursive traversal",
            "M32 docs must deny symlink following": "symlink following",
            "M32 docs must deny caller-selected roots": "caller-selected",
            "M32 docs must deny file mutation": "file mutation",
            "M32 docs must say no backend execute route": "backend execute route",
            "M32 docs must say no Control Center execute controls": "control center execute controls",
            "M32 docs must say authority refs cannot authorize": "cannot authorize",
        }
        if _version_tuple(version) >= (0, 38, 0):
            m32_expectations["M32 docs must acknowledge M33 redacted preview"] = "redacted preview"
            m32_expectations["M32 docs must acknowledge M34 broader file capability review"] = (
                "broader file capability review"
            )
            m32_expectations["M32 docs must keep M36-M60 planned/provisional"] = (
                "m36-m60 remain planned/provisional"
            )
        elif _version_tuple(version) >= (0, 37, 4):
            m32_expectations["M32 docs must acknowledge M33 redacted preview"] = "redacted preview"
            m32_expectations["M32 docs must keep M34-M60 planned/provisional"] = "m34-m60 remain planned/provisional"
        elif _version_tuple(version) >= (0, 37, 0):
            m32_expectations["M32 docs must acknowledge M33 redacted preview"] = "redacted preview"
            m32_expectations["M32 docs must keep M34-M40 planned/provisional"] = "m34-m40 remain planned/provisional"
        else:
            m32_expectations["M32 docs must keep M33-M40 planned/provisional"] = "m33-m40 remain planned/provisional"
        for failure, fragment in m32_expectations.items():
            if fragment not in m32_docs:
                failures.append(failure)
        if _version_tuple(version) >= (0, 36, 1):
            m32_hardening_expectations = {
                "M32 hardening docs must say encoded traversal is denied": "encoded traversal",
                "M32 hardening docs must say home-directory paths are denied": "home-directory",
                "M32 hardening docs must say Windows drive paths are denied": "windows drive",
                "M32 hardening docs must say doubled separators are denied": "doubled separators",
                "M32 hardening docs must say private-key-like paths are denied": "private-key-like",
                "M32 hardening docs must say metadata alias flags are denied": "metadata alias flags",
                "M32 hardening docs must say evaluator boundary revalidates": "evaluator boundary",
            }
            for failure, fragment in m32_hardening_expectations.items():
                if fragment not in m32_docs:
                    failures.append(failure)

    if _version_tuple(version) >= (0, 37, 0):
        for rel_path in REQUIRED_M33_REDACTED_FILE_PREVIEW_DOCS:
            if not (root / rel_path).exists():
                failures.append(f"missing active documentation file: {rel_path}")
        m33_docs = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in REQUIRED_M33_REDACTED_FILE_PREVIEW_DOCS
            if (root / rel_path).exists()
        )
        m33_expectations = {
            "M33 docs must say first safe local file read proposal": "first safe local file read proposal",
            "M33 docs must say redacted preview only": "redacted preview only",
            "M33 docs must name redacted preview tool ref": "tool:filesystem.redacted_preview.v1",
            "M33 docs must say no raw file content returned": "raw file content",
            "M33 docs must say no raw file content stored": "stored",
            "M33 docs must say no full-file read output": "full-file",
            "M33 docs must say no content hash": "content hash",
            "M33 docs must say no directory listing": "directory listing",
            "M33 docs must say no recursive traversal": "recursive traversal",
            "M33 docs must say no symlink following": "symlink",
            "M33 docs must say no caller-selected arbitrary root": "caller-selected",
            "M33 docs must say hidden paths denied": "hidden",
            "M33 docs must say secret-like paths denied": "secret-like",
            "M33 docs must say binary files denied": "binary",
            "M33 docs must say unsupported encodings denied": "unsupported encoding",
            "M33 docs must say no file writes/deletes": "file writes",
            "M33 docs must say result is not context injection": "context injection",
        }
        if _version_tuple(version) >= (0, 39, 0):
            m33_expectations["M33 docs must acknowledge M35 file review release"] = (
                "safe file review workflow contracts"
            )
        elif _version_tuple(version) >= (0, 38, 0):
            m33_expectations["M33 docs must acknowledge M34 broader review release"] = (
                "broader file capability review"
            )
            m33_expectations["M33 docs must keep M35 planned/provisional"] = "m35 remains planned/provisional"
        else:
            m33_expectations["M33 docs must say M34 remains future"] = "m34 remains planned/provisional"
        if _version_tuple(version) >= (0, 37, 1):
            m33_expectations.update(
                {
                    "M33 hardening docs must say symlink safe roots are denied": "symlink safe root",
                    "M33 hardening docs must say output boundary rejects secret-like preview text": "output contract boundary",
                    "M33 hardening docs must say evaluator boundaries revalidate": "evaluator",
                    "M33 hardening docs must say constructor validation alone is not trusted": "constructor validation alone",
                }
            )
        for failure, fragment in m33_expectations.items():
            if fragment not in m33_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 37, 2):
        launcher_docs = " ".join(
            _read(root / path).lower()
            for path in [
                "docs/developer/LOCAL_LAUNCHER.md",
                "scripts/dev/README.md",
                "docs/release_notes/v0_37_2.md",
                "docs/archive/releases/v0_37_2/README_IMPORT.md",
                "docs/archive/releases/v0_37_2/master_plan.md",
            ]
        )
        launcher_expectations = {
            "launcher docs must say local developer launcher": "local developer launcher",
            "launcher docs must say localhost-only": "localhost-only",
            "launcher docs must say not a production installer": "not a production installer",
            "launcher docs must say no execution authority": "execution authority",
            "launcher docs must mention stop command": "uaa stop",
            "launcher docs must mention ignored launcher state": ".uaa/dev",
            "launcher docs must say no backend routes": "backend routes",
            "launcher docs must keep M34 future": "m34",
        }
        for failure, fragment in launcher_expectations.items():
            if fragment not in launcher_docs:
                failures.append(failure)

    if _version_tuple(version) >= (0, 29, 4):
        policy_path = root / "docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md"
        if not policy_path.exists():
            failures.append("missing documentation organization policy: docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md")
        else:
            policy = _read(policy_path).lower()
            for fragment in [
                "root directory policy",
                "historical verifiers",
                "legacy verifiers are not current release gates",
                "docs/archive/releases/vx_y_z/readme_import.md",
                "scripts/verify_documentation_integrity.py",
            ]:
                if fragment not in policy:
                    failures.append(f"documentation organization policy missing fragment: {fragment}")

        docs_readme = _read(root / "docs/README.md")
        docs_index = _read(root / "docs/DOCUMENTATION_INDEX.md")
        policy_ref = "docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md"
        if policy_ref not in docs_readme:
            failures.append("docs/README.md must reference documentation organization policy")
        if policy_ref not in docs_index:
            failures.append("docs/DOCUMENTATION_INDEX.md must reference documentation organization policy")

        for verifier_path in sorted(root.glob("verify_ultimate_ai_agent_v0_*.py")):
            failures.append(f"root historical verifier must be archived: {verifier_path.name}")
        scripts_dir = root / "scripts"
        for verifier_path in sorted(scripts_dir.glob("verify_ultimate_ai_agent_v0_*.py")):
            failures.append(f"scripts historical verifier must be archived: scripts/{verifier_path.name}")

        pyproject_text = _read(root / "pyproject.toml")
        for stale_fragment in [
            "verify_ultimate_ai_agent_v0_5_4.py",
            "scripts/verify_ultimate_ai_agent_v0_5_6.py",
            "scripts/verify_ultimate_ai_agent_v0_5_8.py",
        ]:
            if stale_fragment in pyproject_text:
                failures.append(f"pyproject.toml has stale historical verifier exclude: {stale_fragment}")

        for version_key in ["v0_5_4", "v0_5_5", "v0_5_6", "v0_5_8"]:
            archived = root / f"docs/archive/releases/{version_key}/legacy_verifier_{version_key}.py"
            if not archived.exists():
                failures.append(f"missing archived historical verifier: {archived.relative_to(root).as_posix()}")
            else:
                archived_text = _read(archived).lower()
                if "historical verifier" not in archived_text or "not part of current validation" not in archived_text:
                    failures.append(f"archived historical verifier must be clearly marked historical: {archived.relative_to(root).as_posix()}")

        active_script_text = "\n".join(
            _read(path)
            for path in root.glob("scripts/*.py")
            if not path.name.startswith("verify_ultimate_ai_agent_v0_")
            and path.name != "verify_documentation_integrity.py"
        )
        for root_artifact in [
            "README_IMPORT_v0_5_4.md",
            "ultimate_ai_agent_master_plan_v0_5_4.md",
        ]:
            if root_artifact in active_script_text:
                failures.append(f"active verifier scripts must not depend on root v0.5.4 artifact: {root_artifact}")

    forbidden_active_claims = [
        "web search is implemented",
        "external verification is implemented",
        "truth verification route is implemented",
        "claim verification route is implemented",
    ]
    if _version_tuple(version) < (0, 30, 0):
        forbidden_active_claims.extend(
            [
                "m26 is implemented",
                "m26 has implemented",
                "grounded recall router is implemented",
                "context pack builder is implemented",
            ]
        )
    for claim in forbidden_active_claims:
        if claim in active_docs:
            failures.append(f"active docs must not claim future/runtime truth capability: {claim}")

    return failures


def _verify_mobile_companion_contract_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_MOBILE_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    mobile_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_MOBILE_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "mobile docs must say M19 is contract/API planning only": "contract/api planning only",
        "mobile docs must mention iOS": "ios",
        "mobile docs must mention Android": "android",
        "mobile docs must say no mobile app": "no mobile app",
        "mobile docs must say no Android app": "no android app",
        "mobile docs must say no iOS app": "no ios app",
        "mobile docs must say no native build workflow": "no native build workflow",
        "mobile docs must say no OS permission integration": "no os permission integration",
        "mobile docs must say no mobile sensor access": "no mobile sensor access",
        "mobile docs must say Device Capability Broker is required before sensors": (
            "device capability broker is required before sensors"
        ),
        "mobile docs must say capture cannot silently become memory": (
            "capture cannot silently become memory"
        ),
        "mobile docs must say phone/mobile is not the agent brain": "phone/mobile is not the agent brain",
        "mobile docs must say phone output is not trusted control input": (
            "phone output is not trusted control input"
        ),
        "mobile docs must say no native build workflow is added": "no native build workflow is added",
    }
    if _version_tuple(version) >= (0, 25, 0):
        expectations["mobile docs must say M20 is contract-only"] = (
            "m20 device capability broker contract as contract-only"
        )
    elif _version_tuple(version) >= (0, 24, 0):
        expectations["mobile docs must say M20 is contract-only"] = (
            "m20 device capability broker contract as contract-only"
        )
        expectations["mobile docs must keep M21 planned/provisional"] = "m21 remains planned/provisional"
    else:
        expectations["mobile docs must say M20 remains planned"] = "m20 remains planned"
    for failure, fragment in expectations.items():
        if fragment not in mobile_text:
            failures.append(failure)

    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    sequence = _read(sequence_path).lower() if sequence_path.exists() else ""
    m19_section = _milestone_section(sequence, "v0.23.0 / m19")
    m20_section = _milestone_section(sequence, "v0.24.0 / m20")
    if "status: implemented" not in m19_section:
        failures.append("roadmap sequence must mark M19/v0.23.0 as implemented")
    if _version_tuple(version) >= (0, 24, 0):
        if "status: implemented" not in m20_section:
            failures.append("roadmap sequence must mark M20/v0.24.0 as implemented")
    elif "status: planned/provisional" not in m20_section:
        failures.append("roadmap sequence must keep M20/v0.24.0 planned/provisional")

    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/canonical/09_roadmap.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    for fragment in [
        "m19",
        "contract/api planning only",
        "no mobile app",
        "no android app",
        "no ios app",
        "no native build workflow",
        "no os permission integration",
        "no mobile sensor access",
        "device capability broker is required before sensors",
        "capture cannot silently become memory",
        "phone/mobile is not the agent brain",
    ]:
        if fragment not in active_docs:
            failures.append(f"active docs missing M19 mobile boundary fragment: {fragment}")
    if _version_tuple(version) >= (0, 25, 0):
        for fragment in [
            "v0.24.0 implements m20 device capability broker contract",
            "contract-only planning and validation",
            "v0.25.0",
            "m21",
        ]:
            if fragment not in active_docs:
                failures.append(f"active docs missing M21 bridge fragment: {fragment}")
    elif _version_tuple(version) >= (0, 24, 0):
        for fragment in [
            "v0.24.0 implements m20 device capability broker contract",
            "contract-only planning and validation",
            "m21 remains planned/provisional",
        ]:
            if fragment not in active_docs:
                failures.append(f"active docs missing M20 device contract fragment: {fragment}")
    elif "m20 remains planned" not in active_docs:
        failures.append("active docs missing M19 mobile boundary fragment: m20 remains planned")

    return failures


def _verify_m20_device_capability_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 24, 0):
        return failures

    for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    device_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M20 device docs must be contract-only": "contract-only",
        "M20 device docs must say no sensor access": "no sensor access",
        "M20 device docs must say no OS permission integration": "no os permission integration",
        "M20 device docs must say no native app": "no native app",
        "M20 device docs must say no backend API route": "no backend api route",
        "M20 device docs must say no Device Capability Broker runtime implementation": (
            "no device capability broker runtime implementation"
        ),
        "M20 device docs must say capture cannot silently become memory": (
            "capture cannot silently become memory"
        ),
        "M20 device docs must say broker output is not trusted control input": (
            "device capability broker output is not trusted control input by default"
        ),
        "M20 device docs must block external sends": "external sends are not allowed",
        "M20 device docs must say no capabilities are enabled": "no capabilities are enabled",
        "M20 device docs must say no capabilities are implemented": "no capabilities are implemented",
        "M20 device docs must say raw payloads are blocked": "raw payloads are blocked",
        "M20 device docs must say user gesture is future contract metadata": (
            "user gesture is future contract metadata"
        ),
        "M20 device docs must say notification runtime is blocked": "notification runtime is blocked",
        "M20 device docs must say background services are blocked": "background services are blocked",
        "M20 device docs must say device pairing runtime is future": "device pairing runtime is future",
        "M20 device docs must say receipts remain redacted": "receipts remain redacted",
    }
    if _version_tuple(version) >= (0, 25, 0):
        expectations["M20 device docs must mention M21"] = "m21"
    else:
        expectations["M20 device docs must mention M21 remains planned/provisional"] = (
            "m21 remains planned/provisional"
        )
    for failure, fragment in expectations.items():
        if fragment not in device_text:
            failures.append(f"{failure}: docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md")

    active_roadmaps = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        if (root / rel_path).exists()
    )
    m20_released = re.search(r"v0\.24\.0\s*/\s*m20[^\n]*(implemented|released)", active_roadmaps)
    if _version_tuple(version) >= (0, 26, 0):
        m21_current = re.search(
            r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_current = re.search(
            r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_planned = True
        m21_planned = True
    elif _version_tuple(version) >= (0, 25, 0):
        m21_current = re.search(
            r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_current = True
        m22_planned = re.search(
            r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*planned/provisional",
            active_roadmaps,
        )
        m21_planned = True
    else:
        m21_current = True
        m22_current = True
        m22_planned = True
        m21_planned = re.search(r"v0\.25\.0\s*/\s*m21[^\n]*planned/provisional", active_roadmaps)
    if not m20_released:
        failures.append("active roadmap docs must mark M20/v0.24.0 as implemented/released")
    if not m21_planned:
        failures.append("active roadmap docs must keep M21/v0.25.0 planned/provisional")
    if _version_tuple(version) >= (0, 25, 0):
        if not m21_current:
            failures.append("active roadmap docs must mark M21/v0.25.0 as implemented/released")
        if _version_tuple(version) >= (0, 26, 0):
            if not m22_current:
                failures.append("active roadmap docs must mark M22/v0.26.0 as implemented/released")
        elif not m22_planned:
            failures.append("active roadmap docs must keep M22/v0.26.0 planned/provisional")

    linked_docs_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        if (root / rel_path).exists()
    )
    for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS:
        if rel_path.lower() not in linked_docs_text:
            failures.append(f"device capability docs must be linked from active indexes: {rel_path}")

    forbidden_claims = [
        "openwebui integration is implemented",
        "mobile app is implemented",
        "android app is implemented",
        "ios app is implemented",
        "macos app is implemented",
        "sensor access is implemented",
        "os permission integration is implemented",
    ]
    if _version_tuple(version) < (0, 25, 0):
        forbidden_claims.extend(["m21 is implemented", "m21 has implemented"])
    for claim in forbidden_claims:
        if claim in active_roadmaps:
            failures.append(f"active roadmap docs must not claim future M21/native capability implementation: {claim}")

    return failures


def _verify_post_m20_roadmap_projection(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_POST_M20_ROADMAP_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    roadmap_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_POST_M20_ROADMAP_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "Post-M20 roadmap docs must mention M21": "m21",
        "Post-M20 roadmap docs must mention M22": "m22",
        "Post-M20 roadmap docs must mention M23": "m23",
        "Post-M20 roadmap docs must mention M24": "m24",
        "Post-M20 roadmap docs must mention M25": "m25",
        "Post-M20 roadmap docs must mention M26": "m26",
        "Post-M20 roadmap docs must mention M27": "m27",
        "Post-M20 roadmap docs must mention M28": "m28",
        "Post-M20 roadmap docs must mention M29": "m29",
        "Post-M20 roadmap docs must mention M30": "m30",
        "Post-M20 roadmap docs must mention M31": "m31",
        "Post-M20 roadmap docs must mention M32": "m32",
        "Post-M20 roadmap docs must mention M33": "m33",
        "Post-M20 roadmap docs must mention M34": "m34",
        "Post-M20 roadmap docs must mention M35": "m35",
        "Post-M20 roadmap docs must mention M36": "m36",
        "Post-M20 roadmap docs must mention M37": "m37",
        "Post-M20 roadmap docs must mention M38": "m38",
        "Post-M20 roadmap docs must mention M39": "m39",
        "Post-M20 roadmap docs must mention M40": "m40",
        "M21 must be OpenWebUI Bridge + Chat Shell Integration Contract": (
            "openwebui bridge + chat shell integration contract"
        ),
        "M22 must be Local Model Runtime Activation Contract": "local model runtime activation contract",
        "M23 must be First Real Local LLM Call": "first real local llm call",
        "M24 must be Memory Provider Abstraction": "memory provider abstraction",
        "M26 must be Grounded Recall Router + Evidence-Linked Context Pack Builder": (
            "grounded recall router + evidence-linked context pack builder"
        ),
        "M27 must be Tool Broker v2 + Safe Tool Intent Contracts": (
            "tool broker v2 + safe tool intent contracts"
        ),
        "M28 must be Approval Authority v2 + Action Policy Expansion": (
            "approval authority v2 + action policy expansion"
        ),
        "M31 must be Real Tool Runtime Adapter, Single Safe No-Op Tool": (
            "real tool runtime adapter, single safe no-op tool"
        ),
        "M32 must be Safe Local Filesystem Metadata Tool": (
            "safe local filesystem metadata tool"
        ),
        "Post-M20 roadmap docs must say planned/provisional": "planned/provisional",
        "Post-M20 roadmap docs must say no integration is added": "no integration",
        "Post-M20 roadmap docs must say no dependency is added": "no dependency",
    }
    active_version_tuple = _version_tuple(_active_version(root))
    if active_version_tuple >= (0, 37, 4):
        expectations["M35 must be Safe File Review Workflow Contracts"] = (
            "safe file review workflow contracts"
        )
        expectations["M38 must be Safe Context Proposal From Approved Review"] = (
            "safe context proposal from approved review"
        )
        expectations["M39 must be CCC Context Proposal Surface"] = "ccc context proposal surface"
        expectations["M40 must be Context Handoff Approval, No Injection"] = (
            "context handoff approval, no injection"
        )
        if active_version_tuple >= (0, 42, 0):
            expectations["Post-M20 roadmap docs must say M38 is implemented/released"] = (
                "m38 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M39-M60 planned/provisional"] = (
                "m39-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 41, 0):
            expectations["Post-M20 roadmap docs must say M37 is implemented/released"] = (
                "m37 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M38-M60 planned/provisional"] = (
                "m38-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 40, 0):
            expectations["Post-M20 roadmap docs must say M36 is implemented/released"] = (
                "m36 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M37-M60 planned/provisional"] = (
                "m37-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 38, 0):
            expectations["Post-M20 roadmap docs must say M34 is implemented/released"] = (
                "m34 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M36-M60 planned/provisional"] = (
                "m36-m60 remain planned/provisional"
            )
        else:
            expectations["Post-M20 roadmap docs must keep M34-M60 planned/provisional"] = (
                "m34-m60 remain planned/provisional"
            )
        expectations["Post-M20 roadmap docs must mention M60"] = "m60"
        expectations["Post-M20 roadmap docs must say M31 is implemented/released"] = (
            "m31 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M32 is implemented/released"] = (
            "m32 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M33 is implemented/released"] = (
            "m33 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M33 redacted preview"] = (
            "redacted preview"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M30 is implemented/released"] = (
            "m30 is implemented/released"
        )
    elif active_version_tuple >= (0, 37, 0):
        expectations["M35 must mention Device Capability Broker Implementation, No Sensors"] = (
            "device capability broker implementation, no sensors"
        )
        expectations["M38 must be Browser Automation Contract, No Execution"] = "browser automation contract, no execution"
        expectations["M39 must be Observability Export Adapters"] = "observability export adapters"
        expectations["M40 must be Agent Evaluation + Regression Harness"] = "agent evaluation + regression harness"
        expectations["Post-M20 roadmap docs must say M31 is implemented/released"] = (
            "m31 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M32 is implemented/released"] = (
            "m32 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M33 is implemented/released"] = (
            "m33 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M33 redacted preview"] = (
            "redacted preview"
        )
        expectations["Post-M20 roadmap docs must keep M34-M40 planned/provisional"] = (
            "m34-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M30 is implemented/released"] = (
            "m30 is implemented/released"
        )
    elif active_version_tuple >= (0, 36, 0):
        expectations["Post-M20 roadmap docs must say M31 is implemented/released"] = (
            "m31 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M32 is implemented/released"] = (
            "m32 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must keep M33-M40 planned/provisional"] = (
            "m33-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M30 is implemented/released"] = (
            "m30 is implemented/released"
        )
    elif active_version_tuple >= (0, 35, 0):
        expectations["Post-M20 roadmap docs must say M31 is implemented/released"] = (
            "m31 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must keep M32-M40 planned/provisional"] = (
            "m32-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M30 is implemented/released"] = (
            "m30 is implemented/released"
        )
    elif active_version_tuple >= (0, 34, 0):
        expectations["Post-M20 roadmap docs must keep M31-M40 planned/provisional"] = (
            "m31-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
        expectations["Post-M20 roadmap docs must say M30 is implemented/released"] = (
            "m30 is implemented/released"
        )
        expectations["M30 must be Multi-Step Execution Framework"] = "multi-step execution framework"
    elif active_version_tuple >= (0, 33, 0):
        expectations["Post-M20 roadmap docs must keep M30-M40 planned/provisional"] = (
            "m30-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M29 is implemented/released"] = (
            "m29 is implemented/released"
        )
    elif active_version_tuple >= (0, 32, 0):
        expectations["Post-M20 roadmap docs must keep M29-M40 planned/provisional"] = (
            "m29-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M28 is implemented/released"] = (
            "m28 is implemented/released"
        )
    elif active_version_tuple >= (0, 31, 0):
        expectations["Post-M20 roadmap docs must keep M28-M40 planned/provisional"] = (
            "m28-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M27 is implemented/released"] = (
            "m27 is implemented/released"
        )
    elif active_version_tuple >= (0, 30, 0):
        expectations["Post-M20 roadmap docs must keep M27-M40 planned/provisional"] = (
            "m27-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M26 is implemented/released"] = (
            "m26 is implemented/released"
        )
    elif active_version_tuple >= (0, 29, 0):
        expectations["Post-M20 roadmap docs must keep M26-M40 planned/provisional"] = (
            "m26-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M25 is implemented/released"] = (
            "m25 is implemented/released"
        )
    elif active_version_tuple >= (0, 28, 0):
        expectations["Post-M20 roadmap docs must keep M25-M40 planned/provisional"] = (
            "m25-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M24 is implemented/released"] = (
            "m24 is implemented/released"
        )
    elif active_version_tuple >= (0, 27, 0):
        expectations["Post-M20 roadmap docs must keep M24-M40 planned/provisional"] = (
            "m24-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M23 is implemented/released"] = (
            "m23 is implemented/released"
        )
    elif active_version_tuple >= (0, 26, 0):
        expectations["Post-M20 roadmap docs must keep M23-M40 planned/provisional"] = (
            "m23-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M22 is implemented/released"] = (
            "m22 is implemented/released"
        )
    elif active_version_tuple >= (0, 25, 0):
        expectations["Post-M20 roadmap docs must keep M22-M40 planned/provisional"] = (
            "m22-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M21 is implemented/released"] = (
            "m21 is implemented/released"
        )
    else:
        expectations["Post-M20 roadmap docs must say no implementation is added"] = "no implementation"
    for failure, fragment in expectations.items():
        if fragment not in roadmap_text:
            failures.append(failure)

    if active_version_tuple >= (0, 42, 0):
        implemented_claim_start = 39
    elif active_version_tuple >= (0, 41, 0):
        implemented_claim_start = 38
    elif active_version_tuple >= (0, 40, 0):
        implemented_claim_start = 37
    elif active_version_tuple >= (0, 39, 0):
        implemented_claim_start = 36
    elif active_version_tuple >= (0, 38, 0):
        implemented_claim_start = 35
    elif active_version_tuple >= (0, 37, 0):
        implemented_claim_start = 34
    elif active_version_tuple >= (0, 36, 0):
        implemented_claim_start = 33
    elif active_version_tuple >= (0, 35, 0):
        implemented_claim_start = 32
    elif active_version_tuple >= (0, 34, 0):
        implemented_claim_start = 31
    elif active_version_tuple >= (0, 33, 0):
        implemented_claim_start = 30
    elif active_version_tuple >= (0, 32, 0):
        implemented_claim_start = 29
    elif active_version_tuple >= (0, 31, 0):
        implemented_claim_start = 28
    elif active_version_tuple >= (0, 30, 0):
        implemented_claim_start = 27
    elif active_version_tuple >= (0, 29, 0):
        implemented_claim_start = 26
    elif active_version_tuple >= (0, 28, 0):
        implemented_claim_start = 25
    elif active_version_tuple >= (0, 27, 0):
        implemented_claim_start = 24
    elif active_version_tuple >= (0, 26, 0):
        implemented_claim_start = 23
    elif active_version_tuple >= (0, 25, 0):
        implemented_claim_start = 22
    else:
        implemented_claim_start = 21
    implemented_claims = [
        f"m{number} is implemented" for number in range(implemented_claim_start, 41)
    ] + [
        "m21-m40 are implemented",
        "m21 through m40 are implemented",
        "post-m20 capabilities are implemented",
    ]
    if any(claim in roadmap_text for claim in implemented_claims):
        failures.append("M21-M40 docs must not claim implementation")

    return failures


def _verify_roadmap_milestone_charters(root: Path) -> list[str]:
    failures: list[str] = []
    charter_path = root / "docs/roadmap/MILESTONE_CHARTERS.md"
    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    if not charter_path.exists():
        failures.append("missing roadmap milestone charter doc: docs/roadmap/MILESTONE_CHARTERS.md")
    if not sequence_path.exists():
        failures.append("missing roadmap next sequence doc: docs/roadmap/NEXT_SEQUENCE_v0_17_5.md")
    if failures:
        return failures

    charter = _read(charter_path).lower()
    sequence = _read(sequence_path).lower()
    required_fields = [
        "version",
        "milestone code",
        "title",
        "status",
        "purpose",
        "allowed scope",
        "must not add",
        "dependencies",
        "acceptance criteria",
        "review prompt required",
        "hardening patch expectation",
        "source-of-truth docs",
        "notes",
    ]
    for field in required_fields:
        if field not in charter:
            failures.append(f"milestone charter template missing field: {field}")

    if "m14" not in sequence or "web control center local backend connection stabilization" not in sequence:
        failures.append("roadmap sequence must define M14 as Web Control Center Local Backend Connection Stabilization")
    if "m15" not in sequence or "approval queue + receipt/event viewer ui" not in sequence:
        failures.append("roadmap sequence must define M15 as Approval Queue + Receipt/Event Viewer UI")
    if "v0.17.4" not in sequence or "local browser smoke" not in sequence or "not m14" not in sequence:
        failures.append("roadmap sequence must keep v0.17.4 as local browser smoke / UX polish, not M14")

    forbidden_m14_smoke_patterns = [
        "m14 - local browser smoke",
        "m14 — local browser smoke",
        "m14: local browser smoke",
        "m14 - web control center local browser smoke",
        "m14 — web control center local browser smoke",
        "m14: web control center local browser smoke",
        "m14 - ux polish",
        "m14 — ux polish",
        "m14: ux polish",
    ]
    if any(pattern in sequence for pattern in forbidden_m14_smoke_patterns):
        failures.append("M14 must not be local browser smoke / UX polish")

    if _version_tuple(_active_version(root)) < (0, 19, 0):
        implemented_m15_claims = [
            "m15 is implemented",
            "m15 has been implemented",
            "implemented m15",
            "m15 implementation complete",
            "approval queue is implemented",
            "receipt/event viewer ui is implemented",
        ]
        for rel_path in ACTIVE_DOCS_TO_SCAN:
            path = root / rel_path
            if not path.exists():
                continue
            lowered = _read(path).lower()
            for claim in implemented_m15_claims:
                if claim in lowered:
                    failures.append(f"active docs claim M15 is already implemented: {rel_path}")
    else:
        docs_text = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in [
                "docs/control_center/APPROVAL_QUEUE_UI.md",
                "docs/control_center/RECEIPT_EVENT_VIEWER.md",
                "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
            ]
            if (root / rel_path).exists()
        )
        for fragment in [
            "read-only",
            "preview-only",
            "redacted",
            "no backend route",
            "approval authority remains",
        ]:
            if fragment not in docs_text:
                failures.append(f"M15 active docs missing safety fragment: {fragment}")
    return failures


def _verify_post_m18_roadmap_status_labels(root: Path) -> list[str]:
    active = _version_tuple(_active_version(root))
    if active < (0, 22, 1):
        return []

    failures: list[str] = []
    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    roadmap_path = root / "docs/canonical/09_roadmap.md"
    if not sequence_path.exists() or not roadmap_path.exists():
        return failures

    sequence = _read(sequence_path).lower()
    roadmap = _read(roadmap_path).lower()
    active_capability_charters = _read(root / "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md").lower()
    m18_section = _milestone_section(sequence, "v0.22.0 / m18")
    if not m18_section or "status: implemented" not in m18_section:
        failures.append("roadmap sequence must mark M18/v0.22.0 as implemented after accepted v0.22.0")
    if "v0.22.0 has implemented m18" not in roadmap:
        failures.append("canonical roadmap must mention accepted M18 implementation after v0.22.0")
    milestone_expectations = {
        "v0.23.0 / m19": "implemented",
        "v0.24.0 / m20": "implemented" if active >= (0, 24, 0) else "planned/provisional",
    }
    for milestone, expected_status in milestone_expectations.items():
        section = _milestone_section(sequence, milestone)
        if not section:
            failures.append(f"roadmap sequence missing {milestone.upper()} status")
            continue
        if f"status: {expected_status}" not in section:
            failures.append(f"roadmap sequence must mark {milestone.upper()} {expected_status}")
    if active >= (0, 37, 0):
        if "v0.37.0 / m33" not in active_capability_charters or "status: implemented" not in active_capability_charters:
            failures.append("roadmap sequence must mark M33/v0.37.0 implemented")
        if active >= (0, 37, 1) and "v0.37.1 / m33 hardening" not in active_capability_charters:
            failures.append("roadmap sequence must mark M33/v0.37.1 hardening implemented")
        if active >= (0, 37, 2) and "v0.37.2 / local developer launcher" not in active_capability_charters:
            failures.append("roadmap sequence must mark v0.37.2 local developer launcher implemented")
        if active >= (0, 37, 3) and "v0.37.3 / roadmap label alignment" not in active_capability_charters:
            failures.append("roadmap sequence must mark v0.37.3 roadmap label alignment implemented")
        if active >= (0, 37, 4) and "v0.37.4 / roadmap supersession through m60" not in active_capability_charters:
            failures.append("roadmap sequence must mark v0.37.4 roadmap supersession implemented")
        if (
            "first safe local file read proposal" not in active_capability_charters
            or "redacted preview" not in active_capability_charters
        ):
            failures.append("roadmap sequence must define M33 as redacted file preview")
        if active >= (0, 42, 0):
            if "v0.42.0 / m38" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M38/v0.42.0 implemented")
            if "m39-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M39-M60 planned/provisional")
        elif active >= (0, 41, 0):
            if "v0.41.0 / m37" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M37/v0.41.0 implemented")
            if "m38-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M38-M60 planned/provisional")
        elif active >= (0, 40, 0):
            if "v0.40.0 / m36" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M36/v0.40.0 implemented")
            if "m37-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M37-M60 planned/provisional")
        elif active >= (0, 39, 0):
            if "v0.39.0 / m35" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M35/v0.39.0 implemented")
            if active >= (0, 39, 1) and "v0.39.1 / m35 hardening" not in active_capability_charters:
                failures.append("roadmap sequence must mark v0.39.1 M35 hardening implemented")
            if "m36-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M36-M60 planned/provisional")
        elif active >= (0, 38, 0):
            if "v0.38.0 / m34" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M34/v0.38.0 implemented")
            if "m35-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M36-M60 planned/provisional")
        elif active >= (0, 37, 4):
            if "m34-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M34-M60 planned/provisional")
        elif "m34-m40" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
            failures.append("roadmap sequence must keep M34-M40 planned/provisional")
    elif active >= (0, 35, 0):
        if "m31" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M31/v0.35.0 implemented")
        if "real tool runtime adapter" not in sequence:
            failures.append("roadmap sequence must define M31 as Real Tool Runtime Adapter")
        if "m32-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M32-M40 planned/provisional")
    elif active >= (0, 34, 0):
        if "m30" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M30/v0.34.0 implemented")
        if "multi-step execution framework" not in sequence:
            failures.append("roadmap sequence must define M30 as Multi-Step Execution Framework")
        if "m31-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M31-M40 planned/provisional")
    elif active >= (0, 33, 0):
        if "m29" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M29/v0.33.0 implemented")
        if "m30-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M30-M40 planned/provisional")
    elif active >= (0, 32, 0):
        if "m28" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M28/v0.32.0 implemented")
        if "m29-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M29-M40 planned/provisional")
    elif active >= (0, 31, 0):
        if "m27" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M27/v0.31.0 implemented")
        if "m28-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M28-M40 planned/provisional")
    elif active >= (0, 30, 0):
        if "m26" not in sequence or "status: implemented" not in sequence:
            failures.append("roadmap sequence must mark M26/v0.30.0 implemented")
        if "m27-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M27-M40 planned/provisional")
    elif active >= (0, 29, 0):
        if "m26-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M26-M40 planned/provisional")
    elif active >= (0, 28, 0):
        if "m25-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M25-M40 planned/provisional")
    elif active >= (0, 27, 0):
        if "m24-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M24-M40 planned/provisional")
    elif active >= (0, 26, 0):
        if "m23-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M23-M40 planned/provisional")
    elif active >= (0, 25, 0):
        if "m22-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M22-M40 planned/provisional")
    elif "m21-m40 remain planned/provisional" not in sequence:
        failures.append("roadmap sequence must keep M21-M40 planned/provisional")
    return failures


def _milestone_section(text: str, milestone: str) -> str:
    heading_marker = "## "
    index = text.find(f"{heading_marker}{milestone}")
    if index == -1:
        index = text.find(f"{heading_marker}")
        while index != -1 and milestone not in text[index : text.find("\n", index) if text.find("\n", index) != -1 else None]:
            index = text.find(f"{heading_marker}", index + len(heading_marker))
    if index == -1:
        return ""
    next_heading = text.find("##", index + 1)
    return text[index : next_heading if next_heading != -1 else None]


def main() -> int:
    print("=== Ultimate AI Agent Documentation Integrity Verification ===")
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Documentation integrity verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
