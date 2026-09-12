"""Founder-private Calendar product adoption for Queue V2 Q33.

The accepted ECO-004 Calendar models and repository remain canonical.  This
module supplies the bounded product bridge: private local key persistence,
readable day/week/month/agenda projections, exact preview/approval/commit
orchestration, content-free receipts, and encrypted portable recovery.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import stat
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseConflictError,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalCapacityError,
    AuthorityLeaseApprovalConflictError,
    AuthorityLeaseApprovalStateError,
    AuthorityLeaseApprovalStore,
    build_authority_lease_approval_requirement_for_request,
    capture_authority_lease_backend_approval,
    issue_authority_lease_from_backend_state,
)
from ultimate_ai_agent.core.control_center.work_board_adoption import (
    _fsync_directory,
    _set_windows_private_acl,
)
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MUTATION_ACTION,
    CalendarError,
    CalendarEvent,
    CalendarEventProjection,
    CalendarOccurrenceConflict,
    CalendarParticipant,
    CalendarPortableBundle,
    CalendarRecurrenceRule,
    CalendarReminder,
    CalendarRepository,
    CalendarSet,
    CalendarSetSnapshot,
    CalendarView,
    LocalCalendar,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES,
    EcosystemKeyUnavailable,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataPathResolver,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.time import utc_now


_LOGGER = logging.getLogger(__name__)


CALENDAR_ADOPTION_CONTRACT_REF = "contract-ref:queue-v2-q33-calendar-adoption:v1"
CALENDAR_ADOPTION_WORKSPACE_REF = "workspace-ref:founder-private-calendar"
CALENDAR_ADOPTION_SET_REF = "calendar-set-ref:founder-private"
CALENDAR_ADOPTION_ROUTE_REF = "POST /control-center/calendar/adoption/commit"
CALENDAR_ADOPTION_RESTORE_ROUTE_REF = (
    "POST /control-center/calendar/adoption/restore-commit"
)
CALENDAR_ADOPTION_AUTHORITY_LANE_REF = (
    "authority-lane-ref:calendar-adoption-local-write"
)
CALENDAR_ADOPTION_SAFE_DISABLE_REF = (
    "safe-disable-ref:calendar-adoption-local-write:deny"
)
CALENDAR_ADOPTION_STATE_DIR_ENV = "UAA_CALENDAR_STATE_DIR"
CALENDAR_ADOPTION_DATABASE_FILE = "calendar.sqlite3"
CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE = "adoption-receipts.json"
CALENDAR_ADOPTION_APPROVAL_TTL_MINUTES = 5
CALENDAR_ADOPTION_MAX_BACKUP_BYTES = 2 * 1024 * 1024
CALENDAR_ADOPTION_MAX_BACKUP_B64_CHARS = (
    (CALENDAR_ADOPTION_MAX_BACKUP_BYTES + 2) // 3
) * 4
CALENDAR_ADOPTION_MAX_DATABASE_CLUSTER_BYTES = 64 * 1024 * 1024
CALENDAR_ADOPTION_MAX_REVISION = 9_007_199_254_740_991
CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS = 256
CALENDAR_ADOPTION_MAX_IDEMPOTENCY_TOMBSTONES = 8_192
CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINT_BYTES = 2 * 1024 * 1024
_DEFAULT_CALENDAR_REF = "calendar-ref:founder-private:primary"
_DEFAULT_KEY_VERSION_REF = "key-version-ref:v1"
_BACKUP_AAD = b"uaa:calendar-adoption:portable-backup:v1"
_LOCK_KEY = "calendar-adoption-state"
_PENDING_APPROVAL_VALIDATION_REF = "appr_dec_000000000000"
_PENDING_AUTHORITY_DECISION_REF = (
    "authority-policy-decision-ref:calendar-adoption:pending"
)
_PENDING_AUTHORITY_LEASE_REF = "authority-lease-ref:calendar-adoption:pending"
_SAFE_REF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
)
_IS_WINDOWS = os.name == "nt"
_CALENDAR_ADOPTION_MANAGED_ROOT_NAMES = frozenset(
    {
        ".key-locks",
        ".locks",
        ".uaa-authority-approval-secrets",
        "authority",
        "keys",
        CALENDAR_ADOPTION_DATABASE_FILE,
        f"{CALENDAR_ADOPTION_DATABASE_FILE}-journal",
        f"{CALENDAR_ADOPTION_DATABASE_FILE}-shm",
        f"{CALENDAR_ADOPTION_DATABASE_FILE}-wal",
        CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE,
    }
)
_CALENDAR_ADOPTION_RESTORE_STAGE_PREFIX = ".calendar-restore."
_CALENDAR_ADOPTION_DATABASE_CLUSTER_NAMES = (
    CALENDAR_ADOPTION_DATABASE_FILE,
    f"{CALENDAR_ADOPTION_DATABASE_FILE}-journal",
    f"{CALENDAR_ADOPTION_DATABASE_FILE}-shm",
    f"{CALENDAR_ADOPTION_DATABASE_FILE}-wal",
)


class CalendarAdoptionError(RuntimeError):
    """Safe-code-only Calendar adoption failure."""


class CalendarAdoptionConflict(CalendarAdoptionError):
    """A stale revision, replay mismatch, or lifecycle conflict."""


class _CalendarAdoptionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def _hash_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _validate_ref(value: str, field_name: str) -> str:
    if (
        len(value) < 3
        or len(value) > 191
        or value[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        or any(character not in _SAFE_REF_CHARS for character in value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"CALENDAR_ADOPTION_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _aware(value: datetime, code: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(code)
    return value


def _validate_approval_validation_ref(value: str) -> str:
    if (
        not value.startswith("appr_dec_")
        or len(value) != 21
        or any(character not in "0123456789abcdef" for character in value[9:])
    ):
        raise ValueError("CALENDAR_ADOPTION_APPROVAL_VALIDATION_REF_INVALID")
    return value


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode_b64(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CalendarAdoptionError(
            "CALENDAR_ADOPTION_BACKUP_ENCODING_INVALID"
        ) from exc


class CalendarAdoptionCalendarDraft(_CalendarAdoptionModel):
    calendar_ref: str
    name: str = Field(..., repr=False)
    timezone: str
    color_ref: str | None = None

    @model_validator(mode="after")
    def validate_draft(self) -> "CalendarAdoptionCalendarDraft":
        LocalCalendar(**self.model_dump(mode="python"))
        return self

    def to_calendar(self, *, archived: bool = False) -> LocalCalendar:
        return LocalCalendar(**self.model_dump(mode="python"), archived=archived)


class CalendarAdoptionEventDraft(_CalendarAdoptionModel):
    event_ref: str
    calendar_ref: str
    title: str = Field(..., repr=False)
    description: str | None = Field(default=None, repr=False)
    location: str | None = Field(default=None, repr=False)
    starts_at: datetime
    ends_at: datetime
    timezone: str
    all_day: bool = False
    participant_items: tuple[CalendarParticipant, ...] = Field(
        default=(), max_length=1_000
    )
    reminder_items: tuple[CalendarReminder, ...] = Field(default=(), max_length=64)
    recurrence: CalendarRecurrenceRule | None = None

    @model_validator(mode="after")
    def validate_draft(self) -> "CalendarAdoptionEventDraft":
        CalendarEvent(**self.model_dump(mode="python"))
        return self

    def to_event(self, *, archived: bool = False) -> CalendarEvent:
        return CalendarEvent(**self.model_dump(mode="python"), archived=archived)


CalendarAdoptionAction = Literal[
    "initialize",
    "create_event",
    "update_event",
    "archive_event",
    "recover_event",
    "create_calendar",
    "update_calendar",
    "archive_calendar",
    "recover_calendar",
    "undo",
]


class CalendarAdoptionMutationRequest(_CalendarAdoptionModel):
    action: CalendarAdoptionAction
    expected_revision: int = Field(ge=0, le=CALENDAR_ADOPTION_MAX_REVISION)
    target_ref: str | None = None
    event: CalendarAdoptionEventDraft | None = None
    calendar: CalendarAdoptionCalendarDraft | None = None

    @model_validator(mode="after")
    def validate_action(self) -> "CalendarAdoptionMutationRequest":
        if self.target_ref is not None:
            _validate_ref(self.target_ref, "target_ref")
        event_action = self.action in {"create_event", "update_event"}
        calendar_action = self.action in {
            "initialize",
            "create_calendar",
            "update_calendar",
        }
        target_action = self.action in {
            "update_event",
            "archive_event",
            "recover_event",
            "update_calendar",
            "archive_calendar",
            "recover_calendar",
        }
        if (self.event is not None) != event_action:
            raise ValueError("CALENDAR_ADOPTION_EVENT_DRAFT_SCOPE_INVALID")
        if (self.calendar is not None) != calendar_action:
            raise ValueError("CALENDAR_ADOPTION_CALENDAR_DRAFT_SCOPE_INVALID")
        if (self.target_ref is not None) != target_action:
            raise ValueError("CALENDAR_ADOPTION_TARGET_SCOPE_INVALID")
        if self.action == "update_event" and self.event is not None:
            if self.target_ref != self.event.event_ref:
                raise ValueError("CALENDAR_ADOPTION_EVENT_IDENTITY_MISMATCH")
        if self.action == "update_calendar" and self.calendar is not None:
            if self.target_ref != self.calendar.calendar_ref:
                raise ValueError("CALENDAR_ADOPTION_CALENDAR_IDENTITY_MISMATCH")
        return self


class CalendarAdoptionMutationPreview(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-mutation-preview.v1"] = (
        "uaa-calendar-adoption-mutation-preview.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    action: CalendarAdoptionAction
    expected_revision: int
    resulting_revision: int
    target_ref: str | None
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    operation_ref: str
    safe_summary: str
    mutation_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


class CalendarAdoptionApprovalCaptureRequest(_CalendarAdoptionModel):
    mutation: CalendarAdoptionMutationRequest
    preview_ref: str
    approval_ref: str

    @model_validator(mode="after")
    def validate_refs(self) -> "CalendarAdoptionApprovalCaptureRequest":
        _validate_ref(self.preview_ref, "preview_ref")
        _validate_ref(self.approval_ref, "approval_ref")
        return self


class CalendarAdoptionApprovalReceipt(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-approval-receipt.v1"] = (
        "uaa-calendar-adoption-approval-receipt.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    approval_ref: str
    approval_validation_ref: str
    preview_ref: str
    idempotency_ref: str
    expires_at: datetime
    backend_owned: Literal[True] = True
    mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "CalendarAdoptionApprovalReceipt":
        for ref in [self.approval_ref, self.preview_ref, self.idempotency_ref]:
            _validate_ref(ref, "approval_receipt_ref")
        _validate_approval_validation_ref(self.approval_validation_ref)
        _aware(
            self.expires_at,
            "CALENDAR_ADOPTION_APPROVAL_EXPIRY_TIMEZONE_REQUIRED",
        )
        return self


class CalendarAdoptionCommitRequest(CalendarAdoptionApprovalCaptureRequest):
    pass


class CalendarAdoptionMutationReceipt(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-mutation-receipt.v1"] = (
        "uaa-calendar-adoption-mutation-receipt.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    action: CalendarAdoptionAction | Literal["restore_backup"]
    target_ref: str | None
    before_revision: int
    after_revision: int
    idempotency_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    approval_validation_ref: str
    approval_expires_at: datetime
    authority_decision_ref: str
    authority_lease_ref: str
    operation_ref: str
    receipt_ref: str
    operation_receipt_refs: tuple[str, ...]
    backup_fingerprint_ref: str | None = None
    state_ref: str
    rollback_ref: str
    safe_disable_ref: Literal[CALENDAR_ADOPTION_SAFE_DISABLE_REF] = (
        CALENDAR_ADOPTION_SAFE_DISABLE_REF
    )
    replayed: bool = False
    local_calendar_write_performed: Literal[True] = True
    external_calendar_write_performed: Literal[False] = False
    connector_write_performed: Literal[False] = False
    provider_model_call_performed: Literal[False] = False
    shell_subprocess_execution_performed: Literal[False] = False
    browser_automation_performed: Literal[False] = False
    background_scheduling_performed: Literal[False] = False
    notification_delivery_performed: Literal[False] = False
    production_authority_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "CalendarAdoptionMutationReceipt":
        for ref in [
            self.contract_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.preview_ref,
            self.approval_ref,
            self.authority_decision_ref,
            self.authority_lease_ref,
            self.operation_ref,
            self.receipt_ref,
            *self.operation_receipt_refs,
            self.state_ref,
            self.rollback_ref,
            self.safe_disable_ref,
            *([self.target_ref] if self.target_ref else []),
            *([self.backup_fingerprint_ref] if self.backup_fingerprint_ref else []),
        ]:
            _validate_ref(ref, "receipt_ref")
        _validate_approval_validation_ref(self.approval_validation_ref)
        _aware(
            self.approval_expires_at,
            "CALENDAR_ADOPTION_APPROVAL_EXPIRY_TIMEZONE_REQUIRED",
        )
        if self.after_revision != self.before_revision + 1:
            raise ValueError("CALENDAR_ADOPTION_RECEIPT_REVISION_INVALID")
        if (self.action == "restore_backup") != (
            self.backup_fingerprint_ref is not None
        ):
            raise ValueError("CALENDAR_ADOPTION_RECEIPT_BACKUP_BINDING_INVALID")
        return self


class _CalendarAdoptionReceiptCheckpoint(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-receipt-checkpoint.v1"] = (
        "uaa-calendar-adoption-receipt-checkpoint.v1"
    )
    action: CalendarAdoptionAction | Literal["restore_backup"]
    target_ref: str | None
    before_revision: int = Field(ge=0, le=CALENDAR_ADOPTION_MAX_REVISION)
    after_revision: int = Field(ge=1, le=CALENDAR_ADOPTION_MAX_REVISION)
    idempotency_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    approval_validation_ref: str
    approval_expires_at: datetime
    authority_decision_ref: str
    authority_lease_ref: str
    operation_ref: str
    backup_fingerprint_ref: str | None = None
    mutation_lifecycle_archived: bool | None = None
    approval_pending: bool = False
    receipt: CalendarAdoptionMutationReceipt | None = None

    @model_validator(mode="after")
    def validate_checkpoint(self) -> "_CalendarAdoptionReceiptCheckpoint":
        for ref in [
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.preview_ref,
            self.approval_ref,
            self.authority_decision_ref,
            self.authority_lease_ref,
            self.operation_ref,
            *([self.target_ref] if self.target_ref else []),
            *([self.backup_fingerprint_ref] if self.backup_fingerprint_ref else []),
        ]:
            _validate_ref(ref, "checkpoint_ref")
        _validate_approval_validation_ref(self.approval_validation_ref)
        _aware(
            self.approval_expires_at,
            "CALENDAR_ADOPTION_APPROVAL_EXPIRY_TIMEZONE_REQUIRED",
        )
        if self.after_revision != self.before_revision + 1:
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_REVISION_INVALID")
        if (self.action == "restore_backup") != (
            self.backup_fingerprint_ref is not None
        ):
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_BACKUP_BINDING_INVALID")
        if self.mutation_lifecycle_archived is not None and self.action not in {
            "update_event",
            "update_calendar",
        }:
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_LIFECYCLE_BINDING_INVALID")
        if self.approval_pending and (
            self.approval_validation_ref != _PENDING_APPROVAL_VALIDATION_REF
            or self.authority_decision_ref != _PENDING_AUTHORITY_DECISION_REF
            or self.authority_lease_ref != _PENDING_AUTHORITY_LEASE_REF
            or self.receipt is not None
        ):
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_APPROVAL_BINDING_INVALID")
        if self.receipt is not None and (
            self.approval_pending
            or self.authority_decision_ref == _PENDING_AUTHORITY_DECISION_REF
            or self.authority_lease_ref == _PENDING_AUTHORITY_LEASE_REF
        ):
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_AUTHORITY_PENDING")
        if self.receipt is not None and any(
            [
                self.receipt.action != self.action,
                self.receipt.target_ref != self.target_ref,
                self.receipt.before_revision != self.before_revision,
                self.receipt.after_revision != self.after_revision,
                self.receipt.idempotency_ref != self.idempotency_ref,
                self.receipt.payload_fingerprint_ref != self.payload_fingerprint_ref,
                self.receipt.preview_ref != self.preview_ref,
                self.receipt.approval_ref != self.approval_ref,
                self.receipt.approval_validation_ref != self.approval_validation_ref,
                self.receipt.approval_expires_at != self.approval_expires_at,
                self.receipt.authority_decision_ref != self.authority_decision_ref,
                self.receipt.authority_lease_ref != self.authority_lease_ref,
                self.receipt.operation_ref != self.operation_ref,
                self.receipt.backup_fingerprint_ref != self.backup_fingerprint_ref,
            ]
        ):
            raise ValueError("CALENDAR_ADOPTION_CHECKPOINT_RECEIPT_MISMATCH")
        return self


class _CalendarAdoptionIdempotencyTombstone(_CalendarAdoptionModel):
    """Compact permanent binding for a reclaimed idempotency identity."""

    schema_version: Literal["uaa-calendar-adoption-idempotency-tombstone.v1"] = (
        "uaa-calendar-adoption-idempotency-tombstone.v1"
    )
    idempotency_ref: str
    payload_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_tombstone(self) -> "_CalendarAdoptionIdempotencyTombstone":
        _validate_ref(self.idempotency_ref, "tombstone_idempotency_ref")
        _validate_ref(self.payload_fingerprint_ref, "tombstone_payload_ref")
        return self


_CalendarAdoptionCheckpointEntry = (
    _CalendarAdoptionReceiptCheckpoint | _CalendarAdoptionIdempotencyTombstone
)


class CalendarAdoptionPortableBackupRequest(_CalendarAdoptionModel):
    passphrase: str = Field(..., min_length=12, max_length=1_024, repr=False)

    @field_validator("passphrase", mode="before")
    @classmethod
    def validate_passphrase_utf8(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError("CALENDAR_ADOPTION_PASSPHRASE_UTF8_REQUIRED") from exc
        return value


class CalendarAdoptionPortableBackup(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-portable-backup.v1"] = (
        "uaa-calendar-adoption-portable-backup.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    salt: str = Field(min_length=24, max_length=24)
    nonce: str = Field(min_length=16, max_length=16)
    ciphertext: str = Field(
        min_length=24,
        max_length=CALENDAR_ADOPTION_MAX_BACKUP_B64_CHARS,
        repr=False,
    )
    ciphertext_fingerprint_ref: str
    source_revision: int = Field(ge=1, le=CALENDAR_ADOPTION_MAX_REVISION)
    created_at: datetime
    private_values_encrypted: Literal[True] = True
    key_material_included: Literal[False] = False
    raw_paths_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_backup_metadata(self) -> "CalendarAdoptionPortableBackup":
        _validate_ref(
            self.ciphertext_fingerprint_ref,
            "ciphertext_fingerprint_ref",
        )
        if (
            not self.ciphertext_fingerprint_ref.startswith(
                "ciphertext-fingerprint-ref:sha256:"
            )
            or len(self.ciphertext_fingerprint_ref) != 98
            or any(
                character not in "0123456789abcdef"
                for character in self.ciphertext_fingerprint_ref[-64:]
            )
        ):
            raise ValueError("CALENDAR_ADOPTION_BACKUP_FINGERPRINT_INVALID")
        _aware(
            self.created_at,
            "CALENDAR_ADOPTION_BACKUP_CREATED_AT_TIMEZONE_REQUIRED",
        )
        return self


class _CalendarAdoptionBackupPayload(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-backup-payload.v1"] = (
        "uaa-calendar-adoption-backup-payload.v1"
    )
    source_revision: int = Field(ge=1, le=CALENDAR_ADOPTION_MAX_REVISION)
    created_at: datetime
    bundle: CalendarPortableBundle

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        return _aware(
            value,
            "CALENDAR_ADOPTION_BACKUP_CREATED_AT_TIMEZONE_REQUIRED",
        )


class CalendarAdoptionPortableRestoreRequest(CalendarAdoptionPortableBackupRequest):
    backup: CalendarAdoptionPortableBackup


class CalendarAdoptionRestorePreview(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-restore-preview.v1"] = (
        "uaa-calendar-adoption-restore-preview.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    action: Literal["restore_backup"] = "restore_backup"
    expected_revision: int = Field(ge=0, le=CALENDAR_ADOPTION_MAX_REVISION)
    resulting_revision: int = Field(ge=1, le=CALENDAR_ADOPTION_MAX_REVISION)
    backup_revision: int = Field(ge=1, le=CALENDAR_ADOPTION_MAX_REVISION)
    calendar_count: int = Field(ge=1, le=256)
    event_count: int = Field(ge=0, le=10_000)
    current_state_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    operation_ref: str
    rollback_available: bool
    impact_status: Literal["exact", "empty_target", "unknown_current_state"]
    restore_performed: Literal[False] = False
    private_values_included: Literal[False] = False


class CalendarAdoptionRestoreApprovalCaptureRequest(
    CalendarAdoptionPortableRestoreRequest
):
    preview_ref: str
    approval_ref: str


class CalendarAdoptionRestoreCommitRequest(CalendarAdoptionPortableRestoreRequest):
    preview_ref: str
    approval_ref: str


class CalendarAdoptionReadModel(_CalendarAdoptionModel):
    schema_version: Literal["uaa-calendar-adoption-read-model.v1"] = (
        "uaa-calendar-adoption-read-model.v1"
    )
    contract_ref: Literal[CALENDAR_ADOPTION_CONTRACT_REF] = (
        CALENDAR_ADOPTION_CONTRACT_REF
    )
    status: Literal[
        "onboarding",
        "ready",
        "setup_incomplete",
        "projection_limited",
        "recovery_required",
    ]
    workspace_ref: Literal[CALENDAR_ADOPTION_WORKSPACE_REF] = (
        CALENDAR_ADOPTION_WORKSPACE_REF
    )
    calendar_set_ref: Literal[CALENDAR_ADOPTION_SET_REF] = CALENDAR_ADOPTION_SET_REF
    revision: int
    current_state_ref: str
    calendar_set_name: str | None = Field(default=None, repr=False)
    calendars: tuple[LocalCalendar, ...] = Field(default=(), repr=False)
    occurrence_items: tuple[CalendarEventProjection, ...] = Field(
        default=(), repr=False
    )
    archived_events: tuple[CalendarEvent, ...] = Field(default=(), repr=False)
    conflict_items: tuple[CalendarOccurrenceConflict, ...] = ()
    view: CalendarView
    timezone: str
    range_starts_at: datetime
    range_ends_at: datetime
    result_ref: str
    can_undo: bool
    next_safe_action: str
    backend_owned: Literal[True] = True
    local_only: Literal[True] = True
    exact_approval_required: Literal[True] = True
    backup_restore_available: Literal[True] = True
    external_calendar_write_enabled: Literal[False] = False
    connector_read_enabled: Literal[False] = False
    connector_write_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    shell_subprocess_execution_enabled: Literal[False] = False
    background_scheduling_enabled: Literal[False] = False
    notification_delivery_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False


class _FileCalendarKeyBackend:
    """Current-account-only file key boundary for the private Calendar DB."""

    backend_ref = "key-backend-ref:calendar-adoption:private-file-v1"

    def __init__(self, state_dir: Path) -> None:
        self.key_dir = state_dir / "keys"
        self.lock_manager = FileSingleWriterLockManager(state_dir / ".key-locks")

    @staticmethod
    def _set_private_permissions(path: Path, *, directory: bool) -> None:
        if _IS_WINDOWS:
            _set_windows_private_acl(path, directory=directory)
        else:
            os.chmod(path, 0o700 if directory else 0o600)

    def _ensure_key_dir(self) -> None:
        self.key_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = os.lstat(self.key_dir)
        if not stat.S_ISDIR(metadata.st_mode):
            raise EcosystemKeyUnavailable("CALENDAR_ADOPTION_KEY_DIRECTORY_UNSAFE")
        self._set_private_permissions(self.key_dir, directory=True)

    @staticmethod
    def _digest(key_item_ref: str, key_version_ref: str) -> str:
        validate_task_ref(key_item_ref, "calendar_key_item_ref")
        validate_task_ref(key_version_ref, "calendar_key_version_ref")
        return hashlib.sha256(
            _canonical_json([key_item_ref, key_version_ref])
        ).hexdigest()

    def _path(self, key_item_ref: str, key_version_ref: str) -> Path:
        return self.key_dir / f"{self._digest(key_item_ref, key_version_ref)}.key"

    def _read_key(self, path: Path) -> bytes:
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor, "rb") as handle:
                metadata = os.fstat(handle.fileno())
                path_metadata = os.lstat(path)
                if (
                    not stat.S_ISREG(metadata.st_mode)
                    or metadata.st_nlink != 1
                    or (metadata.st_dev, metadata.st_ino)
                    != (path_metadata.st_dev, path_metadata.st_ino)
                ):
                    raise EcosystemKeyUnavailable("CALENDAR_ADOPTION_KEY_OBJECT_UNSAFE")
                key = handle.read(33)
            if len(key) != 32:
                raise EcosystemKeyUnavailable("CALENDAR_ADOPTION_KEY_INVALID")
            self._set_private_permissions(path, directory=False)
            return key
        except FileNotFoundError as exc:
            raise EcosystemKeyUnavailable("ECO_KEY_NOT_FOUND") from exc
        except OSError as exc:
            raise EcosystemKeyUnavailable("CALENDAR_ADOPTION_KEY_READ_FAILED") from exc

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str:
        self._ensure_key_dir()
        path = self._path(key_item_ref, key_version_ref)
        with self.lock_manager.acquire(path.stem):
            if os.path.lexists(path):
                self._read_key(path)
            else:
                descriptor = -1
                temporary: Path | None = None
                try:
                    descriptor, name = tempfile.mkstemp(
                        dir=self.key_dir, prefix=".calendar-key.", suffix=".tmp"
                    )
                    temporary = Path(name)
                    if _IS_WINDOWS:
                        self._set_private_permissions(temporary, directory=False)
                    else:
                        os.fchmod(descriptor, 0o600)
                    with os.fdopen(descriptor, "wb") as handle:
                        descriptor = -1
                        handle.write(secrets.token_bytes(32))
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, path)
                    temporary = None
                    self._set_private_permissions(path, directory=False)
                    _fsync_directory(self.key_dir)
                except OSError as exc:
                    raise EcosystemKeyUnavailable(
                        "CALENDAR_ADOPTION_KEY_WRITE_FAILED"
                    ) from exc
                finally:
                    if descriptor >= 0:
                        os.close(descriptor)
                    if temporary is not None:
                        try:
                            temporary.unlink()
                        except OSError:
                            pass
        return _hash_ref(
            "key-receipt-ref:calendar-adoption:create",
            [key_item_ref, key_version_ref],
        )

    def _key(self, *, key_item_ref: str, key_version_ref: str) -> bytes:
        return self._read_key(self._path(key_item_ref, key_version_ref))

    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str:
        self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return _hash_ref(
            "key-receipt-ref:calendar-adoption:probe",
            [key_item_ref, key_version_ref],
        )

    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes:
        nonce = secrets.token_bytes(12)
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes:
        if len(ciphertext) < 28:
            raise EcosystemKeyUnavailable("CALENDAR_ADOPTION_CIPHERTEXT_INVALID")
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        try:
            return AESGCM(key).decrypt(ciphertext[:12], ciphertext[12:], aad)
        except InvalidTag as exc:
            raise EcosystemKeyUnavailable(
                "CALENDAR_ADOPTION_CIPHERTEXT_INVALID"
            ) from exc

    def blind_index(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        normalized_term: str,
    ) -> str:
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return hmac.new(
            key, normalized_term.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str:
        path = self._path(key_item_ref, key_version_ref)
        with self.lock_manager.acquire(path.stem):
            self._read_key(path)
            try:
                path.unlink()
                _fsync_directory(self.key_dir)
            except OSError as exc:
                raise EcosystemKeyUnavailable(
                    "CALENDAR_ADOPTION_KEY_DELETE_FAILED"
                ) from exc
        return _hash_ref(
            "key-receipt-ref:calendar-adoption:delete",
            [key_item_ref, key_version_ref],
        )


class CalendarAdoptionStore:
    """Product bridge over the canonical encrypted ECO-004 repository."""

    def __init__(self, state_dir: Path | None = None) -> None:
        selected = (
            state_dir
            or Path(
                os.environ.get(CALENDAR_ADOPTION_STATE_DIR_ENV, ".uaa/calendar")
            ).expanduser()
        )
        # Keep the configured root lexical so the safety checks can observe and
        # reject a root symlink.  Path.resolve() here would erase that identity
        # before _secure_tree() gets a chance to inspect it.
        self.state_dir = Path(os.path.abspath(selected.expanduser()))
        self.database_path = self.state_dir / CALENDAR_ADOPTION_DATABASE_FILE
        self.receipt_checkpoint_path = (
            self.state_dir / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE
        )
        self.lock_manager = FileSingleWriterLockManager(self.state_dir / ".locks")

    @classmethod
    def from_env(cls) -> "CalendarAdoptionStore":
        return cls()

    @staticmethod
    def _set_private_permissions(path: Path, *, directory: bool) -> None:
        if _IS_WINDOWS:
            _set_windows_private_acl(path, directory=directory)
        else:
            os.chmod(path, 0o700 if directory else 0o600)

    def _secure_tree(self, root: Path) -> None:
        metadata = os.lstat(root)
        if stat.S_ISLNK(metadata.st_mode):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
        if stat.S_ISREG(metadata.st_mode):
            if metadata.st_nlink != 1:
                raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
            self._set_private_permissions(root, directory=False)
            return
        if not stat.S_ISDIR(metadata.st_mode):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
        self._set_private_permissions(root, directory=True)
        for child in root.iterdir():
            self._secure_tree(child)

    @staticmethod
    def _managed_root_child(child: Path) -> bool:
        return (
            child.name in _CALENDAR_ADOPTION_MANAGED_ROOT_NAMES
            or (
                child.name.startswith(".calendar-receipts.")
                and child.name.endswith(".tmp")
            )
            or child.name.startswith(_CALENDAR_ADOPTION_RESTORE_STAGE_PREFIX)
        )

    def _validate_state_tree_before_permission_change(self) -> None:
        """Reject broad or aliased roots before chmod touches any object."""

        # Refuse filesystem roots and ordinary account roots without consulting
        # or traversing the user's home directory.  A managed Calendar root
        # must be nested beneath at least one account- or application-owned
        # directory (for example ``.../.uaa/calendar``).
        if len(self.state_dir.parts) < 4:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE")

        def validate_object(path: Path) -> None:
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode):
                raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
            if stat.S_ISREG(metadata.st_mode):
                if metadata.st_nlink != 1:
                    raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
                return
            if not stat.S_ISDIR(metadata.st_mode):
                raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
            for nested in path.iterdir():
                validate_object(nested)

        root_metadata = os.lstat(self.state_dir)
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(
            root_metadata.st_mode
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
        children = tuple(self.state_dir.iterdir())
        if any(not self._managed_root_child(child) for child in children):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE")
        for child in children:
            validate_object(child)

    def _ensure_private_state_directory(self) -> None:
        try:
            self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._validate_state_tree_before_permission_change()
            self._secure_tree(self.state_dir)
        except (OSError, CalendarAdoptionError) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE"
            ) from exc

    def _read_receipt_checkpoints(self) -> list[_CalendarAdoptionCheckpointEntry]:
        try:
            linked = os.lstat(self.receipt_checkpoint_path)
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_READ_FAILED"
            ) from exc
        if (
            not stat.S_ISREG(linked.st_mode)
            or linked.st_nlink != 1
            or linked.st_size <= 0
            or linked.st_size > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINT_BYTES
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID")
        descriptor = -1
        try:
            descriptor = os.open(
                self.receipt_checkpoint_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)
            ):
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID"
                )
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                raw = handle.read(CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINT_BYTES + 1)
            if len(raw) > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINT_BYTES:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_SIZE_INVALID"
                )
            payload = json.loads(raw)
            if not isinstance(payload, list):
                raise ValueError("checkpoint payload must be a list")
            checkpoints: list[_CalendarAdoptionCheckpointEntry] = []
            for item in payload:
                if not isinstance(item, dict):
                    raise ValueError("checkpoint entry must be an object")
                if (
                    item.get("schema_version")
                    == "uaa-calendar-adoption-idempotency-tombstone.v1"
                ):
                    checkpoints.append(
                        _CalendarAdoptionIdempotencyTombstone.model_validate(item)
                    )
                else:
                    checkpoints.append(
                        _CalendarAdoptionReceiptCheckpoint.model_validate(item)
                    )
            full_count = sum(
                isinstance(item, _CalendarAdoptionReceiptCheckpoint)
                for item in checkpoints
            )
            tombstone_count = len(checkpoints) - full_count
            if (
                full_count > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS
                or tombstone_count > CALENDAR_ADOPTION_MAX_IDEMPOTENCY_TOMBSTONES
                or len({item.idempotency_ref for item in checkpoints})
                != len(checkpoints)
            ):
                raise ValueError("checkpoint bounds or identity invalid")
            self._set_private_permissions(self.receipt_checkpoint_path, directory=False)
            return checkpoints
        except CalendarAdoptionError:
            raise
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RecursionError,
            ValueError,
        ) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _write_receipt_checkpoints(
        self, checkpoints: list[_CalendarAdoptionCheckpointEntry]
    ) -> None:
        if len({item.idempotency_ref for item in checkpoints}) != len(checkpoints):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_IDENTITY_CONFLICT"
            )
        tombstones = [
            item
            for item in checkpoints
            if isinstance(item, _CalendarAdoptionIdempotencyTombstone)
        ]
        full_checkpoints = [
            item
            for item in checkpoints
            if isinstance(item, _CalendarAdoptionReceiptCheckpoint)
        ]
        if len(full_checkpoints) > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS:
            now = utc_now()
            pending = [
                item
                for item in full_checkpoints
                if item.receipt is None and item.approval_expires_at > now
            ]
            reclaimable = [
                item
                for item in full_checkpoints
                if item.receipt is not None or item.approval_expires_at <= now
            ]
            if len(pending) > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_CAPACITY_EXHAUSTED"
                )
            reclaimable_slots = CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS - len(pending)
            retained = [
                *pending,
                *(reclaimable[-reclaimable_slots:] if reclaimable_slots else []),
            ]
            retained_refs = {item.idempotency_ref for item in retained}
            tombstones.extend(
                _CalendarAdoptionIdempotencyTombstone(
                    idempotency_ref=item.idempotency_ref,
                    payload_fingerprint_ref=item.payload_fingerprint_ref,
                )
                for item in reclaimable
                if item.idempotency_ref not in retained_refs
            )
            full_checkpoints = retained
        if len(tombstones) > CALENDAR_ADOPTION_MAX_IDEMPOTENCY_TOMBSTONES:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_CAPACITY_EXHAUSTED"
            )
        checkpoints = [*tombstones, *full_checkpoints]
        raw = _canonical_json([item.model_dump(mode="json") for item in checkpoints])
        if len(raw) > CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINT_BYTES:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_SIZE_INVALID"
            )
        descriptor = -1
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                dir=self.state_dir,
                prefix=".calendar-receipts.",
                suffix=".tmp",
            )
            temporary = Path(name)
            if _IS_WINDOWS:
                self._set_private_permissions(temporary, directory=False)
            else:
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.receipt_checkpoint_path)
            temporary = None
            self._set_private_permissions(self.receipt_checkpoint_path, directory=False)
            _fsync_directory(self.state_dir)
        except OSError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_WRITE_FAILED"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary is not None:
                try:
                    temporary.unlink()
                except OSError:
                    pass

    @staticmethod
    def _checkpoint_for(
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        idempotency_ref: str,
    ) -> _CalendarAdoptionReceiptCheckpoint | None:
        return next(
            (
                item
                for item in checkpoints
                if isinstance(item, _CalendarAdoptionReceiptCheckpoint)
                and item.idempotency_ref == idempotency_ref
            ),
            None,
        )

    @staticmethod
    def _tombstone_for(
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        idempotency_ref: str,
    ) -> _CalendarAdoptionIdempotencyTombstone | None:
        return next(
            (
                item
                for item in checkpoints
                if isinstance(item, _CalendarAdoptionIdempotencyTombstone)
                and item.idempotency_ref == idempotency_ref
            ),
            None,
        )

    def _assert_idempotency_not_retired(
        self,
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> None:
        tombstone = self._tombstone_for(checkpoints, idempotency_ref)
        if tombstone is None:
            return
        if not hmac.compare_digest(
            tombstone.payload_fingerprint_ref, payload_fingerprint_ref
        ):
            raise CalendarAdoptionConflict("CALENDAR_ADOPTION_IDEMPOTENCY_CONFLICT")
        raise CalendarAdoptionError("CALENDAR_ADOPTION_IDEMPOTENCY_RETIRED")

    def _save_checkpoint(
        self,
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        checkpoint: _CalendarAdoptionReceiptCheckpoint,
    ) -> None:
        self._assert_idempotency_not_retired(
            checkpoints,
            idempotency_ref=checkpoint.idempotency_ref,
            payload_fingerprint_ref=checkpoint.payload_fingerprint_ref,
        )
        retained = [
            item
            for item in checkpoints
            if item.idempotency_ref != checkpoint.idempotency_ref
        ]
        self._write_receipt_checkpoints([*retained, checkpoint])

    def _database_present(self) -> bool:
        try:
            root = os.lstat(self.state_dir)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE"
            ) from exc
        if stat.S_ISLNK(root.st_mode) or not stat.S_ISDIR(root.st_mode):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
        try:
            metadata = os.lstat(self.database_path)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
        return True

    def _database_cluster_state_ref(self) -> str:
        """Bind an unreadable SQLite target without materializing private bytes."""

        items: list[dict[str, Any]] = []
        total_bytes = 0
        for name in _CALENDAR_ADOPTION_DATABASE_CLUSTER_NAMES:
            path = self.state_dir / name
            try:
                linked = os.lstat(path)
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                ) from exc
            if not stat.S_ISREG(linked.st_mode) or linked.st_nlink != 1:
                raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
            if (
                linked.st_size < 0
                or linked.st_size
                > CALENDAR_ADOPTION_MAX_DATABASE_CLUSTER_BYTES - total_bytes
            ):
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_DATABASE_CLUSTER_SIZE_LIMIT"
                )
            descriptor = -1
            try:
                descriptor = os.open(
                    path,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                )
                opened = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or opened.st_nlink != 1
                    or (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)
                ):
                    raise CalendarAdoptionError("CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE")
                digest = hashlib.sha256()
                file_bytes = 0
                while chunk := os.read(descriptor, 1024 * 1024):
                    file_bytes += len(chunk)
                    if (
                        file_bytes
                        > CALENDAR_ADOPTION_MAX_DATABASE_CLUSTER_BYTES - total_bytes
                    ):
                        raise CalendarAdoptionError(
                            "CALENDAR_ADOPTION_DATABASE_CLUSTER_SIZE_LIMIT"
                        )
                    digest.update(chunk)
            except OSError as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                ) from exc
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
            items.append(
                {
                    "name": name,
                    "size": file_bytes,
                    "sha256": digest.hexdigest(),
                }
            )
            total_bytes += file_bytes
        if not items or items[0]["name"] != CALENDAR_ADOPTION_DATABASE_FILE:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE")
        return _hash_ref("state-ref:calendar-adoption-unreadable", items)

    def _repository(
        self,
        *,
        database_path: Path | None = None,
    ) -> tuple[CalendarRepository, EcosystemLocalDataPlatform, LocalApprovalAuthority]:
        authority = LocalApprovalAuthority()
        platform = EcosystemLocalDataPlatform(
            database_path=database_path or self.database_path,
            crypto_backend=_FileCalendarKeyBackend(self.state_dir),
            approval_authority=authority,
            path_resolver=InMemoryLocalDataPathResolver(),
        )
        return CalendarRepository(platform), platform, authority

    def _repository_for_commit(
        self,
    ) -> tuple[CalendarRepository, EcosystemLocalDataPlatform, LocalApprovalAuthority]:
        """Open live state while preserving the governed recovery envelope."""

        try:
            return self._repository()
        except (
            OSError,
            ValueError,
            sqlite3.Error,
            CalendarError,
            EcosystemLocalDataError,
        ) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
            ) from exc

    def _probe_existing_live_key(self) -> None:
        """Validate an existing workspace key before replacing unreadable state."""

        backend = _FileCalendarKeyBackend(self.state_dir)
        key_item_ref = (
            "key-item-ref:ecosystem:"
            f"{hashlib.sha256(_canonical_json(CALENDAR_ADOPTION_WORKSPACE_REF)).hexdigest()}"
        )
        key_path = backend._path(key_item_ref, _DEFAULT_KEY_VERSION_REF)
        try:
            os.lstat(key_path)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_KEY_RECOVERY_UNAVAILABLE"
            ) from exc
        try:
            backend.probe(
                key_item_ref=key_item_ref,
                key_version_ref=_DEFAULT_KEY_VERSION_REF,
            )
        except (OSError, EcosystemKeyUnavailable) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_KEY_RECOVERY_UNAVAILABLE"
            ) from exc

    @staticmethod
    def _empty_range(
        *, view: CalendarView, anchor: datetime, timezone_name: str
    ) -> tuple[datetime, datetime]:
        try:
            zone = ZoneInfo(timezone_name)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_TIMEZONE_INVALID") from exc
        _aware(anchor, "CALENDAR_ADOPTION_ANCHOR_INVALID")
        try:
            local = anchor.astimezone(zone)
            if view == CalendarView.day:
                start = local.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
            elif view == CalendarView.week:
                start = (local - timedelta(days=local.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end = start + timedelta(days=7)
            elif view == CalendarView.month:
                start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if start.month == 12:
                    end = start.replace(year=start.year + 1, month=1)
                else:
                    end = start.replace(month=start.month + 1)
            else:
                start = local.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=30)
        except (OverflowError, ValueError) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_ANCHOR_OUT_OF_RANGE"
            ) from exc
        return start, end

    def _empty_view(
        self,
        *,
        status: Literal["onboarding", "setup_incomplete", "recovery_required"],
        view: CalendarView,
        anchor: datetime,
        timezone_name: str,
    ) -> CalendarAdoptionReadModel:
        start, end = self._empty_range(
            view=view, anchor=anchor, timezone_name=timezone_name
        )
        return CalendarAdoptionReadModel(
            status=status,
            revision=0,
            current_state_ref=_hash_ref(
                "state-ref:calendar-adoption", {"status": status}
            ),
            view=view,
            timezone=timezone_name,
            range_starts_at=start,
            range_ends_at=end,
            result_ref=_hash_ref(
                "calendar-view-result-ref:adoption",
                {"status": status, "view": view.value, "start": start.isoformat()},
            ),
            can_undo=False,
            next_safe_action=(
                "Create the first private local calendar."
                if status == "onboarding"
                else (
                    "Retry the exact Calendar setup operation."
                    if status == "setup_incomplete"
                    else "Restore a verified encrypted Calendar backup or inspect local storage."
                )
            ),
        )

    def read_view(
        self,
        *,
        view: CalendarView = CalendarView.week,
        anchor: datetime | None = None,
        timezone_name: str = "UTC",
    ) -> CalendarAdoptionReadModel:
        selected_anchor = anchor or utc_now()
        _aware(
            selected_anchor,
            "CALENDAR_ADOPTION_VIEW_ANCHOR_TIMEZONE_REQUIRED",
        )
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_TIMEZONE_INVALID") from exc
        self._empty_range(
            view=view,
            anchor=selected_anchor,
            timezone_name=timezone_name,
        )
        if not self._database_present():
            return self._empty_view(
                status="onboarding",
                view=view,
                anchor=selected_anchor,
                timezone_name=timezone_name,
            )
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            return self._read_view_unlocked(
                view=view,
                anchor=selected_anchor,
                timezone_name=timezone_name,
            )

    def _read_view_unlocked(
        self,
        *,
        view: CalendarView = CalendarView.week,
        anchor: datetime | None = None,
        timezone_name: str = "UTC",
    ) -> CalendarAdoptionReadModel:
        selected_anchor = anchor or utc_now()
        try:
            if not self._database_present():
                return self._empty_view(
                    status="onboarding",
                    view=view,
                    anchor=selected_anchor,
                    timezone_name=timezone_name,
                )
            self._secure_tree(self.state_dir)
            repository, _platform, _authority = self._repository()
            try:
                calendar_set = repository.read(
                    workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                    calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                )
            except EcosystemLocalDataError as exc:
                if str(exc) in {"ECO_WORKSPACE_NOT_FOUND", "ECO_RECORD_NOT_FOUND"}:
                    return self._empty_view(
                        status="setup_incomplete",
                        view=view,
                        anchor=selected_anchor,
                        timezone_name=timezone_name,
                    )
                raise
            projection = repository.view(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                view=view,
                anchor=selected_anchor,
                timezone_name=timezone_name,
            )
            return CalendarAdoptionReadModel(
                status="ready",
                revision=calendar_set.version,
                current_state_ref=self._state_ref(calendar_set),
                calendar_set_name=calendar_set.name,
                calendars=calendar_set.calendars,
                occurrence_items=projection.occurrence_items,
                archived_events=tuple(
                    item for item in calendar_set.events if item.archived
                ),
                conflict_items=projection.conflict_items,
                view=projection.view,
                timezone=projection.timezone,
                range_starts_at=projection.range_starts_at,
                range_ends_at=projection.range_ends_at,
                result_ref=projection.result_ref,
                can_undo=bool(calendar_set.undo_stack),
                next_safe_action=(
                    "Create an event or select one to edit, archive, or recover."
                ),
            )
        except CalendarError as exc:
            if str(exc) in {
                "ECO_CALENDAR_CONFLICT_LIMIT_EXCEEDED",
                "ECO_CALENDAR_OCCURRENCE_LIMIT_EXCEEDED",
            }:
                start, end = self._empty_range(
                    view=view,
                    anchor=selected_anchor,
                    timezone_name=timezone_name,
                )
                return CalendarAdoptionReadModel(
                    status="projection_limited",
                    revision=calendar_set.version,
                    current_state_ref=self._state_ref(calendar_set),
                    calendar_set_name=calendar_set.name,
                    calendars=calendar_set.calendars,
                    archived_events=tuple(
                        item for item in calendar_set.events if item.archived
                    ),
                    view=view,
                    timezone=timezone_name,
                    range_starts_at=start,
                    range_ends_at=end,
                    result_ref=_hash_ref(
                        "calendar-view-result-ref:adoption",
                        {
                            "status": "projection_limited",
                            "view": view.value,
                            "start": start.isoformat(),
                            "reason": str(exc),
                        },
                    ),
                    can_undo=bool(calendar_set.undo_stack),
                    next_safe_action=(
                        "Narrow the Calendar period or switch to day view; "
                        "the stored Calendar remains intact."
                    ),
                )
            return self._empty_view(
                status="recovery_required",
                view=view,
                anchor=selected_anchor,
                timezone_name=timezone_name,
            )
        except (
            OSError,
            ValueError,
            sqlite3.Error,
            EcosystemLocalDataError,
        ):
            return self._empty_view(
                status="recovery_required",
                view=view,
                anchor=selected_anchor,
                timezone_name=timezone_name,
            )

    @staticmethod
    def _state_ref(calendar_set: CalendarSet) -> str:
        return _hash_ref(
            "state-ref:calendar-adoption", calendar_set.model_dump(mode="json")
        )

    @staticmethod
    def _payload_fingerprint(
        request: CalendarAdoptionMutationRequest, *, idempotency_ref: str
    ) -> str:
        return _hash_ref(
            "payload-fingerprint-ref:calendar-adoption",
            {
                "mutation": request.model_dump(mode="json"),
                "idempotency_ref": idempotency_ref,
            },
        )

    def _preview(
        self,
        request: CalendarAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionMutationPreview:
        _validate_ref(idempotency_ref, "idempotency_ref")
        current: CalendarSet | None = None
        if self._database_present():
            try:
                repository, _platform, _authority = self._repository()
                current = repository.read(
                    workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                    calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                )
            except EcosystemLocalDataError as exc:
                if str(exc) in {"ECO_WORKSPACE_NOT_FOUND", "ECO_RECORD_NOT_FOUND"}:
                    current = None
                else:
                    raise CalendarAdoptionError(
                        "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                    ) from exc
            except (OSError, ValueError, sqlite3.Error, CalendarError) as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                ) from exc
        if request.action == "initialize":
            if current is not None or request.expected_revision != 0:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_ALREADY_INITIALIZED")
            if request.calendar is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_CALENDAR_REQUIRED")
            projected = CalendarSet(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                name="My Calendar",
                calendars=(request.calendar.to_calendar(),),
            )
        else:
            if current is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_NOT_INITIALIZED")
            if current.version != request.expected_revision:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_STALE_REVISION")
            projected = self._project_existing(current, request)
        payload_fingerprint_ref = self._payload_fingerprint(
            request, idempotency_ref=idempotency_ref
        )
        operation_ref = _hash_ref(
            "operation-ref:calendar-adoption",
            {"payload_fingerprint_ref": payload_fingerprint_ref},
        )
        preview_ref = _hash_ref(
            "preview-ref:calendar-adoption",
            {
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "resulting_state_ref": self._state_ref(projected),
                "operation_ref": operation_ref,
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:calendar-adoption", {"preview_ref": preview_ref}
        )
        return CalendarAdoptionMutationPreview(
            action=request.action,
            expected_revision=request.expected_revision,
            resulting_revision=projected.version,
            target_ref=request.target_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            operation_ref=operation_ref,
            safe_summary=(
                "Initialize one private local Calendar workspace."
                if request.action == "initialize"
                else "Apply one exact private local Calendar lifecycle change."
            ),
        )

    def _project_existing(
        self, current: CalendarSet, request: CalendarAdoptionMutationRequest
    ) -> CalendarSet:
        calendars = list(current.calendars)
        events = list(current.events)
        if request.action in {"create_event", "update_event"}:
            assert request.event is not None
            event = request.event.to_event(
                archived=(
                    next(
                        (
                            item.archived
                            for item in events
                            if item.event_ref == request.event.event_ref
                        ),
                        False,
                    )
                    if request.action == "update_event"
                    else False
                )
            )
            index = next(
                (
                    i
                    for i, item in enumerate(events)
                    if item.event_ref == event.event_ref
                ),
                None,
            )
            if request.action == "create_event":
                if index is not None:
                    raise CalendarAdoptionConflict(
                        "CALENDAR_ADOPTION_EVENT_ALREADY_EXISTS"
                    )
                events.append(event)
            else:
                if index is None:
                    raise CalendarAdoptionConflict("CALENDAR_ADOPTION_EVENT_NOT_FOUND")
                events[index] = event
        elif request.action in {"archive_event", "recover_event"}:
            desired = request.action == "archive_event"
            index = next(
                (
                    i
                    for i, item in enumerate(events)
                    if item.event_ref == request.target_ref
                ),
                None,
            )
            if index is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_EVENT_NOT_FOUND")
            if events[index].archived == desired:
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_EVENT_LIFECYCLE_CONFLICT"
                )
            events[index] = events[index].model_copy(update={"archived": desired})
        elif request.action in {"create_calendar", "update_calendar"}:
            assert request.calendar is not None
            index = next(
                (
                    i
                    for i, item in enumerate(calendars)
                    if item.calendar_ref == request.calendar.calendar_ref
                ),
                None,
            )
            if request.action == "create_calendar":
                if index is not None:
                    raise CalendarAdoptionConflict(
                        "CALENDAR_ADOPTION_CALENDAR_ALREADY_EXISTS"
                    )
                calendars.append(request.calendar.to_calendar())
            else:
                if index is None:
                    raise CalendarAdoptionConflict(
                        "CALENDAR_ADOPTION_CALENDAR_NOT_FOUND"
                    )
                calendars[index] = request.calendar.to_calendar(
                    archived=calendars[index].archived
                )
        elif request.action in {"archive_calendar", "recover_calendar"}:
            desired = request.action == "archive_calendar"
            index = next(
                (
                    i
                    for i, item in enumerate(calendars)
                    if item.calendar_ref == request.target_ref
                ),
                None,
            )
            if index is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_CALENDAR_NOT_FOUND")
            if calendars[index].archived == desired:
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_CALENDAR_LIFECYCLE_CONFLICT"
                )
            if desired and any(
                not item.archived and item.calendar_ref == request.target_ref
                for item in events
            ):
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_CALENDAR_HAS_ACTIVE_EVENTS"
                )
            calendars[index] = calendars[index].model_copy(update={"archived": desired})
        elif request.action == "undo":
            if not current.undo_stack:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_UNDO_EMPTY")
            snapshot = current.undo_stack[-1]
            return CalendarRepository._build_set(
                workspace_ref=current.workspace_ref,
                calendar_set_ref=current.calendar_set_ref,
                version=current.version + 1,
                undo_stack=current.undo_stack[:-1],
                snapshot=snapshot,
            )
        else:
            raise CalendarAdoptionConflict("CALENDAR_ADOPTION_ACTION_INVALID")
        snapshot = CalendarSetSnapshot(
            name=current.name,
            calendars=tuple(calendars),
            events=tuple(events),
            archived=current.archived,
        )
        return CalendarRepository._with_bounded_undo(
            CalendarRepository.__new__(CalendarRepository),
            current=current,
            snapshot=snapshot,
        )

    def preview_mutation(
        self,
        request: CalendarAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionMutationPreview:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            payload_fingerprint_ref = self._payload_fingerprint(
                request, idempotency_ref=idempotency_ref
            )
            self._assert_idempotency_not_retired(
                self._read_receipt_checkpoints(),
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return self._preview(request, idempotency_ref=idempotency_ref)

    def _lease_context(
        self,
        *,
        action: str,
        expected_revision: int,
        payload_fingerprint_ref: str,
        preview_ref: str,
        approval_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        restore: bool = False,
    ) -> tuple[
        AuthorityLeaseStore, AuthorityLeaseIssueRequest, str, list[str], str, str
    ]:
        action_ref = f"action-ref:calendar-adoption:{action}"
        revision_ref = f"revision-ref:calendar-adoption:{expected_revision}"
        route_ref = (
            CALENDAR_ADOPTION_RESTORE_ROUTE_REF
            if restore
            else CALENDAR_ADOPTION_ROUTE_REF
        )
        resource_refs = [
            CALENDAR_ADOPTION_CONTRACT_REF,
            CALENDAR_ADOPTION_WORKSPACE_REF,
            CALENDAR_ADOPTION_SET_REF,
            payload_fingerprint_ref,
            preview_ref,
            approval_ref,
            operation_ref,
            idempotency_ref,
            action_ref,
            revision_ref,
        ]
        suffix = hashlib.sha256(payload_fingerprint_ref.encode()).hexdigest()[:24]
        request = AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            scope=AuthorityLeaseScope.session,
            requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=f"authority-constraint-ref:calendar-adoption:resources:{suffix}",
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resource_refs,
                    safe_summary="Restrict one Calendar change to exact reviewed refs.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"authority-constraint-ref:calendar-adoption:budget:{suffix}",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Permit one exact private local Calendar operation.",
                ),
            ],
            constraints={
                "exact_lane_ref": CALENDAR_ADOPTION_AUTHORITY_LANE_REF,
                "exact_action_ref": action_ref,
                "exact_route_ref": route_ref,
                "exact_contract_ref": CALENDAR_ADOPTION_CONTRACT_REF,
                "exact_preview_ref": preview_ref,
                "exact_approval_ref": approval_ref,
                "exact_payload_fingerprint_ref": payload_fingerprint_ref,
                "exact_operation_ref": operation_ref,
                "exact_idempotency_ref": idempotency_ref,
                "exact_revision_ref": revision_ref,
                "exact_safe_disable_ref": CALENDAR_ADOPTION_SAFE_DISABLE_REF,
            },
            decision_reason_ref="decision-reason-ref:calendar-adoption:operator-confirmed",
            duration_minutes=CALENDAR_ADOPTION_APPROVAL_TTL_MINUTES,
            safe_summary="Issue one exact operator-confirmed local Calendar write lease.",
        )
        lease_store = AuthorityLeaseStore(self.state_dir / "authority")
        lease_idempotency_ref = _hash_ref(
            "idempotency-ref:calendar-adoption-lease",
            {
                "idempotency_ref": idempotency_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
            },
        )
        return (
            lease_store,
            request,
            lease_idempotency_ref,
            resource_refs,
            action_ref,
            route_ref,
        )

    @staticmethod
    def _lease_approval_ref(*, approval_ref: str, lease_idempotency_ref: str) -> str:
        return _hash_ref(
            "approval-ref:calendar-adoption-lease-scope",
            {
                "approval_ref": approval_ref,
                "lease_idempotency_ref": lease_idempotency_ref,
            },
        )

    def _capture_approval(
        self,
        *,
        action: str,
        expected_revision: int,
        payload_fingerprint_ref: str,
        preview_ref: str,
        approval_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        restore: bool = False,
    ) -> CalendarAdoptionApprovalReceipt:
        lease_store, lease_request, lease_idempotency_ref, _, _, _ = (
            self._lease_context(
                action=action,
                expected_revision=expected_revision,
                payload_fingerprint_ref=payload_fingerprint_ref,
                preview_ref=preview_ref,
                approval_ref=approval_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                restore=restore,
            )
        )
        lease_approval_ref = self._lease_approval_ref(
            approval_ref=approval_ref,
            lease_idempotency_ref=lease_idempotency_ref,
        )
        try:
            requirement, grant = capture_authority_lease_backend_approval(
                lease_store,
                lease_request,
                idempotency_ref=lease_idempotency_ref,
                approved_by_actor_id="operator-ref:local-user",
                approval_ref=lease_approval_ref,
                approval_ttl_minutes=CALENDAR_ADOPTION_APPROVAL_TTL_MINUTES,
            )
            approved_request = lease_request.model_copy(
                update={"approval_ref": lease_approval_ref}
            )
            decision = AuthorityLeaseApprovalStore(lease_store.state_dir).validate(
                approved_request, requirement
            )
        except AuthorityLeaseApprovalConflictError as exc:
            raise CalendarAdoptionConflict(
                "CALENDAR_ADOPTION_APPROVAL_CONFLICT"
            ) from exc
        except AuthorityLeaseApprovalCapacityError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_APPROVAL_CAPACITY_EXHAUSTED"
            ) from exc
        except AuthorityLeaseApprovalStateError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_APPROVAL_STATE_INVALID"
            ) from exc
        if (
            grant is None
            or grant.expires_at is None
            or decision is None
            or not decision.allowed
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_EXACT_APPROVAL_REQUIRED")
        self._secure_tree(self.state_dir)
        return CalendarAdoptionApprovalReceipt(
            approval_ref=approval_ref,
            approval_validation_ref=decision.decision_id,
            preview_ref=preview_ref,
            idempotency_ref=idempotency_ref,
            expires_at=grant.expires_at,
        )

    def capture_approval(
        self,
        request: CalendarAdoptionApprovalCaptureRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionApprovalReceipt:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            payload_fingerprint_ref = self._payload_fingerprint(
                request.mutation, idempotency_ref=idempotency_ref
            )
            operation_ref = _hash_ref(
                "operation-ref:calendar-adoption",
                {"payload_fingerprint_ref": payload_fingerprint_ref},
            )
            checkpoints = self._read_receipt_checkpoints()
            self._assert_idempotency_not_retired(
                checkpoints,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            checkpoint = self._checkpoint_for(checkpoints, idempotency_ref)
            if checkpoint is not None:
                self._assert_checkpoint_matches(
                    checkpoint,
                    action=request.mutation.action,
                    target_ref=request.mutation.target_ref,
                    expected_revision=request.mutation.expected_revision,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    operation_ref=operation_ref,
                )
                if not checkpoint.approval_pending:
                    return CalendarAdoptionApprovalReceipt(
                        approval_ref=checkpoint.approval_ref,
                        approval_validation_ref=checkpoint.approval_validation_ref,
                        preview_ref=checkpoint.preview_ref,
                        idempotency_ref=checkpoint.idempotency_ref,
                        expires_at=checkpoint.approval_expires_at,
                    )
            preview = self._preview(request.mutation, idempotency_ref=idempotency_ref)
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_APPROVAL_SCOPE_MISMATCH"
                )
            if checkpoint is None:
                checkpoint = _CalendarAdoptionReceiptCheckpoint(
                    action=preview.action,
                    target_ref=preview.target_ref,
                    before_revision=preview.expected_revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=_PENDING_APPROVAL_VALIDATION_REF,
                    approval_expires_at=utc_now(),
                    authority_decision_ref=_PENDING_AUTHORITY_DECISION_REF,
                    authority_lease_ref=_PENDING_AUTHORITY_LEASE_REF,
                    operation_ref=preview.operation_ref,
                    approval_pending=True,
                )
                self._save_checkpoint(checkpoints, checkpoint)
            receipt = self._capture_approval(
                action=preview.action,
                expected_revision=preview.expected_revision,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
            )
            captured = checkpoint.model_copy(
                update={
                    "approval_validation_ref": receipt.approval_validation_ref,
                    "approval_expires_at": receipt.expires_at,
                    "approval_pending": False,
                }
            )
            self._save_checkpoint(checkpoints, captured)
            return receipt

    def _authorize(
        self,
        *,
        action: str,
        expected_revision: int,
        payload_fingerprint_ref: str,
        preview_ref: str,
        approval_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        restore: bool = False,
    ) -> tuple[AuthorityLeaseStore, AuthorityLease, str, str, datetime]:
        (
            lease_store,
            lease_request,
            lease_idempotency_ref,
            resource_refs,
            action_ref,
            route_ref,
        ) = self._lease_context(
            action=action,
            expected_revision=expected_revision,
            payload_fingerprint_ref=payload_fingerprint_ref,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            restore=restore,
        )
        requirement = build_authority_lease_approval_requirement_for_request(
            lease_request, idempotency_ref=lease_idempotency_ref
        )
        lease_approval_ref = self._lease_approval_ref(
            approval_ref=approval_ref, lease_idempotency_ref=lease_idempotency_ref
        )
        store = AuthorityLeaseApprovalStore(lease_store.state_dir)
        record = store.resolve(lease_approval_ref)
        if record is None or record.grant.expires_at is None:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_EXACT_APPROVAL_REQUIRED")
        maximum_expiry = record.grant.created_at + timedelta(
            minutes=CALENDAR_ADOPTION_APPROVAL_TTL_MINUTES
        )
        if (
            record.grant.expires_at > maximum_expiry
            or record.grant.expires_at <= datetime.now(timezone.utc)
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_APPROVAL_EXPIRED")
        approved_request = lease_request.model_copy(
            update={"approval_ref": lease_approval_ref}
        )
        try:
            approval_decision = store.validate(approved_request, requirement)
            lease, issue_receipt = issue_authority_lease_from_backend_state(
                lease_store, approved_request, idempotency_ref=lease_idempotency_ref
            )
        except AuthorityLeaseConflictError as exc:
            raise CalendarAdoptionConflict(
                "CALENDAR_ADOPTION_AUTHORITY_IDEMPOTENCY_CONFLICT"
            ) from exc
        except AuthorityLeaseApprovalStateError as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_AUTHORITY_STATE_INVALID"
            ) from exc
        if (
            approval_decision is None
            or not approval_decision.allowed
            or lease is None
            or lease.status == "revoked"
            or issue_receipt.status not in {"issued", "replayed"}
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_LEASE_ISSUANCE_DENIED")
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=action_ref,
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.write,
                safe_summary="Evaluate one exact private local Calendar operation.",
                resource_refs=resource_refs,
                route_ref=route_ref,
                lane_ref=CALENDAR_ADOPTION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget, value=1
                    )
                ],
                rollback_ref=_hash_ref(
                    "rollback-ref:calendar-adoption", {"preview_ref": preview_ref}
                ),
                safe_disable_ref=CALENDAR_ADOPTION_SAFE_DISABLE_REF,
            ),
            [lease],
        )
        if decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            self._revoke_lease(lease_store, lease)
            raise CalendarAdoptionError("CALENDAR_ADOPTION_AUTHORITY_DENIED")
        return (
            lease_store,
            lease,
            decision.decision_ref,
            approval_decision.decision_id,
            record.grant.expires_at,
        )

    @staticmethod
    def _revoke_lease(
        lease_store: AuthorityLeaseStore,
        lease: AuthorityLease,
    ) -> bool:
        if lease.status == "revoked":
            return True
        try:
            lease_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=lease.lease_ref,
                    decision_reason_ref=(
                        "decision-reason-ref:calendar-adoption:commit-failed"
                    ),
                    safe_summary=(
                        "Revoke the exact Calendar lease after the local operation "
                        "failed."
                    ),
                ),
                idempotency_ref=_hash_ref(
                    "idempotency-ref:calendar-adoption-lease-revoke",
                    {"lease_ref": lease.lease_ref},
                ),
            )
        except Exception:
            _LOGGER.warning("CALENDAR_ADOPTION_LEASE_REVOCATION_FAILED")
            return False
        return True

    @staticmethod
    def _repository_approval(
        authority: LocalApprovalAuthority,
        *,
        action: str,
        resource_refs: tuple[str, ...],
        outer_approval_ref: str,
        expires_at: datetime,
    ):
        suffix = hashlib.sha256(
            _canonical_json([action, resource_refs, outer_approval_ref])
        ).hexdigest()[:24]
        request = ApprovalRequest(
            approval_request_id=f"approval-request-ref:calendar-adoption:{suffix}",
            run_id="run-ref:calendar-adoption",
            subject_type=ApprovalSubjectType.kernel_task,
            subject_id="subject-ref:calendar-adoption",
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="operator-ref:local-user",
                authority_source=AuthoritySource.manual_operator_action,
                approval_ref=outer_approval_ref,
            ),
            requested_action=action,
            purpose="Apply one exact approved private local Calendar operation.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.user_private,
                source="source-ref:calendar-adoption",
                requires_redaction=True,
            ),
            resource_refs=list(resource_refs),
            expires_at=expires_at,
        )
        authority.create_request(request)
        grant = authority.grant(
            request.approval_request_id,
            approved_by_actor_id="operator-ref:local-user",
            expires_at=expires_at,
            approval_ref=_hash_ref(
                "approval-ref:calendar-adoption-core",
                {"outer_approval_ref": outer_approval_ref, "action": action},
            ),
        )
        return request.to_validation_request(grant.approval_ref)

    def _mutation_material(
        self,
        repository: CalendarRepository,
        request: CalendarAdoptionMutationRequest,
        *,
        lifecycle_archived: bool | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if request.action in {"create_event", "update_event"}:
            assert request.event is not None
            kind = "add_event" if request.action == "create_event" else "update_event"
            archived = False
            if request.action == "update_event":
                archived = (
                    lifecycle_archived
                    if lifecycle_archived is not None
                    else self._mutation_lifecycle_archived(repository, request)
                )
            return kind, {
                "event": request.event.to_event(archived=archived).model_dump(
                    mode="json"
                )
            }
        if request.action in {"archive_event", "recover_event"}:
            return (
                "archive_event"
                if request.action == "archive_event"
                else "restore_event",
                {"event_ref": request.target_ref},
            )
        if request.action in {"create_calendar", "update_calendar"}:
            assert request.calendar is not None
            kind = (
                "add_calendar"
                if request.action == "create_calendar"
                else "update_calendar"
            )
            archived = False
            if request.action == "update_calendar":
                archived = (
                    lifecycle_archived
                    if lifecycle_archived is not None
                    else self._mutation_lifecycle_archived(repository, request)
                )
            return kind, {
                "calendar": request.calendar.to_calendar(archived=archived).model_dump(
                    mode="json"
                )
            }
        if request.action in {"archive_calendar", "recover_calendar"}:
            return (
                "archive_calendar"
                if request.action == "archive_calendar"
                else "restore_calendar",
                {"calendar_ref": request.target_ref},
            )
        return request.action, {}

    def _mutation_lifecycle_archived(
        self,
        repository: CalendarRepository,
        request: CalendarAdoptionMutationRequest,
    ) -> bool | None:
        if request.action not in {"update_event", "update_calendar"}:
            return None
        current = repository.read(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
        )
        if request.action == "update_event":
            prior = next(
                (
                    item
                    for item in current.events
                    if item.event_ref == request.target_ref
                ),
                None,
            )
            if prior is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_EVENT_NOT_FOUND")
        else:
            prior = next(
                (
                    item
                    for item in current.calendars
                    if item.calendar_ref == request.target_ref
                ),
                None,
            )
            if prior is None:
                raise CalendarAdoptionConflict("CALENDAR_ADOPTION_CALENDAR_NOT_FOUND")
        return prior.archived

    def _recover_existing_receipt(
        self,
        repository: CalendarRepository,
        request: CalendarAdoptionMutationRequest,
        *,
        operation_ref: str,
        idempotency_ref: str,
        lifecycle_archived: bool | None = None,
    ) -> UnitOfWorkReceipt | None:
        if request.action == "undo":
            return repository.recover_undo_receipt(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                expected_version=request.expected_revision,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            )
        if request.action == "initialize":
            assert request.calendar is not None
            calendar_set = CalendarSet(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                name="My Calendar",
                calendars=(request.calendar.to_calendar(),),
            )
            return repository.recover_create_receipt(
                calendar_set=calendar_set,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            )
        kind, material = self._mutation_material(
            repository,
            request,
            lifecycle_archived=lifecycle_archived,
        )
        return repository.recover_mutation_receipt(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
            expected_version=request.expected_revision,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            mutation_kind=kind,
            mutation_material=material,
        )

    def _apply_repository_mutation(
        self,
        repository: CalendarRepository,
        authority: LocalApprovalAuthority,
        request: CalendarAdoptionMutationRequest,
        *,
        operation_ref: str,
        idempotency_ref: str,
        outer_approval_ref: str,
        approval_expires_at: datetime,
    ) -> UnitOfWorkReceipt:
        if request.action == "initialize":
            assert request.calendar is not None
            workspace_approval = self._repository_approval(
                authority,
                action="ecosystem.local_data.create_workspace",
                resource_refs=(
                    CALENDAR_ADOPTION_WORKSPACE_REF,
                    _DEFAULT_KEY_VERSION_REF,
                ),
                outer_approval_ref=outer_approval_ref,
                expires_at=approval_expires_at,
            )
            repository.platform.create_workspace(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                key_version_ref=_DEFAULT_KEY_VERSION_REF,
                approval=workspace_approval,
            )
            calendar_set = CalendarSet(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                name="My Calendar",
                calendars=(request.calendar.to_calendar(),),
            )
            resources = repository.mutation_resource_refs(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                record_ref=CALENDAR_ADOPTION_SET_REF,
            )
            approval = self._repository_approval(
                authority,
                action=ECO_CALENDAR_MUTATION_ACTION,
                resource_refs=resources,
                outer_approval_ref=outer_approval_ref,
                expires_at=approval_expires_at,
            )
            return repository.create_calendar_set(
                calendar_set=calendar_set,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
            )
        resources = repository.mutation_resource_refs(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            idempotency_ref=idempotency_ref,
            operation_ref=operation_ref,
            record_ref=CALENDAR_ADOPTION_SET_REF,
        )
        approval = self._repository_approval(
            authority,
            action=ECO_CALENDAR_MUTATION_ACTION,
            resource_refs=resources,
            outer_approval_ref=outer_approval_ref,
            expires_at=approval_expires_at,
        )
        common = dict(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
            expected_version=request.expected_revision,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )
        if request.action == "create_event":
            assert request.event is not None
            return repository.add_event(event=request.event.to_event(), **common)
        if request.action == "update_event":
            assert request.event is not None
            current = repository.read(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
            )
            prior = next(
                item for item in current.events if item.event_ref == request.target_ref
            )
            return repository.update_event(
                event=request.event.to_event(archived=prior.archived), **common
            )
        if request.action == "archive_event":
            return repository.archive_event(event_ref=request.target_ref, **common)
        if request.action == "recover_event":
            return repository.restore_event(event_ref=request.target_ref, **common)
        if request.action == "create_calendar":
            assert request.calendar is not None
            return repository.add_calendar(
                calendar_item=request.calendar.to_calendar(), **common
            )
        if request.action == "update_calendar":
            assert request.calendar is not None
            current = repository.read(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
            )
            prior = next(
                item
                for item in current.calendars
                if item.calendar_ref == request.target_ref
            )
            return repository.update_calendar(
                calendar_item=request.calendar.to_calendar(archived=prior.archived),
                **common,
            )
        if request.action == "archive_calendar":
            return repository.archive_calendar(
                calendar_ref=request.target_ref, **common
            )
        if request.action == "recover_calendar":
            return repository.restore_calendar(
                calendar_ref=request.target_ref, **common
            )
        if request.action == "undo":
            return repository.undo(**common)
        raise CalendarAdoptionConflict("CALENDAR_ADOPTION_ACTION_INVALID")

    @staticmethod
    def _assert_checkpoint_matches(
        checkpoint: _CalendarAdoptionReceiptCheckpoint,
        *,
        action: CalendarAdoptionAction | Literal["restore_backup"],
        target_ref: str | None,
        expected_revision: int,
        payload_fingerprint_ref: str,
        preview_ref: str,
        approval_ref: str,
        operation_ref: str,
        backup_fingerprint_ref: str | None = None,
    ) -> None:
        if any(
            [
                checkpoint.action != action,
                checkpoint.target_ref != target_ref,
                checkpoint.before_revision != expected_revision,
                checkpoint.payload_fingerprint_ref != payload_fingerprint_ref,
                checkpoint.preview_ref != preview_ref,
                checkpoint.approval_ref != approval_ref,
                checkpoint.operation_ref != operation_ref,
                checkpoint.backup_fingerprint_ref != backup_fingerprint_ref,
            ]
        ):
            raise CalendarAdoptionConflict("CALENDAR_ADOPTION_IDEMPOTENCY_CONFLICT")

    @staticmethod
    def _complete_checkpoint(
        checkpoint: _CalendarAdoptionReceiptCheckpoint,
        unit: UnitOfWorkReceipt,
    ) -> _CalendarAdoptionReceiptCheckpoint:
        if (
            checkpoint.approval_pending
            or checkpoint.authority_decision_ref == _PENDING_AUTHORITY_DECISION_REF
            or checkpoint.authority_lease_ref == _PENDING_AUTHORITY_LEASE_REF
        ):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INCOMPLETE"
            )
        receipt = CalendarAdoptionMutationReceipt(
            action=checkpoint.action,
            target_ref=checkpoint.target_ref,
            before_revision=checkpoint.before_revision,
            after_revision=checkpoint.after_revision,
            idempotency_ref=checkpoint.idempotency_ref,
            payload_fingerprint_ref=checkpoint.payload_fingerprint_ref,
            preview_ref=checkpoint.preview_ref,
            approval_ref=checkpoint.approval_ref,
            approval_validation_ref=checkpoint.approval_validation_ref,
            approval_expires_at=checkpoint.approval_expires_at,
            authority_decision_ref=checkpoint.authority_decision_ref,
            authority_lease_ref=checkpoint.authority_lease_ref,
            operation_ref=checkpoint.operation_ref,
            receipt_ref=unit.receipt_ref,
            operation_receipt_refs=unit.operation_receipt_refs,
            backup_fingerprint_ref=checkpoint.backup_fingerprint_ref,
            state_ref=_hash_ref(
                "state-ref:calendar-adoption-receipt",
                {
                    "receipt_ref": unit.receipt_ref,
                    "operation_receipt_refs": unit.operation_receipt_refs,
                    "after_revision": checkpoint.after_revision,
                },
            ),
            rollback_ref=_hash_ref(
                "rollback-ref:calendar-adoption",
                {"receipt_ref": unit.receipt_ref, "action": "undo"},
            ),
            replayed=False,
        )
        return checkpoint.model_copy(update={"receipt": receipt})

    @classmethod
    def _assert_checkpoint_receipt_matches_unit(
        cls,
        checkpoint: _CalendarAdoptionReceiptCheckpoint,
        unit: UnitOfWorkReceipt,
    ) -> None:
        if checkpoint.receipt is None:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INCOMPLETE"
            )
        expected = cls._complete_checkpoint(
            checkpoint.model_copy(update={"receipt": None}),
            unit,
        ).receipt
        assert expected is not None
        if checkpoint.receipt.model_copy(update={"replayed": False}) != expected:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_DURABLE_MISMATCH"
            )

    def _commit_authorized_mutation(
        self,
        *,
        request: CalendarAdoptionCommitRequest,
        preview: CalendarAdoptionMutationPreview,
        idempotency_ref: str,
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        checkpoint: _CalendarAdoptionReceiptCheckpoint | None,
        repository: CalendarRepository | None,
        authority: LocalApprovalAuthority | None,
        lease: AuthorityLease,
        authority_decision_ref: str,
        approval_validation_ref: str,
        approval_expires_at: datetime,
    ) -> CalendarAdoptionMutationReceipt:
        if repository is None or authority is None:
            repository, _platform, authority = self._repository_for_commit()
        mutation_lifecycle_archived = (
            checkpoint.mutation_lifecycle_archived
            if checkpoint is not None
            and checkpoint.mutation_lifecycle_archived is not None
            else self._mutation_lifecycle_archived(repository, request.mutation)
        )
        if checkpoint is None:
            checkpoint = _CalendarAdoptionReceiptCheckpoint(
                action=preview.action,
                target_ref=preview.target_ref,
                before_revision=preview.expected_revision,
                after_revision=preview.resulting_revision,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                approval_validation_ref=approval_validation_ref,
                approval_expires_at=approval_expires_at,
                authority_decision_ref=authority_decision_ref,
                authority_lease_ref=lease.lease_ref,
                operation_ref=preview.operation_ref,
                mutation_lifecycle_archived=mutation_lifecycle_archived,
            )
            self._save_checkpoint(checkpoints, checkpoint)
            checkpoints = [*checkpoints, checkpoint]
        elif checkpoint.approval_pending:
            checkpoint = checkpoint.model_copy(
                update={
                    "approval_validation_ref": approval_validation_ref,
                    "approval_expires_at": approval_expires_at,
                    "authority_decision_ref": authority_decision_ref,
                    "authority_lease_ref": lease.lease_ref,
                    "mutation_lifecycle_archived": mutation_lifecycle_archived,
                    "approval_pending": False,
                }
            )
            self._save_checkpoint(checkpoints, checkpoint)
        elif (
            checkpoint.authority_decision_ref == _PENDING_AUTHORITY_DECISION_REF
            and checkpoint.authority_lease_ref == _PENDING_AUTHORITY_LEASE_REF
        ):
            checkpoint = checkpoint.model_copy(
                update={
                    "approval_validation_ref": approval_validation_ref,
                    "approval_expires_at": approval_expires_at,
                    "authority_decision_ref": authority_decision_ref,
                    "authority_lease_ref": lease.lease_ref,
                    "mutation_lifecycle_archived": mutation_lifecycle_archived,
                }
            )
            self._save_checkpoint(checkpoints, checkpoint)
        elif any(
            [
                checkpoint.authority_decision_ref != authority_decision_ref,
                checkpoint.authority_lease_ref != lease.lease_ref,
                checkpoint.approval_validation_ref != approval_validation_ref,
                checkpoint.approval_expires_at != approval_expires_at,
            ]
        ):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_AUTHORITY_MISMATCH"
            )
        if checkpoint.mutation_lifecycle_archived != mutation_lifecycle_archived:
            checkpoint = checkpoint.model_copy(
                update={
                    "mutation_lifecycle_archived": mutation_lifecycle_archived,
                }
            )
            self._save_checkpoint(checkpoints, checkpoint)
        try:
            unit = self._apply_repository_mutation(
                repository,
                authority,
                request.mutation,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
                outer_approval_ref=preview.approval_ref,
                approval_expires_at=approval_expires_at,
            )
        except (OSError, sqlite3.Error, EcosystemKeyUnavailable) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
            ) from exc
        self._secure_tree(self.state_dir)
        completed = self._complete_checkpoint(checkpoint, unit)
        self._save_checkpoint(checkpoints, completed)
        assert completed.receipt is not None
        return completed.receipt

    def commit_mutation(
        self,
        request: CalendarAdoptionCommitRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionMutationReceipt:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            _validate_ref(idempotency_ref, "idempotency_ref")
            payload_fingerprint_ref = self._payload_fingerprint(
                request.mutation, idempotency_ref=idempotency_ref
            )
            operation_ref = _hash_ref(
                "operation-ref:calendar-adoption",
                {"payload_fingerprint_ref": payload_fingerprint_ref},
            )
            checkpoints = self._read_receipt_checkpoints()
            self._assert_idempotency_not_retired(
                checkpoints,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            checkpoint = self._checkpoint_for(checkpoints, idempotency_ref)
            repository: CalendarRepository | None = None
            authority: LocalApprovalAuthority | None = None
            if self._database_present():
                repository, _platform, authority = self._repository_for_commit()
            replay: UnitOfWorkReceipt | None = None
            if checkpoint is not None:
                self._assert_checkpoint_matches(
                    checkpoint,
                    action=request.mutation.action,
                    target_ref=request.mutation.target_ref,
                    expected_revision=request.mutation.expected_revision,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    operation_ref=operation_ref,
                )
                if repository is not None:
                    try:
                        replay = self._recover_existing_receipt(
                            repository,
                            request.mutation,
                            operation_ref=operation_ref,
                            idempotency_ref=idempotency_ref,
                            lifecycle_archived=(checkpoint.mutation_lifecycle_archived),
                        )
                    except EcosystemLocalDataError as exc:
                        if str(exc) not in {
                            "ECO_WORKSPACE_NOT_FOUND",
                            "ECO_RECORD_NOT_FOUND",
                        }:
                            raise CalendarAdoptionError(
                                "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                            ) from exc
                        replay = None
                if replay is not None:
                    if checkpoint.receipt is not None:
                        self._assert_checkpoint_receipt_matches_unit(
                            checkpoint,
                            replay,
                        )
                        return checkpoint.receipt.model_copy(update={"replayed": True})
                    completed = self._complete_checkpoint(checkpoint, replay)
                    self._save_checkpoint(checkpoints, completed)
                    assert completed.receipt is not None
                    return completed.receipt.model_copy(update={"replayed": True})
                if checkpoint.receipt is not None:
                    raise CalendarAdoptionError(
                        "CALENDAR_ADOPTION_DURABLE_RECEIPT_MISSING"
                    )
            preview = self._preview(request.mutation, idempotency_ref=idempotency_ref)
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_COMMIT_SCOPE_MISMATCH"
                )
            if checkpoint is None and repository is not None:
                try:
                    replay = self._recover_existing_receipt(
                        repository,
                        request.mutation,
                        operation_ref=operation_ref,
                        idempotency_ref=idempotency_ref,
                    )
                except EcosystemLocalDataError as exc:
                    if str(exc) not in {
                        "ECO_WORKSPACE_NOT_FOUND",
                        "ECO_RECORD_NOT_FOUND",
                    }:
                        raise CalendarAdoptionError(
                            "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                        ) from exc
                if replay is not None:
                    raise CalendarAdoptionError(
                        "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_MISSING"
                    )
            (
                lease_store,
                lease,
                authority_decision_ref,
                approval_validation_ref,
                approval_expires_at,
            ) = self._authorize(
                action=preview.action,
                expected_revision=preview.expected_revision,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
            )
            try:
                return self._commit_authorized_mutation(
                    request=request,
                    preview=preview,
                    idempotency_ref=idempotency_ref,
                    checkpoints=checkpoints,
                    checkpoint=checkpoint,
                    repository=repository,
                    authority=authority,
                    lease=lease,
                    authority_decision_ref=authority_decision_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                )
            except Exception:
                self._revoke_lease(lease_store, lease)
                raise

    @staticmethod
    def _derive_backup_key(passphrase: str, salt: bytes) -> bytes:
        return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
            passphrase.encode("utf-8")
        )

    def create_portable_backup(
        self, request: CalendarAdoptionPortableBackupRequest
    ) -> CalendarAdoptionPortableBackup:
        if not self._database_present():
            raise CalendarAdoptionError("CALENDAR_ADOPTION_BACKUP_EMPTY")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            try:
                repository, _platform, _authority = self._repository()
                calendar_set = repository.read(
                    workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                    calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                )
                bundle = repository.export_bundle(
                    workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                    calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                )
            except (
                OSError,
                ValueError,
                sqlite3.Error,
                CalendarError,
                EcosystemLocalDataError,
            ) as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                ) from exc
            created_at = datetime.now(timezone.utc)
            payload = _CalendarAdoptionBackupPayload(
                source_revision=calendar_set.version,
                created_at=created_at,
                bundle=bundle,
            )
            plaintext = _canonical_json(payload.model_dump(mode="json"))
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)
            ciphertext = AESGCM(
                self._derive_backup_key(request.passphrase, salt)
            ).encrypt(nonce, plaintext, _BACKUP_AAD)
            if len(ciphertext) > CALENDAR_ADOPTION_MAX_BACKUP_BYTES:
                raise CalendarAdoptionError("CALENDAR_ADOPTION_BACKUP_SIZE_LIMIT")
            return CalendarAdoptionPortableBackup(
                salt=_b64(salt),
                nonce=_b64(nonce),
                ciphertext=_b64(ciphertext),
                ciphertext_fingerprint_ref=(
                    "ciphertext-fingerprint-ref:sha256:"
                    f"{hashlib.sha256(ciphertext).hexdigest()}"
                ),
                source_revision=calendar_set.version,
                created_at=created_at,
            )

    def _open_backup(
        self, request: CalendarAdoptionPortableRestoreRequest
    ) -> CalendarPortableBundle:
        salt = _decode_b64(request.backup.salt)
        nonce = _decode_b64(request.backup.nonce)
        ciphertext = _decode_b64(request.backup.ciphertext)
        if (
            len(salt) != 16
            or len(nonce) != 12
            or len(ciphertext) > CALENDAR_ADOPTION_MAX_BACKUP_BYTES
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_BACKUP_INVALID")
        expected = (
            "ciphertext-fingerprint-ref:sha256:"
            f"{hashlib.sha256(ciphertext).hexdigest()}"
        )
        if not hmac.compare_digest(expected, request.backup.ciphertext_fingerprint_ref):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_BACKUP_FINGERPRINT_MISMATCH")
        try:
            plaintext = AESGCM(
                self._derive_backup_key(request.passphrase, salt)
            ).decrypt(nonce, ciphertext, _BACKUP_AAD)
            payload = _CalendarAdoptionBackupPayload.model_validate(
                json.loads(plaintext)
            )
        except (
            InvalidTag,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RecursionError,
            ValueError,
        ) as exc:
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_BACKUP_DECRYPT_FAILED"
            ) from exc
        if (
            payload.source_revision != request.backup.source_revision
            or payload.created_at != request.backup.created_at
        ):
            raise CalendarAdoptionError("CALENDAR_ADOPTION_BACKUP_METADATA_MISMATCH")
        bundle = payload.bundle
        if any(event.task_ref is not None for event in bundle.events):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_TASK_BLOCK_RESTORE_UNAVAILABLE"
            )
        return bundle

    def _restore_preview(
        self,
        request: CalendarAdoptionPortableRestoreRequest,
        *,
        idempotency_ref: str,
    ) -> tuple[CalendarAdoptionRestorePreview, CalendarPortableBundle]:
        _validate_ref(idempotency_ref, "idempotency_ref")
        bundle = self._open_backup(request)
        current: CalendarSet | None = None
        current_readable = True
        if self._database_present():
            try:
                repository, _platform, _authority = self._repository()
                current = repository.read(
                    workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                    calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                )
            except EcosystemLocalDataError as exc:
                if isinstance(exc, EcosystemKeyUnavailable):
                    raise CalendarAdoptionError(
                        "CALENDAR_ADOPTION_KEY_RECOVERY_UNAVAILABLE"
                    ) from exc
                if str(exc) not in {
                    "ECO_WORKSPACE_NOT_FOUND",
                    "ECO_RECORD_NOT_FOUND",
                }:
                    current_readable = False
            except (OSError, sqlite3.Error, CalendarError):
                current_readable = False
            if not current_readable:
                self._probe_existing_live_key()
        else:
            self._probe_existing_live_key()
        expected_revision = current.version if current is not None else 0
        resulting_revision = expected_revision + 1
        rollback_available = False
        snapshot = CalendarSetSnapshot(
            name=bundle.name,
            calendars=bundle.calendars,
            events=bundle.events,
            archived=False,
        )
        if current is not None:
            restored = CalendarRepository._with_bounded_undo(
                CalendarRepository.__new__(CalendarRepository),
                current=current,
                snapshot=snapshot,
            )
            rollback_available = bool(restored.undo_stack)
        else:
            restored = CalendarRepository._build_set(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                version=resulting_revision,
                undo_stack=(),
                snapshot=snapshot,
            )
        if (
            CalendarRepository._record_plaintext_size(restored)
            > ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES
        ):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RESTORE_PAYLOAD_LIMIT_EXCEEDED"
            )
        current_state_ref = (
            self._state_ref(current)
            if current is not None
            else (
                _hash_ref(
                    "state-ref:calendar-adoption",
                    {"status": "empty"},
                )
                if current_readable
                else self._database_cluster_state_ref()
            )
        )
        payload_fingerprint_ref = _hash_ref(
            "payload-fingerprint-ref:calendar-adoption-restore",
            {
                "backup_fingerprint_ref": request.backup.ciphertext_fingerprint_ref,
                "current_state_ref": current_state_ref,
                "idempotency_ref": idempotency_ref,
                "resulting_revision": resulting_revision,
            },
        )
        operation_ref = _hash_ref(
            "operation-ref:calendar-adoption-restore",
            {"payload_fingerprint_ref": payload_fingerprint_ref},
        )
        preview_ref = _hash_ref(
            "preview-ref:calendar-adoption-restore",
            {
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "calendar_count": len(bundle.calendars),
                "event_count": len(bundle.events),
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:calendar-adoption-restore", {"preview_ref": preview_ref}
        )
        return (
            CalendarAdoptionRestorePreview(
                expected_revision=expected_revision,
                resulting_revision=resulting_revision,
                backup_revision=request.backup.source_revision,
                calendar_count=len(bundle.calendars),
                event_count=len(bundle.events),
                current_state_ref=current_state_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                preview_ref=preview_ref,
                approval_ref=approval_ref,
                operation_ref=operation_ref,
                rollback_available=rollback_available,
                impact_status=(
                    "exact"
                    if current is not None
                    else (
                        "empty_target" if current_readable else "unknown_current_state"
                    )
                ),
            ),
            bundle,
        )

    def preview_restore(
        self,
        request: CalendarAdoptionPortableRestoreRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionRestorePreview:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            preview = self._restore_preview(request, idempotency_ref=idempotency_ref)[0]
            self._assert_idempotency_not_retired(
                self._read_receipt_checkpoints(),
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
            )
            return preview

    def capture_restore_approval(
        self,
        request: CalendarAdoptionRestoreApprovalCaptureRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionApprovalReceipt:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            checkpoints = self._read_receipt_checkpoints()
            checkpoint = self._checkpoint_for(checkpoints, idempotency_ref)
            if checkpoint is not None:
                self._assert_checkpoint_matches(
                    checkpoint,
                    action="restore_backup",
                    target_ref=CALENDAR_ADOPTION_SET_REF,
                    expected_revision=checkpoint.before_revision,
                    payload_fingerprint_ref=checkpoint.payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    operation_ref=checkpoint.operation_ref,
                    backup_fingerprint_ref=(request.backup.ciphertext_fingerprint_ref),
                )
                if not checkpoint.approval_pending:
                    return CalendarAdoptionApprovalReceipt(
                        approval_ref=checkpoint.approval_ref,
                        approval_validation_ref=checkpoint.approval_validation_ref,
                        preview_ref=checkpoint.preview_ref,
                        idempotency_ref=checkpoint.idempotency_ref,
                        expires_at=checkpoint.approval_expires_at,
                    )
            preview, _bundle = self._restore_preview(
                request, idempotency_ref=idempotency_ref
            )
            self._assert_idempotency_not_retired(
                checkpoints,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_RESTORE_APPROVAL_SCOPE_MISMATCH"
                )
            if checkpoint is None:
                checkpoint = _CalendarAdoptionReceiptCheckpoint(
                    action="restore_backup",
                    target_ref=CALENDAR_ADOPTION_SET_REF,
                    before_revision=preview.expected_revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=_PENDING_APPROVAL_VALIDATION_REF,
                    approval_expires_at=utc_now(),
                    authority_decision_ref=_PENDING_AUTHORITY_DECISION_REF,
                    authority_lease_ref=_PENDING_AUTHORITY_LEASE_REF,
                    operation_ref=preview.operation_ref,
                    backup_fingerprint_ref=(request.backup.ciphertext_fingerprint_ref),
                    approval_pending=True,
                )
                self._save_checkpoint(checkpoints, checkpoint)
            receipt = self._capture_approval(
                action=preview.action,
                expected_revision=preview.expected_revision,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
                restore=True,
            )
            captured = checkpoint.model_copy(
                update={
                    "approval_validation_ref": receipt.approval_validation_ref,
                    "approval_expires_at": receipt.expires_at,
                    "approval_pending": False,
                }
            )
            self._save_checkpoint(checkpoints, captured)
            return receipt

    def _commit_authorized_restore(
        self,
        *,
        request: CalendarAdoptionRestoreCommitRequest,
        preview: CalendarAdoptionRestorePreview,
        bundle: CalendarPortableBundle,
        idempotency_ref: str,
        checkpoints: list[_CalendarAdoptionCheckpointEntry],
        checkpoint: _CalendarAdoptionReceiptCheckpoint | None,
        repository: CalendarRepository | None,
        authority: LocalApprovalAuthority | None,
        lease: AuthorityLease,
        authority_decision_ref: str,
        approval_validation_ref: str,
        approval_expires_at: datetime,
    ) -> CalendarAdoptionMutationReceipt:
        if checkpoint is None:
            checkpoint = _CalendarAdoptionReceiptCheckpoint(
                action="restore_backup",
                target_ref=CALENDAR_ADOPTION_SET_REF,
                before_revision=preview.expected_revision,
                after_revision=preview.resulting_revision,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                approval_validation_ref=approval_validation_ref,
                approval_expires_at=approval_expires_at,
                authority_decision_ref=authority_decision_ref,
                authority_lease_ref=lease.lease_ref,
                operation_ref=preview.operation_ref,
                backup_fingerprint_ref=request.backup.ciphertext_fingerprint_ref,
            )
            self._save_checkpoint(checkpoints, checkpoint)
            checkpoints = [*checkpoints, checkpoint]
        elif checkpoint.approval_pending:
            checkpoint = checkpoint.model_copy(
                update={
                    "approval_validation_ref": approval_validation_ref,
                    "approval_expires_at": approval_expires_at,
                    "authority_decision_ref": authority_decision_ref,
                    "authority_lease_ref": lease.lease_ref,
                    "approval_pending": False,
                }
            )
            self._save_checkpoint(checkpoints, checkpoint)
        elif (
            checkpoint.authority_decision_ref == _PENDING_AUTHORITY_DECISION_REF
            and checkpoint.authority_lease_ref == _PENDING_AUTHORITY_LEASE_REF
        ):
            checkpoint = checkpoint.model_copy(
                update={
                    "approval_validation_ref": approval_validation_ref,
                    "approval_expires_at": approval_expires_at,
                    "authority_decision_ref": authority_decision_ref,
                    "authority_lease_ref": lease.lease_ref,
                }
            )
            self._save_checkpoint(checkpoints, checkpoint)
        elif any(
            [
                checkpoint.authority_decision_ref != authority_decision_ref,
                checkpoint.authority_lease_ref != lease.lease_ref,
                checkpoint.approval_validation_ref != approval_validation_ref,
                checkpoint.approval_expires_at != approval_expires_at,
            ]
        ):
            raise CalendarAdoptionError(
                "CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_AUTHORITY_MISMATCH"
            )
        if preview.impact_status == "unknown_current_state":
            unit = self._replace_unreadable_database(
                bundle=bundle,
                preview=preview,
                idempotency_ref=idempotency_ref,
                outer_approval_ref=preview.approval_ref,
                approval_expires_at=approval_expires_at,
            )
        else:
            if repository is None or authority is None:
                repository, _platform, authority = self._repository_for_commit()
            try:
                unit = self._apply_repository_restore(
                    repository=repository,
                    authority=authority,
                    bundle=bundle,
                    preview=preview,
                    idempotency_ref=idempotency_ref,
                    outer_approval_ref=preview.approval_ref,
                    approval_expires_at=approval_expires_at,
                )
            except (OSError, sqlite3.Error, EcosystemKeyUnavailable) as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                ) from exc
        self._secure_tree(self.state_dir)
        completed = self._complete_checkpoint(checkpoint, unit)
        self._save_checkpoint(checkpoints, completed)
        assert completed.receipt is not None
        return completed.receipt

    def _apply_repository_restore(
        self,
        *,
        repository: CalendarRepository,
        authority: LocalApprovalAuthority,
        bundle: CalendarPortableBundle,
        preview: CalendarAdoptionRestorePreview,
        idempotency_ref: str,
        outer_approval_ref: str,
        approval_expires_at: datetime,
    ) -> UnitOfWorkReceipt:
        if preview.expected_revision == 0:
            workspace_approval = self._repository_approval(
                authority,
                action="ecosystem.local_data.create_workspace",
                resource_refs=(
                    CALENDAR_ADOPTION_WORKSPACE_REF,
                    _DEFAULT_KEY_VERSION_REF,
                ),
                outer_approval_ref=preview.approval_ref,
                expires_at=approval_expires_at,
            )
            repository.platform.create_workspace(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                key_version_ref=_DEFAULT_KEY_VERSION_REF,
                approval=workspace_approval,
            )
            calendar_set = CalendarSet(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                name=bundle.name,
                calendars=bundle.calendars,
                events=bundle.events,
            )
            resources = repository.mutation_resource_refs(
                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                idempotency_ref=idempotency_ref,
                operation_ref=preview.operation_ref,
                record_ref=CALENDAR_ADOPTION_SET_REF,
            )
            approval = self._repository_approval(
                authority,
                action=ECO_CALENDAR_MUTATION_ACTION,
                resource_refs=resources,
                outer_approval_ref=preview.approval_ref,
                expires_at=approval_expires_at,
            )
            unit = repository.create_calendar_set(
                calendar_set=calendar_set,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
            )
            return unit
        resources = repository.mutation_resource_refs(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            idempotency_ref=idempotency_ref,
            operation_ref=preview.operation_ref,
            record_ref=CALENDAR_ADOPTION_SET_REF,
        )
        approval = self._repository_approval(
            authority,
            action=ECO_CALENDAR_MUTATION_ACTION,
            resource_refs=resources,
            outer_approval_ref=outer_approval_ref,
            expires_at=approval_expires_at,
        )
        return repository.restore_bundle(
            workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
            calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
            bundle=bundle,
            expected_version=preview.expected_revision,
            operation_ref=preview.operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def _replace_unreadable_database(
        self,
        *,
        bundle: CalendarPortableBundle,
        preview: CalendarAdoptionRestorePreview,
        idempotency_ref: str,
        outer_approval_ref: str,
        approval_expires_at: datetime,
    ) -> UnitOfWorkReceipt:
        """Build a complete replacement before atomically publishing it."""

        if self._database_cluster_state_ref() != preview.current_state_ref:
            raise CalendarAdoptionConflict("CALENDAR_ADOPTION_CURRENT_STATE_CHANGED")
        with tempfile.TemporaryDirectory(
            dir=self.state_dir,
            prefix=_CALENDAR_ADOPTION_RESTORE_STAGE_PREFIX,
        ) as directory:
            stage_dir = Path(directory)
            self._set_private_permissions(stage_dir, directory=True)
            stage_database = stage_dir / CALENDAR_ADOPTION_DATABASE_FILE
            try:
                repository, _platform, authority = self._repository(
                    database_path=stage_database
                )
                unit = self._apply_repository_restore(
                    repository=repository,
                    authority=authority,
                    bundle=bundle,
                    preview=preview,
                    idempotency_ref=idempotency_ref,
                    outer_approval_ref=outer_approval_ref,
                    approval_expires_at=approval_expires_at,
                )
                connection = sqlite3.connect(stage_database)
                try:
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    journal_mode = connection.execute(
                        "PRAGMA journal_mode = DELETE"
                    ).fetchone()[0]
                    integrity = connection.execute("PRAGMA integrity_check").fetchone()[
                        0
                    ]
                    if str(journal_mode).lower() != "delete" or integrity != "ok":
                        raise CalendarAdoptionError(
                            "CALENDAR_ADOPTION_REPLACEMENT_DATABASE_INVALID"
                        )
                finally:
                    connection.close()
            except EcosystemKeyUnavailable as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_KEY_RECOVERY_UNAVAILABLE"
                ) from exc
            except (
                OSError,
                ValueError,
                sqlite3.Error,
                CalendarError,
                EcosystemLocalDataError,
            ) as exc:
                raise CalendarAdoptionError(
                    "CALENDAR_ADOPTION_REPLACEMENT_DATABASE_FAILED"
                ) from exc
            if self._database_cluster_state_ref() != preview.current_state_ref:
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_CURRENT_STATE_CHANGED"
                )
            moved_sidecars: list[tuple[Path, Path]] = []
            published = False
            try:
                for name in _CALENDAR_ADOPTION_DATABASE_CLUSTER_NAMES[1:]:
                    source = self.state_dir / name
                    if not os.path.lexists(source):
                        continue
                    retained = stage_dir / f"replaced-{name}"
                    os.replace(source, retained)
                    moved_sidecars.append((source, retained))
                os.replace(stage_database, self.database_path)
                published = True
                self._set_private_permissions(self.database_path, directory=False)
                _fsync_directory(self.state_dir)
            except OSError as exc:
                if not published:
                    for source, retained in reversed(moved_sidecars):
                        try:
                            if not os.path.lexists(source):
                                os.replace(retained, source)
                        except OSError:
                            pass
                    try:
                        _fsync_directory(self.state_dir)
                    except OSError:
                        pass
                code = (
                    "CALENDAR_ADOPTION_RESTORE_PUBLICATION_UNCERTAIN"
                    if published
                    else "CALENDAR_ADOPTION_REPLACEMENT_DATABASE_FAILED"
                )
                raise CalendarAdoptionError(code) from exc
            return unit

    def commit_restore(
        self,
        request: CalendarAdoptionRestoreCommitRequest,
        *,
        idempotency_ref: str,
    ) -> CalendarAdoptionMutationReceipt:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            _validate_ref(idempotency_ref, "idempotency_ref")
            checkpoints = self._read_receipt_checkpoints()
            checkpoint = self._checkpoint_for(checkpoints, idempotency_ref)
            repository: CalendarRepository | None = None
            authority: LocalApprovalAuthority | None = None
            if self._database_present():
                try:
                    repository, _platform, authority = self._repository()
                except (OSError, sqlite3.Error, CalendarError, EcosystemLocalDataError):
                    repository = None
                    authority = None
            if checkpoint is not None:
                self._assert_checkpoint_matches(
                    checkpoint,
                    action="restore_backup",
                    target_ref=CALENDAR_ADOPTION_SET_REF,
                    expected_revision=checkpoint.before_revision,
                    payload_fingerprint_ref=checkpoint.payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    operation_ref=checkpoint.operation_ref,
                    backup_fingerprint_ref=(request.backup.ciphertext_fingerprint_ref),
                )
                bundle = self._open_backup(request)
                replay: UnitOfWorkReceipt | None = None
                if repository is not None:
                    try:
                        if checkpoint.before_revision == 0:
                            calendar_set = CalendarSet(
                                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                                name=bundle.name,
                                calendars=bundle.calendars,
                                events=bundle.events,
                            )
                            replay = repository.recover_create_receipt(
                                calendar_set=calendar_set,
                                operation_ref=checkpoint.operation_ref,
                                idempotency_ref=idempotency_ref,
                            )
                        else:
                            replay = repository.recover_mutation_receipt(
                                workspace_ref=CALENDAR_ADOPTION_WORKSPACE_REF,
                                calendar_set_ref=CALENDAR_ADOPTION_SET_REF,
                                expected_version=checkpoint.before_revision,
                                operation_ref=checkpoint.operation_ref,
                                idempotency_ref=idempotency_ref,
                                mutation_kind="restore_bundle",
                                mutation_material={
                                    "bundle": bundle.model_dump(mode="json")
                                },
                            )
                    except EcosystemLocalDataError as exc:
                        if str(exc) not in {
                            "ECO_WORKSPACE_NOT_FOUND",
                            "ECO_RECORD_NOT_FOUND",
                        }:
                            raise CalendarAdoptionError(
                                "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
                            ) from exc
                        replay = None
                if replay is not None:
                    if checkpoint.receipt is not None:
                        self._assert_checkpoint_receipt_matches_unit(
                            checkpoint,
                            replay,
                        )
                        return checkpoint.receipt.model_copy(update={"replayed": True})
                    completed = self._complete_checkpoint(checkpoint, replay)
                    self._save_checkpoint(checkpoints, completed)
                    assert completed.receipt is not None
                    return completed.receipt.model_copy(update={"replayed": True})
                if checkpoint.receipt is not None:
                    raise CalendarAdoptionError(
                        "CALENDAR_ADOPTION_DURABLE_RECEIPT_MISSING"
                    )
            preview, bundle = self._restore_preview(
                request, idempotency_ref=idempotency_ref
            )
            self._assert_idempotency_not_retired(
                checkpoints,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise CalendarAdoptionConflict(
                    "CALENDAR_ADOPTION_RESTORE_COMMIT_SCOPE_MISMATCH"
                )
            if checkpoint is not None:
                self._assert_checkpoint_matches(
                    checkpoint,
                    action="restore_backup",
                    target_ref=CALENDAR_ADOPTION_SET_REF,
                    expected_revision=preview.expected_revision,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    operation_ref=preview.operation_ref,
                    backup_fingerprint_ref=(request.backup.ciphertext_fingerprint_ref),
                )
            (
                lease_store,
                lease,
                authority_decision_ref,
                approval_validation_ref,
                approval_expires_at,
            ) = self._authorize(
                action=preview.action,
                expected_revision=preview.expected_revision,
                payload_fingerprint_ref=preview.payload_fingerprint_ref,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
                operation_ref=preview.operation_ref,
                idempotency_ref=idempotency_ref,
                restore=True,
            )
            try:
                return self._commit_authorized_restore(
                    request=request,
                    preview=preview,
                    bundle=bundle,
                    idempotency_ref=idempotency_ref,
                    checkpoints=checkpoints,
                    checkpoint=checkpoint,
                    repository=repository,
                    authority=authority,
                    lease=lease,
                    authority_decision_ref=authority_decision_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                )
            except Exception:
                self._revoke_lease(lease_store, lease)
                raise


__all__ = [
    "CALENDAR_ADOPTION_CONTRACT_REF",
    "CalendarAdoptionApprovalCaptureRequest",
    "CalendarAdoptionApprovalReceipt",
    "CalendarAdoptionCalendarDraft",
    "CalendarAdoptionCommitRequest",
    "CalendarAdoptionConflict",
    "CalendarAdoptionError",
    "CalendarAdoptionEventDraft",
    "CalendarAdoptionMutationPreview",
    "CalendarAdoptionMutationReceipt",
    "CalendarAdoptionMutationRequest",
    "CalendarAdoptionPortableBackup",
    "CalendarAdoptionPortableBackupRequest",
    "CalendarAdoptionPortableRestoreRequest",
    "CalendarAdoptionReadModel",
    "CalendarAdoptionRestoreApprovalCaptureRequest",
    "CalendarAdoptionRestoreCommitRequest",
    "CalendarAdoptionRestorePreview",
    "CalendarAdoptionStore",
]
