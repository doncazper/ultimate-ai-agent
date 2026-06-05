from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.mobile_companion.enums import (
    MobileReviewApprovalCaptureDecisionStatus,
    MobileReviewApprovalDecisionKind,
)
from ultimate_ai_agent.core.time import utc_now


class MobileReviewApprovalCaptureRequest(BaseModel):
    approval_ref: str = Field(default_factory=lambda: "mobile-review-approval-capture:local")
    actor_ref: str
    mobile_surface_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    receipt_plan_ref: str
    decision: MobileReviewApprovalDecisionKind
    idempotency_key: str
    expected_actor_ref: str
    expected_mobile_surface_ref: str
    expected_review_packet_ref: str
    expected_preview_result_ref: str
    expected_redaction_summary_ref: str
    expected_file_ref: str
    expected_safe_path_ref: str
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    replay_nonce: str | None = None
    used_replay_nonces: list[str] = Field(default_factory=list)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_file_access_enabled: bool = False
    raw_content_enabled: bool = False
    full_file_content_enabled: bool = False
    unredacted_preview_enabled: bool = False
    context_proposal_enabled: bool = False
    context_injection_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    approval_execution_enabled: bool = False
    mobile_sensor_access_enabled: bool = False
    background_collection_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_capture_request(self):
        for value, field_name in _request_ref_pairs(self):
            if value is not None:
                validate_action_ref(value, field_name)
        for nonce in self.used_replay_nonces:
            validate_action_ref(nonce, "used_replay_nonce")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        validate_safe_action_payload(self.metadata, "metadata")
        for field_name, reason in _CAPTURE_BLOCKED_FLAGS.items():
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MobileReviewApprovalRecord(BaseModel):
    approval_ref: str
    actor_ref: str
    mobile_surface_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    receipt_plan_ref: str
    decision: MobileReviewApprovalDecisionKind
    status: MobileReviewApprovalCaptureDecisionStatus
    idempotency_key: str
    created_at: datetime = Field(default_factory=utc_now)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self):
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.mobile_surface_ref, "mobile_surface_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.idempotency_key, "idempotency_key"),
        ]:
            validate_action_ref(value, field_name)
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class MobileReviewApprovalCaptureReceiptPlan(BaseModel):
    receipt_plan_ref: str
    approval_ref: str
    mobile_surface_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    raw_absolute_path_stored: bool = False
    context_proposal_created: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = "Mobile review-only approval capture receipt stores safe refs only."

    model_config = ConfigDict(extra="forbid")


class MobileReviewApprovalCaptureDecision(BaseModel):
    decision_ref: str
    status: MobileReviewApprovalCaptureDecisionStatus
    review_packet_ref: str
    approval_ref: str | None = None
    captured: bool = False
    persisted: bool = False
    review_only: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    record: MobileReviewApprovalRecord | None = None
    receipt_plan: MobileReviewApprovalCaptureReceiptPlan | None = None
    raw_file_access_authorized: bool = False
    context_proposal_authorized: bool = False
    context_injection_authorized: bool = False
    memory_write_authorized: bool = False
    export_authorized: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self):
        validate_action_ref(self.decision_ref, "decision_ref")
        validate_action_ref(self.review_packet_ref, "review_packet_ref")
        if self.approval_ref:
            validate_action_ref(self.approval_ref, "approval_ref")
        validate_safe_action_text(self.safe_message, "safe_message")
        if not self.review_only:
            raise ValueError("MOBILE_REVIEW_APPROVAL_CAPTURE_MUST_BE_REVIEW_ONLY")
        for field_name in [
            "raw_file_access_authorized",
            "context_proposal_authorized",
            "context_injection_authorized",
            "memory_write_authorized",
            "export_authorized",
            "execution_authorized",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M49")
        return self


class MobileReviewApprovalStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else None
        self._records: dict[str, MobileReviewApprovalRecord] = {}

    def persist(self, record: MobileReviewApprovalRecord) -> MobileReviewApprovalCaptureDecision:
        reasons = _revalidate_record_for_persistence(record)
        if reasons:
            return _capture_rejected(
                review_packet_ref=getattr(record, "review_packet_ref", "mobile-review-packet:invalid"),
                approval_ref=getattr(record, "approval_ref", None),
                reasons=reasons,
            )

        active_record = MobileReviewApprovalRecord.model_validate(record.model_dump())
        existing = self._records.get(active_record.idempotency_key)
        if existing is not None:
            if _record_fingerprint(existing) == _record_fingerprint(active_record):
                return _capture_decision(
                    active_record,
                    reason_codes=["MOBILE_REVIEW_APPROVAL_CAPTURE_IDEMPOTENT_REPLAY"],
                    persisted=True,
                )
            return _capture_rejected(
                review_packet_ref=active_record.review_packet_ref,
                approval_ref=active_record.approval_ref,
                reasons=["MOBILE_REVIEW_APPROVAL_CAPTURE_REPLAY_MISMATCH"],
            )

        self._records[active_record.idempotency_key] = active_record
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(active_record.model_dump(mode="json"), sort_keys=True) + "\n")
        return _capture_decision(
            active_record,
            reason_codes=["MOBILE_REVIEW_APPROVAL_CAPTURED_FOR_REVIEW_ONLY"],
            persisted=True,
        )


def capture_mobile_review_approval(
    request: MobileReviewApprovalCaptureRequest,
    *,
    store: MobileReviewApprovalStore | None = None,
    current_time: datetime | None = None,
) -> MobileReviewApprovalCaptureDecision:
    reasons = _dedupe(
        _revalidate_capture_request(request, current_time=current_time)
        + _binding_reasons(request)
    )
    if reasons:
        return _capture_rejected(request.review_packet_ref, request.approval_ref, reasons)

    record = MobileReviewApprovalRecord(
        approval_ref=request.approval_ref,
        actor_ref=request.actor_ref,
        mobile_surface_ref=request.mobile_surface_ref,
        review_packet_ref=request.review_packet_ref,
        preview_result_ref=request.preview_result_ref,
        redaction_summary_ref=request.redaction_summary_ref,
        file_ref=request.file_ref,
        safe_path_ref=request.safe_path_ref,
        receipt_plan_ref=request.receipt_plan_ref,
        decision=request.decision,
        status=_record_status_for_decision(request.decision),
        idempotency_key=request.idempotency_key,
        safe_reason=request.safe_reason,
        metadata_refs=request.metadata_refs,
        metadata=request.metadata,
    )
    active_store = store or MobileReviewApprovalStore()
    return active_store.persist(record)


def _record_status_for_decision(
    decision: MobileReviewApprovalDecisionKind,
) -> MobileReviewApprovalCaptureDecisionStatus:
    if decision == MobileReviewApprovalDecisionKind.deny_review_only:
        return MobileReviewApprovalCaptureDecisionStatus.denied_for_mobile_review
    return MobileReviewApprovalCaptureDecisionStatus.approved_for_mobile_review_only


def _capture_decision(
    record: MobileReviewApprovalRecord,
    *,
    reason_codes: list[str],
    persisted: bool,
) -> MobileReviewApprovalCaptureDecision:
    receipt_plan = MobileReviewApprovalCaptureReceiptPlan(
        receipt_plan_ref=record.receipt_plan_ref,
        approval_ref=record.approval_ref,
        mobile_surface_ref=record.mobile_surface_ref,
        review_packet_ref=record.review_packet_ref,
        preview_result_ref=record.preview_result_ref,
        redaction_summary_ref=record.redaction_summary_ref,
    )
    return MobileReviewApprovalCaptureDecision(
        decision_ref=f"mobile-review-approval-capture-decision:{_safe_suffix(record.review_packet_ref)}",
        status=record.status,
        review_packet_ref=record.review_packet_ref,
        approval_ref=record.approval_ref,
        captured=True,
        persisted=persisted,
        reason_codes=reason_codes,
        safe_message="Review-only mobile approval capture persisted safe refs only. No authority was granted.",
        record=record,
        receipt_plan=receipt_plan,
    )


def _capture_rejected(
    review_packet_ref: str,
    approval_ref: str | None,
    reasons: list[str],
) -> MobileReviewApprovalCaptureDecision:
    safe_approval_ref = approval_ref
    if safe_approval_ref is not None:
        try:
            validate_action_ref(safe_approval_ref, "approval_ref")
        except ValueError:
            safe_approval_ref = None
    return MobileReviewApprovalCaptureDecision(
        decision_ref=f"mobile-review-approval-capture-decision:{_safe_suffix(review_packet_ref)}",
        status=MobileReviewApprovalCaptureDecisionStatus.rejected,
        review_packet_ref=review_packet_ref,
        approval_ref=safe_approval_ref,
        captured=False,
        persisted=False,
        reason_codes=_dedupe(reasons),
        safe_message="Mobile review approval capture was rejected safely. No raw access, context, memory, export, or execution authority was granted.",
    )


def _revalidate_capture_request(
    request: MobileReviewApprovalCaptureRequest,
    *,
    current_time: datetime | None = None,
) -> list[str]:
    reasons: list[str] = []
    for value, field_name in _request_ref_pairs(request):
        if value is None:
            if field_name != "replay_nonce":
                reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED")
            continue
        reasons.extend(_validate_ref_reason(value, field_name))
    if str(getattr(request, "approval_ref", "")).startswith("approval_test_"):
        reasons.append("MOBILE_REVIEW_APPROVAL_TEST_REF_DENIED")
    if getattr(request, "revoked_at", None) is not None:
        reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_REVOKED")
    if getattr(request, "expires_at", None) is not None and request.expires_at <= (current_time or utc_now()):
        reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_EXPIRED")
    active_replay_nonce = getattr(request, "replay_nonce", None)
    if active_replay_nonce and active_replay_nonce in list(getattr(request, "used_replay_nonces", [])):
        reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_REPLAY_DETECTED")
    if getattr(request, "safe_reason", None):
        reasons.extend(_validate_safe_text_reason(request.safe_reason, "safe_reason"))
    for ref in list(getattr(request, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref"))
    reasons.extend(_validate_payload_reason(getattr(request, "metadata", {}), "metadata"))
    if _looks_like_raw_path(str(getattr(request, "safe_path_ref", ""))):
        reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED")
    for field_name, reason in _CAPTURE_BLOCKED_FLAGS.items():
        if bool(getattr(request, field_name, False)):
            reasons.append(reason)
    for extra_key in _extra_keys(request):
        if extra_key in _EXTRA_CAPTURE_FIELD_REASONS:
            reasons.append(_EXTRA_CAPTURE_FIELD_REASONS[extra_key])
    return _dedupe(reasons)


def _revalidate_record_for_persistence(record: MobileReviewApprovalRecord) -> list[str]:
    reasons: list[str] = []
    for field_name, reason in _EXTRA_CAPTURE_FIELD_REASONS.items():
        if field_name in _extra_keys(record) or getattr(record, field_name, None) is not None:
            reasons.append(reason)
    reasons.extend(_validate_payload_reason(getattr(record, "metadata", {}), "metadata"))
    if _looks_like_raw_path(str(getattr(record, "safe_path_ref", ""))):
        reasons.append("MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED")
    for ref in list(getattr(record, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref"))
    return _dedupe(reasons)


def _binding_reasons(request: MobileReviewApprovalCaptureRequest) -> list[str]:
    checks = [
        (request.actor_ref, request.expected_actor_ref, "MOBILE_REVIEW_APPROVAL_CAPTURE_ACTOR_MISMATCH"),
        (
            request.mobile_surface_ref,
            request.expected_mobile_surface_ref,
            "MOBILE_REVIEW_APPROVAL_CAPTURE_SURFACE_MISMATCH",
        ),
        (
            request.review_packet_ref,
            request.expected_review_packet_ref,
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PACKET_MISMATCH",
        ),
        (
            request.preview_result_ref,
            request.expected_preview_result_ref,
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PREVIEW_RESULT_MISMATCH",
        ),
        (
            request.redaction_summary_ref,
            request.expected_redaction_summary_ref,
            "MOBILE_REVIEW_APPROVAL_CAPTURE_REDACTION_SUMMARY_MISMATCH",
        ),
        (request.file_ref, request.expected_file_ref, "MOBILE_REVIEW_APPROVAL_CAPTURE_FILE_REF_MISMATCH"),
        (
            request.safe_path_ref,
            request.expected_safe_path_ref,
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PATH_REF_MISMATCH",
        ),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _request_ref_pairs(request: MobileReviewApprovalCaptureRequest):
    return [
        (getattr(request, "approval_ref", None), "approval_ref"),
        (getattr(request, "actor_ref", None), "actor_ref"),
        (getattr(request, "mobile_surface_ref", None), "mobile_surface_ref"),
        (getattr(request, "review_packet_ref", None), "review_packet_ref"),
        (getattr(request, "preview_result_ref", None), "preview_result_ref"),
        (getattr(request, "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(request, "file_ref", None), "file_ref"),
        (getattr(request, "safe_path_ref", None), "safe_path_ref"),
        (getattr(request, "receipt_plan_ref", None), "receipt_plan_ref"),
        (getattr(request, "idempotency_key", None), "idempotency_key"),
        (getattr(request, "expected_actor_ref", None), "expected_actor_ref"),
        (getattr(request, "expected_mobile_surface_ref", None), "expected_mobile_surface_ref"),
        (getattr(request, "expected_review_packet_ref", None), "expected_review_packet_ref"),
        (getattr(request, "expected_preview_result_ref", None), "expected_preview_result_ref"),
        (getattr(request, "expected_redaction_summary_ref", None), "expected_redaction_summary_ref"),
        (getattr(request, "expected_file_ref", None), "expected_file_ref"),
        (getattr(request, "expected_safe_path_ref", None), "expected_safe_path_ref"),
        (getattr(request, "replay_nonce", None), "replay_nonce"),
    ]


def _record_fingerprint(record: MobileReviewApprovalRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    data.pop("created_at", None)
    return data


def _validate_ref_reason(value: str, field_name: str) -> list[str]:
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return ["MOBILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED"]
    return []


def _validate_safe_text_reason(value: str, field_name: str) -> list[str]:
    try:
        validate_safe_action_text(value, field_name)
    except ValueError:
        return ["MOBILE_REVIEW_APPROVAL_CAPTURE_SAFE_REASON_DENIED"]
    return []


def _validate_payload_reason(value, field_name: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return ["MOBILE_REVIEW_APPROVAL_CAPTURE_SECRET_METADATA_DENIED"]
    return []


def _extra_keys(model: BaseModel) -> set[str]:
    return set(getattr(model, "__dict__", {})) - set(getattr(type(model), "model_fields", {}))


def _looks_like_raw_path(value: str) -> bool:
    return value.startswith(("/Users/", "/home/", "/var/", "/etc/")) or ":\\" in value


def _safe_suffix(ref: str) -> str:
    return ref.rsplit(":", maxsplit=1)[-1] if ":" in ref else "invalid"


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


_CAPTURE_BLOCKED_FLAGS = {
    "raw_file_access_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_ACCESS_DENIED",
    "raw_content_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED",
    "full_file_content_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED",
    "context_proposal_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_PROPOSAL_DENIED",
    "context_injection_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_INJECTION_DENIED",
    "memory_write_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_MEMORY_WRITE_DENIED",
    "export_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_EXPORT_DENIED",
    "execution_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_EXECUTION_DENIED",
    "approval_execution_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_APPROVAL_EXECUTION_DENIED",
    "mobile_sensor_access_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_SENSOR_DENIED",
    "background_collection_enabled": "MOBILE_REVIEW_APPROVAL_CAPTURE_BACKGROUND_DENIED",
}

_EXTRA_CAPTURE_FIELD_REASONS = {
    "raw_content": "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED",
    "full_file_content": "MOBILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview": "MOBILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED",
    "raw_absolute_path": "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED",
    "absolute_path": "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED",
    "context_payload": "MOBILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_PROPOSAL_DENIED",
    "memory_payload": "MOBILE_REVIEW_APPROVAL_CAPTURE_MEMORY_WRITE_DENIED",
    "export_payload": "MOBILE_REVIEW_APPROVAL_CAPTURE_EXPORT_DENIED",
    "execution_payload": "MOBILE_REVIEW_APPROVAL_CAPTURE_EXECUTION_DENIED",
}
