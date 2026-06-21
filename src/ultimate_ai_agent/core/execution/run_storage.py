import hashlib
import json
import os
import uuid
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.durable_runs import (
    DurableRunCorruptionError,
    DurableRunError,
    DurableRunRecord,
    DurableRunSnapshot,
    build_durable_run_snapshot,
    restore_durable_run_snapshot,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


DURABLE_RUN_STORAGE_SCHEMA_VERSION = "durable_run_storage.v1"
DURABLE_RECEIPT_HASH_SCHEMA_VERSION = "durable_receipt_hash.v1"
UNSAFE_STORAGE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "environment dump",
    "environment_dump",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
)
RECEIPT_HASH_METADATA_KEYS = frozenset(
    {
        "receipt_hash_ref",
        "receipt_hash_schema_version",
        "replay_validation_ref",
    }
)
UNSAFE_RECEIPT_HASH_KEY_FRAGMENTS = (
    "prompt",
    "response",
    "provider",
    "path",
    "log",
    "username",
    "hostname",
    "serial",
    "environment",
    "credential",
    "secret",
    "token",
    "password",
    "cookie",
    "authorization",
)


class DurableRunStorageError(DurableRunError):
    """Base error for append-first local durable run storage."""


class DurableRunStorageDuplicateError(DurableRunStorageError):
    """Raised when a duplicate idempotency key is denied."""


class DurableRunStorageWriteError(DurableRunStorageError):
    """Raised when an atomic local storage mutation fails safely."""


class DurableRunStorageCorruptionError(DurableRunCorruptionError):
    """Raised when local durable run storage fails integrity checks."""


class DurableRunStorageEntryKind(str, Enum):
    run_record = "run_record"
    receipt = "receipt"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_payload(value: Any) -> str:
    payload = _canonical_json(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _validate_storage_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_STORAGE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe durable storage language")


def _validate_storage_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_storage_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_storage_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_storage_payload(str(key), field_name)
            _validate_storage_payload(item, field_name)


def _validate_receipt_hash_key(key: str) -> None:
    _validate_storage_text(key, "receipt_summary_key")
    normalized = key.lower().replace("-", "_")
    for fragment in UNSAFE_RECEIPT_HASH_KEY_FRAGMENTS:
        if fragment in normalized:
            raise ValueError("receipt summary contains unsafe durable receipt hash key")


def _canonical_receipt_hash_payload(value: Any) -> Any:
    if isinstance(value, dict):
        canonical: dict[str, Any] = {}
        for key in sorted(value):
            normalized_key = str(key)
            if normalized_key in RECEIPT_HASH_METADATA_KEYS:
                continue
            _validate_receipt_hash_key(normalized_key)
            canonical[normalized_key] = _canonical_receipt_hash_payload(value[key])
        return canonical
    if isinstance(value, list):
        return [_canonical_receipt_hash_payload(item) for item in value]
    return value


def build_receipt_summary_hash_ref(receipt_summary: dict[str, Any]) -> str:
    """Build a stable replay hash over a redacted receipt summary only."""

    validate_safe_execution_payload(receipt_summary, "receipt_summary")
    _validate_storage_payload(receipt_summary, "receipt_summary")
    canonical_summary = _canonical_receipt_hash_payload(receipt_summary)
    return _hash_payload(
        {
            "schema_version": DURABLE_RECEIPT_HASH_SCHEMA_VERSION,
            "receipt_summary": canonical_summary,
        }
    )


def validate_receipt_summary_hash_ref(receipt_summary: dict[str, Any], receipt_hash_ref: str) -> bool:
    validate_execution_ref(receipt_hash_ref, "receipt_hash_ref")
    expected_hash_ref = build_receipt_summary_hash_ref(receipt_summary)
    if receipt_hash_ref != expected_hash_ref:
        raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_RECEIPT_HASH_MISMATCH")
    return True


def _build_replay_validation_ref(run_id: str, receipt_ref: str, receipt_hash_ref: str) -> str:
    return _hash_payload(
        {
            "schema_version": DURABLE_RECEIPT_HASH_SCHEMA_VERSION,
            "run_id": run_id,
            "receipt_ref": receipt_ref,
            "receipt_hash_ref": receipt_hash_ref,
        }
    )


class DurableRunStorageEntry(BaseModel):
    entry_id: str = Field(..., min_length=1)
    schema_version: str = DURABLE_RUN_STORAGE_SCHEMA_VERSION
    kind: DurableRunStorageEntryKind
    run_id: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    record_snapshot: DurableRunSnapshot | None = None
    receipt_summary: dict[str, Any] | None = None
    receipt_hash_schema_version: str | None = None
    receipt_hash_ref: str | None = None
    replay_validation_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> Any:
        for value, field_name in [
            (self.entry_id, "entry_id"),
            (self.run_id, "run_id"),
            (self.idempotency_key, "idempotency_key"),
            (self.audit_ref, "audit_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.entry_hash_ref, "entry_hash_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.previous_entry_hash_ref:
            validate_execution_ref(self.previous_entry_hash_ref, "previous_entry_hash_ref")
        _validate_storage_text(self.schema_version, "schema_version")
        _validate_storage_text(self.safe_summary, "safe_summary")
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        if self.schema_version != DURABLE_RUN_STORAGE_SCHEMA_VERSION:
            raise ValueError("DURABLE_RUN_STORAGE_SCHEMA_VERSION_UNSUPPORTED")
        if self.kind == DurableRunStorageEntryKind.run_record:
            if self.record_snapshot is None:
                raise ValueError("DURABLE_RUN_STORAGE_RECORD_SNAPSHOT_REQUIRED")
            if self.receipt_summary is not None:
                raise ValueError("DURABLE_RUN_STORAGE_RECORD_RECEIPT_SUMMARY_DENIED")
            if self.receipt_hash_schema_version is not None:
                raise ValueError("DURABLE_RUN_STORAGE_RECORD_RECEIPT_HASH_SCHEMA_DENIED")
            if self.receipt_hash_ref is not None:
                raise ValueError("DURABLE_RUN_STORAGE_RECORD_RECEIPT_HASH_DENIED")
            if self.replay_validation_ref is not None:
                raise ValueError("DURABLE_RUN_STORAGE_RECORD_REPLAY_VALIDATION_DENIED")
            restored = restore_durable_run_snapshot(self.record_snapshot)
            if restored.run_id != self.run_id:
                raise ValueError("DURABLE_RUN_STORAGE_RUN_REF_MISMATCH")
        if self.kind == DurableRunStorageEntryKind.receipt:
            if self.record_snapshot is not None:
                raise ValueError("DURABLE_RUN_STORAGE_RECEIPT_RECORD_SNAPSHOT_DENIED")
            if self.receipt_summary is None:
                raise ValueError("DURABLE_RUN_STORAGE_RECEIPT_SUMMARY_REQUIRED")
            if self.receipt_hash_schema_version != DURABLE_RECEIPT_HASH_SCHEMA_VERSION:
                raise ValueError("DURABLE_RUN_STORAGE_RECEIPT_HASH_SCHEMA_UNSUPPORTED")
            if not self.receipt_hash_ref:
                raise ValueError("DURABLE_RUN_STORAGE_RECEIPT_HASH_REQUIRED")
            if not self.replay_validation_ref:
                raise ValueError("DURABLE_RUN_STORAGE_REPLAY_VALIDATION_REF_REQUIRED")
            _validate_storage_text(self.receipt_hash_schema_version, "receipt_hash_schema_version")
            validate_execution_ref(self.receipt_hash_ref, "receipt_hash_ref")
            validate_execution_ref(self.replay_validation_ref, "replay_validation_ref")
            validate_safe_execution_payload(self.receipt_summary, "receipt_summary")
            _validate_storage_payload(self.receipt_summary, "receipt_summary")
            validate_receipt_summary_hash_ref(self.receipt_summary, self.receipt_hash_ref)
            expected_replay_ref = _build_replay_validation_ref(self.run_id, self.receipt_ref, self.receipt_hash_ref)
            if self.replay_validation_ref != expected_replay_ref:
                raise ValueError("DURABLE_RUN_STORAGE_REPLAY_VALIDATION_REF_MISMATCH")
        return self


def _entry_hash_ref(entry: DurableRunStorageEntry) -> str:
    payload = entry.model_dump(mode="json")
    payload.pop("entry_hash_ref", None)
    return _hash_payload(payload)


class AppendFirstRunStorage:
    """Append-first local storage for durable run records and receipt summaries."""

    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)
        self._entries: list[DurableRunStorageEntry] = []
        self._entry_ids: set[str] = set()
        self._idempotency_keys_by_run: dict[str, set[str]] = defaultdict(set)
        self._entries_by_run: dict[str, list[DurableRunStorageEntry]] = defaultdict(list)
        self._load_from_file()

    def append_run_record(
        self,
        record: DurableRunRecord,
        *,
        idempotency_key: str,
        audit_ref: str,
        receipt_ref: str,
        rollback_ref: str,
        safe_summary: str,
        evidence_refs: Iterable[str] = (),
    ) -> DurableRunStorageEntry:
        validated_record = DurableRunRecord.model_validate(record.model_dump())
        snapshot = build_durable_run_snapshot(validated_record)
        entry = self._build_entry(
            kind=DurableRunStorageEntryKind.run_record,
            run_id=validated_record.run_id,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            rollback_ref=rollback_ref,
            safe_summary=safe_summary,
            record_snapshot=snapshot,
            evidence_refs=list(evidence_refs),
        )
        self._append_entry(entry)
        return entry.model_copy(deep=True)

    def append_receipt_summary(
        self,
        *,
        run_id: str,
        receipt_ref: str,
        idempotency_key: str,
        audit_ref: str,
        rollback_ref: str,
        safe_summary: str,
        receipt_summary: dict[str, Any],
        evidence_refs: Iterable[str] = (),
    ) -> DurableRunStorageEntry:
        entry = self._build_entry(
            kind=DurableRunStorageEntryKind.receipt,
            run_id=run_id,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            rollback_ref=rollback_ref,
            safe_summary=safe_summary,
            receipt_summary=dict(receipt_summary),
            evidence_refs=list(evidence_refs),
        )
        self._append_entry(entry)
        return entry.model_copy(deep=True)

    def list_entries(self, run_id: str | None = None) -> list[DurableRunStorageEntry]:
        entries = self._entries_by_run.get(run_id, []) if run_id else self._entries
        return [entry.model_copy(deep=True) for entry in entries]

    def latest_run_record(self, run_id: str) -> DurableRunRecord | None:
        validate_execution_ref(run_id, "run_id")
        for entry in reversed(self._entries_by_run.get(run_id, [])):
            if entry.kind == DurableRunStorageEntryKind.run_record and entry.record_snapshot is not None:
                return restore_durable_run_snapshot(entry.record_snapshot)
        return None

    def list_receipt_summaries(self, run_id: str) -> list[dict[str, Any]]:
        validate_execution_ref(run_id, "run_id")
        receipts = []
        for entry in self._entries_by_run.get(run_id, []):
            if entry.kind == DurableRunStorageEntryKind.receipt and entry.receipt_summary is not None:
                receipts.append(dict(entry.receipt_summary))
        return receipts

    def validate_receipt_replay(self, run_id: str, receipt_ref: str) -> DurableRunStorageEntry:
        validate_execution_ref(run_id, "run_id")
        validate_execution_ref(receipt_ref, "receipt_ref")
        for entry in self._entries_by_run.get(run_id, []):
            if entry.kind != DurableRunStorageEntryKind.receipt or entry.receipt_ref != receipt_ref:
                continue
            if entry.receipt_summary is None or entry.receipt_hash_ref is None:
                raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_RECEIPT_HASH_REQUIRED")
            validate_receipt_summary_hash_ref(entry.receipt_summary, entry.receipt_hash_ref)
            if entry.entry_hash_ref != _entry_hash_ref(entry):
                raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_ENTRY_HASH_MISMATCH")
            return entry.model_copy(deep=True)
        raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_RECEIPT_REPLAY_REF_MISSING")

    def _build_entry(
        self,
        *,
        kind: DurableRunStorageEntryKind,
        run_id: str,
        idempotency_key: str,
        audit_ref: str,
        receipt_ref: str,
        rollback_ref: str,
        safe_summary: str,
        evidence_refs: list[str],
        record_snapshot: DurableRunSnapshot | None = None,
        receipt_summary: dict[str, Any] | None = None,
    ) -> DurableRunStorageEntry:
        for value, field_name in [
            (run_id, "run_id"),
            (idempotency_key, "idempotency_key"),
            (audit_ref, "audit_ref"),
            (receipt_ref, "receipt_ref"),
            (rollback_ref, "rollback_ref"),
        ]:
            validate_execution_ref(value, field_name)
        _validate_storage_text(safe_summary, "safe_summary")
        for ref in evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        if idempotency_key in self._idempotency_keys_by_run[run_id]:
            raise DurableRunStorageDuplicateError("DURABLE_RUN_STORAGE_IDEMPOTENCY_REPLAY_DENIED")

        receipt_hash_schema_version = None
        receipt_hash_ref = None
        replay_validation_ref = None
        if kind == DurableRunStorageEntryKind.receipt:
            if receipt_summary is None:
                raise ValueError("DURABLE_RUN_STORAGE_RECEIPT_SUMMARY_REQUIRED")
            receipt_hash_schema_version = DURABLE_RECEIPT_HASH_SCHEMA_VERSION
            receipt_hash_ref = build_receipt_summary_hash_ref(receipt_summary)
            replay_validation_ref = _build_replay_validation_ref(run_id, receipt_ref, receipt_hash_ref)

        previous_hash_ref = self._entries[-1].entry_hash_ref if self._entries else None
        entry_seed = _hash_payload(
            {
                "kind": kind.value,
                "run_id": run_id,
                "idempotency_key": idempotency_key,
                "position": len(self._entries) + 1,
            }
        ).split(":", 1)[1][:16]
        draft = DurableRunStorageEntry(
            entry_id=f"durable-run-storage-entry:{entry_seed}",
            kind=kind,
            run_id=run_id,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            rollback_ref=rollback_ref,
            safe_summary=safe_summary,
            record_snapshot=record_snapshot,
            receipt_summary=receipt_summary,
            receipt_hash_schema_version=receipt_hash_schema_version,
            receipt_hash_ref=receipt_hash_ref,
            replay_validation_ref=replay_validation_ref,
            evidence_refs=evidence_refs,
            previous_entry_hash_ref=previous_hash_ref,
            entry_hash_ref="sha256:pending",
        )
        return draft.model_copy(update={"entry_hash_ref": _entry_hash_ref(draft)})

    def _append_entry(self, entry: DurableRunStorageEntry) -> None:
        validated = DurableRunStorageEntry.model_validate(entry.model_dump())
        expected_hash = _entry_hash_ref(validated)
        if validated.entry_hash_ref != expected_hash:
            raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_ENTRY_HASH_MISMATCH")
        if validated.entry_id in self._entry_ids:
            raise DurableRunStorageDuplicateError("DURABLE_RUN_STORAGE_ENTRY_REPLAY_DENIED")
        if validated.idempotency_key in self._idempotency_keys_by_run[validated.run_id]:
            raise DurableRunStorageDuplicateError("DURABLE_RUN_STORAGE_IDEMPOTENCY_REPLAY_DENIED")

        next_entries = [*self._entries, validated]
        self._write_entries_atomically(next_entries)
        self._append_in_memory(validated)

    def _append_in_memory(self, entry: DurableRunStorageEntry) -> None:
        if entry.entry_id in self._entry_ids:
            raise DurableRunStorageDuplicateError("DURABLE_RUN_STORAGE_ENTRY_REPLAY_DENIED")
        if entry.idempotency_key in self._idempotency_keys_by_run[entry.run_id]:
            raise DurableRunStorageDuplicateError("DURABLE_RUN_STORAGE_IDEMPOTENCY_REPLAY_DENIED")
        self._entries.append(entry)
        self._entry_ids.add(entry.entry_id)
        self._idempotency_keys_by_run[entry.run_id].add(entry.idempotency_key)
        self._entries_by_run[entry.run_id].append(entry)

    def _load_from_file(self) -> None:
        if not self.filepath.exists():
            return

        previous_hash_ref: str | None = None
        with self.filepath.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = DurableRunStorageEntry.model_validate(json.loads(line))
                except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                    raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_CORRUPT_ENTRY") from exc
                if entry.previous_entry_hash_ref != previous_hash_ref:
                    raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_HASH_CHAIN_MISMATCH")
                if entry.entry_hash_ref != _entry_hash_ref(entry):
                    raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_ENTRY_HASH_MISMATCH")
                try:
                    self._append_in_memory(entry)
                except DurableRunStorageDuplicateError as exc:
                    raise DurableRunStorageCorruptionError("DURABLE_RUN_STORAGE_DUPLICATE_ENTRY_ON_LOAD") from exc
                previous_hash_ref = entry.entry_hash_ref

    def _write_entries_atomically(self, entries: list[DurableRunStorageEntry]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(entry.model_dump_json() + "\n" for entry in entries)
        temp_path = self.filepath.with_name(f".{self.filepath.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            self._replace_temp_file(temp_path, self.filepath)
            self._fsync_parent_directory()
        except DurableRunStorageWriteError:
            temp_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise DurableRunStorageWriteError("DURABLE_RUN_STORAGE_ATOMIC_WRITE_FAILED") from exc

    def _replace_temp_file(self, temp_path: Path, target_path: Path) -> None:
        os.replace(temp_path, target_path)

    def _fsync_parent_directory(self) -> None:
        try:
            directory_fd = os.open(self.filepath.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
