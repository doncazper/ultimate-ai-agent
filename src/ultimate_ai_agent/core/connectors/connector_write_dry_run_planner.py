from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.connector_approval_capture import (
    ConnectorApprovalCaptureDecision,
    ConnectorApprovalCaptureDecisionStatus,
    ConnectorApprovalCaptureRecord,
    validate_connector_approval_capture_record,
)
from ultimate_ai_agent.core.time import utc_now


CONNECTOR_WRITE_DRY_RUN_PLANNER_DOCS = [
    "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER.md",
    "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_NON_GOALS.md",
    "docs/connectors/M127_TO_M128_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorWriteDryRunActionKind(str, Enum):
    plan_email_draft = "plan_email_draft"
    plan_calendar_event_draft = "plan_calendar_event_draft"
    plan_contact_metadata_update = "plan_contact_metadata_update"
    plan_message_reply_draft = "plan_message_reply_draft"


class ConnectorWriteDryRunStatus(str, Enum):
    planned_for_review = "planned_for_review"
    rejected = "rejected"


class _ConnectorWriteDryRun(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorWriteDryRunPolicy(_ConnectorWriteDryRun):
    policy_ref: str = "connector-write-dry-run-policy:m127"
    dry_run_only_required: bool = True
    safe_refs_required: bool = True
    exact_approval_binding_required: bool = True
    actor_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    connector_allowlist_binding_required: bool = True
    dry_run_operation_allowlist_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    revocation_required: bool = True
    approval_ref_not_authority_required: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_safe_payload(self.metadata)
        return self


class ConnectorWriteDryRunRequest(_ConnectorWriteDryRun):
    dry_run_request_ref: str
    approval_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    source_operation_allowlist_refs: list[str]
    redacted_metadata_preview_refs: list[str]
    dry_run_operation_refs: list[str]
    write_target_refs: list[str]
    safe_payload_summary_refs: list[str]
    data_minimization_refs: list[str]
    redaction_refs: list[str]
    audit_ref: str
    replay_ref: str
    idempotency_key: str
    dry_run_receipt_plan_ref: str
    action_kind: ConnectorWriteDryRunActionKind
    requested_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    replay_nonce: str | None = None
    used_replay_nonces: list[str] = Field(default_factory=list)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    dry_run_only: bool = True
    safe_ref_only: bool = True
    approval_ref_not_authority: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _request_ref_pairs(self):
            if value is not None:
                _validate_m61_ref(value, field_name)
        for refs, field_name, _required in _request_ref_list_pairs(self):
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if self.safe_reason:
            _validate_safe_text(self.safe_reason)
        _validate_safe_payload(self.metadata)
        return self


class ConnectorWriteDryRunPlan(_ConnectorWriteDryRun):
    dry_run_plan_ref: str
    approval_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    source_operation_allowlist_refs: list[str]
    redacted_metadata_preview_refs: list[str]
    dry_run_operation_refs: list[str]
    write_target_refs: list[str]
    safe_payload_summary_refs: list[str]
    data_minimization_refs: list[str]
    redaction_refs: list[str]
    audit_ref: str
    replay_ref: str
    idempotency_key: str
    dry_run_receipt_plan_ref: str
    action_kind: ConnectorWriteDryRunActionKind
    status: ConnectorWriteDryRunStatus = ConnectorWriteDryRunStatus.planned_for_review
    created_at: datetime = Field(default_factory=utc_now)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    dry_run_only: bool = True
    safe_ref_only: bool = True
    approval_bound: bool = True
    actor_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    connector_allowlist_bound: bool = True
    dry_run_operation_allowlist_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    revocable: bool = True
    approval_ref_not_authority: bool = True
    side_effects_performed: list[str] = Field(default_factory=list)
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _plan_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        for refs, field_name in _plan_ref_list_pairs(self):
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if self.safe_reason:
            _validate_safe_text(self.safe_reason)
        _validate_safe_payload(self.metadata)
        _validate_safe_text(self.safe_summary)
        return self


class ConnectorWriteDryRunReceiptPlan(_ConnectorWriteDryRun):
    receipt_plan_ref: str
    dry_run_plan_ref: str
    approval_ref: str
    connector_read_only_runtime_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    raw_connector_content_stored: bool = False
    full_content_stored: bool = False
    credential_material_stored: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    attachment_download_performed: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = (
        "M127 connector write dry-run receipt stores safe refs only and records "
        "no connector write, send, delete, export, context, memory, or execution."
    )

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.dry_run_plan_ref, "dry_run_plan_ref"),
            (self.approval_ref, "approval_ref"),
            (self.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for field_name in _RECEIPT_MUST_STAY_FALSE:
            if getattr(self, field_name):
                raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_RECEIPT_MUST_BE_NO_EFFECT")
        _validate_safe_text(self.safe_summary)
        return self


class ConnectorWriteDryRunDecision(_ConnectorWriteDryRun):
    decision_ref: str
    status: ConnectorWriteDryRunStatus
    approval_ref: str | None = None
    connector_read_only_runtime_ref: str
    planned: bool = False
    persisted: bool = False
    dry_run_only: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    plan: ConnectorWriteDryRunPlan | None = None
    receipt_plan: ConnectorWriteDryRunReceiptPlan | None = None
    live_connector_runtime_authorized: bool = False
    account_auth_authorized: bool = False
    network_access_authorized: bool = False
    credential_handling_authorized: bool = False
    raw_connector_content_authorized: bool = False
    full_content_read_authorized: bool = False
    connector_write_authorized: bool = False
    connector_send_authorized: bool = False
    connector_delete_authorized: bool = False
    connector_export_authorized: bool = False
    connector_bulk_export_authorized: bool = False
    attachment_download_authorized: bool = False
    model_call_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(
            self.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"
        )
        if self.approval_ref:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        _validate_safe_text(self.safe_message)
        if not self.dry_run_only:
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_ONLY_REQUIRED")
        for field_name in _DECISION_AUTHORITY_FALSE_FIELDS:
            if getattr(self, field_name):
                raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_GRANTS_AUTHORITY")
        return self


def plan_connector_write_dry_run(
    approval_decision: ConnectorApprovalCaptureDecision,
    request: ConnectorWriteDryRunRequest,
    *,
    current_time: datetime | None = None,
    policy: ConnectorWriteDryRunPolicy | None = None,
) -> ConnectorWriteDryRunDecision:
    active_policy = validate_connector_write_dry_run_policy(
        policy or ConnectorWriteDryRunPolicy()
    )
    approval_record, approval_reasons = _approval_record_or_reasons(approval_decision)
    reasons = _dedupe(
        approval_reasons
        + _revalidate_request(request, current_time=current_time)
        + _binding_reasons(approval_record, request)
    )
    if reasons:
        return _rejected_decision(
            connector_read_only_runtime_ref=getattr(
                request,
                "connector_read_only_runtime_ref",
                "connector-read-only-runtime:m127:invalid",
            ),
            approval_ref=getattr(request, "approval_ref", None),
            reasons=reasons,
        )
    plan = ConnectorWriteDryRunPlan(
        dry_run_plan_ref=(
            "connector-write-dry-run-plan:"
            f"{_safe_suffix(request.dry_run_request_ref)}"
        ),
        approval_ref=request.approval_ref,
        connector_read_only_runtime_ref=request.connector_read_only_runtime_ref,
        source_messages_connector_contract_review_ref=(
            request.source_messages_connector_contract_review_ref
        ),
        source_baseline_ref=request.source_baseline_ref,
        actor_ref=request.actor_ref,
        user_ref=request.user_ref,
        workspace_ref=request.workspace_ref,
        connector_scope_refs=request.connector_scope_refs,
        connector_allowlist_refs=request.connector_allowlist_refs,
        source_operation_allowlist_refs=request.source_operation_allowlist_refs,
        redacted_metadata_preview_refs=request.redacted_metadata_preview_refs,
        dry_run_operation_refs=request.dry_run_operation_refs,
        write_target_refs=request.write_target_refs,
        safe_payload_summary_refs=request.safe_payload_summary_refs,
        data_minimization_refs=request.data_minimization_refs,
        redaction_refs=request.redaction_refs,
        audit_ref=request.audit_ref,
        replay_ref=request.replay_ref,
        idempotency_key=request.idempotency_key,
        dry_run_receipt_plan_ref=request.dry_run_receipt_plan_ref,
        action_kind=request.action_kind,
        safe_reason=request.safe_reason,
        metadata_refs=request.metadata_refs,
        metadata=request.metadata,
        dry_run_only=active_policy.dry_run_only_required,
        safe_ref_only=active_policy.safe_refs_required,
        approval_bound=active_policy.exact_approval_binding_required,
        actor_bound=active_policy.actor_binding_required,
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        connector_allowlist_bound=active_policy.connector_allowlist_binding_required,
        dry_run_operation_allowlist_bound=(
            active_policy.dry_run_operation_allowlist_required
        ),
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        revocable=active_policy.revocation_required,
        approval_ref_not_authority=active_policy.approval_ref_not_authority_required,
        side_effects_performed=[],
        safe_summary=(
            "M127 records a connector write dry-run plan for governed review. "
            "The plan is safe-ref-only and performs no connector write, send, "
            "delete, export, network access, credential handling, context "
            "injection, memory write, model call, backend route, Control Center "
            "control, dependency change, or production action."
        ),
    )
    return _planned_decision(validate_connector_write_dry_run_plan(plan))


def validate_connector_write_dry_run_policy(
    policy: ConnectorWriteDryRunPolicy,
) -> ConnectorWriteDryRunPolicy:
    payload = _model_payload(policy)
    validated = ConnectorWriteDryRunPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    _validate_m127_metadata(validated.metadata)
    return validated


def validate_connector_write_dry_run_request(
    request: ConnectorWriteDryRunRequest,
) -> ConnectorWriteDryRunRequest:
    reasons = _revalidate_request(request, current_time=None)
    if reasons:
        raise ValueError(reasons[0])
    return ConnectorWriteDryRunRequest.model_validate(_model_payload(request))


def validate_connector_write_dry_run_plan(
    plan: ConnectorWriteDryRunPlan,
) -> ConnectorWriteDryRunPlan:
    payload = _model_payload(plan)
    if _has_secret_like_extra(payload, ConnectorWriteDryRunPlan):
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_SECRET_METADATA_DENIED")
    for field_name, reason in _DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    for field_name, reason in _PLAN_REQUIRED_TRUE:
        if not payload.get(field_name):
            raise ValueError(reason)
    if payload.get("raw_connector_content") is not None:
        raise ValueError("M127_RAW_CONNECTOR_CONTENT_DENIED")
    if payload.get("full_connector_content") is not None:
        raise ValueError("M127_FULL_CONTENT_READ_DENIED")
    validated = ConnectorWriteDryRunPlan.model_validate(payload)
    if validated.status != ConnectorWriteDryRunStatus.planned_for_review:
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_SIDE_EFFECTS_DENIED")
    _validate_dry_run_refs(validated)
    _validate_m127_metadata(validated.metadata)
    _validate_safe_text(validated.safe_summary)
    return validated


def _planned_decision(
    plan: ConnectorWriteDryRunPlan,
) -> ConnectorWriteDryRunDecision:
    receipt_plan = ConnectorWriteDryRunReceiptPlan(
        receipt_plan_ref=plan.dry_run_receipt_plan_ref,
        dry_run_plan_ref=plan.dry_run_plan_ref,
        approval_ref=plan.approval_ref,
        connector_read_only_runtime_ref=plan.connector_read_only_runtime_ref,
        actor_ref=plan.actor_ref,
        user_ref=plan.user_ref,
        workspace_ref=plan.workspace_ref,
    )
    return ConnectorWriteDryRunDecision(
        decision_ref=(
            "connector-write-dry-run-decision:"
            f"{_safe_suffix(plan.dry_run_plan_ref)}"
        ),
        status=ConnectorWriteDryRunStatus.planned_for_review,
        approval_ref=plan.approval_ref,
        connector_read_only_runtime_ref=plan.connector_read_only_runtime_ref,
        planned=True,
        persisted=True,
        reason_codes=[
            "M127_CONNECTOR_WRITE_DRY_RUN_PLANNED_FOR_REVIEW",
            "M127_NO_CONNECTOR_WRITE_EXECUTION",
        ],
        safe_message=(
            "M127 connector write dry-run planner persisted safe refs only. "
            "Approval refs remain identifiers, not connector write authority."
        ),
        plan=plan,
        receipt_plan=receipt_plan,
    )


def _rejected_decision(
    *,
    connector_read_only_runtime_ref: str,
    approval_ref: str | None,
    reasons: list[str],
) -> ConnectorWriteDryRunDecision:
    safe_approval_ref = approval_ref
    if safe_approval_ref is not None:
        try:
            _validate_m61_ref(safe_approval_ref, "approval_ref")
        except ValueError:
            safe_approval_ref = None
    safe_runtime_ref = connector_read_only_runtime_ref
    try:
        _validate_m61_ref(safe_runtime_ref, "connector_read_only_runtime_ref")
    except ValueError:
        safe_runtime_ref = "connector-read-only-runtime:m127:invalid"
    return ConnectorWriteDryRunDecision(
        decision_ref=(
            "connector-write-dry-run-decision:"
            f"{_safe_suffix(safe_runtime_ref)}"
        ),
        status=ConnectorWriteDryRunStatus.rejected,
        approval_ref=safe_approval_ref,
        connector_read_only_runtime_ref=safe_runtime_ref,
        planned=False,
        persisted=False,
        reason_codes=_dedupe(reasons),
        safe_message=(
            "M127 connector write dry-run planner rejected the request safely. "
            "No connector write, send, delete, export, context, memory, or "
            "execution authority was granted."
        ),
    )


def _approval_record_or_reasons(
    approval_decision: ConnectorApprovalCaptureDecision,
) -> tuple[ConnectorApprovalCaptureRecord | None, list[str]]:
    reasons: list[str] = []
    try:
        decision = ConnectorApprovalCaptureDecision.model_validate(
            _model_payload(approval_decision)
        )
    except ValueError:
        return None, ["M127_SOURCE_APPROVAL_DECISION_INVALID"]
    if decision.status != ConnectorApprovalCaptureDecisionStatus.approved_for_review_only:
        reasons.append("M127_SOURCE_APPROVAL_NOT_APPROVED")
    if not decision.captured or not decision.persisted or not decision.review_only:
        reasons.append("M127_SOURCE_APPROVAL_NOT_CAPTURED")
    if decision.record is None:
        reasons.append("M127_SOURCE_APPROVAL_RECORD_REQUIRED")
        return None, _dedupe(reasons)
    try:
        record = validate_connector_approval_capture_record(decision.record)
    except ValueError:
        reasons.append("M127_SOURCE_APPROVAL_RECORD_INVALID")
        return None, _dedupe(reasons)
    if record.status != ConnectorApprovalCaptureDecisionStatus.approved_for_review_only:
        reasons.append("M127_SOURCE_APPROVAL_NOT_APPROVED")
    return record, _dedupe(reasons)


def _revalidate_request(
    request: ConnectorWriteDryRunRequest,
    *,
    current_time: datetime | None,
) -> list[str]:
    payload = _model_payload(request)
    reasons: list[str] = []
    if _has_secret_like_extra(payload, ConnectorWriteDryRunRequest):
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_SECRET_METADATA_DENIED")
    for field_name, reason in _DENIAL_FIELDS.items():
        if payload.get(field_name):
            reasons.append(reason)
    for field_name, reason in _REQUEST_REQUIRED_TRUE:
        if not payload.get(field_name):
            reasons.append(reason)
    for value, field_name in _request_ref_pairs(request):
        if value is None:
            if field_name != "replay_nonce":
                reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_REVALIDATION_FAILED")
            continue
        try:
            _validate_m61_ref(value, field_name)
        except ValueError:
            reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_REVALIDATION_FAILED")
    for refs, field_name, required in _request_ref_list_pairs(request):
        if required and not refs:
            reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_SAFE_REF_REQUIRED")
        for ref in refs:
            try:
                _validate_m61_ref(ref, field_name)
            except ValueError:
                reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_REVALIDATION_FAILED")
    if not isinstance(
        getattr(request, "action_kind", None), ConnectorWriteDryRunActionKind
    ):
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_ACTION_NOT_ALLOWED")
    if str(getattr(request, "approval_ref", "")).startswith("approval_test_"):
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_TEST_APPROVAL_DENIED")
    if getattr(request, "revoked_at", None) is not None:
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_REVOKED")
    if (
        getattr(request, "expires_at", None) is not None
        and request.expires_at <= (current_time or utc_now())
    ):
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_EXPIRED")
    replay_nonce = getattr(request, "replay_nonce", None)
    if replay_nonce and replay_nonce in list(getattr(request, "used_replay_nonces", [])):
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_REPLAY_DETECTED")
    try:
        _validate_action_operation_refs(request)
        _validate_dry_run_ref_lists(request)
    except ValueError as exc:
        reasons.append(str(exc))
    if getattr(request, "safe_reason", None):
        try:
            _validate_safe_text(request.safe_reason)
        except ValueError:
            reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_SAFE_REASON_DENIED")
    try:
        _validate_m127_metadata(getattr(request, "metadata", {}))
    except ValueError:
        reasons.append("M127_CONNECTOR_WRITE_DRY_RUN_SECRET_METADATA_DENIED")
    return _dedupe(reasons)


def _binding_reasons(
    approval_record: ConnectorApprovalCaptureRecord | None,
    request: ConnectorWriteDryRunRequest,
) -> list[str]:
    if approval_record is None:
        return []
    checks = [
        (
            request.approval_ref,
            approval_record.approval_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_REF_MISMATCH",
        ),
        (
            request.actor_ref,
            approval_record.actor_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_ACTOR_MISMATCH",
        ),
        (
            request.user_ref,
            approval_record.user_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_USER_MISMATCH",
        ),
        (
            request.workspace_ref,
            approval_record.workspace_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_WORKSPACE_MISMATCH",
        ),
        (
            request.connector_read_only_runtime_ref,
            approval_record.connector_read_only_runtime_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_RUNTIME_REF_MISMATCH",
        ),
        (
            request.source_messages_connector_contract_review_ref,
            approval_record.source_messages_connector_contract_review_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_SOURCE_REVIEW_REF_MISMATCH",
        ),
        (
            request.source_baseline_ref,
            approval_record.source_baseline_ref,
            "M127_CONNECTOR_WRITE_DRY_RUN_BASELINE_REF_MISMATCH",
        ),
        (
            request.connector_scope_refs,
            approval_record.connector_scope_refs,
            "M127_CONNECTOR_WRITE_DRY_RUN_SCOPE_REF_MISMATCH",
        ),
        (
            request.connector_allowlist_refs,
            approval_record.connector_allowlist_refs,
            "M127_CONNECTOR_WRITE_DRY_RUN_ALLOWLIST_REF_MISMATCH",
        ),
        (
            request.source_operation_allowlist_refs,
            approval_record.operation_allowlist_refs,
            "M127_CONNECTOR_WRITE_DRY_RUN_SOURCE_OPERATION_REF_MISMATCH",
        ),
        (
            request.redacted_metadata_preview_refs,
            approval_record.redacted_metadata_preview_refs,
            "M127_CONNECTOR_WRITE_DRY_RUN_METADATA_PREVIEW_REF_MISMATCH",
        ),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _validate_action_operation_refs(request: ConnectorWriteDryRunRequest) -> None:
    operation_ref = _ACTION_OPERATION_REF.get(getattr(request, "action_kind", None))
    if operation_ref is None or operation_ref not in request.dry_run_operation_refs:
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_ACTION_OPERATION_REQUIRED")
    for ref in request.dry_run_operation_refs:
        if ref not in _ALLOWED_DRY_RUN_OPERATION_REFS:
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_OPERATION_NOT_ALLOWED")


def _validate_dry_run_ref_lists(request: ConnectorWriteDryRunRequest) -> None:
    for ref in request.write_target_refs:
        if not ref.startswith("connector-write-target-ref:m127:"):
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_TARGET_REF_REQUIRED")
    for ref in request.safe_payload_summary_refs:
        if not ref.startswith("safe-payload-summary-ref:m127:"):
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_SAFE_SUMMARY_REF_REQUIRED")
    for ref in request.data_minimization_refs:
        if not ref.startswith("data-minimization-ref:m127:"):
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_DATA_MINIMIZATION_REQUIRED")
    for ref in request.redaction_refs:
        if not ref.startswith("redaction-ref:m127:"):
            raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_REDACTION_REQUIRED")


def _validate_dry_run_refs(plan: ConnectorWriteDryRunPlan) -> None:
    _validate_action_operation_refs(plan)  # type: ignore[arg-type]
    _validate_dry_run_ref_lists(plan)  # type: ignore[arg-type]
    if not plan.dry_run_plan_ref.startswith("connector-write-dry-run-plan:"):
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_PLAN_REF_REQUIRED")
    if not plan.dry_run_receipt_plan_ref.startswith("receipt-plan-ref:m127:"):
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_RECEIPT_PLAN_REF_REQUIRED")


def _validate_m127_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("M127_CONNECTOR_WRITE_DRY_RUN_SECRET_METADATA_DENIED") from exc


def _validate_safe_text(value: str) -> None:
    _validate_safe_payload({"safe_text": value})


def _request_ref_pairs(request: ConnectorWriteDryRunRequest) -> list[Any]:
    return [
        (getattr(request, "dry_run_request_ref", None), "dry_run_request_ref"),
        (getattr(request, "approval_ref", None), "approval_ref"),
        (
            getattr(request, "connector_read_only_runtime_ref", None),
            "connector_read_only_runtime_ref",
        ),
        (
            getattr(request, "source_messages_connector_contract_review_ref", None),
            "source_messages_connector_contract_review_ref",
        ),
        (getattr(request, "source_baseline_ref", None), "source_baseline_ref"),
        (getattr(request, "actor_ref", None), "actor_ref"),
        (getattr(request, "user_ref", None), "user_ref"),
        (getattr(request, "workspace_ref", None), "workspace_ref"),
        (getattr(request, "audit_ref", None), "audit_ref"),
        (getattr(request, "replay_ref", None), "replay_ref"),
        (getattr(request, "idempotency_key", None), "idempotency_key"),
        (
            getattr(request, "dry_run_receipt_plan_ref", None),
            "dry_run_receipt_plan_ref",
        ),
        (getattr(request, "replay_nonce", None), "replay_nonce"),
    ]


def _request_ref_list_pairs(request: ConnectorWriteDryRunRequest) -> list[Any]:
    return [
        (getattr(request, "connector_scope_refs", []), "connector_scope_ref", True),
        (
            getattr(request, "connector_allowlist_refs", []),
            "connector_allowlist_ref",
            True,
        ),
        (
            getattr(request, "source_operation_allowlist_refs", []),
            "source_operation_allowlist_ref",
            True,
        ),
        (
            getattr(request, "redacted_metadata_preview_refs", []),
            "redacted_metadata_preview_ref",
            True,
        ),
        (
            getattr(request, "dry_run_operation_refs", []),
            "dry_run_operation_ref",
            True,
        ),
        (getattr(request, "write_target_refs", []), "write_target_ref", True),
        (
            getattr(request, "safe_payload_summary_refs", []),
            "safe_payload_summary_ref",
            True,
        ),
        (
            getattr(request, "data_minimization_refs", []),
            "data_minimization_ref",
            True,
        ),
        (getattr(request, "redaction_refs", []), "redaction_ref", True),
        (getattr(request, "metadata_refs", []), "metadata_ref", False),
        (getattr(request, "used_replay_nonces", []), "used_replay_nonce", False),
    ]


def _plan_ref_pairs(plan: ConnectorWriteDryRunPlan) -> list[Any]:
    return [
        (plan.dry_run_plan_ref, "dry_run_plan_ref"),
        (plan.approval_ref, "approval_ref"),
        (plan.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"),
        (
            plan.source_messages_connector_contract_review_ref,
            "source_messages_connector_contract_review_ref",
        ),
        (plan.source_baseline_ref, "source_baseline_ref"),
        (plan.actor_ref, "actor_ref"),
        (plan.user_ref, "user_ref"),
        (plan.workspace_ref, "workspace_ref"),
        (plan.audit_ref, "audit_ref"),
        (plan.replay_ref, "replay_ref"),
        (plan.idempotency_key, "idempotency_key"),
        (plan.dry_run_receipt_plan_ref, "dry_run_receipt_plan_ref"),
    ]


def _plan_ref_list_pairs(plan: ConnectorWriteDryRunPlan) -> list[Any]:
    return [
        (plan.connector_scope_refs, "connector_scope_ref"),
        (plan.connector_allowlist_refs, "connector_allowlist_ref"),
        (plan.source_operation_allowlist_refs, "source_operation_allowlist_ref"),
        (plan.redacted_metadata_preview_refs, "redacted_metadata_preview_ref"),
        (plan.dry_run_operation_refs, "dry_run_operation_ref"),
        (plan.write_target_refs, "write_target_ref"),
        (plan.safe_payload_summary_refs, "safe_payload_summary_ref"),
        (plan.data_minimization_refs, "data_minimization_ref"),
        (plan.redaction_refs, "redaction_ref"),
        (plan.metadata_refs, "metadata_ref"),
    ]


def _safe_suffix(ref: str) -> str:
    return ref.replace(":", "-").replace("/", "-")


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


_ALLOWED_DRY_RUN_OPERATION_REFS = {
    "connector-write-dry-run-operation-ref:m127:plan-email-draft",
    "connector-write-dry-run-operation-ref:m127:plan-calendar-event-draft",
    "connector-write-dry-run-operation-ref:m127:plan-contact-metadata-update",
    "connector-write-dry-run-operation-ref:m127:plan-message-reply-draft",
}

_ACTION_OPERATION_REF = {
    ConnectorWriteDryRunActionKind.plan_email_draft: (
        "connector-write-dry-run-operation-ref:m127:plan-email-draft"
    ),
    ConnectorWriteDryRunActionKind.plan_calendar_event_draft: (
        "connector-write-dry-run-operation-ref:m127:plan-calendar-event-draft"
    ),
    ConnectorWriteDryRunActionKind.plan_contact_metadata_update: (
        "connector-write-dry-run-operation-ref:m127:plan-contact-metadata-update"
    ),
    ConnectorWriteDryRunActionKind.plan_message_reply_draft: (
        "connector-write-dry-run-operation-ref:m127:plan-message-reply-draft"
    ),
}

_POLICY_REQUIRED_TRUE = [
    ("dry_run_only_required", "M127_CONNECTOR_WRITE_DRY_RUN_ONLY_REQUIRED"),
    ("safe_refs_required", "M127_CONNECTOR_WRITE_DRY_RUN_SAFE_REFS_REQUIRED"),
    (
        "exact_approval_binding_required",
        "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_BINDING_REQUIRED",
    ),
    ("actor_binding_required", "M127_CONNECTOR_WRITE_DRY_RUN_ACTOR_BINDING_REQUIRED"),
    ("user_binding_required", "M127_CONNECTOR_WRITE_DRY_RUN_USER_BINDING_REQUIRED"),
    (
        "workspace_binding_required",
        "M127_CONNECTOR_WRITE_DRY_RUN_WORKSPACE_BINDING_REQUIRED",
    ),
    (
        "connector_allowlist_binding_required",
        "M127_CONNECTOR_WRITE_DRY_RUN_ALLOWLIST_BINDING_REQUIRED",
    ),
    (
        "dry_run_operation_allowlist_required",
        "M127_CONNECTOR_WRITE_DRY_RUN_OPERATION_ALLOWLIST_REQUIRED",
    ),
    ("audit_required", "M127_CONNECTOR_WRITE_DRY_RUN_AUDIT_REQUIRED"),
    ("replay_required", "M127_CONNECTOR_WRITE_DRY_RUN_REPLAY_REQUIRED"),
    ("revocation_required", "M127_CONNECTOR_WRITE_DRY_RUN_REVOCATION_REQUIRED"),
    (
        "approval_ref_not_authority_required",
        "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_NOT_AUTHORITY_REQUIRED",
    ),
]

_REQUEST_REQUIRED_TRUE = [
    ("dry_run_only", "M127_CONNECTOR_WRITE_DRY_RUN_ONLY_REQUIRED"),
    ("safe_ref_only", "M127_CONNECTOR_WRITE_DRY_RUN_SAFE_REFS_REQUIRED"),
    (
        "approval_ref_not_authority",
        "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_NOT_AUTHORITY_REQUIRED",
    ),
]

_PLAN_REQUIRED_TRUE = [
    ("dry_run_only", "M127_CONNECTOR_WRITE_DRY_RUN_ONLY_REQUIRED"),
    ("safe_ref_only", "M127_CONNECTOR_WRITE_DRY_RUN_SAFE_REFS_REQUIRED"),
    ("approval_bound", "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_BINDING_REQUIRED"),
    ("actor_bound", "M127_CONNECTOR_WRITE_DRY_RUN_ACTOR_BINDING_REQUIRED"),
    ("user_bound", "M127_CONNECTOR_WRITE_DRY_RUN_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M127_CONNECTOR_WRITE_DRY_RUN_WORKSPACE_BINDING_REQUIRED"),
    (
        "connector_allowlist_bound",
        "M127_CONNECTOR_WRITE_DRY_RUN_ALLOWLIST_BINDING_REQUIRED",
    ),
    (
        "dry_run_operation_allowlist_bound",
        "M127_CONNECTOR_WRITE_DRY_RUN_OPERATION_ALLOWLIST_REQUIRED",
    ),
    ("audit_required", "M127_CONNECTOR_WRITE_DRY_RUN_AUDIT_REQUIRED"),
    ("replay_safe", "M127_CONNECTOR_WRITE_DRY_RUN_REPLAY_REQUIRED"),
    ("revocable", "M127_CONNECTOR_WRITE_DRY_RUN_REVOCATION_REQUIRED"),
    (
        "approval_ref_not_authority",
        "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_NOT_AUTHORITY_REQUIRED",
    ),
]

_DENIAL_FIELDS = {
    "live_connector_runtime_enabled": "M127_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M127_ACCOUNT_AUTH_DENIED",
    "network_access_enabled": "M127_NETWORK_ACCESS_DENIED",
    "credential_handling_enabled": "M127_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_enabled": "M127_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_enabled": "M127_FULL_CONTENT_READ_DENIED",
    "connector_write_enabled": "M127_CONNECTOR_WRITE_EXECUTION_DENIED",
    "connector_send_enabled": "M127_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M127_CONNECTOR_DELETE_DENIED",
    "connector_export_enabled": "M127_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_enabled": "M127_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_enabled": "M127_ATTACHMENT_DOWNLOAD_DENIED",
    "model_call_enabled": "M127_MODEL_CALL_DENIED",
    "memory_write_enabled": "M127_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M127_CONTEXT_INJECTION_DENIED",
    "execution_enabled": "M127_EXECUTION_DENIED",
    "backend_route_added": "M127_BACKEND_ROUTE_DENIED",
    "backend_route_enabled": "M127_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M127_CONTROL_CENTER_CONTROL_DENIED",
    "control_center_control_enabled": "M127_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M127_DEPENDENCY_DENIED",
}

_RECEIPT_MUST_STAY_FALSE = [
    "raw_connector_content_stored",
    "full_content_stored",
    "credential_material_stored",
    "connector_write_performed",
    "connector_send_performed",
    "connector_delete_performed",
    "connector_export_performed",
    "attachment_download_performed",
    "context_injection_performed",
    "memory_write_performed",
    "execution_performed",
]

_DECISION_AUTHORITY_FALSE_FIELDS = [
    "live_connector_runtime_authorized",
    "account_auth_authorized",
    "network_access_authorized",
    "credential_handling_authorized",
    "raw_connector_content_authorized",
    "full_content_read_authorized",
    "connector_write_authorized",
    "connector_send_authorized",
    "connector_delete_authorized",
    "connector_export_authorized",
    "connector_bulk_export_authorized",
    "attachment_download_authorized",
    "model_call_authorized",
    "memory_write_authorized",
    "context_injection_authorized",
    "execution_authorized",
    "execution_performed",
    "backend_route_added",
    "control_center_control_added",
    "dependency_added",
]
