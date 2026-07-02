from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.run_storage import (
    AppendFirstRunStorage,
    DurableRunStorageEntryKind,
)
from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    validate_execution_ref,
    validate_safe_execution_text,
)


CONNECTOR_DELIVERY_ENVELOPE_SCHEMA_VERSION = "connector_delivery_envelope_contract.v1"
CONNECTOR_DELIVERY_EVENT_SCHEMA_VERSION = "connector_delivery_event_contract.v1"
CONNECTOR_DELIVERY_EVENT_RECEIPT_SCHEMA_VERSION = "connector_delivery_event_receipt.v1"
CONNECTOR_DELIVERY_READ_MODEL_SCHEMA_VERSION = "connector_delivery_read_model.v1"
CONNECTOR_DELIVERY_REVIEW_QUEUE_ITEM_SCHEMA_VERSION = "connector_delivery_review_queue_item.v1"
CONNECTOR_DELIVERY_REVIEW_QUEUE_SCHEMA_VERSION = "connector_delivery_review_queue.v1"
CONNECTOR_DELIVERY_STATUS_SCHEMA_VERSION = "connector_delivery_status_read_model.v1"
CONNECTOR_DELIVERY_VALIDATION_SCHEMA_VERSION = "connector_delivery_validation_decision.v1"
CONNECTOR_DELIVERY_SOURCE_FREEZE_REF = "connector-safety-freeze:m130"

ConnectorDeliveryState = Literal[
    "draft_created_metadata_only",
    "pending_approval",
    "approval_denied",
    "delivery_blocked",
    "delivery_ready_not_sent",
    "retry_scheduled_metadata_only",
    "failed_metadata_only",
    "canceled_metadata_only",
    "sent_not_supported",
]

ConnectorDeliveryValidationStatus = Literal[
    "valid_contract_only",
    "blocked",
    "approval_required",
    "validation_failed",
]

ConnectorDeliveryApprovalState = Literal[
    "not_validated",
    "requested",
    "approved_metadata_only",
    "denied",
    "expired",
    "revoked",
    "blocked",
]

CONNECTOR_DELIVERY_STATES: tuple[ConnectorDeliveryState, ...] = (
    "draft_created_metadata_only",
    "pending_approval",
    "approval_denied",
    "delivery_blocked",
    "delivery_ready_not_sent",
    "retry_scheduled_metadata_only",
    "failed_metadata_only",
    "canceled_metadata_only",
    "sent_not_supported",
)

PENDING_CONNECTOR_DELIVERY_STATES = {"pending_approval", "delivery_ready_not_sent"}
BLOCKED_CONNECTOR_DELIVERY_STATES = {"approval_denied", "delivery_blocked", "sent_not_supported"}
RETRY_CONNECTOR_DELIVERY_STATES = {"retry_scheduled_metadata_only"}
FAILURE_CONNECTOR_DELIVERY_STATES = {"failed_metadata_only", "canceled_metadata_only"}

_RAW_DELIVERY_FIELD_RE = re.compile(
    r"(?i)(^|[_-])("
    r"raw|message[_-]?body|body|content|contact[_-]?data|file[_-]?content|"
    r"prompt|response|provider[_-]?payload|payload|local[_-]?path|env[_-]?dump|"
    r"credential|cookie|token|secret|api[_-]?key|password|username|hostname"
    r")($|[_-])"
)
_RAW_DELIVERY_VALUE_RE = re.compile(
    r"(?i)(raw\s+(message|body|content|prompt|response|payload|file|local\s+path)|"
    r"message[\s_-]?body|provider[\s_-]?payload|env[\s_-]?dump|credential|"
    r"secret|api[_-]?key|bearer\s+|cookie|token|/Users/|/home/|-----BEGIN|"
    r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})"
)
_RAW_DELIVERY_ALLOWED_KEYS = {
    "raw_body_persisted",
    "raw_content_persisted",
    "raw_payloads_persisted",
    "raw_message_body_persisted",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "file_content_persisted",
    "contact_data_persisted",
    "credential_material_persisted",
    "credential_collection_enabled",
    "credential_collection_performed",
    "redacted_body_summary_ref",
    "redacted_body_summary_refs",
    "body_summary_redacted",
}


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _sorted_unique(refs: Iterable[str | None]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        if not ref:
            continue
        validate_execution_ref(ref, "connector_delivery_ref")
        safe_refs.append(ref)
    return sorted(dict.fromkeys(safe_refs))


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        _validate_ref(value, field_name)


def _validate_ref_list(values: Sequence[str], field_name: str) -> None:
    for value in values:
        _validate_ref(value, field_name)


def _raw_delivery_reasons(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text not in _RAW_DELIVERY_ALLOWED_KEYS and _RAW_DELIVERY_FIELD_RE.search(key_text):
                reasons.append("CONNECTOR_DELIVERY_RAW_CONTENT_FIELD_BLOCKED")
            reasons.extend(_raw_delivery_reasons(item))
        return dedupe_reasons(reasons)
    if isinstance(value, list):
        for item in value:
            reasons.extend(_raw_delivery_reasons(item))
        return dedupe_reasons(reasons)
    if isinstance(value, str) and _RAW_DELIVERY_VALUE_RE.search(value):
        reasons.append("CONNECTOR_DELIVERY_RAW_CONTENT_VALUE_BLOCKED")
    return dedupe_reasons(reasons)


def validate_connector_delivery_contract_payload(value: Mapping[str, Any]) -> list[str]:
    """Return fail-closed reason codes for unsafe connector delivery-shaped content."""

    return _raw_delivery_reasons(value)


def _validate_safe_contract_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    reasons = _raw_delivery_reasons(value)
    if reasons:
        raise ValueError(f"{field_name.upper()}_RAW_CONNECTOR_DELIVERY_CONTENT_DENIED")


def _deny_true_flags(model: Any, field_names: Iterable[str], reason_prefix: str) -> None:
    for field_name in field_names:
        if getattr(model, field_name):
            raise ValueError(f"{reason_prefix}:{field_name}")


def _missing_required_reasons(payload: Mapping[str, Any]) -> list[str]:
    checks = {
        "source_connector_safety_freeze_ref": "MISSING_CONNECTOR_SAFETY_FREEZE_REF_BLOCKED",
        "run_ref": "MISSING_RUN_REF_BLOCKED",
        "delivery_ref": "MISSING_DELIVERY_REF_BLOCKED",
        "connector_ref": "MISSING_CONNECTOR_REF_BLOCKED",
        "channel_ref": "MISSING_CHANNEL_REF_BLOCKED",
        "target_session_ref": "MISSING_TARGET_SESSION_REF_BLOCKED",
        "origin_ref": "MISSING_ORIGIN_REF_BLOCKED",
        "origin_cleanup_posture_ref": "MISSING_ORIGIN_CLEANUP_POSTURE_BLOCKED",
        "outbound_approval_ref": "MISSING_OUTBOUND_APPROVAL_BLOCKED",
        "idempotency_key_ref": "MISSING_IDEMPOTENCY_REF_BLOCKED",
        "redacted_subject_ref": "MISSING_REDACTED_SUBJECT_REF_BLOCKED",
        "redacted_body_summary_ref": "MISSING_REDACTED_BODY_SUMMARY_REF_BLOCKED",
    }
    return dedupe_reasons([reason for key, reason in checks.items() if not payload.get(key)])


def _approval_ref_reasons(value: str) -> list[str]:
    lowered = value.lower()
    reasons: list[str] = []
    if lowered.startswith("approval_test") or ":approval_test" in lowered:
        reasons.append("APPROVAL_TEST_REF_BLOCKED")
    if ":*" in lowered or lowered.endswith(":all") or ":all:" in lowered or "*" in lowered:
        reasons.append("WILDCARD_APPROVAL_REF_BLOCKED")
    return reasons


class _ConnectorDeliveryContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, validate_assignment=True)


class ConnectorDeliveryEnvelopeContract(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_ENVELOPE_SCHEMA_VERSION
    source_connector_safety_freeze_ref: str = CONNECTOR_DELIVERY_SOURCE_FREEZE_REF
    delivery_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    connector_ref: str = Field(..., min_length=1)
    channel_ref: str = Field(..., min_length=1)
    target_session_ref: str = Field(..., min_length=1)
    origin_ref: str = Field(..., min_length=1)
    origin_cleanup_posture_ref: str = Field(..., min_length=1)
    outbound_approval_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    redacted_subject_ref: str = Field(..., min_length=1)
    redacted_body_summary_ref: str = Field(..., min_length=1)
    attachment_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    rollback_posture_ref: str = Field(..., min_length=1)
    safe_disable_posture_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(
        default="Connector delivery envelope is proposal metadata only; send and write authority remain blocked.",
        min_length=1,
    )
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    target_session_ref_grants_authority: bool = False
    outbound_approval_ref_grants_authority: bool = False
    raw_body_persisted: bool = False
    raw_content_persisted: bool = False
    file_content_persisted: bool = False
    contact_data_persisted: bool = False
    credential_material_persisted: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_delivery_worker_enabled: bool = False
    account_sync_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    provider_model_calls_enabled: bool = False
    live_web_runtime_enabled: bool = False
    browser_runtime_enabled: bool = False
    shell_runtime_enabled: bool = False
    scheduler_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_envelope(self) -> Any:
        for value, field_name in [
            (self.source_connector_safety_freeze_ref, "source_connector_safety_freeze_ref"),
            (self.delivery_ref, "delivery_ref"),
            (self.run_ref, "run_ref"),
            (self.connector_ref, "connector_ref"),
            (self.channel_ref, "channel_ref"),
            (self.target_session_ref, "target_session_ref"),
            (self.origin_ref, "origin_ref"),
            (self.origin_cleanup_posture_ref, "origin_cleanup_posture_ref"),
            (self.outbound_approval_ref, "outbound_approval_ref"),
            (self.idempotency_key_ref, "idempotency_key_ref"),
            (self.redacted_subject_ref, "redacted_subject_ref"),
            (self.redacted_body_summary_ref, "redacted_body_summary_ref"),
            (self.rollback_posture_ref, "rollback_posture_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_ref_list(self.attachment_refs, "attachment_ref")
        _validate_ref_list(self.evidence_refs, "evidence_ref")
        _validate_ref_list(self.expected_receipt_refs, "expected_receipt_ref")
        if self.source_connector_safety_freeze_ref != CONNECTOR_DELIVERY_SOURCE_FREEZE_REF:
            raise ValueError("CONNECTOR_DELIVERY_SOURCE_FREEZE_REF_MISMATCH")
        approval_reasons = _approval_ref_reasons(self.outbound_approval_ref)
        if approval_reasons:
            raise ValueError(":".join(approval_reasons))
        if self.side_effects_performed:
            raise ValueError("CONNECTOR_DELIVERY_SIDE_EFFECTS_DENIED")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_contract_text(text, field_name)
        if not self.expected_receipt_refs:
            raise ValueError("CONNECTOR_DELIVERY_EXPECTED_RECEIPT_REF_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("CONNECTOR_DELIVERY_SAFE_REFS_REQUIRED")
        if _raw_delivery_reasons(self.model_dump(mode="json")):
            raise ValueError("CONNECTOR_DELIVERY_RAW_CONTENT_DENIED")
        _deny_true_flags(
            self,
            [
                "target_session_ref_grants_authority",
                "outbound_approval_ref_grants_authority",
                "raw_body_persisted",
                "raw_content_persisted",
                "file_content_persisted",
                "contact_data_persisted",
                "credential_material_persisted",
                "connector_write_enabled",
                "connector_send_enabled",
                "connector_delete_enabled",
                "connector_delivery_worker_enabled",
                "account_sync_enabled",
                "oauth_enabled",
                "credential_collection_enabled",
                "provider_model_calls_enabled",
                "live_web_runtime_enabled",
                "browser_runtime_enabled",
                "shell_runtime_enabled",
                "scheduler_enabled",
                "production_authority_enabled",
            ],
            "CONNECTOR_DELIVERY_AUTHORITY_DENIED",
        )
        return self


class ConnectorDeliveryTimelineEventContract(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_EVENT_SCHEMA_VERSION
    source_connector_safety_freeze_ref: str = CONNECTOR_DELIVERY_SOURCE_FREEZE_REF
    event_ref: str = Field(..., min_length=1)
    delivery_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    connector_ref: str = Field(..., min_length=1)
    channel_ref: str = Field(..., min_length=1)
    target_session_ref: str = Field(..., min_length=1)
    origin_ref: str = Field(..., min_length=1)
    origin_cleanup_posture_ref: str = Field(..., min_length=1)
    outbound_approval_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    delivery_state: ConnectorDeliveryState
    redacted_subject_ref: str | None = None
    redacted_body_summary_ref: str | None = None
    attachment_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    retry_ref: str | None = None
    failure_receipt_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata_only: bool = True
    safe_refs_only: bool = True
    no_send_action: bool = True
    target_session_ref_grants_authority: bool = False
    raw_body_persisted: bool = False
    raw_content_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    file_content_persisted: bool = False
    contact_data_persisted: bool = False
    credential_material_persisted: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    account_sync_performed: bool = False
    oauth_performed: bool = False
    credential_collection_performed: bool = False
    background_delivery_worker_started: bool = False
    scheduler_started: bool = False
    provider_model_called: bool = False
    live_web_runtime_used: bool = False
    browser_runtime_used: bool = False
    shell_runtime_used: bool = False
    production_authority_enabled: bool = False

    @classmethod
    def from_envelope(
        cls,
        envelope: ConnectorDeliveryEnvelopeContract,
        *,
        event_ref: str,
        delivery_state: ConnectorDeliveryState = "draft_created_metadata_only",
        safe_summary: str = "Connector delivery envelope was recorded as metadata-only safe refs.",
        retry_ref: str | None = None,
        failure_receipt_refs: Sequence[str] = (),
        blocked_reason_refs: Sequence[str] = (),
    ) -> ConnectorDeliveryTimelineEventContract:
        return cls(
            event_ref=event_ref,
            source_connector_safety_freeze_ref=envelope.source_connector_safety_freeze_ref,
            delivery_ref=envelope.delivery_ref,
            run_ref=envelope.run_ref,
            connector_ref=envelope.connector_ref,
            channel_ref=envelope.channel_ref,
            target_session_ref=envelope.target_session_ref,
            origin_ref=envelope.origin_ref,
            origin_cleanup_posture_ref=envelope.origin_cleanup_posture_ref,
            outbound_approval_ref=envelope.outbound_approval_ref,
            idempotency_key_ref=envelope.idempotency_key_ref,
            delivery_state=delivery_state,
            redacted_subject_ref=envelope.redacted_subject_ref,
            redacted_body_summary_ref=envelope.redacted_body_summary_ref,
            attachment_refs=list(envelope.attachment_refs),
            evidence_refs=list(envelope.evidence_refs),
            expected_receipt_refs=list(envelope.expected_receipt_refs),
            retry_ref=retry_ref,
            failure_receipt_refs=list(failure_receipt_refs),
            blocked_reason_refs=list(blocked_reason_refs),
            audit_refs=[envelope.audit_ref],
            replay_refs=[envelope.replay_ref],
            rollback_refs=[envelope.rollback_posture_ref],
            safe_disable_refs=[envelope.safe_disable_posture_ref],
            safe_summary=safe_summary,
        )

    @model_validator(mode="after")
    def validate_event(self) -> Any:
        for value, field_name in [
            (self.source_connector_safety_freeze_ref, "source_connector_safety_freeze_ref"),
            (self.event_ref, "event_ref"),
            (self.delivery_ref, "delivery_ref"),
            (self.run_ref, "run_ref"),
            (self.connector_ref, "connector_ref"),
            (self.channel_ref, "channel_ref"),
            (self.target_session_ref, "target_session_ref"),
            (self.origin_ref, "origin_ref"),
            (self.origin_cleanup_posture_ref, "origin_cleanup_posture_ref"),
            (self.outbound_approval_ref, "outbound_approval_ref"),
            (self.idempotency_key_ref, "idempotency_key_ref"),
        ]:
            _validate_ref(value, field_name)
        for value, field_name in [
            (self.redacted_subject_ref, "redacted_subject_ref"),
            (self.redacted_body_summary_ref, "redacted_body_summary_ref"),
            (self.retry_ref, "retry_ref"),
        ]:
            _validate_optional_ref(value, field_name)
        for ref in [
            *self.attachment_refs,
            *self.evidence_refs,
            *self.expected_receipt_refs,
            *self.failure_receipt_refs,
            *self.blocked_reason_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.safe_disable_refs,
        ]:
            _validate_ref(ref, "connector_delivery_event_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.delivery_state, "delivery_state"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_contract_text(text, field_name)
        if self.delivery_state == "retry_scheduled_metadata_only" and not self.retry_ref:
            raise ValueError("CONNECTOR_DELIVERY_RETRY_REF_REQUIRED")
        if self.delivery_state == "failed_metadata_only" and not self.failure_receipt_refs:
            raise ValueError("CONNECTOR_DELIVERY_FAILURE_RECEIPT_REF_REQUIRED")
        if self.delivery_state in {"delivery_blocked", "sent_not_supported"} and not self.blocked_reason_refs:
            raise ValueError("CONNECTOR_DELIVERY_BLOCKED_REASON_REF_REQUIRED")
        if self.delivery_state == "approval_denied" and not self.outbound_approval_ref:
            raise ValueError("CONNECTOR_DELIVERY_APPROVAL_REF_REQUIRED")
        if self.source_connector_safety_freeze_ref != CONNECTOR_DELIVERY_SOURCE_FREEZE_REF:
            raise ValueError("CONNECTOR_DELIVERY_EVENT_SOURCE_FREEZE_REF_MISMATCH")
        approval_reasons = _approval_ref_reasons(self.outbound_approval_ref)
        if approval_reasons:
            raise ValueError(":".join(approval_reasons))
        if self.side_effects_performed:
            raise ValueError("CONNECTOR_DELIVERY_EVENT_SIDE_EFFECTS_DENIED")
        if not self.metadata_only:
            raise ValueError("CONNECTOR_DELIVERY_EVENT_METADATA_ONLY_REQUIRED")
        if not self.safe_refs_only or not self.no_send_action:
            raise ValueError("CONNECTOR_DELIVERY_EVENT_SAFE_REFS_REQUIRED")
        if _raw_delivery_reasons(self.model_dump(mode="json")):
            raise ValueError("CONNECTOR_DELIVERY_EVENT_RAW_CONTENT_DENIED")
        _deny_true_flags(
            self,
            [
                "target_session_ref_grants_authority",
                "raw_body_persisted",
                "raw_content_persisted",
                "raw_prompt_persisted",
                "raw_response_persisted",
                "raw_provider_payload_persisted",
                "file_content_persisted",
                "contact_data_persisted",
                "credential_material_persisted",
                "connector_write_performed",
                "connector_send_performed",
                "connector_delete_performed",
                "account_sync_performed",
                "oauth_performed",
                "credential_collection_performed",
                "background_delivery_worker_started",
                "scheduler_started",
                "provider_model_called",
                "live_web_runtime_used",
                "browser_runtime_used",
                "shell_runtime_used",
                "production_authority_enabled",
            ],
            "CONNECTOR_DELIVERY_EVENT_AUTHORITY_DENIED",
        )
        return self

    def to_receipt_summary(self) -> dict[str, Any]:
        return {
            "schema_version": CONNECTOR_DELIVERY_EVENT_RECEIPT_SCHEMA_VERSION,
            "source_connector_safety_freeze_ref": self.source_connector_safety_freeze_ref,
            "event_ref": self.event_ref,
            "delivery_ref": self.delivery_ref,
            "run_ref": self.run_ref,
            "connector_ref": self.connector_ref,
            "channel_ref": self.channel_ref,
            "target_session_ref": self.target_session_ref,
            "origin_ref": self.origin_ref,
            "origin_cleanup_posture_ref": self.origin_cleanup_posture_ref,
            "outbound_approval_ref": self.outbound_approval_ref,
            "idempotency_key_ref": self.idempotency_key_ref,
            "delivery_state": self.delivery_state,
            "redacted_subject_ref": self.redacted_subject_ref,
            "redacted_body_summary_ref": self.redacted_body_summary_ref,
            "attachment_refs": list(self.attachment_refs),
            "evidence_refs": list(self.evidence_refs),
            "expected_receipt_refs": list(self.expected_receipt_refs),
            "retry_ref": self.retry_ref,
            "failure_receipt_refs": list(self.failure_receipt_refs),
            "blocked_reason_refs": list(self.blocked_reason_refs),
            "safe_refs_only": True,
            "metadata_only": True,
            "no_send_action": True,
            "raw_content_persisted": False,
            "connector_write_performed": False,
            "connector_send_performed": False,
            "account_sync_performed": False,
            "oauth_performed": False,
            "background_delivery_worker_started": False,
            "scheduler_started": False,
            "side_effects_performed": [],
        }


class ConnectorDeliveryValidationContext(_ConnectorDeliveryContractModel):
    known_connector_refs: list[str] = Field(default_factory=list)
    known_channel_refs: list[str] = Field(default_factory=list)
    outbound_approval_ref: str | None = None
    outbound_approval_state: ConnectorDeliveryApprovalState = "not_validated"

    @model_validator(mode="after")
    def validate_context(self) -> Any:
        _validate_ref_list(self.known_connector_refs, "known_connector_ref")
        _validate_ref_list(self.known_channel_refs, "known_channel_ref")
        _validate_optional_ref(self.outbound_approval_ref, "outbound_approval_ref")
        _validate_safe_contract_text(self.outbound_approval_state, "outbound_approval_state")
        return self


class ConnectorDeliveryValidationDecision(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_VALIDATION_SCHEMA_VERSION
    validation_status: ConnectorDeliveryValidationStatus
    contract_valid: bool = False
    blocked: bool = True
    delivery_ref: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    delivery_permitted: bool = False
    delivery_performed: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    account_sync_performed: bool = False
    oauth_performed: bool = False
    credential_collection_performed: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        _validate_optional_ref(self.delivery_ref, "delivery_ref")
        _validate_safe_contract_text(self.safe_message, "safe_message")
        if self.delivery_permitted or self.delivery_performed:
            raise ValueError("CONNECTOR_DELIVERY_DECISION_MUST_NOT_GRANT_DELIVERY")
        _deny_true_flags(
            self,
            [
                "connector_write_performed",
                "connector_send_performed",
                "account_sync_performed",
                "oauth_performed",
                "credential_collection_performed",
            ],
            "CONNECTOR_DELIVERY_DECISION_AUTHORITY_DENIED",
        )
        if self.validation_status == "valid_contract_only" and (self.blocked or not self.contract_valid):
            raise ValueError("CONNECTOR_DELIVERY_VALID_DECISION_SHAPE_DENIED")
        if self.validation_status != "valid_contract_only" and not self.blocked:
            raise ValueError("CONNECTOR_DELIVERY_BLOCKED_DECISION_SHAPE_DENIED")
        return self


class ConnectorDeliveryStatusReadModel(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_STATUS_SCHEMA_VERSION
    delivery_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    connector_ref: str = Field(..., min_length=1)
    channel_ref: str = Field(..., min_length=1)
    target_session_ref: str = Field(..., min_length=1)
    latest_state: ConnectorDeliveryState
    event_refs: list[str] = Field(default_factory=list)
    outbound_approval_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    retry_refs: list[str] = Field(default_factory=list)
    failure_receipt_refs: list[str] = Field(default_factory=list)
    pending_approval_visible: bool = False
    delivery_blocked_visible: bool = False
    retry_posture_visible: bool = False
    failure_posture_visible: bool = False
    sent_not_supported_visible: bool = False
    safe_refs_only: bool = True
    no_send_action: bool = True
    target_session_ref_grants_authority: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_status(self) -> Any:
        for value, field_name in [
            (self.delivery_ref, "delivery_ref"),
            (self.run_ref, "run_ref"),
            (self.connector_ref, "connector_ref"),
            (self.channel_ref, "channel_ref"),
            (self.target_session_ref, "target_session_ref"),
        ]:
            _validate_ref(value, field_name)
        for ref in [
            *self.event_refs,
            *self.outbound_approval_refs,
            *self.expected_receipt_refs,
            *self.blocked_reason_refs,
            *self.retry_refs,
            *self.failure_receipt_refs,
        ]:
            _validate_ref(ref, "connector_delivery_status_ref")
        _validate_safe_contract_text(self.latest_state, "latest_state")
        if not self.safe_refs_only or not self.no_send_action:
            raise ValueError("CONNECTOR_DELIVERY_STATUS_SAFE_REFS_REQUIRED")
        _deny_true_flags(
            self,
            [
                "target_session_ref_grants_authority",
                "connector_write_enabled",
                "connector_send_enabled",
                "account_sync_enabled",
            ],
            "CONNECTOR_DELIVERY_STATUS_AUTHORITY_DENIED",
        )
        return self


class ConnectorDeliveryReadModel(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_READ_MODEL_SCHEMA_VERSION
    source: str = "python_core_connector_delivery_read_model"
    backend_owned: bool = True
    cli_ref: str = "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-connector-deliveries"
    route_ref: str = "planned:none"
    event_count: int = Field(..., ge=0)
    delivery_count: int = Field(..., ge=0)
    pending_approval_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    events: list[ConnectorDeliveryTimelineEventContract] = Field(default_factory=list)
    delivery_statuses: list[ConnectorDeliveryStatusReadModel] = Field(default_factory=list)
    state_counts: dict[str, int] = Field(default_factory=dict)
    safe_summary: str = Field(
        default="Connector delivery semantics are contract-only and do not send or write.",
        min_length=1,
    )
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    no_send_action: bool = True
    target_session_refs_grant_authority: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    account_sync_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    provider_model_calls_enabled: bool = False
    live_web_runtime_enabled: bool = False
    browser_runtime_enabled: bool = False
    shell_runtime_enabled: bool = False
    background_delivery_worker_enabled: bool = False
    scheduler_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.cli_ref, "cli_ref"),
            (self.route_ref, "route_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_contract_text(text, field_name)
        if not self.backend_owned:
            raise ValueError("CONNECTOR_DELIVERY_BACKEND_OWNED_REQUIRED")
        if self.event_count != len(self.events):
            raise ValueError("CONNECTOR_DELIVERY_EVENT_COUNT_MISMATCH")
        if self.delivery_count != len(self.delivery_statuses):
            raise ValueError("CONNECTOR_DELIVERY_STATUS_COUNT_MISMATCH")
        if not self.safe_refs_only or not self.no_send_action:
            raise ValueError("CONNECTOR_DELIVERY_READ_MODEL_SAFE_REFS_REQUIRED")
        _deny_true_flags(
            self,
            [
                "raw_payloads_persisted",
                "target_session_refs_grant_authority",
                "connector_writes_enabled",
                "connector_sends_enabled",
                "account_sync_enabled",
                "oauth_enabled",
                "credential_collection_enabled",
                "provider_model_calls_enabled",
                "live_web_runtime_enabled",
                "browser_runtime_enabled",
                "shell_runtime_enabled",
                "background_delivery_worker_enabled",
                "scheduler_enabled",
                "production_authority_enabled",
            ],
            "CONNECTOR_DELIVERY_READ_MODEL_AUTHORITY_DENIED",
        )
        return self


class ConnectorDeliveryReviewQueueItemReadModel(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_REVIEW_QUEUE_ITEM_SCHEMA_VERSION
    item_ref: str = Field(..., min_length=1)
    delivery_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    connector_ref: str = Field(..., min_length=1)
    channel_ref: str = Field(..., min_length=1)
    target_session_ref: str = Field(..., min_length=1)
    latest_state: ConnectorDeliveryState
    delivery_state_label: str = Field(..., min_length=1)
    delivery_execution_posture: str = "blocked_planned_no_delivery_execution"
    event_refs: list[str] = Field(default_factory=list)
    redacted_subject_refs: list[str] = Field(default_factory=list)
    redacted_body_summary_refs: list[str] = Field(default_factory=list)
    outbound_approval_refs: list[str] = Field(default_factory=list)
    idempotency_key_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    retry_refs: list[str] = Field(default_factory=list)
    failure_receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    next_safe_action: str = "inspect_connector_delivery_review_refs_only"
    safe_refs_only: bool = True
    no_send_action: bool = True
    metadata_only: bool = True
    raw_payloads_persisted: bool = False
    raw_body_persisted: bool = False
    raw_content_persisted: bool = False
    file_content_persisted: bool = False
    contact_data_persisted: bool = False
    credential_material_persisted: bool = False
    outbound_approval_refs_are_identifiers_only: bool = True
    target_session_ref_grants_authority: bool = False
    delivery_execution_performed: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    account_sync_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    provider_model_calls_enabled: bool = False
    live_web_runtime_enabled: bool = False
    browser_runtime_enabled: bool = False
    shell_runtime_enabled: bool = False
    background_delivery_worker_enabled: bool = False
    scheduler_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_review_item(self) -> Any:
        for value, field_name in [
            (self.item_ref, "item_ref"),
            (self.delivery_ref, "delivery_ref"),
            (self.run_ref, "run_ref"),
            (self.connector_ref, "connector_ref"),
            (self.channel_ref, "channel_ref"),
            (self.target_session_ref, "target_session_ref"),
        ]:
            _validate_ref(value, field_name)
        for ref in [
            *self.event_refs,
            *self.redacted_subject_refs,
            *self.redacted_body_summary_refs,
            *self.outbound_approval_refs,
            *self.idempotency_key_refs,
            *self.blocked_reason_refs,
            *self.retry_refs,
            *self.failure_receipt_refs,
            *self.evidence_refs,
            *self.receipt_refs,
            *self.proof_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.safe_disable_refs,
            *self.blocked_authority_refs,
        ]:
            _validate_ref(ref, "connector_delivery_review_queue_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.latest_state, "latest_state"),
            (self.delivery_state_label, "delivery_state_label"),
            (self.delivery_execution_posture, "delivery_execution_posture"),
            (self.safe_summary, "safe_summary"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            _validate_safe_contract_text(text, field_name)
        if self.latest_state == "delivery_ready_not_sent" and "not sent" not in self.delivery_state_label:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_READY_STATE_MUST_LABEL_NOT_SENT")
        if not self.safe_refs_only or not self.no_send_action or not self.metadata_only:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_ITEM_SAFE_REFS_REQUIRED")
        if not self.outbound_approval_refs_are_identifiers_only:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_APPROVAL_REFS_IDENTIFIER_ONLY_REQUIRED")
        if _raw_delivery_reasons(self.model_dump(mode="json")):
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_ITEM_RAW_CONTENT_DENIED")
        _deny_true_flags(
            self,
            [
                "raw_payloads_persisted",
                "raw_body_persisted",
                "raw_content_persisted",
                "file_content_persisted",
                "contact_data_persisted",
                "credential_material_persisted",
                "target_session_ref_grants_authority",
                "delivery_execution_performed",
                "connector_write_enabled",
                "connector_send_enabled",
                "account_sync_enabled",
                "oauth_enabled",
                "credential_collection_enabled",
                "provider_model_calls_enabled",
                "live_web_runtime_enabled",
                "browser_runtime_enabled",
                "shell_runtime_enabled",
                "background_delivery_worker_enabled",
                "scheduler_enabled",
                "production_authority_enabled",
            ],
            "CONNECTOR_DELIVERY_REVIEW_ITEM_AUTHORITY_DENIED",
        )
        return self


class ConnectorDeliveryReviewQueueReadModel(_ConnectorDeliveryContractModel):
    schema_version: str = CONNECTOR_DELIVERY_REVIEW_QUEUE_SCHEMA_VERSION
    source: str = "python_core_connector_delivery_review_queue_read_model"
    backend_owned: bool = True
    review_ref: str = Field(..., min_length=1)
    route_ref: str = "/control-center/approvals/queue"
    route_refs: list[str] = Field(default_factory=lambda: ["GET /control-center/approvals/queue"])
    cli_ref: str = "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-connector-delivery-review"
    queue_items: list[ConnectorDeliveryReviewQueueItemReadModel] = Field(default_factory=list)
    delivery_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    connector_refs: list[str] = Field(default_factory=list)
    channel_refs: list[str] = Field(default_factory=list)
    target_session_refs: list[str] = Field(default_factory=list)
    outbound_approval_refs: list[str] = Field(default_factory=list)
    idempotency_key_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    state_counts: dict[str, int] = Field(default_factory=dict)
    delivery_count: int = Field(..., ge=0)
    pending_count: int = Field(default=0, ge=0)
    delivery_ready_not_sent_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    safe_summary: str = Field(
        default=(
            "Connector delivery review queue is backend-owned and read-only; "
            "delivery execution remains blocked and planned."
        ),
        min_length=1,
    )
    next_safe_action: str = "inspect_connector_delivery_review_refs_only"
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    no_send_action: bool = True
    metadata_only: bool = True
    outbound_approval_refs_are_identifiers_only: bool = True
    target_session_refs_grant_authority: bool = False
    delivery_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    account_sync_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    provider_model_calls_enabled: bool = False
    live_web_runtime_enabled: bool = False
    browser_runtime_enabled: bool = False
    shell_runtime_enabled: bool = False
    background_delivery_worker_enabled: bool = False
    scheduler_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_review_queue(self) -> Any:
        _validate_ref(self.review_ref, "review_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            _validate_safe_contract_text(text, field_name)
        for route_ref in self.route_refs:
            _validate_safe_contract_text(route_ref, "route_ref")
        for state in self.state_counts:
            _validate_safe_contract_text(state, "state_count_key")
        for ref in [
            *self.delivery_refs,
            *self.run_refs,
            *self.connector_refs,
            *self.channel_refs,
            *self.target_session_refs,
            *self.outbound_approval_refs,
            *self.idempotency_key_refs,
            *self.evidence_refs,
            *self.receipt_refs,
            *self.proof_refs,
            *self.blocked_reason_refs,
            *self.blocked_authority_refs,
        ]:
            _validate_ref(ref, "connector_delivery_review_queue_ref")
        if not self.backend_owned:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_BACKEND_OWNED_REQUIRED")
        if self.delivery_count != len(self.queue_items):
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_COUNT_MISMATCH")
        if self.delivery_ready_not_sent_count != sum(
            1 for item in self.queue_items if item.latest_state == "delivery_ready_not_sent"
        ):
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_READY_COUNT_MISMATCH")
        if not self.safe_refs_only or not self.no_send_action or not self.metadata_only:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_SAFE_REFS_REQUIRED")
        if not self.outbound_approval_refs_are_identifiers_only:
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_APPROVAL_REFS_IDENTIFIER_ONLY_REQUIRED")
        if _raw_delivery_reasons(self.model_dump(mode="json")):
            raise ValueError("CONNECTOR_DELIVERY_REVIEW_QUEUE_RAW_CONTENT_DENIED")
        _deny_true_flags(
            self,
            [
                "raw_payloads_persisted",
                "target_session_refs_grant_authority",
                "delivery_execution_enabled",
                "connector_writes_enabled",
                "connector_sends_enabled",
                "account_sync_enabled",
                "oauth_enabled",
                "credential_collection_enabled",
                "provider_model_calls_enabled",
                "live_web_runtime_enabled",
                "browser_runtime_enabled",
                "shell_runtime_enabled",
                "background_delivery_worker_enabled",
                "scheduler_enabled",
                "production_authority_enabled",
            ],
            "CONNECTOR_DELIVERY_REVIEW_QUEUE_AUTHORITY_DENIED",
        )
        return self


def _delivery_state_label(state: ConnectorDeliveryState) -> str:
    labels: dict[ConnectorDeliveryState, str] = {
        "draft_created_metadata_only": "draft metadata only / not sent",
        "pending_approval": "approval requested / not sent",
        "approval_denied": "approval denied / not sent",
        "delivery_blocked": "delivery blocked / not sent",
        "delivery_ready_not_sent": "delivery ready metadata only / not sent",
        "retry_scheduled_metadata_only": "retry posture metadata only / not sent",
        "failed_metadata_only": "failure metadata only / not sent",
        "canceled_metadata_only": "canceled metadata only / not sent",
        "sent_not_supported": "sent unsupported / not sent",
    }
    return labels[state]


def _build_connector_delivery_review_items(
    events: list[ConnectorDeliveryTimelineEventContract],
) -> list[ConnectorDeliveryReviewQueueItemReadModel]:
    by_delivery: dict[str, list[ConnectorDeliveryTimelineEventContract]] = defaultdict(list)
    for event in events:
        by_delivery[event.delivery_ref].append(event)

    items: list[ConnectorDeliveryReviewQueueItemReadModel] = []
    for delivery_ref, delivery_events in sorted(by_delivery.items()):
        latest = delivery_events[-1]
        proof_ref = _stable_ref("proof-ref", delivery_ref)
        blocked_authority_refs = _sorted_unique(
            [
                "blocked-state:no-connector-write",
                "blocked-state:no-connector-send",
                "blocked-state:no-account-sync",
                "blocked-state:no-oauth",
                "blocked-state:no-auth-material-collection",
                "blocked-state:no-provider-model-call",
                "blocked-state:no-live-web-runtime",
                "blocked-state:no-browser-runtime",
                "blocked-state:no-shell-runtime",
                "blocked-state:no-background-delivery-worker",
                "blocked-state:no-scheduler",
                "blocked-state:delivery-execution-blocked-planned",
                *[ref for event in delivery_events for ref in event.blocked_reason_refs],
            ]
        )
        receipt_refs = _sorted_unique(
            ref
            for event in delivery_events
            for ref in [*event.expected_receipt_refs, *event.failure_receipt_refs]
        )
        items.append(
            ConnectorDeliveryReviewQueueItemReadModel(
                item_ref=_stable_ref("connector-delivery-review-item", delivery_ref),
                delivery_ref=delivery_ref,
                run_ref=latest.run_ref,
                connector_ref=latest.connector_ref,
                channel_ref=latest.channel_ref,
                target_session_ref=latest.target_session_ref,
                latest_state=latest.delivery_state,
                delivery_state_label=_delivery_state_label(latest.delivery_state),
                event_refs=_sorted_unique(event.event_ref for event in delivery_events),
                redacted_subject_refs=_sorted_unique(
                    event.redacted_subject_ref for event in delivery_events
                ),
                redacted_body_summary_refs=_sorted_unique(
                    event.redacted_body_summary_ref for event in delivery_events
                ),
                outbound_approval_refs=_sorted_unique(
                    event.outbound_approval_ref for event in delivery_events
                ),
                idempotency_key_refs=_sorted_unique(
                    event.idempotency_key_ref for event in delivery_events
                ),
                blocked_reason_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.blocked_reason_refs
                ),
                retry_refs=_sorted_unique(event.retry_ref for event in delivery_events),
                failure_receipt_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.failure_receipt_refs
                ),
                evidence_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.evidence_refs
                ),
                receipt_refs=receipt_refs,
                proof_refs=[proof_ref],
                audit_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.audit_refs
                ),
                replay_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.replay_refs
                ),
                rollback_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.rollback_refs
                ),
                safe_disable_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.safe_disable_refs
                ),
                blocked_authority_refs=blocked_authority_refs,
                safe_summary=(
                    f"Connector delivery is {_delivery_state_label(latest.delivery_state)}; "
                    "review refs only, with no send, write, account sync, retry worker, or scheduler."
                ),
            )
        )
    return items


def build_connector_delivery_review_queue(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    limit: int = 100,
) -> ConnectorDeliveryReviewQueueReadModel:
    events = connector_delivery_events_from_storage(storage, run_ref=run_ref, limit=limit)
    items = _build_connector_delivery_review_items(events)
    state_counts = Counter(item.latest_state for item in items)
    blocked_authority_refs = _sorted_unique(
        ref for item in items for ref in item.blocked_authority_refs
    )
    review_ref = _stable_ref("connector-delivery-review-queue", run_ref or "all-runs", str(len(items)))
    return ConnectorDeliveryReviewQueueReadModel(
        review_ref=review_ref,
        queue_items=items,
        delivery_refs=_sorted_unique(item.delivery_ref for item in items),
        run_refs=_sorted_unique(item.run_ref for item in items),
        connector_refs=_sorted_unique(item.connector_ref for item in items),
        channel_refs=_sorted_unique(item.channel_ref for item in items),
        target_session_refs=_sorted_unique(item.target_session_ref for item in items),
        outbound_approval_refs=_sorted_unique(
            ref for item in items for ref in item.outbound_approval_refs
        ),
        idempotency_key_refs=_sorted_unique(
            ref for item in items for ref in item.idempotency_key_refs
        ),
        evidence_refs=_sorted_unique(ref for item in items for ref in item.evidence_refs),
        receipt_refs=_sorted_unique(ref for item in items for ref in item.receipt_refs),
        proof_refs=_sorted_unique(ref for item in items for ref in item.proof_refs),
        blocked_reason_refs=_sorted_unique(
            ref for item in items for ref in item.blocked_reason_refs
        ),
        blocked_authority_refs=blocked_authority_refs,
        state_counts=dict(sorted(state_counts.items())),
        delivery_count=len(items),
        pending_count=sum(
            1
            for item in items
            if item.latest_state in {"pending_approval", "delivery_ready_not_sent"}
        ),
        delivery_ready_not_sent_count=state_counts["delivery_ready_not_sent"],
        blocked_count=sum(
            1
            for item in items
            if item.latest_state in {"approval_denied", "delivery_blocked", "sent_not_supported"}
        ),
        retry_count=sum(1 for item in items if item.latest_state == "retry_scheduled_metadata_only"),
        failure_count=sum(
            1
            for item in items
            if item.latest_state in {"failed_metadata_only", "canceled_metadata_only"}
        ),
    )


def _decision(
    status: ConnectorDeliveryValidationStatus,
    reason_codes: Sequence[str],
    safe_message: str,
    delivery_ref: str | None = None,
    *,
    contract_valid: bool = False,
) -> ConnectorDeliveryValidationDecision:
    return ConnectorDeliveryValidationDecision(
        validation_status=status,
        contract_valid=contract_valid,
        blocked=status != "valid_contract_only",
        delivery_ref=delivery_ref,
        reason_codes=dedupe_reasons(list(reason_codes)),
        safe_message=safe_message,
    )


def validate_connector_delivery_envelope(
    payload: ConnectorDeliveryEnvelopeContract | Mapping[str, Any],
    context: ConnectorDeliveryValidationContext | Mapping[str, Any] | None = None,
) -> ConnectorDeliveryValidationDecision:
    raw_mapping = payload.model_dump(mode="json") if isinstance(payload, ConnectorDeliveryEnvelopeContract) else payload
    if isinstance(raw_mapping, Mapping):
        raw_reasons = _raw_delivery_reasons(raw_mapping)
        if raw_reasons:
            return _decision(
                "blocked",
                raw_reasons,
                "Connector delivery envelope contains unsafe connector delivery fields and is blocked.",
            )
        missing_reasons = _missing_required_reasons(raw_mapping)
        if missing_reasons:
            status: ConnectorDeliveryValidationStatus = (
                "approval_required" if "MISSING_OUTBOUND_APPROVAL_BLOCKED" in missing_reasons else "blocked"
            )
            return _decision(status, missing_reasons, "Connector delivery envelope is missing required safe refs.")
    try:
        envelope_source = payload.model_dump(mode="python") if isinstance(payload, ConnectorDeliveryEnvelopeContract) else payload
        envelope = ConnectorDeliveryEnvelopeContract.model_validate(envelope_source)
        context_source = context.model_dump(mode="python") if isinstance(context, ConnectorDeliveryValidationContext) else context
        validation_context = (
            ConnectorDeliveryValidationContext()
            if context is None
            else ConnectorDeliveryValidationContext.model_validate(context_source)
        )
    except (TypeError, ValueError, ValidationError) as exc:
        return _decision(
            "validation_failed",
            ["CONNECTOR_DELIVERY_CONTRACT_VALIDATION_FAILED"],
            f"Connector delivery envelope failed validation: {exc.__class__.__name__}.",
        )

    reasons: list[str] = []
    if envelope.connector_ref not in set(validation_context.known_connector_refs):
        reasons.append("UNKNOWN_CONNECTOR_BLOCKED")
    if envelope.channel_ref not in set(validation_context.known_channel_refs):
        reasons.append("UNKNOWN_CHANNEL_BLOCKED")
    if (
        validation_context.outbound_approval_ref
        and validation_context.outbound_approval_ref != envelope.outbound_approval_ref
    ):
        reasons.append("OUTBOUND_APPROVAL_SCOPE_MISMATCH_BLOCKED")
    if validation_context.outbound_approval_state in {"denied", "expired", "revoked", "blocked"}:
        reasons.append("OUTBOUND_APPROVAL_STATE_BLOCKED")
    if reasons:
        return _decision(
            "blocked",
            reasons,
            "Connector delivery envelope is blocked before any send or write authority.",
            envelope.delivery_ref,
        )
    if validation_context.outbound_approval_state != "approved_metadata_only":
        return _decision(
            "approval_required",
            ["OUTBOUND_APPROVAL_REQUIRED"],
            "Connector delivery envelope still requires approved metadata-only posture before contract validation.",
            envelope.delivery_ref,
        )
    return _decision(
        "valid_contract_only",
        ["CONNECTOR_DELIVERY_CONTRACT_VALID_NO_SEND"],
        "Connector delivery envelope is valid as metadata only; send and write authority remain disabled.",
        envelope.delivery_ref,
        contract_valid=True,
    )


def connector_delivery_event_from_receipt_summary(
    receipt_summary: Mapping[str, Any],
) -> ConnectorDeliveryTimelineEventContract | None:
    if receipt_summary.get("schema_version") != CONNECTOR_DELIVERY_EVENT_RECEIPT_SCHEMA_VERSION:
        return None
    state = receipt_summary.get("delivery_state")
    if state not in CONNECTOR_DELIVERY_STATES:
        return None
    return ConnectorDeliveryTimelineEventContract(
        source_connector_safety_freeze_ref=str(
            receipt_summary.get("source_connector_safety_freeze_ref", CONNECTOR_DELIVERY_SOURCE_FREEZE_REF)
        ),
        event_ref=str(receipt_summary["event_ref"]),
        delivery_ref=str(receipt_summary["delivery_ref"]),
        run_ref=str(receipt_summary["run_ref"]),
        connector_ref=str(receipt_summary["connector_ref"]),
        channel_ref=str(receipt_summary["channel_ref"]),
        target_session_ref=str(receipt_summary["target_session_ref"]),
        origin_ref=str(receipt_summary["origin_ref"]),
        origin_cleanup_posture_ref=str(receipt_summary["origin_cleanup_posture_ref"]),
        outbound_approval_ref=str(receipt_summary["outbound_approval_ref"]),
        idempotency_key_ref=str(receipt_summary["idempotency_key_ref"]),
        delivery_state=state,
        redacted_subject_ref=receipt_summary.get("redacted_subject_ref"),
        redacted_body_summary_ref=receipt_summary.get("redacted_body_summary_ref"),
        attachment_refs=_sorted_unique(receipt_summary.get("attachment_refs", [])),
        evidence_refs=_sorted_unique(receipt_summary.get("evidence_refs", [])),
        expected_receipt_refs=_sorted_unique(receipt_summary.get("expected_receipt_refs", [])),
        retry_ref=receipt_summary.get("retry_ref"),
        failure_receipt_refs=_sorted_unique(receipt_summary.get("failure_receipt_refs", [])),
        blocked_reason_refs=_sorted_unique(receipt_summary.get("blocked_reason_refs", [])),
        safe_summary="Connector delivery event was restored from safe receipt metadata.",
    )


def record_connector_delivery_event(
    storage: AppendFirstRunStorage,
    event: ConnectorDeliveryTimelineEventContract,
    *,
    idempotency_key_ref: str,
    audit_ref: str,
    receipt_ref: str,
    rollback_ref: str,
) -> None:
    validated = ConnectorDeliveryTimelineEventContract.model_validate(event.model_dump(mode="python"))
    for value, field_name in [
        (idempotency_key_ref, "idempotency_key_ref"),
        (audit_ref, "audit_ref"),
        (receipt_ref, "receipt_ref"),
        (rollback_ref, "rollback_ref"),
    ]:
        _validate_ref(value, field_name)
    storage.append_receipt_summary(
        run_id=validated.run_ref,
        receipt_ref=receipt_ref,
        idempotency_key=idempotency_key_ref,
        audit_ref=audit_ref,
        rollback_ref=rollback_ref,
        safe_summary="Connector delivery metadata event was recorded as safe refs only.",
        receipt_summary=validated.to_receipt_summary(),
        evidence_refs=validated.evidence_refs,
    )


def connector_delivery_events_from_storage(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    limit: int = 100,
) -> list[ConnectorDeliveryTimelineEventContract]:
    if run_ref is not None:
        _validate_ref(run_ref, "run_ref")
    events: list[ConnectorDeliveryTimelineEventContract] = []
    bounded_limit = max(1, min(limit, 200))
    for entry in storage.list_entries(run_ref):
        if entry.kind != DurableRunStorageEntryKind.receipt or not entry.receipt_summary:
            continue
        event = connector_delivery_event_from_receipt_summary(entry.receipt_summary)
        if event is None:
            continue
        events.append(
            event.model_copy(
                update={
                    "audit_refs": _sorted_unique([entry.audit_ref, *event.audit_refs]),
                    "replay_refs": _sorted_unique([entry.replay_validation_ref, *event.replay_refs]),
                    "rollback_refs": _sorted_unique([entry.rollback_ref, *event.rollback_refs]),
                }
            )
        )
    return events[-bounded_limit:]


def _build_delivery_statuses(
    events: list[ConnectorDeliveryTimelineEventContract],
) -> list[ConnectorDeliveryStatusReadModel]:
    by_delivery: dict[str, list[ConnectorDeliveryTimelineEventContract]] = defaultdict(list)
    for event in events:
        by_delivery[event.delivery_ref].append(event)

    statuses: list[ConnectorDeliveryStatusReadModel] = []
    for delivery_ref, delivery_events in sorted(by_delivery.items()):
        latest = delivery_events[-1]
        states = {event.delivery_state for event in delivery_events}
        statuses.append(
            ConnectorDeliveryStatusReadModel(
                delivery_ref=delivery_ref,
                run_ref=latest.run_ref,
                connector_ref=latest.connector_ref,
                channel_ref=latest.channel_ref,
                target_session_ref=latest.target_session_ref,
                latest_state=latest.delivery_state,
                event_refs=_sorted_unique(event.event_ref for event in delivery_events),
                outbound_approval_refs=_sorted_unique(event.outbound_approval_ref for event in delivery_events),
                expected_receipt_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.expected_receipt_refs
                ),
                blocked_reason_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.blocked_reason_refs
                ),
                retry_refs=_sorted_unique(event.retry_ref for event in delivery_events),
                failure_receipt_refs=_sorted_unique(
                    ref for event in delivery_events for ref in event.failure_receipt_refs
                ),
                pending_approval_visible=bool(states & PENDING_CONNECTOR_DELIVERY_STATES),
                delivery_blocked_visible=bool(states & BLOCKED_CONNECTOR_DELIVERY_STATES),
                retry_posture_visible=bool(states & RETRY_CONNECTOR_DELIVERY_STATES),
                failure_posture_visible=bool(states & FAILURE_CONNECTOR_DELIVERY_STATES),
                sent_not_supported_visible="sent_not_supported" in states,
            )
        )
    return statuses


def build_connector_delivery_read_model(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    limit: int = 100,
) -> ConnectorDeliveryReadModel:
    events = connector_delivery_events_from_storage(storage, run_ref=run_ref, limit=limit)
    statuses = _build_delivery_statuses(events)
    state_counts = Counter(event.delivery_state for event in events)
    return ConnectorDeliveryReadModel(
        event_count=len(events),
        delivery_count=len(statuses),
        pending_approval_count=sum(1 for status in statuses if status.pending_approval_visible),
        blocked_count=sum(1 for status in statuses if status.delivery_blocked_visible),
        retry_count=sum(1 for status in statuses if status.retry_posture_visible),
        failure_count=sum(1 for status in statuses if status.failure_posture_visible),
        events=events,
        delivery_statuses=statuses,
        state_counts=dict(sorted(state_counts.items())),
    )
