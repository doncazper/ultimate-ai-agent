from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from enum import Enum
from ipaddress import IPv6Address
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.capability_availability import (
    CapabilityAvailabilitySnapshot,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.safe_contract_text import validate_safe_contract_text_shape
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret

from .matrix_crypto.constants import MATRIX_CRYPTO_LANES, MatrixCryptoOperation


COMMUNICATIONS_SCHEMA_VERSION = "uaa-communications.v1"
COMMUNICATIONS_MAX_PAGE_SIZE = 50
COMMUNICATIONS_MAX_PROVIDERS = 16
_SAFE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_IPV6_CANDIDATE_RE = re.compile(r"(?i)(?:[0-9a-f]{0,4}:){2,}[0-9a-f]{0,4}")
_HOSTNAME_RE = re.compile(
    r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}\b"
)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class CommunicationsProviderStatus(str, Enum):
    partial = "partial"
    unsupported = "unsupported"
    disabled = "disabled"
    unknown = "unknown"


class CommunicationsSessionStatus(str, Enum):
    not_configured = "not_configured"
    ready_for_authentication = "ready_for_authentication"
    active = "active"
    refresh_required = "refresh_required"
    soft_logged_out = "soft_logged_out"
    revoked = "revoked"
    recovery_required = "recovery_required"
    blocked = "blocked"
    unknown = "unknown"


class CommunicationsFreshnessStatus(str, Enum):
    current = "current"
    stale = "stale"
    unknown = "unknown"


class CommunicationsProjectionStatus(str, Enum):
    ready = "ready"
    empty = "empty"
    stale = "stale"
    blocked = "blocked"


class CommunicationsProjectionSourceKind(str, Enum):
    reviewed_manual_import = "reviewed_manual_import"


class CommunicationsCryptoRuntimeStatus(str, Enum):
    adapter_required = "adapter_required"
    configuration_required = "configuration_required"
    blocked = "blocked"
    ready = "ready"
    unknown = "unknown"


class CommunicationsRedactionStatus(str, Enum):
    safe_refs_only = "safe_refs_only"
    content_omitted = "content_omitted"
    unknown = "unknown"


class CommunicationsConversationKind(str, Enum):
    direct = "direct"
    room = "room"
    space = "space"
    unknown = "unknown"


class CommunicationsEventKind(str, Enum):
    message = "message"
    edit = "edit"
    reaction = "reaction"
    redaction = "redaction"
    membership = "membership"
    unknown = "unknown"


class CommunicationsAttachmentPosture(str, Enum):
    metadata_only = "metadata_only"
    unavailable = "unavailable"
    unknown = "unknown"


class CommunicationsRoomAIPolicyKind(str, Enum):
    off = "off"
    ask_each_time = "ask_each_time"
    scoped_allow = "scoped_allow"


class CommunicationsActionPosture(str, Enum):
    proposal_only = "proposal_only"
    blocked = "blocked"


class CommunicationsRollbackPosture(str, Enum):
    not_applicable = "not_applicable"
    readiness_required = "readiness_required"
    blocked = "blocked"


class CommunicationsReceiptOutcome(str, Enum):
    inspected = "inspected"
    not_executed = "not_executed"
    blocked = "blocked"


class _CommunicationsContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        payload = self.model_dump(mode="python")
        if deep:
            payload = deepcopy(payload)
        if update:
            payload.update(update)
        return self.__class__.model_validate(payload)

    @model_validator(mode="after")
    def reject_unsafe_payload(self) -> "_CommunicationsContract":
        payload = self.model_dump(mode="json")
        if contains_secret_like(payload) or contains_obvious_secret(payload):
            raise ValueError("COMMUNICATIONS_SECRET_LIKE_VALUE_REJECTED")
        for field_name in ("reason_codes", "blocker_codes"):
            values = payload.get(field_name, [])
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not _SAFE_CODE_RE.fullmatch(value)
                for value in values
            ):
                raise ValueError("COMMUNICATIONS_REASON_CODE_INVALID")
        return self


def _contains_ipv6_literal(value: str) -> bool:
    for match in _IPV6_CANDIDATE_RE.finditer(value):
        candidate = match.group(0)
        candidates = (
            (candidate, candidate[1:]) if candidate.startswith(":") else (candidate,)
        )
        for item in candidates:
            try:
                IPv6Address(item)
            except ValueError:
                continue
            return True
    return False


def _validated_ref(value: str, field_name: str) -> str:
    validate_execution_ref(value, field_name)
    lowered = value.lower()
    if (
        "@" in value
        or "." in value
        or "://" in value
        or "/" in value
        or "[" in value
        or "]" in value
        or "localhost" in lowered
        or _contains_ipv6_literal(value)
    ):
        raise ValueError(f"{field_name} contains unhashed identity or host data")
    return value


def _validated_optional_ref(value: str | None, field_name: str) -> str | None:
    if value is not None:
        _validated_ref(value, field_name)
    return value


def _validated_refs(values: list[str], field_name: str) -> list[str]:
    for value in values:
        _validated_ref(value, field_name)
    return list(dict.fromkeys(values))


def _validated_summary(value: str, field_name: str = "safe_summary") -> str:
    validate_safe_execution_text(value, field_name)
    validate_safe_contract_text_shape(value, field_name)
    if (
        "@" in value
        or "://" in value
        or _HOSTNAME_RE.search(value)
        or _IPV4_RE.search(value)
        or _contains_ipv6_literal(value)
    ):
        raise ValueError(f"{field_name} must not contain identity or network data")
    return value


def communications_idempotency_binding_ref(
    *, request_fingerprint_ref: str, idempotency_ref: str
) -> str:
    """Bind proposal idempotency to one exact safe request fingerprint."""

    _validated_ref(request_fingerprint_ref, "request_fingerprint_ref")
    _validated_ref(idempotency_ref, "idempotency_ref")
    digest = hash_text(f"{request_fingerprint_ref}|{idempotency_ref}")
    return f"binding-ref:communications:{digest}"


class CommunicationsProviderDescriptor(_CommunicationsContract):
    schema_version: Literal["uaa-communications.v1"] = COMMUNICATIONS_SCHEMA_VERSION
    provider_ref: str
    adapter_ref: str
    capability_ref: str
    provider_status: CommunicationsProviderStatus
    availability: CapabilityAvailabilitySnapshot
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)

    @field_validator("provider_ref", "adapter_ref", "capability_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_provider_ref")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_evidence_ref")

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @model_validator(mode="after")
    def validate_nested_availability(self) -> "CommunicationsProviderDescriptor":
        availability = self.availability
        for field_name in ("snapshot_ref", "capability_ref", "source_ref"):
            _validated_ref(
                getattr(availability, field_name),
                f"communications_availability_{field_name}",
            )
        for field_name in (
            "provider_ref",
            "adapter_ref",
            "declared_or_observed_version_ref",
        ):
            _validated_optional_ref(
                getattr(availability, field_name),
                f"communications_availability_{field_name}",
            )
        _validated_refs(
            availability.evidence_refs,
            "communications_availability_evidence_ref",
        )
        _validated_refs(
            availability.probe_refs,
            "communications_availability_probe_ref",
        )
        _validated_summary(
            availability.safe_summary,
            "communications_availability_safe_summary",
        )
        if (
            availability.capability_ref != self.capability_ref
            or availability.provider_ref != self.provider_ref
            or availability.adapter_ref != self.adapter_ref
        ):
            raise ValueError("COMMUNICATIONS_AVAILABILITY_SCOPE_MISMATCH")
        return self


class CommunicationsSessionPosture(_CommunicationsContract):
    provider_ref: str
    session_ref: str
    status: CommunicationsSessionStatus
    freshness: CommunicationsFreshnessStatus
    account_refs: list[str] = Field(default_factory=list, max_length=50)
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    network_performed: Literal[False] = False
    authentication_performed: Literal[False] = False
    sync_performed: Literal[False] = False

    @field_validator("provider_ref", "session_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_session_ref")

    @field_validator("account_refs")
    @classmethod
    def validate_account_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_account_ref")

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)


class CommunicationAccount(_CommunicationsContract):
    account_ref: str
    provider_ref: str
    session_ref: str
    status: CommunicationsSessionStatus
    freshness: CommunicationsFreshnessStatus
    redaction_status: CommunicationsRedactionStatus
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("account_ref", "provider_ref", "session_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_account_ref")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_evidence_ref")


class CommunicationConversation(_CommunicationsContract):
    conversation_ref: str
    account_ref: str
    provider_ref: str
    kind: CommunicationsConversationKind
    member_refs: list[str] = Field(default_factory=list, max_length=50)
    unread_count: int = Field(default=0, ge=0, le=100_000)
    freshness: CommunicationsFreshnessStatus
    redaction_status: CommunicationsRedactionStatus
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("conversation_ref", "account_ref", "provider_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_conversation_ref")

    @field_validator("member_refs", "evidence_refs")
    @classmethod
    def validate_ref_lists(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_projection_ref")


class CommunicationEvent(_CommunicationsContract):
    event_ref: str
    conversation_ref: str
    sender_ref: str
    kind: CommunicationsEventKind
    occurred_at: datetime
    content_fingerprint_ref: str
    relation_ref: str | None = None
    redaction_status: CommunicationsRedactionStatus
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True

    @field_validator(
        "event_ref",
        "conversation_ref",
        "sender_ref",
        "content_fingerprint_ref",
        "relation_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return _validated_optional_ref(value, "communications_event_ref")

    @field_validator("occurred_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("COMMUNICATIONS_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        return value


class CommunicationMember(_CommunicationsContract):
    member_ref: str
    participant_ref: str
    conversation_ref: str
    role_ref: str
    membership_ref: str

    @field_validator(
        "member_ref",
        "participant_ref",
        "conversation_ref",
        "role_ref",
        "membership_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_member_ref")


class CommunicationAttachment(_CommunicationsContract):
    attachment_ref: str
    event_ref: str
    media_ref: str
    fingerprint_ref: str
    byte_count: int | None = Field(default=None, ge=0, le=100_000_000)
    posture: CommunicationsAttachmentPosture
    redaction_status: CommunicationsRedactionStatus

    @field_validator("attachment_ref", "event_ref", "media_ref", "fingerprint_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_attachment_ref")


class CommunicationsPagination(_CommunicationsContract):
    page_size: int = Field(default=25, ge=1, le=COMMUNICATIONS_MAX_PAGE_SIZE)
    returned_count: int = Field(default=0, ge=0, le=COMMUNICATIONS_MAX_PAGE_SIZE)
    next_cursor_ref: str | None = None
    bounded: Literal[True] = True

    @field_validator("next_cursor_ref")
    @classmethod
    def validate_cursor_ref(cls, value: str | None) -> str | None:
        return _validated_optional_ref(value, "communications_cursor_ref")


class CommunicationsRoomPage(_CommunicationsContract):
    items: list[CommunicationConversation] = Field(
        default_factory=list, max_length=COMMUNICATIONS_MAX_PAGE_SIZE
    )
    pagination: CommunicationsPagination
    freshness: CommunicationsFreshnessStatus
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    message_read_performed: Literal[False] = False
    raw_content_omitted: Literal[True] = True

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @model_validator(mode="after")
    def validate_page_count(self) -> "CommunicationsRoomPage":
        if self.pagination.returned_count != len(self.items):
            raise ValueError("COMMUNICATIONS_PAGE_COUNT_MISMATCH")
        return self


class ConversationSourcePosture(_CommunicationsContract):
    source_ref: str
    source_kind: CommunicationsProjectionSourceKind
    schema_version: Literal["uaa-communications-reviewed-projection.v1"] = (
        "uaa-communications-reviewed-projection.v1"
    )
    observed_at: datetime
    freshness: CommunicationsFreshnessStatus
    coverage_ref: str
    retention_ref: str
    privacy_ref: str
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)
    connector_configured: Literal[False] = False
    live_sync_enabled: Literal[False] = False
    external_actions_enabled: Literal[False] = False
    raw_content_persisted: Literal[False] = False

    @field_validator("source_ref", "coverage_ref", "retention_ref", "privacy_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_projection_source_ref")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_projection_evidence_ref")

    @field_validator("observed_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("COMMUNICATIONS_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        return value


class ReviewedCommunicationItem(_CommunicationsContract):
    item_ref: str
    conversation_ref: str
    sender_ref: str
    item_kind: CommunicationsEventKind
    occurred_at: datetime
    safe_summary: str = Field(..., min_length=1, max_length=240)
    content_fingerprint_ref: str
    relation_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True
    reviewed_redacted_summary_only: Literal[True] = True
    raw_content_omitted: Literal[True] = True

    @field_validator(
        "item_ref",
        "conversation_ref",
        "sender_ref",
        "content_fingerprint_ref",
        "relation_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return _validated_optional_ref(value, "communications_projection_item_ref")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_projection_evidence_ref")

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @field_validator("occurred_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("COMMUNICATIONS_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        return value


class ReviewedCommunicationThread(_CommunicationsContract):
    conversation_ref: str
    channel_ref: str
    participant_refs: list[str] = Field(default_factory=list, max_length=50)
    item_refs: list[str] = Field(default_factory=list, max_length=50)
    latest_activity_at: datetime
    needs_attention: bool = False
    safe_label: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("conversation_ref", "channel_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_projection_thread_ref")

    @field_validator("participant_refs", "item_refs", "evidence_refs")
    @classmethod
    def validate_ref_lists(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_projection_ref")

    @field_validator("safe_label", "safe_summary")
    @classmethod
    def validate_summaries(cls, value: str) -> str:
        return _validated_summary(value, "communications_projection_summary")

    @field_validator("latest_activity_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("COMMUNICATIONS_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        return value


class ReviewedCommunicationsSnapshot(_CommunicationsContract):
    schema_version: Literal["uaa-communications-reviewed-projection.v1"] = (
        "uaa-communications-reviewed-projection.v1"
    )
    snapshot_ref: str
    source: ConversationSourcePosture
    threads: list[ReviewedCommunicationThread] = Field(
        default_factory=list, max_length=50
    )
    items: list[ReviewedCommunicationItem] = Field(default_factory=list, max_length=250)
    raw_content_persisted: Literal[False] = False

    @field_validator("snapshot_ref")
    @classmethod
    def validate_snapshot_ref(cls, value: str) -> str:
        return _validated_ref(value, "communications_projection_snapshot_ref")

    @model_validator(mode="after")
    def validate_projection_links(self) -> "ReviewedCommunicationsSnapshot":
        thread_refs = [thread.conversation_ref for thread in self.threads]
        item_refs = [item.item_ref for item in self.items]
        if len(thread_refs) != len(set(thread_refs)):
            raise ValueError("COMMUNICATIONS_PROJECTION_THREAD_REF_DUPLICATE")
        if len(item_refs) != len(set(item_refs)):
            raise ValueError("COMMUNICATIONS_PROJECTION_ITEM_REF_DUPLICATE")
        item_by_ref = {item.item_ref: item for item in self.items}
        for thread in self.threads:
            if any(ref not in item_by_ref for ref in thread.item_refs):
                raise ValueError("COMMUNICATIONS_PROJECTION_ITEM_REF_MISSING")
            if any(
                item_by_ref[ref].conversation_ref != thread.conversation_ref
                for ref in thread.item_refs
            ):
                raise ValueError("COMMUNICATIONS_PROJECTION_ITEM_SCOPE_MISMATCH")
        if any(item.conversation_ref not in set(thread_refs) for item in self.items):
            raise ValueError("COMMUNICATIONS_PROJECTION_THREAD_REF_MISSING")
        return self


class ReviewedCommunicationsThreadPage(_CommunicationsContract):
    status: CommunicationsProjectionStatus
    source: ConversationSourcePosture | None = None
    items: list[ReviewedCommunicationThread] = Field(
        default_factory=list, max_length=50
    )
    pagination: CommunicationsPagination
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    read_only: Literal[True] = True
    send_enabled: Literal[False] = False
    reply_enabled: Literal[False] = False
    delete_enabled: Literal[False] = False
    moderate_enabled: Literal[False] = False
    raw_content_omitted: Literal[True] = True

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @model_validator(mode="after")
    def validate_page_count(self) -> "ReviewedCommunicationsThreadPage":
        if self.pagination.returned_count != len(self.items):
            raise ValueError("COMMUNICATIONS_PAGE_COUNT_MISMATCH")
        return self


class ReviewedCommunicationThreadDetail(_CommunicationsContract):
    status: CommunicationsProjectionStatus
    source: ConversationSourcePosture
    thread: ReviewedCommunicationThread
    items: list[ReviewedCommunicationItem] = Field(default_factory=list, max_length=50)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    read_only: Literal[True] = True
    send_enabled: Literal[False] = False
    reply_enabled: Literal[False] = False
    delete_enabled: Literal[False] = False
    moderate_enabled: Literal[False] = False
    raw_content_omitted: Literal[True] = True

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)


class CommunicationsFailedSendPage(_CommunicationsContract):
    receipt_refs: list[str] = Field(
        default_factory=list, max_length=COMMUNICATIONS_MAX_PAGE_SIZE
    )
    pagination: CommunicationsPagination
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    send_performed: Literal[False] = False
    raw_content_omitted: Literal[True] = True

    @field_validator("receipt_refs")
    @classmethod
    def validate_receipt_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_receipt_ref")

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @model_validator(mode="after")
    def validate_page_count(self) -> "CommunicationsFailedSendPage":
        if self.pagination.returned_count != len(self.receipt_refs):
            raise ValueError("COMMUNICATIONS_PAGE_COUNT_MISMATCH")
        return self


class CommunicationsSecurityPosture(_CommunicationsContract):
    posture_ref: str
    provider_ref: str
    encryption_posture_ref: str
    key_lifecycle_posture_ref: str
    cache_posture_ref: str
    crypto_runtime_status: CommunicationsCryptoRuntimeStatus
    crypto_availability: CapabilityAvailabilitySnapshot
    crypto_authority_lane_refs: list[str] = Field(default_factory=list, max_length=32)
    crypto_live_executor_refs: list[str] = Field(default_factory=list, max_length=32)
    crypto_blocked_operation_refs: list[str] = Field(
        default_factory=list, max_length=32
    )
    recovery_posture_ref: str
    backup_posture_ref: str
    single_owner_posture_ref: str
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    credentials_loaded: Literal[False] = False
    crypto_initialized: Literal[False] = False
    local_cache_opened: Literal[False] = False
    recovery_material_included: Literal[False] = False
    raw_crypto_payload_included: Literal[False] = False
    request_scoped_evaluation_required: Literal[True] = True
    desktop_only: Literal[True] = True

    @field_validator(
        "posture_ref",
        "provider_ref",
        "encryption_posture_ref",
        "key_lifecycle_posture_ref",
        "cache_posture_ref",
        "recovery_posture_ref",
        "backup_posture_ref",
        "single_owner_posture_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_security_ref")

    @field_validator(
        "crypto_authority_lane_refs",
        "crypto_live_executor_refs",
        "crypto_blocked_operation_refs",
    )
    @classmethod
    def validate_crypto_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_crypto_ref")

    @model_validator(mode="after")
    def validate_crypto_truth(self) -> "CommunicationsSecurityPosture":
        if self.crypto_live_executor_refs or self.crypto_initialized:
            raise ValueError("COMMUNICATIONS_CRYPTO_LIVE_RUNTIME_NOT_PROVEN")
        if (
            self.crypto_runtime_status
            != CommunicationsCryptoRuntimeStatus.adapter_required
        ):
            raise ValueError("COMMUNICATIONS_CRYPTO_RUNTIME_STATUS_NOT_PROVEN")
        expected_lanes = [lane.lane_ref for lane in MATRIX_CRYPTO_LANES.values()]
        expected_operations = [
            f"operation-ref:matrix-crypto:{operation.value.replace('_', '-')}"
            for operation in MatrixCryptoOperation
        ]
        if self.crypto_authority_lane_refs != expected_lanes:
            raise ValueError("COMMUNICATIONS_CRYPTO_AUTHORITY_LANE_SET_MISMATCH")
        if self.crypto_blocked_operation_refs != expected_operations:
            raise ValueError("COMMUNICATIONS_CRYPTO_BLOCKED_OPERATION_SET_MISMATCH")
        return self

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)


class CommunicationsRoomAIPolicy(_CommunicationsContract):
    policy_ref: str
    conversation_ref: str
    policy: CommunicationsRoomAIPolicyKind = CommunicationsRoomAIPolicyKind.off
    context_materialization_allowed: Literal[False] = False
    memory_write_allowed: Literal[False] = False
    action_execution_allowed: Literal[False] = False
    reason_codes: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("policy_ref", "conversation_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value, "communications_ai_policy_ref")

    @model_validator(mode="after")
    def require_off_policy(self) -> "CommunicationsRoomAIPolicy":
        if self.policy != CommunicationsRoomAIPolicyKind.off:
            raise ValueError("COMMUNICATIONS_AI_POLICY_RUNTIME_AUTHORITY_NOT_ACCEPTED")
        return self


class CommunicationsActionEnvelope(_CommunicationsContract):
    envelope_ref: str
    request_ref: str
    request_fingerprint_ref: str
    capability_ref: str
    authority_domain_ref: str
    provider_ref: str
    adapter_ref: str
    target_refs: list[str] = Field(min_length=1, max_length=16)
    approval_ref: str | None = None
    authority_lease_ref: str | None = None
    idempotency_ref: str
    idempotency_binding_ref: str
    expected_receipt_ref: str
    rollback_ref: str
    safe_disable_ref: str
    posture: CommunicationsActionPosture = CommunicationsActionPosture.proposal_only
    rollback_posture: CommunicationsRollbackPosture = (
        CommunicationsRollbackPosture.readiness_required
    )
    redaction_status: CommunicationsRedactionStatus = (
        CommunicationsRedactionStatus.safe_refs_only
    )
    authority_granted: Literal[False] = False
    execution_permitted: Literal[False] = False
    mutation_performed: Literal[False] = False
    approval_ref_authorizes_execution: Literal[False] = False

    @field_validator(
        "envelope_ref",
        "request_ref",
        "request_fingerprint_ref",
        "capability_ref",
        "authority_domain_ref",
        "provider_ref",
        "adapter_ref",
        "approval_ref",
        "authority_lease_ref",
        "idempotency_ref",
        "idempotency_binding_ref",
        "expected_receipt_ref",
        "rollback_ref",
        "safe_disable_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return _validated_optional_ref(value, "communications_action_ref")

    @field_validator("target_refs")
    @classmethod
    def validate_target_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_target_ref")

    @model_validator(mode="after")
    def validate_idempotency_binding(self) -> "CommunicationsActionEnvelope":
        expected = communications_idempotency_binding_ref(
            request_fingerprint_ref=self.request_fingerprint_ref,
            idempotency_ref=self.idempotency_ref,
        )
        if self.idempotency_binding_ref != expected:
            raise ValueError("COMMUNICATIONS_IDEMPOTENCY_BINDING_MISMATCH")
        return self


class CommunicationsReceipt(_CommunicationsContract):
    receipt_ref: str
    operation_ref: str
    request_ref: str
    provider_ref: str
    account_ref: str | None = None
    conversation_ref: str | None = None
    outcome: CommunicationsReceiptOutcome
    occurred_at: datetime
    reason_codes: list[str] = Field(default_factory=list, max_length=32)
    blocker_codes: list[str] = Field(default_factory=list, max_length=32)
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)
    redaction_status: CommunicationsRedactionStatus
    safe_summary: str = Field(..., min_length=1, max_length=240)
    network_performed: Literal[False] = False
    authentication_performed: Literal[False] = False
    message_read_performed: Literal[False] = False
    message_sent: Literal[False] = False
    raw_content_stored: Literal[False] = False
    provider_payload_persisted: Literal[False] = False
    approval_or_lease_minted: Literal[False] = False

    @field_validator(
        "receipt_ref",
        "operation_ref",
        "request_ref",
        "provider_ref",
        "account_ref",
        "conversation_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return _validated_optional_ref(value, "communications_receipt_ref")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        return _validated_refs(value, "communications_evidence_ref")

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _validated_summary(value)

    @field_validator("occurred_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("COMMUNICATIONS_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        return value
