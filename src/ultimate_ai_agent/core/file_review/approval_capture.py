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
from ultimate_ai_agent.core.file_review.contracts import FileReviewPacket, file_review_suffix
from ultimate_ai_agent.core.file_review.enums import (
    FileReviewApprovalCaptureDecisionStatus,
    FileReviewApprovalDecisionKind,
)
from ultimate_ai_agent.core.file_review.workflow import evaluate_file_review_packet
from ultimate_ai_agent.core.time import utc_now


FILE_REVIEW_APPROVAL_CAPTURE_ROUTE_REF = "/files/review" + "/approvals" + "/capture"
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_ACTION_REF = (
    "authority-action-ref:file-review-approval-capture"
)
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_LANE_REF = (
    "lane-ref:file-review-approval-capture"
)
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_DOMAIN_REF = "authority-domain-ref:files"
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_CAPABILITY_REF = (
    "authority-capability-ref:write"
)
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED_MODE_REF = (
    "authority-mode-ref:ask-before-changes"
)
FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED_BLOCKED_REF = (
    "blocked-state:file-review-approval-capture-authority-lease-required"
)
FILE_REVIEW_APPROVAL_CAPTURE_SAFE_DISABLE_REF = (
    "safe-disable-ref:file-review-approval-capture:safe-ref-store"
)
FILE_REVIEW_APPROVAL_CAPTURE_ROLLBACK_REF = (
    "rollback-ref:file-review-approval-capture:remove-safe-ref-record"
)


class FileReviewApprovalCaptureRequest(BaseModel):
    approval_ref: str = Field(default_factory=lambda: "file-review-approval-capture:local")
    actor_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    decision: FileReviewApprovalDecisionKind
    idempotency_key: str
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

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_capture_request(self) -> Any:
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.idempotency_key, "idempotency_key"),
        ]:
            validate_action_ref(value, field_name)
        if self.replay_nonce:
            validate_action_ref(self.replay_nonce, "replay_nonce")
        for nonce in self.used_replay_nonces:
            validate_action_ref(nonce, "used_replay_nonce")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        validate_safe_action_payload(self.metadata, "metadata")
        for field_name in _CAPTURE_BLOCKED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(_CAPTURE_BLOCKED_FLAGS[field_name])
        return self


class FileReviewApprovalRecord(BaseModel):
    approval_ref: str
    actor_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    decision: FileReviewApprovalDecisionKind
    status: FileReviewApprovalCaptureDecisionStatus
    idempotency_key: str
    created_at: datetime = Field(default_factory=utc_now)
    safe_reason: str | None = None
    receipt_plan_ref: str | None = None
    authority_decision_ref: str
    authority_decision_outcome: str
    authority_lease_ref: str
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> Any:
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.idempotency_key, "idempotency_key"),
        ]:
            validate_action_ref(value, field_name)
        if self.receipt_plan_ref:
            validate_action_ref(self.receipt_plan_ref, "receipt_plan_ref")
        for value, field_name in [
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.authority_lease_ref, "authority_lease_ref"),
        ]:
            validate_action_ref(value, field_name)
        validate_safe_action_text(
            self.authority_decision_outcome,
            "authority_decision_outcome",
        )
        if self.authority_decision_outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise ValueError("FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED")
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class FileReviewApprovalCaptureReceiptPlan(BaseModel):
    receipt_plan_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    approval_ref: str
    authority_decision_ref: str
    authority_decision_outcome: str
    authority_lease_ref: str
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    raw_absolute_path_stored: bool = False
    context_proposal_created: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = "Review-only approval capture receipt stores safe refs only."

    model_config = ConfigDict(extra="forbid")


class FileReviewApprovalCaptureDecision(BaseModel):
    decision_ref: str
    status: FileReviewApprovalCaptureDecisionStatus
    review_packet_ref: str
    approval_ref: str | None = None
    captured: bool = False
    persisted: bool = False
    review_only: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    record: FileReviewApprovalRecord | None = None
    receipt_plan: FileReviewApprovalCaptureReceiptPlan | None = None
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    raw_file_access_authorized: bool = False
    context_proposal_authorized: bool = False
    context_injection_authorized: bool = False
    memory_write_authorized: bool = False
    export_authorized: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        validate_action_ref(self.decision_ref, "decision_ref")
        validate_action_ref(self.review_packet_ref, "review_packet_ref")
        if self.approval_ref:
            validate_action_ref(self.approval_ref, "approval_ref")
        for value, field_name in [
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.authority_lease_ref, "authority_lease_ref"),
        ]:
            if value:
                validate_action_ref(value, field_name)
        if self.authority_decision_outcome is not None:
            validate_safe_action_text(
                self.authority_decision_outcome,
                "authority_decision_outcome",
            )
            if self.authority_decision_outcome not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
                AuthorityDecisionOutcome.deny.value,
                AuthorityDecisionOutcome.degrade_to_draft.value,
            }:
                raise ValueError("FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_OUTCOME_INVALID")
        if self.captured and (
            self.authority_decision_ref is None
            or self.authority_decision_outcome not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }
            or self.authority_lease_ref is None
        ):
            raise ValueError("FILE_REVIEW_APPROVAL_CAPTURE_REQUIRES_AUTHORITY_PROOF")
        validate_safe_action_text(self.safe_message, "safe_message")
        if not self.review_only:
            raise ValueError("FILE_REVIEW_APPROVAL_CAPTURE_MUST_BE_REVIEW_ONLY")
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
                raise ValueError(f"{field_name} must be False in M37")
        return self


def active_file_review_authority_leases() -> list[AuthorityLease]:
    active = AuthorityLeaseStore().list_leases(active_only=True)
    return active or build_default_authority_leases()


class FileReviewApprovalStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: dict[str, FileReviewApprovalRecord] = {}

    def persist(self, record: FileReviewApprovalRecord) -> FileReviewApprovalCaptureDecision:
        reasons = _revalidate_record_for_persistence(record)
        if reasons:
            return _capture_rejected(
                review_packet_ref=getattr(record, "review_packet_ref", "file-review-packet:invalid"),
                approval_ref=getattr(record, "approval_ref", None),
                reasons=reasons,
            )

        active_record = FileReviewApprovalRecord.model_validate(record.model_dump())
        existing = self._records.get(active_record.idempotency_key)
        if existing is not None:
            if _record_fingerprint(existing) == _record_fingerprint(active_record):
                return _capture_decision(
                    active_record,
                    reason_codes=["FILE_REVIEW_APPROVAL_CAPTURE_IDEMPOTENT_REPLAY"],
                    persisted=True,
                )
            return _capture_rejected(
                review_packet_ref=active_record.review_packet_ref,
                approval_ref=active_record.approval_ref,
                reasons=["FILE_REVIEW_APPROVAL_CAPTURE_REPLAY_MISMATCH"],
            )

        self._records[active_record.idempotency_key] = active_record
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(active_record.model_dump(mode="json"), sort_keys=True) + "\n")
        return _capture_decision(
            active_record,
            reason_codes=["FILE_REVIEW_APPROVAL_CAPTURED_FOR_REVIEW_ONLY"],
            persisted=True,
        )


def capture_file_review_approval(
    packet: FileReviewPacket,
    request: FileReviewApprovalCaptureRequest,
    *,
    store: FileReviewApprovalStore | None = None,
    current_time: datetime | None = None,
    active_authority_leases: list[AuthorityLease] | None = None,
) -> FileReviewApprovalCaptureDecision:
    reasons = []
    packet_decision = evaluate_file_review_packet(packet)
    if not packet_decision.packet_valid_for_review:
        reasons.extend(packet_decision.reason_codes)
    reasons.extend(_revalidate_capture_request(request, current_time=current_time))
    reasons.extend(_binding_reasons(packet, request))
    reasons = _dedupe(reasons)
    if reasons:
        return _capture_rejected(
            review_packet_ref=getattr(request, "review_packet_ref", getattr(packet, "review_packet_ref", "file-review-packet:invalid")),
            approval_ref=getattr(request, "approval_ref", None),
            reasons=reasons,
        )
    return capture_file_review_approval_request(
        request,
        store=store,
        active_authority_leases=active_authority_leases,
    )


def capture_file_review_approval_request(
    request: FileReviewApprovalCaptureRequest,
    *,
    store: FileReviewApprovalStore | None = None,
    current_time: datetime | None = None,
    active_authority_leases: list[AuthorityLease] | None = None,
) -> FileReviewApprovalCaptureDecision:
    reasons = _revalidate_capture_request(request, current_time=current_time)
    reasons = _dedupe(reasons)
    if reasons:
        return _capture_rejected(request.review_packet_ref, request.approval_ref, reasons)
    authority_decision = _file_review_capture_authority_decision(
        request,
        active_authority_leases=active_authority_leases,
    )
    if authority_decision.outcome not in {
        AuthorityDecisionOutcome.allow.value,
        AuthorityDecisionOutcome.ask.value,
    }:
        return _capture_rejected(
            request.review_packet_ref,
            request.approval_ref,
            [
                *authority_decision.reason_refs,
                FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED_BLOCKED_REF,
                "FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_DENIED",
            ],
            authority_decision=authority_decision,
        )

    record = FileReviewApprovalRecord(
        approval_ref=request.approval_ref,
        actor_ref=request.actor_ref,
        review_packet_ref=request.review_packet_ref,
        preview_result_ref=request.preview_result_ref,
        redaction_summary_ref=request.redaction_summary_ref,
        file_ref=request.file_ref,
        safe_path_ref=request.safe_path_ref,
        decision=request.decision,
        status=_record_status_for_decision(request.decision),
        idempotency_key=request.idempotency_key,
        safe_reason=request.safe_reason,
        receipt_plan_ref=f"file-review-approval-capture-receipt:{file_review_suffix(request.review_packet_ref)}",
        authority_decision_ref=authority_decision.decision_ref,
        authority_decision_outcome=authority_decision.outcome,
        authority_lease_ref=str(authority_decision.lease_ref),
        metadata_refs=request.metadata_refs,
        metadata=request.metadata,
    )
    active_store = store or FileReviewApprovalStore()
    return active_store.persist(record)


def _record_status_for_decision(decision: FileReviewApprovalDecisionKind) -> FileReviewApprovalCaptureDecisionStatus:
    if decision == FileReviewApprovalDecisionKind.deny_review_only:
        return FileReviewApprovalCaptureDecisionStatus.denied_for_review
    return FileReviewApprovalCaptureDecisionStatus.approved_for_review_only


def _capture_decision(
    record: FileReviewApprovalRecord,
    *,
    reason_codes: list[str],
    persisted: bool,
) -> FileReviewApprovalCaptureDecision:
    receipt_plan = FileReviewApprovalCaptureReceiptPlan(
        receipt_plan_ref=record.receipt_plan_ref or f"file-review-approval-capture-receipt:{file_review_suffix(record.review_packet_ref)}",
        review_packet_ref=record.review_packet_ref,
        preview_result_ref=record.preview_result_ref,
        redaction_summary_ref=record.redaction_summary_ref,
        approval_ref=record.approval_ref,
        authority_decision_ref=record.authority_decision_ref,
        authority_decision_outcome=record.authority_decision_outcome,
        authority_lease_ref=record.authority_lease_ref,
        safe_summary=(
            "AuthorityLease-governed review-only approval capture stores safe "
            "refs only; it grants no raw file, context, memory, export, or "
            "execution authority."
        ),
    )
    return FileReviewApprovalCaptureDecision(
        decision_ref=f"file-review-approval-capture-decision:{file_review_suffix(record.review_packet_ref)}",
        status=record.status,
        review_packet_ref=record.review_packet_ref,
        approval_ref=record.approval_ref,
        captured=True,
        persisted=persisted,
        reason_codes=reason_codes,
        safe_message=(
            "Review-only file approval capture persisted safe refs only. No raw "
            "file, context, memory, export, or execution authority was granted."
        ),
        record=record,
        receipt_plan=receipt_plan,
        authority_decision_ref=record.authority_decision_ref,
        authority_decision_outcome=record.authority_decision_outcome,
        authority_lease_ref=record.authority_lease_ref,
    )


def _capture_rejected(
    review_packet_ref: str,
    approval_ref: str | None,
    reasons: list[str],
    *,
    authority_decision: Any | None = None,
) -> FileReviewApprovalCaptureDecision:
    safe_approval_ref = approval_ref
    if safe_approval_ref is not None:
        try:
            validate_action_ref(safe_approval_ref, "approval_ref")
        except ValueError:
            safe_approval_ref = None
    return FileReviewApprovalCaptureDecision(
        decision_ref=f"file-review-approval-capture-decision:{file_review_suffix(review_packet_ref)}",
        status=FileReviewApprovalCaptureDecisionStatus.rejected,
        review_packet_ref=review_packet_ref,
        approval_ref=safe_approval_ref,
        captured=False,
        persisted=False,
        reason_codes=_dedupe(reasons),
        safe_message="File review approval capture was rejected safely. No raw access, context, memory, export, or execution authority was granted.",
        authority_decision_ref=(
            getattr(authority_decision, "decision_ref", None)
            if authority_decision is not None
            else None
        ),
        authority_decision_outcome=(
            getattr(authority_decision, "outcome", None)
            if authority_decision is not None
            else None
        ),
        authority_lease_ref=(
            getattr(authority_decision, "lease_ref", None)
            if getattr(authority_decision, "lease_ref", None)
            else None
        ),
    )


def _file_review_capture_authority_decision(
    request: FileReviewApprovalCaptureRequest,
    *,
    active_authority_leases: list[AuthorityLease] | None,
):
    leases = (
        active_authority_leases
        if active_authority_leases is not None
        else active_file_review_authority_leases()
    )
    return evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_ACTION_REF,
            domain=AuthorityDomain.files,
            capability=AuthorityCapability.write,
            safe_summary=(
                "Evaluate Files write authority for review-only file approval "
                "capture safe-ref persistence."
            ),
            resource_refs=list(
                dict.fromkeys(
                    [
                        request.review_packet_ref,
                        request.preview_result_ref,
                        request.redaction_summary_ref,
                        request.file_ref,
                        request.safe_path_ref,
                        request.approval_ref,
                        request.idempotency_key,
                        f"file-review-decision-kind:{request.decision.value}",
                    ]
                )
            ),
            route_ref=FILE_REVIEW_APPROVAL_CAPTURE_ROUTE_REF,
            lane_ref=FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_LANE_REF,
            requested_mode=TrustMode.ask_before_changes,
            rollback_ref=FILE_REVIEW_APPROVAL_CAPTURE_ROLLBACK_REF,
            safe_disable_ref=FILE_REVIEW_APPROVAL_CAPTURE_SAFE_DISABLE_REF,
        ),
        leases,
    )


def _revalidate_capture_request(
    request: FileReviewApprovalCaptureRequest,
    *,
    current_time: datetime | None = None,
) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(request, "approval_ref", None), "approval_ref"),
        (getattr(request, "actor_ref", None), "actor_ref"),
        (getattr(request, "review_packet_ref", None), "review_packet_ref"),
        (getattr(request, "preview_result_ref", None), "preview_result_ref"),
        (getattr(request, "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(request, "file_ref", None), "file_ref"),
        (getattr(request, "safe_path_ref", None), "safe_path_ref"),
        (getattr(request, "idempotency_key", None), "idempotency_key"),
        (getattr(request, "replay_nonce", None), "replay_nonce"),
    ]:
        if value is None:
            if field_name != "replay_nonce":
                reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED")
            continue
        reasons.extend(_validate_ref_reason(value, field_name, "FILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED"))
    if str(getattr(request, "approval_ref", "")).startswith("approval_test_"):
        reasons.append("FILE_REVIEW_APPROVAL_TEST_REF_DENIED")
    if getattr(request, "revoked_at", None) is not None:
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_REVOKED")
    if getattr(request, "expires_at", None) is not None and request.expires_at <= (current_time or utc_now()):
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_EXPIRED")
    active_replay_nonce = getattr(request, "replay_nonce", None)
    if active_replay_nonce and active_replay_nonce in list(getattr(request, "used_replay_nonces", [])):
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_REPLAY_DETECTED")
    if getattr(request, "safe_reason", None):
        reasons.extend(_validate_safe_text_reason(request.safe_reason, "safe_reason", "FILE_REVIEW_APPROVAL_CAPTURE_SAFE_REASON_DENIED"))
    for ref in list(getattr(request, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref", "FILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED"))
    reasons.extend(_validate_payload_reason(getattr(request, "metadata", {}), "metadata", "FILE_REVIEW_APPROVAL_CAPTURE_SECRET_METADATA_DENIED"))
    if _looks_like_raw_path(str(getattr(request, "safe_path_ref", ""))):
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED")
    for field_name, reason in _CAPTURE_BLOCKED_FLAGS.items():
        if bool(getattr(request, field_name, False)):
            reasons.append(reason)
    for extra_key in _extra_keys(request):
        if extra_key in _EXTRA_CAPTURE_FIELD_REASONS:
            reasons.append(_EXTRA_CAPTURE_FIELD_REASONS[extra_key])
    return _dedupe(reasons)


def _revalidate_record_for_persistence(record: FileReviewApprovalRecord) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(record, "authority_decision_ref", None), "authority_decision_ref"),
        (getattr(record, "authority_lease_ref", None), "authority_lease_ref"),
    ]:
        if value is None:
            reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED")
        else:
            reasons.extend(
                _validate_ref_reason(
                    value,
                    field_name,
                    "FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED",
                )
            )
    authority_outcome = getattr(record, "authority_decision_outcome", None)
    if authority_outcome not in {
        AuthorityDecisionOutcome.allow.value,
        AuthorityDecisionOutcome.ask.value,
    }:
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_REQUIRED")
    for field_name, reason in _EXTRA_CAPTURE_FIELD_REASONS.items():
        if field_name in _extra_keys(record) or getattr(record, field_name, None) is not None:
            reasons.append(reason)
    reasons.extend(_validate_payload_reason(getattr(record, "metadata", {}), "metadata", "FILE_REVIEW_APPROVAL_CAPTURE_SECRET_METADATA_DENIED"))
    if _looks_like_raw_path(str(getattr(record, "safe_path_ref", ""))):
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED")
    for ref in list(getattr(record, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref", "FILE_REVIEW_APPROVAL_CAPTURE_REVALIDATION_FAILED"))
    return _dedupe(reasons)


def _binding_reasons(packet: FileReviewPacket, request: FileReviewApprovalCaptureRequest) -> list[str]:
    checks = [
        (getattr(request, "actor_ref", None), packet.source.actor_ref, "FILE_REVIEW_APPROVAL_CAPTURE_ACTOR_MISMATCH"),
        (getattr(request, "review_packet_ref", None), packet.review_packet_ref, "FILE_REVIEW_APPROVAL_CAPTURE_PACKET_MISMATCH"),
        (getattr(request, "preview_result_ref", None), packet.source.preview_result_ref, "FILE_REVIEW_APPROVAL_CAPTURE_PREVIEW_RESULT_MISMATCH"),
        (
            getattr(request, "redaction_summary_ref", None),
            packet.redaction_verification.redaction_summary_ref,
            "FILE_REVIEW_APPROVAL_CAPTURE_REDACTION_SUMMARY_MISMATCH",
        ),
        (getattr(request, "file_ref", None), packet.source.file_ref, "FILE_REVIEW_APPROVAL_CAPTURE_FILE_REF_MISMATCH"),
        (getattr(request, "safe_path_ref", None), packet.source.safe_path_ref, "FILE_REVIEW_APPROVAL_CAPTURE_PATH_REF_MISMATCH"),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _record_fingerprint(record: FileReviewApprovalRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    data.pop("created_at", None)
    return data


def _validate_ref_reason(value: str, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_safe_text_reason(value: str, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_text(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_payload_reason(value: str, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _extra_keys(model: BaseModel) -> set[str]:
    return set(getattr(model, "__dict__", {})) - set(getattr(type(model), "model_fields", {}))


def _looks_like_raw_path(value: str) -> bool:
    return value.startswith(("/Users/", "/home/", "/var/", "/etc/")) or ":\\" in value


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


_CAPTURE_BLOCKED_FLAGS = {
    "raw_file_access_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_RAW_ACCESS_DENIED",
    "raw_content_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED",
    "full_file_content_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED",
    "context_proposal_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_PROPOSAL_DENIED",
    "context_injection_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_INJECTION_DENIED",
    "memory_write_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_MEMORY_WRITE_DENIED",
    "export_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_EXPORT_DENIED",
    "execution_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_EXECUTION_DENIED",
}

_EXTRA_CAPTURE_FIELD_REASONS = {
    "raw_content": "FILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED",
    "full_file_content": "FILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview": "FILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED",
    "raw_absolute_path": "FILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED",
    "absolute_path": "FILE_REVIEW_APPROVAL_CAPTURE_RAW_PATH_DENIED",
}
