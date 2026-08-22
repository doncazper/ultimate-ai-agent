from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalStatus,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseStore,
    TrustMode,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.chat import (
    CHAT_DURABLE_RECEIPT_CONTRACT_REF,
    CHAT_DURABLE_RECEIPT_ROUTE_REFS,
    CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS,
    CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS,
    CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
    ChatHandoffReceipt,
    ChatHandoffRequest,
    ChatTurnReceipt,
    ChatTurnReceiptRequest,
    build_chat_local_operator_turn_envelope,
    chat_handoff_audit_ref,
    chat_handoff_created_ref,
    chat_handoff_payload_for_fingerprint,
    chat_handoff_receipt_ref,
    chat_local_operator_authority_posture,
    chat_local_operator_surface_bindings,
    chat_payload_fingerprint_ref,
    chat_turn_harness_binding_receipt_summary,
    chat_turn_evidence_ref,
    chat_turn_handoff_ref,
    chat_turn_payload_for_fingerprint,
    chat_turn_receipt_ref,
    chat_turn_ref_for_request,
)
from ultimate_ai_agent.core.code import (
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
    GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS,
    build_governed_code_workbench_proposal,
    governed_code_workbench_authority_posture,
    governed_code_workbench_surface_bindings,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    ACTION_DECISION_REQUESTED_ACTION,
    FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_ACTION_REF,
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_LANE_REF,
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF,
    FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS,
    FOUNDER_LOOP_ACTION_DECISION_KINDS,
    FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM,
    FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_ACTION_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_LANE_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_BLOCKED_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
    FounderLoopActionDecisionReceipt,
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionReceipt,
    FounderLoopActionEnvelopePromotionRequest,
    action_approval_request,
    action_decision_approval_scope_ref,
    action_decision_audit_ref,
    action_decision_deadline_ref,
    action_decision_receipt_ref,
    action_decision_ref,
    action_decision_route_binding_ref,
    action_decision_route_ref,
    action_envelope_promotion_audit_ref,
    action_envelope_promotion_event_ref,
    action_envelope_promotion_receipt_ref,
    action_id_to_item_ref,
    action_generation_ref,
    action_payload_fingerprint_ref,
    action_revision_fingerprint_ref,
    action_revision_ref,
    decision_payload_for_fingerprint,
    promotion_payload_for_fingerprint,
    today_item_to_action_item_ref,
)
from ultimate_ai_agent.core.costs import (
    BudgetScope,
    CostBudget,
    CostEstimate,
    CostGovernor,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_ACTION_REF,
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_CAPABILITY_REF,
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DOMAIN_REF,
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_LANE_REF,
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_MODE_REF,
    FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_POSTURE_REF,
    FounderLoopLocalTaskCommitReceipt,
    FounderLoopLocalTaskCommitRequest,
    local_task_commit_approval_request,
    local_task_commit_audit_ref,
    local_task_commit_event_ref,
    local_task_commit_payload_fingerprint_ref,
    local_task_commit_payload_for_fingerprint,
    local_task_commit_receipt_ref,
    local_task_authority_proof_refs,
    local_task_ref_for_action,
)
from ultimate_ai_agent.core.storage import founder_loop_exact_action
from ultimate_ai_agent.core.control_center.today_loop import (
    TODAY_LOOP_TIGHTENING_CONTRACT_REF,
    build_today_loop_read_model,
)
from ultimate_ai_agent.core.control_center.follow_up_tracker import (
    FOLLOW_UP_TRACKER_CONTRACT_REF,
    build_follow_up_tracker_read_model,
)
from ultimate_ai_agent.core.control_center.action_inbox_decision_lanes import (
    ACTION_INBOX_DECISION_LANE_CONTRACT_REF,
    build_action_inbox_decision_lane_read_model,
)
from ultimate_ai_agent.core.control_center.action_inbox_work_queue import (
    ACTION_INBOX_WORK_QUEUE_CONTRACT_REF,
    build_action_inbox_work_queue_read_model,
)
from ultimate_ai_agent.core.control_center.action_tool_code_catalog import (
    ACTION_TOOL_CODE_CATALOG_CONTRACT_REF,
    build_action_tool_code_lane_catalog_read_model,
)
from ultimate_ai_agent.core.control_center.evidence_memory_loop_binding import (
    EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF,
    build_evidence_memory_loop_binding_read_model,
)
from ultimate_ai_agent.core.control_center.operator_workspace_spine import (
    build_operator_workspace_spine_read_model,
)
from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF,
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.control_center.fusion_routing import (
    FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
    FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS,
    WorkClassificationValue,
    build_cache_context_economics,
    build_delegation_proposal,
    build_fusion_routing_delegation_read_model,
    build_work_classification,
    fusion_routing_authority_posture,
    fusion_routing_surface_bindings,
)
from ultimate_ai_agent.core.control_center.plans_to_actions import (
    PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF,
    build_plans_to_actions_bridge_read_model,
)
from ultimate_ai_agent.core.control_center.morning_briefing import (
    MORNING_BRIEFING_V1_CONTRACT_REF,
    build_morning_briefing_v1_read_model,
)
from ultimate_ai_agent.core.control_center.weekly_ceo_review import (
    WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
    build_weekly_ceo_review_v1_read_model,
)
from ultimate_ai_agent.core.control_center.founder_loop_product_proof import (
    FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
    build_founder_loop_product_proof_read_model,
)
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
    build_founder_loop_runs_integration_read_model,
)
from ultimate_ai_agent.core.control_center.chat_to_loop_handoff import (
    CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
    build_chat_to_loop_handoff_read_model,
)
from ultimate_ai_agent.core.control_center.unified_work_thread import (
    UNIFIED_WORK_THREAD_CONTRACT_REF,
    build_unified_work_thread_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
    WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF,
    WebEvidenceProductSliceReceipt,
)
from ultimate_ai_agent.core.connectors.connector_draft_proposals import (
    build_connector_draft_proposal_read_model,
)
from ultimate_ai_agent.core.connectors.founder_loop_read_only_integration_contracts import (
    build_fcc_read_only_integration_contract_pair,
)
from ultimate_ai_agent.core.control_center.health_recommendations import (
    FCC_HEALTH_RECOMMENDATION_ACTION_KIND,
    FCC_HEALTH_RECOMMENDATION_BINDING_CONTRACT_REF,
    build_fcc_health_recommendations,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway import RuntimeInvocationStore
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.intent import (
    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
    USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS,
    USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES,
    USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS,
    build_user_intent_understanding_contract,
    user_intent_understanding_authority_posture,
    user_intent_understanding_surface_bindings,
)
from ultimate_ai_agent.core.memory.intake import (
    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES,
    cross_surface_memory_intake_authority_posture,
    cross_surface_memory_intake_proposals,
    cross_surface_memory_intake_surface_bindings,
)
from ultimate_ai_agent.core.memory.loop_binding import (
    MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
    MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_REQUIRED_SURFACES,
    build_memory_derived_action_proposal,
    build_memory_to_loop_binding_item,
    memory_to_loop_authority_posture,
    memory_to_loop_surface_bindings,
)
from ultimate_ai_agent.core.memory.source_provenance import (
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_DENIED_CONTENT_REFS,
    MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS,
    MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
    memory_source_provenance_policy_rows,
    memory_source_provenance_review_posture,
)
from ultimate_ai_agent.core.memory.business_memory import (
    BUSINESS_MEMORY_CANDIDATE_KINDS,
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    BUSINESS_MEMORY_REQUIRED_REF_FIELDS,
    CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF,
    build_crm_lite_relationship_followup,
    business_memory_authority_posture,
    business_memory_candidate_kind_rows,
    business_memory_candidate_ref,
    business_memory_quality_ref,
    business_memory_quality_state_rows,
    business_memory_surface_bindings,
    crm_lite_relationship_authority_posture,
)
from ultimate_ai_agent.core.memory.local_store import LocalMemoryStore
from ultimate_ai_agent.core.memory.l1_index import (
    L1_HOT_MEMORY_INDEX_BLOCKED_STATE_REFS,
    L1_HOT_MEMORY_INDEX_CONTRACT_REF,
    L1_HOT_MEMORY_INDEX_ROUTE_REF,
    build_l1_hot_memory_index,
)
from ultimate_ai_agent.core.memory.l2_index import (
    L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS,
    L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF,
    L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF,
    build_l2_factual_graph_temporal_index,
)
from ultimate_ai_agent.core.memory.l3_index import (
    L3_IDENTITY_SESSION_MODELING_BLOCKED_STATE_REFS,
    L3_IDENTITY_SESSION_MODELING_CONTRACT_REF,
    L3_IDENTITY_SESSION_MODELING_ROUTE_REF,
    build_l3_identity_session_preference_index,
)
from ultimate_ai_agent.core.memory.context_packs import (
    build_context_pack_proposal_index,
)
from ultimate_ai_agent.core.memory.diagnostics import (
    MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_QUALITY_CONTRACT_REF,
    MEMORY_FEEDBACK_ROUTE_REF as DIAGNOSTIC_MEMORY_FEEDBACK_ROUTE_REF,
    build_memory_citation_integrity,
    build_memory_context_manifest,
    build_memory_context_pack_preview,
    build_memory_feedback_quality_queue,
    build_memory_maintenance_runs,
    build_memory_retrieval_diagnostics,
    known_memory_feedback_target_refs,
    memory_feedback_payload_fingerprint_ref as diagnostic_memory_feedback_payload_fingerprint_ref,
    memory_feedback_payload_for_fingerprint as diagnostic_memory_feedback_payload_for_fingerprint,
    memory_feedback_receipt_ref as diagnostic_memory_feedback_receipt_ref,
    memory_feedback_ref as diagnostic_memory_feedback_ref,
)
from ultimate_ai_agent.core.memory.feature_mine import (
    MEMORY_CONTRADICTION_BLOCKED_STATE_REFS,
    MEMORY_CONTRADICTION_PREVIEW_CONTRACT_REF,
    MEMORY_CONTRADICTION_PREVIEW_ROUTE_REF,
    MEMORY_FEEDBACK_CONTRACT_REF,
    MEMORY_FEEDBACK_EXACT_SCOPE_REF,
    MEMORY_OBSERVATION_BLOCKED_STATE_REFS,
    MEMORY_OBSERVATION_CANDIDATE_CONTRACT_REF,
    MEMORY_OBSERVATION_CANDIDATE_ROUTE_REF,
    MEMORY_PROBE_BLOCKED_STATE_REFS,
    MEMORY_PROBE_CONTRACT_REF,
    MEMORY_PROBE_ROUTE_REF,
    MemoryFeedbackRequest,
    bounded_observation_summary,
    memory_feature_flags,
    memory_feedback_payload_fingerprint_ref,
    memory_feedback_payload_for_fingerprint,
    memory_feedback_receipt_ref,
    memory_hrr_readiness,
    refs_intersect,
    validate_query_mode,
)
from ultimate_ai_agent.core.memory.execution_hooks import (
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_ACTION_REF,
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_CAPABILITY_REF,
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_DOMAIN_REF,
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_LANE_REF,
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_REQUIRED_BLOCKED_REF,
    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_REQUIRED_MODE_REF,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE_REF,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_STATUS,
    MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS,
    MemoryContextPackActionProposalReceipt,
    MemoryContextPackActionProposalRequest,
    memory_context_pack_action_approval_request,
    memory_context_pack_action_audit_ref,
    memory_context_pack_action_envelope_ref,
    memory_context_pack_action_event_ref,
    memory_context_pack_action_item_ref,
    memory_context_pack_action_payload_fingerprint_ref,
    memory_context_pack_action_payload_for_fingerprint,
    memory_context_pack_action_proposal_ref,
    memory_context_pack_action_receipt_ref,
    memory_context_pack_action_scope_ref,
)
from ultimate_ai_agent.core.memory.governed_context import (
    build_governed_memory_context_manifest,
)
from ultimate_ai_agent.core.memory.review_decisions import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_AUTHORITY_ACTION_REF,
    MEMORY_REVIEW_AUTHORITY_CAPABILITY_REF,
    MEMORY_REVIEW_AUTHORITY_DOMAIN_REF,
    MEMORY_REVIEW_AUTHORITY_LANE_REF,
    MEMORY_REVIEW_AUTHORITY_REQUIRED_BLOCKED_REF,
    MEMORY_REVIEW_AUTHORITY_REQUIRED_MODE_REF,
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_LIFECYCLE_AUTHORITY_ACTION_REF,
    MEMORY_REVIEW_LIFECYCLE_AUTHORITY_LANE_REF,
    MEMORY_REVIEW_LIFECYCLE_SCOPE_REF,
    MEMORY_REVIEW_RECEIPT_SCOPE_REF,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_KINDS,
    MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS,
    MEMORY_REVIEW_DECISION_ROUTE_REFS,
    MEMORY_REVIEW_DECISION_STATES,
    MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_POSTURE_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
    MemoryReviewDecision,
    MemoryReviewDecisionKind,
    MemoryReviewDecisionRequest,
    MemoryReviewDecisionReceipt,
    memory_review_correction_ref,
    memory_review_defer_ref,
    memory_review_decision_audit_ref,
    memory_review_decision_authority_posture,
    memory_review_decision_evidence_ref,
    memory_review_decision_payload_for_fingerprint,
    memory_review_decision_receipt_ref,
    memory_review_decision_ref,
    memory_review_decision_state_rows,
    memory_review_expire_ref,
    memory_review_payload_fingerprint_ref,
    memory_review_forget_request_ref,
    memory_review_merge_ref,
    memory_review_rejection_ref,
    memory_review_reviewed_recall_ref,
    memory_review_supersede_ref,
)
from ultimate_ai_agent.core.memory.review_runtime import (
    MemoryReviewRuntimeError,
    activate_memory_review_recall_record,
    build_memory_feedback_receipt,
    ensure_memory_runtime_operation_tables,
    evaluate_memory_feedback_write_authority,
    evaluate_memory_review_write_authority,
    load_memory_review_suppression_operation,
    memory_feedback_pre_start_is_valid,
    memory_feedback_update_operation,
    memory_workbench_loop_refs,
    memory_review_recall_record_refs_for_candidate,
    memory_review_recall_search_index_status,
    persist_memory_feedback_receipt,
    prepare_memory_feedback_update_operation,
    prepare_memory_review_suppression_operation,
    settle_memory_review_suppression_operation,
    suppress_memory_review_recall_records_after_terminal_decision,
    update_memory_review_projection_after_decision,
    validate_prepared_suppression_authority_binding,
    write_memory_review_recall_record,
)
from ultimate_ai_agent.core.memory.workbench import (
    MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS,
    MEMORY_MANUAL_INTAKE_CONTRACT_REF,
    MEMORY_MANUAL_INTAKE_ROUTE_REF,
    MEMORY_RANKING_CONTRACT_REF,
    MEMORY_WORKBENCH_BLOCKED_STATE_REFS,
    MEMORY_WORKBENCH_CONTRACT_REF,
    MEMORY_WORKBENCH_ROUTE_REF,
    ManualMemoryCandidateRequest,
    build_memory_impact_graph,
    build_memory_workbench,
    filter_memory_workbench,
    manual_memory_candidate_payload_fingerprint_ref,
    manual_memory_candidate_payload_for_fingerprint,
    manual_memory_candidate_ref,
)
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.planning.action_envelopes import (
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS,
    PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS,
    PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS,
    build_plan_action_envelope,
    plans_action_envelope_authority_posture,
    plans_action_envelope_review_posture_rows,
    plans_action_envelope_surface_bindings,
)
from ultimate_ai_agent.core.task_decomposition.proposals import (
    TASK_DECOMPOSITION_ACTION_KIND,
    TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF,
    TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS,
    build_task_decomposition_review_envelope,
    task_decomposition_action_items,
    task_decomposition_read_model_for_plan,
)
from ultimate_ai_agent.core.readiness import (
    PRIVATE_BETA_READINESS_CONTRACT_REF,
    PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
    PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS,
    PRIVATE_BETA_READINESS_REQUIRED_SURFACES,
    build_private_beta_readiness_gate,
    private_beta_readiness_authority_posture,
    private_beta_readiness_surface_bindings,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.founder_loop_schema import (
    FOUNDER_LOOP_SCHEMA_VERSION,
    append_durable_jsonl,
    backup_contract_manifest,
    connect_founder_loop_sqlite,
    require_compatible_schema,
    record_bootstrap_migration,
)


FOUNDER_LOOP_STATE_DIR_ENV = "UAA_FOUNDER_LOOP_STATE_DIR"
DEFAULT_FOUNDER_LOOP_STATE_DIR = Path(".uaa") / "founder_loop"
SAFE_STATUS_REF_CHARS = re.compile(r"[^a-z0-9_.@-]+")
TODAY_PRODUCT_SPINE_CONTRACT_REF = "contract-ref:today-product-spine:v1"
EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF = "contract-ref:evidence-history-grammar:v1"
EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF = (
    "contract-ref:founder-loop-evidence-timeline-productization:v1"
)
EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF = (
    "contract-ref:product-loop-010-evidence-timeline-narrative:v1"
)
EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE = (
    "python_core_evidence_timeline_narrative_read_model"
)
EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF = (
    "contract-ref:runtime-evidence-audit-spine:v1"
)
EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE = "python_core_runtime_evidence_audit_spine"
EVIDENCE_TIMELINE_PRODUCTIZATION_ROUTE_REFS = ("GET /control-center/evidence/timeline",)
EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES = (
    "action_envelope_created",
    "action_decision_recorded",
    "local_task_created",
    "chat_turn_receipt_recorded",
    "chat_handoff_created",
    "memory_review_decision_recorded",
    "web_evidence_attached",
)
EVIDENCE_TIMELINE_PRODUCTIZED_GROUP_KINDS = (
    "today_item",
    "action",
    "chat_turn",
    "memory_candidate",
    "web_evidence",
)
EVIDENCE_AUDIT_GROUP_KINDS = (
    "plan_changes",
    "approval_waits",
    "action_proposals",
    "execution_receipts",
    "memory_proposals_review_decisions",
    "blocked_no_go_events",
    "recovery_events",
)
OPERATOR_RUN_TIMELINE_CONTRACT_REF = "contract-ref:operator-run-timeline:v1"
FRONTIER_AI_COST_USAGE_CONTRACT_REF = "contract-ref:frontier-ai-cost-usage-telemetry:v1"
OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS = (
    {
        "pattern_id": "typed_event_ledger",
        "label": "Typed event ledger",
        "safe_summary": (
            "Each operator-visible step is represented as a typed event with "
            "stable safe refs."
        ),
    },
    {
        "pattern_id": "run_control_states",
        "label": "Run control states",
        "safe_summary": (
            "Waiting, blocked, evidence-needed, and receipt-recorded states are "
            "visible without adding runtime pause or resume authority."
        ),
    },
    {
        "pattern_id": "evidence_based_completion",
        "label": "Evidence-based completion",
        "safe_summary": (
            "Completion posture depends on receipt, audit, and evidence refs "
            "instead of model-written claims."
        ),
    },
    {
        "pattern_id": "approval_preview_and_rejection_feedback",
        "label": "Approval preview and rejection feedback",
        "safe_summary": (
            "Approval posture and blocked decisions stay reviewable before any "
            "future scoped mutation is considered."
        ),
    },
    {
        "pattern_id": "evidence_condensing_with_safe_refs",
        "label": "Evidence condensing with safe refs",
        "safe_summary": (
            "Dense receipts are condensed into safe summaries that keep source "
            "refs inspectable."
        ),
    },
)
OPERATOR_RUN_TIMELINE_STATES = (
    "waiting_for_approval",
    "receipt_recorded",
    "blocked",
    "needs_evidence",
)
ACTION_INBOX_GROUP_DEFINITIONS = (
    {
        "group_id": "ready_for_decision",
        "label": "Ready for decision",
        "safe_summary": (
            "Items with backend-known exact scope that can record approve, edit, "
            "reject, or defer receipts without executing work."
        ),
        "available_action": "Record a backend-owned decision receipt.",
    },
    {
        "group_id": "approved_local_task_lane",
        "label": "Approved local-task create lane",
        "safe_summary": (
            "Exact-approved local_task_create items that can be committed only "
            "through the typed local task route."
        ),
        "available_action": "Inspect approval posture or commit the local-task create lane.",
    },
    {
        "group_id": "blocked_by_authority",
        "label": "Blocked by authority",
        "safe_summary": (
            "Items blocked by missing authority, missing exact scope, policy "
            "posture, or disallowed external capability."
        ),
        "available_action": "Inspect blockers; no decision or commit control is exposed.",
    },
    {
        "group_id": "expired_stale",
        "label": "Expired/stale",
        "safe_summary": (
            "Items whose approval window, evidence, or state is no longer fresh "
            "enough for a decision."
        ),
        "available_action": "Recheck source and evidence refs before any decision.",
    },
    {
        "group_id": "receipt_recorded",
        "label": "Receipt recorded",
        "safe_summary": (
            "Items with backend decision, commit, or evidence receipts already "
            "recorded."
        ),
        "available_action": "Inspect receipt and evidence refs.",
    },
    {
        "group_id": "proposal_only_no_execution_path",
        "label": "Proposal-only / no execution path",
        "safe_summary": (
            "Planning, documentation, or review-only items without a validated "
            "core/API/CLI execution path."
        ),
        "available_action": "Review proposal refs only.",
    },
)
ACTION_INBOX_GROUP_ORDER = tuple(
    str(group["group_id"]) for group in ACTION_INBOX_GROUP_DEFINITIONS
)
SOURCE_READINESS_PROPOSAL_BINDING_CONTRACT_REF = (
    "contract-ref:founder-loop-source-readiness-draft-proposals:v1"
)
SOURCE_READINESS_PROPOSAL_ACTION_KIND = "source_readiness_contract_proposal"
SOURCE_READINESS_EMAIL_METADATA_CONTRACT_REF = (
    "fcc-email-metadata-read-only-contract:fcc-p1-008"
)
SOURCE_READINESS_CALENDAR_METADATA_CONTRACT_REF = (
    "fcc-calendar-read-only-contract:fcc-p1-007"
)
TODAY_PRODUCT_SPINE_LOOP_SURFACES = ["Today", "Actions", "Evidence", "Memory"]
EVIDENCE_HISTORY_GRAMMAR_KEYS = (
    "proposed",
    "approved",
    "happened",
    "changed",
    "undoable",
    "stale",
    "blocked",
)
EVIDENCE_HISTORY_GRAMMAR_REQUIRED_QUESTIONS = [
    {
        "key": "proposed",
        "question": "What was proposed?",
        "required": True,
    },
    {
        "key": "approved",
        "question": "What was approved?",
        "required": True,
    },
    {
        "key": "happened",
        "question": "What happened?",
        "required": True,
    },
    {
        "key": "changed",
        "question": "What changed?",
        "required": True,
    },
    {
        "key": "undoable",
        "question": "What can be undone?",
        "required": True,
    },
    {
        "key": "stale",
        "question": "What is stale?",
        "required": True,
    },
    {
        "key": "blocked",
        "question": "What remains blocked?",
        "required": True,
    },
]
EVIDENCE_HISTORY_SURFACE_BINDINGS = [
    {
        "surface": "Actions",
        "current_status": "implemented_via_action_timeline_refs",
        "required_history_keys": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
        "authority_boundary": (
            "Action evidence can describe proposals, approval posture, receipts, "
            "changes, rollback posture, stale state, and blockers without "
            "granting approval or execution."
        ),
    },
    {
        "surface": "Plans",
        "current_status": "implemented_reviewable_action_envelope_refs",
        "required_history_keys": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
        "authority_boundary": (
            "Plan evidence can describe reviewable Action envelope posture, "
            "expected receipts, rollback posture, and blockers, but plan "
            "summaries are not execution authority."
        ),
    },
    {
        "surface": "Memory",
        "current_status": "implemented_review_queue_refs_only",
        "required_history_keys": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
        "authority_boundary": (
            "Memory evidence can describe source, review, stale, and blocked "
            "posture; recall is not truth, write authority, or context injection."
        ),
    },
    {
        "surface": "Chat",
        "current_status": "implemented_local_operator_turn_truth_refs",
        "required_history_keys": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
        "authority_boundary": (
            "Chat evidence records route, runtime, auth, tool-denial, and safe "
            "handoff refs only; model output remains non-authoritative."
        ),
    },
    {
        "surface": "Code",
        "current_status": "implemented_governed_diff_validation_refs",
        "required_history_keys": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
        "authority_boundary": (
            "Code evidence uses repo-local proposal scope, safe diff summary, "
            "validation, apply posture, rollback posture, and blockers; "
            "unrestricted shell or broad coding autonomy is not scoped."
        ),
    },
]
TODAY_PRODUCT_SPINE_REQUIRED_SIGNALS = [
    {
        "signal": "priorities",
        "source": "action_and_briefing_priority_fields",
        "required": True,
    },
    {
        "signal": "blockers",
        "source": "blocked_states_and_missing_contract_refs",
        "required": True,
    },
    {
        "signal": "follow_ups",
        "source": "next_safe_action_fields",
        "required": True,
    },
    {
        "signal": "plan_action_state",
        "source": "plans_actions_and_approval_posture",
        "required": True,
    },
    {
        "signal": "memory_review_count",
        "source": "sections.memory_review_count",
        "required": True,
    },
    {
        "signal": "stale_source_posture",
        "source": "stale_state_fields",
        "required": True,
    },
    {
        "signal": "next_safe_actions",
        "source": "next_safe_actions",
        "required": True,
    },
]
TODAY_PRODUCT_SPINE_MODULE_FEEDS = [
    {
        "module": "Today",
        "status": "implemented_storage_backed_partial_loop",
        "required_loop_outputs": [
            "today_state",
            "action_state",
            "evidence_state",
            "memory_state",
        ],
        "current_feed_refs": [
            "GET /control-center/today/summary",
            "evidence-ref:founder-loop:today-summary",
            PRIVATE_BETA_READINESS_CONTRACT_REF,
            USER_INTENT_UNDERSTANDING_CONTRACT_REF,
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Actions",
        "status": "implemented_review_queue_execution_blocked",
        "required_loop_outputs": [
            "today_priority_or_blocker",
            "action_envelope_or_blocked_state",
            "evidence_ref",
            "memory_review_or_blocked_state",
        ],
        "current_feed_refs": [
            "GET /control-center/actions/inbox",
            "evidence-ref:founder-loop:action-inbox",
            "private-beta-readiness:action-inbox",
            "user-intent-understanding:actions",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Plans",
        "status": "implemented_reviewable_action_envelope_contract",
        "required_loop_outputs": [
            "today_plan_state",
            "action_envelope_or_blocked_state",
            "plan_evidence_ref",
            "memory_candidate_or_blocked_state",
        ],
        "current_feed_refs": [
            "status-ref:founder-loop-plan-summary",
            PLANS_ACTION_ENVELOPE_CONTRACT_REF,
            "user-intent-understanding:plans",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Memory",
        "status": "implemented_review_queue_quality_intake_and_loop_binding_contract",
        "required_loop_outputs": [
            "today_memory_review_count",
            "action_or_follow_up_candidate",
            "memory_evidence_ref",
            "reviewed_recall_or_blocked_state",
        ],
        "current_feed_refs": [
            "status-ref:founder-loop-memory-review",
            MEMORY_REVIEW_DECISION_CONTRACT_REF,
            BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
            CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
            MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
            "private-beta-readiness:memory-review",
            "user-intent-understanding:memory-review",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Evidence",
        "status": "implemented_redacted_history_grammar_contract_partial",
        "required_loop_outputs": [
            "today_evidence_state",
            "action_receipt_or_blocked_state",
            "evidence_timeline_ref",
            "memory_evidence_or_blocked_state",
        ],
        "current_feed_refs": [
            "GET /control-center/today/summary",
            EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
            "private-beta-readiness:evidence-timeline",
            "user-intent-understanding:evidence-timeline",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Morning Briefing",
        "status": "implemented_skeleton_source_contracts_missing",
        "required_loop_outputs": [
            "today_priority_or_blocker",
            "follow_up_or_action_candidate",
            "source_readiness_evidence_ref",
            "memory_candidate_or_blocked_state",
        ],
        "current_feed_refs": [
            "GET /control-center/morning-briefing/summary",
            "contract-ref:calendar-read-only-missing",
            "private-beta-readiness:morning-briefing",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Chat",
        "status": "implemented_local_operator_surface_contract",
        "required_loop_outputs": [
            "today_chat_state",
            "plan_or_action_handoff_state",
            "chat_evidence_ref",
            "memory_candidate_or_blocked_state",
        ],
        "current_feed_refs": [
            CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
            "/v1/chat/completions",
            "private-beta-readiness:chat-plans-handoff",
            "user-intent-understanding:chat",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Code",
        "status": "implemented_governed_code_workbench_contract_apply_blocked",
        "required_loop_outputs": [
            "today_code_state",
            "action_or_apply_blocked_state",
            "diff_validation_evidence_ref",
            "memory_candidate_or_blocked_state",
        ],
        "current_feed_refs": [
            GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
            "private-beta-readiness:governed-code",
            "user-intent-understanding:governed-code",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "Private Beta Readiness",
        "status": "implemented_local_readiness_gate_authority_blocked",
        "required_loop_outputs": [
            "today_readiness_state",
            "action_inbox_acceptance_state",
            "evidence_history_state",
            "memory_review_and_crm_lite_follow_up_state",
        ],
        "current_feed_refs": [
            PRIVATE_BETA_READINESS_CONTRACT_REF,
            "evidence-packet:private-beta-readiness:local-founder-loop",
        ],
        "standalone_complete_allowed": False,
    },
    {
        "module": "User Intent Understanding",
        "status": "implemented_reviewable_intent_proposals_authority_blocked",
        "required_loop_outputs": [
            "today_intent_proposal_state",
            "ask_act_defer_action_gate",
            "evidence_history_dependency_refs",
            "memory_and_source_ambiguity_posture",
        ],
        "current_feed_refs": [
            USER_INTENT_UNDERSTANDING_CONTRACT_REF,
            "policy-ref:user-intent:low-confidence-asks-user",
            "policy-ref:user-intent:conflict-asks-user",
        ],
        "standalone_complete_allowed": False,
    },
]

UNSAFE_STORAGE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "account identifier",
    "account_identifier",
    "account id",
    "account_id",
    "raw private content",
    "raw_private_content",
    "environment dump",
    "environment_dump",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)
UNSAFE_STORAGE_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "account_identifier",
    "account_id",
    "client_secret",
    "cookie",
    "credential",
    "hostname",
    "password",
    "private_key",
    "provider_payload",
    "raw_log",
    "raw_path",
    "raw_prompt",
    "raw_response",
    "raw_private_content",
    "secret",
    "serial",
    "token",
    "username",
)


class FounderLoopStorageError(Exception):
    """Base error for storage-backed Founder Loop state."""


class FounderLoopStorageDuplicateError(FounderLoopStorageError):
    """Raised when a duplicate idempotency key is denied."""


class FounderLoopActionRevisionConflict(FounderLoopStorageError):
    """Raised when a decision targets an Action revision that is no longer current."""

    def __init__(
        self,
        *,
        current_revision_ref: str,
        current_generation_ref: str,
    ) -> None:
        super().__init__("FOUNDER_LOOP_ACTION_STALE_REVISION")
        self.code = "FOUNDER_LOOP_ACTION_STALE_REVISION"
        self.current_revision_ref = current_revision_ref
        self.current_generation_ref = current_generation_ref
        self.refresh_route_ref = "GET /control-center/actions/inbox"


class FounderLoopStorageMigrationRequiredError(FounderLoopStorageError):
    """Raised before a newer or unknown on-disk schema can be overwritten."""


class FounderLoopAuthorityError(FounderLoopStorageError):
    def __init__(
        self,
        reason_refs: list[str],
        *,
        code: str = "FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DENIED",
        required_refs: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.reason_refs = reason_refs
        self.required_refs = required_refs or {}


def active_founder_loop_authority_leases() -> list[AuthorityLease]:
    active = AuthorityLeaseStore().list_leases(active_only=True)
    return active or build_default_authority_leases()


MEMORY_REVIEW_WRITE_LANE_ID = "memory_review_accept_correct_reviewed_recall_write"
MEMORY_REVIEW_WRITE_SAFE_DISABLED_POSTURE_REF = (
    "safe-disable-posture-ref:memory-review:accept-correct-write-disabled"
)
MEMORY_REVIEW_WRITE_SAFE_DISABLED_BLOCKED_REF = (
    "blocked-state:memory-review-write-safe-disabled"
)


class JsonlLogKind(str, Enum):
    audit = "audit"
    transcript = "transcript"
    realtime = "realtime"
    receipt = "receipt"


class FounderLoopActionRecord(BaseModel):
    item_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    surface: str = Field(..., min_length=1, max_length=80)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    risk_class: str = Field(default="medium", min_length=1, max_length=40)
    action_kind: str = Field(default="review_only", min_length=1, max_length=80)
    status: str = Field(default="review_ready", min_length=1, max_length=80)
    side_effect_class: str = Field(
        default="validation_only", min_length=1, max_length=80
    )
    authority_boundary: str = Field(
        default=(
            "Control Center is review-only; Python Agent Core approval is required "
            "before mutation."
        ),
        min_length=1,
        max_length=240,
    )
    approval_required: bool = True
    approval_envelope_ref: str | None = Field(default=None, max_length=120)
    approval_envelope_status: str = Field(
        default="missing_until_scoped_contract",
        min_length=1,
        max_length=80,
    )
    state_change_contract_ref: str | None = Field(default=None, max_length=120)
    state_change_readiness: str = Field(
        default="blocked_missing_backend_contract",
        min_length=1,
        max_length=80,
    )
    blocked_state: str | None = Field(default=None, max_length=160)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_key_ref: str | None = Field(default=None, max_length=120)
    expires_at: str | None = Field(default=None, max_length=80)
    stale_state: str = Field(
        default="recheck_required_before_mutation",
        min_length=1,
        max_length=120,
    )
    rollback_ref: str | None = Field(default=None, max_length=120)
    safe_disable_ref: str | None = Field(default=None, max_length=120)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    max_approved_cost_usd: float = Field(default=0.0, ge=0)
    provider_ref: str = Field(default="provider-ref:not-invoked", min_length=1)
    model_profile_ref: str = Field(
        default="model-profile-ref:not-invoked",
        min_length=1,
    )
    input_metered_units: int = Field(default=0, ge=0)
    output_metered_units: int = Field(default=0, ge=0)
    total_metered_units: int = Field(default=0, ge=0)
    cost_estimate_ref: str = Field(default="cost-estimate-ref:not-invoked")
    captured_usage_ref: str = Field(default="usage-capture-ref:not-invoked")
    budget_decision_ref: str = Field(default="budget-decision-ref:not-invoked")
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    cost_state_label: str = Field(default="Cost blocked", min_length=1, max_length=80)
    provider_authority_state_label: str = Field(
        default="No provider authority",
        min_length=1,
        max_length=80,
    )
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False
    next_safe_action: str = Field(
        default="Review the safe summary and keep mutation blocked until a scoped backend contract exists.",
        min_length=1,
        max_length=240,
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopActionRecord":
        _validate_safe_ref(self.item_ref, "item_ref")
        for field_name in [
            "approval_envelope_ref",
            "state_change_contract_ref",
            "idempotency_key_ref",
            "rollback_ref",
            "safe_disable_ref",
            "provider_ref",
            "model_profile_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for field_name in [
            "evidence_refs",
            "receipt_refs",
            "audit_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("action cost metered unit total must match inputs")
        if self.frontier_usage_claimed and not self.cost_receipt_refs:
            raise ValueError("frontier usage claims require cost receipt refs")
        if not self.unknown_paid_cost_requires_explicit_approval:
            raise ValueError("unknown paid cost must require explicit approval")
        _validate_safe_ref(f"action-kind:{self.action_kind}", "action_kind")
        _validate_safe_payload(self.model_dump(mode="json"), "action_record")
        return self


class FounderLoopPlanRecord(BaseModel):
    plan_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    status: str = Field(
        default="partial_backend_not_product_ready", min_length=1, max_length=80
    )
    safe_summary: str = Field(..., min_length=1, max_length=500)
    next_step_summary: str = Field(..., min_length=1, max_length=500)
    evidence_refs: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopPlanRecord":
        _validate_safe_ref(self.plan_ref, "plan_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "plan_record")
        return self


class FounderLoopMemoryReviewRecord(BaseModel):
    review_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    candidate_kind: str = Field(default="preference", min_length=1, max_length=80)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="review_needed", min_length=1, max_length=80)
    review_state: str = Field(default="review_needed", min_length=1, max_length=80)
    side_effect_class: str = Field(
        default="local_dev_workspace_only", min_length=1, max_length=80
    )
    authority_boundary: str = Field(
        default=(
            "Review-only memory candidate; memory writes and context injection "
            "remain unscoped."
        ),
        min_length=1,
        max_length=240,
    )
    provenance_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    missing_contract_refs: list[str] = Field(default_factory=list)
    correction_posture: str = Field(
        default="correction_requires_scoped_memory_write_contract",
        min_length=1,
        max_length=160,
    )
    rejection_posture: str = Field(
        default="rejection_is_review_state_only",
        min_length=1,
        max_length=160,
    )
    retention_posture: str = Field(
        default="retention_policy_not_bound",
        min_length=1,
        max_length=160,
    )
    delete_posture: str = Field(
        default="delete_execution_not_scoped",
        min_length=1,
        max_length=160,
    )
    confidence_posture: str = Field(
        default="safe_summary_unverified",
        min_length=1,
        max_length=160,
    )
    stale_state: str = Field(
        default="recheck_source_refs_before_memory_use",
        min_length=1,
        max_length=160,
    )
    blocked_states: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(
        default=(
            "Review provenance and evidence refs; keep writes blocked until a "
            "scoped memory policy milestone."
        ),
        min_length=1,
        max_length=240,
    )
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopMemoryReviewRecord":
        _validate_safe_ref(self.review_ref, "review_ref")
        if self.candidate_kind not in BUSINESS_MEMORY_CANDIDATE_KINDS:
            raise ValueError(
                "memory review candidate_kind is not a supported business memory kind"
            )
        for field_name in [
            "provenance_refs",
            "source_refs",
            "missing_contract_refs",
            "evidence_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "memory_review_record")
        return self


class FounderLoopBriefingRecord(BaseModel):
    briefing_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="active", min_length=1, max_length=80)
    side_effect_class: str = Field(
        default="local_dev_workspace_only", min_length=1, max_length=80
    )
    authority_boundary: str = Field(
        default="Review-only briefing summary; source reads and delivery remain unscoped.",
        min_length=1,
        max_length=240,
    )
    source_readiness: str = Field(
        default="blocked_missing_source_contract",
        min_length=1,
        max_length=100,
    )
    source_refs: list[str] = Field(default_factory=list)
    missing_contract_refs: list[str] = Field(default_factory=list)
    blocked_states: list[str] = Field(default_factory=list)
    stale_state: str = Field(
        default="recheck_required_before_source_contract",
        min_length=1,
        max_length=120,
    )
    evidence_gap: str = Field(
        default="No source connector evidence is bound in this briefing slice.",
        min_length=1,
        max_length=240,
    )
    next_safe_action: str = Field(
        default="Define read-only source contracts before source reads or refresh.",
        min_length=1,
        max_length=240,
    )
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopBriefingRecord":
        _validate_safe_ref(self.briefing_ref, "briefing_ref")
        for field_name in ["source_refs", "missing_contract_refs", "evidence_refs"]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "briefing_record")
        return self


class FounderLoopEvidenceHistoryAnswer(BaseModel):
    question: str = Field(..., min_length=1, max_length=80)
    answer: str = Field(..., min_length=1, max_length=320)
    refs: list[str] = Field(default_factory=list)
    status: str = Field(default="present", min_length=1, max_length=80)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_answer(self) -> "FounderLoopEvidenceHistoryAnswer":
        for ref_value in self.refs:
            _validate_safe_ref(ref_value, "history_answer_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_history_answer")
        return self


class FounderLoopEvidenceTimelineItem(BaseModel):
    timeline_item_ref: str = Field(..., min_length=1)
    item_kind: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    history_contract_ref: str = Field(
        default=EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
        min_length=1,
        max_length=120,
    )
    history_answers: dict[str, FounderLoopEvidenceHistoryAnswer]
    source_refs: list[str] = Field(default_factory=list)
    status_refs: list[str] = Field(default_factory=list)
    related_route_refs: list[str] = Field(default_factory=list)
    side_effect_class: str = Field(
        default="local_dev_workspace_only", min_length=1, max_length=80
    )
    authority_posture: str = Field(..., min_length=1, max_length=240)
    approval_posture: str = Field(
        default="approval_refs_are_identifiers_only_not_authority",
        min_length=1,
        max_length=160,
    )
    approval_ref_authority: bool = False
    rollback_execution_enabled: bool = False
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    raw_evidence_included: bool = False
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    rollback_blockers: list[str] = Field(default_factory=list)
    latency_refs: list[str] = Field(default_factory=list)
    foundation_gate_refs: list[str] = Field(default_factory=list)
    redaction_status: str = Field(
        default="redacted_summary_only", min_length=1, max_length=80
    )
    stale_state: str = Field(
        default="recheck_refs_before_use", min_length=1, max_length=120
    )
    missing_evidence_posture: str = Field(
        default="no_missing_safe_refs", min_length=1, max_length=180
    )
    blocked_states: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceTimelineItem":
        _validate_safe_ref(self.timeline_item_ref, "timeline_item_ref")
        _validate_safe_ref(self.history_contract_ref, "history_contract_ref")
        if self.history_contract_ref != EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF:
            raise ValueError(
                "evidence timeline item must use the current history grammar"
            )
        if set(self.history_answers) != set(EVIDENCE_HISTORY_GRAMMAR_KEYS):
            raise ValueError(
                "evidence timeline item must answer every history grammar question"
            )
        if self.approval_ref_authority:
            raise ValueError("approval refs are identifiers only")
        if self.rollback_execution_enabled:
            raise ValueError("rollback execution is not scoped")
        if self.memory_truth_authority:
            raise ValueError("memory evidence is not truth authority")
        if self.context_injection_authorized:
            raise ValueError("context injection is not authorized")
        if self.raw_evidence_included:
            raise ValueError("raw evidence is not allowed")
        for field_name in [
            "source_refs",
            "status_refs",
            "receipt_refs",
            "audit_refs",
            "idempotency_refs",
            "replay_refs",
            "rollback_refs",
            "safe_disable_refs",
            "latency_refs",
            "foundation_gate_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        for route_ref in self.related_route_refs:
            _validate_safe_text(route_ref, "related_route_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_timeline_item")
        return self


EvidenceTimelineProductizedEventType = Literal[
    "action_envelope_created",
    "action_decision_recorded",
    "local_task_created",
    "chat_turn_receipt_recorded",
    "chat_handoff_created",
    "memory_review_decision_recorded",
    "web_evidence_attached",
]
EvidenceTimelineProductizedGroupKind = Literal[
    "today_item",
    "action",
    "chat_turn",
    "memory_candidate",
    "web_evidence",
]


class FounderLoopEvidenceTimelineEvent(BaseModel):
    event_ref: str = Field(..., min_length=1)
    event_type: EvidenceTimelineProductizedEventType
    event_type_ref: str = Field(..., min_length=1)
    group_kind: EvidenceTimelineProductizedGroupKind
    group_ref: str = Field(..., min_length=1)
    group_label: str = Field(..., min_length=1, max_length=120)
    timeline_item_ref: str = Field(..., min_length=1)
    item_kind: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    history_answers: dict[str, FounderLoopEvidenceHistoryAnswer]
    source_refs: list[str] = Field(default_factory=list)
    status_refs: list[str] = Field(default_factory=list)
    related_route_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    rollback_blockers: list[str] = Field(default_factory=list)
    blocked_states: list[str] = Field(default_factory=list)
    rollback_posture: str = Field(..., min_length=1, max_length=180)
    authority_posture: str = Field(..., min_length=1, max_length=240)
    redaction_status: str = Field(
        default="redacted_summary_only", min_length=1, max_length=80
    )
    raw_evidence_included: bool = False
    approval_ref_authority: bool = False
    rollback_execution_enabled: bool = False
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceTimelineEvent":
        for ref_value in [
            self.event_ref,
            self.event_type_ref,
            self.group_ref,
            self.timeline_item_ref,
        ]:
            _validate_safe_ref(ref_value, "evidence_timeline_event_ref")
        if set(self.history_answers) != set(EVIDENCE_HISTORY_GRAMMAR_KEYS):
            raise ValueError(
                "evidence timeline event must answer every history grammar question"
            )
        if self.raw_evidence_included:
            raise ValueError("raw evidence is not allowed")
        if self.approval_ref_authority:
            raise ValueError("approval refs are identifiers only")
        if self.rollback_execution_enabled:
            raise ValueError("rollback execution is not scoped")
        if self.memory_truth_authority:
            raise ValueError("memory evidence is not truth authority")
        if self.context_injection_authorized:
            raise ValueError("context injection is not authorized")
        for field_name in [
            "source_refs",
            "status_refs",
            "receipt_refs",
            "approval_refs",
            "idempotency_refs",
            "audit_refs",
            "rollback_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        for route_ref in self.related_route_refs:
            _validate_safe_text(route_ref, "related_route_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_timeline_event")
        return self


class FounderLoopEvidenceTimelineGroup(BaseModel):
    group_ref: str = Field(..., min_length=1)
    group_kind: EvidenceTimelineProductizedGroupKind
    group_label: str = Field(..., min_length=1, max_length=120)
    event_count: int = Field(..., ge=0)
    event_refs: list[str] = Field(default_factory=list)
    event_types: list[EvidenceTimelineProductizedEventType] = Field(
        default_factory=list
    )
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    blocked_states: list[str] = Field(default_factory=list)
    rollback_posture: str = Field(..., min_length=1, max_length=180)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceTimelineGroup":
        _validate_safe_ref(self.group_ref, "evidence_timeline_group_ref")
        for field_name in [
            "event_refs",
            "receipt_refs",
            "approval_refs",
            "idempotency_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_timeline_group")
        return self


class FounderLoopEvidenceNarrativeEntry(BaseModel):
    narrative_ref: str = Field(..., min_length=1)
    event_ref: str = Field(..., min_length=1)
    timeline_item_ref: str = Field(..., min_length=1)
    group_ref: str = Field(..., min_length=1)
    group_kind: str = Field(..., min_length=1, max_length=80)
    event_type: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    what_happened: str = Field(..., min_length=1, max_length=320)
    why_recorded: str = Field(..., min_length=1, max_length=320)
    approval_posture: str = Field(..., min_length=1, max_length=320)
    change_summary: str = Field(..., min_length=1, max_length=320)
    remaining_blocked: str = Field(..., min_length=1, max_length=320)
    inspection_summary: str = Field(..., min_length=1, max_length=320)
    source_refs: list[str] = Field(default_factory=list)
    status_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    raw_content_included: bool = False
    approval_ref_authority: bool = False
    rollback_execution_enabled: bool = False
    action_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    workflow_execution_enabled: bool = False
    connector_write_enabled: bool = False
    connector_runtime_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    public_beta_enabled: bool = False
    distribution_enabled: bool = False
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceNarrativeEntry":
        for ref_value in [
            self.narrative_ref,
            self.event_ref,
            self.timeline_item_ref,
            self.group_ref,
        ]:
            _validate_evidence_narrative_ref(ref_value, "evidence_narrative_ref")
        for field_name in [
            "source_refs",
            "status_refs",
            "receipt_refs",
            "approval_refs",
            "audit_refs",
            "idempotency_refs",
            "rollback_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_evidence_narrative_ref(ref_value, field_name)
        for field_name in [
            "group_kind",
            "event_type",
            "title",
            "what_happened",
            "why_recorded",
            "approval_posture",
            "change_summary",
            "remaining_blocked",
            "inspection_summary",
        ]:
            _validate_evidence_narrative_text(
                str(getattr(self, field_name)), field_name
            )
        denied_flags = {
            "raw_content_included": self.raw_content_included,
            "approval_ref_authority": self.approval_ref_authority,
            "rollback_execution_enabled": self.rollback_execution_enabled,
            "action_execution_enabled": self.action_execution_enabled,
            "tool_execution_enabled": self.tool_execution_enabled,
            "workflow_execution_enabled": self.workflow_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "connector_runtime_enabled": self.connector_runtime_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "runtime_model_calls_enabled": self.runtime_model_calls_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "live_web_enabled": self.live_web_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "browser_execution_enabled": self.browser_execution_enabled,
            "public_beta_enabled": self.public_beta_enabled,
            "distribution_enabled": self.distribution_enabled,
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
            "memory_truth_authority": self.memory_truth_authority,
            "context_injection_authorized": self.context_injection_authorized,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"evidence narrative violated authority: {enabled[0]}")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "evidence_timeline_narrative_entry",
        )
        return self


class FounderLoopEvidenceTimelineNarrativeReadModel(BaseModel):
    schema_version: str = "product-loop-010-evidence-timeline-narrative.v1"
    contract_ref: str = EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF
    source: str = EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE
    status: str = "implemented_evidence_timeline_narrative_safe_refs_only"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    narrative_from_existing_refs_only: bool = True
    raw_content_included: bool = False
    entry_count: int = Field(default=0, ge=0)
    event_count: int = Field(default=0, ge=0)
    group_count: int = Field(default=0, ge=0)
    narrative_item_count: int = Field(default=0, ge=0)
    entries: list[FounderLoopEvidenceNarrativeEntry] = Field(default_factory=list)
    narrative_refs: list[str] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    timeline_item_refs: list[str] = Field(default_factory=list)
    group_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    authority_boundary: str = (
        "Evidence Timeline narrative is a read-only safe-ref history over "
        "existing receipts, audit refs, approval posture refs, blocker refs, "
        "and redacted summaries; it grants no approval, rollback, action, "
        "connector, memory, context, provider, or production authority."
    )
    next_safe_action: str = (
        "Inspect narrative entries and underlying refs; use owner routes for "
        "any later exact-scoped decisions."
    )
    approval_ref_authority: bool = False
    rollback_execution_enabled: bool = False
    action_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    workflow_execution_enabled: bool = False
    connector_write_enabled: bool = False
    connector_runtime_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    public_beta_enabled: bool = False
    distribution_enabled: bool = False
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "FounderLoopEvidenceTimelineNarrativeReadModel":
        if self.schema_version != "product-loop-010-evidence-timeline-narrative.v1":
            raise ValueError("unexpected evidence narrative schema version")
        if self.contract_ref != EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF:
            raise ValueError("unexpected evidence narrative contract ref")
        if self.source != EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE:
            raise ValueError("unexpected evidence narrative source")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
            "redacted_summaries_only",
            "narrative_from_existing_refs_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        denied_flags = {
            "raw_content_included": self.raw_content_included,
            "approval_ref_authority": self.approval_ref_authority,
            "rollback_execution_enabled": self.rollback_execution_enabled,
            "action_execution_enabled": self.action_execution_enabled,
            "tool_execution_enabled": self.tool_execution_enabled,
            "workflow_execution_enabled": self.workflow_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "connector_runtime_enabled": self.connector_runtime_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "runtime_model_calls_enabled": self.runtime_model_calls_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "live_web_enabled": self.live_web_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "browser_execution_enabled": self.browser_execution_enabled,
            "public_beta_enabled": self.public_beta_enabled,
            "distribution_enabled": self.distribution_enabled,
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
            "memory_truth_authority": self.memory_truth_authority,
            "context_injection_authorized": self.context_injection_authorized,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"evidence narrative violated authority: {enabled[0]}")
        if self.entry_count != len(self.entries):
            raise ValueError("evidence narrative entry count mismatch")
        if self.narrative_refs != [entry.narrative_ref for entry in self.entries]:
            raise ValueError("evidence narrative refs must match entries")
        expected_ref_sets = {
            "event_refs": _unique_sorted_refs(
                entry.event_ref for entry in self.entries
            ),
            "timeline_item_refs": _unique_sorted_refs(
                entry.timeline_item_ref for entry in self.entries
            ),
            "group_refs": _unique_sorted_refs(
                entry.group_ref for entry in self.entries
            ),
            "receipt_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.receipt_refs
            ),
            "approval_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.approval_refs
            ),
            "audit_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.audit_refs
            ),
            "idempotency_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.idempotency_refs
            ),
            "rollback_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.rollback_refs
            ),
            "evidence_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.evidence_refs
            ),
            "blocked_state_refs": _unique_sorted_refs(
                ref for entry in self.entries for ref in entry.blocked_state_refs
            ),
        }
        for field_name, expected_refs in expected_ref_sets.items():
            if getattr(self, field_name) != expected_refs:
                raise ValueError(f"{field_name} must match narrative entries")
        for field_name in [
            "narrative_refs",
            "event_refs",
            "timeline_item_refs",
            "group_refs",
            "receipt_refs",
            "approval_refs",
            "audit_refs",
            "idempotency_refs",
            "rollback_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_evidence_narrative_ref(ref_value, field_name)
        _validate_evidence_narrative_text(self.status, "status")
        _validate_evidence_narrative_text(self.authority_boundary, "authority_boundary")
        _validate_evidence_narrative_text(self.next_safe_action, "next_safe_action")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "evidence_timeline_narrative_read_model",
        )
        return self


EvidenceAuditGroupKind = Literal[
    "plan_changes",
    "approval_waits",
    "action_proposals",
    "execution_receipts",
    "memory_proposals_review_decisions",
    "blocked_no_go_events",
    "recovery_events",
]


class FounderLoopEvidenceAuditReceiptEnvelope(BaseModel):
    envelope_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    receipt_recorded: bool = False
    run_ref: str = Field(..., min_length=1)
    action_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    event_ref: str = Field(..., min_length=1)
    timeline_item_ref: str = Field(..., min_length=1)
    group_ref: str = Field(..., min_length=1)
    side_effect_class: str = "local_dev_workspace_only"
    authority_decision_ref: str = Field(..., min_length=1)
    input_ref: str = Field(..., min_length=1)
    output_ref: str = Field(..., min_length=1)
    artifact_hash_ref: str = Field(..., min_length=1)
    timestamp_ref: str = Field(..., min_length=1)
    verifier_version_ref: str = Field(..., min_length=1)
    redaction_status: str = "redacted_summary_only"
    safe_summary: str = Field(..., min_length=1, max_length=420)
    route_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    missing_receipt_refs: list[str] = Field(default_factory=list)
    raw_content_included: bool = False
    approval_ref_authority: bool = False
    action_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_envelope(self) -> "FounderLoopEvidenceAuditReceiptEnvelope":
        for field_name in [
            "envelope_ref",
            "receipt_ref",
            "run_ref",
            "action_ref",
            "approval_ref",
            "event_ref",
            "timeline_item_ref",
            "group_ref",
            "authority_decision_ref",
            "input_ref",
            "output_ref",
            "artifact_hash_ref",
            "timestamp_ref",
            "verifier_version_ref",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.side_effect_class, "side_effect_class")
        _validate_safe_text(self.redaction_status, "redaction_status")
        _validate_safe_text(self.safe_summary, "safe_summary")
        for route_ref in self.route_refs:
            _validate_safe_text(route_ref, "route_ref")
        for field_name in [
            "evidence_refs",
            "audit_refs",
            "idempotency_refs",
            "rollback_refs",
            "blocked_state_refs",
            "missing_receipt_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        if self.receipt_recorded and self.missing_receipt_refs:
            raise ValueError("recorded receipt envelope cannot have missing refs")
        if not self.receipt_recorded and not self.missing_receipt_refs:
            raise ValueError("missing receipt envelope must expose missing ref")
        denied_flags = {
            "raw_content_included": self.raw_content_included,
            "approval_ref_authority": self.approval_ref_authority,
            "action_execution_enabled": self.action_execution_enabled,
            "tool_execution_enabled": self.tool_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "runtime_model_call_enabled": self.runtime_model_call_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "live_web_enabled": self.live_web_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "browser_execution_enabled": self.browser_execution_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                f"evidence audit receipt envelope enabled denied authority: {enabled[0]}"
            )
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "evidence_audit_receipt_envelope",
        )
        return self


class FounderLoopEvidenceAuditGroup(BaseModel):
    group_ref: str = Field(..., min_length=1)
    group_kind: EvidenceAuditGroupKind
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    event_refs: list[str] = Field(default_factory=list)
    timeline_item_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    missing_receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=300)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_group(self) -> "FounderLoopEvidenceAuditGroup":
        _validate_safe_ref(self.group_ref, "evidence_audit_group_ref")
        for field_name in ["group_kind", "label", "status", "safe_summary"]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in [
            "event_refs",
            "timeline_item_refs",
            "receipt_refs",
            "approval_refs",
            "audit_refs",
            "idempotency_refs",
            "rollback_refs",
            "evidence_refs",
            "missing_receipt_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_text(self.next_safe_action, "next_safe_action")
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_audit_group")
        return self


class FounderLoopEvidenceAuditReceiptSpine(BaseModel):
    schema_version: str = "runtime-evidence-audit-spine.v1"
    contract_ref: str = EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    source: str = EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE
    status: str = "implemented_backend_owned_evidence_audit_receipt_spine"
    backend_owned: bool = True
    control_center_presentation_only: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    raw_content_included: bool = False
    route_refs: list[str] = Field(default_factory=list)
    cli_ref: str = "python scripts/dev/uaa_founder_loop.py inspect-evidence-audit-spine"
    receipt_envelope_field_refs: list[str] = Field(default_factory=list)
    timeline_group_kinds: list[EvidenceAuditGroupKind] = Field(default_factory=list)
    group_count: int = Field(..., ge=0)
    envelope_count: int = Field(..., ge=0)
    missing_receipt_count: int = Field(..., ge=0)
    groups: list[FounderLoopEvidenceAuditGroup] = Field(default_factory=list)
    receipt_envelopes: list[FounderLoopEvidenceAuditReceiptEnvelope] = Field(
        default_factory=list
    )
    receipt_refs: list[str] = Field(default_factory=list)
    missing_receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    portable_evidence_posture: str = (
        "hash_refs_and_verifier_refs_available_for_local_inspection_only"
    )
    redaction_posture: str = (
        "safe_refs_and_bounded_summaries_only_private_source_material_omitted"
    )
    authority_boundary: str = (
        "Evidence audit receipt spine is read-only lineage over existing "
        "timeline, receipt, proof, approval, audit, idempotency, rollback, "
        "and blocked refs. It grants no approval, execution, connector, "
        "provider, browser, shell, background, or production authority."
    )
    next_safe_action: str = (
        "Inspect groups, receipt envelopes, missing receipt refs, and proof "
        "refs before promoting any later exact authority lane."
    )
    approval_ref_authority: bool = False
    action_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    external_export_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_spine(self) -> "FounderLoopEvidenceAuditReceiptSpine":
        if self.schema_version != "runtime-evidence-audit-spine.v1":
            raise ValueError("evidence audit spine schema drift")
        if self.contract_ref != EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF:
            raise ValueError("evidence audit spine contract drift")
        if self.source != EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE:
            raise ValueError("evidence audit spine source drift")
        for field_name in [
            "backend_owned",
            "control_center_presentation_only",
            "local_read_model_only",
            "safe_refs_only",
            "redacted_summaries_only",
        ]:
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        denied_flags = {
            "raw_content_included": self.raw_content_included,
            "approval_ref_authority": self.approval_ref_authority,
            "action_execution_enabled": self.action_execution_enabled,
            "tool_execution_enabled": self.tool_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "runtime_model_call_enabled": self.runtime_model_call_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "live_web_enabled": self.live_web_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "browser_execution_enabled": self.browser_execution_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "external_export_enabled": self.external_export_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                f"evidence audit spine enabled denied authority: {enabled[0]}"
            )
        if self.timeline_group_kinds != list(EVIDENCE_AUDIT_GROUP_KINDS):
            raise ValueError("evidence audit spine group kinds drifted")
        if self.group_count != len(self.groups):
            raise ValueError("evidence audit group count mismatch")
        if self.envelope_count != len(self.receipt_envelopes):
            raise ValueError("evidence audit envelope count mismatch")
        if self.missing_receipt_count != len(self.missing_receipt_refs):
            raise ValueError("evidence audit missing receipt count mismatch")
        expected = {
            "receipt_refs": _unique_sorted_refs(
                envelope.receipt_ref
                for envelope in self.receipt_envelopes
                if envelope.receipt_recorded
            ),
            "missing_receipt_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.missing_receipt_refs
            ),
            "evidence_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.evidence_refs
            ),
            "audit_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.audit_refs
            ),
            "approval_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in (
                    []
                    if envelope.approval_ref.startswith("approval-ref:not-")
                    else [envelope.approval_ref]
                )
            ),
            "idempotency_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.idempotency_refs
            ),
            "rollback_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.rollback_refs
            ),
            "blocked_state_refs": _unique_sorted_refs(
                ref
                for envelope in self.receipt_envelopes
                for ref in envelope.blocked_state_refs
            ),
        }
        for field_name, expected_refs in expected.items():
            if getattr(self, field_name) != expected_refs:
                raise ValueError(f"{field_name} must match receipt envelopes")
        for route_ref in self.route_refs:
            _validate_safe_text(route_ref, "route_ref")
        for field_name in [
            "contract_ref",
            "cli_ref",
            "portable_evidence_posture",
            "redaction_posture",
            "authority_boundary",
            "next_safe_action",
        ]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in [
            "receipt_envelope_field_refs",
            "receipt_refs",
            "missing_receipt_refs",
            "evidence_refs",
            "audit_refs",
            "approval_refs",
            "idempotency_refs",
            "rollback_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "evidence_audit_receipt_spine",
        )
        return self


class FounderLoopOperatorRunBorrowedPattern(BaseModel):
    pattern_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=320)
    implemented: bool = True
    source_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_pattern(self) -> "FounderLoopOperatorRunBorrowedPattern":
        if self.pattern_id not in {
            str(pattern["pattern_id"])
            for pattern in OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS
        }:
            raise ValueError("operator run borrowed pattern is not recognized")
        _validate_safe_ref(self.source_ref, "operator_run_pattern_source_ref")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "operator_run_borrowed_pattern",
        )
        return self


class FounderLoopOperatorRunCostUsage(BaseModel):
    schema_version: str = "uaa_frontier_ai_cost_usage_slot.v1"
    contract_ref: str = FRONTIER_AI_COST_USAGE_CONTRACT_REF
    cost_event_ref: str = Field(..., min_length=1)
    cost_estimate_ref: str = Field(..., min_length=1)
    captured_usage_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    source_event_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    model_profile_ref: str = Field(..., min_length=1)
    provider_model_ref_status: str = Field(..., min_length=1, max_length=120)
    usage_capture_status: str = Field(..., min_length=1, max_length=120)
    cost_capture_status: str = Field(..., min_length=1, max_length=120)
    cost_state_label: str = Field(..., min_length=1, max_length=80)
    provider_authority_state_label: str = Field(..., min_length=1, max_length=80)
    frontier_usage_claimed: bool = False
    frontier_ai_routing_allowed: bool = False
    input_metered_units: int = Field(default=0, ge=0)
    output_metered_units: int = Field(default=0, ge=0)
    total_metered_units: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    captured_cost_usd: float = Field(default=0.0, ge=0)
    max_approved_cost_usd: float = Field(default=0.0, ge=0)
    unknown_cost: bool = False
    approval_required_for_unknown_paid_cost: bool = True
    cost_governor_ref: str = "core.costs.CostGovernor"
    cost_governor_allowed: bool = False
    cost_governor_decision_status: str = Field(..., min_length=1, max_length=80)
    cost_governor_reason_refs: list[str] = Field(default_factory=list)
    budget_status_ref: str = Field(..., min_length=1)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_cost_usage(self) -> "FounderLoopOperatorRunCostUsage":
        for field_name in [
            "contract_ref",
            "cost_event_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
            "source_event_ref",
            "provider_ref",
            "model_profile_ref",
            "budget_status_ref",
        ]:
            _validate_safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "cost_governor_reason_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("frontier AI metered unit total must match inputs")
        if self.unknown_cost and not self.approval_required_for_unknown_paid_cost:
            raise ValueError("unknown paid cost must require explicit approval")
        if self.frontier_usage_claimed and not self.cost_receipt_refs:
            raise ValueError("frontier usage claims require cost receipt refs")
        if self.frontier_usage_claimed and (
            self.provider_ref == "provider-ref:not-invoked"
            or self.model_profile_ref == "model-profile-ref:not-invoked"
        ):
            if "blocked-state:frontier-provider-model-ref-missing" not in set(
                self.cost_blocked_state_refs
            ):
                raise ValueError("claimed frontier usage requires provider/model refs")
        if self.estimated_cost_usd > self.max_approved_cost_usd:
            if "blocked-state:frontier-ai-cost-budget-exceeded" not in set(
                self.cost_blocked_state_refs
            ):
                raise ValueError("cost above approved max must be blocked")
        denied_flags = {
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                f"frontier AI cost usage stored denied content: {enabled[0]}"
            )
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "operator_run_cost_usage",
        )
        return self


class FounderLoopOperatorRunEvent(BaseModel):
    run_event_ref: str = Field(..., min_length=1)
    event_ref: str = Field(..., min_length=1)
    event_kind: str = Field(..., min_length=1, max_length=80)
    event_source: str = Field(..., min_length=1, max_length=120)
    llm_role_projection: str = Field(..., min_length=1, max_length=80)
    operator_state: str = Field(..., min_length=1, max_length=80)
    approval_state: str = Field(..., min_length=1, max_length=120)
    completion_state: str = Field(..., min_length=1, max_length=120)
    completion_claim_allowed: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=500)
    condensed_summary_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    status_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    related_route_refs: list[str] = Field(default_factory=list)
    authority_boundary: str = Field(..., min_length=1, max_length=360)
    cost_usage: FounderLoopOperatorRunCostUsage
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False
    provider_model_authority_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_run_event(self) -> "FounderLoopOperatorRunEvent":
        if self.operator_state not in set(OPERATOR_RUN_TIMELINE_STATES):
            raise ValueError("operator run state is not recognized")
        for field_name in [
            "run_event_ref",
            "event_ref",
            "condensed_summary_ref",
        ]:
            _validate_safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "source_refs",
            "status_refs",
            "receipt_refs",
            "approval_refs",
            "audit_refs",
            "idempotency_refs",
            "rollback_refs",
            "blocked_state_refs",
            "evidence_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        for route_ref in self.related_route_refs:
            _validate_safe_text(route_ref, "operator_run_route_ref")
        denied_flags = {
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
            "provider_model_authority_allowed": self.provider_model_authority_allowed,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                f"operator run event enabled denied authority: {enabled[0]}"
            )
        _validate_safe_payload(self.model_dump(mode="json"), "operator_run_event")
        return self


class FounderLoopOperatorRunControlSummary(BaseModel):
    states: list[str]
    state_refs: list[str]
    waiting_for_approval_count: int = Field(..., ge=0)
    receipt_recorded_count: int = Field(..., ge=0)
    blocked_count: int = Field(..., ge=0)
    needs_evidence_count: int = Field(..., ge=0)
    stuck_detection_status: str = Field(..., min_length=1, max_length=120)
    pause_resume_status: str = Field(..., min_length=1, max_length=120)
    goal_completion_status: str = Field(..., min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_control_summary(self) -> "FounderLoopOperatorRunControlSummary":
        if set(self.states) != set(OPERATOR_RUN_TIMELINE_STATES):
            raise ValueError("operator run control summary must include all states")
        for ref_value in self.state_refs:
            _validate_safe_ref(ref_value, "operator_run_state_ref")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "operator_run_control_summary",
        )
        return self


class FounderLoopFrontierAiUsageSummary(BaseModel):
    schema_version: str = "uaa_frontier_ai_usage_summary.v1"
    contract_ref: str = FRONTIER_AI_COST_USAGE_CONTRACT_REF
    status: str = Field(..., min_length=1, max_length=120)
    provider_model_authority_allowed: bool = False
    provider_sdk_call_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False
    estimated_total_cost_usd: float = Field(default=0.0, ge=0)
    captured_total_cost_usd: float = Field(default=0.0, ge=0)
    input_metered_units: int = Field(default=0, ge=0)
    output_metered_units: int = Field(default=0, ge=0)
    total_metered_units: int = Field(default=0, ge=0)
    unknown_paid_cost_requires_approval_before_routing: bool = True
    cost_governor_ref: str = "core.costs.CostGovernor"
    budget_status_ref: str = Field(..., min_length=1)
    cost_event_refs: list[str] = Field(default_factory=list)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_usage_summary(self) -> "FounderLoopFrontierAiUsageSummary":
        _validate_safe_ref(self.contract_ref, "frontier_ai_usage_contract_ref")
        _validate_safe_ref(self.budget_status_ref, "budget_status_ref")
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("frontier AI usage summary metered total mismatch")
        for field_name in [
            "cost_event_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        denied_flags = {
            "provider_model_authority_allowed": self.provider_model_authority_allowed,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "runtime_model_calls_enabled": self.runtime_model_calls_enabled,
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                f"frontier AI usage summary enabled denied authority: {enabled[0]}"
            )
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "frontier_ai_usage_summary",
        )
        return self


class FounderLoopOperatorRunTimeline(BaseModel):
    schema_version: str = "founder_loop_operator_run_timeline.v1"
    contract_ref: str = OPERATOR_RUN_TIMELINE_CONTRACT_REF
    status: str = Field(..., min_length=1, max_length=120)
    source: str = Field(..., min_length=1, max_length=120)
    route_ref: str = Field(..., min_length=1, max_length=120)
    frontend_route_refs: list[str]
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    provider_model_authority_allowed: bool = False
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_exchange_content_stored: bool = False
    borrowed_patterns: list[FounderLoopOperatorRunBorrowedPattern]
    event_count: int = Field(..., ge=0)
    group_count: int = Field(..., ge=0)
    narrative_item_count: int = Field(..., ge=0)
    run_events: list[FounderLoopOperatorRunEvent]
    run_control_summary: FounderLoopOperatorRunControlSummary
    frontier_ai_usage_summary: FounderLoopFrontierAiUsageSummary
    blocked_state_refs: list[str] = Field(default_factory=list)
    authority_boundary: str = Field(..., min_length=1, max_length=420)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_timeline(self) -> "FounderLoopOperatorRunTimeline":
        _validate_safe_ref(self.contract_ref, "operator_run_timeline_contract_ref")
        _validate_safe_text(self.route_ref, "operator_run_timeline_route_ref")
        for route_ref in self.frontend_route_refs:
            _validate_safe_text(route_ref, "operator_run_frontend_route_ref")
        if {pattern.pattern_id for pattern in self.borrowed_patterns} != {
            str(pattern["pattern_id"])
            for pattern in OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS
        }:
            raise ValueError("operator run timeline must expose all borrowed patterns")
        if self.event_count != len(self.run_events):
            raise ValueError("operator run timeline event count mismatch")
        for ref_value in self.blocked_state_refs:
            _validate_safe_ref(ref_value, "operator_run_blocked_state_ref")
        denied_flags = {
            "safe_refs_only": not self.safe_refs_only,
            "redacted_summaries_only": not self.redacted_summaries_only,
            "action_execution_enabled": self.action_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "runtime_model_calls_enabled": self.runtime_model_calls_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "provider_model_authority_allowed": self.provider_model_authority_allowed,
            "prompt_content_stored": self.prompt_content_stored,
            "response_content_stored": self.response_content_stored,
            "provider_exchange_content_stored": self.provider_exchange_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"operator run timeline violated authority: {enabled[0]}")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "operator_run_timeline",
        )
        return self


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_evidence_narrative_ref(value: str, field_name: str) -> None:
    _validate_safe_ref(value, field_name)
    lowered = value.lower()
    unsafe_fragments = (
        "raw-prompt",
        "raw_prompt",
        "raw-response",
        "raw_response",
        "raw-provider",
        "raw_provider",
        "raw-path",
        "raw_path",
        "raw-log",
        "raw_log",
        "prompt-content",
        "prompt_content",
        "response-content",
        "response_content",
        "provider-exchange-content",
        "provider_exchange_content",
        "username",
        "hostname",
        "serial",
        "private-key",
        "private_key",
        "provider-payload",
        "provider_payload",
        "raw-private-content",
        "raw_private_content",
        "credential",
        "password",
        "secret",
        "bearer",
        "token",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe private/provider ref")
    if "@" in value or "\\" in value:
        raise ValueError(f"{field_name} contains unsafe identity/path-shaped ref")
    if "." in value:
        raise ValueError(f"{field_name} contains unsafe host-shaped ref")
    if "/" in value and not value.startswith("evidence-timeline:"):
        raise ValueError(f"{field_name} contains unsafe path-shaped ref")


def _validate_evidence_narrative_text(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    lowered = value.lower()
    unsafe_fragments = (
        "raw-prompt",
        "raw-response",
        "raw-provider",
        "raw-path",
        "raw-log",
        "prompt-content",
        "response-content",
        "provider-exchange-content",
        "username ",
        "username:",
        "hostname ",
        "hostname:",
        "serial ",
        "serial:",
        "actor-ref:username",
        "host-ref:hostname",
        "device-ref:serial",
        "private_key",
        "private-key",
        "authorization",
        "bearer token",
        "api key",
        "password",
        "secret",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe narrative text")


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_STORAGE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe Founder Loop storage text")


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_safe_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(
                fragment in normalized_key for fragment in UNSAFE_STORAGE_KEY_FRAGMENTS
            ):
                raise ValueError(
                    f"{field_name} contains unsafe Founder Loop storage key"
                )
            _validate_safe_payload(str(key), field_name)
            _validate_safe_payload(item, field_name)


def _json_dumps(value: Any) -> str:
    _validate_safe_payload(value, "json_payload")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _timeline_ref(kind: str, source_ref: str) -> str:
    return f"evidence-timeline:{kind}/{source_ref.replace(':', '/')}"


def _evidence_event_ref(event_type: str, timeline_item_ref: str) -> str:
    return _status_ref("evidence-event", f"{event_type}:{timeline_item_ref}")


def _first_ref_with_prefix(refs: list[str], prefix: str) -> str | None:
    for ref in refs:
        if str(ref).startswith(prefix):
            return str(ref)
    return None


def _first_ref_or(refs: list[str], fallback: str) -> str:
    return str(refs[0]) if refs else fallback


def _unique_sorted_refs(refs: Any) -> list[str]:
    return sorted({str(ref) for ref in refs if ref})


def _loop_trace_refs_from_runs_integration(
    read_model: dict[str, Any],
) -> dict[str, list[str]]:
    return {
        "run_refs": list(read_model.get("run_refs") or []),
        "operator_run_event_refs": list(
            read_model.get("operator_run_event_refs") or []
        ),
        "receipt_refs": list(read_model.get("receipt_refs") or []),
        "evidence_refs": list(read_model.get("evidence_refs") or []),
        "evidence_event_refs": list(read_model.get("evidence_event_refs") or []),
        "proof_refs": list(read_model.get("proof_refs") or []),
        "approval_refs": list(read_model.get("approval_refs") or []),
        "blocked_authority_refs": list(read_model.get("blocked_authority_refs") or []),
    }


def _safe_blocked_refs(values: Any) -> list[str]:
    safe_refs: list[str] = []
    for value in values:
        ref = _evidence_narrative_status_ref("blocked-state", str(value))
        safe_refs.append(ref)
    return _unique_sorted_refs(safe_refs)


def _status_ref(prefix: str, value: str) -> str:
    safe_value = SAFE_STATUS_REF_CHARS.sub("-", value.lower()).strip("-")
    if not safe_value:
        safe_value = "missing"
    return f"{prefix}:{safe_value}"


def _missing_receipt_ref(value: str) -> str:
    return _status_ref("missing-receipt", value)


def _artifact_hash_ref(kind: str, value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"artifact-hash-ref:{kind}:sha256-{digest[:16]}"


def _first_action_ref(value: dict[str, Any]) -> str:
    for ref_value in [
        *list(value.get("source_refs") or []),
        str(value.get("group_ref") or ""),
    ]:
        ref = str(ref_value)
        if ref.startswith(
            (
                "founder-action:",
                "action-envelope:",
                "local-task:",
                "internal-action-proposal:",
            )
        ):
            return ref
    return "action-ref:not-applicable"


def _evidence_audit_group_definition(
    group_kind: EvidenceAuditGroupKind,
) -> dict[str, str]:
    definitions = {
        "plan_changes": {
            "label": "Plan changes",
            "safe_summary": (
                "Plan and proposal changes are grouped as read-only evidence refs."
            ),
            "next_safe_action": (
                "Inspect plan and proposal refs before creating any exact Action lane."
            ),
        },
        "approval_waits": {
            "label": "Approval waits",
            "safe_summary": (
                "Approval refs are identifiers only until an owner lane validates scope."
            ),
            "next_safe_action": (
                "Inspect approval refs and blocked states; approval refs alone grant no authority."
            ),
        },
        "action_proposals": {
            "label": "Action proposals",
            "safe_summary": (
                "Action proposals and envelopes are visible before any execution lane."
            ),
            "next_safe_action": (
                "Use Action Inbox owner routes for exact decision receipts."
            ),
        },
        "execution_receipts": {
            "label": "Execution receipts",
            "safe_summary": (
                "Recorded receipts are grouped for accepted AuthorityLease "
                "capabilities and receipt-only decisions."
            ),
            "next_safe_action": (
                "Inspect receipt envelopes and proof refs; do not infer broader execution authority."
            ),
        },
        "memory_proposals_review_decisions": {
            "label": "Memory proposals and review decisions",
            "safe_summary": (
                "Memory proposals and reviewed decisions stay recall and review posture."
            ),
            "next_safe_action": (
                "Inspect Memory Review receipts; broad memory write and context injection remain blocked."
            ),
        },
        "blocked_no_go_events": {
            "label": "Blocked and no-go events",
            "safe_summary": (
                "Blocked states are grouped so missing authority remains visible."
            ),
            "next_safe_action": (
                "Keep the lane blocked until exact approval, receipt, rollback, and verifier coverage exist."
            ),
        },
        "recovery_events": {
            "label": "Recovery and rollback posture",
            "safe_summary": (
                "Rollback, idempotency, replay, and safe-disable refs are inspection posture only."
            ),
            "next_safe_action": (
                "Inspect recovery refs; rollback execution requires a separate scoped lane."
            ),
        },
    }
    return definitions[group_kind]


def _evidence_event_matches_audit_group(
    event: dict[str, Any],
    group_kind: EvidenceAuditGroupKind,
) -> bool:
    event_type = str(event.get("event_type") or "")
    item_kind = str(event.get("item_kind") or "").lower()
    text = " ".join(
        [
            item_kind,
            str(event.get("title") or "").lower(),
            " ".join(str(ref).lower() for ref in event.get("source_refs", [])),
            " ".join(str(ref).lower() for ref in event.get("status_refs", [])),
        ]
    )
    receipt_refs = list(event.get("receipt_refs") or [])
    approval_refs = list(event.get("approval_refs") or [])
    blocked_states = list(event.get("blocked_states") or [])
    if group_kind == "plan_changes":
        return "plan" in text or "proposal" in text
    if group_kind == "approval_waits":
        return bool(approval_refs and not receipt_refs)
    if group_kind == "action_proposals":
        return event_type == "action_envelope_created" or "action" in text
    if group_kind == "execution_receipts":
        return bool(receipt_refs)
    if group_kind == "memory_proposals_review_decisions":
        return event_type == "memory_review_decision_recorded" or "memory" in text
    if group_kind == "blocked_no_go_events":
        return bool(blocked_states) or not receipt_refs
    if group_kind == "recovery_events":
        return bool(
            event.get("rollback_refs")
            or event.get("rollback_blockers")
            or event.get("idempotency_refs")
        )
    return False


def _timeline_item_matches_audit_group(
    item: dict[str, Any],
    group_kind: EvidenceAuditGroupKind,
) -> bool:
    item_kind = str(item.get("item_kind") or "").lower()
    text = " ".join(
        [
            item_kind,
            str(item.get("title") or "").lower(),
            " ".join(str(ref).lower() for ref in item.get("source_refs", [])),
            " ".join(str(ref).lower() for ref in item.get("status_refs", [])),
        ]
    )
    receipt_refs = list(item.get("receipt_refs") or [])
    blocked_states = list(item.get("blocked_states") or [])
    approved = item.get("history_answers", {}).get("approved", {})
    approval_refs = approved.get("refs", []) if isinstance(approved, dict) else []
    if group_kind == "plan_changes":
        return "plan" in text or "proposal" in text
    if group_kind == "approval_waits":
        return bool(approval_refs and not receipt_refs)
    if group_kind == "action_proposals":
        return "action" in text or "envelope" in text
    if group_kind == "execution_receipts":
        return bool(receipt_refs)
    if group_kind == "memory_proposals_review_decisions":
        return "memory" in text
    if group_kind == "blocked_no_go_events":
        return bool(blocked_states) or approved.get("status") == "blocked"
    if group_kind == "recovery_events":
        return bool(
            item.get("rollback_refs")
            or item.get("rollback_blockers")
            or item.get("idempotency_refs")
            or item.get("replay_refs")
            or item.get("safe_disable_refs")
        )
    return False


def _evidence_narrative_status_ref(prefix: str, value: str) -> str:
    safe_value = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    if not safe_value:
        safe_value = "missing"
    return f"{prefix}:{safe_value}"


def _action_decision_safe_summary(decision: str, status: str) -> str:
    if status == "blocked":
        return (
            "Action decision was blocked safely; no action execution, connector "
            "write, shell/subprocess execution, memory write, or provider call occurred."
        )
    return (
        f"Action decision '{decision}' recorded as backend-owned receipt state; "
        "the underlying action was not executed."
    )


def _memory_review_decision_safe_summary(decision: str) -> str:
    if decision == "accept":
        return (
            "Memory candidate was accepted as reviewed recall refs only; no context "
            "injection, connector write, CRM sync, action execution, or production "
            "authority was granted."
        )
    if decision == "correct":
        return (
            "Memory candidate correction was recorded as a safe corrected-summary "
            "ref only; no raw content, context injection, connector write, CRM sync, "
            "or production authority was granted."
        )
    if decision == "defer":
        return (
            "Memory candidate review was deferred as backend-owned receipt state; no "
            "memory write, delete, export, context injection, or production authority "
            "was granted."
        )
    if decision == "merge":
        return (
            "Memory candidate merge posture was recorded with safe merge refs only; "
            "no silent deletion, context injection, connector write, or production "
            "authority was granted."
        )
    if decision == "supersede":
        return (
            "Memory candidate supersede posture was recorded with safe superseded refs "
            "only; no silent deletion, delete execution, or production authority was "
            "granted."
        )
    if decision == "expire":
        return (
            "Memory candidate expiry was recorded with exact governed suppression "
            "refs; context injection, deletion, and production authority remain blocked."
        )
    if decision == "forget_request":
        return (
            "Memory candidate forget request posture was recorded as a receipt only; "
            "delete and export execution remain blocked."
        )
    return (
        "Memory candidate was rejected and preserved as blocked review state so stale "
        "candidate refs do not silently return."
    )


def _promoted_action_title(source_title: str) -> str:
    candidate = f"Action envelope for {source_title}".strip()
    if len(candidate) <= 120:
        return candidate
    return candidate[:117].rstrip() + "..."


def _history_answer(
    key: str,
    answer: str,
    *,
    refs: list[str] | None = None,
    status: str = "present",
) -> FounderLoopEvidenceHistoryAnswer:
    question_by_key = {
        item["key"]: str(item["question"])
        for item in EVIDENCE_HISTORY_GRAMMAR_REQUIRED_QUESTIONS
    }
    return FounderLoopEvidenceHistoryAnswer(
        question=question_by_key[key],
        answer=answer,
        refs=refs or [],
        status=status,
    )


def _history_answers(
    *,
    proposed: FounderLoopEvidenceHistoryAnswer,
    approved: FounderLoopEvidenceHistoryAnswer,
    happened: FounderLoopEvidenceHistoryAnswer,
    changed: FounderLoopEvidenceHistoryAnswer,
    undoable: FounderLoopEvidenceHistoryAnswer,
    stale: FounderLoopEvidenceHistoryAnswer,
    blocked: FounderLoopEvidenceHistoryAnswer,
) -> dict[str, FounderLoopEvidenceHistoryAnswer]:
    return {
        "proposed": proposed,
        "approved": approved,
        "happened": happened,
        "changed": changed,
        "undoable": undoable,
        "stale": stale,
        "blocked": blocked,
    }


def _history_answer_text(
    record: dict[str, Any],
    question_key: str,
    fallback: str,
) -> str:
    answers = record.get("history_answers")
    if not isinstance(answers, dict):
        return fallback
    answer = answers.get(question_key)
    if not isinstance(answer, dict):
        return fallback
    value = str(answer.get("answer") or fallback)
    return value[:320]


def _utc_iso() -> str:
    return utc_now().isoformat()


def _utc_iso_after(*, hours: int = 1) -> str:
    return (utc_now() + timedelta(hours=hours)).isoformat()


def _is_future_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=utc_now().tzinfo)
    return parsed > utc_now()


def _is_expired_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=utc_now().tzinfo)
    return parsed <= utc_now()


def _has_actual_receipt_ref(action: dict[str, Any]) -> bool:
    return any(
        str(ref).startswith("receipt:") for ref in action.get("receipt_refs") or []
    )


def _has_expired_or_stale_marker(action: dict[str, Any]) -> bool:
    status = str(action.get("status") or "").lower()
    stale_state = str(action.get("stale_state") or "").lower()
    expires_at = action.get("expires_at")
    if status in {"expired", "stale", "superseded"}:
        return True
    if (
        isinstance(expires_at, str)
        and expires_at
        and not _is_future_iso_datetime(expires_at)
    ):
        try:
            datetime.fromisoformat(expires_at)
        except ValueError:
            pass
        else:
            return True
    return any(
        marker in stale_state
        for marker in ["expired", "stale", "superseded", "outdated"]
    )


def _has_authority_blocker(action: dict[str, Any]) -> bool:
    state_change_readiness = str(action.get("state_change_readiness") or "").lower()
    blocked_state = str(action.get("blocked_state") or "").lower()
    local_task_blockers = list(action.get("local_task_commit_blocked_reasons") or [])
    if str(action.get("status") or "").lower() == "blocked":
        return True
    if "blocked" in state_change_readiness:
        return True
    if any(marker in blocked_state for marker in ["blocked", "not scoped", "unscoped"]):
        return True
    return any(
        str(ref)
        in {
            "blocked-state:exact-scope-ref-missing",
            "blocked-state:action-envelope-ref-missing",
            "blocked-state:local-task-contract-missing",
            "blocked-state:unsupported-action-kind",
            "blocked-state:backend-owned-approval-not-approved",
        }
        for ref in local_task_blockers
    )


def _has_ready_exact_scope(action: dict[str, Any]) -> bool:
    return all(
        isinstance(action.get(key), str) and bool(action.get(key))
        for key in [
            "action_envelope_ref",
            "action_scope_ref",
            "action_approval_requirement_ref",
            "rollback_ref",
            "safe_disable_ref",
        ]
    )


def _action_inbox_group_projection(action: dict[str, Any]) -> dict[str, Any]:
    group_id, reason = _classify_action_inbox_group(action)
    definition = _action_group_definition(group_id)
    return {
        "action_group_id": group_id,
        "action_group_label": definition["label"],
        "action_group_reason": reason,
        "action_group_available_action": definition["available_action"],
    }


def _classify_action_inbox_group(action: dict[str, Any]) -> tuple[str, str]:
    status = str(action.get("status") or "").lower()
    action_kind = str(action.get("action_kind") or "review_only")
    is_local_task = action_kind == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND

    if (
        action.get("state_change_contract_ref")
        == MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF
    ):
        return (
            "proposal_only_no_execution_path",
            "Memory context-pack handoff created an internal Action proposal receipt only; no execution path is available.",
        )
    if (
        is_local_task
        and status == "approved"
        and action.get("local_task_commit_eligible") is True
    ):
        return (
            "approved_local_task_lane",
            "Exact backend approval is recorded and the typed local-task commit lane is eligible.",
        )
    if (
        status in {"edited", "rejected", "deferred", "receipt_recorded"}
        or action.get("local_task_commit_receipt_ref")
        or (
            _has_actual_receipt_ref(action)
            and not (status == "approved" and is_local_task)
        )
    ):
        return (
            "receipt_recorded",
            "A backend decision, local task, or evidence receipt ref is already recorded.",
        )
    if _has_expired_or_stale_marker(action):
        return (
            "expired_stale",
            "The item has expired, stale, superseded, or outdated state markers.",
        )
    if (
        status in {"review_ready", "proposed"}
        and action.get("approval_required") is True
        and _has_ready_exact_scope(action)
        and "blocked" not in str(action.get("state_change_readiness") or "").lower()
    ):
        return (
            "ready_for_decision",
            "Exact scope and approval posture are present for a backend decision receipt.",
        )
    if action.get("approval_required") is False or not action.get(
        "state_change_contract_ref"
    ):
        return (
            "proposal_only_no_execution_path",
            "This is review or planning posture only; no validated execution path is available.",
        )
    if _has_authority_blocker(action):
        return (
            "blocked_by_authority",
            "The item requires authority, scope, or a capability that is not currently granted.",
        )
    if action_kind == "review_only":
        return (
            "proposal_only_no_execution_path",
            "This is review or planning posture only; no validated execution path is available.",
        )
    return (
        "proposal_only_no_execution_path",
        "No backend-validated execution path is available for this item.",
    )


def _action_group_definition(group_id: str) -> dict[str, Any]:
    for definition in ACTION_INBOX_GROUP_DEFINITIONS:
        if definition["group_id"] == group_id:
            return definition
    return ACTION_INBOX_GROUP_DEFINITIONS[-1]


def _action_group_summaries(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = {group_id: 0 for group_id in ACTION_INBOX_GROUP_ORDER}
    for item in items:
        group_id = str(item.get("action_group_id") or "proposal_only_no_execution_path")
        counts[group_id] = counts.get(group_id, 0) + 1
    return [
        {
            **definition,
            "count": counts[str(definition["group_id"])],
        }
        for definition in ACTION_INBOX_GROUP_DEFINITIONS
    ]


def _priority_refs(
    actions: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for action in actions:
        refs.append(
            f"priority-ref:action:{action['priority']}:{str(action['item_ref']).replace(':', '-')}"
        )
    for item in briefing_items:
        refs.append(
            f"priority-ref:briefing:{item['priority']}:{str(item['briefing_ref']).replace(':', '-')}"
        )
    return refs[:8]


def _blocked_state_refs(
    actions: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
) -> list[str]:
    refs = [
        "blocked-state:no_action_execution_route",
        "blocked-state:no_connector_write_route",
        "blocked-state:no_runtime_model_call_route",
    ]
    for action in actions:
        item_ref = str(action["item_ref"]).replace(":", "-")
        if action.get("blocked_state"):
            refs.append(f"blocked-state:action:{item_ref}:mutation-blocked")
        if action.get("state_change_readiness"):
            refs.append(
                f"blocked-state:action:{str(action['state_change_readiness']).replace('_', '-')}"
            )
    for item in memory_items:
        refs.extend(
            f"blocked-state:memory:{str(value).replace('_', '-')}"
            for value in item.get("blocked_states", [])
        )
    for item in briefing_items:
        refs.extend(
            f"blocked-state:briefing:{str(value).replace('_', '-')}"
            for value in item.get("blocked_states", [])
        )
    return refs[:16]


def _next_safe_actions(
    actions: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for action in actions[:3]:
        items.append(
            {
                "surface": "Actions",
                "source_ref": str(action["item_ref"]),
                "safe_summary": str(action["next_safe_action"]),
            }
        )
    for plan in plans[:2]:
        items.append(
            {
                "surface": "Plans",
                "source_ref": str(plan["plan_ref"]),
                "safe_summary": str(plan["next_step_summary"]),
            }
        )
    for item in memory_items[:2]:
        items.append(
            {
                "surface": "Memory",
                "source_ref": str(item["review_ref"]),
                "safe_summary": str(item["next_safe_action"]),
            }
        )
    for item in briefing_items[:2]:
        items.append(
            {
                "surface": "Today",
                "source_ref": str(item["briefing_ref"]),
                "safe_summary": str(item["next_safe_action"]),
            }
        )
    return items[:8]


def _source_readiness_items(
    *,
    briefing_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    briefing_source_refs = [
        str(item["briefing_ref"]) for item in briefing_items[:3]
    ] or ["briefing-ref:source-readiness:not-yet-seeded"]
    return [
        {
            "source_ref": "source-ref:inbox:readiness-blocked",
            "source_kind": "inbox",
            "status": "blocked",
            "safe_summary": (
                "Inbox source readiness is blocked until a read-only email "
                "metadata contract exists; live email access is not present."
            ),
            "next_safe_action": (
                "Define a read-only email metadata contract before inbox-derived "
                "items enter the daily loop."
            ),
            "source_refs": ["contract-ref:email-read-only-missing"],
            "evidence_refs": ["evidence-ref:source-readiness:inbox"],
            "blocked_state_refs": [
                "blocked-state:no-email-read-authority",
                "blocked-state:no-email-send",
                "blocked-state:no-account-auth",
                "blocked-state:no-background-polling",
            ],
            "authority_boundary": (
                "Readiness display only; no account auth, polling, email send, "
                "archive, label, move, or connector write authority."
            ),
        },
        {
            "source_ref": "source-ref:calendar:not-configured",
            "source_kind": "calendar",
            "status": "not_configured",
            "safe_summary": (
                "Calendar source readiness is not configured; commitments remain "
                "blocked until a read-only metadata contract exists."
            ),
            "next_safe_action": (
                "Define calendar metadata refs and stale-state checks before "
                "calendar-derived commitments enter Today."
            ),
            "source_refs": ["contract-ref:calendar-read-only-missing"],
            "evidence_refs": ["evidence-ref:source-readiness:calendar"],
            "blocked_state_refs": [
                "blocked-state:no-calendar-read-authority",
                "blocked-state:no-calendar-write",
                "blocked-state:no-account-auth",
                "blocked-state:no-background-polling",
            ],
            "authority_boundary": (
                "Calendar state is a readiness label only; no account auth, "
                "event read, event write, invite, or connector runtime authority."
            ),
        },
        {
            "source_ref": "source-ref:tasks:manual-only",
            "source_kind": "tasks",
            "status": "metadata_only",
            "safe_summary": (
                "Tasks are represented by local Plans, Today items, and Action "
                "Inbox safe refs; external task systems are not connected."
            ),
            "next_safe_action": (
                "Review local plan and action refs before drafting any task-like "
                "proposal."
            ),
            "source_refs": ["source-ref:founder-loop:plans-actions"],
            "evidence_refs": ["evidence-ref:source-readiness:tasks"],
            "blocked_state_refs": [
                "blocked-state:no-external-task-write",
                "blocked-state:no-account-sync",
                "blocked-state:no-background-polling",
            ],
            "authority_boundary": (
                "Manual/local task posture only; no external task sync, write, "
                "completion, or connector runtime authority."
            ),
        },
        {
            "source_ref": "source-ref:crm-manual-notes:manual-only",
            "source_kind": "crm_manual_notes",
            "status": "metadata_only",
            "safe_summary": (
                "CRM-lite relationship signals come from reviewed memory, local "
                "follow-up refs, and manual safe summaries."
            ),
            "next_safe_action": (
                "Review memory provenance and evidence refs before turning a "
                "relationship signal into a draft proposal."
            ),
            "source_refs": ["source-ref:memory:reviewed-recall"],
            "evidence_refs": ["evidence-ref:source-readiness:crm-lite"],
            "blocked_state_refs": [
                "blocked-state:no-external-crm-write",
                "blocked-state:no-account-sync",
                "blocked-state:no-automatic-memory-truth",
            ],
            "authority_boundary": (
                "CRM-lite is local reviewed recall only; no CRM sync, external "
                "write, contact mutation, or connector runtime authority."
            ),
        },
        {
            "source_ref": "source-ref:repo:local-status-ready",
            "source_kind": "repo",
            "status": "ready",
            "safe_summary": (
                "Repo and local product health can be shown through route, gate, "
                "storage, and evidence refs already available to the Control Center."
            ),
            "next_safe_action": (
                "Inspect route, storage, and Foundation Gate refs before making "
                "any product or release claim."
            ),
            "source_refs": [
                "status-ref:control-center-route-manifest",
                "status-ref:founder-loop-storage",
            ],
            "evidence_refs": ["evidence-ref:source-readiness:repo"],
            "blocked_state_refs": [
                "blocked-state:no-unrestricted-shell",
                "blocked-state:no-automatic-patch-apply",
                "blocked-state:no-production-authority",
            ],
            "authority_boundary": (
                "Local inspection refs are visible; unrestricted shell execution, "
                "auto-apply, and production authority remain blocked."
            ),
        },
        {
            "source_ref": "source-ref:local-files:metadata-only",
            "source_kind": "local_files",
            "status": "metadata_only",
            "safe_summary": (
                "Local-file signals may be represented by safe refs and bounded "
                "summaries only; private filesystem identifiers and file bodies "
                "stay omitted."
            ),
            "next_safe_action": (
                "Use safe refs and redacted summaries before showing local-file "
                "derived work in the daily loop."
            ),
            "source_refs": briefing_source_refs,
            "evidence_refs": ["evidence-ref:source-readiness:local-files"],
            "blocked_state_refs": [
                "blocked-state:no-private-filesystem-identifiers",
                "blocked-state:no-file-body-ingestion",
                "blocked-state:no-connector-runtime",
            ],
            "authority_boundary": (
                "Metadata-only local posture; no file body ingestion, private "
                "identifier display, background watch, or connector write authority."
            ),
        },
    ]


def _source_readiness_posture(
    source_readiness_items: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_contract_refs = _unique_sorted_refs(
        ref
        for item in source_readiness_items
        for ref in item.get("source_refs", [])
        if str(ref).startswith("contract-ref:")
    )
    blocked_state_refs = _unique_sorted_refs(
        ref
        for item in source_readiness_items
        for ref in item.get("blocked_state_refs", [])
    )
    posture = {
        "schema_version": "founder_loop_source_readiness_posture.v1",
        "source": "python_core_source_readiness_read_model",
        "backend_owned": True,
        "status": "read_only_posture_missing_external_source_contracts",
        "source_count": len(source_readiness_items),
        "ready_source_count": sum(
            1 for item in source_readiness_items if item.get("status") == "ready"
        ),
        "blocked_source_count": sum(
            1 for item in source_readiness_items if item.get("status") == "blocked"
        ),
        "metadata_only_source_count": sum(
            1
            for item in source_readiness_items
            if item.get("status") == "metadata_only"
        ),
        "not_configured_source_count": sum(
            1
            for item in source_readiness_items
            if item.get("status") == "not_configured"
        ),
        "supported_statuses": [
            "ready",
            "blocked",
            "missing",
            "metadata_only",
            "unavailable",
            "not_configured",
        ],
        "missing_contract_refs": missing_contract_refs,
        "blocked_state_refs": blocked_state_refs,
        "blocked_authority_refs": blocked_state_refs,
        "connector_runtime_enabled": False,
        "source_refresh_enabled": False,
        "notification_delivery_enabled": False,
        "account_auth_enabled": False,
        "raw_source_ingestion_enabled": False,
        "write_authority_enabled": False,
        "authority_boundary": (
            "Source readiness is a read-only posture summary. It does not grant "
            "email, calendar, connector, polling, refresh, notification, or "
            "delivery authority."
        ),
        "next_safe_action": (
            "Review missing source contracts and keep source reads, refresh, "
            "notifications, and connector runtime blocked."
        ),
    }
    _validate_safe_payload(posture, "source_readiness_posture")
    return posture


def _source_readiness_read_model(
    *,
    briefing_items: list[dict[str, Any]],
) -> dict[str, Any]:
    source_readiness_items = _source_readiness_items(briefing_items=briefing_items)
    source_readiness_posture = _source_readiness_posture(source_readiness_items)
    read_only_metadata_contracts = _source_readiness_metadata_contracts()
    connector_draft_proposals = (
        build_connector_draft_proposal_read_model().storage_record()
    )
    blocked_authority_refs = _unique_sorted_refs(
        [
            *source_readiness_posture["blocked_authority_refs"],
            *connector_draft_proposals["blocked_authority_refs"],
            "blocked-state:no-account-auth",
            "blocked-state:no-background-polling",
            "blocked-state:no-connector-runtime",
            "blocked-state:no-connector-write",
            "blocked-state:no-email-send",
            "blocked-state:no-calendar-write",
            "blocked-state:no-raw-source-ingestion",
            "blocked-state:no-source-refresh",
            "blocked-state:no-notification-delivery",
        ]
    )
    evidence_refs = _unique_sorted_refs(
        [
            *[
                ref
                for item in source_readiness_items
                for ref in item.get("evidence_refs", [])
            ],
            *[
                ref
                for contract in read_only_metadata_contracts
                for ref in contract.get("evidence_refs", [])
            ],
        ]
    )
    proposal_candidates = _source_readiness_proposal_candidates(
        source_readiness_items=source_readiness_items,
        source_readiness_posture=source_readiness_posture,
        blocked_authority_refs=blocked_authority_refs,
        evidence_refs=evidence_refs,
    )
    route_refs = [
        "GET /control-center/sources/readiness",
        "GET /control-center/sources/readiness#read_only_metadata_contracts",
        "GET /control-center/today/summary",
        "GET /control-center/morning-briefing/summary",
    ]
    read_model = {
        "schema_version": "founder_loop_source_readiness.v1",
        "source": "python_core_source_readiness_read_model",
        "backend_owned": True,
        "generated_at": _utc_iso(),
        "status": "read_only_source_readiness_missing_external_contracts",
        "surface": "Sources",
        "route_ref": "/control-center/sources/readiness",
        "route_refs": route_refs,
        "source_readiness_items": source_readiness_items,
        "source_readiness_posture": source_readiness_posture,
        "source_readiness_proposal_candidates": proposal_candidates,
        "read_only_metadata_contracts": read_only_metadata_contracts,
        "read_only_metadata_contract_count": len(read_only_metadata_contracts),
        "connector_draft_proposals": connector_draft_proposals,
        "supported_statuses": source_readiness_posture["supported_statuses"],
        "missing_contract_refs": source_readiness_posture["missing_contract_refs"],
        "blocked_state_refs": source_readiness_posture["blocked_state_refs"],
        "blocked_authority_refs": blocked_authority_refs,
        "evidence_refs": evidence_refs,
        "connector_runtime_enabled": False,
        "source_refresh_enabled": False,
        "notification_delivery_enabled": False,
        "account_auth_enabled": False,
        "raw_source_ingestion_enabled": False,
        "write_authority_enabled": False,
        "connector_draft_proposals_enabled": True,
        "authority_boundary": (
            "Dedicated Source Readiness is a read-only local read model. It does "
            "not authenticate accounts, poll connectors, ingest raw source bodies, "
            "send or write external data, refresh sources, deliver notifications, "
            "or grant production authority. Connector draft proposals are "
            "safe-ref review artifacts only and cannot send or write."
        ),
        "next_safe_action": (
            "Use the dedicated read-only source readiness route to inspect missing "
            "source contracts and review connector draft proposal refs before any "
            "future connector metadata or send/write lane."
        ),
    }
    _validate_safe_payload(read_model, "source_readiness_read_model")
    return read_model


def _source_readiness_metadata_contracts() -> list[dict[str, Any]]:
    pair = build_fcc_read_only_integration_contract_pair()
    contracts = [
        _source_readiness_calendar_metadata_contract(pair.calendar),
        _source_readiness_email_metadata_contract(pair.email),
    ]
    for contract in contracts:
        _validate_safe_payload(contract, "source_readiness_metadata_contract")
    return contracts


def _source_readiness_calendar_metadata_contract(record: Any) -> dict[str, Any]:
    return {
        "schema_version": "founder_loop_read_only_metadata_contract.v1",
        "source": "python_core_source_readiness_read_model",
        "backend_owned": True,
        "source_kind": "calendar",
        "contract_ref": str(record.calendar_contract_ref),
        "product_loop_ref": str(record.product_loop_ref),
        "status": _enum_value(record.status),
        "route_ref": (
            "GET /control-center/sources/readiness#read_only_metadata_contracts"
        ),
        "safe_summary": str(record.redacted_meeting_prep_summary),
        "metadata_refs": [
            str(record.event_ref),
            str(record.time_window_ref),
            str(record.account_identity_ref),
            str(record.meeting_prep_summary_ref),
            *[str(ref) for ref in record.attendee_identity_refs],
        ],
        "source_readiness_refs": [str(ref) for ref in record.source_readiness_refs],
        "evidence_refs": [str(ref) for ref in record.evidence_refs],
        "audit_ref": str(record.audit_ref),
        "replay_ref": str(record.replay_ref),
        "missing_runtime_ref": str(record.missing_runtime_ref),
        "blocked_runtime_refs": [str(ref) for ref in record.blocked_runtime_refs],
        "reason_codes": [str(code) for code in record.reason_codes],
        "contract_only": bool(record.contract_only),
        "read_only": bool(record.read_only),
        "metadata_only": bool(record.metadata_only),
        "safe_refs_only": bool(record.safe_refs_required),
        "connector_runtime_missing": bool(record.connector_runtime_missing),
        "account_auth_enabled": bool(record.account_auth_enabled),
        "runtime_read_enabled": bool(record.calendar_read_runtime_enabled),
        "runtime_search_enabled": bool(record.calendar_search_runtime_enabled),
        "raw_content_enabled": bool(
            record.event_title_body_storage_enabled or record.raw_invite_body_enabled
        ),
        "write_enabled": bool(
            record.event_create_enabled
            or record.event_update_enabled
            or record.event_delete_enabled
            or record.invite_send_enabled
        ),
        "background_collection_enabled": bool(record.background_collection_enabled),
        "connector_runtime_enabled": bool(record.connector_runtime_enabled),
        "model_call_enabled": bool(record.model_call_enabled),
        "memory_write_enabled": bool(record.memory_write_enabled),
        "context_injection_enabled": bool(record.context_injection_enabled),
        "production_authority_enabled": bool(record.production_authority_enabled),
        "next_safe_action": (
            "Use this calendar metadata contract as source-readiness evidence only; "
            "live calendar fetch, writes, invite sends, and account auth remain blocked."
        ),
        "authority_boundary": (
            "Calendar metadata contracts expose safe refs and redacted summaries "
            "only. They do not authorize account auth, runtime fetch, event body "
            "storage, calendar writes, invite sends, connector runtime, or "
            "production authority."
        ),
    }


def _source_readiness_email_metadata_contract(record: Any) -> dict[str, Any]:
    return {
        "schema_version": "founder_loop_read_only_metadata_contract.v1",
        "source": "python_core_source_readiness_read_model",
        "backend_owned": True,
        "source_kind": "email",
        "contract_ref": str(record.email_contract_ref),
        "product_loop_ref": str(record.product_loop_ref),
        "status": _enum_value(record.status),
        "route_ref": (
            "GET /control-center/sources/readiness#read_only_metadata_contracts"
        ),
        "safe_summary": str(record.redacted_inbox_summary),
        "metadata_refs": [
            str(record.sender_summary_ref),
            str(record.thread_ref),
            str(record.time_window_ref),
            str(record.inbox_summary_ref),
            str(record.follow_up_summary_ref),
            *[str(ref) for ref in record.label_summary_refs],
        ],
        "source_readiness_refs": [str(ref) for ref in record.source_readiness_refs],
        "evidence_refs": [str(ref) for ref in record.evidence_refs],
        "audit_ref": str(record.audit_ref),
        "replay_ref": str(record.replay_ref),
        "missing_runtime_ref": str(record.missing_runtime_ref),
        "blocked_runtime_refs": [str(ref) for ref in record.blocked_runtime_refs],
        "reason_codes": [str(code) for code in record.reason_codes],
        "contract_only": bool(record.contract_only),
        "read_only": bool(record.read_only),
        "metadata_only": bool(record.metadata_only),
        "safe_refs_only": bool(record.safe_refs_required),
        "connector_runtime_missing": bool(record.connector_runtime_missing),
        "account_auth_enabled": bool(record.account_auth_enabled),
        "runtime_read_enabled": bool(record.email_fetch_runtime_enabled),
        "runtime_search_enabled": bool(record.email_search_runtime_enabled),
        "raw_content_enabled": bool(
            record.raw_body_enabled
            or record.subject_text_enabled
            or record.participant_identifiers_enabled
            or record.attachment_names_enabled
        ),
        "write_enabled": bool(
            record.send_enabled
            or record.delete_enabled
            or record.archive_enabled
            or record.label_write_enabled
        ),
        "background_collection_enabled": False,
        "connector_runtime_enabled": bool(record.connector_runtime_enabled),
        "model_call_enabled": bool(record.model_call_enabled),
        "memory_write_enabled": bool(record.memory_write_enabled),
        "context_injection_enabled": bool(record.context_injection_enabled),
        "production_authority_enabled": bool(record.production_authority_enabled),
        "next_safe_action": (
            "Use this email metadata contract as source-readiness evidence only; "
            "live inbox fetch, sends, archive/delete/label moves, and account auth "
            "remain blocked."
        ),
        "authority_boundary": (
            "Email metadata contracts expose safe refs and redacted summaries only. "
            "They do not authorize account auth, runtime fetch, message body or "
            "participant display, sends, archive/delete/label/move writes, connector "
            "runtime, or production authority."
        ),
    }


def _source_readiness_proposal_candidates(
    *,
    source_readiness_items: list[dict[str, Any]],
    source_readiness_posture: dict[str, Any],
    blocked_authority_refs: list[str],
    evidence_refs: list[str],
) -> list[dict[str, Any]]:
    items_by_kind = {
        str(item.get("source_kind")): item for item in source_readiness_items
    }
    missing_contract_refs = set(
        source_readiness_posture.get("missing_contract_refs", [])
    )
    blocked_ref_set = set(blocked_authority_refs)
    candidate_specs = [
        {
            "slug": "email-read-only-metadata-contract",
            "title": "Define email read-only metadata contract",
            "source_kind": "email",
            "missing_contract_ref": "contract-ref:email-read-only-missing",
            "proposal_kind": "proposal-kind:read-only-email-metadata-contract",
            "trigger_ref": "contract-ref:email-read-only-missing",
            "safe_summary": (
                "Email source readiness is blocked until a safe read-only "
                "metadata contract exists; no account auth, source-body access, "
                "polling, send, archive, label, move, or connector write is available."
            ),
            "next_safe_action": (
                "Draft the email metadata contract with safe refs, configured posture, "
                "blocked authority refs, and no source body ingestion."
            ),
        },
        {
            "slug": "calendar-read-only-metadata-contract",
            "title": "Define calendar read-only metadata contract",
            "source_kind": "calendar",
            "missing_contract_ref": "contract-ref:calendar-read-only-missing",
            "proposal_kind": "proposal-kind:read-only-calendar-metadata-contract",
            "trigger_ref": "contract-ref:calendar-read-only-missing",
            "safe_summary": (
                "Calendar source readiness is blocked until a safe read-only "
                "metadata contract exists; no account auth, event body access, "
                "polling, create, update, delete, or connector write is available."
            ),
            "next_safe_action": (
                "Draft the calendar metadata contract with safe refs, configured "
                "posture, blocked authority refs, and no event body ingestion."
            ),
        },
        {
            "slug": "account-auth-boundary",
            "title": "Resolve missing account-auth boundary",
            "source_kind": "inbox",
            "missing_contract_ref": "contract-ref:source-account-auth-boundary-missing",
            "proposal_kind": "proposal-kind:source-account-auth-boundary",
            "trigger_ref": "blocked-state:no-account-auth",
            "safe_summary": (
                "Source readiness needs an explicit account-auth boundary before "
                "any future connector sign-in posture can be designed; no account "
                "connection flow is enabled."
            ),
            "next_safe_action": (
                "Draft the account-auth boundary as proposal text with safe refs "
                "and blocked runtime authority."
            ),
        },
    ]
    proposals: list[dict[str, Any]] = []
    for spec in candidate_specs:
        trigger_ref = str(spec["trigger_ref"])
        if (
            trigger_ref not in missing_contract_refs
            and trigger_ref not in blocked_ref_set
        ):
            continue
        source_item = items_by_kind.get(str(spec["source_kind"])) or (
            source_readiness_items[0] if source_readiness_items else {}
        )
        slug = str(spec["slug"])
        proposal_ref = f"source-readiness-proposal:{slug}"
        action_item_ref = f"action:source-readiness:{slug}"
        proposal_evidence_refs = _unique_sorted_refs(
            [
                f"evidence-ref:source-readiness-proposal:{slug}",
                "evidence-ref:founder-loop:source-readiness",
                *list(source_item.get("evidence_refs") or []),
                *evidence_refs,
            ]
        )
        proposal = {
            "schema_version": "founder_loop_source_readiness_proposal.v1",
            "source": "python_core_source_readiness_read_model",
            "backend_owned": True,
            "proposal_ref": proposal_ref,
            "action_item_ref": action_item_ref,
            "title": str(spec["title"]),
            "safe_summary": str(spec["safe_summary"]),
            "surface": "Sources",
            "source_kind": str(spec["source_kind"]),
            "source_readiness_ref": str(
                source_item.get("source_ref") or "source-readiness:missing"
            ),
            "source_readiness_route_ref": "/control-center/sources/readiness",
            "missing_contract_ref": str(spec["missing_contract_ref"]),
            "proposal_kind": str(spec["proposal_kind"]),
            "proposal_classification": "proposal_only_no_execution_path",
            "action_kind": SOURCE_READINESS_PROPOSAL_ACTION_KIND,
            "status": "proposal_only",
            "side_effect_class": "local_dev_workspace_only",
            "risk_class": "low",
            "approval_required": False,
            "local_task_commit_eligible": False,
            "connector_runtime_enabled": False,
            "account_auth_enabled": False,
            "source_refresh_enabled": False,
            "raw_source_ingestion_enabled": False,
            "write_authority_enabled": False,
            "blocked_authority_refs": _unique_sorted_refs(
                [
                    *blocked_authority_refs,
                    *list(source_item.get("blocked_state_refs") or []),
                    "blocked-state:no-account-auth",
                    "blocked-state:no-background-polling",
                    "blocked-state:no-connector-runtime",
                    "blocked-state:no-connector-write",
                    "blocked-state:no-raw-source-ingestion",
                    "blocked-state:no-source-refresh",
                ]
            ),
            "evidence_refs": proposal_evidence_refs,
            "next_safe_action": str(spec["next_safe_action"]),
            "authority_boundary": (
                "Source readiness proposal candidates are read-only review "
                "metadata. They do not grant connector runtime, account auth, "
                "source ingestion, polling, writes, execution, or production authority."
            ),
        }
        _validate_safe_payload(proposal, "source_readiness_proposal_candidate")
        proposals.append(proposal)
    return proposals


def _source_readiness_action_items(
    proposal_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for proposal in proposal_candidates:
        slug = _safe_suffix(str(proposal["proposal_ref"]))
        blocked_refs = list(proposal.get("blocked_authority_refs") or [])
        evidence_refs = list(proposal.get("evidence_refs") or [])
        action_record = FounderLoopActionRecord(
            item_ref=str(proposal["action_item_ref"]),
            title=str(proposal["title"]),
            safe_summary=str(proposal["safe_summary"]),
            surface="Sources",
            priority="medium",
            risk_class=str(proposal["risk_class"]),
            action_kind=SOURCE_READINESS_PROPOSAL_ACTION_KIND,
            status="proposed",
            side_effect_class="local_dev_workspace_only",
            authority_boundary=str(proposal["authority_boundary"]),
            approval_required=False,
            approval_envelope_ref=f"approval-envelope:source-readiness:{slug}",
            approval_envelope_status="not_required_proposal_only",
            state_change_contract_ref=SOURCE_READINESS_PROPOSAL_BINDING_CONTRACT_REF,
            state_change_readiness="draft_only_proposal_no_execution_path",
            blocked_state=(
                "Connector runtime, account auth, source ingestion, polling, "
                "writes, and execution remain blocked."
            ),
            evidence_refs=evidence_refs,
            receipt_refs=[],
            audit_refs=[],
            idempotency_key_ref=None,
            expires_at=None,
            stale_state="recheck_source_readiness_before_contract_work",
            rollback_ref=None,
            safe_disable_ref=None,
            next_safe_action=str(proposal["next_safe_action"]),
        ).model_dump(mode="json")
        action_record.update(
            {
                "source_readiness_proposal_ref": proposal["proposal_ref"],
                "source_readiness_proposal_kind": proposal["proposal_kind"],
                "source_readiness_missing_contract_ref": proposal[
                    "missing_contract_ref"
                ],
                "source_readiness_ref": proposal["source_readiness_ref"],
                "source_readiness_route_ref": proposal["source_readiness_route_ref"],
                "source_readiness_blocked_authority_refs": blocked_refs,
                "source_readiness_backend_owned": proposal["backend_owned"],
                "source_readiness_proposal_classification": proposal[
                    "proposal_classification"
                ],
            }
        )
        _validate_safe_payload(action_record, "source_readiness_action_item")
        actions.append(action_record)
    return actions


def _health_recommendation_action_items(
    recommendation_candidates: list[Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for recommendation_candidate in recommendation_candidates:
        recommendation = (
            recommendation_candidate.model_dump(mode="json")
            if hasattr(recommendation_candidate, "model_dump")
            else dict(recommendation_candidate)
        )
        slug = _safe_suffix(str(recommendation["recommendation_ref"]))
        blocked_refs = list(recommendation.get("blocked_authority_refs") or [])
        evidence_refs = list(recommendation.get("evidence_refs") or [])
        severity = str(recommendation.get("severity") or "medium")
        priority = "high" if severity == "high" else "medium"
        if severity in {"info", "low"}:
            priority = "low"
        risk_class = "low" if severity == "info" else severity
        action_record = FounderLoopActionRecord(
            item_ref=f"action-item:fcc-health-001:{slug}",
            title=str(recommendation["safe_title"]),
            safe_summary=str(recommendation["safe_summary"]),
            surface="Actions",
            priority=priority,
            risk_class=risk_class,
            action_kind=FCC_HEALTH_RECOMMENDATION_ACTION_KIND,
            status="proposed",
            side_effect_class="local_dev_workspace_only",
            authority_boundary=(
                "Recommendation review material only; no execution, auto-apply, "
                "model/provider call, shell use, connector write, or production authority."
            ),
            approval_required=False,
            approval_envelope_ref=f"approval-envelope:fcc-health-001:{slug}",
            approval_envelope_status="not_required_recommendation_review_only",
            state_change_contract_ref=FCC_HEALTH_RECOMMENDATION_BINDING_CONTRACT_REF,
            state_change_readiness="recommendation_review_only_no_execution_path",
            blocked_state=(
                "Auto-code, auto-apply, background self-repair, scheduler, "
                "model/provider, shell, connector, and action execution remain blocked."
            ),
            evidence_refs=evidence_refs,
            receipt_refs=[],
            audit_refs=[],
            idempotency_key_ref=None,
            expires_at=None,
            stale_state="recheck_recommendation_refs_before_conversion",
            rollback_ref=None,
            safe_disable_ref=None,
            next_safe_action=str(recommendation["next_safe_action"]),
        ).model_dump(mode="json")
        action_record.update(
            {
                "health_recommendation_ref": recommendation["recommendation_ref"],
                "health_recommendation_kind": recommendation["kind"],
                "health_recommendation_severity": recommendation["severity"],
                "health_recommendation_lifecycle_state": recommendation[
                    "lifecycle_state"
                ],
                "health_recommendation_missing_proof_refs": recommendation[
                    "missing_proof_refs"
                ],
                "health_recommendation_validation_plan_refs": recommendation[
                    "validation_plan_refs"
                ],
                "health_recommendation_expected_receipt_refs": recommendation[
                    "expected_receipt_refs"
                ],
                "health_recommendation_conversion_option_refs": recommendation[
                    "conversion_option_refs"
                ],
                "health_recommendation_blocked_authority_refs": blocked_refs,
                "health_recommendation_source_signal_refs": recommendation[
                    "source_signal_refs"
                ],
                "health_recommendation_source_surface_refs": recommendation[
                    "source_surface_refs"
                ],
                "health_recommendation_source_route_refs": recommendation[
                    "source_route_refs"
                ],
                "health_recommendation_source_doc_refs": recommendation[
                    "source_doc_refs"
                ],
                "health_recommendation_source_test_refs": recommendation[
                    "source_test_refs"
                ],
                "health_recommendation_source_verifier_refs": recommendation[
                    "source_verifier_refs"
                ],
                "health_recommendation_rollback_or_safe_disable_refs": recommendation[
                    "rollback_or_safe_disable_refs"
                ],
                "health_recommendation_auto_apply_authorized": False,
                "health_recommendation_auto_code_authorized": False,
                "health_recommendation_provider_model_call_authorized": False,
                "health_recommendation_shell_execution_authorized": False,
                "health_recommendation_connector_write_authorized": False,
                "health_recommendation_memory_write_authorized": False,
                "health_recommendation_context_injection_authorized": False,
                "health_recommendation_action_execution_authorized": False,
                "health_recommendation_production_authority_enabled": False,
            }
        )
        _validate_safe_payload(action_record, "health_recommendation_action_item")
        actions.append(action_record)
    return actions


def _action_inbox_review_filter_facets(
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def build_facet(
        facet_id: str,
        label: str,
        values: list[str],
    ) -> dict[str, Any]:
        counts = {value: values.count(value) for value in sorted(set(values))}
        return {
            "facet_id": facet_id,
            "label": label,
            "backend_owned": True,
            "options": [
                {
                    "option_ref": _status_ref(f"action-filter-{facet_id}", value),
                    "label": value,
                    "count": count,
                }
                for value, count in counts.items()
            ],
        }

    def receipt_state(action: dict[str, Any]) -> str:
        visibility = action.get("receipt_visibility") or {}
        local_task_receipt = str(visibility.get("local_task_commit_receipt_ref") or "")
        decision_receipt = str(visibility.get("decision_receipt_ref") or "")
        if local_task_receipt.startswith("receipt:founder-loop-local-task:"):
            return "local_task_receipt_recorded"
        if decision_receipt.startswith("receipt:founder-loop-action:"):
            return "decision_receipt_recorded"
        if local_task_receipt == "pending" or decision_receipt == "pending":
            return "receipt_pending"
        return "receipt_not_applicable"

    facets = [
        build_facet("status", "Status", [str(item["status"]) for item in actions]),
        build_facet(
            "action_kind",
            "Action kind",
            [str(item.get("action_kind", "review_only")) for item in actions],
        ),
        build_facet(
            "risk",
            "Risk",
            [str(item.get("risk_class", "medium")) for item in actions],
        ),
        build_facet(
            "authority_requirement",
            "Authority requirement",
            [
                "approval_required"
                if bool(item.get("approval_required"))
                else "approval_not_required"
                for item in actions
            ],
        ),
        build_facet(
            "receipt_state",
            "Receipt state",
            [receipt_state(item) for item in actions],
        ),
        build_facet(
            "source_surface",
            "Source surface",
            [str(item["surface"]) for item in actions],
        ),
    ]
    _validate_safe_payload(facets, "action_inbox_review_filter_facets")
    return facets


def _crm_lite_followups(
    *,
    memory_to_loop_binding_contract: dict[str, Any],
    memory_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    follow_up_refs = [
        str(ref)
        for ref in memory_to_loop_binding_contract.get(
            "follow_up_commitment_refs",
            [],
        )
    ]
    if not follow_up_refs and memory_items:
        follow_up_refs = [
            f"follow-up-commitment-ref:{str(memory_items[0]['review_ref']).replace(':', '-')}"
        ]
    if not follow_up_refs:
        return []

    memory_refs = [
        str(ref)
        for ref in memory_to_loop_binding_contract.get("memory_candidate_refs", [])
    ]
    memory_refs.extend(str(item["review_ref"]) for item in memory_items[:2])
    source_refs = list(memory_items[0].get("source_refs", [])) if memory_items else []
    evidence_refs = (
        list(memory_items[0].get("evidence_refs", [])) if memory_items else []
    ) or ["evidence-ref:crm-lite:reviewed-memory"]
    proposal_refs = [
        str(proposal["proposal_ref"])
        for proposal in memory_to_loop_binding_contract.get(
            "memory_derived_action_proposals",
            [],
        )
    ]
    items: list[dict[str, Any]] = []
    for index, follow_up_ref in enumerate(follow_up_refs[:3], start=1):
        followup = build_crm_lite_relationship_followup(
            follow_up_ref=follow_up_ref,
            relationship_ref=f"crm-lite-relationship-ref:{index}",
            person_ref=f"crm-lite-person-ref:{index}",
            org_ref=f"crm-lite-org-ref:{index}",
            project_ref=f"crm-lite-project-ref:{index}",
            opportunity_ref=f"crm-lite-opportunity-ref:{index}",
            promise_ref=f"crm-lite-promise-ref:{index}",
            safe_summary=(
                "A local relationship follow-up is visible because reviewed "
                "memory produced a follow-up commitment ref."
            ),
            why_now=(
                "This appears because memory-to-loop binding marked a "
                "follow-up commitment that can be reviewed in the daily loop."
            ),
            draft_available=bool(proposal_refs),
            review_envelope_ref=f"review-envelope-ref:crm-lite-follow-up:{index}",
            memory_refs=memory_refs[:5],
            source_refs=source_refs[:5],
            evidence_refs=evidence_refs[:5],
            next_safe_action=(
                "Review the memory, source, and evidence refs before drafting "
                "a local follow-up proposal."
            ),
            blocked_state_refs=[
                "blocked-state:crm-lite-no-external-crm-sync",
                "blocked-state:crm-lite-no-external-crm-write",
                "blocked-state:crm-lite-no-account-sync",
                "blocked-state:crm-lite-no-connector-read",
                "blocked-state:crm-lite-no-connector-write",
                "blocked-state:crm-lite-no-email-calendar-fetch",
                "blocked-state:crm-lite-no-hidden-context-injection",
                "blocked-state:crm-lite-no-hidden-memory-write",
                "blocked-state:crm-lite-no-action-execution",
                "blocked-state:crm-lite-no-model-provider-call",
                "blocked-state:crm-lite-no-production-authority",
                "blocked-state:no-external-crm-write",
                "blocked-state:no-account-sync",
                "blocked-state:no-connector-write",
                "blocked-state:no-action-execution",
            ],
            authority_boundary=(
                "CRM-lite follow-ups are reviewed local recall only; no CRM "
                "sync, connector read/write, email or calendar fetch, hidden "
                "context injection, hidden memory write, or action execution."
            ),
        )
        items.append(followup.model_dump())
    return items


def _memory_why_shown_items(
    *,
    memory_to_loop_binding_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for loop_item in memory_to_loop_binding_contract.get("memory_to_loop_items", [])[
        :6
    ]:
        surface = str(loop_item["surface"])
        items.append(
            {
                "memory_ref": str(loop_item["memory_candidate_ref"]),
                "loop_item_ref": str(loop_item["loop_item_ref"]),
                "surface": surface,
                "why_shown": (
                    f"{surface} shows this memory because it is a reviewed recall "
                    "candidate tied to daily-loop source and evidence refs."
                ),
                "review_state": str(loop_item["loop_binding_state"]),
                "stale_state": str(loop_item["stale_state"]),
                "conflict_state": "conflict_unknown_review_required",
                "source_refs": list(loop_item.get("source_refs", [])),
                "evidence_refs": list(loop_item.get("evidence_refs", [])),
                "missing_evidence_refs": list(
                    loop_item.get("missing_evidence_refs", [])
                ),
                "next_safe_action": str(loop_item["next_safe_action"]),
                "authority_boundary": (
                    "Memory is reviewed recall only; it is not truth, hidden "
                    "context, approval, connector authority, or execution."
                ),
                "reviewed_recall_only": True,
                "context_injection_authorized": False,
                "memory_truth_authority": False,
            }
        )
    return items


def _review_queue_groups(
    *,
    actions: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    memory_to_loop_binding_contract: dict[str, Any],
    private_beta_readiness_gate_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    proposal_refs = [
        str(proposal["proposal_ref"])
        for proposal in memory_to_loop_binding_contract.get(
            "memory_derived_action_proposals",
            [],
        )
    ]
    follow_up_refs = [
        str(ref)
        for ref in memory_to_loop_binding_contract.get(
            "follow_up_commitment_refs",
            [],
        )
    ]
    return [
        {
            "group_ref": "review-group:action-proposals",
            "kind": "actions",
            "count": len(actions),
            "status": "review_ready" if actions else "empty",
            "safe_summary": (
                "Action Inbox items can be approved, edited, rejected, or deferred "
                "only where receipt routes already support decisions."
            ),
            "source_refs": [str(action["item_ref"]) for action in actions[:5]],
            "evidence_refs": ["evidence-ref:review-group:actions"],
            "next_safe_action": "Review exact scope and receipts before any later action lane.",
            "blocked_state_refs": [
                "blocked-state:no-action-execution",
                "blocked-state:approval-ref-is-identifier-only",
            ],
        },
        {
            "group_ref": "review-group:memory-candidates",
            "kind": "memory",
            "count": len(memory_items),
            "status": "review_ready" if memory_items else "empty",
            "safe_summary": (
                "Memory candidates can be reviewed as recall posture only; they do "
                "not become truth or hidden context."
            ),
            "source_refs": [str(item["review_ref"]) for item in memory_items[:5]],
            "evidence_refs": ["evidence-ref:review-group:memory"],
            "next_safe_action": "Review provenance, stale state, and conflicts before recall use.",
            "blocked_state_refs": [
                "blocked-state:no-memory-write",
                "blocked-state:no-context-injection",
                "blocked-state:no-automatic-memory-truth",
            ],
        },
        {
            "group_ref": "review-group:draft-opportunities",
            "kind": "drafts",
            "count": len(proposal_refs),
            "status": "draft_only" if proposal_refs else "empty",
            "safe_summary": (
                "Draft opportunities are reviewable proposal refs only; no send, "
                "write, or external mutation is available."
            ),
            "source_refs": proposal_refs[:5],
            "evidence_refs": ["evidence-ref:review-group:drafts"],
            "next_safe_action": "Review proposal refs before any later exact-scope local action.",
            "blocked_state_refs": [
                "blocked-state:no-email-send",
                "blocked-state:no-connector-write",
                "blocked-state:no-action-execution",
            ],
        },
        {
            "group_ref": "review-group:crm-follow-ups",
            "kind": "crm_followups",
            "count": len(follow_up_refs),
            "status": "review_only" if follow_up_refs else "empty",
            "safe_summary": (
                "CRM-lite follow-ups are local relationship refs derived from "
                "reviewed memory, not external CRM state."
            ),
            "source_refs": follow_up_refs[:5],
            "evidence_refs": ["evidence-ref:review-group:crm-lite"],
            "next_safe_action": "Review source and memory refs before drafting a follow-up.",
            "blocked_state_refs": [
                "blocked-state:no-external-crm-write",
                "blocked-state:no-account-sync",
            ],
        },
        {
            "group_ref": "review-group:system-health",
            "kind": "system_health",
            "count": int(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_criterion_count"
                ]
            ),
            "status": str(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_overall_state"
                ]
            ),
            "safe_summary": (
                "System and product health are readiness refs for private use; "
                "they do not confer release authority."
            ),
            "source_refs": [
                str(
                    private_beta_readiness_gate_contract[
                        "private_beta_readiness_contract_ref"
                    ]
                )
            ],
            "evidence_refs": [
                str(
                    private_beta_readiness_gate_contract[
                        "private_beta_readiness_evidence_packet_ref"
                    ]
                )
            ],
            "next_safe_action": str(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_next_safe_action"
                ]
            ),
            "blocked_state_refs": list(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_blocked_state_refs"
                ]
            ),
        },
        {
            "group_ref": "review-group:patch-proposals",
            "kind": "patch_proposals",
            "count": 1,
            "status": "review_only_apply_blocked",
            "safe_summary": (
                "Patch proposals can be inspected as safe summaries; no "
                "self-healing or auto-apply authority is available."
            ),
            "source_refs": ["proposal-ref:governed-code-workbench:safe-diff"],
            "evidence_refs": ["evidence-ref:review-group:patch-proposals"],
            "next_safe_action": "Review validation refs before any separately scoped code change.",
            "blocked_state_refs": [
                "blocked-state:no-automatic-patch-apply",
                "blocked-state:no-unrestricted-shell",
                "blocked-state:no-self-healing-execution",
            ],
        },
    ]


def _dogfood_capture_summary(
    *,
    actions: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
    private_beta_readiness_gate_contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        "capture_ref": "dogfood-capture-ref:founder-loop:private-local",
        "status": "private_dogfood_capture_ready_safe_refs_only",
        "safe_summary": (
            "Private dogfood capture can record daily-loop usefulness, false "
            "positives, memory decisions, follow-ups, drafts, recommendations, "
            "terminal-needed moments, and UI friction as safe refs only."
        ),
        "capture_event_kinds": [
            "morning_briefing_opened",
            "useful_item_marked",
            "false_positive_marked",
            "memory_decision_recorded",
            "action_inbox_decision_recorded",
            "follow_up_caught",
            "draft_created",
            "self_heal_recommendation_reviewed",
            "terminal_needed_moment",
            "ui_friction_note",
        ],
        "metric_refs": [
            "dogfood-metric-ref:morning-briefing-open",
            "dogfood-metric-ref:useful-item",
            "dogfood-metric-ref:false-positive",
            "dogfood-metric-ref:memory-decision",
            "dogfood-metric-ref:action-inbox-decision",
            "dogfood-metric-ref:follow-up-caught",
            "dogfood-metric-ref:draft-created",
            "dogfood-metric-ref:terminal-needed",
            "dogfood-metric-ref:ui-friction",
        ],
        "review_item_refs": [
            *[str(action["item_ref"]) for action in actions[:3]],
            *[str(item["review_ref"]) for item in memory_items[:3]],
            *[str(item["briefing_ref"]) for item in briefing_items[:3]],
        ],
        "friction_refs": [
            "product-friction-ref:source-readiness-gap",
            "product-friction-ref:blocked-state-copy",
            "product-friction-ref:terminal-needed",
        ],
        "recommendation_candidate_refs": [
            "recommendation-candidate:source-readiness-gap",
            "recommendation-candidate:daily-loop-friction",
            "recommendation-candidate:blocked-state-clarity",
        ],
        "evidence_refs": [
            str(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_evidence_packet_ref"
                ]
            ),
            "evidence-ref:dogfood-capture:private-local",
        ],
        "next_safe_action": (
            "Capture private daily-loop friction as safe refs and review any "
            "recommendation before a separately scoped change."
        ),
        "authority_boundary": (
            "Dogfood capture is local and private; it does not imply public beta, "
            "production readiness, distribution, self-healing apply, or action "
            "execution authority."
        ),
        "local_private_only": True,
        "safe_refs_only": True,
        "public_beta_claim_enabled": False,
        "production_readiness_claim_enabled": False,
        "public_distribution_enabled": False,
        "action_execution_enabled": False,
        "auto_apply_enabled": False,
    }


def _weekly_review_narrative(
    *,
    memory_to_loop_binding_contract: dict[str, Any],
    evidence_timeline: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    source_readiness_items: list[dict[str, Any]],
    crm_lite_followups: list[dict[str, Any]],
    dogfood_capture: dict[str, Any],
) -> dict[str, Any]:
    weekly_summary = memory_to_loop_binding_contract["weekly_ceo_review_summary"]
    action_status_refs = [
        f"action-status-ref:{str(action['item_ref']).replace(':', '-')}:{str(action.get('status', 'unknown'))}"
        for action in actions
    ]
    completed_refs = [
        ref
        for action, ref in zip(actions, action_status_refs, strict=False)
        if str(action.get("status")) in {"approved", "completed", "receipt_recorded"}
        or list(action.get("receipt_refs") or [])
    ][:5]
    deferred_refs = [
        ref
        for action, ref in zip(actions, action_status_refs, strict=False)
        if str(action.get("status")) in {"deferred", "snoozed"}
    ][:5]
    rejected_refs = [
        *list(weekly_summary["rejected_item_refs"]),
        *[
            ref
            for action, ref in zip(actions, action_status_refs, strict=False)
            if str(action.get("status")) in {"rejected", "blocked"}
        ],
    ][:5]
    planned_refs = [
        *[str(action["item_ref"]) for action in actions[:5]],
        *[follow_up["follow_up_ref"] for follow_up in crm_lite_followups[:3]],
    ]
    memory_change_refs = [
        *list(weekly_summary["memory_correction_refs"]),
        *list(weekly_summary["decision_refs"]),
    ][:6]
    crm_movement_refs = [
        *[follow_up["relationship_ref"] for follow_up in crm_lite_followups[:3]],
        *[follow_up["opportunity_ref"] for follow_up in crm_lite_followups[:3]],
    ][:6]
    draft_refs = [
        follow_up["review_envelope_ref"]
        for follow_up in crm_lite_followups
        if follow_up.get("draft_available") or follow_up.get("review_envelope_ref")
    ][:6]
    next_week_priority_refs = _unique_sorted_refs(
        [
            *list(weekly_summary["carry_forward_task_refs"]),
            *list(weekly_summary["unresolved_blocker_refs"]),
            *[
                source["source_ref"]
                for source in source_readiness_items
                if source["status"] in {"missing", "blocked", "not_configured"}
            ],
        ]
    )[:8]
    return {
        "weekly_review_ref": "weekly-review-narrative-ref:founder-loop:v1",
        "status": "safe_ref_history_ready",
        "safe_summary": (
            "Weekly Review reads the daily loop as history: proposed work, "
            "recorded decisions, changed refs, carry-forward items, blocked "
            "states, stale memory, missing sources, and private dogfood signals."
        ),
        "proposed_refs": planned_refs,
        "decided_refs": list(weekly_summary["decision_refs"]),
        "changed_refs": [
            str(item["timeline_item_ref"])
            for item in evidence_timeline
            if str(item.get("item_kind", "")).endswith("receipt_ref")
        ][:5],
        "completed_refs": completed_refs,
        "deferred_refs": deferred_refs,
        "rejected_refs": rejected_refs,
        "planned_refs": planned_refs,
        "memory_change_refs": memory_change_refs,
        "crm_movement_refs": crm_movement_refs,
        "draft_refs": draft_refs,
        "next_week_priority_refs": next_week_priority_refs,
        "carry_forward_refs": list(weekly_summary["carry_forward_task_refs"]),
        "blocked_refs": [
            *list(weekly_summary["unresolved_blocker_refs"]),
            *[
                blocked_ref
                for source in source_readiness_items
                for blocked_ref in source["blocked_state_refs"]
            ][:8],
        ],
        "stale_refs": list(weekly_summary["stale_memory_refs"]),
        "missing_source_refs": [
            source["source_ref"]
            for source in source_readiness_items
            if source["status"]
            in {"missing", "blocked", "unavailable", "not_configured"}
        ],
        "dogfood_refs": [
            dogfood_capture["capture_ref"],
            *dogfood_capture["friction_refs"],
        ],
        "evidence_refs": [
            "evidence-ref:weekly-review:narrative",
            *list(weekly_summary["input_refs"])[:6],
        ],
        "next_safe_action": (
            "Review carry-forward, blocked, stale, and missing-source refs before "
            "planning the next local-only loop."
        ),
        "authority_boundary": (
            "Weekly Review summarizes refs only; it does not invent truth, write "
            "memory, sync accounts, execute actions, or claim release readiness."
        ),
    }


def _daily_loop_summary(
    *,
    actions: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
    source_readiness_items: list[dict[str, Any]],
    crm_lite_followups: list[dict[str, Any]],
    memory_why_shown_items: list[dict[str, Any]],
    review_queue_groups: list[dict[str, Any]],
    weekly_review_narrative: dict[str, Any],
    dogfood_capture: dict[str, Any],
) -> dict[str, Any]:
    return {
        "loop_ref": "daily-loop-ref:founder-command-center:v1",
        "status": "implemented_readable_review_only_daily_loop",
        "home_surface": "Morning Briefing",
        "decision_surface": "Today",
        "safe_summary": (
            "Morning Briefing is the daily home and Today is the decision view; "
            "both use safe refs, blocked states, reviewed memory, Action Inbox "
            "receipts, source-readiness posture, CRM-lite follow-ups, evidence "
            "history, and dogfood capture."
        ),
        "today_plan_summary": (
            f"{len(plans)} local plan refs, {len(actions)} reviewable action refs, "
            f"{len(memory_items)} memory review refs, and {len(briefing_items)} "
            "briefing refs are available for local daily review."
        ),
        "review_queue_summary": (
            f"{sum(group['count'] for group in review_queue_groups)} grouped "
            "review refs across actions, memory, drafts, CRM-lite, system health, "
            "and patch proposals."
        ),
        "source_readiness_state_refs": [
            f"{item['source_ref']}:{item['status']}" for item in source_readiness_items
        ],
        "crm_follow_up_refs": [item["follow_up_ref"] for item in crm_lite_followups],
        "memory_reason_refs": [
            item["loop_item_ref"] for item in memory_why_shown_items
        ],
        "review_group_refs": [group["group_ref"] for group in review_queue_groups],
        "weekly_review_ref": weekly_review_narrative["weekly_review_ref"],
        "dogfood_capture_ref": dogfood_capture["capture_ref"],
        "next_safe_action": (
            "Open Morning Briefing, review Today decisions, then record only "
            "supported Action Inbox or Memory receipts."
        ),
        "authority_boundary": (
            "This loop is review-only, draft-only, and local-only; no email send, "
            "calendar write, connector write, source polling, provider call, "
            "action execution, automatic memory truth, hidden context injection, "
            "or public distribution authority is granted."
        ),
        "action_execution_enabled": False,
        "connector_runtime_enabled": False,
        "external_write_enabled": False,
        "runtime_model_calls_enabled": False,
    }


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for key in list(payload):
        if key.endswith("_json"):
            payload[key.removesuffix("_json")] = json.loads(payload.pop(key) or "[]")
    for bool_key in [
        "approval_required",
        "unknown_paid_cost_requires_explicit_approval",
        "frontier_usage_claimed",
    ]:
        if bool_key in payload:
            payload[bool_key] = bool(payload[bool_key])
    return payload


def _memory_source_policy_for(item: dict[str, Any]) -> dict[str, Any]:
    source_refs = [str(ref) for ref in item.get("source_refs", [])]
    policies = memory_source_provenance_policy_rows()
    for policy in policies:
        prefix = str(policy["safe_ref_prefix"])
        if any(ref == prefix or ref.startswith(f"{prefix}:") for ref in source_refs):
            return policy

    candidate_kind = str(item.get("candidate_kind", "")).lower()
    source_kind_by_candidate = {
        "operator_preference": "manual_note",
        "preference": "manual_note",
        "manual_note": "manual_note",
        "business_contact": "crm_lite_business_record",
        "business_record": "crm_lite_business_record",
        "plan": "task_plan",
        "task_plan": "task_plan",
        "action": "action_proposal",
        "action_proposal": "action_proposal",
        "evidence": "evidence_timeline_ref",
        "calendar": "read_only_calendar_metadata_ref",
        "email": "read_only_email_metadata_ref",
        "chat": "local_chat_summary",
        "coding": "local_coding_summary",
        "external_assistant": "external_assistant_review_summary",
    }
    source_kind = source_kind_by_candidate.get(candidate_kind, "manual_note")
    return next(policy for policy in policies if policy["source_kind"] == source_kind)


def _memory_source_ref_status(
    item: dict[str, Any],
    policy: dict[str, Any],
) -> str:
    source_refs = [str(ref) for ref in item.get("source_refs", [])]
    if not source_refs:
        return "missing_safe_source_refs"
    prefix = str(policy["safe_ref_prefix"])
    if any(ref == prefix or ref.startswith(f"{prefix}:") for ref in source_refs):
        return "safe_source_refs_present"
    return "legacy_safe_refs_need_review"


def _memory_provenance_ref_status(item: dict[str, Any]) -> str:
    if item.get("provenance_refs"):
        return "safe_provenance_refs_present"
    return "missing_provenance_refs"


def _memory_source_contract_payload(item: dict[str, Any]) -> dict[str, Any]:
    policy = _memory_source_policy_for(item)
    return {
        "source_policy_ref": MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
        "source_kind": policy["source_kind"],
        "source_kind_ref": policy["source_kind_ref"],
        "source_refs_status": _memory_source_ref_status(item, policy),
        "provenance_refs_status": _memory_provenance_ref_status(item),
        "source_review_required": True,
        "source_trust_posture": MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
        "safe_summary_only": True,
        "source_truth_authority": False,
        "memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "account_auth_enabled": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
        "source_payload_storage_allowed": False,
        "prompt_body_storage_allowed": False,
        "response_body_storage_allowed": False,
        "provider_body_storage_allowed": False,
        "path_body_storage_allowed": False,
        "log_body_storage_allowed": False,
        "account_ref_storage_allowed": False,
        "private_content_storage_allowed": False,
        "connector_runtime_allowed": False,
        "provider_or_model_authority_allowed": False,
        "accepted_as_truth": False,
    }


def _safe_suffix(value: str) -> str:
    return SAFE_STATUS_REF_CHARS.sub("-", value.lower()).strip("-") or "missing"


def _short_ref_suffix(value: str, *, prefix_len: int = 48) -> str:
    suffix = _safe_suffix(value)
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{suffix[:prefix_len].strip('-') or 'ref'}-{digest}"


def _action_revision_source_payload(action: dict[str, Any]) -> dict[str, Any]:
    item_ref = str(action["item_ref"])
    generation = int(action.get("action_generation") or 1)
    authoritative_expiry = str(action.get("expires_at") or "expiry-not-set")
    reviewed_content_fingerprint_ref = action_payload_fingerprint_ref(
        {
            "title": str(action.get("title") or "Action item"),
            "safe_summary": str(
                action.get("safe_summary")
                or "Action item is available as safe review metadata only."
            ),
            "surface": str(action.get("surface") or "Actions"),
            "priority": str(action.get("priority") or "medium"),
            "authority_boundary": str(
                action.get("authority_boundary")
                or "Python Core authority validation is required."
            ),
            "approval_required": bool(action.get("approval_required", True)),
            "evidence_refs": sorted(
                str(ref) for ref in action.get("evidence_refs") or []
            ),
        }
    )
    cost_provider_posture_fingerprint_ref = action_payload_fingerprint_ref(
        {
            "estimated_cost_usd": float(action.get("estimated_cost_usd") or 0.0),
            "max_approved_cost_usd": float(action.get("max_approved_cost_usd") or 0.0),
            "provider_ref": str(
                action.get("provider_ref") or "provider-ref:not-invoked"
            ),
            "model_profile_ref": str(
                action.get("model_profile_ref") or "model-profile-ref:not-invoked"
            ),
            "input_metered_units": int(action.get("input_metered_units") or 0),
            "output_metered_units": int(action.get("output_metered_units") or 0),
            "total_metered_units": int(action.get("total_metered_units") or 0),
            "cost_estimate_ref": str(
                action.get("cost_estimate_ref") or "cost-estimate-ref:not-invoked"
            ),
            "captured_usage_ref": str(
                action.get("captured_usage_ref") or "usage-capture-ref:not-invoked"
            ),
            "budget_decision_ref": str(
                action.get("budget_decision_ref") or "budget-decision-ref:not-invoked"
            ),
            "cost_receipt_refs": sorted(
                str(ref) for ref in action.get("cost_receipt_refs") or []
            ),
            "cost_blocked_state_refs": sorted(
                str(ref) for ref in action.get("cost_blocked_state_refs") or []
            ),
            "cost_state_label": str(action.get("cost_state_label") or "Cost blocked"),
            "provider_authority_state_label": str(
                action.get("provider_authority_state_label") or "No provider authority"
            ),
            "unknown_paid_cost_requires_explicit_approval": bool(
                action.get("unknown_paid_cost_requires_explicit_approval", True)
            ),
            "frontier_usage_claimed": bool(action.get("frontier_usage_claimed", False)),
        }
    )
    return {
        "revision_contract_ref": FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF,
        "item_ref": item_ref,
        "reviewed_content_fingerprint_ref": reviewed_content_fingerprint_ref,
        "cost_provider_posture_fingerprint_ref": (
            cost_provider_posture_fingerprint_ref
        ),
        "action_envelope_ref": str(action["action_envelope_ref"]),
        "approval_envelope_ref": str(
            action.get("approval_envelope_ref") or "approval-envelope-ref:missing"
        ),
        "exact_scope_ref": str(action["action_scope_ref"]),
        "approval_requirement_ref": str(action["action_approval_requirement_ref"]),
        "rollback_ref": str(
            action.get("rollback_ref")
            or action.get("action_rollback_ref")
            or "rollback-ref:missing"
        ),
        "safe_disable_ref": str(
            action.get("safe_disable_ref")
            or action.get("action_safe_disable_ref")
            or "safe-disable-ref:missing"
        ),
        "action_kind": str(action.get("action_kind") or "review_only"),
        "risk_class": str(action.get("risk_class") or "high"),
        "side_effect_class": str(
            action.get("side_effect_class") or "local_dev_workspace_only"
        ),
        "deadline_ref": action_decision_deadline_ref(
            item_ref,
            generation,
            authoritative_expiry,
        ),
        "decision_route_refs": list(FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS),
        "decision_adapter_ref": FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
        "authority_input_refs": list(FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS),
    }


def _build_action_revision_state(
    action: dict[str, Any],
    *,
    generation: int,
    previous_revision_ref: str | None = None,
    transition_ref: str = "revision-transition:action-inbox:initial",
) -> dict[str, Any]:
    item_ref = str(action["item_ref"])
    source_payload = _action_revision_source_payload(
        {**action, "action_generation": generation}
    )
    source_fingerprint_ref = action_payload_fingerprint_ref(source_payload)
    generation_ref = action_generation_ref(item_ref, generation)
    revision_payload = {
        "revision_contract_ref": FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF,
        "item_ref": item_ref,
        "generation": generation,
        "generation_ref": generation_ref,
        "source_fingerprint_ref": source_fingerprint_ref,
        "previous_revision_ref": previous_revision_ref,
        "transition_ref": transition_ref,
    }
    revision_fingerprint_ref = action_revision_fingerprint_ref(revision_payload)
    revision_ref = action_revision_ref(
        item_ref,
        generation,
        revision_fingerprint_ref,
    )
    state = {
        **revision_payload,
        "revision_ref": revision_ref,
        "revision_fingerprint_ref": revision_fingerprint_ref,
        "backend_owned": True,
        "safe_refs_only": True,
        "expected_revision_required": True,
        "stale_conflict_code": "FOUNDER_LOOP_ACTION_STALE_REVISION",
        "refresh_route_ref": "GET /control-center/actions/inbox",
    }
    _validate_safe_payload(state, "action_revision_state")
    return state


def _memory_review_decision_contract_payload(item: dict[str, Any]) -> dict[str, Any]:
    review_ref = str(item.get("review_ref", "memory-review:missing"))
    suffix = _safe_suffix(review_ref)
    review_state = str(item.get("review_state", "review_needed"))
    decision_status = (
        "review_needed_no_decision_captured"
        if review_state == "review_needed"
        else "decision_metadata_present_requires_recheck"
    )
    return {
        "decision_contract_ref": MEMORY_REVIEW_DECISION_CONTRACT_REF,
        "available_decision_states": MEMORY_REVIEW_DECISION_STATES,
        "decision_capture_status": decision_status,
        "decision_required_ref_fields": MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS,
        "decision_actor_ref": "actor-ref:local-operator-review-required",
        "decision_source_provenance_contract_ref": (
            MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
        ),
        "decision_source_kind": _memory_source_policy_for(item)["source_kind"],
        "decision_source_trust_posture": MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
        "decision_redaction_status": "redacted_summary_only",
        "decision_audit_refs": [f"audit-plan:memory-review:{suffix}"],
        "decision_receipt_refs": [f"receipt-plan:memory-review:{suffix}"],
        "decision_blocked_state_refs": [
            "blocked-state:no-memory-write",
            "blocked-state:no-memory-delete",
            "blocked-state:no-memory-export",
            "blocked-state:no-context-injection",
            "blocked-state:no-connector-runtime",
            "blocked-state:no-account-auth",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-public-beta-or-production-authority",
        ],
        "decision_stale_state": str(
            item.get("stale_state", "recheck_source_refs_before_memory_use")
        ),
        "decision_retention_posture": str(
            item.get("retention_posture", "retention_policy_not_bound")
        ),
        "decision_correction_posture": str(
            item.get(
                "correction_posture",
                "correction_requires_scoped_memory_write_contract",
            )
        ),
        "decision_authority_boundary": (
            "Memory review decisions are review metadata only; writes, deletes, "
            "exports, context injection, connector runtime, account auth, and "
            "production authority remain unscoped."
        ),
        "decision_review_only": True,
        "memory_delete_authorized": False,
        "memory_export_authorized": False,
        "retention_execution_authorized": False,
    }


def _business_memory_quality_contract_payload(item: dict[str, Any]) -> dict[str, Any]:
    review_ref = str(item.get("review_ref", "memory-review:missing"))
    suffix = _safe_suffix(review_ref)
    candidate_kind = str(item.get("candidate_kind", "preference"))
    if candidate_kind not in BUSINESS_MEMORY_CANDIDATE_KINDS:
        candidate_kind = "preference"
    quality_state_refs = [
        business_memory_quality_ref("low_confidence"),
        business_memory_quality_ref("blocked"),
    ]
    if str(item.get("review_state", "")) == "reviewed":
        quality_state_refs = [business_memory_quality_ref("reviewed")]
    if not item.get("source_refs"):
        quality_state_refs.append(business_memory_quality_ref("source_missing"))
    if not item.get("evidence_refs"):
        quality_state_refs.append(business_memory_quality_ref("evidence_missing"))
    related_entity_refs = [
        f"business-memory-entity:{candidate_kind.replace('_', '-')}:{suffix}"
    ]
    source_policy = _memory_source_policy_for(item)
    return {
        "business_memory_quality_contract_ref": BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
        "business_memory_candidate_ref": business_memory_candidate_ref(
            candidate_kind,
            suffix,
        ),
        "business_memory_candidate_kind": candidate_kind,
        "business_memory_candidate_kind_ref": (
            f"business-memory-kind:{candidate_kind.replace('_', '-')}"
        ),
        "business_memory_source_provenance_contract_ref": (
            MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
        ),
        "business_memory_source_kind": source_policy["source_kind"],
        "business_memory_source_trust_posture": MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
        "business_memory_redaction_status": "redacted_summary_only",
        "business_memory_quality_state_refs": sorted(set(quality_state_refs)),
        "business_memory_quality_posture": "review_required_quality_blocked",
        "business_memory_review_state": str(item.get("review_state", "review_needed")),
        "business_memory_correction_path": str(
            item.get(
                "correction_posture",
                "correction_requires_scoped_memory_write_contract",
            )
        ),
        "business_memory_stale_state": str(
            item.get("stale_state", "recheck_source_refs_before_memory_use")
        ),
        "business_memory_retention_posture": str(
            item.get("retention_posture", "retention_policy_not_bound")
        ),
        "business_memory_delete_posture": str(
            item.get("delete_posture", "delete_execution_not_scoped")
        ),
        "business_memory_export_posture": "export_execution_not_scoped",
        "business_memory_related_entity_refs": related_entity_refs,
        "business_memory_duplicate_of_refs": [],
        "business_memory_conflict_with_refs": [],
        "business_memory_blocker_refs": [
            "blocked-state:no-memory-write",
            "blocked-state:no-memory-delete",
            "blocked-state:no-memory-export",
            "blocked-state:no-context-injection",
            "blocked-state:no-external-crm-write",
            "blocked-state:no-account-sync",
            "blocked-state:no-automatic-recall",
            "blocked-state:no-connector-runtime",
            "blocked-state:no-account-auth",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-source-truth-authority",
            "blocked-state:no-raw-source-display",
            "blocked-state:no-public-beta-or-distribution",
            "blocked-state:no-production-authority",
        ],
        "business_memory_surface_refs": [
            "today-ref:memory-review-business-quality",
            "action-inbox-ref:memory-follow-up-candidates",
            "evidence-ref:memory-business-quality-history",
            "weekly-review-ref:business-memory-carry-forward",
        ],
        "business_memory_next_safe_action": (
            "Review quality posture and safe refs; keep memory writes, CRM sync, "
            "and context injection blocked until scoped policy milestones exist."
        ),
        "business_memory_safe_refs_only": True,
        "business_memory_review_required_before_recall": True,
        "business_memory_accepted_as_recall": False,
        "business_memory_write_authorized": False,
        "business_memory_delete_authorized": False,
        "business_memory_export_authorized": False,
        "business_memory_crm_write_authorized": False,
        "business_memory_account_sync_authorized": False,
        "business_memory_context_injection_authorized": False,
        "business_memory_authority_boundary": (
            "Business memory quality is review metadata only; external CRM writes, "
            "account sync, automatic recall, memory mutation, and context injection "
            "remain unscoped."
        ),
    }


def _plans_action_envelope_blockers(extra: list[str] | None = None) -> list[str]:
    return list(
        dict.fromkeys([*PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS, *(extra or [])])
    )


def _plan_action_envelope_contract_payload(plan: dict[str, Any]) -> dict[str, Any]:
    plan_ref = str(plan.get("plan_ref", "plan-summary:missing"))
    envelope = build_plan_action_envelope(
        source_plan_ref=plan_ref,
        title=str(plan.get("title", "Plan summary")),
        safe_summary=(
            "Plan summary has a reviewable Action envelope with exact-scope, "
            "receipt, idempotency, rollback, and safe-disable refs; execution "
            "remains blocked."
        ),
        evidence_refs=list(plan.get("evidence_refs") or [])
        or ["evidence-ref:founder-loop:plan-summary"],
        blocked_state_refs=[
            "blocked-state:no-plan-action-execution",
            "blocked-state:no-plan-approval-grant-capture",
        ],
        next_safe_action=str(
            plan.get(
                "next_step_summary",
                "Review the Action envelope metadata before any future scoped authority.",
            )
        ),
    )
    payload = envelope.model_dump(mode="json")
    cost_slot = _frontier_ai_cost_slot(str(payload["action_envelope_ref"]))
    return {
        "action_envelope_contract_ref": payload["contract_ref"],
        "action_envelope_ref": payload["action_envelope_ref"],
        "action_envelope_status": "review_ready_execution_blocked",
        "action_envelope_safe_summary": payload["safe_summary"],
        "scope_ref": payload["scope_ref"],
        "side_effect_class": payload["side_effect_class"],
        "risk_class": payload["risk_class"],
        "approval_required": payload["approval_required"],
        "approval_requirement_ref": payload["approval_requirement_ref"],
        "review_actions": payload["review_actions"],
        "review_posture_refs": payload["review_posture_refs"],
        "expected_receipt_refs": payload["expected_receipt_refs"],
        "idempotency_key_ref": payload["idempotency_key_ref"],
        "expires_at": payload["expires_at"],
        "stale_state": payload["stale_state"],
        "rollback_ref": payload["rollback_ref"],
        "safe_disable_ref": payload["safe_disable_ref"],
        "blocked_state_refs": payload["blocked_state_refs"],
        "authority_boundary": payload["authority_boundary"],
        "exact_scope_required": payload["exact_scope_required"],
        "approval_ref_authority": payload["approval_ref_authority"],
        "approval_grant_capture_enabled": payload["approval_grant_capture_enabled"],
        "action_execution_enabled": payload["action_execution_enabled"],
        "tool_execution_enabled": payload["tool_execution_enabled"],
        "workflow_execution_enabled": payload["workflow_execution_enabled"],
        "browser_execution_enabled": payload["browser_execution_enabled"],
        "connector_runtime_enabled": payload["connector_runtime_enabled"],
        "connector_write_enabled": payload["connector_write_enabled"],
        "shell_subprocess_execution_enabled": payload[
            "shell_subprocess_execution_enabled"
        ],
        "model_provider_authority_allowed": payload["model_provider_authority_allowed"],
        "safe_refs_only": payload["safe_refs_only"],
        "raw_content_included": payload["raw_content_included"],
        "plan_action_envelope_ref": payload["action_envelope_ref"],
        "plan_action_scope_ref": payload["scope_ref"],
        "plan_action_approval_requirement_ref": payload["approval_requirement_ref"],
        "plan_action_review_posture_refs": payload["review_posture_refs"],
        "plan_action_expected_receipt_refs": payload["expected_receipt_refs"],
        "plan_action_blocked_state_refs": [
            *payload["blocked_state_refs"],
            *cost_slot["cost_blocked_state_refs"],
        ],
        "plan_action_authority_boundary": payload["authority_boundary"],
        "action_envelope_cost_contract_ref": FRONTIER_AI_COST_USAGE_CONTRACT_REF,
        "action_envelope_estimated_cost_usd": cost_slot["estimated_cost_usd"],
        "action_envelope_max_approved_cost_usd": cost_slot["max_approved_cost_usd"],
        "action_envelope_provider_ref": cost_slot["provider_ref"],
        "action_envelope_model_profile_ref": cost_slot["model_profile_ref"],
        "action_envelope_input_metered_units": cost_slot["input_metered_units"],
        "action_envelope_output_metered_units": cost_slot["output_metered_units"],
        "action_envelope_total_metered_units": cost_slot["total_metered_units"],
        "action_envelope_cost_estimate_ref": cost_slot["cost_estimate_ref"],
        "action_envelope_captured_usage_ref": cost_slot["captured_usage_ref"],
        "action_envelope_budget_decision_ref": cost_slot["budget_decision_ref"],
        "action_envelope_cost_receipt_refs": cost_slot["cost_receipt_refs"],
        "action_envelope_cost_blocked_state_refs": cost_slot["cost_blocked_state_refs"],
        "action_envelope_cost_state_label": cost_slot["cost_state_label"],
        "action_envelope_provider_authority_state_label": cost_slot[
            "provider_authority_state_label"
        ],
        "action_envelope_unknown_paid_cost_requires_explicit_approval": cost_slot[
            "approval_required_for_unknown_paid_cost"
        ],
        "action_envelope_frontier_usage_claimed": cost_slot["frontier_usage_claimed"],
    }


def _task_decomposition_contract_payload(plan: dict[str, Any]) -> dict[str, Any]:
    payload = task_decomposition_read_model_for_plan(
        str(plan.get("plan_ref", "plan-summary:missing")),
        title=str(plan.get("title", "Plan summary")),
        safe_summary=str(
            plan.get(
                "safe_summary",
                "Plan summary needs a review-only decomposition proposal.",
            )
        ),
        evidence_refs=list(plan.get("evidence_refs") or []),
    )
    _validate_safe_payload(payload, "task_decomposition_plan_payload")
    return payload


def _task_decomposition_action_items_for_plans(
    plans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    action_items: list[dict[str, Any]] = []
    for plan in plans[:3]:
        payload = _task_decomposition_contract_payload(plan)
        request = {
            "request_ref": payload["task_decomposition_request_ref"],
            "original_request_ref": payload["task_decomposition_original_request_ref"],
            "original_request_safe_summary": str(
                plan.get(
                    "safe_summary",
                    "Plan summary needs a review-only decomposition proposal.",
                )
            ),
            "source_refs": [str(plan.get("plan_ref", "plan-summary:missing"))],
            "evidence_refs": list(plan.get("evidence_refs") or []),
        }
        envelope = build_task_decomposition_review_envelope(request)
        action_items.extend(task_decomposition_action_items(envelope))
    return action_items


def _task_decomposition_action_proposal_summary(
    proposals: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "contract_ref": TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF,
        "source": "python_core_task_decomposition_proposal_engine",
        "status": "proposal_only_review_required",
        "proposal_count": len(proposals),
        "action_kind": TASK_DECOMPOSITION_ACTION_KIND,
        "proposal_refs": [
            str(item["task_decomposition_proposal_ref"]) for item in proposals
        ],
        "action_item_refs": [str(item["item_ref"]) for item in proposals],
        "blocked_authority_refs": list(
            TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS
        ),
        "review_only": True,
        "proposal_only": True,
        "local_task_commit_eligible": False,
        "action_execution_enabled": False,
        "workflow_execution_enabled": False,
        "tool_execution_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "connector_write_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_network_enabled": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
    }


def _frontier_ai_cost_slot(
    source_ref: str,
    *,
    estimated_cost_usd: float = 0.0,
    max_approved_cost_usd: float = 0.0,
    provider_ref: str = "provider-ref:not-invoked",
    model_profile_ref: str = "model-profile-ref:not-invoked",
    input_metered_units: int = 0,
    output_metered_units: int = 0,
    frontier_usage_claimed: bool = False,
    unknown_cost: bool = False,
) -> dict[str, Any]:
    total_metered_units = input_metered_units + output_metered_units
    cost_event_ref = _status_ref("cost-estimate-ref", source_ref)
    cost_estimate_ref = cost_event_ref
    captured_usage_ref = _status_ref("usage-capture-ref", source_ref)
    estimate = CostEstimate(
        estimate_id=cost_estimate_ref,
        input_tokens=input_metered_units,
        output_tokens=output_metered_units,
        total_tokens=total_metered_units,
        estimated_cost_usd=None if unknown_cost else estimated_cost_usd,
        estimated_token_cost_usd=None if unknown_cost else estimated_cost_usd,
        model_profile_id=model_profile_ref,
        provider_id=provider_ref,
        unknown_cost=unknown_cost,
    )
    decision = CostGovernor().evaluate(
        estimate,
        [
            CostBudget(
                budget_id="budget:frontier-ai:operator-run-default",
                scope=BudgetScope.run,
                max_cost_usd=max_approved_cost_usd,
                hard_limit=True,
            )
        ],
    )
    budget_decision_ref = _status_ref("budget-decision-ref", str(decision.decision_id))
    cost_blocked_state_refs = [
        "blocked-state:no-provider-model-authority",
        "blocked-state:no-provider-sdk-call",
        "blocked-state:no-runtime-model-call",
        "blocked-state:unknown-paid-cost-requires-approval",
    ]
    provider_model_ref_missing = (
        provider_ref == "provider-ref:not-invoked"
        or model_profile_ref == "model-profile-ref:not-invoked"
    )
    if provider_model_ref_missing:
        cost_blocked_state_refs.append(
            "blocked-state:frontier-provider-model-ref-missing"
        )
    if decision.approval_required:
        cost_blocked_state_refs.append(
            "blocked-state:unknown-paid-cost-requires-approval"
        )
    if not decision.allowed:
        cost_blocked_state_refs.append("blocked-state:frontier-ai-cost-blocked")
    if estimated_cost_usd > max_approved_cost_usd:
        cost_blocked_state_refs.append("blocked-state:frontier-ai-cost-budget-exceeded")
    if frontier_usage_claimed:
        cost_blocked_state_refs.append(
            "blocked-state:frontier-ai-usage-claim-requires-cost-receipts"
        )
    cost_receipt_refs = _unique_sorted_refs(
        [
            cost_estimate_ref,
            captured_usage_ref,
            budget_decision_ref,
            provider_ref,
            model_profile_ref,
        ]
    )
    slot = FounderLoopOperatorRunCostUsage(
        cost_event_ref=cost_event_ref,
        cost_estimate_ref=cost_estimate_ref,
        captured_usage_ref=captured_usage_ref,
        budget_decision_ref=budget_decision_ref,
        source_event_ref=source_ref,
        provider_ref=provider_ref,
        model_profile_ref=model_profile_ref,
        provider_model_ref_status=(
            "provider_model_ref_missing_or_not_invoked"
            if provider_model_ref_missing
            else "provider_model_ref_present_safe_ref_only"
        ),
        usage_capture_status=(
            "frontier_ai_usage_claimed_receipt_required"
            if frontier_usage_claimed
            else "no_frontier_ai_usage_recorded"
        ),
        cost_capture_status=(
            "cost_receipts_required_for_claimed_frontier_usage"
            if frontier_usage_claimed
            else "accounting_slot_ready_no_provider_call"
        ),
        cost_state_label=(
            "Unknown paid cost"
            if decision.approval_required
            else (
                "Cost blocked"
                if provider_model_ref_missing
                or not decision.allowed
                or estimated_cost_usd > max_approved_cost_usd
                else "Cost approved"
            )
        ),
        provider_authority_state_label=(
            "No provider authority"
            if provider_model_ref_missing
            else "Provider/model refs present"
        ),
        frontier_usage_claimed=frontier_usage_claimed,
        frontier_ai_routing_allowed=False,
        input_metered_units=input_metered_units,
        output_metered_units=output_metered_units,
        total_metered_units=total_metered_units,
        estimated_cost_usd=estimated_cost_usd,
        captured_cost_usd=0.0,
        max_approved_cost_usd=max_approved_cost_usd,
        unknown_cost=unknown_cost,
        approval_required_for_unknown_paid_cost=True,
        cost_governor_ref="core.costs.CostGovernor",
        cost_governor_allowed=bool(decision.allowed),
        cost_governor_decision_status=str(decision.status),
        cost_governor_reason_refs=[
            _status_ref(
                "cost-governor-reason",
                str(reason).lower().replace("token", "metered-unit"),
            )
            for reason in decision.reason_codes
        ],
        budget_status_ref=(
            "budget-status:unknown-paid-cost-requires-approval"
            if decision.approval_required
            else _status_ref("budget-status", str(decision.status))
        ),
        cost_receipt_refs=cost_receipt_refs,
        cost_blocked_state_refs=_unique_sorted_refs(cost_blocked_state_refs),
        prompt_content_stored=False,
        response_content_stored=False,
        provider_exchange_content_stored=False,
    )
    return slot.model_dump(mode="json")


def _action_envelope_contract_payload(action: dict[str, Any]) -> dict[str, Any]:
    action_ref = str(action.get("item_ref", "founder-action:missing"))
    source_plan_ref = _status_ref("plan-summary", str(action.get("surface", "Actions")))
    receipt_refs = list(action.get("receipt_refs") or [])
    audit_refs = list(action.get("audit_refs") or [])
    blocked_state_refs = _plans_action_envelope_blockers(
        [
            _status_ref(
                "blocked-state",
                str(action.get("state_change_readiness", "state-change-blocked")),
            ),
            _status_ref(
                "blocked-state",
                str(action.get("blocked_state", "mutation-blocked")),
            ),
        ]
    )
    envelope = build_plan_action_envelope(
        source_plan_ref=source_plan_ref,
        source_action_ref=action_ref,
        title=str(action.get("title", "Action item")),
        safe_summary=str(
            action.get(
                "safe_summary",
                "Action item is available as safe review metadata only.",
            )
        ),
        evidence_refs=list(action.get("evidence_refs") or [])
        or ["evidence-ref:founder-loop:action-inbox"],
        side_effect_class=str(action.get("side_effect_class", "validation_only")),
        risk_class=str(action.get("risk_class", "medium")),
        approval_required=bool(action.get("approval_required", True)),
        audit_refs=audit_refs,
        blocked_state_refs=blocked_state_refs,
        next_safe_action=str(
            action.get(
                "next_safe_action",
                "Review the safe summary and keep mutation blocked until scoped.",
            )
        ),
    )
    payload = envelope.model_dump(mode="json")
    expected_receipt_refs = receipt_refs or payload["expected_receipt_refs"]
    action_envelope_ref = str(payload["action_envelope_ref"])
    action_scope_ref = str(payload["scope_ref"])
    action_approval_requirement_ref = str(payload["approval_requirement_ref"])
    if (
        action.get("state_change_contract_ref")
        == MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF
    ):
        context_pack_ref = _first_ref_with_prefix(
            list(action.get("evidence_refs") or []),
            "context-pack-ref:",
        )
        if context_pack_ref:
            action_envelope_ref = memory_context_pack_action_envelope_ref(
                context_pack_ref
            )
            action_scope_ref = memory_context_pack_action_scope_ref(context_pack_ref)
            action_approval_requirement_ref = (
                "approval-requirement:memory-context-pack-action:"
                f"{_short_ref_suffix(context_pack_ref)}"
            )
    cost_slot = _frontier_ai_cost_slot(
        action_envelope_ref,
        estimated_cost_usd=float(action.get("estimated_cost_usd") or 0.0),
        max_approved_cost_usd=float(action.get("max_approved_cost_usd") or 0.0),
        provider_ref=str(action.get("provider_ref") or "provider-ref:not-invoked"),
        model_profile_ref=str(
            action.get("model_profile_ref") or "model-profile-ref:not-invoked"
        ),
        input_metered_units=int(action.get("input_metered_units") or 0),
        output_metered_units=int(action.get("output_metered_units") or 0),
        frontier_usage_claimed=bool(action.get("frontier_usage_claimed", False)),
        unknown_cost=False,
    )
    return {
        "action_envelope_contract_ref": payload["contract_ref"],
        "action_envelope_ref": action_envelope_ref,
        "action_envelope_status": "review_ready_execution_blocked",
        "action_envelope_safe_summary": payload["safe_summary"],
        "action_scope_ref": action_scope_ref,
        "action_approval_requirement_ref": action_approval_requirement_ref,
        "action_review_actions": payload["review_actions"],
        "action_review_posture_refs": payload["review_posture_refs"],
        "action_expected_receipt_refs": expected_receipt_refs,
        "action_idempotency_key_ref": payload["idempotency_key_ref"],
        "action_expires_at": payload["expires_at"],
        "action_stale_state": payload["stale_state"],
        "action_rollback_ref": payload["rollback_ref"],
        "action_safe_disable_ref": payload["safe_disable_ref"],
        "action_blocked_state_refs": payload["blocked_state_refs"],
        "action_authority_boundary": payload["authority_boundary"],
        "action_exact_scope_required": payload["exact_scope_required"],
        "action_envelope_approval_ref_authority": payload["approval_ref_authority"],
        "action_envelope_grant_capture_enabled": payload[
            "approval_grant_capture_enabled"
        ],
        "action_envelope_execution_enabled": payload["action_execution_enabled"],
        "action_envelope_tool_execution_enabled": payload["tool_execution_enabled"],
        "action_envelope_workflow_execution_enabled": payload[
            "workflow_execution_enabled"
        ],
        "action_envelope_browser_execution_enabled": payload[
            "browser_execution_enabled"
        ],
        "action_envelope_connector_runtime_enabled": payload[
            "connector_runtime_enabled"
        ],
        "action_envelope_connector_write_enabled": payload["connector_write_enabled"],
        "action_envelope_shell_execution_enabled": payload[
            "shell_subprocess_execution_enabled"
        ],
        "action_envelope_model_provider_authority_allowed": payload[
            "model_provider_authority_allowed"
        ],
        "action_envelope_safe_refs_only": payload["safe_refs_only"],
        "action_envelope_raw_content_included": payload["raw_content_included"],
        "action_envelope_cost_contract_ref": FRONTIER_AI_COST_USAGE_CONTRACT_REF,
        "action_envelope_estimated_cost_usd": cost_slot["estimated_cost_usd"],
        "action_envelope_max_approved_cost_usd": cost_slot["max_approved_cost_usd"],
        "action_envelope_provider_ref": cost_slot["provider_ref"],
        "action_envelope_model_profile_ref": cost_slot["model_profile_ref"],
        "action_envelope_input_metered_units": cost_slot["input_metered_units"],
        "action_envelope_output_metered_units": cost_slot["output_metered_units"],
        "action_envelope_total_metered_units": cost_slot["total_metered_units"],
        "action_envelope_cost_estimate_ref": cost_slot["cost_estimate_ref"],
        "action_envelope_captured_usage_ref": cost_slot["captured_usage_ref"],
        "action_envelope_budget_decision_ref": cost_slot["budget_decision_ref"],
        "action_envelope_cost_receipt_refs": cost_slot["cost_receipt_refs"],
        "action_envelope_cost_blocked_state_refs": cost_slot["cost_blocked_state_refs"],
        "action_envelope_cost_state_label": cost_slot["cost_state_label"],
        "action_envelope_provider_authority_state_label": cost_slot[
            "provider_authority_state_label"
        ],
        "action_envelope_unknown_paid_cost_requires_explicit_approval": cost_slot[
            "approval_required_for_unknown_paid_cost"
        ],
        "action_envelope_frontier_usage_claimed": cost_slot["frontier_usage_claimed"],
    }


def _action_approval_envelope_read_model(action: dict[str, Any]) -> dict[str, Any]:
    approval_required = bool(action.get("approval_required", True))
    has_state_change_contract = bool(action.get("state_change_contract_ref"))
    exact_scope = _approval_envelope_value_for_contract(
        action.get("action_scope_ref"),
        has_contract=has_state_change_contract,
        approval_required=approval_required,
    )
    approval_requirement = (
        _approval_envelope_value(
            action.get("action_approval_requirement_ref"),
            missing_state="missing",
        )
        if approval_required
        else "not_applicable"
    )
    if approval_required and not has_state_change_contract:
        approval_requirement = "missing"
    idempotency_ref = _approval_envelope_value_for_contract(
        action.get("idempotency_key_ref") or action.get("action_idempotency_key_ref"),
        has_contract=has_state_change_contract,
        approval_required=approval_required,
    )
    if not approval_required:
        expected_receipt_refs = ["not_applicable"]
    elif not has_state_change_contract:
        expected_receipt_refs = ["missing"]
    else:
        expected_receipt_refs = _approval_envelope_list(
            action.get("action_expected_receipt_refs") or action.get("receipt_refs"),
            missing_state="missing",
        )
    rollback_safe_disable_refs = [
        _approval_envelope_value(action.get("rollback_ref"), missing_state="missing"),
        _approval_envelope_value(
            action.get("safe_disable_ref"),
            missing_state="missing",
        ),
    ]
    blocked_authority_refs = _approval_envelope_list(
        [
            *(action.get("action_blocked_state_refs") or []),
            *(action.get("action_envelope_cost_blocked_state_refs") or []),
            *(action.get("cost_blocked_state_refs") or []),
            *(action.get("local_task_commit_blocked_reasons") or []),
            *(action.get("local_task_commit_external_authority_blocked_refs") or []),
        ],
        missing_state="not_applicable",
    )
    evidence_refs = _approval_envelope_list(
        action.get("evidence_refs"),
        missing_state="missing",
    )
    expires_at = _approval_envelope_value(
        action.get("expires_at") or action.get("action_expires_at"),
        missing_state="unknown",
    )
    stale_state = _approval_envelope_value(
        action.get("stale_state") or action.get("action_stale_state"),
        missing_state="unknown",
    )
    return {
        "schema_version": "founder_loop_action_approval_envelope.v1",
        "contract_ref": "contract-ref:founder-loop-action-approval-envelope:v1",
        "source": "python_core_action_inbox_read_model",
        "backend_owned": True,
        "revision_contract_ref": str(
            action.get("action_revision_contract_ref")
            or FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF
        ),
        "generation_ref": str(
            action.get("action_generation_ref") or "action-generation:missing:00000000"
        ),
        "revision_ref": str(
            action.get("action_revision_ref")
            or "action-revision:missing:00000000:missing"
        ),
        "revision_fingerprint_ref": str(
            action.get("action_revision_fingerprint_ref")
            or "revision-fingerprint:action-inbox:missing"
        ),
        "expected_revision_required": True,
        "action_kind": str(action.get("action_kind") or "review_only"),
        "exact_scope": exact_scope,
        "risk_class": str(action.get("risk_class") or "unknown"),
        "side_effect_class": str(action.get("side_effect_class") or "unknown"),
        "approval_requirement": approval_requirement,
        "expiry_or_staleness": f"{expires_at}; {stale_state}",
        "idempotency_ref": idempotency_ref,
        "expected_receipt_refs": expected_receipt_refs,
        "rollback_safe_disable_posture": (
            f"{rollback_safe_disable_refs[0]}; {rollback_safe_disable_refs[1]}"
        ),
        "estimated_cost_usd": float(
            action.get("action_envelope_estimated_cost_usd")
            or action.get("estimated_cost_usd")
            or 0.0
        ),
        "max_approved_cost_usd": float(
            action.get("action_envelope_max_approved_cost_usd")
            or action.get("max_approved_cost_usd")
            or 0.0
        ),
        "provider_ref": str(
            action.get("action_envelope_provider_ref")
            or action.get("provider_ref")
            or "provider-ref:not-invoked"
        ),
        "model_profile_ref": str(
            action.get("action_envelope_model_profile_ref")
            or action.get("model_profile_ref")
            or "model-profile-ref:not-invoked"
        ),
        "input_metered_units": int(
            action.get("action_envelope_input_metered_units")
            or action.get("input_metered_units")
            or 0
        ),
        "output_metered_units": int(
            action.get("action_envelope_output_metered_units")
            or action.get("output_metered_units")
            or 0
        ),
        "total_metered_units": int(
            action.get("action_envelope_total_metered_units")
            or action.get("total_metered_units")
            or 0
        ),
        "cost_estimate_ref": str(
            action.get("action_envelope_cost_estimate_ref")
            or action.get("cost_estimate_ref")
            or "cost-estimate-ref:not-invoked"
        ),
        "captured_usage_ref": str(
            action.get("action_envelope_captured_usage_ref")
            or action.get("captured_usage_ref")
            or "usage-capture-ref:not-invoked"
        ),
        "budget_decision_ref": str(
            action.get("action_envelope_budget_decision_ref")
            or action.get("budget_decision_ref")
            or "budget-decision-ref:not-invoked"
        ),
        "cost_receipt_refs": _approval_envelope_list(
            action.get("action_envelope_cost_receipt_refs")
            or action.get("cost_receipt_refs"),
            missing_state="missing",
        ),
        "cost_blocked_state_refs": _approval_envelope_list(
            action.get("action_envelope_cost_blocked_state_refs")
            or action.get("cost_blocked_state_refs"),
            missing_state="missing",
        ),
        "cost_state_label": str(
            action.get("action_envelope_cost_state_label")
            or action.get("cost_state_label")
            or "Cost blocked"
        ),
        "provider_authority_state_label": str(
            action.get("action_envelope_provider_authority_state_label")
            or action.get("provider_authority_state_label")
            or "No provider authority"
        ),
        "unknown_paid_cost_requires_explicit_approval": bool(
            action.get("action_envelope_unknown_paid_cost_requires_explicit_approval")
            if action.get(
                "action_envelope_unknown_paid_cost_requires_explicit_approval"
            )
            is not None
            else action.get("unknown_paid_cost_requires_explicit_approval", True)
        ),
        "frontier_usage_claimed": bool(
            action.get("action_envelope_frontier_usage_claimed")
            or action.get("frontier_usage_claimed", False)
        ),
        "blocked_authority_refs": blocked_authority_refs,
        "evidence_refs": evidence_refs,
        "missing_field_states": _approval_envelope_missing_states(
            exact_scope=exact_scope,
            approval_requirement=approval_requirement,
            idempotency_ref=idempotency_ref,
            expected_receipt_refs=expected_receipt_refs,
            rollback_safe_disable_refs=rollback_safe_disable_refs,
            evidence_refs=evidence_refs,
        ),
    }


def _approval_envelope_value(value: Any, *, missing_state: str) -> str:
    if isinstance(value, str) and value:
        return value
    return missing_state


def _approval_envelope_value_for_contract(
    value: Any,
    *,
    has_contract: bool,
    approval_required: bool,
) -> str:
    if not approval_required:
        return "not_applicable"
    if not has_contract:
        return "missing"
    return _approval_envelope_value(value, missing_state="missing")


def _approval_envelope_list(value: Any, *, missing_state: str) -> list[str]:
    if isinstance(value, list):
        values = [str(item) for item in value if str(item)]
        if values:
            return values
    return [missing_state]


def _approval_envelope_missing_states(
    *,
    exact_scope: str,
    approval_requirement: str,
    idempotency_ref: str,
    expected_receipt_refs: list[str],
    rollback_safe_disable_refs: list[str],
    evidence_refs: list[str],
) -> list[str]:
    states: list[str] = []
    if exact_scope in {"missing", "unknown", "planned"}:
        states.append("exact_scope:missing")
    if approval_requirement in {"missing", "unknown", "planned"}:
        states.append("approval_requirement:missing")
    if idempotency_ref in {"missing", "unknown", "planned"}:
        states.append("idempotency_ref:missing")
    if expected_receipt_refs == ["missing"]:
        states.append("expected_receipt_refs:missing")
    if any(
        value in {"missing", "unknown", "planned"}
        for value in rollback_safe_disable_refs
    ):
        states.append("rollback_safe_disable_posture:missing")
    if evidence_refs == ["missing"]:
        states.append("evidence_refs:missing")
    return states or ["none"]


def _action_receipt_visibility_read_model(
    *,
    action: dict[str, Any],
    decision_receipts: list[dict[str, Any]],
    local_task_receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    item_ref = str(action.get("item_ref") or "founder-action:unknown")
    action_kind = str(action.get("action_kind") or "review_only")
    approval_required = bool(action.get("approval_required", True))
    latest_decision_receipt = decision_receipts[-1] if decision_receipts else None
    decision_receipt_ref = (
        str(latest_decision_receipt["receipt_ref"])
        if latest_decision_receipt and latest_decision_receipt.get("receipt_ref")
        else ("pending" if approval_required else "not_applicable")
    )
    local_task_is_relevant = action_kind == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    local_task_ref = (
        str(local_task_receipt["local_task_ref"])
        if local_task_receipt and local_task_receipt.get("local_task_ref")
        else ("pending" if local_task_is_relevant else "not_applicable")
    )
    local_task_commit_receipt_ref = (
        str(local_task_receipt["receipt_ref"])
        if local_task_receipt and local_task_receipt.get("receipt_ref")
        else ("pending" if local_task_is_relevant else "not_applicable")
    )
    evidence_timeline_event_ref = (
        str(local_task_receipt["evidence_timeline_event_ref"])
        if local_task_receipt and local_task_receipt.get("evidence_timeline_event_ref")
        else (
            _evidence_event_ref(
                "action_decision_recorded", _timeline_ref("action", item_ref)
            )
            if latest_decision_receipt
            else ("pending" if approval_required else "not_applicable")
        )
    )
    if local_task_receipt is not None:
        replay_posture = "idempotency_replay_available"
        conflict_posture = "conflicting_idempotency_payload_rejected"
    elif latest_decision_receipt is not None:
        replay_posture = "decision_idempotency_replay_available"
        conflict_posture = "decision_conflicting_idempotency_payload_rejected"
    elif approval_required:
        replay_posture = "pending"
        conflict_posture = "pending"
    else:
        replay_posture = "not_applicable"
        conflict_posture = "not_applicable"
    visibility = {
        "schema_version": "founder_loop_action_receipt_visibility.v1",
        "contract_ref": "contract-ref:founder-loop-action-receipt-visibility:v1",
        "source": "python_core_action_inbox_read_model",
        "backend_owned": True,
        "decision_receipt_ref": decision_receipt_ref,
        "local_task_ref": local_task_ref,
        "local_task_commit_receipt_ref": local_task_commit_receipt_ref,
        "evidence_timeline_event_ref": evidence_timeline_event_ref,
        "replay_posture": replay_posture,
        "conflict_posture": conflict_posture,
        "missing_field_states": _receipt_visibility_missing_states(
            decision_receipt_ref=decision_receipt_ref,
            local_task_ref=local_task_ref,
            local_task_commit_receipt_ref=local_task_commit_receipt_ref,
            evidence_timeline_event_ref=evidence_timeline_event_ref,
            replay_posture=replay_posture,
            conflict_posture=conflict_posture,
        ),
    }
    _validate_safe_payload(visibility, "action_receipt_visibility")
    return visibility


def _fusion_routing_fields_for_action(action: dict[str, Any]) -> dict[str, Any]:
    item_ref = str(action.get("item_ref") or "founder-action:unknown")
    action_kind = str(action.get("action_kind") or "review_only")
    status = str(action.get("status") or "proposed")
    blocked_refs = [
        *(action.get("blocked_state_refs") or []),
        *(action.get("action_blocked_state_refs") or []),
        *(action.get("task_decomposition_blocked_authority_refs") or []),
    ]
    if status == "blocked" or blocked_refs:
        classification = WorkClassificationValue.blocked
    elif action_kind in {"local_task_create", "review_only"}:
        classification = WorkClassificationValue.mechanical
    else:
        classification = WorkClassificationValue.judgment_required
    work_classification = build_work_classification(
        classification,
        suffix_ref=item_ref,
        source_ref=item_ref,
        evidence_ref=(
            str((action.get("evidence_refs") or ["evidence-ref:fusion:action"])[0])
        ),
        reason_ref=f"classification-reason-ref:fusion-action:{_safe_suffix(item_ref)}",
        blocked_authority_refs=blocked_refs or None,
    )
    return {
        "work_classification": work_classification.model_dump(mode="json"),
        "delegation_proposal": build_delegation_proposal(
            work_classification=work_classification,
            suffix_ref=item_ref,
        ).model_dump(mode="json"),
        "cache_context_economics": build_cache_context_economics(
            suffix_ref=item_ref,
            blocker_refs=[
                ref
                for ref in blocked_refs
                if "context" in str(ref).lower() or "cost" in str(ref).lower()
            ],
        ).model_dump(mode="json"),
    }


def _receipt_visibility_missing_states(
    *,
    decision_receipt_ref: str,
    local_task_ref: str,
    local_task_commit_receipt_ref: str,
    evidence_timeline_event_ref: str,
    replay_posture: str,
    conflict_posture: str,
) -> list[str]:
    states: list[str] = []
    for field_name, value in [
        ("decision_receipt_ref", decision_receipt_ref),
        ("local_task_ref", local_task_ref),
        ("local_task_commit_receipt_ref", local_task_commit_receipt_ref),
        ("evidence_timeline_event_ref", evidence_timeline_event_ref),
        ("replay_posture", replay_posture),
        ("conflict_posture", conflict_posture),
    ]:
        if value in {"missing", "pending", "unknown", "unavailable"}:
            states.append(f"{field_name}:{value}")
    return states or ["none"]


def _chat_local_operator_contract_payload() -> dict[str, Any]:
    envelope = build_chat_local_operator_turn_envelope(
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_evidence_refs=["evidence-ref:chat-local-operator:today"],
    )
    payload = envelope.model_dump(mode="json")
    return {
        "chat_local_operator_contract_ref": payload["contract_ref"],
        "chat_local_operator_status": "implemented_local_turn_truth_surface",
        "chat_local_operator_turn_ref": payload["turn_ref"],
        "chat_local_operator_route_ref": payload["route_ref"],
        "chat_local_operator_model_ref": payload["model_ref"],
        "chat_local_operator_runtime_truth": payload["runtime_truth"],
        "chat_local_operator_auth_truth": payload["auth_truth"],
        "chat_local_operator_tool_denial_truth": payload["tool_denial_truth"],
        "chat_local_operator_tool_denial_ref": payload["tool_denial_ref"],
        "chat_local_operator_safe_evidence_refs": payload["safe_evidence_refs"],
        "chat_local_operator_plans_handoff_ref": payload["plans_handoff_ref"],
        "chat_local_operator_actions_handoff_ref": payload["actions_handoff_ref"],
        "chat_local_operator_required_truth_fields": (
            CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS
        ),
        "chat_local_operator_required_blocked_refs": (
            CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS
        ),
        "chat_local_operator_surface_bindings": (
            chat_local_operator_surface_bindings()
        ),
        "chat_local_operator_authority_posture": (
            chat_local_operator_authority_posture()
        ),
        "chat_local_operator_blocked_state_refs": payload["blocked_state_refs"],
    }


def _governed_code_workbench_contract_payload() -> dict[str, Any]:
    proposal = build_governed_code_workbench_proposal()
    payload = proposal.model_dump(mode="json")
    return {
        "governed_code_workbench_contract_ref": payload["contract_ref"],
        "governed_code_workbench_status": (
            "implemented_reviewable_repo_local_diff_contract_apply_blocked"
        ),
        "governed_code_workbench_proposal_ref": payload["proposal_ref"],
        "governed_code_workbench_repo_scope_ref": payload["repo_scope_ref"],
        "governed_code_workbench_safe_diff_summary_ref": (
            payload["safe_diff_summary_ref"]
        ),
        "governed_code_workbench_validation_plan_ref": (payload["validation_plan_ref"]),
        "governed_code_workbench_validation_result_refs": (
            payload["validation_result_refs"]
        ),
        "governed_code_workbench_approval_requirement_ref": (
            payload["approval_requirement_ref"]
        ),
        "governed_code_workbench_expected_apply_receipt_ref": (
            payload["expected_apply_receipt_ref"]
        ),
        "governed_code_workbench_expected_rollback_receipt_ref": (
            payload["expected_rollback_receipt_ref"]
        ),
        "governed_code_workbench_evidence_refs": payload["evidence_refs"],
        "governed_code_workbench_idempotency_key_ref": (payload["idempotency_key_ref"]),
        "governed_code_workbench_work_classification": (payload["work_classification"]),
        "governed_code_workbench_delegation_proposal": (payload["delegation_proposal"]),
        "governed_code_workbench_cache_context_economics": (
            payload["cache_context_economics"]
        ),
        "governed_code_workbench_safe_summary": payload["safe_summary"],
        "governed_code_workbench_validation_plan_summary": (
            payload["validation_plan_summary"]
        ),
        "governed_code_workbench_required_ref_fields": (
            GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS
        ),
        "governed_code_workbench_required_blocked_refs": (
            GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS
        ),
        "governed_code_workbench_surface_bindings": (
            governed_code_workbench_surface_bindings()
        ),
        "governed_code_workbench_authority_posture": (
            governed_code_workbench_authority_posture()
        ),
        "governed_code_workbench_blocked_state_refs": payload["blocked_state_refs"],
    }


def _cross_surface_memory_intake_contract_payload() -> dict[str, Any]:
    proposals = [
        proposal.model_dump(mode="json")
        for proposal in cross_surface_memory_intake_proposals()
    ]
    return {
        "cross_surface_memory_intake_contract_ref": (
            CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
        ),
        "cross_surface_memory_intake_status": (
            "implemented_review_only_proposal_intake_contract"
        ),
        "cross_surface_memory_intake_required_surfaces": (
            CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
        ),
        "cross_surface_memory_intake_required_ref_fields": (
            CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS
        ),
        "cross_surface_memory_intake_required_blocked_refs": (
            CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS
        ),
        "cross_surface_memory_intake_proposal_count": len(proposals),
        "cross_surface_memory_intake_proposals": proposals,
        "cross_surface_memory_intake_surface_bindings": (
            cross_surface_memory_intake_surface_bindings()
        ),
        "cross_surface_memory_intake_authority_posture": (
            cross_surface_memory_intake_authority_posture()
        ),
        "cross_surface_memory_intake_blocked_state_refs": (
            CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS
        ),
    }


def _memory_to_loop_binding_contract_payload(
    *,
    memory_items: list[dict[str, Any]],
    cross_surface_memory_intake_contract: dict[str, Any],
) -> dict[str, Any]:
    intake_proposals = list(
        cross_surface_memory_intake_contract["cross_surface_memory_intake_proposals"]
    )
    loop_source_items = memory_items or [
        {
            "review_ref": proposal["review_queue_ref"],
            "business_memory_candidate_ref": proposal["candidate_ref"],
            "safe_summary": proposal["safe_summary"],
            "source_refs": proposal["source_refs"],
            "evidence_refs": proposal["evidence_refs"],
            "missing_contract_refs": proposal["missing_evidence_refs"],
            "correction_posture": "correction_requires_scoped_memory_write_contract",
            "rejection_posture": "rejection_is_review_state_only_until_capture_contract",
            "stale_state": proposal["stale_state"],
            "next_safe_action": proposal["next_safe_action"],
        }
        for proposal in intake_proposals[:1]
    ]
    primary = loop_source_items[0]
    memory_candidate_ref = str(
        primary.get("business_memory_candidate_ref")
        or f"business-memory-candidate:{str(primary['review_ref']).replace(':', '-')}"
    )
    review_ref = str(primary["review_ref"])
    source_refs = list(primary.get("source_refs") or ["source-ref:memory-loop:review"])
    evidence_refs = list(
        primary.get("evidence_refs") or ["evidence-ref:memory-loop:review"]
    )
    missing_evidence_refs = list(
        primary.get("missing_contract_refs")
        or ["missing-evidence-ref:memory-loop:review"]
    )
    correction_refs = [
        _status_ref(
            "correction-ref",
            str(
                primary.get("correction_posture", "correction_requires_scoped_contract")
            ),
        )
    ]
    rejected_item_refs = [
        _status_ref(
            "rejected-memory-ref",
            str(primary.get("rejection_posture", "rejection_is_review_state_only")),
        )
    ]
    follow_up_commitment_refs = [
        f"follow-up-commitment-ref:{review_ref.replace(':', '-')}"
    ]
    accepted_recall_refs = [
        f"accepted-recall-ref:not-authorized:{review_ref.replace(':', '-')}"
    ]
    stale_memory_refs = [
        _status_ref(
            "stale-memory-ref",
            str(primary.get("stale_state", "recheck_memory_refs_before_loop_use")),
        )
    ]
    state_by_surface = {
        "Today": "candidate",
        "Action Inbox": "follow_up_commitment",
        "Evidence Timeline": "missing_evidence_blocker",
        "Weekly CEO Review": "stale",
    }
    loop_items = [
        build_memory_to_loop_binding_item(
            surface=surface,
            loop_binding_state=state_by_surface[surface],
            memory_candidate_ref=memory_candidate_ref,
            review_ref=review_ref,
            safe_summary=(
                f"{surface} shows reviewed memory state as safe refs only; "
                "recall is not truth and action remains approval-bound."
            ),
            source_refs=source_refs,
            evidence_refs=evidence_refs,
            missing_evidence_refs=missing_evidence_refs,
            stale_state=str(
                primary.get("stale_state", "recheck_memory_refs_before_loop_use")
            ),
            correction_refs=(
                correction_refs if state_by_surface[surface] == "correction" else []
            ),
            rejected_item_refs=(
                rejected_item_refs if state_by_surface[surface] == "rejected" else []
            ),
            follow_up_commitment_refs=(
                follow_up_commitment_refs
                if state_by_surface[surface] == "follow_up_commitment"
                else []
            ),
            accepted_recall_refs=(
                accepted_recall_refs
                if state_by_surface[surface] == "accepted_recall"
                else []
            ),
            next_safe_action=(
                "Review memory source, evidence, stale-state, and approval posture "
                "before creating or changing any action."
            ),
        ).model_dump(mode="json")
        for surface in MEMORY_TO_LOOP_REQUIRED_SURFACES
    ]
    source_loop_item_ref = loop_items[0]["loop_item_ref"]
    source_intake_proposal_ref = (
        intake_proposals[0]["proposal_ref"] if intake_proposals else None
    )
    memory_derived_action_proposals = [
        build_memory_derived_action_proposal(
            proposal_ref=f"memory-derived-action-proposal:{review_ref.replace(':', '-')}",
            source_memory_ref=memory_candidate_ref,
            source_loop_item_ref=source_loop_item_ref,
            source_review_ref=review_ref,
            source_intake_proposal_ref=source_intake_proposal_ref,
            safe_summary=(
                "A memory-derived follow-up can be reviewed as an Action proposal; "
                "execution and approval capture remain blocked."
            ),
            source_refs=source_refs,
            provenance_refs=list(primary.get("provenance_refs") or []),
            evidence_refs=evidence_refs,
            missing_evidence_refs=missing_evidence_refs,
            next_safe_action=(
                "Review the memory-derived proposal in Action Inbox before any "
                "later scoped state-change contract."
            ),
        ).model_dump(mode="json")
    ]
    weekly_review_refs = [
        f"weekly-review-ref:{item['loop_item_ref'].replace(':', '-')}"
        for item in loop_items
    ]
    memory_derived_action_proposal_refs = [
        proposal["proposal_ref"] for proposal in memory_derived_action_proposals
    ]
    weekly_ceo_review_summary = {
        "weekly_review_ref": "weekly-review-ref:memory-to-loop-binding",
        "input_refs": [*weekly_review_refs, *source_refs],
        "decision_refs": accepted_recall_refs,
        "commitment_refs": follow_up_commitment_refs,
        "carry_forward_task_refs": memory_derived_action_proposal_refs,
        "unresolved_blocker_refs": MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
        "memory_correction_refs": correction_refs,
        "rejected_item_refs": rejected_item_refs,
        "stale_memory_refs": stale_memory_refs,
        "missing_evidence_blocker_refs": missing_evidence_refs,
        "follow_up_opportunity_refs": follow_up_commitment_refs,
        "authority_boundary": (
            "Weekly CEO Review carries memory refs forward for review only; it "
            "does not write memory, inject context, approve work, or sync accounts."
        ),
        "next_safe_action": (
            "Review carry-forward memory refs before any later action, recall, "
            "or memory-write milestone."
        ),
    }
    return {
        "memory_to_loop_binding_contract_ref": MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
        "memory_to_loop_binding_status": (
            "implemented_read_only_memory_loop_binding_contract"
        ),
        "memory_to_loop_required_surfaces": MEMORY_TO_LOOP_REQUIRED_SURFACES,
        "memory_to_loop_required_ref_fields": MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
        "memory_derived_action_required_ref_fields": (
            MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS
        ),
        "memory_to_loop_required_blocked_refs": MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
        "memory_to_loop_item_count": len(loop_items),
        "memory_to_loop_items": loop_items,
        "memory_derived_action_proposal_count": len(memory_derived_action_proposals),
        "memory_derived_action_proposals": memory_derived_action_proposals,
        "memory_candidate_refs": [memory_candidate_ref],
        "accepted_recall_refs": accepted_recall_refs,
        "correction_refs": correction_refs,
        "rejected_item_refs": rejected_item_refs,
        "follow_up_commitment_refs": follow_up_commitment_refs,
        "stale_memory_refs": stale_memory_refs,
        "missing_evidence_blocker_refs": missing_evidence_refs,
        "memory_derived_action_proposal_refs": memory_derived_action_proposal_refs,
        "memory_to_loop_surface_bindings": memory_to_loop_surface_bindings(),
        "memory_to_loop_authority_posture": memory_to_loop_authority_posture(),
        "memory_to_loop_weekly_review_refs": weekly_review_refs,
        "weekly_ceo_review_summary": weekly_ceo_review_summary,
        "memory_to_loop_blocked_state_refs": MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
    }


def _private_beta_readiness_gate_contract_payload() -> dict[str, Any]:
    gate = build_private_beta_readiness_gate()
    payload = gate.model_dump(mode="json")
    return {
        "private_beta_readiness_contract_ref": payload["contract_ref"],
        "private_beta_readiness_status": payload["status"],
        "private_beta_readiness_overall_state": payload["overall_gate_state"],
        "private_beta_readiness_evidence_packet_ref": payload["evidence_packet_ref"],
        "private_beta_readiness_window_ref": payload["readiness_window_ref"],
        "private_beta_readiness_full_strength_goal": payload["full_strength_goal"],
        "private_beta_readiness_repo_safe_scope": payload["repo_safe_scope"],
        "private_beta_readiness_blocked_authority_summary": payload[
            "blocked_authority_summary"
        ],
        "private_beta_readiness_promotion_path_refs": payload["promotion_path_refs"],
        "private_beta_readiness_product_loop_trial_script_ref": payload[
            "product_loop_trial_script_ref"
        ],
        "private_beta_readiness_private_operator_trial_ledger_ref": payload[
            "private_operator_trial_ledger_ref"
        ],
        "private_beta_readiness_required_surfaces": (
            PRIVATE_BETA_READINESS_REQUIRED_SURFACES
        ),
        "private_beta_readiness_acceptance_states": payload["acceptance_states"],
        "private_beta_readiness_acceptance_state_definitions": payload[
            "acceptance_state_definitions"
        ],
        "private_beta_readiness_required_ref_fields": (
            PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS
        ),
        "private_beta_readiness_required_blocked_refs": (
            PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS
        ),
        "private_beta_readiness_criterion_count": len(payload["criteria"]),
        "private_beta_readiness_criteria": payload["criteria"],
        "private_beta_readiness_surface_bindings": (
            private_beta_readiness_surface_bindings()
        ),
        "private_beta_readiness_authority_posture": (
            private_beta_readiness_authority_posture()
        ),
        "private_beta_readiness_blocked_state_refs": payload["blocked_state_refs"],
        "private_beta_readiness_missing_evidence_refs": (
            payload["missing_evidence_refs"]
        ),
        "private_beta_readiness_next_safe_action": payload["next_safe_action"],
        "private_beta_readiness_local_private_only": payload["local_private_only"],
        "private_beta_readiness_safe_refs_only": payload["safe_refs_only"],
        "private_beta_readiness_review_required": payload["review_required"],
        "private_beta_readiness_evidence_required": payload["evidence_required"],
        "private_beta_readiness_redaction_required": payload["redaction_required"],
        "private_beta_readiness_execution_authorized": (
            payload["private_beta_execution_authorized"]
        ),
    }


def _user_intent_understanding_contract_payload() -> dict[str, Any]:
    contract = build_user_intent_understanding_contract()
    payload = contract.model_dump(mode="json")
    return {
        "user_intent_understanding_contract_ref": payload["contract_ref"],
        "user_intent_understanding_status": payload["status"],
        "user_intent_required_surfaces": USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES,
        "user_intent_routing_decisions": USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS,
        "user_intent_required_dependency_refs": (
            USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS
        ),
        "user_intent_required_ref_fields": (
            USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS
        ),
        "user_intent_required_blocked_refs": (
            USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS
        ),
        "user_intent_proposal_count": payload["proposal_count"],
        "user_intent_proposals": payload["proposals"],
        "user_intent_surface_bindings": user_intent_understanding_surface_bindings(),
        "user_intent_authority_posture": (
            user_intent_understanding_authority_posture()
        ),
        "user_intent_blocked_state_refs": payload["blocked_state_refs"],
        "user_intent_low_confidence_policy_ref": payload["low_confidence_policy_ref"],
        "user_intent_conflict_policy_ref": payload["conflict_policy_ref"],
        "user_intent_next_safe_action": payload["next_safe_action"],
        "user_intent_review_required": payload["review_required"],
        "user_intent_safe_refs_only": payload["safe_refs_only"],
        "user_intent_evidence_required": payload["evidence_required"],
        "user_intent_low_confidence_asks_user": payload["low_confidence_asks_user"],
        "user_intent_conflicting_intent_asks_user": payload[
            "conflicting_intent_asks_user"
        ],
        "user_intent_hidden_authority_enabled": payload["hidden_authority_enabled"],
        "user_intent_action_execution_enabled": payload["action_execution_enabled"],
    }


class FounderLoopRepository:
    """Stdlib SQLite plus JSONL repository for the first Founder Loop state."""

    def __init__(
        self,
        state_dir: Path,
        *,
        seed_defaults: bool = True,
        ensure_storage: bool = True,
        read_only: bool = False,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> None:
        self.state_dir = state_dir
        self.db_path = self.state_dir / "founder_loop.sqlite3"
        self.memory_review_recall_db_path = (
            self.state_dir / "memory_review_recall.sqlite3"
        )
        self.logs_dir = self.state_dir / "logs"
        self.seed_defaults = seed_defaults
        self.read_only = read_only
        self._active_authority_leases = active_authority_leases
        if ensure_storage:
            self._ensure_storage()

    @classmethod
    def from_env(
        cls,
        *,
        seed_defaults: bool = True,
        ensure_storage: bool = True,
        read_only: bool = False,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> "FounderLoopRepository":
        configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_FOUNDER_LOOP_STATE_DIR
        return cls(
            state_dir=state_dir,
            seed_defaults=seed_defaults,
            ensure_storage=ensure_storage,
            read_only=read_only,
            active_authority_leases=active_authority_leases,
        )

    def storage_status(self) -> dict[str, Any]:
        counts = {
            "action_inbox": self._count("action_inbox"),
            "action_envelopes": self._count("action_envelopes"),
            "action_envelope_promotions": self._count("action_envelope_promotions"),
            "action_envelope_receipts": self._count("action_envelope_receipts"),
            "action_decision_events": self._count("action_decision_events"),
            "action_receipts": self._count("action_receipts"),
            "internal_approval_grants": self._count(
                "founder_loop_internal_approval_grants"
            ),
            "local_tasks": self._count("local_tasks"),
            "local_task_commit_receipts": self._count("local_task_commit_receipts"),
            "local_task_lane_postures": self._count("local_task_lane_postures"),
            "memory_review_write_lane_postures": self._count(
                "memory_review_write_lane_postures"
            ),
            "chat_turn_receipts": self._count("chat_turn_receipts"),
            "chat_handoff_receipts": self._count("chat_handoff_receipts"),
            "briefing_items": self._count("briefing_items"),
            "plan_summaries": self._count("plan_summaries"),
            "memory_review_queue": self._count("memory_review_queue"),
            "memory_review_decisions": self._count("memory_review_decisions"),
            "memory_manual_candidate_replays": self._count(
                "memory_manual_candidate_replays"
            ),
            "memory_feedback_receipts": self._count("memory_feedback_receipts"),
            "memory_context_pack_action_proposals": self._count(
                "memory_context_pack_action_proposals"
            ),
            "web_evidence_attachments": self._count("web_evidence_attachments"),
            "idempotency_keys": self._count("idempotency_keys"),
            "route_state_snapshots": self._count("route_state_snapshots"),
            "evidence_refs": self._count("evidence_refs"),
        }
        log_refs = {
            kind.value: f"founder-loop-log:{kind.value}" for kind in JsonlLogKind
        }
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "migration_version": self._schema_version(),
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "sqlite_state_ref": "founder-loop-sqlite:local-state",
            "jsonl_log_refs": log_refs,
            "counts": counts,
            "safe_refs_only": True,
            "raw_content_stored": False,
            "postgres_sync_required": False,
            "postgres_sync_status": "adapter_boundary_only",
            "backup_manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "updated_at": _utc_iso(),
        }

    def _memory_workbench_read_only_status(self) -> dict[str, Any]:
        needs_attention_refs: list[str] = []
        if self._count("memory_review_queue") > 0:
            needs_attention_refs.append("memory-workbench-attention:review-queue")
        if self._count("memory_review_decisions") > 0:
            needs_attention_refs.append("memory-workbench-attention:decision-receipts")
        return {
            "contract_ref": MEMORY_WORKBENCH_CONTRACT_REF,
            "route_ref": MEMORY_WORKBENCH_ROUTE_REF,
            "status": "read_only_status_no_recall_store_probe",
            "health": {
                "status": "read_only_status",
                "needs_attention_refs": needs_attention_refs,
                "safe_refs_only": True,
                "raw_content_stored": False,
                "recall_store_probe_performed": False,
            },
            "blocked_state_refs": [
                *list(MEMORY_WORKBENCH_BLOCKED_STATE_REFS),
                "blocked-state:morning-briefing-no-workbench-apply",
            ],
            "safe_refs_only": True,
            "read_only_status_only": True,
            "recall_store_probe_performed": False,
            "workbench_apply_enabled": False,
            "memory_write_authorized": False,
            "context_injection_authorized": False,
            "production_authority_enabled": False,
        }

    def today_summary(self, *, limit: int = 6) -> dict[str, Any]:
        actions = self.list_action_inbox(limit=limit)
        bridge_action_items = self.list_action_inbox(limit=50)
        plans = self.list_plan_summaries(limit=3)
        memory_items = self.list_memory_review_queue(limit=3)
        briefing_items = self.list_briefing_items(limit=3)
        chat_turn_receipts = self.list_chat_turn_receipts(limit=5)
        chat_handoff_receipts = self.list_chat_handoff_receipts(limit=5)
        web_evidence_attachments = self.list_web_evidence_attachments(limit=5)
        chat_to_loop_handoff_read_model = build_chat_to_loop_handoff_read_model(
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
        )
        memory_review_decisions = self.list_memory_review_decisions(limit=5)
        cross_surface_memory_intake_contract = (
            _cross_surface_memory_intake_contract_payload()
        )
        memory_to_loop_binding_contract = _memory_to_loop_binding_contract_payload(
            memory_items=memory_items,
            cross_surface_memory_intake_contract=cross_surface_memory_intake_contract,
        )
        private_beta_readiness_gate_contract = (
            _private_beta_readiness_gate_contract_payload()
        )
        user_intent_understanding_contract = (
            _user_intent_understanding_contract_payload()
        )
        evidence_timeline = self._build_evidence_timeline(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
            cross_surface_memory_intake_contract=cross_surface_memory_intake_contract,
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            private_beta_readiness_gate_contract=(private_beta_readiness_gate_contract),
            user_intent_understanding_contract=user_intent_understanding_contract,
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
            memory_review_decisions=memory_review_decisions,
            web_evidence_attachments=web_evidence_attachments,
        )
        next_safe_actions = _next_safe_actions(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
        )
        chat_local_operator_contract = _chat_local_operator_contract_payload()
        governed_code_workbench_contract = _governed_code_workbench_contract_payload()
        operator_workspace_spine_read_model = (
            build_operator_workspace_spine_read_model()
        )
        fusion_routing_delegation_read_model = (
            build_fusion_routing_delegation_read_model().model_dump(mode="json")
        )
        source_readiness = self.source_readiness(briefing_items=briefing_items)
        source_readiness_items = source_readiness["source_readiness_items"]
        source_readiness_posture = source_readiness["source_readiness_posture"]
        crm_lite_followups = _crm_lite_followups(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            memory_items=memory_items,
        )
        memory_why_shown_items = _memory_why_shown_items(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
        )
        review_queue_groups = _review_queue_groups(
            actions=actions,
            memory_items=memory_items,
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        dogfood_capture = _dogfood_capture_summary(
            actions=actions,
            memory_items=memory_items,
            briefing_items=briefing_items,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        weekly_review_narrative = _weekly_review_narrative(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            evidence_timeline=evidence_timeline,
            actions=actions,
            source_readiness_items=source_readiness_items,
            crm_lite_followups=crm_lite_followups,
            dogfood_capture=dogfood_capture,
        )
        daily_loop_summary = _daily_loop_summary(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
            source_readiness_items=source_readiness_items,
            crm_lite_followups=crm_lite_followups,
            memory_why_shown_items=memory_why_shown_items,
            review_queue_groups=review_queue_groups,
            weekly_review_narrative=weekly_review_narrative,
            dogfood_capture=dogfood_capture,
        )
        today_loop_read_model = build_today_loop_read_model(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
            evidence_timeline=evidence_timeline,
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
            memory_review_decisions=memory_review_decisions,
            crm_lite_followups=crm_lite_followups,
            source_readiness_items=source_readiness_items,
        )
        follow_up_tracker = build_follow_up_tracker_read_model(
            actions=actions,
            memory_items=memory_items,
            memory_review_decisions=memory_review_decisions,
            crm_lite_followups=crm_lite_followups,
            source_readiness_items=source_readiness_items,
            evidence_timeline=evidence_timeline,
        )
        evidence_event_refs = [
            str(event["event_ref"])
            for event in self._productized_evidence_events(evidence_timeline)
        ]
        weekly_ceo_review_v1_read_model = build_weekly_ceo_review_v1_read_model(
            weekly_review_narrative=weekly_review_narrative,
            actions=actions,
            memory_review_decisions=memory_review_decisions,
            follow_up_tracker=follow_up_tracker,
            evidence_timeline=evidence_timeline,
            source_readiness_items=source_readiness_items,
            evidence_event_refs=evidence_event_refs,
        )
        founder_loop_v1_product_proof_read_model = (
            build_founder_loop_product_proof_read_model(
                actions=actions,
                briefing_items=briefing_items,
                memory_items=memory_items,
                evidence_timeline=evidence_timeline,
                memory_review_decisions=memory_review_decisions,
                today_loop_read_model=today_loop_read_model,
                weekly_ceo_review_v1_read_model=weekly_ceo_review_v1_read_model,
                daily_loop_summary=daily_loop_summary,
                evidence_event_refs=evidence_event_refs,
            )
        )
        founder_loop_runs_integration_read_model = (
            build_founder_loop_runs_integration_read_model(
                actions=actions,
                briefing_items=briefing_items,
                memory_items=memory_items,
                evidence_timeline=evidence_timeline,
                memory_review_decisions=memory_review_decisions,
                founder_loop_product_proof_read_model=(
                    founder_loop_v1_product_proof_read_model
                ),
                weekly_ceo_review_v1_read_model=weekly_ceo_review_v1_read_model,
                evidence_event_refs=evidence_event_refs,
            )
        )
        plans_to_actions_bridge_read_model = build_plans_to_actions_bridge_read_model(
            plans=plans,
            action_items=bridge_action_items,
        )
        unified_work_thread_read_model = build_unified_work_thread_read_model(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            memory_review_decisions=memory_review_decisions,
            evidence_timeline=evidence_timeline,
            chat_to_loop_handoff_read_model=chat_to_loop_handoff_read_model,
            plans_to_actions_bridge_read_model=plans_to_actions_bridge_read_model,
            weekly_ceo_review_v1_read_model=weekly_ceo_review_v1_read_model,
            founder_loop_product_proof_read_model=(
                founder_loop_v1_product_proof_read_model
            ),
            evidence_event_refs=evidence_event_refs,
        )
        evidence_memory_loop_binding_read_model = (
            build_evidence_memory_loop_binding_read_model(
                memory_items=memory_items,
                memory_why_shown_items=memory_why_shown_items,
                memory_to_loop_items=memory_to_loop_binding_contract[
                    "memory_to_loop_items"
                ],
                memory_review_decisions=memory_review_decisions,
                evidence_timeline=evidence_timeline,
                evidence_events=self._productized_evidence_events(evidence_timeline),
                founder_loop_product_proof_read_model=(
                    founder_loop_v1_product_proof_read_model
                ),
                unified_work_thread_read_model=unified_work_thread_read_model,
            )
        )
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_partial_loop",
            "surface": "Today",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "approval_required_before_mutation": True,
            "product_spine_contract_ref": TODAY_PRODUCT_SPINE_CONTRACT_REF,
            "required_loop_surfaces": TODAY_PRODUCT_SPINE_LOOP_SURFACES,
            "required_today_signals": TODAY_PRODUCT_SPINE_REQUIRED_SIGNALS,
            "module_feed_contract": TODAY_PRODUCT_SPINE_MODULE_FEEDS,
            "module_completion_contract": {
                "visibility_requirement": (
                    "Module state must be visible in Today, Actions, Evidence, "
                    "and Memory before completion can be claimed."
                ),
                "visibility_is_sufficient_for_completion": False,
                "standalone_module_complete_allowed": False,
                "required_done_gates": [
                    "definition_of_done",
                    "schema_or_typed_contract",
                    "focused_tests",
                    "redaction_checks",
                    "policy_approval_boundary",
                    "openapi_api_manifest_when_routes_change",
                    "cli_or_repo_local_inspection_path",
                ],
            },
            "evidence_history_contract_ref": EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
            "evidence_history_required_states": list(EVIDENCE_HISTORY_GRAMMAR_KEYS),
            "evidence_history_required_questions": (
                EVIDENCE_HISTORY_GRAMMAR_REQUIRED_QUESTIONS
            ),
            "evidence_history_surface_bindings": EVIDENCE_HISTORY_SURFACE_BINDINGS,
            "memory_source_provenance_contract_ref": (
                MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
            ),
            "memory_source_required_kinds": (MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS),
            "memory_source_policy": memory_source_provenance_policy_rows(),
            "memory_source_denied_content_refs": (
                MEMORY_SOURCE_PROVENANCE_DENIED_CONTENT_REFS
            ),
            "memory_source_review_posture": (memory_source_provenance_review_posture()),
            "memory_review_decision_contract_ref": (
                MEMORY_REVIEW_DECISION_CONTRACT_REF
            ),
            "memory_review_decision_states": memory_review_decision_state_rows(),
            "memory_review_decision_required_ref_fields": (
                MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS
            ),
            "memory_review_decision_authority_posture": (
                memory_review_decision_authority_posture()
            ),
            "fcc_memory_review_decision_contract_ref": (
                FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF
            ),
            "fcc_memory_review_decision_route_refs": (
                list(MEMORY_REVIEW_DECISION_ROUTE_REFS)
            ),
            "memory_review_decision_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in memory_review_decisions
            ],
            "memory_review_decision_status": (
                "implemented_backend_decisions_receipt_backed_context_injection_blocked"
                if memory_review_decisions
                else "implemented_decision_routes_ready_no_decision_recorded"
            ),
            "business_memory_quality_contract_ref": (
                BUSINESS_MEMORY_QUALITY_CONTRACT_REF
            ),
            "business_memory_candidate_kinds": business_memory_candidate_kind_rows(),
            "business_memory_quality_states": business_memory_quality_state_rows(),
            "business_memory_required_ref_fields": (
                BUSINESS_MEMORY_REQUIRED_REF_FIELDS
            ),
            "business_memory_surface_bindings": business_memory_surface_bindings(),
            "business_memory_authority_posture": business_memory_authority_posture(),
            "business_memory_status": (
                "implemented_review_queue_safe_ref_quality_metadata_contract"
            ),
            "crm_lite_relationship_memory_contract_ref": (
                CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
            ),
            "crm_lite_relationship_authority_posture": (
                crm_lite_relationship_authority_posture()
            ),
            **cross_surface_memory_intake_contract,
            **memory_to_loop_binding_contract,
            **private_beta_readiness_gate_contract,
            **user_intent_understanding_contract,
            **chat_local_operator_contract,
            **governed_code_workbench_contract,
            "operator_workspace_spine_read_model": (
                operator_workspace_spine_read_model.model_dump(mode="json")
            ),
            "operator_workspace_spine_contract_ref": (
                operator_workspace_spine_read_model.contract_ref
            ),
            "operator_workspace_spine_status": (
                operator_workspace_spine_read_model.status
            ),
            "fusion_routing_delegation_contract_ref": (
                FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
            ),
            "fusion_routing_delegation_status": (
                "implemented_backend_owned_readability_metadata_no_execution"
            ),
            "fusion_routing_delegation_read_model": (
                fusion_routing_delegation_read_model
            ),
            "fusion_routing_delegation_surface_bindings": (
                fusion_routing_surface_bindings()
            ),
            "fusion_routing_delegation_authority_posture": (
                fusion_routing_authority_posture()
            ),
            "fusion_routing_delegation_blocked_state_refs": (
                list(FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS)
            ),
            "today_loop_tightening_contract_ref": TODAY_LOOP_TIGHTENING_CONTRACT_REF,
            "today_loop_read_model": today_loop_read_model,
            "follow_up_tracker_contract_ref": FOLLOW_UP_TRACKER_CONTRACT_REF,
            "follow_up_tracker": follow_up_tracker,
            "weekly_ceo_review_v1_contract_ref": WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
            "weekly_ceo_review_v1_read_model": weekly_ceo_review_v1_read_model,
            "founder_loop_v1_product_proof_contract_ref": (
                FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
            ),
            "founder_loop_v1_product_proof_read_model": (
                founder_loop_v1_product_proof_read_model
            ),
            "founder_loop_runs_integration_contract_ref": (
                FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF
            ),
            "founder_loop_runs_integration_read_model": (
                founder_loop_runs_integration_read_model
            ),
            "loop_trace_refs": _loop_trace_refs_from_runs_integration(
                founder_loop_runs_integration_read_model
            ),
            "plans_to_actions_bridge_contract_ref": (
                PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
            ),
            "plans_to_actions_bridge_read_model": (plans_to_actions_bridge_read_model),
            "unified_work_thread_contract_ref": UNIFIED_WORK_THREAD_CONTRACT_REF,
            "unified_work_thread_read_model": unified_work_thread_read_model,
            "evidence_memory_loop_binding_contract_ref": (
                EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF
            ),
            "evidence_memory_loop_binding_read_model": (
                evidence_memory_loop_binding_read_model
            ),
            "daily_loop_summary": daily_loop_summary,
            "source_readiness_route_ref": source_readiness["route_ref"],
            "source_readiness_items": source_readiness_items,
            "source_readiness_posture": source_readiness_posture,
            "crm_lite_followups": crm_lite_followups,
            "memory_why_shown_items": memory_why_shown_items,
            "review_queue_groups": review_queue_groups,
            "weekly_review_narrative": weekly_review_narrative,
            "dogfood_capture": dogfood_capture,
            "chat_durable_receipt_contract_ref": CHAT_DURABLE_RECEIPT_CONTRACT_REF,
            "chat_durable_receipt_route_refs": list(CHAT_DURABLE_RECEIPT_ROUTE_REFS),
            "chat_durable_receipt_status": (
                "implemented_durable_receipts_and_reviewable_handoffs_execution_blocked"
                if chat_turn_receipts or chat_handoff_receipts
                else "implemented_receipt_routes_ready_no_turn_recorded"
            ),
            "chat_to_loop_handoff_contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
            "chat_to_loop_handoff_read_model": chat_to_loop_handoff_read_model,
            "chat_turn_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in chat_turn_receipts
            ],
            "chat_handoff_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in chat_handoff_receipts
            ],
            "chat_handoff_created_refs": [
                str(receipt["created_ref"]) for receipt in chat_handoff_receipts
            ],
            "web_evidence_product_slice_contract_ref": (
                WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF
            ),
            "web_evidence_product_slice_route_ref": (
                WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF
            ),
            "web_evidence_product_slice_status": (
                "implemented_allowlisted_gateway_preview_receipts"
                if web_evidence_attachments
                else "implemented_route_ready_no_web_evidence_attached"
            ),
            "web_evidence_attachment_count": len(web_evidence_attachments),
            "web_evidence_attachment_refs": [
                str(receipt["attachment_ref"]) for receipt in web_evidence_attachments
            ],
            "web_evidence_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in web_evidence_attachments
            ],
            "web_evidence_evidence_refs": [
                str(receipt["evidence_ref"]) for receipt in web_evidence_attachments
            ],
            "web_evidence_preview_refs": [
                str(receipt["preview_ref"]) for receipt in web_evidence_attachments
            ],
            "web_evidence_host_refs": [
                str(receipt["host_ref"]) for receipt in web_evidence_attachments
            ],
            "web_evidence_audit_refs": [
                str(receipt["web_access_audit_ref"])
                for receipt in web_evidence_attachments
            ],
            "web_evidence_web_access_request_refs": [
                str(receipt["web_access_request_ref"])
                for receipt in web_evidence_attachments
            ],
            "web_evidence_proof_ref": WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
            "web_evidence_blocked_authority_refs": list(
                WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS
            ),
            "plans_action_envelope_contract_ref": PLANS_ACTION_ENVELOPE_CONTRACT_REF,
            "plans_action_envelope_review_postures": (
                plans_action_envelope_review_posture_rows()
            ),
            "plans_action_envelope_required_ref_fields": (
                PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS
            ),
            "plans_action_envelope_required_blocked_refs": (
                PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS
            ),
            "plans_action_envelope_surface_bindings": (
                plans_action_envelope_surface_bindings()
            ),
            "plans_action_envelope_authority_posture": (
                plans_action_envelope_authority_posture()
            ),
            "plans_action_envelope_status": (
                "implemented_today_to_action_envelope_vertical_slice_execution_blocked"
            ),
            "task_decomposition_proposal_contract_ref": (
                TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
            ),
            "task_decomposition_proposal_status": (
                "implemented_review_only_proposal_engine_execution_blocked"
            ),
            "task_decomposition_proposal_count": len(plans),
            "task_decomposition_action_proposal_refs": [
                str(plan["task_decomposition_action_inbox_bridge_ref"])
                for plan in plans
                if plan.get("task_decomposition_action_inbox_bridge_ref")
            ],
            "task_decomposition_required_blocked_refs": list(
                TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS
            ),
            "task_decomposition_authority_posture": {
                "review_only": True,
                "proposal_only": True,
                "safe_refs_only": True,
                "raw_content_included": False,
                "local_task_commit_eligible": False,
                "action_execution_enabled": False,
                "workflow_execution_enabled": False,
                "tool_execution_enabled": False,
                "memory_write_authorized": False,
                "context_injection_authorized": False,
                "connector_write_enabled": False,
                "shell_subprocess_execution_enabled": False,
                "browser_network_enabled": False,
                "model_provider_authority_allowed": False,
                "production_authority_enabled": False,
            },
            "priority_refs": _priority_refs(actions, briefing_items),
            "blocker_refs": _blocked_state_refs(actions, memory_items, briefing_items),
            "follow_up_refs": [
                f"follow-up-ref:{item['surface'].lower()}:{item['source_ref'].replace(':', '-')}"
                for item in next_safe_actions
            ],
            "plan_action_state": {
                "action_count": len(actions),
                "plan_count": len(plans),
                "approval_required_before_mutation": True,
                "mutating_controls_enabled": True,
                "execution_authorized": False,
                "action_envelope_contract_status": (
                    "implemented_today_promotion_and_action_decision_receipts_execution_blocked"
                ),
                "action_envelope_contract_ref": PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                "vertical_slice_contract_ref": FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
                "today_action_envelope_route_refs": list(
                    FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS
                ),
                "review_actions": list(PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS),
                "approval_grant_capture_enabled": False,
                "state_change_enabled": True,
            },
            "stale_source_posture": {
                "status": "recheck_required_before_action_or_source_use",
                "source_refresh_enabled": False,
                "connector_runtime_enabled": False,
                "stale_state_refs": [
                    *[
                        f"stale-ref:action:{str(action['item_ref']).replace(':', '-')}"
                        for action in actions
                    ],
                    *[
                        f"stale-ref:memory:{str(item['review_ref']).replace(':', '-')}"
                        for item in memory_items
                    ],
                    *[
                        f"stale-ref:briefing:{str(item['briefing_ref']).replace(':', '-')}"
                        for item in briefing_items
                    ],
                ][:12],
            },
            "next_safe_actions": next_safe_actions,
            "sections": {
                "action_inbox_count": len(actions),
                "plan_count": len(plans),
                "memory_review_count": len(memory_items),
                "briefing_count": len(briefing_items),
                "evidence_timeline_count": len(evidence_timeline),
            },
            "actions": actions,
            "plans": plans,
            "memory_review_queue": memory_items,
            "memory_review_route_ref": "/memory",
            "memory_review_backend_route_ref": "GET /control-center/memory/review",
            "memory_review_status": (
                "storage_backed_review_queue_with_backend_decision_receipts"
            ),
            "memory_review_authority_boundary": (
                "Review-only memory candidates; recall is not truth, and writes, "
                "deletes, context injection, connector writes, model/provider calls, "
                "and background sync are unscoped."
            ),
            "memory_write_enabled": False,
            "memory_delete_enabled": False,
            "context_injection_enabled": False,
            "memory_review_missing_contract_refs": [
                "contract-ref:memory-write-policy-binding-missing",
                "contract-ref:memory-retention-delete-missing",
                "contract-ref:context-injection-missing",
            ],
            "memory_review_blocked_states": [
                "no_memory_write",
                "no_context_injection",
                "no_memory_delete",
                "no_memory_export",
                "no_raw_source_display",
                "no_external_crm_write",
                "no_account_sync",
                "no_automatic_recall",
                "no_connector_write",
                "no_model_provider_authority",
                "no_background_sync",
            ],
            "briefing_items": briefing_items,
            "evidence_timeline": evidence_timeline,
            "evidence_timeline_route_ref": "/evidence",
            "evidence_timeline_backend_route_ref": "GET /control-center/evidence/timeline",
            "evidence_timeline_status": "implemented_productized_evidence_timeline_safe_refs_only",
            "evidence_timeline_productization_contract_ref": (
                EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF
            ),
            "evidence_timeline_productized_event_types": (
                list(EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES)
            ),
            "evidence_timeline_productized_group_kinds": (
                list(EVIDENCE_TIMELINE_PRODUCTIZED_GROUP_KINDS)
            ),
            "evidence_timeline_authority_boundary": (
                "Evidence Timeline is safe-ref and redacted-summary only. It does "
                "not expose raw content, grant approval, execute rollback, or confer "
                "production authority."
            ),
            "evidence_timeline_blocked_states": [
                "no_raw_evidence_display",
                "no_rollback_execution",
                "approval_refs_are_identifiers_only",
                "foundation_gate_refs_not_production_authority",
                "latency_refs_not_authority",
                "connector_source_runtime_blocked",
            ],
            "evidence_refs": ["evidence-ref:founder-loop:today-summary"],
            "blocked_states": [
                "no_action_execution_route",
                "no_approval_grant_capture_route",
                "no_connector_write_route",
                "no_shell_subprocess_execution",
                "no_runtime_model_call_route",
            ],
        }

    def evidence_timeline(self, *, limit: int = 50) -> dict[str, Any]:
        today = self.today_summary(limit=min(max(int(limit), 6), 50))
        binding_today = self.today_summary(limit=6)
        timeline = list(today["evidence_timeline"])
        events = self._productized_evidence_events(timeline)
        groups = self._productized_evidence_groups(events)
        narrative_read_model = self._evidence_timeline_narrative_read_model(
            events=events,
            groups=groups,
            narrative_items=timeline,
        )
        evidence_audit_receipt_spine = self._evidence_audit_receipt_spine(
            events=events,
            groups=groups,
            narrative_items=timeline,
        )
        event_type_counts = {
            event_type: sum(1 for event in events if event["event_type"] == event_type)
            for event_type in EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES
        }
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "contract_ref": EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF,
            "status": "implemented_productized_evidence_timeline_safe_refs_only",
            "surface": "Evidence",
            "route_ref": "GET /control-center/evidence/timeline",
            "frontend_route_ref": "/evidence",
            "source_today_route_ref": "GET /control-center/today/summary",
            "storage_ref": today["storage_ref"],
            "side_effect_class": "local_dev_workspace_only",
            "read_only": True,
            "safe_refs_only": True,
            "redacted_summaries_only": True,
            "raw_content_stored": False,
            "approval_ref_authority": False,
            "rollback_execution_enabled": False,
            "memory_truth_authority": False,
            "context_injection_authorized": False,
            "action_execution_enabled": False,
            "connector_write_enabled": False,
            "production_authority_enabled": False,
            "event_type_refs": [
                f"evidence-event-type:{event_type}"
                for event_type in EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES
            ],
            "event_types": list(EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES),
            "group_kinds": list(EVIDENCE_TIMELINE_PRODUCTIZED_GROUP_KINDS),
            "event_type_counts": event_type_counts,
            "event_count": len(events),
            "group_count": len(groups),
            "groups": groups,
            "events": events,
            "evidence_audit_receipt_spine_contract_ref": (
                EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
            ),
            "evidence_audit_receipt_spine": evidence_audit_receipt_spine,
            "narrative_contract_ref": EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF,
            "narrative_read_model": narrative_read_model,
            "operator_run_timeline": self._operator_run_timeline(
                events=events,
                groups=groups,
                narrative_items=timeline,
            ),
            "founder_loop_runs_integration_contract_ref": (
                today.get("founder_loop_runs_integration_contract_ref")
            ),
            "founder_loop_runs_integration_read_model": (
                today.get("founder_loop_runs_integration_read_model")
            ),
            "loop_trace_refs": today.get("loop_trace_refs"),
            "evidence_memory_loop_binding_contract_ref": binding_today.get(
                "evidence_memory_loop_binding_contract_ref"
            ),
            "evidence_memory_loop_binding_read_model": binding_today.get(
                "evidence_memory_loop_binding_read_model"
            ),
            "narrative_items": timeline,
            "review_answer_refs": {
                "proposed": _unique_sorted_refs(
                    ref
                    for item in timeline
                    for ref in item["history_answers"]["proposed"]["refs"]
                ),
                "decided": _unique_sorted_refs(
                    ref
                    for item in timeline
                    for key in ("approved", "happened")
                    for ref in item["history_answers"][key]["refs"]
                ),
                "changed": _unique_sorted_refs(
                    ref
                    for item in timeline
                    for ref in item["history_answers"]["changed"]["refs"]
                ),
                "denied": _unique_sorted_refs(
                    ref
                    for item in timeline
                    if item["history_answers"]["approved"]["status"] == "blocked"
                    for ref in item["history_answers"]["approved"]["refs"]
                ),
                "skipped": _unique_sorted_refs(
                    ref
                    for item in timeline
                    if "skip" in str(item.get("stale_state", "")).lower()
                    for ref in item["history_answers"]["stale"]["refs"]
                ),
                "corrected": _unique_sorted_refs(
                    ref
                    for item in timeline
                    if "correction" in str(item.get("item_kind", "")).lower()
                    or "correct" in str(item.get("title", "")).lower()
                    for ref in item["history_answers"]["changed"]["refs"]
                ),
                "blocked": _unique_sorted_refs(
                    ref
                    for item in timeline
                    for ref in item["history_answers"]["blocked"]["refs"]
                ),
                "reversible_safe_disabled": _unique_sorted_refs(
                    ref
                    for item in timeline
                    for ref in [
                        *item["history_answers"]["undoable"]["refs"],
                        *item.get("rollback_refs", []),
                        *item.get("rollback_blockers", []),
                    ]
                ),
            },
            "receipt_refs": _unique_sorted_refs(
                ref for event in events for ref in event.get("receipt_refs", [])
            ),
            "approval_refs": _unique_sorted_refs(
                ref for event in events for ref in event.get("approval_refs", [])
            ),
            "idempotency_refs": _unique_sorted_refs(
                ref for event in events for ref in event.get("idempotency_refs", [])
            ),
            "rollback_refs": _unique_sorted_refs(
                ref for event in events for ref in event.get("rollback_refs", [])
            ),
            "blocked_states": [
                "no_raw_evidence_display",
                "no_approval_ref_authority",
                "no_rollback_execution",
                "no_memory_truth_authority",
                "no_context_injection",
                "no_action_execution",
                "no_connector_write",
                "no_production_authority",
            ],
            "authority_boundary": (
                "Evidence Timeline is a read-only audit index over safe refs and "
                "redacted summaries. It does not approve, execute, roll back, "
                "inject memory into context, treat recall as truth, write "
                "connectors, or confer production authority."
            ),
        }

    def list_web_evidence_attachments(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM web_evidence_attachments
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def record_web_evidence_attachment(
        self,
        receipt: WebEvidenceProductSliceReceipt,
    ) -> dict[str, Any]:
        durable = receipt.durable_record()
        _validate_safe_payload(durable, "web_evidence_attachment")
        existing = self._web_evidence_attachment_by_request_ref(receipt.request_ref)
        if existing is not None:
            if existing["payload_fingerprint_ref"] != receipt.payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_WEB_EVIDENCE_REQUEST_CONFLICT"
                )
            return {**existing, "replayed": True}

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO web_evidence_attachments (
                    attachment_ref, request_ref, receipt_ref, evidence_ref,
                    safe_url_ref, host_ref, payload_fingerprint_ref,
                    receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.attachment_ref,
                    receipt.request_ref,
                    receipt.receipt_ref,
                    receipt.evidence_ref,
                    receipt.safe_url_ref,
                    receipt.host_ref,
                    receipt.payload_fingerprint_ref,
                    _json_dumps(durable),
                    _utc_iso(),
                ),
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": (
                    "Web evidence product slice receipt recorded as safe refs only."
                ),
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.web_access_audit_ref,
                "safe_summary": (
                    "WebAccessGateway read-only web evidence audit ref recorded."
                ),
                "evidence_refs": receipt.evidence_refs,
                "web_access_audit_summary": receipt.web_access_audit_summary,
            },
        )
        return durable

    def _web_evidence_attachment_by_request_ref(
        self,
        request_ref: str,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(request_ref, "web_evidence_request_ref")
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM web_evidence_attachments
            WHERE request_ref = ?
            LIMIT 1
            """,
            (request_ref,),
        )
        if not rows:
            return None
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def weekly_ceo_review(self, *, limit: int = 20) -> dict[str, Any]:
        today = self.today_summary(limit=min(max(int(limit), 6), 50))
        read_model = today["weekly_ceo_review_v1_read_model"]
        return {
            "schema_version": "product-loop-008-weekly-ceo-review.index.v1",
            "contract_ref": WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
            "status": read_model["status"],
            "surface": "Weekly CEO Review",
            "source_today_route_ref": "GET /control-center/today/summary",
            "source_evidence_route_ref": "GET /control-center/evidence/timeline",
            "storage_ref": today["storage_ref"],
            "side_effect_class": "local_dev_workspace_only",
            "read_only": True,
            "safe_refs_only": True,
            "safe_summary_only": True,
            "raw_content_included": False,
            "connector_read_enabled": False,
            "connector_runtime_enabled": False,
            "connector_write_enabled": False,
            "email_calendar_fetch_enabled": False,
            "live_web_enabled": False,
            "model_summary_enabled": False,
            "provider_model_call_enabled": False,
            "runtime_model_call_enabled": False,
            "automatic_memory_write_authorized": False,
            "context_injection_authorized": False,
            "action_execution_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "browser_execution_enabled": False,
            "production_claim_enabled": False,
            "production_authority_enabled": False,
            "weekly_ceo_review_v1_contract_ref": WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
            "weekly_ceo_review_v1_read_model": read_model,
            "founder_loop_runs_integration_contract_ref": (
                today.get("founder_loop_runs_integration_contract_ref")
            ),
            "founder_loop_runs_integration_read_model": (
                today.get("founder_loop_runs_integration_read_model")
            ),
            "loop_trace_refs": today.get("loop_trace_refs"),
            "evidence_refs": read_model["evidence_refs"],
            "blocked_authority_refs": read_model["blocked_authority_refs"],
            "next_safe_action": read_model["next_safe_action"],
            "authority_boundary": read_model["authority_boundary"],
        }

    def founder_loop_product_proof(self, *, limit: int = 6) -> dict[str, Any]:
        today = self.today_summary(limit=min(max(int(limit), 6), 50))
        read_model = today["founder_loop_v1_product_proof_read_model"]
        return {
            "schema_version": "founder-loop-v1-product-proof.index.v1",
            "contract_ref": FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
            "status": read_model["status"],
            "surface": "Founder Loop V1 Product Proof",
            "source_today_route_ref": "GET /control-center/today/summary",
            "source_morning_briefing_route_ref": (
                "GET /control-center/morning-briefing/summary"
            ),
            "source_evidence_route_ref": "GET /control-center/evidence/timeline",
            "storage_ref": today["storage_ref"],
            "side_effect_class": "local_dev_workspace_only",
            "read_only": True,
            "safe_refs_only": True,
            "safe_summary_only": True,
            "raw_content_included": False,
            "provider_model_call_enabled": False,
            "runtime_model_call_enabled": False,
            "a2a_runtime_dispatch_enabled": False,
            "mcp_runtime_dispatch_enabled": False,
            "browser_execution_enabled": False,
            "live_web_enabled": False,
            "connector_write_enabled": False,
            "email_calendar_send_enabled": False,
            "crm_write_enabled": False,
            "account_sync_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "background_autonomy_enabled": False,
            "memory_write_authorized": False,
            "context_injection_authorized": False,
            "public_beta_claim_enabled": False,
            "public_release_claim_enabled": False,
            "production_authority_enabled": False,
            "founder_loop_v1_product_proof_read_model": read_model,
            "founder_loop_runs_integration_contract_ref": (
                today.get("founder_loop_runs_integration_contract_ref")
            ),
            "founder_loop_runs_integration_read_model": (
                today.get("founder_loop_runs_integration_read_model")
            ),
            "loop_trace_refs": today.get("loop_trace_refs"),
            "receipt_refs": read_model["receipt_refs"],
            "evidence_refs": read_model["evidence_refs"],
            "blocked_authority_refs": read_model["blocked_authority_refs"],
            "next_safe_action": read_model["next_safe_action"],
            "authority_boundary": read_model["authority_boundary"],
        }

    def chat_to_loop_handoff(self, *, limit: int = 20) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 50))
        read_model = build_chat_to_loop_handoff_read_model(
            chat_turn_receipts=self.list_chat_turn_receipts(limit=bounded_limit),
            chat_handoff_receipts=self.list_chat_handoff_receipts(limit=bounded_limit),
        )
        return {
            "schema_version": "product-loop-009-chat-to-loop-handoff.index.v1",
            "contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
            "status": read_model["status"],
            "surface": "Chat To Loop Handoff",
            "source_today_route_ref": "GET /control-center/today/summary",
            "source_chat_route_refs": list(CHAT_DURABLE_RECEIPT_ROUTE_REFS),
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "read_only": True,
            "proposal_only": True,
            "safe_refs_only": True,
            "safe_summary_only": True,
            "raw_content_included": False,
            "chat_to_loop_handoff_contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
            "chat_to_loop_handoff_read_model": read_model,
            "evidence_refs": read_model["evidence_refs"],
            "blocked_state_refs": read_model["blocked_state_refs"],
            "next_safe_action": read_model["next_safe_action"],
        }

    def _evidence_timeline_narrative_read_model(
        self,
        *,
        events: list[dict[str, Any]],
        groups: list[dict[str, Any]],
        narrative_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        entries = (
            [self._evidence_narrative_entry_from_event(event) for event in events[:50]]
            if events
            else [
                self._evidence_narrative_entry_from_item(item)
                for item in narrative_items[:50]
            ]
        )
        model = FounderLoopEvidenceTimelineNarrativeReadModel(
            entry_count=len(entries),
            event_count=len(events),
            group_count=len(groups),
            narrative_item_count=len(narrative_items),
            entries=entries,
            narrative_refs=[entry.narrative_ref for entry in entries],
            event_refs=_unique_sorted_refs(entry.event_ref for entry in entries),
            timeline_item_refs=_unique_sorted_refs(
                entry.timeline_item_ref for entry in entries
            ),
            group_refs=_unique_sorted_refs(entry.group_ref for entry in entries),
            receipt_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.receipt_refs
            ),
            approval_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.approval_refs
            ),
            audit_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.audit_refs
            ),
            idempotency_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.idempotency_refs
            ),
            rollback_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.rollback_refs
            ),
            evidence_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.evidence_refs
            ),
            blocked_state_refs=_unique_sorted_refs(
                ref for entry in entries for ref in entry.blocked_state_refs
            ),
        )
        return model.model_dump(mode="json")

    def _evidence_narrative_entry_from_event(
        self,
        event: dict[str, Any],
    ) -> FounderLoopEvidenceNarrativeEntry:
        event_ref = str(event["event_ref"])
        timeline_item_ref = str(event["timeline_item_ref"])
        source_refs = list(event.get("source_refs") or [])
        status_refs = list(event.get("status_refs") or [])
        receipt_refs = list(event.get("receipt_refs") or [])
        approval_refs = list(event.get("approval_refs") or [])
        audit_refs = list(event.get("audit_refs") or [])
        idempotency_refs = list(event.get("idempotency_refs") or [])
        rollback_refs = list(event.get("rollback_refs") or [])
        blocked_state_refs = _safe_blocked_refs(event.get("blocked_states") or [])
        evidence_refs = _unique_sorted_refs(
            [
                event_ref,
                timeline_item_ref,
                str(event["event_type_ref"]),
                *source_refs,
                *status_refs,
                *receipt_refs,
                *audit_refs,
            ]
        )
        return FounderLoopEvidenceNarrativeEntry(
            narrative_ref=f"evidence-narrative:{_short_ref_suffix(event_ref)}",
            event_ref=event_ref,
            timeline_item_ref=timeline_item_ref,
            group_ref=str(event["group_ref"]),
            group_kind=str(event["group_kind"]),
            event_type=str(event["event_type"]),
            title=str(event["title"]),
            what_happened=_history_answer_text(
                event, "happened", "A safe evidence event was recorded."
            ),
            why_recorded=_history_answer_text(
                event, "proposed", "The event exists to make the proposal inspectable."
            ),
            approval_posture=_history_answer_text(
                event,
                "approved",
                "Approval refs are identifiers only and grant no authority.",
            ),
            change_summary=_history_answer_text(
                event, "changed", "Only review posture changed."
            ),
            remaining_blocked=_history_answer_text(
                event, "blocked", "Execution and production authority remain blocked."
            ),
            inspection_summary=(
                "Inspect event, timeline, receipt, audit, approval, idempotency, "
                "rollback, and blocker refs only."
            ),
            source_refs=source_refs,
            status_refs=status_refs,
            receipt_refs=receipt_refs,
            approval_refs=approval_refs,
            audit_refs=audit_refs,
            idempotency_refs=idempotency_refs,
            rollback_refs=rollback_refs,
            evidence_refs=evidence_refs,
            blocked_state_refs=blocked_state_refs,
            raw_content_included=bool(event.get("raw_evidence_included", False)),
            approval_ref_authority=bool(event.get("approval_ref_authority", False)),
            rollback_execution_enabled=bool(
                event.get("rollback_execution_enabled", False)
            ),
            memory_truth_authority=bool(event.get("memory_truth_authority", False)),
            context_injection_authorized=bool(
                event.get("context_injection_authorized", False)
            ),
        )

    def _evidence_narrative_entry_from_item(
        self,
        item: dict[str, Any],
    ) -> FounderLoopEvidenceNarrativeEntry:
        timeline_item_ref = str(item["timeline_item_ref"])
        event_ref = f"evidence-event:narrative:{_short_ref_suffix(timeline_item_ref)}"
        source_refs = list(item.get("source_refs") or [])
        status_refs = list(item.get("status_refs") or [])
        receipt_refs = list(item.get("receipt_refs") or [])
        approval_refs = _unique_sorted_refs(
            item.get("history_answers", {}).get("approved", {}).get("refs", [])
        )
        audit_refs = list(item.get("audit_refs") or [])
        idempotency_refs = list(item.get("idempotency_refs") or [])
        rollback_refs = list(item.get("rollback_refs") or [])
        blocked_state_refs = _safe_blocked_refs(item.get("blocked_states") or [])
        evidence_refs = _unique_sorted_refs(
            [
                event_ref,
                timeline_item_ref,
                *source_refs,
                *status_refs,
                *receipt_refs,
                *audit_refs,
            ]
        )
        return FounderLoopEvidenceNarrativeEntry(
            narrative_ref=f"evidence-narrative:{_short_ref_suffix(timeline_item_ref)}",
            event_ref=event_ref,
            timeline_item_ref=timeline_item_ref,
            group_ref=timeline_item_ref,
            group_kind="timeline_item",
            event_type=str(item["item_kind"]),
            title=str(item["title"]),
            what_happened=_history_answer_text(
                item, "happened", "A safe timeline item was recorded."
            ),
            why_recorded=_history_answer_text(
                item, "proposed", "The item exists to make the proposal inspectable."
            ),
            approval_posture=_history_answer_text(
                item,
                "approved",
                "Approval refs are identifiers only and grant no authority.",
            ),
            change_summary=_history_answer_text(
                item, "changed", "Only review posture changed."
            ),
            remaining_blocked=_history_answer_text(
                item, "blocked", "Execution and production authority remain blocked."
            ),
            inspection_summary=(
                "Inspect timeline, receipt, audit, approval, idempotency, rollback, "
                "and blocker refs only."
            ),
            source_refs=source_refs,
            status_refs=status_refs,
            receipt_refs=receipt_refs,
            approval_refs=approval_refs,
            audit_refs=audit_refs,
            idempotency_refs=idempotency_refs,
            rollback_refs=rollback_refs,
            evidence_refs=evidence_refs,
            blocked_state_refs=blocked_state_refs,
            raw_content_included=bool(item.get("raw_evidence_included", False)),
            approval_ref_authority=bool(item.get("approval_ref_authority", False)),
            rollback_execution_enabled=bool(
                item.get("rollback_execution_enabled", False)
            ),
            memory_truth_authority=bool(item.get("memory_truth_authority", False)),
            context_injection_authorized=bool(
                item.get("context_injection_authorized", False)
            ),
        )

    def _productized_evidence_events(
        self,
        timeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for item in timeline:
            if item.get("item_kind") == "receipt_audit_rollback_ref":
                action_envelope_ref = _first_ref_with_prefix(
                    [*item.get("status_refs", []), *item.get("source_refs", [])],
                    "action-envelope:",
                )
                if action_envelope_ref:
                    events.append(
                        self._productized_event(
                            item=item,
                            event_type="action_envelope_created",
                            group_kind="today_item",
                            group_ref=action_envelope_ref,
                            group_label="Today-to-Action envelope",
                        )
                    )
                action_source_ref = _first_ref_or(
                    list(item.get("source_refs") or []),
                    "founder-action:unknown",
                )
                durable_action_receipts = self._action_decision_receipts_for_item_ref(
                    action_source_ref
                )
                recorded_receipt_refs = _unique_sorted_refs(
                    [
                        *[
                            ref
                            for ref in item.get("receipt_refs", [])
                            if str(ref).startswith("receipt:founder-loop-action:")
                        ],
                        *[
                            str(receipt.get("receipt_ref"))
                            for receipt in durable_action_receipts
                            if receipt.get("receipt_ref")
                        ],
                    ]
                )
                if recorded_receipt_refs:
                    recorded_audit_refs = _unique_sorted_refs(
                        [
                            *list(item.get("audit_refs") or []),
                            *[
                                str(receipt.get("audit_ref"))
                                for receipt in durable_action_receipts
                                if receipt.get("audit_ref")
                            ],
                        ]
                    )
                    recorded_idempotency_refs = _unique_sorted_refs(
                        [
                            *list(item.get("idempotency_refs") or []),
                            *[
                                str(receipt.get("idempotency_key_ref"))
                                for receipt in durable_action_receipts
                                if receipt.get("idempotency_key_ref")
                            ],
                        ]
                    )
                    recorded_blocked_states = _unique_sorted_refs(
                        [
                            *list(item.get("blocked_states") or []),
                            *[
                                str(blocked_state)
                                for receipt in durable_action_receipts
                                for blocked_state in receipt.get(
                                    "blocked_state_refs", []
                                )
                            ],
                        ]
                    )
                    events.append(
                        self._productized_event(
                            item={
                                **item,
                                "receipt_refs": recorded_receipt_refs,
                                "audit_refs": recorded_audit_refs,
                                "idempotency_refs": recorded_idempotency_refs,
                                "blocked_states": recorded_blocked_states,
                            },
                            event_type="action_decision_recorded",
                            group_kind="action",
                            group_ref=action_source_ref,
                            group_label="Action decision receipt",
                        )
                    )
                local_task_receipt_refs = _unique_sorted_refs(
                    [
                        ref
                        for ref in item.get("receipt_refs", [])
                        if str(ref).startswith("receipt:founder-loop-local-task:")
                    ]
                )
                if local_task_receipt_refs:
                    events.append(
                        self._productized_event(
                            item={**item, "receipt_refs": local_task_receipt_refs},
                            event_type="local_task_created",
                            group_kind="action",
                            group_ref=action_source_ref,
                            group_label="Local task commit receipt",
                        )
                    )
            elif item.get("item_kind") == "chat_local_operator_turn_ref":
                chat_turn_receipt_refs = [
                    ref
                    for ref in item.get("receipt_refs", [])
                    if str(ref).startswith("receipt:chat-turn:")
                ]
                if chat_turn_receipt_refs:
                    events.append(
                        self._productized_event(
                            item={**item, "receipt_refs": chat_turn_receipt_refs},
                            event_type="chat_turn_receipt_recorded",
                            group_kind="chat_turn",
                            group_ref=_first_ref_or(
                                list(item.get("source_refs") or []),
                                "chat-turn:unknown",
                            ),
                            group_label="Chat turn receipt",
                        )
                    )
                chat_handoff_receipt_refs = [
                    ref
                    for ref in item.get("receipt_refs", [])
                    if str(ref).startswith("receipt:chat-handoff:")
                ]
                if chat_handoff_receipt_refs:
                    events.append(
                        self._productized_event(
                            item={**item, "receipt_refs": chat_handoff_receipt_refs},
                            event_type="chat_handoff_created",
                            group_kind="chat_turn",
                            group_ref=_first_ref_or(
                                list(item.get("source_refs") or []),
                                "chat-turn:unknown",
                            ),
                            group_label="Chat handoff receipt",
                        )
                    )
            elif item.get("item_kind") == "memory_review_evidence_ref":
                if item.get("receipt_refs"):
                    events.append(
                        self._productized_event(
                            item=item,
                            event_type="memory_review_decision_recorded",
                            group_kind="memory_candidate",
                            group_ref=_first_ref_or(
                                list(item.get("source_refs") or []),
                                "memory-review:unknown",
                            ),
                            group_label="Memory Review decision receipt",
                        )
                    )
            elif item.get("item_kind") == "web_evidence_attachment_ref":
                if item.get("receipt_refs"):
                    events.append(
                        self._productized_event(
                            item=item,
                            event_type="web_evidence_attached",
                            group_kind="web_evidence",
                            group_ref=_first_ref_or(
                                list(item.get("source_refs") or []),
                                "web-evidence-attachment:unknown",
                            ),
                            group_label="Web evidence attachment",
                        )
                    )
        return events

    def _productized_event(
        self,
        *,
        item: dict[str, Any],
        event_type: EvidenceTimelineProductizedEventType,
        group_kind: EvidenceTimelineProductizedGroupKind,
        group_ref: str,
        group_label: str,
    ) -> dict[str, Any]:
        timeline_item_ref = str(item["timeline_item_ref"])
        approval_refs = _unique_sorted_refs(
            item.get("history_answers", {}).get("approved", {}).get("refs", [])
            if isinstance(item.get("history_answers"), dict)
            else []
        )
        idempotency_refs = _unique_sorted_refs(item.get("idempotency_refs", []))
        event = FounderLoopEvidenceTimelineEvent(
            event_ref=_evidence_event_ref(event_type, timeline_item_ref),
            event_type=event_type,
            event_type_ref=f"evidence-event-type:{event_type}",
            group_kind=group_kind,
            group_ref=group_ref,
            group_label=group_label,
            timeline_item_ref=timeline_item_ref,
            item_kind=str(item["item_kind"]),
            title=str(item["title"]),
            safe_summary=str(item["safe_summary"]),
            history_answers=item["history_answers"],
            source_refs=list(item.get("source_refs") or []),
            status_refs=list(item.get("status_refs") or []),
            related_route_refs=[
                *list(item.get("related_route_refs") or []),
                "GET /control-center/evidence/timeline",
            ],
            receipt_refs=list(item.get("receipt_refs") or []),
            approval_refs=approval_refs,
            idempotency_refs=idempotency_refs,
            audit_refs=list(item.get("audit_refs") or []),
            rollback_refs=list(item.get("rollback_refs") or []),
            rollback_blockers=list(item.get("rollback_blockers") or []),
            blocked_states=list(item.get("blocked_states") or []),
            rollback_posture=(
                "rollback_refs_are_inspection_only_no_rollback_execution"
                if item.get("rollback_refs")
                else "rollback_not_applicable_or_not_scoped"
            ),
            authority_posture=str(item["authority_posture"]),
            redaction_status=str(item.get("redaction_status", "redacted_summary_only")),
            raw_evidence_included=bool(item.get("raw_evidence_included", False)),
            approval_ref_authority=bool(item.get("approval_ref_authority", False)),
            rollback_execution_enabled=bool(
                item.get("rollback_execution_enabled", False)
            ),
            memory_truth_authority=bool(item.get("memory_truth_authority", False)),
            context_injection_authorized=bool(
                item.get("context_injection_authorized", False)
            ),
        )
        return event.model_dump(mode="json")

    def _productized_evidence_groups(
        self,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for event in events:
            group_ref = str(event["group_ref"])
            group = groups.setdefault(
                group_ref,
                {
                    "group_ref": group_ref,
                    "group_kind": event["group_kind"],
                    "group_label": event["group_label"],
                    "event_count": 0,
                    "event_refs": [],
                    "event_types": [],
                    "receipt_refs": [],
                    "approval_refs": [],
                    "idempotency_refs": [],
                    "blocked_states": [],
                    "rollback_posture": "rollback_not_applicable_or_not_scoped",
                },
            )
            group["event_count"] += 1
            group["event_refs"].append(event["event_ref"])
            group["event_types"].append(event["event_type"])
            group["receipt_refs"].extend(event.get("receipt_refs", []))
            group["approval_refs"].extend(event.get("approval_refs", []))
            group["idempotency_refs"].extend(event.get("idempotency_refs", []))
            group["blocked_states"].extend(event.get("blocked_states", []))
            if event.get("rollback_refs"):
                group["rollback_posture"] = (
                    "rollback_refs_are_inspection_only_no_rollback_execution"
                )
        return [
            FounderLoopEvidenceTimelineGroup(
                **{
                    **group,
                    "event_refs": _unique_sorted_refs(group["event_refs"]),
                    "event_types": sorted(set(group["event_types"])),
                    "receipt_refs": _unique_sorted_refs(group["receipt_refs"]),
                    "approval_refs": _unique_sorted_refs(group["approval_refs"]),
                    "idempotency_refs": _unique_sorted_refs(group["idempotency_refs"]),
                    "blocked_states": sorted(set(group["blocked_states"])),
                }
            ).model_dump(mode="json")
            for group in groups.values()
        ]

    def _operator_run_timeline(
        self,
        *,
        events: list[dict[str, Any]],
        groups: list[dict[str, Any]],
        narrative_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        run_events = [self._operator_run_timeline_event(event) for event in events]
        state_counts = {
            state: sum(
                1 for event in run_events if event.get("operator_state") == state
            )
            for state in OPERATOR_RUN_TIMELINE_STATES
        }
        event_cost_slots = [event["cost_usage"] for event in run_events]
        estimated_total_cost = round(
            sum(
                float(slot.get("estimated_cost_usd", 0.0)) for slot in event_cost_slots
            ),
            6,
        )
        captured_total_cost = round(
            sum(float(slot.get("captured_cost_usd", 0.0)) for slot in event_cost_slots),
            6,
        )
        total_input_metered_units = sum(
            int(slot.get("input_metered_units", 0)) for slot in event_cost_slots
        )
        total_output_metered_units = sum(
            int(slot.get("output_metered_units", 0)) for slot in event_cost_slots
        )
        blocked_state_refs = _unique_sorted_refs(
            [
                "blocked-state:no-action-execution",
                "blocked-state:no-connector-write",
                "blocked-state:no-provider-model-authority",
                "blocked-state:no-provider-sdk-call",
                "blocked-state:no-runtime-model-call",
                *[
                    str(blocked_state)
                    for event in run_events
                    for blocked_state in event.get("blocked_state_refs", [])
                ],
            ]
        )
        frontier_ai_usage = FounderLoopFrontierAiUsageSummary(
            status="accounting_slots_ready_no_provider_calls",
            provider_model_authority_allowed=False,
            provider_sdk_call_enabled=False,
            runtime_model_calls_enabled=False,
            prompt_content_stored=False,
            response_content_stored=False,
            provider_exchange_content_stored=False,
            estimated_total_cost_usd=estimated_total_cost,
            captured_total_cost_usd=captured_total_cost,
            input_metered_units=total_input_metered_units,
            output_metered_units=total_output_metered_units,
            total_metered_units=(
                total_input_metered_units + total_output_metered_units
            ),
            unknown_paid_cost_requires_approval_before_routing=True,
            cost_governor_ref="core.costs.CostGovernor",
            budget_status_ref="budget-status:unknown-paid-cost-requires-approval",
            cost_event_refs=_unique_sorted_refs(
                slot.get("cost_event_ref") for slot in event_cost_slots
            )
            or ["cost-estimate-ref:pending-frontier-ai-usage"],
            cost_receipt_refs=_unique_sorted_refs(
                ref
                for slot in event_cost_slots
                for ref in slot.get("cost_receipt_refs", [])
            ),
            cost_blocked_state_refs=_unique_sorted_refs(
                ref
                for slot in event_cost_slots
                for ref in slot.get("cost_blocked_state_refs", [])
            ),
        )
        timeline = FounderLoopOperatorRunTimeline(
            status="implemented_read_only_operator_run_timeline_safe_refs_only",
            source="python_core_evidence_timeline_read_model",
            route_ref="GET /control-center/evidence/timeline",
            frontend_route_refs=[
                "/",
                "/actions",
                "/plans",
                "/memory",
                "/evidence",
                "/settings",
            ],
            safe_refs_only=True,
            redacted_summaries_only=True,
            action_execution_enabled=False,
            connector_write_enabled=False,
            runtime_model_calls_enabled=False,
            provider_sdk_call_enabled=False,
            provider_model_authority_allowed=False,
            prompt_content_stored=False,
            response_content_stored=False,
            provider_exchange_content_stored=False,
            borrowed_patterns=[
                FounderLoopOperatorRunBorrowedPattern(
                    **pattern,
                    implemented=True,
                    source_ref=f"borrowed-pattern:{pattern['pattern_id']}",
                )
                for pattern in OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS
            ],
            event_count=len(run_events),
            group_count=len(groups),
            narrative_item_count=len(narrative_items),
            run_events=run_events,
            run_control_summary=FounderLoopOperatorRunControlSummary(
                states=list(OPERATOR_RUN_TIMELINE_STATES),
                state_refs=[
                    f"operator-run-state:{state}"
                    for state in OPERATOR_RUN_TIMELINE_STATES
                ],
                waiting_for_approval_count=state_counts["waiting_for_approval"],
                receipt_recorded_count=state_counts["receipt_recorded"],
                blocked_count=state_counts["blocked"],
                needs_evidence_count=state_counts["needs_evidence"],
                stuck_detection_status=(
                    "timeline_state_counts_available_no_autonomous_resume"
                ),
                pause_resume_status="status_visible_no_runtime_pause_resume_route",
                goal_completion_status=(
                    "evidence_refs_required_no_model_judge_authority"
                ),
            ),
            frontier_ai_usage_summary=frontier_ai_usage,
            blocked_state_refs=blocked_state_refs,
            authority_boundary=(
                "Operator Run Timeline is a read-only projection over Evidence "
                "Timeline safe refs. It records state, receipt posture, and "
                "frontier AI cost accounting slots without approving work, "
                "executing actions, invoking provider SDKs, calling models, or "
                "storing prompt, response, or provider exchange content."
            ),
        )
        return timeline.model_dump(mode="json")

    def _operator_run_timeline_event(self, event: dict[str, Any]) -> dict[str, Any]:
        receipt_refs = list(event.get("receipt_refs") or [])
        approval_refs = list(event.get("approval_refs") or [])
        blocked_state_refs = _unique_sorted_refs(
            [
                (
                    str(ref)
                    if str(ref).startswith("blocked-state:")
                    else _status_ref("blocked-state", str(ref))
                )
                for ref in [
                    *list(event.get("blocked_states") or []),
                    *list(event.get("rollback_blockers") or []),
                ]
            ]
        )
        if receipt_refs:
            operator_state = "receipt_recorded"
        elif blocked_state_refs:
            operator_state = "blocked"
        elif approval_refs:
            operator_state = "waiting_for_approval"
        else:
            operator_state = "needs_evidence"
        completion_state = (
            "evidence_refs_present"
            if receipt_refs or event.get("audit_refs")
            else "needs_receipt_or_validation_evidence"
        )
        event_ref = str(event["event_ref"])
        evidence_refs = _unique_sorted_refs(
            [
                event_ref,
                str(event.get("timeline_item_ref", "")),
                *list(event.get("source_refs") or []),
                *list(event.get("status_refs") or []),
                *receipt_refs,
                *approval_refs,
                *list(event.get("audit_refs") or []),
                *list(event.get("idempotency_refs") or []),
                *list(event.get("rollback_refs") or []),
                *blocked_state_refs,
            ]
        )
        run_event = FounderLoopOperatorRunEvent(
            run_event_ref=_status_ref("operator-run-event", event_ref),
            event_ref=event_ref,
            event_kind=str(event["event_type"]),
            event_source="python_core_evidence_timeline",
            llm_role_projection="not_sent_to_model",
            operator_state=operator_state,
            approval_state=(
                "receipt_recorded"
                if receipt_refs
                else (
                    "waiting_for_approval"
                    if approval_refs
                    else "approval_not_required_or_not_scoped"
                )
            ),
            completion_state=completion_state,
            completion_claim_allowed=bool(receipt_refs),
            safe_summary=str(event["safe_summary"]),
            condensed_summary_ref=_status_ref(
                "safe-summary-ref:operator-run",
                event_ref,
            ),
            source_refs=list(event.get("source_refs") or []),
            status_refs=list(event.get("status_refs") or []),
            receipt_refs=receipt_refs,
            approval_refs=approval_refs,
            audit_refs=list(event.get("audit_refs") or []),
            idempotency_refs=list(event.get("idempotency_refs") or []),
            rollback_refs=list(event.get("rollback_refs") or []),
            blocked_state_refs=blocked_state_refs,
            evidence_refs=evidence_refs,
            related_route_refs=_unique_sorted_refs(
                [
                    *list(event.get("related_route_refs") or []),
                    "GET /control-center/evidence/timeline",
                ]
            ),
            authority_boundary=(
                "Run event is read-only evidence projection. It does not grant "
                "approval, execute actions, call models, invoke provider SDKs, "
                "or store prompt, response, or provider exchange content."
            ),
            cost_usage=self._operator_run_timeline_cost_slot(event_ref),
            prompt_content_stored=False,
            response_content_stored=False,
            provider_exchange_content_stored=False,
            provider_model_authority_allowed=False,
        )
        return run_event.model_dump(mode="json")

    def _operator_run_timeline_cost_slot(
        self,
        event_ref: str,
        *,
        estimated_cost_usd: float = 0.0,
        max_approved_cost_usd: float = 0.0,
        provider_ref: str = "provider-ref:not-invoked",
        model_profile_ref: str = "model-profile-ref:not-invoked",
        input_metered_units: int = 0,
        output_metered_units: int = 0,
        frontier_usage_claimed: bool = False,
        unknown_cost: bool = False,
    ) -> dict[str, Any]:
        return _frontier_ai_cost_slot(
            event_ref,
            estimated_cost_usd=estimated_cost_usd,
            max_approved_cost_usd=max_approved_cost_usd,
            provider_ref=provider_ref,
            model_profile_ref=model_profile_ref,
            input_metered_units=input_metered_units,
            output_metered_units=output_metered_units,
            frontier_usage_claimed=frontier_usage_claimed,
            unknown_cost=unknown_cost,
        )

    def _evidence_audit_receipt_spine(
        self,
        *,
        events: list[dict[str, Any]],
        groups: list[dict[str, Any]],
        narrative_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        envelopes = [
            self._evidence_audit_receipt_envelope(event) for event in events[:50]
        ]
        if not envelopes:
            envelopes = [
                self._evidence_audit_receipt_envelope_from_item(item)
                for item in narrative_items[:10]
            ]
        audit_groups = [
            self._evidence_audit_group(
                group_kind=group_kind,
                events=events,
                narrative_items=narrative_items,
            )
            for group_kind in EVIDENCE_AUDIT_GROUP_KINDS
        ]
        spine = FounderLoopEvidenceAuditReceiptSpine(
            route_refs=[
                "GET /control-center/evidence/timeline",
                "GET /control-center/proof/index",
                "GET /control-center/proof/{proof_ref}",
            ],
            receipt_envelope_field_refs=[
                "receipt-envelope-field:receipt-ref",
                "receipt-envelope-field:run-ref",
                "receipt-envelope-field:action-ref",
                "receipt-envelope-field:approval-ref",
                "receipt-envelope-field:side-effect-class",
                "receipt-envelope-field:authority-decision-ref",
                "receipt-envelope-field:input-ref",
                "receipt-envelope-field:output-ref",
                "receipt-envelope-field:artifact-hash-ref",
                "receipt-envelope-field:timestamp-ref",
                "receipt-envelope-field:verifier-version-ref",
                "receipt-envelope-field:redaction-status",
            ],
            timeline_group_kinds=list(EVIDENCE_AUDIT_GROUP_KINDS),
            group_count=len(audit_groups),
            envelope_count=len(envelopes),
            missing_receipt_count=len(
                _unique_sorted_refs(
                    ref
                    for envelope in envelopes
                    for ref in envelope.missing_receipt_refs
                )
            ),
            groups=audit_groups,
            receipt_envelopes=envelopes,
            receipt_refs=_unique_sorted_refs(
                envelope.receipt_ref
                for envelope in envelopes
                if envelope.receipt_recorded
            ),
            missing_receipt_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.missing_receipt_refs
            ),
            evidence_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.evidence_refs
            ),
            audit_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.audit_refs
            ),
            approval_refs=_unique_sorted_refs(
                envelope.approval_ref
                for envelope in envelopes
                if not envelope.approval_ref.startswith("approval-ref:not-")
            ),
            idempotency_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.idempotency_refs
            ),
            rollback_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.rollback_refs
            ),
            blocked_state_refs=_unique_sorted_refs(
                ref for envelope in envelopes for ref in envelope.blocked_state_refs
            ),
        )
        _ = groups
        return spine.model_dump(mode="json")

    def _evidence_audit_receipt_envelope(
        self,
        event: dict[str, Any],
    ) -> FounderLoopEvidenceAuditReceiptEnvelope:
        event_ref = str(event["event_ref"])
        receipt_refs = list(event.get("receipt_refs") or [])
        recorded_receipt_ref = (
            str(receipt_refs[0]) if receipt_refs else _missing_receipt_ref(event_ref)
        )
        receipt_recorded = bool(receipt_refs)
        approval_refs = list(event.get("approval_refs") or [])
        audit_refs = list(event.get("audit_refs") or [])
        idempotency_refs = list(event.get("idempotency_refs") or [])
        rollback_refs = list(event.get("rollback_refs") or [])
        blocked_state_refs = _safe_blocked_refs(
            [
                *list(event.get("blocked_states") or []),
                *list(event.get("rollback_blockers") or []),
            ]
        )
        artifact_hash_ref = _artifact_hash_ref("evidence-audit-envelope", event)
        evidence_refs = _unique_sorted_refs(
            [
                event_ref,
                str(event.get("timeline_item_ref", "")),
                str(event.get("event_type_ref", "")),
                *list(event.get("source_refs") or []),
                *list(event.get("status_refs") or []),
                *receipt_refs,
                *audit_refs,
                *idempotency_refs,
                *rollback_refs,
                *blocked_state_refs,
                artifact_hash_ref,
            ]
        )
        return FounderLoopEvidenceAuditReceiptEnvelope(
            envelope_ref=f"receipt-envelope:{_short_ref_suffix(event_ref)}",
            receipt_ref=recorded_receipt_ref,
            receipt_recorded=receipt_recorded,
            run_ref="run-ref:founder-loop:daily-loop-v1",
            action_ref=_first_action_ref(event),
            approval_ref=(
                str(approval_refs[0])
                if approval_refs
                else "approval-ref:not-required-or-not-scoped"
            ),
            event_ref=event_ref,
            timeline_item_ref=str(event["timeline_item_ref"]),
            group_ref=str(event["group_ref"]),
            authority_decision_ref=(
                "authority-decision-ref:receipt-recorded-read-only"
                if receipt_recorded
                else "authority-decision-ref:missing-receipt-read-only"
            ),
            input_ref=f"input-ref:redacted:{_short_ref_suffix(event_ref)}",
            output_ref=f"output-ref:redacted:{_short_ref_suffix(event_ref)}",
            artifact_hash_ref=artifact_hash_ref,
            timestamp_ref=_status_ref(
                "timestamp-ref",
                str(event.get("created_at") or "recorded"),
            ),
            verifier_version_ref="verifier-ref:runtime-evidence-audit:v1",
            safe_summary=str(event["safe_summary"]),
            route_refs=_unique_sorted_refs(
                [
                    *list(event.get("related_route_refs") or []),
                    "GET /control-center/evidence/timeline",
                ]
            ),
            evidence_refs=evidence_refs,
            audit_refs=audit_refs,
            idempotency_refs=idempotency_refs,
            rollback_refs=rollback_refs,
            blocked_state_refs=blocked_state_refs,
            missing_receipt_refs=(
                [] if receipt_recorded else [_missing_receipt_ref(event_ref)]
            ),
        )

    def _evidence_audit_receipt_envelope_from_item(
        self,
        item: dict[str, Any],
    ) -> FounderLoopEvidenceAuditReceiptEnvelope:
        event_ref = f"evidence-event:missing-receipt:{_short_ref_suffix(str(item['timeline_item_ref']))}"
        event = {
            "event_ref": event_ref,
            "event_type_ref": "evidence-event-type:timeline-item",
            "timeline_item_ref": item["timeline_item_ref"],
            "group_ref": item["timeline_item_ref"],
            "safe_summary": item["safe_summary"],
            "source_refs": list(item.get("source_refs") or []),
            "status_refs": list(item.get("status_refs") or []),
            "receipt_refs": list(item.get("receipt_refs") or []),
            "approval_refs": _unique_sorted_refs(
                item.get("history_answers", {}).get("approved", {}).get("refs", [])
            ),
            "audit_refs": list(item.get("audit_refs") or []),
            "idempotency_refs": list(item.get("idempotency_refs") or []),
            "rollback_refs": list(item.get("rollback_refs") or []),
            "blocked_states": list(item.get("blocked_states") or []),
            "rollback_blockers": list(item.get("rollback_blockers") or []),
            "related_route_refs": list(item.get("related_route_refs") or []),
            "created_at": item.get("created_at"),
        }
        return self._evidence_audit_receipt_envelope(event)

    def _evidence_audit_group(
        self,
        *,
        group_kind: EvidenceAuditGroupKind,
        events: list[dict[str, Any]],
        narrative_items: list[dict[str, Any]],
    ) -> FounderLoopEvidenceAuditGroup:
        selected_events = [
            event
            for event in events
            if _evidence_event_matches_audit_group(event, group_kind)
        ]
        selected_items = [
            item
            for item in narrative_items
            if _timeline_item_matches_audit_group(item, group_kind)
        ]
        event_refs = _unique_sorted_refs(
            event["event_ref"] for event in selected_events
        )
        timeline_item_refs = _unique_sorted_refs(
            [
                *[event["timeline_item_ref"] for event in selected_events],
                *[item["timeline_item_ref"] for item in selected_items],
            ]
        )
        receipt_refs = _unique_sorted_refs(
            [
                *[
                    ref
                    for event in selected_events
                    for ref in event.get("receipt_refs", [])
                ],
                *[
                    ref
                    for item in selected_items
                    for ref in item.get("receipt_refs", [])
                ],
            ]
        )
        missing_receipt_refs = (
            []
            if receipt_refs
            else [_missing_receipt_ref(f"evidence-audit-group:{group_kind}")]
            if selected_events or selected_items
            else []
        )
        blocked_state_refs = _unique_sorted_refs(
            [
                *_safe_blocked_refs(
                    blocked
                    for event in selected_events
                    for blocked in event.get("blocked_states", [])
                ),
                *_safe_blocked_refs(
                    blocked
                    for item in selected_items
                    for blocked in item.get("blocked_states", [])
                ),
            ]
        )
        status = (
            "receipt_refs_recorded"
            if receipt_refs
            else (
                "missing_receipt_refs_visible"
                if missing_receipt_refs
                else "not_present_in_current_timeline"
            )
        )
        definition = _evidence_audit_group_definition(group_kind)
        return FounderLoopEvidenceAuditGroup(
            group_ref=f"evidence-audit-group:{group_kind}",
            group_kind=group_kind,
            label=definition["label"],
            status=status,
            safe_summary=definition["safe_summary"],
            event_refs=event_refs,
            timeline_item_refs=timeline_item_refs,
            receipt_refs=receipt_refs,
            approval_refs=_unique_sorted_refs(
                ref
                for event in selected_events
                for ref in event.get("approval_refs", [])
            ),
            audit_refs=_unique_sorted_refs(
                [
                    *[
                        ref
                        for event in selected_events
                        for ref in event.get("audit_refs", [])
                    ],
                    *[
                        ref
                        for item in selected_items
                        for ref in item.get("audit_refs", [])
                    ],
                ]
            ),
            idempotency_refs=_unique_sorted_refs(
                [
                    *[
                        ref
                        for event in selected_events
                        for ref in event.get("idempotency_refs", [])
                    ],
                    *[
                        ref
                        for item in selected_items
                        for ref in item.get("idempotency_refs", [])
                    ],
                ]
            ),
            rollback_refs=_unique_sorted_refs(
                [
                    *[
                        ref
                        for event in selected_events
                        for ref in event.get("rollback_refs", [])
                    ],
                    *[
                        ref
                        for item in selected_items
                        for ref in item.get("rollback_refs", [])
                    ],
                ]
            ),
            evidence_refs=_unique_sorted_refs(
                [
                    *event_refs,
                    *timeline_item_refs,
                    *receipt_refs,
                    *blocked_state_refs,
                    *missing_receipt_refs,
                ]
            ),
            missing_receipt_refs=missing_receipt_refs,
            blocked_state_refs=blocked_state_refs,
            next_safe_action=definition["next_safe_action"],
        )

    def _build_evidence_timeline(
        self,
        *,
        actions: list[dict[str, Any]],
        plans: list[dict[str, Any]],
        memory_items: list[dict[str, Any]],
        briefing_items: list[dict[str, Any]],
        cross_surface_memory_intake_contract: dict[str, Any],
        memory_to_loop_binding_contract: dict[str, Any],
        private_beta_readiness_gate_contract: dict[str, Any],
        user_intent_understanding_contract: dict[str, Any],
        chat_turn_receipts: list[dict[str, Any]],
        chat_handoff_receipts: list[dict[str, Any]],
        memory_review_decisions: list[dict[str, Any]],
        web_evidence_attachments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        timeline: list[FounderLoopEvidenceTimelineItem] = []
        for action in actions:
            action_ref = str(action["item_ref"])
            action_evidence_refs = list(action.get("evidence_refs") or [])
            receipt_refs = list(action.get("receipt_refs") or [])
            audit_refs = list(action.get("audit_refs") or [])
            idempotency_refs = (
                [str(action["idempotency_key_ref"])]
                if action.get("idempotency_key_ref")
                else []
            )
            rollback_refs = (
                [action["rollback_ref"]] if action.get("rollback_ref") else []
            )
            rollback_blockers = (
                []
                if rollback_refs
                else ["rollback_refs_missing_until_scoped_state_change_contract"]
            )
            blocked_states = [
                str(value)
                for value in [
                    action.get("blocked_state"),
                    action.get("state_change_readiness"),
                ]
                if value
            ]
            approval_history_ref = action.get("approval_envelope_ref") or _status_ref(
                "approval-status",
                str(
                    action.get(
                        "approval_envelope_status", "missing_until_scoped_contract"
                    )
                ),
            )
            changed_history_ref = action.get(
                "state_change_contract_ref"
            ) or _status_ref(
                "change-status",
                str(
                    action.get(
                        "state_change_readiness", "blocked_missing_backend_contract"
                    )
                ),
            )
            action_stale_ref = _status_ref(
                "stale-ref",
                str(action.get("stale_state", "recheck_action_refs_before_use")),
            )
            blocked_history_refs = [
                _status_ref("blocked-state", value) for value in blocked_states
            ] or ["blocked-state:no-action-blockers-recorded"]
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("action", action_ref),
                    item_kind="receipt_audit_rollback_ref",
                    title=str(action["title"]),
                    safe_summary=(
                        "Action evidence is shown as receipt, audit, idempotency, "
                        "rollback, and safe-disable refs only; mutation stays blocked."
                    ),
                    history_answers=_history_answers(
                        proposed=_history_answer(
                            "proposed",
                            "A reviewed Action item was proposed from a safe summary ref with a reviewable envelope.",
                            refs=[
                                action_ref,
                                str(action.get("action_envelope_ref")),
                                PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                                "status-ref:founder-loop-action-inbox",
                                *action_evidence_refs,
                            ],
                        ),
                        approved=_history_answer(
                            "approved",
                            "Only approval posture is recorded; approval refs are identifiers, not authority.",
                            refs=[str(approval_history_ref)],
                            status="posture_only",
                        ),
                        happened=_history_answer(
                            "happened",
                            "Receipt and audit refs are available for inspection; execution remains blocked here.",
                            refs=[*receipt_refs, *audit_refs, *action_evidence_refs]
                            or ["receipt-status:missing-until-scoped-contract"],
                            status="receipt_refs_available"
                            if receipt_refs
                            else "blocked",
                        ),
                        changed=_history_answer(
                            "changed",
                            "A state-change contract or readiness posture is recorded without applying a mutation.",
                            refs=[str(changed_history_ref)],
                            status="posture_only",
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "Rollback refs describe undo posture only and do not execute rollback.",
                            refs=rollback_refs
                            or ["undo-blocker:rollback-refs-missing"],
                            status="posture_only" if rollback_refs else "blocked",
                        ),
                        stale=_history_answer(
                            "stale",
                            "The action must be rechecked before any future mutation or approval.",
                            refs=[action_stale_ref],
                            status="recheck_required",
                        ),
                        blocked=_history_answer(
                            "blocked",
                            "Mutation, approval grant capture, and execution remain blocked until a scoped contract exists.",
                            refs=blocked_history_refs,
                            status="blocked",
                        ),
                    ),
                    source_refs=[action_ref, *action_evidence_refs],
                    status_refs=[
                        "status-ref:founder-loop-action-inbox",
                        PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                        str(action.get("action_envelope_ref")),
                    ],
                    related_route_refs=[
                        "GET /control-center/actions/inbox",
                        "/actions",
                    ],
                    side_effect_class=str(
                        action.get("side_effect_class", "validation_only")
                    ),
                    authority_posture=str(action.get("authority_boundary")),
                    approval_posture=str(
                        action.get(
                            "approval_envelope_status",
                            "approval_refs_are_identifiers_only_not_authority",
                        )
                    ),
                    receipt_refs=receipt_refs,
                    audit_refs=audit_refs,
                    idempotency_refs=idempotency_refs,
                    replay_refs=["replay-ref:founder-loop:action-inbox"],
                    rollback_refs=rollback_refs,
                    rollback_blockers=rollback_blockers,
                    redaction_status="redacted_summary_only",
                    stale_state=str(
                        action.get("stale_state", "recheck_action_refs_before_use")
                    ),
                    missing_evidence_posture=(
                        "receipt_refs_available"
                        if receipt_refs
                        else "receipt_refs_missing_until_scoped_contract"
                    ),
                    blocked_states=blocked_states,
                    next_safe_action=str(action.get("next_safe_action")),
                )
            )
        for plan in plans:
            plan_ref = str(plan["plan_ref"])
            expected_receipt_refs = list(plan.get("expected_receipt_refs") or [])
            idempotency_refs = (
                [str(plan["idempotency_key_ref"])]
                if plan.get("idempotency_key_ref")
                else []
            )
            rollback_refs = [plan["rollback_ref"]] if plan.get("rollback_ref") else []
            plan_stale_ref = _status_ref(
                "stale-ref",
                str(plan.get("stale_state", "recheck-plan-envelope-before-mutation")),
            )
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("plan", plan_ref),
                    item_kind="plan_action_envelope_ref",
                    title=str(plan["title"]),
                    safe_summary=(
                        "Plan evidence includes a reviewable Action envelope ref with "
                        "exact scope, expected receipts, idempotency, rollback, and "
                        "safe-disable posture; execution remains blocked."
                    ),
                    history_answers=_history_answers(
                        proposed=_history_answer(
                            "proposed",
                            "A reviewable Action envelope was proposed from a bounded plan summary.",
                            refs=[
                                plan_ref,
                                str(plan.get("action_envelope_ref")),
                                PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                            ],
                        ),
                        approved=_history_answer(
                            "approved",
                            "No execution approval was granted; approval refs remain identifiers only.",
                            refs=[
                                str(plan.get("approval_requirement_ref")),
                                "approval-status:refs-identifiers-only",
                            ],
                            status="blocked",
                        ),
                        happened=_history_answer(
                            "happened",
                            "Only safe envelope metadata was produced; no action was executed.",
                            refs=expected_receipt_refs
                            or ["receipt-status:expected-receipts-not-created"],
                            status="inspection_only",
                        ),
                        changed=_history_answer(
                            "changed",
                            "No repo, connector, shell, model, memory, or task state changed.",
                            refs=["change-status:no-state-change-from-plan-envelope"],
                            status="not_applicable",
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "Rollback refs describe undo posture only and do not execute rollback.",
                            refs=rollback_refs
                            or ["undo-blocker:rollback-execution-not-scoped"],
                            status="blocked",
                        ),
                        stale=_history_answer(
                            "stale",
                            "Plan and envelope refs must be rechecked before any future mutation claim.",
                            refs=[plan_stale_ref],
                            status="recheck_required",
                        ),
                        blocked=_history_answer(
                            "blocked",
                            "Plan execution, approval grant capture, connector writes, shell/subprocess execution, and model/provider authority remain blocked.",
                            refs=list(plan.get("blocked_state_refs") or []),
                            status="blocked",
                        ),
                    ),
                    source_refs=[plan_ref],
                    status_refs=[
                        "status-ref:founder-loop-plan-summary",
                        PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                        str(plan.get("action_envelope_ref")),
                    ],
                    related_route_refs=["/plans", "/task-decomposition/status"],
                    side_effect_class="validation_only",
                    authority_posture=str(plan.get("authority_boundary")),
                    approval_posture=str(plan.get("approval_requirement_ref")),
                    receipt_refs=expected_receipt_refs,
                    audit_refs=[],
                    idempotency_refs=idempotency_refs,
                    replay_refs=["replay-ref:founder-loop:plan-summary"],
                    rollback_refs=rollback_refs,
                    rollback_blockers=["rollback_execution_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(plan.get("stale_state")),
                    missing_evidence_posture=(
                        "execution_receipt_missing_until_scoped_action_contract"
                    ),
                    blocked_states=list(plan.get("blocked_state_refs") or []),
                    next_safe_action=str(plan.get("next_step_summary")),
                )
            )
        chat_contract = _chat_local_operator_contract_payload()
        chat_turn_receipt_refs = [
            str(receipt["receipt_ref"]) for receipt in chat_turn_receipts
        ]
        chat_handoff_receipt_refs = [
            str(receipt["receipt_ref"]) for receipt in chat_handoff_receipts
        ]
        chat_handoff_created_refs = [
            str(receipt["created_ref"]) for receipt in chat_handoff_receipts
        ]
        chat_idempotency_refs = [
            str(receipt["idempotency_key_ref"])
            for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
            if receipt.get("idempotency_key_ref")
        ]
        chat_evidence_refs = list(
            dict.fromkeys(
                [
                    *chat_contract["chat_local_operator_safe_evidence_refs"],
                    *[
                        str(receipt["evidence_ref"])
                        for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
                        if receipt.get("evidence_ref")
                    ],
                ]
            )
        )
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "chat", chat_contract["chat_local_operator_turn_ref"]
                ),
                item_kind="chat_local_operator_turn_ref",
                title="Chat local operator surface",
                safe_summary=(
                    "Chat evidence records a redacted local operator turn, route "
                    "truth, runtime/auth posture, tool-denial posture, and "
                    "proposal handoff refs only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "A local Chat operator turn can be sent through the governed local gateway as a redacted readiness/proposal exchange.",
                        refs=[
                            chat_contract["chat_local_operator_turn_ref"],
                            CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
                            "route-ref:v1-chat-completions",
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No model output, tool use, memory write, approval grant, or action execution authority is approved by Chat output.",
                        refs=["approval-status:chat-output-not-authority"],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only safe route/runtime/auth/tool-denial evidence refs and durable receipt refs are produced; turn content is withheld from durable history.",
                        refs=[*chat_evidence_refs, *chat_turn_receipt_refs],
                        status=(
                            "receipt_recorded"
                            if chat_turn_receipt_refs
                            else "inspection_only"
                        ),
                    ),
                    changed=_history_answer(
                        "changed",
                        "Chat handoffs create reviewable Plan or Action refs only; execution, connector, memory, shell, and repo state remain unchanged.",
                        refs=[
                            chat_contract["chat_local_operator_plans_handoff_ref"],
                            chat_contract["chat_local_operator_actions_handoff_ref"],
                            *chat_handoff_created_refs,
                        ],
                        status=(
                            "reviewable_handoff_refs"
                            if chat_handoff_created_refs
                            else "proposal_refs_only"
                        ),
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "No mutation is performed, so there is no rollback execution from Chat.",
                        refs=["rollback-status:chat-no-mutation-performed"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Runtime, auth, and model readiness must be rechecked before each local turn.",
                        refs=["stale-ref:chat-local-gateway-recheck-required"],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Tools, memory writes, context injection, provider SDK calls, web fetch, connector writes, shell/subprocess execution, action execution, approval grant capture, and production authority remain blocked.",
                        refs=chat_contract["chat_local_operator_blocked_state_refs"],
                        status="blocked",
                    ),
                ),
                source_refs=[chat_contract["chat_local_operator_turn_ref"]],
                status_refs=[
                    CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
                    "route-ref:v1-chat-completions",
                    chat_contract["chat_local_operator_tool_denial_ref"],
                ],
                related_route_refs=["/chat", "/v1/chat/completions"],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Chat local operator turn evidence is safe-ref metadata only; "
                    "model output is not truth, memory, approval, or execution authority."
                ),
                approval_posture="approval-status:chat-output-not-authority",
                receipt_refs=[
                    *chat_contract["chat_local_operator_safe_evidence_refs"],
                    *chat_turn_receipt_refs,
                    *chat_handoff_receipt_refs,
                ],
                audit_refs=[
                    str(receipt["audit_ref"])
                    for receipt in chat_handoff_receipts
                    if receipt.get("audit_ref")
                ],
                idempotency_refs=chat_idempotency_refs,
                replay_refs=["replay-ref:chat-local-operator:turn"],
                rollback_refs=[],
                rollback_blockers=[
                    "rollback_execution_not_applicable_no_chat_mutation"
                ],
                redaction_status="redacted_summary_only",
                stale_state="recheck_local_gateway_before_each_turn",
                missing_evidence_posture="raw_chat_content_intentionally_hidden",
                blocked_states=chat_contract["chat_local_operator_blocked_state_refs"],
                next_safe_action=(
                    "Use Chat handoff refs as proposals only; route any work "
                    "through Plans or Actions review."
                ),
            )
        )
        code_contract = _governed_code_workbench_contract_payload()
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "code", code_contract["governed_code_workbench_proposal_ref"]
                ),
                item_kind="governed_code_workbench_proposal_ref",
                title="Governed Code workbench",
                safe_summary=(
                    "Code evidence records repo-local proposal scope, safe diff "
                    "summary refs, validation plan refs, expected apply and "
                    "rollback receipt refs, and blocked mutation posture only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "A governed Code proposal can be represented as repo-local safe refs with a validation plan.",
                        refs=[
                            code_contract["governed_code_workbench_proposal_ref"],
                            GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
                            code_contract["governed_code_workbench_repo_scope_ref"],
                            code_contract[
                                "governed_code_workbench_safe_diff_summary_ref"
                            ],
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No Code apply authority, approval grant authority, or grant capture authority is approved by this contract; approval refs remain identifiers only.",
                        refs=[
                            code_contract[
                                "governed_code_workbench_approval_requirement_ref"
                            ],
                            "approval-status:code-apply-not-authorized",
                        ],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only safe Code workbench metadata was produced; no files were changed.",
                        refs=code_contract[
                            "governed_code_workbench_validation_result_refs"
                        ],
                        status="inspection_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No repo, connector, shell, model, memory, or task state changed.",
                        refs=["change-status:no-code-apply-performed"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "Rollback receipt refs describe required undo evidence posture only and do not execute rollback.",
                        refs=[
                            code_contract[
                                "governed_code_workbench_expected_rollback_receipt_ref"
                            ]
                        ],
                        status="posture_only",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Code proposals, validation refs, and approval scope must be rechecked before any future mutation.",
                        refs=["stale-ref:governed-code-recheck-required"],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Apply execution, approval grant capture, unrestricted shell, subprocess execution, remote execution, provider calls, web fetch, connector writes, diff body storage, and production authority remain blocked.",
                        refs=code_contract[
                            "governed_code_workbench_blocked_state_refs"
                        ],
                        status="blocked",
                    ),
                ),
                source_refs=[
                    code_contract["governed_code_workbench_proposal_ref"],
                    code_contract["governed_code_workbench_repo_scope_ref"],
                ],
                status_refs=[
                    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
                    code_contract["governed_code_workbench_safe_diff_summary_ref"],
                    code_contract["governed_code_workbench_validation_plan_ref"],
                    code_contract["governed_code_workbench_expected_apply_receipt_ref"],
                ],
                related_route_refs=["/code", "GET /control-center/today/summary"],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Governed Code workbench evidence is proposal metadata only; "
                    "repo mutations require a later exact approval-bound apply contract."
                ),
                approval_posture=code_contract[
                    "governed_code_workbench_approval_requirement_ref"
                ],
                receipt_refs=[
                    code_contract["governed_code_workbench_expected_apply_receipt_ref"],
                    code_contract[
                        "governed_code_workbench_expected_rollback_receipt_ref"
                    ],
                ],
                audit_refs=code_contract["governed_code_workbench_evidence_refs"],
                replay_refs=["replay-ref:governed-code:proposal-review"],
                rollback_refs=[
                    code_contract[
                        "governed_code_workbench_expected_rollback_receipt_ref"
                    ]
                ],
                rollback_blockers=["rollback_execution_not_scoped_for_code"],
                redaction_status="redacted_summary_only",
                stale_state="recheck_code_proposal_before_any_apply",
                missing_evidence_posture="apply_receipt_missing_until_scoped_contract",
                blocked_states=code_contract[
                    "governed_code_workbench_blocked_state_refs"
                ],
                next_safe_action=(
                    "Review safe proposal refs and validation posture; require a "
                    "later exact approval-bound apply contract before mutation."
                ),
            )
        )
        fusion_read_model = build_fusion_routing_delegation_read_model().model_dump(
            mode="json"
        )
        fusion_work_refs = [
            str(item["source_refs"][0])
            for item in fusion_read_model["work_classifications"]
            if item.get("source_refs")
        ]
        fusion_receipt_refs = [
            str(ref)
            for proposal in fusion_read_model["delegation_proposals"]
            for ref in proposal.get("expected_receipt_refs", [])
        ]
        fusion_evidence_refs = [
            str(ref)
            for record in fusion_read_model["dogfood_records"]
            for ref in record.get("evidence_refs", [])
        ]
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "fusion", FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
                ),
                item_kind="fusion_routing_delegation_read_model_ref",
                title="Fusion routing and delegation visibility",
                safe_summary=(
                    "Fusion evidence records work type, route-preview reasons, "
                    "future-only delegation proposals, context/cost posture, and "
                    "private dogfood refs as review metadata only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "Work classification, route visibility, delegation proposals, and cache/context posture are available as operator review aids.",
                        refs=[
                            FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
                            *fusion_work_refs,
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No sidekick, worker, action, provider, model, shell, browser, connector, memory, or context authority is approved.",
                        refs=["approval-status:fusion-readability-not-authority"],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only backend-owned safe metadata was produced for readability; no delegation, routing execution, model call, or action happened.",
                        refs=[*fusion_receipt_refs, *fusion_evidence_refs],
                        status="inspection_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "The operator can inspect classification and route rationale; system authority and runtime state remain unchanged.",
                        refs=["change-status:fusion-readability-only"],
                        status="metadata_only",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "No mutation is performed, so rollback execution is not applicable.",
                        refs=["rollback-status:fusion-no-mutation-performed"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Classification, route, and context/cost posture must be rechecked before any later scoped execution lane.",
                        refs=["stale-ref:fusion-recheck-before-use"],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Execution, provider/model calls, background work, connector writes, memory writes, context injection, and production authority remain blocked.",
                        refs=fusion_read_model["blocked_state_refs"],
                        status="blocked",
                    ),
                ),
                source_refs=[FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF],
                status_refs=[
                    FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
                    "source-ref:fusion-routing-delegation-read-model",
                    "status-ref:fusion-routing-delegation:readability-metadata",
                ],
                related_route_refs=[
                    "GET /control-center/today/summary",
                    "GET /control-center/actions/inbox",
                    "/plans",
                    "/actions",
                    "/chat",
                    "/evidence",
                ],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Fusion metadata is review aid only; it cannot authorize "
                    "delegation, routing execution, model calls, or actions."
                ),
                approval_posture="approval-status:fusion-readability-not-authority",
                receipt_refs=fusion_receipt_refs,
                audit_refs=fusion_evidence_refs,
                replay_refs=["replay-ref:fusion-readability:metadata-only"],
                rollback_refs=[],
                rollback_blockers=["rollback_execution_not_applicable_no_mutation"],
                redaction_status="redacted_summary_only",
                stale_state="recheck_fusion_metadata_before_any_future_lane",
                missing_evidence_posture="runtime_evidence_missing_by_design",
                blocked_states=fusion_read_model["blocked_state_refs"],
                next_safe_action=(
                    "Use the readable metadata to decide review focus; keep "
                    "execution in separately scoped lanes."
                ),
            )
        )
        memory_intake_proposals = list(
            cross_surface_memory_intake_contract[
                "cross_surface_memory_intake_proposals"
            ]
        )
        memory_intake_proposal_refs = [
            str(proposal["proposal_ref"]) for proposal in memory_intake_proposals
        ]
        memory_intake_source_refs = [
            ref
            for proposal in memory_intake_proposals
            for ref in proposal.get("source_refs", [])
        ]
        memory_intake_evidence_refs = [
            ref
            for proposal in memory_intake_proposals
            for ref in proposal.get("evidence_refs", [])
        ]
        memory_intake_stale_refs = [
            _status_ref("stale-ref", str(proposal["stale_state"]))
            for proposal in memory_intake_proposals
        ]
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "memory-intake",
                    cross_surface_memory_intake_contract[
                        "cross_surface_memory_intake_contract_ref"
                    ],
                ),
                item_kind="cross_surface_memory_intake_proposal_ref",
                title="Cross-surface memory intake",
                safe_summary=(
                    "Today, Chat, Plans, Actions, Evidence, local coding, and "
                    "manual external-assistant review imports can produce reviewed "
                    "memory intake proposals with safe refs only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "Seven review-only memory intake candidates were proposed from bounded surface summaries and safe refs.",
                        refs=[
                            CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
                            *memory_intake_proposal_refs,
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No memory write authority, automatic intake authority, context injection authority, provider call authority, account fetch authority, browser import authority, or shell-history import authority is approved.",
                        refs=CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only safe memory intake proposal metadata was produced; source payloads remain hidden.",
                        refs=memory_intake_evidence_refs,
                        status="proposal_refs_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No memory record, context pack, source account, connector, repo, shell, model, or task state changed.",
                        refs=["change-status:no-memory-intake-state-change"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "There is no rollback execution because no memory mutation was performed.",
                        refs=["rollback-status:memory-intake-no-mutation"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Each intake proposal must be rechecked before a later memory review decision.",
                        refs=memory_intake_stale_refs,
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Automatic memory writes, accepted recall, context injection, provider calls, account fetch, browser import, shell-history import, raw-file import, connector runtime, and production authority remain blocked.",
                        refs=CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
                        status="blocked",
                    ),
                ),
                source_refs=memory_intake_proposal_refs + memory_intake_source_refs,
                status_refs=[
                    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
                    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
                    MEMORY_REVIEW_DECISION_CONTRACT_REF,
                    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
                ],
                related_route_refs=["GET /control-center/today/summary", "/memory"],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Cross-surface memory intake is proposal metadata only; review "
                    "is required and writes or context injection remain unscoped."
                ),
                approval_posture="approval-status:memory-intake-write-not-authorized",
                receipt_refs=[],
                audit_refs=memory_intake_evidence_refs,
                replay_refs=["replay-ref:cross-surface-memory-intake:review"],
                rollback_refs=[],
                rollback_blockers=["memory_intake_no_mutation_to_rollback"],
                redaction_status="redacted_summary_only",
                stale_state="recheck_each_intake_candidate_before_review",
                missing_evidence_posture="missing_evidence_refs_require_review",
                blocked_states=CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
                next_safe_action=(
                    "Review candidate refs in the Memory inbox before any later "
                    "memory decision milestone."
                ),
            )
        )
        memory_loop_items = list(
            memory_to_loop_binding_contract["memory_to_loop_items"]
        )
        memory_derived_actions = list(
            memory_to_loop_binding_contract["memory_derived_action_proposals"]
        )
        memory_loop_refs = [str(item["loop_item_ref"]) for item in memory_loop_items]
        memory_loop_source_refs = [
            ref for item in memory_loop_items for ref in item.get("source_refs", [])
        ]
        memory_loop_evidence_refs = [
            ref for item in memory_loop_items for ref in item.get("evidence_refs", [])
        ]
        memory_loop_missing_refs = [
            ref
            for item in memory_loop_items
            for ref in item.get("missing_evidence_refs", [])
        ]
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "memory-loop",
                    memory_to_loop_binding_contract[
                        "memory_to_loop_binding_contract_ref"
                    ],
                ),
                item_kind="memory_to_loop_binding_ref",
                title="Memory-to-loop binding",
                safe_summary=(
                    "Today, Action Inbox, Evidence Timeline, and Weekly CEO "
                    "Review show memory candidates, recall posture, corrections, "
                    "rejections, follow-up commitments, stale state, and blockers "
                    "as safe refs only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "Memory loop bindings and memory-derived Action proposals were proposed as review-only safe refs.",
                        refs=[
                            MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
                            *memory_loop_refs,
                            *[
                                proposal["proposal_ref"]
                                for proposal in memory_derived_actions
                            ],
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No memory write, accepted recall, approval grant, action execution, context injection, connector write, or production authority is approved.",
                        refs=MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only memory-to-loop binding metadata was produced for review surfaces.",
                        refs=memory_loop_evidence_refs,
                        status="safe_refs_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No memory record, action state, context pack, connector, account, model, shell, or repo state changed.",
                        refs=["change-status:no-memory-loop-state-change"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "There is no rollback execution because no loop-binding mutation was performed.",
                        refs=["rollback-status:memory-loop-no-mutation"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Memory-derived actions must recheck stale and missing-evidence refs before any later review decision.",
                        refs=[
                            *[
                                _status_ref("stale-ref", str(item["stale_state"]))
                                for item in memory_loop_items
                            ],
                            *memory_loop_missing_refs,
                        ],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Memory writes, automatic recall, context injection, approval capture, action execution, connector writes, account sync, source truth authority, and production authority remain blocked.",
                        refs=MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
                        status="blocked",
                    ),
                ),
                source_refs=memory_loop_refs + memory_loop_source_refs,
                status_refs=[
                    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
                    MEMORY_REVIEW_DECISION_CONTRACT_REF,
                    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
                    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
                ],
                related_route_refs=[
                    "GET /control-center/today/summary",
                    "GET /control-center/actions/inbox",
                    "/evidence",
                ],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Memory-to-loop binding is review-only metadata; memory "
                    "writes, recall promotion, approval capture, execution, and "
                    "context injection remain unscoped."
                ),
                approval_posture="approval-status:memory-derived-actions-not-authorized",
                receipt_refs=[],
                audit_refs=memory_loop_evidence_refs,
                replay_refs=["replay-ref:memory-to-loop-binding:review"],
                rollback_refs=[],
                rollback_blockers=["memory_loop_binding_no_mutation_to_rollback"],
                redaction_status="redacted_summary_only",
                stale_state="recheck_memory_loop_refs_before_action_review",
                missing_evidence_posture="missing_evidence_blocks_memory_derived_action",
                blocked_states=MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
                next_safe_action=(
                    "Review memory-derived Action proposal refs before any later "
                    "state-change or memory-write milestone."
                ),
            )
        )
        private_beta_criteria = list(
            private_beta_readiness_gate_contract["private_beta_readiness_criteria"]
        )
        private_beta_criterion_refs = [
            str(criterion["criterion_ref"]) for criterion in private_beta_criteria
        ]
        private_beta_evidence_refs = [
            ref
            for criterion in private_beta_criteria
            for ref in criterion.get("evidence_refs", [])
        ]
        private_beta_missing_refs = [
            *list(
                private_beta_readiness_gate_contract[
                    "private_beta_readiness_missing_evidence_refs"
                ]
            ),
            *[
                ref
                for criterion in private_beta_criteria
                for ref in criterion.get("missing_evidence_refs", [])
            ],
        ]
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "private-beta",
                    private_beta_readiness_gate_contract[
                        "private_beta_readiness_contract_ref"
                    ],
                ),
                item_kind="private_beta_readiness_gate_ref",
                title="Private beta-readiness gate",
                safe_summary=(
                    "Private local beta-test readiness is represented as "
                    "acceptance-state evidence for the founder loop surfaces; "
                    "public beta, distribution, production authority, writes, "
                    "execution, and Code apply remain blocked."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "A private local beta-test acceptance gate was proposed for the Founder Loop surfaces as safe refs only.",
                        refs=[
                            PRIVATE_BETA_READINESS_CONTRACT_REF,
                            *private_beta_criterion_refs,
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "Only the readiness evidence gate is accepted; no public beta authority, distribution authority, production readiness authority, write authority, execution authority, or broad autonomy authority is approved.",
                        refs=private_beta_readiness_gate_contract[
                            "private_beta_readiness_required_blocked_refs"
                        ],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Readiness criteria, acceptance states, missing evidence refs, and blocked authority refs were produced for review.",
                        refs=private_beta_evidence_refs,
                        status="safe_refs_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No connector, account, CRM, memory, action, Code apply, provider, shell, remote, or production state changed.",
                        refs=["change-status:no-private-beta-runtime-change"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "There is no rollback execution because the gate is read-only readiness metadata.",
                        refs=["rollback-status:private-beta-gate-no-mutation"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Readiness refs must be rechecked after each local rehearsal or API perimeter hardening milestone.",
                        refs=private_beta_missing_refs,
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Public beta, public distribution, production readiness, broad autonomy, connector writes, model/provider authority, unrestricted shell, remote execution, account sync, CRM writes, memory writes, context injection, action execution, approval grant capture, and Code apply remain blocked.",
                        refs=private_beta_readiness_gate_contract[
                            "private_beta_readiness_blocked_state_refs"
                        ],
                        status="blocked",
                    ),
                ),
                source_refs=private_beta_criterion_refs,
                status_refs=[
                    PRIVATE_BETA_READINESS_CONTRACT_REF,
                    private_beta_readiness_gate_contract[
                        "private_beta_readiness_evidence_packet_ref"
                    ],
                    private_beta_readiness_gate_contract[
                        "private_beta_readiness_window_ref"
                    ],
                ],
                related_route_refs=[
                    "GET /control-center/today/summary",
                    "GET /control-center/actions/inbox",
                    "/today",
                    "/evidence",
                    "/memory",
                ],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Private beta-readiness evidence is local safe-ref metadata "
                    "only; it does not open public beta, distribution, production "
                    "readiness, writes, execution, provider authority, or Code apply."
                ),
                approval_posture="approval-status:private-beta-gate-not-authority",
                receipt_refs=[],
                audit_refs=private_beta_evidence_refs,
                replay_refs=["replay-ref:private-beta-readiness:local-rehearsal"],
                rollback_refs=[],
                rollback_blockers=[
                    "private_beta_readiness_gate_no_mutation_to_rollback"
                ],
                redaction_status="redacted_summary_only",
                stale_state="recheck_readiness_gate_after_each_local_rehearsal",
                missing_evidence_posture=(
                    "private_beta_rehearsal_receipts_missing_until_recorded"
                ),
                blocked_states=private_beta_readiness_gate_contract[
                    "private_beta_readiness_blocked_state_refs"
                ],
                next_safe_action=private_beta_readiness_gate_contract[
                    "private_beta_readiness_next_safe_action"
                ],
            )
        )
        user_intent_proposals = list(
            user_intent_understanding_contract["user_intent_proposals"]
        )
        user_intent_proposal_refs = [
            str(proposal["proposal_ref"]) for proposal in user_intent_proposals
        ]
        user_intent_source_refs = [
            ref
            for proposal in user_intent_proposals
            for ref in proposal.get("source_refs", [])
        ]
        user_intent_evidence_refs = [
            ref
            for proposal in user_intent_proposals
            for ref in proposal.get("evidence_refs", [])
        ]
        user_intent_conflict_refs = [
            ref
            for proposal in user_intent_proposals
            for ref in proposal.get("conflict_refs", [])
        ]
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref=_timeline_ref(
                    "user-intent",
                    user_intent_understanding_contract[
                        "user_intent_understanding_contract_ref"
                    ],
                ),
                item_kind="user_intent_understanding_proposal_ref",
                title="User intent understanding",
                safe_summary=(
                    "User intent understanding produces reviewable intent "
                    "proposals with confidence, source refs, ambiguity posture, "
                    "ask/act/defer routing, and evidence refs only."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "Reviewable user intent proposals were proposed from Today, memory, evidence, Plans, Actions, Chat, and Code safe refs.",
                        refs=[
                            USER_INTENT_UNDERSTANDING_CONTRACT_REF,
                            *user_intent_proposal_refs,
                        ],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No hidden intent authority, action execution authority, approval grant authority, memory write authority, context injection authority, tool authority, provider authority, connector authority, shell authority, Code apply authority, broad autonomy authority, public beta authority, or production authority is approved.",
                        refs=user_intent_understanding_contract[
                            "user_intent_required_blocked_refs"
                        ],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Only intent proposal metadata, confidence bands, ambiguity posture, ask/act/defer routing refs, and evidence refs were produced.",
                        refs=user_intent_evidence_refs,
                        status="safe_refs_only",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No Action, Plan, Memory, context pack, Chat, Code, connector, model, shell, or production state changed.",
                        refs=["change-status:no-user-intent-state-change"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "There is no rollback execution because user intent understanding is review-only metadata.",
                        refs=["rollback-status:user-intent-no-mutation"],
                        status="not_applicable",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Intent proposals must be rechecked when memory, evidence, Action envelopes, Chat receipts, or Code receipts change.",
                        refs=[
                            "stale-ref:user-intent:memory-evidence-actions-chat-code",
                            *user_intent_conflict_refs,
                        ],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Low-confidence and conflicting intent must ask the user; hidden authority, execution, approval capture, memory writes, context injection, tool execution, provider authority, connector writes, shell execution, Code apply, broad autonomy, public beta, and production authority remain blocked.",
                        refs=user_intent_understanding_contract[
                            "user_intent_blocked_state_refs"
                        ],
                        status="blocked",
                    ),
                ),
                source_refs=user_intent_proposal_refs + user_intent_source_refs,
                status_refs=[
                    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
                    user_intent_understanding_contract[
                        "user_intent_low_confidence_policy_ref"
                    ],
                    user_intent_understanding_contract[
                        "user_intent_conflict_policy_ref"
                    ],
                ],
                related_route_refs=[
                    "GET /control-center/today/summary",
                    "GET /control-center/actions/inbox",
                    "/today",
                    "/actions",
                    "/evidence",
                    "/memory",
                ],
                side_effect_class="local_dev_workspace_only",
                authority_posture=(
                    "Intent understanding is review-only safe-ref metadata. "
                    "Ask/act/defer routing does not execute actions, capture "
                    "approval, write memory, inject context, run tools, or apply Code."
                ),
                approval_posture="approval-status:user-intent-not-authority",
                receipt_refs=[],
                audit_refs=user_intent_evidence_refs,
                replay_refs=["replay-ref:user-intent-understanding:review"],
                rollback_refs=[],
                rollback_blockers=["user_intent_no_mutation_to_rollback"],
                redaction_status="redacted_summary_only",
                stale_state="recheck_intent_proposals_before_any_routing",
                missing_evidence_posture="low_confidence_or_conflict_requires_user_question",
                blocked_states=user_intent_understanding_contract[
                    "user_intent_blocked_state_refs"
                ],
                next_safe_action=user_intent_understanding_contract[
                    "user_intent_next_safe_action"
                ],
            )
        )
        for item in memory_items:
            review_ref = str(item["review_ref"])
            candidate_ref = str(
                item.get("business_memory_candidate_ref")
                or f"business-memory-candidate:{review_ref.replace(':', '-')}"
            )
            decision_receipts = [
                receipt
                for receipt in memory_review_decisions
                if receipt.get("review_ref") == review_ref
                or receipt.get("candidate_ref") == candidate_ref
            ]
            latest_decision = decision_receipts[0] if decision_receipts else None
            decision_receipt_refs = [
                str(receipt["receipt_ref"]) for receipt in decision_receipts
            ]
            decision_audit_refs = [
                str(receipt["audit_ref"])
                for receipt in decision_receipts
                if receipt.get("audit_ref")
            ]
            decision_idempotency_refs = [
                str(receipt["idempotency_key_ref"])
                for receipt in decision_receipts
                if receipt.get("idempotency_key_ref")
            ]
            decision_evidence_refs = [
                str(ref)
                for receipt in decision_receipts
                for ref in receipt.get("evidence_refs", [])
            ]
            decision_status = (
                f"{latest_decision['decision']}_decision_receipt_recorded"
                if latest_decision
                else "no_memory_decision_captured"
            )
            missing_contract_refs = list(item.get("missing_contract_refs") or [])
            memory_stale_ref = _status_ref(
                "stale-ref",
                str(item.get("stale_state", "recheck_memory_refs_before_use")),
            )
            memory_blocked_refs = [
                _status_ref("blocked-state", str(value))
                for value in item.get("blocked_states", [])
            ] or ["blocked-state:no-memory-blockers-recorded"]
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("memory", review_ref),
                    item_kind="memory_review_evidence_ref",
                    title=str(item["title"]),
                    safe_summary=(
                        "Memory evidence is recall metadata only. Memory is not "
                        "truth, not approval, and not context-injection authority."
                    ),
                    history_answers=_history_answers(
                        proposed=_history_answer(
                            "proposed",
                            "A memory review candidate was proposed from safe source refs.",
                            refs=[review_ref, *list(item.get("source_refs") or [])],
                        ),
                        approved=_history_answer(
                            "approved",
                            "A Memory Review decision receipt records operator review state only; it does not approve context injection, connector writes, CRM sync, action execution, or production authority.",
                            refs=decision_receipt_refs
                            or [
                                "approval-status:memory-review-refs-do-not-authorize-writes"
                            ],
                            status=(
                                "decision_receipt_recorded"
                                if decision_receipt_refs
                                else "blocked"
                            ),
                        ),
                        happened=_history_answer(
                            "happened",
                            "Memory Review accept, correct, reject, defer, merge, supersede, expire, and forget-request decisions are stored as durable safe receipt refs when recorded.",
                            refs=decision_receipt_refs
                            or ["status-ref:founder-loop-memory-review"],
                            status=(
                                "receipt_recorded"
                                if decision_receipt_refs
                                else "inspection_only"
                            ),
                        ),
                        changed=_history_answer(
                            "changed",
                            "The memory review queue projection changes only to explicit review lifecycle posture such as accepted, corrected, rejected, deferred, merged, superseded, or forget-requested; raw memory content is not stored.",
                            refs=[
                                str(latest_decision.get("reviewed_recall_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision
                                and latest_decision.get("reviewed_recall_ref")
                            ]
                            or [
                                str(latest_decision.get("correction_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision
                                and latest_decision.get("correction_ref")
                            ]
                            or [
                                str(latest_decision.get("rejection_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision
                                and latest_decision.get("rejection_ref")
                            ]
                            or [
                                str(latest_decision.get("defer_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision and latest_decision.get("defer_ref")
                            ]
                            or [
                                str(latest_decision.get("merge_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision and latest_decision.get("merge_ref")
                            ]
                            or [
                                str(latest_decision.get("supersede_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision
                                and latest_decision.get("supersede_ref")
                            ]
                            or [
                                str(latest_decision.get("forget_request_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision
                                and latest_decision.get("forget_request_ref")
                            ]
                            or missing_contract_refs
                            or ["change-status:no-memory-decision-captured"],
                            status=decision_status,
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "Memory write/delete rollback is not scoped; merge, supersede, and forget-request receipts preserve refs and do not silently delete records.",
                            refs=[
                                "undo-blocker:memory-write-or-delete-rollback-not-scoped"
                            ],
                            status="blocked",
                        ),
                        stale=_history_answer(
                            "stale",
                            "Source refs must be rechecked before memory can inform future work.",
                            refs=[memory_stale_ref],
                            status="recheck_required",
                        ),
                        blocked=_history_answer(
                            "blocked",
                            "Memory writes, deletes, exports, context injection, connector writes, CRM/account sync, action execution, and model/provider authority remain blocked.",
                            refs=memory_blocked_refs,
                            status="blocked",
                        ),
                    ),
                    source_refs=[review_ref, *list(item.get("source_refs") or [])],
                    status_refs=[
                        "status-ref:founder-loop-memory-review",
                        FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
                        *decision_evidence_refs,
                        *missing_contract_refs,
                    ],
                    related_route_refs=[
                        "GET /control-center/memory/review",
                        "POST /control-center/memory/review/{candidate_ref}/accept",
                        "POST /control-center/memory/review/{candidate_ref}/correct",
                        "POST /control-center/memory/review/{candidate_ref}/reject",
                        "POST /control-center/memory/review/{candidate_ref}/defer",
                        "POST /control-center/memory/review/{candidate_ref}/merge",
                        "POST /control-center/memory/review/{candidate_ref}/supersede",
                        "POST /control-center/memory/review/{candidate_ref}/forget-request",
                        "/memory",
                    ],
                    side_effect_class=str(
                        item.get("side_effect_class", "local_dev_workspace_only")
                    ),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="memory_review_refs_do_not_authorize_writes",
                    receipt_refs=decision_receipt_refs,
                    audit_refs=decision_audit_refs,
                    idempotency_refs=decision_idempotency_refs,
                    replay_refs=["replay-ref:founder-loop:memory-review"],
                    rollback_refs=[],
                    rollback_blockers=["memory_write_or_delete_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(
                        item.get("stale_state", "recheck_memory_refs_before_use")
                    ),
                    missing_evidence_posture=(
                        "memory_contract_refs_missing_until_scoped_review_contracts"
                        if missing_contract_refs
                        else "no_missing_memory_contract_refs"
                    ),
                    blocked_states=list(item.get("blocked_states") or []),
                    next_safe_action=str(item.get("next_safe_action")),
                )
            )
        for item in briefing_items:
            briefing_ref = str(item["briefing_ref"])
            source_readiness_ref = _timeline_ref(
                "briefing-status",
                str(item.get("source_readiness", "blocked_missing_source_contract")),
            )
            briefing_stale_ref = _status_ref(
                "stale-ref",
                str(item.get("stale_state", "recheck_source_refs_before_use")),
            )
            briefing_blocked_refs = [
                _status_ref("blocked-state", str(value))
                for value in item.get("blocked_states", [])
            ] or ["blocked-state:no-briefing-blockers-recorded"]
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("briefing", briefing_ref),
                    item_kind="source_readiness_evidence_ref",
                    title=str(item["title"]),
                    safe_summary=(
                        "Briefing evidence is source-readiness posture only. Email, "
                        "calendar, connector, refresh, and notification runtime stay blocked."
                    ),
                    history_answers=_history_answers(
                        proposed=_history_answer(
                            "proposed",
                            "A briefing summary was proposed from local safe refs only.",
                            refs=[briefing_ref, *list(item.get("source_refs") or [])],
                        ),
                        approved=_history_answer(
                            "approved",
                            "Source refs do not approve connector runtime, refresh, or delivery.",
                            refs=[
                                "approval-status:source-refs-do-not-authorize-connector-runtime"
                            ],
                            status="blocked",
                        ),
                        happened=_history_answer(
                            "happened",
                            "Only source-readiness inspection happened; no email, calendar, or notification read occurred.",
                            refs=[source_readiness_ref],
                            status="inspection_only",
                        ),
                        changed=_history_answer(
                            "changed",
                            "No external source, account, connector, or notification state changed.",
                            refs=["change-status:no-source-state-change"],
                            status="not_applicable",
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "There is no source refresh or delivery mutation to undo.",
                            refs=["undo-blocker:source-refresh-rollback-not-scoped"],
                            status="blocked",
                        ),
                        stale=_history_answer(
                            "stale",
                            "Briefing source posture must be rechecked before future source use.",
                            refs=[briefing_stale_ref],
                            status="recheck_required",
                        ),
                        blocked=_history_answer(
                            "blocked",
                            "Email, calendar, connector runtime, refresh, and notification delivery remain blocked.",
                            refs=briefing_blocked_refs,
                            status="blocked",
                        ),
                    ),
                    source_refs=[briefing_ref, *list(item.get("source_refs") or [])],
                    status_refs=[source_readiness_ref],
                    related_route_refs=[
                        "GET /control-center/morning-briefing/summary",
                        "/briefing",
                    ],
                    side_effect_class=str(
                        item.get("side_effect_class", "local_dev_workspace_only")
                    ),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="source_refs_do_not_authorize_connector_runtime",
                    receipt_refs=[],
                    audit_refs=[],
                    replay_refs=["replay-ref:founder-loop:morning-briefing"],
                    rollback_refs=[],
                    rollback_blockers=["source_refresh_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(
                        item.get("stale_state", "recheck_source_refs_before_use")
                    ),
                    missing_evidence_posture=str(item.get("evidence_gap")),
                    blocked_states=list(item.get("blocked_states") or []),
                    next_safe_action=str(item.get("next_safe_action")),
                )
            )
        for attachment in web_evidence_attachments:
            attachment_ref = str(attachment["attachment_ref"])
            receipt_ref = str(attachment["receipt_ref"])
            evidence_ref = str(attachment["evidence_ref"])
            host_ref = str(attachment["host_ref"])
            preview_ref = str(attachment["preview_ref"])
            web_access_request_ref = str(attachment["web_access_request_ref"])
            web_access_audit_ref = str(attachment["web_access_audit_ref"])
            payload_fingerprint_ref = str(attachment["payload_fingerprint_ref"])
            rollback_refs = list(attachment.get("rollback_refs") or [])
            safe_disable_refs = list(attachment.get("safe_disable_refs") or [])
            blocked_refs = list(
                attachment.get("blocked_authority_refs")
                or WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS
            )
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("web-evidence", attachment_ref),
                    item_kind="web_evidence_attachment_ref",
                    title="Web evidence preview attached",
                    safe_summary=(
                        "One allowlisted HTTPS GET preview was fetched through "
                        "WebAccessGateway and attached as safe refs. Page text is "
                        "omitted from durable loop, proof, and timeline records."
                    ),
                    history_answers=_history_answers(
                        proposed=_history_answer(
                            "proposed",
                            "An operator requested one allowlisted read-only web evidence preview.",
                            refs=[
                                str(attachment["request_ref"]),
                                WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
                                host_ref,
                                preview_ref,
                            ],
                        ),
                        approved=_history_answer(
                            "approved",
                            "Tier 1 read-only preview does not require action approval and does not approve browser, connector, provider, context, memory, or production authority.",
                            refs=[
                                "approval-status:web-evidence-tier-1-no-action-approval-required",
                                WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
                            ],
                            status="not_required",
                        ),
                        happened=_history_answer(
                            "happened",
                            "WebAccessGateway returned a bounded redacted preview and recorded receipt and audit refs.",
                            refs=[
                                receipt_ref,
                                evidence_ref,
                                web_access_request_ref,
                                web_access_audit_ref,
                            ],
                            status="receipt_recorded",
                        ),
                        changed=_history_answer(
                            "changed",
                            "Only local receipt metadata changed; external web, connector, memory, provider, shell, and production state did not change.",
                            refs=[
                                "change-status:web-evidence-local-receipt-only",
                                payload_fingerprint_ref,
                            ],
                            status="local_receipt_only",
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "Rollback is represented as local receipt suppression posture only.",
                            refs=rollback_refs
                            or [WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF],
                            status="posture_only",
                        ),
                        stale=_history_answer(
                            "stale",
                            "Fetched web evidence must be rechecked before future reliance.",
                            refs=["stale-ref:recheck-web-evidence-before-use"],
                            status="recheck_required",
                        ),
                        blocked=_history_answer(
                            "blocked",
                            "Browser actions, session state, downloads, uploads, mutation methods, context injection, memory writes, connector writes, model calls, and production authority remain blocked.",
                            refs=blocked_refs,
                            status="blocked",
                        ),
                    ),
                    source_refs=[
                        attachment_ref,
                        evidence_ref,
                        host_ref,
                        preview_ref,
                        web_access_request_ref,
                        web_access_audit_ref,
                    ],
                    status_refs=[
                        WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
                        WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
                        payload_fingerprint_ref,
                        "status-ref:web-evidence-product-slice:preview-attached",
                    ],
                    related_route_refs=[
                        WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
                        "GET /control-center/evidence/timeline",
                        "/evidence",
                        "/proof",
                    ],
                    side_effect_class="governed_network_read_only",
                    authority_posture=str(attachment["authority_posture"]),
                    approval_posture="tier_1_local_read_preview_no_action_approval_required",
                    receipt_refs=[receipt_ref],
                    audit_refs=[web_access_audit_ref],
                    idempotency_refs=[payload_fingerprint_ref],
                    replay_refs=["replay-ref:web-evidence-product-slice"],
                    rollback_refs=rollback_refs,
                    safe_disable_refs=safe_disable_refs,
                    rollback_blockers=["rollback_is_local_receipt_suppression_only"],
                    redaction_status=str(attachment["redaction_posture_ref"]),
                    stale_state="recheck_web_evidence_before_future_reliance",
                    missing_evidence_posture="receipt_and_audit_refs_available",
                    blocked_states=blocked_refs,
                    next_safe_action=str(attachment["next_safe_action"]),
                )
            )
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref="evidence-timeline:foundation-gate/latency",
                item_kind="foundation_gate_latency_ref",
                title="Foundation Gate and latency posture",
                safe_summary=(
                    "Foundation Gate and latency refs are status evidence only; "
                    "they do not grant production authority or runtime authority."
                ),
                history_answers=_history_answers(
                    proposed=_history_answer(
                        "proposed",
                        "Foundation Gate and latency refs were proposed as status evidence for release review.",
                        refs=["status-ref:foundation-gate-summary"],
                    ),
                    approved=_history_answer(
                        "approved",
                        "No production, release, or runtime authority is approved by these refs.",
                        refs=[
                            "approval-status:foundation-gate-refs-not-production-authority"
                        ],
                        status="blocked",
                    ),
                    happened=_history_answer(
                        "happened",
                        "Foundation Gate and latency status refs are inspectable as evidence only.",
                        refs=[
                            "foundation-gate-ref:latest-report",
                            "latency-ref:foundation-gate:latest-report",
                        ],
                        status="status_available",
                    ),
                    changed=_history_answer(
                        "changed",
                        "No release, runtime, connector, memory, or provider state changed.",
                        refs=["change-status:no-release-state-change"],
                        status="not_applicable",
                    ),
                    undoable=_history_answer(
                        "undoable",
                        "There is no production release mutation to undo in this timeline item.",
                        refs=["undo-blocker:rollback-execution-not-scoped"],
                        status="blocked",
                    ),
                    stale=_history_answer(
                        "stale",
                        "Reports must be rechecked before any future release or readiness claim.",
                        refs=[
                            "stale-ref:recheck-foundation-gate-report-before-release-claim"
                        ],
                        status="recheck_required",
                    ),
                    blocked=_history_answer(
                        "blocked",
                        "Production, release, and runtime authority claims remain blocked.",
                        refs=[
                            "blocked-state:foundation-gate-refs-not-production-authority",
                            "blocked-state:latency-refs-not-authority",
                            "blocked-state:no-release-authority",
                        ],
                        status="blocked",
                    ),
                ),
                source_refs=["status-ref:foundation-gate-summary"],
                status_refs=["status-ref:foundation-gate-report"],
                related_route_refs=[
                    "GET /control-center/foundation-gate/summary",
                    "/foundation-gate",
                ],
                side_effect_class="validation_only",
                authority_posture=(
                    "Foundation Gate status and latency measurements are evidence, "
                    "not production authority."
                ),
                approval_posture="approval_refs_are_identifiers_only_not_authority",
                audit_refs=["audit-ref:foundation-gate:latest"],
                replay_refs=["replay-ref:foundation-gate:latest"],
                rollback_blockers=["rollback_execution_not_scoped"],
                latency_refs=[
                    "latency-ref:foundation-gate:latest-report",
                    "performance-ref:release-latency-baseline",
                ],
                foundation_gate_refs=["foundation-gate-ref:latest-report"],
                redaction_status="safe_refs_only",
                stale_state="recheck_foundation_gate_report_before_release_claim",
                missing_evidence_posture="release_evidence_packet_missing_until_scoped_release",
                blocked_states=[
                    "foundation_gate_refs_not_production_authority",
                    "latency_refs_not_authority",
                    "no_release_authority",
                ],
                next_safe_action=(
                    "Inspect Foundation Gate and latency refs; keep production "
                    "claims blocked until release evidence is scoped."
                ),
            )
        )
        return [item.model_dump(mode="json") for item in timeline]

    def actions_inbox(self, *, limit: int = 50) -> dict[str, Any]:
        items = self.list_action_inbox(limit=limit)
        chat_turn_receipts = self.list_chat_turn_receipts(limit=5)
        chat_handoff_receipts = self.list_chat_handoff_receipts(limit=5)
        chat_to_loop_handoff_read_model = build_chat_to_loop_handoff_read_model(
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
        )
        memory_items = self.list_memory_review_queue(limit=3)
        briefing_items = self.list_briefing_items(limit=3)
        memory_review_decisions = self.list_memory_review_decisions(limit=5)
        memory_to_loop_binding_contract = _memory_to_loop_binding_contract_payload(
            memory_items=memory_items,
            cross_surface_memory_intake_contract=(
                _cross_surface_memory_intake_contract_payload()
            ),
        )
        private_beta_readiness_gate_contract = (
            _private_beta_readiness_gate_contract_payload()
        )
        user_intent_understanding_contract = (
            _user_intent_understanding_contract_payload()
        )
        source_readiness = self.source_readiness(briefing_items=briefing_items)
        source_readiness_items = source_readiness["source_readiness_items"]
        source_readiness_proposal_candidates = source_readiness[
            "source_readiness_proposal_candidates"
        ]
        crm_lite_followups = _crm_lite_followups(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            memory_items=memory_items,
        )
        memory_why_shown_items = _memory_why_shown_items(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
        )
        review_queue_groups = _review_queue_groups(
            actions=items,
            memory_items=memory_items,
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        review_filter_facets = _action_inbox_review_filter_facets(items)
        action_groups = _action_group_summaries(items)
        action_inbox_work_queue_read_model = build_action_inbox_work_queue_read_model(
            actions=items,
            action_groups=action_groups,
        )
        try:
            runtime_store = RuntimeInvocationStore()
            runtime_action_inbox_bridge_read_model = (
                build_runtime_action_inbox_bridge_read_model(
                    runtime_store.list_invocations(),
                    entries=runtime_store.list_entries(),
                )
            )
        except Exception:
            runtime_action_inbox_bridge_read_model = (
                build_runtime_action_inbox_bridge_read_model([])
            )
        task_decomposition_proposal_items = [
            item
            for item in items
            if item.get("action_kind") == TASK_DECOMPOSITION_ACTION_KIND
        ]
        dogfood_capture = _dogfood_capture_summary(
            actions=items,
            memory_items=memory_items,
            briefing_items=briefing_items,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        follow_up_tracker = build_follow_up_tracker_read_model(
            actions=items,
            memory_items=memory_items,
            memory_review_decisions=memory_review_decisions,
            crm_lite_followups=crm_lite_followups,
            source_readiness_items=source_readiness_items,
            evidence_timeline=[],
        )
        action_inbox_decision_lane_read_model = (
            build_action_inbox_decision_lane_read_model(actions=items)
        )
        action_tool_code_lane_catalog_read_model = (
            build_action_tool_code_lane_catalog_read_model(
                action_work_queue=action_inbox_work_queue_read_model,
                runtime_action_bridge=runtime_action_inbox_bridge_read_model,
            ).model_dump(mode="json")
        )
        plans_to_actions_bridge_read_model = build_plans_to_actions_bridge_read_model(
            plans=self.list_plan_summaries(limit=3),
            action_items=items,
        )
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_review_queue",
            "surface": "Actions",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "route_ref": "/control-center/actions/inbox",
            "read_only_route_refs": [
                "GET /control-center/actions/inbox",
                "GET /control-center/actions/{action_id}/receipt",
                "GET /control-center/sources/readiness",
                "GET /control-center/storage/status",
                "GET /control-center/routes",
                "GET /control-center/runtime-readiness/summary",
                "GET /control-center/foundation-gate/summary",
            ],
            "today_action_envelope_route_refs": list(
                FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS
            ),
            "decision_route_refs": list(FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS),
            "local_prerequisite_refs": [
                "status-ref:founder-loop-storage",
                "status-ref:control-center-route-manifest",
                "capability-ref:local-approval-authority",
            ],
            "action_group_order": list(ACTION_INBOX_GROUP_ORDER),
            "action_groups": action_groups,
            "action_inbox_work_queue_contract_ref": (
                ACTION_INBOX_WORK_QUEUE_CONTRACT_REF
            ),
            "action_inbox_work_queue_read_model": (action_inbox_work_queue_read_model),
            "runtime_action_inbox_bridge_contract_ref": (
                RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF
            ),
            "runtime_action_inbox_bridge_read_model": (
                runtime_action_inbox_bridge_read_model
            ),
            "action_tool_code_lane_catalog_contract_ref": (
                ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
            ),
            "action_tool_code_lane_catalog_read_model": (
                action_tool_code_lane_catalog_read_model
            ),
            "action_inbox_decision_lane_contract_ref": (
                ACTION_INBOX_DECISION_LANE_CONTRACT_REF
            ),
            "action_inbox_decision_lane_read_model": (
                action_inbox_decision_lane_read_model
            ),
            "plans_to_actions_bridge_contract_ref": (
                PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
            ),
            "plans_to_actions_bridge_read_model": (plans_to_actions_bridge_read_model),
            "chat_to_loop_handoff_contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
            "chat_to_loop_handoff_read_model": chat_to_loop_handoff_read_model,
            "items": items,
            "approval_required_before_mutation": True,
            "mutating_controls_enabled": True,
            "action_execution_enabled": False,
            "decision_state_contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
            "action_revision_contract_ref": FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF,
            "expected_revision_required": True,
            "stale_revision_conflict_code": "FOUNDER_LOOP_ACTION_STALE_REVISION",
            "stale_revision_refresh_route_ref": ("GET /control-center/actions/inbox"),
            "cancel_decision_enabled": True,
            "cancel_invalidates_prior_approvals": True,
            "edit_invalidates_prior_approvals": True,
            "action_decision_receipt_limit_per_item": (
                FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM
            ),
            "decision_statuses": [
                "proposed",
                "approved",
                "edited",
                "rejected",
                "deferred",
                "cancelled",
                "expired",
                "receipt_recorded",
                "blocked",
            ],
            "decision_actions": list(FOUNDER_LOOP_ACTION_DECISION_KINDS),
            "decision_receipts_required": True,
            "today_action_envelope_receipts_required": True,
            "idempotency_replay_enabled": True,
            "idempotency_conflict_rejected": True,
            "vertical_slice_contract_ref": FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
            "action_envelope_contract_ref": PLANS_ACTION_ENVELOPE_CONTRACT_REF,
            "action_envelope_review_postures": (
                plans_action_envelope_review_posture_rows()
            ),
            "action_envelope_required_ref_fields": (
                PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS
            ),
            "action_envelope_authority_posture": (
                plans_action_envelope_authority_posture()
            ),
            "task_decomposition_action_proposals": task_decomposition_proposal_items,
            "task_decomposition_proposal_summary": (
                _task_decomposition_action_proposal_summary(
                    task_decomposition_proposal_items
                )
            ),
            **memory_to_loop_binding_contract,
            **private_beta_readiness_gate_contract,
            **user_intent_understanding_contract,
            "source_readiness_items": source_readiness_items,
            "source_readiness_route_ref": source_readiness["route_ref"],
            "source_readiness_proposal_candidates": source_readiness_proposal_candidates,
            "source_readiness_proposal_binding_contract_ref": (
                SOURCE_READINESS_PROPOSAL_BINDING_CONTRACT_REF
            ),
            "crm_lite_relationship_memory_contract_ref": (
                CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
            ),
            "crm_lite_relationship_authority_posture": (
                crm_lite_relationship_authority_posture()
            ),
            "follow_up_tracker_contract_ref": FOLLOW_UP_TRACKER_CONTRACT_REF,
            "follow_up_tracker": follow_up_tracker,
            "crm_lite_followups": crm_lite_followups,
            "memory_why_shown_items": memory_why_shown_items,
            "review_queue_groups": review_queue_groups,
            "review_filter_facets": review_filter_facets,
            "dogfood_capture": dogfood_capture,
            "disabled_state_label": "Action execution remains blocked",
            "evidence_refs": ["evidence-ref:founder-loop:action-inbox"],
            "blocked_states": [
                "no_action_execution_route",
                "approval_ref_must_validate_exact_scope",
                "no_connector_write_route",
                "no_shell_subprocess_execution",
                "no_runtime_model_call_route",
                "no_memory_write",
                "no_context_injection",
                "no_production_authority",
            ],
        }

    def morning_briefing(self, *, limit: int = 10) -> dict[str, Any]:
        items = self.list_briefing_items(limit=limit)
        actions = self.list_action_inbox(limit=6)
        plans = self.list_plan_summaries(limit=3)
        memory_items = self.list_memory_review_queue(limit=3)
        memory_review_decisions = self.list_memory_review_decisions(limit=5)
        chat_turn_receipts = self.list_chat_turn_receipts(limit=5)
        chat_handoff_receipts = self.list_chat_handoff_receipts(limit=5)
        web_evidence_attachments = self.list_web_evidence_attachments(limit=5)
        chat_to_loop_handoff_read_model = build_chat_to_loop_handoff_read_model(
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
        )
        cross_surface_memory_intake_contract = (
            _cross_surface_memory_intake_contract_payload()
        )
        memory_to_loop_binding_contract = _memory_to_loop_binding_contract_payload(
            memory_items=memory_items,
            cross_surface_memory_intake_contract=cross_surface_memory_intake_contract,
        )
        private_beta_readiness_gate_contract = (
            _private_beta_readiness_gate_contract_payload()
        )
        user_intent_understanding_contract = (
            _user_intent_understanding_contract_payload()
        )
        source_readiness = self.source_readiness(briefing_items=items)
        source_readiness_items = source_readiness["source_readiness_items"]
        source_readiness_posture = source_readiness["source_readiness_posture"]
        crm_lite_followups = _crm_lite_followups(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            memory_items=memory_items,
        )
        memory_why_shown_items = _memory_why_shown_items(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
        )
        review_queue_groups = _review_queue_groups(
            actions=actions,
            memory_items=memory_items,
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        dogfood_capture = _dogfood_capture_summary(
            actions=actions,
            memory_items=memory_items,
            briefing_items=items,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
        )
        evidence_timeline = self._build_evidence_timeline(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=items,
            cross_surface_memory_intake_contract=cross_surface_memory_intake_contract,
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            private_beta_readiness_gate_contract=private_beta_readiness_gate_contract,
            user_intent_understanding_contract=user_intent_understanding_contract,
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
            memory_review_decisions=memory_review_decisions,
            web_evidence_attachments=web_evidence_attachments,
        )
        weekly_review_narrative = _weekly_review_narrative(
            memory_to_loop_binding_contract=memory_to_loop_binding_contract,
            evidence_timeline=evidence_timeline,
            actions=actions,
            source_readiness_items=source_readiness_items,
            crm_lite_followups=crm_lite_followups,
            dogfood_capture=dogfood_capture,
        )
        daily_loop_summary = _daily_loop_summary(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=items,
            source_readiness_items=source_readiness_items,
            crm_lite_followups=crm_lite_followups,
            memory_why_shown_items=memory_why_shown_items,
            review_queue_groups=review_queue_groups,
            weekly_review_narrative=weekly_review_narrative,
            dogfood_capture=dogfood_capture,
        )
        follow_up_tracker = build_follow_up_tracker_read_model(
            actions=actions,
            memory_items=memory_items,
            memory_review_decisions=memory_review_decisions,
            crm_lite_followups=crm_lite_followups,
            source_readiness_items=source_readiness_items,
            evidence_timeline=evidence_timeline,
        )
        evidence_event_refs = [
            str(event["event_ref"])
            for event in self._productized_evidence_events(evidence_timeline)
        ]
        weekly_ceo_review_v1_read_model = build_weekly_ceo_review_v1_read_model(
            weekly_review_narrative=weekly_review_narrative,
            actions=actions,
            memory_review_decisions=memory_review_decisions,
            follow_up_tracker=follow_up_tracker,
            evidence_timeline=evidence_timeline,
            source_readiness_items=source_readiness_items,
            evidence_event_refs=evidence_event_refs,
        )
        today_loop_read_model = build_today_loop_read_model(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=items,
            evidence_timeline=evidence_timeline,
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
            memory_review_decisions=memory_review_decisions,
            crm_lite_followups=crm_lite_followups,
            source_readiness_items=source_readiness_items,
        )
        founder_loop_v1_product_proof_read_model = (
            build_founder_loop_product_proof_read_model(
                actions=actions,
                briefing_items=items,
                memory_items=memory_items,
                evidence_timeline=evidence_timeline,
                memory_review_decisions=memory_review_decisions,
                today_loop_read_model=today_loop_read_model,
                weekly_ceo_review_v1_read_model=weekly_ceo_review_v1_read_model,
                daily_loop_summary=daily_loop_summary,
                evidence_event_refs=evidence_event_refs,
            )
        )
        founder_loop_runs_integration_read_model = (
            build_founder_loop_runs_integration_read_model(
                actions=actions,
                briefing_items=items,
                memory_items=memory_items,
                evidence_timeline=evidence_timeline,
                memory_review_decisions=memory_review_decisions,
                founder_loop_product_proof_read_model=(
                    founder_loop_v1_product_proof_read_model
                ),
                weekly_ceo_review_v1_read_model=weekly_ceo_review_v1_read_model,
                evidence_event_refs=evidence_event_refs,
            )
        )
        storage_status = self.storage_status()
        memory_workbench = self._memory_workbench_read_only_status()
        payload = {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_briefing_skeleton",
            "surface": "Morning Briefing",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "route_ref": "/control-center/morning-briefing/summary",
            "read_only_route_refs": [
                "GET /control-center/morning-briefing/summary",
                "GET /control-center/sources/readiness",
                "GET /control-center/storage/status",
                "GET /control-center/routes",
                "GET /control-center/runtime-readiness/summary",
                "GET /control-center/foundation-gate/summary",
            ],
            "local_prerequisite_refs": [
                "status-ref:founder-loop-storage",
                "status-ref:control-center-route-manifest",
                "contract-ref:email-read-only-missing",
                "contract-ref:calendar-read-only-missing",
                "contract-ref:notification-delivery-missing",
            ],
            "source_readiness": "blocked_missing_email_calendar_notification_contracts",
            "authority_boundary": (
                "Read-only briefing summary; no email, calendar, connector, refresh, "
                "notification, model, memory, or delivery authority."
            ),
            "bounded_preview_only": True,
            "refresh_enabled": False,
            "notification_delivery_enabled": False,
            "missing_contract_refs": [
                "contract-ref:email-read-only-missing",
                "contract-ref:calendar-read-only-missing",
                "contract-ref:notification-delivery-missing",
            ],
            "source_readiness_route_ref": source_readiness["route_ref"],
            "source_readiness_posture": source_readiness_posture,
            "follow_up_tracker_contract_ref": FOLLOW_UP_TRACKER_CONTRACT_REF,
            "follow_up_tracker": follow_up_tracker,
            "daily_loop_summary": daily_loop_summary,
            "daily_loop_sections": [
                {
                    "section_ref": "briefing-section:today-priorities",
                    "title": "Today priorities",
                    "status": "safe_refs_ready",
                    "safe_summary": daily_loop_summary["today_plan_summary"],
                    "source_refs": [str(action["item_ref"]) for action in actions[:3]],
                    "evidence_refs": ["evidence-ref:briefing-section:today-priorities"],
                    "next_safe_action": "Review Today refs before recording supported receipts.",
                    "blocked_state_refs": ["blocked-state:no-action-execution"],
                },
                {
                    "section_ref": "briefing-section:source-readiness",
                    "title": "Blocked and missing sources",
                    "status": "explicit_readiness_states",
                    "safe_summary": (
                        "Inbox, calendar, tasks, CRM-lite, repo, and local-file "
                        "readiness are visible as safe refs and blocked states."
                    ),
                    "source_refs": [
                        item["source_ref"] for item in source_readiness_items
                    ],
                    "evidence_refs": ["evidence-ref:briefing-section:source-readiness"],
                    "next_safe_action": "Inspect missing-source posture before trusting a daily item.",
                    "blocked_state_refs": [
                        "blocked-state:no-account-auth",
                        "blocked-state:no-connector-runtime",
                    ],
                },
                {
                    "section_ref": "briefing-section:crm-lite-follow-ups",
                    "title": "CRM-lite follow-ups",
                    "status": "review_only",
                    "safe_summary": (
                        "Relationship follow-ups are local reviewed-memory refs; "
                        "drafts remain review-only."
                    ),
                    "source_refs": [
                        item["follow_up_ref"] for item in crm_lite_followups
                    ],
                    "evidence_refs": ["evidence-ref:briefing-section:crm-lite"],
                    "next_safe_action": "Review memory provenance before drafting a follow-up.",
                    "blocked_state_refs": ["blocked-state:no-external-crm-write"],
                },
                {
                    "section_ref": "briefing-section:memory-why-shown",
                    "title": "Memory why shown",
                    "status": "reviewed_recall_only",
                    "safe_summary": (
                        "Surfaced memory includes why it appears, provenance refs, "
                        "stale posture, and explicit recall boundaries."
                    ),
                    "source_refs": [
                        item["loop_item_ref"] for item in memory_why_shown_items
                    ],
                    "evidence_refs": ["evidence-ref:briefing-section:memory-why-shown"],
                    "next_safe_action": "Review stale and conflict posture before relying on recall.",
                    "blocked_state_refs": [
                        "blocked-state:no-automatic-memory-truth",
                        "blocked-state:no-context-injection",
                    ],
                },
                {
                    "section_ref": "briefing-section:review-queue",
                    "title": "Review queue summary",
                    "status": "grouped_review_refs",
                    "safe_summary": daily_loop_summary["review_queue_summary"],
                    "source_refs": [
                        group["group_ref"] for group in review_queue_groups
                    ],
                    "evidence_refs": ["evidence-ref:briefing-section:review-queue"],
                    "next_safe_action": "Open Action Inbox for supported review receipts only.",
                    "blocked_state_refs": ["blocked-state:no-action-execution"],
                },
                {
                    "section_ref": "briefing-section:dogfood-capture",
                    "title": "Dogfood capture",
                    "status": dogfood_capture["status"],
                    "safe_summary": dogfood_capture["safe_summary"],
                    "source_refs": [dogfood_capture["capture_ref"]],
                    "evidence_refs": dogfood_capture["evidence_refs"],
                    "next_safe_action": dogfood_capture["next_safe_action"],
                    "blocked_state_refs": [
                        "blocked-state:no-public-beta",
                        "blocked-state:no-production-authority",
                    ],
                },
            ],
            "source_readiness_items": source_readiness_items,
            "crm_lite_relationship_memory_contract_ref": (
                CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
            ),
            "crm_lite_relationship_authority_posture": (
                crm_lite_relationship_authority_posture()
            ),
            "crm_lite_followups": crm_lite_followups,
            "memory_why_shown_items": memory_why_shown_items,
            "review_queue_groups": review_queue_groups,
            "weekly_review_narrative": weekly_review_narrative,
            "weekly_ceo_review_v1_contract_ref": WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
            "weekly_ceo_review_v1_read_model": weekly_ceo_review_v1_read_model,
            "founder_loop_v1_product_proof_contract_ref": (
                FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
            ),
            "founder_loop_v1_product_proof_read_model": (
                founder_loop_v1_product_proof_read_model
            ),
            "founder_loop_runs_integration_contract_ref": (
                FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF
            ),
            "founder_loop_runs_integration_read_model": (
                founder_loop_runs_integration_read_model
            ),
            "loop_trace_refs": _loop_trace_refs_from_runs_integration(
                founder_loop_runs_integration_read_model
            ),
            "chat_to_loop_handoff_contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
            "chat_to_loop_handoff_read_model": chat_to_loop_handoff_read_model,
            "dogfood_capture": dogfood_capture,
            "items": items,
            "evidence_refs": ["evidence-ref:founder-loop:morning-briefing"],
            "blocked_states": [
                "no_email_read_authority",
                "no_calendar_read_authority",
                "no_connector_runtime",
                "no_account_auth",
                "no_background_refresh",
                "no_notification_delivery",
                "no_memory_write",
                "no_model_provider_call",
            ],
        }
        payload["morning_briefing_v1_contract_ref"] = MORNING_BRIEFING_V1_CONTRACT_REF
        payload["morning_briefing_v1_read_model"] = (
            build_morning_briefing_v1_read_model(
                briefing=payload,
                actions=actions,
                memory_items=memory_items,
                evidence_timeline=evidence_timeline,
                storage_status=storage_status,
                memory_workbench=memory_workbench,
            )
        )
        return payload

    def source_readiness(
        self,
        *,
        briefing_items: list[dict[str, Any]] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        items = (
            briefing_items
            if briefing_items is not None
            else self.list_briefing_items(limit=limit)
        )
        return _source_readiness_read_model(briefing_items=items)

    def list_action_inbox(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   risk_class, action_kind, side_effect_class, authority_boundary,
                   approval_required, approval_envelope_ref,
                   approval_envelope_status, state_change_contract_ref,
                   state_change_readiness, blocked_state, evidence_refs_json,
                   receipt_refs_json, audit_refs_json, idempotency_key_ref,
                   expires_at, stale_state, rollback_ref, safe_disable_ref,
                   estimated_cost_usd, max_approved_cost_usd, provider_ref,
                   model_profile_ref, input_metered_units, output_metered_units,
                   total_metered_units, cost_estimate_ref, captured_usage_ref,
                   budget_decision_ref, cost_receipt_refs_json,
                   cost_blocked_state_refs_json, cost_state_label,
                   provider_authority_state_label,
                   unknown_paid_cost_requires_explicit_approval,
                   frontier_usage_claimed,
                   next_safe_action, created_at, updated_at
            FROM action_inbox
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        actions = [_row_to_payload(row) for row in rows]
        revision_decision_eligible_item_refs = {
            str(action["item_ref"]) for action in actions
        }

        def merge_generated_actions(
            generated_actions: list[dict[str, Any]],
        ) -> None:
            action_indexes = {
                str(action["item_ref"]): index for index, action in enumerate(actions)
            }
            for generated_action in generated_actions:
                item_ref = str(generated_action["item_ref"])
                existing_index = action_indexes.get(item_ref)
                if existing_index is None:
                    action_indexes[item_ref] = len(actions)
                    actions.append(generated_action)
                    continue
                actions[existing_index] = {
                    **generated_action,
                    **actions[existing_index],
                }

        source_readiness = self.source_readiness()
        source_readiness_actions = _source_readiness_action_items(
            list(source_readiness.get("source_readiness_proposal_candidates") or [])
        )
        merge_generated_actions(source_readiness_actions)
        health_recommendation_actions = _health_recommendation_action_items(
            build_fcc_health_recommendations(
                source_readiness=source_readiness,
                memory_quality_issue_refs=self._memory_action_inbox_signal_refs(
                    limit=10
                ),
            )
        )
        merge_generated_actions(health_recommendation_actions)
        task_decomposition_actions = _task_decomposition_action_items_for_plans(
            self.list_plan_summaries(limit=3)
        )
        merge_generated_actions(task_decomposition_actions)
        projected_actions: list[dict[str, Any]] = []
        for action in actions:
            action_envelope_payload = _action_envelope_contract_payload(action)
            projected = {
                **action,
                **action_envelope_payload,
                **_fusion_routing_fields_for_action(action),
                **self._local_task_commit_projection(action),
            }
            revision_state = self._action_revision_state_for_action(projected)
            projected.update(
                {
                    "action_revision_contract_ref": (
                        FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF
                    ),
                    "action_generation": revision_state["generation"],
                    "action_generation_ref": revision_state["generation_ref"],
                    "action_revision_ref": revision_state["revision_ref"],
                    "action_revision_fingerprint_ref": revision_state[
                        "revision_fingerprint_ref"
                    ],
                    "action_revision_source_fingerprint_ref": revision_state[
                        "source_fingerprint_ref"
                    ],
                    "action_revision_transition_ref": revision_state["transition_ref"],
                    "action_revision_state": revision_state,
                    "expected_revision_ref": revision_state["revision_ref"],
                    "action_revision_decision_eligible": (
                        str(projected["item_ref"])
                        in revision_decision_eligible_item_refs
                    ),
                }
            )
            projected["approval_envelope"] = _action_approval_envelope_read_model(
                projected
            )
            local_task_receipt = self._latest_local_task_commit_receipt_for_item_ref(
                str(projected["item_ref"])
            )
            decision_receipts = self._action_decision_receipts_for_item_ref(
                str(projected["item_ref"])
            )
            receipt_refs = list(projected.get("receipt_refs") or [])
            audit_refs = list(projected.get("audit_refs") or [])
            for decision_receipt in decision_receipts:
                receipt_ref = decision_receipt.get("receipt_ref")
                audit_ref = decision_receipt.get("audit_ref")
                if isinstance(receipt_ref, str) and receipt_ref:
                    receipt_refs.append(receipt_ref)
                if isinstance(audit_ref, str) and audit_ref:
                    audit_refs.append(audit_ref)
            if local_task_receipt is not None:
                receipt_ref = local_task_receipt.get("receipt_ref")
                audit_ref = local_task_receipt.get("audit_ref")
                if isinstance(receipt_ref, str) and receipt_ref:
                    receipt_refs.append(receipt_ref)
                if isinstance(audit_ref, str) and audit_ref:
                    audit_refs.append(audit_ref)
            projected["receipt_refs"] = list(dict.fromkeys(receipt_refs))
            projected["audit_refs"] = list(dict.fromkeys(audit_refs))
            projected["receipt_visibility"] = _action_receipt_visibility_read_model(
                action=projected,
                decision_receipts=decision_receipts,
                local_task_receipt=local_task_receipt,
            )
            projected_actions.append(
                {
                    **projected,
                    **_action_inbox_group_projection(projected),
                }
            )
        return projected_actions[: self._bounded_limit(limit)]

    def list_durable_local_task_actions(
        self,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Project a bounded newest-first durable local-task candidate window."""
        bounded_limit = min(self._bounded_limit(limit), 50)
        rows = self._fetch_all(
            """
            SELECT item_ref
            FROM local_task_commit_receipts
            ORDER BY created_at DESC, item_ref ASC
            LIMIT ?
            """,
            (bounded_limit,),
        )
        actions: list[dict[str, Any]] = []
        for row in rows:
            item_ref = str(row["item_ref"])
            action = self._action_payload_for_item_ref(item_ref)
            if action is None:
                continue
            projected = {**action, **self._local_task_commit_projection(action)}
            receipt = self._latest_local_task_commit_receipt_for_item_ref(item_ref)
            if receipt is None:
                continue
            projected["receipt_refs"] = list(
                dict.fromkeys(
                    [
                        *list(projected.get("receipt_refs") or []),
                        str(receipt.get("receipt_ref") or ""),
                    ]
                )
            )
            projected["audit_refs"] = list(
                dict.fromkeys(
                    [
                        *list(projected.get("audit_refs") or []),
                        str(receipt.get("audit_ref") or ""),
                    ]
                )
            )
            actions.append(projected)
        return actions

    def record_chat_turn_receipt(
        self,
        *,
        request: ChatTurnReceiptRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        payload_fingerprint_ref = chat_payload_fingerprint_ref(
            chat_turn_payload_for_fingerprint(request=request)
        )
        replay = self._chat_turn_receipt_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_CHAT_TURN_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._chat_turn_receipt_by_ref(str(replay["receipt_ref"]))
            return {
                **receipt,
                "replayed": True,
                "safe_summary_ref": "safe-summary-ref:chat-turn-replay",
            }

        turn_ref = chat_turn_ref_for_request(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
        receipt_ref = chat_turn_receipt_ref(turn_ref, idempotency_key_ref)
        evidence_ref = chat_turn_evidence_ref(turn_ref)
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:chat-turn-receipt",
                    evidence_ref,
                    *request.evidence_refs,
                    *request.metadata_refs,
                ]
            )
        )
        receipt = ChatTurnReceipt(
            turn_ref=turn_ref,
            route_ref=request.route_ref,
            model_ref=request.model_ref,
            runtime_truth=request.runtime_truth,
            auth_truth=request.auth_truth,
            tool_denial_truth=request.tool_denial_truth,
            safe_summary_ref=request.safe_summary_ref,
            turn_harness_binding=chat_turn_harness_binding_receipt_summary(
                request.turn_harness_binding
            ),
            handoff_refs=[
                chat_turn_handoff_ref(turn_ref, "actions"),
                chat_turn_handoff_ref(turn_ref, "plans"),
            ],
            receipt_ref=receipt_ref,
            evidence_ref=evidence_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            evidence_refs=evidence_refs,
            blocked_state_refs=list(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS),
        )
        receipt_payload = receipt.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_turn_receipts (
                    receipt_ref, turn_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    receipt.receipt_ref,
                    receipt.turn_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO chat_turn_receipt_replays (
                    key_ref, turn_ref, payload_fingerprint_ref, receipt_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    receipt.turn_ref,
                    payload_fingerprint_ref,
                    receipt.receipt_ref,
                    receipt.created_at,
                ),
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": "Chat turn durable receipt recorded as safe refs only.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def latest_chat_turn_receipt(self, turn_ref: str) -> dict[str, Any] | None:
        _validate_safe_ref(turn_ref, "turn_ref")
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM chat_turn_receipts
            WHERE turn_ref = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (turn_ref,),
        )
        if not rows:
            return None
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def record_chat_handoff(
        self,
        *,
        turn_ref: str,
        request: ChatHandoffRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(turn_ref, "turn_ref")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        turn_receipt = self.latest_chat_turn_receipt(turn_ref)
        if turn_receipt is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_TURN_RECEIPT_NOT_FOUND")

        payload_fingerprint_ref = chat_payload_fingerprint_ref(
            chat_handoff_payload_for_fingerprint(turn_ref=turn_ref, request=request)
        )
        replay = self._chat_handoff_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_CHAT_HANDOFF_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._chat_handoff_receipt_by_ref(str(replay["receipt_ref"]))
            return {
                **receipt,
                "replayed": True,
                "safe_summary_ref": "safe-summary-ref:chat-handoff-replay",
            }

        target = request.handoff_target
        handoff_ref = chat_turn_handoff_ref(turn_ref, target)
        created_ref = chat_handoff_created_ref(turn_ref, target)
        receipt_ref = chat_handoff_receipt_ref(turn_ref, target, idempotency_key_ref)
        audit_ref = chat_handoff_audit_ref(turn_ref, target, idempotency_key_ref)
        evidence_ref = (
            f"evidence-ref:chat-handoff:{_safe_suffix(target)}:{_safe_suffix(turn_ref)}"
        )
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:chat-handoff",
                    str(turn_receipt.get("receipt_ref")),
                    evidence_ref,
                    *list(turn_receipt.get("evidence_refs") or []),
                    *request.metadata_refs,
                ]
            )
        )
        receipt = ChatHandoffReceipt(
            turn_ref=turn_ref,
            handoff_target=target,
            handoff_ref=handoff_ref,
            created_ref=created_ref,
            receipt_ref=receipt_ref,
            audit_ref=audit_ref,
            evidence_ref=evidence_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            safe_summary_ref="safe-summary-ref:chat-handoff-review-only",
            evidence_refs=evidence_refs,
            blocked_state_refs=list(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS),
        )
        receipt_payload = receipt.model_dump(mode="json")
        if target == "actions":
            self._upsert_chat_handoff_action(
                created_ref=created_ref,
                receipt=receipt,
                turn_receipt=turn_receipt,
                idempotency_key_ref=idempotency_key_ref,
                evidence_refs=evidence_refs,
            )
        else:
            self._upsert_chat_handoff_plan(
                created_ref=created_ref,
                receipt=receipt,
                turn_receipt=turn_receipt,
                evidence_refs=evidence_refs,
            )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_handoff_receipts (
                    receipt_ref, turn_ref, handoff_target, handoff_ref, created_ref,
                    receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_ref,
                    receipt.turn_ref,
                    receipt.handoff_target,
                    receipt.handoff_ref,
                    receipt.created_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO chat_handoff_replays (
                    key_ref, turn_ref, handoff_target, payload_fingerprint_ref,
                    receipt_ref, handoff_ref, created_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    receipt.turn_ref,
                    receipt.handoff_target,
                    payload_fingerprint_ref,
                    receipt.receipt_ref,
                    receipt.handoff_ref,
                    receipt.created_ref,
                    receipt.created_at,
                ),
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": "Chat handoff receipt recorded as review-only refs.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": "Chat handoff audit ref recorded without execution.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def list_chat_turn_receipts(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM chat_turn_receipts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def list_chat_handoff_receipts(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM chat_handoff_receipts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def _upsert_chat_handoff_action(
        self,
        *,
        created_ref: str,
        receipt: ChatHandoffReceipt,
        turn_receipt: dict[str, Any],
        idempotency_key_ref: str,
        evidence_refs: list[str],
    ) -> None:
        suffix = _short_ref_suffix(created_ref)
        self.upsert_action(
            FounderLoopActionRecord(
                item_ref=created_ref,
                title="Action envelope from Chat handoff",
                safe_summary=(
                    "Chat safe refs were handed off into a reviewable Action envelope; "
                    "no action execution occurred."
                ),
                surface="Chat",
                priority="medium",
                risk_class="medium",
                status="proposed",
                side_effect_class="local_dev_workspace_only",
                authority_boundary=(
                    "Chat handoff creates reviewable local state only; model output "
                    "is not approval or execution authority."
                ),
                approval_required=True,
                approval_envelope_ref=f"approval-envelope:chat-handoff:{suffix}",
                approval_envelope_status="review_ready_exact_scope_required",
                state_change_contract_ref=CHAT_DURABLE_RECEIPT_CONTRACT_REF,
                state_change_readiness="chat_handoff_action_envelope_created_no_execution",
                blocked_state=(
                    "Action execution, connector writes, memory writes, shell/subprocess "
                    "work, provider/model calls, and production authority remain blocked."
                ),
                evidence_refs=evidence_refs,
                receipt_refs=[
                    str(turn_receipt.get("receipt_ref")),
                    receipt.receipt_ref,
                ],
                audit_refs=[receipt.audit_ref],
                idempotency_key_ref=idempotency_key_ref,
                expires_at=None,
                stale_state="recheck_chat_receipt_before_action_decision",
                rollback_ref=f"rollback-plan:chat-handoff:{suffix}",
                safe_disable_ref=f"safe-disable:chat-handoff:{suffix}",
                next_safe_action=(
                    "Review the Chat handoff Action envelope; execution remains blocked."
                ),
            )
        )

    def _upsert_chat_handoff_plan(
        self,
        *,
        created_ref: str,
        receipt: ChatHandoffReceipt,
        turn_receipt: dict[str, Any],
        evidence_refs: list[str],
    ) -> None:
        _ = turn_receipt
        self.upsert_plan(
            FounderLoopPlanRecord(
                plan_ref=created_ref,
                title="Plan proposal from Chat handoff",
                status="partial_backend_not_product_ready",
                safe_summary=(
                    "Chat safe refs were handed off into a reviewable plan proposal; "
                    "no plan execution occurred."
                ),
                next_step_summary=(
                    "Review the plan proposal and create exact Action envelopes before "
                    "any mutation is considered."
                ),
                evidence_refs=list(
                    dict.fromkeys([*evidence_refs, receipt.receipt_ref])
                ),
            )
        )

    def promote_today_item_to_action_envelope(
        self,
        *,
        request: FounderLoopActionEnvelopePromotionRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        source = self._today_item_payload_for_ref(request.today_item_ref)
        if source is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_TODAY_ITEM_NOT_FOUND")

        item_ref = today_item_to_action_item_ref(request.today_item_ref)
        authority_decision = self._today_action_envelope_authority_decision(
            today_item_ref=request.today_item_ref,
            item_ref=item_ref,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=active_authority_leases,
        )
        fingerprint_payload = promotion_payload_for_fingerprint(request=request)
        payload_fingerprint_ref = action_payload_fingerprint_ref(fingerprint_payload)
        replay = self._action_envelope_promotion_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_ACTION_ENVELOPE_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._action_envelope_promotion_receipt_by_ref(
                str(replay["receipt_ref"])
            )
            return {
                **receipt,
                "replayed": True,
                "safe_summary": (
                    "Prior Today-to-Action envelope receipt returned for matching "
                    "idempotency key."
                ),
            }

        existing_action = self._action_payload_for_item_ref(item_ref)
        action_envelope_ref = (
            f"action-envelope:founder-loop-v1:{_safe_suffix(item_ref)}"
        )
        receipt_ref = action_envelope_promotion_receipt_ref(
            item_ref,
            idempotency_key_ref,
        )
        audit_ref = action_envelope_promotion_audit_ref(item_ref, idempotency_key_ref)
        evidence_event_ref = action_envelope_promotion_event_ref(item_ref)
        cost_slot = self._operator_run_timeline_cost_slot(
            action_envelope_ref,
            estimated_cost_usd=request.estimated_cost_usd,
            max_approved_cost_usd=request.max_approved_cost_usd,
            provider_ref=request.provider_ref,
            model_profile_ref=request.model_profile_ref,
            input_metered_units=request.input_metered_units,
            output_metered_units=request.output_metered_units,
            frontier_usage_claimed=request.frontier_usage_claimed,
            unknown_cost=False,
        )
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:today-action-envelope",
                    evidence_event_ref,
                    *cost_slot["cost_receipt_refs"],
                    request.today_item_ref,
                    authority_decision.decision_ref,
                    authority_decision.audit_record_ref,
                    *(
                        [authority_decision.receipt_ref]
                        if authority_decision.receipt_ref
                        else []
                    ),
                    *(
                        [authority_decision.lease_ref]
                        if authority_decision.lease_ref
                        else []
                    ),
                    *list((existing_action or {}).get("evidence_refs") or []),
                    *list(source.get("evidence_refs") or []),
                    *request.metadata_refs,
                ]
            )
        )
        receipt_refs = list(
            dict.fromkeys(
                [*list((existing_action or {}).get("receipt_refs") or []), receipt_ref]
            )
        )
        audit_refs = list(
            dict.fromkeys(
                [*list((existing_action or {}).get("audit_refs") or []), audit_ref]
            )
        )
        action_status = str((existing_action or {}).get("status") or "proposed")
        approval_envelope_status = str(
            (existing_action or {}).get("approval_envelope_status")
            or "review_ready_exact_scope_required"
        )
        state_change_readiness = str(
            (existing_action or {}).get("state_change_readiness")
            or "action_envelope_created_no_execution"
        )
        receipt = FounderLoopActionEnvelopePromotionReceipt(
            today_item_ref=request.today_item_ref,
            item_ref=item_ref,
            action_envelope_ref=action_envelope_ref,
            receipt_ref=receipt_ref,
            audit_ref=audit_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            evidence_timeline_event_ref=evidence_event_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            authority_audit_ref=authority_decision.audit_record_ref,
            authority_policy_receipt_ref=authority_decision.receipt_ref,
            safe_summary=(
                "Today item ref was promoted into a reviewable Action envelope; "
                "no action execution, connector write, memory write, shell/subprocess "
                "work, provider/model call, or production authority occurred."
            ),
            evidence_refs=evidence_refs,
            blocked_state_refs=[
                *list(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS),
                *cost_slot["cost_blocked_state_refs"],
            ],
            estimated_cost_usd=cost_slot["estimated_cost_usd"],
            max_approved_cost_usd=cost_slot["max_approved_cost_usd"],
            provider_ref=cost_slot["provider_ref"],
            model_profile_ref=cost_slot["model_profile_ref"],
            input_metered_units=cost_slot["input_metered_units"],
            output_metered_units=cost_slot["output_metered_units"],
            total_metered_units=cost_slot["total_metered_units"],
            cost_estimate_ref=cost_slot["cost_estimate_ref"],
            captured_usage_ref=cost_slot["captured_usage_ref"],
            budget_decision_ref=cost_slot["budget_decision_ref"],
            cost_receipt_refs=cost_slot["cost_receipt_refs"],
            cost_blocked_state_refs=cost_slot["cost_blocked_state_refs"],
            cost_state_label=cost_slot["cost_state_label"],
            provider_authority_state_label=cost_slot["provider_authority_state_label"],
            unknown_paid_cost_requires_explicit_approval=cost_slot[
                "approval_required_for_unknown_paid_cost"
            ],
            frontier_usage_claimed=cost_slot["frontier_usage_claimed"],
        )
        receipt_payload = receipt.model_dump(mode="json")
        action_record = FounderLoopActionRecord(
            item_ref=item_ref,
            title=_promoted_action_title(str(source.get("title", "Today item"))),
            safe_summary=(
                "Today item safe refs were promoted into an Action envelope for "
                "review only; execution remains blocked."
            ),
            surface="Today",
            priority=request.priority,
            risk_class=request.risk_class,
            status=action_status,
            side_effect_class="local_dev_workspace_only",
            authority_boundary=(
                "Today-to-Action promotion creates reviewable local state only; "
                "LocalApprovalAuthority must validate exact scope before an approve "
                "decision, and the action still cannot execute."
            ),
            approval_required=True,
            approval_envelope_ref=f"approval-envelope:founder-loop-v1:{_safe_suffix(item_ref)}",
            approval_envelope_status=approval_envelope_status,
            state_change_contract_ref=FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
            state_change_readiness=state_change_readiness,
            blocked_state=(
                "Action execution, connector writes, memory writes, shell/subprocess "
                "work, provider/model calls, and production authority remain blocked."
            ),
            evidence_refs=evidence_refs,
            receipt_refs=receipt_refs,
            audit_refs=audit_refs,
            idempotency_key_ref=idempotency_key_ref,
            expires_at=None,
            stale_state="recheck_today_item_before_action_decision",
            rollback_ref=f"rollback-plan:founder-loop-v1:{_safe_suffix(item_ref)}",
            safe_disable_ref=f"safe-disable:founder-loop-v1:{_safe_suffix(item_ref)}",
            estimated_cost_usd=cost_slot["estimated_cost_usd"],
            max_approved_cost_usd=cost_slot["max_approved_cost_usd"],
            provider_ref=cost_slot["provider_ref"],
            model_profile_ref=cost_slot["model_profile_ref"],
            input_metered_units=cost_slot["input_metered_units"],
            output_metered_units=cost_slot["output_metered_units"],
            total_metered_units=cost_slot["total_metered_units"],
            cost_estimate_ref=cost_slot["cost_estimate_ref"],
            captured_usage_ref=cost_slot["captured_usage_ref"],
            budget_decision_ref=cost_slot["budget_decision_ref"],
            cost_receipt_refs=cost_slot["cost_receipt_refs"],
            cost_blocked_state_refs=cost_slot["cost_blocked_state_refs"],
            cost_state_label=cost_slot["cost_state_label"],
            provider_authority_state_label=cost_slot["provider_authority_state_label"],
            unknown_paid_cost_requires_explicit_approval=cost_slot[
                "approval_required_for_unknown_paid_cost"
            ],
            frontier_usage_claimed=cost_slot["frontier_usage_claimed"],
            next_safe_action=(
                "Review the Action envelope and record approve, edit, reject, or "
                "defer; execution remains blocked."
            ),
        )
        envelope_payload = {
            "contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
            "vertical_slice_contract_ref": FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
            "today_item_ref": request.today_item_ref,
            "item_ref": item_ref,
            "action_envelope_ref": action_envelope_ref,
            "status": "proposed",
            "exact_scope_ref": f"scope:founder-loop-v1:{_safe_suffix(item_ref)}",
            "risk_class": request.risk_class,
            "side_effect_class": "local_dev_workspace_only",
            "approval_requirement_ref": (
                f"approval-requirement:founder-loop-v1:{_safe_suffix(item_ref)}"
            ),
            "expected_receipt_ref": receipt_ref,
            "authority_decision_ref": authority_decision.decision_ref,
            "authority_decision_outcome": authority_decision.outcome,
            "authority_lease_ref": authority_decision.lease_ref,
            "authority_domain_ref": FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF,
            "authority_capability_ref": (
                FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
            ),
            "authority_required_mode_ref": (
                FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF
            ),
            "authority_audit_ref": authority_decision.audit_record_ref,
            "authority_policy_receipt_ref": authority_decision.receipt_ref,
            "rollback_ref": action_record.rollback_ref,
            "safe_disable_ref": action_record.safe_disable_ref,
            "blocked_state_refs": list(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS),
            "action_execution_enabled": False,
            "connector_write_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "model_provider_authority_allowed": False,
            "production_authority_enabled": False,
            "cost_contract_ref": FRONTIER_AI_COST_USAGE_CONTRACT_REF,
            "estimated_cost_usd": cost_slot["estimated_cost_usd"],
            "max_approved_cost_usd": cost_slot["max_approved_cost_usd"],
            "provider_ref": cost_slot["provider_ref"],
            "model_profile_ref": cost_slot["model_profile_ref"],
            "input_metered_units": cost_slot["input_metered_units"],
            "output_metered_units": cost_slot["output_metered_units"],
            "total_metered_units": cost_slot["total_metered_units"],
            "cost_estimate_ref": cost_slot["cost_estimate_ref"],
            "captured_usage_ref": cost_slot["captured_usage_ref"],
            "budget_decision_ref": cost_slot["budget_decision_ref"],
            "cost_receipt_refs": cost_slot["cost_receipt_refs"],
            "cost_blocked_state_refs": cost_slot["cost_blocked_state_refs"],
            "cost_state_label": cost_slot["cost_state_label"],
            "provider_authority_state_label": cost_slot[
                "provider_authority_state_label"
            ],
            "unknown_paid_cost_requires_explicit_approval": cost_slot[
                "approval_required_for_unknown_paid_cost"
            ],
            "frontier_usage_claimed": cost_slot["frontier_usage_claimed"],
        }
        _validate_safe_payload(envelope_payload, "action_envelope_promotion")
        self.upsert_action(action_record)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO action_envelopes (
                    envelope_ref, item_ref, status, envelope_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    action_envelope_ref,
                    item_ref,
                    "proposed",
                    _json_dumps(envelope_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_envelope_receipts (
                    receipt_ref, item_ref, action_envelope_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_ref,
                    item_ref,
                    action_envelope_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_envelope_promotions (
                    promotion_ref, today_item_ref, item_ref, action_envelope_ref,
                    receipt_ref, audit_ref, idempotency_key_ref,
                    payload_fingerprint_ref, evidence_timeline_event_ref,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        "action-envelope-promotion:"
                        f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
                    ),
                    request.today_item_ref,
                    item_ref,
                    action_envelope_ref,
                    receipt_ref,
                    audit_ref,
                    idempotency_key_ref,
                    payload_fingerprint_ref,
                    evidence_event_ref,
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_envelope_promotion_replays (
                    key_ref, today_item_ref, item_ref, payload_fingerprint_ref,
                    receipt_ref, action_envelope_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    request.today_item_ref,
                    item_ref,
                    payload_fingerprint_ref,
                    receipt_ref,
                    action_envelope_ref,
                    receipt.created_at,
                ),
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": receipt.safe_summary,
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": "Founder Loop Today-to-Action envelope audit ref recorded.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def capture_memory_context_pack_action_approval(
        self,
        *,
        context_pack_ref: str,
        approval_ref: str,
        idempotency_key_ref: str,
        risk_class: str = "low",
    ) -> dict[str, Any]:
        """Capture a backend-owned approval grant for proposal-state mutation only."""

        _validate_safe_ref(context_pack_ref, "context_pack_ref")
        _validate_safe_ref(approval_ref, "approval_ref")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        context_pack = self._memory_context_pack_payload_for_ref(context_pack_ref)
        if context_pack is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_CONTEXT_PACK_NOT_FOUND")
        context_pack_proposal_ref = str(context_pack["proposal_ref"])
        exact_scope_ref = memory_context_pack_action_scope_ref(context_pack_ref)
        capture_request = MemoryContextPackActionProposalRequest(
            exact_approval_scope_ref=exact_scope_ref,
            approval_ref=approval_ref,
            risk_class=risk_class,  # type: ignore[arg-type]
        )
        approval_request = memory_context_pack_action_approval_request(
            context_pack_ref=context_pack_ref,
            context_pack_proposal_ref=context_pack_proposal_ref,
            actor_context=capture_request.actor_context,
            risk_class=capture_request.risk_class,
            exact_approval_scope_ref=exact_scope_ref,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id="local_operator",
            approval_ref=approval_ref,
        )
        grant_payload = grant.model_dump(mode="json")
        receipt_payload = {
            "contract_ref": "contract-ref:founder-loop-internal-approval-capture:v1",
            "approval_kind": "memory_context_pack_action_proposal",
            "approval_ref": approval_ref,
            "subject_ref": context_pack_ref,
            "requested_action": MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_key_ref": idempotency_key_ref,
            "status": "approved",
            "safe_summary": (
                "Backend-owned approval captured for Memory context-pack "
                "internal Action proposal state only."
            ),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "created_at": _utc_iso(),
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else "",
        }
        _validate_safe_payload(receipt_payload, "memory_context_pack_approval_capture")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO founder_loop_internal_approval_grants (
                    approval_ref, approval_kind, subject_ref, requested_action,
                    exact_scope_ref, idempotency_key_ref, grant_json, receipt_json,
                    created_at, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(approval_ref) DO UPDATE SET
                    approval_kind = excluded.approval_kind,
                    subject_ref = excluded.subject_ref,
                    requested_action = excluded.requested_action,
                    exact_scope_ref = excluded.exact_scope_ref,
                    idempotency_key_ref = excluded.idempotency_key_ref,
                    grant_json = excluded.grant_json,
                    receipt_json = excluded.receipt_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (
                    approval_ref,
                    "memory_context_pack_action_proposal",
                    context_pack_ref,
                    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
                    exact_scope_ref,
                    idempotency_key_ref,
                    _json_dumps(grant_payload),
                    _json_dumps(receipt_payload),
                    str(receipt_payload["created_at"]),
                    str(receipt_payload["expires_at"]),
                ),
            )
        return receipt_payload

    def record_memory_context_pack_action_proposal(
        self,
        *,
        context_pack_ref: str,
        request: MemoryContextPackActionProposalRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        _validate_safe_ref(context_pack_ref, "context_pack_ref")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        context_pack = self._memory_context_pack_payload_for_ref(context_pack_ref)
        if context_pack is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_CONTEXT_PACK_NOT_FOUND")
        expected_scope_ref = memory_context_pack_action_scope_ref(context_pack_ref)
        if (
            request.exact_approval_scope_ref is not None
            and request.exact_approval_scope_ref != expected_scope_ref
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_SCOPE_MISMATCH"
            )
        context_pack_proposal_ref = str(context_pack["proposal_ref"])
        authority_decision = self._memory_context_pack_action_authority_decision(
            context_pack_ref=context_pack_ref,
            context_pack_proposal_ref=context_pack_proposal_ref,
            expected_scope_ref=expected_scope_ref,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=active_authority_leases,
        )
        request = self._request_with_backend_owned_memory_context_pack_action_approval_if_needed(
            context_pack_ref=context_pack_ref,
            context_pack_proposal_ref=context_pack_proposal_ref,
            request=request,
            expected_scope_ref=expected_scope_ref,
            idempotency_key_ref=idempotency_key_ref,
        )

        fingerprint_payload = memory_context_pack_action_payload_for_fingerprint(
            context_pack_ref=context_pack_ref,
            request=request,
        )
        payload_fingerprint_ref = memory_context_pack_action_payload_fingerprint_ref(
            fingerprint_payload
        )
        replay = self._memory_context_pack_action_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._memory_context_pack_action_receipt_by_ref(
                str(replay["receipt_ref"])
            )
            return {
                **receipt,
                "replayed": True,
                "safe_summary": (
                    "Prior Memory context-pack internal Action proposal receipt "
                    "returned for matching idempotency key."
                ),
            }

        approval_status, approval_reason_refs = (
            self._memory_context_pack_action_approval_status(
                context_pack_ref=context_pack_ref,
                context_pack_proposal_ref=context_pack_proposal_ref,
                request=request,
                expected_scope_ref=expected_scope_ref,
                idempotency_key_ref=idempotency_key_ref,
            )
        )
        if approval_status != "approved":
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_APPROVAL_REQUIRED"
            )

        item_ref = memory_context_pack_action_item_ref(context_pack_ref)
        action_envelope_ref = memory_context_pack_action_envelope_ref(context_pack_ref)
        internal_action_proposal_ref = memory_context_pack_action_proposal_ref(
            context_pack_ref,
            idempotency_key_ref,
        )
        receipt_ref = memory_context_pack_action_receipt_ref(
            context_pack_ref,
            idempotency_key_ref,
        )
        audit_ref = memory_context_pack_action_audit_ref(
            context_pack_ref,
            idempotency_key_ref,
        )
        evidence_event_ref = memory_context_pack_action_event_ref(context_pack_ref)
        source_memory_record_refs = list(
            context_pack.get("source_memory_record_refs") or []
        )
        l1_preview_refs = list(context_pack.get("l1_preview_refs") or [])
        l2_projection_refs = list(context_pack.get("l2_projection_refs") or [])
        l3_representation_refs = list(context_pack.get("l3_representation_refs") or [])
        source_refs = list(context_pack.get("source_refs") or [])
        source_evidence_refs = list(context_pack.get("evidence_refs") or [])
        supporting_receipt_refs = list(context_pack.get("receipt_refs") or [])
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:memory-context-pack-action-proposal",
                    evidence_event_ref,
                    context_pack_ref,
                    context_pack_proposal_ref,
                    *source_memory_record_refs,
                    *l1_preview_refs,
                    *l2_projection_refs,
                    *l3_representation_refs,
                    *source_refs,
                    *source_evidence_refs,
                    *supporting_receipt_refs,
                    *request.metadata_refs,
                    authority_decision.decision_ref,
                    authority_decision.audit_record_ref,
                    *(
                        [authority_decision.receipt_ref]
                        if authority_decision.receipt_ref
                        else []
                    ),
                    *(
                        [authority_decision.lease_ref]
                        if authority_decision.lease_ref
                        else []
                    ),
                ]
            )
        )
        rollback_ref = f"rollback-ref:memory-context-pack-action:{_short_ref_suffix(context_pack_ref)}"
        safe_disable_ref = f"safe-disable-ref:memory-context-pack-action:{_short_ref_suffix(context_pack_ref)}"
        receipt = MemoryContextPackActionProposalReceipt(
            context_pack_ref=context_pack_ref,
            context_pack_proposal_ref=context_pack_proposal_ref,
            internal_action_proposal_ref=internal_action_proposal_ref,
            item_ref=item_ref,
            action_envelope_ref=action_envelope_ref,
            exact_approval_scope_ref=expected_scope_ref,
            approval_ref=request.approval_ref,
            approval_status=approval_status,
            approval_reason_refs=approval_reason_refs,
            receipt_ref=receipt_ref,
            audit_ref=audit_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            authority_audit_ref=authority_decision.audit_record_ref,
            authority_policy_receipt_ref=authority_decision.receipt_ref,
            evidence_timeline_event_ref=evidence_event_ref,
            source_memory_record_refs=source_memory_record_refs,
            l1_preview_refs=l1_preview_refs,
            l2_projection_refs=l2_projection_refs,
            l3_representation_refs=l3_representation_refs,
            source_refs=source_refs,
            evidence_refs=evidence_refs,
            supporting_receipt_refs=supporting_receipt_refs,
            rollback_ref=rollback_ref,
            safe_disable_ref=safe_disable_ref,
            blocked_state_refs=list(MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS),
            safe_summary=(
                "Reviewed context-pack safe refs created an internal Action "
                "proposal for review only; execution and external side effects "
                "remain blocked."
            ),
        )
        receipt_payload = receipt.model_dump(mode="json")
        existing_action = self._action_payload_for_item_ref(item_ref)
        receipt_refs = list(
            dict.fromkeys(
                [
                    *list((existing_action or {}).get("receipt_refs") or []),
                    *supporting_receipt_refs,
                    receipt_ref,
                ]
            )
        )
        audit_refs = list(
            dict.fromkeys(
                [*list((existing_action or {}).get("audit_refs") or []), audit_ref]
            )
        )
        action_record = FounderLoopActionRecord(
            item_ref=item_ref,
            title="Action proposal from Memory context pack",
            safe_summary=(
                "Reviewed Memory context-pack safe refs created an internal "
                "Action proposal for review only; execution remains blocked."
            ),
            surface="Memory",
            priority=request.priority,
            risk_class=request.risk_class,
            status="proposed",
            side_effect_class="local_dev_workspace_only",
            authority_boundary=(
                "Memory context-pack hook creates internal Action proposal state "
                "only; exact approval covers proposal creation, not execution."
            ),
            approval_required=True,
            approval_envelope_ref=(
                "approval-envelope:memory-context-pack-action:"
                f"{_short_ref_suffix(context_pack_ref)}"
            ),
            approval_envelope_status=(
                "approved_for_internal_proposal_only_execution_blocked"
            ),
            state_change_contract_ref=MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF,
            state_change_readiness="internal_action_proposal_created_no_execution",
            blocked_state=(
                "External execution, connector writes, CRM/account sync, "
                "shell/browser behavior, provider calls, and context injection blocked."
            ),
            evidence_refs=evidence_refs,
            receipt_refs=receipt_refs,
            audit_refs=audit_refs,
            idempotency_key_ref=idempotency_key_ref,
            expires_at=None,
            stale_state="recheck_context_pack_before_action_decision",
            rollback_ref=rollback_ref,
            safe_disable_ref=safe_disable_ref,
            next_safe_action=(
                "Review the internal Action proposal; action execution remains blocked."
            ),
        )
        envelope_payload = {
            "contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
            "memory_context_pack_action_contract_ref": (
                MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF
            ),
            "route_ref": MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE_REF,
            "status": MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_STATUS,
            "requested_action": MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
            "context_pack_ref": context_pack_ref,
            "context_pack_proposal_ref": context_pack_proposal_ref,
            "internal_action_proposal_ref": internal_action_proposal_ref,
            "item_ref": item_ref,
            "action_envelope_ref": action_envelope_ref,
            "exact_scope_ref": expected_scope_ref,
            "risk_class": request.risk_class,
            "side_effect_class": "local_dev_workspace_only",
            "approval_requirement_ref": (
                "approval-requirement:memory-context-pack-action:"
                f"{_short_ref_suffix(context_pack_ref)}"
            ),
            "approval_ref": request.approval_ref,
            "expected_receipt_ref": receipt_ref,
            "authority_decision_ref": authority_decision.decision_ref,
            "authority_decision_outcome": authority_decision.outcome,
            "authority_lease_ref": authority_decision.lease_ref,
            "authority_domain_ref": MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_DOMAIN_REF,
            "authority_capability_ref": (
                MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_CAPABILITY_REF
            ),
            "authority_required_mode_ref": (
                MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_REQUIRED_MODE_REF
            ),
            "authority_audit_ref": authority_decision.audit_record_ref,
            "authority_policy_receipt_ref": authority_decision.receipt_ref,
            "rollback_ref": rollback_ref,
            "safe_disable_ref": safe_disable_ref,
            "blocked_state_refs": list(MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS),
            "action_execution_enabled": False,
            "connector_write_enabled": False,
            "crm_sync_enabled": False,
            "account_sync_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "browser_automation_enabled": False,
            "model_provider_authority_allowed": False,
            "context_injection_authorized": False,
            "production_authority_enabled": False,
        }
        _validate_safe_payload(envelope_payload, "memory_context_pack_action_proposal")
        with self._connect() as conn:
            self._upsert_action_record(conn, action_record)
            conn.execute(
                """
                INSERT INTO action_envelopes (
                    envelope_ref, item_ref, status, envelope_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    action_envelope_ref,
                    item_ref,
                    "proposed",
                    _json_dumps(envelope_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_envelope_receipts (
                    receipt_ref, item_ref, action_envelope_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_ref,
                    item_ref,
                    action_envelope_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO memory_context_pack_action_proposals (
                    receipt_ref, context_pack_ref, context_pack_proposal_ref,
                    item_ref, action_envelope_ref, proposal_ref, receipt_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_ref,
                    context_pack_ref,
                    context_pack_proposal_ref,
                    item_ref,
                    action_envelope_ref,
                    internal_action_proposal_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO memory_context_pack_action_replays (
                    key_ref, context_pack_ref, payload_fingerprint_ref,
                    receipt_ref, proposal_ref, action_envelope_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    context_pack_ref,
                    payload_fingerprint_ref,
                    receipt_ref,
                    internal_action_proposal_ref,
                    action_envelope_ref,
                    receipt.created_at,
                ),
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": receipt.safe_summary,
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": (
                    "Memory context-pack internal Action proposal audit ref recorded."
                ),
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def _request_with_backend_owned_memory_context_pack_action_approval_if_needed(
        self,
        *,
        context_pack_ref: str,
        context_pack_proposal_ref: str,
        request: MemoryContextPackActionProposalRequest,
        expected_scope_ref: str,
        idempotency_key_ref: str,
    ) -> MemoryContextPackActionProposalRequest:
        updates: dict[str, Any] = {}
        if request.exact_approval_scope_ref is None:
            updates["exact_approval_scope_ref"] = expected_scope_ref
        if request.approval_ref is None:
            approval_ref = (
                "approval-ref:memory-context-pack-action:"
                f"{_safe_suffix(context_pack_ref)}:{_safe_suffix(idempotency_key_ref)}"
            )
            approval_request = memory_context_pack_action_approval_request(
                context_pack_ref=context_pack_ref,
                context_pack_proposal_ref=context_pack_proposal_ref,
                actor_context=request.actor_context,
                risk_class=request.risk_class,
                exact_approval_scope_ref=expected_scope_ref,
            )
            authority = LocalApprovalAuthority()
            authority.create_request(approval_request)
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id=request.actor_context.actor_id,
                approval_ref=approval_ref,
            )
            grant_payload = grant.model_dump(mode="json")
            receipt_payload = {
                "contract_ref": "contract-ref:founder-loop-internal-approval-capture:v1",
                "approval_kind": "memory_context_pack_action_proposal",
                "approval_ref": approval_ref,
                "subject_ref": context_pack_ref,
                "requested_action": MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
                "exact_scope_ref": expected_scope_ref,
                "idempotency_key_ref": idempotency_key_ref,
                "status": "approved",
                "safe_summary": (
                    "Backend-owned approval captured for Memory context-pack "
                    "internal Action proposal state only."
                ),
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "created_at": _utc_iso(),
                "expires_at": (
                    grant.expires_at.isoformat() if grant.expires_at else ""
                ),
            }
            _validate_safe_payload(
                receipt_payload, "memory_context_pack_approval_capture"
            )
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO founder_loop_internal_approval_grants (
                        approval_ref, approval_kind, subject_ref, requested_action,
                        exact_scope_ref, idempotency_key_ref, grant_json, receipt_json,
                        created_at, expires_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(approval_ref) DO UPDATE SET
                        approval_kind = excluded.approval_kind,
                        subject_ref = excluded.subject_ref,
                        requested_action = excluded.requested_action,
                        exact_scope_ref = excluded.exact_scope_ref,
                        idempotency_key_ref = excluded.idempotency_key_ref,
                        grant_json = excluded.grant_json,
                        receipt_json = excluded.receipt_json,
                        created_at = excluded.created_at,
                        expires_at = excluded.expires_at
                    """,
                    (
                        approval_ref,
                        "memory_context_pack_action_proposal",
                        context_pack_ref,
                        MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
                        expected_scope_ref,
                        idempotency_key_ref,
                        _json_dumps(grant_payload),
                        _json_dumps(receipt_payload),
                        str(receipt_payload["created_at"]),
                        str(receipt_payload["expires_at"]),
                    ),
                )
            updates["approval_ref"] = approval_ref
        if not updates:
            return request
        return request.model_copy(update=updates)

    def latest_action_receipt(self, action_id: str) -> dict[str, Any] | None:
        item_ref = action_id_to_item_ref(action_id)
        local_task_rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM local_task_commit_receipts
            WHERE item_ref = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (item_ref,),
        )
        if local_task_rows:
            return dict(json.loads(str(local_task_rows[0]["receipt_json"])))
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM action_receipts
            WHERE item_ref = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (item_ref,),
        )
        if not rows:
            return None
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _historical_action_approval_evidence_for_committed_receipt(
        self,
        receipt: FounderLoopLocalTaskCommitReceipt,
    ) -> dict[str, Any] | None:
        matching_receipts: list[FounderLoopActionDecisionReceipt] = []
        for payload in self._action_decision_receipts_for_item_ref(receipt.item_ref):
            if payload.get("approval_ref") != receipt.approval_ref:
                continue
            try:
                decision_receipt = FounderLoopActionDecisionReceipt.model_validate(
                    payload
                )
            except ValueError:
                return None
            if (
                decision_receipt.decision != "approve"
                or decision_receipt.status != "approved"
                or decision_receipt.approval_status != "approved"
            ):
                return None
            matching_receipts.append(decision_receipt)
        if len(matching_receipts) != 1:
            return None
        decision_receipt = matching_receipts[0]

        rows = self._fetch_all(
            """
            SELECT approval_kind, subject_ref, requested_action,
                   exact_scope_ref, idempotency_key_ref,
                   grant_json, receipt_json
            FROM founder_loop_internal_approval_grants
            WHERE approval_ref = ?
            LIMIT 1
            """,
            (receipt.approval_ref,),
        )
        if len(rows) != 1:
            return None
        row = dict(rows[0])
        revision_rows = self._fetch_all(
            """
            SELECT state_json
            FROM action_revision_state
            WHERE item_ref = ?
            LIMIT 1
            """,
            (receipt.item_ref,),
        )
        if len(revision_rows) != 1:
            return None
        try:
            grant = ApprovalGrant.model_validate(json.loads(str(row["grant_json"])))
            approval_evidence = dict(json.loads(str(row["receipt_json"])))
            terminal_revision = dict(
                json.loads(str(revision_rows[0]["state_json"]))
            )
            _validate_safe_payload(
                approval_evidence,
                "historical_action_approval_evidence",
            )
            _validate_safe_payload(
                terminal_revision,
                "historical_action_terminal_revision",
            )
            commit_created_at = datetime.fromisoformat(
                receipt.created_at.replace("Z", "+00:00")
            )
            decision_created_at = datetime.fromisoformat(
                decision_receipt.created_at.replace("Z", "+00:00")
            )
            evidence_created_at = datetime.fromisoformat(
                str(approval_evidence["created_at"]).replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

        row_bindings = {
            "approval_kind": "founder_loop_action_decision",
            "subject_ref": receipt.item_ref,
            "requested_action": ACTION_DECISION_REQUESTED_ACTION,
            "exact_scope_ref": decision_receipt.approval_scope_ref,
            "idempotency_key_ref": decision_receipt.idempotency_key_ref,
        }
        if any(row.get(field) != expected for field, expected in row_bindings.items()):
            return None
        evidence_bindings: dict[str, Any] = {
            "approval_kind": "founder_loop_action_decision",
            "approval_ref": receipt.approval_ref,
            "subject_ref": receipt.item_ref,
            "requested_action": ACTION_DECISION_REQUESTED_ACTION,
            "exact_scope_ref": decision_receipt.approval_scope_ref,
            "idempotency_key_ref": decision_receipt.idempotency_key_ref,
            "generation_ref": decision_receipt.generation_ref,
            "revision_ref": decision_receipt.revision_ref,
            "revision_fingerprint_ref": decision_receipt.revision_fingerprint_ref,
            "payload_fingerprint_ref": decision_receipt.payload_fingerprint_ref,
            "decision_route_binding_ref": (
                decision_receipt.decision_route_binding_ref
            ),
            "decision_adapter_ref": decision_receipt.decision_adapter_ref,
            "decision_deadline_ref": decision_receipt.decision_deadline_ref,
            "authority_input_refs": decision_receipt.authority_input_refs,
        }
        if any(
            approval_evidence.get(field) != expected
            for field, expected in evidence_bindings.items()
        ):
            return None
        if (
            grant.approval_ref != receipt.approval_ref
            or grant.subject_id != receipt.item_ref
            or ACTION_DECISION_REQUESTED_ACTION not in grant.approved_actions
        ):
            return None
        required_resource_refs = {
            receipt.item_ref,
            decision_receipt.approval_scope_ref,
            decision_receipt.generation_ref,
            decision_receipt.revision_ref,
            decision_receipt.revision_fingerprint_ref,
            decision_receipt.payload_fingerprint_ref,
            decision_receipt.decision_route_binding_ref,
            decision_receipt.decision_adapter_ref,
            decision_receipt.decision_deadline_ref,
            *decision_receipt.authority_input_refs,
        }
        if not required_resource_refs.issubset(set(grant.approved_resource_refs)):
            return None
        if (
            decision_created_at > commit_created_at
            or evidence_created_at > commit_created_at
            or grant.created_at > commit_created_at
            or grant.expires_at is None
            or grant.expires_at < commit_created_at
            or approval_evidence.get("expires_at") != grant.expires_at.isoformat()
        ):
            return None

        evidence_status = approval_evidence.get("status")
        if evidence_status == "approved":
            if (
                grant.status != ApprovalStatus.granted.value
                or grant.revoked_at is not None
            ):
                return None
        elif evidence_status == "invalidated":
            invalidation_reason_ref = approval_evidence.get(
                "invalidation_reason_ref"
            )
            invalidated_by_revision_ref = approval_evidence.get(
                "invalidated_by_revision_ref"
            )
            try:
                _validate_safe_ref(
                    invalidation_reason_ref,
                    "invalidation_reason_ref",
                )
                _validate_safe_ref(
                    invalidated_by_revision_ref,
                    "invalidated_by_revision_ref",
                )
            except (TypeError, ValueError):
                return None
            if (
                grant.status != ApprovalStatus.revoked.value
                or grant.revoked_at is None
                or grant.metadata.get("revocation_reason_ref")
                != invalidation_reason_ref
                or grant.metadata.get("invalidated_by_revision_ref")
                != invalidated_by_revision_ref
                or invalidated_by_revision_ref
                != terminal_revision.get("revision_ref")
                or terminal_revision.get("generation")
                != decision_receipt.result_generation + 1
                or terminal_revision.get("previous_revision_ref")
                != decision_receipt.result_revision_ref
                or terminal_revision.get("transition_ref")
                != "revision-transition:action-inbox:local-task-commit"
            ):
                return None
        else:
            return None
        return decision_receipt.model_dump(mode="json")

    def validated_local_task_commit_receipt(
        self,
        receipt_ref: str,
    ) -> dict[str, Any]:
        """Load an exact local-task receipt and verify its durable bindings."""
        _validate_safe_ref(receipt_ref, "receipt_ref")
        rows = self._fetch_all(
            """
            SELECT receipts.receipt_ref AS stored_receipt_ref,
                   receipts.item_ref AS stored_item_ref,
                   receipts.local_task_ref AS stored_local_task_ref,
                   receipts.receipt_json,
                   replays.key_ref AS replay_key_ref,
                   replays.item_ref AS replay_item_ref,
                   replays.local_task_ref AS replay_local_task_ref,
                   replays.payload_fingerprint_ref AS replay_payload_fingerprint_ref,
                   replays.receipt_ref AS replay_receipt_ref,
                   tasks.status AS task_status,
                   tasks.item_ref AS task_item_ref,
                   tasks.action_kind AS task_action_kind,
                   tasks.evidence_refs_json AS task_evidence_refs_json,
                   tasks.receipt_ref AS task_receipt_ref
            FROM local_task_commit_receipts AS receipts
            LEFT JOIN local_task_commit_replays AS replays
              ON replays.receipt_ref = receipts.receipt_ref
            LEFT JOIN local_tasks AS tasks
              ON tasks.local_task_ref = receipts.local_task_ref
            WHERE receipts.receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_RECEIPT_NOT_FOUND")
        row = dict(rows[0])
        try:
            receipt = FounderLoopLocalTaskCommitReceipt(
                **dict(json.loads(str(row["receipt_json"])))
            )
            task_evidence_refs = list(json.loads(str(row["task_evidence_refs_json"])))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_INVALID"
            ) from exc

        expected_bindings = {
            "stored_receipt_ref": receipt.receipt_ref,
            "stored_item_ref": receipt.item_ref,
            "stored_local_task_ref": receipt.local_task_ref,
            "replay_key_ref": receipt.idempotency_key_ref,
            "replay_item_ref": receipt.item_ref,
            "replay_local_task_ref": receipt.local_task_ref,
            "replay_payload_fingerprint_ref": receipt.payload_fingerprint_ref,
            "replay_receipt_ref": receipt.receipt_ref,
            "task_status": receipt.status,
            "task_item_ref": receipt.item_ref,
            "task_action_kind": FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
            "task_receipt_ref": receipt.receipt_ref,
        }
        if any(
            row.get(field) != expected for field, expected in expected_bindings.items()
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        if receipt.local_task_ref != local_task_ref_for_action(receipt.item_ref):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        if receipt.receipt_ref != local_task_commit_receipt_ref(
            receipt.item_ref,
            receipt.idempotency_key_ref,
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        if receipt.audit_ref != local_task_commit_audit_ref(
            receipt.item_ref,
            receipt.idempotency_key_ref,
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        if receipt.evidence_timeline_event_ref != local_task_commit_event_ref(
            receipt.item_ref
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        if task_evidence_refs != receipt.evidence_refs:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        expected_authority_bindings = {
            "contract_ref": FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
            "approval_status": "approved",
            "authority_domain_ref": FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DOMAIN_REF,
            "authority_capability_ref": (
                FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_CAPABILITY_REF
            ),
            "authority_required_mode_ref": (
                FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_MODE_REF
            ),
            "safe_disable_ref": FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
            "rollback_ref": FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
            "safe_disable_posture_ref": (
                FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF
            ),
        }
        if any(
            getattr(receipt, field) != expected
            for field, expected in expected_authority_bindings.items()
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_AUTHORITY_MISMATCH"
            )
        if (
            not receipt.approval_reason_refs
            or receipt.authority_decision_ref is None
            or receipt.authority_decision_outcome
            not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }
            or receipt.authority_lease_ref is None
            or not receipt.safe_disable_enabled
            or receipt.rollback_execution_enabled
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_AUTHORITY_MISMATCH"
            )
        expected_authority_refs = local_task_authority_proof_refs(
            authority_lease_ref=str(receipt.authority_lease_ref),
            authority_decision_outcome=str(receipt.authority_decision_outcome),
        )
        if (
            receipt.authority_decision_ref
            != expected_authority_refs["authority_decision_ref"]
            or receipt.authority_audit_ref
            != expected_authority_refs["authority_audit_ref"]
            or receipt.authority_policy_receipt_ref
            != expected_authority_refs["authority_policy_receipt_ref"]
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_AUTHORITY_MISMATCH"
            )

        action = self._action_payload_for_item_ref(receipt.item_ref)
        if action is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_ACTION_NOT_FOUND"
            )
        projected = {**action, **self._local_task_commit_projection(action)}
        approval_receipt = (
            self._historical_action_approval_evidence_for_committed_receipt(
                receipt
            )
        )
        if (
            projected.get("action_kind") != FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
            or projected.get("local_task_ref") != receipt.local_task_ref
            or projected.get("local_task_commit_receipt_ref") != receipt.receipt_ref
            or projected.get("local_task_commit_approval_ref") != receipt.approval_ref
            or receipt.receipt_ref not in list(projected.get("receipt_refs") or [])
            or receipt.audit_ref not in list(projected.get("audit_refs") or [])
            or not set(receipt.evidence_refs).issubset(
                set(projected.get("evidence_refs") or [])
            )
            or approval_receipt is None
            or approval_receipt.get("approval_ref") != receipt.approval_ref
            or approval_receipt.get("approval_status") != "approved"
            or approval_receipt.get("authority_domain_ref")
            != FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DOMAIN_REF
            or approval_receipt.get("authority_capability_ref")
            != FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_CAPABILITY_REF
            or approval_receipt.get("authority_required_mode_ref")
            != FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_MODE_REF
            or approval_receipt.get("authority_lease_ref")
            != receipt.authority_lease_ref
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_RECEIPT_BINDING_MISMATCH"
            )
        return receipt.model_dump(mode="json")

    def local_task_safe_disable_posture(
        self,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
            SELECT lane_id, enabled, safe_disable_ref, rollback_ref,
                   safe_disable_posture_ref, disabled_reason_refs_json,
                   blocked_state_refs_json, updated_at
            FROM local_task_lane_postures
            WHERE lane_id = ?
            LIMIT 1
            """
        query_params = (FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,)
        rows = (
            self._fetch_all(query, query_params)
            if conn is None
            else list(conn.execute(query, query_params).fetchall())
        )
        if not rows:
            if conn is None:
                with self._connect() as posture_conn:
                    self._ensure_local_task_lane_posture(posture_conn)
                rows = self._fetch_all(query, query_params)
            else:
                self._ensure_local_task_lane_posture(conn)
                rows = list(conn.execute(query, query_params).fetchall())
        payload = _row_to_payload(rows[0])
        enabled = bool(payload.get("enabled"))
        disabled_reason_refs = list(payload.get("disabled_reason_refs") or [])
        blocked_state_refs = list(payload.get("blocked_state_refs") or [])
        if (
            not enabled
            and FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
            not in blocked_state_refs
        ):
            blocked_state_refs.append(FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF)
        posture = {
            "schema_version": "founder_loop_local_task_safe_disable_posture.v1",
            "source": "python_core_founder_loop_storage",
            "backend_owned": True,
            "lane_id": FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
            "action_kind": FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
            "local_task_commits_enabled": enabled,
            "safe_disable_active": not enabled,
            "safe_disable_ref": str(payload["safe_disable_ref"]),
            "rollback_ref": str(payload["rollback_ref"]),
            "safe_disable_posture_ref": str(payload["safe_disable_posture_ref"]),
            "disabled_reason_refs": disabled_reason_refs,
            "blocked_state_refs": blocked_state_refs,
            "rollback_execution_enabled": False,
            "rollback_blocker_refs": [FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF],
            "next_safe_action": (
                "Commit exact-scoped approved local tasks through the local-task route."
                if enabled
                else "Keep local task creation disabled until backend posture is re-enabled."
            ),
            "updated_at": str(payload["updated_at"]),
        }
        _validate_safe_payload(posture, "local_task_safe_disable_posture")
        return posture

    def _disable_local_task_create_lane_for_test(
        self,
        *,
        disabled_reason_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        reason_refs = list(disabled_reason_refs or [])
        if not reason_refs:
            reason_refs = ["safe-disable-reason:local-task-create-disabled"]
        for ref_value in reason_refs:
            _validate_safe_ref(ref_value, "disabled_reason_refs")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO local_task_lane_postures (
                    lane_id, enabled, safe_disable_ref, rollback_ref,
                    safe_disable_posture_ref, disabled_reason_refs_json,
                    blocked_state_refs_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lane_id) DO UPDATE SET
                    enabled = excluded.enabled,
                    safe_disable_ref = excluded.safe_disable_ref,
                    rollback_ref = excluded.rollback_ref,
                    safe_disable_posture_ref = excluded.safe_disable_posture_ref,
                    disabled_reason_refs_json = excluded.disabled_reason_refs_json,
                    blocked_state_refs_json = excluded.blocked_state_refs_json,
                    updated_at = excluded.updated_at
                """,
                (
                    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
                    0,
                    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
                    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
                    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_POSTURE_REF,
                    _json_dumps(reason_refs),
                    _json_dumps([FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF]),
                    _utc_iso(),
                ),
            )
        return self.local_task_safe_disable_posture()

    def memory_review_write_safe_disable_posture(self) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT lane_id, enabled, safe_disable_ref, rollback_ref,
                   safe_disable_posture_ref, disabled_reason_refs_json,
                   blocked_state_refs_json, updated_at
            FROM memory_review_write_lane_postures
            WHERE lane_id = ?
            LIMIT 1
            """,
            (MEMORY_REVIEW_WRITE_LANE_ID,),
        )
        if not rows:
            with self._connect() as conn:
                self._ensure_memory_review_write_lane_posture(conn)
            rows = self._fetch_all(
                """
                SELECT lane_id, enabled, safe_disable_ref, rollback_ref,
                       safe_disable_posture_ref, disabled_reason_refs_json,
                       blocked_state_refs_json, updated_at
                FROM memory_review_write_lane_postures
                WHERE lane_id = ?
                LIMIT 1
                """,
                (MEMORY_REVIEW_WRITE_LANE_ID,),
            )
        payload = _row_to_payload(rows[0])
        enabled = bool(payload.get("enabled"))
        disabled_reason_refs = list(payload.get("disabled_reason_refs") or [])
        blocked_state_refs = list(payload.get("blocked_state_refs") or [])
        if (
            not enabled
            and MEMORY_REVIEW_WRITE_SAFE_DISABLED_BLOCKED_REF not in blocked_state_refs
        ):
            blocked_state_refs.append(MEMORY_REVIEW_WRITE_SAFE_DISABLED_BLOCKED_REF)
        posture = {
            "schema_version": "memory_review_write_safe_disable_posture.v1",
            "source": "python_core_founder_loop_storage",
            "backend_owned": True,
            "lane_id": MEMORY_REVIEW_WRITE_LANE_ID,
            "exact_scope_ref": MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
            "memory_review_writes_enabled": enabled,
            "safe_disable_active": not enabled,
            "safe_disable_ref": str(payload["safe_disable_ref"]),
            "rollback_ref": str(payload["rollback_ref"]),
            "safe_disable_posture_ref": str(payload["safe_disable_posture_ref"]),
            "disabled_reason_refs": disabled_reason_refs,
            "blocked_state_refs": blocked_state_refs,
            "rollback_execution_enabled": False,
            "rollback_blocker_refs": [MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF],
            "rollback_posture": (
                "Terminal reject, merge, supersede, or forget-request decisions "
                "suppress reviewed recall records without deleting audit history."
            ),
            "next_safe_action": (
                "Record exact-scoped accept/correct reviewed recall writes."
                if enabled
                else "Keep reviewed recall writes disabled until backend posture is re-enabled."
            ),
            "updated_at": str(payload["updated_at"]),
        }
        _validate_safe_payload(posture, "memory_review_write_safe_disable_posture")
        return posture

    def _disable_memory_review_write_lane_for_test(
        self,
        *,
        disabled_reason_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        reason_refs = list(disabled_reason_refs or [])
        if not reason_refs:
            reason_refs = ["safe-disable-reason:memory-review-write-disabled"]
        for ref_value in reason_refs:
            _validate_safe_ref(ref_value, "disabled_reason_refs")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_review_write_lane_postures (
                    lane_id, enabled, safe_disable_ref, rollback_ref,
                    safe_disable_posture_ref, disabled_reason_refs_json,
                    blocked_state_refs_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lane_id) DO UPDATE SET
                    enabled = excluded.enabled,
                    safe_disable_ref = excluded.safe_disable_ref,
                    rollback_ref = excluded.rollback_ref,
                    safe_disable_posture_ref = excluded.safe_disable_posture_ref,
                    disabled_reason_refs_json = excluded.disabled_reason_refs_json,
                    blocked_state_refs_json = excluded.blocked_state_refs_json,
                    updated_at = excluded.updated_at
                """,
                (
                    MEMORY_REVIEW_WRITE_LANE_ID,
                    0,
                    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
                    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
                    MEMORY_REVIEW_WRITE_SAFE_DISABLED_POSTURE_REF,
                    _json_dumps(reason_refs),
                    _json_dumps([MEMORY_REVIEW_WRITE_SAFE_DISABLED_BLOCKED_REF]),
                    _utc_iso(),
                ),
            )
        return self.memory_review_write_safe_disable_posture()

    def commit_local_task(
        self,
        *,
        action_id: str,
        request: FounderLoopLocalTaskCommitRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        item_ref = action_id_to_item_ref(action_id)
        action = self._action_payload_for_item_ref(item_ref)
        if action is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
        action = {**action, **_action_envelope_contract_payload(action)}
        if action.get("action_kind") != FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_UNSUPPORTED_ACTION_KIND"
            )

        payload_fingerprint_ref = local_task_commit_payload_fingerprint_ref(
            local_task_commit_payload_for_fingerprint(
                item_ref=item_ref,
                request=request,
            )
        )
        replay = self._local_task_commit_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_LOCAL_TASK_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._local_task_commit_receipt_by_ref(str(replay["receipt_ref"]))
            return {
                **receipt,
                "replayed": True,
                "safe_summary": "Prior local task commit receipt returned for matching idempotency key.",
            }

        local_task_ref = local_task_ref_for_action(item_ref)
        safe_disable_posture = self.local_task_safe_disable_posture()
        if self._latest_local_task_commit_receipt_for_item_ref(item_ref) is not None:
            raise FounderLoopStorageDuplicateError(
                "FOUNDER_LOOP_LOCAL_TASK_ALREADY_COMMITTED"
            )
        approval_receipt = self._latest_approved_action_decision_receipt_for_item_ref(
            item_ref
        )
        blocked_reasons = self._local_task_commit_blocked_reasons(
            action=action,
            local_task_ref=local_task_ref,
            receipt=None,
            approval_receipt=approval_receipt,
            safe_disable_posture=safe_disable_posture,
        )
        if blocked_reasons:
            if FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF in blocked_reasons:
                raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED")
            if "blocked-state:action-not-approved" in blocked_reasons:
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_REQUIRED"
                )
            raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED")
        approval_status, approval_reason_refs = self._local_task_approval_status(
            action=action,
            request=request,
            local_task_ref=local_task_ref,
            idempotency_key_ref=idempotency_key_ref,
        )
        if approval_status != "approved":
            raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED")
        authority_decision = self._local_task_authority_decision(
            item_ref=item_ref,
            local_task_ref=local_task_ref,
            idempotency_key_ref=idempotency_key_ref,
        )

        receipt_ref = local_task_commit_receipt_ref(item_ref, idempotency_key_ref)
        audit_ref = local_task_commit_audit_ref(item_ref, idempotency_key_ref)
        evidence_event_ref = local_task_commit_event_ref(item_ref)
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:local-task-commit",
                    "evidence-ref:founder-loop:action-inbox",
                    evidence_event_ref,
                    authority_decision.decision_ref,
                    authority_decision.audit_record_ref,
                    *(
                        [authority_decision.receipt_ref]
                        if authority_decision.receipt_ref
                        else []
                    ),
                    *(
                        [authority_decision.lease_ref]
                        if authority_decision.lease_ref
                        else []
                    ),
                    *list(action.get("evidence_refs") or []),
                    *request.metadata_refs,
                ]
            )
        )
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            locked_safe_disable_posture = self.local_task_safe_disable_posture(
                conn=conn
            )
            locked_action = self._action_payload_for_item_ref(item_ref, conn=conn)
            if locked_action is None:
                raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
            locked_action = {
                **locked_action,
                **_action_envelope_contract_payload(locked_action),
            }
            locked_approval_receipt = (
                self._latest_approved_action_decision_receipt_for_item_ref(
                    item_ref,
                    conn=conn,
                    action=locked_action,
                )
            )
            locked_blocked_reasons = self._local_task_commit_blocked_reasons(
                action=locked_action,
                local_task_ref=local_task_ref,
                receipt=self._latest_local_task_commit_receipt_for_item_ref(
                    item_ref,
                    conn=conn,
                ),
                approval_receipt=locked_approval_receipt,
                safe_disable_posture=locked_safe_disable_posture,
            )
            if (
                locked_blocked_reasons
                or locked_approval_receipt is None
                or locked_approval_receipt.get("approval_ref") != request.approval_ref
            ):
                if FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF in (
                    locked_blocked_reasons
                ):
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED"
                    )
                if "blocked-state:action-not-approved" in locked_blocked_reasons:
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_REQUIRED"
                    )
                raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED")
            receipt = FounderLoopLocalTaskCommitReceipt(
                item_ref=item_ref,
                local_task_ref=local_task_ref,
                receipt_ref=receipt_ref,
                audit_ref=audit_ref,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                run_ref=FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
                evidence_timeline_event_ref=evidence_event_ref,
                approval_ref=request.approval_ref,
                approval_status=approval_status,
                approval_reason_refs=approval_reason_refs,
                authority_decision_ref=authority_decision.decision_ref,
                authority_decision_outcome=authority_decision.outcome,
                authority_lease_ref=authority_decision.lease_ref,
                authority_audit_ref=authority_decision.audit_record_ref,
                authority_policy_receipt_ref=authority_decision.receipt_ref,
                safe_disable_ref=str(locked_safe_disable_posture["safe_disable_ref"]),
                rollback_ref=str(locked_safe_disable_posture["rollback_ref"]),
                safe_disable_posture_ref=str(
                    locked_safe_disable_posture["safe_disable_posture_ref"]
                ),
                safe_disable_enabled=bool(
                    locked_safe_disable_posture["local_task_commits_enabled"]
                ),
                rollback_execution_enabled=bool(
                    locked_safe_disable_posture["rollback_execution_enabled"]
                ),
                rollback_blocker_refs=list(
                    locked_safe_disable_posture["rollback_blocker_refs"]
                ),
                safe_summary=(
                    "Approved Action Inbox local task was committed to local "
                    "Founder Loop state."
                ),
                evidence_refs=evidence_refs,
                blocked_state_refs=list(FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS),
            )
            receipt_payload = receipt.model_dump(mode="json")
            conn.execute(
                """
                INSERT INTO local_tasks (
                    local_task_ref, item_ref, action_kind, status, safe_summary,
                    evidence_refs_json, receipt_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.local_task_ref,
                    receipt.item_ref,
                    receipt.action_kind,
                    receipt.status,
                    receipt.safe_summary,
                    _json_dumps(receipt.evidence_refs),
                    receipt.receipt_ref,
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO local_task_commit_receipts (
                    receipt_ref, item_ref, local_task_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_ref,
                    receipt.item_ref,
                    receipt.local_task_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO local_task_commit_replays (
                    key_ref, item_ref, local_task_ref, payload_fingerprint_ref,
                    receipt_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    receipt.item_ref,
                    receipt.local_task_ref,
                    payload_fingerprint_ref,
                    receipt.receipt_ref,
                    receipt.created_at,
                ),
            )
            self._update_action_projection_after_local_task_commit(
                conn=conn,
                action=locked_action,
                receipt=receipt,
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": receipt.safe_summary,
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": "Founder Loop local task commit audit ref recorded.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def record_action_decision(
        self,
        *,
        action_id: str,
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        if decision not in FOUNDER_LOOP_ACTION_DECISION_KINDS:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_DECISION_UNSUPPORTED")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        item_ref = action_id_to_item_ref(action_id)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            action = self._action_payload_for_item_ref(
                item_ref,
                conn=conn,
                include_generated=False,
            )
            if action is None and decision == "defer":
                generated_action = self._generated_action_payload_for_item_ref(item_ref)
                if generated_action is not None:
                    generated_record = {
                        field_name: generated_action[field_name]
                        for field_name in FounderLoopActionRecord.model_fields
                        if field_name in generated_action
                    }
                    self._upsert_action_record(
                        conn,
                        FounderLoopActionRecord.model_validate(generated_record),
                    )
                    action = self._action_payload_for_item_ref(
                        item_ref,
                        conn=conn,
                        include_generated=False,
                    )
            if action is None:
                raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
            action = {**action, **_action_envelope_contract_payload(action)}
            replay_rows = list(
                conn.execute(
                    """
                    SELECT item_ref, decision, payload_fingerprint_ref, receipt_ref
                    FROM action_idempotency_replays
                    WHERE key_ref = ?
                    LIMIT 1
                    """,
                    (idempotency_key_ref,),
                ).fetchall()
            )
            if replay_rows:
                replay = dict(replay_rows[0])
                receipt_rows = list(
                    conn.execute(
                        """
                        SELECT receipt_json
                        FROM action_receipts
                        WHERE receipt_ref = ?
                        LIMIT 1
                        """,
                        (str(replay["receipt_ref"]),),
                    ).fetchall()
                )
                if not receipt_rows:
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_ACTION_RECEIPT_NOT_FOUND"
                    )
                prior_receipt = dict(json.loads(str(receipt_rows[0]["receipt_json"])))
                revision_receipt_fields = (
                    "generation_ref",
                    "revision_fingerprint_ref",
                    "decision_route_ref",
                    "decision_route_binding_ref",
                    "decision_deadline_ref",
                )
                if any(
                    not isinstance(prior_receipt.get(field), str)
                    for field in revision_receipt_fields
                ):
                    raise FounderLoopStorageDuplicateError(
                        "FOUNDER_LOOP_ACTION_IDEMPOTENCY_LEGACY_CONFLICT"
                    )
                replay_request = request
                deterministic_approval_ref = self._action_approval_ref(
                    item_ref=item_ref,
                    idempotency_key_ref=idempotency_key_ref,
                )
                if (
                    request.approval_ref is None
                    and prior_receipt.get("approval_ref") == deterministic_approval_ref
                ):
                    replay_request = request.model_copy(
                        update={"approval_ref": deterministic_approval_ref}
                    )
                replay_fingerprint = self._action_decision_payload_fingerprint(
                    item_ref=item_ref,
                    decision=decision,
                    request=replay_request,
                    generation_ref=str(prior_receipt["generation_ref"]),
                    revision_fingerprint_ref=str(
                        prior_receipt["revision_fingerprint_ref"]
                    ),
                    decision_route=str(prior_receipt["decision_route_ref"]),
                    decision_route_binding=str(
                        prior_receipt["decision_route_binding_ref"]
                    ),
                    decision_deadline=str(prior_receipt["decision_deadline_ref"]),
                )
                if (
                    replay.get("item_ref") != item_ref
                    or replay.get("decision") != decision
                    or replay.get("payload_fingerprint_ref") != replay_fingerprint
                ):
                    raise FounderLoopStorageDuplicateError(
                        "FOUNDER_LOOP_ACTION_IDEMPOTENCY_CONFLICT"
                    )
                return {
                    **prior_receipt,
                    "replayed": True,
                    "safe_summary": (
                        "Prior Action decision receipt returned for matching "
                        "idempotency key and revision-bound payload."
                    ),
                }

            if (
                self._latest_local_task_commit_receipt_for_item_ref(
                    item_ref,
                    conn=conn,
                )
                is not None
            ):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_ACTION_TERMINAL_LOCAL_TASK_COMMITTED"
                )

            current_revision, revision_state_synchronized = (
                self._synchronize_action_revision_state(
                    action,
                    conn=conn,
                )
            )
            if request.expected_revision_ref != current_revision["revision_ref"]:
                if revision_state_synchronized:
                    conn.commit()
                raise FounderLoopActionRevisionConflict(
                    current_revision_ref=str(current_revision["revision_ref"]),
                    current_generation_ref=str(current_revision["generation_ref"]),
                )
            if _is_expired_iso_datetime(action.get("expires_at")):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_ACTION_DECISION_DEADLINE_EXPIRED"
                )
            decision_route = action_decision_route_ref(decision)
            decision_route_binding = action_decision_route_binding_ref(decision)
            decision_deadline = action_decision_deadline_ref(
                item_ref,
                int(current_revision["generation"]),
                str(action.get("expires_at") or "expiry-not-set"),
            )
            authority_decision = self._action_decision_authority_decision(
                item_ref=item_ref,
                decision=decision,
                idempotency_key_ref=idempotency_key_ref,
                revision_state=current_revision,
                decision_route_binding_ref=decision_route_binding,
                decision_deadline_ref=decision_deadline,
                active_authority_leases=active_authority_leases,
            )
            authority_allowed = authority_decision.outcome in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }
            receipt_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM action_receipts
                    WHERE item_ref = ?
                    """,
                    (item_ref,),
                ).fetchone()["count"]
            )
            active_approval = (
                self._latest_approved_action_decision_receipt_for_item_ref(
                    item_ref,
                    conn=conn,
                    action=action,
                )
            )
            decision_invalidates_approval = decision == "cancel" or (
                decision == "edit" and request.edited_envelope_ref is not None
            )
            invalidation_overflow_allowed = (
                authority_allowed
                and decision_invalidates_approval
                and active_approval is not None
            )
            if (
                receipt_count >= FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM
                and not invalidation_overflow_allowed
            ):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED"
                )
            effective_request = request
            if (
                authority_allowed
                and decision == "approve"
                and request.approval_ref is None
            ):
                effective_request = request.model_copy(
                    update={
                        "approval_ref": self._action_approval_ref(
                            item_ref=item_ref,
                            idempotency_key_ref=idempotency_key_ref,
                        ),
                        "approval_grants": [],
                    }
                )
            payload_fingerprint_ref = self._action_decision_payload_fingerprint(
                item_ref=item_ref,
                decision=decision,
                request=effective_request,
                generation_ref=str(current_revision["generation_ref"]),
                revision_fingerprint_ref=str(
                    current_revision["revision_fingerprint_ref"]
                ),
                decision_route=decision_route,
                decision_route_binding=decision_route_binding,
                decision_deadline=decision_deadline,
            )
            approval_scope_ref = action_decision_approval_scope_ref(
                expected_revision_ref=str(current_revision["revision_ref"]),
                payload_fingerprint_ref=payload_fingerprint_ref,
                decision_route_binding_ref=decision_route_binding,
                decision_adapter_ref=FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
                decision_deadline_ref=decision_deadline,
                authority_input_refs=list(
                    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS
                ),
            )
            captured_grant: ApprovalGrant | None = None
            if (
                authority_allowed
                and decision == "approve"
                and request.approval_ref is None
            ):
                captured_grant = self._capture_backend_owned_action_approval(
                    conn=conn,
                    action=action,
                    decision=decision,
                    request=effective_request,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    approval_scope_ref=approval_scope_ref,
                    revision_state=current_revision,
                    decision_route_binding_ref=decision_route_binding,
                    decision_deadline_ref=decision_deadline,
                )

            if authority_allowed:
                decision_status = self._decision_status(
                    action=action,
                    decision=decision,
                    request=effective_request,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    approval_scope_ref=approval_scope_ref,
                    revision_state=current_revision,
                    decision_route_binding_ref=decision_route_binding,
                    decision_deadline_ref=decision_deadline,
                    captured_grant=captured_grant,
                    conn=conn,
                )
            else:
                decision_status = (
                    "blocked",
                    "authority_denied",
                    list(
                        dict.fromkeys(
                            [
                                *authority_decision.reason_refs,
                                FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF,
                            ]
                        )
                    ),
                )

            local_task_approved = (
                action.get("action_kind") == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
                and decision_status[0] == "approved"
            )
            projection_expires_at = (
                _utc_iso_after(hours=1)
                if local_task_approved
                else action.get("expires_at")
            )
            result_revision = current_revision
            invalidated_approval_refs: list[str] = []
            revision_changing_statuses = {
                "approved",
                "edited",
                "rejected",
                "deferred",
                "cancelled",
            }
            if decision_status[0] in revision_changing_statuses:
                next_action = {
                    **action,
                    "approval_envelope_ref": (
                        effective_request.edited_envelope_ref
                        if decision_status[0] == "edited"
                        else None
                        if decision_status[0] == "cancelled"
                        else action.get("approval_envelope_ref")
                    ),
                    "status": decision_status[0],
                    "expires_at": projection_expires_at,
                }
                result_revision = _build_action_revision_state(
                    next_action,
                    generation=int(current_revision["generation"]) + 1,
                    previous_revision_ref=str(current_revision["revision_ref"]),
                    transition_ref=(
                        "revision-transition:action-inbox:edit"
                        if decision_status[0] == "edited"
                        else "revision-transition:action-inbox:cancel"
                        if decision_status[0] == "cancelled"
                        else "revision-transition:action-inbox:reject"
                        if decision_status[0] == "rejected"
                        else "revision-transition:action-inbox:defer"
                        if decision_status[0] == "deferred"
                        else "revision-transition:action-inbox:approval-window"
                        if local_task_approved
                        else "revision-transition:action-inbox:approve"
                    ),
                )
                if decision_status[0] in {"edited", "cancelled"}:
                    invalidated_approval_refs = self._invalidate_action_approvals(
                        conn=conn,
                        item_ref=item_ref,
                        result_revision_ref=str(result_revision["revision_ref"]),
                        decision=decision,
                    )

            receipt = self._build_action_decision_receipt(
                action=action,
                decision=decision,
                request=effective_request,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                authority_decision=authority_decision,
                decision_status=decision_status,
                approval_scope_ref=approval_scope_ref,
                revision_state=current_revision,
                result_revision_state=result_revision,
                decision_route_ref=decision_route,
                decision_route_binding_ref=decision_route_binding,
                decision_deadline_ref=decision_deadline,
                invalidated_approval_refs=invalidated_approval_refs,
            )
            receipt_payload = receipt.model_dump(mode="json")
            self._persist_action_revision_state(conn, result_revision)
            conn.execute(
                """
                INSERT INTO action_envelopes (
                    envelope_ref, item_ref, status, envelope_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    action["action_envelope_ref"],
                    item_ref,
                    receipt.status,
                    _json_dumps(
                        {
                            "contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
                            "item_ref": item_ref,
                            "action_envelope_ref": action["action_envelope_ref"],
                            "status": receipt.status,
                            "generation_ref": receipt.result_generation_ref,
                            "revision_ref": receipt.result_revision_ref,
                            "revision_fingerprint_ref": (
                                receipt.result_revision_fingerprint_ref
                            ),
                            "exact_scope_ref": action["action_scope_ref"],
                            "risk_class": action["risk_class"],
                            "side_effect_class": action["side_effect_class"],
                            "approval_requirement_ref": action[
                                "action_approval_requirement_ref"
                            ],
                            "expected_receipt_ref": receipt.receipt_ref,
                            "rollback_ref": action["action_rollback_ref"],
                            "safe_disable_ref": action["action_safe_disable_ref"],
                            "blocked_state_refs": list(
                                FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS
                            ),
                            "action_execution_enabled": False,
                            "connector_write_enabled": False,
                            "shell_subprocess_execution_enabled": False,
                            "model_provider_authority_allowed": False,
                            "production_authority_enabled": False,
                        }
                    ),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_receipts (
                    receipt_ref, item_ref, decision_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_ref,
                    item_ref,
                    receipt.decision_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_decision_events (
                    decision_ref, item_ref, decision, status, receipt_ref,
                    audit_ref, idempotency_key_ref, payload_fingerprint_ref,
                    approval_ref, approval_status, approval_reason_refs_json,
                    safe_summary, evidence_refs_json, blocked_state_refs_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.decision_ref,
                    item_ref,
                    decision,
                    receipt.status,
                    receipt.receipt_ref,
                    receipt.audit_ref,
                    idempotency_key_ref,
                    payload_fingerprint_ref,
                    effective_request.approval_ref,
                    receipt.approval_status,
                    _json_dumps(receipt.approval_reason_refs),
                    receipt.safe_summary,
                    _json_dumps(receipt.evidence_refs),
                    _json_dumps(receipt.blocked_state_refs),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO action_idempotency_replays (
                    key_ref, item_ref, decision, payload_fingerprint_ref,
                    receipt_ref, decision_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    item_ref,
                    decision,
                    payload_fingerprint_ref,
                    receipt.receipt_ref,
                    receipt.decision_ref,
                    receipt.created_at,
                ),
            )
            self._update_action_projection_after_decision(
                conn=conn,
                action=action,
                receipt=receipt,
                edited_envelope_ref=effective_request.edited_envelope_ref,
                projection_expires_at=projection_expires_at,
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": receipt.safe_summary,
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": "Founder Loop Action decision audit ref recorded.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    @staticmethod
    def _action_approval_ref(
        *,
        item_ref: str,
        idempotency_key_ref: str,
    ) -> str:
        readable_ref = (
            "approval-ref:founder-loop-action:"
            f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
        )
        if len(readable_ref) <= 160:
            return readable_ref
        digest = hashlib.sha256(
            json.dumps(
                {
                    "item_ref": item_ref,
                    "idempotency_key_ref": idempotency_key_ref,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return f"approval-ref:founder-loop-action:{digest}"

    @staticmethod
    def _action_decision_payload_fingerprint(
        *,
        item_ref: str,
        decision: str,
        request: FounderLoopActionDecisionRequest,
        generation_ref: str,
        revision_fingerprint_ref: str,
        decision_route: str,
        decision_route_binding: str,
        decision_deadline: str,
    ) -> str:
        fingerprint_payload = decision_payload_for_fingerprint(
            item_ref=item_ref,
            decision=decision,
            request=request,
            generation_ref=generation_ref,
            revision_fingerprint_ref=revision_fingerprint_ref,
            decision_route_ref=decision_route,
            decision_route_binding_ref=decision_route_binding,
            decision_adapter_ref=FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
            decision_deadline_ref=decision_deadline,
            authority_input_refs=list(
                FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS
            ),
        )
        return action_payload_fingerprint_ref(fingerprint_payload)

    def _capture_backend_owned_action_approval(
        self,
        *,
        conn: sqlite3.Connection,
        action: dict[str, Any],
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        approval_scope_ref: str,
        revision_state: dict[str, Any],
        decision_route_binding_ref: str,
        decision_deadline_ref: str,
    ) -> ApprovalGrant:
        if decision != "approve" or request.approval_ref is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_ACTION_APPROVAL_CAPTURE_INVALID"
            )
        revision_resource_refs = [
            str(revision_state["generation_ref"]),
            str(revision_state["revision_ref"]),
            str(revision_state["revision_fingerprint_ref"]),
            payload_fingerprint_ref,
            decision_route_binding_ref,
            FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
            decision_deadline_ref,
            *FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
        ]
        approval_request = action_approval_request(
            item_ref=str(action["item_ref"]),
            actor_context=request.actor_context,
            risk_class=str(action.get("risk_class", "high")),
            resource_refs=[
                str(action["item_ref"]),
                str(action["action_envelope_ref"]),
                str(action["action_scope_ref"]),
                str(action["action_approval_requirement_ref"]),
                *revision_resource_refs,
            ],
            decision=decision,
            expected_revision_ref=str(revision_state["revision_ref"]),
            approval_scope_ref=approval_scope_ref,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id=request.actor_context.actor_id,
            approval_ref=request.approval_ref,
        )
        grant_payload = grant.model_dump(mode="json")
        receipt_payload = {
            "contract_ref": "contract-ref:founder-loop-internal-approval-capture:v1",
            "approval_kind": "founder_loop_action_decision",
            "approval_ref": request.approval_ref,
            "subject_ref": str(action["item_ref"]),
            "requested_action": ACTION_DECISION_REQUESTED_ACTION,
            "exact_scope_ref": approval_scope_ref,
            "idempotency_key_ref": idempotency_key_ref,
            "generation_ref": str(revision_state["generation_ref"]),
            "revision_ref": str(revision_state["revision_ref"]),
            "revision_fingerprint_ref": str(revision_state["revision_fingerprint_ref"]),
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "decision_route_binding_ref": decision_route_binding_ref,
            "decision_adapter_ref": FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
            "decision_deadline_ref": decision_deadline_ref,
            "authority_input_refs": list(
                FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS
            ),
            "status": "approved",
            "safe_summary": (
                "Backend-owned approval captured for Founder Loop Action "
                "decision state only."
            ),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "created_at": _utc_iso(),
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else "",
        }
        _validate_safe_payload(receipt_payload, "founder_loop_action_approval_capture")
        conn.execute(
            """
            INSERT INTO founder_loop_internal_approval_grants (
                approval_ref, approval_kind, subject_ref, requested_action,
                exact_scope_ref, idempotency_key_ref, grant_json, receipt_json,
                created_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.approval_ref,
                "founder_loop_action_decision",
                str(action["item_ref"]),
                ACTION_DECISION_REQUESTED_ACTION,
                approval_scope_ref,
                idempotency_key_ref,
                _json_dumps(grant_payload),
                _json_dumps(receipt_payload),
                str(receipt_payload["created_at"]),
                str(receipt_payload["expires_at"]),
            ),
        )
        return grant

    @staticmethod
    def _invalidate_action_approvals(
        *,
        conn: sqlite3.Connection,
        item_ref: str,
        result_revision_ref: str,
        decision: str,
    ) -> list[str]:
        rows = list(
            conn.execute(
                """
                SELECT approval_ref, grant_json, receipt_json
                FROM founder_loop_internal_approval_grants
                WHERE approval_kind = 'founder_loop_action_decision'
                  AND subject_ref = ?
                ORDER BY created_at ASC, approval_ref ASC
                """,
                (item_ref,),
            ).fetchall()
        )
        invalidated_refs: list[str] = []
        revoked_at = utc_now()
        reason_ref = f"approval-revocation-reason-ref:action-inbox-{decision}"
        for row in rows:
            approval_ref = str(row["approval_ref"])
            grant = ApprovalGrant.model_validate(json.loads(str(row["grant_json"])))
            if (
                grant.status == ApprovalStatus.revoked.value
                or grant.revoked_at is not None
            ):
                continue
            revoked = grant.model_copy(
                update={
                    "status": ApprovalStatus.revoked,
                    "revoked_at": revoked_at,
                    "metadata": {
                        **grant.metadata,
                        "revocation_reason_ref": reason_ref,
                        "invalidated_by_revision_ref": result_revision_ref,
                    },
                }
            )
            approval_receipt = dict(json.loads(str(row["receipt_json"])))
            approval_receipt.update(
                {
                    "status": "invalidated",
                    "invalidated_by_revision_ref": result_revision_ref,
                    "invalidation_reason_ref": reason_ref,
                    "safe_summary": (
                        "Earlier Action approval invalidated by a revision-changing "
                        "decision."
                    ),
                }
            )
            _validate_safe_payload(
                approval_receipt,
                "founder_loop_action_approval_invalidation",
            )
            conn.execute(
                """
                UPDATE founder_loop_internal_approval_grants
                SET grant_json = ?, receipt_json = ?
                WHERE approval_ref = ?
                """,
                (
                    _json_dumps(revoked.model_dump(mode="json")),
                    _json_dumps(approval_receipt),
                    approval_ref,
                ),
            )
            invalidated_refs.append(approval_ref)
        return invalidated_refs

    def _action_payload_for_item_ref(
        self,
        item_ref: str,
        *,
        conn: sqlite3.Connection | None = None,
        include_generated: bool = True,
    ) -> dict[str, Any] | None:
        query = """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   risk_class, action_kind, side_effect_class, authority_boundary,
                   approval_required, approval_envelope_ref,
                   approval_envelope_status, state_change_contract_ref,
                   state_change_readiness, blocked_state, evidence_refs_json,
                   receipt_refs_json, audit_refs_json, idempotency_key_ref,
                   expires_at, stale_state, rollback_ref, safe_disable_ref,
                   estimated_cost_usd, max_approved_cost_usd, provider_ref,
                   model_profile_ref, input_metered_units, output_metered_units,
                   total_metered_units, cost_estimate_ref, captured_usage_ref,
                   budget_decision_ref, cost_receipt_refs_json,
                   cost_blocked_state_refs_json, cost_state_label,
                   provider_authority_state_label,
                   unknown_paid_cost_requires_explicit_approval,
                   frontier_usage_claimed,
                   next_safe_action, created_at, updated_at
            FROM action_inbox
            WHERE item_ref = ?
            LIMIT 1
            """
        rows = (
            self._fetch_all(query, (item_ref,))
            if conn is None
            else list(conn.execute(query, (item_ref,)).fetchall())
        )
        if not rows and include_generated:
            return self._generated_action_payload_for_item_ref(item_ref)
        if not rows:
            return None
        return _row_to_payload(rows[0])

    def action_revision(self, action_id: str) -> dict[str, Any]:
        item_ref = action_id_to_item_ref(action_id)
        action = self._action_payload_for_item_ref(item_ref)
        if action is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
        projected = {**action, **_action_envelope_contract_payload(action)}
        return self._action_revision_state_for_action(projected)

    def _action_revision_state_for_action(
        self,
        action: dict[str, Any],
        *,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        item_ref = str(action["item_ref"])
        query = """
            SELECT state_json
            FROM action_revision_state
            WHERE item_ref = ?
            LIMIT 1
            """
        rows = (
            self._fetch_all(query, (item_ref,))
            if conn is None
            else list(conn.execute(query, (item_ref,)).fetchall())
        )
        stored = (
            dict(json.loads(str(rows[0]["state_json"]))) if rows else None
        )
        return self._project_action_revision_state(action, stored=stored)

    @staticmethod
    def _project_action_revision_state(
        action: dict[str, Any],
        *,
        stored: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if stored is None:
            return _build_action_revision_state(action, generation=1)
        generation = int(stored["generation"])
        current_source_fingerprint = action_payload_fingerprint_ref(
            _action_revision_source_payload({**action, "action_generation": generation})
        )
        if stored.get("source_fingerprint_ref") == current_source_fingerprint:
            return stored
        return _build_action_revision_state(
            action,
            generation=generation + 1,
            previous_revision_ref=str(stored["revision_ref"]),
            transition_ref="revision-transition:action-inbox:source-binding-changed",
        )

    def _synchronize_action_revision_state(
        self,
        action: dict[str, Any],
        *,
        conn: sqlite3.Connection | None = None,
    ) -> tuple[dict[str, Any], bool]:
        item_ref = str(action["item_ref"])
        if conn is None:
            with self._connect() as locked_conn:
                locked_conn.execute("BEGIN IMMEDIATE")
                locked_action = self._action_payload_for_item_ref(
                    item_ref,
                    conn=locked_conn,
                    include_generated=False,
                )
                if locked_action is None:
                    return _build_action_revision_state(action, generation=1), False
                projected = {
                    **locked_action,
                    **_action_envelope_contract_payload(locked_action),
                }
                return self._synchronize_action_revision_state(
                    projected,
                    conn=locked_conn,
                )
        rows = list(
            conn.execute(
                """
                SELECT state_json
                FROM action_revision_state
                WHERE item_ref = ?
                LIMIT 1
                """,
                (item_ref,),
            ).fetchall()
        )
        stored = (
            dict(json.loads(str(rows[0]["state_json"]))) if rows else None
        )
        projected = self._project_action_revision_state(action, stored=stored)
        if stored is not None and projected["revision_ref"] == stored["revision_ref"]:
            return stored, False
        self._persist_action_revision_state(conn, projected)
        if stored is None:
            return projected, True
        self._invalidate_action_approvals(
            conn=conn,
            item_ref=item_ref,
            result_revision_ref=str(projected["revision_ref"]),
            decision="source-binding-change",
        )
        return projected, True

    @staticmethod
    def _persist_action_revision_state(
        conn: sqlite3.Connection,
        state: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO action_revision_state (
                item_ref, generation, generation_ref, revision_ref,
                revision_fingerprint_ref, source_fingerprint_ref,
                state_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_ref) DO UPDATE SET
                generation = excluded.generation,
                generation_ref = excluded.generation_ref,
                revision_ref = excluded.revision_ref,
                revision_fingerprint_ref = excluded.revision_fingerprint_ref,
                source_fingerprint_ref = excluded.source_fingerprint_ref,
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
            """,
            (
                str(state["item_ref"]),
                int(state["generation"]),
                str(state["generation_ref"]),
                str(state["revision_ref"]),
                str(state["revision_fingerprint_ref"]),
                str(state["source_fingerprint_ref"]),
                _json_dumps(state),
                _utc_iso(),
            ),
        )

    def _generated_action_payload_for_item_ref(
        self,
        item_ref: str,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(item_ref, "item_ref")
        if not item_ref.startswith("action-item:fcc-health-001:"):
            return None
        source_readiness = self.source_readiness()
        health_actions = _health_recommendation_action_items(
            build_fcc_health_recommendations(
                source_readiness=source_readiness,
                memory_quality_issue_refs=self._memory_action_inbox_signal_refs(
                    limit=10
                ),
            )
        )
        return next(
            (action for action in health_actions if action.get("item_ref") == item_ref),
            None,
        )

    def _memory_action_inbox_signal_refs(self, *, limit: int = 10) -> list[str]:
        """Recursion-safe MEM-018/MEM-019 signal refs for Action Inbox projection."""

        bounded_limit = self._bounded_limit(limit)
        refs: list[str] = []
        for item in self.list_memory_review_queue(limit=bounded_limit):
            memory_ref = str(
                item.get("business_memory_candidate_ref")
                or item.get("review_ref")
                or ""
            )
            quality_refs = list(item.get("business_memory_quality_state_refs") or [])
            stale_state = str(item.get("business_memory_stale_state") or "")
            duplicate_refs = list(item.get("business_memory_duplicate_of_refs") or [])
            conflict_refs = list(item.get("business_memory_conflict_with_refs") or [])
            if (
                quality_refs
                or duplicate_refs
                or conflict_refs
                or stale_state not in {"", "fresh", "current", "not_stale", "not-stale"}
            ):
                refs.append(memory_ref)
                refs.extend(str(ref) for ref in quality_refs)
            if stale_state and stale_state not in {
                "fresh",
                "current",
                "not_stale",
                "not-stale",
            }:
                refs.append(_status_ref("memory-maintenance-signal-ref", stale_state))
            if duplicate_refs:
                refs.append("memory-maintenance-signal-ref:duplicate-review")
                refs.extend(str(ref) for ref in duplicate_refs)
            if conflict_refs:
                refs.append("memory-maintenance-signal-ref:conflict-review")
                refs.extend(str(ref) for ref in conflict_refs)
            if not item.get("evidence_refs"):
                refs.append("memory-quality-signal-ref:missing-evidence")
        for receipt in self.list_memory_feedback_receipts(limit=bounded_limit):
            refs.extend(
                str(ref)
                for ref in [
                    receipt.get("feedback_ref"),
                    receipt.get("receipt_ref"),
                    receipt.get("target_ref"),
                    _status_ref(
                        "memory-feedback-kind-ref",
                        str(receipt.get("feedback_kind") or "missing"),
                    ),
                ]
                if ref
            )
        if refs:
            refs.extend(
                [
                    "memory-read-model-ref:fcc-mem-018-quality-issues",
                    "memory-read-model-ref:fcc-mem-019-maintenance-runs",
                    "memory-proposal-bridge-ref:fcc-mem-021-action-inbox",
                ]
            )
        return _unique_sorted_refs(refs)[:bounded_limit]

    def _today_item_payload_for_ref(self, today_item_ref: str) -> dict[str, Any] | None:
        _validate_safe_ref(today_item_ref, "today_item_ref")
        for item in self.list_action_inbox(limit=200):
            if item.get("item_ref") == today_item_ref:
                return {
                    "source_kind": "action",
                    "title": item.get("title"),
                    "safe_summary": item.get("safe_summary"),
                    "evidence_refs": item.get("evidence_refs", []),
                }
        for item in self.list_briefing_items(limit=200):
            if item.get("briefing_ref") == today_item_ref:
                return {
                    "source_kind": "briefing",
                    "title": item.get("title"),
                    "safe_summary": item.get("safe_summary"),
                    "evidence_refs": item.get("evidence_refs", []),
                }
        for item in self.list_memory_review_queue(limit=200):
            if item.get("review_ref") == today_item_ref:
                return {
                    "source_kind": "memory",
                    "title": item.get("title"),
                    "safe_summary": item.get("safe_summary"),
                    "evidence_refs": item.get("evidence_refs", []),
                }
        for item in self.list_plan_summaries(limit=200):
            if item.get("plan_ref") == today_item_ref:
                return {
                    "source_kind": "plan",
                    "title": item.get("title"),
                    "safe_summary": item.get("safe_summary"),
                    "evidence_refs": item.get("evidence_refs", []),
                }
        return None

    def _chat_turn_receipt_replay(
        self, idempotency_key_ref: str
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, turn_ref, payload_fingerprint_ref, receipt_ref, created_at
            FROM chat_turn_receipt_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _chat_handoff_replay(self, idempotency_key_ref: str) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, turn_ref, handoff_target, payload_fingerprint_ref,
                   receipt_ref, handoff_ref, created_ref, created_at
            FROM chat_handoff_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _chat_turn_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM chat_turn_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_TURN_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _chat_handoff_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM chat_handoff_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_HANDOFF_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _action_decision_replay(
        self, idempotency_key_ref: str
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, item_ref, decision, payload_fingerprint_ref,
                   receipt_ref, decision_ref, created_at
            FROM action_idempotency_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _action_envelope_promotion_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, today_item_ref, item_ref, payload_fingerprint_ref,
                   receipt_ref, action_envelope_ref, created_at
            FROM action_envelope_promotion_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _action_envelope_promotion_receipt_by_ref(
        self, receipt_ref: str
    ) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM action_envelope_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_ACTION_ENVELOPE_RECEIPT_NOT_FOUND"
            )
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _memory_context_pack_action_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, context_pack_ref, payload_fingerprint_ref,
                   receipt_ref, proposal_ref, action_envelope_ref, created_at
            FROM memory_context_pack_action_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _memory_context_pack_action_receipt_by_ref(
        self,
        receipt_ref: str,
    ) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM memory_context_pack_action_proposals
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_RECEIPT_NOT_FOUND"
            )
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _memory_feedback_receipt_by_ref(
        self,
        receipt_ref: str,
    ) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM memory_feedback_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_FEEDBACK_RECEIPT_NOT_FOUND"
            )
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def list_memory_context_pack_action_proposal_receipts(
        self,
        *,
        context_pack_ref: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: tuple[Any, ...]
        where_clause = ""
        if context_pack_ref is not None:
            _validate_safe_ref(context_pack_ref, "context_pack_ref")
            where_clause = "WHERE context_pack_ref = ?"
            params = (context_pack_ref, limit)
        else:
            params = (limit,)
        rows = self._fetch_all(
            f"""
            SELECT receipt_json
            FROM memory_context_pack_action_proposals
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def _local_task_commit_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, item_ref, local_task_ref, payload_fingerprint_ref,
                   receipt_ref, created_at
            FROM local_task_commit_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _local_task_commit_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM local_task_commit_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError("FOUNDER_LOOP_LOCAL_TASK_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _latest_local_task_commit_receipt_for_item_ref(
        self,
        item_ref: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(item_ref, "item_ref")
        query = """
            SELECT receipt_json
            FROM local_task_commit_receipts
            WHERE item_ref = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
        rows = (
            self._fetch_all(query, (item_ref,))
            if conn is None
            else list(conn.execute(query, (item_ref,)).fetchall())
        )
        if not rows:
            return None
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _local_task_commit_projection(self, action: dict[str, Any]) -> dict[str, Any]:
        action = {**action, **_action_envelope_contract_payload(action)}
        item_ref = str(action.get("item_ref") or "founder-action:unknown")
        action_kind = str(action.get("action_kind") or "review_only")
        local_task_ref = (
            local_task_ref_for_action(item_ref)
            if action_kind == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
            else None
        )
        receipt = (
            self._latest_local_task_commit_receipt_for_item_ref(item_ref)
            if local_task_ref is not None
            else None
        )
        approval_receipt = self._latest_approved_action_decision_receipt_for_item_ref(
            item_ref
        )
        safe_disable_posture = self.local_task_safe_disable_posture()
        blocked_reasons = self._local_task_commit_blocked_reasons(
            action=action,
            local_task_ref=local_task_ref,
            receipt=receipt,
            approval_receipt=approval_receipt,
            safe_disable_posture=safe_disable_posture,
        )
        eligible = not blocked_reasons
        current_approval_ref = (
            str(approval_receipt.get("approval_ref"))
            if approval_receipt and approval_receipt.get("approval_ref")
            else None
        )
        committed_approval_ref = receipt.get("approval_ref") if receipt else None
        if committed_approval_ref is not None:
            try:
                _validate_safe_ref(
                    committed_approval_ref,
                    "local_task_commit_approval_ref",
                )
            except (TypeError, ValueError):
                committed_approval_ref = None
        approval_ref = committed_approval_ref or current_approval_ref
        return {
            "action_kind": action_kind,
            "local_task_commit_contract_ref": FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
            "local_task_commit_route_ref": FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF,
            "local_task_ref": local_task_ref,
            "local_task_commit_approval_ref": approval_ref,
            "local_task_commit_approval_status": (
                "committed_receipt_reference_only"
                if committed_approval_ref
                else "backend_owned_approval_ready"
                if current_approval_ref
                else "missing"
            ),
            "local_task_commit_eligible": eligible,
            "local_task_commit_receipt_ref": (
                str(receipt.get("receipt_ref")) if receipt else None
            ),
            "local_task_commit_blocked_reasons": blocked_reasons,
            "local_task_commit_next_safe_action": (
                "Commit this approved local task through the exact local-task route."
                if eligible
                else (
                    "Keep local task creation disabled until backend posture is re-enabled."
                    if FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
                    in blocked_reasons
                    else "Keep this item in review until local-task action kind and approval are present."
                )
            ),
            "local_task_safe_disable_posture": safe_disable_posture,
            "local_task_safe_disable_ref": safe_disable_posture["safe_disable_ref"],
            "local_task_rollback_ref": safe_disable_posture["rollback_ref"],
            "local_task_safe_disable_active": safe_disable_posture[
                "safe_disable_active"
            ],
            "local_task_safe_disable_posture_ref": safe_disable_posture[
                "safe_disable_posture_ref"
            ],
            "local_task_rollback_execution_enabled": safe_disable_posture[
                "rollback_execution_enabled"
            ],
            "local_task_rollback_blocker_refs": safe_disable_posture[
                "rollback_blocker_refs"
            ],
            "local_task_commit_external_authority_blocked_refs": list(
                FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS
            ),
        }

    def _local_task_commit_blocked_reasons(
        self,
        *,
        action: dict[str, Any],
        local_task_ref: str | None,
        receipt: dict[str, Any] | None,
        approval_receipt: dict[str, Any] | None,
        safe_disable_posture: dict[str, Any],
    ) -> list[str]:
        blocked_reasons: list[str] = []
        action_kind = str(action.get("action_kind") or "review_only")
        if action_kind != FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND:
            blocked_reasons.append("blocked-state:unsupported-action-kind")
        if action.get("status") != "approved":
            blocked_reasons.append("blocked-state:action-not-approved")
        if receipt is not None:
            blocked_reasons.append("blocked-state:local-task-already-committed")
        if local_task_ref is None:
            blocked_reasons.append("blocked-state:local-task-ref-missing")
        if (
            action.get("state_change_contract_ref")
            != FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
        ):
            blocked_reasons.append("blocked-state:local-task-contract-missing")
        for key, reason_ref in [
            ("action_envelope_ref", "blocked-state:action-envelope-ref-missing"),
            ("action_scope_ref", "blocked-state:exact-scope-ref-missing"),
            ("rollback_ref", "blocked-state:rollback-ref-missing"),
            ("safe_disable_ref", "blocked-state:safe-disable-ref-missing"),
        ]:
            value = action.get(key)
            if not isinstance(value, str) or not value:
                blocked_reasons.append(reason_ref)
        if action_kind == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND:
            if action.get("safe_disable_ref") != safe_disable_posture.get(
                "safe_disable_ref"
            ):
                blocked_reasons.append("blocked-state:safe-disable-ref-mismatch")
            if action.get("rollback_ref") != safe_disable_posture.get("rollback_ref"):
                blocked_reasons.append("blocked-state:rollback-ref-mismatch")
            if not bool(safe_disable_posture.get("local_task_commits_enabled")):
                blocked_reasons.append(
                    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
                )
        if not _is_future_iso_datetime(action.get("expires_at")):
            blocked_reasons.append("blocked-state:local-task-approval-expired")
        stale_state = str(action.get("stale_state") or "")
        if stale_state.startswith("recheck") or "stale" in stale_state:
            blocked_reasons.append("blocked-state:local-task-state-stale")
        if approval_receipt is None:
            blocked_reasons.append("blocked-state:backend-owned-approval-missing")
        elif approval_receipt.get("approval_status") != "approved":
            blocked_reasons.append("blocked-state:backend-owned-approval-not-approved")
        return list(dict.fromkeys(blocked_reasons))

    def _today_action_envelope_authority_decision(
        self,
        *,
        today_item_ref: str,
        item_ref: str,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None,
    ):
        leases = (
            active_authority_leases
            if active_authority_leases is not None
            else self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        authority_decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=(
                    f"{FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_ACTION_REF}:"
                    f"{_safe_suffix(item_ref)}"
                ),
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.draft,
                safe_summary=(
                    "Evaluate Workspace draft authority before promoting a Today "
                    "item into a reviewable Action envelope."
                ),
                resource_refs=[
                    today_item_ref,
                    item_ref,
                    FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
                    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
                    idempotency_key_ref,
                ],
                route_ref=FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS[0],
                lane_ref=FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.read_only,
                draft_fallback_available=False,
                rollback_ref=(
                    f"rollback-ref:today-action-envelope:{_short_ref_suffix(item_ref)}"
                ),
                safe_disable_ref=(
                    "safe-disable-ref:today-action-envelope:"
                    f"{_short_ref_suffix(item_ref)}"
                ),
            ),
            leases,
        )
        if authority_decision.outcome != AuthorityDecisionOutcome.allow.value:
            raise FounderLoopAuthorityError(
                [
                    *authority_decision.reason_refs,
                    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                code="FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DENIED",
                required_refs={
                    "authority_decision_ref": authority_decision.decision_ref,
                    "required_mode_ref": (
                        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF
                    ),
                    "required_domain_ref": (
                        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF
                    ),
                    "required_capability_ref": (
                        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
                    ),
                    "safe_disable_ref": authority_decision.safe_disable_ref,
                    "rollback_ref": authority_decision.rollback_ref,
                },
            )
        return authority_decision

    def _action_decision_authority_decision(
        self,
        *,
        item_ref: str,
        decision: str,
        idempotency_key_ref: str,
        revision_state: dict[str, Any],
        decision_route_binding_ref: str,
        decision_deadline_ref: str,
        active_authority_leases: list[AuthorityLease] | None,
    ):
        leases = (
            active_authority_leases
            if active_authority_leases is not None
            else self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        route_ref = f"POST /control-center/actions/{{action_id}}/{decision}"
        return evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=(
                    f"{FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_ACTION_REF}:"
                    f"{_safe_suffix(item_ref)}:{_safe_suffix(decision)}"
                ),
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.write,
                safe_summary=(
                    "Evaluate Workspace write authority before recording an "
                    "Action Inbox decision receipt."
                ),
                resource_refs=[
                    item_ref,
                    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
                    idempotency_key_ref,
                    str(revision_state["generation_ref"]),
                    str(revision_state["revision_ref"]),
                    str(revision_state["revision_fingerprint_ref"]),
                    decision_route_binding_ref,
                    FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
                    decision_deadline_ref,
                    *FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
                ],
                route_ref=route_ref,
                lane_ref=FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                draft_fallback_available=True,
                rollback_ref=(
                    "rollback-ref:action-inbox-decision:"
                    f"{_short_ref_suffix(item_ref)}:{_safe_suffix(decision)}"
                ),
                safe_disable_ref=(
                    "safe-disable-ref:action-inbox-decision:"
                    f"{_short_ref_suffix(item_ref)}:{_safe_suffix(decision)}"
                ),
            ),
            leases,
        )

    def _local_task_authority_decision(
        self,
        *,
        item_ref: str,
        local_task_ref: str,
        idempotency_key_ref: str,
    ):
        leases = (
            self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_ACTION_REF,
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.write,
                safe_summary=(
                    "Evaluate Workspace write authority for exact Action Inbox "
                    "local task commit."
                ),
                resource_refs=[
                    item_ref,
                    local_task_ref,
                    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
                    idempotency_key_ref,
                ],
                route_ref=FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF,
                lane_ref=FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                draft_fallback_available=True,
                rollback_ref=FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
                safe_disable_ref=FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
            ),
            leases,
        )
        if decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise FounderLoopAuthorityError(
                [
                    *decision.reason_refs,
                    FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                required_refs={
                    "authority_decision_ref": decision.decision_ref,
                    "required_mode_ref": (
                        FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_REQUIRED_MODE_REF
                    ),
                    "required_domain_ref": FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DOMAIN_REF,
                    "required_capability_ref": (
                        FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_CAPABILITY_REF
                    ),
                    "safe_disable_ref": decision.safe_disable_ref,
                    "rollback_ref": decision.rollback_ref,
                },
            )
        return decision

    def _memory_review_write_authority_decision(
        self,
        *,
        candidate_ref: str,
        review_ref: str,
        decision: MemoryReviewDecisionKind,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        lifecycle_suppression: bool = False,
        suppression_record_refs: Sequence[str] = (),
    ):
        leases = (
            self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        authority_decision = evaluate_memory_review_write_authority(
            active_authority_leases=leases,
            candidate_ref=candidate_ref,
            review_ref=review_ref,
            decision=decision,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            lifecycle_suppression=lifecycle_suppression,
            suppression_record_refs=suppression_record_refs,
        )
        if authority_decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise FounderLoopAuthorityError(
                [
                    *authority_decision.reason_refs,
                    MEMORY_REVIEW_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                code="FOUNDER_LOOP_MEMORY_WRITE_AUTHORITY_DENIED",
                required_refs={
                    "authority_decision_ref": authority_decision.decision_ref,
                    "required_mode_ref": MEMORY_REVIEW_AUTHORITY_REQUIRED_MODE_REF,
                    "required_domain_ref": MEMORY_REVIEW_AUTHORITY_DOMAIN_REF,
                    "required_capability_ref": MEMORY_REVIEW_AUTHORITY_CAPABILITY_REF,
                    "safe_disable_ref": authority_decision.safe_disable_ref,
                    "rollback_ref": authority_decision.rollback_ref,
                },
            )
        return authority_decision

    def _revalidate_memory_review_write_before_mutation(
        self,
        *,
        candidate_ref: str,
        review_ref: str,
        decision: MemoryReviewDecisionKind,
        approval_ref: str,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        lifecycle_suppression: bool,
        suppression_record_refs: Sequence[str] = (),
    ):
        safe_disable = self.memory_review_write_safe_disable_posture()
        if not bool(safe_disable.get("memory_review_writes_enabled")):
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_WRITE_SAFE_DISABLED")
        requested_action = (
            "record-memory-review-lifecycle-suppression-write"
            if lifecycle_suppression
            else "record-memory-review-reviewed-recall-write"
        )
        exact_scope_ref = (
            MEMORY_REVIEW_LIFECYCLE_SCOPE_REF
            if lifecycle_suppression
            else MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
        )
        approval_kind = (
            "approval-kind:memory-review-lifecycle-suppression-write"
            if lifecycle_suppression
            else "approval-kind:memory-review-reviewed-recall-write"
        )
        persisted_approval = self._internal_approval_grant_for_ref(
            approval_ref=approval_ref,
            approval_kind=approval_kind,
            subject_ref=candidate_ref,
            requested_action=requested_action,
            exact_scope_ref=exact_scope_ref,
            idempotency_key_ref=idempotency_key_ref,
        )
        required_resources = {
            candidate_ref,
            review_ref,
            exact_scope_ref,
            idempotency_key_ref,
            payload_fingerprint_ref,
            *suppression_record_refs,
        }
        now = datetime.now().astimezone()
        if (
            persisted_approval is None
            or persisted_approval.revoked_at is not None
            or (
                persisted_approval.expires_at is not None
                and persisted_approval.expires_at <= now
            )
            or not required_resources.issubset(
                set(persisted_approval.approved_resource_refs)
            )
            or requested_action not in persisted_approval.approved_actions
        ):
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_APPROVAL_SCOPE_DENIED")
        return self._memory_review_write_authority_decision(
            candidate_ref=candidate_ref,
            review_ref=review_ref,
            decision=decision,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            lifecycle_suppression=lifecycle_suppression,
            suppression_record_refs=suppression_record_refs,
        )

    def _memory_context_pack_action_authority_decision(
        self,
        *,
        context_pack_ref: str,
        context_pack_proposal_ref: str,
        expected_scope_ref: str,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None,
    ):
        leases = (
            active_authority_leases
            if active_authority_leases is not None
            else self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        authority_decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=(
                    f"{MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_ACTION_REF}:"
                    f"{_safe_suffix(context_pack_ref)}"
                ),
                domain=AuthorityDomain.memory,
                capability=AuthorityCapability.draft,
                safe_summary=(
                    "Evaluate Memory draft authority before creating an "
                    "internal Action proposal from reviewed context-pack refs."
                ),
                resource_refs=[
                    context_pack_ref,
                    context_pack_proposal_ref,
                    expected_scope_ref,
                    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF,
                    idempotency_key_ref,
                ],
                route_ref=MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE_REF,
                lane_ref=MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.read_only,
                draft_fallback_available=False,
                rollback_ref=(
                    "rollback-ref:memory-context-pack-action:"
                    f"{_short_ref_suffix(context_pack_ref)}"
                ),
                safe_disable_ref=(
                    "safe-disable-ref:memory-context-pack-action:"
                    f"{_short_ref_suffix(context_pack_ref)}"
                ),
            ),
            leases,
        )
        if authority_decision.outcome != AuthorityDecisionOutcome.allow.value:
            raise FounderLoopAuthorityError(
                [
                    *authority_decision.reason_refs,
                    MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                code="FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_DENIED",
                required_refs={
                    "authority_decision_ref": authority_decision.decision_ref,
                    "required_mode_ref": (
                        MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_REQUIRED_MODE_REF
                    ),
                    "required_domain_ref": (
                        MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_DOMAIN_REF
                    ),
                    "required_capability_ref": (
                        MEMORY_CONTEXT_PACK_ACTION_AUTHORITY_CAPABILITY_REF
                    ),
                    "safe_disable_ref": authority_decision.safe_disable_ref,
                    "rollback_ref": authority_decision.rollback_ref,
                },
            )
        return authority_decision

    def _memory_context_pack_action_approval_status(
        self,
        *,
        context_pack_ref: str,
        context_pack_proposal_ref: str,
        request: MemoryContextPackActionProposalRequest,
        expected_scope_ref: str,
        idempotency_key_ref: str,
    ) -> tuple[str, list[str]]:
        approval_request = memory_context_pack_action_approval_request(
            context_pack_ref=context_pack_ref,
            context_pack_proposal_ref=context_pack_proposal_ref,
            actor_context=request.actor_context,
            risk_class=request.risk_class,
            exact_approval_scope_ref=expected_scope_ref,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = self._internal_approval_grant_for_ref(
            approval_ref=request.approval_ref,
            approval_kind="memory_context_pack_action_proposal",
            subject_ref=context_pack_ref,
            requested_action=MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_REQUESTED_ACTION,
            exact_scope_ref=expected_scope_ref,
            idempotency_key_ref=idempotency_key_ref,
        )
        if grant is not None:
            authority.load_grant_for_validation(grant)
        decision_result = authority.validate_for_request(
            approval_request,
            request.approval_ref,
        )
        reason_refs = [
            _status_ref("approval-reason", str(reason))
            for reason in decision_result.reason_codes
        ]
        status = getattr(decision_result.status, "value", str(decision_result.status))
        return str(status), reason_refs

    def _local_task_approval_status(
        self,
        *,
        action: dict[str, Any],
        request: FounderLoopLocalTaskCommitRequest,
        local_task_ref: str,
        idempotency_key_ref: str,
    ) -> tuple[str, list[str]]:
        approval_request = local_task_commit_approval_request(
            item_ref=str(action["item_ref"]),
            actor_context=request.actor_context,
            risk_class=str(action.get("risk_class", "medium")),
            resource_refs=[
                str(action["item_ref"]),
                str(action["action_envelope_ref"]),
                str(action["action_scope_ref"]),
                local_task_ref,
                FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
                idempotency_key_ref,
            ],
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        approval_receipt = self._latest_approved_action_decision_receipt_for_item_ref(
            str(action["item_ref"])
        )
        if (
            approval_receipt is not None
            and approval_receipt.get("approval_ref") == request.approval_ref
        ):
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id="local_operator",
                approval_ref=request.approval_ref,
            )
            authority.load_grant_for_validation(grant)
        decision_result = authority.validate_for_request(
            approval_request,
            request.approval_ref,
        )
        reason_refs = [
            _status_ref("approval-reason", str(reason))
            for reason in decision_result.reason_codes
        ]
        status = getattr(decision_result.status, "value", str(decision_result.status))
        return str(status), reason_refs

    def _internal_approval_grant_for_ref(
        self,
        *,
        approval_ref: str,
        approval_kind: str,
        subject_ref: str,
        requested_action: str,
        exact_scope_ref: str,
        idempotency_key_ref: str,
        conn: sqlite3.Connection | None = None,
    ) -> ApprovalGrant | None:
        query = """
                SELECT grant_json, approval_kind, subject_ref, requested_action,
                       exact_scope_ref, idempotency_key_ref, expires_at
                FROM founder_loop_internal_approval_grants
                WHERE approval_ref = ?
                LIMIT 1
                """
        rows = (
            self._fetch_all(query, (approval_ref,))
            if conn is None
            else list(conn.execute(query, (approval_ref,)).fetchall())
        )
        if not rows:
            return None
        row = dict(rows[0])
        expected = {
            "approval_kind": approval_kind,
            "subject_ref": subject_ref,
            "requested_action": requested_action,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_key_ref": idempotency_key_ref,
        }
        if any(row.get(key) != value for key, value in expected.items()):
            return None
        if not _is_future_iso_datetime(row.get("expires_at")):
            return None
        try:
            return ApprovalGrant(**json.loads(str(row["grant_json"])))
        except Exception:
            return None

    def _latest_approved_action_decision_receipt_for_item_ref(
        self,
        item_ref: str,
        *,
        conn: sqlite3.Connection | None = None,
        action: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        action = action or self._action_payload_for_item_ref(item_ref, conn=conn)
        if action is None:
            return None
        revision = self._action_revision_state_for_action(
            {**action, **_action_envelope_contract_payload(action)},
            conn=conn,
        )
        receipts = self._action_decision_receipts_for_item_ref(item_ref, conn=conn)
        for receipt in reversed(receipts):
            if (
                receipt.get("status") != "approved"
                or receipt.get("result_revision_ref") != revision["revision_ref"]
                or not isinstance(receipt.get("approval_ref"), str)
            ):
                continue
            grant = self._internal_approval_grant_for_ref(
                approval_ref=str(receipt["approval_ref"]),
                approval_kind="founder_loop_action_decision",
                subject_ref=item_ref,
                requested_action=ACTION_DECISION_REQUESTED_ACTION,
                exact_scope_ref=str(receipt.get("approval_scope_ref") or ""),
                idempotency_key_ref=str(receipt.get("idempotency_key_ref") or ""),
                conn=conn,
            )
            if grant is not None and grant.revoked_at is None:
                return receipt
        return None

    def _action_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM action_receipts
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _action_decision_receipts_for_item_ref(
        self,
        item_ref: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> list[dict[str, Any]]:
        _validate_safe_ref(item_ref, "item_ref")
        query = """
            SELECT receipt_json
            FROM action_receipts
            WHERE item_ref = ?
            ORDER BY created_at DESC, receipt_ref DESC
            LIMIT 50
            """
        rows = (
            self._fetch_all(query, (item_ref,))
            if conn is None
            else list(conn.execute(query, (item_ref,)).fetchall())
        )
        newest_first = [dict(json.loads(str(row["receipt_json"]))) for row in rows]
        return list(reversed(newest_first))

    def _build_action_decision_receipt(
        self,
        *,
        action: dict[str, Any],
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        authority_decision,
        decision_status: tuple[str, str, list[str]],
        approval_scope_ref: str,
        revision_state: dict[str, Any],
        result_revision_state: dict[str, Any],
        decision_route_ref: str,
        decision_route_binding_ref: str,
        decision_deadline_ref: str,
        invalidated_approval_refs: list[str],
    ) -> FounderLoopActionDecisionReceipt:
        item_ref = str(action["item_ref"])
        authority_allowed = authority_decision.outcome in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }
        status, approval_status, approval_reason_refs = decision_status
        receipt_ref = action_decision_receipt_ref(
            item_ref,
            decision,
            idempotency_key_ref,
        )
        decision_ref = action_decision_ref(item_ref, decision, idempotency_key_ref)
        audit_ref = action_decision_audit_ref(item_ref, decision, idempotency_key_ref)
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:action-inbox",
                    "evidence-ref:founder-loop:action-decision",
                    *list(action.get("cost_receipt_refs") or []),
                    *list(action.get("evidence_refs") or []),
                ]
            )
        )
        cost_blocked_state_refs = _unique_sorted_refs(
            list(action.get("cost_blocked_state_refs") or [])
            or [
                "blocked-state:no-provider-model-authority",
                "blocked-state:no-provider-sdk-call",
                "blocked-state:no-runtime-model-call",
                "blocked-state:frontier-provider-model-ref-missing",
                "blocked-state:unknown-paid-cost-requires-approval",
            ]
        )
        return FounderLoopActionDecisionReceipt(
            decision_ref=decision_ref,
            item_ref=item_ref,
            decision=decision,  # type: ignore[arg-type]
            status=status,
            receipt_ref=receipt_ref,
            audit_ref=audit_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            expected_revision_ref=request.expected_revision_ref,
            generation=int(revision_state["generation"]),
            generation_ref=str(revision_state["generation_ref"]),
            revision_ref=str(revision_state["revision_ref"]),
            revision_fingerprint_ref=str(revision_state["revision_fingerprint_ref"]),
            result_generation=int(result_revision_state["generation"]),
            result_generation_ref=str(result_revision_state["generation_ref"]),
            result_revision_ref=str(result_revision_state["revision_ref"]),
            result_revision_fingerprint_ref=str(
                result_revision_state["revision_fingerprint_ref"]
            ),
            revision_advanced=(
                revision_state["revision_ref"] != result_revision_state["revision_ref"]
            ),
            approval_scope_ref=approval_scope_ref,
            decision_route_ref=decision_route_ref,
            decision_route_binding_ref=decision_route_binding_ref,
            decision_adapter_ref=FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
            decision_deadline_ref=decision_deadline_ref,
            authority_input_refs=list(
                FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS
            ),
            invalidated_approval_refs=invalidated_approval_refs,
            invalidated_approval_count=len(invalidated_approval_refs),
            approval_ref=request.approval_ref,
            approval_status=approval_status,
            approval_reason_refs=approval_reason_refs,
            safe_summary=_action_decision_safe_summary(decision, status),
            evidence_refs=evidence_refs,
            blocked_state_refs=list(
                dict.fromkeys(
                    [
                        *FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS,
                        *(
                            [
                                FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF
                            ]
                            if not authority_allowed
                            else []
                        ),
                    ]
                )
            ),
            estimated_cost_usd=float(action.get("estimated_cost_usd") or 0.0),
            max_approved_cost_usd=float(action.get("max_approved_cost_usd") or 0.0),
            provider_ref=str(action.get("provider_ref") or "provider-ref:not-invoked"),
            model_profile_ref=str(
                action.get("model_profile_ref") or "model-profile-ref:not-invoked"
            ),
            input_metered_units=int(action.get("input_metered_units") or 0),
            output_metered_units=int(action.get("output_metered_units") or 0),
            total_metered_units=int(action.get("total_metered_units") or 0),
            cost_estimate_ref=str(
                action.get("cost_estimate_ref") or "cost-estimate-ref:not-invoked"
            ),
            captured_usage_ref=str(
                action.get("captured_usage_ref") or "usage-capture-ref:not-invoked"
            ),
            budget_decision_ref=str(
                action.get("budget_decision_ref") or "budget-decision-ref:not-invoked"
            ),
            cost_receipt_refs=list(action.get("cost_receipt_refs") or []),
            cost_blocked_state_refs=cost_blocked_state_refs,
            cost_state_label=str(action.get("cost_state_label") or "Cost blocked"),
            provider_authority_state_label=str(
                action.get("provider_authority_state_label") or "No provider authority"
            ),
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            authority_audit_ref=authority_decision.audit_record_ref,
            authority_receipt_ref=authority_decision.receipt_ref,
            authority_reason_refs=list(authority_decision.reason_refs),
            unknown_paid_cost_requires_explicit_approval=bool(
                action.get("unknown_paid_cost_requires_explicit_approval", True)
            ),
            frontier_usage_claimed=bool(action.get("frontier_usage_claimed", False)),
        )

    def _decision_status(
        self,
        *,
        action: dict[str, Any],
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        approval_scope_ref: str,
        revision_state: dict[str, Any],
        decision_route_binding_ref: str,
        decision_deadline_ref: str,
        captured_grant: ApprovalGrant | None,
        conn: sqlite3.Connection,
    ) -> tuple[str, str, list[str]]:
        if decision == "approve":
            if request.approval_ref is None:
                return (
                    "blocked",
                    "approval_required",
                    ["approval-reason:missing-exact-local-approval"],
                )
            approval_request = action_approval_request(
                item_ref=str(action["item_ref"]),
                actor_context=request.actor_context,
                risk_class=str(action.get("risk_class", "high")),
                resource_refs=[
                    str(action["item_ref"]),
                    str(action["action_envelope_ref"]),
                    str(action["action_scope_ref"]),
                    str(action["action_approval_requirement_ref"]),
                    str(revision_state["generation_ref"]),
                    str(revision_state["revision_ref"]),
                    str(revision_state["revision_fingerprint_ref"]),
                    payload_fingerprint_ref,
                    decision_route_binding_ref,
                    FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
                    decision_deadline_ref,
                    *FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
                ],
                decision=decision,
                expected_revision_ref=str(revision_state["revision_ref"]),
                approval_scope_ref=approval_scope_ref,
            )
            authority = LocalApprovalAuthority()
            authority.create_request(approval_request)
            grant = captured_grant or self._internal_approval_grant_for_ref(
                approval_ref=request.approval_ref,
                approval_kind="founder_loop_action_decision",
                subject_ref=str(action["item_ref"]),
                requested_action=ACTION_DECISION_REQUESTED_ACTION,
                exact_scope_ref=approval_scope_ref,
                idempotency_key_ref=idempotency_key_ref,
                conn=conn,
            )
            if grant is not None:
                authority.load_grant_for_validation(grant)
            decision_result = authority.validate_for_request(
                approval_request,
                request.approval_ref,
            )
            reason_refs = [
                _status_ref("approval-reason", str(reason))
                for reason in decision_result.reason_codes
            ]
            if decision_result.allowed:
                return "approved", str(decision_result.status), reason_refs
            return "blocked", str(decision_result.status), reason_refs
        if decision == "edit":
            if request.edited_envelope_ref is None:
                return (
                    "blocked",
                    "edited_envelope_ref_required",
                    ["approval-reason:edit-requires-corrected-envelope-ref"],
                )
            return (
                "edited",
                "not_required_for_edit_decision",
                ["approval-reason:edit-recorded-no-execution"],
            )
        if decision == "reject":
            return (
                "rejected",
                "not_required_for_reject_decision",
                ["approval-reason:reject-recorded-no-execution"],
            )
        if decision == "defer":
            return (
                "deferred",
                "not_required_for_defer_decision",
                ["approval-reason:defer-recorded-no-execution"],
            )
        if decision == "cancel":
            return (
                "cancelled",
                "not_required_for_cancel_decision",
                ["approval-reason:cancel-recorded-no-execution"],
            )
        raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_DECISION_UNSUPPORTED")

    def _update_action_projection_after_decision(
        self,
        *,
        conn: sqlite3.Connection,
        action: dict[str, Any],
        receipt: FounderLoopActionDecisionReceipt,
        edited_envelope_ref: str | None,
        projection_expires_at: str | None,
    ) -> None:
        receipt_refs = list(
            dict.fromkeys(
                [*list(action.get("receipt_refs") or []), receipt.receipt_ref]
            )
        )
        audit_refs = list(
            dict.fromkeys([*list(action.get("audit_refs") or []), receipt.audit_ref])
        )
        approval_envelope_ref = (
            edited_envelope_ref
            if receipt.status == "edited" and edited_envelope_ref is not None
            else None
            if receipt.status == "cancelled"
            else action.get("approval_envelope_ref")
        )
        projection_status = {
            "approved": "approved",
            "edited": "edited",
            "rejected": "rejected",
            "deferred": "deferred",
            "cancelled": "cancelled",
            "blocked": "blocked",
        }.get(receipt.status, "receipt_recorded")
        local_task_approved = (
            action.get("action_kind") == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
            and receipt.status == "approved"
        )
        state_change_contract_ref = (
            FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
            if local_task_approved
            else FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF
        )
        state_change_readiness = (
            "local_task_commit_ready_contract_approval_recorded"
            if local_task_approved
            else "action_cancelled_no_execution"
            if receipt.status == "cancelled"
            else "decision_receipt_recorded_no_action_execution"
        )
        next_safe_action = (
            "Commit this exact local task through the typed local-task route."
            if local_task_approved
            else "Inspect the cancellation receipt; the action remains disabled."
            if receipt.status == "cancelled"
            else "Inspect the decision receipt; action execution remains blocked."
        )
        stale_state = (
            "fresh_exact_scope_local_task_commit_window"
            if local_task_approved
            else action.get("stale_state")
        )
        conn.execute(
            """
            UPDATE action_inbox
            SET status = ?,
                approval_envelope_ref = ?,
                approval_envelope_status = ?,
                state_change_contract_ref = ?,
                state_change_readiness = ?,
                receipt_refs_json = ?,
                audit_refs_json = ?,
                idempotency_key_ref = ?,
                expires_at = ?,
                stale_state = ?,
                next_safe_action = ?,
                updated_at = ?
            WHERE item_ref = ?
            """,
            (
                projection_status,
                approval_envelope_ref,
                f"{receipt.status}_receipt_recorded",
                state_change_contract_ref,
                state_change_readiness,
                _json_dumps(receipt_refs),
                _json_dumps(audit_refs),
                receipt.idempotency_key_ref,
                projection_expires_at,
                stale_state,
                next_safe_action,
                _utc_iso(),
                receipt.item_ref,
            ),
        )

    def _update_action_projection_after_local_task_commit(
        self,
        *,
        conn: sqlite3.Connection,
        action: dict[str, Any],
        receipt: FounderLoopLocalTaskCommitReceipt,
    ) -> None:
        current_revision = self._action_revision_state_for_action(
            {**action, **_action_envelope_contract_payload(action)},
            conn=conn,
        )
        receipt_refs = list(
            dict.fromkeys(
                [*list(action.get("receipt_refs") or []), receipt.receipt_ref]
            )
        )
        audit_refs = list(
            dict.fromkeys([*list(action.get("audit_refs") or []), receipt.audit_ref])
        )
        evidence_refs = list(
            dict.fromkeys(
                [*list(action.get("evidence_refs") or []), *receipt.evidence_refs]
            )
        )
        conn.execute(
            """
            UPDATE action_inbox
            SET status = ?,
                state_change_contract_ref = ?,
                state_change_readiness = ?,
                evidence_refs_json = ?,
                receipt_refs_json = ?,
                audit_refs_json = ?,
                idempotency_key_ref = ?,
                next_safe_action = ?,
                updated_at = ?
            WHERE item_ref = ?
            """,
            (
                "receipt_recorded",
                FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
                "local_task_created_receipt_recorded",
                _json_dumps(evidence_refs),
                _json_dumps(receipt_refs),
                _json_dumps(audit_refs),
                receipt.idempotency_key_ref,
                "Inspect the local task receipt; external authority remains blocked.",
                _utc_iso(),
                receipt.item_ref,
            ),
        )
        committed_action = self._action_payload_for_item_ref(
            receipt.item_ref,
            conn=conn,
            include_generated=False,
        )
        if committed_action is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
        result_revision = _build_action_revision_state(
            {
                **committed_action,
                **_action_envelope_contract_payload(committed_action),
            },
            generation=int(current_revision["generation"]) + 1,
            previous_revision_ref=str(current_revision["revision_ref"]),
            transition_ref="revision-transition:action-inbox:local-task-commit",
        )
        self._persist_action_revision_state(conn, result_revision)
        invalidated_approval_refs = self._invalidate_action_approvals(
            conn=conn,
            item_ref=receipt.item_ref,
            result_revision_ref=str(result_revision["revision_ref"]),
            decision="local-task-commit",
        )
        if receipt.approval_ref not in invalidated_approval_refs:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_INVALIDATION_MISMATCH"
            )

    def list_plan_summaries(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT plan_ref, title, status, safe_summary, next_step_summary,
                   evidence_refs_json, updated_at
            FROM plan_summaries
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        plans = [_row_to_payload(row) for row in rows]
        return [
            {
                **plan,
                **_plan_action_envelope_contract_payload(plan),
                **_task_decomposition_contract_payload(plan),
            }
            for plan in plans
        ]

    def list_memory_review_queue(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT review_ref, title, safe_summary, candidate_kind, priority,
                   status, review_state, side_effect_class, authority_boundary,
                   provenance_refs_json, source_refs_json,
                   missing_contract_refs_json, correction_posture,
                   rejection_posture, retention_posture, delete_posture,
                   confidence_posture, stale_state, blocked_states_json,
                   next_safe_action, evidence_refs_json, created_at
            FROM memory_review_queue
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        items = [_row_to_payload(row) for row in rows]
        return [
            {
                **item,
                **_memory_source_contract_payload(item),
                **_memory_review_decision_contract_payload(item),
                **_business_memory_quality_contract_payload(item),
            }
            for item in items
        ]

    def memory_review(self, *, limit: int = 20) -> dict[str, Any]:
        items = self.list_memory_review_queue(limit=limit)
        decisions = self.list_memory_review_decisions(limit=limit)
        workbench = self.memory_workbench(limit=limit)
        write_posture = self.memory_review_write_safe_disable_posture()
        binding_today = self.today_summary(limit=6)
        return {
            "route_ref": "/control-center/memory/review",
            "surface_ref": "/memory",
            "contract_ref": FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
            "legacy_decision_contract_ref": MEMORY_REVIEW_DECISION_CONTRACT_REF,
            "workbench_route_ref": MEMORY_WORKBENCH_ROUTE_REF,
            "workbench_contract_ref": MEMORY_WORKBENCH_CONTRACT_REF,
            "workbench_health": workbench["health"],
            "workbench_groups": workbench["groups"],
            "bounded_memory_posture_contract_ref": workbench["bounded_memory_posture"][
                "contract_ref"
            ],
            "bounded_memory_posture": workbench["bounded_memory_posture"],
            "decision_route_refs": list(MEMORY_REVIEW_DECISION_ROUTE_REFS),
            "decision_kinds": list(MEMORY_REVIEW_DECISION_KINDS),
            "exact_write_scope_ref": MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
            "write_safe_disable_posture": write_posture,
            "write_safe_disable_ref": write_posture["safe_disable_ref"],
            "write_rollback_ref": write_posture["rollback_ref"],
            "write_rollback_execution_enabled": False,
            "evidence_memory_loop_binding_contract_ref": binding_today.get(
                "evidence_memory_loop_binding_contract_ref"
            ),
            "evidence_memory_loop_binding_read_model": binding_today.get(
                "evidence_memory_loop_binding_read_model"
            ),
            "reviewed_recall_write_authorized_decisions": ["accept", "correct"],
            "items": items,
            "decision_receipts": decisions,
            "decision_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in decisions
            ],
            "l1_hot_memory_index_contract_ref": L1_HOT_MEMORY_INDEX_CONTRACT_REF,
            "l1_hot_memory_index_route_ref": L1_HOT_MEMORY_INDEX_ROUTE_REF,
            "l1_hot_memory_index_status": "implemented_read_only_derived_preview",
            "l1_hot_memory_index_blocked_state_refs": list(
                L1_HOT_MEMORY_INDEX_BLOCKED_STATE_REFS
            ),
            "l2_factual_graph_temporal_index_contract_ref": (
                L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
            ),
            "l2_factual_graph_temporal_index_route_ref": (
                L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF
            ),
            "l2_factual_graph_temporal_index_status": (
                "implemented_read_only_derived_preview"
            ),
            "l2_factual_graph_temporal_index_blocked_state_refs": list(
                L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS
            ),
            "l3_identity_session_modeling_contract_ref": (
                L3_IDENTITY_SESSION_MODELING_CONTRACT_REF
            ),
            "l3_identity_session_modeling_route_ref": (
                L3_IDENTITY_SESSION_MODELING_ROUTE_REF
            ),
            "l3_identity_session_modeling_status": (
                "implemented_read_only_representation_proposals"
            ),
            "l3_identity_session_modeling_blocked_state_refs": list(
                L3_IDENTITY_SESSION_MODELING_BLOCKED_STATE_REFS
            ),
            "decision_count": len(decisions),
            "idempotency_replay_enabled": True,
            "idempotency_conflict_rejected": True,
            "approval_scope_ref": MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
            "approval_binding": "local_approval_authority_exact_scope_validated",
            "safe_refs_only": True,
            "raw_content_stored": False,
            "context_injection_authorized": False,
            "connector_write_authorized": False,
            "external_crm_sync_authorized": False,
            "automatic_action_execution_authorized": False,
            "production_authority_enabled": False,
            "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
            "authority_boundary": (
                "Memory Review decisions are backend-owned receipt state only. "
                "Accepted recall refs are not truth or context-injection authority; "
                "corrections store safe corrected-summary refs only, and rejected "
                "candidates remain preserved as blocked review state."
            ),
        }

    def memory_workbench(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        bounded_limit = self._bounded_limit(limit)
        search_index_status = self._memory_review_recall_search_index_status()
        l1_index = self.memory_l1_hot_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=bounded_limit,
        )
        l2_index = self.memory_l2_factual_graph_temporal_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=bounded_limit,
        )
        l3_index = self.memory_l3_identity_session_preference_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=bounded_limit,
        )
        context_packs = self.memory_context_pack_proposals(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=bounded_limit,
        )
        return build_memory_workbench(
            candidates=self.list_memory_review_queue(limit=bounded_limit),
            decision_receipts=self.list_memory_review_decisions(limit=bounded_limit),
            l1_index=l1_index,
            l2_index=l2_index,
            l3_index=l3_index,
            context_packs=context_packs,
            loop_refs=self._memory_workbench_loop_refs(limit=bounded_limit),
            query_ref=query_ref,
            safe_query=safe_query,
            search_index_status=search_index_status,
        )

    def memory_search(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        kind: str | None = None,
        source_ref: str | None = None,
        project_ref: str | None = None,
        person_ref: str | None = None,
        org_ref: str | None = None,
        deal_ref: str | None = None,
        review_state: str | None = None,
        quality_state: str | None = None,
        stale_state: str | None = None,
        conflict_state: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        workbench = self.memory_workbench(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        return filter_memory_workbench(
            workbench=workbench,
            query_ref=query_ref,
            safe_query=safe_query,
            kind=kind,
            source_ref=source_ref,
            project_ref=project_ref,
            person_ref=person_ref,
            org_ref=org_ref,
            deal_ref=deal_ref,
            review_state=review_state,
            quality_state=quality_state,
            stale_state=stale_state,
            conflict_state=conflict_state,
            limit=limit,
        )

    def memory_impact_graph(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(query_ref=query_ref, limit=bounded_limit)
        return build_memory_impact_graph(
            workbench=workbench,
            today_summary=self.today_summary(limit=bounded_limit),
            actions_inbox=self.actions_inbox(limit=bounded_limit),
            morning_briefing=self.morning_briefing(limit=bounded_limit),
            evidence_timeline=self.evidence_timeline(limit=bounded_limit),
            context_packs=self.memory_context_pack_proposals(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            limit=bounded_limit,
        )

    def memory_follow_up_queue(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        impact_graph = self.memory_impact_graph(query_ref=query_ref, limit=limit)
        return dict(impact_graph.get("follow_up_queue") or {})

    def memory_recall_health_v2(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        impact_graph = self.memory_impact_graph(query_ref=query_ref, limit=limit)
        return dict(impact_graph.get("health_v2") or {})

    def memory_retrieval_diagnostics(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(query_ref=query_ref, limit=bounded_limit)
        impact_graph = self.memory_impact_graph(
            query_ref=query_ref, limit=bounded_limit
        )
        return build_memory_retrieval_diagnostics(
            workbench=workbench,
            impact_graph=impact_graph,
            context_packs=self.memory_context_pack_proposals(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            feedback_receipts=self.list_memory_feedback_receipts(limit=bounded_limit),
            limit=bounded_limit,
        )

    def memory_citation_integrity(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(query_ref=query_ref, limit=bounded_limit)
        return build_memory_citation_integrity(
            context_packs=self.memory_context_pack_proposals(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            workbench=workbench,
            decision_receipts=self.list_memory_review_decisions(limit=bounded_limit),
            evidence_timeline=self.evidence_timeline(limit=bounded_limit),
            limit=bounded_limit,
        )

    def memory_quality_issues(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(query_ref=query_ref, limit=bounded_limit)
        impact_graph = self.memory_impact_graph(
            query_ref=query_ref, limit=bounded_limit
        )
        return build_memory_feedback_quality_queue(
            workbench=workbench,
            impact_graph=impact_graph,
            feedback_receipts=self.list_memory_feedback_receipts(limit=bounded_limit),
            limit=bounded_limit,
        )

    def memory_maintenance_runs(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        return build_memory_maintenance_runs(
            quality_queue=self.memory_quality_issues(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            citation_integrity=self.memory_citation_integrity(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            limit=bounded_limit,
        )

    def memory_context_manifest(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if query_ref is not None:
            _validate_safe_ref(query_ref, "query_ref")
        bounded_limit = self._bounded_limit(limit)
        quality_queue = self.memory_quality_issues(
            query_ref=query_ref,
            limit=bounded_limit,
        )
        manifest = build_memory_context_manifest(
            context_packs=self.memory_context_pack_proposals(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            retrieval_diagnostics=self.memory_retrieval_diagnostics(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            citation_integrity=self.memory_citation_integrity(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            quality_queue=quality_queue,
            limit=bounded_limit,
        )
        governed_context = build_governed_memory_context_manifest(
            l1_index=self.memory_l1_hot_index(
                query_ref=query_ref,
                limit=bounded_limit,
            ),
            query_ref=query_ref,
            max_items=min(bounded_limit, 8),
            max_tokens=512,
        )
        manifest["governed_context"] = governed_context.model_dump(mode="json")
        manifest["governed_context_manifest_ref"] = (
            governed_context.context_manifest_ref
        )
        manifest["governed_context_receipt_ref"] = governed_context.context_receipt_ref
        manifest["governed_context_fingerprint_ref"] = (
            governed_context.manifest_fingerprint_ref
        )
        return manifest

    def memory_context_pack_preview(
        self,
        *,
        context_pack_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(context_pack_ref, "context_pack_ref")
        context_packs = self.memory_context_pack_proposals(limit=200)
        context_pack = next(
            (
                dict(proposal)
                for proposal in context_packs.get("proposals", []) or []
                if proposal.get("context_pack_ref") == context_pack_ref
            ),
            None,
        )
        if context_pack is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_NOT_FOUND"
            )
        context_manifest = self.memory_context_manifest(limit=200)
        memory_candidate_refs = self._memory_candidate_refs_for_record_refs(
            context_pack.get("source_memory_record_refs") or []
        )
        return build_memory_context_pack_preview(
            context_pack=context_pack,
            context_manifest=context_manifest,
            memory_candidate_refs=memory_candidate_refs,
        )

    def _memory_candidate_refs_for_record_refs(
        self,
        memory_record_refs: Sequence[str],
    ) -> list[str]:
        wanted = set()
        for ref in memory_record_refs:
            _validate_safe_ref(str(ref), "memory_record_ref")
            wanted.add(str(ref))
        candidate_refs: list[str] = []
        for record in self.list_memory_review_recall_records():
            record_ref = f"memory-record-ref:{record.get('memory_id')}"
            if record_ref not in wanted:
                continue
            for ref in record.get("metadata_refs") or []:
                ref_text = str(ref)
                if ref_text.startswith("business-memory-candidate:"):
                    _validate_safe_ref(ref_text, "memory_candidate_ref")
                    candidate_refs.append(ref_text)
        return list(dict.fromkeys(candidate_refs))

    def _record_memory_quality_feedback(
        self,
        *,
        request: MemoryFeedbackRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        target_refs = known_memory_feedback_target_refs(
            workbench=self.memory_workbench(limit=200),
            impact_graph=self.memory_impact_graph(limit=200),
            context_packs=self.memory_context_pack_proposals(limit=200),
            evidence_timeline=self.evidence_timeline(limit=200),
        )
        if request.target_ref not in set(target_refs):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_FEEDBACK_TARGET_NOT_FOUND"
            )
        fingerprint_payload = diagnostic_memory_feedback_payload_for_fingerprint(
            request
        )
        payload_fingerprint_ref = diagnostic_memory_feedback_payload_fingerprint_ref(
            fingerprint_payload
        )
        replay = self._memory_feedback_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_FEEDBACK_IDEMPOTENCY_CONFLICT"
                )
            return dict(json.loads(str(replay["receipt_json"])))

        feedback_ref = diagnostic_memory_feedback_ref(idempotency_key_ref)
        receipt_ref = diagnostic_memory_feedback_receipt_ref(idempotency_key_ref)
        quality_issue_ref = (
            "memory-quality-issue:fcc-mem-018:"
            f"{_short_ref_suffix(request.target_ref)}:"
            f"{_safe_suffix(request.feedback_kind)}"
        )
        receipt = {
            "schema_version": "fcc_mem_018_memory_feedback_receipt.v1",
            "contract_ref": MEMORY_FEEDBACK_QUALITY_CONTRACT_REF,
            "route_ref": DIAGNOSTIC_MEMORY_FEEDBACK_ROUTE_REF,
            "feedback_ref": feedback_ref,
            "receipt_ref": receipt_ref,
            "quality_issue_ref": quality_issue_ref,
            "target_ref": request.target_ref,
            "target_kind": request.target_kind,
            "feedback_kind": request.feedback_kind,
            "reviewer_ref": request.reviewer_ref,
            "evidence_refs": list(request.evidence_refs),
            "reason_refs": list(request.reason_refs),
            "metadata_refs": list(request.metadata_refs),
            "blocked_state_refs": list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
            "idempotency_key_ref": idempotency_key_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "status": "feedback_receipt_recorded_quality_issue_signal_only",
            "quality_issue_created": True,
            "memory_write_performed": False,
            "automatic_memory_write_authorized": False,
            "delete_execution_authorized": False,
            "context_injection_authorized": False,
            "action_execution_authorized": False,
            "production_authority_enabled": False,
            "replayed": False,
            "created_at": _utc_iso(),
        }
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO memory_feedback_receipts (
                        receipt_ref, feedback_ref, target_ref, feedback_kind,
                        payload_fingerprint_ref, receipt_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        receipt_ref,
                        feedback_ref,
                        request.target_ref,
                        request.feedback_kind,
                        payload_fingerprint_ref,
                        _json_dumps(receipt),
                        receipt["created_at"],
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO memory_feedback_replays (
                        key_ref, receipt_ref, feedback_ref,
                        payload_fingerprint_ref, receipt_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        idempotency_key_ref,
                        receipt_ref,
                        feedback_ref,
                        payload_fingerprint_ref,
                        _json_dumps(receipt),
                        receipt["created_at"],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                replay = self._memory_feedback_replay(idempotency_key_ref)
                if (
                    replay is not None
                    and replay["payload_fingerprint_ref"] == payload_fingerprint_ref
                ):
                    return dict(json.loads(str(replay["receipt_json"])))
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_FEEDBACK_IDEMPOTENCY_CONFLICT"
                ) from exc
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt_ref,
                "safe_summary": (
                    "Memory feedback receipt recorded as a quality signal only; "
                    "no memory write, delete, context injection, or action execution occurred."
                ),
                "evidence_refs": receipt["evidence_refs"] or receipt["reason_refs"],
            },
        )
        return receipt

    def _memory_feedback_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        rows = self._fetch_all(
            """
            SELECT key_ref, memory_record_ref, feedback_ref,
                   payload_fingerprint_ref, receipt_ref, receipt_json, created_at
            FROM memory_feedback_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _record_memory_review_local_approval(
        self,
        *,
        subject_ref: str,
        reviewer_ref: str,
        requested_action: str,
        resource_refs: Sequence[str],
        idempotency_key_ref: str,
        approval_kind: str = "approval-kind:memory-review-decision",
        exact_scope_ref: str = MEMORY_REVIEW_RECEIPT_SCOPE_REF,
    ) -> dict[str, Any]:
        _validate_safe_ref(subject_ref, "approval_subject_ref")
        _validate_safe_ref(reviewer_ref, "approval_reviewer_ref")
        _validate_safe_ref(idempotency_key_ref, "approval_idempotency_key_ref")
        _validate_safe_ref(approval_kind, "approval_kind")
        _validate_safe_ref(exact_scope_ref, "approval_exact_scope_ref")
        safe_resources = []
        for ref in resource_refs:
            if not ref:
                continue
            _validate_safe_ref(str(ref), "approval_resource_ref")
            safe_resources.append(str(ref))
        safe_resources = list(
            dict.fromkeys([exact_scope_ref, idempotency_key_ref, *safe_resources])
        )
        approval_request = ApprovalRequest(
            approval_request_id=(
                "areq_memory_review_"
                f"{_safe_suffix(subject_ref)}_{_safe_suffix(idempotency_key_ref)}"
            ),
            run_id="founder-loop-memory-review",
            subject_type=ApprovalSubjectType.unknown,
            subject_id=subject_ref,
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id=reviewer_ref,
                authority_source=AuthoritySource.manual_operator_action,
            ),
            requested_action=requested_action,
            purpose=(
                "Validate exact local Memory Review receipt scope for "
                f"{subject_ref}; no execution, connector write, delete, export, "
                "context injection, model call, or production authority is granted."
            ),
            risk_level=ApprovalRiskLevel.low,
            data_classification=DataClassification(
                classification=ClassificationValue.project_private,
                source="founder_loop_memory_review",
                reason="Safe-ref-only local review receipt.",
                requires_redaction=True,
            ),
            resource_refs=list(dict.fromkeys([subject_ref, *safe_resources])),
            event_ref=f"approval-event:memory-review:{_safe_suffix(subject_ref)}",
            trace_id=f"trace:memory-review:{_safe_suffix(idempotency_key_ref)}",
        )
        approval_ref = (
            "approval-ref:memory-review:"
            f"{_safe_suffix(requested_action)}:"
            f"{_safe_suffix(subject_ref)}:"
            f"{_safe_suffix(idempotency_key_ref)}"
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id=reviewer_ref,
            approval_ref=approval_ref,
        )
        grant_payload = grant.model_dump(mode="json")
        receipt_payload = {
            "contract_ref": "contract-ref:founder-loop-internal-approval-capture:v1",
            "approval_kind": approval_kind,
            "approval_ref": approval_ref,
            "subject_ref": subject_ref,
            "requested_action": requested_action,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_key_ref": idempotency_key_ref,
            "status": "approved",
            "safe_summary": (
                "Backend-owned approval captured for exact-scoped Memory Review "
                "state; approval refs remain identifiers and do not grant broader "
                "memory, context, connector, provider, or production authority."
            ),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "created_at": _utc_iso(),
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else "",
        }
        _validate_safe_payload(receipt_payload, "memory_review_approval_capture")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO founder_loop_internal_approval_grants (
                    approval_ref, approval_kind, subject_ref, requested_action,
                    exact_scope_ref, idempotency_key_ref, grant_json, receipt_json,
                    created_at, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(approval_ref) DO UPDATE SET
                    approval_kind = excluded.approval_kind,
                    subject_ref = excluded.subject_ref,
                    requested_action = excluded.requested_action,
                    exact_scope_ref = excluded.exact_scope_ref,
                    idempotency_key_ref = excluded.idempotency_key_ref,
                    grant_json = excluded.grant_json,
                    receipt_json = excluded.receipt_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (
                    approval_ref,
                    approval_kind,
                    subject_ref,
                    requested_action,
                    exact_scope_ref,
                    idempotency_key_ref,
                    _json_dumps(grant_payload),
                    _json_dumps(receipt_payload),
                    str(receipt_payload["created_at"]),
                    str(receipt_payload["expires_at"]),
                ),
            )
        persisted_grant = self._internal_approval_grant_for_ref(
            approval_ref=approval_ref,
            approval_kind=approval_kind,
            subject_ref=subject_ref,
            requested_action=requested_action,
            exact_scope_ref=exact_scope_ref,
            idempotency_key_ref=idempotency_key_ref,
        )
        if persisted_grant is not None:
            authority.load_grant_for_validation(persisted_grant)
        decision = authority.validate_for_request(approval_request, approval_ref)
        if not decision.allowed:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_APPROVAL_SCOPE_DENIED")
        return {
            "approval_ref": approval_ref,
            "approval_scope_ref": exact_scope_ref,
            "approval_receipt_ref": f"approval-receipt-ref:memory-review:{_safe_suffix(approval_ref)}",
            "approval_status": getattr(decision.status, "value", str(decision.status)),
            "approval_reason_refs": [
                _status_ref("approval-reason", str(reason))
                for reason in decision.reason_codes
            ],
        }

    def record_manual_memory_candidate(
        self,
        *,
        request: ManualMemoryCandidateRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        if request.candidate_kind not in BUSINESS_MEMORY_CANDIDATE_KINDS:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CANDIDATE_KIND_UNSUPPORTED"
            )
        fingerprint_payload = manual_memory_candidate_payload_for_fingerprint(request)
        payload_fingerprint_ref = manual_memory_candidate_payload_fingerprint_ref(
            fingerprint_payload
        )
        replay = self._manual_memory_candidate_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_MANUAL_CANDIDATE_IDEMPOTENCY_CONFLICT"
                )
            return dict(json.loads(str(replay["receipt_json"])))

        review_ref = manual_memory_candidate_ref(idempotency_key_ref)
        approval = self._record_memory_review_local_approval(
            subject_ref=review_ref,
            reviewer_ref=request.reviewer_ref,
            requested_action="record_manual_memory_candidate_receipt",
            resource_refs=[
                MEMORY_MANUAL_INTAKE_CONTRACT_REF,
                "route-ref:control-center-memory-review-manual-candidate",
                idempotency_key_ref,
                *request.source_refs,
                *request.provenance_refs,
                *request.evidence_refs,
                *request.missing_evidence_refs,
            ],
            idempotency_key_ref=idempotency_key_ref,
        )
        missing_contract_refs = [
            "contract-ref:manual-memory-evidence-missing"
            if request.missing_evidence_refs
            else "contract-ref:manual-memory-evidence-bound",
            "contract-ref:memory-write-policy-binding-missing",
            "contract-ref:context-injection-missing",
            "contract-ref:memory-retention-delete-missing",
        ]
        candidate = FounderLoopMemoryReviewRecord(
            review_ref=review_ref,
            title=request.title,
            safe_summary=request.safe_summary,
            candidate_kind=request.candidate_kind,
            priority=request.priority,
            status="review_needed",
            review_state="review_needed",
            authority_boundary=(
                "Manual memory intake creates a review candidate only; recall, "
                "writes, deletes, exports, context injection, connector writes, "
                "and production authority remain blocked."
            ),
            provenance_refs=request.provenance_refs,
            source_refs=request.source_refs,
            missing_contract_refs=list(dict.fromkeys(missing_contract_refs)),
            correction_posture="correction_requires_scoped_memory_write_contract",
            rejection_posture="rejection_is_review_state_only",
            retention_posture="retention_policy_not_bound",
            delete_posture="delete_execution_not_scoped",
            confidence_posture=(
                "manual_safe_summary_pending_review_missing_evidence"
                if request.missing_evidence_refs
                else "manual_safe_summary_pending_review_evidence_bound"
            ),
            stale_state="recheck_manual_source_refs_before_memory_use",
            blocked_states=[
                ref.removeprefix("blocked-state:")
                for ref in MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS
            ],
            next_safe_action=(
                "Review the manual safe summary, source refs, and evidence posture "
                "before any accept/correct/reject/defer/merge/supersede/forget receipt."
            ),
            evidence_refs=list(request.evidence_refs),
        )
        receipt_ref = f"receipt:manual-memory-candidate:{_short_ref_suffix(review_ref)}"
        receipt = {
            "schema_version": "fcc_mem_001_manual_memory_candidate_receipt.v1",
            "contract_ref": MEMORY_MANUAL_INTAKE_CONTRACT_REF,
            "route_ref": MEMORY_MANUAL_INTAKE_ROUTE_REF,
            "review_ref": review_ref,
            "candidate_ref": review_ref,
            "candidate_kind": request.candidate_kind,
            "status": "review_candidate_created_no_recall_record",
            "receipt_ref": receipt_ref,
            "idempotency_key_ref": idempotency_key_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "source_refs": list(request.source_refs),
            "provenance_refs": list(request.provenance_refs),
            "evidence_refs": list(request.evidence_refs),
            "missing_evidence_refs": list(request.missing_evidence_refs),
            "related_entity_refs": list(request.related_entity_refs),
            "tag_refs": list(request.tag_refs),
            "metadata_refs": list(request.metadata_refs),
            "safe_summary_ref": f"safe-summary-ref:manual-memory-candidate:{_safe_suffix(review_ref)}",
            **approval,
            "blocked_state_refs": list(MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS),
            "review_candidate_created": True,
            "reviewed_recall_record_created": False,
            "memory_write_performed": False,
            "memory_delete_performed": False,
            "memory_export_performed": False,
            "context_injection_authorized": False,
            "connector_write_authorized": False,
            "production_authority_enabled": False,
            "replayed": False,
            "created_at": _utc_iso(),
        }
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO memory_manual_candidate_replays (
                        key_ref, review_ref, payload_fingerprint_ref,
                        receipt_ref, receipt_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        idempotency_key_ref,
                        review_ref,
                        payload_fingerprint_ref,
                        receipt_ref,
                        _json_dumps(receipt),
                        receipt["created_at"],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                replay_rows = conn.execute(
                    """
                    SELECT payload_fingerprint_ref, receipt_json
                    FROM memory_manual_candidate_replays
                    WHERE key_ref = ?
                    LIMIT 1
                    """,
                    (idempotency_key_ref,),
                ).fetchall()
                if (
                    replay_rows
                    and replay_rows[0]["payload_fingerprint_ref"]
                    == payload_fingerprint_ref
                ):
                    return dict(json.loads(str(replay_rows[0]["receipt_json"])))
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_MANUAL_CANDIDATE_IDEMPOTENCY_CONFLICT"
                ) from exc
            self._upsert_memory_review_record(conn, candidate)
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt_ref,
                "safe_summary": (
                    "Manual memory candidate intake created review queue state only; "
                    "no recall record, context injection, delete, export, or connector write occurred."
                ),
                "evidence_refs": receipt["evidence_refs"]
                or receipt["missing_evidence_refs"],
            },
        )
        return receipt

    def record_memory_review_decision(
        self,
        *,
        candidate_ref: str,
        decision: MemoryReviewDecisionKind,
        request: MemoryReviewDecisionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        lock_manager = FileSingleWriterLockManager(self.state_dir / ".locks")
        with lock_manager.acquire("memory-review-decisions"):
            return self._record_memory_review_decision_locked(
                candidate_ref=candidate_ref,
                decision=decision,
                request=request,
                idempotency_key_ref=idempotency_key_ref,
            )

    def _record_memory_review_decision_locked(
        self,
        *,
        candidate_ref: str,
        decision: MemoryReviewDecisionKind,
        request: MemoryReviewDecisionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        if decision not in MEMORY_REVIEW_DECISION_KINDS:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_DECISION_UNSUPPORTED")
        _validate_safe_ref(candidate_ref, "candidate_ref")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        candidate = self._memory_review_payload_for_ref(candidate_ref)
        if candidate is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_CANDIDATE_NOT_FOUND")
        if decision == "correct" and request.corrected_summary_ref is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_CORRECTION_REF_REQUIRED")
        if decision == "correct" and request.corrected_safe_summary is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CORRECTION_SUMMARY_REQUIRED"
            )
        if decision != "correct" and request.corrected_summary_ref is not None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CORRECTION_REF_NOT_ALLOWED"
            )
        if decision != "correct" and request.corrected_safe_summary is not None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_CORRECTION_SUMMARY_NOT_ALLOWED"
            )
        if decision == "merge" and not request.merge_refs:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_MERGE_REFS_REQUIRED")
        if decision == "supersede" and not request.supersedes_refs:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_SUPERSEDES_REFS_REQUIRED"
            )
        if decision != "merge" and request.merge_refs:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_MERGE_REFS_NOT_ALLOWED")
        if decision != "supersede" and request.supersedes_refs:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_SUPERSEDES_REFS_NOT_ALLOWED"
            )
        if decision != "forget_request" and request.forget_request_ref is not None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_FORGET_REQUEST_REF_NOT_ALLOWED"
            )
        related_refs = (
            request.merge_refs if decision == "merge" else request.supersedes_refs
        )
        if related_refs:
            candidate_aliases = {
                candidate_ref,
                str(candidate.get("review_ref") or ""),
                str(candidate.get("business_memory_candidate_ref") or ""),
            }
            if len(set(related_refs)) != len(related_refs):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_MEMORY_RELATED_REFS_DUPLICATE"
                )
            if candidate_aliases.intersection(related_refs):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_MEMORY_RELATED_REF_SELF_DENIED"
                )
            resolved_related = self._memory_review_payloads_for_refs(related_refs)
            resolved_aliases = {
                alias
                for related in resolved_related
                for alias in {
                    str(related.get("review_ref") or ""),
                    str(related.get("business_memory_candidate_ref") or ""),
                }
                if alias
            }
            if any(ref not in resolved_aliases for ref in related_refs):
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_MEMORY_RELATED_REF_NOT_FOUND"
                )

        mutable_decision_evidence_prefixes = (
            "evidence-ref:memory-review:accept:",
            "evidence-ref:memory-review:correct:",
            "evidence-ref:memory-review:reject:",
            "evidence-ref:memory-review:defer:",
            "evidence-ref:memory-review:merge:",
            "evidence-ref:memory-review:supersede:",
            "evidence-ref:memory-review:expire:",
            "evidence-ref:memory-review:forget-request:",
        )
        candidate_evidence_refs = [
            ref
            for ref in list(candidate.get("evidence_refs") or [])
            if not str(ref).startswith("receipt:memory-review:")
            and not str(ref).startswith(mutable_decision_evidence_prefixes)
        ]
        review_ref = str(candidate["review_ref"])
        enriched_request = MemoryReviewDecisionRequest(
            reviewer_ref=request.reviewer_ref,
            corrected_summary_ref=request.corrected_summary_ref,
            corrected_safe_summary=request.corrected_safe_summary,
            source_refs=list(
                dict.fromkeys(
                    [
                        *list(candidate.get("source_refs") or []),
                        *request.source_refs,
                    ]
                )
            ),
            evidence_refs=list(
                dict.fromkeys(
                    [
                        "evidence-ref:founder-loop:memory-review-decision",
                        *candidate_evidence_refs,
                        *request.evidence_refs,
                    ]
                )
            ),
            metadata_refs=request.metadata_refs,
            merge_refs=request.merge_refs,
            supersedes_refs=request.supersedes_refs,
            forget_request_ref=(
                request.forget_request_ref
                if request.forget_request_ref is not None
                else memory_review_forget_request_ref(candidate_ref)
                if decision == "forget_request"
                else None
            ),
            blocked_state_refs=list(
                dict.fromkeys(
                    [
                        *FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
                        *request.blocked_state_refs,
                    ]
                )
            ),
        )
        fingerprint_payload = memory_review_decision_payload_for_fingerprint(
            candidate_ref=candidate_ref,
            decision=decision,
            request=enriched_request,
        )
        payload_fingerprint_ref = memory_review_payload_fingerprint_ref(
            fingerprint_payload
        )
        replay = self._memory_review_decision_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_DECISION_IDEMPOTENCY_CONFLICT"
                )
            replay_payload = self._memory_review_decision_receipt_by_ref(
                str(replay["receipt_ref"])
            )
            replay_receipt = MemoryReviewDecisionReceipt(**replay_payload)
            if replay_receipt.suppressed_recall_record_refs:
                self._revalidate_memory_review_write_before_mutation(
                    candidate_ref=candidate_ref,
                    review_ref=str(replay["review_ref"]),
                    decision=decision,
                    approval_ref=replay_receipt.approval_ref,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    lifecycle_suppression=True,
                    suppression_record_refs=(
                        replay_receipt.suppressed_recall_record_refs
                    ),
                )
                self._suppress_memory_review_recall_records_after_terminal_decision(
                    receipt=replay_receipt
                )
            if replay_receipt.reviewed_recall_record_ref:
                self._revalidate_memory_review_write_before_mutation(
                    candidate_ref=candidate_ref,
                    review_ref=str(replay["review_ref"]),
                    decision=decision,
                    approval_ref=replay_receipt.approval_ref,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    lifecycle_suppression=False,
                )
                activate_memory_review_recall_record(
                    storage_path=self.memory_review_recall_db_path,
                    record_ref=replay_receipt.reviewed_recall_record_ref,
                    receipt_ref=replay_receipt.receipt_ref,
                )
            return replay_payload
        prepared_suppression = load_memory_review_suppression_operation(
            fetch_all=self._fetch_all,
            idempotency_key_ref=idempotency_key_ref,
        )
        if (
            prepared_suppression is not None
            and prepared_suppression["payload_fingerprint_ref"]
            != payload_fingerprint_ref
        ):
            raise FounderLoopStorageDuplicateError(
                "FOUNDER_LOOP_MEMORY_SUPPRESSION_IDEMPOTENCY_CONFLICT"
            )
        current_review_state = str(candidate.get("review_state") or "review_needed")
        if current_review_state in {"forget_requested", "expired"}:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_DECISION_TERMINAL_STATE")
        if current_review_state in {
            "rejected",
            "merged",
            "superseded",
        } and decision not in {"forget_request", "expire"}:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_DECISION_INVALID_TRANSITION"
            )
        if decision == "accept" and current_review_state in {"accepted", "corrected"}:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_DECISION_INVALID_TRANSITION"
            )
        related_candidate_refs = (
            enriched_request.merge_refs
            if decision == "merge"
            else enriched_request.supersedes_refs
            if decision == "supersede"
            else []
        )
        related_projection_candidates = self._memory_review_payloads_for_refs(
            related_candidate_refs
        )
        suppressed_recall_record_refs: list[str] = []
        if decision in {
            "reject",
            "merge",
            "supersede",
            "expire",
            "forget_request",
        }:
            suppression_candidates = [(candidate_ref, candidate)]
            if decision in {"merge", "supersede"}:
                suppression_candidates.extend(
                    (
                        str(
                            related_candidate.get("review_ref")
                            or related_candidate.get("business_memory_candidate_ref")
                            or ""
                        ),
                        related_candidate,
                    )
                    for related_candidate in related_projection_candidates
                )
            for suppression_ref, suppression_candidate in suppression_candidates:
                if not suppression_ref:
                    continue
                suppressed_recall_record_refs.extend(
                    self._memory_review_recall_record_refs_for_candidate(
                        candidate=suppression_candidate,
                        candidate_ref=suppression_ref,
                    )
                )
            suppressed_recall_record_refs = list(
                dict.fromkeys(suppressed_recall_record_refs)
            )
        if prepared_suppression is not None:
            suppressed_recall_record_refs = list(
                prepared_suppression["suppressed_recall_record_refs"]
            )
        requires_memory_write_authority = decision in {"accept", "correct"} or bool(
            suppressed_recall_record_refs
        )
        lifecycle_suppression = decision not in {"accept", "correct"} and bool(
            suppressed_recall_record_refs
        )
        authority_scope_ref = (
            MEMORY_REVIEW_LIFECYCLE_SCOPE_REF
            if lifecycle_suppression
            else MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
        )
        safe_disable_posture = self.memory_review_write_safe_disable_posture()
        if requires_memory_write_authority and not bool(
            safe_disable_posture.get("memory_review_writes_enabled")
        ):
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_WRITE_SAFE_DISABLED")
        approval = self._record_memory_review_local_approval(
            subject_ref=candidate_ref,
            reviewer_ref=enriched_request.reviewer_ref,
            requested_action=(
                "record-memory-review-lifecycle-suppression-write"
                if lifecycle_suppression
                else "record-memory-review-reviewed-recall-write"
                if requires_memory_write_authority
                else f"record-memory-review-{decision.replace('_', '-')}-receipt"
            ),
            resource_refs=[
                review_ref,
                FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
                (
                    authority_scope_ref
                    if requires_memory_write_authority
                    else MEMORY_REVIEW_RECEIPT_SCOPE_REF
                ),
                idempotency_key_ref,
                payload_fingerprint_ref,
                *enriched_request.source_refs,
                *enriched_request.evidence_refs,
                *enriched_request.metadata_refs,
                *enriched_request.merge_refs,
                *enriched_request.supersedes_refs,
                *suppressed_recall_record_refs,
                *(
                    [enriched_request.corrected_summary_ref]
                    if enriched_request.corrected_summary_ref
                    else []
                ),
            ],
            idempotency_key_ref=idempotency_key_ref,
            approval_kind=(
                "approval-kind:memory-review-lifecycle-suppression-write"
                if lifecycle_suppression
                else "approval-kind:memory-review-reviewed-recall-write"
                if requires_memory_write_authority
                else "approval-kind:memory-review-decision-receipt"
            ),
            exact_scope_ref=authority_scope_ref
            if requires_memory_write_authority
            else MEMORY_REVIEW_RECEIPT_SCOPE_REF,
        )

        receipt_ref = memory_review_decision_receipt_ref(
            candidate_ref,
            decision,
            idempotency_key_ref,
        )
        decision_ref = memory_review_decision_ref(
            candidate_ref,
            decision,
            idempotency_key_ref,
        )
        audit_ref = memory_review_decision_audit_ref(
            candidate_ref,
            decision,
            idempotency_key_ref,
        )
        evidence_ref = memory_review_decision_evidence_ref(candidate_ref, decision)
        reviewed_recall_ref = (
            memory_review_reviewed_recall_ref(review_ref)
            if decision in {"accept", "correct"}
            else None
        )
        correction_ref = (
            memory_review_correction_ref(candidate_ref)
            if decision == "correct"
            else None
        )
        rejection_ref = (
            memory_review_rejection_ref(candidate_ref) if decision == "reject" else None
        )
        defer_ref = (
            memory_review_defer_ref(candidate_ref) if decision == "defer" else None
        )
        merge_ref = (
            memory_review_merge_ref(candidate_ref) if decision == "merge" else None
        )
        supersede_ref = (
            memory_review_supersede_ref(candidate_ref)
            if decision == "supersede"
            else None
        )
        expire_ref = (
            memory_review_expire_ref(candidate_ref) if decision == "expire" else None
        )
        forget_request_receipt_ref = (
            enriched_request.forget_request_ref
            if decision == "forget_request"
            else None
        )
        authority_decision = (
            self._memory_review_write_authority_decision(
                candidate_ref=candidate_ref,
                review_ref=review_ref,
                decision=decision,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                lifecycle_suppression=lifecycle_suppression,
                suppression_record_refs=suppressed_recall_record_refs,
            )
            if requires_memory_write_authority
            else None
        )
        reviewed_recall_record_ref = (
            self._write_memory_review_recall_record(
                candidate=candidate,
                decision=decision,
                request=enriched_request,
                receipt_ref=receipt_ref,
                evidence_ref=evidence_ref,
                reviewed_recall_ref=reviewed_recall_ref,
            )
            if decision in {"accept", "correct"} and reviewed_recall_ref is not None
            else None
        )
        receipt = MemoryReviewDecision(
            candidate_ref=candidate_ref,
            review_ref=review_ref,
            decision=decision,
            corrected_summary_ref=enriched_request.corrected_summary_ref,
            approval_ref=approval["approval_ref"],
            approval_scope_ref=approval["approval_scope_ref"],
            approval_status=approval["approval_status"],
            approval_reason_refs=approval["approval_reason_refs"],
            authority_decision_ref=(
                authority_decision.decision_ref if authority_decision else None
            ),
            authority_decision_outcome=(
                authority_decision.outcome if authority_decision else None
            ),
            authority_lease_ref=(
                authority_decision.lease_ref if authority_decision else None
            ),
            authority_action_ref=(
                MEMORY_REVIEW_LIFECYCLE_AUTHORITY_ACTION_REF
                if lifecycle_suppression
                else MEMORY_REVIEW_AUTHORITY_ACTION_REF
                if authority_decision
                else None
            ),
            authority_lane_ref=(
                MEMORY_REVIEW_LIFECYCLE_AUTHORITY_LANE_REF
                if lifecycle_suppression
                else MEMORY_REVIEW_AUTHORITY_LANE_REF
                if authority_decision
                else None
            ),
            authority_scope_ref=authority_scope_ref if authority_decision else None,
            safe_disable_ref=str(safe_disable_posture["safe_disable_ref"]),
            rollback_ref=str(safe_disable_posture["rollback_ref"]),
            safe_disable_posture_ref=str(
                safe_disable_posture["safe_disable_posture_ref"]
            ),
            safe_disable_enabled=bool(
                safe_disable_posture["memory_review_writes_enabled"]
            ),
            rollback_execution_enabled=False,
            rollback_blocker_refs=list(safe_disable_posture["rollback_blocker_refs"]),
            source_refs=enriched_request.source_refs,
            evidence_refs=list(
                dict.fromkeys(
                    [
                        *enriched_request.evidence_refs,
                        evidence_ref,
                    ]
                )
            ),
            reviewer_ref=enriched_request.reviewer_ref,
            receipt_ref=receipt_ref,
            decision_ref=decision_ref,
            audit_ref=audit_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            evidence_timeline_event_ref=evidence_ref,
            reviewed_recall_ref=reviewed_recall_ref,
            reviewed_recall_record_ref=reviewed_recall_record_ref,
            reviewed_recall_write_performed=reviewed_recall_record_ref is not None,
            correction_ref=correction_ref,
            rejection_ref=rejection_ref,
            safe_summary_ref=f"safe-summary-ref:memory-review:{decision}",
            defer_ref=defer_ref,
            merge_ref=merge_ref,
            supersede_ref=supersede_ref,
            expire_ref=expire_ref,
            forget_request_ref=forget_request_receipt_ref,
            merge_refs=enriched_request.merge_refs,
            supersedes_refs=enriched_request.supersedes_refs,
            suppressed_recall_record_refs=suppressed_recall_record_refs,
            blocked_state_refs=enriched_request.blocked_state_refs,
        )
        if prepared_suppression is not None:
            validate_prepared_suppression_authority_binding(
                prepared=prepared_suppression,
                receipt=receipt,
            )
        if receipt.suppressed_recall_record_refs:
            with self._connect() as conn:
                prepare_memory_review_suppression_operation(
                    conn=conn,
                    idempotency_key_ref=idempotency_key_ref,
                    candidate_ref=candidate_ref,
                    review_ref=review_ref,
                    decision=decision,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    receipt_ref=receipt.receipt_ref,
                    approval_ref=receipt.approval_ref,
                    approval_scope_ref=receipt.approval_scope_ref,
                    authority_decision_ref=str(receipt.authority_decision_ref),
                    authority_decision_outcome=str(receipt.authority_decision_outcome),
                    authority_lease_ref=str(receipt.authority_lease_ref),
                    authority_action_ref=str(receipt.authority_action_ref),
                    authority_lane_ref=str(receipt.authority_lane_ref),
                    authority_scope_ref=str(receipt.authority_scope_ref),
                    safe_disable_ref=receipt.safe_disable_ref,
                    safe_disable_posture_ref=receipt.safe_disable_posture_ref,
                    safe_disable_enabled=receipt.safe_disable_enabled,
                    rollback_ref=receipt.rollback_ref,
                    suppressed_recall_record_refs=(
                        receipt.suppressed_recall_record_refs
                    ),
                    created_at=receipt.created_at,
                )
            self._revalidate_memory_review_write_before_mutation(
                candidate_ref=candidate_ref,
                review_ref=review_ref,
                decision=decision,
                approval_ref=receipt.approval_ref,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                lifecycle_suppression=True,
                suppression_record_refs=receipt.suppressed_recall_record_refs,
            )
            self._suppress_memory_review_recall_records_after_terminal_decision(
                receipt=receipt,
            )
        receipt_payload = receipt.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_review_decisions (
                    receipt_ref, candidate_ref, review_ref, decision,
                    decision_ref, receipt_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_ref,
                    receipt.candidate_ref,
                    receipt.review_ref,
                    receipt.decision,
                    receipt.decision_ref,
                    _json_dumps(receipt_payload),
                    receipt.created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO memory_review_decision_replays (
                    key_ref, candidate_ref, review_ref, decision,
                    payload_fingerprint_ref, receipt_ref, decision_ref, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key_ref,
                    receipt.candidate_ref,
                    receipt.review_ref,
                    receipt.decision,
                    payload_fingerprint_ref,
                    receipt.receipt_ref,
                    receipt.decision_ref,
                    receipt.created_at,
                ),
            )
            update_memory_review_projection_after_decision(
                conn=conn,
                candidate=candidate,
                receipt=receipt,
                related_candidates=related_projection_candidates,
            )
            if receipt.suppressed_recall_record_refs:
                settle_memory_review_suppression_operation(
                    conn=conn,
                    idempotency_key_ref=idempotency_key_ref,
                    receipt_ref=receipt.receipt_ref,
                    settled_at=receipt.created_at,
                )
        if receipt.reviewed_recall_record_ref:
            self._revalidate_memory_review_write_before_mutation(
                candidate_ref=candidate_ref,
                review_ref=review_ref,
                decision=decision,
                approval_ref=receipt.approval_ref,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                lifecycle_suppression=False,
            )
            activate_memory_review_recall_record(
                storage_path=self.memory_review_recall_db_path,
                record_ref=receipt.reviewed_recall_record_ref,
                receipt_ref=receipt.receipt_ref,
            )
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt.receipt_ref,
                "safe_summary": _memory_review_decision_safe_summary(decision),
                "evidence_refs": receipt.evidence_refs,
            },
        )
        self.append_log(
            JsonlLogKind.audit,
            {
                "event_ref": receipt.audit_ref,
                "safe_summary": "Founder Loop Memory Review decision audit ref recorded.",
                "evidence_refs": receipt.evidence_refs,
            },
        )
        return receipt_payload

    def list_memory_review_decisions(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM memory_review_decisions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def latest_memory_review_receipt(self, candidate_ref: str) -> dict[str, Any] | None:
        _validate_safe_ref(candidate_ref, "candidate_ref")
        candidate = self._memory_review_payload_for_ref(candidate_ref)
        candidate_refs = [candidate_ref]
        if candidate is not None:
            candidate_refs.extend(
                [
                    str(candidate.get("review_ref") or ""),
                    str(candidate.get("business_memory_candidate_ref") or ""),
                ]
            )
        candidate_refs = list(dict.fromkeys(ref for ref in candidate_refs if ref))
        placeholders = ", ".join("?" for _ in candidate_refs)
        rows = self._fetch_all(
            f"""
            SELECT receipt_json
            FROM memory_review_decisions
            WHERE candidate_ref IN ({placeholders}) OR review_ref IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT 1
            """,
            tuple([*candidate_refs, *candidate_refs]),
        )
        if not rows:
            return None
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def list_memory_review_recall_records(
        self,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        store = self._memory_review_recall_store()
        try:
            return [
                record.model_dump(mode="json")
                for record in store.list_records(limit=limit)
            ]
        finally:
            store.close()

    def memory_l1_hot_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        search_index_status = self._memory_review_recall_search_index_status()
        index = build_l1_hot_memory_index(
            self.list_memory_review_recall_records(limit=201),
            query_ref=query_ref,
            safe_query=safe_query,
            search_index_status=search_index_status,
            limit=limit,
        )
        return index.model_dump(mode="json")

    def memory_l2_factual_graph_temporal_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        search_index_status = self._memory_review_recall_search_index_status()
        l1_index = build_l1_hot_memory_index(
            self.list_memory_review_recall_records(limit=201),
            query_ref=query_ref,
            safe_query=safe_query,
            search_index_status=search_index_status,
            limit=limit,
        )
        l2_index = build_l2_factual_graph_temporal_index(
            l1_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        return l2_index.model_dump(mode="json")

    def memory_l3_identity_session_preference_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        search_index_status = self._memory_review_recall_search_index_status()
        l1_index = build_l1_hot_memory_index(
            self.list_memory_review_recall_records(limit=201),
            query_ref=query_ref,
            safe_query=safe_query,
            search_index_status=search_index_status,
            limit=limit,
        )
        l2_index = build_l2_factual_graph_temporal_index(
            l1_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        l3_index = build_l3_identity_session_preference_index(
            l2_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        return l3_index.model_dump(mode="json")

    def memory_context_pack_proposals(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, _safe_query_ref, _query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        search_index_status = self._memory_review_recall_search_index_status()
        l1_index = build_l1_hot_memory_index(
            self.list_memory_review_recall_records(limit=201),
            query_ref=query_ref,
            safe_query=safe_query,
            search_index_status=search_index_status,
            limit=limit,
        )
        l2_index = build_l2_factual_graph_temporal_index(
            l1_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        l3_index = build_l3_identity_session_preference_index(
            l2_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        context_packs = build_context_pack_proposal_index(
            l1_index,
            l2_index,
            l3_index,
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        payload = context_packs.model_dump(mode="json")
        action_receipts = self.list_memory_context_pack_action_proposal_receipts(
            limit=100
        )
        receipts_by_pack: dict[str, list[dict[str, Any]]] = {}
        for receipt in action_receipts:
            receipts_by_pack.setdefault(str(receipt["context_pack_ref"]), []).append(
                receipt
            )
        for proposal in payload.get("proposals", []):
            pack_ref = str(proposal.get("context_pack_ref"))
            pack_receipts = receipts_by_pack.get(pack_ref, [])
            proposal["internal_action_proposal_refs"] = [
                str(receipt["internal_action_proposal_ref"])
                for receipt in pack_receipts
            ]
            proposal["internal_action_receipt_refs"] = [
                str(receipt["receipt_ref"]) for receipt in pack_receipts
            ]
            proposal["phase6_1_internal_action_proposal_status"] = (
                "proposal_receipt_recorded_execution_blocked"
                if pack_receipts
                else "not_recorded"
            )
        payload["internal_action_proposal_receipts"] = action_receipts[:limit]
        payload["phase6_1_internal_action_proposal_status"] = (
            "implemented_internal_action_proposal_only_execution_blocked"
        )
        return payload

    def record_memory_feedback(
        self,
        *,
        request: MemoryFeedbackRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        lock_manager = FileSingleWriterLockManager(self.state_dir / ".locks")
        with lock_manager.acquire("memory-feedback"):
            return self._record_memory_feedback_locked(
                request=request,
                idempotency_key_ref=idempotency_key_ref,
            )

    def _record_memory_feedback_locked(
        self,
        *,
        request: MemoryFeedbackRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        if getattr(request, "memory_record_ref", None) is None:
            return self._record_memory_quality_feedback(
                request=request,
                idempotency_key_ref=idempotency_key_ref,
            )
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        memory_record_ref = request.memory_record_ref
        memory_id = memory_record_ref.removeprefix("memory-record-ref:")
        if memory_id == memory_record_ref:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_FEEDBACK_RECORD_REF_DENIED"
            )
        fingerprint_payload = memory_feedback_payload_for_fingerprint(request)
        payload_fingerprint_ref = memory_feedback_payload_fingerprint_ref(
            fingerprint_payload
        )
        replay = self._memory_feedback_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_MEMORY_FEEDBACK_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._memory_feedback_receipt_by_ref(str(replay["receipt_ref"]))
            receipt["replayed"] = True
            return receipt
        approval = self._record_memory_review_local_approval(
            subject_ref=memory_record_ref,
            reviewer_ref=request.reviewer_ref,
            requested_action="record-memory-feedback-metadata-update",
            resource_refs=[
                MEMORY_FEEDBACK_CONTRACT_REF,
                "route-ref:control-center-memory-feedback",
                idempotency_key_ref,
                payload_fingerprint_ref,
                *request.source_refs,
                *request.evidence_refs,
                *request.blocked_state_refs,
            ],
            idempotency_key_ref=idempotency_key_ref,
            approval_kind="approval-kind:memory-feedback-metadata-update",
            exact_scope_ref=MEMORY_FEEDBACK_EXACT_SCOPE_REF,
        )
        receipt_ref = memory_feedback_receipt_ref(
            memory_record_ref,
            idempotency_key_ref,
        )
        leases = (
            self._active_authority_leases
            if self._active_authority_leases is not None
            else active_founder_loop_authority_leases()
        )
        authority_decision = evaluate_memory_feedback_write_authority(
            active_authority_leases=leases,
            memory_record_ref=memory_record_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        if authority_decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise FounderLoopAuthorityError(
                [
                    *authority_decision.reason_refs,
                    MEMORY_REVIEW_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                code="FOUNDER_LOOP_MEMORY_FEEDBACK_AUTHORITY_DENIED",
            )
        safe_disable = self.memory_review_write_safe_disable_posture()
        operation = memory_feedback_update_operation(
            idempotency_key_ref=idempotency_key_ref,
            memory_record_ref=memory_record_ref,
            feedback_kind=request.feedback_kind,
            payload_fingerprint_ref=payload_fingerprint_ref,
            receipt_ref=receipt_ref,
            approval=approval,
            authority_decision=authority_decision,
            safe_disable_enabled=bool(safe_disable["memory_review_writes_enabled"]),
            created_at=_utc_iso(),
        )
        with self._connect() as conn:
            prepare_memory_feedback_update_operation(conn=conn, operation=operation)
        persisted_approval = self._internal_approval_grant_for_ref(
            approval_ref=approval["approval_ref"],
            approval_kind="approval-kind:memory-feedback-metadata-update",
            subject_ref=memory_record_ref,
            requested_action="record-memory-feedback-metadata-update",
            exact_scope_ref=MEMORY_FEEDBACK_EXACT_SCOPE_REF,
            idempotency_key_ref=idempotency_key_ref,
        )
        fresh_authority = evaluate_memory_feedback_write_authority(
            active_authority_leases=leases,
            memory_record_ref=memory_record_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        if not memory_feedback_pre_start_is_valid(
            approval_grant=persisted_approval,
            memory_record_ref=memory_record_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            authority_decision=authority_decision,
            fresh_authority_decision=fresh_authority,
            safe_disable_enabled=bool(safe_disable["memory_review_writes_enabled"]),
            checked_at=datetime.now().astimezone(),
        ):
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_FEEDBACK_SCOPE_DENIED")
        store = self._memory_review_recall_store()
        try:
            updated = store.record_feedback(
                memory_id=memory_id,
                feedback_kind=request.feedback_kind,
                receipt_ref=receipt_ref,
            )
        except KeyError as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_FEEDBACK_RECORD_NOT_FOUND"
            ) from exc
        finally:
            store.close()

        receipt = build_memory_feedback_receipt(
            request=request,
            receipt_ref=receipt_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval=approval,
            authority_decision=authority_decision,
            safe_disable_enabled=bool(safe_disable["memory_review_writes_enabled"]),
            updated_record=updated,
        )
        with self._connect() as conn:
            persist_memory_feedback_receipt(conn=conn, receipt=receipt)
        self.append_log(
            JsonlLogKind.receipt,
            {
                "event_ref": receipt["receipt_ref"],
                "safe_summary": (
                    "Memory feedback receipt recorded locally; only reviewed recall "
                    "trust/stale/conflict posture changed."
                ),
                "evidence_refs": receipt["evidence_refs"],
            },
        )
        return receipt

    def list_memory_feedback_receipts(
        self,
        *,
        memory_record_ref: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: tuple[Any, ...]
        where_clause = ""
        if memory_record_ref is not None:
            _validate_safe_ref(memory_record_ref, "memory_record_ref")
            where_clause = "WHERE memory_record_ref = ?"
            params = (memory_record_ref, self._bounded_limit(limit))
        else:
            params = (self._bounded_limit(limit),)
        rows = self._fetch_all(
            f"""
            SELECT receipt_json
            FROM memory_feedback_receipts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def memory_observation_candidates(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        query_ref, safe_query_ref, query_mode = validate_query_mode(
            query_ref=query_ref,
            safe_query=safe_query,
        )
        l1_index = self.memory_l1_hot_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        l2_index = self.memory_l2_factual_graph_temporal_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
        l2_by_memory_ref: dict[str, list[str]] = {}
        for key, ref_key in [
            ("facts", "fact_ref"),
            ("graph_relations", "relation_ref"),
            ("temporal_items", "temporal_ref"),
        ]:
            for item in l2_index.get(key, []) or []:
                l2_by_memory_ref.setdefault(str(item["memory_record_ref"]), []).append(
                    str(item[ref_key])
                )
        candidates: list[dict[str, Any]] = []
        for preview in l1_index.get("previews", [])[: self._bounded_limit(limit)]:
            role = str(preview.get("epistemic_role") or "unknown")
            memory_record_ref = str(preview["memory_record_ref"])
            supporting_l2_refs = list(
                dict.fromkeys(l2_by_memory_ref.get(memory_record_ref, []))
            )
            supporting_memory_refs = [memory_record_ref]
            source_refs = list(preview.get("source_refs") or [])
            evidence_refs = list(preview.get("evidence_refs") or [])
            receipt_refs = list(preview.get("receipt_refs") or [])
            stale_state = str(preview.get("stale_state") or "none")
            conflict_state = str(preview.get("conflict_state") or "none")
            suffix = _safe_suffix(memory_record_ref)
            candidates.append(
                {
                    "observation_candidate_ref": (
                        f"observation-candidate-ref:fcc-mem-022:{suffix}"
                    ),
                    "epistemic_role": role,
                    "memory_kind": str(preview.get("memory_kind") or "unknown"),
                    "safe_summary": bounded_observation_summary(
                        role,
                        len(supporting_memory_refs),
                    ),
                    "proof_count": len(
                        list(
                            dict.fromkeys(
                                [
                                    *supporting_memory_refs,
                                    *supporting_l2_refs,
                                    *source_refs,
                                    *evidence_refs,
                                    *receipt_refs,
                                ]
                            )
                        )
                    ),
                    "supporting_memory_record_refs": supporting_memory_refs,
                    "supporting_l2_refs": supporting_l2_refs,
                    "supporting_source_refs": source_refs,
                    "supporting_evidence_refs": evidence_refs,
                    "supporting_receipt_refs": receipt_refs,
                    "duplicate_ref": f"duplicate-key-ref:observation:{suffix}",
                    "conflict_ref": f"conflict-key-ref:observation:{suffix}",
                    "duplicate_candidate_refs": [],
                    "conflict_candidate_refs": (
                        [f"conflict-state-ref:{conflict_state}"]
                        if conflict_state != "none"
                        else []
                    ),
                    "freshness_refs": [
                        f"stale-state-ref:{stale_state}",
                        f"freshness-ref:reviewed-record:{suffix}",
                    ],
                    "score_components": dict(preview.get("score_components") or {}),
                    "retrieval_strategy_refs": list(
                        preview.get("retrieval_strategy_refs") or []
                    ),
                    "query_mode": query_mode,
                    "safe_query_ref": safe_query_ref,
                    **memory_feature_flags(),
                }
            )
        return {
            "schema_version": "fcc_mem_022_observation_candidates.v1",
            "contract_ref": MEMORY_OBSERVATION_CANDIDATE_CONTRACT_REF,
            "route_ref": MEMORY_OBSERVATION_CANDIDATE_ROUTE_REF,
            "status": "implemented_read_only_observation_candidates",
            "query_ref": query_ref,
            "safe_query_ref": safe_query_ref,
            "query_mode": query_mode,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "source_l1_preview_count": int(l1_index.get("preview_count") or 0),
            "source_l2_projection_count": sum(
                len(l2_index.get(key, []) or [])
                for key in ["facts", "graph_relations", "temporal_items"]
            ),
            "retrieval_strategy_refs": list(
                l1_index.get("retrieval_strategy_refs") or []
            ),
            "search_index_status": dict(l1_index.get("search_index_status") or {}),
            "hrr_readiness": memory_hrr_readiness(),
            "blocked_state_refs": list(MEMORY_OBSERVATION_BLOCKED_STATE_REFS),
            **memory_feature_flags(),
        }

    def memory_probe(
        self,
        *,
        entity_ref: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        _validate_safe_ref(entity_ref, "entity_ref")
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(limit=bounded_limit)
        l1_index = self.memory_l1_hot_index(limit=bounded_limit)
        l2_index = self.memory_l2_factual_graph_temporal_index(limit=bounded_limit)
        l3_index = self.memory_l3_identity_session_preference_index(limit=bounded_limit)
        context_packs = self.memory_context_pack_proposals(limit=bounded_limit)
        observations = self.memory_observation_candidates(limit=bounded_limit)
        feedback = self.list_memory_feedback_receipts(limit=bounded_limit)

        def _matching_items(
            items: Sequence[dict[str, Any]], keys: Sequence[str]
        ) -> list[dict[str, Any]]:
            matches: list[dict[str, Any]] = []
            for item in items:
                refs: list[str] = []
                for key in keys:
                    value = item.get(key)
                    if isinstance(value, list):
                        refs.extend(str(ref) for ref in value)
                    elif value:
                        refs.append(str(value))
                if refs_intersect(entity_ref, refs):
                    matches.append(item)
            return matches[:bounded_limit]

        workbench_items = _matching_items(
            workbench.get("items", []) or [],
            [
                "memory_ref",
                "review_ref",
                "source_refs",
                "evidence_refs",
                "related_entity_refs",
                "tag_refs",
                "receipt_refs",
                "metadata_refs",
            ],
        )
        l1_previews = _matching_items(
            l1_index.get("previews", []) or [],
            [
                "memory_record_ref",
                "reviewed_recall_ref",
                "source_refs",
                "evidence_refs",
                "receipt_refs",
                "metadata_refs",
                "tag_refs",
            ],
        )
        l2_items = _matching_items(
            [
                *list(l2_index.get("facts", []) or []),
                *list(l2_index.get("graph_relations", []) or []),
                *list(l2_index.get("temporal_items", []) or []),
            ],
            [
                "memory_record_ref",
                "reviewed_recall_ref",
                "fact_subject_ref",
                "fact_value_ref",
                "source_node_ref",
                "target_node_ref",
                "temporal_anchor_ref",
                "source_refs",
                "evidence_refs",
                "receipt_refs",
                "metadata_refs",
                "tag_refs",
                "supporting_refs",
            ],
        )
        l3_items = _matching_items(
            l3_index.get("items", []) or [],
            [
                "l3_item_ref",
                "subject_ref",
                "observer_ref",
                "observed_ref",
                "workspace_ref",
                "session_ref",
                "representation_scope_ref",
                "supporting_memory_record_refs",
                "supporting_l1_preview_refs",
                "supporting_l2_item_refs",
                "source_refs",
                "evidence_refs",
                "receipt_refs",
            ],
        )
        pack_items = _matching_items(
            context_packs.get("proposals", []) or [],
            [
                "context_pack_ref",
                "observed_ref",
                "observer_ref",
                "representation_scope_ref",
                "source_memory_record_refs",
                "l1_preview_refs",
                "l2_projection_refs",
                "l3_representation_refs",
                "source_refs",
                "evidence_refs",
                "receipt_refs",
            ],
        )
        feedback_items = _matching_items(
            feedback,
            ["memory_record_ref", "receipt_ref", "source_refs", "evidence_refs"],
        )
        observation_items = _matching_items(
            observations.get("candidates", []) or [],
            [
                "observation_candidate_ref",
                "supporting_memory_record_refs",
                "supporting_l2_refs",
                "supporting_source_refs",
                "supporting_evidence_refs",
                "supporting_receipt_refs",
            ],
        )
        return {
            "schema_version": "fcc_mem_022_memory_probe.v1",
            "contract_ref": MEMORY_PROBE_CONTRACT_REF,
            "route_ref": MEMORY_PROBE_ROUTE_REF,
            "status": "implemented_read_only_safe_ref_probe",
            "entity_ref": entity_ref,
            "reviewed_recall_refs": [
                str(item.get("memory_record_ref")) for item in l1_previews
            ],
            "workbench_item_refs": [
                str(item.get("memory_ref")) for item in workbench_items
            ],
            "l1_preview_refs": [
                str(item.get("memory_record_ref")) for item in l1_previews
            ],
            "l2_projection_refs": [
                str(
                    item.get("fact_ref")
                    or item.get("relation_ref")
                    or item.get("temporal_ref")
                )
                for item in l2_items
            ],
            "l3_representation_refs": [
                str(item.get("l3_item_ref")) for item in l3_items
            ],
            "context_pack_refs": [
                str(item.get("context_pack_ref")) for item in pack_items
            ],
            "feedback_receipt_refs": [
                str(item.get("receipt_ref")) for item in feedback_items
            ],
            "observation_candidate_refs": [
                str(item.get("observation_candidate_ref")) for item in observation_items
            ],
            "counts": {
                "workbench": len(workbench_items),
                "l1": len(l1_previews),
                "l2": len(l2_items),
                "l3": len(l3_items),
                "context_packs": len(pack_items),
                "feedback": len(feedback_items),
                "observations": len(observation_items),
            },
            "search_index_status": dict(l1_index.get("search_index_status") or {}),
            "hrr_readiness": memory_hrr_readiness(),
            "blocked_state_refs": list(MEMORY_PROBE_BLOCKED_STATE_REFS),
            **memory_feature_flags(),
        }

    def memory_contradictions(self, *, limit: int = 20) -> dict[str, Any]:
        bounded_limit = self._bounded_limit(limit)
        workbench = self.memory_workbench(limit=bounded_limit)
        feedback = self.list_memory_feedback_receipts(limit=bounded_limit)
        previews: list[dict[str, Any]] = []
        for item in workbench.get("items", []) or []:
            reason_refs = [
                ref
                for ref in list(item.get("excluded_reason_refs") or [])
                if any(marker in ref for marker in ["conflict", "stale", "duplicate"])
            ]
            quality_refs = [
                ref
                for ref in list(item.get("quality_state_refs") or [])
                if any(marker in ref for marker in ["conflict", "stale", "duplicate"])
            ]
            if not reason_refs and not quality_refs:
                continue
            suffix = _safe_suffix(str(item.get("memory_ref") or "memory-ref:none"))
            previews.append(
                {
                    "contradiction_preview_ref": (
                        f"contradiction-preview-ref:fcc-mem-022:{suffix}"
                    ),
                    "memory_ref": str(item.get("memory_ref")),
                    "duplicate_key_ref": str(item.get("duplicate_key_ref")),
                    "conflict_key_ref": str(item.get("conflict_key_ref")),
                    "stale_state_ref": _status_ref(
                        "stale-state-ref",
                        str(item.get("stale_state") or "none"),
                    ),
                    "reason_refs": list(dict.fromkeys([*reason_refs, *quality_refs])),
                    "supporting_source_refs": list(item.get("source_refs") or []),
                    "supporting_evidence_refs": list(item.get("evidence_refs") or []),
                    "supporting_receipt_refs": list(item.get("receipt_refs") or []),
                    "safe_summary": (
                        "Contradiction preview for reviewed memory refs; "
                        "inspection only, no merge or forget action performed."
                    ),
                    **memory_feature_flags(),
                }
            )
        for receipt in feedback:
            if receipt.get("feedback_kind") not in {"stale", "conflict"}:
                continue
            suffix = _safe_suffix(str(receipt.get("receipt_ref") or "receipt:none"))
            previews.append(
                {
                    "contradiction_preview_ref": (
                        f"contradiction-preview-ref:memory-feedback:{suffix}"
                    ),
                    "memory_ref": str(receipt.get("memory_record_ref")),
                    "duplicate_key_ref": f"duplicate-key-ref:feedback:{suffix}",
                    "conflict_key_ref": f"conflict-key-ref:feedback:{suffix}",
                    "stale_state_ref": _status_ref(
                        "stale-state-ref",
                        str(receipt.get("stale_state_after") or "none"),
                    ),
                    "reason_refs": [
                        f"feedback-kind-ref:memory:{receipt.get('feedback_kind')}",
                        str(receipt.get("receipt_ref")),
                    ],
                    "supporting_source_refs": list(receipt.get("source_refs") or []),
                    "supporting_evidence_refs": list(
                        receipt.get("evidence_refs") or []
                    ),
                    "supporting_receipt_refs": [str(receipt.get("receipt_ref"))],
                    "safe_summary": (
                        "Contradiction preview from memory feedback receipt; "
                        "inspection only, no merge or forget action performed."
                    ),
                    **memory_feature_flags(),
                }
            )
        previews = previews[:bounded_limit]
        return {
            "schema_version": "fcc_mem_022_memory_contradiction_previews.v1",
            "contract_ref": MEMORY_CONTRADICTION_PREVIEW_CONTRACT_REF,
            "route_ref": MEMORY_CONTRADICTION_PREVIEW_ROUTE_REF,
            "status": "implemented_read_only_contradiction_preview",
            "preview_count": len(previews),
            "previews": previews,
            "ranking_contract_ref": MEMORY_RANKING_CONTRACT_REF,
            "search_index_status": dict(workbench.get("search_index_status") or {}),
            "hrr_readiness": memory_hrr_readiness(),
            "blocked_state_refs": list(MEMORY_CONTRADICTION_BLOCKED_STATE_REFS),
            **memory_feature_flags(),
        }

    def _memory_context_pack_payload_for_ref(
        self,
        context_pack_ref: str,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(context_pack_ref, "context_pack_ref")
        context_packs = self.memory_context_pack_proposals(limit=200)
        for proposal in context_packs.get("proposals", []):
            if proposal.get("context_pack_ref") == context_pack_ref:
                return dict(proposal)
        return None

    def _write_memory_review_recall_record(
        self,
        *,
        candidate: dict[str, Any],
        decision: MemoryReviewDecisionKind,
        request: MemoryReviewDecisionRequest,
        receipt_ref: str,
        evidence_ref: str,
        reviewed_recall_ref: str,
    ) -> str:
        try:
            return write_memory_review_recall_record(
                storage_path=self.memory_review_recall_db_path,
                candidate=candidate,
                decision=decision,
                request=request,
                receipt_ref=receipt_ref,
                evidence_ref=evidence_ref,
                reviewed_recall_ref=reviewed_recall_ref,
            )
        except MemoryReviewRuntimeError as exc:
            raise FounderLoopStorageError(str(exc)) from exc

    def _memory_review_recall_store(self) -> LocalMemoryStore:
        return LocalMemoryStore(storage_path=self.memory_review_recall_db_path)

    def _memory_review_recall_search_index_status(self) -> dict[str, Any]:
        return memory_review_recall_search_index_status(
            storage_path=self.memory_review_recall_db_path
        )

    def _memory_review_payload_for_ref(
        self,
        candidate_ref: str,
    ) -> dict[str, Any] | None:
        _validate_safe_ref(candidate_ref, "candidate_ref")
        for item in self.list_memory_review_queue(limit=200):
            if item.get("review_ref") == candidate_ref:
                return item
            if item.get("business_memory_candidate_ref") == candidate_ref:
                return item
        return None

    def _memory_review_payloads_for_refs(
        self,
        candidate_refs: Sequence[str],
    ) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        seen_review_refs: set[str] = set()
        for candidate_ref in candidate_refs:
            candidate = self._memory_review_payload_for_ref(candidate_ref)
            if candidate is None:
                continue
            review_ref = str(candidate.get("review_ref") or "")
            if not review_ref or review_ref in seen_review_refs:
                continue
            seen_review_refs.add(review_ref)
            payloads.append(candidate)
        return payloads

    def _memory_review_recall_record_refs_for_candidate(
        self,
        *,
        candidate: dict[str, Any],
        candidate_ref: str,
    ) -> list[str]:
        try:
            return memory_review_recall_record_refs_for_candidate(
                storage_path=self.memory_review_recall_db_path,
                candidate=candidate,
                candidate_ref=candidate_ref,
            )
        except MemoryReviewRuntimeError as exc:
            raise FounderLoopStorageError(str(exc)) from exc

    def _suppress_memory_review_recall_records_after_terminal_decision(
        self,
        *,
        receipt: MemoryReviewDecisionReceipt,
    ) -> None:
        suppress_memory_review_recall_records_after_terminal_decision(
            storage_path=self.memory_review_recall_db_path,
            receipt=receipt,
        )

    def _memory_workbench_loop_refs(self, *, limit: int = 20) -> list[str]:
        return memory_workbench_loop_refs(
            actions=self.list_action_inbox(limit=limit),
            plans=self.list_plan_summaries(limit=limit),
            briefings=self.list_briefing_items(limit=limit),
            turn_receipts=self.list_chat_turn_receipts(limit=limit),
            handoff_receipts=self.list_chat_handoff_receipts(limit=limit),
        )

    def _manual_memory_candidate_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, review_ref, payload_fingerprint_ref,
                   receipt_ref, receipt_json, created_at
            FROM memory_manual_candidate_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _memory_review_decision_replay(
        self,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT key_ref, candidate_ref, review_ref, decision,
                   payload_fingerprint_ref, receipt_ref, decision_ref, created_at
            FROM memory_review_decision_replays
            WHERE key_ref = ?
            LIMIT 1
            """,
            (idempotency_key_ref,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _memory_review_decision_receipt_by_ref(
        self, receipt_ref: str
    ) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM memory_review_decisions
            WHERE receipt_ref = ?
            LIMIT 1
            """,
            (receipt_ref,),
        )
        if not rows:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_NOT_FOUND"
            )
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def list_briefing_items(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT briefing_ref, title, safe_summary, priority, status,
                   side_effect_class, authority_boundary, source_readiness,
                   source_refs_json, missing_contract_refs_json,
                   blocked_states_json, stale_state, evidence_gap,
                   next_safe_action, evidence_refs_json, created_at
            FROM briefing_items
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def upsert_action(self, record: FounderLoopActionRecord) -> None:
        with self._connect() as conn:
            self._upsert_action_record(conn, record)

    def _upsert_action_record(
        self,
        conn: sqlite3.Connection,
        record: FounderLoopActionRecord,
    ) -> None:
        conn.execute(
            """
            INSERT INTO action_inbox (
                item_ref, title, safe_summary, surface, priority, status,
                risk_class, action_kind, side_effect_class, authority_boundary,
                approval_required, approval_envelope_ref,
                approval_envelope_status, state_change_contract_ref,
                state_change_readiness, blocked_state, evidence_refs_json,
                receipt_refs_json, audit_refs_json, idempotency_key_ref,
                expires_at, stale_state, rollback_ref, safe_disable_ref,
                estimated_cost_usd, max_approved_cost_usd, provider_ref,
                model_profile_ref, input_metered_units, output_metered_units,
                total_metered_units, cost_estimate_ref, captured_usage_ref,
                budget_decision_ref, cost_receipt_refs_json,
                cost_blocked_state_refs_json, cost_state_label,
                provider_authority_state_label,
                unknown_paid_cost_requires_explicit_approval,
                frontier_usage_claimed,
                next_safe_action, created_at, updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(item_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                surface = excluded.surface,
                priority = excluded.priority,
                status = excluded.status,
                risk_class = excluded.risk_class,
                action_kind = excluded.action_kind,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                approval_required = excluded.approval_required,
                approval_envelope_ref = excluded.approval_envelope_ref,
                approval_envelope_status = excluded.approval_envelope_status,
                state_change_contract_ref = excluded.state_change_contract_ref,
                state_change_readiness = excluded.state_change_readiness,
                blocked_state = excluded.blocked_state,
                evidence_refs_json = excluded.evidence_refs_json,
                receipt_refs_json = excluded.receipt_refs_json,
                audit_refs_json = excluded.audit_refs_json,
                idempotency_key_ref = excluded.idempotency_key_ref,
                expires_at = excluded.expires_at,
                stale_state = excluded.stale_state,
                rollback_ref = excluded.rollback_ref,
                safe_disable_ref = excluded.safe_disable_ref,
                estimated_cost_usd = excluded.estimated_cost_usd,
                max_approved_cost_usd = excluded.max_approved_cost_usd,
                provider_ref = excluded.provider_ref,
                model_profile_ref = excluded.model_profile_ref,
                input_metered_units = excluded.input_metered_units,
                output_metered_units = excluded.output_metered_units,
                total_metered_units = excluded.total_metered_units,
                cost_estimate_ref = excluded.cost_estimate_ref,
                captured_usage_ref = excluded.captured_usage_ref,
                budget_decision_ref = excluded.budget_decision_ref,
                cost_receipt_refs_json = excluded.cost_receipt_refs_json,
                cost_blocked_state_refs_json = excluded.cost_blocked_state_refs_json,
                cost_state_label = excluded.cost_state_label,
                provider_authority_state_label = excluded.provider_authority_state_label,
                unknown_paid_cost_requires_explicit_approval = excluded.unknown_paid_cost_requires_explicit_approval,
                frontier_usage_claimed = excluded.frontier_usage_claimed,
                next_safe_action = excluded.next_safe_action,
                updated_at = excluded.updated_at
            """,
            (
                record.item_ref,
                record.title,
                record.safe_summary,
                record.surface,
                record.priority,
                record.status,
                record.risk_class,
                record.action_kind,
                record.side_effect_class,
                record.authority_boundary,
                int(record.approval_required),
                record.approval_envelope_ref,
                record.approval_envelope_status,
                record.state_change_contract_ref,
                record.state_change_readiness,
                record.blocked_state,
                _json_dumps(record.evidence_refs),
                _json_dumps(record.receipt_refs),
                _json_dumps(record.audit_refs),
                record.idempotency_key_ref,
                record.expires_at,
                record.stale_state,
                record.rollback_ref,
                record.safe_disable_ref,
                record.estimated_cost_usd,
                record.max_approved_cost_usd,
                record.provider_ref,
                record.model_profile_ref,
                record.input_metered_units,
                record.output_metered_units,
                record.total_metered_units,
                record.cost_estimate_ref,
                record.captured_usage_ref,
                record.budget_decision_ref,
                _json_dumps(record.cost_receipt_refs),
                _json_dumps(record.cost_blocked_state_refs),
                record.cost_state_label,
                record.provider_authority_state_label,
                int(record.unknown_paid_cost_requires_explicit_approval),
                int(record.frontier_usage_claimed),
                record.next_safe_action,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )
        persisted = self._action_payload_for_item_ref(
            record.item_ref,
            conn=conn,
            include_generated=False,
        )
        if persisted is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
        self._synchronize_action_revision_state(
            {**persisted, **_action_envelope_contract_payload(persisted)},
            conn=conn,
        )

    def upsert_plan(self, record: FounderLoopPlanRecord) -> None:
        self._execute(
            """
            INSERT INTO plan_summaries (
                plan_ref, title, status, safe_summary, next_step_summary,
                evidence_refs_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_ref) DO UPDATE SET
                title = excluded.title,
                status = excluded.status,
                safe_summary = excluded.safe_summary,
                next_step_summary = excluded.next_step_summary,
                evidence_refs_json = excluded.evidence_refs_json,
                updated_at = excluded.updated_at
            """,
            (
                record.plan_ref,
                record.title,
                record.status,
                record.safe_summary,
                record.next_step_summary,
                _json_dumps(record.evidence_refs),
                record.updated_at.isoformat(),
            ),
        )

    def upsert_memory_review(self, record: FounderLoopMemoryReviewRecord) -> None:
        with self._connect() as conn:
            self._upsert_memory_review_record(conn, record)

    def _upsert_memory_review_record(
        self,
        conn: sqlite3.Connection,
        record: FounderLoopMemoryReviewRecord,
    ) -> None:
        conn.execute(
            """
            INSERT INTO memory_review_queue (
                review_ref, title, safe_summary, candidate_kind, priority,
                status, review_state, side_effect_class, authority_boundary,
                provenance_refs_json, source_refs_json, missing_contract_refs_json,
                correction_posture, rejection_posture, retention_posture,
                delete_posture, confidence_posture, stale_state,
                blocked_states_json, next_safe_action, evidence_refs_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                candidate_kind = excluded.candidate_kind,
                priority = excluded.priority,
                status = excluded.status,
                review_state = excluded.review_state,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                provenance_refs_json = excluded.provenance_refs_json,
                source_refs_json = excluded.source_refs_json,
                missing_contract_refs_json = excluded.missing_contract_refs_json,
                correction_posture = excluded.correction_posture,
                rejection_posture = excluded.rejection_posture,
                retention_posture = excluded.retention_posture,
                delete_posture = excluded.delete_posture,
                confidence_posture = excluded.confidence_posture,
                stale_state = excluded.stale_state,
                blocked_states_json = excluded.blocked_states_json,
                next_safe_action = excluded.next_safe_action,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.review_ref,
                record.title,
                record.safe_summary,
                record.candidate_kind,
                record.priority,
                record.status,
                record.review_state,
                record.side_effect_class,
                record.authority_boundary,
                _json_dumps(record.provenance_refs),
                _json_dumps(record.source_refs),
                _json_dumps(record.missing_contract_refs),
                record.correction_posture,
                record.rejection_posture,
                record.retention_posture,
                record.delete_posture,
                record.confidence_posture,
                record.stale_state,
                _json_dumps(record.blocked_states),
                record.next_safe_action,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def upsert_briefing_item(self, record: FounderLoopBriefingRecord) -> None:
        self._execute(
            """
            INSERT INTO briefing_items (
                briefing_ref, title, safe_summary, priority, status,
                side_effect_class, authority_boundary, source_readiness,
                source_refs_json, missing_contract_refs_json, blocked_states_json,
                stale_state, evidence_gap, next_safe_action, evidence_refs_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(briefing_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                priority = excluded.priority,
                status = excluded.status,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                source_readiness = excluded.source_readiness,
                source_refs_json = excluded.source_refs_json,
                missing_contract_refs_json = excluded.missing_contract_refs_json,
                blocked_states_json = excluded.blocked_states_json,
                stale_state = excluded.stale_state,
                evidence_gap = excluded.evidence_gap,
                next_safe_action = excluded.next_safe_action,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.briefing_ref,
                record.title,
                record.safe_summary,
                record.priority,
                record.status,
                record.side_effect_class,
                record.authority_boundary,
                record.source_readiness,
                _json_dumps(record.source_refs),
                _json_dumps(record.missing_contract_refs),
                _json_dumps(record.blocked_states),
                record.stale_state,
                record.evidence_gap,
                record.next_safe_action,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def record_idempotency_key(
        self, *, key_ref: str, scope_ref: str, receipt_ref: str
    ) -> None:
        _validate_safe_ref(key_ref, "key_ref")
        _validate_safe_ref(scope_ref, "scope_ref")
        _validate_safe_ref(receipt_ref, "receipt_ref")
        try:
            self._execute(
                """
                INSERT INTO idempotency_keys (key_ref, scope_ref, receipt_ref, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key_ref, scope_ref, receipt_ref, _utc_iso()),
            )
        except sqlite3.IntegrityError as exc:
            raise FounderLoopStorageDuplicateError(
                "FOUNDER_LOOP_IDEMPOTENCY_DUPLICATE"
            ) from exc

    def append_log(self, kind: JsonlLogKind, payload: dict[str, Any]) -> dict[str, str]:
        _validate_safe_payload(payload, f"{kind.value}_log")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        path = self.logs_dir / f"{kind.value}.jsonl"
        record = {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "kind": kind.value,
            "event_ref": payload.get("event_ref", f"founder-loop-log:{kind.value}"),
            "safe_summary": payload.get(
                "safe_summary", "Founder Loop redacted event recorded."
            ),
            "evidence_refs": payload.get("evidence_refs", []),
            "created_at": _utc_iso(),
        }
        _validate_safe_payload(record, f"{kind.value}_log_record")
        append_durable_jsonl(path, _json_dumps(record))
        return {
            "log_ref": f"founder-loop-log:{kind.value}",
            "event_ref": str(record["event_ref"]),
        }

    def backup_manifest(self) -> dict[str, Any]:
        return backup_contract_manifest()

    def _ensure_storage(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            require_compatible_schema(
                conn, migration_error=FounderLoopStorageMigrationRequiredError
            )
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS storage_migrations (
                    migration_ref TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_inbox (
                    item_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    surface TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_class TEXT NOT NULL DEFAULT 'medium',
                    action_kind TEXT NOT NULL DEFAULT 'review_only',
                    side_effect_class TEXT NOT NULL,
                    authority_boundary TEXT NOT NULL DEFAULT 'Control Center is review-only; Python Agent Core approval is required before mutation.',
                    approval_required INTEGER NOT NULL,
                    approval_envelope_ref TEXT,
                    approval_envelope_status TEXT NOT NULL DEFAULT 'missing_until_scoped_contract',
                    state_change_contract_ref TEXT,
                    state_change_readiness TEXT NOT NULL DEFAULT 'blocked_missing_backend_contract',
                    blocked_state TEXT,
                    evidence_refs_json TEXT NOT NULL,
                    receipt_refs_json TEXT NOT NULL DEFAULT '[]',
                    audit_refs_json TEXT NOT NULL DEFAULT '[]',
                    idempotency_key_ref TEXT,
                    expires_at TEXT,
                    stale_state TEXT NOT NULL DEFAULT 'recheck_required_before_mutation',
                    rollback_ref TEXT,
                    safe_disable_ref TEXT,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
                    max_approved_cost_usd REAL NOT NULL DEFAULT 0.0,
                    provider_ref TEXT NOT NULL DEFAULT 'provider-ref:not-invoked',
                    model_profile_ref TEXT NOT NULL DEFAULT 'model-profile-ref:not-invoked',
                    input_metered_units INTEGER NOT NULL DEFAULT 0,
                    output_metered_units INTEGER NOT NULL DEFAULT 0,
                    total_metered_units INTEGER NOT NULL DEFAULT 0,
                    cost_estimate_ref TEXT NOT NULL DEFAULT 'cost-estimate-ref:not-invoked',
                    captured_usage_ref TEXT NOT NULL DEFAULT 'usage-capture-ref:not-invoked',
                    budget_decision_ref TEXT NOT NULL DEFAULT 'budget-decision-ref:not-invoked',
                    cost_receipt_refs_json TEXT NOT NULL DEFAULT '[]',
                    cost_blocked_state_refs_json TEXT NOT NULL DEFAULT '[]',
                    cost_state_label TEXT NOT NULL DEFAULT 'Cost blocked',
                    provider_authority_state_label TEXT NOT NULL DEFAULT 'No provider authority',
                    unknown_paid_cost_requires_explicit_approval INTEGER NOT NULL DEFAULT 1,
                    frontier_usage_claimed INTEGER NOT NULL DEFAULT 0,
                    next_safe_action TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked until a scoped backend contract exists.',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_revision_state (
                    item_ref TEXT PRIMARY KEY,
                    generation INTEGER NOT NULL,
                    generation_ref TEXT NOT NULL,
                    revision_ref TEXT NOT NULL,
                    revision_fingerprint_ref TEXT NOT NULL,
                    source_fingerprint_ref TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_envelopes (
                    envelope_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    envelope_ref TEXT NOT NULL,
                    item_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_envelope_promotions (
                    promotion_ref TEXT PRIMARY KEY,
                    today_item_ref TEXT NOT NULL,
                    item_ref TEXT NOT NULL,
                    action_envelope_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    audit_ref TEXT NOT NULL,
                    idempotency_key_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    evidence_timeline_event_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_envelope_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    action_envelope_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_envelope_promotion_replays (
                    key_ref TEXT PRIMARY KEY,
                    today_item_ref TEXT NOT NULL,
                    item_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    action_envelope_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_decision_events (
                    decision_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    status TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    audit_ref TEXT NOT NULL,
                    idempotency_key_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    approval_ref TEXT,
                    approval_status TEXT NOT NULL,
                    approval_reason_refs_json TEXT NOT NULL DEFAULT '[]',
                    safe_summary TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
                    blocked_state_refs_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    decision_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_idempotency_replays (
                    key_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    decision_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS founder_loop_internal_approval_grants (
                    approval_ref TEXT PRIMARY KEY,
                    approval_kind TEXT NOT NULL,
                    subject_ref TEXT NOT NULL,
                    requested_action TEXT NOT NULL,
                    exact_scope_ref TEXT NOT NULL,
                    idempotency_key_ref TEXT NOT NULL,
                    grant_json TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS local_tasks (
                    local_task_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    action_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS local_task_commit_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    local_task_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS
                    idx_local_task_commit_receipts_created_item
                ON local_task_commit_receipts(created_at DESC, item_ref ASC);
                CREATE TABLE IF NOT EXISTS local_task_commit_replays (
                    key_ref TEXT PRIMARY KEY,
                    item_ref TEXT NOT NULL,
                    local_task_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS local_task_lane_postures (
                    lane_id TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    safe_disable_ref TEXT NOT NULL,
                    rollback_ref TEXT NOT NULL,
                    safe_disable_posture_ref TEXT NOT NULL,
                    disabled_reason_refs_json TEXT NOT NULL DEFAULT '[]',
                    blocked_state_refs_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_write_lane_postures (
                    lane_id TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    safe_disable_ref TEXT NOT NULL,
                    rollback_ref TEXT NOT NULL,
                    safe_disable_posture_ref TEXT NOT NULL,
                    disabled_reason_refs_json TEXT NOT NULL DEFAULT '[]',
                    blocked_state_refs_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_context_pack_action_proposals (
                    receipt_ref TEXT PRIMARY KEY,
                    context_pack_ref TEXT NOT NULL,
                    context_pack_proposal_ref TEXT NOT NULL,
                    item_ref TEXT NOT NULL,
                    action_envelope_ref TEXT NOT NULL,
                    proposal_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_context_pack_action_replays (
                    key_ref TEXT PRIMARY KEY,
                    context_pack_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    proposal_ref TEXT NOT NULL,
                    action_envelope_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS web_evidence_attachments (
                    attachment_ref TEXT PRIMARY KEY,
                    request_ref TEXT UNIQUE NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    safe_url_ref TEXT NOT NULL,
                    host_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_feedback_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    memory_record_ref TEXT,
                    feedback_ref TEXT,
                    target_ref TEXT,
                    feedback_kind TEXT NOT NULL,
                    payload_fingerprint_ref TEXT,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_feedback_replays (
                    key_ref TEXT PRIMARY KEY,
                    memory_record_ref TEXT,
                    feedback_ref TEXT,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    receipt_json TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_turn_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    turn_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_turn_receipt_replays (
                    key_ref TEXT PRIMARY KEY,
                    turn_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_handoff_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    turn_ref TEXT NOT NULL,
                    handoff_target TEXT NOT NULL,
                    handoff_ref TEXT NOT NULL,
                    created_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_handoff_replays (
                    key_ref TEXT PRIMARY KEY,
                    turn_ref TEXT NOT NULL,
                    handoff_target TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    handoff_ref TEXT NOT NULL,
                    created_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plan_summaries (
                    plan_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    next_step_summary TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_queue (
                    review_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    candidate_kind TEXT NOT NULL DEFAULT 'preference',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL,
                    review_state TEXT NOT NULL DEFAULT 'review_needed',
                    side_effect_class TEXT NOT NULL DEFAULT 'local_dev_workspace_only',
                    authority_boundary TEXT NOT NULL DEFAULT 'Review-only memory candidate; memory writes and context injection remain unscoped.',
                    provenance_refs_json TEXT NOT NULL DEFAULT '[]',
                    source_refs_json TEXT NOT NULL DEFAULT '[]',
                    missing_contract_refs_json TEXT NOT NULL DEFAULT '[]',
                    correction_posture TEXT NOT NULL DEFAULT 'correction_requires_scoped_memory_write_contract',
                    rejection_posture TEXT NOT NULL DEFAULT 'rejection_is_review_state_only',
                    retention_posture TEXT NOT NULL DEFAULT 'retention_policy_not_bound',
                    delete_posture TEXT NOT NULL DEFAULT 'delete_execution_not_scoped',
                    confidence_posture TEXT NOT NULL DEFAULT 'safe_summary_unverified',
                    stale_state TEXT NOT NULL DEFAULT 'recheck_source_refs_before_memory_use',
                    blocked_states_json TEXT NOT NULL DEFAULT '[]',
                    next_safe_action TEXT NOT NULL DEFAULT 'Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.',
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_decisions (
                    receipt_ref TEXT PRIMARY KEY,
                    candidate_ref TEXT NOT NULL,
                    review_ref TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    decision_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_decision_replays (
                    key_ref TEXT PRIMARY KEY,
                    candidate_ref TEXT NOT NULL,
                    review_ref TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    decision_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_manual_candidate_replays (
                    key_ref TEXT PRIMARY KEY,
                    review_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_feedback_receipts (
                    receipt_ref TEXT PRIMARY KEY,
                    memory_record_ref TEXT,
                    feedback_ref TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    feedback_kind TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_feedback_replays (
                    key_ref TEXT PRIMARY KEY,
                    memory_record_ref TEXT,
                    receipt_ref TEXT NOT NULL,
                    feedback_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS briefing_items (
                    briefing_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL DEFAULT 'local_dev_workspace_only',
                    authority_boundary TEXT NOT NULL DEFAULT 'Review-only briefing summary; source reads and delivery remain unscoped.',
                    source_readiness TEXT NOT NULL DEFAULT 'blocked_missing_source_contract',
                    source_refs_json TEXT NOT NULL DEFAULT '[]',
                    missing_contract_refs_json TEXT NOT NULL DEFAULT '[]',
                    blocked_states_json TEXT NOT NULL DEFAULT '[]',
                    stale_state TEXT NOT NULL DEFAULT 'recheck_required_before_source_contract',
                    evidence_gap TEXT NOT NULL DEFAULT 'No source connector evidence is bound in this briefing slice.',
                    next_safe_action TEXT NOT NULL DEFAULT 'Define read-only source contracts before source reads or refresh.',
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key_ref TEXT PRIMARY KEY,
                    scope_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS route_state_snapshots (
                    snapshot_ref TEXT PRIMARY KEY,
                    route_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_refs (
                    evidence_ref TEXT PRIMARY KEY,
                    safe_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            ensure_memory_runtime_operation_tables(conn)
            conn.execute(
                """
                INSERT INTO storage_metadata (key, value, updated_at)
                VALUES ('schema_version', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (FOUNDER_LOOP_SCHEMA_VERSION, _utc_iso()),
            )
            record_bootstrap_migration(conn, applied_at=_utc_iso())
            self._ensure_action_inbox_contract_columns(conn)
            self._ensure_memory_review_contract_columns(conn)
            self._ensure_briefing_contract_columns(conn)
            self._ensure_local_task_lane_posture(conn)
            self._ensure_memory_review_write_lane_posture(conn)
        if self.seed_defaults:
            self._seed_defaults_if_empty()
            founder_loop_exact_action.ensure_exact_attention_action(
                self, FounderLoopActionRecord
            )
            self._backfill_seed_action_contract_metadata()
            self._backfill_seed_memory_review_contract_metadata()
            self._backfill_seed_briefing_contract_metadata()

    def _ensure_local_task_lane_posture(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            INSERT INTO local_task_lane_postures (
                lane_id, enabled, safe_disable_ref, rollback_ref,
                safe_disable_posture_ref, disabled_reason_refs_json,
                blocked_state_refs_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(lane_id) DO NOTHING
            """,
            (
                FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
                1,
                FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
                FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
                FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF,
                "[]",
                "[]",
                _utc_iso(),
            ),
        )

    def _ensure_memory_review_write_lane_posture(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        conn.execute(
            """
            INSERT INTO memory_review_write_lane_postures (
                lane_id, enabled, safe_disable_ref, rollback_ref,
                safe_disable_posture_ref, disabled_reason_refs_json,
                blocked_state_refs_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(lane_id) DO NOTHING
            """,
            (
                MEMORY_REVIEW_WRITE_LANE_ID,
                1,
                MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
                MEMORY_REVIEW_WRITE_ROLLBACK_REF,
                MEMORY_REVIEW_WRITE_SAFE_DISABLE_POSTURE_REF,
                "[]",
                "[]",
                _utc_iso(),
            ),
        )

    def _ensure_action_inbox_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(action_inbox)").fetchall()
        }
        additions = {
            "risk_class": "TEXT NOT NULL DEFAULT 'medium'",
            "action_kind": "TEXT NOT NULL DEFAULT 'review_only'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Control Center is review-only; Python Agent Core "
                "approval is required before mutation.'"
            ),
            "approval_envelope_ref": "TEXT",
            "approval_envelope_status": "TEXT NOT NULL DEFAULT 'missing_until_scoped_contract'",
            "state_change_contract_ref": "TEXT",
            "state_change_readiness": "TEXT NOT NULL DEFAULT 'blocked_missing_backend_contract'",
            "receipt_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "audit_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "idempotency_key_ref": "TEXT",
            "expires_at": "TEXT",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_required_before_mutation'",
            "rollback_ref": "TEXT",
            "safe_disable_ref": "TEXT",
            "estimated_cost_usd": "REAL NOT NULL DEFAULT 0.0",
            "max_approved_cost_usd": "REAL NOT NULL DEFAULT 0.0",
            "provider_ref": "TEXT NOT NULL DEFAULT 'provider-ref:not-invoked'",
            "model_profile_ref": "TEXT NOT NULL DEFAULT 'model-profile-ref:not-invoked'",
            "input_metered_units": "INTEGER NOT NULL DEFAULT 0",
            "output_metered_units": "INTEGER NOT NULL DEFAULT 0",
            "total_metered_units": "INTEGER NOT NULL DEFAULT 0",
            "cost_estimate_ref": "TEXT NOT NULL DEFAULT 'cost-estimate-ref:not-invoked'",
            "captured_usage_ref": "TEXT NOT NULL DEFAULT 'usage-capture-ref:not-invoked'",
            "budget_decision_ref": "TEXT NOT NULL DEFAULT 'budget-decision-ref:not-invoked'",
            "cost_receipt_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "cost_blocked_state_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "cost_state_label": "TEXT NOT NULL DEFAULT 'Cost blocked'",
            "provider_authority_state_label": (
                "TEXT NOT NULL DEFAULT 'No provider authority'"
            ),
            "unknown_paid_cost_requires_explicit_approval": (
                "INTEGER NOT NULL DEFAULT 1"
            ),
            "frontier_usage_claimed": "INTEGER NOT NULL DEFAULT 0",
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked "
                "until a scoped backend contract exists.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE action_inbox ADD COLUMN {column_name} {column_spec}"
                )
        legacy_deadline_markers = (
            "review_required_before_action_decision",
            "review_required_before_decision_or_execution",
            "review_required_before_any_future_action_decision",
            "review_required_before_mutation",
            "review_required_before_source_contract",
            "review_required_before_local_task_commit",
        )
        placeholders = ", ".join("?" for _ in legacy_deadline_markers)
        affected_item_refs = [
            str(row["item_ref"])
            for row in conn.execute(
                f"SELECT item_ref FROM action_inbox "
                f"WHERE expires_at IN ({placeholders})",
                legacy_deadline_markers,
            ).fetchall()
        ]
        for item_ref in affected_item_refs:
            action = self._action_payload_for_item_ref(
                item_ref,
                conn=conn,
                include_generated=False,
            )
            if action is not None:
                self._synchronize_action_revision_state(
                    {**action, **_action_envelope_contract_payload(action)},
                    conn=conn,
                )
        conn.execute(
            f"UPDATE action_inbox SET expires_at = NULL "
            f"WHERE expires_at IN ({placeholders})",
            legacy_deadline_markers,
        )
        for item_ref in affected_item_refs:
            action = self._action_payload_for_item_ref(
                item_ref,
                conn=conn,
                include_generated=False,
            )
            if action is not None:
                self._synchronize_action_revision_state(
                    {**action, **_action_envelope_contract_payload(action)},
                    conn=conn,
                )

    def _ensure_memory_review_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(memory_review_queue)").fetchall()
        }
        additions = {
            "candidate_kind": "TEXT NOT NULL DEFAULT 'preference'",
            "priority": "TEXT NOT NULL DEFAULT 'medium'",
            "review_state": "TEXT NOT NULL DEFAULT 'review_needed'",
            "side_effect_class": "TEXT NOT NULL DEFAULT 'local_dev_workspace_only'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Review-only memory candidate; memory writes "
                "and context injection remain unscoped.'"
            ),
            "provenance_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "source_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "missing_contract_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "correction_posture": (
                "TEXT NOT NULL DEFAULT 'correction_requires_scoped_memory_write_contract'"
            ),
            "rejection_posture": "TEXT NOT NULL DEFAULT 'rejection_is_review_state_only'",
            "retention_posture": "TEXT NOT NULL DEFAULT 'retention_policy_not_bound'",
            "delete_posture": "TEXT NOT NULL DEFAULT 'delete_execution_not_scoped'",
            "confidence_posture": "TEXT NOT NULL DEFAULT 'safe_summary_unverified'",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_source_refs_before_memory_use'",
            "blocked_states_json": "TEXT NOT NULL DEFAULT '[]'",
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Review provenance and evidence refs; keep "
                "writes blocked until a scoped memory policy milestone.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE memory_review_queue ADD COLUMN {column_name} {column_spec}"
                )

    def _ensure_briefing_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(briefing_items)").fetchall()
        }
        additions = {
            "priority": "TEXT NOT NULL DEFAULT 'medium'",
            "side_effect_class": "TEXT NOT NULL DEFAULT 'local_dev_workspace_only'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Review-only briefing summary; source reads and "
                "delivery remain unscoped.'"
            ),
            "source_readiness": "TEXT NOT NULL DEFAULT 'blocked_missing_source_contract'",
            "source_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "missing_contract_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "blocked_states_json": "TEXT NOT NULL DEFAULT '[]'",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_required_before_source_contract'",
            "evidence_gap": (
                "TEXT NOT NULL DEFAULT 'No source connector evidence is bound in this "
                "briefing slice.'"
            ),
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Define read-only source contracts before source "
                "reads or refresh.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE briefing_items ADD COLUMN {column_name} {column_spec}"
                )

    def _seed_defaults_if_empty(self) -> None:
        if self._count("action_inbox") == 0:
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:setup-assistant-hardening",
                    title="Setup Assistant hardening review",
                    safe_summary=(
                        "Dry-run setup envelopes are available for review only; installer and "
                        "background-service authority remain blocked."
                    ),
                    surface="Actions",
                    priority="high",
                    risk_class="high",
                    status="review_ready",
                    side_effect_class="validation_only",
                    authority_boundary=(
                        "Review-only display; Python Agent Core and LocalApprovalAuthority must "
                        "validate exact scope before mutation."
                    ),
                    approval_required=True,
                    approval_envelope_ref="approval-envelope:founder-loop:setup-assistant-hardening",
                    approval_envelope_status="dry_run_ref_available",
                    state_change_contract_ref="contract-ref:founder-loop:setup-assistant-hardening",
                    state_change_readiness="blocked_pending_scoped_mutation_contract",
                    blocked_state="Mutation requires exact approval, idempotency, rollback, and receipt refs.",
                    evidence_refs=["evidence-ref:founder-loop:setup-assistant"],
                    receipt_refs=[
                        "receipt-plan:founder-loop:setup-assistant-hardening"
                    ],
                    audit_refs=["audit-plan:founder-loop:setup-assistant-hardening"],
                    idempotency_key_ref="idempotency-ref:founder-loop:setup-assistant-hardening",
                    expires_at=None,
                    stale_state="recheck_setup_summary_before_mutation",
                    rollback_ref="rollback-plan:founder-loop:setup-assistant-hardening",
                    safe_disable_ref="safe-disable:founder-loop:setup-assistant-hardening",
                    next_safe_action=(
                        "Review refs only; request a scoped state-change milestone before mutation."
                    ),
                )
            )
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:morning-briefing-skeleton",
                    title="Morning Briefing skeleton review",
                    safe_summary=(
                        "Briefing items are storage-backed summaries only; email and calendar reads "
                        "remain future contracts."
                    ),
                    surface="Today",
                    priority="medium",
                    risk_class="medium",
                    status="review_ready",
                    side_effect_class="local_dev_workspace_only",
                    authority_boundary=(
                        "Review-only display; source reads and delivery remain unscoped."
                    ),
                    approval_required=False,
                    approval_envelope_status="not_required_for_inspection",
                    state_change_readiness="blocked_no_source_read_contract",
                    blocked_state="Connector reads and notification delivery are not scoped.",
                    evidence_refs=["evidence-ref:founder-loop:briefing"],
                    audit_refs=["audit-plan:founder-loop:briefing-review"],
                    expires_at=None,
                    stale_state="recheck_source_status_before_contract",
                    safe_disable_ref="safe-disable:founder-loop:briefing-surface",
                    next_safe_action="Define read-only briefing source refs before source reads.",
                )
            )
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:local-task-create-scorecard",
                    title="Create operational maturity scorecard task",
                    safe_summary=(
                        "Create a local Founder Loop task for maintaining the "
                        "operational maturity scorecard; no external connector, "
                        "shell, model, memory, or context action is involved."
                    ),
                    surface="Actions",
                    priority="high",
                    risk_class="medium",
                    action_kind=FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
                    status="review_ready",
                    side_effect_class="local_dev_workspace_only",
                    authority_boundary=(
                        "Exact LocalApprovalAuthority scope is required before "
                        "the local task can be committed."
                    ),
                    approval_required=True,
                    approval_envelope_ref="approval-envelope:founder-loop:local-task-create-scorecard",
                    approval_envelope_status="review_ready_exact_scope_required",
                    state_change_contract_ref=FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
                    state_change_readiness="local_task_commit_contract_requires_approval",
                    blocked_state=(
                        "Local task commit is blocked until this Action item is "
                        "approved with exact scope and idempotency."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:local-task-commit"],
                    receipt_refs=[
                        "receipt-plan:founder-loop:local-task-create-scorecard"
                    ],
                    audit_refs=["audit-plan:founder-loop:local-task-create-scorecard"],
                    idempotency_key_ref="idempotency-ref:founder-loop:local-task-create-scorecard",
                    expires_at=None,
                    stale_state="recheck_action_approval_before_local_task_commit",
                    rollback_ref="rollback-not-applicable:local-task-safe-disable",
                    safe_disable_ref="safe-disable:founder-loop:local-task-create-scorecard",
                    next_safe_action=(
                        "Approve this exact local task action before committing it "
                        "through the local-task route."
                    ),
                )
            )
        if self._count("plan_summaries") == 0:
            self.upsert_plan(
                FounderLoopPlanRecord(
                    plan_ref="plan-summary:founder-loop-v1",
                    title="Founder Loop v1 product spine",
                    safe_summary=(
                        "Today, Actions, Plans, Memory, Evidence, and Settings are the active "
                        "single-user operator loop."
                    ),
                    next_step_summary=(
                        "Keep the loop storage-backed and review-gated before adding broader "
                        "runtime surfaces."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:product-spine"],
                )
            )
        if self._count("memory_review_queue") == 0:
            self.upsert_memory_review(
                FounderLoopMemoryReviewRecord(
                    review_ref="memory-review:founder-loop-preferences",
                    title="Founder Loop memory review",
                    safe_summary=(
                        "Memory remains a review queue with safe summaries; recall is not treated "
                        "as truth or execution authority."
                    ),
                    candidate_kind="preference",
                    priority="high",
                    status="review_needed",
                    review_state="review_needed",
                    authority_boundary=(
                        "Review-only memory candidate; recall is not truth, and writes, "
                        "deletes, and context injection remain unscoped."
                    ),
                    provenance_refs=[
                        "provenance-ref:manual-note:founder-loop-preferences"
                    ],
                    source_refs=["source-ref:manual-note:founder-loop-storage"],
                    missing_contract_refs=[
                        "contract-ref:memory-write-policy-binding-missing",
                        "contract-ref:memory-retention-delete-missing",
                        "contract-ref:context-injection-missing",
                    ],
                    correction_posture="correction_requires_scoped_memory_write_contract",
                    rejection_posture="rejection_is_review_state_only_until_capture_contract",
                    retention_posture="retention_policy_not_bound",
                    delete_posture="delete_execution_not_scoped",
                    confidence_posture="safe_summary_unverified",
                    stale_state="recheck_source_refs_before_memory_use",
                    blocked_states=[
                        "no_memory_write",
                        "no_context_injection",
                        "no_memory_delete",
                        "no_memory_export",
                        "no_raw_source_display",
                        "no_external_crm_write",
                        "no_account_sync",
                        "no_automatic_recall",
                        "no_connector_write",
                        "no_model_provider_authority",
                        "no_background_sync",
                    ],
                    next_safe_action=(
                        "Review provenance and evidence refs; keep writes blocked until a "
                        "scoped memory policy milestone."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:memory"],
                )
            )
        if self._count("briefing_items") == 0:
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:api-boundary-modularization",
                    title="API boundary modularization",
                    safe_summary=(
                        "New Founder Loop summaries use router and repository seams while the "
                        "legacy FastAPI module remains a compatibility boundary."
                    ),
                    priority="high",
                    status="active",
                    source_readiness="local_status_refs_only",
                    source_refs=["source-ref:control-center-route-status"],
                    missing_contract_refs=[
                        "contract-ref:email-read-only-missing",
                        "contract-ref:calendar-read-only-missing",
                        "contract-ref:notification-delivery-missing",
                    ],
                    blocked_states=[
                        "no_email_calendar_source_contract",
                        "no_background_refresh",
                    ],
                    stale_state="recheck_route_status_before_briefing_use",
                    evidence_gap="No email, calendar, or notification source evidence is bound.",
                    next_safe_action=(
                        "Use route and storage refs only; define source contracts before refresh."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:api-boundary"],
                )
            )
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:storage-state-first-loop",
                    title="Storage-backed first loop",
                    safe_summary=(
                        "SQLite stores indexed loop state and JSONL logs are reserved for "
                        "redacted append-only receipts, audits, transcripts, and realtime events."
                    ),
                    priority="medium",
                    status="active",
                    source_readiness="local_storage_refs_only",
                    source_refs=["source-ref:founder-loop-storage"],
                    missing_contract_refs=[
                        "contract-ref:email-read-only-missing",
                        "contract-ref:calendar-read-only-missing",
                        "contract-ref:notification-delivery-missing",
                    ],
                    blocked_states=[
                        "no_connector_runtime",
                        "no_notification_delivery",
                    ],
                    stale_state="recheck_storage_status_before_briefing_use",
                    evidence_gap="No connector receipts or source refresh receipts are bound.",
                    next_safe_action=(
                        "Inspect storage status only; keep source reads blocked until scoped."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:storage"],
                )
            )
        if self._count("evidence_refs") == 0:
            self._execute(
                """
                INSERT INTO evidence_refs (evidence_ref, safe_summary, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    "evidence-ref:founder-loop:seed",
                    "Initial storage-backed Founder Loop safe refs.",
                    _utc_iso(),
                ),
            )

    def _backfill_seed_action_contract_metadata(self) -> None:
        self._update_action_contract_metadata(
            "founder-action:setup-assistant-hardening",
            {
                "risk_class": "high",
                "authority_boundary": (
                    "Review-only display; Python Agent Core and LocalApprovalAuthority must "
                    "validate exact scope before mutation."
                ),
                "approval_envelope_ref": "approval-envelope:founder-loop:setup-assistant-hardening",
                "approval_envelope_status": "dry_run_ref_available",
                "state_change_contract_ref": "contract-ref:founder-loop:setup-assistant-hardening",
                "state_change_readiness": "blocked_pending_scoped_mutation_contract",
                "receipt_refs": ["receipt-plan:founder-loop:setup-assistant-hardening"],
                "audit_refs": ["audit-plan:founder-loop:setup-assistant-hardening"],
                "idempotency_key_ref": "idempotency-ref:founder-loop:setup-assistant-hardening",
                "expires_at": None,
                "stale_state": "recheck_setup_summary_before_mutation",
                "rollback_ref": "rollback-plan:founder-loop:setup-assistant-hardening",
                "safe_disable_ref": "safe-disable:founder-loop:setup-assistant-hardening",
                "next_safe_action": (
                    "Review refs only; request a scoped state-change milestone before mutation."
                ),
            },
        )
        self._update_action_contract_metadata(
            "founder-action:morning-briefing-skeleton",
            {
                "risk_class": "medium",
                "authority_boundary": (
                    "Review-only display; source reads and delivery remain unscoped."
                ),
                "approval_envelope_status": "not_required_for_inspection",
                "state_change_readiness": "blocked_no_source_read_contract",
                "audit_refs": ["audit-plan:founder-loop:briefing-review"],
                "expires_at": None,
                "stale_state": "recheck_source_status_before_contract",
                "safe_disable_ref": "safe-disable:founder-loop:briefing-surface",
                "next_safe_action": "Define read-only briefing source refs before source reads.",
            },
        )

    def _update_action_contract_metadata(
        self, item_ref: str, metadata: dict[str, Any]
    ) -> None:
        _validate_safe_ref(item_ref, "item_ref")
        _validate_safe_payload(metadata, "action_contract_metadata")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                UPDATE action_inbox
                SET risk_class = COALESCE(?, risk_class),
                    authority_boundary = COALESCE(?, authority_boundary),
                    approval_envelope_ref = ?,
                    approval_envelope_status = COALESCE(?, approval_envelope_status),
                    state_change_contract_ref = ?,
                    state_change_readiness = COALESCE(?, state_change_readiness),
                    receipt_refs_json = COALESCE(?, receipt_refs_json),
                    audit_refs_json = COALESCE(?, audit_refs_json),
                    idempotency_key_ref = ?,
                    expires_at = ?,
                    stale_state = COALESCE(?, stale_state),
                    rollback_ref = ?,
                    safe_disable_ref = ?,
                    next_safe_action = COALESCE(?, next_safe_action),
                    updated_at = ?
                WHERE item_ref = ?
                """,
                (
                    metadata.get("risk_class"),
                    metadata.get("authority_boundary"),
                    metadata.get("approval_envelope_ref"),
                    metadata.get("approval_envelope_status"),
                    metadata.get("state_change_contract_ref"),
                    metadata.get("state_change_readiness"),
                    _json_dumps(metadata["receipt_refs"])
                    if "receipt_refs" in metadata
                    else None,
                    _json_dumps(metadata["audit_refs"])
                    if "audit_refs" in metadata
                    else None,
                    metadata.get("idempotency_key_ref"),
                    metadata.get("expires_at"),
                    metadata.get("stale_state"),
                    metadata.get("rollback_ref"),
                    metadata.get("safe_disable_ref"),
                    metadata.get("next_safe_action"),
                    _utc_iso(),
                    item_ref,
                ),
            )
            action = self._action_payload_for_item_ref(
                item_ref,
                conn=conn,
                include_generated=False,
            )
            if action is not None:
                self._synchronize_action_revision_state(
                    {**action, **_action_envelope_contract_payload(action)},
                    conn=conn,
                )

    def _backfill_seed_memory_review_contract_metadata(self) -> None:
        if self._count("memory_review_decisions") > 0:
            return
        self._update_memory_review_contract_metadata(
            "memory-review:founder-loop-preferences",
            {
                "candidate_kind": "preference",
                "priority": "high",
                "review_state": "review_needed",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only memory candidate; recall is not truth, and writes, "
                    "deletes, and context injection remain unscoped."
                ),
                "provenance_refs": [
                    "provenance-ref:manual-note:founder-loop-preferences"
                ],
                "source_refs": ["source-ref:manual-note:founder-loop-storage"],
                "missing_contract_refs": [
                    "contract-ref:memory-write-policy-binding-missing",
                    "contract-ref:memory-retention-delete-missing",
                    "contract-ref:context-injection-missing",
                ],
                "correction_posture": "correction_requires_scoped_memory_write_contract",
                "rejection_posture": "rejection_is_review_state_only_until_capture_contract",
                "retention_posture": "retention_policy_not_bound",
                "delete_posture": "delete_execution_not_scoped",
                "confidence_posture": "safe_summary_unverified",
                "stale_state": "recheck_source_refs_before_memory_use",
                "blocked_states": [
                    "no_memory_write",
                    "no_context_injection",
                    "no_memory_delete",
                    "no_memory_export",
                    "no_raw_source_display",
                    "no_external_crm_write",
                    "no_account_sync",
                    "no_automatic_recall",
                    "no_connector_write",
                    "no_model_provider_authority",
                    "no_background_sync",
                ],
                "next_safe_action": (
                    "Review provenance and evidence refs; keep writes blocked until a "
                    "scoped memory policy milestone."
                ),
            },
        )

    def _update_memory_review_contract_metadata(
        self,
        review_ref: str,
        metadata: dict[str, Any],
    ) -> None:
        _validate_safe_ref(review_ref, "review_ref")
        _validate_safe_payload(metadata, "memory_review_contract_metadata")
        self._execute(
            """
            UPDATE memory_review_queue
            SET candidate_kind = COALESCE(?, candidate_kind),
                priority = COALESCE(?, priority),
                review_state = COALESCE(?, review_state),
                side_effect_class = COALESCE(?, side_effect_class),
                authority_boundary = COALESCE(?, authority_boundary),
                provenance_refs_json = COALESCE(?, provenance_refs_json),
                source_refs_json = COALESCE(?, source_refs_json),
                missing_contract_refs_json = COALESCE(?, missing_contract_refs_json),
                correction_posture = COALESCE(?, correction_posture),
                rejection_posture = COALESCE(?, rejection_posture),
                retention_posture = COALESCE(?, retention_posture),
                delete_posture = COALESCE(?, delete_posture),
                confidence_posture = COALESCE(?, confidence_posture),
                stale_state = COALESCE(?, stale_state),
                blocked_states_json = COALESCE(?, blocked_states_json),
                next_safe_action = COALESCE(?, next_safe_action)
            WHERE review_ref = ?
            """,
            (
                metadata.get("candidate_kind"),
                metadata.get("priority"),
                metadata.get("review_state"),
                metadata.get("side_effect_class"),
                metadata.get("authority_boundary"),
                (
                    _json_dumps(metadata["provenance_refs"])
                    if "provenance_refs" in metadata
                    else None
                ),
                _json_dumps(metadata["source_refs"])
                if "source_refs" in metadata
                else None,
                (
                    _json_dumps(metadata["missing_contract_refs"])
                    if "missing_contract_refs" in metadata
                    else None
                ),
                metadata.get("correction_posture"),
                metadata.get("rejection_posture"),
                metadata.get("retention_posture"),
                metadata.get("delete_posture"),
                metadata.get("confidence_posture"),
                metadata.get("stale_state"),
                _json_dumps(metadata["blocked_states"])
                if "blocked_states" in metadata
                else None,
                metadata.get("next_safe_action"),
                review_ref,
            ),
        )

    def _backfill_seed_briefing_contract_metadata(self) -> None:
        common_missing_contract_refs = [
            "contract-ref:email-read-only-missing",
            "contract-ref:calendar-read-only-missing",
            "contract-ref:notification-delivery-missing",
        ]
        self._update_briefing_contract_metadata(
            "briefing:api-boundary-modularization",
            {
                "priority": "high",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only briefing summary; source reads and delivery remain unscoped."
                ),
                "source_readiness": "local_status_refs_only",
                "source_refs": ["source-ref:control-center-route-status"],
                "missing_contract_refs": common_missing_contract_refs,
                "blocked_states": [
                    "no_email_calendar_source_contract",
                    "no_background_refresh",
                ],
                "stale_state": "recheck_route_status_before_briefing_use",
                "evidence_gap": "No email, calendar, or notification source evidence is bound.",
                "next_safe_action": (
                    "Use route and storage refs only; define source contracts before refresh."
                ),
            },
        )
        self._update_briefing_contract_metadata(
            "briefing:storage-state-first-loop",
            {
                "priority": "medium",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only briefing summary; source reads and delivery remain unscoped."
                ),
                "source_readiness": "local_storage_refs_only",
                "source_refs": ["source-ref:founder-loop-storage"],
                "missing_contract_refs": common_missing_contract_refs,
                "blocked_states": [
                    "no_connector_runtime",
                    "no_notification_delivery",
                ],
                "stale_state": "recheck_storage_status_before_briefing_use",
                "evidence_gap": "No connector receipts or source refresh receipts are bound.",
                "next_safe_action": (
                    "Inspect storage status only; keep source reads blocked until scoped."
                ),
            },
        )

    def _update_briefing_contract_metadata(
        self,
        briefing_ref: str,
        metadata: dict[str, Any],
    ) -> None:
        _validate_safe_ref(briefing_ref, "briefing_ref")
        _validate_safe_payload(metadata, "briefing_contract_metadata")
        self._execute(
            """
            UPDATE briefing_items
            SET priority = COALESCE(?, priority),
                side_effect_class = COALESCE(?, side_effect_class),
                authority_boundary = COALESCE(?, authority_boundary),
                source_readiness = COALESCE(?, source_readiness),
                source_refs_json = COALESCE(?, source_refs_json),
                missing_contract_refs_json = COALESCE(?, missing_contract_refs_json),
                blocked_states_json = COALESCE(?, blocked_states_json),
                stale_state = COALESCE(?, stale_state),
                evidence_gap = COALESCE(?, evidence_gap),
                next_safe_action = COALESCE(?, next_safe_action)
            WHERE briefing_ref = ?
            """,
            (
                metadata.get("priority"),
                metadata.get("side_effect_class"),
                metadata.get("authority_boundary"),
                metadata.get("source_readiness"),
                _json_dumps(metadata["source_refs"])
                if "source_refs" in metadata
                else None,
                (
                    _json_dumps(metadata["missing_contract_refs"])
                    if "missing_contract_refs" in metadata
                    else None
                ),
                _json_dumps(metadata["blocked_states"])
                if "blocked_states" in metadata
                else None,
                metadata.get("stale_state"),
                metadata.get("evidence_gap"),
                metadata.get("next_safe_action"),
                briefing_ref,
            ),
        )

    def _schema_version(self) -> str:
        rows = self._fetch_all(
            "SELECT value FROM storage_metadata WHERE key = 'schema_version' LIMIT 1",
            (),
        )
        return str(rows[0]["value"]) if rows else FOUNDER_LOOP_SCHEMA_VERSION

    def _count(self, table: str) -> int:
        allowed = {
            "action_envelopes",
            "action_decision_events",
            "action_envelope_promotions",
            "action_envelope_receipts",
            "action_inbox",
            "action_receipts",
            "founder_loop_internal_approval_grants",
            "local_tasks",
            "local_task_commit_receipts",
            "local_task_commit_replays",
            "local_task_lane_postures",
            "memory_review_write_lane_postures",
            "briefing_items",
            "chat_handoff_receipts",
            "chat_turn_receipts",
            "plan_summaries",
            "memory_review_decision_replays",
            "memory_review_decisions",
            "memory_review_queue",
            "memory_manual_candidate_replays",
            "memory_feedback_receipts",
            "memory_feedback_replays",
            "memory_context_pack_action_proposals",
            "memory_context_pack_action_replays",
            "memory_feedback_receipts",
            "memory_feedback_replays",
            "idempotency_keys",
            "route_state_snapshots",
            "evidence_refs",
            "web_evidence_attachments",
        }
        if table not in allowed:
            raise FounderLoopStorageError("FOUNDER_LOOP_TABLE_REF_DENIED")
        rows = self._fetch_all(f"SELECT COUNT(*) AS count FROM {table}", ())
        return int(rows[0]["count"])

    def _connect(self) -> sqlite3.Connection:
        return connect_founder_loop_sqlite(self.db_path, read_only=self.read_only)

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _bounded_limit(limit: int) -> int:
        return max(1, min(int(limit), 100))

    (persist_memory_feedback_receipt,)
    (prepare_memory_feedback_update_operation,)
