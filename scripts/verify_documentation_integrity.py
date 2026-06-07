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

REQUIRED_M39_CONTEXT_PROPOSAL_SURFACE_DOCS = [
    "docs/control_center/CONTEXT_PROPOSAL_SURFACE.md",
    "docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md",
    "docs/control_center/CONTEXT_PROPOSAL_MOCK_DATA_POLICY.md",
    "docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md",
    "docs/control_center/M39_TO_M40_BOUNDARY.md",
]

REQUIRED_M40_CONTEXT_HANDOFF_APPROVAL_DOCS = [
    "docs/context/CONTEXT_HANDOFF_APPROVAL.md",
    "docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md",
    "docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md",
    "docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md",
    "docs/context/M40_TO_M41_BOUNDARY.md",
]

REQUIRED_M41_LOCAL_PROTOTYPE_SAFETY_DOCS = [
    "docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md",
    "docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md",
    "docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md",
    "docs/prototype/M41_TO_M42_BOUNDARY.md",
]

REQUIRED_M48_FIRST_INTERNAL_TESTFLIGHT_BUILD_DOCS = [
    "docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md",
    "docs/mobile/M48_TO_M49_BOUNDARY.md",
    "docs/release_notes/v0_52_0.md",
    "docs/archive/releases/v0_52_0/README_IMPORT.md",
    "docs/archive/releases/v0_52_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_52_0.md",
]

REQUIRED_M49_MOBILE_REVIEW_APPROVAL_CAPTURE_DOCS = [
    "docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md",
    "docs/mobile/M49_TO_M50_BOUNDARY.md",
    "docs/release_notes/v0_53_0.md",
    "docs/archive/releases/v0_53_0/README_IMPORT.md",
    "docs/archive/releases/v0_53_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_53_0.md",
]

REQUIRED_M50_MOBILE_APPROVAL_AUDIT_DOCS = [
    "docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md",
    "docs/mobile/M50_TO_M51_BOUNDARY.md",
    "docs/release_notes/v0_54_0.md",
    "docs/archive/releases/v0_54_0/README_IMPORT.md",
    "docs/archive/releases/v0_54_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_54_0.md",
]

REQUIRED_M51_OPENWEBUI_BRIDGE_ADAPTER_DOCS = [
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md",
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md",
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/M51_TO_M52_BOUNDARY.md",
    "docs/release_notes/v0_55_0.md",
    "docs/archive/releases/v0_55_0/README_IMPORT.md",
    "docs/archive/releases/v0_55_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_55_0.md",
]

REQUIRED_M52_OPENWEBUI_SAFE_CONVERSATION_DOCS = [
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md",
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md",
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/M52_TO_M53_BOUNDARY.md",
    "docs/release_notes/v0_56_0.md",
    "docs/archive/releases/v0_56_0/README_IMPORT.md",
    "docs/archive/releases/v0_56_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_56_0.md",
]

REQUIRED_M53_CONTROLLED_TOOL_EXPANSION_DOCS = [
    "docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md",
    "docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md",
    "docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
    "docs/tools/M53_TO_M54_BOUNDARY.md",
    "docs/release_notes/v0_57_0.md",
    "docs/archive/releases/v0_57_0/README_IMPORT.md",
    "docs/archive/releases/v0_57_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_57_0.md",
]

REQUIRED_M54_SAFE_MEDIA_METADATA_DOCS = [
    "docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md",
    "docs/media/SAFE_MEDIA_METADATA_POLICY.md",
    "docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md",
    "docs/media/M54_TO_M55_BOUNDARY.md",
    "docs/release_notes/v0_58_0.md",
    "docs/archive/releases/v0_58_0/README_IMPORT.md",
    "docs/archive/releases/v0_58_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_58_0.md",
]

REQUIRED_M55_REDACTED_OBSERVABILITY_DOCS = [
    "docs/canonical/63_observability_standards_mapping.md",
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT.md",
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md",
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md",
    "docs/observability/M55_TO_M56_BOUNDARY.md",
    "docs/release_notes/v0_59_0.md",
    "docs/archive/releases/v0_59_0/README_IMPORT.md",
    "docs/archive/releases/v0_59_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_59_0.md",
]

REQUIRED_M56_AGENT_EVAL_DOCS = [
    "docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md",
    "docs/evals/AGENT_EVAL_REGRESSION_POLICY.md",
    "docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md",
    "docs/evals/M56_TO_M57_BOUNDARY.md",
    "docs/release_notes/v0_60_0.md",
    "docs/archive/releases/v0_60_0/README_IMPORT.md",
    "docs/archive/releases/v0_60_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_60_0.md",
]

REQUIRED_M57_RUNTIME_SANDBOX_DOCS = [
    "docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md",
    "docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md",
    "docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/M57_TO_M58_BOUNDARY.md",
    "docs/release_notes/v0_61_0.md",
    "docs/archive/releases/v0_61_0/README_IMPORT.md",
    "docs/archive/releases/v0_61_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_61_0.md",
]

REQUIRED_M58_DRY_RUN_AUDIT_DOCS = [
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md",
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md",
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/dry_run_audit/M58_TO_M59_BOUNDARY.md",
    "docs/release_notes/v0_62_0.md",
    "docs/archive/releases/v0_62_0/README_IMPORT.md",
    "docs/archive/releases/v0_62_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_62_0.md",
]

REQUIRED_M59_PUBLIC_GITHUB_READINESS_DOCS = [
    "docs/public_readiness/PUBLIC_GITHUB_READINESS.md",
    "docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md",
    "docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md",
    "docs/public_readiness/M59_TO_M60_BOUNDARY.md",
    "docs/release_notes/v0_63_0.md",
    "docs/archive/releases/v0_63_0/README_IMPORT.md",
    "docs/archive/releases/v0_63_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_63_0.md",
]

REQUIRED_M60_LOCAL_DEVELOPER_BETA_FREEZE_DOCS = [
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md",
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md",
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/beta/POST_M60_AUTONOMY_BOUNDARY.md",
    "docs/release_notes/v0_64_0.md",
    "docs/archive/releases/v0_64_0/README_IMPORT.md",
    "docs/archive/releases/v0_64_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_64_0.md",
]

REQUIRED_M61_AUTONOMY_MODE_CHARTER_DOCS = [
    "docs/autonomy/AUTONOMY_MODE_CHARTER.md",
    "docs/autonomy/AUTHORITY_LEVELS.md",
    "docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md",
    "docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md",
    "docs/autonomy/M61_TO_M62_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_65_0.md",
    "docs/archive/releases/v0_65_0/README_IMPORT.md",
    "docs/archive/releases/v0_65_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_65_0.md",
]

REQUIRED_M62_SCOPED_AUTONOMY_SESSION_DOCS = [
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md",
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md",
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md",
    "docs/autonomy/M62_TO_M63_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_66_0.md",
    "docs/archive/releases/v0_66_0/README_IMPORT.md",
    "docs/archive/releases/v0_66_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_66_0.md",
]

REQUIRED_M63_AUTONOMY_POLICY_ENGINE_DOCS = [
    "docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md",
    "docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md",
    "docs/autonomy/M63_TO_M64_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_67_0.md",
    "docs/archive/releases/v0_67_0/README_IMPORT.md",
    "docs/archive/releases/v0_67_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_67_0.md",
]

REQUIRED_M64_AUTONOMOUS_PLAN_SIMULATOR_DOCS = [
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md",
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md",
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md",
    "docs/autonomy/M64_TO_M65_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_68_0.md",
    "docs/archive/releases/v0_68_0/README_IMPORT.md",
    "docs/archive/releases/v0_68_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_68_0.md",
]

REQUIRED_M65_AUTONOMY_AUDIT_REPLAY_VIEWER_DOCS = [
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md",
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md",
    "docs/autonomy/M65_TO_M66_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_69_0.md",
    "docs/archive/releases/v0_69_0/README_IMPORT.md",
    "docs/archive/releases/v0_69_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_69_0.md",
]

REQUIRED_M66_SCOPED_APPROVAL_BUNDLE_DOCS = [
    "docs/autonomy/SCOPED_APPROVAL_BUNDLES.md",
    "docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md",
    "docs/autonomy/SCOPED_APPROVAL_BUNDLE_NON_GOALS.md",
    "docs/autonomy/M66_TO_M67_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_70_0.md",
    "docs/archive/releases/v0_70_0/README_IMPORT.md",
    "docs/archive/releases/v0_70_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_70_0.md",
]

REQUIRED_M67_REVOCATION_KILL_SWITCH_DOCS = [
    "docs/autonomy/REVOCATION_KILL_SWITCH.md",
    "docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md",
    "docs/autonomy/REVOCATION_KILL_SWITCH_NON_GOALS.md",
    "docs/autonomy/M67_TO_M68_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_71_0.md",
    "docs/archive/releases/v0_71_0/README_IMPORT.md",
    "docs/archive/releases/v0_71_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_71_0.md",
]

REQUIRED_M68_AUTONOMY_RISK_CLASSIFIER_DOCS = [
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md",
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_NON_GOALS.md",
    "docs/autonomy/M68_TO_M69_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_72_0.md",
    "docs/archive/releases/v0_72_0/README_IMPORT.md",
    "docs/archive/releases/v0_72_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_72_0.md",
]

REQUIRED_M69_LOW_RISK_AUTONOMOUS_DRY_RUN_DOCS = [
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md",
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md",
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_NON_GOALS.md",
    "docs/autonomy/M69_TO_M70_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_73_0.md",
    "docs/archive/releases/v0_73_0/README_IMPORT.md",
    "docs/archive/releases/v0_73_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_73_0.md",
]

REQUIRED_M70_AUTONOMY_FOUNDATION_FREEZE_DOCS = [
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md",
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_NON_GOALS.md",
    "docs/autonomy/M70_TO_M71_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_74_0.md",
    "docs/archive/releases/v0_74_0/README_IMPORT.md",
    "docs/archive/releases/v0_74_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_74_0.md",
]

REQUIRED_M71_NETWORK_TOOL_CONTRACT_REVIEW_DOCS = [
    "docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md",
    "docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md",
    "docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md",
    "docs/network/M71_TO_M72_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_75_0.md",
    "docs/archive/releases/v0_75_0/README_IMPORT.md",
    "docs/archive/releases/v0_75_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_75_0.md",
]

REQUIRED_M72_READ_ONLY_HTTP_FETCH_DOCS = [
    "docs/network/READ_ONLY_HTTP_FETCH_TOOL.md",
    "docs/network/READ_ONLY_HTTP_FETCH_POLICY.md",
    "docs/network/READ_ONLY_HTTP_FETCH_AUTHORITY_BOUNDARY.md",
    "docs/network/READ_ONLY_HTTP_FETCH_RECEIPT_PLAN.md",
    "docs/network/M72_TO_M73_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_76_0.md",
    "docs/archive/releases/v0_76_0/README_IMPORT.md",
    "docs/archive/releases/v0_76_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_76_0.md",
]

REQUIRED_M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_DOCS = [
    "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW.md",
    "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW_POLICY.md",
    "docs/browser/BROWSER_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_AUTOMATION_RECEIPT_PLAN.md",
    "docs/browser/M73_TO_M74_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_77_0.md",
    "docs/archive/releases/v0_77_0/README_IMPORT.md",
    "docs/archive/releases/v0_77_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_77_0.md",
]

REQUIRED_M74_BROWSER_OBSERVE_ONLY_DOCS = [
    "docs/browser/BROWSER_OBSERVE_ONLY_ADAPTER.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_POLICY.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_RESULT_CONTRACT.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_RECEIPT_PLAN.md",
    "docs/browser/M74_TO_M75_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_78_0.md",
    "docs/archive/releases/v0_78_0/README_IMPORT.md",
    "docs/archive/releases/v0_78_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_78_0.md",
]

REQUIRED_M75_BROWSER_ACTION_DRY_RUN_DOCS = [
    "docs/browser/BROWSER_ACTION_DRY_RUN_PLANNER.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_POLICY.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_RESULT_CONTRACT.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_RECEIPT_PLAN.md",
    "docs/browser/M75_TO_M76_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_79_0.md",
    "docs/archive/releases/v0_79_0/README_IMPORT.md",
    "docs/archive/releases/v0_79_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_79_0.md",
]

REQUIRED_M76_OPENWEBUI_RUNTIME_BRIDGE_DOCS = [
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_V1.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_POLICY.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RESULT_CONTRACT.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RECEIPT_PLAN.md",
    "docs/openwebui/M76_TO_M77_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_80_0.md",
    "docs/archive/releases/v0_80_0/README_IMPORT.md",
    "docs/archive/releases/v0_80_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_80_0.md",
]

REQUIRED_M77_OPENWEBUI_SAFE_HANDOFF_DOCS = [
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_EXECUTION.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RESULT_CONTRACT.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RECEIPT_PLAN.md",
    "docs/openwebui/M77_TO_M78_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_81_0.md",
    "docs/archive/releases/v0_81_0/README_IMPORT.md",
    "docs/archive/releases/v0_81_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_81_0.md",
]

REQUIRED_M78_PLUGIN_MANIFEST_SECURITY_DOCS = [
    "docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md",
    "docs/tooling/PLUGIN_MANIFEST_POLICY.md",
    "docs/tooling/PLUGIN_PERMISSION_MODEL.md",
    "docs/tooling/PLUGIN_PROVENANCE_REVIEW.md",
    "docs/tooling/PLUGIN_SANDBOX_TEST_PLAN.md",
    "docs/tooling/PLUGIN_MANIFEST_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_MANIFEST_RECEIPT_PLAN.md",
    "docs/tooling/M78_TO_M79_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_82_0.md",
    "docs/archive/releases/v0_82_0/README_IMPORT.md",
    "docs/archive/releases/v0_82_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_82_0.md",
]

REQUIRED_M79_PLUGIN_INSTALL_REVIEW_DOCS = [
    "docs/tooling/PLUGIN_INSTALL_REVIEW.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md",
    "docs/tooling/M79_TO_M80_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_83_0.md",
    "docs/archive/releases/v0_83_0/README_IMPORT.md",
    "docs/archive/releases/v0_83_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_83_0.md",
]

REQUIRED_M80_NETWORK_BROWSER_OPENWEBUI_FREEZE_DOCS = [
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE.md",
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_CONTRACTS.md",
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_NON_GOALS.md",
    "docs/hardening/M80_TO_M81_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_84_0.md",
    "docs/archive/releases/v0_84_0/README_IMPORT.md",
    "docs/archive/releases/v0_84_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_84_0.md",
]

REQUIRED_M81_RUNTIME_SANDBOX_SPEC_DOCS = [
    "docs/sandbox/RUNTIME_SANDBOX_SPEC.md",
    "docs/sandbox/RUNTIME_SANDBOX_SPEC_CONTRACTS.md",
    "docs/sandbox/RUNTIME_SANDBOX_SPEC_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/RUNTIME_SANDBOX_SPEC_NON_GOALS.md",
    "docs/sandbox/M81_TO_M82_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_85_0.md",
    "docs/archive/releases/v0_85_0/README_IMPORT.md",
    "docs/archive/releases/v0_85_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_85_0.md",
]

REQUIRED_M82_COMMAND_PROPOSAL_DOCS = [
    "docs/sandbox/COMMAND_PROPOSAL_CONTRACTS.md",
    "docs/sandbox/COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/COMMAND_PROPOSAL_RECEIPT_PLAN.md",
    "docs/sandbox/COMMAND_PROPOSAL_NON_GOALS.md",
    "docs/sandbox/M82_TO_M83_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_86_0.md",
    "docs/archive/releases/v0_86_0/README_IMPORT.md",
    "docs/archive/releases/v0_86_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_86_0.md",
]

REQUIRED_M83_SHELL_DRY_RUN_CLASSIFIER_DOCS = [
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_POLICY.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_NON_GOALS.md",
    "docs/sandbox/M83_TO_M84_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_87_0.md",
    "docs/archive/releases/v0_87_0/README_IMPORT.md",
    "docs/archive/releases/v0_87_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_87_0.md",
]

REQUIRED_M84_SANDBOXED_ECHO_NOOP_DOCS = [
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_POLICY.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_RECEIPT_PLAN.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_NON_GOALS.md",
    "docs/sandbox/M84_TO_M85_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_88_0.md",
    "docs/archive/releases/v0_88_0/README_IMPORT.md",
    "docs/archive/releases/v0_88_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_88_0.md",
]

REQUIRED_M85_READ_ONLY_COMMAND_ALLOWLIST_DOCS = [
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_POLICY.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_RECEIPT_PLAN.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_NON_GOALS.md",
    "docs/sandbox/M85_TO_M86_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_89_0.md",
    "docs/archive/releases/v0_89_0/README_IMPORT.md",
    "docs/archive/releases/v0_89_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_89_0.md",
]

REQUIRED_M86_SHELL_APPROVAL_GATE_DOCS = [
    "docs/sandbox/SHELL_APPROVAL_GATE.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_POLICY.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_NON_GOALS.md",
    "docs/sandbox/M86_TO_M87_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_90_0.md",
    "docs/archive/releases/v0_90_0/README_IMPORT.md",
    "docs/archive/releases/v0_90_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_90_0.md",
]

REQUIRED_M87_SANDBOXED_COMMAND_AUDIT_REPLAY_DOCS = [
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_POLICY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_RECEIPT_PLAN.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_NON_GOALS.md",
    "docs/sandbox/M87_TO_M88_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_91_0.md",
    "docs/archive/releases/v0_91_0/README_IMPORT.md",
    "docs/archive/releases/v0_91_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_91_0.md",
]

REQUIRED_M88_MUTATING_COMMAND_PROPOSAL_DOCS = [
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_POLICY.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_RECEIPT_PLAN.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_NON_GOALS.md",
    "docs/sandbox/M88_TO_M89_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_92_0.md",
    "docs/archive/releases/v0_92_0/README_IMPORT.md",
    "docs/archive/releases/v0_92_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_92_0.md",
]

REQUIRED_M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_DOCS = [
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_POLICY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_RECEIPT_PLAN.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_NON_GOALS.md",
    "docs/sandbox/M89_TO_M90_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_93_0.md",
    "docs/archive/releases/v0_93_0/README_IMPORT.md",
    "docs/archive/releases/v0_93_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_93_0.md",
]

REQUIRED_M90_SHELL_SUBPROCESS_HARDENING_FREEZE_DOCS = [
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_NON_GOALS.md",
    "docs/sandbox/M90_TO_M91_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_94_0.md",
    "docs/archive/releases/v0_94_0/README_IMPORT.md",
    "docs/archive/releases/v0_94_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_94_0.md",
]

REQUIRED_M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_DOCS = [
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT_POLICY.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_RECEIPT_PLAN.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_NON_GOALS.md",
    "docs/tools/M91_TO_M92_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_95_0.md",
    "docs/archive/releases/v0_95_0/README_IMPORT.md",
    "docs/archive/releases/v0_95_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_95_0.md",
]

REQUIRED_M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_DOCS = [
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_POLICY.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_RECEIPT_PLAN.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_NON_GOALS.md",
    "docs/autonomy/M92_TO_M93_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_96_0.md",
    "docs/archive/releases/v0_96_0/README_IMPORT.md",
    "docs/archive/releases/v0_96_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_96_0.md",
]

REQUIRED_M93_MULTI_TOOL_DRY_RUN_PROMOTION_DOCS = [
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_POLICY.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_RECEIPT_PLAN.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_NON_GOALS.md",
    "docs/autonomy/M93_TO_M94_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_97_0.md",
    "docs/archive/releases/v0_97_0/README_IMPORT.md",
    "docs/archive/releases/v0_97_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_97_0.md",
]

REQUIRED_M94_LOW_RISK_BROWSER_CLICK_DOCS = [
    "docs/browser/LOW_RISK_BROWSER_CLICKS.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_POLICY.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_AUTHORITY_BOUNDARY.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_RECEIPT_PLAN.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_NON_GOALS.md",
    "docs/browser/M94_TO_M95_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_98_0.md",
    "docs/archive/releases/v0_98_0/README_IMPORT.md",
    "docs/archive/releases/v0_98_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_98_0.md",
]

REQUIRED_M95_AUTHLESS_NETWORK_EXPANSION_DOCS = [
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_POLICY.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_RECEIPT_PLAN.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_NON_GOALS.md",
    "docs/network/M95_TO_M96_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v0_99_0.md",
    "docs/archive/releases/v0_99_0/README_IMPORT.md",
    "docs/archive/releases/v0_99_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_99_0.md",
]

REQUIRED_M96_PLUGIN_EXECUTION_SANDBOX_DOCS = [
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_POLICY.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_RECEIPT_PLAN.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_NON_GOALS.md",
    "docs/tooling/M96_TO_M97_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v1_0_0.md",
    "docs/archive/releases/v1_0_0/README_IMPORT.md",
    "docs/archive/releases/v1_0_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v1_0_0.md",
]

REQUIRED_M97_RECURRING_AUTOMATION_DOCS = [
    "docs/automation/RECURRING_AUTOMATION_CONTRACTS.md",
    "docs/automation/RECURRING_AUTOMATION_RENEWAL_POLICY.md",
    "docs/automation/RECURRING_AUTOMATION_STOP_CONDITIONS.md",
    "docs/automation/RECURRING_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/automation/RECURRING_AUTOMATION_RECEIPT_PLAN.md",
    "docs/automation/RECURRING_AUTOMATION_NON_GOALS.md",
    "docs/automation/M97_TO_M98_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v1_1_0.md",
    "docs/archive/releases/v1_1_0/README_IMPORT.md",
    "docs/archive/releases/v1_1_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v1_1_0.md",
]

REQUIRED_M98_SCOPED_RECURRING_LOW_RISK_AUTOMATION_DOCS = [
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_POLICY.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_RECEIPT_PLAN.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_NON_GOALS.md",
    "docs/automation/M98_TO_M99_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v1_2_0.md",
    "docs/archive/releases/v1_2_0/README_IMPORT.md",
    "docs/archive/releases/v1_2_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v1_2_0.md",
]

REQUIRED_M99_AUTONOMY_V1_SAFETY_FREEZE_DOCS = [
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_POLICY.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_NON_GOALS.md",
    "docs/autonomy/M99_TO_M100_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v1_3_0.md",
    "docs/archive/releases/v1_3_0/README_IMPORT.md",
    "docs/archive/releases/v1_3_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v1_3_0.md",
]

REQUIRED_M100_MOBILE_PERMISSION_MODEL_V1_DOCS = [
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_POLICY.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_CONSENT_REVOCATION.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_PRIVACY_COPY.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_AUDIT.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_NON_GOALS.md",
    "docs/mobile/M100_FINAL_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
    "docs/release_notes/v1_4_0.md",
    "docs/archive/releases/v1_4_0/README_IMPORT.md",
    "docs/archive/releases/v1_4_0/master_plan.md",
    "docs/implementation/foundation_gate_implementation_plan_v1_4_0.md",
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
    "docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md",
    "docs/mobile/M48_TO_M49_BOUNDARY.md",
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
    "docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md",
    "docs/mobile/M42_TO_M43_BOUNDARY.md",
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
    failures.extend(_verify_m39_context_proposal_surface_docs(root, version))
    failures.extend(_verify_m40_context_handoff_approval_docs(root, version))
    failures.extend(_verify_m41_local_prototype_safety_docs(root, version))
    failures.extend(_verify_m42_mobile_product_contract_docs(root, version))
    failures.extend(_verify_m43_mobile_api_boundary_docs(root, version))
    failures.extend(_verify_m44_ccc_ios_skeleton_docs(root, version))
    failures.extend(_verify_m45_ccc_ios_local_read_only_connection_docs(root, version))
    failures.extend(_verify_m46_ccc_ios_review_receipt_read_only_surface_docs(root, version))
    failures.extend(_verify_m47_testflight_pipeline_internal_only_docs(root, version))
    failures.extend(_verify_m48_first_internal_testflight_build_docs(root, version))
    failures.extend(_verify_m49_mobile_review_approval_capture_docs(root, version))
    failures.extend(_verify_m50_mobile_approval_audit_docs(root, version))
    failures.extend(_verify_m51_openwebui_bridge_adapter_docs(root, version))
    failures.extend(_verify_m52_openwebui_safe_conversation_docs(root, version))
    failures.extend(_verify_m53_controlled_tool_expansion_docs(root, version))
    failures.extend(_verify_m54_safe_media_metadata_docs(root, version))
    failures.extend(_verify_m55_redacted_observability_docs(root, version))
    failures.extend(_verify_m56_agent_eval_docs(root, version))
    failures.extend(_verify_m57_runtime_sandbox_docs(root, version))
    failures.extend(_verify_m58_dry_run_audit_docs(root, version))
    failures.extend(_verify_m59_public_github_readiness_docs(root, version))
    failures.extend(_verify_m60_local_developer_beta_freeze_docs(root, version))
    failures.extend(_verify_m61_autonomy_mode_charter_docs(root, version))
    failures.extend(_verify_m62_scoped_autonomy_session_docs(root, version))
    failures.extend(_verify_m63_autonomy_policy_engine_docs(root, version))
    failures.extend(_verify_m64_autonomous_plan_simulator_docs(root, version))
    failures.extend(_verify_m65_autonomy_audit_replay_viewer_docs(root, version))
    failures.extend(_verify_m66_scoped_approval_bundle_docs(root, version))
    failures.extend(_verify_m67_revocation_kill_switch_docs(root, version))
    failures.extend(_verify_m68_autonomy_risk_classifier_docs(root, version))
    failures.extend(_verify_m69_low_risk_autonomous_dry_run_docs(root, version))
    failures.extend(_verify_m70_autonomy_foundation_freeze_docs(root, version))
    failures.extend(_verify_m71_network_tool_contract_review_docs(root, version))
    failures.extend(_verify_m72_read_only_http_fetch_docs(root, version))
    failures.extend(_verify_m73_browser_automation_contract_review_docs(root, version))
    failures.extend(_verify_m74_browser_observe_only_docs(root, version))
    failures.extend(_verify_m75_browser_action_dry_run_docs(root, version))
    failures.extend(_verify_m76_openwebui_runtime_bridge_docs(root, version))
    failures.extend(_verify_m77_openwebui_safe_handoff_docs(root, version))
    failures.extend(_verify_m78_plugin_manifest_security_docs(root, version))
    failures.extend(_verify_m79_plugin_install_review_docs(root, version))
    failures.extend(_verify_m80_network_browser_openwebui_freeze_docs(root, version))
    failures.extend(_verify_m81_runtime_sandbox_spec_docs(root, version))
    failures.extend(_verify_m82_command_proposal_docs(root, version))
    failures.extend(_verify_m83_shell_dry_run_classifier_docs(root, version))
    failures.extend(_verify_m84_sandboxed_echo_noop_docs(root, version))
    failures.extend(_verify_m85_read_only_command_allowlist_docs(root, version))
    failures.extend(_verify_m86_shell_approval_gate_docs(root, version))
    failures.extend(_verify_m87_sandboxed_command_audit_replay_docs(root, version))
    failures.extend(_verify_m88_mutating_command_proposal_docs(root, version))
    failures.extend(_verify_m89_emergency_stop_process_kill_safety_docs(root, version))
    failures.extend(_verify_m90_shell_subprocess_hardening_freeze_docs(root, version))
    failures.extend(_verify_m91_autonomous_tool_execution_contract_docs(root, version))
    failures.extend(_verify_m92_low_risk_tool_autonomy_single_session_docs(root, version))
    failures.extend(_verify_m93_multi_tool_dry_run_promotion_docs(root, version))
    failures.extend(_verify_m94_low_risk_browser_click_docs(root, version))
    failures.extend(_verify_m95_authless_network_expansion_docs(root, version))
    failures.extend(_verify_m96_plugin_execution_sandbox_docs(root, version))
    failures.extend(_verify_m97_recurring_automation_docs(root, version))
    failures.extend(_verify_m98_scoped_recurring_low_risk_automation_docs(root, version))
    failures.extend(_verify_m99_autonomy_v1_safety_freeze_docs(root, version))
    failures.extend(_verify_m100_mobile_permission_model_v1_docs(root, version))
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
    if _version_tuple(version) >= (0, 48, 0):
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
                "M39 must be released as CCC Context Proposal Surface": (
                    "m39 is implemented/released"
                ),
                "M40 must be released as Context Handoff Approval": (
                    "m40 is implemented/released"
                ),
                "M41 must be released as Local Prototype Safety Freeze": (
                    "m41 is implemented/released"
                ),
                "M42 must be released as Mobile Companion Product Contract Refresh": (
                    "m42 is implemented/released"
                ),
                "M43 must be released as Mobile API Boundary, Read-Only": (
                    "m43 is implemented/released"
                ),
                "M44 must be released as CCC iOS Skeleton, No Authority": (
                    "m44 is implemented/released"
                ),
                **(
                    {
                        "M45 must be released as CCC iOS Local Read-Only Connection": (
                            "m45 is implemented/released"
                        ),
                        "M46 must be released as iOS Review/Receipt Read-Only Surfaces": (
                            "m46 is implemented/released"
                        ),
                        **(
                            {
                                "M47 must be released as TestFlight Pipeline, Internal Only": (
                                    "m47 is implemented/released"
                                ),
                                "M48 must be released as First Internal TestFlight Build": (
                                    "m48 is implemented/released"
                                ),
                                **(
                                    (
                                        (
                                            {
                                                "M49 must be released as Mobile Review Approval Capture": (
                                                    "m49 is implemented/released"
                                                ),
                                                "M50 must be released as Mobile Approval Audit Hardening": (
                                                    "m50 is implemented/released"
                                                ),
                                                "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                    "m51 is implemented/released"
                                                ),
                                                "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                    "m52 is implemented/released"
                                                ),
                                                "M53 must be released as Controlled Tool Expansion Review": (
                                                    "m53 is implemented/released"
                                                ),
                                                "M54 must be released as Safe Media Metadata Inspector": (
                                                    "m54 is implemented/released"
                                                ),
                                                "M55 must be released as Redacted Observability Export": (
                                                    "m55 is implemented/released"
                                                ),
                                                "M56 must be released as Agent Eval Regression Harness": (
                                                    "m56 is implemented/released"
                                                ),
                                                "M57 must be released as Runtime Sandbox Architecture Review": (
                                                    "m57 is implemented/released"
                                                ),
                                                "M58 must be released as Dry-Run Execution Audit Harness": (
                                                    "m58 is implemented/released"
                                                ),
                                                **(
                                                    {
                                                        "M59 must be released as Public GitHub Readiness": (
                                                            "m59 is implemented/released"
                                                        ),
                                                        "M60 must be released as Local Developer Beta Freeze": (
                                                            "m60 is implemented/released"
                                                        ),
                                                    }
                                                    if _version_tuple(version) >= (0, 64, 0)
                                                    else (
                                                        {
                                                            "M59 must be released as Public GitHub Readiness": (
                                                                "m59 is implemented/released"
                                                            ),
                                                            "M60 must remain planned/provisional": (
                                                                "m60 remains planned/provisional"
                                                            ),
                                                        }
                                                        if _version_tuple(version) >= (0, 63, 0)
                                                        else {
                                                            "M59-M60 must remain planned/provisional": (
                                                                "m59-m60 remain planned/provisional"
                                                            ),
                                                        }
                                                    )
                                                ),
                                            }
                                            if _version_tuple(version) >= (0, 62, 0)
                                            else (
                                            {
                                                "M49 must be released as Mobile Review Approval Capture": (
                                                    "m49 is implemented/released"
                                                ),
                                                "M50 must be released as Mobile Approval Audit Hardening": (
                                                    "m50 is implemented/released"
                                                ),
                                                "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                    "m51 is implemented/released"
                                                ),
                                                "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                    "m52 is implemented/released"
                                                ),
                                                "M53 must be released as Controlled Tool Expansion Review": (
                                                    "m53 is implemented/released"
                                                ),
                                                "M54 must be released as Safe Media Metadata Inspector": (
                                                    "m54 is implemented/released"
                                                ),
                                                "M55 must be released as Redacted Observability Export": (
                                                    "m55 is implemented/released"
                                                ),
                                                "M56 must be released as Agent Eval Regression Harness": (
                                                    "m56 is implemented/released"
                                                ),
                                                "M57 must be released as Runtime Sandbox Architecture Review": (
                                                    "m57 is implemented/released"
                                                ),
                                                "M58-M60 must remain planned/provisional": (
                                                    "m58-m60 remain planned/provisional"
                                                ),
                                            }
                                            )
                                            if _version_tuple(version) >= (0, 60, 0)
                                            else {
                                                "M49 must be released as Mobile Review Approval Capture": (
                                                    "m49 is implemented/released"
                                                ),
                                                "M50 must be released as Mobile Approval Audit Hardening": (
                                                    "m50 is implemented/released"
                                                ),
                                                "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                    "m51 is implemented/released"
                                                ),
                                                "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                    "m52 is implemented/released"
                                                ),
                                                "M53 must be released as Controlled Tool Expansion Review": (
                                                    "m53 is implemented/released"
                                                ),
                                                "M54 must be released as Safe Media Metadata Inspector": (
                                                    "m54 is implemented/released"
                                                ),
                                                "M55 must be released as Redacted Observability Export": (
                                                    "m55 is implemented/released"
                                                ),
                                                "M56-M60 must remain planned/provisional": (
                                                    "m56-m60 remain planned/provisional"
                                                ),
                                            }
                                        )
                                        if _version_tuple(version) >= (0, 59, 0)
                                        else {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50 must be released as Mobile Approval Audit Hardening": (
                                                "m50 is implemented/released"
                                            ),
                                            "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                "m51 is implemented/released"
                                            ),
                                            "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                "m52 is implemented/released"
                                            ),
                                            "M53 must be released as Controlled Tool Expansion Review": (
                                                "m53 is implemented/released"
                                            ),
                                            "M54 must be released as Safe Media Metadata Inspector": (
                                                "m54 is implemented/released"
                                            ),
                                            "M55-M60 must remain planned/provisional": (
                                                "m55-m60 remain planned/provisional"
                                            ),
                                        }
                                        if _version_tuple(version) >= (0, 58, 0)
                                        else {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50 must be released as Mobile Approval Audit Hardening": (
                                                "m50 is implemented/released"
                                            ),
                                            "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                "m51 is implemented/released"
                                            ),
                                            "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                "m52 is implemented/released"
                                            ),
                                            "M53 must be released as Controlled Tool Expansion Review": (
                                                "m53 is implemented/released"
                                            ),
                                            "M54-M60 must remain planned/provisional": (
                                                "m54-m60 remain planned/provisional"
                                            ),
                                        }
                                        if _version_tuple(version) >= (0, 57, 0)
                                        else {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50 must be released as Mobile Approval Audit Hardening": (
                                                "m50 is implemented/released"
                                            ),
                                            "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                "m51 is implemented/released"
                                            ),
                                            "M52 must be released as OpenWebUI Safe Conversation Surface": (
                                                "m52 is implemented/released"
                                            ),
                                            "M53-M60 must remain planned/provisional": (
                                                "m53-m60 remain planned/provisional"
                                            ),
                                        }
                                        if _version_tuple(version) >= (0, 56, 0)
                                        else {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50 must be released as Mobile Approval Audit Hardening": (
                                                "m50 is implemented/released"
                                            ),
                                            "M51 must be released as OpenWebUI Bridge Adapter Pilot": (
                                                "m51 is implemented/released"
                                            ),
                                            "M52-M60 must remain planned/provisional": (
                                                "m52-m60 remain planned/provisional"
                                            ),
                                        }
                                        if _version_tuple(version) >= (0, 55, 0)
                                        else {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50 must be released as Mobile Approval Audit Hardening": (
                                                "m50 is implemented/released"
                                            ),
                                            "M51-M60 must remain planned/provisional": (
                                                "m51-m60 remain planned/provisional"
                                            ),
                                        }
                                    )
                                    if _version_tuple(version) >= (0, 54, 0)
                                    else (
                                        {
                                            "M49 must be released as Mobile Review Approval Capture": (
                                                "m49 is implemented/released"
                                            ),
                                            "M50-M60 must remain planned/provisional": (
                                                "m50-m60 remain planned/provisional"
                                            ),
                                        }
                                        if _version_tuple(version) >= (0, 53, 0)
                                        else {
                                            "M49-M60 must remain planned/provisional": (
                                                "m49-m60 remain planned/provisional"
                                            ),
                                        }
                                    )
                                ),
                            }
                            if _version_tuple(version) >= (0, 52, 0)
                            else {
                                "M47 must be released as TestFlight Pipeline, Internal Only": (
                                    "m47 is implemented/released"
                                ),
                                "M48-M60 must remain planned/provisional": (
                                    "m48-m60 remain planned/provisional"
                                ),
                            }
                            if _version_tuple(version) >= (0, 51, 0)
                            else {
                                "M47-M60 must remain planned/provisional": (
                                    "m47-m60 remain planned/provisional"
                                ),
                            }
                        ),
                    }
                    if _version_tuple(version) >= (0, 50, 0)
                    else {
                        "M45 must be released as CCC iOS Local Read-Only Connection": (
                            "m45 is implemented/released"
                        ),
                        "M46-M60 must remain planned/provisional": (
                            "m46-m60 remain planned/provisional"
                        ),
                    }
                    if _version_tuple(version) >= (0, 49, 0)
                    else {
                        "M45-M60 must remain planned/provisional": (
                            "m45-m60 remain planned/provisional"
                        ),
                    }
                ),
            }
        )
    elif _version_tuple(version) >= (0, 46, 0):
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
                "M39 must be released as CCC Context Proposal Surface": (
                    "m39 is implemented/released"
                ),
                "M40 must be released as Context Handoff Approval": (
                    "m40 is implemented/released"
                ),
                "M41 must be released as Local Prototype Safety Freeze": (
                    "m41 is implemented/released"
                ),
                "M42 must be released as Mobile Companion Product Contract Refresh": (
                    "m42 is implemented/released"
                ),
                "M43 must be released as Mobile API Boundary, Read-Only": (
                    "m43 is implemented/released"
                ),
                "M44-M60 must remain planned/provisional": "m44-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 45, 0):
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
                "M39 must be released as CCC Context Proposal Surface": (
                    "m39 is implemented/released"
                ),
                "M40 must be released as Context Handoff Approval": (
                    "m40 is implemented/released"
                ),
                "M41 must be released as Local Prototype Safety Freeze": (
                    "m41 is implemented/released"
                ),
                "M42-M60 must remain planned/provisional": "m42-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 44, 0):
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
                "M39 must be released as CCC Context Proposal Surface": (
                    "m39 is implemented/released"
                ),
                "M40 must be released as Context Handoff Approval": (
                    "m40 is implemented/released"
                ),
                "M41-M60 must remain planned/provisional": "m41-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 43, 0):
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
                "M39 must be released as CCC Context Proposal Surface": (
                    "m39 is implemented/released"
                ),
                "M40-M60 must remain planned/provisional": "m40-m60 remain planned/provisional",
            }
        )
    elif _version_tuple(version) >= (0, 42, 0):
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
    }
    if _version_tuple(version) >= (0, 43, 0):
        required_fragments["M38 docs must say M39 implemented/released"] = "m39 is implemented/released"
        required_fragments["M38 docs must keep M40 future"] = "m40 remains future"
    else:
        required_fragments["M38 docs must keep M39 planned/provisional"] = "m39 remains planned/provisional"
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
    }
    if _version_tuple(version) < (0, 44, 0):
        forbidden_fragments["M38 docs must not claim M40 implementation"] = [
            "m40 is implemented",
            "v0.44.0 implements m40",
        ]
    if _version_tuple(version) < (0, 43, 0):
        forbidden_fragments["M38 docs must not claim M39 implementation"] = [
            "m39 is implemented",
            "v0.43.0 implements m39",
        ]
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")
    return failures


def _verify_m39_context_proposal_surface_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 43, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M39_CONTEXT_PROPOSAL_SURFACE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M39 context proposal surface doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M39 docs must say read-only": "read-only",
        "M39 docs must say proposal-only": "proposal-only",
        "M39 docs must say mock and non-authoritative": "mock and non-authoritative",
        "M39 docs must mention exact binding refs": "exact binding refs",
        "M39 docs must mention redaction verification": "redaction verification",
        "M39 docs must deny context handoff": "no context handoff",
        "M39 docs must deny context injection": "no context injection",
        "M39 docs must deny OpenWebUI handoff": "no openwebui handoff",
        "M39 docs must deny memory writes": "no memory writes",
        "M39 docs must deny export": "no export",
        "M39 docs must deny execution": "no execution",
        "M39 docs must deny raw file access": "no raw file access",
        "M39 docs must keep M40 future": "m40 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M39 docs must not claim context injection implementation": [
            "context injection is implemented",
            "automatic context injection is implemented",
        ],
        "M39 docs must not claim OpenWebUI handoff implementation": [
            "openwebui handoff is implemented",
            "send to openwebui is implemented",
        ],
    }
    if _version_tuple(version) < (0, 44, 0):
        forbidden_fragments["M39 docs must not claim M40 implementation"] = [
            "m40 is implemented",
            "v0.44.0 implements m40",
        ]
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")
    return failures


def _verify_m40_context_handoff_approval_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 44, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M40_CONTEXT_HANDOFF_APPROVAL_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M40 context handoff approval doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M40 docs must mention exact proposal binding": "exact proposal binding",
        "M40 docs must say review-only": "review-only",
        "M40 docs must deny context injection": "no context injection",
        "M40 docs must deny OpenWebUI handoff execution": "no openwebui handoff execution",
        "M40 docs must deny model calls": "no model calls",
        "M40 docs must deny memory writes": "no memory writes",
        "M40 docs must deny export": "no export",
        "M40 docs must deny execution": "no execution",
        "M40 docs must deny approval_ref authority": "approval_ref alone is not authority",
        "M40 docs must deny approval_test_ authority": "approval_test_ is not runtime authority",
        "M40 docs must say evaluator revalidation exists": "evaluator boundaries revalidate",
        "M40 docs must keep M41 future": "m41 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M40 docs must not claim context injection implementation": [
            "context injection is implemented",
            "automatic context injection is implemented",
        ],
        "M40 docs must not claim OpenWebUI handoff execution implementation": [
            "openwebui handoff execution is implemented",
            "send to openwebui is implemented",
        ],
        "M40 docs must not claim memory/export/execution implementation": [
            "memory writes are implemented",
            "export is implemented",
            "execution is implemented",
        ],
        "M40 docs must not claim M41 implementation": [
            "m41 is implemented",
            "v0.45.0 implements m41",
        ],
    }
    for message, fragments in forbidden_fragments.items():
        for fragment in fragments:
            if fragment in text:
                failures.append(f"{message}: {fragment}")
    return failures


def _verify_m41_local_prototype_safety_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 45, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M41_LOCAL_PROTOTYPE_SAFETY_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M41 local prototype safety doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M41 docs must say local prototype safety freeze": "local prototype safety freeze",
        "M41 docs must say localhost-only": "localhost-only",
        "M41 docs must say review-only": "review-only",
        "M41 docs must say mock/non-authoritative": "mock/non-authoritative",
        "M41 docs must deny raw file browsing": "no raw file browsing",
        "M41 docs must deny raw file export": "no raw file export",
        "M41 docs must deny full-file reads": "no full-file reads",
        "M41 docs must deny caller-selected roots": "no arbitrary caller-selected roots",
        "M41 docs must deny shell/subprocess": "no shell/subprocess",
        "M41 docs must deny unrestricted network tools": "no network tools",
        "M41 docs must deny model authority": "no provider/model calls as authority",
        "M41 docs must deny background workers": "no background workers",
        "M41 docs must deny mobile sensors": "no mobile sensors",
        "M41 docs must deny plugin enablement": "no plugin enablement",
        "M41 docs must deny production authority": "no production authority",
        "M41 docs must deny unreviewed memory writes": "no unreviewed memory writes",
        "M41 docs must deny context injection": "no automatic context injection",
        "M41 docs must deny raw prompt/provider payloads": "no raw prompt/provider payload exposure",
        "M41 docs must deny credentials/cookies": "no credentials/cookie handling",
        "M41 docs must deny remote execution": "no remote execution",
        "M41 docs must deny browser automation execution": "no browser automation execution",
        "M41 docs must deny approval-ref authority": "approval refs are not authority",
        "M41 docs must define local browser smoke review": "browser smoke review is local-only",
        "M41 docs must keep M42 future": "m42 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M41 docs must not claim raw file browsing implementation": "raw file browsing is implemented",
        "M41 docs must not claim raw file export implementation": "raw file export is implemented",
        "M41 docs must not claim full-file reads implementation": "full-file reads are implemented",
        "M41 docs must not claim shell execution implementation": "shell execution is implemented",
        "M41 docs must not claim network tools implementation": "network tools are implemented",
        "M41 docs must not claim background workers implementation": "background workers are implemented",
        "M41 docs must not claim mobile sensors implementation": "mobile sensors are implemented",
        "M41 docs must not claim plugin enablement implementation": "plugin enablement is implemented",
        "M41 docs must not claim production authority implementation": "production authority is implemented",
        "M41 docs must not claim automatic context injection implementation": "automatic context injection is implemented",
        "M41 docs must not claim remote execution implementation": "remote execution is implemented",
        "M41 docs must not claim browser automation execution implementation": "browser automation execution is implemented",
        "M41 docs must not claim approval refs as authority": "approval refs are authority",
        "M41 docs must not claim M42 implementation": "m42 is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m42_mobile_product_contract_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 46, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md",
        "docs/mobile/M42_TO_M43_BOUNDARY.md",
        "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
        "docs/mobile/MOBILE_SECURITY_MODEL.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M42 mobile product contract doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M42 docs must say product contract refresh": "mobile companion product contract refresh",
        "M42 docs must say planning/docs/contracts/verifier": "planning/docs/contracts/verifier",
        "M42 docs must say governance/control": "governance/control",
        "M42 docs must say not the agent brain": "not the agent brain",
        "M42 docs must say review-only": "review-only",
        "M42 docs must say read-only": "read-only",
        "M42 docs must acknowledge M43 release": "m43 is implemented/released",
        "M42 docs must keep M44 future": "m44 remains future",
        "M42 docs must deny mobile app": "no mobile app",
        "M42 docs must deny iOS app": "no ios app",
        "M42 docs must deny Android app": "no android app",
        "M42 docs must deny native package": "no native package",
        "M42 docs must deny native build workflow": "no native build workflow",
        "M42 docs must deny signing": "no signing",
        "M42 docs must deny TestFlight": "no testflight",
        "M42 docs must deny backend route": "no backend route",
        "M42 docs must deny mobile API route": "no mobile api route",
        "M42 docs must deny approval capture": "no approval capture",
        "M42 docs must deny approval execution": "no approval execution",
        "M42 docs must deny mobile sensor access": "no mobile sensor access",
        "M42 docs must deny OS permission integration": "no os permission integration",
        "M42 docs must deny background service": "no background service",
        "M42 docs must deny notification runtime": "no notification runtime",
        "M42 docs must deny raw payload exposure": "no raw payload exposure",
        "M42 docs must deny memory write": "no memory write",
        "M42 docs must deny context injection": "no context injection",
        "M42 docs must deny production authority": "no production authority",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M42 docs must not claim mobile app implementation": "mobile app is implemented",
        "M42 docs must not claim iOS app implementation": "ios app is implemented",
        "M42 docs must not claim Android app implementation": "android app is implemented",
        "M42 docs must not claim mobile API implementation": "mobile api is implemented",
        "M42 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M42 docs must not claim approval execution implementation": "approval execution is implemented",
        "M42 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 47, 0):
        forbidden_fragments["M42 docs must not claim M43 implementation"] = "m43 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m43_mobile_api_boundary_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 47, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md",
        "docs/mobile/M43_TO_M44_BOUNDARY.md",
        "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
        "docs/mobile/MOBILE_SECURITY_MODEL.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M43 mobile API boundary doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M43 docs must say Mobile API Boundary, Read-Only": "mobile api boundary, read-only",
        "M43 docs must say contract-only": "contract-only",
        "M43 docs must say read-only": "read-only",
        "M43 docs must say redacted summary only": "redacted summary only",
        "M43 docs must say planned endpoint refs": "planned endpoint refs",
        "M43 docs must deny backend route": "no backend route",
        "M43 docs must deny mobile mutation": "no mobile mutation",
        "M43 docs must deny approval capture": "no approval capture",
        "M43 docs must deny approval execution": "no approval execution",
        "M43 docs must deny mobile sensor access": "no mobile sensor access",
        "M43 docs must deny raw data": "no raw data",
        "M43 docs must deny raw payload exposure": "no raw payload exposure",
        "M43 docs must deny raw absolute path": "no raw absolute path",
        "M43 docs must deny credential handling": "no credential",
        "M43 docs must deny cookie handling": "no cookie",
        "M43 docs must deny context injection": "no context injection",
        "M43 docs must deny memory write": "no memory write",
        "M43 docs must deny export": "no export",
        "M43 docs must deny execution": "no execution",
        "M43 docs must deny production authority": "no production authority",
        "M43 docs must keep M44 future": "m44 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M43 docs must not claim mobile app implementation": "mobile app is implemented",
        "M43 docs must not claim mobile route implementation": "mobile api route is implemented",
        "M43 docs must not claim mobile mutation implementation": "mobile mutation is implemented",
        "M43 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M43 docs must not claim approval execution implementation": "approval execution is implemented",
        "M43 docs must not claim production authority": "production authority is implemented",
        "M43 docs must not claim M44 implementation": "m44 is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m44_ccc_ios_skeleton_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 48, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md",
        "docs/mobile/M44_TO_M45_BOUNDARY.md",
        "docs/release_notes/v0_48_0.md",
        "docs/archive/releases/v0_48_0/README_IMPORT.md",
        "docs/archive/releases/v0_48_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_48_0.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M44 CCC iOS skeleton doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M44 docs must say CCC iOS Skeleton, No Authority": "ccc ios skeleton, no authority",
        "M44 docs must say source-only": "source-only",
        "M44 docs must say mock-only": "mock-only",
        "M44 docs must say read-only": "read-only",
        "M44 docs must say non-authoritative": "non-authoritative",
        "M44 docs must deny Xcode project": "no xcode project",
        "M44 docs must deny Swift package": "no swift package",
        "M44 docs must deny Info.plist": "no info.plist",
        "M44 docs must deny entitlements": "no entitlements",
        "M44 docs must deny backend route": "no backend route",
        "M44 docs must deny mobile API route runtime": "no mobile api route runtime",
        "M44 docs must deny network": "no network",
        "M44 docs must deny mobile sensor access": "no mobile sensor access",
        "M44 docs must deny OS permission integration": "no os permission integration",
        "M44 docs must deny approval capture": "no approval capture",
        "M44 docs must deny approval execution": "no approval execution",
        "M44 docs must deny context injection": "no context injection",
        "M44 docs must deny memory write": "no memory write",
        "M44 docs must deny file mutation": "no file mutation",
        "M44 docs must deny execution": "no execution",
        "M44 docs must deny credentials": "no credential",
        "M44 docs must deny background": "no background",
        "M44 docs must deny production authority": "no production authority",
        "M44 docs must keep M45 future": "m45 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M44 docs must not claim M45 implementation": "m45 is implemented",
        "M44 docs must not claim local connection implementation": "local read-only connection is implemented",
        "M44 docs must not claim TestFlight implementation": "testflight pipeline is implemented",
        "M44 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M44 docs must not claim approval execution implementation": "approval execution is implemented",
        "M44 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m45_ccc_ios_local_read_only_connection_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 49, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md",
        "docs/mobile/M45_TO_M46_BOUNDARY.md",
        "docs/release_notes/v0_49_0.md",
        "docs/archive/releases/v0_49_0/README_IMPORT.md",
        "docs/archive/releases/v0_49_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_49_0.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M45 CCC iOS local connection doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M45 docs must say CCC iOS Local Read-Only Connection": "ccc ios local read-only connection",
        "M45 docs must say local-only": "local-only",
        "M45 docs must say loopback-only": "loopback-only",
        "M45 docs must say read-only": "read-only",
        "M45 docs must say redacted summary": "redacted summary",
        "M45 docs must say non-authoritative": "non-authoritative",
        "M45 docs must deny runtime network call": "no runtime network call",
        "M45 docs must deny backend route": "no backend route",
        "M45 docs must deny approval capture": "no approval capture",
        "M45 docs must deny approval execution": "no approval execution",
        "M45 docs must deny raw data": "no raw data",
        "M45 docs must deny context injection": "no context injection",
        "M45 docs must deny memory write": "no memory write",
        "M45 docs must deny file mutation": "no file mutation",
        "M45 docs must deny execution": "no execution",
        "M45 docs must deny background collection": "no background collection",
        "M45 docs must deny mobile sensor access": "no mobile sensor access",
        "M45 docs must deny credentials": "no credential",
        "M45 docs must deny Xcode project": "no xcode project",
        "M45 docs must deny Swift package": "no swift package",
        "M45 docs must deny signing": "no signing",
        "M45 docs must deny TestFlight": "no testflight",
        "M45 docs must deny production authority": "no production authority",
        "M45 docs must keep M46 future": "m46 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M45 docs must not claim M46 implementation": "m46 is implemented",
        "M45 docs must not claim review/receipt surfaces implementation": (
            "review/receipt read-only surfaces are implemented"
        ),
        "M45 docs must not claim TestFlight implementation": "testflight pipeline is implemented",
        "M45 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M45 docs must not claim approval execution implementation": "approval execution is implemented",
        "M45 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m46_ccc_ios_review_receipt_read_only_surface_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 50, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md",
        "docs/mobile/M46_TO_M47_BOUNDARY.md",
        "docs/release_notes/v0_50_0.md",
        "docs/archive/releases/v0_50_0/README_IMPORT.md",
        "docs/archive/releases/v0_50_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_50_0.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M46 CCC iOS review/receipt doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M46 docs must say iOS Review/Receipt Read-Only Surfaces": "ios review/receipt read-only surfaces",
        "M46 docs must say source-only": "source-only",
        "M46 docs must say read-only": "read-only",
        "M46 docs must say redacted summary": "redacted summary",
        "M46 docs must say mock": "mock",
        "M46 docs must say non-authoritative": "non-authoritative",
        "M46 docs must deny runtime network call": "no runtime network call",
        "M46 docs must deny backend route": "no backend route",
        "M46 docs must deny approval capture": "no approval capture",
        "M46 docs must deny approval execution": "no approval execution",
        "M46 docs must deny raw data": "no raw data",
        "M46 docs must deny context injection": "no context injection",
        "M46 docs must deny memory write": "no memory write",
        "M46 docs must deny file mutation": "no file mutation",
        "M46 docs must deny export": "no export",
        "M46 docs must deny execution": "no execution",
        "M46 docs must deny background collection": "no background collection",
        "M46 docs must deny mobile sensor access": "no mobile sensor access",
        "M46 docs must deny credentials": "no credential",
        "M46 docs must deny Xcode project": "no xcode project",
        "M46 docs must deny Swift package": "no swift package",
        "M46 docs must deny signing": "no signing",
        "M46 docs must deny TestFlight": "no testflight",
        "M46 docs must deny production authority": "no production authority",
        "M46 docs must keep M47 future": "m47 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M46 docs must not claim M47 implementation": "m47 is implemented",
        "M46 docs must not claim TestFlight implementation": "testflight pipeline is implemented",
        "M46 docs must not claim mobile approval capture": "mobile approval capture is implemented",
        "M46 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M46 docs must not claim approval execution implementation": "approval execution is implemented",
        "M46 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m47_testflight_pipeline_internal_only_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 51, 0):
        return []

    failures: list[str] = []
    required_docs = [
        "docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md",
        "docs/mobile/M47_TO_M48_BOUNDARY.md",
        "docs/release_notes/v0_51_0.md",
        "docs/archive/releases/v0_51_0/README_IMPORT.md",
        "docs/archive/releases/v0_51_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_51_0.md",
    ]
    parts: list[str] = []
    for rel_path in required_docs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M47 TestFlight pipeline doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M47 docs must say TestFlight Pipeline, Internal Only": "testflight pipeline, internal only",
        "M47 docs must say internal-only": "internal-only",
        "M47 docs must say contract": "contract",
        "M47 docs must say checklist": "checklist",
        "M47 docs must deny build execution": "no build execution",
        "M47 docs must deny upload execution": "no upload execution",
        "M47 docs must deny signing asset storage": "no signing asset storage",
        "M47 docs must deny App Store Connect API": "no app store connect api",
        "M47 docs must deny credential handling": "no credential",
        "M47 docs must deny external beta": "no external beta",
        "M47 docs must deny public distribution": "no public distribution",
        "M47 docs must deny production authority": "no production authority",
        "M47 docs must deny mobile sensor access": "no mobile sensor access",
        "M47 docs must deny background collection": "no background collection",
        "M47 docs must keep M48 future": "m48 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M47 docs must not claim M48 implementation": "m48 is implemented",
        "M47 docs must not claim first internal build implementation": (
            "first internal testflight build is implemented"
        ),
        "M47 docs must not claim upload implementation": "upload execution is implemented",
        "M47 docs must not claim signing implementation": "signing asset storage is implemented",
        "M47 docs must not claim App Store Connect implementation": "app store connect api is implemented",
        "M47 docs must not claim external beta": "external beta is implemented",
        "M47 docs must not claim public distribution": "public distribution is implemented",
        "M47 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m48_first_internal_testflight_build_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 52, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M48_FIRST_INTERNAL_TESTFLIGHT_BUILD_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M48 first internal TestFlight build doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M48 docs must say First Internal TestFlight Build": "first internal testflight build",
        "M48 docs must say build candidate": "build candidate",
        "M48 docs must say review-only": "review-only",
        "M48 docs must say internal-only": "internal-only",
        "M48 docs must deny committed build artifact": "no committed build artifact",
        "M48 docs must deny IPA": "no ipa",
        "M48 docs must deny Xcode archive": "no xcode archive",
        "M48 docs must deny signing material": "no signing material",
        "M48 docs must deny App Store Connect": "no app store connect",
        "M48 docs must deny TestFlight upload": "no testflight upload",
        "M48 docs must deny external beta": "no external beta",
        "M48 docs must deny public distribution": "no public distribution",
        "M48 docs must deny mobile approval capture": "no mobile approval capture",
        "M48 docs must deny mobile sensor access": "no mobile sensor access",
        "M48 docs must deny background collection": "no background collection",
        "M48 docs must deny context injection": "no context injection",
        "M48 docs must deny memory write": "no memory write",
        "M48 docs must deny raw data export": "no raw data export",
        "M48 docs must deny execution": "no execution",
        "M48 docs must deny production authority": "no production authority",
        "M48 docs must keep M49 future": "m49 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M48 docs must not claim M49 implementation": "m49 is implemented",
        "M48 docs must not claim mobile approval capture implementation": (
            "mobile review approval capture is implemented"
        ),
        "M48 docs must not claim upload implementation": "testflight upload is implemented",
        "M48 docs must not claim signing implementation": "signing material storage is implemented",
        "M48 docs must not claim external beta": "external beta is implemented",
        "M48 docs must not claim public distribution": "public distribution is implemented",
        "M48 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m49_mobile_review_approval_capture_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 53, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M49_MOBILE_REVIEW_APPROVAL_CAPTURE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M49 mobile review approval capture doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M49 docs must say Mobile Review Approval Capture": "mobile review approval capture",
        "M49 docs must say review-only": "review-only",
        "M49 docs must say exact-scope": "exact-scope",
        "M49 docs must say actor-bound": "actor-bound",
        "M49 docs must say resource-bound": "resource-bound",
        "M49 docs must say replay-safe": "replay-safe",
        "M49 docs must say revocable": "revocable",
        "M49 docs must say safe refs only": "safe refs only",
        "M49 docs must deny raw file access": "no raw file access",
        "M49 docs must deny raw content": "no raw content",
        "M49 docs must deny full-file content": "no full-file content",
        "M49 docs must deny unredacted preview": "no unredacted preview",
        "M49 docs must deny context proposal": "no context proposal",
        "M49 docs must deny context injection": "no context injection",
        "M49 docs must deny memory write": "no memory write",
        "M49 docs must deny export": "no export",
        "M49 docs must deny execution": "no execution",
        "M49 docs must deny mobile sensor access": "no mobile sensor access",
        "M49 docs must deny background collection": "no background collection",
        "M49 docs must deny backend mobile approval route": "no backend mobile approval route",
        "M49 docs must deny native approval capture UI": "no native approval capture ui",
        "M49 docs must keep M50 future": "m50 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M49 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M49 docs must not claim context injection implementation": "context injection is implemented",
        "M49 docs must not claim execution implementation": "execution is implemented",
        "M49 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 54, 0):
        forbidden_fragments.update(
            {
                "M49 docs must not claim M50 implementation": "m50 is implemented",
                "M49 docs must not claim audit hardening implementation": (
                    "mobile approval audit hardening is implemented"
                ),
            }
        )
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m50_mobile_approval_audit_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 54, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M50_MOBILE_APPROVAL_AUDIT_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M50 mobile approval audit doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M50 docs must say Mobile Approval Audit Hardening": "mobile approval audit hardening",
        "M50 docs must say review-only": "review-only",
        "M50 docs must say safe-ref-only": "safe-ref-only",
        "M50 docs must mention model_copy revalidation": "model_copy",
        "M50 docs must deny raw content": "no raw content",
        "M50 docs must deny context injection": "no context injection",
        "M50 docs must deny memory write": "no memory write",
        "M50 docs must deny export": "no export",
        "M50 docs must deny execution": "no execution",
        "M50 docs must deny mobile sensor access": "no mobile sensor access",
        "M50 docs must deny backend route": "no backend route",
        "M50 docs must keep M51 future": "m51 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M50 docs must not claim M51 implementation": "m51 is implemented",
        "M50 docs must not claim OpenWebUI bridge implementation": (
            "openwebui bridge adapter pilot is implemented"
        ),
        "M50 docs must not claim sensor implementation": "mobile sensors are implemented",
        "M50 docs must not claim context injection implementation": "context injection is implemented",
        "M50 docs must not claim execution implementation": "execution is implemented",
        "M50 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m51_openwebui_bridge_adapter_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 55, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M51_OPENWEBUI_BRIDGE_ADAPTER_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M51 OpenWebUI bridge adapter doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M51 docs must say OpenWebUI Bridge Adapter Pilot": "openwebui bridge adapter pilot",
        "M51 docs must say safe-summary-only": "safe-summary-only",
        "M51 docs must keep Agent Core authority": "agent core remains authority",
        "M51 docs must say OpenWebUI is not the brain": "openwebui is not the agent brain",
        "M51 docs must deny raw prompt exposure": "no raw prompt",
        "M51 docs must deny raw provider payload exposure": "no raw provider payload",
        "M51 docs must deny provider calls": "no provider call",
        "M51 docs must deny model authority": "no model authority",
        "M51 docs must deny tool execution": "no tool execution",
        "M51 docs must deny memory writes": "no memory write",
        "M51 docs must deny context injection": "no context injection",
        "M51 docs must deny backend routes": "no backend route",
    }
    if _version_tuple(version) < (0, 56, 0):
        required_fragments["M51 docs must keep M52 future"] = "m52 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M51 docs must not claim OpenWebUI runtime calls": "openwebui runtime call is implemented",
        "M51 docs must not claim tool execution": "tool execution is implemented",
        "M51 docs must not claim context injection implementation": "context injection is implemented",
        "M51 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 56, 0):
        forbidden_fragments.update(
            {
                "M51 docs must not claim M52 implementation": "m52 is implemented",
                "M51 docs must not claim OpenWebUI safe conversation surface implementation": (
                    "openwebui safe conversation surface is implemented"
                ),
            }
        )
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m52_openwebui_safe_conversation_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 56, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M52_OPENWEBUI_SAFE_CONVERSATION_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M52 OpenWebUI safe conversation doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M52 docs must say OpenWebUI Safe Conversation Surface": "openwebui safe conversation surface",
        "M52 docs must say safe-summary-only": "safe-summary-only",
        "M52 docs must keep Agent Core authority": "agent core remains authority",
        "M52 docs must say OpenWebUI is not the brain": "openwebui is not the agent brain",
        "M52 docs must deny raw prompt exposure": "no raw prompt",
        "M52 docs must deny raw provider payload exposure": "no raw provider payload",
        "M52 docs must deny raw content": "no raw content",
        "M52 docs must deny provider calls": "no provider call",
        "M52 docs must deny model calls": "no model call",
        "M52 docs must deny model authority": "no model authority",
        "M52 docs must deny tool execution": "no tool execution",
        "M52 docs must deny memory writes": "no memory write",
        "M52 docs must deny context injection": "no context injection",
        "M52 docs must deny backend routes": "no backend route",
    }
    if _version_tuple(version) < (0, 57, 0):
        required_fragments["M52 docs must keep M53 future"] = "m53 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M52 docs must not claim OpenWebUI runtime calls": "openwebui runtime call is implemented",
        "M52 docs must not claim provider calls": "provider call is implemented",
        "M52 docs must not claim model authority": "model authority is implemented",
        "M52 docs must not claim tool execution": "tool execution is implemented",
        "M52 docs must not claim context injection implementation": "context injection is implemented",
        "M52 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 57, 0):
        forbidden_fragments["M52 docs must not claim M53 implementation"] = "m53 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m53_controlled_tool_expansion_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 57, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M53_CONTROLLED_TOOL_EXPANSION_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M53 controlled tool expansion doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M53 docs must say Controlled Tool Expansion Review": "controlled tool expansion review",
        "M53 docs must say review-only": "review-only",
        "M53 docs must say planning-only": "planning-only",
        "M53 docs must deny tool execution": "no tool execution",
        "M53 docs must deny tool enablement": "no tool enablement",
        "M53 docs must deny shell execution": "no shell execution",
        "M53 docs must deny subprocess execution": "no subprocess execution",
        "M53 docs must deny unrestricted network tools": "no network tool",
        "M53 docs must deny provider model calls": "no provider model call",
        "M53 docs must deny browser automation execution": "no browser automation execution",
        "M53 docs must deny plugin enablement": "no plugin enablement",
        "M53 docs must deny mobile sensor access": "no mobile sensor access",
        "M53 docs must deny remote execution": "no remote execution",
        "M53 docs must deny raw file browsing": "no raw file browsing",
        "M53 docs must deny raw file export": "no raw file export",
        "M53 docs must deny full-file reads": "no full-file read",
        "M53 docs must deny memory writes": "no memory write",
        "M53 docs must deny context injection": "no context injection",
        "M53 docs must deny backend routes": "no backend route",
        "M53 docs must keep M54 future": "m54 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M53 docs must not claim tool execution implementation": "tool execution is implemented",
        "M53 docs must not claim shell execution implementation": "shell execution is implemented",
        "M53 docs must not claim provider calls": "provider model call is implemented",
        "M53 docs must not claim M54 implementation": "m54 is implemented",
        "M53 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m54_safe_media_metadata_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 58, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M54_SAFE_MEDIA_METADATA_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M54 safe media metadata doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M54 docs must say Safe Media Metadata Inspector": "safe media metadata inspector",
        "M54 docs must say metadata-only": "metadata-only",
        "M54 docs must deny raw media export": "no raw media export",
        "M54 docs must deny raw media storage": "no raw media storage",
        "M54 docs must deny full-file reads": "no full-file read",
        "M54 docs must deny file mutation": "no file mutation",
        "M54 docs must deny original overwrite": "no original overwrite",
        "M54 docs must deny OCIO transform": "no ocio transform",
        "M54 docs must deny AI gamut expansion": "no ai gamut expansion",
        "M54 docs must deny model calls": "no model call",
        "M54 docs must deny context injection": "no context injection",
        "M54 docs must deny backend routes": "no backend route",
        "M54 docs must keep M55 future": "m55 remains future",
        "M54 Foundation Gate docs must mention Skill Package Security Rule": "skill package security rule",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M54 docs must not claim raw media export implementation": "raw media export is implemented",
        "M54 docs must not claim OCIO transform implementation": "ocio transform is implemented",
        "M54 docs must not claim AI gamut expansion implementation": "ai gamut expansion is implemented",
        "M54 docs must not claim model calls": "model call is implemented",
        "M54 docs must not claim M55 implementation": "m55 is implemented",
        "M54 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m55_redacted_observability_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 59, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M55_REDACTED_OBSERVABILITY_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M55 redacted observability doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M55 docs must say Redacted Observability Export": "redacted observability export",
        "M55 docs must say redacted-only": "redacted-only",
        "M55 docs must say contract-only": "contract-only",
        "M55 docs must deny external SaaS": "no external saas",
        "M55 docs must deny network delivery": "no network delivery",
        "M55 docs must deny raw prompt export": "no raw prompt",
        "M55 docs must deny raw provider payload export": "no raw provider payload",
        "M55 docs must deny raw private content": "no raw private content",
        "M55 docs must deny secrets": "no secrets",
        "M55 docs must deny forensic trace export": "no forensic trace export",
        "M55 docs must deny model calls": "no model call",
        "M55 docs must deny memory writes": "no memory write",
        "M55 docs must deny context injection": "no context injection",
        "M55 docs must deny backend routes": "no backend route",
        "M55 docs must deny Control Center controls": "no control center control",
        "M55 docs must deny dependencies": "no dependency",
        "M55 docs must deny production authority": "no production authority",
        "M55 docs must keep M56 future": "m56 remains future",
        "M55 Foundation Gate docs must mention Skill Package Security Rule": "skill package security rule",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M55 active docs must not allow user-enabled forensic trace export": "unless the user explicitly enables forensic trace export",
        "M55 docs must not claim external delivery implementation": "external delivery is implemented",
        "M55 docs must not claim network delivery implementation": "network delivery is implemented",
        "M55 docs must not claim raw prompt export implementation": "raw prompt export is implemented",
        "M55 docs must not claim provider payload export implementation": "provider payload export is implemented",
        "M55 docs must not claim model calls": "model call is implemented",
        "M55 docs must not claim M56 implementation": "m56 is implemented",
        "M55 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m56_agent_eval_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 60, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M56_AGENT_EVAL_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M56 agent eval doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M56 docs must say Agent Eval Regression Harness": "agent eval regression harness",
        "M56 docs must say deterministic": "deterministic",
        "M56 docs must say contract-only": "contract-only",
        "M56 docs must deny model calls": "no model call",
        "M56 docs must deny provider calls": "no provider call",
        "M56 docs must deny tool execution": "no tool execution",
        "M56 docs must deny shell execution": "no shell execution",
        "M56 docs must deny browser automation": "no browser automation",
        "M56 docs must deny network access": "no network access",
        "M56 docs must deny memory writes": "no memory write",
        "M56 docs must deny context injection": "no context injection",
        "M56 docs must deny raw prompt capture": "no raw prompt",
        "M56 docs must deny raw provider payload capture": "no raw provider payload",
        "M56 docs must deny backend routes": "no backend route",
        "M56 docs must deny Control Center controls": "no control center control",
        "M56 docs must deny dependencies": "no dependency",
        "M56 docs must deny production authority": "no production authority",
        "M56 docs must keep M57 future": "m57 remains future",
        "M56 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M56 docs must not claim eval execution API": "eval execution api is implemented",
        "M56 docs must not claim model calls": "model call is implemented",
        "M56 docs must not claim provider calls": "provider call is implemented",
        "M56 docs must not claim tool execution": "tool execution is implemented",
        "M56 docs must not claim network access": "network access is implemented",
        "M56 docs must not claim M57 implementation": "m57 is implemented",
        "M56 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m57_runtime_sandbox_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 61, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M57_RUNTIME_SANDBOX_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M57 runtime sandbox doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M57 docs must say Runtime Sandbox Architecture Review": "runtime sandbox architecture review",
        "M57 docs must say architecture review only": "architecture review only",
        "M57 docs must say contract-only": "contract-only",
        "M57 docs must deny sandbox execution": "no sandbox execution",
        "M57 docs must deny subprocess": "no subprocess",
        "M57 docs must deny shell execution": "no shell execution",
        "M57 docs must deny process spawn": "no process spawn",
        "M57 docs must deny file mutation": "no file mutation",
        "M57 docs must deny network access": "no network access",
        "M57 docs must deny tool execution": "no tool execution",
        "M57 docs must deny memory writes": "no memory write",
        "M57 docs must deny context injection": "no context injection",
        "M57 docs must deny backend routes": "no backend route",
        "M57 docs must deny dependencies": "no dependency",
        "M57 docs must deny production authority": "no production authority",
        "M57 docs must keep M58 future": "m58 remains future",
        "M57 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M57 docs must not claim sandbox execution": "sandbox execution is implemented",
        "M57 docs must not claim subprocess execution": "subprocess execution is implemented",
        "M57 docs must not claim shell execution": "shell execution is implemented",
        "M57 docs must not claim process spawn": "process spawn is implemented",
        "M57 docs must not claim file mutation": "file mutation is implemented",
        "M57 docs must not claim network access": "network access is implemented",
        "M57 docs must not claim M58 implementation": "m58 is implemented",
        "M57 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m58_dry_run_audit_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 62, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M58_DRY_RUN_AUDIT_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M58 dry-run execution audit doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M58 docs must say Dry-Run Execution Audit Harness": (
            "dry-run execution audit harness"
        ),
        "M58 docs must say dry-run-only": "dry-run-only",
        "M58 docs must say contract-only": "contract-only",
        "M58 docs must deny real execution": "no real execution",
        "M58 docs must deny tool execution": "no tool execution",
        "M58 docs must deny subprocess": "no subprocess",
        "M58 docs must deny shell execution": "no shell execution",
        "M58 docs must deny process spawn": "no process spawn",
        "M58 docs must deny file mutation": "no file mutation",
        "M58 docs must deny network access": "no network access",
        "M58 docs must deny model calls": "no model call",
        "M58 docs must deny memory writes": "no memory write",
        "M58 docs must deny context injection": "no context injection",
        "M58 docs must deny browser automation": "no browser automation",
        "M58 docs must deny plugin execution": "no plugin execution",
        "M58 docs must deny backend routes": "no backend route",
        "M58 docs must deny Control Center controls": "no control center control",
        "M58 docs must deny dependencies": "no dependency",
        "M58 docs must deny production authority": "no production authority",
        "M58 docs must keep M59 future": "m59 remains future",
        "M58 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M58 docs must not claim real execution": "real execution is implemented",
        "M58 docs must not claim tool execution": "tool execution is implemented",
        "M58 docs must not claim subprocess execution": "subprocess execution is implemented",
        "M58 docs must not claim shell execution": "shell execution is implemented",
        "M58 docs must not claim process spawn": "process spawn is implemented",
        "M58 docs must not claim file mutation": "file mutation is implemented",
        "M58 docs must not claim network access": "network access is implemented",
        "M58 docs must not claim model calls": "model call is implemented",
        "M58 docs must not claim M59 implementation": "m59 is implemented",
        "M58 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m59_public_github_readiness_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 63, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M59_PUBLIC_GITHUB_READINESS_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M59 public GitHub readiness doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M59 docs must say Public GitHub Readiness": "public github readiness",
        "M59 docs must say review-only": "review-only",
        "M59 docs must say contract-only": "contract-only",
        "M59 docs must deny GitHub push": "no github push",
        "M59 docs must deny GitHub release": "no github release",
        "M59 docs must deny wiki automation": "no wiki automation",
        "M59 docs must deny artifact upload": "no artifact upload",
        "M59 docs must deny external service": "no external service",
        "M59 docs must deny credential handling": "no credential handling",
        "M59 docs must deny network access": "no network access",
        "M59 docs must deny backend routes": "no backend route",
        "M59 docs must deny Control Center controls": "no control center control",
        "M59 docs must deny dependencies": "no dependency",
        "M59 docs must deny production authority": "no production authority",
        "M59 docs must keep M60 future": "m60 remains future",
        "M59 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M59 docs must not claim GitHub push implementation": "github push is implemented",
        "M59 docs must not claim GitHub release automation": (
            "github release automation is implemented"
        ),
        "M59 docs must not claim wiki automation": "wiki automation is implemented",
        "M59 docs must not claim artifact upload": "artifact upload is implemented",
        "M59 docs must not claim external service": "external service is implemented",
        "M59 docs must not claim credential handling": "credential handling is implemented",
        "M59 docs must not claim production authority": "production authority is implemented",
        "M59 docs must not claim M60 implementation": "m60 is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m60_local_developer_beta_freeze_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 64, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M60_LOCAL_DEVELOPER_BETA_FREEZE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M60 local developer beta freeze doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M60 docs must say Local Developer Beta Freeze": "local developer beta freeze",
        "M60 docs must say freeze-only": "freeze-only",
        "M60 docs must say local developer beta only": "local developer beta only",
        "M60 docs must say review-only": "review-only",
        "M60 docs must deny public release": "no public release",
        "M60 docs must deny external distribution": "no external distribution",
        "M60 docs must deny post-M60 autonomy": "no post-m60 autonomy",
        "M60 docs must deny production authority": "no production authority",
        "M60 docs must deny execution": "no execution",
        "M60 docs must deny tool execution": "no tool execution",
        "M60 docs must deny shell execution": "no shell execution",
        "M60 docs must deny network tools": "no network tools",
        "M60 docs must deny browser automation": "no browser automation",
        "M60 docs must deny plugin execution": "no plugin execution",
        "M60 docs must deny mobile sensor access": "no mobile sensor access",
        "M60 docs must deny remote execution": "no remote execution",
        "M60 docs must deny credential handling": "no credential handling",
        "M60 docs must deny memory writes": "no memory writes",
        "M60 docs must deny context injection": "no context injection",
        "M60 docs must deny model/provider calls": "no model/provider calls",
        "M60 docs must deny backend routes": "no backend route",
        "M60 docs must deny Control Center controls": "no control center control",
        "M60 docs must deny dependencies": "no dependency",
        "M60 docs must keep M61+ future": "m61+ remains future",
        "M60 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    forbidden_fragments = {
        "M60 docs must not claim public release implementation": "public release is implemented",
        "M60 docs must not claim external distribution": "external distribution is implemented",
        "M60 docs must not claim post-M60 autonomy implementation": "post-m60 autonomy is implemented",
        "M60 docs must not claim production authority": "production authority is implemented",
        "M60 docs must not claim M61 implementation": "m61 is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m61_autonomy_mode_charter_docs(root: Path, version: str | None) -> list[str]:
    if _version_tuple(version) < (0, 65, 0):
        return []

    failures: list[str] = []
    parts: list[str] = []
    for rel_path in REQUIRED_M61_AUTONOMY_MODE_CHARTER_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active M61 autonomy mode charter doc: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M61 docs must say Autonomy Mode Charter": "autonomy mode charter",
        "M61 docs must say authority levels": "authority levels",
        "M61 docs must define Mode 0": "mode 0",
        "M61 docs must define Mode 1": "mode 1",
        "M61 docs must define Mode 2": "mode 2",
        "M61 docs must define Mode 3": "mode 3",
        "M61 docs must define Mode 4": "mode 4",
        "M61 docs must define Mode 5": "mode 5",
        "M61 docs must define Mode 6": "mode 6",
        "M61 docs must say default mode off": "default mode off",
        "M61 docs must say disabled by default": "disabled by default",
        "M61 docs must say dry-run first": "dry-run first",
        "M61 docs must say limited allowlist": "limited allowlist",
        "M61 docs must say explicit approval": "explicit approval",
        "M61 docs must say scoped autonomy window": "scoped autonomy window",
        "M61 docs must say audit/replay": "audit/replay",
        "M61 docs must say revocation": "revocation",
        "M61 docs must deny global autonomy switch": "no global autonomy switch",
        "M61 docs must deny production authority": "no production authority",
        "M61 docs must deny execution": "no execution",
        "M61 docs must deny tool execution": "no tool execution",
        "M61 docs must deny browser automation": "no browser automation",
        "M61 docs must deny shell execution": "no shell execution",
        "M61 docs must deny network tools": "no network tools",
        "M61 docs must deny background worker": "no background worker",
        "M61 docs must deny autonomous session": "no autonomous session",
        "M61 docs must deny backend routes": "no backend route",
        "M61 docs must deny dependencies": "no dependency",
        "M61 docs must keep M62 future": "m62 remains future",
        "M61 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.66.0", "m62", "scoped autonomy session contracts"),
        ("v0.67.0", "m63", "autonomy policy engine v1"),
        ("v0.68.0", "m64", "autonomous plan simulator"),
        ("v0.69.0", "m65", "autonomy audit + replay viewer"),
        ("v0.74.0", "m70", "autonomy foundation freeze"),
        ("v0.80.0", "m76", "openwebui runtime bridge v1"),
        ("v0.81.0", "m77", "openwebui safe handoff execution"),
        ("v0.82.0", "m78", "plugin manifest security model"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M61-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M61 docs must not claim global autonomy implementation": "global autonomy switch is implemented",
        "M61 docs must not claim production authority": "production authority is implemented",
        "M61 docs must not claim execution": "execution is implemented",
        "M61 docs must not claim tool execution": "tool execution is implemented",
        "M61 docs must not claim shell execution": "shell execution is implemented",
        "M61 docs must not claim browser automation": "browser automation is implemented",
    }
    if _version_tuple(version) < (0, 66, 0):
        forbidden_fragments["M61 docs must not claim M62 implementation"] = "m62 is implemented"
    if _version_tuple(version) < (0, 67, 0):
        forbidden_fragments["M61 docs must not claim M63 implementation"] = "m63 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m62_scoped_autonomy_session_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 66, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M62_SCOPED_AUTONOMY_SESSION_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M62 scoped autonomy session doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M62 docs must say scoped autonomy session contracts": "scoped autonomy session contracts",
        "M62 docs must say contract-only": "contract-only",
        "M62 docs must say review-only": "review-only",
        "M62 docs must say actor-bound": "actor-bound",
        "M62 docs must say resource-bound": "resource-bound",
        "M62 docs must say duration-bound": "duration-bound",
        "M62 docs must say allowlist": "allowlist",
        "M62 docs must say revocation": "revocation",
        "M62 docs must say audit/replay": "audit/replay",
        "M62 docs must deny session start": "no session start",
        "M62 docs must deny session activation": "no session activation",
        "M62 docs must deny autonomous actions": "no autonomous actions",
        "M62 docs must deny background worker": "no background worker",
        "M62 docs must deny execution": "no execution",
        "M62 docs must deny tool execution": "no tool execution",
        "M62 docs must deny shell execution": "no shell execution",
        "M62 docs must deny network tools": "no network tools",
        "M62 docs must deny browser automation": "no browser automation",
        "M62 docs must deny backend routes": "no backend route",
        "M62 docs must deny dependencies": "no dependency",
        "M62 docs must keep M63 future": "m63 remains future",
        "M62 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.67.0", "m63", "autonomy policy engine v1"),
        ("v0.68.0", "m64", "autonomous plan simulator"),
        ("v0.69.0", "m65", "autonomy audit + replay viewer"),
        ("v0.70.0", "m66", "scoped approval bundles"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M62-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M62 docs must not claim session start": "session start is implemented",
        "M62 docs must not claim session activation": "session activation is implemented",
        "M62 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M62 docs must not claim background workers": "background workers are implemented",
        "M62 docs must not claim execution": "execution is implemented",
        "M62 docs must not claim tool execution": "tool execution is implemented",
        "M62 docs must not claim shell execution": "shell execution is implemented",
        "M62 docs must not claim browser automation": "browser automation is implemented",
        "M62 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 67, 0):
        forbidden_fragments["M62 docs must not claim M63 implementation"] = "m63 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m63_autonomy_policy_engine_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 67, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M63_AUTONOMY_POLICY_ENGINE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M63 autonomy policy engine doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M63 docs must say autonomy policy engine v1": "autonomy policy engine v1",
        "M63 docs must say contract-only": "contract-only",
        "M63 docs must say review-only": "review-only",
        "M63 docs must say policy rules": "policy rules",
        "M63 docs must say actor-bound": "actor-bound",
        "M63 docs must say resource-bound": "resource-bound",
        "M63 docs must say capability-bound": "capability-bound",
        "M63 docs must say allowlist": "allowlist",
        "M63 docs must say risk ceiling": "risk ceiling",
        "M63 docs must say duration ceiling": "duration ceiling",
        "M63 docs must say revocation": "revocation",
        "M63 docs must say audit/replay": "audit/replay",
        "M63 docs must say approval refs are identifiers": "approval refs are identifiers",
        "M63 docs must deny policy activation": "no policy activation",
        "M63 docs must deny session start": "no session start",
        "M63 docs must deny autonomous actions": "no autonomous actions",
        "M63 docs must deny background worker": "no background worker",
        "M63 docs must deny execution": "no execution",
        "M63 docs must deny tool execution": "no tool execution",
        "M63 docs must deny shell execution": "no shell execution",
        "M63 docs must deny network tools": "no network tools",
        "M63 docs must deny browser automation": "no browser automation",
        "M63 docs must deny backend routes": "no backend route",
        "M63 docs must deny dependencies": "no dependency",
        "M63 Foundation Gate docs must mention Skill Package Security Rule": (
            "skill package security rule"
        ),
    }
    if _version_tuple(version) < (0, 68, 0):
        required_fragments["M63 docs must keep M64 future"] = "m64 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.68.0", "m64", "autonomous plan simulator"),
        ("v0.69.0", "m65", "autonomy audit + replay viewer"),
        ("v0.70.0", "m66", "scoped approval bundles"),
        ("v0.71.0", "m67", "revocation + kill switch"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M63-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M63 docs must not claim policy activation": "policy activation is implemented",
        "M63 docs must not claim session start": "session start is implemented",
        "M63 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M63 docs must not claim background workers": "background workers are implemented",
        "M63 docs must not claim execution": "execution is implemented",
        "M63 docs must not claim tool execution": "tool execution is implemented",
        "M63 docs must not claim shell execution": "shell execution is implemented",
        "M63 docs must not claim browser automation": "browser automation is implemented",
        "M63 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 68, 0):
        forbidden_fragments["M63 docs must not claim M64 implementation"] = "m64 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m64_autonomous_plan_simulator_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 68, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M64_AUTONOMOUS_PLAN_SIMULATOR_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M64 autonomous plan simulator doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M64 docs must say autonomous plan simulator": "autonomous plan simulator",
        "M64 docs must say contract-only": "contract-only",
        "M64 docs must say review-only": "review-only",
        "M64 docs must say dry-run-only": "dry-run-only",
        "M64 docs must say deterministic": "deterministic",
        "M64 docs must say dependency graph": "dependency graph",
        "M64 docs must say acyclic": "acyclic",
        "M64 docs must deny duplicate dependencies": "duplicate",
        "M64 docs must deny missing dependencies": "missing",
        "M64 docs must say policy decision": "policy decision",
        "M64 docs must say approval refs are identifiers": "approval refs are identifiers",
        "M64 docs must deny policy activation": "no policy activation",
        "M64 docs must deny session start": "no session start",
        "M64 docs must deny autonomous actions": "no autonomous actions",
        "M64 docs must deny background workers": "no background worker",
        "M64 docs must deny execution": "no execution",
        "M64 docs must deny tool execution": "no tool execution",
        "M64 docs must deny shell execution": "no shell execution",
        "M64 docs must deny network tools": "no network tools",
        "M64 docs must deny browser automation": "no browser automation",
        "M64 docs must deny context injection": "no context injection",
        "M64 docs must deny memory writes": "no memory write",
        "M64 docs must deny backend routes": "no backend route",
        "M64 docs must deny dependencies": "no dependency",
    }
    if _version_tuple(version) < (0, 69, 0):
        required_fragments["M64 docs must keep M65 future"] = "m65 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.69.0", "m65", "autonomy audit + replay viewer"),
        ("v0.70.0", "m66", "scoped approval bundles"),
        ("v0.71.0", "m67", "revocation + kill switch"),
        ("v0.72.0", "m68", "autonomy risk classifier"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M64-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M64 docs must not claim policy activation": "policy activation is implemented",
        "M64 docs must not claim session start": "session start is implemented",
        "M64 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M64 docs must not claim background workers": "background workers are implemented",
        "M64 docs must not claim execution": "execution is implemented",
        "M64 docs must not claim tool execution": "tool execution is implemented",
        "M64 docs must not claim shell execution": "shell execution is implemented",
        "M64 docs must not claim browser automation": "browser automation is implemented",
        "M64 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 69, 0):
        forbidden_fragments["M64 docs must not claim M65 implementation"] = "m65 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m65_autonomy_audit_replay_viewer_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 69, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M65_AUTONOMY_AUDIT_REPLAY_VIEWER_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M65 autonomy audit replay viewer doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M65 docs must say autonomy audit": "autonomy audit",
        "M65 docs must say replay viewer": "replay viewer",
        "M65 docs must say contract-only": "contract-only",
        "M65 docs must say review-only": "review-only",
        "M65 docs must say replay-view-only": "replay-view-only",
        "M65 docs must say deterministic": "deterministic",
        "M65 docs must say exact simulation result": "exact simulation result",
        "M65 docs must say exact replay step": "exact replay step",
        "M65 docs must say approval refs are identifiers": "approval refs are identifiers",
        "M65 docs must deny policy activation": "no policy activation",
        "M65 docs must deny session start": "no session start",
        "M65 docs must deny autonomous actions": "no autonomous actions",
        "M65 docs must deny background workers": "no background worker",
        "M65 docs must deny execution": "no execution",
        "M65 docs must deny tool execution": "no tool execution",
        "M65 docs must deny shell execution": "no shell execution",
        "M65 docs must deny network tools": "no network tools",
        "M65 docs must deny browser automation": "no browser automation",
        "M65 docs must deny context injection": "no context injection",
        "M65 docs must deny memory writes": "no memory write",
        "M65 docs must deny backend routes": "no backend route",
        "M65 docs must deny dependencies": "no dependency",
    }
    if _version_tuple(version) < (0, 70, 0):
        required_fragments["M65 docs must keep M66 future"] = "m66 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.70.0", "m66", "scoped approval bundles"),
        ("v0.71.0", "m67", "revocation + kill switch"),
        ("v0.72.0", "m68", "autonomy risk classifier"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M65-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M65 docs must not claim policy activation": "policy activation is implemented",
        "M65 docs must not claim session start": "session start is implemented",
        "M65 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M65 docs must not claim background workers": "background workers are implemented",
        "M65 docs must not claim execution": "execution is implemented",
        "M65 docs must not claim tool execution": "tool execution is implemented",
        "M65 docs must not claim shell execution": "shell execution is implemented",
        "M65 docs must not claim browser automation": "browser automation is implemented",
        "M65 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 70, 0):
        forbidden_fragments["M65 docs must not claim M66 implementation"] = "m66 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m66_scoped_approval_bundle_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 70, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M66_SCOPED_APPROVAL_BUNDLE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M66 scoped approval bundle doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M66 docs must say scoped approval bundles": "scoped approval bundles",
        "M66 docs must say contract-only": "contract-only",
        "M66 docs must say review-only": "review-only",
        "M66 docs must say exact-scope": "exact-scope",
        "M66 docs must say actor-bound": "actor-bound",
        "M66 docs must say resource-bound": "resource-bound",
        "M66 docs must say capability-bound": "capability-bound",
        "M66 docs must say allowlist-bound": "allowlist-bound",
        "M66 docs must say non-transferable": "non-transferable",
        "M66 docs must say revocable": "revocable",
        "M66 docs must say replay-safe": "replay-safe",
        "M66 docs must say approval refs are identifiers": "approval refs are identifiers",
        "M66 docs must deny policy activation": "no policy activation",
        "M66 docs must deny session start": "no session start",
        "M66 docs must deny autonomous actions": "no autonomous actions",
        "M66 docs must deny background worker": "no background worker",
        "M66 docs must deny execution": "no execution",
        "M66 docs must deny tool execution": "no tool execution",
        "M66 docs must deny shell execution": "no shell execution",
        "M66 docs must deny network tools": "no network tools",
        "M66 docs must deny browser automation": "no browser automation",
        "M66 docs must deny context injection": "no context injection",
        "M66 docs must deny memory writes": "no memory write",
        "M66 docs must deny backend routes": "no backend route",
        "M66 docs must deny dependencies": "no dependency",
    }
    if _version_tuple(version) < (0, 71, 0):
        required_fragments["M66 docs must keep M67 future"] = "m67 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.71.0", "m67", "revocation + kill switch"),
        ("v0.72.0", "m68", "autonomy risk classifier"),
        ("v0.73.0", "m69", "low-risk autonomous dry run"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M66-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M66 docs must not claim policy activation": "policy activation is implemented",
        "M66 docs must not claim session start": "session start is implemented",
        "M66 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M66 docs must not claim background workers": "background workers are implemented",
        "M66 docs must not claim execution": "execution is implemented",
        "M66 docs must not claim tool execution": "tool execution is implemented",
        "M66 docs must not claim shell execution": "shell execution is implemented",
        "M66 docs must not claim browser automation": "browser automation is implemented",
        "M66 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 71, 0):
        forbidden_fragments["M66 docs must not claim M67 implementation"] = "m67 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m67_revocation_kill_switch_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 71, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M67_REVOCATION_KILL_SWITCH_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M67 revocation kill switch doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M67 docs must say revocation + kill switch": "revocation + kill switch",
        "M67 docs must say contract-only": "contract-only",
        "M67 docs must say review-only": "review-only",
        "M67 docs must say exact-bound": "exact-bound",
        "M67 docs must say scoped approval bundle": "scoped approval bundle",
        "M67 docs must say revocation requested": "revocation requested",
        "M67 docs must say kill-switch requested": "kill-switch requested",
        "M67 docs must say approval refs identifiers": "approval refs are identifiers",
        "M67 docs must deny revocation action": "no revocation action",
        "M67 docs must deny kill switch activation": "no kill-switch activation",
        "M67 docs must deny session stop": "no session stop",
        "M67 docs must deny process kill": "no process kill",
        "M67 docs must deny policy activation": "no policy activation",
        "M67 docs must deny session start": "no session start",
        "M67 docs must deny autonomous actions": "no autonomous actions",
        "M67 docs must deny background worker": "no background worker",
        "M67 docs must deny execution": "no execution",
        "M67 docs must deny tool execution": "no tool execution",
        "M67 docs must deny shell execution": "no shell execution",
        "M67 docs must deny network tools": "no network tools",
        "M67 docs must deny browser automation": "no browser automation",
        "M67 docs must deny context injection": "no context injection",
        "M67 docs must deny memory writes": "no memory write",
        "M67 docs must deny backend routes": "no backend route",
        "M67 docs must deny dependencies": "no dependency",
    }
    if _version_tuple(version) < (0, 72, 0):
        required_fragments["M67 docs must keep M68 future"] = "m68 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.72.0", "m68", "autonomy risk classifier"),
        ("v0.73.0", "m69", "low-risk autonomous dry run"),
        ("v0.74.0", "m70", "autonomy foundation freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M67-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M67 docs must not claim revocation action": "revocation action is implemented",
        "M67 docs must not claim kill switch activation": "kill-switch activation is implemented",
        "M67 docs must not claim session stop": "session stop is implemented",
        "M67 docs must not claim process kill": "process kill is implemented",
        "M67 docs must not claim policy activation": "policy activation is implemented",
        "M67 docs must not claim session start": "session start is implemented",
        "M67 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M67 docs must not claim background workers": "background workers are implemented",
        "M67 docs must not claim execution": "execution is implemented",
        "M67 docs must not claim tool execution": "tool execution is implemented",
        "M67 docs must not claim shell execution": "shell execution is implemented",
        "M67 docs must not claim browser automation": "browser automation is implemented",
        "M67 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 72, 0):
        forbidden_fragments["M67 docs must not claim M68 implementation"] = "m68 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m68_autonomy_risk_classifier_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 72, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M68_AUTONOMY_RISK_CLASSIFIER_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M68 autonomy risk classifier doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M68 docs must say autonomy risk classifier": "autonomy risk classifier",
        "M68 docs must say contract-only": "contract-only",
        "M68 docs must say review-only": "review-only",
        "M68 docs must say deterministic": "deterministic",
        "M68 docs must say highest risk": "highest risk",
        "M68 docs must say declared risk": "declared risk",
        "M68 docs must say scoped approval bundle risk": "scoped approval bundle risk",
        "M68 docs must say explicit risk signals": "explicit risk signals",
        "M68 docs must deny risk downgrade": "risk downgrade is denied",
        "M68 docs must bind scoped approval bundles": "scoped approval bundle",
        "M68 docs must bind revocation records": "revocation + kill switch",
        "M68 docs must say approval refs identifiers": "approval refs are identifiers",
        "M68 docs must deny approval_test refs": "approval_test_",
        "M68 docs must say evaluator revalidation": "evaluator boundaries revalidate",
        "M68 docs must deny policy activation": "no policy activation",
        "M68 docs must deny session start": "no session start",
        "M68 docs must deny autonomous actions": "no autonomous actions",
        "M68 docs must deny background worker": "no background worker",
        "M68 docs must deny execution": "no execution",
        "M68 docs must deny tool execution": "no tool execution",
        "M68 docs must deny shell execution": "no shell execution",
        "M68 docs must deny network tools": "no network tools",
        "M68 docs must deny browser automation": "no browser automation",
        "M68 docs must deny context injection": "no context injection",
        "M68 docs must deny memory writes": "no memory write",
        "M68 docs must deny model/provider authority": "no model/provider authority",
        "M68 docs must deny backend routes": "no backend route",
        "M68 docs must deny Control Center controls": "no control center control",
        "M68 docs must deny dependencies": "no dependency",
        "M68 docs must deny production authority": "no production authority",
    }
    if _version_tuple(version) < (0, 73, 0):
        required_fragments["M68 docs must keep M69 future"] = "m69 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.73.0", "m69", "low-risk autonomous dry run"),
        ("v0.74.0", "m70", "autonomy foundation freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M68-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M68 docs must not claim policy activation": "policy activation is implemented",
        "M68 docs must not claim session start": "session start is implemented",
        "M68 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M68 docs must not claim background workers": "background workers are implemented",
        "M68 docs must not claim execution": "execution is implemented",
        "M68 docs must not claim tool execution": "tool execution is implemented",
        "M68 docs must not claim shell execution": "shell execution is implemented",
        "M68 docs must not claim browser automation": "browser automation is implemented",
        "M68 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 73, 0):
        forbidden_fragments["M68 docs must not claim M69 implementation"] = "m69 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m69_low_risk_autonomous_dry_run_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 73, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M69_LOW_RISK_AUTONOMOUS_DRY_RUN_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M69 low-risk autonomous dry-run doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M69 docs must say low-risk autonomous dry run": "low-risk autonomous dry run",
        "M69 docs must say contract-only": "contract-only",
        "M69 docs must say review-only": "review-only",
        "M69 docs must say dry-run-only": "dry-run-only",
        "M69 docs must say deterministic": "deterministic",
        "M69 docs must say low risk": "low risk",
        "M69 docs must say risk ceiling": "risk ceiling",
        "M69 docs must bind M68 risk decisions": "autonomy risk classifier",
        "M69 docs must say approval refs identifiers": "approval refs are identifiers",
        "M69 docs must deny approval_test refs": "approval_test_",
        "M69 docs must say evaluator revalidation": "evaluator boundaries revalidate",
        "M69 docs must deny policy activation": "no policy activation",
        "M69 docs must deny session start": "no session start",
        "M69 docs must deny autonomous actions": "no autonomous actions",
        "M69 docs must deny background worker": "no background worker",
        "M69 docs must deny execution": "no execution",
        "M69 docs must deny tool execution": "no tool execution",
        "M69 docs must deny shell execution": "no shell execution",
        "M69 docs must deny network tools": "no network tools",
        "M69 docs must deny browser automation": "no browser automation",
        "M69 docs must deny context injection": "no context injection",
        "M69 docs must deny memory writes": "no memory write",
        "M69 docs must deny model/provider authority": "no model/provider authority",
        "M69 docs must deny backend routes": "no backend route",
        "M69 docs must deny Control Center controls": "no control center control",
        "M69 docs must deny dependencies": "no dependency",
        "M69 docs must deny production authority": "no production authority",
    }
    if _version_tuple(version) < (0, 74, 0):
        required_fragments["M69 docs must keep M70 future"] = "m70 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.74.0", "m70", "autonomy foundation freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M69-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M69 docs must not claim policy activation": "policy activation is implemented",
        "M69 docs must not claim session start": "session start is implemented",
        "M69 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M69 docs must not claim background workers": "background workers are implemented",
        "M69 docs must not claim execution": "execution is implemented",
        "M69 docs must not claim tool execution": "tool execution is implemented",
        "M69 docs must not claim shell execution": "shell execution is implemented",
        "M69 docs must not claim browser automation": "browser automation is implemented",
        "M69 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 74, 0):
        forbidden_fragments["M69 docs must not claim M70 implementation"] = "m70 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m70_autonomy_foundation_freeze_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 74, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M70_AUTONOMY_FOUNDATION_FREEZE_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M70 autonomy foundation freeze doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M70 docs must say autonomy foundation freeze": "autonomy foundation freeze",
        "M70 docs must say M61-M69": "m61-m69",
        "M70 docs must say contract-only": "contract-only",
        "M70 docs must say review-only": "review-only",
        "M70 docs must say freeze-only": "freeze-only",
        "M70 docs must say deterministic": "deterministic",
        "M70 docs must say accepted milestone refs": "accepted milestone refs",
        "M70 docs must say checklist refs": "checklist refs",
        "M70 docs must say evaluator revalidation": "evaluator boundaries revalidate",
        "M70 docs must deny policy activation": "no policy activation",
        "M70 docs must deny session start": "no session start",
        "M70 docs must deny low-risk dry-run execution": "no low-risk dry-run execution",
        "M70 docs must deny autonomous actions": "no autonomous actions",
        "M70 docs must deny background worker": "no background worker",
        "M70 docs must deny execution": "no execution",
        "M70 docs must deny tool execution": "no tool execution",
        "M70 docs must deny shell execution": "no shell execution",
        "M70 docs must deny network tool": "no network tool",
        "M70 docs must deny browser automation": "no browser automation",
        "M70 docs must deny plugin execution": "no plugin execution",
        "M70 docs must deny mobile sensors": "no mobile sensor",
        "M70 docs must deny remote execution": "no remote execution",
        "M70 docs must deny memory writes": "no memory write",
        "M70 docs must deny context injection": "no context injection",
        "M70 docs must deny model/provider calls": "no model/provider call",
        "M70 docs must deny backend routes": "no backend route",
        "M70 docs must deny Control Center controls": "no control center control",
        "M70 docs must deny dependencies": "no dependency",
        "M70 docs must deny production authority": "no production authority",
        "M70 docs must keep M71 future": "m71 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.74.0", "m70", "autonomy foundation freeze"),
        ("v0.75.0", "m71", "network tool contract review"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M70-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M70 docs must not claim policy activation": "policy activation is implemented",
        "M70 docs must not claim session start": "session start is implemented",
        "M70 docs must not claim autonomous actions": "autonomous actions are implemented",
        "M70 docs must not claim background workers": "background workers are implemented",
        "M70 docs must not claim execution": "execution is implemented",
        "M70 docs must not claim tool execution": "tool execution is implemented",
        "M70 docs must not claim shell execution": "shell execution is implemented",
        "M70 docs must not claim browser automation": "browser automation is implemented",
        "M70 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m71_network_tool_contract_review_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 75, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M71_NETWORK_TOOL_CONTRACT_REVIEW_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M71 network tool contract review doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M71 docs must say network tool contract review": "network tool contract review",
        "M71 docs must say contract-only": "contract-only",
        "M71 docs must say review-only": "review-only",
        "M71 docs must say disabled by default": "disabled by default",
        "M71 docs must keep M72 future": "m72 remains future",
        "M71 docs must deny network calls": "no network call",
        "M71 docs must deny HTTP fetch": "no http fetch",
        "M71 docs must deny unrestricted network tools": "no network tool",
        "M71 docs must deny authenticated network actions": "no authenticated network action",
        "M71 docs must deny credentials/cookies": "no credentials or cookies",
        "M71 docs must deny request bodies": "no request body",
        "M71 docs must deny non-GET methods": "no non-get method",
        "M71 docs must deny download/export": "no download or export",
        "M71 docs must deny raw response body": "no raw response body",
        "M71 docs must deny backend routes": "no backend route",
        "M71 docs must deny Control Center controls": "no control center control",
        "M71 docs must deny dependencies": "no dependency",
        "M71 docs must deny production authority": "no production authority",
        "M71 docs must say evaluator revalidation": "evaluator boundaries revalidate",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.75.0", "m71", "network tool contract review"),
        ("v0.76.0", "m72", "read-only http fetch tool, allowlisted"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M71-M100 roadmap missing planned label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M71 docs must not claim network call implementation": "network call is implemented",
        "M71 docs must not claim HTTP fetch implementation": "http fetch is implemented",
        "M71 docs must not claim unrestricted network implementation": "unrestricted network tool is implemented",
        "M71 docs must not claim authenticated network implementation": "authenticated network action is implemented",
        "M71 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m72_read_only_http_fetch_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 76, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M72_READ_ONLY_HTTP_FETCH_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M72 read-only HTTP fetch doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M72 docs must say read-only HTTP fetch": "read-only http fetch",
        "M72 docs must say allowlisted": "allowlisted",
        "M72 docs must say bounded redacted preview": "bounded redacted preview",
        "M72 docs must say redaction before return": "redaction before return",
        "M72 docs must deny credentials/cookies": "no credentials or cookies",
        "M72 docs must deny request bodies": "no request body",
        "M72 docs must deny non-GET methods": "no non-get method",
        "M72 docs must deny raw response bodies": "no raw response body",
        "M72 docs must deny raw headers": "no raw headers",
        "M72 docs must deny download/export": "no download or export",
        "M72 docs must deny context injection": "no context injection",
        "M72 docs must deny memory writes": "no memory write",
        "M72 docs must deny model calls": "no model call",
        "M72 docs must deny browser automation": "no browser automation",
        "M72 docs must deny backend routes": "no backend route",
        "M72 docs must deny Control Center controls": "no control center control",
        "M72 docs must deny dependencies": "no dependency",
        "M72 docs must deny production authority": "no production authority",
        "M72 docs must keep M73 future": "m73 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.76.0", "m72", "read-only http fetch tool, allowlisted"),
        ("v0.77.0", "m73", "browser automation contract review"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M72-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M72 docs must not claim unrestricted network implementation": "unrestricted network tool is implemented",
        "M72 docs must not claim authenticated network implementation": "authenticated network action is implemented",
        "M72 docs must not claim browser automation implementation": "browser automation is implemented",
        "M72 docs must not claim tool execution implementation": "tool execution is implemented",
        "M72 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 77, 0):
        forbidden_fragments["M72 docs must not claim M73 implementation"] = "m73 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m73_browser_automation_contract_review_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 77, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M73 browser automation contract review doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M73 docs must say browser automation contract review": "browser automation contract review",
        "M73 docs must say contract-only": "contract-only",
        "M73 docs must say review-only": "review-only",
        "M73 docs must say disabled by default": "disabled by default",
        "M73 docs must deny browser automation": "no browser automation",
        "M73 docs must deny browser observe": "no browser observe",
        "M73 docs must deny browser navigation": "no browser navigation",
        "M73 docs must deny browser click": "no browser click",
        "M73 docs must deny form fill": "no form fill",
        "M73 docs must deny screenshot": "no screenshot",
        "M73 docs must deny raw DOM": "no raw dom",
        "M73 docs must deny authenticated browser profile": "no authenticated browser profile",
        "M73 docs must deny download/upload": "no download or upload",
        "M73 docs must deny remote browser": "no remote browser",
        "M73 docs must deny network interception": "no network interception",
        "M73 docs must deny backend routes": "no backend route",
        "M73 docs must deny Control Center controls": "no control center control",
        "M73 docs must deny dependencies": "no dependency",
        "M73 docs must deny production authority": "no production authority",
        "M73 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M73 docs must keep M74 future": "m74 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.77.0", "m73", "browser automation contract review"),
        ("v0.78.0", "m74", "browser observe-only adapter"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M73-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M73 docs must not claim browser observe adapter implementation": (
            "browser observe-only adapter is implemented"
        ),
        "M73 docs must not claim browser automation execution": "browser automation execution is implemented",
        "M73 docs must not claim browser click execution": "browser click execution is implemented",
        "M73 docs must not claim tool execution implementation": "tool execution is implemented",
        "M73 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 78, 0):
        forbidden_fragments["M73 docs must not claim M74 implementation"] = "m74 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m74_browser_observe_only_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 78, 0):
        return failures
    parts: list[str] = []
    for rel_path in REQUIRED_M74_BROWSER_OBSERVE_ONLY_DOCS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"M74 browser observe-only doc missing: {rel_path}")
            continue
        parts.append(_read(path).lower())
    text = "\n".join(parts)
    required_fragments = {
        "M74 docs must say browser observe-only adapter": "browser observe-only adapter",
        "M74 docs must say observe-only": "observe-only",
        "M74 docs must require injected observation": "injected observation",
        "M74 docs must say redacted visible text": "redacted visible text",
        "M74 docs must say safe refs only": "safe refs only",
        "M74 docs must deny browser automation": "no browser automation",
        "M74 docs must deny browser navigation": "no browser navigation",
        "M74 docs must deny browser click": "no browser click",
        "M74 docs must deny form fill": "no form fill",
        "M74 docs must deny screenshot": "no screenshot",
        "M74 docs must deny raw DOM": "no raw dom",
        "M74 docs must deny authenticated browser profile": "no authenticated browser profile",
        "M74 docs must deny cookies or credentials": "no cookies or credentials",
        "M74 docs must deny download/upload": "no download or upload",
        "M74 docs must deny remote browser": "no remote browser",
        "M74 docs must deny network interception": "no network interception",
        "M74 docs must deny backend routes": "no backend route",
        "M74 docs must deny Control Center controls": "no control center control",
        "M74 docs must deny memory writes": "no memory write",
        "M74 docs must deny context injection": "no context injection",
        "M74 docs must deny dependencies": "no dependency",
        "M74 docs must deny production authority": "no production authority",
        "M74 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
    }
    if _version_tuple(version) < (0, 79, 0):
        required_fragments["M74 docs must keep M75 future"] = "m75 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.78.0", "m74", "browser observe-only adapter"),
        ("v0.79.0", "m75", "browser action dry-run planner"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M74-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M74 docs must not claim browser action dry-run implementation": (
            "browser action dry-run planner is implemented"
        ),
        "M74 docs must not claim browser automation execution": "browser automation execution is implemented",
        "M74 docs must not claim browser click execution": "browser click execution is implemented",
        "M74 docs must not claim tool execution implementation": "tool execution is implemented",
        "M74 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 79, 0):
        forbidden_fragments["M74 docs must not claim M75 implementation"] = "m75 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m75_browser_action_dry_run_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 79, 0):
        return failures

    missing = [rel_path for rel_path in REQUIRED_M75_BROWSER_ACTION_DRY_RUN_DOCS if not (root / rel_path).exists()]
    failures.extend(f"missing M75 browser action dry-run doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M75_BROWSER_ACTION_DRY_RUN_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M75 docs must say browser action dry-run planner": "browser action dry-run planner",
        "M75 docs must say dry-run only": "dry-run only",
        "M75 docs must say reviewable action plan": "reviewable action plan",
        "M75 docs must say safe refs only": "safe refs only",
        "M75 docs must deny browser action execution": "no browser action execution",
        "M75 docs must deny browser session start": "no browser session start",
        "M75 docs must deny browser navigation execution": "no browser navigation execution",
        "M75 docs must deny browser click execution": "no browser click execution",
        "M75 docs must deny form fill execution": "no form fill execution",
        "M75 docs must deny screenshot": "no screenshot",
        "M75 docs must deny raw DOM": "no raw dom",
        "M75 docs must deny authenticated browser profile": "no authenticated browser profile",
        "M75 docs must deny cookies or credentials": "no cookies or credentials",
        "M75 docs must deny download/upload": "no download or upload",
        "M75 docs must deny remote browser": "no remote browser",
        "M75 docs must deny network interception": "no network interception",
        "M75 docs must deny network calls": "no network call",
        "M75 docs must deny model calls": "no model call",
        "M75 docs must deny tool execution": "no tool execution",
        "M75 docs must deny backend routes": "no backend route",
        "M75 docs must deny Control Center controls": "no control center control",
        "M75 docs must deny memory writes": "no memory write",
        "M75 docs must deny context injection": "no context injection",
        "M75 docs must deny dependencies": "no dependency",
        "M75 docs must deny production authority": "no production authority",
        "M75 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
    }
    if _version_tuple(version) < (0, 80, 0):
        required_fragments["M75 docs must keep M76 future"] = "m76 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.79.0", "m75", "browser action dry-run planner"),
        ("v0.80.0", "m76", "openwebui runtime bridge v1"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M75-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M75 docs must not claim browser automation execution": "browser automation execution is implemented",
        "M75 docs must not claim browser click execution": "browser click execution is implemented",
        "M75 docs must not claim tool execution implementation": "tool execution is implemented",
        "M75 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 80, 0):
        forbidden_fragments["M75 docs must not claim M76 implementation"] = "m76 is implemented"
        forbidden_fragments["M75 docs must not claim OpenWebUI runtime bridge implementation"] = (
            "openwebui runtime bridge v1 is implemented"
        )
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m76_openwebui_runtime_bridge_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 80, 0):
        return failures

    missing = [rel_path for rel_path in REQUIRED_M76_OPENWEBUI_RUNTIME_BRIDGE_DOCS if not (root / rel_path).exists()]
    failures.extend(f"missing M76 OpenWebUI runtime bridge doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M76_OPENWEBUI_RUNTIME_BRIDGE_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M76 docs must say OpenWebUI runtime bridge v1": "openwebui runtime bridge v1",
        "M76 docs must say review-only bridge envelope": "review-only bridge envelope",
        "M76 docs must say safe refs only": "safe refs only",
        "M76 docs must say redacted summary only": "redacted summary only",
        "M76 docs must say Python Agent Core remains authority": "python agent core remains authority",
        "M76 docs must say OpenWebUI is shell/bridge": "openwebui is a shell/bridge, not the brain",
        "M76 docs must deny live OpenWebUI connection": "no live openwebui connection",
        "M76 docs must deny OpenWebUI runtime call": "no openwebui runtime call",
        "M76 docs must deny provider calls": "no provider call",
        "M76 docs must deny model calls": "no model call",
        "M76 docs must deny model authority": "no model authority",
        "M76 docs must deny tool execution": "no tool execution",
        "M76 docs must deny memory writes": "no memory write",
        "M76 docs must deny context injection": "no context injection",
        "M76 docs must deny network calls": "no network call",
        "M76 docs must deny credentials/cookies": "no credentials or cookies",
        "M76 docs must deny raw prompts": "no raw prompt",
        "M76 docs must deny raw provider payloads": "no raw provider payload",
        "M76 docs must deny raw content": "no raw content",
        "M76 docs must deny backend routes": "no backend route",
        "M76 docs must deny Control Center controls": "no control center control",
        "M76 docs must deny dependencies": "no dependency",
        "M76 docs must deny production authority": "no production authority",
        "M76 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
    }
    if _version_tuple(version) < (0, 81, 0):
        required_fragments["M76 docs must keep M77 future"] = "m77 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.80.0", "m76", "openwebui runtime bridge v1"),
        ("v0.81.0", "m77", "openwebui safe handoff execution"),
        ("v0.82.0", "m78", "plugin manifest security model"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M76-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M76 docs must not claim OpenWebUI runtime calls": "openwebui runtime calls are implemented",
        "M76 docs must not claim model authority implementation": "model authority is implemented",
        "M76 docs must not claim tool execution implementation": "tool execution is implemented",
        "M76 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 81, 0):
        forbidden_fragments.update(
            {
                "M76 docs must not claim M77 implementation": "m77 is implemented",
                "M76 docs must not claim OpenWebUI safe handoff execution implementation": (
                    "openwebui safe handoff execution is implemented"
                ),
            }
        )
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m77_openwebui_safe_handoff_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 81, 0):
        return failures

    missing = [rel_path for rel_path in REQUIRED_M77_OPENWEBUI_SAFE_HANDOFF_DOCS if not (root / rel_path).exists()]
    failures.extend(f"missing M77 OpenWebUI safe handoff doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M77_OPENWEBUI_SAFE_HANDOFF_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M77 docs must say OpenWebUI safe handoff execution": "openwebui safe handoff execution",
        "M77 docs must say exact approval binding": "exact approval binding",
        "M77 docs must say safe handoff result": "safe handoff result",
        "M77 docs must say Agent Core remains authority": "agent core remains authority",
        "M77 docs must say OpenWebUI is shell/bridge": "openwebui is a shell/bridge, not the brain",
        "M77 docs must deny live OpenWebUI connection": "no live openwebui connection",
        "M77 docs must deny OpenWebUI runtime call": "no openwebui runtime call",
        "M77 docs must deny provider calls": "no provider call",
        "M77 docs must deny model calls": "no model call",
        "M77 docs must deny model authority": "no model authority",
        "M77 docs must deny tool execution": "no tool execution",
        "M77 docs must deny memory writes": "no memory write",
        "M77 docs must deny context injection": "no context injection",
        "M77 docs must deny network calls": "no network call",
        "M77 docs must deny credentials/cookies": "no credentials or cookies",
        "M77 docs must deny raw prompts": "no raw prompt",
        "M77 docs must deny raw provider payloads": "no raw provider payload",
        "M77 docs must deny raw content": "no raw content",
        "M77 docs must deny backend routes": "no backend route",
        "M77 docs must deny Control Center controls": "no control center control",
        "M77 docs must deny dependencies": "no dependency",
        "M77 docs must deny production authority": "no production authority",
        "M77 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
    }
    if _version_tuple(version) < (0, 82, 0):
        required_fragments["M77 docs must keep M78 future"] = "m78 remains future"
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.81.0", "m77", "openwebui safe handoff execution"),
        ("v0.82.0", "m78", "plugin manifest security model"),
        ("v0.83.0", "m79", "plugin install review, disabled by default"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M77-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M77 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M77 docs must not claim OpenWebUI runtime calls": "openwebui runtime calls are implemented",
        "M77 docs must not claim model authority implementation": "model authority is implemented",
        "M77 docs must not claim tool execution implementation": "tool execution is implemented",
        "M77 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 82, 0):
        forbidden_fragments["M77 docs must not claim M78 implementation"] = "m78 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m78_plugin_manifest_security_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 82, 0):
        return failures

    missing = [rel_path for rel_path in REQUIRED_M78_PLUGIN_MANIFEST_SECURITY_DOCS if not (root / rel_path).exists()]
    failures.extend(f"missing M78 plugin manifest security doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M78_PLUGIN_MANIFEST_SECURITY_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M78 docs must say plugin manifest security model": "plugin manifest security model",
        "M78 docs must say declared permissions": "declared permissions",
        "M78 docs must say source/provenance metadata": "source/provenance metadata",
        "M78 docs must say static review": "static review",
        "M78 docs must say sandbox test plan": "sandbox test plan",
        "M78 docs must say Tool Broker permission mapping": "tool broker permission mapping",
        "M78 docs must say Event Ledger logging": "event ledger logging",
        "M78 docs must say version pinning": "version pinning",
        "M78 docs must say revocation": "revocation",
        "M78 docs must say human approval for high-risk capabilities": "human approval for high-risk capabilities",
        "M78 docs must say plugins remain disabled": "plugins remain disabled",
        "M78 docs must deny plugin install": "no plugin install",
        "M78 docs must deny plugin enablement": "no plugin enablement",
        "M78 docs must deny plugin execution": "no plugin execution",
        "M78 docs must deny runtime import": "no runtime import",
        "M78 docs must deny network access": "no network access",
        "M78 docs must deny model/provider calls": "no model/provider call",
        "M78 docs must deny browser automation": "no browser automation",
        "M78 docs must deny shell execution": "no shell execution",
        "M78 docs must deny mobile device access": "no mobile device access",
        "M78 docs must deny remote execution": "no remote execution",
        "M78 docs must deny credentials/cookies": "no credentials or cookies",
        "M78 docs must deny raw prompts": "no raw prompt",
        "M78 docs must deny raw provider payloads": "no raw provider payload",
        "M78 docs must deny backend routes": "no backend route",
        "M78 docs must deny Control Center controls": "no control center control",
        "M78 docs must deny dependencies": "no dependency",
        "M78 docs must deny production authority": "no production authority",
        "M78 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M78 docs must keep M79 future": "m79 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.82.0", "m78", "plugin manifest security model"),
        ("v0.83.0", "m79", "plugin install review, disabled by default"),
        ("v0.84.0", "m80", "network/browser/openwebui hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M78-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M78 docs must not claim plugin install implementation": "plugin install is implemented",
        "M78 docs must not claim plugin enablement implementation": "plugin enablement is implemented",
        "M78 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M78 docs must not claim shell execution implementation": "shell execution is implemented",
        "M78 docs must not claim production authority": "production authority is implemented",
    }
    if _version_tuple(version) < (0, 83, 0):
        forbidden_fragments["M78 docs must not claim M79 implementation"] = "m79 is implemented"
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m79_plugin_install_review_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 83, 0):
        return failures

    missing = [rel_path for rel_path in REQUIRED_M79_PLUGIN_INSTALL_REVIEW_DOCS if not (root / rel_path).exists()]
    failures.extend(f"missing M79 plugin install review doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M79_PLUGIN_INSTALL_REVIEW_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M79 docs must say plugin install review": "plugin install review",
        "M79 docs must say disabled by default": "disabled by default",
        "M79 docs must say exact approval binding": "exact approval binding",
        "M79 docs must say manifest security decision": "manifest security decision",
        "M79 docs must say source package ref": "source package ref",
        "M79 docs must say static review": "static review",
        "M79 docs must say sandbox test plan": "sandbox test plan",
        "M79 docs must say Tool Broker mapping": "tool broker mapping",
        "M79 docs must say Event Ledger": "event ledger",
        "M79 docs must say version pin": "version pin",
        "M79 docs must say revocation": "revocation",
        "M79 docs must deny plugin install": "no plugin install",
        "M79 docs must deny plugin enablement": "no plugin enablement",
        "M79 docs must deny plugin execution": "no plugin execution",
        "M79 docs must deny runtime import": "no runtime import",
        "M79 docs must deny network access": "no network access",
        "M79 docs must deny model/provider calls": "no model/provider call",
        "M79 docs must deny browser automation": "no browser automation",
        "M79 docs must deny shell execution": "no shell execution",
        "M79 docs must deny mobile device access": "no mobile device access",
        "M79 docs must deny remote execution": "no remote execution",
        "M79 docs must deny credentials/cookies": "no credentials or cookies",
        "M79 docs must deny raw package content": "no raw package content",
        "M79 docs must deny raw prompts": "no raw prompt",
        "M79 docs must deny raw provider payloads": "no raw provider payload",
        "M79 docs must deny backend routes": "no backend route",
        "M79 docs must deny Control Center controls": "no control center control",
        "M79 docs must deny dependencies": "no dependency",
        "M79 docs must deny production authority": "no production authority",
        "M79 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M79 docs must keep M80 future": "m80 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.83.0", "m79", "plugin install review, disabled by default"),
        ("v0.84.0", "m80", "network/browser/openwebui hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M79-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M79 docs must not claim plugin install implementation": "plugin install is implemented",
        "M79 docs must not claim plugin enablement implementation": "plugin enablement is implemented",
        "M79 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M79 docs must not claim runtime import implementation": "runtime import is implemented",
        "M79 docs must not claim shell execution implementation": "shell execution is implemented",
        "M79 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m80_network_browser_openwebui_freeze_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 84, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M80_NETWORK_BROWSER_OPENWEBUI_FREEZE_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M80 hardening freeze doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M80_NETWORK_BROWSER_OPENWEBUI_FREEZE_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M80 docs must say hardening freeze": "network/browser/openwebui hardening freeze",
        "M80 docs must say M71-M79": "m71-m79",
        "M80 docs must say freeze-only": "freeze-only",
        "M80 docs must say review-only": "review-only",
        "M80 docs must say deterministic": "deterministic",
        "M80 docs must say accepted milestone refs": "accepted milestone refs",
        "M80 docs must say checklist refs": "checklist refs",
        "M80 docs must deny unrestricted network": "no unrestricted network",
        "M80 docs must deny authenticated network action": "no authenticated network action",
        "M80 docs must deny raw network response": "no raw network response",
        "M80 docs must deny browser navigation": "no browser navigation",
        "M80 docs must deny browser click": "no browser click",
        "M80 docs must deny browser screenshot": "no browser screenshot",
        "M80 docs must deny raw DOM": "no raw dom",
        "M80 docs must deny authenticated browser profile": "no authenticated browser profile",
        "M80 docs must deny OpenWebUI model authority": "no openwebui model authority",
        "M80 docs must deny OpenWebUI tool execution": "no openwebui tool execution",
        "M80 docs must deny OpenWebUI memory write": "no openwebui memory write",
        "M80 docs must deny OpenWebUI context injection": "no openwebui context injection",
        "M80 docs must deny raw prompts": "no raw prompt",
        "M80 docs must deny raw provider payloads": "no raw provider payload",
        "M80 docs must deny plugin install": "no plugin install",
        "M80 docs must deny plugin enablement": "no plugin enablement",
        "M80 docs must deny plugin execution": "no plugin execution",
        "M80 docs must deny runtime import": "no runtime import",
        "M80 docs must deny shell execution": "no shell execution",
        "M80 docs must deny background worker": "no background worker",
        "M80 docs must deny remote execution": "no remote execution",
        "M80 docs must deny backend routes": "no backend route",
        "M80 docs must deny Control Center controls": "no control center control",
        "M80 docs must deny dependencies": "no dependency",
        "M80 docs must deny production authority": "no production authority",
        "M80 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M80 docs must keep M81 future": "m81 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.84.0", "m80", "network/browser/openwebui hardening freeze"),
        ("v0.85.0", "m81", "runtime sandbox spec"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M80-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M80 docs must not claim unrestricted network implementation": "unrestricted network is implemented",
        "M80 docs must not claim browser click implementation": "browser click is implemented",
        "M80 docs must not claim OpenWebUI model authority implementation": "openwebui model authority is implemented",
        "M80 docs must not claim OpenWebUI tool execution implementation": "openwebui tool execution is implemented",
        "M80 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M80 docs must not claim shell execution implementation": "shell execution is implemented",
        "M80 docs must not claim remote execution implementation": "remote execution is implemented",
        "M80 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m81_runtime_sandbox_spec_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 85, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M81_RUNTIME_SANDBOX_SPEC_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M81 runtime sandbox spec doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M81_RUNTIME_SANDBOX_SPEC_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M81 docs must say runtime sandbox spec": "runtime sandbox spec",
        "M81 docs must say spec-only": "spec-only",
        "M81 docs must say review-only": "review-only",
        "M81 docs must say deterministic": "deterministic",
        "M81 docs must say local-only": "local-only",
        "M81 docs must say prior milestone refs": "prior milestone refs",
        "M81 docs must say boundary refs": "boundary refs",
        "M81 docs must say threat model refs": "threat model refs",
        "M81 docs must say audit requirement refs": "audit requirement refs",
        "M81 docs must deny runtime sandbox execution": "no runtime sandbox execution",
        "M81 docs must deny command proposal": "no command proposal",
        "M81 docs must deny command execution": "no command execution",
        "M81 docs must deny subprocess execution": "no subprocess execution",
        "M81 docs must deny shell execution": "no shell execution",
        "M81 docs must deny process spawn": "no process spawn",
        "M81 docs must deny filesystem mutation": "no filesystem mutation",
        "M81 docs must deny network access": "no network access",
        "M81 docs must deny tool execution": "no tool execution",
        "M81 docs must deny browser automation": "no browser automation",
        "M81 docs must deny plugin execution": "no plugin execution",
        "M81 docs must deny remote execution": "no remote execution",
        "M81 docs must deny model call": "no model call",
        "M81 docs must deny memory write": "no memory write",
        "M81 docs must deny context injection": "no context injection",
        "M81 docs must deny background worker": "no background worker",
        "M81 docs must deny backend routes": "no backend route",
        "M81 docs must deny Control Center controls": "no control center control",
        "M81 docs must deny dependencies": "no dependency",
        "M81 docs must deny production authority": "no production authority",
        "M81 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.85.0", "m81", "runtime sandbox spec"),
        ("v0.86.0", "m82", "command proposal contracts"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M81-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M81 docs must not claim runtime sandbox execution implementation": "runtime sandbox execution is implemented",
        "M81 docs must not claim command execution implementation": "command execution is implemented",
        "M81 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M81 docs must not claim shell execution implementation": "shell execution is implemented",
        "M81 docs must not claim process spawn implementation": "process spawn is implemented",
        "M81 docs must not claim browser click implementation": "browser click is implemented",
        "M81 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M81 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m82_command_proposal_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 86, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M82_COMMAND_PROPOSAL_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M82 command proposal doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M82_COMMAND_PROPOSAL_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M82 docs must say command proposal contracts": "command proposal contracts",
        "M82 docs must say proposal-only": "proposal-only",
        "M82 docs must say review-only": "review-only",
        "M82 docs must say deterministic": "deterministic",
        "M82 docs must say local-only": "local-only",
        "M82 docs must say structured argv preview": "structured argv preview",
        "M82 docs must deny shell strings": "no shell string",
        "M82 docs must deny command execution": "no command execution",
        "M82 docs must deny subprocess execution": "no subprocess execution",
        "M82 docs must deny shell execution": "no shell execution",
        "M82 docs must deny process spawn": "no process spawn",
        "M82 docs must deny filesystem mutation": "no filesystem mutation",
        "M82 docs must deny network access": "no network access",
        "M82 docs must deny tool execution": "no tool execution",
        "M82 docs must deny browser automation": "no browser automation",
        "M82 docs must deny plugin execution": "no plugin execution",
        "M82 docs must deny remote execution": "no remote execution",
        "M82 docs must deny model call": "no model call",
        "M82 docs must deny memory write": "no memory write",
        "M82 docs must deny context injection": "no context injection",
        "M82 docs must deny background worker": "no background worker",
        "M82 docs must deny backend routes": "no backend route",
        "M82 docs must deny Control Center controls": "no control center control",
        "M82 docs must deny dependencies": "no dependency",
        "M82 docs must deny production authority": "no production authority",
        "M82 docs must say safe summary only": "safe summary only",
        "M82 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M82 docs must keep M83 future": "m83 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.86.0", "m82", "command proposal contracts"),
        ("v0.87.0", "m83", "shell dry-run classifier"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M82-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M82 docs must not claim command execution implementation": "command execution is implemented",
        "M82 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M82 docs must not claim shell execution implementation": "shell execution is implemented",
        "M82 docs must not claim process spawn implementation": "process spawn is implemented",
        "M82 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M82 docs must not claim network access implementation": "network access is implemented",
        "M82 docs must not claim browser click implementation": "browser click is implemented",
        "M82 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M82 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m83_shell_dry_run_classifier_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 87, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M83_SHELL_DRY_RUN_CLASSIFIER_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M83 shell dry-run classifier doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M83_SHELL_DRY_RUN_CLASSIFIER_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M83 docs must say shell dry-run classifier": "shell dry-run classifier",
        "M83 docs must say classifier-only": "classifier-only",
        "M83 docs must say review-only": "review-only",
        "M83 docs must say deterministic": "deterministic",
        "M83 docs must say local-only": "local-only",
        "M83 docs must require M82 command proposal": "m82 command proposal",
        "M83 docs must deny dry-run execution": "no dry-run execution",
        "M83 docs must deny shell strings": "no shell string",
        "M83 docs must deny command execution": "no command execution",
        "M83 docs must deny subprocess execution": "no subprocess execution",
        "M83 docs must deny shell execution": "no shell execution",
        "M83 docs must deny process spawn": "no process spawn",
        "M83 docs must deny filesystem mutation": "no filesystem mutation",
        "M83 docs must deny network access": "no network access",
        "M83 docs must deny tool execution": "no tool execution",
        "M83 docs must deny browser automation": "no browser automation",
        "M83 docs must deny plugin execution": "no plugin execution",
        "M83 docs must deny remote execution": "no remote execution",
        "M83 docs must deny model call": "no model call",
        "M83 docs must deny memory write": "no memory write",
        "M83 docs must deny context injection": "no context injection",
        "M83 docs must deny background worker": "no background worker",
        "M83 docs must deny backend routes": "no backend route",
        "M83 docs must deny Control Center controls": "no control center control",
        "M83 docs must deny dependencies": "no dependency",
        "M83 docs must deny production authority": "no production authority",
        "M83 docs must say safe summary only": "safe summary only",
        "M83 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M83 docs must keep M84 future": "m84 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.87.0", "m83", "shell dry-run classifier"),
        ("v0.88.0", "m84", "sandboxed echo/no-op command"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M83-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M83 docs must not claim dry-run execution implementation": "dry-run execution is implemented",
        "M83 docs must not claim command execution implementation": "command execution is implemented",
        "M83 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M83 docs must not claim shell execution implementation": "shell execution is implemented",
        "M83 docs must not claim process spawn implementation": "process spawn is implemented",
        "M83 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M83 docs must not claim network access implementation": "network access is implemented",
        "M83 docs must not claim browser click implementation": "browser click is implemented",
        "M83 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M83 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m84_sandboxed_echo_noop_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 88, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M84_SANDBOXED_ECHO_NOOP_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M84 sandboxed echo/no-op doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M84_SANDBOXED_ECHO_NOOP_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M84 docs must say sandboxed echo/no-op command": "sandboxed echo/no-op command",
        "M84 docs must say in-process only": "in-process only",
        "M84 docs must say deterministic": "deterministic",
        "M84 docs must say local-only": "local-only",
        "M84 docs must require M83 shell dry-run classifier": "m83 shell dry-run classifier",
        "M84 docs must deny shell strings": "no shell string",
        "M84 docs must deny raw commands": "no raw command",
        "M84 docs must deny raw output": "no raw output",
        "M84 docs must deny command execution": "no command execution",
        "M84 docs must deny subprocess execution": "no subprocess execution",
        "M84 docs must deny shell execution": "no shell execution",
        "M84 docs must deny process spawn": "no process spawn",
        "M84 docs must deny filesystem mutation": "no filesystem mutation",
        "M84 docs must deny network access": "no network access",
        "M84 docs must deny tool execution": "no tool execution",
        "M84 docs must deny browser automation": "no browser automation",
        "M84 docs must deny plugin execution": "no plugin execution",
        "M84 docs must deny remote execution": "no remote execution",
        "M84 docs must deny model call": "no model call",
        "M84 docs must deny memory write": "no memory write",
        "M84 docs must deny context injection": "no context injection",
        "M84 docs must deny background worker": "no background worker",
        "M84 docs must deny backend routes": "no backend route",
        "M84 docs must deny Control Center controls": "no control center control",
        "M84 docs must deny dependencies": "no dependency",
        "M84 docs must deny production authority": "no production authority",
        "M84 docs must say safe summary only": "safe summary only",
        "M84 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M84 docs must keep M85 future": "m85 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.88.0", "m84", "sandboxed echo/no-op command"),
        ("v0.89.0", "m85", "read-only command allowlist"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M84-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M84 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M84 docs must not claim shell execution implementation": "shell execution is implemented",
        "M84 docs must not claim process spawn implementation": "process spawn is implemented",
        "M84 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M84 docs must not claim network access implementation": "network access is implemented",
        "M84 docs must not claim browser click implementation": "browser click is implemented",
        "M84 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M84 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m85_read_only_command_allowlist_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 89, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M85_READ_ONLY_COMMAND_ALLOWLIST_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M85 read-only command allowlist doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M85_READ_ONLY_COMMAND_ALLOWLIST_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M85 docs must say read-only command allowlist": "read-only command allowlist",
        "M85 docs must say contract-only": "contract-only",
        "M85 docs must say review-only": "review-only",
        "M85 docs must say deterministic": "deterministic",
        "M85 docs must say local-only": "local-only",
        "M85 docs must require M84 sandboxed echo/no-op command": "m84 sandboxed echo/no-op command",
        "M85 docs must say exact M84 binding": "exact m84 binding",
        "M85 docs must say safe refs only": "safe refs only",
        "M85 docs must deny shell strings": "no shell string",
        "M85 docs must deny raw commands": "no raw command",
        "M85 docs must deny raw output": "no raw output",
        "M85 docs must deny command execution": "no command execution",
        "M85 docs must deny subprocess execution": "no subprocess execution",
        "M85 docs must deny shell execution": "no shell execution",
        "M85 docs must deny process spawn": "no process spawn",
        "M85 docs must deny filesystem mutation": "no filesystem mutation",
        "M85 docs must deny network access": "no network access",
        "M85 docs must deny tool execution": "no tool execution",
        "M85 docs must deny browser automation": "no browser automation",
        "M85 docs must deny plugin execution": "no plugin execution",
        "M85 docs must deny remote execution": "no remote execution",
        "M85 docs must deny model call": "no model call",
        "M85 docs must deny memory write": "no memory write",
        "M85 docs must deny context injection": "no context injection",
        "M85 docs must deny background worker": "no background worker",
        "M85 docs must deny backend routes": "no backend route",
        "M85 docs must deny Control Center controls": "no control center control",
        "M85 docs must deny dependencies": "no dependency",
        "M85 docs must deny production authority": "no production authority",
        "M85 docs must say safe summary only": "safe summary only",
        "M85 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M85 docs must keep M86 future": "m86 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.89.0", "m85", "read-only command allowlist"),
        ("v0.90.0", "m86", "shell approval gate v1"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M85-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M85 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M85 docs must not claim shell execution implementation": "shell execution is implemented",
        "M85 docs must not claim process spawn implementation": "process spawn is implemented",
        "M85 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M85 docs must not claim network access implementation": "network access is implemented",
        "M85 docs must not claim browser click implementation": "browser click is implemented",
        "M85 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M85 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m86_shell_approval_gate_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 90, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M86_SHELL_APPROVAL_GATE_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M86 shell approval gate doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M86_SHELL_APPROVAL_GATE_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M86 docs must say shell approval gate": "shell approval gate",
        "M86 docs must say contract-only": "contract-only",
        "M86 docs must say review-only": "review-only",
        "M86 docs must say deterministic": "deterministic",
        "M86 docs must say local-only": "local-only",
        "M86 docs must require M85 read-only command allowlist": "m85 read-only command allowlist",
        "M86 docs must say exact M85 binding": "exact m85 binding",
        "M86 docs must require scoped approval bundle": "scoped approval bundle",
        "M86 docs must say approval refs are identifiers only": "approval refs are identifiers only",
        "M86 docs must say safe refs only": "safe refs only",
        "M86 docs must deny shell strings": "no shell string",
        "M86 docs must deny raw commands": "no raw command",
        "M86 docs must deny raw output": "no raw output",
        "M86 docs must deny command execution": "no command execution",
        "M86 docs must deny subprocess execution": "no subprocess execution",
        "M86 docs must deny shell execution": "no shell execution",
        "M86 docs must deny process spawn": "no process spawn",
        "M86 docs must deny filesystem mutation": "no filesystem mutation",
        "M86 docs must deny network access": "no network access",
        "M86 docs must deny tool execution": "no tool execution",
        "M86 docs must deny browser automation": "no browser automation",
        "M86 docs must deny plugin execution": "no plugin execution",
        "M86 docs must deny remote execution": "no remote execution",
        "M86 docs must deny model call": "no model call",
        "M86 docs must deny memory write": "no memory write",
        "M86 docs must deny context injection": "no context injection",
        "M86 docs must deny background worker": "no background worker",
        "M86 docs must deny backend routes": "no backend route",
        "M86 docs must deny Control Center controls": "no control center control",
        "M86 docs must deny dependencies": "no dependency",
        "M86 docs must deny production authority": "no production authority",
        "M86 docs must say safe summary only": "safe summary only",
        "M86 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M86 docs must keep M87 future": "m87 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.90.0", "m86", "shell approval gate v1"),
        ("v0.91.0", "m87", "sandboxed command audit replay"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M86-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M86 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M86 docs must not claim shell execution implementation": "shell execution is implemented",
        "M86 docs must not claim process spawn implementation": "process spawn is implemented",
        "M86 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M86 docs must not claim network access implementation": "network access is implemented",
        "M86 docs must not claim browser click implementation": "browser click is implemented",
        "M86 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M86 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m87_sandboxed_command_audit_replay_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 91, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M87_SANDBOXED_COMMAND_AUDIT_REPLAY_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M87 sandboxed command audit replay doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M87_SANDBOXED_COMMAND_AUDIT_REPLAY_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M87 docs must say sandboxed command audit replay": "sandboxed command audit replay",
        "M87 docs must say contract-only": "contract-only",
        "M87 docs must say review-only": "review-only",
        "M87 docs must say replay-view-only": "replay-view-only",
        "M87 docs must say deterministic": "deterministic",
        "M87 docs must say local-only": "local-only",
        "M87 docs must require M86 shell approval gate": "m86 shell approval gate",
        "M87 docs must say exact M86 binding": "exact m86",
        "M87 docs must say exact replay step binding": "exact replay step",
        "M87 docs must say safe refs only": "safe refs only",
        "M87 docs must deny replay runner": "no replay runner",
        "M87 docs must deny replay execution": "no replay execution",
        "M87 docs must deny shell strings": "no shell string",
        "M87 docs must deny raw commands": "no raw command",
        "M87 docs must deny raw output": "no raw output",
        "M87 docs must deny command execution": "no command execution",
        "M87 docs must deny subprocess execution": "no subprocess execution",
        "M87 docs must deny shell execution": "no shell execution",
        "M87 docs must deny process spawn": "no process spawn",
        "M87 docs must deny filesystem mutation": "no filesystem mutation",
        "M87 docs must deny network access": "no network access",
        "M87 docs must deny tool execution": "no tool execution",
        "M87 docs must deny browser automation": "no browser automation",
        "M87 docs must deny plugin execution": "no plugin execution",
        "M87 docs must deny remote execution": "no remote execution",
        "M87 docs must deny model call": "no model call",
        "M87 docs must deny memory write": "no memory write",
        "M87 docs must deny context injection": "no context injection",
        "M87 docs must deny background worker": "no background worker",
        "M87 docs must deny backend routes": "no backend route",
        "M87 docs must deny Control Center controls": "no control center control",
        "M87 docs must deny dependencies": "no dependency",
        "M87 docs must deny production authority": "no production authority",
        "M87 docs must say safe summary only": "safe summary only",
        "M87 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M87 docs must keep M88 future": "m88 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.91.0", "m87", "sandboxed command audit replay"),
        ("v0.92.0", "m88", "mutating command proposal, no execution"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M87-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M87 docs must not claim replay runner implementation": "replay runner is implemented",
        "M87 docs must not claim replay execution implementation": "replay execution is implemented",
        "M87 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M87 docs must not claim shell execution implementation": "shell execution is implemented",
        "M87 docs must not claim process spawn implementation": "process spawn is implemented",
        "M87 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M87 docs must not claim network access implementation": "network access is implemented",
        "M87 docs must not claim browser click implementation": "browser click is implemented",
        "M87 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M87 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m88_mutating_command_proposal_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 92, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M88_MUTATING_COMMAND_PROPOSAL_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M88 mutating command proposal doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M88_MUTATING_COMMAND_PROPOSAL_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M88 docs must say mutating command proposal": "mutating command proposal",
        "M88 docs must say contract-only": "contract-only",
        "M88 docs must say proposal-only": "proposal-only",
        "M88 docs must say review-only": "review-only",
        "M88 docs must say deterministic": "deterministic",
        "M88 docs must say local-only": "local-only",
        "M88 docs must require M87 sandboxed command audit replay": "m87 sandboxed command audit replay",
        "M88 docs must say exact M87 binding": "exact m87",
        "M88 docs must say safe mutation scope": "safe mutation scope",
        "M88 docs must say safe argument refs": "safe argument refs",
        "M88 docs must say safe refs only": "safe refs only",
        "M88 docs must deny command execution": "no command execution",
        "M88 docs must deny subprocess execution": "no subprocess execution",
        "M88 docs must deny shell execution": "no shell execution",
        "M88 docs must deny process spawn": "no process spawn",
        "M88 docs must deny filesystem mutation": "no filesystem mutation",
        "M88 docs must deny network access": "no network access",
        "M88 docs must deny tool execution": "no tool execution",
        "M88 docs must deny browser automation": "no browser automation",
        "M88 docs must deny plugin execution": "no plugin execution",
        "M88 docs must deny remote execution": "no remote execution",
        "M88 docs must deny model call": "no model call",
        "M88 docs must deny memory write": "no memory write",
        "M88 docs must deny context injection": "no context injection",
        "M88 docs must deny background worker": "no background worker",
        "M88 docs must deny backend routes": "no backend route",
        "M88 docs must deny Control Center controls": "no control center control",
        "M88 docs must deny dependencies": "no dependency",
        "M88 docs must deny production authority": "no production authority",
        "M88 docs must say safe summary only": "safe summary only",
        "M88 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M88 docs must keep M89 future": "m89 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.92.0", "m88", "mutating command proposal, no execution"),
        ("v0.93.0", "m89", "emergency stop + process kill safety"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M88-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M88 docs must not claim command execution implementation": "command execution is implemented",
        "M88 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M88 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M88 docs must not claim shell execution implementation": "shell execution is implemented",
        "M88 docs must not claim process spawn implementation": "process spawn is implemented",
        "M88 docs must not claim network access implementation": "network access is implemented",
        "M88 docs must not claim browser click implementation": "browser click is implemented",
        "M88 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M88 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m89_emergency_stop_process_kill_safety_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 93, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M89 emergency stop/process kill safety doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M89 docs must say emergency stop + process kill safety": "emergency stop + process kill safety",
        "M89 docs must say contract-only": "contract-only",
        "M89 docs must say review-only": "review-only",
        "M89 docs must say deterministic": "deterministic",
        "M89 docs must say local-only": "local-only",
        "M89 docs must require M88 mutating command proposal": "m88 mutating command proposal",
        "M89 docs must say exact M88 binding": "exact m88",
        "M89 docs must say safe target process ref": "safe target process ref",
        "M89 docs must say safe emergency scope ref": "safe emergency scope ref",
        "M89 docs must say safe refs only": "safe refs only",
        "M89 docs must deny emergency stop execution": "no emergency stop execution",
        "M89 docs must deny process kill": "no process kill",
        "M89 docs must deny process signal": "no process signal",
        "M89 docs must deny command execution": "no command execution",
        "M89 docs must deny subprocess execution": "no subprocess execution",
        "M89 docs must deny shell execution": "no shell execution",
        "M89 docs must deny process spawn": "no process spawn",
        "M89 docs must deny filesystem mutation": "no filesystem mutation",
        "M89 docs must deny network access": "no network access",
        "M89 docs must deny tool execution": "no tool execution",
        "M89 docs must deny browser automation": "no browser automation",
        "M89 docs must deny plugin execution": "no plugin execution",
        "M89 docs must deny remote execution": "no remote execution",
        "M89 docs must deny model call": "no model call",
        "M89 docs must deny memory write": "no memory write",
        "M89 docs must deny context injection": "no context injection",
        "M89 docs must deny background worker": "no background worker",
        "M89 docs must deny backend routes": "no backend route",
        "M89 docs must deny Control Center controls": "no control center control",
        "M89 docs must deny dependencies": "no dependency",
        "M89 docs must deny production authority": "no production authority",
        "M89 docs must deny raw PID": "no raw pid",
        "M89 docs must deny raw signal": "no raw signal",
        "M89 docs must say safe summary only": "safe summary only",
        "M89 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M89 docs must keep M90 future": "m90 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.93.0", "m89", "emergency stop + process kill safety"),
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M89-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M89 docs must not claim process kill implementation": "process kill is implemented",
        "M89 docs must not claim process signal implementation": "process signal is implemented",
        "M89 docs must not claim emergency stop execution implementation": "emergency stop execution is implemented",
        "M89 docs must not claim command execution implementation": "command execution is implemented",
        "M89 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M89 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M89 docs must not claim shell execution implementation": "shell execution is implemented",
        "M89 docs must not claim process spawn implementation": "process spawn is implemented",
        "M89 docs must not claim network access implementation": "network access is implemented",
        "M89 docs must not claim browser click implementation": "browser click is implemented",
        "M89 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M89 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m90_shell_subprocess_hardening_freeze_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 94, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M90_SHELL_SUBPROCESS_HARDENING_FREEZE_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M90 shell/subprocess hardening freeze doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M90_SHELL_SUBPROCESS_HARDENING_FREEZE_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M90 docs must say shell/subprocess hardening freeze": "shell/subprocess hardening freeze",
        "M90 docs must say contract-only": "contract-only",
        "M90 docs must say review-only": "review-only",
        "M90 docs must say freeze-only": "freeze-only",
        "M90 docs must say deterministic": "deterministic",
        "M90 docs must say local-only": "local-only",
        "M90 docs must require M89 emergency stop + process kill safety": "m89 emergency stop + process kill safety",
        "M90 docs must say exact M89 binding": "exact m89",
        "M90 docs must say safe refs only": "safe refs only",
        "M90 docs must deny command execution": "no command execution",
        "M90 docs must deny shell execution": "no shell execution",
        "M90 docs must deny subprocess execution": "no subprocess execution",
        "M90 docs must deny process spawn": "no process spawn",
        "M90 docs must deny emergency stop execution": "no emergency stop execution",
        "M90 docs must deny process kill": "no process kill",
        "M90 docs must deny process signal": "no process signal",
        "M90 docs must deny filesystem mutation": "no filesystem mutation",
        "M90 docs must deny network access": "no network access",
        "M90 docs must deny tool execution": "no tool execution",
        "M90 docs must deny browser automation": "no browser automation",
        "M90 docs must deny plugin execution": "no plugin execution",
        "M90 docs must deny remote execution": "no remote execution",
        "M90 docs must deny model call": "no model call",
        "M90 docs must deny memory write": "no memory write",
        "M90 docs must deny context injection": "no context injection",
        "M90 docs must deny background worker": "no background worker",
        "M90 docs must deny backend routes": "no backend route",
        "M90 docs must deny Control Center controls": "no control center control",
        "M90 docs must deny dependencies": "no dependency",
        "M90 docs must deny production authority": "no production authority",
        "M90 docs must deny shell string": "no shell string",
        "M90 docs must deny raw command": "no raw command",
        "M90 docs must deny raw PID": "no raw pid",
        "M90 docs must deny raw signal": "no raw signal",
        "M90 docs must say safe summary only": "safe summary only",
        "M90 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M90 docs must keep M91 future": "m91 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.94.0", "m90", "shell/subprocess hardening freeze"),
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v0.96.0", "m92", "low-risk tool autonomy, single session"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M90-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M90 docs must not claim command execution implementation": "command execution is implemented",
        "M90 docs must not claim shell execution implementation": "shell execution is implemented",
        "M90 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M90 docs must not claim process spawn implementation": "process spawn is implemented",
        "M90 docs must not claim process kill implementation": "process kill is implemented",
        "M90 docs must not claim emergency stop execution implementation": "emergency stop execution is implemented",
        "M90 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M90 docs must not claim network access implementation": "network access is implemented",
        "M90 docs must not claim browser click implementation": "browser click is implemented",
        "M90 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M90 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m91_autonomous_tool_execution_contract_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 95, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M91 autonomous tool execution contract doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M91 docs must say autonomous tool execution contract": "autonomous tool execution contract",
        "M91 docs must say contract-only": "contract-only",
        "M91 docs must say review-only": "review-only",
        "M91 docs must say deterministic": "deterministic",
        "M91 docs must say local-only": "local-only",
        "M91 docs must require M90 shell/subprocess hardening freeze": "m90 shell/subprocess hardening freeze",
        "M91 docs must say exact M90 binding": "exact m90",
        "M91 docs must say safe refs only": "safe refs only",
        "M91 docs must say approval refs are identifiers only": "approval refs are identifiers only",
        "M91 docs must say dry-run plan only": "dry-run plan only",
        "M91 docs must deny real tool execution": "no real tool execution",
        "M91 docs must deny autonomous execution": "no autonomous execution",
        "M91 docs must deny autonomous session start": "no autonomous session start",
        "M91 docs must deny command execution": "no command execution",
        "M91 docs must deny shell execution": "no shell execution",
        "M91 docs must deny subprocess execution": "no subprocess execution",
        "M91 docs must deny filesystem mutation": "no filesystem mutation",
        "M91 docs must deny network access": "no network access",
        "M91 docs must deny browser automation": "no browser automation",
        "M91 docs must deny plugin execution": "no plugin execution",
        "M91 docs must deny remote execution": "no remote execution",
        "M91 docs must deny model call": "no model call",
        "M91 docs must deny memory write": "no memory write",
        "M91 docs must deny context injection": "no context injection",
        "M91 docs must deny background worker": "no background worker",
        "M91 docs must deny backend routes": "no backend route",
        "M91 docs must deny Control Center controls": "no control center control",
        "M91 docs must deny dependencies": "no dependency",
        "M91 docs must deny production authority": "no production authority",
        "M91 docs must deny raw tool payload": "no raw tool payload",
        "M91 docs must deny raw provider payload": "no raw provider payload",
        "M91 docs must say safe summary only": "safe summary only",
        "M91 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M91 docs must keep M92 future": "m92 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.95.0", "m91", "autonomous tool execution contract"),
        ("v0.96.0", "m92", "low-risk tool autonomy, single session"),
        ("v0.97.0", "m93", "multi-tool dry-run to real run promotion"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M91-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M91 docs must not claim real tool execution implementation": "real tool execution is implemented",
        "M91 docs must not claim autonomous session start implementation": "autonomous session start is implemented",
        "M91 docs must not claim command execution implementation": "command execution is implemented",
        "M91 docs must not claim shell execution implementation": "shell execution is implemented",
        "M91 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M91 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M91 docs must not claim network access implementation": "network access is implemented",
        "M91 docs must not claim browser click implementation": "browser click is implemented",
        "M91 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M91 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m92_low_risk_tool_autonomy_single_session_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 96, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M92 low-risk tool autonomy single-session doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M92 docs must say low-risk tool autonomy, single session": "low-risk tool autonomy, single session",
        "M92 docs must say review-only": "review-only",
        "M92 docs must say low-risk only": "low-risk only",
        "M92 docs must say single-session only": "single-session only",
        "M92 docs must say deterministic": "deterministic",
        "M92 docs must say local-only": "local-only",
        "M92 docs must say safe refs only": "safe refs only",
        "M92 docs must require exact M91 binding": "exact m91",
        "M92 docs must name autonomous tool execution contract": "autonomous tool execution contract",
        "M92 docs must require exact dry-run binding": "exact low-risk autonomous dry run",
        "M92 docs must deny real tool execution": "no real tool execution",
        "M92 docs must deny autonomous execution": "no autonomous execution",
        "M92 docs must deny session start": "no session start",
        "M92 docs must deny additional sessions": "no additional session",
        "M92 docs must deny multi-tool execution": "no multi-tool",
        "M92 docs must deny command execution": "no command execution",
        "M92 docs must deny shell execution": "no shell execution",
        "M92 docs must deny subprocess execution": "no subprocess execution",
        "M92 docs must deny filesystem mutation": "no filesystem mutation",
        "M92 docs must deny network access": "no network access",
        "M92 docs must deny browser automation": "no browser automation",
        "M92 docs must deny plugin execution": "no plugin execution",
        "M92 docs must deny remote execution": "no remote execution",
        "M92 docs must deny model call": "no model call",
        "M92 docs must deny memory write": "no memory write",
        "M92 docs must deny context injection": "no context injection",
        "M92 docs must deny background worker": "no background worker",
        "M92 docs must deny backend routes": "no backend route",
        "M92 docs must deny Control Center controls": "no control center control",
        "M92 docs must deny dependencies": "no dependency",
        "M92 docs must deny production authority": "no production authority",
        "M92 docs must deny raw tool payload": "no raw tool payload",
        "M92 docs must deny raw provider payload": "no raw provider payload",
        "M92 docs must say safe summary only": "safe summary only",
        "M92 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M92 docs must keep M93 future": "m93 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.96.0", "m92", "low-risk tool autonomy, single session"),
        ("v0.97.0", "m93", "multi-tool dry-run to real run promotion"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M92-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M92 docs must not claim real tool execution implementation": "real tool execution is implemented",
        "M92 docs must not claim autonomous session start implementation": "autonomous session start is implemented",
        "M92 docs must not claim multi-tool real run implementation": "multi-tool real run is implemented",
        "M92 docs must not claim command execution implementation": "command execution is implemented",
        "M92 docs must not claim shell execution implementation": "shell execution is implemented",
        "M92 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M92 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M92 docs must not claim network access implementation": "network access is implemented",
        "M92 docs must not claim browser click implementation": "browser click is implemented",
        "M92 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M92 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m93_multi_tool_dry_run_promotion_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 97, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M93_MULTI_TOOL_DRY_RUN_PROMOTION_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M93 multi-tool dry-run promotion doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M93_MULTI_TOOL_DRY_RUN_PROMOTION_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M93 docs must say multi-tool dry-run to real run promotion": "multi-tool dry-run to real run promotion",
        "M93 docs must say review-only": "review-only",
        "M93 docs must mention dry-run plan": "dry-run plan",
        "M93 docs must mention real-run plan": "real-run plan",
        "M93 docs must require exact M92 binding": "exact m92",
        "M93 docs must require exact promotion approval": "exact promotion approval",
        "M93 docs must deny wildcard approval": "wildcard approval denied",
        "M93 docs must require plan hash binding": "plan hash",
        "M93 docs must require equivalence": "dry-run and real-run equivalence",
        "M93 docs must deny unapproved real execution": "no unapproved real execution",
        "M93 docs must deny real-run execution": "no real-run execution",
        "M93 docs must deny tool execution": "no tool execution",
        "M93 docs must deny autonomous execution": "no autonomous execution",
        "M93 docs must deny session start": "no session start",
        "M93 docs must deny command execution": "no command execution",
        "M93 docs must deny shell execution": "no shell execution",
        "M93 docs must deny subprocess execution": "no subprocess execution",
        "M93 docs must deny filesystem mutation": "no filesystem mutation",
        "M93 docs must deny network access": "no network access",
        "M93 docs must deny browser click": "no browser click",
        "M93 docs must deny browser form": "no browser form",
        "M93 docs must deny plugin execution": "no plugin execution",
        "M93 docs must deny remote execution": "no remote execution",
        "M93 docs must deny model call": "no model call",
        "M93 docs must deny memory write": "no memory write",
        "M93 docs must deny context injection": "no context injection",
        "M93 docs must deny background worker": "no background worker",
        "M93 docs must deny backend routes": "no backend route",
        "M93 docs must deny Control Center controls": "no control center control",
        "M93 docs must deny dependencies": "no dependency",
        "M93 docs must deny production authority": "no production authority",
        "M93 docs must say safe refs only": "safe refs only",
        "M93 docs must say safe summary only": "safe summary only",
        "M93 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M93 docs must keep M94 future": "m94 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.97.0", "m93", "multi-tool dry-run to real run promotion"),
        ("v0.98.0", "m94", "autonomous browser clicks, low-risk only"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M93-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M93 docs must not claim real-run execution implementation": "real-run execution is implemented",
        "M93 docs must not claim real tool execution implementation": "real tool execution is implemented",
        "M93 docs must not claim browser click implementation": "browser click is implemented",
        "M93 docs must not claim browser form implementation": "browser form is implemented",
        "M93 docs must not claim command execution implementation": "command execution is implemented",
        "M93 docs must not claim shell execution implementation": "shell execution is implemented",
        "M93 docs must not claim subprocess execution implementation": "subprocess execution is implemented",
        "M93 docs must not claim filesystem mutation implementation": "filesystem mutation is implemented",
        "M93 docs must not claim network access implementation": "network access is implemented",
        "M93 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M93 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m94_low_risk_browser_click_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 98, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M94_LOW_RISK_BROWSER_CLICK_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M94 low-risk browser click doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M94_LOW_RISK_BROWSER_CLICK_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M94 docs must say autonomous browser clicks, low-risk only": "autonomous browser clicks, low-risk only",
        "M94 docs must say low-risk click": "low-risk click",
        "M94 docs must say scoped session": "scoped session",
        "M94 docs must say allowlisted page": "allowlisted page",
        "M94 docs must say allowlisted action": "allowlisted action",
        "M94 docs must require exact M93 binding": "exact m93",
        "M94 docs must require exact click approval": "exact click approval",
        "M94 docs must say audit": "audit",
        "M94 docs must say revocation": "revocation",
        "M94 docs must say injected transport": "injected transport",
        "M94 docs must say safe refs only": "safe refs only",
        "M94 docs must say safe summary only": "safe summary only",
        "M94 docs must deny form submission": "no form submission",
        "M94 docs must deny typing": "no typing",
        "M94 docs must deny purchase": "no purchase",
        "M94 docs must deny download": "no download",
        "M94 docs must deny upload": "no upload",
        "M94 docs must deny authentication": "no authentication",
        "M94 docs must deny account change": "no account change",
        "M94 docs must deny destructive action": "no destructive action",
        "M94 docs must deny credential or cookie access": "no credential or cookie access",
        "M94 docs must deny raw DOM": "no raw dom",
        "M94 docs must deny screenshot": "no screenshot",
        "M94 docs must deny broad navigation": "no broad navigation",
        "M94 docs must deny external network": "no external network",
        "M94 docs must deny shell execution": "no shell execution",
        "M94 docs must deny plugin execution": "no plugin execution",
        "M94 docs must deny model call": "no model call",
        "M94 docs must deny memory write": "no memory write",
        "M94 docs must deny context injection": "no context injection",
        "M94 docs must deny backend route": "no backend route",
        "M94 docs must deny Control Center control": "no control center control",
        "M94 docs must deny dependency": "no dependency",
        "M94 docs must deny production authority": "no production authority",
        "M94 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M94 docs must keep M95 future": "m95 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.98.0", "m94", "autonomous browser clicks, low-risk only"),
        ("v0.99.0", "m95", "network tool expansion, authless only"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M94-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M94 docs must not claim browser form implementation": "browser form is implemented",
        "M94 docs must not claim browser download implementation": "browser download is implemented",
        "M94 docs must not claim browser authentication implementation": "browser authentication is implemented",
        "M94 docs must not claim unrestricted network implementation": "unrestricted network is implemented",
        "M94 docs must not claim network mutation implementation": "network mutation is implemented",
        "M94 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M94 docs must not claim recurring automation implementation": "recurring automation is implemented",
        "M94 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m95_authless_network_expansion_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 99, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M95_AUTHLESS_NETWORK_EXPANSION_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M95 authless network expansion doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M95_AUTHLESS_NETWORK_EXPANSION_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M95 docs must say network tool expansion, authless only": "network tool expansion, authless only",
        "M95 docs must say authless": "authless",
        "M95 docs must say read-only": "read-only",
        "M95 docs must say allowlisted domain": "allowlisted domain",
        "M95 docs must say HTTPS": "https",
        "M95 docs must say GET only": "get only",
        "M95 docs must say redirect controls": "redirect controls",
        "M95 docs must say bounded output": "bounded output",
        "M95 docs must say redaction": "redaction",
        "M95 docs must say exact scope": "exact scope",
        "M95 docs must say audit": "audit",
        "M95 docs must say revocation": "revocation",
        "M95 docs must say transport injection": "transport injection",
        "M95 docs must say safe refs only": "safe refs only",
        "M95 docs must say redacted preview only": "redacted preview only",
        "M95 docs must deny credentials": "no credentials",
        "M95 docs must deny cookies": "no cookies",
        "M95 docs must deny credential headers": "no credential headers",
        "M95 docs must deny request body": "no request body",
        "M95 docs must deny POST": "no post",
        "M95 docs must deny PUT": "no put",
        "M95 docs must deny PATCH": "no patch",
        "M95 docs must deny DELETE": "no delete",
        "M95 docs must deny account action": "no account action",
        "M95 docs must deny private network": "no private network",
        "M95 docs must deny download": "no download",
        "M95 docs must deny export": "no export",
        "M95 docs must deny browser form": "no browser form",
        "M95 docs must deny provider model call": "no provider model call",
        "M95 docs must deny shell execution": "no shell execution",
        "M95 docs must deny plugin execution": "no plugin execution",
        "M95 docs must deny memory write": "no memory write",
        "M95 docs must deny context injection": "no context injection",
        "M95 docs must deny backend route": "no backend route",
        "M95 docs must deny Control Center control": "no control center control",
        "M95 docs must deny dependency": "no dependency",
        "M95 docs must deny production authority": "no production authority",
        "M95 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M95 docs must keep M96 future": "m96 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v0.99.0", "m95", "network tool expansion, authless only"),
        ("v1.0.0", "m96", "plugin execution sandbox, no external plugins"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M95-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M95 docs must not claim authenticated network implementation": "authenticated network is implemented",
        "M95 docs must not claim network mutation implementation": "network mutation is implemented",
        "M95 docs must not claim external plugin execution implementation": "external plugin execution is implemented",
        "M95 docs must not claim recurring automation implementation": "recurring automation is implemented",
        "M95 docs must not claim mobile permission runtime implementation": "mobile permission runtime is implemented",
        "M95 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m96_plugin_execution_sandbox_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (1, 0, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M96_PLUGIN_EXECUTION_SANDBOX_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M96 plugin execution sandbox doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M96_PLUGIN_EXECUTION_SANDBOX_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M96 docs must say plugin execution sandbox, no external plugins": "plugin execution sandbox, no external plugins",
        "M96 docs must say built-in test plugin": "built-in test plugin",
        "M96 docs must say sandbox": "sandbox",
        "M96 docs must say manifest permission": "manifest permission",
        "M96 docs must say audit receipt": "audit receipt",
        "M96 docs must say revocation": "revocation",
        "M96 docs must say deterministic": "deterministic",
        "M96 docs must say safe refs only": "safe refs only",
        "M96 docs must deny external plugin loading": "no external plugin loading",
        "M96 docs must deny marketplace plugin": "no marketplace plugin",
        "M96 docs must deny arbitrary plugin code": "no arbitrary plugin code",
        "M96 docs must deny runtime import": "no runtime import",
        "M96 docs must deny networked plugin fetch": "no networked plugin fetch",
        "M96 docs must deny plugin secret access": "no plugin secret access",
        "M96 docs must deny raw plugin payload": "no raw plugin payload",
        "M96 docs must deny shell execution": "no shell execution",
        "M96 docs must deny network access": "no network access",
        "M96 docs must deny browser automation": "no browser automation",
        "M96 docs must deny filesystem mutation": "no filesystem mutation",
        "M96 docs must deny model provider call": "no model provider call",
        "M96 docs must deny memory write": "no memory write",
        "M96 docs must deny context injection": "no context injection",
        "M96 docs must deny backend route": "no backend route",
        "M96 docs must deny Control Center control": "no control center control",
        "M96 docs must deny dependency": "no dependency",
        "M96 docs must deny production authority": "no production authority",
        "M96 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M96 docs must keep M97 future": "m97 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v1.0.0", "m96", "plugin execution sandbox, no external plugins"),
        ("v1.1.0", "m97", "recurring automation contracts"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M96-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M96 docs must not claim external plugin loading implementation": "external plugin loading is implemented",
        "M96 docs must not claim marketplace plugin implementation": "marketplace plugin is implemented",
        "M96 docs must not claim arbitrary plugin code implementation": "arbitrary plugin code is implemented",
        "M96 docs must not claim recurring automation implementation": "recurring automation is implemented",
        "M96 docs must not claim mobile permission runtime implementation": "mobile permission runtime is implemented",
        "M96 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m97_recurring_automation_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (1, 1, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M97_RECURRING_AUTOMATION_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M97 recurring automation doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M97_RECURRING_AUTOMATION_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M97 docs must say recurring automation contracts": "recurring automation contracts",
        "M97 docs must say contract-only": "contract-only",
        "M97 docs must say disabled by default": "disabled by default",
        "M97 docs must say approval renewal required": "approval renewal required",
        "M97 docs must say expiration required": "expiration required",
        "M97 docs must say stop conditions required": "stop conditions required",
        "M97 docs must deny recurrence runtime": "no recurrence runtime",
        "M97 docs must deny background execution": "no background execution",
        "M97 docs must deny cron": "no cron",
        "M97 docs must deny daemon": "no daemon",
        "M97 docs must deny scheduler": "no scheduler",
        "M97 docs must deny side effects": "no side effects",
        "M97 docs must deny backend route": "no backend route",
        "M97 docs must deny Control Center control": "no control center control",
        "M97 docs must deny dependency": "no dependency",
        "M97 docs must deny production authority": "no production authority",
        "M97 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M97 docs must keep M98 future": "m98 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v1.1.0", "m97", "recurring automation contracts"),
        ("v1.2.0", "m98", "scoped recurring low-risk automation"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M97-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M97 docs must not claim recurrence runtime implementation": "recurrence runtime is implemented",
        "M97 docs must not claim background worker implementation": "background worker is implemented",
        "M97 docs must not claim cron implementation": "cron daemon is implemented",
        "M97 docs must not claim scheduler implementation": "scheduler is implemented",
        "M97 docs must not claim recurring execution implementation": "recurring execution is implemented",
        "M97 docs must not claim mobile permission runtime implementation": "mobile permission runtime is implemented",
        "M97 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m98_scoped_recurring_low_risk_automation_docs(
    root: Path, version: str | None
) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (1, 2, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M98_SCOPED_RECURRING_LOW_RISK_AUTOMATION_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(
        f"missing M98 scoped recurring low-risk automation doc: {rel_path}"
        for rel_path in missing
    )
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M98_SCOPED_RECURRING_LOW_RISK_AUTOMATION_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M98 docs must say scoped recurring low-risk automation": "scoped recurring low-risk automation",
        "M98 docs must say low-risk read-only": "low-risk read-only",
        "M98 docs must say strict cadence": "strict cadence",
        "M98 docs must say approval renewal required": "approval renewal required",
        "M98 docs must say renewal expiry": "renewal expiry",
        "M98 docs must say stop conditions required": "stop conditions required",
        "M98 docs must say kill switch": "kill switch",
        "M98 docs must say audit trail": "audit trail",
        "M98 docs must say revocation": "revocation",
        "M98 docs must deny scheduler": "no scheduler",
        "M98 docs must deny background worker": "no background worker",
        "M98 docs must deny recurring execution runtime": "no recurring execution runtime",
        "M98 docs must deny mutating tasks": "no mutating tasks",
        "M98 docs must deny credential/account actions": "no credential or account actions",
        "M98 docs must deny shell write": "no shell write",
        "M98 docs must deny network write": "no network write",
        "M98 docs must deny browser write": "no browser write",
        "M98 docs must deny silent background collection": "no silent background collection",
        "M98 docs must deny secret access": "no secret access",
        "M98 docs must deny memory write": "no memory write",
        "M98 docs must deny context injection": "no context injection",
        "M98 docs must deny export": "no export",
        "M98 docs must deny backend route": "no backend route",
        "M98 docs must deny dependency": "no dependency",
        "M98 docs must deny production authority": "no production authority",
        "M98 docs must say evaluator boundaries revalidate": "evaluator boundaries revalidate",
        "M98 docs must keep M99 future": "m99 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v1.2.0", "m98", "scoped recurring low-risk automation"),
        ("v1.3.0", "m99", "autonomy v1 safety freeze"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M98-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M98 docs must not claim scheduler implementation": "scheduler is implemented",
        "M98 docs must not claim background worker implementation": "background worker is implemented",
        "M98 docs must not claim recurring execution runtime implementation": "recurring execution runtime is implemented",
        "M98 docs must not claim mutating recurring task implementation": "mutating recurring task is implemented",
        "M98 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m99_autonomy_v1_safety_freeze_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (1, 3, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M99_AUTONOMY_V1_SAFETY_FREEZE_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M99 Autonomy v1 Safety Freeze doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M99_AUTONOMY_V1_SAFETY_FREEZE_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M99 docs must say Autonomy v1 Safety Freeze": "autonomy v1 safety freeze",
        "M99 docs must say M61-M98 coverage": "m61-m98",
        "M99 docs must say freeze-only": "freeze-only",
        "M99 docs must say review-only": "review-only",
        "M99 docs must deny broad unsandboxed autonomy": "no broad unsandboxed autonomy",
        "M99 docs must deny global autonomy switch": "no global autonomy switch",
        "M99 docs must deny production authority": "no production authority",
        "M99 docs must deny shell execution": "no shell execution",
        "M99 docs must deny browser action": "no browser action",
        "M99 docs must deny network mutation": "no network mutation",
        "M99 docs must deny plugin execution": "no plugin execution",
        "M99 docs must deny scheduler": "no scheduler",
        "M99 docs must deny background worker": "no background worker",
        "M99 docs must deny mobile sensor": "no mobile sensor",
        "M99 docs must deny memory write": "no memory write",
        "M99 docs must deny context injection": "no context injection",
        "M99 docs must deny raw prompt": "no raw prompt",
        "M99 docs must deny raw file export": "no raw file export",
        "M99 docs must deny full-file read": "no full-file read",
        "M99 docs must deny backend route": "no backend route",
        "M99 docs must deny dependency": "no dependency",
        "M99 docs must say evaluator revalidation": "evaluator revalidation",
        "M99 docs must keep M100 future": "m100 remains future",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    for version_label, milestone, title in [
        ("v1.3.0", "m99", "autonomy v1 safety freeze"),
        ("v1.4.0", "m100", "mobile permission model v1"),
    ]:
        if version_label not in text or milestone not in text or title not in text:
            failures.append(
                f"M99-M100 roadmap missing label: {version_label} / {milestone.upper()} - {title}"
            )

    forbidden_fragments = {
        "M99 docs must not claim global autonomy switch implementation": "global autonomy switch is implemented",
        "M99 docs must not claim broad autonomy implementation": "broad autonomy is implemented",
        "M99 docs must not claim shell execution implementation": "shell execution is implemented",
        "M99 docs must not claim browser action implementation": "browser action is implemented",
        "M99 docs must not claim network mutation implementation": "network mutation is implemented",
        "M99 docs must not claim plugin execution implementation": "plugin execution is implemented",
        "M99 docs must not claim scheduler implementation": "scheduler is implemented",
        "M99 docs must not claim background worker implementation": "background worker is implemented",
        "M99 docs must not claim production authority": "production authority is implemented",
    }
    for message, fragment in forbidden_fragments.items():
        if fragment in text:
            failures.append(f"{message}: {fragment}")
    return failures


def _verify_m100_mobile_permission_model_v1_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (1, 4, 0):
        return failures

    missing = [
        rel_path
        for rel_path in REQUIRED_M100_MOBILE_PERMISSION_MODEL_V1_DOCS
        if not (root / rel_path).exists()
    ]
    failures.extend(f"missing M100 Mobile Permission Model v1 doc: {rel_path}" for rel_path in missing)
    text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_M100_MOBILE_PERMISSION_MODEL_V1_DOCS
        if (root / rel_path).exists()
    )
    required_fragments = {
        "M100 docs must say Mobile Permission Model v1": "mobile permission model v1",
        "M100 docs must say permission taxonomy": "permission taxonomy",
        "M100 docs must say consent": "consent",
        "M100 docs must say revocation": "revocation",
        "M100 docs must say privacy copy": "privacy copy",
        "M100 docs must say permission audit": "permission audit",
        "M100 docs must say contract-only": "contract-only",
        "M100 docs must say sensors remain off": "sensors remain off",
        "M100 docs must say no background collection": "no background collection",
        "M100 docs must say no runtime permission prompts": "no runtime permission prompts",
        "M100 docs must say no native permission request": "no native permission request",
        "M100 docs must say no backend route": "no backend route",
        "M100 docs must say no dependency": "no dependency",
        "M100 docs must say no production authority": "no production authority",
        "M100 docs must say implemented/released": "m100 implemented/released",
        "M100 docs must say do not start M101": "do not start m101",
    }
    for message, fragment in required_fragments.items():
        if fragment not in text:
            failures.append(message)

    active_paths = [
        "README.md",
        "VERSION.md",
        "docs/canonical/09_roadmap.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        "docs/roadmap/MILESTONE_CHARTERS.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
    ]
    active_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in active_paths
        if (root / rel_path).exists()
    )
    if "v1.4.0" not in active_text or "m100" not in active_text or "mobile permission model v1" not in active_text:
        failures.append("active docs missing v1.4.0/M100 Mobile Permission Model v1")
    if "m100 is implemented/released" not in active_text and "v1.4.0 implements m100" not in active_text:
        failures.append("active docs do not mark M100 implemented/released")
    forbidden_fragments = {
        "M100 docs must not claim M101 implementation": "m101 is implemented",
        "M100 docs must not claim mobile permission runtime": "mobile permission runtime is implemented",
        "M100 docs must not claim mobile sensors": "mobile sensors are implemented",
        "M100 docs must not claim runtime permission prompts": "runtime permission prompts are implemented",
        "M100 docs must not claim native permission requests": "native permission requests are implemented",
        "M100 docs must not claim background collection": "background collection is implemented",
        "M100 docs must not claim push execution": "push execution is implemented",
        "M100 docs must not claim production authority": "production authority is implemented",
    }
    combined_text = "\n".join([text, active_text])
    for message, fragment in forbidden_fragments.items():
        if fragment in combined_text:
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
        if active_version_tuple >= (0, 63, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M55 is implemented/released"] = (
                "m55 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M56 is implemented/released"] = (
                "m56 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M57 is implemented/released"] = (
                "m57 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M58 is implemented/released"] = (
                "m58 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M59 is implemented/released"] = (
                "m59 is implemented/released"
            )
            if active_version_tuple >= (0, 64, 0):
                expectations["Post-M20 roadmap docs must say M60 is implemented/released"] = (
                    "m60 is implemented/released"
                )
            else:
                expectations["Post-M20 roadmap docs must keep M60 planned/provisional"] = (
                    "m60 remains planned/provisional"
                )
        elif active_version_tuple >= (0, 62, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M55 is implemented/released"] = (
                "m55 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M56 is implemented/released"] = (
                "m56 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M57 is implemented/released"] = (
                "m57 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M58 is implemented/released"] = (
                "m58 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M59-M60 planned/provisional"] = (
                "m59-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 61, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M55 is implemented/released"] = (
                "m55 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M56 is implemented/released"] = (
                "m56 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M57 is implemented/released"] = (
                "m57 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M58-M60 planned/provisional"] = (
                "m58-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 60, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M55 is implemented/released"] = (
                "m55 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M56 is implemented/released"] = (
                "m56 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M57-M60 planned/provisional"] = (
                "m57-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 59, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M55 is implemented/released"] = (
                "m55 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M56-M60 planned/provisional"] = (
                "m56-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 58, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M54 is implemented/released"] = (
                "m54 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M55-M60 planned/provisional"] = (
                "m55-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 57, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M53 is implemented/released"] = (
                "m53 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M54-M60 planned/provisional"] = (
                "m54-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 56, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M52 is implemented/released"] = (
                "m52 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M53-M60 planned/provisional"] = (
                "m53-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 55, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M51 is implemented/released"] = (
                "m51 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M52-M60 planned/provisional"] = (
                "m52-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 54, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M50 is implemented/released"] = (
                "m50 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M51-M60 planned/provisional"] = (
                "m51-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 53, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M49 is implemented/released"] = (
                "m49 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M50-M60 planned/provisional"] = (
                "m50-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 52, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M48 is implemented/released"] = (
                "m48 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M49-M60 planned/provisional"] = (
                "m49-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 51, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M47 is implemented/released"] = (
                "m47 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M48-M60 planned/provisional"] = (
                "m48-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 50, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M46 is implemented/released"] = (
                "m46 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M47-M60 planned/provisional"] = (
                "m47-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 49, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M45 is implemented/released"] = (
                "m45 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M46-M60 planned/provisional"] = (
                "m46-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 48, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                "m43 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must say M44 is implemented/released"] = (
                "m44 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M45-M60 planned/provisional"] = (
                "m45-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 46, 0):
            expectations["Post-M20 roadmap docs must say M42 is implemented/released"] = (
                "m42 is implemented/released"
            )
            if active_version_tuple >= (0, 47, 0):
                expectations["Post-M20 roadmap docs must say M43 is implemented/released"] = (
                    "m43 is implemented/released"
                )
            expectations["Post-M20 roadmap docs must keep M44-M60 planned/provisional"] = (
                "m44-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 45, 0):
            expectations["Post-M20 roadmap docs must say M41 is implemented/released"] = (
                "m41 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M42-M60 planned/provisional"] = (
                "m42-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 44, 0):
            expectations["Post-M20 roadmap docs must say M40 is implemented/released"] = (
                "m40 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M41-M60 planned/provisional"] = (
                "m41-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 43, 0):
            expectations["Post-M20 roadmap docs must say M39 is implemented/released"] = (
                "m39 is implemented/released"
            )
            expectations["Post-M20 roadmap docs must keep M40-M60 planned/provisional"] = (
                "m40-m60 remain planned/provisional"
            )
        elif active_version_tuple >= (0, 42, 0):
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

    if active_version_tuple >= (0, 44, 0):
        implemented_claim_start = 41
    elif active_version_tuple >= (0, 43, 0):
        implemented_claim_start = 40
    elif active_version_tuple >= (0, 42, 0):
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
    implemented_claims = [f"m{number} is implemented" for number in range(implemented_claim_start, 41)]
    if active_version_tuple < (0, 44, 0):
        implemented_claims.extend(
            [
                "m21-m40 are implemented",
                "m21 through m40 are implemented",
            ]
        )
    implemented_claims.append("post-m20 capabilities are implemented")
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
        if active >= (0, 63, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "v0.59.0" not in active_capability_charters or "m55" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M55/v0.59.0 implemented")
            if "v0.60.0" not in active_capability_charters or "m56" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M56/v0.60.0 implemented")
            if "v0.61.0" not in active_capability_charters or "m57" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M57/v0.61.0 implemented")
            if "v0.62.0" not in active_capability_charters or "m58" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M58/v0.62.0 implemented")
            if "v0.63.0" not in active_capability_charters or "m59" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M59/v0.63.0 implemented")
            if active >= (0, 64, 0):
                if not re.search(
                    r"(?:\|\s*)?v0\.64\.0[^\n]*m60[^\n]*implemented/released",
                    active_capability_charters,
                ):
                    failures.append("roadmap sequence must mark M60/v0.64.0 implemented")
            elif not re.search(
                r"(?:\|\s*)?v0\.64\.0[^\n]*m60[^\n]*planned/provisional",
                active_capability_charters,
            ) and "m60 remains planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M60 planned/provisional")
        elif active >= (0, 62, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "v0.59.0" not in active_capability_charters or "m55" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M55/v0.59.0 implemented")
            if "v0.60.0" not in active_capability_charters or "m56" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M56/v0.60.0 implemented")
            if "v0.61.0" not in active_capability_charters or "m57" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M57/v0.61.0 implemented")
            if "v0.62.0" not in active_capability_charters or "m58" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M58/v0.62.0 implemented")
            if "m59-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M59-M60 planned/provisional")
        elif active >= (0, 61, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "v0.59.0" not in active_capability_charters or "m55" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M55/v0.59.0 implemented")
            if "v0.60.0" not in active_capability_charters or "m56" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M56/v0.60.0 implemented")
            if "v0.61.0" not in active_capability_charters or "m57" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M57/v0.61.0 implemented")
            if "m58-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M58-M60 planned/provisional")
        elif active >= (0, 60, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "v0.59.0" not in active_capability_charters or "m55" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M55/v0.59.0 implemented")
            if "v0.60.0" not in active_capability_charters or "m56" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M56/v0.60.0 implemented")
            if "m57-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M57-M60 planned/provisional")
        elif active >= (0, 59, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "v0.59.0" not in active_capability_charters or "m55" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M55/v0.59.0 implemented")
            if "m56-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M56-M60 planned/provisional")
        elif active >= (0, 58, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "v0.58.0" not in active_capability_charters or "m54" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M54/v0.58.0 implemented")
            if "m55-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M55-M60 planned/provisional")
        elif active >= (0, 57, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "v0.57.0" not in active_capability_charters or "m53" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M53/v0.57.0 implemented")
            if "m54-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M54-M60 planned/provisional")
        elif active >= (0, 56, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "v0.56.0" not in active_capability_charters or "m52" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M52/v0.56.0 implemented")
            if "m53-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M53-M60 planned/provisional")
        elif active >= (0, 55, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "v0.55.0" not in active_capability_charters or "m51" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M51/v0.55.0 implemented")
            if "m52-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M52-M60 planned/provisional")
        elif active >= (0, 54, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "v0.54.0" not in active_capability_charters or "m50" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M50/v0.54.0 implemented")
            if "m51-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M51-M60 planned/provisional")
        elif active >= (0, 53, 0):
            if "v0.53.0" not in active_capability_charters or "m49" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M49/v0.53.0 implemented")
            if "m50-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M50-M60 planned/provisional")
        elif active >= (0, 52, 0):
            if "v0.52.0" not in active_capability_charters or "m48" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M48/v0.52.0 implemented")
            if "m49-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M49-M60 planned/provisional")
        elif active >= (0, 51, 0):
            if "v0.51.0 / m47" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M47/v0.51.0 implemented")
            if "m48-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M48-M60 planned/provisional")
        elif active >= (0, 50, 0):
            if "v0.50.0 / m46" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M46/v0.50.0 implemented")
            if "m47-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M47-M60 planned/provisional")
        elif active >= (0, 49, 0):
            if "v0.49.0 / m45" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M45/v0.49.0 implemented")
            if "m46-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M46-M60 planned/provisional")
        elif active >= (0, 48, 0):
            if "v0.48.0 / m44" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M44/v0.48.0 implemented")
            if "m45-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M45-M60 planned/provisional")
        elif active >= (0, 47, 0):
            if "v0.47.0 / m43" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M43/v0.47.0 implemented")
            if "m44-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M44-M60 planned/provisional")
        elif active >= (0, 46, 0):
            if "v0.46.0 / m42" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M42/v0.46.0 implemented")
            if "m44-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M44-M60 planned/provisional")
        elif active >= (0, 45, 0):
            if "v0.45.0 / m41" not in active_capability_charters or "implemented/released" not in active_capability_charters:
                failures.append("roadmap sequence must mark M41/v0.45.0 implemented")
            if "m42-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M42-M60 planned/provisional")
        elif active >= (0, 44, 0):
            if "v0.44.0 / m40" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M40/v0.44.0 implemented")
            if "m41-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M41-M60 planned/provisional")
        elif active >= (0, 43, 0):
            if "v0.43.0 / m39" not in active_capability_charters or "status: implemented" not in active_capability_charters:
                failures.append("roadmap sequence must mark M39/v0.43.0 implemented")
            if "m40-m60" not in active_capability_charters or "planned/provisional" not in active_capability_charters:
                failures.append("roadmap sequence must keep M40-M60 planned/provisional")
        elif active >= (0, 42, 0):
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
