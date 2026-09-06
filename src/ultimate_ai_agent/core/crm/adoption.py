"""Founder-private CRM adoption repository for Queue V2 Q32.

The repository keeps private record values inside one AES-256-GCM envelope,
records only content-free audit refs, and exposes exact preview/commit/restore
lanes.  It is intentionally local-only: no connector, provider, model, web,
send, or external CRM authority is granted here.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
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
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.crm.private_repository import ECO_CRM_SCHEMA_VERSION
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager


CRM_ADOPTION_CONTRACT_REF = "contract-ref:queue-v2-q32-crm-adoption:v1"
CRM_ADOPTION_FOUNDATION_REF = ECO_CRM_SCHEMA_VERSION
CRM_ADOPTION_ROUTE_REF = "POST /control-center/crm/adoption/commit"
CRM_ADOPTION_BACKUP_ROUTE_REF = "POST /control-center/crm/adoption/restore"
CRM_ADOPTION_AUTHORITY_LANE_REF = "authority-lane-ref:crm-adoption-local-write"
CRM_ADOPTION_SAFE_DISABLE_REF = "safe-disable-ref:crm-adoption-local-write:deny"
CRM_ADOPTION_MAX_RECORDS = 10_000
CRM_ADOPTION_MAX_IMPORT_ROWS = 500
CRM_ADOPTION_MAX_UNDO = 20
CRM_ADOPTION_MAX_RECEIPTS = 2_000
CRM_ADOPTION_MAX_BACKUP_BYTES = 32 * 1024 * 1024
CRM_ADOPTION_MAX_STATE_BYTES = 32 * 1024 * 1024
CRM_ADOPTION_MAX_AUDIT_BYTES = 16 * 1024 * 1024
CRM_ADOPTION_MAX_BACKUP_B64_CHARS = ((CRM_ADOPTION_MAX_BACKUP_BYTES + 2) // 3) * 4
_STATE_MAGIC = b"UAACRMQ32\x00"
_STATE_AAD = b"uaa:crm-adoption:state:v1"
_BACKUP_AAD = b"uaa:crm-adoption:portable-backup:v1"
_LOCK_KEY = "crm-adoption-state"


class CrmAdoptionError(RuntimeError):
    """Safe-code-only Q32 CRM error."""


class CrmAdoptionConflict(CrmAdoptionError):
    """An exact revision, idempotency, or preview binding did not match."""


class _PrivateModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        str_strip_whitespace=True,
    )


CrmAdoptionRecordKind = Literal[
    "person",
    "organization",
    "property",
    "relationship",
    "opportunity",
    "activity",
    "follow_up",
]


def _private_text(value: str | None, *, maximum: int, required: bool = False) -> None:
    if value is None:
        if required:
            raise ValueError("CRM_ADOPTION_PRIVATE_TEXT_REQUIRED")
        return
    if (required and not value) or len(value.encode("utf-8")) > maximum:
        raise ValueError("CRM_ADOPTION_PRIVATE_TEXT_INVALID")
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError("CRM_ADOPTION_PRIVATE_TEXT_INVALID")


def _private_ref(value: str) -> None:
    if (
        len(value) < 3
        or len(value) > 220
        or not value[0].isalpha()
        or any(not (character.isalnum() or character in "_.:-") for character in value)
    ):
        raise ValueError("CRM_ADOPTION_SAFE_REF_REQUIRED")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _hash_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode_b64(value: str, *, code: str) -> bytes:
    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise CrmAdoptionError(code) from exc
    if not decoded:
        raise CrmAdoptionError(code)
    return decoded


class CrmAdoptionRecord(_PrivateModel):
    record_ref: str
    record_kind: CrmAdoptionRecordKind
    display_name: str
    subtitle: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=64)
    status: str | None = None
    related_refs: list[str] = Field(default_factory=list, max_length=64)
    due_at: datetime | None = None
    occurred_at: datetime | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    currency: str | None = None
    priority: Literal["high", "medium", "low"] | None = None
    archived: bool = False
    version: int = Field(default=1, ge=1)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_record(self) -> "CrmAdoptionRecord":
        _private_ref(self.record_ref)
        _private_text(self.display_name, maximum=2_048, required=True)
        for value, maximum in (
            (self.subtitle, 2_048),
            (self.email, 8_192),
            (self.phone, 2_048),
            (self.website, 8_192),
            (self.notes, 131_072),
            (self.status, 1_024),
            (self.currency, 32),
        ):
            _private_text(value, maximum=maximum)
        for tag in self.tags:
            _private_text(tag, maximum=256, required=True)
        if len(self.tags) != len(set(item.casefold() for item in self.tags)):
            raise ValueError("CRM_ADOPTION_DUPLICATE_TAG")
        for related_ref in self.related_refs:
            _private_ref(related_ref)
        if len(self.related_refs) != len(set(self.related_refs)):
            raise ValueError("CRM_ADOPTION_DUPLICATE_RELATED_REF")
        for timestamp in (self.created_at, self.updated_at, self.due_at, self.occurred_at):
            if timestamp is not None and timestamp.tzinfo is None:
                raise ValueError("CRM_ADOPTION_TIMESTAMP_TIMEZONE_REQUIRED")
        return self


class CrmAdoptionRecordDraft(_PrivateModel):
    record_kind: CrmAdoptionRecordKind
    display_name: str
    subtitle: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=64)
    status: str | None = None
    related_refs: list[str] = Field(default_factory=list, max_length=64)
    due_at: datetime | None = None
    occurred_at: datetime | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    currency: str | None = None
    priority: Literal["high", "medium", "low"] | None = None

    @model_validator(mode="after")
    def validate_draft(self) -> "CrmAdoptionRecordDraft":
        now = _utc_now()
        CrmAdoptionRecord(
            record_ref="record-ref:crm-private:validation",
            created_at=now,
            updated_at=now,
            **self.model_dump(mode="python"),
        )
        return self


class CrmAdoptionRecordPatch(_PrivateModel):
    display_name: str | None = None
    subtitle: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    tags: list[str] | None = Field(default=None, max_length=64)
    status: str | None = None
    related_refs: list[str] | None = Field(default=None, max_length=64)
    due_at: datetime | None = None
    occurred_at: datetime | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    currency: str | None = None
    priority: Literal["high", "medium", "low"] | None = None
    clear_fields: list[
        Literal[
            "subtitle",
            "email",
            "phone",
            "website",
            "notes",
            "status",
            "due_at",
            "occurred_at",
            "amount_minor",
            "currency",
            "priority",
        ]
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_patch(self) -> "CrmAdoptionRecordPatch":
        if len(self.clear_fields) != len(set(self.clear_fields)):
            raise ValueError("CRM_ADOPTION_DUPLICATE_CLEAR_FIELD")
        if set(self.clear_fields) & (self.model_fields_set - {"clear_fields"}):
            raise ValueError("CRM_ADOPTION_PATCH_CLEAR_CONFLICT")
        if not self.model_fields_set - {"clear_fields"} and not self.clear_fields:
            raise ValueError("CRM_ADOPTION_EMPTY_PATCH")
        for value, maximum in (
            (self.display_name, 2_048),
            (self.subtitle, 2_048),
            (self.email, 8_192),
            (self.phone, 2_048),
            (self.website, 8_192),
            (self.notes, 131_072),
            (self.status, 1_024),
            (self.currency, 32),
        ):
            _private_text(value, maximum=maximum)
        if self.display_name is not None and not self.display_name:
            raise ValueError("CRM_ADOPTION_DISPLAY_NAME_REQUIRED")
        if self.tags is not None:
            for tag in self.tags:
                _private_text(tag, maximum=256, required=True)
            if len(self.tags) != len(set(item.casefold() for item in self.tags)):
                raise ValueError("CRM_ADOPTION_DUPLICATE_TAG")
        if self.related_refs is not None:
            for related_ref in self.related_refs:
                _private_ref(related_ref)
            if len(self.related_refs) != len(set(self.related_refs)):
                raise ValueError("CRM_ADOPTION_DUPLICATE_RELATED_REF")
        for timestamp in (self.due_at, self.occurred_at):
            if timestamp is not None and timestamp.tzinfo is None:
                raise ValueError("CRM_ADOPTION_TIMESTAMP_TIMEZONE_REQUIRED")
        return self


class CrmAdoptionMutationRequest(_PrivateModel):
    action: Literal["create", "update", "archive", "restore", "undo", "import_contacts"]
    expected_revision: int = Field(..., ge=0)
    target_ref: str | None = None
    record: CrmAdoptionRecordDraft | None = None
    patch: CrmAdoptionRecordPatch | None = None
    csv_text: str | None = Field(default=None, max_length=2_000_000, repr=False)

    @model_validator(mode="after")
    def validate_action(self) -> "CrmAdoptionMutationRequest":
        if self.target_ref is not None:
            _private_ref(self.target_ref)
        if self.action == "create" and (
            self.record is None
            or self.target_ref is not None
            or self.patch is not None
            or self.csv_text is not None
        ):
            raise ValueError("CRM_ADOPTION_CREATE_SHAPE_INVALID")
        if self.action == "update" and (
            self.target_ref is None
            or self.patch is None
            or self.record is not None
            or self.csv_text is not None
        ):
            raise ValueError("CRM_ADOPTION_UPDATE_SHAPE_INVALID")
        if self.action in {"archive", "restore"} and (
            self.target_ref is None
            or self.record is not None
            or self.patch is not None
            or self.csv_text is not None
        ):
            raise ValueError("CRM_ADOPTION_LIFECYCLE_SHAPE_INVALID")
        if self.action == "undo" and any(
            value is not None
            for value in (self.target_ref, self.record, self.patch, self.csv_text)
        ):
            raise ValueError("CRM_ADOPTION_UNDO_SHAPE_INVALID")
        if self.action == "import_contacts" and (
            not self.csv_text
            or self.target_ref is not None
            or self.record is not None
            or self.patch is not None
        ):
            raise ValueError("CRM_ADOPTION_IMPORT_SHAPE_INVALID")
        return self


class CrmAdoptionMutationPreview(_PrivateModel):
    schema_version: Literal["uaa-crm-adoption-mutation-preview.v1"] = (
        "uaa-crm-adoption-mutation-preview.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q32-crm-adoption:v1"] = (
        CRM_ADOPTION_CONTRACT_REF
    )
    action: str
    expected_revision: int
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    affected_count: int
    duplicate_candidate_count: int = 0
    safe_summary: str
    private_preview_labels: list[str] = Field(default_factory=list, repr=False)
    local_only: Literal[True] = True
    external_write_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False


class CrmAdoptionCommitRequest(_PrivateModel):
    mutation: CrmAdoptionMutationRequest
    preview_ref: str
    approval_ref: str

    @model_validator(mode="after")
    def validate_refs(self) -> "CrmAdoptionCommitRequest":
        _private_ref(self.preview_ref)
        _private_ref(self.approval_ref)
        return self


class CrmAdoptionMutationReceipt(_PrivateModel):
    schema_version: Literal["uaa-crm-adoption-mutation-receipt.v1"] = (
        "uaa-crm-adoption-mutation-receipt.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q32-crm-adoption:v1"] = (
        CRM_ADOPTION_CONTRACT_REF
    )
    receipt_ref: str
    action: str
    target_ref: str | None = None
    idempotency_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    approval_validation_ref: str
    authority_lease_ref: str
    authority_decision_ref: str
    before_revision: int
    after_revision: int
    rollback_ref: str
    safe_summary: str
    replayed: bool = False
    local_write_performed: Literal[True] = True
    external_write_performed: Literal[False] = False
    raw_private_values_included: Literal[False] = False
    approval_authority_granted: Literal[True] = True

    @model_validator(mode="after")
    def validate_receipt(self) -> "CrmAdoptionMutationReceipt":
        for value in (
            self.receipt_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.preview_ref,
            self.approval_ref,
            self.approval_validation_ref,
            self.authority_lease_ref,
            self.authority_decision_ref,
            self.rollback_ref,
        ):
            _private_ref(value)
        if self.target_ref is not None:
            _private_ref(self.target_ref)
        if self.after_revision <= self.before_revision:
            raise ValueError("CRM_ADOPTION_RECEIPT_REVISION_INVALID")
        return self


class CrmAdoptionSnapshot(_PrivateModel):
    workspace_name: str = "My private CRM"
    workspace_preset: Literal[
        "personal_network",
        "private_relationships",
        "sales",
        "real_estate",
        "professional_network",
    ] = "real_estate"
    records: list[CrmAdoptionRecord] = Field(
        default_factory=list, max_length=CRM_ADOPTION_MAX_RECORDS
    )

    @model_validator(mode="after")
    def validate_snapshot(self) -> "CrmAdoptionSnapshot":
        _private_text(self.workspace_name, maximum=512, required=True)
        refs = [item.record_ref for item in self.records]
        if len(refs) != len(set(refs)):
            raise ValueError("CRM_ADOPTION_DUPLICATE_RECORD_REF")
        known = set(refs)
        if any(
            related_ref not in known or related_ref == record.record_ref
            for record in self.records
            for related_ref in record.related_refs
        ):
            raise ValueError("CRM_ADOPTION_RELATED_RECORD_NOT_FOUND")
        return self


class CrmAdoptionState(CrmAdoptionSnapshot):
    schema_version: Literal["uaa-crm-adoption-state.v1"] = "uaa-crm-adoption-state.v1"
    revision: int = Field(default=0, ge=0)
    undo_stack: list[CrmAdoptionSnapshot] = Field(
        default_factory=list, max_length=CRM_ADOPTION_MAX_UNDO, repr=False
    )
    receipts: list[CrmAdoptionMutationReceipt] = Field(
        default_factory=list, max_length=CRM_ADOPTION_MAX_RECEIPTS, repr=False
    )

    @model_validator(mode="after")
    def validate_state(self) -> "CrmAdoptionState":
        idempotency_refs = [item.idempotency_ref for item in self.receipts]
        if len(idempotency_refs) != len(set(idempotency_refs)):
            raise ValueError("CRM_ADOPTION_DUPLICATE_IDEMPOTENCY_REF")
        return self

    def snapshot(self) -> CrmAdoptionSnapshot:
        return CrmAdoptionSnapshot(
            workspace_name=self.workspace_name,
            workspace_preset=self.workspace_preset,
            records=self.records,
        )


class CrmAdoptionWorkspaceView(_PrivateModel):
    schema_version: Literal["uaa-crm-adoption-workspace.v1"] = (
        "uaa-crm-adoption-workspace.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q32-crm-adoption:v1"] = (
        CRM_ADOPTION_CONTRACT_REF
    )
    foundation_contract_ref: str = CRM_ADOPTION_FOUNDATION_REF
    storage_state: Literal["empty", "ready", "locked", "recovery_required"]
    revision: int
    workspace_name: str
    workspace_preset: str
    records: list[CrmAdoptionRecord]
    counts: dict[str, int]
    can_undo: bool
    next_safe_action: str
    private_values_included: Literal[True] = True
    private_values_confined_to_local_response: Literal[True] = True
    raw_paths_included: Literal[False] = False
    fixture_primary_truth: Literal[False] = False
    connector_runtime_enabled: Literal[False] = False
    external_crm_write_enabled: Literal[False] = False
    send_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False


class CrmPortableBackupRequest(_PrivateModel):
    passphrase: str = Field(..., min_length=12, max_length=1_024, repr=False)


class CrmPortableBackup(_PrivateModel):
    schema_version: Literal["uaa-crm-adoption-portable-backup.v1"] = (
        "uaa-crm-adoption-portable-backup.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q32-crm-adoption:v1"] = (
        CRM_ADOPTION_CONTRACT_REF
    )
    salt: str = Field(..., min_length=24, max_length=24)
    nonce: str = Field(..., min_length=16, max_length=16)
    ciphertext: str = Field(
        ..., min_length=24, max_length=CRM_ADOPTION_MAX_BACKUP_B64_CHARS, repr=False
    )
    ciphertext_fingerprint_ref: str
    created_at: datetime
    private_values_encrypted: Literal[True] = True
    key_material_included: Literal[False] = False
    raw_paths_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_backup(self) -> "CrmPortableBackup":
        _private_ref(self.ciphertext_fingerprint_ref)
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("CRM_ADOPTION_TIMESTAMP_TIMEZONE_REQUIRED")
        return self


class CrmPortableRestoreRequest(CrmPortableBackupRequest):
    backup: CrmPortableBackup


class CrmPortableRestorePreview(_PrivateModel):
    schema_version: Literal["uaa-crm-adoption-restore-preview.v1"] = (
        "uaa-crm-adoption-restore-preview.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q32-crm-adoption:v1"] = (
        CRM_ADOPTION_CONTRACT_REF
    )
    preview_ref: str
    approval_ref: str
    current_state_ref: str
    backup_revision: int
    record_count: int
    counts: dict[str, int]
    integrity_status: Literal["ok"] = "ok"
    private_values_included: Literal[False] = False
    restore_performed: Literal[False] = False


class CrmPortableRestoreCommitRequest(CrmPortableRestoreRequest):
    preview_ref: str
    approval_ref: str


class CrmAdoptionStore:
    """Encrypted local CRM state with exact preview/commit and portable recovery."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.state_file = state_dir / "crm_private_state.enc"
        self.key_file = state_dir / "crm_private_state.key"
        self.audit_file = state_dir / "crm_private_audit.jsonl"
        self.lock = FileSingleWriterLockManager(state_dir / ".locks")

    @classmethod
    def from_env(cls) -> "CrmAdoptionStore":
        configured = os.environ.get("UAA_CRM_ADOPTION_STATE_DIR", "").strip()
        if configured:
            return cls(Path(configured).expanduser())
        return cls(
            Path.home()
            / ".local"
            / "state"
            / "ultimate-ai-agent"
            / "crm_adoption"
        )

    def read_view(
        self,
        *,
        query: str = "",
        record_kind: CrmAdoptionRecordKind | None = None,
        include_archived: bool = False,
    ) -> CrmAdoptionWorkspaceView:
        try:
            state = self._read_state()
        except CrmAdoptionError as exc:
            storage_state = (
                "locked" if str(exc) == "CRM_ADOPTION_KEY_UNAVAILABLE" else "recovery_required"
            )
            return self._view(
                CrmAdoptionState(),
                records=[],
                storage_state=storage_state,
                next_safe_action=(
                    "Restore an encrypted CRM backup from the Recovery panel."
                ),
            )
        normalized_query = query.strip().casefold()
        records = [
            item
            for item in state.records
            if (include_archived or not item.archived)
            and (record_kind is None or item.record_kind == record_kind)
            and (
                not normalized_query
                or normalized_query
                in " ".join(
                    value
                    for value in (
                        item.display_name,
                        item.subtitle or "",
                        item.email or "",
                        item.phone or "",
                        item.website or "",
                        item.notes or "",
                        item.status or "",
                        " ".join(item.tags),
                    )
                ).casefold()
            )
        ]
        return self._view(
            state,
            records=records,
            storage_state="ready" if self.state_file.exists() else "empty",
            next_safe_action=(
                "Capture the next person, property, opportunity, activity, or follow-up."
                if state.records
                else "Create your first private CRM record."
            ),
        )

    def preview_mutation(
        self, request: CrmAdoptionMutationRequest
    ) -> CrmAdoptionMutationPreview:
        state = self._read_state()
        if request.expected_revision != state.revision:
            raise CrmAdoptionConflict("CRM_ADOPTION_STALE_REVISION")
        fingerprint = self._mutation_fingerprint(request)
        labels: list[str] = []
        affected_count = 1
        duplicate_count = 0
        if request.action == "create":
            assert request.record is not None
            if len(state.records) >= CRM_ADOPTION_MAX_RECORDS:
                raise CrmAdoptionError("CRM_ADOPTION_RECORD_CAPACITY_EXHAUSTED")
            labels = [request.record.display_name]
            self._validate_related_refs(state, request.record.related_refs)
        elif request.action in {"update", "archive", "restore"}:
            target = self._find_record(state, str(request.target_ref))
            labels = [target.display_name]
            if request.action == "archive" and target.archived:
                raise CrmAdoptionConflict("CRM_ADOPTION_RECORD_ALREADY_ARCHIVED")
            if request.action == "restore" and not target.archived:
                raise CrmAdoptionConflict("CRM_ADOPTION_RECORD_NOT_ARCHIVED")
            if request.patch is not None and request.patch.related_refs is not None:
                self._validate_related_refs(
                    state, request.patch.related_refs, target_ref=target.record_ref
                )
        elif request.action == "undo":
            if not state.undo_stack:
                raise CrmAdoptionConflict("CRM_ADOPTION_UNDO_EMPTY")
        else:
            rows = self._parse_import(str(request.csv_text))
            labels = [item.display_name for item in rows]
            duplicate_count = self._import_duplicate_count(state, rows)
            affected_count = len(rows) - duplicate_count
            if affected_count == 0:
                raise CrmAdoptionConflict("CRM_ADOPTION_IMPORT_NO_NEW_RECORDS")
            if len(state.records) + affected_count > CRM_ADOPTION_MAX_RECORDS:
                raise CrmAdoptionError("CRM_ADOPTION_RECORD_CAPACITY_EXHAUSTED")
        preview_ref = _hash_ref(
            "preview-ref:crm-adoption",
            {"revision": state.revision, "fingerprint": fingerprint},
        )
        approval_ref = _hash_ref(
            "approval-ref:crm-adoption",
            {"preview_ref": preview_ref, "action": request.action},
        )
        return CrmAdoptionMutationPreview(
            action=request.action,
            expected_revision=state.revision,
            payload_fingerprint_ref=fingerprint,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            affected_count=affected_count,
            duplicate_candidate_count=duplicate_count,
            safe_summary={
                "create": "Create one private CRM record locally.",
                "update": "Update one private CRM record locally.",
                "archive": "Archive one private CRM record locally.",
                "restore": "Restore one archived private CRM record locally.",
                "undo": "Undo the most recent local CRM change.",
                "import_contacts": "Import reviewed private contact rows locally without silent merging.",
            }[request.action],
            private_preview_labels=labels[:CRM_ADOPTION_MAX_IMPORT_ROWS],
        )

    def commit_mutation(
        self,
        *,
        request: CrmAdoptionMutationRequest,
        preview_ref: str,
        approval_ref: str,
        idempotency_ref: str,
        confirmed: bool,
    ) -> CrmAdoptionMutationReceipt:
        for value in (preview_ref, approval_ref, idempotency_ref):
            _private_ref(value)
        if not confirmed:
            raise CrmAdoptionError("CRM_ADOPTION_OPERATOR_CONFIRMATION_REQUIRED")
        self._secure_state_dir()
        with self.lock.acquire(_LOCK_KEY):
            state = self._read_state()
            fingerprint = self._mutation_fingerprint(request)
            prior = next(
                (
                    item
                    for item in state.receipts
                    if item.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if prior is not None:
                if (
                    prior.payload_fingerprint_ref != fingerprint
                    or prior.preview_ref != preview_ref
                    or prior.approval_ref != approval_ref
                ):
                    raise CrmAdoptionConflict("CRM_ADOPTION_IDEMPOTENCY_CONFLICT")
                return prior.model_copy(update={"replayed": True})
            preview = self.preview_mutation(request)
            if preview.preview_ref != preview_ref or preview.approval_ref != approval_ref:
                raise CrmAdoptionError("CRM_ADOPTION_EXACT_APPROVAL_REQUIRED")
            approval_validation_ref = self._capture_exact_approval(
                action=request.action,
                preview_ref=preview.preview_ref,
                approval_ref=approval_ref,
                payload_fingerprint_ref=fingerprint,
                expected_revision=request.expected_revision,
                idempotency_ref=idempotency_ref,
            )
            lease_store, lease, authority_decision_ref = (
                self._authorize_exact_local_write(
                    action=request.action,
                    preview_ref=preview.preview_ref,
                    approval_ref=approval_ref,
                    payload_fingerprint_ref=fingerprint,
                    expected_revision=request.expected_revision,
                    idempotency_ref=idempotency_ref,
                )
            )
            before_revision = state.revision
            try:
                updated, target_ref = self._apply_mutation(
                    state, request, idempotency_ref=idempotency_ref
                )
                receipt = CrmAdoptionMutationReceipt(
                    receipt_ref=_hash_ref(
                        "receipt-ref:crm-adoption",
                        {
                            "idempotency_ref": idempotency_ref,
                            "fingerprint": fingerprint,
                            "after_revision": updated.revision,
                        },
                    ),
                    action=request.action,
                    target_ref=target_ref,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=fingerprint,
                    preview_ref=preview_ref,
                    approval_ref=approval_ref,
                    approval_validation_ref=approval_validation_ref,
                    authority_lease_ref=lease.lease_ref,
                    authority_decision_ref=authority_decision_ref,
                    before_revision=before_revision,
                    after_revision=updated.revision,
                    rollback_ref=_hash_ref(
                        "rollback-ref:crm-adoption",
                        {"after_revision": updated.revision, "action": "undo"},
                    ),
                    safe_summary="One exact operator-confirmed private CRM change was committed locally.",
                )
                updated = updated.model_copy(
                    update={
                        "receipts": [
                            *updated.receipts[-(CRM_ADOPTION_MAX_RECEIPTS - 1) :],
                            receipt,
                        ]
                    }
                )
                self._append_audit(receipt)
                self._write_state(updated)
                return receipt
            except ValueError as exc:
                self._revoke_authority_lease(lease_store, lease)
                raise CrmAdoptionError(
                    "CRM_ADOPTION_PROSPECTIVE_STATE_INVALID"
                ) from exc
            except Exception:
                self._revoke_authority_lease(lease_store, lease)
                raise

    def create_portable_backup(
        self, request: CrmPortableBackupRequest
    ) -> CrmPortableBackup:
        self._secure_state_dir()
        with self.lock.acquire(_LOCK_KEY):
            state = self._read_state()
            if not self.state_file.exists():
                raise CrmAdoptionError("CRM_ADOPTION_BACKUP_EMPTY")
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)
            key = self._derive_backup_key(request.passphrase, salt)
            ciphertext = AESGCM(key).encrypt(
                nonce, _canonical_json(state.model_dump(mode="json")), _BACKUP_AAD
            )
            if len(ciphertext) > CRM_ADOPTION_MAX_BACKUP_BYTES:
                raise CrmAdoptionError("CRM_ADOPTION_BACKUP_SIZE_LIMIT")
            fingerprint = hashlib.sha256(ciphertext).hexdigest()
            return CrmPortableBackup(
                salt=_b64(salt),
                nonce=_b64(nonce),
                ciphertext=_b64(ciphertext),
                ciphertext_fingerprint_ref=(
                    f"ciphertext-fingerprint-ref:sha256:{fingerprint}"
                ),
                created_at=_utc_now(),
            )

    def preview_restore(
        self, request: CrmPortableRestoreRequest
    ) -> CrmPortableRestorePreview:
        restored = self._open_portable_backup(request)
        current_state_ref = self._current_state_ref()
        preview_ref = _hash_ref(
            "restore-preview-ref:crm-adoption",
            {
                "current_state_ref": current_state_ref,
                "backup_fingerprint_ref": request.backup.ciphertext_fingerprint_ref,
                "backup_revision": restored.revision,
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:crm-adoption-restore", {"preview_ref": preview_ref}
        )
        return CrmPortableRestorePreview(
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            current_state_ref=current_state_ref,
            backup_revision=restored.revision,
            record_count=len(restored.records),
            counts=self._counts(restored.records),
        )

    def commit_restore(
        self,
        *,
        request: CrmPortableRestoreCommitRequest,
        idempotency_ref: str,
        confirmed: bool,
    ) -> CrmAdoptionMutationReceipt:
        _private_ref(idempotency_ref)
        if not confirmed:
            raise CrmAdoptionError("CRM_ADOPTION_OPERATOR_CONFIRMATION_REQUIRED")
        self._secure_state_dir()
        with self.lock.acquire(_LOCK_KEY):
            restored = self._open_portable_backup(request)
            try:
                current = self._read_state()
            except CrmAdoptionError:
                current = CrmAdoptionState()
            fingerprint = _hash_ref(
                "payload-fingerprint-ref:crm-adoption-restore",
                {
                    "backup": request.backup.ciphertext_fingerprint_ref,
                    "preview_ref": request.preview_ref,
                },
            )
            prior = next(
                (
                    item
                    for item in current.receipts
                    if item.idempotency_ref == idempotency_ref
                ),
                None,
            )
            if prior is not None:
                if (
                    prior.payload_fingerprint_ref != fingerprint
                    or prior.preview_ref != request.preview_ref
                    or prior.approval_ref != request.approval_ref
                ):
                    raise CrmAdoptionConflict("CRM_ADOPTION_IDEMPOTENCY_CONFLICT")
                return prior.model_copy(update={"replayed": True})
            preview = self.preview_restore(request)
            if (
                request.preview_ref != preview.preview_ref
                or request.approval_ref != preview.approval_ref
            ):
                raise CrmAdoptionError("CRM_ADOPTION_EXACT_APPROVAL_REQUIRED")
            if any(item.idempotency_ref == idempotency_ref for item in restored.receipts):
                raise CrmAdoptionConflict("CRM_ADOPTION_IDEMPOTENCY_CONFLICT")
            approval_validation_ref = self._capture_exact_approval(
                action="restore_backup",
                preview_ref=request.preview_ref,
                approval_ref=request.approval_ref,
                payload_fingerprint_ref=fingerprint,
                expected_revision=current.revision,
                idempotency_ref=idempotency_ref,
            )
            lease_store, lease, authority_decision_ref = (
                self._authorize_exact_local_write(
                    action="restore_backup",
                    preview_ref=request.preview_ref,
                    approval_ref=request.approval_ref,
                    payload_fingerprint_ref=fingerprint,
                    expected_revision=current.revision,
                    idempotency_ref=idempotency_ref,
                )
            )
            after_revision = max(current.revision, restored.revision) + 1
            undo_stack = [
                *restored.undo_stack,
                *([current.snapshot()] if self.state_file.exists() else []),
            ][-CRM_ADOPTION_MAX_UNDO:]
            receipt = CrmAdoptionMutationReceipt(
                receipt_ref=_hash_ref(
                    "receipt-ref:crm-adoption-restore",
                    {"idempotency_ref": idempotency_ref, "revision": after_revision},
                ),
                action="restore_backup",
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=fingerprint,
                preview_ref=request.preview_ref,
                approval_ref=request.approval_ref,
                approval_validation_ref=approval_validation_ref,
                authority_lease_ref=lease.lease_ref,
                authority_decision_ref=authority_decision_ref,
                before_revision=current.revision,
                after_revision=after_revision,
                rollback_ref=_hash_ref(
                    "rollback-ref:crm-adoption",
                    {"after_revision": after_revision, "action": "undo"},
                ),
                safe_summary="One encrypted CRM backup was restored locally after exact confirmation.",
            )
            try:
                next_state = CrmAdoptionState.model_validate(
                    {
                        **restored.model_dump(mode="python"),
                        "revision": after_revision,
                        "undo_stack": undo_stack,
                        "receipts": [
                            *restored.receipts[-(CRM_ADOPTION_MAX_RECEIPTS - 1) :],
                            receipt,
                        ],
                    }
                )
                self._append_audit(receipt)
                self._write_state(next_state)
                return receipt
            except ValueError as exc:
                self._revoke_authority_lease(lease_store, lease)
                raise CrmAdoptionError(
                    "CRM_ADOPTION_PROSPECTIVE_STATE_INVALID"
                ) from exc
            except Exception:
                self._revoke_authority_lease(lease_store, lease)
                raise

    def _apply_mutation(
        self,
        state: CrmAdoptionState,
        request: CrmAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> tuple[CrmAdoptionState, str | None]:
        if request.expected_revision != state.revision:
            raise CrmAdoptionConflict("CRM_ADOPTION_STALE_REVISION")
        if request.action == "undo":
            if not state.undo_stack:
                raise CrmAdoptionConflict("CRM_ADOPTION_UNDO_EMPTY")
            snapshot = state.undo_stack[-1]
            return (
                CrmAdoptionState(
                    **snapshot.model_dump(mode="python"),
                    revision=state.revision + 1,
                    undo_stack=state.undo_stack[:-1],
                    receipts=state.receipts,
                ),
                None,
            )
        records = list(state.records)
        target_ref: str | None = request.target_ref
        if request.action == "create":
            assert request.record is not None
            target_ref = _hash_ref(
                f"{request.record.record_kind}-ref:crm-private",
                {"idempotency_ref": idempotency_ref, "record": request.record.model_dump(mode="json")},
            )
            if any(item.record_ref == target_ref for item in records):
                raise CrmAdoptionConflict("CRM_ADOPTION_RECORD_ALREADY_EXISTS")
            now = _utc_now()
            records.append(
                CrmAdoptionRecord(
                    record_ref=target_ref,
                    created_at=now,
                    updated_at=now,
                    **request.record.model_dump(mode="python"),
                )
            )
        elif request.action == "update":
            assert request.target_ref is not None and request.patch is not None
            index, current = self._record_index(records, request.target_ref)
            updates = request.patch.model_dump(
                mode="python", exclude_unset=True, exclude={"clear_fields"}
            )
            updates.update({field: None for field in request.patch.clear_fields})
            updates.update({"version": current.version + 1, "updated_at": _utc_now()})
            records[index] = CrmAdoptionRecord.model_validate(
                {**current.model_dump(mode="python"), **updates}
            )
        elif request.action in {"archive", "restore"}:
            assert request.target_ref is not None
            index, current = self._record_index(records, request.target_ref)
            expected_archived = request.action == "archive"
            if current.archived == expected_archived:
                raise CrmAdoptionConflict(
                    "CRM_ADOPTION_RECORD_ALREADY_ARCHIVED"
                    if expected_archived
                    else "CRM_ADOPTION_RECORD_NOT_ARCHIVED"
                )
            records[index] = CrmAdoptionRecord.model_validate(
                {
                    **current.model_dump(mode="python"),
                    "archived": expected_archived,
                    "version": current.version + 1,
                    "updated_at": _utc_now(),
                }
            )
        else:
            rows = self._parse_import(str(request.csv_text))
            existing_keys = self._identity_keys(records)
            for index, draft in enumerate(rows):
                keys = self._draft_identity_keys(draft)
                if keys & existing_keys:
                    continue
                record_ref = _hash_ref(
                    "person-ref:crm-private-import",
                    {"idempotency_ref": idempotency_ref, "row": index},
                )
                now = _utc_now()
                records.append(
                    CrmAdoptionRecord(
                        record_ref=record_ref,
                        created_at=now,
                        updated_at=now,
                        **draft.model_dump(mode="python"),
                    )
                )
                existing_keys.update(keys)
            target_ref = _hash_ref(
                "import-ref:crm-private", {"idempotency_ref": idempotency_ref}
            )
        next_state = CrmAdoptionState(
            workspace_name=state.workspace_name,
            workspace_preset=state.workspace_preset,
            records=records,
            revision=state.revision + 1,
            undo_stack=[
                *state.undo_stack[-(CRM_ADOPTION_MAX_UNDO - 1) :],
                state.snapshot(),
            ],
            receipts=state.receipts,
        )
        return next_state, target_ref

    def _read_state(self) -> CrmAdoptionState:
        if not self.state_file.exists():
            return CrmAdoptionState()
        if self.state_file.is_symlink() or not self.state_file.is_file():
            raise CrmAdoptionError("CRM_ADOPTION_STATE_UNSAFE")
        if self.state_file.stat().st_size > CRM_ADOPTION_MAX_STATE_BYTES:
            raise CrmAdoptionError("CRM_ADOPTION_STATE_SIZE_LIMIT")
        payload = self.state_file.read_bytes()
        if len(payload) <= len(_STATE_MAGIC) + 28 or not payload.startswith(_STATE_MAGIC):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_UNREADABLE")
        key = self._read_key()
        nonce = payload[len(_STATE_MAGIC) : len(_STATE_MAGIC) + 12]
        try:
            plaintext = AESGCM(key).decrypt(
                nonce, payload[len(_STATE_MAGIC) + 12 :], _STATE_AAD
            )
            decoded = json.loads(plaintext)
            return CrmAdoptionState.model_validate(decoded)
        except (InvalidTag, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise CrmAdoptionError("CRM_ADOPTION_STATE_UNREADABLE") from exc

    def _write_state(self, state: CrmAdoptionState) -> None:
        key = self._read_key(create=True)
        nonce = secrets.token_bytes(12)
        plaintext = _canonical_json(state.model_dump(mode="json"))
        if (
            len(plaintext) + 16 > CRM_ADOPTION_MAX_BACKUP_BYTES
            or len(_STATE_MAGIC) + 12 + len(plaintext) + 16
            > CRM_ADOPTION_MAX_STATE_BYTES
        ):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_SIZE_LIMIT")
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, _STATE_AAD)
        self._atomic_write(self.state_file, _STATE_MAGIC + nonce + ciphertext)

    def _read_key(self, *, create: bool = False) -> bytes:
        if self.key_file.exists():
            if self.key_file.is_symlink() or not self.key_file.is_file():
                raise CrmAdoptionError("CRM_ADOPTION_KEY_UNSAFE")
            key = self.key_file.read_bytes()
            if len(key) != 32:
                raise CrmAdoptionError("CRM_ADOPTION_KEY_UNAVAILABLE")
            return key
        if not create:
            raise CrmAdoptionError("CRM_ADOPTION_KEY_UNAVAILABLE")
        return self._create_key()

    def _create_key(self) -> bytes:
        """Create the state key without ever replacing an existing key inode."""
        key = AESGCM.generate_key(bit_length=256)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.key_file.name}.", suffix=".tmp", dir=self.state_dir
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            view = memoryview(key)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise CrmAdoptionError("CRM_ADOPTION_KEY_WRITE_FAILED")
                view = view[written:]
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            try:
                os.link(temporary, self.key_file, follow_symlinks=False)
            except FileExistsError:
                return self._read_key(create=False)
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return key
        except CrmAdoptionError:
            raise
        except OSError as exc:
            raise CrmAdoptionError("CRM_ADOPTION_KEY_WRITE_FAILED") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _append_audit(self, receipt: CrmAdoptionMutationReceipt) -> None:
        existing = b""
        if self.audit_file.exists():
            if self.audit_file.is_symlink() or not self.audit_file.is_file():
                raise CrmAdoptionError("CRM_ADOPTION_AUDIT_UNSAFE")
            if self.audit_file.stat().st_size > CRM_ADOPTION_MAX_AUDIT_BYTES:
                raise CrmAdoptionError("CRM_ADOPTION_AUDIT_CAPACITY_EXHAUSTED")
            existing = self.audit_file.read_bytes()
        event_ref = _hash_ref(
            "event-ref:crm-adoption", {"receipt_ref": receipt.receipt_ref}
        )
        for line in existing.splitlines():
            try:
                if json.loads(line).get("event_ref") == event_ref:
                    return
            except (AttributeError, json.JSONDecodeError) as exc:
                raise CrmAdoptionError("CRM_ADOPTION_AUDIT_UNREADABLE") from exc
        event = _canonical_json(
            {
                "event_ref": event_ref,
                "receipt_ref": receipt.receipt_ref,
                "action_ref": f"action-ref:crm-adoption:{receipt.action}",
                "approval_validation_ref": receipt.approval_validation_ref,
                "authority_lease_ref": receipt.authority_lease_ref,
                "authority_decision_ref": receipt.authority_decision_ref,
                "after_revision": receipt.after_revision,
                "occurred_at": _utc_now().isoformat(),
                "private_values_included": False,
                "external_write_performed": False,
            }
        )
        if len(existing) + len(event) + 1 > CRM_ADOPTION_MAX_AUDIT_BYTES:
            raise CrmAdoptionError("CRM_ADOPTION_AUDIT_CAPACITY_EXHAUSTED")
        self._atomic_write(
            self.audit_file,
            existing + (b"" if not existing or existing.endswith(b"\n") else b"\n") + event + b"\n",
        )

    def _secure_state_dir(self) -> None:
        if not self.state_dir.is_absolute() or self.state_dir == Path(
            self.state_dir.anchor
        ):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_PATH_UNSAFE")
        if self.state_dir.exists() and (
            self.state_dir.is_symlink() or not self.state_dir.is_dir()
        ):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_PATH_UNSAFE")
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.state_dir, 0o700)

    def _atomic_write(self, path: Path, payload: bytes) -> None:
        if not path.parent.is_absolute() or path.parent == Path(path.anchor):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_PATH_UNSAFE")
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.parent.is_symlink() or (path.exists() and path.is_symlink()):
            raise CrmAdoptionError("CRM_ADOPTION_STATE_PATH_UNSAFE")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise CrmAdoptionError("CRM_ADOPTION_STATE_WRITE_FAILED")
                view = view[written:]
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, path)
            os.chmod(path, 0o600)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _open_portable_backup(
        self, request: CrmPortableRestoreRequest
    ) -> CrmAdoptionState:
        ciphertext = _decode_b64(
            request.backup.ciphertext, code="CRM_ADOPTION_BACKUP_INVALID"
        )
        if len(ciphertext) > CRM_ADOPTION_MAX_BACKUP_BYTES:
            raise CrmAdoptionError("CRM_ADOPTION_BACKUP_SIZE_LIMIT")
        fingerprint = hashlib.sha256(ciphertext).hexdigest()
        if request.backup.ciphertext_fingerprint_ref != (
            f"ciphertext-fingerprint-ref:sha256:{fingerprint}"
        ):
            raise CrmAdoptionError("CRM_ADOPTION_BACKUP_FINGERPRINT_INVALID")
        salt = _decode_b64(request.backup.salt, code="CRM_ADOPTION_BACKUP_INVALID")
        nonce = _decode_b64(request.backup.nonce, code="CRM_ADOPTION_BACKUP_INVALID")
        if len(salt) != 16 or len(nonce) != 12:
            raise CrmAdoptionError("CRM_ADOPTION_BACKUP_INVALID")
        try:
            plaintext = AESGCM(
                self._derive_backup_key(request.passphrase, salt)
            ).decrypt(nonce, ciphertext, _BACKUP_AAD)
            return CrmAdoptionState.model_validate_json(plaintext)
        except (InvalidTag, ValueError) as exc:
            raise CrmAdoptionError("CRM_ADOPTION_BACKUP_UNLOCK_FAILED") from exc

    @staticmethod
    def _derive_backup_key(passphrase: str, salt: bytes) -> bytes:
        return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
            passphrase.encode("utf-8")
        )

    def _current_state_ref(self) -> str:
        if not self.state_file.exists():
            return "state-ref:crm-adoption:empty"
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return "state-ref:crm-adoption:unsafe"
        if self.state_file.stat().st_size > CRM_ADOPTION_MAX_STATE_BYTES:
            return "state-ref:crm-adoption:oversize"
        return (
            "state-ref:crm-adoption:sha256:"
            f"{hashlib.sha256(self.state_file.read_bytes()).hexdigest()}"
        )

    @staticmethod
    def _mutation_fingerprint(request: CrmAdoptionMutationRequest) -> str:
        return _hash_ref(
            "payload-fingerprint-ref:crm-adoption",
            request.model_dump(mode="json"),
        )

    def _authorize_exact_local_write(
        self,
        *,
        action: str,
        preview_ref: str,
        approval_ref: str,
        payload_fingerprint_ref: str,
        expected_revision: int,
        idempotency_ref: str,
    ) -> tuple[AuthorityLeaseStore, AuthorityLease, str]:
        route_ref = (
            CRM_ADOPTION_BACKUP_ROUTE_REF
            if action == "restore_backup"
            else CRM_ADOPTION_ROUTE_REF
        )
        action_ref = f"action-ref:crm-adoption:{action}"
        revision_ref = f"revision-ref:crm-adoption:{expected_revision}"
        foundation_ref = _hash_ref(
            "foundation-contract-ref:crm-adoption",
            {"schema_version": CRM_ADOPTION_FOUNDATION_REF},
        )
        resource_refs = [
            CRM_ADOPTION_CONTRACT_REF,
            foundation_ref,
            preview_ref,
            approval_ref,
            payload_fingerprint_ref,
            idempotency_ref,
            action_ref,
            revision_ref,
        ]
        suffix = hashlib.sha256(payload_fingerprint_ref.encode("utf-8")).hexdigest()[:24]
        lease_request = AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            scope=AuthorityLeaseScope.session,
            requested_domains={
                AuthorityDomain.contacts: [AuthorityCapability.write],
            },
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=(
                        f"authority-constraint-ref:crm-adoption:resources:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resource_refs,
                    safe_summary=(
                        "Restrict one founder-private CRM write to its exact "
                        "preview, approval, revision, payload, and idempotency refs."
                    ),
                ),
                AuthorityConstraint(
                    constraint_ref=(
                        f"authority-constraint-ref:crm-adoption:budget:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Permit one exact local CRM state write.",
                ),
            ],
            constraints={
                "exact_lane_ref": CRM_ADOPTION_AUTHORITY_LANE_REF,
                "exact_action_ref": action_ref,
                "exact_route_ref": route_ref,
                "exact_contract_ref": CRM_ADOPTION_CONTRACT_REF,
                "exact_foundation_ref": foundation_ref,
                "exact_preview_ref": preview_ref,
                "exact_approval_ref": approval_ref,
                "exact_payload_fingerprint_ref": payload_fingerprint_ref,
                "exact_idempotency_ref": idempotency_ref,
                "exact_revision_ref": revision_ref,
                "exact_safe_disable_ref": CRM_ADOPTION_SAFE_DISABLE_REF,
            },
            decision_reason_ref=(
                "decision-reason-ref:crm-adoption:operator-confirmed"
            ),
            duration_minutes=5,
            safe_summary="Issue one exact operator-confirmed local CRM write lease.",
        )
        lease_store = AuthorityLeaseStore(self.state_dir / "authority")
        lease_idempotency_ref = self._lease_idempotency_ref(
            lease_store,
            payload_fingerprint_ref=payload_fingerprint_ref,
            idempotency_ref=idempotency_ref,
        )
        _requirement, _grant, lease, receipt = (
            issue_authority_lease_with_backend_approval(
                lease_store,
                lease_request,
                idempotency_ref=lease_idempotency_ref,
                approved_by_actor_id="operator-ref:local-user",
            )
        )
        if (
            lease is None
            or lease.status == "revoked"
            or receipt.status not in {"issued", "replayed"}
        ):
            raise CrmAdoptionError("CRM_ADOPTION_EXACT_LEASE_ISSUANCE_DENIED")
        rollback_ref = _hash_ref(
            "rollback-ref:crm-adoption",
            {"payload_fingerprint_ref": payload_fingerprint_ref, "action": "undo"},
        )
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=action_ref,
                domain=AuthorityDomain.contacts,
                capability=AuthorityCapability.write,
                safe_summary="Evaluate authority for one exact local CRM state write.",
                resource_refs=resource_refs,
                route_ref=route_ref,
                lane_ref=CRM_ADOPTION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget,
                        value=1,
                    )
                ],
                rollback_ref=rollback_ref,
                safe_disable_ref=CRM_ADOPTION_SAFE_DISABLE_REF,
            ),
            [lease],
        )
        if decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            self._revoke_authority_lease(lease_store, lease)
            raise CrmAdoptionError("CRM_ADOPTION_EXACT_LEASE_AUTHORITY_DENIED")
        return lease_store, lease, decision.decision_ref

    @staticmethod
    def _lease_idempotency_ref(
        lease_store: AuthorityLeaseStore,
        *,
        payload_fingerprint_ref: str,
        idempotency_ref: str,
    ) -> str:
        leases = lease_store.list_leases()
        receipts = lease_store.list_receipts(limit=1_000_000)
        candidate = _hash_ref(
            "idempotency-ref:crm-adoption-lease",
            {
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "idempotency_ref": idempotency_ref,
            },
        )
        for retry_index in range(1, len(leases) + len(receipts) + 2):
            matching = next(
                (
                    lease
                    for lease in leases
                    if lease.constraints.get("idempotency_ref") == candidate
                ),
                None,
            )
            denied = any(
                receipt.operation == "issue"
                and receipt.idempotency_ref == candidate
                and receipt.status == "denied"
                for receipt in receipts
            )
            if matching is None and not denied:
                return candidate
            if matching is not None and matching.status != "revoked":
                return candidate
            candidate = _hash_ref(
                "idempotency-ref:crm-adoption-lease-retry",
                {
                    "payload_fingerprint_ref": payload_fingerprint_ref,
                    "retry_index": retry_index,
                },
            )
        raise CrmAdoptionError("CRM_ADOPTION_EXACT_LEASE_RETRY_EXHAUSTED")

    @staticmethod
    def _revoke_authority_lease(
        lease_store: AuthorityLeaseStore,
        lease: AuthorityLease,
    ) -> None:
        if lease.status == "revoked":
            return
        _revoked, receipt = lease_store.revoke_lease(
            AuthorityLeaseRevokeRequest(
                lease_ref=lease.lease_ref,
                decision_reason_ref=(
                    "decision-reason-ref:crm-adoption:pre-commit-failure"
                ),
                safe_summary=(
                    "Revoke the exact CRM lease after the local write failed "
                    "before durable state commit."
                ),
            ),
            idempotency_ref=_hash_ref(
                "idempotency-ref:crm-adoption-lease-revoke",
                {"lease_ref": lease.lease_ref},
            ),
        )
        if receipt.status not in {"revoked", "replayed"}:
            raise CrmAdoptionError("CRM_ADOPTION_EXACT_LEASE_REVOCATION_FAILED")

    @staticmethod
    def _capture_exact_approval(
        *,
        action: str,
        preview_ref: str,
        approval_ref: str,
        payload_fingerprint_ref: str,
        expected_revision: int,
        idempotency_ref: str,
    ) -> str:
        resource_refs = [
            CRM_ADOPTION_CONTRACT_REF,
            CRM_ADOPTION_FOUNDATION_REF,
            preview_ref,
            payload_fingerprint_ref,
            idempotency_ref,
            f"action-ref:crm-adoption:{action}",
            f"revision-ref:crm-adoption:{expected_revision}",
        ]
        approval_request = ApprovalRequest(
            approval_request_id=_hash_ref(
                "approval-request-ref:crm-adoption",
                {"approval_ref": approval_ref, "idempotency_ref": idempotency_ref},
            ),
            run_id=_hash_ref(
                "run-ref:crm-adoption",
                {"preview_ref": preview_ref, "idempotency_ref": idempotency_ref},
            ),
            subject_type=ApprovalSubjectType.external_action,
            subject_id=preview_ref,
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="operator-ref:local-user",
                authority_source=AuthoritySource.manual_operator_action,
            ),
            requested_action=f"crm_adoption:{action}",
            purpose=(
                "Approve one exact founder-private local CRM state change after "
                "the operator reviewed its bound preview."
            ),
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.user_private,
                source="source-ref:crm-adoption-local-workspace",
                requires_redaction=True,
            ),
            resource_refs=resource_refs,
            event_ref=_hash_ref(
                "event-ref:crm-adoption-approval",
                {"preview_ref": preview_ref, "idempotency_ref": idempotency_ref},
            ),
            trace_id=preview_ref,
            expires_at=_utc_now() + timedelta(minutes=5),
            metadata={
                "exact_preview_required": True,
                "local_operator_confirmation_required": True,
            },
        )
        authority = LocalApprovalAuthority()
        with authority.hold_validation_lock():
            stored = authority.create_request(approval_request)
            authority.grant(
                stored.approval_request_id,
                approved_by_actor_id="operator-ref:local-user",
                approval_ref=approval_ref,
                expires_at=stored.expires_at,
            )
            decision = authority.validate_for_request(stored, approval_ref)
            if not decision.allowed or decision.matched_grant_ref != approval_ref:
                raise CrmAdoptionError("CRM_ADOPTION_EXACT_APPROVAL_REQUIRED")
        return decision.decision_id

    @staticmethod
    def _find_record(state: CrmAdoptionState, target_ref: str) -> CrmAdoptionRecord:
        return CrmAdoptionStore._record_index(state.records, target_ref)[1]

    @staticmethod
    def _record_index(
        records: list[CrmAdoptionRecord], target_ref: str
    ) -> tuple[int, CrmAdoptionRecord]:
        for index, item in enumerate(records):
            if item.record_ref == target_ref:
                return index, item
        raise CrmAdoptionConflict("CRM_ADOPTION_RECORD_NOT_FOUND")

    @staticmethod
    def _validate_related_refs(
        state: CrmAdoptionState,
        related_refs: list[str],
        *,
        target_ref: str | None = None,
    ) -> None:
        known = {item.record_ref for item in state.records}
        if any(item not in known or item == target_ref for item in related_refs):
            raise CrmAdoptionConflict("CRM_ADOPTION_RELATED_RECORD_NOT_FOUND")

    @staticmethod
    def _parse_import(csv_text: str) -> list[CrmAdoptionRecordDraft]:
        if len(csv_text.encode("utf-8")) > 2_000_000:
            raise CrmAdoptionError("CRM_ADOPTION_IMPORT_SIZE_LIMIT")
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            if reader.fieldnames is None:
                raise CrmAdoptionError("CRM_ADOPTION_IMPORT_HEADER_REQUIRED")
            normalized = {
                name.strip().casefold().replace(" ", "_"): name
                for name in reader.fieldnames
                if name is not None
            }
            name_field = next(
                (normalized[item] for item in ("name", "display_name", "full_name") if item in normalized),
                None,
            )
            if name_field is None:
                raise CrmAdoptionError("CRM_ADOPTION_IMPORT_NAME_COLUMN_REQUIRED")
            rows: list[CrmAdoptionRecordDraft] = []
            for index, row in enumerate(reader):
                if index >= CRM_ADOPTION_MAX_IMPORT_ROWS:
                    raise CrmAdoptionError("CRM_ADOPTION_IMPORT_ROW_LIMIT")
                display_name = str(row.get(name_field) or "").strip()
                if not display_name:
                    raise CrmAdoptionError("CRM_ADOPTION_IMPORT_NAME_REQUIRED")
                def value(*names: str) -> str | None:
                    for candidate in names:
                        source = normalized.get(candidate)
                        if source is not None:
                            result = str(row.get(source) or "").strip()
                            if result:
                                return result
                    return None
                tags_value = value("tags", "tag")
                rows.append(
                    CrmAdoptionRecordDraft(
                        record_kind="person",
                        display_name=display_name,
                        email=value("email", "email_address"),
                        phone=value("phone", "phone_number"),
                        subtitle=value("organization", "company"),
                        notes=value("notes", "note"),
                        tags=(
                            [item.strip() for item in tags_value.split(",") if item.strip()]
                            if tags_value
                            else []
                        ),
                        status="imported",
                    )
                )
            if not rows:
                raise CrmAdoptionError("CRM_ADOPTION_IMPORT_EMPTY")
            return rows
        except (csv.Error, ValueError) as exc:
            raise CrmAdoptionError("CRM_ADOPTION_IMPORT_INVALID") from exc

    @staticmethod
    def _draft_identity_keys(draft: CrmAdoptionRecordDraft) -> set[str]:
        keys = {f"name:{draft.display_name.casefold()}"}
        if draft.email:
            keys.add(f"email:{draft.email.casefold()}")
        if draft.phone:
            keys.add(f"phone:{''.join(ch for ch in draft.phone if ch.isdigit())}")
        return keys

    @classmethod
    def _identity_keys(cls, records: list[CrmAdoptionRecord]) -> set[str]:
        keys: set[str] = set()
        for item in records:
            if item.record_kind != "person" or item.archived:
                continue
            keys.update(
                cls._draft_identity_keys(
                    CrmAdoptionRecordDraft(
                        **item.model_dump(
                            mode="python",
                            include=set(CrmAdoptionRecordDraft.model_fields),
                        )
                    )
                )
            )
        return keys

    @classmethod
    def _import_duplicate_count(
        cls, state: CrmAdoptionState, rows: list[CrmAdoptionRecordDraft]
    ) -> int:
        known = cls._identity_keys(state.records)
        duplicates = 0
        for row in rows:
            keys = cls._draft_identity_keys(row)
            if keys & known:
                duplicates += 1
            else:
                known.update(keys)
        return duplicates

    @staticmethod
    def _counts(records: list[CrmAdoptionRecord]) -> dict[str, int]:
        counts = {kind: 0 for kind in CrmAdoptionRecordKind.__args__}
        counts["archived"] = 0
        for item in records:
            counts[item.record_kind] += 1
            if item.archived:
                counts["archived"] += 1
        return counts

    @classmethod
    def _view(
        cls,
        state: CrmAdoptionState,
        *,
        records: list[CrmAdoptionRecord],
        storage_state: Literal["empty", "ready", "locked", "recovery_required"],
        next_safe_action: str,
    ) -> CrmAdoptionWorkspaceView:
        return CrmAdoptionWorkspaceView(
            storage_state=storage_state,
            revision=state.revision,
            workspace_name=state.workspace_name,
            workspace_preset=state.workspace_preset,
            records=records,
            counts=cls._counts(state.records),
            can_undo=bool(state.undo_stack),
            next_safe_action=next_safe_action,
        )


__all__ = [
    "CRM_ADOPTION_BACKUP_ROUTE_REF",
    "CRM_ADOPTION_CONTRACT_REF",
    "CRM_ADOPTION_ROUTE_REF",
    "CrmAdoptionConflict",
    "CrmAdoptionCommitRequest",
    "CrmAdoptionError",
    "CrmAdoptionMutationPreview",
    "CrmAdoptionMutationReceipt",
    "CrmAdoptionMutationRequest",
    "CrmAdoptionRecord",
    "CrmAdoptionRecordDraft",
    "CrmAdoptionRecordKind",
    "CrmAdoptionRecordPatch",
    "CrmAdoptionStore",
    "CrmAdoptionWorkspaceView",
    "CrmPortableBackup",
    "CrmPortableBackupRequest",
    "CrmPortableRestoreCommitRequest",
    "CrmPortableRestorePreview",
    "CrmPortableRestoreRequest",
]
