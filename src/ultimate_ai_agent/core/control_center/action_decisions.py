from __future__ import annotations

import hashlib
import json
import re
from datetime import timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.time import utc_now


FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF = (
    "contract-ref:founder-loop-action-state-machine:v1"
)
FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF = (
    "contract-ref:founder-loop-v1-vertical-slice:v1"
)
FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS = (
    "POST /control-center/actions/{action_id}/approve",
    "POST /control-center/actions/{action_id}/edit",
    "POST /control-center/actions/{action_id}/reject",
    "POST /control-center/actions/{action_id}/defer",
    "GET /control-center/actions/{action_id}/receipt",
)
FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS = (
    "POST /control-center/today/action-envelope",
)
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_ACTION_REF = (
    "authority-action-ref:today-action-envelope-promotion"
)
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_LANE_REF = (
    "lane-ref:today-action-envelope-promotion"
)
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:draft"
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF = (
    "authority-mode-ref:read-only"
)
FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_BLOCKED_REF = (
    "blocked-state:today-action-envelope:workspace-draft-authority-required"
)
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_ACTION_REF = (
    "authority-action-ref:action-inbox-decision-receipt"
)
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_LANE_REF = (
    "lane-ref:action-inbox-decision-receipts"
)
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_MODE_REF = (
    "authority-mode-ref:ask-before-changes"
)
FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF = (
    "blocked-state:action-inbox-decision:workspace-write-authority-required"
)
FOUNDER_LOOP_ACTION_DECISION_KINDS = ("approve", "edit", "reject", "defer")
FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_STATUS = "action_envelope_created"
FRONTIER_AI_COST_USAGE_CONTRACT_REF = (
    "contract-ref:frontier-ai-cost-usage-telemetry:v1"
)
FOUNDER_LOOP_ACTION_STATUSES = (
    "proposed",
    "approved",
    "edited",
    "rejected",
    "deferred",
    "expired",
    "receipt_recorded",
    "blocked",
)
FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS = (
    "blocked-state:no-action-execution",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:approval-ref-must-validate-exact-scope",
    "blocked-state:no-production-authority",
)
FOUNDER_LOOP_ACTION_COST_BLOCKED_REFS = (
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-runtime-model-call",
    "blocked-state:frontier-provider-model-ref-missing",
    "blocked-state:unknown-paid-cost-requires-approval",
)
ACTION_DECISION_REQUESTED_ACTION = "approve_founder_loop_action_decision"
SAFE_ACTION_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")


def _default_actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_operator",
        authority_source=AuthoritySource.explicit_user_request,
    )


class FounderLoopActionDecisionRequest(BaseModel):
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    approval_ref: str | None = Field(default=None, max_length=160)
    approval_grants: list[ApprovalGrant] = Field(default_factory=list)
    decision_reason_ref: str = Field(
        default="decision-reason-ref:founder-loop:operator-review",
        min_length=1,
        max_length=160,
    )
    edited_envelope_ref: str | None = Field(default=None, max_length=160)
    defer_until_ref: str | None = Field(default=None, max_length=160)
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_safe_refs(self) -> "FounderLoopActionDecisionRequest":
        for field_name in [
            "approval_ref",
            "decision_reason_ref",
            "edited_envelope_ref",
            "defer_until_ref",
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for ref_value in self.metadata_refs:
            _validate_safe_ref(ref_value, "metadata_refs")
        _validate_safe_payload(self.model_dump(mode="json"), "action_decision_request")
        return self


class FounderLoopActionEnvelopePromotionRequest(BaseModel):
    today_item_ref: str = Field(..., min_length=1, max_length=200)
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    decision_reason_ref: str = Field(
        default="decision-reason-ref:founder-loop:today-action-envelope",
        min_length=1,
        max_length=160,
    )
    risk_class: Literal["low", "medium", "high", "critical"] = "medium"
    priority: Literal["low", "medium", "high"] = "medium"
    metadata_refs: list[str] = Field(default_factory=list)
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
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_safe_refs(self) -> "FounderLoopActionEnvelopePromotionRequest":
        _validate_safe_ref(self.today_item_ref, "today_item_ref")
        _validate_safe_ref(self.decision_reason_ref, "decision_reason_ref")
        _validate_safe_ref(self.provider_ref, "provider_ref")
        _validate_safe_ref(self.model_profile_ref, "model_profile_ref")
        for ref_value in self.metadata_refs:
            _validate_safe_ref(ref_value, "metadata_refs")
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("cost metered unit total must match inputs")
        if not self.unknown_paid_cost_requires_explicit_approval:
            raise ValueError("unknown paid cost must require explicit approval")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "action_envelope_promotion_request",
        )
        return self


class FounderLoopActionEnvelope(BaseModel):
    contract_ref: str = FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF
    item_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    status: Literal[
        "proposed",
        "approved",
        "edited",
        "rejected",
        "deferred",
        "expired",
        "receipt_recorded",
        "blocked",
    ] = "proposed"
    exact_scope_ref: str = Field(..., min_length=1)
    risk_class: str = Field(..., min_length=1, max_length=40)
    side_effect_class: str = Field(..., min_length=1, max_length=80)
    approval_requirement_ref: str = Field(..., min_length=1)
    expected_receipt_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=list)
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    model_provider_authority_allowed: bool = False
    production_authority_enabled: bool = False
    cost_contract_ref: str = FRONTIER_AI_COST_USAGE_CONTRACT_REF
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
    cost_estimate_ref: str = Field(..., min_length=1)
    captured_usage_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    cost_state_label: str = Field(default="Cost blocked", min_length=1)
    provider_authority_state_label: str = Field(
        default="No provider authority",
        min_length=1,
    )
    authority_decision_ref: str | None = Field(default=None, max_length=180)
    authority_decision_outcome: str | None = Field(default=None, max_length=80)
    authority_lease_ref: str | None = Field(default=None, max_length=180)
    authority_domain_ref: str = FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = (
        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
    )
    authority_required_mode_ref: str = (
        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF
    )
    authority_audit_ref: str | None = Field(default=None, max_length=180)
    authority_policy_receipt_ref: str | None = Field(default=None, max_length=180)
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "FounderLoopActionEnvelope":
        for field_name in [
            "contract_ref",
            "item_ref",
            "action_envelope_ref",
            "exact_scope_ref",
            "approval_requirement_ref",
            "expected_receipt_ref",
            "rollback_ref",
            "safe_disable_ref",
            "cost_contract_ref",
            "provider_ref",
            "model_profile_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
            "authority_decision_ref",
            "authority_lease_ref",
            "authority_domain_ref",
            "authority_capability_ref",
            "authority_required_mode_ref",
            "authority_audit_ref",
            "authority_policy_receipt_ref",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                _validate_safe_ref(value, field_name)
        for field_name in [
            "blocked_state_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        if self.status not in FOUNDER_LOOP_ACTION_STATUSES:
            raise ValueError("unsupported Founder Loop action status")
        if not set(FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS).issubset(
            set(self.blocked_state_refs)
        ):
            raise ValueError("action envelope must preserve blocked authority refs")
        if not set(FOUNDER_LOOP_ACTION_COST_BLOCKED_REFS).issubset(
            set(self.cost_blocked_state_refs)
        ):
            raise ValueError("action envelope must preserve cost blocked refs")
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("cost metered unit total must match inputs")
        if self.frontier_usage_claimed and not self.cost_receipt_refs:
            raise ValueError("frontier usage claims require cost receipt refs")
        if not self.unknown_paid_cost_requires_explicit_approval:
            raise ValueError("unknown paid cost must require explicit approval")
        denied_flags = {
            "action_execution_enabled": self.action_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "model_provider_authority_allowed": self.model_provider_authority_allowed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"action envelope enabled denied authority: {enabled[0]}")
        _validate_safe_payload(self.model_dump(mode="json"), "action_envelope")
        return self


class FounderLoopActionDecisionReceipt(BaseModel):
    contract_ref: str = FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF
    decision_ref: str = Field(..., min_length=1)
    item_ref: str = Field(..., min_length=1)
    decision: Literal["approve", "edit", "reject", "defer"]
    status: str = Field(..., min_length=1, max_length=80)
    receipt_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    approval_ref: str | None = Field(default=None, max_length=160)
    approval_status: str = Field(default="not_required_for_decision", min_length=1)
    approval_reason_refs: list[str] = Field(default_factory=list)
    action_executed: bool = False
    approval_grants_execution: bool = False
    connector_write_performed: bool = False
    memory_write_performed: bool = False
    raw_content_stored: bool = False
    replayed: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=320)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    cost_contract_ref: str = FRONTIER_AI_COST_USAGE_CONTRACT_REF
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
    cost_estimate_ref: str = Field(..., min_length=1)
    captured_usage_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    cost_state_label: str = Field(default="Cost blocked", min_length=1)
    provider_authority_state_label: str = Field(
        default="No provider authority",
        min_length=1,
    )
    authority_decision_ref: str | None = Field(default=None, max_length=180)
    authority_decision_outcome: str | None = Field(default=None, max_length=80)
    authority_lease_ref: str | None = Field(default=None, max_length=180)
    authority_audit_ref: str | None = Field(default=None, max_length=180)
    authority_receipt_ref: str | None = Field(default=None, max_length=180)
    authority_reason_refs: list[str] = Field(default_factory=list)
    authority_domain_ref: str = FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = (
        FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_CAPABILITY_REF
    )
    authority_required_mode_ref: str = (
        FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_MODE_REF
    )
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "FounderLoopActionDecisionReceipt":
        for field_name in [
            "contract_ref",
            "decision_ref",
            "item_ref",
            "receipt_ref",
            "audit_ref",
            "idempotency_key_ref",
            "payload_fingerprint_ref",
            "approval_ref",
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for field_name in [
            "approval_reason_refs",
            "evidence_refs",
            "blocked_state_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        for field_name in [
            "cost_contract_ref",
            "provider_ref",
            "model_profile_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
            "authority_domain_ref",
            "authority_capability_ref",
            "authority_required_mode_ref",
        ]:
            _validate_safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "authority_decision_ref",
            "authority_lease_ref",
            "authority_audit_ref",
            "authority_receipt_ref",
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for ref_value in self.authority_reason_refs:
            _validate_safe_ref(ref_value, "authority_reason_refs")
        if self.authority_decision_outcome is not None:
            _validate_safe_text(
                self.authority_decision_outcome,
                "authority_decision_outcome",
            )
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("cost metered unit total must match inputs")
        if self.frontier_usage_claimed and not self.cost_receipt_refs:
            raise ValueError("frontier usage claims require cost receipt refs")
        if not self.unknown_paid_cost_requires_explicit_approval:
            raise ValueError("unknown paid cost must require explicit approval")
        denied_flags = {
            "action_executed": self.action_executed,
            "approval_grants_execution": self.approval_grants_execution,
            "connector_write_performed": self.connector_write_performed,
            "memory_write_performed": self.memory_write_performed,
            "raw_content_stored": self.raw_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"action receipt enabled denied authority: {enabled[0]}")
        _validate_safe_payload(self.model_dump(mode="json"), "action_decision_receipt")
        return self


class FounderLoopActionEnvelopePromotionReceipt(BaseModel):
    contract_ref: str = FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF
    today_item_ref: str = Field(..., min_length=1)
    item_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    status: str = Field(
        default=FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_STATUS,
        min_length=1,
        max_length=80,
    )
    receipt_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    evidence_timeline_event_ref: str = Field(..., min_length=1)
    action_executed: bool = False
    approval_grants_execution: bool = False
    connector_write_performed: bool = False
    memory_write_performed: bool = False
    raw_content_stored: bool = False
    replayed: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=320)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    cost_contract_ref: str = FRONTIER_AI_COST_USAGE_CONTRACT_REF
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
    cost_estimate_ref: str = Field(..., min_length=1)
    captured_usage_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    cost_state_label: str = Field(default="Cost blocked", min_length=1)
    provider_authority_state_label: str = Field(
        default="No provider authority",
        min_length=1,
    )
    authority_decision_ref: str = Field(..., min_length=1)
    authority_decision_outcome: str = Field(..., min_length=1)
    authority_lease_ref: str | None = Field(default=None, max_length=180)
    authority_domain_ref: str = FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = (
        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
    )
    authority_required_mode_ref: str = (
        FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_REQUIRED_MODE_REF
    )
    authority_audit_ref: str = Field(..., min_length=1)
    authority_policy_receipt_ref: str | None = Field(default=None, max_length=180)
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "FounderLoopActionEnvelopePromotionReceipt":
        for field_name in [
            "contract_ref",
            "today_item_ref",
            "item_ref",
            "action_envelope_ref",
            "receipt_ref",
            "audit_ref",
            "idempotency_key_ref",
            "payload_fingerprint_ref",
            "evidence_timeline_event_ref",
            "cost_contract_ref",
            "provider_ref",
            "model_profile_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
            "authority_decision_ref",
            "authority_lease_ref",
            "authority_domain_ref",
            "authority_capability_ref",
            "authority_required_mode_ref",
            "authority_audit_ref",
            "authority_policy_receipt_ref",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                _validate_safe_ref(value, field_name)
        for field_name in [
            "evidence_refs",
            "blocked_state_refs",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        if not set(FOUNDER_LOOP_ACTION_COST_BLOCKED_REFS).issubset(
            set(self.cost_blocked_state_refs)
        ):
            raise ValueError("action envelope receipt must preserve cost blocked refs")
        if self.total_metered_units != (
            self.input_metered_units + self.output_metered_units
        ):
            raise ValueError("cost metered unit total must match inputs")
        if self.frontier_usage_claimed and not self.cost_receipt_refs:
            raise ValueError("frontier usage claims require cost receipt refs")
        if not self.unknown_paid_cost_requires_explicit_approval:
            raise ValueError("unknown paid cost must require explicit approval")
        _validate_safe_text(
            self.authority_decision_outcome,
            "authority_decision_outcome",
        )
        if self.authority_decision_outcome != "allow":
            raise ValueError("action envelope receipt requires allowed draft authority")
        if not self.authority_lease_ref:
            raise ValueError("action envelope receipt requires authority lease ref")
        denied_flags = {
            "action_executed": self.action_executed,
            "approval_grants_execution": self.approval_grants_execution,
            "connector_write_performed": self.connector_write_performed,
            "memory_write_performed": self.memory_write_performed,
            "raw_content_stored": self.raw_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"action envelope receipt enabled denied authority: {enabled[0]}")
        _validate_safe_payload(
            self.model_dump(mode="json"),
            "action_envelope_promotion_receipt",
        )
        return self


def action_id_to_item_ref(action_id: str) -> str:
    if action_id.startswith(("founder-action:", "action-item:")):
        _validate_safe_ref(action_id, "action_id")
        return action_id
    _validate_safe_text(action_id, "action_id")
    safe_suffix = _safe_suffix(action_id)
    _validate_safe_ref(f"founder-action:{safe_suffix}", "action_id")
    return f"founder-action:{safe_suffix}"


def action_decision_ref(item_ref: str, decision: str, idempotency_key_ref: str) -> str:
    return (
        "action-decision:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(decision)}:{_safe_suffix(idempotency_key_ref)}"
    )


def action_decision_receipt_ref(
    item_ref: str,
    decision: str,
    idempotency_key_ref: str,
) -> str:
    return (
        "receipt:founder-loop-action:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(decision)}:{_safe_suffix(idempotency_key_ref)}"
    )


def action_decision_audit_ref(
    item_ref: str,
    decision: str,
    idempotency_key_ref: str,
) -> str:
    return (
        "audit:founder-loop-action:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(decision)}:{_safe_suffix(idempotency_key_ref)}"
    )


def today_item_to_action_item_ref(today_item_ref: str) -> str:
    _validate_safe_ref(today_item_ref, "today_item_ref")
    if today_item_ref.startswith("founder-action:"):
        return today_item_ref
    return f"founder-action:today-promotion:{_safe_suffix(today_item_ref)}"


def action_envelope_promotion_receipt_ref(
    item_ref: str,
    idempotency_key_ref: str,
) -> str:
    return (
        "receipt:founder-loop-action-envelope:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
    )


def action_envelope_promotion_audit_ref(
    item_ref: str,
    idempotency_key_ref: str,
) -> str:
    return (
        "audit:founder-loop-action-envelope:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
    )


def action_envelope_promotion_event_ref(item_ref: str) -> str:
    return f"evidence-timeline:action-envelope/{_safe_suffix(item_ref)}"


def action_payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"payload-fingerprint:founder-loop-action:{digest}"


def action_approval_request(
    *,
    item_ref: str,
    actor_context: ActorContext,
    risk_class: str,
    resource_refs: list[str],
) -> ApprovalRequest:
    _validate_safe_ref(item_ref, "item_ref")
    for ref_value in resource_refs:
        _validate_safe_ref(ref_value, "resource_refs")
    risk_values = {item.value for item in ApprovalRiskLevel}
    risk_level = (
        ApprovalRiskLevel(risk_class)
        if risk_class in risk_values
        else ApprovalRiskLevel.high
    )
    return ApprovalRequest(
        approval_request_id=f"approval-request:{_safe_suffix(item_ref)}",
        run_id=f"run:founder-loop-action:{_safe_suffix(item_ref)}",
        subject_type=ApprovalSubjectType.external_action,
        subject_id=item_ref,
        actor_context=actor_context,
        requested_action=ACTION_DECISION_REQUESTED_ACTION,
        purpose="Approve Founder Loop Action decision metadata for exact safe refs.",
        risk_level=risk_level,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="founder_loop_action_decision",
            requires_redaction=True,
        ),
        resource_refs=resource_refs,
        event_ref=f"event-ref:founder-loop-action:{_safe_suffix(item_ref)}",
        trace_id=f"trace-ref:founder-loop-action:{_safe_suffix(item_ref)}",
        expires_at=utc_now() + timedelta(hours=1),
    )


def decision_payload_for_fingerprint(
    *,
    item_ref: str,
    decision: str,
    request: FounderLoopActionDecisionRequest,
) -> dict[str, Any]:
    return {
        "contract_ref": FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
        "item_ref": item_ref,
        "decision": decision,
        "actor_id": request.actor_context.actor_id,
        "approval_ref": request.approval_ref,
        "decision_reason_ref": request.decision_reason_ref,
        "edited_envelope_ref": request.edited_envelope_ref,
        "defer_until_ref": request.defer_until_ref,
        "metadata_refs": sorted(request.metadata_refs),
    }


def promotion_payload_for_fingerprint(
    *,
    request: FounderLoopActionEnvelopePromotionRequest,
) -> dict[str, Any]:
    return {
        "contract_ref": FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
        "today_item_ref": request.today_item_ref,
        "actor_id": request.actor_context.actor_id,
        "decision_reason_ref": request.decision_reason_ref,
        "risk_class": request.risk_class,
        "priority": request.priority,
        "metadata_refs": sorted(request.metadata_refs),
        "estimated_cost_usd": request.estimated_cost_usd,
        "max_approved_cost_usd": request.max_approved_cost_usd,
        "provider_ref": request.provider_ref,
        "model_profile_ref": request.model_profile_ref,
        "input_metered_units": request.input_metered_units,
        "output_metered_units": request.output_metered_units,
        "total_metered_units": request.total_metered_units,
        "unknown_paid_cost_requires_explicit_approval": (
            request.unknown_paid_cost_requires_explicit_approval
        ),
        "frontier_usage_claimed": request.frontier_usage_claimed,
    }


def _safe_suffix(value: str) -> str:
    suffix = SAFE_ACTION_SUFFIX_CHARS.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)


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
            _validate_safe_text(str(key), field_name)
            _validate_safe_payload(item, field_name)
