"""Founder-private Work Board lifecycle for Queue V2 Q33.

This module turns the existing Work Board shell into a usable local planning
surface without granting task execution or external authority.  It persists
only the operator's local board items, requires one exact short-lived approval
for every change, and keeps a bounded undo history and content-free receipts.
"""

from __future__ import annotations

import hashlib
import json
import os
import base64
import binascii
import secrets
import stat
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
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
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager


WORK_BOARD_ADOPTION_CONTRACT_REF = "contract-ref:queue-v2-q33-work-board-adoption:v1"
WORK_BOARD_ADOPTION_BOARD_REF = "work-board-ref:founder-private"
WORK_BOARD_ADOPTION_ROUTE_REF = "POST /control-center/work-board/adoption/commit"
WORK_BOARD_ADOPTION_RESTORE_ROUTE_REF = (
    "POST /control-center/work-board/adoption/restore-commit"
)
WORK_BOARD_ADOPTION_AUTHORITY_LANE_REF = (
    "authority-lane-ref:work-board-adoption-local-write"
)
WORK_BOARD_ADOPTION_SAFE_DISABLE_REF = (
    "safe-disable-ref:work-board-adoption-local-write:deny"
)
WORK_BOARD_ADOPTION_STATE_DIR_ENV = "UAA_WORK_BOARD_STATE_DIR"
WORK_BOARD_ADOPTION_STATE_FILE = "work_board_adoption_state.json"
WORK_BOARD_ADOPTION_MAX_CARDS = 1_000
WORK_BOARD_ADOPTION_MAX_UNDO = 20
WORK_BOARD_ADOPTION_MAX_RECEIPTS = 2_000
WORK_BOARD_ADOPTION_MAX_STATE_BYTES = 16 * 1024 * 1024
WORK_BOARD_ADOPTION_MAX_BACKUP_BYTES = WORK_BOARD_ADOPTION_MAX_STATE_BYTES + 16
WORK_BOARD_ADOPTION_MAX_BACKUP_B64_CHARS = (
    (WORK_BOARD_ADOPTION_MAX_BACKUP_BYTES + 2) // 3
) * 4
WORK_BOARD_ADOPTION_APPROVAL_TTL_MINUTES = 5
WORK_BOARD_ADOPTION_MAX_REVISION = 9_007_199_254_740_991
WORK_BOARD_ADOPTION_LANES = (
    "work-board-lane:inbox",
    "work-board-lane:planned",
    "work-board-lane:doing",
    "work-board-lane:done",
)
_LOCK_KEY = "work-board-adoption-state"
_BACKUP_AAD = b"uaa:work-board-adoption:portable-backup:v1"
_SAFE_REF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
)


class WorkBoardAdoptionError(RuntimeError):
    """Safe-code-only Work Board adoption failure."""


class WorkBoardAdoptionConflict(WorkBoardAdoptionError):
    """A stale revision, replay mismatch, or lifecycle conflict."""


class _WorkBoardAdoptionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_JSON_INVALID") from exc


def _hash_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _validate_ref(value: str, field_name: str) -> str:
    if (
        not 3 <= len(value) <= 191
        or not value[0].isalpha()
        or any(character not in _SAFE_REF_CHARS for character in value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"WORK_BOARD_ADOPTION_{field_name.upper()}_INVALID")
    validate_task_ref(value, f"work_board_adoption_{field_name}")
    return value


def _private_text(value: str, *, maximum: int, code: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        raise ValueError(code)
    return normalized


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode_b64(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_BACKUP_INVALID") from exc


def _fsync_directory(path: Path) -> None:
    """Persist a published rename where directory descriptors are supported."""

    if os.name == "nt":
        return
    directory_fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class WorkBoardAdoptionCard(_WorkBoardAdoptionModel):
    card_ref: str
    title: str = Field(..., repr=False)
    description: str | None = Field(default=None, repr=False)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    lane_ref: Literal[
        "work-board-lane:inbox",
        "work-board-lane:planned",
        "work-board-lane:doing",
        "work-board-lane:done",
    ] = "work-board-lane:inbox"
    tag_refs: tuple[str, ...] = Field(default=(), max_length=16)
    archived: bool = False

    @model_validator(mode="after")
    def validate_card(self) -> "WorkBoardAdoptionCard":
        _validate_ref(self.card_ref, "card_ref")
        _private_text(
            self.title,
            maximum=160,
            code="WORK_BOARD_ADOPTION_TITLE_INVALID",
        )
        if self.description is not None:
            _private_text(
                self.description,
                maximum=4_000,
                code="WORK_BOARD_ADOPTION_DESCRIPTION_INVALID",
            )
        if len(self.tag_refs) != len(set(self.tag_refs)):
            raise ValueError("WORK_BOARD_ADOPTION_DUPLICATE_TAG_REF")
        for ref in self.tag_refs:
            _validate_ref(ref, "tag_ref")
        return self


class WorkBoardAdoptionCardDraft(_WorkBoardAdoptionModel):
    title: str = Field(..., min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4_000)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    lane_ref: Literal[
        "work-board-lane:inbox",
        "work-board-lane:planned",
        "work-board-lane:doing",
        "work-board-lane:done",
    ] = "work-board-lane:inbox"
    tag_refs: tuple[str, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def validate_draft(self) -> "WorkBoardAdoptionCardDraft":
        _private_text(
            self.title,
            maximum=160,
            code="WORK_BOARD_ADOPTION_TITLE_INVALID",
        )
        if self.description is not None:
            _private_text(
                self.description,
                maximum=4_000,
                code="WORK_BOARD_ADOPTION_DESCRIPTION_INVALID",
            )
        if len(self.tag_refs) != len(set(self.tag_refs)):
            raise ValueError("WORK_BOARD_ADOPTION_DUPLICATE_TAG_REF")
        for ref in self.tag_refs:
            _validate_ref(ref, "tag_ref")
        return self


class WorkBoardAdoptionSnapshot(_WorkBoardAdoptionModel):
    cards: tuple[WorkBoardAdoptionCard, ...] = Field(
        default=(), max_length=WORK_BOARD_ADOPTION_MAX_CARDS
    )


class WorkBoardAdoptionMutationRequest(_WorkBoardAdoptionModel):
    action: Literal["create", "update", "move", "archive", "recover", "undo"]
    expected_revision: int = Field(
        ..., ge=0, le=WORK_BOARD_ADOPTION_MAX_REVISION
    )
    target_ref: str | None = None
    draft: WorkBoardAdoptionCardDraft | None = None
    lane_ref: Literal[
        "work-board-lane:inbox",
        "work-board-lane:planned",
        "work-board-lane:doing",
        "work-board-lane:done",
    ] | None = None

    @model_validator(mode="after")
    def validate_action(self) -> "WorkBoardAdoptionMutationRequest":
        if self.target_ref is not None:
            _validate_ref(self.target_ref, "target_ref")
        if self.action == "create":
            if self.draft is None or self.target_ref is not None or self.lane_ref is not None:
                raise ValueError("WORK_BOARD_ADOPTION_CREATE_SCOPE_INVALID")
        elif self.action == "update":
            if self.target_ref is None or self.draft is None or self.lane_ref is not None:
                raise ValueError("WORK_BOARD_ADOPTION_UPDATE_SCOPE_INVALID")
        elif self.action == "move":
            if self.target_ref is None or self.lane_ref is None or self.draft is not None:
                raise ValueError("WORK_BOARD_ADOPTION_MOVE_SCOPE_INVALID")
        elif self.action in {"archive", "recover"}:
            if self.target_ref is None or self.draft is not None or self.lane_ref is not None:
                raise ValueError("WORK_BOARD_ADOPTION_LIFECYCLE_SCOPE_INVALID")
        elif any(value is not None for value in (self.target_ref, self.draft, self.lane_ref)):
            raise ValueError("WORK_BOARD_ADOPTION_UNDO_SCOPE_INVALID")
        return self


class WorkBoardAdoptionMutationPreview(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-mutation-preview.v1"] = (
        "uaa-work-board-adoption-mutation-preview.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    action: str
    expected_revision: int
    resulting_revision: int
    target_ref: str | None
    card_ref: str | None
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    safe_summary: str
    mutation_performed: Literal[False] = False
    external_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_preview(self) -> "WorkBoardAdoptionMutationPreview":
        for ref in [
            self.contract_ref,
            self.payload_fingerprint_ref,
            self.preview_ref,
            self.approval_ref,
            *([self.target_ref] if self.target_ref else []),
            *([self.card_ref] if self.card_ref else []),
        ]:
            _validate_ref(ref, "preview_ref")
        return self


class WorkBoardAdoptionApprovalCaptureRequest(_WorkBoardAdoptionModel):
    mutation: WorkBoardAdoptionMutationRequest
    preview_ref: str
    approval_ref: str

    @model_validator(mode="after")
    def validate_capture(self) -> "WorkBoardAdoptionApprovalCaptureRequest":
        _validate_ref(self.preview_ref, "preview_ref")
        _validate_ref(self.approval_ref, "approval_ref")
        return self


class WorkBoardAdoptionApprovalReceipt(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-approval-receipt.v1"] = (
        "uaa-work-board-adoption-approval-receipt.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    approval_ref: str
    approval_validation_ref: str
    preview_ref: str
    idempotency_ref: str
    expires_at: datetime
    backend_owned: Literal[True] = True
    mutation_performed: Literal[False] = False


class WorkBoardAdoptionCommitRequest(_WorkBoardAdoptionModel):
    mutation: WorkBoardAdoptionMutationRequest
    preview_ref: str
    approval_ref: str

    @model_validator(mode="after")
    def validate_commit(self) -> "WorkBoardAdoptionCommitRequest":
        _validate_ref(self.preview_ref, "preview_ref")
        _validate_ref(self.approval_ref, "approval_ref")
        return self


class WorkBoardAdoptionMutationReceipt(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-mutation-receipt.v1"] = (
        "uaa-work-board-adoption-mutation-receipt.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    action: Literal[
        "create",
        "update",
        "move",
        "archive",
        "recover",
        "undo",
        "restore_backup",
    ]
    target_ref: str | None
    card_ref: str | None
    before_revision: int
    after_revision: int
    idempotency_ref: str
    payload_fingerprint_ref: str
    backup_fingerprint_ref: str | None = None
    backup_revision: int | None = Field(
        default=None,
        ge=0,
        le=WORK_BOARD_ADOPTION_MAX_REVISION,
    )
    preview_ref: str
    approval_ref: str
    approval_validation_ref: str
    approval_expires_at: datetime
    authority_decision_ref: str
    authority_lease_ref: str
    receipt_ref: str
    state_ref: str
    rollback_ref: str
    safe_disable_ref: Literal[WORK_BOARD_ADOPTION_SAFE_DISABLE_REF] = (
        WORK_BOARD_ADOPTION_SAFE_DISABLE_REF
    )
    safe_summary: str
    replayed: bool = False
    task_execution_performed: Literal[False] = False
    connector_write_performed: Literal[False] = False
    provider_model_call_performed: Literal[False] = False
    shell_subprocess_execution_performed: Literal[False] = False
    browser_automation_performed: Literal[False] = False
    background_autonomy_performed: Literal[False] = False
    production_authority_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "WorkBoardAdoptionMutationReceipt":
        required_refs = [
            self.contract_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.preview_ref,
            self.approval_ref,
            self.authority_decision_ref,
            self.authority_lease_ref,
            self.receipt_ref,
            self.state_ref,
            self.rollback_ref,
            self.safe_disable_ref,
        ]
        for ref in [
            *required_refs,
            *([self.target_ref] if self.target_ref else []),
            *([self.card_ref] if self.card_ref else []),
            *([self.backup_fingerprint_ref] if self.backup_fingerprint_ref else []),
        ]:
            _validate_ref(ref, "receipt_ref")
        if (
            not self.approval_validation_ref.startswith("appr_dec_")
            or len(self.approval_validation_ref) != 21
            or any(
                character not in "0123456789abcdef"
                for character in self.approval_validation_ref[9:]
            )
        ):
            raise ValueError("WORK_BOARD_ADOPTION_APPROVAL_VALIDATION_REF_INVALID")
        if (
            self.approval_expires_at.tzinfo is None
            or self.approval_expires_at.utcoffset() is None
        ):
            raise ValueError("WORK_BOARD_ADOPTION_TIMESTAMP_TIMEZONE_REQUIRED")
        if self.action == "restore_backup":
            revision_valid = (
                self.backup_revision is not None
                and self.after_revision
                == max(self.before_revision, self.backup_revision) + 1
            )
        else:
            revision_valid = (
                self.backup_revision is None
                and self.after_revision == self.before_revision + 1
            )
        if not revision_valid:
            raise ValueError("WORK_BOARD_ADOPTION_RECEIPT_REVISION_INVALID")
        if self.action == "create":
            valid_identity = self.target_ref is None and self.card_ref is not None
        elif self.action in {"update", "move", "archive", "recover"}:
            valid_identity = (
                self.target_ref is not None and self.target_ref == self.card_ref
            )
        else:
            valid_identity = self.target_ref is None and self.card_ref is None
        if not valid_identity:
            raise ValueError("WORK_BOARD_ADOPTION_RECEIPT_IDENTITY_INVALID")
        if (self.action == "restore_backup") != (self.backup_fingerprint_ref is not None):
            raise ValueError("WORK_BOARD_ADOPTION_RECEIPT_BACKUP_BINDING_INVALID")
        return self


class WorkBoardAdoptionPortableBackupRequest(_WorkBoardAdoptionModel):
    passphrase: str = Field(..., min_length=12, max_length=1_024, repr=False)

    @field_validator("passphrase", mode="before")
    @classmethod
    def validate_passphrase_utf8(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    "WORK_BOARD_ADOPTION_PASSPHRASE_UTF8_REQUIRED"
                ) from exc
        return value


class WorkBoardAdoptionPortableBackup(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-portable-backup.v1"] = (
        "uaa-work-board-adoption-portable-backup.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    salt: str = Field(..., min_length=24, max_length=24)
    nonce: str = Field(..., min_length=16, max_length=16)
    ciphertext: str = Field(
        ...,
        min_length=24,
        max_length=WORK_BOARD_ADOPTION_MAX_BACKUP_B64_CHARS,
        repr=False,
    )
    ciphertext_fingerprint_ref: str
    created_at: datetime
    private_values_encrypted: Literal[True] = True
    key_material_included: Literal[False] = False
    raw_paths_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_backup(self) -> "WorkBoardAdoptionPortableBackup":
        _validate_ref(self.ciphertext_fingerprint_ref, "backup_fingerprint_ref")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("WORK_BOARD_ADOPTION_TIMESTAMP_TIMEZONE_REQUIRED")
        return self


class WorkBoardAdoptionPortableRestoreRequest(WorkBoardAdoptionPortableBackupRequest):
    backup: WorkBoardAdoptionPortableBackup


class WorkBoardAdoptionPortableRestorePreview(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-restore-preview.v1"] = (
        "uaa-work-board-adoption-restore-preview.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    action: Literal["restore_backup"] = "restore_backup"
    expected_revision: int = Field(..., ge=0, le=WORK_BOARD_ADOPTION_MAX_REVISION)
    resulting_revision: int = Field(..., ge=1, le=WORK_BOARD_ADOPTION_MAX_REVISION)
    current_state_ref: str
    backup_revision: int = Field(..., ge=0, le=WORK_BOARD_ADOPTION_MAX_REVISION)
    card_count: int = Field(..., ge=0, le=WORK_BOARD_ADOPTION_MAX_CARDS)
    rollback_available: bool
    impact_status: Literal["exact", "unknown_current_state"]
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    safe_summary: str = "Restore one encrypted local Work Board backup."
    private_values_included: Literal[False] = False
    restore_performed: Literal[False] = False


class WorkBoardAdoptionRestoreApprovalCaptureRequest(
    WorkBoardAdoptionPortableRestoreRequest
):
    preview_ref: str
    approval_ref: str


class WorkBoardAdoptionRestoreCommitRequest(WorkBoardAdoptionPortableRestoreRequest):
    preview_ref: str
    approval_ref: str


class WorkBoardAdoptionState(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-state.v1"] = (
        "uaa-work-board-adoption-state.v1"
    )
    board_ref: Literal[WORK_BOARD_ADOPTION_BOARD_REF] = WORK_BOARD_ADOPTION_BOARD_REF
    revision: int = Field(default=0, ge=0, le=WORK_BOARD_ADOPTION_MAX_REVISION)
    cards: tuple[WorkBoardAdoptionCard, ...] = Field(
        default=(), max_length=WORK_BOARD_ADOPTION_MAX_CARDS
    )
    undo_stack: tuple[WorkBoardAdoptionSnapshot, ...] = Field(
        default=(), max_length=WORK_BOARD_ADOPTION_MAX_UNDO, repr=False
    )
    receipts: tuple[WorkBoardAdoptionMutationReceipt, ...] = Field(
        default=(), max_length=WORK_BOARD_ADOPTION_MAX_RECEIPTS, repr=False
    )

    @model_validator(mode="after")
    def validate_state(self) -> "WorkBoardAdoptionState":
        refs = [card.card_ref for card in self.cards]
        if len(refs) != len(set(refs)):
            raise ValueError("WORK_BOARD_ADOPTION_DUPLICATE_CARD_REF")
        idempotency_refs = [receipt.idempotency_ref for receipt in self.receipts]
        if len(idempotency_refs) != len(set(idempotency_refs)):
            raise ValueError("WORK_BOARD_ADOPTION_DUPLICATE_RECEIPT")
        return self


class WorkBoardAdoptionReadModel(_WorkBoardAdoptionModel):
    schema_version: Literal["uaa-work-board-adoption-read-model.v1"] = (
        "uaa-work-board-adoption-read-model.v1"
    )
    contract_ref: Literal[WORK_BOARD_ADOPTION_CONTRACT_REF] = (
        WORK_BOARD_ADOPTION_CONTRACT_REF
    )
    board_ref: Literal[WORK_BOARD_ADOPTION_BOARD_REF] = WORK_BOARD_ADOPTION_BOARD_REF
    status: Literal["ready", "recovery_required"]
    revision: int
    current_state_ref: str
    active_cards: tuple[WorkBoardAdoptionCard, ...]
    archived_cards: tuple[WorkBoardAdoptionCard, ...]
    lane_refs: tuple[str, ...] = WORK_BOARD_ADOPTION_LANES
    can_undo: bool
    latest_receipt_ref: str | None
    next_safe_action: str
    backend_owned: Literal[True] = True
    local_only: Literal[True] = True
    exact_approval_required: Literal[True] = True
    backup_restore_available: Literal[True] = True
    task_execution_enabled: Literal[False] = False
    connector_write_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    shell_subprocess_execution_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    background_autonomy_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False


class WorkBoardAdoptionStore:
    """Exact-approved durable lifecycle for founder-owned local board cards."""

    def __init__(self, state_dir: Path | None = None) -> None:
        selected = state_dir or Path(
            os.environ.get(WORK_BOARD_ADOPTION_STATE_DIR_ENV, ".uaa/work_board")
        ).expanduser()
        self.state_dir = selected.resolve()
        self.state_path = self.state_dir / WORK_BOARD_ADOPTION_STATE_FILE
        self.lock_manager = FileSingleWriterLockManager(self.state_dir / ".locks")

    @classmethod
    def from_env(cls) -> "WorkBoardAdoptionStore":
        return cls()

    def read_view(self) -> WorkBoardAdoptionReadModel:
        try:
            os.lstat(self.state_path)
        except FileNotFoundError:
            return self._read_model(WorkBoardAdoptionState())
        except OSError:
            return self._recovery_read_model()
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            try:
                state = self._read_state()
            except (OSError, ValueError, WorkBoardAdoptionError):
                return self._recovery_read_model()
            return self._read_model(state)

    def _ensure_private_state_directory(self) -> None:
        try:
            self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            metadata = os.lstat(self.state_dir)
            if not stat.S_ISDIR(metadata.st_mode):
                raise OSError("unsafe Work Board state directory")
            os.chmod(self.state_dir, 0o700)
        except OSError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_STATE_DIRECTORY_UNSAFE"
            ) from exc

    def _read_model(
        self,
        state: WorkBoardAdoptionState,
    ) -> WorkBoardAdoptionReadModel:
        active = tuple(card for card in state.cards if not card.archived)
        archived = tuple(card for card in state.cards if card.archived)
        return WorkBoardAdoptionReadModel(
            status="ready",
            revision=state.revision,
            current_state_ref=self._state_ref(state),
            active_cards=active,
            archived_cards=archived,
            can_undo=bool(state.undo_stack),
            latest_receipt_ref=(
                state.receipts[-1].receipt_ref if state.receipts else None
            ),
            next_safe_action=(
                "Create a private board item, or select one to edit, move, archive, "
                "or recover after exact confirmation."
                if active or archived
                else "Create the first private Work Board item."
            ),
        )

    @staticmethod
    def _recovery_read_model() -> WorkBoardAdoptionReadModel:
        return WorkBoardAdoptionReadModel(
            status="recovery_required",
            revision=0,
            current_state_ref=_hash_ref(
                "state-ref:work-board-adoption", {"status": "unreadable"}
            ),
            active_cards=(),
            archived_cards=(),
            can_undo=False,
            latest_receipt_ref=None,
            next_safe_action=(
                "Restore a verified local Work Board backup or inspect the "
                "private state directory before making another change."
            ),
        )

    def preview_mutation(
        self,
        request: WorkBoardAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionMutationPreview:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state()
            return self._preview(state, request, idempotency_ref=idempotency_ref)

    def capture_approval(
        self,
        request: WorkBoardAdoptionApprovalCaptureRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionApprovalReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state()
            payload_fingerprint_ref = self._payload_fingerprint(
                request.mutation,
                idempotency_ref=idempotency_ref,
            )
            prior = next(
                (
                    receipt
                    for receipt in state.receipts
                    if receipt.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if prior is not None:
                return self._replay_captured_approval(
                    prior,
                    action=request.mutation.action,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    idempotency_ref=idempotency_ref,
                )
            preview = self._preview(
                state,
                request.mutation,
                idempotency_ref=idempotency_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_APPROVAL_SCOPE_MISMATCH"
                )
            return self._capture_preview_approval(
                preview,
                idempotency_ref=idempotency_ref,
            )

    def commit_mutation(
        self,
        request: WorkBoardAdoptionCommitRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionMutationReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state()
            payload_fingerprint_ref = self._payload_fingerprint(
                request.mutation,
                idempotency_ref=idempotency_ref,
            )
            replay = next(
                (
                    receipt
                    for receipt in state.receipts
                    if receipt.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if replay is not None:
                if replay.payload_fingerprint_ref != payload_fingerprint_ref:
                    raise WorkBoardAdoptionConflict(
                        "WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT"
                    )
                return replay.model_copy(update={"replayed": True})
            preview = self._preview(
                state,
                request.mutation,
                idempotency_ref=idempotency_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_COMMIT_SCOPE_MISMATCH"
                )
            (
                lease_store,
                lease,
                authority_decision_ref,
                approval_validation_ref,
                approval_expires_at,
            ) = self._authorize(preview, idempotency_ref=idempotency_ref)
            try:
                updated_cards, updated_undo = self._apply_mutation(
                    state,
                    request.mutation,
                    preview=preview,
                )
                receipt_ref = _hash_ref(
                    "receipt-ref:work-board-adoption",
                    {
                        "approval_ref": preview.approval_ref,
                        "payload_fingerprint_ref": preview.payload_fingerprint_ref,
                        "after_revision": preview.resulting_revision,
                    },
                )
                provisional = WorkBoardAdoptionMutationReceipt(
                    action=request.mutation.action,
                    target_ref=request.mutation.target_ref,
                    card_ref=preview.card_ref,
                    before_revision=state.revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                    authority_decision_ref=authority_decision_ref,
                    authority_lease_ref=lease.lease_ref,
                    receipt_ref=receipt_ref,
                    state_ref="state-ref:work-board-adoption:sha256:pending",
                    rollback_ref=_hash_ref(
                        "rollback-ref:work-board-adoption",
                        {"receipt_ref": receipt_ref, "action": "undo"},
                    ),
                    safe_summary=(
                        "One exact confirmed local Work Board change was persisted."
                    ),
                )
                next_receipts = tuple(
                    [*state.receipts[-(WORK_BOARD_ADOPTION_MAX_RECEIPTS - 1) :], provisional]
                )
                next_state = WorkBoardAdoptionState(
                    revision=preview.resulting_revision,
                    cards=updated_cards,
                    undo_stack=updated_undo,
                    receipts=next_receipts,
                )
                state_ref = self._state_ref(next_state)
                receipt = provisional.model_copy(update={"state_ref": state_ref})
                next_state = next_state.model_copy(
                    update={
                        "receipts": tuple([*next_receipts[:-1], receipt]),
                    }
                )
                self._write_state(next_state)
                return receipt
            except Exception:
                self._revoke_lease(lease_store, lease)
                raise

    def create_portable_backup(
        self,
        request: WorkBoardAdoptionPortableBackupRequest,
    ) -> WorkBoardAdoptionPortableBackup:
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            if not self.state_path.exists():
                raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_BACKUP_EMPTY")
            state = self._read_state()
            plaintext = _canonical_json(state.model_dump(mode="json"))
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)
            ciphertext = AESGCM(self._derive_backup_key(request.passphrase, salt)).encrypt(
                nonce,
                plaintext,
                _BACKUP_AAD,
            )
            if len(ciphertext) > WORK_BOARD_ADOPTION_MAX_BACKUP_BYTES:
                raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_BACKUP_SIZE_LIMIT")
            return WorkBoardAdoptionPortableBackup(
                salt=_b64(salt),
                nonce=_b64(nonce),
                ciphertext=_b64(ciphertext),
                ciphertext_fingerprint_ref=(
                    "ciphertext-fingerprint-ref:sha256:"
                    f"{hashlib.sha256(ciphertext).hexdigest()}"
                ),
                created_at=_utc_now(),
            )

    def preview_restore(
        self,
        request: WorkBoardAdoptionPortableRestoreRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionPortableRestorePreview:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            return self._preview_restore(request, idempotency_ref=idempotency_ref)

    def capture_restore_approval(
        self,
        request: WorkBoardAdoptionRestoreApprovalCaptureRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionApprovalReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            current, current_readable = self._read_current_for_restore()
            restored = self._open_portable_backup(request)
            prior = next(
                (
                    receipt
                    for receipt in current.receipts
                    if receipt.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if prior is not None:
                return self._replay_captured_approval(
                    prior,
                    action="restore_backup",
                    payload_fingerprint_ref=prior.payload_fingerprint_ref,
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    idempotency_ref=idempotency_ref,
                    backup_fingerprint_ref=(
                        request.backup.ciphertext_fingerprint_ref
                    ),
                )
            preview = self._build_restore_preview(
                request,
                restored=restored,
                current=current,
                current_readable=current_readable,
                idempotency_ref=idempotency_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_RESTORE_APPROVAL_SCOPE_MISMATCH"
                )
            return self._capture_preview_approval(
                preview,
                idempotency_ref=idempotency_ref,
            )

    def commit_restore(
        self,
        request: WorkBoardAdoptionRestoreCommitRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionMutationReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        self._ensure_private_state_directory()
        with self.lock_manager.acquire(_LOCK_KEY):
            current, current_readable = self._read_current_for_restore()
            restored = self._open_portable_backup(request)
            replay = next(
                (
                    receipt
                    for receipt in current.receipts
                    if receipt.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if replay is not None:
                if (
                    replay.action != "restore_backup"
                    or replay.backup_fingerprint_ref
                    != request.backup.ciphertext_fingerprint_ref
                    or replay.preview_ref != request.preview_ref
                    or replay.approval_ref != request.approval_ref
                ):
                    raise WorkBoardAdoptionConflict(
                        "WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT"
                    )
                return replay.model_copy(update={"replayed": True})
            preview = self._build_restore_preview(
                request,
                restored=restored,
                current=current,
                current_readable=current_readable,
                idempotency_ref=idempotency_ref,
            )
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_RESTORE_COMMIT_SCOPE_MISMATCH"
                )
            if any(
                receipt.idempotency_ref == idempotency_ref
                for receipt in restored.receipts
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT"
                )
            (
                lease_store,
                lease,
                authority_decision_ref,
                approval_validation_ref,
                approval_expires_at,
            ) = self._authorize(preview, idempotency_ref=idempotency_ref)
            try:
                receipt_ref = _hash_ref(
                    "receipt-ref:work-board-adoption-restore",
                    {
                        "idempotency_ref": idempotency_ref,
                        "after_revision": preview.resulting_revision,
                    },
                )
                provisional = WorkBoardAdoptionMutationReceipt(
                    action="restore_backup",
                    target_ref=None,
                    card_ref=None,
                    before_revision=current.revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    backup_fingerprint_ref=(
                        request.backup.ciphertext_fingerprint_ref
                    ),
                    backup_revision=restored.revision,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                    authority_decision_ref=authority_decision_ref,
                    authority_lease_ref=lease.lease_ref,
                    receipt_ref=receipt_ref,
                    state_ref="state-ref:work-board-adoption:sha256:pending",
                    rollback_ref=_hash_ref(
                        "rollback-ref:work-board-adoption",
                        {"receipt_ref": receipt_ref, "action": "undo"},
                    ),
                    safe_summary=(
                        "One encrypted local Work Board backup was restored after exact "
                        "confirmation."
                    ),
                )
                undo_stack = (
                    (WorkBoardAdoptionSnapshot(cards=current.cards),)
                    if current_readable and self.state_path.exists()
                    else ()
                )
                merged_receipts = self._merged_restore_receipts(
                    current=current,
                    restored=restored,
                    receipt=provisional,
                )
                next_state = WorkBoardAdoptionState(
                    revision=preview.resulting_revision,
                    cards=restored.cards,
                    undo_stack=undo_stack,
                    receipts=merged_receipts,
                )
                state_ref = self._state_ref(next_state)
                receipt = provisional.model_copy(update={"state_ref": state_ref})
                next_state = next_state.model_copy(
                    update={"receipts": tuple([*merged_receipts[:-1], receipt])}
                )
                self._write_state(next_state)
                return receipt
            except Exception:
                self._revoke_lease(lease_store, lease)
                raise

    def _preview(
        self,
        state: WorkBoardAdoptionState,
        request: WorkBoardAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionMutationPreview:
        if request.expected_revision != state.revision:
            raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_STALE_REVISION")
        payload_fingerprint_ref = self._payload_fingerprint(
            request,
            idempotency_ref=idempotency_ref,
        )
        existing = self._card(state, request.target_ref) if request.target_ref else None
        card_ref = (
            _hash_ref(
                "work-board-card-ref:founder-private",
                {
                    "idempotency_ref": idempotency_ref,
                    "payload_fingerprint_ref": payload_fingerprint_ref,
                },
            )
            if request.action == "create"
            else request.target_ref
        )
        if request.action == "create":
            if len(state.cards) >= WORK_BOARD_ADOPTION_MAX_CARDS:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_CARD_LIMIT")
        elif request.action == "update":
            if existing is None or existing.archived:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_ACTIVE_CARD_REQUIRED")
        elif request.action == "move":
            if existing is None or existing.archived:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_ACTIVE_CARD_REQUIRED")
            if existing.lane_ref == request.lane_ref:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_MOVE_NO_CHANGE")
        elif request.action == "archive":
            if existing is None or existing.archived:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_ACTIVE_CARD_REQUIRED")
        elif request.action == "recover":
            if existing is None or not existing.archived:
                raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_ARCHIVED_CARD_REQUIRED")
        elif not state.undo_stack:
            raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_UNDO_EMPTY")
        preview_ref = _hash_ref(
            "preview-ref:work-board-adoption",
            {
                "action": request.action,
                "card_ref": card_ref,
                "expected_revision": state.revision,
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "state_ref": self._state_ref(state),
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:work-board-adoption",
            {
                "preview_ref": preview_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
            },
        )
        summaries = {
            "create": "Create one founder-private local Work Board item.",
            "update": "Update the selected founder-private Work Board item.",
            "move": "Move the selected item to another local board lane.",
            "archive": "Archive the selected local Work Board item.",
            "recover": "Recover the selected archived Work Board item.",
            "undo": "Undo the most recent local Work Board change.",
        }
        return WorkBoardAdoptionMutationPreview(
            action=request.action,
            expected_revision=state.revision,
            resulting_revision=state.revision + 1,
            target_ref=request.target_ref,
            card_ref=card_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            safe_summary=summaries[request.action],
        )

    def _preview_restore(
        self,
        request: WorkBoardAdoptionPortableRestoreRequest,
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionPortableRestorePreview:
        current, current_readable = self._read_current_for_restore()
        restored = self._open_portable_backup(request)
        return self._build_restore_preview(
            request,
            restored=restored,
            current=current,
            current_readable=current_readable,
            idempotency_ref=idempotency_ref,
        )

    def _build_restore_preview(
        self,
        request: WorkBoardAdoptionPortableRestoreRequest,
        *,
        restored: WorkBoardAdoptionState,
        current: WorkBoardAdoptionState,
        current_readable: bool,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionPortableRestorePreview:
        base_revision = max(current.revision, restored.revision)
        if base_revision >= WORK_BOARD_ADOPTION_MAX_REVISION:
            raise WorkBoardAdoptionConflict(
                "WORK_BOARD_ADOPTION_REVISION_CAPACITY_EXHAUSTED"
            )
        current_state_ref = self._current_state_ref()
        payload_fingerprint_ref = _hash_ref(
            "payload-fingerprint-ref:work-board-adoption-restore",
            {
                "backup_fingerprint_ref": (
                    request.backup.ciphertext_fingerprint_ref
                ),
                "current_state_ref": current_state_ref,
                "idempotency_ref": idempotency_ref,
                "resulting_revision": base_revision + 1,
            },
        )
        preview_ref = _hash_ref(
            "preview-ref:work-board-adoption-restore",
            {
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "backup_revision": restored.revision,
                "current_state_readable": current_readable,
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:work-board-adoption-restore",
            {"preview_ref": preview_ref},
        )
        return WorkBoardAdoptionPortableRestorePreview(
            expected_revision=current.revision,
            resulting_revision=base_revision + 1,
            current_state_ref=current_state_ref,
            backup_revision=restored.revision,
            card_count=len(restored.cards),
            rollback_available=current_readable and self.state_path.exists(),
            impact_status=("exact" if current_readable else "unknown_current_state"),
            payload_fingerprint_ref=payload_fingerprint_ref,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
        )

    def _capture_preview_approval(
        self,
        preview: (
            WorkBoardAdoptionMutationPreview
            | WorkBoardAdoptionPortableRestorePreview
        ),
        *,
        idempotency_ref: str,
    ) -> WorkBoardAdoptionApprovalReceipt:
        (
            lease_store,
            lease_request,
            lease_idempotency_ref,
            _,
            _,
            _,
        ) = self._lease_context(preview, idempotency_ref=idempotency_ref)
        lease_approval_ref = self._lease_approval_ref(
            approval_ref=preview.approval_ref,
            lease_idempotency_ref=lease_idempotency_ref,
        )
        try:
            requirement, grant = capture_authority_lease_backend_approval(
                lease_store,
                lease_request,
                idempotency_ref=lease_idempotency_ref,
                approved_by_actor_id="operator-ref:local-user",
                approval_ref=lease_approval_ref,
                approval_ttl_minutes=WORK_BOARD_ADOPTION_APPROVAL_TTL_MINUTES,
            )
        except AuthorityLeaseApprovalConflictError as exc:
            raise WorkBoardAdoptionConflict(
                "WORK_BOARD_ADOPTION_APPROVAL_CONFLICT"
            ) from exc
        except AuthorityLeaseApprovalCapacityError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_APPROVAL_CAPACITY_EXHAUSTED"
            ) from exc
        except AuthorityLeaseApprovalStateError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_APPROVAL_STATE_INVALID"
            ) from exc
        if (
            grant is None
            or grant.approval_ref != lease_approval_ref
            or grant.expires_at is None
        ):
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_EXACT_APPROVAL_REQUIRED"
            )
        approved_request = lease_request.model_copy(
            update={"approval_ref": lease_approval_ref}
        )
        try:
            decision = AuthorityLeaseApprovalStore(lease_store.state_dir).validate(
                approved_request,
                requirement,
            )
        except AuthorityLeaseApprovalStateError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_APPROVAL_STATE_INVALID"
            ) from exc
        if decision is None or not decision.allowed:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_EXACT_APPROVAL_REQUIRED"
            )
        return WorkBoardAdoptionApprovalReceipt(
            approval_ref=preview.approval_ref,
            approval_validation_ref=decision.decision_id,
            preview_ref=preview.preview_ref,
            idempotency_ref=idempotency_ref,
            expires_at=grant.expires_at,
        )

    @staticmethod
    def _replay_captured_approval(
        prior: WorkBoardAdoptionMutationReceipt,
        *,
        action: str,
        payload_fingerprint_ref: str,
        preview_ref: str,
        approval_ref: str,
        idempotency_ref: str,
        backup_fingerprint_ref: str | None = None,
    ) -> WorkBoardAdoptionApprovalReceipt:
        if (
            prior.action != action
            or prior.payload_fingerprint_ref != payload_fingerprint_ref
            or prior.preview_ref != preview_ref
            or prior.approval_ref != approval_ref
            or prior.backup_fingerprint_ref != backup_fingerprint_ref
        ):
            raise WorkBoardAdoptionConflict(
                "WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT"
            )
        return WorkBoardAdoptionApprovalReceipt(
            approval_ref=prior.approval_ref,
            approval_validation_ref=prior.approval_validation_ref,
            preview_ref=prior.preview_ref,
            idempotency_ref=idempotency_ref,
            expires_at=prior.approval_expires_at,
        )

    @staticmethod
    def _card(
        state: WorkBoardAdoptionState,
        target_ref: str | None,
    ) -> WorkBoardAdoptionCard | None:
        return next(
            (card for card in state.cards if card.card_ref == target_ref),
            None,
        )

    @staticmethod
    def _payload_fingerprint(
        request: WorkBoardAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> str:
        return _hash_ref(
            "payload-fingerprint-ref:work-board-adoption",
            {
                "request": request.model_dump(mode="json"),
                "idempotency_ref": idempotency_ref,
            },
        )

    def _apply_mutation(
        self,
        state: WorkBoardAdoptionState,
        request: WorkBoardAdoptionMutationRequest,
        *,
        preview: WorkBoardAdoptionMutationPreview,
    ) -> tuple[tuple[WorkBoardAdoptionCard, ...], tuple[WorkBoardAdoptionSnapshot, ...]]:
        if request.action == "undo":
            snapshot = state.undo_stack[-1]
            return snapshot.cards, state.undo_stack[:-1]
        history = tuple(
            [
                *state.undo_stack[-(WORK_BOARD_ADOPTION_MAX_UNDO - 1) :],
                WorkBoardAdoptionSnapshot(cards=state.cards),
            ]
        )
        if request.action == "create":
            assert request.draft is not None and preview.card_ref is not None
            added = WorkBoardAdoptionCard(
                card_ref=preview.card_ref,
                **request.draft.model_dump(mode="python"),
            )
            return tuple([*state.cards, added]), history
        assert request.target_ref is not None
        target = self._card(state, request.target_ref)
        if target is None:
            raise WorkBoardAdoptionConflict("WORK_BOARD_ADOPTION_CARD_NOT_FOUND")
        if request.action == "update":
            assert request.draft is not None
            replacement = target.model_copy(
                update={**request.draft.model_dump(mode="python"), "archived": False}
            )
        elif request.action == "move":
            assert request.lane_ref is not None
            replacement = target.model_copy(update={"lane_ref": request.lane_ref})
        elif request.action == "archive":
            replacement = target.model_copy(update={"archived": True})
        else:
            replacement = target.model_copy(update={"archived": False})
        return tuple(
            replacement if card.card_ref == request.target_ref else card
            for card in state.cards
        ), history

    def _lease_context(
        self,
        preview: (
            WorkBoardAdoptionMutationPreview
            | WorkBoardAdoptionPortableRestorePreview
        ),
        *,
        idempotency_ref: str,
    ) -> tuple[
        AuthorityLeaseStore,
        AuthorityLeaseIssueRequest,
        str,
        list[str],
        str,
        str,
    ]:
        revision_ref = f"revision-ref:work-board-adoption:{preview.expected_revision}"
        action_ref = f"action-ref:work-board-adoption:{preview.action}"
        route_ref = (
            WORK_BOARD_ADOPTION_RESTORE_ROUTE_REF
            if preview.action == "restore_backup"
            else WORK_BOARD_ADOPTION_ROUTE_REF
        )
        resource_refs = [
            WORK_BOARD_ADOPTION_CONTRACT_REF,
            WORK_BOARD_ADOPTION_BOARD_REF,
            preview.preview_ref,
            preview.approval_ref,
            preview.payload_fingerprint_ref,
            idempotency_ref,
            action_ref,
            revision_ref,
        ]
        suffix = hashlib.sha256(
            preview.payload_fingerprint_ref.encode("utf-8")
        ).hexdigest()[:24]
        request = AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            scope=AuthorityLeaseScope.session,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.write]
            },
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=(
                        f"authority-constraint-ref:work-board-adoption:resources:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resource_refs,
                    safe_summary=(
                        "Restrict one founder-private Work Board change to exact "
                        "preview, approval, revision, payload, and idempotency refs."
                    ),
                ),
                AuthorityConstraint(
                    constraint_ref=(
                        f"authority-constraint-ref:work-board-adoption:budget:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Permit one exact local Work Board state write.",
                ),
            ],
            constraints={
                "exact_lane_ref": WORK_BOARD_ADOPTION_AUTHORITY_LANE_REF,
                "exact_action_ref": action_ref,
                "exact_route_ref": route_ref,
                "exact_contract_ref": WORK_BOARD_ADOPTION_CONTRACT_REF,
                "exact_preview_ref": preview.preview_ref,
                "exact_approval_ref": preview.approval_ref,
                "exact_payload_fingerprint_ref": preview.payload_fingerprint_ref,
                "exact_idempotency_ref": idempotency_ref,
                "exact_revision_ref": revision_ref,
                "exact_safe_disable_ref": WORK_BOARD_ADOPTION_SAFE_DISABLE_REF,
            },
            decision_reason_ref=(
                "decision-reason-ref:work-board-adoption:operator-confirmed"
            ),
            duration_minutes=WORK_BOARD_ADOPTION_APPROVAL_TTL_MINUTES,
            safe_summary=(
                "Issue one exact operator-confirmed local Work Board write lease."
            ),
        )
        lease_store = AuthorityLeaseStore(self.state_dir / "authority")
        lease_idempotency_ref = _hash_ref(
            "idempotency-ref:work-board-adoption-lease",
            {
                "idempotency_ref": idempotency_ref,
                "payload_fingerprint_ref": preview.payload_fingerprint_ref,
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
            "approval-ref:work-board-adoption-lease-scope",
            {
                "approval_ref": approval_ref,
                "lease_idempotency_ref": lease_idempotency_ref,
            },
        )

    def _authorize(
        self,
        preview: (
            WorkBoardAdoptionMutationPreview
            | WorkBoardAdoptionPortableRestorePreview
        ),
        *,
        idempotency_ref: str,
    ) -> tuple[AuthorityLeaseStore, AuthorityLease, str, str, datetime]:
        (
            lease_store,
            lease_request,
            lease_idempotency_ref,
            resource_refs,
            action_ref,
            route_ref,
        ) = self._lease_context(preview, idempotency_ref=idempotency_ref)
        requirement = build_authority_lease_approval_requirement_for_request(
            lease_request,
            idempotency_ref=lease_idempotency_ref,
        )
        lease_approval_ref = self._lease_approval_ref(
            approval_ref=preview.approval_ref,
            lease_idempotency_ref=lease_idempotency_ref,
        )
        approval_store = AuthorityLeaseApprovalStore(lease_store.state_dir)
        record = approval_store.resolve(lease_approval_ref)
        if record is None:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_EXACT_APPROVAL_REQUIRED")
        grant = record.grant
        maximum_expiry = grant.created_at + timedelta(
            minutes=WORK_BOARD_ADOPTION_APPROVAL_TTL_MINUTES
        )
        if (
            grant.expires_at is None
            or grant.expires_at > maximum_expiry
            or grant.expires_at <= _utc_now()
        ):
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_APPROVAL_EXPIRED")
        approved_request = lease_request.model_copy(
            update={"approval_ref": lease_approval_ref}
        )
        try:
            approval_decision = approval_store.validate(
                approved_request,
                requirement,
            )
            lease, receipt = issue_authority_lease_from_backend_state(
                lease_store,
                approved_request,
                idempotency_ref=lease_idempotency_ref,
            )
        except AuthorityLeaseApprovalStateError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_AUTHORITY_STATE_INVALID"
            ) from exc
        if (
            approval_decision is None
            or not approval_decision.allowed
            or lease is None
            or lease.status == "revoked"
            or receipt.status not in {"issued", "replayed"}
        ):
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_EXACT_LEASE_ISSUANCE_DENIED"
            )
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=action_ref,
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.write,
                safe_summary="Evaluate one exact local Work Board state change.",
                resource_refs=resource_refs,
                route_ref=route_ref,
                lane_ref=WORK_BOARD_ADOPTION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget,
                        value=1,
                    )
                ],
                rollback_ref=_hash_ref(
                    "rollback-ref:work-board-adoption",
                    {"preview_ref": preview.preview_ref, "action": "undo"},
                ),
                safe_disable_ref=WORK_BOARD_ADOPTION_SAFE_DISABLE_REF,
            ),
            [lease],
        )
        if decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            self._revoke_lease(lease_store, lease)
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_AUTHORITY_DENIED")
        return (
            lease_store,
            lease,
            decision.decision_ref,
            approval_decision.decision_id,
            grant.expires_at,
        )

    @staticmethod
    def _revoke_lease(
        lease_store: AuthorityLeaseStore,
        lease: AuthorityLease,
    ) -> None:
        if lease.status == "revoked":
            return
        # Failed writes retain no usable broad capability. The lease is exact,
        # operation-budgeted, and expires after five minutes; revocation failure
        # is therefore reported without masking the original persistence error.
        try:
            from ultimate_ai_agent.core.authority import AuthorityLeaseRevokeRequest

            lease_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=lease.lease_ref,
                    decision_reason_ref=(
                        "decision-reason-ref:work-board-adoption:commit-failed"
                    ),
                    safe_summary=(
                        "Revoke the exact Work Board lease after local persistence failed."
                    ),
                ),
                idempotency_ref=_hash_ref(
                    "idempotency-ref:work-board-adoption-lease-revoke",
                    {"lease_ref": lease.lease_ref},
                ),
            )
        except Exception as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_LEASE_REVOCATION_FAILED"
            ) from exc

    @staticmethod
    def _derive_backup_key(passphrase: str, salt: bytes) -> bytes:
        return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
            passphrase.encode("utf-8")
        )

    def _open_portable_backup(
        self,
        request: WorkBoardAdoptionPortableRestoreRequest,
    ) -> WorkBoardAdoptionState:
        ciphertext = _decode_b64(request.backup.ciphertext)
        if len(ciphertext) > WORK_BOARD_ADOPTION_MAX_BACKUP_BYTES:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_BACKUP_SIZE_LIMIT")
        fingerprint = hashlib.sha256(ciphertext).hexdigest()
        if request.backup.ciphertext_fingerprint_ref != (
            f"ciphertext-fingerprint-ref:sha256:{fingerprint}"
        ):
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_BACKUP_FINGERPRINT_INVALID"
            )
        salt = _decode_b64(request.backup.salt)
        nonce = _decode_b64(request.backup.nonce)
        if len(salt) != 16 or len(nonce) != 12:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_BACKUP_INVALID")
        try:
            plaintext = AESGCM(
                self._derive_backup_key(request.passphrase, salt)
            ).decrypt(nonce, ciphertext, _BACKUP_AAD)
            if len(plaintext) > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
                raise WorkBoardAdoptionError(
                    "WORK_BOARD_ADOPTION_BACKUP_SIZE_LIMIT"
                )
            return WorkBoardAdoptionState.model_validate_json(plaintext)
        except (InvalidTag, UnicodeDecodeError, ValueError) as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_BACKUP_UNLOCK_FAILED"
            ) from exc

    def _read_current_for_restore(
        self,
    ) -> tuple[WorkBoardAdoptionState, bool]:
        if not self.state_path.exists():
            return WorkBoardAdoptionState(), True
        try:
            return self._read_state(), True
        except (OSError, ValueError, WorkBoardAdoptionError):
            return WorkBoardAdoptionState(), False

    def _current_state_ref(self) -> str:
        descriptor = -1
        try:
            descriptor = os.open(
                self.state_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                return "state-ref:work-board-adoption:unsafe"
            if metadata.st_size > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
                return "state-ref:work-board-adoption:oversize"
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                payload = handle.read(WORK_BOARD_ADOPTION_MAX_STATE_BYTES + 1)
            if len(payload) > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
                return "state-ref:work-board-adoption:oversize"
        except FileNotFoundError:
            return "state-ref:work-board-adoption:empty"
        except OSError:
            return "state-ref:work-board-adoption:unreadable"
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        return (
            "state-ref:work-board-adoption-raw:sha256:"
            f"{hashlib.sha256(payload).hexdigest()}"
        )

    @staticmethod
    def _merged_restore_receipts(
        *,
        current: WorkBoardAdoptionState,
        restored: WorkBoardAdoptionState,
        receipt: WorkBoardAdoptionMutationReceipt,
    ) -> tuple[WorkBoardAdoptionMutationReceipt, ...]:
        merged: dict[str, WorkBoardAdoptionMutationReceipt] = {}
        for candidate in [*restored.receipts, *current.receipts, receipt]:
            prior = merged.get(candidate.idempotency_ref)
            if prior is not None and (
                prior.payload_fingerprint_ref != candidate.payload_fingerprint_ref
            ):
                raise WorkBoardAdoptionConflict(
                    "WORK_BOARD_ADOPTION_RESTORE_RECEIPT_CONFLICT"
                )
            merged[candidate.idempotency_ref] = candidate
        return tuple(list(merged.values())[-WORK_BOARD_ADOPTION_MAX_RECEIPTS:])

    def _read_state(self) -> WorkBoardAdoptionState:
        if not self.state_path.exists():
            return WorkBoardAdoptionState()
        try:
            descriptor = os.open(
                self.state_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
            with os.fdopen(descriptor, "rb") as handle:
                metadata = os.fstat(handle.fileno())
                if not stat.S_ISREG(metadata.st_mode):
                    raise WorkBoardAdoptionError(
                        "WORK_BOARD_ADOPTION_STATE_OBJECT_UNSAFE"
                    )
                if metadata.st_size > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
                    raise WorkBoardAdoptionError(
                        "WORK_BOARD_ADOPTION_STATE_SIZE_LIMIT"
                    )
                encoded = handle.read(WORK_BOARD_ADOPTION_MAX_STATE_BYTES + 1)
            if len(encoded) > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
                raise WorkBoardAdoptionError(
                    "WORK_BOARD_ADOPTION_STATE_SIZE_LIMIT"
                )
            payload = json.loads(encoded.decode("utf-8"))
            return WorkBoardAdoptionState.model_validate(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_STATE_INVALID") from exc
        except OSError as exc:
            raise WorkBoardAdoptionError(
                "WORK_BOARD_ADOPTION_STATE_READ_FAILED"
            ) from exc

    def _write_state(self, state: WorkBoardAdoptionState) -> None:
        payload = _canonical_json(state.model_dump(mode="json"))
        if len(payload) > WORK_BOARD_ADOPTION_MAX_STATE_BYTES:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_STATE_SIZE_LIMIT")
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.state_dir, 0o700)
        descriptor = -1
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.state_dir,
                prefix=".work_board_adoption.",
                suffix=".tmp",
            )
            temporary = Path(temporary_name)
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_path)
            temporary = None
            os.chmod(self.state_path, 0o600)
            _fsync_directory(self.state_dir)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    @staticmethod
    def _state_ref(state: WorkBoardAdoptionState) -> str:
        return _hash_ref(
            "state-ref:work-board-adoption",
            {
                "board_ref": state.board_ref,
                "revision": state.revision,
                "cards": [card.model_dump(mode="json") for card in state.cards],
                "undo_stack": [
                    snapshot.model_dump(mode="json") for snapshot in state.undo_stack
                ],
            },
        )
