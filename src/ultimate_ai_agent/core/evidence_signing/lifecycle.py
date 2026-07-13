from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.evidence_signing.portable import (
    PortableEvidenceKeyStatus,
    PortableEvidencePublicKeyRecord,
    build_public_key_bundle,
    ed25519_public_key_fingerprint_ref,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.time import utc_now


PORTABLE_EVIDENCE_KEY_LEDGER_FILE = "portable_evidence_key_lifecycle.jsonl"
PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES = 2 * 1024 * 1024
PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES = 1_000
PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH = 520
PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES = 8 * 1024


class PortableEvidenceKeyLifecycleError(RuntimeError):
    pass


class PortableEvidenceKeyLifecycleConflictError(PortableEvidenceKeyLifecycleError):
    pass


class PortableEvidenceKeyLifecycleCorruptionError(PortableEvidenceKeyLifecycleError):
    pass


class PortableEvidenceKeyLifecycleAction(str, Enum):
    created = "created"
    rotated = "rotated"
    retired_key_delete_completed = "retired_key_delete_completed"
    revoked = "revoked"
    revocation_delete_completed = "revocation_delete_completed"
    marked_lost = "marked_lost"
    lost_key_delete_completed = "lost_key_delete_completed"


class _LifecycleModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    def model_copy(
        self,
        *,
        update: dict[str, Any] | None = None,
        deep: bool = False,
    ) -> "_LifecycleModel":
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class PortableEvidenceKeyLifecycleEntry(_LifecycleModel):
    schema_version: Literal["uaa-portable-evidence-key-lifecycle-entry.v1"] = (
        "uaa-portable-evidence-key-lifecycle-entry.v1"
    )
    sequence: StrictInt = Field(..., ge=1, le=PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES)
    action: PortableEvidenceKeyLifecycleAction
    request_ref: str = Field(..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH)
    request_fingerprint_ref: str = Field(
        ..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH
    )
    receipt_ref: str = Field(..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH)
    key_ref: str = Field(..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH)
    key_version_ref: str = Field(
        ..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH
    )
    generation: StrictInt = Field(
        ..., ge=1, le=PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES
    )
    public_key_base64url: str = Field(..., min_length=43, max_length=43)
    public_key_fingerprint_ref: str = Field(
        ..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH
    )
    predecessor_key_version_ref: str | None = Field(
        default=None,
        max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH,
    )
    revocation_ref: str | None = Field(
        default=None,
        max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH,
    )
    checked_at: datetime = Field(default_factory=utc_now)
    previous_entry_hash_ref: str | None = Field(
        default=None,
        max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH,
    )
    entry_hash_ref: str = Field(
        ..., max_length=PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH
    )
    raw_content_persisted: Literal[False] = False
    private_key_persisted: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_entry(self) -> "PortableEvidenceKeyLifecycleEntry":
        _validate_refs(self.model_dump(mode="python"))
        if self.public_key_fingerprint_ref != ed25519_public_key_fingerprint_ref(
            _decode_public_key(self.public_key_base64url)
        ):
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_FINGERPRINT_INVALID")
        if self.generation == 1 and self.predecessor_key_version_ref is not None:
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_FIRST_PREDECESSOR_DENIED")
        if self.generation > 1 and self.predecessor_key_version_ref is None:
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_PREDECESSOR_REQUIRED")
        if self.action in {
            PortableEvidenceKeyLifecycleAction.revoked.value,
            PortableEvidenceKeyLifecycleAction.revocation_delete_completed.value,
        }:
            if self.revocation_ref is None:
                raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_REVOCATION_REQUIRED")
        elif self.revocation_ref is not None:
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_REVOCATION_DENIED")
        if self.entry_hash_ref != _entry_hash(self):
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_HASH_INVALID")
        return self


class PortableEvidenceKeyLifecycleInspection(_LifecycleModel):
    schema_version: Literal["uaa-portable-evidence-key-lifecycle-inspection.v1"] = (
        "uaa-portable-evidence-key-lifecycle-inspection.v1"
    )
    status: Literal[
        "not_configured",
        "active",
        "active_rotation_delete_pending",
        "retired",
        "revoked_deletion_pending",
        "revoked",
        "lost_deletion_pending",
        "lost",
    ]
    active_key_ref: str | None = None
    active_key_version_ref: str | None = None
    active_public_key_fingerprint_ref: str | None = None
    generation_count: StrictInt = Field(
        ..., ge=0, le=PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES
    )
    lifecycle_terminal_entry_hash_ref: str | None = None
    reason_refs: tuple[str, ...] = Field(default=(), max_length=16)
    private_key_included: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_inspection(self) -> "PortableEvidenceKeyLifecycleInspection":
        _validate_refs(self.model_dump(mode="python"))
        return self


class PortableEvidenceKeyLifecycleLedger:
    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / PORTABLE_EVIDENCE_KEY_LEDGER_FILE
        self._locks = FileSingleWriterLockManager(self.state_dir / ".locks")

    def operation_lock(self):  # type: ignore[no-untyped-def]
        self._ensure_state_dir()
        return self._locks.acquire("portable-evidence-key-lifecycle")

    @property
    def store_ref(self) -> str:
        digest = hashlib.sha256(
            os.fspath(self.state_dir.absolute()).encode("utf-8")
        ).hexdigest()
        return f"lifecycle-store-ref:portable-evidence:sha256:{digest}"

    def inspect(self) -> PortableEvidenceKeyLifecycleInspection:
        entries = self.load_entries()
        records = _project_records(entries)
        active = next((record for record in records if record.status == "active"), None)
        latest = records[-1] if records else None
        last_action = entries[-1].action if entries else None
        if last_action == "rotated":
            status = "active_rotation_delete_pending"
            reasons = (
                "reason-ref:portable-evidence-signing:retired-key-delete-pending",
            )
        elif last_action == "revoked":
            status = "revoked_deletion_pending"
            reasons = (
                "reason-ref:portable-evidence-signing:key-revoked-deletion-pending",
            )
        elif last_action == "marked_lost":
            status = "lost_deletion_pending"
            reasons = (
                "reason-ref:portable-evidence-signing:key-lost-deletion-pending",
            )
        elif active is not None:
            status = "active"
            reasons = ("reason-ref:portable-evidence-signing:key-active",)
        elif latest is None:
            status = "not_configured"
            reasons = ("reason-ref:portable-evidence-signing:key-not-configured",)
        else:
            status = str(latest.status)
            reasons = (f"reason-ref:portable-evidence-signing:key-{status}",)
        return PortableEvidenceKeyLifecycleInspection(
            status=status,
            active_key_ref=active.key_ref if active else None,
            active_key_version_ref=active.key_version_ref if active else None,
            active_public_key_fingerprint_ref=(
                active.public_key_fingerprint_ref if active else None
            ),
            generation_count=len(records),
            lifecycle_terminal_entry_hash_ref=(
                entries[-1].entry_hash_ref if entries else None
            ),
            reason_refs=reasons,
        )

    def public_key_bundle(
        self,
        *,
        issuer_ref: str,
        previous_public_key_bundle_ref: str | None = None,
    ):  # type: ignore[no-untyped-def]
        entries = self.load_entries()
        if not entries:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_NOT_CONFIGURED"
            )
        return build_public_key_bundle(
            _project_records(entries),
            issuer_ref=issuer_ref,
            lifecycle_terminal_entry_hash_ref=entries[-1].entry_hash_ref,
            previous_public_key_bundle_ref=previous_public_key_bundle_ref,
        )

    def active_record(self) -> PortableEvidencePublicKeyRecord:
        active = [
            record
            for record in _project_records(self.load_entries())
            if record.status == "active"
        ]
        if len(active) != 1:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_ACTIVE_KEY_REQUIRED"
            )
        return active[0]

    def latest_record(self) -> PortableEvidencePublicKeyRecord:
        records = _project_records(self.load_entries())
        if not records:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_NOT_CONFIGURED"
            )
        return records[-1]

    def pending_key_deletion(
        self,
    ) -> tuple[PortableEvidencePublicKeyRecord, str, str | None]:
        entries = self.load_entries()
        records = _project_records(entries)
        if entries and entries[-1].action == "rotated" and len(records) >= 2:
            return records[-2], "rotation", None
        if entries and entries[-1].action == "revoked" and records:
            return records[-1], "revocation", records[-1].revocation_ref
        if entries and entries[-1].action == "marked_lost" and records:
            return records[-1], "lost", None
        raise PortableEvidenceKeyLifecycleConflictError(
            "PORTABLE_EVIDENCE_KEY_DELETE_NOT_PENDING"
        )

    def append_created(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        key_ref: str,
        key_version_ref: str,
        public_key_base64url: str,
        public_key_fingerprint_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        return self._append(
            action=PortableEvidenceKeyLifecycleAction.created,
            request_ref=request_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            receipt_ref=receipt_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            generation=1,
            public_key_base64url=public_key_base64url,
            public_key_fingerprint_ref=public_key_fingerprint_ref,
            checked_at=checked_at,
        )

    def append_rotated(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        key_ref: str,
        key_version_ref: str,
        public_key_base64url: str,
        public_key_fingerprint_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            entries = self.load_entries()
            if entries and entries[-1].action not in {
                "created",
                "retired_key_delete_completed",
            }:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_KEY_LIFECYCLE_NOT_SETTLED"
                )
            active = [
                record
                for record in _project_records(entries)
                if record.status == "active"
            ]
            if len(active) != 1:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_ACTIVE_KEY_REQUIRED"
                )
            return self._append_locked(
                entries=entries,
                action=PortableEvidenceKeyLifecycleAction.rotated,
                request_ref=request_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                generation=active[0].generation + 1,
                public_key_base64url=public_key_base64url,
                public_key_fingerprint_ref=public_key_fingerprint_ref,
                predecessor_key_version_ref=active[0].key_version_ref,
                checked_at=checked_at,
            )

    def append_revoked(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        revocation_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        return self._append_terminal(
            action=PortableEvidenceKeyLifecycleAction.revoked,
            request_ref=request_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            receipt_ref=receipt_ref,
            revocation_ref=revocation_ref,
            checked_at=checked_at,
        )

    def append_marked_lost(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        return self._append_terminal(
            action=PortableEvidenceKeyLifecycleAction.marked_lost,
            request_ref=request_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            receipt_ref=receipt_ref,
            checked_at=checked_at,
        )

    def append_revocation_delete_completed(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        revocation_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            entries = self.load_entries()
            existing = next(
                (item for item in entries if item.request_ref == request_ref),
                None,
            )
            if existing is not None:
                if existing.request_fingerprint_ref != request_fingerprint_ref:
                    raise PortableEvidenceKeyLifecycleConflictError(
                        "PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT"
                    )
                return existing
            if not entries or entries[-1].action != "revoked":
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_KEY_REVOCATION_DELETE_NOT_PENDING"
                )
            current = _project_records(entries)[-1]
            if current.revocation_ref != revocation_ref:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_KEY_REVOCATION_REF_MISMATCH"
                )
            return self._append_locked(
                entries=entries,
                action=PortableEvidenceKeyLifecycleAction.revocation_delete_completed,
                request_ref=request_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=current.key_ref,
                key_version_ref=current.key_version_ref,
                generation=current.generation,
                public_key_base64url=current.public_key_base64url,
                public_key_fingerprint_ref=current.public_key_fingerprint_ref,
                predecessor_key_version_ref=current.predecessor_key_version_ref,
                revocation_ref=revocation_ref,
                checked_at=checked_at,
            )

    def append_retired_key_delete_completed(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        retired_key_version_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            entries = self.load_entries()
            existing = next(
                (item for item in entries if item.request_ref == request_ref),
                None,
            )
            if existing is not None:
                if existing.request_fingerprint_ref != request_fingerprint_ref:
                    raise PortableEvidenceKeyLifecycleConflictError(
                        "PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT"
                    )
                return existing
            if not entries or entries[-1].action != "rotated":
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_RETIRED_KEY_DELETE_NOT_PENDING"
                )
            retired = _project_records(entries)[-2]
            if retired.key_version_ref != retired_key_version_ref:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_RETIRED_KEY_VERSION_MISMATCH"
                )
            return self._append_locked(
                entries=entries,
                action=PortableEvidenceKeyLifecycleAction.retired_key_delete_completed,
                request_ref=request_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=retired.key_ref,
                key_version_ref=retired.key_version_ref,
                generation=retired.generation,
                public_key_base64url=retired.public_key_base64url,
                public_key_fingerprint_ref=retired.public_key_fingerprint_ref,
                predecessor_key_version_ref=retired.predecessor_key_version_ref,
                checked_at=checked_at,
            )

    def append_lost_key_delete_completed(
        self,
        *,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            entries = self.load_entries()
            existing = next(
                (item for item in entries if item.request_ref == request_ref),
                None,
            )
            if existing is not None:
                if existing.request_fingerprint_ref != request_fingerprint_ref:
                    raise PortableEvidenceKeyLifecycleConflictError(
                        "PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT"
                    )
                return existing
            if not entries or entries[-1].action != "marked_lost":
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_LOST_KEY_DELETE_NOT_PENDING"
                )
            current = _project_records(entries)[-1]
            return self._append_locked(
                entries=entries,
                action=PortableEvidenceKeyLifecycleAction.lost_key_delete_completed,
                request_ref=request_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=current.key_ref,
                key_version_ref=current.key_version_ref,
                generation=current.generation,
                public_key_base64url=current.public_key_base64url,
                public_key_fingerprint_ref=current.public_key_fingerprint_ref,
                predecessor_key_version_ref=current.predecessor_key_version_ref,
                checked_at=checked_at,
            )

    def load_entries(self) -> tuple[PortableEvidenceKeyLifecycleEntry, ...]:
        if not self._validate_existing_state_dir():
            return ()
        try:
            os.lstat(self.path)
        except FileNotFoundError:
            return ()
        descriptor = _open_regular(self.path, os.O_RDONLY)
        try:
            raw = _read_bounded(descriptor)
        finally:
            os.close(descriptor)
        if not raw:
            return ()
        if not raw.endswith(b"\n"):
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_UNTERMINATED_RECORD"
            )
        lines = raw.decode("utf-8").splitlines()
        if len(lines) > PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES:
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_LIMIT_EXCEEDED"
            )
        try:
            entries = tuple(
                PortableEvidenceKeyLifecycleEntry.model_validate_json(line)
                for line in lines
            )
        except (UnicodeDecodeError, ValueError) as exc:
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_INVALID"
            ) from exc
        _validate_chain(entries)
        return entries

    def require_entry_capacity(self, *, required_entries: int) -> None:
        """Fail before backend mutation unless all transition entry slots exist."""
        with self.operation_lock():
            self._require_entry_capacity_locked(required_entries=required_entries)

    def _require_entry_capacity_locked(self, *, required_entries: int) -> None:
        if required_entries not in {1, 2, 3, 4}:
            raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_CAPACITY_REQUEST_INVALID")
        entries = self.load_entries()
        if (
            len(entries) + required_entries
            > PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES
        ):
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_FULL"
            )
        current_size = 0
        if entries:
            descriptor = _open_regular(self.path, os.O_RDONLY)
            try:
                current_size = os.fstat(descriptor).st_size
            finally:
                os.close(descriptor)
        if (
            current_size
            + required_entries * PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES
            > PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES
        ):
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_SIZE_LIMIT_EXCEEDED"
            )

    def _append_terminal(
        self,
        *,
        action: PortableEvidenceKeyLifecycleAction,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        revocation_ref: str | None = None,
        checked_at: datetime | None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            entries = self.load_entries()
            existing = next(
                (item for item in entries if item.request_ref == request_ref),
                None,
            )
            if existing is not None:
                if existing.request_fingerprint_ref != request_fingerprint_ref:
                    raise PortableEvidenceKeyLifecycleConflictError(
                        "PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT"
                    )
                return existing
            if entries and entries[-1].action not in {
                "created",
                "retired_key_delete_completed",
            }:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_KEY_LIFECYCLE_NOT_SETTLED"
                )
            active = [
                record
                for record in _project_records(entries)
                if record.status == "active"
            ]
            if len(active) != 1:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_ACTIVE_KEY_REQUIRED"
                )
            current = active[0]
            return self._append_locked(
                entries=entries,
                action=action,
                request_ref=request_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=current.key_ref,
                key_version_ref=current.key_version_ref,
                generation=current.generation,
                public_key_base64url=current.public_key_base64url,
                public_key_fingerprint_ref=current.public_key_fingerprint_ref,
                predecessor_key_version_ref=current.predecessor_key_version_ref,
                revocation_ref=revocation_ref,
                checked_at=checked_at,
            )

    def _append(self, **kwargs: Any) -> PortableEvidenceKeyLifecycleEntry:
        with self.operation_lock():
            return self._append_locked(entries=self.load_entries(), **kwargs)

    def _append_locked(
        self,
        *,
        entries: tuple[PortableEvidenceKeyLifecycleEntry, ...],
        action: PortableEvidenceKeyLifecycleAction,
        request_ref: str,
        request_fingerprint_ref: str,
        receipt_ref: str,
        key_ref: str,
        key_version_ref: str,
        generation: int,
        public_key_base64url: str,
        public_key_fingerprint_ref: str,
        predecessor_key_version_ref: str | None = None,
        revocation_ref: str | None = None,
        checked_at: datetime | None = None,
    ) -> PortableEvidenceKeyLifecycleEntry:
        existing = next(
            (item for item in entries if item.request_ref == request_ref), None
        )
        if existing is not None:
            if existing.request_fingerprint_ref != request_fingerprint_ref:
                raise PortableEvidenceKeyLifecycleConflictError(
                    "PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT"
                )
            return existing
        reserved_entries_after_append = {
            # An active key must always retain room for one terminal transition
            # and its deletion settlement.  A rotation additionally needs its
            # own settlement before that emergency pair remains available.
            PortableEvidenceKeyLifecycleAction.created: 2,
            PortableEvidenceKeyLifecycleAction.rotated: 3,
            PortableEvidenceKeyLifecycleAction.retired_key_delete_completed: 2,
            PortableEvidenceKeyLifecycleAction.revoked: 1,
            PortableEvidenceKeyLifecycleAction.marked_lost: 1,
        }.get(action, 0)
        entry_limit = PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES
        entry_limit -= reserved_entries_after_append
        if len(entries) >= entry_limit:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_FULL"
            )
        if action == PortableEvidenceKeyLifecycleAction.created and entries:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_ALREADY_CONFIGURED"
            )
        base = PortableEvidenceKeyLifecycleEntry.model_construct(
            sequence=len(entries) + 1,
            action=action,
            request_ref=request_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            receipt_ref=receipt_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            generation=generation,
            public_key_base64url=public_key_base64url,
            public_key_fingerprint_ref=public_key_fingerprint_ref,
            predecessor_key_version_ref=predecessor_key_version_ref,
            revocation_ref=revocation_ref,
            checked_at=checked_at or utc_now(),
            previous_entry_hash_ref=entries[-1].entry_hash_ref if entries else None,
            entry_hash_ref="portable-evidence-key-entry-hash-ref:pending",
        )
        entry = PortableEvidenceKeyLifecycleEntry.model_validate(
            base.model_dump(mode="python", exclude={"entry_hash_ref"})
            | {"entry_hash_ref": _entry_hash(base)}
        )
        _validate_chain((*entries, entry))
        self._append_bytes(entry)
        return entry

    def _append_bytes(self, entry: PortableEvidenceKeyLifecycleEntry) -> None:
        self._ensure_state_dir()
        encoded = (entry.model_dump_json() + "\n").encode("utf-8")
        if len(encoded) > PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_SIZE_LIMIT_EXCEEDED"
            )
        current_size = self.path.stat().st_size if self.path.exists() else 0
        reserved_entries_after_append = {
            PortableEvidenceKeyLifecycleAction.created.value: 2,
            PortableEvidenceKeyLifecycleAction.rotated.value: 3,
            PortableEvidenceKeyLifecycleAction.retired_key_delete_completed.value: 2,
            PortableEvidenceKeyLifecycleAction.revoked.value: 1,
            PortableEvidenceKeyLifecycleAction.marked_lost.value: 1,
        }.get(entry.action, 0)
        size_limit = PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES
        size_limit -= (
            reserved_entries_after_append
            * PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES
        )
        if current_size + len(encoded) > size_limit:
            raise PortableEvidenceKeyLifecycleConflictError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_SIZE_LIMIT_EXCEEDED"
            )
        ledger_existed = self._ledger_exists_no_follow()
        descriptor = _open_regular(
            self.path,
            os.O_WRONLY | os.O_APPEND | os.O_CREAT,
            mode=0o600,
        )
        try:
            os.fchmod(descriptor, 0o600)
            written = os.write(descriptor, encoded)
            if written != len(encoded):
                raise PortableEvidenceKeyLifecycleCorruptionError(
                    "PORTABLE_EVIDENCE_KEY_LEDGER_SHORT_WRITE"
                )
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if not ledger_existed:
            self._fsync_state_dir()

    def _ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self._validate_existing_state_dir():
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_STATE_DIR_INVALID"
            )
        os.chmod(self.state_dir, 0o700)

    def _validate_existing_state_dir(self) -> bool:
        try:
            metadata = os.lstat(self.state_dir)
        except FileNotFoundError:
            return False
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_STATE_DIR_INVALID"
            )
        return True

    def _ledger_exists_no_follow(self) -> bool:
        try:
            os.lstat(self.path)
        except FileNotFoundError:
            return False
        return True

    def _fsync_state_dir(self) -> None:
        descriptor = os.open(
            self.state_dir,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _project_records(
    entries: tuple[PortableEvidenceKeyLifecycleEntry, ...],
) -> tuple[PortableEvidencePublicKeyRecord, ...]:
    records: list[PortableEvidencePublicKeyRecord] = []
    for entry in entries:
        if entry.action in {"created", "rotated"}:
            if entry.action == "created" and records:
                raise ValueError("PORTABLE_EVIDENCE_KEY_CREATE_TRANSITION_INVALID")
            if entry.action == "rotated" and (
                not records or records[-1].status != "active"
            ):
                raise ValueError("PORTABLE_EVIDENCE_KEY_ROTATE_TRANSITION_INVALID")
            if entry.action == "rotated":
                records[-1] = records[-1].model_copy(
                    update={"status": PortableEvidenceKeyStatus.retired}
                )
            records.append(
                PortableEvidencePublicKeyRecord(
                    key_ref=entry.key_ref,
                    key_version_ref=entry.key_version_ref,
                    generation=entry.generation,
                    status=PortableEvidenceKeyStatus.active,
                    public_key_base64url=entry.public_key_base64url,
                    public_key_fingerprint_ref=entry.public_key_fingerprint_ref,
                    predecessor_key_version_ref=entry.predecessor_key_version_ref,
                    lifecycle_receipt_ref=entry.receipt_ref,
                )
            )
        elif entry.action == "revoked":
            if not records or records[-1].status != "active":
                raise ValueError("PORTABLE_EVIDENCE_KEY_REVOKE_TRANSITION_INVALID")
            records[-1] = records[-1].model_copy(
                update={
                    "status": PortableEvidenceKeyStatus.revoked,
                    "revocation_ref": entry.revocation_ref,
                    "lifecycle_receipt_ref": entry.receipt_ref,
                }
            )
        elif entry.action == "marked_lost":
            if not records or records[-1].status != "active":
                raise ValueError("PORTABLE_EVIDENCE_KEY_LOST_TRANSITION_INVALID")
            records[-1] = records[-1].model_copy(
                update={
                    "status": PortableEvidenceKeyStatus.lost,
                    "lifecycle_receipt_ref": entry.receipt_ref,
                }
            )
        elif entry.action == "revocation_delete_completed":
            if not records or records[-1].status != "revoked":
                raise ValueError(
                    "PORTABLE_EVIDENCE_KEY_DELETE_COMPLETE_TRANSITION_INVALID"
                )
            if records[-1].revocation_ref != entry.revocation_ref:
                raise ValueError("PORTABLE_EVIDENCE_KEY_REVOCATION_REF_MISMATCH")
        elif entry.action == "retired_key_delete_completed":
            if len(records) < 2 or records[-2].status != "retired":
                raise ValueError(
                    "PORTABLE_EVIDENCE_RETIRED_KEY_DELETE_TRANSITION_INVALID"
                )
            if records[-2].key_version_ref != entry.key_version_ref:
                raise ValueError("PORTABLE_EVIDENCE_RETIRED_KEY_VERSION_MISMATCH")
        elif entry.action == "lost_key_delete_completed":
            if not records or records[-1].status != "lost":
                raise ValueError("PORTABLE_EVIDENCE_LOST_KEY_DELETE_TRANSITION_INVALID")
            if records[-1].key_version_ref != entry.key_version_ref:
                raise ValueError("PORTABLE_EVIDENCE_LOST_KEY_VERSION_MISMATCH")
    return tuple(records)


def _validate_chain(entries: tuple[PortableEvidenceKeyLifecycleEntry, ...]) -> None:
    previous: str | None = None
    for sequence, entry in enumerate(entries, 1):
        if entry.sequence != sequence or entry.previous_entry_hash_ref != previous:
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_CHAIN_INVALID"
            )
        previous = entry.entry_hash_ref
    try:
        records = _project_records(entries)
    except ValueError as exc:
        raise PortableEvidenceKeyLifecycleCorruptionError(
            "PORTABLE_EVIDENCE_KEY_LEDGER_TRANSITION_INVALID"
        ) from exc
    if len({record.key_version_ref for record in records}) != len(records):
        raise PortableEvidenceKeyLifecycleCorruptionError(
            "PORTABLE_EVIDENCE_KEY_LEDGER_VERSION_DUPLICATE"
        )
    if len({record.public_key_fingerprint_ref for record in records}) != len(records):
        raise PortableEvidenceKeyLifecycleCorruptionError(
            "PORTABLE_EVIDENCE_KEY_LEDGER_FINGERPRINT_DUPLICATE"
        )
    if len({record.key_ref for record in records}) > 1:
        raise PortableEvidenceKeyLifecycleCorruptionError(
            "PORTABLE_EVIDENCE_KEY_LEDGER_KEY_REF_CHANGED"
        )
    for index, record in enumerate(records):
        expected_predecessor = (
            None if index == 0 else records[index - 1].key_version_ref
        )
        if (
            record.generation != index + 1
            or record.predecessor_key_version_ref != expected_predecessor
        ):
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_CONTINUITY_INVALID"
            )


def _entry_hash(entry: PortableEvidenceKeyLifecycleEntry) -> str:
    payload = entry.model_dump(mode="json", exclude={"entry_hash_ref"})
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return f"portable-evidence-key-entry-hash-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _decode_public_key(value: str) -> bytes:
    import base64

    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("PORTABLE_EVIDENCE_KEY_LEDGER_PUBLIC_KEY_INVALID") from exc


def _open_regular(path: Path, flags: int, *, mode: int = 0o600) -> int:
    descriptor = os.open(
        path,
        flags
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
        mode,
    )
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_mode & 0o077
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_FILE_INVALID"
            )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_bounded(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(
            descriptor, min(65_536, PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES + 1 - total)
        )
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES:
            raise PortableEvidenceKeyLifecycleCorruptionError(
                "PORTABLE_EVIDENCE_KEY_LEDGER_SIZE_LIMIT_EXCEEDED"
            )
    return b"".join(chunks)


def _validate_refs(value: object) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"portable_evidence_lifecycle_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"portable_evidence_lifecycle_{name}")
            else:
                _validate_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested)
