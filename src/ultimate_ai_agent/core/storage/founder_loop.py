from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
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
    FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS,
    FOUNDER_LOOP_ACTION_DECISION_KINDS,
    FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
    FounderLoopActionDecisionReceipt,
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionReceipt,
    FounderLoopActionEnvelopePromotionRequest,
    action_approval_request,
    action_decision_audit_ref,
    action_decision_receipt_ref,
    action_decision_ref,
    action_envelope_promotion_audit_ref,
    action_envelope_promotion_event_ref,
    action_envelope_promotion_receipt_ref,
    action_id_to_item_ref,
    action_payload_fingerprint_ref,
    decision_payload_for_fingerprint,
    promotion_payload_for_fingerprint,
    today_item_to_action_item_ref,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
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
    business_memory_authority_posture,
    business_memory_candidate_kind_rows,
    business_memory_candidate_ref,
    business_memory_quality_ref,
    business_memory_quality_state_rows,
    business_memory_surface_bindings,
)
from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
)
from ultimate_ai_agent.core.memory.local_store import LocalMemoryStore
from ultimate_ai_agent.core.memory.provider import MemoryProviderWriteRequest
from ultimate_ai_agent.core.memory.review_decisions import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_KINDS,
    MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS,
    MEMORY_REVIEW_DECISION_ROUTE_REFS,
    MEMORY_REVIEW_DECISION_STATES,
    MemoryReviewDecision,
    MemoryReviewDecisionKind,
    MemoryReviewDecisionRequest,
    MemoryReviewDecisionReceipt,
    memory_review_correction_ref,
    memory_review_decision_audit_ref,
    memory_review_decision_authority_posture,
    memory_review_decision_evidence_ref,
    memory_review_decision_payload_for_fingerprint,
    memory_review_decision_receipt_ref,
    memory_review_decision_ref,
    memory_review_decision_state_rows,
    memory_review_payload_fingerprint_ref,
    memory_review_rejection_ref,
    memory_review_reviewed_recall_ref,
)
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


FOUNDER_LOOP_SCHEMA_VERSION = "founder_loop_storage.v1"
FOUNDER_LOOP_STATE_DIR_ENV = "UAA_FOUNDER_LOOP_STATE_DIR"
DEFAULT_FOUNDER_LOOP_STATE_DIR = Path(".uaa") / "founder_loop"
SAFE_STATUS_REF_CHARS = re.compile(r"[^a-z0-9_.@-]+")
TODAY_PRODUCT_SPINE_CONTRACT_REF = "contract-ref:today-product-spine:v1"
EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF = "contract-ref:evidence-history-grammar:v1"
EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF = (
    "contract-ref:founder-loop-evidence-timeline-productization:v1"
)
EVIDENCE_TIMELINE_PRODUCTIZATION_ROUTE_REFS = (
    "GET /control-center/evidence/timeline",
)
EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES = (
    "action_envelope_created",
    "action_decision_recorded",
    "chat_turn_receipt_recorded",
    "chat_handoff_created",
    "memory_review_decision_recorded",
)
EVIDENCE_TIMELINE_PRODUCTIZED_GROUP_KINDS = (
    "today_item",
    "action",
    "chat_turn",
    "memory_candidate",
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
    status: str = Field(default="review_ready", min_length=1, max_length=80)
    side_effect_class: str = Field(default="validation_only", min_length=1, max_length=80)
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
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for field_name in ["evidence_refs", "receipt_refs", "audit_refs"]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "action_record")
        return self


class FounderLoopPlanRecord(BaseModel):
    plan_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    status: str = Field(default="partial_backend_not_product_ready", min_length=1, max_length=80)
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
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
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
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
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
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
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
    rollback_blockers: list[str] = Field(default_factory=list)
    latency_refs: list[str] = Field(default_factory=list)
    foundation_gate_refs: list[str] = Field(default_factory=list)
    redaction_status: str = Field(default="redacted_summary_only", min_length=1, max_length=80)
    stale_state: str = Field(default="recheck_refs_before_use", min_length=1, max_length=120)
    missing_evidence_posture: str = Field(default="no_missing_safe_refs", min_length=1, max_length=180)
    blocked_states: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceTimelineItem":
        _validate_safe_ref(self.timeline_item_ref, "timeline_item_ref")
        _validate_safe_ref(self.history_contract_ref, "history_contract_ref")
        if self.history_contract_ref != EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF:
            raise ValueError("evidence timeline item must use the current history grammar")
        if set(self.history_answers) != set(EVIDENCE_HISTORY_GRAMMAR_KEYS):
            raise ValueError("evidence timeline item must answer every history grammar question")
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
    "chat_turn_receipt_recorded",
    "chat_handoff_created",
    "memory_review_decision_recorded",
]
EvidenceTimelineProductizedGroupKind = Literal[
    "today_item",
    "action",
    "chat_turn",
    "memory_candidate",
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
    redaction_status: str = Field(default="redacted_summary_only", min_length=1, max_length=80)
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
            raise ValueError("evidence timeline event must answer every history grammar question")
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
    event_types: list[EvidenceTimelineProductizedEventType] = Field(default_factory=list)
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


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_STORAGE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe Founder Loop storage text")


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
            if any(fragment in normalized_key for fragment in UNSAFE_STORAGE_KEY_FRAGMENTS):
                raise ValueError(f"{field_name} contains unsafe Founder Loop storage key")
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


def _status_ref(prefix: str, value: str) -> str:
    safe_value = SAFE_STATUS_REF_CHARS.sub("-", value.lower()).strip("-")
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


def _utc_iso() -> str:
    return utc_now().isoformat()


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


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for key in list(payload):
        if key.endswith("_json"):
            payload[key.removesuffix("_json")] = json.loads(payload.pop(key) or "[]")
    if "approval_required" in payload:
        payload["approval_required"] = bool(payload["approval_required"])
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
    return next(
        policy
        for policy in policies
        if policy["source_kind"] == source_kind
    )


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
        "connector_write_enabled": payload["connector_write_enabled"],
        "shell_subprocess_execution_enabled": payload[
            "shell_subprocess_execution_enabled"
        ],
        "model_provider_authority_allowed": payload[
            "model_provider_authority_allowed"
        ],
        "safe_refs_only": payload["safe_refs_only"],
        "raw_content_included": payload["raw_content_included"],
        "plan_action_envelope_ref": payload["action_envelope_ref"],
        "plan_action_scope_ref": payload["scope_ref"],
        "plan_action_approval_requirement_ref": payload["approval_requirement_ref"],
        "plan_action_review_posture_refs": payload["review_posture_refs"],
        "plan_action_expected_receipt_refs": payload["expected_receipt_refs"],
        "plan_action_blocked_state_refs": payload["blocked_state_refs"],
        "plan_action_authority_boundary": payload["authority_boundary"],
    }


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
    return {
        "action_envelope_contract_ref": payload["contract_ref"],
        "action_envelope_ref": payload["action_envelope_ref"],
        "action_envelope_status": "review_ready_execution_blocked",
        "action_envelope_safe_summary": payload["safe_summary"],
        "action_scope_ref": payload["scope_ref"],
        "action_approval_requirement_ref": payload["approval_requirement_ref"],
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
        "action_envelope_connector_write_enabled": payload["connector_write_enabled"],
        "action_envelope_shell_execution_enabled": payload[
            "shell_subprocess_execution_enabled"
        ],
        "action_envelope_model_provider_authority_allowed": payload[
            "model_provider_authority_allowed"
        ],
        "action_envelope_safe_refs_only": payload["safe_refs_only"],
        "action_envelope_raw_content_included": payload["raw_content_included"],
    }


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
        "governed_code_workbench_validation_plan_ref": (
            payload["validation_plan_ref"]
        ),
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
        "governed_code_workbench_idempotency_key_ref": (
            payload["idempotency_key_ref"]
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
        str(primary.get("correction_posture", "correction_requires_scoped_contract")),
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
        "user_intent_low_confidence_policy_ref": payload[
            "low_confidence_policy_ref"
        ],
        "user_intent_conflict_policy_ref": payload["conflict_policy_ref"],
        "user_intent_next_safe_action": payload["next_safe_action"],
        "user_intent_review_required": payload["review_required"],
        "user_intent_safe_refs_only": payload["safe_refs_only"],
        "user_intent_evidence_required": payload["evidence_required"],
        "user_intent_low_confidence_asks_user": payload[
            "low_confidence_asks_user"
        ],
        "user_intent_conflicting_intent_asks_user": payload[
            "conflicting_intent_asks_user"
        ],
        "user_intent_hidden_authority_enabled": payload[
            "hidden_authority_enabled"
        ],
        "user_intent_action_execution_enabled": payload["action_execution_enabled"],
    }


class FounderLoopRepository:
    """Stdlib SQLite plus JSONL repository for the first Founder Loop state."""

    def __init__(self, state_dir: Path, *, seed_defaults: bool = True) -> None:
        self.state_dir = state_dir
        self.db_path = self.state_dir / "founder_loop.sqlite3"
        self.memory_review_recall_db_path = self.state_dir / "memory_review_recall.sqlite3"
        self.logs_dir = self.state_dir / "logs"
        self.seed_defaults = seed_defaults
        self._ensure_storage()

    @classmethod
    def from_env(cls, *, seed_defaults: bool = True) -> "FounderLoopRepository":
        configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_FOUNDER_LOOP_STATE_DIR
        return cls(state_dir=state_dir, seed_defaults=seed_defaults)

    def storage_status(self) -> dict[str, Any]:
        counts = {
            "action_inbox": self._count("action_inbox"),
            "action_envelopes": self._count("action_envelopes"),
            "action_envelope_promotions": self._count("action_envelope_promotions"),
            "action_envelope_receipts": self._count("action_envelope_receipts"),
            "action_decision_events": self._count("action_decision_events"),
            "action_receipts": self._count("action_receipts"),
            "chat_turn_receipts": self._count("chat_turn_receipts"),
            "chat_handoff_receipts": self._count("chat_handoff_receipts"),
            "briefing_items": self._count("briefing_items"),
            "plan_summaries": self._count("plan_summaries"),
            "memory_review_queue": self._count("memory_review_queue"),
            "memory_review_decisions": self._count("memory_review_decisions"),
            "idempotency_keys": self._count("idempotency_keys"),
            "route_state_snapshots": self._count("route_state_snapshots"),
            "evidence_refs": self._count("evidence_refs"),
        }
        log_refs = {
            kind.value: f"founder-loop-log:{kind.value}"
            for kind in JsonlLogKind
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

    def today_summary(self, *, limit: int = 6) -> dict[str, Any]:
        actions = self.list_action_inbox(limit=limit)
        plans = self.list_plan_summaries(limit=3)
        memory_items = self.list_memory_review_queue(limit=3)
        briefing_items = self.list_briefing_items(limit=3)
        chat_turn_receipts = self.list_chat_turn_receipts(limit=5)
        chat_handoff_receipts = self.list_chat_handoff_receipts(limit=5)
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
            private_beta_readiness_gate_contract=(
                private_beta_readiness_gate_contract
            ),
            user_intent_understanding_contract=user_intent_understanding_contract,
            chat_turn_receipts=chat_turn_receipts,
            chat_handoff_receipts=chat_handoff_receipts,
            memory_review_decisions=memory_review_decisions,
        )
        next_safe_actions = _next_safe_actions(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
        )
        chat_local_operator_contract = _chat_local_operator_contract_payload()
        governed_code_workbench_contract = _governed_code_workbench_contract_payload()
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
            "memory_source_required_kinds": (
                MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS
            ),
            "memory_source_policy": memory_source_provenance_policy_rows(),
            "memory_source_denied_content_refs": (
                MEMORY_SOURCE_PROVENANCE_DENIED_CONTENT_REFS
            ),
            "memory_source_review_posture": (
                memory_source_provenance_review_posture()
            ),
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
            **cross_surface_memory_intake_contract,
            **memory_to_loop_binding_contract,
            **private_beta_readiness_gate_contract,
            **user_intent_understanding_contract,
            **chat_local_operator_contract,
            **governed_code_workbench_contract,
            "chat_durable_receipt_contract_ref": CHAT_DURABLE_RECEIPT_CONTRACT_REF,
            "chat_durable_receipt_route_refs": list(CHAT_DURABLE_RECEIPT_ROUTE_REFS),
            "chat_durable_receipt_status": (
                "implemented_durable_receipts_and_reviewable_handoffs_execution_blocked"
                if chat_turn_receipts or chat_handoff_receipts
                else "implemented_receipt_routes_ready_no_turn_recorded"
            ),
            "chat_turn_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in chat_turn_receipts
            ],
            "chat_handoff_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in chat_handoff_receipts
            ],
            "chat_handoff_created_refs": [
                str(receipt["created_ref"]) for receipt in chat_handoff_receipts
            ],
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
                "today_action_envelope_route_refs": list(FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS),
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
        timeline = list(today["evidence_timeline"])
        events = self._productized_evidence_events(timeline)
        groups = self._productized_evidence_groups(events)
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
                                for blocked_state in receipt.get("blocked_state_refs", [])
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
            rollback_execution_enabled=bool(item.get("rollback_execution_enabled", False)),
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
    ) -> list[dict[str, Any]]:
        timeline: list[FounderLoopEvidenceTimelineItem] = []
        for action in actions:
            action_ref = str(action["item_ref"])
            receipt_refs = list(action.get("receipt_refs") or [])
            audit_refs = list(action.get("audit_refs") or [])
            idempotency_refs = [
                str(action["idempotency_key_ref"])
            ] if action.get("idempotency_key_ref") else []
            rollback_refs = [action["rollback_ref"]] if action.get("rollback_ref") else []
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
                str(action.get("approval_envelope_status", "missing_until_scoped_contract")),
            )
            changed_history_ref = action.get("state_change_contract_ref") or _status_ref(
                "change-status",
                str(action.get("state_change_readiness", "blocked_missing_backend_contract")),
            )
            action_stale_ref = _status_ref(
                "stale-ref",
                str(action.get("stale_state", "recheck_action_refs_before_use")),
            )
            blocked_history_refs = (
                [_status_ref("blocked-state", value) for value in blocked_states]
                or ["blocked-state:no-action-blockers-recorded"]
            )
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
                            refs=[*receipt_refs, *audit_refs]
                            or ["receipt-status:missing-until-scoped-contract"],
                            status="receipt_refs_available" if receipt_refs else "blocked",
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
                            refs=rollback_refs or ["undo-blocker:rollback-refs-missing"],
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
                    source_refs=[action_ref],
                    status_refs=[
                        "status-ref:founder-loop-action-inbox",
                        PLANS_ACTION_ENVELOPE_CONTRACT_REF,
                        str(action.get("action_envelope_ref")),
                    ],
                    related_route_refs=["GET /control-center/actions/inbox", "/actions"],
                    side_effect_class=str(action.get("side_effect_class", "validation_only")),
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
                    stale_state=str(action.get("stale_state", "recheck_action_refs_before_use")),
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
            idempotency_refs = [
                str(plan["idempotency_key_ref"])
            ] if plan.get("idempotency_key_ref") else []
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
                            refs=rollback_refs or ["undo-blocker:rollback-execution-not-scoped"],
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
                rollback_blockers=["rollback_execution_not_applicable_no_chat_mutation"],
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
                    code_contract[
                        "governed_code_workbench_expected_apply_receipt_ref"
                    ],
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
            ref
            for item in memory_loop_items
            for ref in item.get("source_refs", [])
        ]
        memory_loop_evidence_refs = [
            ref
            for item in memory_loop_items
            for ref in item.get("evidence_refs", [])
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
            private_beta_readiness_gate_contract[
                "private_beta_readiness_criteria"
            ]
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
            memory_blocked_refs = (
                [
                    _status_ref("blocked-state", str(value))
                    for value in item.get("blocked_states", [])
                ]
                or ["blocked-state:no-memory-blockers-recorded"]
            )
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
                            or ["approval-status:memory-review-refs-do-not-authorize-writes"],
                            status=(
                                "decision_receipt_recorded"
                                if decision_receipt_refs
                                else "blocked"
                            ),
                        ),
                        happened=_history_answer(
                            "happened",
                            "Memory Review accept, correct, or reject decisions are stored as durable safe receipt refs when recorded.",
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
                            "The memory review queue projection changes only to accepted, corrected, or rejected review state; raw memory content is not stored.",
                            refs=[
                                str(latest_decision.get("reviewed_recall_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision and latest_decision.get("reviewed_recall_ref")
                            ]
                            or [
                                str(latest_decision.get("correction_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision and latest_decision.get("correction_ref")
                            ]
                            or [
                                str(latest_decision.get("rejection_ref"))
                                for latest_decision in [latest_decision]
                                if latest_decision and latest_decision.get("rejection_ref")
                            ]
                            or missing_contract_refs
                            or ["change-status:no-memory-decision-captured"],
                            status=decision_status,
                        ),
                        undoable=_history_answer(
                            "undoable",
                            "Memory write/delete rollback is not scoped because no memory mutation is performed.",
                            refs=["undo-blocker:memory-write-or-delete-rollback-not-scoped"],
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
                            "Memory writes, deletes, context injection, and model/provider authority remain blocked.",
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
                        "/memory",
                    ],
                    side_effect_class=str(item.get("side_effect_class", "local_dev_workspace_only")),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="memory_review_refs_do_not_authorize_writes",
                    receipt_refs=decision_receipt_refs,
                    audit_refs=decision_audit_refs,
                    idempotency_refs=decision_idempotency_refs,
                    replay_refs=["replay-ref:founder-loop:memory-review"],
                    rollback_refs=[],
                    rollback_blockers=["memory_write_or_delete_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(item.get("stale_state", "recheck_memory_refs_before_use")),
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
            briefing_blocked_refs = (
                [
                    _status_ref("blocked-state", str(value))
                    for value in item.get("blocked_states", [])
                ]
                or ["blocked-state:no-briefing-blockers-recorded"]
            )
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
                            refs=["approval-status:source-refs-do-not-authorize-connector-runtime"],
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
                    status_refs=[
                        source_readiness_ref
                    ],
                    related_route_refs=[
                        "GET /control-center/morning-briefing/summary",
                        "/briefing",
                    ],
                    side_effect_class=str(item.get("side_effect_class", "local_dev_workspace_only")),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="source_refs_do_not_authorize_connector_runtime",
                    receipt_refs=[],
                    audit_refs=[],
                    replay_refs=["replay-ref:founder-loop:morning-briefing"],
                    rollback_refs=[],
                    rollback_blockers=["source_refresh_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(item.get("stale_state", "recheck_source_refs_before_use")),
                    missing_evidence_posture=str(item.get("evidence_gap")),
                    blocked_states=list(item.get("blocked_states") or []),
                    next_safe_action=str(item.get("next_safe_action")),
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
                        refs=["approval-status:foundation-gate-refs-not-production-authority"],
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
                        refs=["stale-ref:recheck-foundation-gate-report-before-release-claim"],
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
        memory_to_loop_binding_contract = _memory_to_loop_binding_contract_payload(
            memory_items=self.list_memory_review_queue(limit=3),
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
                "GET /control-center/storage/status",
                "GET /control-center/routes",
                "GET /control-center/runtime-readiness/summary",
                "GET /control-center/foundation-gate/summary",
            ],
            "today_action_envelope_route_refs": list(FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS),
            "decision_route_refs": list(FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS),
            "local_prerequisite_refs": [
                "status-ref:founder-loop-storage",
                "status-ref:control-center-route-manifest",
                "capability-ref:local-approval-authority",
            ],
            "items": items,
            "approval_required_before_mutation": True,
            "mutating_controls_enabled": True,
            "action_execution_enabled": False,
            "decision_state_contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
            "decision_statuses": [
                "proposed",
                "approved",
                "edited",
                "rejected",
                "deferred",
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
            **memory_to_loop_binding_contract,
            **private_beta_readiness_gate_contract,
            **user_intent_understanding_contract,
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
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_briefing_skeleton",
            "surface": "Morning Briefing",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "route_ref": "/control-center/morning-briefing/summary",
            "read_only_route_refs": [
                "GET /control-center/morning-briefing/summary",
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

    def list_action_inbox(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   risk_class, side_effect_class, authority_boundary,
                   approval_required, approval_envelope_ref,
                   approval_envelope_status, state_change_contract_ref,
                   state_change_readiness, blocked_state, evidence_refs_json,
                   receipt_refs_json, audit_refs_json, idempotency_key_ref,
                   expires_at, stale_state, rollback_ref, safe_disable_ref,
                   next_safe_action, created_at, updated_at
            FROM action_inbox
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        actions = [_row_to_payload(row) for row in rows]
        return [
            {**action, **_action_envelope_contract_payload(action)}
            for action in actions
        ]

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
        evidence_ref = f"evidence-ref:chat-handoff:{_safe_suffix(target)}:{_safe_suffix(turn_ref)}"
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
                receipt_refs=[str(turn_receipt.get("receipt_ref")), receipt.receipt_ref],
                audit_refs=[receipt.audit_ref],
                idempotency_key_ref=idempotency_key_ref,
                expires_at="review_required_before_action_decision",
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
                evidence_refs=list(dict.fromkeys([*evidence_refs, receipt.receipt_ref])),
            )
        )

    def promote_today_item_to_action_envelope(
        self,
        *,
        request: FounderLoopActionEnvelopePromotionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        source = self._today_item_payload_for_ref(request.today_item_ref)
        if source is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_TODAY_ITEM_NOT_FOUND")

        item_ref = today_item_to_action_item_ref(request.today_item_ref)
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
        action_envelope_ref = f"action-envelope:founder-loop-v1:{_safe_suffix(item_ref)}"
        receipt_ref = action_envelope_promotion_receipt_ref(
            item_ref,
            idempotency_key_ref,
        )
        audit_ref = action_envelope_promotion_audit_ref(item_ref, idempotency_key_ref)
        evidence_event_ref = action_envelope_promotion_event_ref(item_ref)
        evidence_refs = list(
            dict.fromkeys(
                [
                    "evidence-ref:founder-loop:today-action-envelope",
                    evidence_event_ref,
                    request.today_item_ref,
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
            safe_summary=(
                "Today item ref was promoted into a reviewable Action envelope; "
                "no action execution, connector write, memory write, shell/subprocess "
                "work, provider/model call, or production authority occurred."
            ),
            evidence_refs=evidence_refs,
            blocked_state_refs=list(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS),
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
            expires_at="review_required_before_decision_or_execution",
            stale_state="recheck_today_item_before_action_decision",
            rollback_ref=f"rollback-plan:founder-loop-v1:{_safe_suffix(item_ref)}",
            safe_disable_ref=f"safe-disable:founder-loop-v1:{_safe_suffix(item_ref)}",
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
            "rollback_ref": action_record.rollback_ref,
            "safe_disable_ref": action_record.safe_disable_ref,
            "blocked_state_refs": list(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS),
            "action_execution_enabled": False,
            "connector_write_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "model_provider_authority_allowed": False,
            "production_authority_enabled": False,
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

    def latest_action_receipt(self, action_id: str) -> dict[str, Any] | None:
        item_ref = action_id_to_item_ref(action_id)
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

    def record_action_decision(
        self,
        *,
        action_id: str,
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        if decision not in FOUNDER_LOOP_ACTION_DECISION_KINDS:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_DECISION_UNSUPPORTED")
        _validate_safe_ref(idempotency_key_ref, "idempotency_key_ref")
        item_ref = action_id_to_item_ref(action_id)
        action = self._action_payload_for_item_ref(item_ref)
        if action is None:
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_NOT_FOUND")
        action = {**action, **_action_envelope_contract_payload(action)}
        fingerprint_payload = decision_payload_for_fingerprint(
            item_ref=item_ref,
            decision=decision,
            request=request,
        )
        payload_fingerprint_ref = action_payload_fingerprint_ref(fingerprint_payload)
        replay = self._action_decision_replay(idempotency_key_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise FounderLoopStorageDuplicateError(
                    "FOUNDER_LOOP_ACTION_IDEMPOTENCY_CONFLICT"
                )
            receipt = self._action_receipt_by_ref(str(replay["receipt_ref"]))
            return {
                **receipt,
                "replayed": True,
                "safe_summary": "Prior Action decision receipt returned for matching idempotency key.",
            }

        receipt = self._build_action_decision_receipt(
            action=action,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        receipt_payload = receipt.model_dump(mode="json")
        with self._connect() as conn:
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
                    request.approval_ref,
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
                edited_envelope_ref=request.edited_envelope_ref,
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

    def _action_payload_for_item_ref(self, item_ref: str) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   risk_class, side_effect_class, authority_boundary,
                   approval_required, approval_envelope_ref,
                   approval_envelope_status, state_change_contract_ref,
                   state_change_readiness, blocked_state, evidence_refs_json,
                   receipt_refs_json, audit_refs_json, idempotency_key_ref,
                   expires_at, stale_state, rollback_ref, safe_disable_ref,
                   next_safe_action, created_at, updated_at
            FROM action_inbox
            WHERE item_ref = ?
            LIMIT 1
            """,
            (item_ref,),
        )
        if not rows:
            return None
        return _row_to_payload(rows[0])

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

    def _chat_turn_receipt_replay(self, idempotency_key_ref: str) -> dict[str, Any] | None:
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

    def _action_decision_replay(self, idempotency_key_ref: str) -> dict[str, Any] | None:
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

    def _action_envelope_promotion_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
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
            raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_ENVELOPE_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

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

    def _action_decision_receipts_for_item_ref(self, item_ref: str) -> list[dict[str, Any]]:
        _validate_safe_ref(item_ref, "item_ref")
        rows = self._fetch_all(
            """
            SELECT receipt_json
            FROM action_receipts
            WHERE item_ref = ?
            ORDER BY created_at ASC
            LIMIT 50
            """,
            (item_ref,),
        )
        return [dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def _build_action_decision_receipt(
        self,
        *,
        action: dict[str, Any],
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
    ) -> FounderLoopActionDecisionReceipt:
        item_ref = str(action["item_ref"])
        status, approval_status, approval_reason_refs = self._decision_status(
            action=action,
            decision=decision,
            request=request,
        )
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
                    *list(action.get("evidence_refs") or []),
                ]
            )
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
            approval_ref=request.approval_ref,
            approval_status=approval_status,
            approval_reason_refs=approval_reason_refs,
            safe_summary=_action_decision_safe_summary(decision, status),
            evidence_refs=evidence_refs,
            blocked_state_refs=list(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS),
        )

    def _decision_status(
        self,
        *,
        action: dict[str, Any],
        decision: str,
        request: FounderLoopActionDecisionRequest,
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
                ],
            )
            authority = LocalApprovalAuthority()
            authority.create_request(approval_request)
            for grant in request.approval_grants:
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
        raise FounderLoopStorageError("FOUNDER_LOOP_ACTION_DECISION_UNSUPPORTED")

    def _update_action_projection_after_decision(
        self,
        *,
        conn: sqlite3.Connection,
        action: dict[str, Any],
        receipt: FounderLoopActionDecisionReceipt,
        edited_envelope_ref: str | None,
    ) -> None:
        receipt_refs = list(
            dict.fromkeys([*list(action.get("receipt_refs") or []), receipt.receipt_ref])
        )
        audit_refs = list(
            dict.fromkeys([*list(action.get("audit_refs") or []), receipt.audit_ref])
        )
        approval_envelope_ref = (
            edited_envelope_ref
            if receipt.status == "edited" and edited_envelope_ref is not None
            else action.get("approval_envelope_ref")
        )
        projection_status = {
            "approved": "approved",
            "edited": "edited",
            "rejected": "rejected",
            "deferred": "deferred",
            "blocked": "blocked",
        }.get(receipt.status, "receipt_recorded")
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
                next_safe_action = ?,
                updated_at = ?
            WHERE item_ref = ?
            """,
            (
                projection_status,
                approval_envelope_ref,
                f"{receipt.status}_receipt_recorded",
                FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
                "decision_receipt_recorded_no_action_execution",
                _json_dumps(receipt_refs),
                _json_dumps(audit_refs),
                receipt.idempotency_key_ref,
                "Inspect the decision receipt; action execution remains blocked.",
                _utc_iso(),
                receipt.item_ref,
            ),
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
            {**plan, **_plan_action_envelope_contract_payload(plan)}
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
        return {
            "route_ref": "/control-center/memory/review",
            "surface_ref": "/memory",
            "contract_ref": FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
            "legacy_decision_contract_ref": MEMORY_REVIEW_DECISION_CONTRACT_REF,
            "decision_route_refs": list(MEMORY_REVIEW_DECISION_ROUTE_REFS),
            "decision_kinds": list(MEMORY_REVIEW_DECISION_KINDS),
            "items": items,
            "decision_receipts": decisions,
            "decision_receipt_refs": [
                str(receipt["receipt_ref"]) for receipt in decisions
            ],
            "decision_count": len(decisions),
            "idempotency_replay_enabled": True,
            "idempotency_conflict_rejected": True,
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

    def record_memory_review_decision(
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
        if decision != "correct" and request.corrected_summary_ref is not None:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_CORRECTION_REF_NOT_ALLOWED")

        enriched_request = MemoryReviewDecisionRequest(
            reviewer_ref=request.reviewer_ref,
            corrected_summary_ref=request.corrected_summary_ref,
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
                        *list(candidate.get("evidence_refs") or []),
                        *request.evidence_refs,
                    ]
                )
            ),
            metadata_refs=request.metadata_refs,
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
            request=request,
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
            receipt = self._memory_review_decision_receipt_by_ref(
                str(replay["receipt_ref"])
            )
            return {
                **receipt,
                "replayed": True,
                "safe_summary_ref": "safe-summary-ref:memory-review-decision-replay",
            }

        review_ref = str(candidate["review_ref"])
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
            memory_review_reviewed_recall_ref(candidate_ref)
            if decision in {"accept", "correct"}
            else None
        )
        correction_ref = (
            memory_review_correction_ref(candidate_ref)
            if decision == "correct"
            else None
        )
        rejection_ref = (
            memory_review_rejection_ref(candidate_ref)
            if decision == "reject"
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
            correction_ref=correction_ref,
            rejection_ref=rejection_ref,
            safe_summary_ref=f"safe-summary-ref:memory-review:{decision}",
            blocked_state_refs=enriched_request.blocked_state_refs,
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
            self._update_memory_review_projection_after_decision(
                conn=conn,
                candidate=candidate,
                receipt=receipt,
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

    def list_memory_review_recall_records(self) -> list[dict[str, Any]]:
        store = self._memory_review_recall_store()
        try:
            return [record.model_dump(mode="json") for record in store.list_records()]
        finally:
            store.close()

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
        safe_summary = str(candidate.get("safe_summary") or "").strip()
        if decision == "correct":
            safe_summary = (
                "Reviewed memory correction recorded from corrected-summary ref "
                f"{request.corrected_summary_ref}."
            )
        memory_request = MemoryProviderWriteRequest(
            request_id=f"memory-review-recall-write:{receipt_ref}",
            provider_ref="provider-ref:local-memory-store:memory-review",
            memory_kind=(
                MemoryRecordKind.correction
                if decision == "correct"
                else MemoryRecordKind.structured_fact
            ),
            memory_layer=MemoryLayer.record,
            provider_kind=MemoryProviderKind.local_sqlite,
            safe_summary=safe_summary,
            source_refs=request.source_refs,
            evidence_refs=list(dict.fromkeys([*request.evidence_refs, evidence_ref])),
            event_refs=[evidence_ref],
            receipt_refs=[receipt_ref],
            user_reviewed=True,
            automatic_write=False,
            data_classification=MemoryDataClassification.internal,
            confidence_score=0.7,
            trust_score=0.7,
            dedup_key=reviewed_recall_ref,
            context_pack_eligible=False,
            injection_priority=0,
            tags=[
                "memory-review-decision",
                f"memory-review-decision:{decision}",
            ],
            metadata_refs=list(
                dict.fromkeys(
                    ref
                    for ref in [
                        reviewed_recall_ref,
                        str(candidate.get("review_ref") or ""),
                        str(candidate.get("business_memory_candidate_ref") or ""),
                    ]
                    if ref
                )
            ),
            metadata={
                "authority_boundary_ref": (
                    "memory-review-recall-record-is-not-truth-or-context-injection"
                ),
                "decision": decision,
                "reviewed_recall_ref": reviewed_recall_ref,
                "context_injection_authorized": False,
                "source_truth_authority": False,
                "connector_write_authorized": False,
                "automatic_action_execution_authorized": False,
            },
        )
        store = self._memory_review_recall_store()
        try:
            decision_result = store.put_record(memory_request)
        finally:
            store.close()
        if not getattr(decision_result, "allowed", False) or not decision_result.memory_id:
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_RECALL_RECORD_DENIED")
        return f"memory-record-ref:{decision_result.memory_id}"

    def _memory_review_recall_store(self) -> LocalMemoryStore:
        return LocalMemoryStore(storage_path=self.memory_review_recall_db_path)

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

    def _memory_review_decision_receipt_by_ref(self, receipt_ref: str) -> dict[str, Any]:
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
            raise FounderLoopStorageError("FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_NOT_FOUND")
        return dict(json.loads(str(rows[0]["receipt_json"])))

    def _update_memory_review_projection_after_decision(
        self,
        *,
        conn: sqlite3.Connection,
        candidate: dict[str, Any],
        receipt: MemoryReviewDecisionReceipt,
    ) -> None:
        review_state = {
            "accept": "accepted",
            "correct": "corrected",
            "reject": "rejected",
        }[receipt.decision]
        confidence_posture = {
            "accept": "reviewed_recall_safe_ref_only",
            "correct": "corrected_summary_ref_reviewed",
            "reject": "rejected_candidate_preserved",
        }[receipt.decision]
        next_safe_action = {
            "accept": (
                "Use reviewed recall refs only after scoped retrieval/context policy; "
                "context injection remains blocked."
            ),
            "correct": (
                "Review the corrected safe summary ref; memory writes and context "
                "injection remain blocked."
            ),
            "reject": (
                "Keep the rejected candidate preserved as blocked review state so "
                "stale refs do not silently return."
            ),
        }[receipt.decision]
        evidence_refs = list(
            dict.fromkeys(
                [
                    *list(candidate.get("evidence_refs") or []),
                    *receipt.evidence_refs,
                    receipt.receipt_ref,
                ]
            )
        )
        blocked_states = list(
            dict.fromkeys(
                [
                    *list(candidate.get("blocked_states") or []),
                    *[
                        ref.removeprefix("blocked-state:")
                        for ref in receipt.blocked_state_refs
                    ],
                ]
            )
        )
        conn.execute(
            """
            UPDATE memory_review_queue
            SET status = ?,
                review_state = ?,
                correction_posture = ?,
                rejection_posture = ?,
                confidence_posture = ?,
                stale_state = ?,
                blocked_states_json = ?,
                next_safe_action = ?,
                evidence_refs_json = ?
            WHERE review_ref = ?
            """,
            (
                review_state,
                review_state,
                (
                    "corrected_summary_ref_recorded_no_raw_content"
                    if receipt.decision == "correct"
                    else str(candidate.get("correction_posture"))
                ),
                (
                    "rejected_candidate_preserved_with_receipt"
                    if receipt.decision == "reject"
                    else str(candidate.get("rejection_posture"))
                ),
                confidence_posture,
                "recheck_memory_decision_receipt_before_recall",
                _json_dumps(blocked_states),
                next_safe_action,
                _json_dumps(evidence_refs),
                receipt.review_ref,
            ),
        )

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
        self._execute(
            """
            INSERT INTO action_inbox (
                item_ref, title, safe_summary, surface, priority, status,
                risk_class, side_effect_class, authority_boundary,
                approval_required, approval_envelope_ref,
                approval_envelope_status, state_change_contract_ref,
                state_change_readiness, blocked_state, evidence_refs_json,
                receipt_refs_json, audit_refs_json, idempotency_key_ref,
                expires_at, stale_state, rollback_ref, safe_disable_ref,
                next_safe_action, created_at, updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(item_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                surface = excluded.surface,
                priority = excluded.priority,
                status = excluded.status,
                risk_class = excluded.risk_class,
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
                record.next_safe_action,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
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
        self._execute(
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

    def record_idempotency_key(self, *, key_ref: str, scope_ref: str, receipt_ref: str) -> None:
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
            raise FounderLoopStorageDuplicateError("FOUNDER_LOOP_IDEMPOTENCY_DUPLICATE") from exc

    def append_log(self, kind: JsonlLogKind, payload: dict[str, Any]) -> dict[str, str]:
        _validate_safe_payload(payload, f"{kind.value}_log")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        path = self.logs_dir / f"{kind.value}.jsonl"
        record = {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "kind": kind.value,
            "event_ref": payload.get("event_ref", f"founder-loop-log:{kind.value}"),
            "safe_summary": payload.get("safe_summary", "Founder Loop redacted event recorded."),
            "evidence_refs": payload.get("evidence_refs", []),
            "created_at": _utc_iso(),
        }
        _validate_safe_payload(record, f"{kind.value}_log_record")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_json_dumps(record) + "\n")
        return {
            "log_ref": f"founder-loop-log:{kind.value}",
            "event_ref": str(record["event_ref"]),
        }

    def backup_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "required_artifact_refs": [
                "founder-loop-sqlite:local-state",
                "founder-loop-log:audit",
                "founder-loop-log:transcript",
                "founder-loop-log:realtime",
                "founder-loop-log:receipt",
            ],
            "raw_paths_included": False,
            "raw_logs_included": False,
            "safe_refs_only": True,
        }

    def _ensure_storage(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS storage_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_inbox (
                    item_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    surface TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_class TEXT NOT NULL DEFAULT 'medium',
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
                    next_safe_action TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked until a scoped backend contract exists.',
                    created_at TEXT NOT NULL,
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
            conn.execute(
                """
                INSERT INTO storage_metadata (key, value, updated_at)
                VALUES ('schema_version', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (FOUNDER_LOOP_SCHEMA_VERSION, _utc_iso()),
            )
            self._ensure_action_inbox_contract_columns(conn)
            self._ensure_memory_review_contract_columns(conn)
            self._ensure_briefing_contract_columns(conn)
        if self.seed_defaults:
            self._seed_defaults_if_empty()
            self._backfill_seed_action_contract_metadata()
            self._backfill_seed_memory_review_contract_metadata()
            self._backfill_seed_briefing_contract_metadata()

    def _ensure_action_inbox_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(action_inbox)").fetchall()
        }
        additions = {
            "risk_class": "TEXT NOT NULL DEFAULT 'medium'",
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
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked "
                "until a scoped backend contract exists.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(f"ALTER TABLE action_inbox ADD COLUMN {column_name} {column_spec}")

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
                conn.execute(f"ALTER TABLE briefing_items ADD COLUMN {column_name} {column_spec}")

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
                    receipt_refs=["receipt-plan:founder-loop:setup-assistant-hardening"],
                    audit_refs=["audit-plan:founder-loop:setup-assistant-hardening"],
                    idempotency_key_ref="idempotency-ref:founder-loop:setup-assistant-hardening",
                    expires_at="review_required_before_mutation",
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
                    expires_at="review_required_before_source_contract",
                    stale_state="recheck_source_status_before_contract",
                    safe_disable_ref="safe-disable:founder-loop:briefing-surface",
                    next_safe_action="Define read-only briefing source refs before source reads.",
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
                "expires_at": "review_required_before_mutation",
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
                "expires_at": "review_required_before_source_contract",
                "stale_state": "recheck_source_status_before_contract",
                "safe_disable_ref": "safe-disable:founder-loop:briefing-surface",
                "next_safe_action": "Define read-only briefing source refs before source reads.",
            },
        )

    def _update_action_contract_metadata(self, item_ref: str, metadata: dict[str, Any]) -> None:
        _validate_safe_ref(item_ref, "item_ref")
        _validate_safe_payload(metadata, "action_contract_metadata")
        self._execute(
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
                _json_dumps(metadata["receipt_refs"]) if "receipt_refs" in metadata else None,
                _json_dumps(metadata["audit_refs"]) if "audit_refs" in metadata else None,
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
                _json_dumps(metadata["source_refs"]) if "source_refs" in metadata else None,
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
                _json_dumps(metadata["blocked_states"]) if "blocked_states" in metadata else None,
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
                _json_dumps(metadata["source_refs"]) if "source_refs" in metadata else None,
                (
                    _json_dumps(metadata["missing_contract_refs"])
                    if "missing_contract_refs" in metadata
                    else None
                ),
                _json_dumps(metadata["blocked_states"]) if "blocked_states" in metadata else None,
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
            "briefing_items",
            "chat_handoff_receipts",
            "chat_turn_receipts",
            "plan_summaries",
            "memory_review_decision_replays",
            "memory_review_decisions",
            "memory_review_queue",
            "idempotency_keys",
            "route_state_snapshots",
            "evidence_refs",
        }
        if table not in allowed:
            raise FounderLoopStorageError("FOUNDER_LOOP_TABLE_REF_DENIED")
        rows = self._fetch_all(f"SELECT COUNT(*) AS count FROM {table}", ())
        return int(rows[0]["count"])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _bounded_limit(limit: int) -> int:
        return max(1, min(int(limit), 100))
