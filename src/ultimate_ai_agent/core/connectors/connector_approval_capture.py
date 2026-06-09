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
from ultimate_ai_agent.core.connectors.connector_read_only_runtime import (
    ConnectorReadOnlyRuntimeRecord,
    validate_connector_read_only_runtime_record,
)
from ultimate_ai_agent.core.time import utc_now


CONNECTOR_APPROVAL_CAPTURE_DOCS = [
    "docs/connectors/CONNECTOR_APPROVAL_CAPTURE.md",
    "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_NON_GOALS.md",
    "docs/connectors/M126_TO_M127_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorApprovalDecisionKind(str, Enum):
    approve_review_only = "approve_review_only"
    deny_review_only = "deny_review_only"


class ConnectorApprovalCaptureDecisionStatus(str, Enum):
    approved_for_review_only = "approved_for_review_only"
    denied_for_review = "denied_for_review"
    rejected = "rejected"


class _ConnectorApprovalCapture(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorApprovalCaptureRequest(_ConnectorApprovalCapture):
    approval_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    operation_allowlist_refs: list[str]
    redacted_metadata_preview_refs: list[str]
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    decision: ConnectorApprovalDecisionKind
    idempotency_key: str
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    replay_nonce: str | None = None
    used_replay_nonces: list[str] = Field(default_factory=list)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
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
    def validate_shape(self):
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


class ConnectorApprovalCaptureRecord(_ConnectorApprovalCapture):
    approval_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    operation_allowlist_refs: list[str]
    redacted_metadata_preview_refs: list[str]
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    decision: ConnectorApprovalDecisionKind
    status: ConnectorApprovalCaptureDecisionStatus
    idempotency_key: str
    created_at: datetime = Field(default_factory=utc_now)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    review_only: bool = True
    safe_ref_only: bool = True
    approval_captured: bool = True
    approval_persisted: bool = True
    exact_runtime_binding_required: bool = True
    actor_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    replay_safe: bool = True

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _record_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        for refs, field_name in _record_ref_list_pairs(self):
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if self.safe_reason:
            _validate_safe_text(self.safe_reason)
        _validate_safe_payload(self.metadata)
        return self


class ConnectorApprovalCaptureReceiptPlan(_ConnectorApprovalCapture):
    receipt_plan_ref: str
    approval_ref: str
    connector_read_only_runtime_ref: str
    source_messages_connector_contract_review_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    raw_connector_content_stored: bool = False
    full_content_stored: bool = False
    credential_material_stored: bool = False
    connector_export_performed: bool = False
    attachment_download_performed: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = (
        "M126 connector approval capture receipt stores safe refs only and "
        "grants no connector, context, memory, export, or execution authority."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.approval_ref, "approval_ref"),
            (self.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"),
            (
                self.source_messages_connector_contract_review_ref,
                "source_messages_connector_contract_review_ref",
            ),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for field_name in [
            "raw_connector_content_stored",
            "full_content_stored",
            "credential_material_stored",
            "connector_export_performed",
            "attachment_download_performed",
            "context_injection_performed",
            "memory_write_performed",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError("M126_CONNECTOR_APPROVAL_RECEIPT_MUST_BE_NO_EFFECT")
        _validate_safe_text(self.safe_summary)
        return self


class ConnectorApprovalCaptureDecision(_ConnectorApprovalCapture):
    decision_ref: str
    status: ConnectorApprovalCaptureDecisionStatus
    connector_read_only_runtime_ref: str
    approval_ref: str | None = None
    captured: bool = False
    persisted: bool = False
    review_only: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    record: ConnectorApprovalCaptureRecord | None = None
    receipt_plan: ConnectorApprovalCaptureReceiptPlan | None = None
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
    def validate_shape(self):
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(
            self.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"
        )
        if self.approval_ref:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        _validate_safe_text(self.safe_message)
        if not self.review_only:
            raise ValueError("M126_CONNECTOR_APPROVAL_MUST_BE_REVIEW_ONLY")
        for field_name in _DECISION_AUTHORITY_FALSE_FIELDS:
            if getattr(self, field_name):
                raise ValueError("M126_CONNECTOR_APPROVAL_DECISION_GRANTS_AUTHORITY")
        return self


def capture_connector_approval(
    runtime_record: ConnectorReadOnlyRuntimeRecord,
    request: ConnectorApprovalCaptureRequest,
    *,
    current_time: datetime | None = None,
) -> ConnectorApprovalCaptureDecision:
    validated_runtime = validate_connector_read_only_runtime_record(runtime_record)
    reasons = _dedupe(
        _revalidate_capture_request(request, current_time=current_time)
        + _binding_reasons(validated_runtime, request)
    )
    if reasons:
        return _rejected_decision(
            connector_read_only_runtime_ref=getattr(
                request,
                "connector_read_only_runtime_ref",
                validated_runtime.connector_read_only_runtime_ref,
            ),
            approval_ref=getattr(request, "approval_ref", None),
            reasons=reasons,
        )
    record = ConnectorApprovalCaptureRecord(
        approval_ref=request.approval_ref,
        actor_ref=request.actor_ref,
        user_ref=request.user_ref,
        workspace_ref=request.workspace_ref,
        connector_read_only_runtime_ref=request.connector_read_only_runtime_ref,
        source_messages_connector_contract_review_ref=(
            request.source_messages_connector_contract_review_ref
        ),
        source_baseline_ref=request.source_baseline_ref,
        connector_scope_refs=request.connector_scope_refs,
        connector_allowlist_refs=request.connector_allowlist_refs,
        operation_allowlist_refs=request.operation_allowlist_refs,
        redacted_metadata_preview_refs=request.redacted_metadata_preview_refs,
        audit_ref=request.audit_ref,
        replay_ref=request.replay_ref,
        no_effect_receipt_plan_ref=request.no_effect_receipt_plan_ref,
        decision=request.decision,
        status=_status_for_decision(request.decision),
        idempotency_key=request.idempotency_key,
        safe_reason=request.safe_reason,
        metadata_refs=request.metadata_refs,
        metadata=request.metadata,
    )
    return _approved_or_denied_decision(record)


def validate_connector_approval_capture_record(
    record: ConnectorApprovalCaptureRecord,
) -> ConnectorApprovalCaptureRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ConnectorApprovalCaptureRecord):
        raise ValueError("M126_CONNECTOR_APPROVAL_SECRET_METADATA_DENIED")
    for field_name, reason in _M126_DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    if payload.get("raw_connector_content") is not None:
        raise ValueError("M126_RAW_CONNECTOR_CONTENT_DENIED")
    if payload.get("full_connector_content") is not None:
        raise ValueError("M126_FULL_CONTENT_READ_DENIED")
    validated = ConnectorApprovalCaptureRecord.model_validate(payload)
    if not validated.review_only:
        raise ValueError("M126_CONNECTOR_APPROVAL_MUST_BE_REVIEW_ONLY")
    if not validated.safe_ref_only:
        raise ValueError("M126_CONNECTOR_APPROVAL_MUST_BE_SAFE_REF_ONLY")
    for field_name, reason in _M126_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != _status_for_decision(validated.decision):
        raise ValueError("M126_CONNECTOR_APPROVAL_STATUS_DECISION_MISMATCH")
    if str(validated.approval_ref).startswith("approval_test_"):
        raise ValueError("M126_CONNECTOR_APPROVAL_TEST_REF_DENIED")
    _validate_request_like_safe_payload(validated)
    return validated


def validate_connector_approval_capture_request(
    request: ConnectorApprovalCaptureRequest,
) -> ConnectorApprovalCaptureRequest:
    reasons = _revalidate_capture_request(request, current_time=None)
    if reasons:
        raise ValueError(reasons[0])
    return ConnectorApprovalCaptureRequest.model_validate(_model_payload(request))


def _approved_or_denied_decision(
    record: ConnectorApprovalCaptureRecord,
) -> ConnectorApprovalCaptureDecision:
    validated_record = validate_connector_approval_capture_record(record)
    receipt_plan = ConnectorApprovalCaptureReceiptPlan(
        receipt_plan_ref=validated_record.no_effect_receipt_plan_ref,
        approval_ref=validated_record.approval_ref,
        connector_read_only_runtime_ref=(
            validated_record.connector_read_only_runtime_ref
        ),
        source_messages_connector_contract_review_ref=(
            validated_record.source_messages_connector_contract_review_ref
        ),
        actor_ref=validated_record.actor_ref,
        user_ref=validated_record.user_ref,
        workspace_ref=validated_record.workspace_ref,
    )
    reason_code = (
        "M126_CONNECTOR_APPROVAL_CAPTURED_FOR_REVIEW_ONLY"
        if validated_record.decision == ConnectorApprovalDecisionKind.approve_review_only
        else "M126_CONNECTOR_APPROVAL_DENIAL_CAPTURED_FOR_REVIEW_ONLY"
    )
    return ConnectorApprovalCaptureDecision(
        decision_ref=(
            "connector-approval-capture-decision:"
            f"{_safe_suffix(validated_record.connector_read_only_runtime_ref)}"
        ),
        status=validated_record.status,
        connector_read_only_runtime_ref=(
            validated_record.connector_read_only_runtime_ref
        ),
        approval_ref=validated_record.approval_ref,
        captured=True,
        persisted=True,
        reason_codes=[reason_code],
        safe_message=(
            "M126 connector approval capture persisted safe refs only. "
            "Approval refs remain identifiers, not authority."
        ),
        record=validated_record,
        receipt_plan=receipt_plan,
    )


def _rejected_decision(
    *,
    connector_read_only_runtime_ref: str,
    approval_ref: str | None,
    reasons: list[str],
) -> ConnectorApprovalCaptureDecision:
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
        safe_runtime_ref = "connector-read-only-runtime:m126:invalid"
    return ConnectorApprovalCaptureDecision(
        decision_ref=(
            "connector-approval-capture-decision:"
            f"{_safe_suffix(safe_runtime_ref)}"
        ),
        status=ConnectorApprovalCaptureDecisionStatus.rejected,
        connector_read_only_runtime_ref=safe_runtime_ref,
        approval_ref=safe_approval_ref,
        captured=False,
        persisted=False,
        reason_codes=_dedupe(reasons),
        safe_message=(
            "M126 connector approval capture was rejected safely. No connector, "
            "context, memory, export, or execution authority was granted."
        ),
    )


def _revalidate_capture_request(
    request: ConnectorApprovalCaptureRequest,
    *,
    current_time: datetime | None,
) -> list[str]:
    payload = _model_payload(request)
    reasons: list[str] = []
    if _has_secret_like_extra(payload, ConnectorApprovalCaptureRequest):
        reasons.append("M126_CONNECTOR_APPROVAL_SECRET_METADATA_DENIED")
    for field_name, reason in _M126_DENIAL_FIELDS.items():
        if payload.get(field_name):
            reasons.append(reason)
    for value, field_name in _request_ref_pairs(request):
        if value is None:
            if field_name != "replay_nonce":
                reasons.append("M126_CONNECTOR_APPROVAL_REVALIDATION_FAILED")
            continue
        try:
            _validate_m61_ref(value, field_name)
        except ValueError:
            reasons.append("M126_CONNECTOR_APPROVAL_REVALIDATION_FAILED")
    for refs, field_name, required in _request_ref_list_pairs(request):
        if required and not refs:
            reasons.append("M126_CONNECTOR_APPROVAL_SAFE_REF_REQUIRED")
        for ref in refs:
            try:
                _validate_m61_ref(ref, field_name)
            except ValueError:
                reasons.append("M126_CONNECTOR_APPROVAL_REVALIDATION_FAILED")
    if str(getattr(request, "approval_ref", "")).startswith("approval_test_"):
        reasons.append("M126_CONNECTOR_APPROVAL_TEST_REF_DENIED")
    if getattr(request, "revoked_at", None) is not None:
        reasons.append("M126_CONNECTOR_APPROVAL_REVOKED")
    if (
        getattr(request, "expires_at", None) is not None
        and request.expires_at <= (current_time or utc_now())
    ):
        reasons.append("M126_CONNECTOR_APPROVAL_EXPIRED")
    active_replay_nonce = getattr(request, "replay_nonce", None)
    if active_replay_nonce and active_replay_nonce in list(
        getattr(request, "used_replay_nonces", [])
    ):
        reasons.append("M126_CONNECTOR_APPROVAL_REPLAY_DETECTED")
    if getattr(request, "safe_reason", None):
        try:
            _validate_safe_text(request.safe_reason)
        except ValueError:
            reasons.append("M126_CONNECTOR_APPROVAL_SAFE_REASON_DENIED")
    try:
        _validate_safe_payload(getattr(request, "metadata", {}))
    except ValueError:
        reasons.append("M126_CONNECTOR_APPROVAL_SECRET_METADATA_DENIED")
    return _dedupe(reasons)


def _binding_reasons(
    runtime_record: ConnectorReadOnlyRuntimeRecord,
    request: ConnectorApprovalCaptureRequest,
) -> list[str]:
    checks = [
        (
            request.actor_ref,
            runtime_record.actor_ref,
            "M126_CONNECTOR_APPROVAL_ACTOR_MISMATCH",
        ),
        (
            request.user_ref,
            runtime_record.user_ref,
            "M126_CONNECTOR_APPROVAL_USER_MISMATCH",
        ),
        (
            request.workspace_ref,
            runtime_record.workspace_ref,
            "M126_CONNECTOR_APPROVAL_WORKSPACE_MISMATCH",
        ),
        (
            request.connector_read_only_runtime_ref,
            runtime_record.connector_read_only_runtime_ref,
            "M126_CONNECTOR_APPROVAL_RUNTIME_REF_MISMATCH",
        ),
        (
            request.source_messages_connector_contract_review_ref,
            runtime_record.source_messages_connector_contract_review_ref,
            "M126_CONNECTOR_APPROVAL_SOURCE_REVIEW_REF_MISMATCH",
        ),
        (
            request.source_baseline_ref,
            runtime_record.source_baseline_ref,
            "M126_CONNECTOR_APPROVAL_BASELINE_REF_MISMATCH",
        ),
        (
            request.connector_scope_refs,
            runtime_record.connector_scope_refs,
            "M126_CONNECTOR_APPROVAL_SCOPE_REF_MISMATCH",
        ),
        (
            request.connector_allowlist_refs,
            runtime_record.connector_allowlist_refs,
            "M126_CONNECTOR_APPROVAL_ALLOWLIST_REF_MISMATCH",
        ),
        (
            request.operation_allowlist_refs,
            runtime_record.operation_allowlist_refs,
            "M126_CONNECTOR_APPROVAL_OPERATION_REF_MISMATCH",
        ),
        (
            request.redacted_metadata_preview_refs,
            runtime_record.redacted_metadata_preview_refs,
            "M126_CONNECTOR_APPROVAL_METADATA_PREVIEW_REF_MISMATCH",
        ),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _status_for_decision(
    decision: ConnectorApprovalDecisionKind,
) -> ConnectorApprovalCaptureDecisionStatus:
    if decision == ConnectorApprovalDecisionKind.deny_review_only:
        return ConnectorApprovalCaptureDecisionStatus.denied_for_review
    return ConnectorApprovalCaptureDecisionStatus.approved_for_review_only


def _validate_request_like_safe_payload(
    record: ConnectorApprovalCaptureRecord,
) -> None:
    try:
        _validate_safe_payload(record.metadata)
        if record.safe_reason:
            _validate_safe_text(record.safe_reason)
    except ValueError as exc:
        raise ValueError("M126_CONNECTOR_APPROVAL_SECRET_METADATA_DENIED") from exc


def _validate_safe_text(value: str) -> None:
    _validate_safe_payload({"safe_text": value})


def _request_ref_pairs(request: ConnectorApprovalCaptureRequest):
    return [
        (getattr(request, "approval_ref", None), "approval_ref"),
        (getattr(request, "actor_ref", None), "actor_ref"),
        (getattr(request, "user_ref", None), "user_ref"),
        (getattr(request, "workspace_ref", None), "workspace_ref"),
        (
            getattr(request, "connector_read_only_runtime_ref", None),
            "connector_read_only_runtime_ref",
        ),
        (
            getattr(request, "source_messages_connector_contract_review_ref", None),
            "source_messages_connector_contract_review_ref",
        ),
        (getattr(request, "source_baseline_ref", None), "source_baseline_ref"),
        (getattr(request, "audit_ref", None), "audit_ref"),
        (getattr(request, "replay_ref", None), "replay_ref"),
        (
            getattr(request, "no_effect_receipt_plan_ref", None),
            "no_effect_receipt_plan_ref",
        ),
        (getattr(request, "idempotency_key", None), "idempotency_key"),
        (getattr(request, "replay_nonce", None), "replay_nonce"),
    ]


def _request_ref_list_pairs(request: ConnectorApprovalCaptureRequest):
    return [
        (getattr(request, "connector_scope_refs", []), "connector_scope_ref", True),
        (
            getattr(request, "connector_allowlist_refs", []),
            "connector_allowlist_ref",
            True,
        ),
        (
            getattr(request, "operation_allowlist_refs", []),
            "operation_allowlist_ref",
            True,
        ),
        (
            getattr(request, "redacted_metadata_preview_refs", []),
            "redacted_metadata_preview_ref",
            True,
        ),
        (getattr(request, "metadata_refs", []), "metadata_ref", False),
        (getattr(request, "used_replay_nonces", []), "used_replay_nonce", False),
    ]


def _record_ref_pairs(record: ConnectorApprovalCaptureRecord):
    return [
        (record.approval_ref, "approval_ref"),
        (record.actor_ref, "actor_ref"),
        (record.user_ref, "user_ref"),
        (record.workspace_ref, "workspace_ref"),
        (record.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"),
        (
            record.source_messages_connector_contract_review_ref,
            "source_messages_connector_contract_review_ref",
        ),
        (record.source_baseline_ref, "source_baseline_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        (record.idempotency_key, "idempotency_key"),
    ]


def _record_ref_list_pairs(record: ConnectorApprovalCaptureRecord):
    return [
        (record.connector_scope_refs, "connector_scope_ref"),
        (record.connector_allowlist_refs, "connector_allowlist_ref"),
        (record.operation_allowlist_refs, "operation_allowlist_ref"),
        (record.redacted_metadata_preview_refs, "redacted_metadata_preview_ref"),
        (record.metadata_refs, "metadata_ref"),
    ]


def _safe_suffix(ref: str) -> str:
    return ref.replace(":", "-").replace("/", "-")


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


_M126_DENIAL_FIELDS = {
    "live_connector_runtime_enabled": "M126_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M126_ACCOUNT_AUTH_DENIED",
    "network_access_enabled": "M126_NETWORK_ACCESS_DENIED",
    "credential_handling_enabled": "M126_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_enabled": "M126_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_enabled": "M126_FULL_CONTENT_READ_DENIED",
    "connector_write_enabled": "M126_CONNECTOR_WRITE_DENIED",
    "connector_send_enabled": "M126_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M126_CONNECTOR_DELETE_DENIED",
    "connector_export_enabled": "M126_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_enabled": "M126_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_enabled": "M126_ATTACHMENT_DOWNLOAD_DENIED",
    "model_call_enabled": "M126_MODEL_CALL_DENIED",
    "memory_write_enabled": "M126_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M126_CONTEXT_INJECTION_DENIED",
    "execution_enabled": "M126_EXECUTION_DENIED",
    "backend_route_added": "M126_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M126_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M126_DEPENDENCY_DENIED",
}


_M126_RECORD_REQUIRED_TRUE = [
    ("approval_captured", "M126_CONNECTOR_APPROVAL_CAPTURE_REQUIRED"),
    ("approval_persisted", "M126_CONNECTOR_APPROVAL_PERSISTENCE_REQUIRED"),
    ("exact_runtime_binding_required", "M126_CONNECTOR_APPROVAL_RUNTIME_BINDING_REQUIRED"),
    ("actor_bound", "M126_CONNECTOR_APPROVAL_ACTOR_BINDING_REQUIRED"),
    ("user_bound", "M126_CONNECTOR_APPROVAL_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M126_CONNECTOR_APPROVAL_WORKSPACE_BINDING_REQUIRED"),
    ("replay_safe", "M126_CONNECTOR_APPROVAL_REPLAY_REQUIRED"),
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
