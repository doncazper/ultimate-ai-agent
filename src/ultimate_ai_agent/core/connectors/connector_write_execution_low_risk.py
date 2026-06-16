from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.connector_write_dry_run_planner import (
    ConnectorWriteDryRunDecision,
    ConnectorWriteDryRunStatus,
    validate_connector_write_dry_run_plan,
)


CONNECTOR_WRITE_EXECUTION_LOW_RISK_DOCS = [
    "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK.md",
    "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_NON_GOALS.md",
    "docs/connectors/M128_TO_M129_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorWriteExecutionLowRiskStatus(str, Enum):
    write_allowed_for_low_risk_transport = "write_allowed_for_low_risk_transport"
    write_completed = "write_completed"
    rejected = "rejected"


class _ConnectorWriteExecutionLowRisk(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorWriteExecutionLowRiskPolicy(_ConnectorWriteExecutionLowRisk):
    policy_ref: str = "connector-write-execution-low-risk-policy:m128"
    enabled_for_review: bool = True
    low_risk_write_allowed_by_policy: bool = True
    exact_m127_dry_run_binding_required: bool = True
    exact_connector_write_approval_required: bool = True
    transport_required: bool = True
    safe_result_only_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    revocation_required: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_safe_payload(self.metadata)
        return self


class ConnectorWriteExecutionLowRiskRequest(_ConnectorWriteExecutionLowRisk):
    request_ref: str
    execution_ref: str
    connector_write_dry_run_decision_ref: str
    connector_write_dry_run_plan_ref: str
    connector_write_approval_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    dry_run_operation_refs: list[str]
    write_target_refs: list[str]
    safe_payload_summary_refs: list[str]
    safe_result_ref: str
    safe_execution_scope_ref: str
    low_risk_classification_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    idempotency_key: str
    prior_milestone_refs: list[str]
    m127_decision: ConnectorWriteDryRunDecision
    safe_write_summary: str
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    local_only: bool = True
    safe_refs_only: bool = True
    low_risk_only: bool = True
    transport_required: bool = True
    live_connector_runtime_requested: bool = False
    account_auth_requested: bool = False
    network_access_requested: bool = False
    credential_handling_requested: bool = False
    raw_connector_content_requested: bool = False
    full_content_read_requested: bool = False
    connector_send_requested: bool = False
    connector_delete_requested: bool = False
    connector_export_requested: bool = False
    connector_bulk_export_requested: bool = False
    attachment_download_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    high_risk_write_requested: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        for refs, field_name in _request_ref_list_pairs(self):
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        _validate_safe_payload({"safe_write_summary": self.safe_write_summary})
        _validate_safe_payload(self.metadata)
        return self


class ConnectorWriteExecutionReceiptPlan(_ConnectorWriteExecutionLowRisk):
    receipt_plan_ref: str
    execution_ref: str
    connector_write_dry_run_plan_ref: str
    connector_write_approval_ref: str
    safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_connector_content: bool = False
    store_full_connector_content: bool = False
    store_credential_material: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    attachment_download_performed: bool = False
    network_access_performed: bool = False
    account_auth_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    production_authority_granted: bool = False
    safe_summary: str = (
        "M128 connector write execution receipt stores safe refs and safe "
        "summaries only for a low-risk injected transport result."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.execution_ref, "execution_ref"),
            (
                self.connector_write_dry_run_plan_ref,
                "connector_write_dry_run_plan_ref",
            ),
            (self.connector_write_approval_ref, "connector_write_approval_ref"),
            (self.safe_result_ref, "safe_result_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.store_safe_summary_only or not self.store_safe_refs_only:
            raise ValueError("M128_SAFE_RECEIPT_STORAGE_REQUIRED")
        for field_name, reason in _PERFORMED_DENIAL_FIELDS.items():
            if getattr(self, field_name, False):
                raise ValueError(reason)
        _validate_safe_payload({"safe_summary": self.safe_summary})
        return self


class ConnectorWriteExecutionDecision(_ConnectorWriteExecutionLowRisk):
    decision_ref: str
    status: ConnectorWriteExecutionLowRiskStatus
    execution_ref: str
    connector_write_dry_run_decision_ref: str
    connector_write_dry_run_plan_ref: str
    connector_write_approval_ref: str
    safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    low_risk_write_allowed: bool = True
    exact_m127_dry_run_bound: bool = True
    exact_connector_write_approval_bound: bool = True
    transport_required: bool = True
    safe_refs_only: bool = True
    local_only: bool = True
    audit_bound: bool = True
    replay_bound: bool = True
    revocation_bound: bool = True
    write_performed: bool = False
    reason_codes: list[str]
    safe_message: str
    receipt_plan: ConnectorWriteExecutionReceiptPlan
    live_connector_runtime_performed: bool = False
    account_auth_performed: bool = False
    network_access_performed: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_returned: bool = False
    full_connector_content_returned: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    connector_bulk_export_performed: bool = False
    attachment_download_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.execution_ref, "execution_ref"),
            (
                self.connector_write_dry_run_decision_ref,
                "connector_write_dry_run_decision_ref",
            ),
            (
                self.connector_write_dry_run_plan_ref,
                "connector_write_dry_run_plan_ref",
            ),
            (self.connector_write_approval_ref, "connector_write_approval_ref"),
            (self.safe_result_ref, "safe_result_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload({"safe_message": self.safe_message})
        return self


class ConnectorWriteExecutionTransportResponse(_ConnectorWriteExecutionLowRisk):
    write_completed: bool
    safe_result_ref: str
    safe_summary: str
    live_connector_runtime_performed: bool = False
    account_auth_performed: bool = False
    network_access_performed: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_returned: bool = False
    full_connector_content_returned: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    connector_bulk_export_performed: bool = False
    attachment_download_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.safe_result_ref, "safe_result_ref")
        _validate_safe_payload({"safe_summary": self.safe_summary})
        return self


class ConnectorWriteExecutionResult(_ConnectorWriteExecutionLowRisk):
    result_ref: str
    execution_ref: str
    connector_write_dry_run_plan_ref: str
    connector_write_approval_ref: str
    status: ConnectorWriteExecutionLowRiskStatus
    write_performed: bool = True
    safe_result_ref: str
    safe_summary: str
    reason_codes: list[str]
    live_connector_runtime_performed: bool = False
    account_auth_performed: bool = False
    network_access_performed: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_returned: bool = False
    full_connector_content_returned: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    connector_bulk_export_performed: bool = False
    attachment_download_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.result_ref, "result_ref"),
            (self.execution_ref, "execution_ref"),
            (
                self.connector_write_dry_run_plan_ref,
                "connector_write_dry_run_plan_ref",
            ),
            (self.connector_write_approval_ref, "connector_write_approval_ref"),
            (self.safe_result_ref, "safe_result_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload({"safe_summary": self.safe_summary})
        return self


ConnectorWriteExecutionTransport = Callable[
    [ConnectorWriteExecutionDecision], ConnectorWriteExecutionTransportResponse
]


def build_connector_write_execution_decision(
    request: ConnectorWriteExecutionLowRiskRequest,
    *,
    policy: ConnectorWriteExecutionLowRiskPolicy | None = None,
) -> ConnectorWriteExecutionDecision:
    active_policy = validate_connector_write_execution_policy(
        policy or ConnectorWriteExecutionLowRiskPolicy()
    )
    validated_request = validate_connector_write_execution_request(request)
    plan = validated_request.m127_decision.plan
    if plan is None:
        raise ValueError("M128_M127_DRY_RUN_PLAN_REQUIRED")
    receipt_plan = ConnectorWriteExecutionReceiptPlan(
        receipt_plan_ref=f"connector-write-execution-receipt-plan:{_suffix(validated_request.execution_ref)}",
        execution_ref=validated_request.execution_ref,
        connector_write_dry_run_plan_ref=validated_request.connector_write_dry_run_plan_ref,
        connector_write_approval_ref=validated_request.connector_write_approval_ref,
        safe_result_ref=validated_request.safe_result_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
    )
    decision = ConnectorWriteExecutionDecision(
        decision_ref=f"connector-write-execution-decision:{_suffix(validated_request.execution_ref)}",
        status=ConnectorWriteExecutionLowRiskStatus.write_allowed_for_low_risk_transport,
        execution_ref=validated_request.execution_ref,
        connector_write_dry_run_decision_ref=(
            validated_request.connector_write_dry_run_decision_ref
        ),
        connector_write_dry_run_plan_ref=(
            validated_request.connector_write_dry_run_plan_ref
        ),
        connector_write_approval_ref=validated_request.connector_write_approval_ref,
        safe_result_ref=validated_request.safe_result_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        low_risk_write_allowed=active_policy.low_risk_write_allowed_by_policy,
        exact_m127_dry_run_bound=active_policy.exact_m127_dry_run_binding_required,
        exact_connector_write_approval_bound=(
            active_policy.exact_connector_write_approval_required
        ),
        transport_required=active_policy.transport_required,
        safe_refs_only=active_policy.safe_refs_only,
        local_only=active_policy.local_only,
        audit_bound=active_policy.audit_required,
        replay_bound=active_policy.replay_required,
        revocation_bound=active_policy.revocation_required,
        reason_codes=[
            "M128_LOW_RISK_CONNECTOR_WRITE_ALLOWED",
            "M128_EXACT_M127_DRY_RUN_REQUIRED",
            "M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED",
            "M128_SAFE_TRANSPORT_REQUIRED",
            "M129_REMAINS_FUTURE",
        ],
        safe_message=(
            "M128 allows a low-risk connector write only through an injected "
            "safe transport over exact M127 dry-run refs."
        ),
        receipt_plan=receipt_plan,
    )
    return validate_connector_write_execution_decision(decision)


def perform_low_risk_connector_write(
    decision: ConnectorWriteExecutionDecision,
    *,
    transport: ConnectorWriteExecutionTransport | None,
) -> ConnectorWriteExecutionResult:
    validated_decision = validate_connector_write_execution_decision(decision)
    if transport is None:
        raise ValueError("M128_CONNECTOR_WRITE_TRANSPORT_REQUIRED")
    response = ConnectorWriteExecutionTransportResponse.model_validate(
        _model_payload(transport(validated_decision))
    )
    _validate_transport_response(response)
    if response.safe_result_ref != validated_decision.safe_result_ref:
        raise ValueError("M128_SAFE_RESULT_REF_MISMATCH")
    result = ConnectorWriteExecutionResult(
        result_ref=f"connector-write-execution-result:{_suffix(validated_decision.execution_ref)}",
        execution_ref=validated_decision.execution_ref,
        connector_write_dry_run_plan_ref=(
            validated_decision.connector_write_dry_run_plan_ref
        ),
        connector_write_approval_ref=validated_decision.connector_write_approval_ref,
        status=ConnectorWriteExecutionLowRiskStatus.write_completed,
        write_performed=True,
        safe_result_ref=response.safe_result_ref,
        safe_summary=response.safe_summary,
        reason_codes=[
            "M128_LOW_RISK_CONNECTOR_WRITE_COMPLETED",
            "M128_SAFE_RESULT_ONLY",
            "M128_AUDIT_AND_REVOCATION_REQUIRED",
        ],
    )
    return validate_connector_write_execution_result(result)


def validate_connector_write_execution_policy(
    policy: ConnectorWriteExecutionLowRiskPolicy,
) -> ConnectorWriteExecutionLowRiskPolicy:
    payload = _model_payload(policy)
    validated = ConnectorWriteExecutionLowRiskPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _ENABLEMENT_DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ConnectorWriteExecutionLowRiskPolicy):
        raise ValueError("M128_SECRET_LIKE_CONNECTOR_WRITE_CONTENT_DENIED")
    return validated


def validate_connector_write_execution_request(
    request: ConnectorWriteExecutionLowRiskRequest,
) -> ConnectorWriteExecutionLowRiskRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, ConnectorWriteExecutionLowRiskRequest):
        raise ValueError("M128_SECRET_LIKE_CONNECTOR_WRITE_CONTENT_DENIED")
    m127_payload = payload.get("m127_decision")
    if isinstance(m127_payload, dict) and (
        m127_payload.get("connector_write_authorized")
        or m127_payload.get("execution_authorized")
    ):
        raise ValueError("M128_M127_DRY_RUN_AUTHORITY_MISMATCH")
    validated = ConnectorWriteExecutionLowRiskRequest.model_validate(payload)
    for field_name, reason in _REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _REQUEST_DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    _validate_connector_write_approval_ref(validated.connector_write_approval_ref)
    _validate_low_risk_ref(validated.low_risk_classification_ref)
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_m127_binding(validated)
    return validated


def validate_connector_write_execution_decision(
    decision: ConnectorWriteExecutionDecision,
) -> ConnectorWriteExecutionDecision:
    payload = _model_payload(decision)
    validated = ConnectorWriteExecutionDecision.model_validate(payload)
    if validated.status != (
        ConnectorWriteExecutionLowRiskStatus.write_allowed_for_low_risk_transport
    ):
        raise ValueError("M128_CONNECTOR_WRITE_ALLOWED_STATUS_REQUIRED")
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.write_performed:
        raise ValueError("M128_WRITE_NOT_ALLOWED_IN_DECISION")
    for field_name, reason in _PERFORMED_DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M128_SIDE_EFFECTS_MUST_BE_EXACT_WRITE_ONLY")
    if "M128_LOW_RISK_CONNECTOR_WRITE_ALLOWED" not in validated.reason_codes:
        raise ValueError("M128_REASON_CODE_REQUIRED")
    return validated


def validate_connector_write_execution_result(
    result: ConnectorWriteExecutionResult,
) -> ConnectorWriteExecutionResult:
    payload = _model_payload(result)
    if _has_secret_like_extra(payload, ConnectorWriteExecutionResult):
        raise ValueError("M128_SECRET_LIKE_CONNECTOR_WRITE_CONTENT_DENIED")
    validated = ConnectorWriteExecutionResult.model_validate(payload)
    if validated.status != ConnectorWriteExecutionLowRiskStatus.write_completed:
        raise ValueError("M128_CONNECTOR_WRITE_COMPLETED_STATUS_REQUIRED")
    if not validated.write_performed:
        raise ValueError("M128_CONNECTOR_WRITE_COMPLETION_REQUIRED")
    for field_name, reason in _PERFORMED_DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M128_SIDE_EFFECTS_MUST_BE_EXACT_WRITE_ONLY")
    if "M128_LOW_RISK_CONNECTOR_WRITE_COMPLETED" not in validated.reason_codes:
        raise ValueError("M128_RESULT_REASON_CODE_REQUIRED")
    return validated


def _validate_transport_response(
    response: ConnectorWriteExecutionTransportResponse,
) -> None:
    if not response.write_completed:
        raise ValueError("M128_CONNECTOR_WRITE_NOT_COMPLETED")
    for field_name, reason in _PERFORMED_DENIAL_FIELDS.items():
        if getattr(response, field_name, False):
            raise ValueError(reason)
    if response.side_effects_performed:
        raise ValueError("M128_SIDE_EFFECTS_MUST_BE_EXACT_WRITE_ONLY")


def _validate_m127_binding(request: ConnectorWriteExecutionLowRiskRequest) -> None:
    decision = ConnectorWriteDryRunDecision.model_validate(
        _model_payload(request.m127_decision)
    )
    if decision.status != ConnectorWriteDryRunStatus.planned_for_review:
        raise ValueError("M128_M127_DRY_RUN_NOT_PLANNED")
    if not decision.planned or not decision.persisted or decision.plan is None:
        raise ValueError("M128_M127_DRY_RUN_PLAN_REQUIRED")
    if decision.connector_write_authorized or decision.execution_authorized:
        raise ValueError("M128_M127_DRY_RUN_AUTHORITY_MISMATCH")
    plan = validate_connector_write_dry_run_plan(decision.plan)
    comparisons = [
        (request.connector_write_dry_run_decision_ref, decision.decision_ref, "M128_M127_DRY_RUN_DECISION_REF_MISMATCH"),
        (request.connector_write_dry_run_plan_ref, plan.dry_run_plan_ref, "M128_M127_DRY_RUN_PLAN_REF_MISMATCH"),
        (request.connector_read_only_runtime_ref, plan.connector_read_only_runtime_ref, "M128_CONNECTOR_RUNTIME_REF_MISMATCH"),
        (request.source_messages_connector_contract_review_ref, plan.source_messages_connector_contract_review_ref, "M128_SOURCE_REVIEW_REF_MISMATCH"),
        (request.source_baseline_ref, plan.source_baseline_ref, "M128_BASELINE_REF_MISMATCH"),
        (request.actor_ref, plan.actor_ref, "M128_ACTOR_BINDING_MISMATCH"),
        (request.user_ref, plan.user_ref, "M128_USER_BINDING_MISMATCH"),
        (request.workspace_ref, plan.workspace_ref, "M128_WORKSPACE_BINDING_MISMATCH"),
        (request.connector_scope_refs, plan.connector_scope_refs, "M128_CONNECTOR_SCOPE_REF_MISMATCH"),
        (request.connector_allowlist_refs, plan.connector_allowlist_refs, "M128_CONNECTOR_ALLOWLIST_REF_MISMATCH"),
        (request.dry_run_operation_refs, plan.dry_run_operation_refs, "M128_DRY_RUN_OPERATION_REF_MISMATCH"),
        (request.write_target_refs, plan.write_target_refs, "M128_WRITE_TARGET_REF_MISMATCH"),
        (request.safe_payload_summary_refs, plan.safe_payload_summary_refs, "M128_SAFE_PAYLOAD_SUMMARY_REF_MISMATCH"),
        (request.audit_ref, plan.audit_ref, "M128_AUDIT_REF_MISMATCH"),
        (request.replay_ref, plan.replay_ref, "M128_REPLAY_REF_MISMATCH"),
        (request.idempotency_key, plan.idempotency_key, "M128_IDEMPOTENCY_REF_MISMATCH"),
    ]
    for actual, expected, reason in comparisons:
        if actual != expected:
            raise ValueError(reason)


def _validate_connector_write_approval_ref(ref: str) -> None:
    lower = ref.lower()
    if lower.startswith("approval_test_") or "approval-test" in lower:
        raise ValueError("M128_CONNECTOR_WRITE_APPROVAL_TEST_REF_DENIED")
    if "wildcard" in lower or lower.endswith(":all") or lower.endswith(":*"):
        raise ValueError("M128_WILDCARD_CONNECTOR_WRITE_APPROVAL_DENIED")
    if "m128" not in lower or "connector-write" not in lower:
        raise ValueError("M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED")
    _validate_m61_ref(ref, "connector_write_approval_ref")


def _validate_low_risk_ref(ref: str) -> None:
    if "low-risk" not in ref.lower() or "m128" not in ref.lower():
        raise ValueError("M128_LOW_RISK_CLASSIFICATION_REQUIRED")
    _validate_m61_ref(ref, "low_risk_classification_ref")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M128_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(set(refs)) != len(refs):
        raise ValueError("M128_PRIOR_MILESTONE_REF_DUPLICATE")
    missing = [ref for ref in _REQUIRED_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M128_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in _REQUIRED_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M128_PRIOR_MILESTONE_REF_UNEXPECTED")


def _request_ref_pairs(request: ConnectorWriteExecutionLowRiskRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.execution_ref, "execution_ref"),
        (
            request.connector_write_dry_run_decision_ref,
            "connector_write_dry_run_decision_ref",
        ),
        (
            request.connector_write_dry_run_plan_ref,
            "connector_write_dry_run_plan_ref",
        ),
        (request.connector_write_approval_ref, "connector_write_approval_ref"),
        (
            request.connector_read_only_runtime_ref,
            "connector_read_only_runtime_ref",
        ),
        (
            request.source_messages_connector_contract_review_ref,
            "source_messages_connector_contract_review_ref",
        ),
        (request.source_baseline_ref, "source_baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.safe_result_ref, "safe_result_ref"),
        (request.safe_execution_scope_ref, "safe_execution_scope_ref"),
        (request.low_risk_classification_ref, "low_risk_classification_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.idempotency_key, "idempotency_key"),
    ]


def _request_ref_list_pairs(request: ConnectorWriteExecutionLowRiskRequest):
    return [
        (request.connector_scope_refs, "connector_scope_ref"),
        (request.connector_allowlist_refs, "connector_allowlist_ref"),
        (request.dry_run_operation_refs, "dry_run_operation_ref"),
        (request.write_target_refs, "write_target_ref"),
        (request.safe_payload_summary_refs, "safe_payload_summary_ref"),
        (request.prior_milestone_refs, "prior_milestone_ref"),
        (request.metadata_refs, "metadata_ref"),
    ]


def _suffix(ref: str) -> str:
    return ref.replace(":", "-").replace("/", "-")


_REQUIRED_PRIOR_MILESTONE_REFS = [
    "milestone:M125",
    "milestone:M126",
    "milestone:M127",
]

_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "M128_REVIEW_ENABLED_REQUIRED"),
    ("low_risk_write_allowed_by_policy", "M128_LOW_RISK_WRITE_POLICY_REQUIRED"),
    (
        "exact_m127_dry_run_binding_required",
        "M128_EXACT_M127_DRY_RUN_REQUIRED",
    ),
    (
        "exact_connector_write_approval_required",
        "M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED",
    ),
    ("transport_required", "M128_CONNECTOR_WRITE_TRANSPORT_REQUIRED"),
    ("safe_result_only_required", "M128_SAFE_RESULT_ONLY_REQUIRED"),
    ("audit_required", "M128_AUDIT_REQUIRED"),
    ("replay_required", "M128_REPLAY_REQUIRED"),
    ("revocation_required", "M128_REVOCATION_REQUIRED"),
    ("local_only", "M128_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M128_SAFE_REFS_ONLY_REQUIRED"),
]

_REQUEST_REQUIRED_TRUE = [
    ("local_only", "M128_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M128_SAFE_REFS_ONLY_REQUIRED"),
    ("low_risk_only", "M128_LOW_RISK_ONLY_REQUIRED"),
    ("transport_required", "M128_CONNECTOR_WRITE_TRANSPORT_REQUIRED"),
]

_DECISION_REQUIRED_TRUE = [
    ("low_risk_write_allowed", "M128_LOW_RISK_WRITE_REQUIRED"),
    ("exact_m127_dry_run_bound", "M128_EXACT_M127_DRY_RUN_REQUIRED"),
    (
        "exact_connector_write_approval_bound",
        "M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED",
    ),
    ("transport_required", "M128_CONNECTOR_WRITE_TRANSPORT_REQUIRED"),
    ("safe_refs_only", "M128_SAFE_REFS_ONLY_REQUIRED"),
    ("local_only", "M128_LOCAL_ONLY_REQUIRED"),
    ("audit_bound", "M128_AUDIT_REQUIRED"),
    ("replay_bound", "M128_REPLAY_REQUIRED"),
    ("revocation_bound", "M128_REVOCATION_REQUIRED"),
]

_ENABLEMENT_DENIAL_FIELDS = {
    "live_connector_runtime_enabled": "M128_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M128_ACCOUNT_AUTH_DENIED",
    "network_access_enabled": "M128_NETWORK_ACCESS_DENIED",
    "credential_handling_enabled": "M128_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_enabled": "M128_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_enabled": "M128_FULL_CONTENT_READ_DENIED",
    "connector_send_enabled": "M128_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M128_CONNECTOR_DELETE_DENIED",
    "connector_export_enabled": "M128_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_enabled": "M128_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_enabled": "M128_ATTACHMENT_DOWNLOAD_DENIED",
    "model_call_enabled": "M128_MODEL_CALL_DENIED",
    "memory_write_enabled": "M128_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M128_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M128_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M128_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M128_DEPENDENCY_DENIED",
    "production_authority_granted": "M128_PRODUCTION_AUTHORITY_DENIED",
}

_REQUEST_DENIAL_FIELDS = {
    "live_connector_runtime_requested": "M128_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M128_ACCOUNT_AUTH_DENIED",
    "network_access_requested": "M128_NETWORK_ACCESS_DENIED",
    "credential_handling_requested": "M128_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_requested": "M128_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_requested": "M128_FULL_CONTENT_READ_DENIED",
    "connector_send_requested": "M128_CONNECTOR_SEND_DENIED",
    "connector_delete_requested": "M128_CONNECTOR_DELETE_DENIED",
    "connector_export_requested": "M128_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_requested": "M128_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_requested": "M128_ATTACHMENT_DOWNLOAD_DENIED",
    "model_call_requested": "M128_MODEL_CALL_DENIED",
    "memory_write_requested": "M128_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M128_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M128_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M128_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M128_DEPENDENCY_DENIED",
    "production_authority_requested": "M128_PRODUCTION_AUTHORITY_DENIED",
    "high_risk_write_requested": "M128_HIGH_RISK_CONNECTOR_WRITE_DENIED",
}

_PERFORMED_DENIAL_FIELDS = {
    "live_connector_runtime_performed": "M128_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M128_ACCOUNT_AUTH_DENIED",
    "network_access_performed": "M128_NETWORK_ACCESS_DENIED",
    "credential_handling_performed": "M128_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_returned": "M128_RAW_CONNECTOR_CONTENT_DENIED",
    "full_connector_content_returned": "M128_FULL_CONTENT_READ_DENIED",
    "connector_send_performed": "M128_CONNECTOR_SEND_DENIED",
    "connector_delete_performed": "M128_CONNECTOR_DELETE_DENIED",
    "connector_export_performed": "M128_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_performed": "M128_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_performed": "M128_ATTACHMENT_DOWNLOAD_DENIED",
    "model_call_performed": "M128_MODEL_CALL_DENIED",
    "memory_write_performed": "M128_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M128_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M128_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M128_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M128_DEPENDENCY_DENIED",
    "production_authority_granted": "M128_PRODUCTION_AUTHORITY_DENIED",
}
