"""Shared local application-data foundation for ECO-001.

The store deliberately keeps private values encrypted inside SQLite while the
governance plane contains safe references, fingerprints, and bounded status
metadata only.  It provides no connector, network, model, or standing runtime
authority.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import struct
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ultimate_ai_agent.core.safe_contract_text import validate_safe_contract_text_shape
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_LOCAL_DATA_SCHEMA_VERSION = 1
ECO_LOCAL_DATA_SCHEMA_REF = "schema-ref:ecosystem-local-data:v1"
_BACKUP_MAGIC = b"UAA-ECO-LOCAL-BACKUP-V1\x00"
_NONCE_BYTES = 12
_MAX_PRIVATE_PAYLOAD_BYTES = 1024 * 1024
_MAX_BACKUP_BYTES = 512 * 1024 * 1024
_SAFE_REF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
)


class EcosystemLocalDataError(RuntimeError):
    """Fail-closed local-data error with a stable, non-sensitive code."""


class EcosystemKeyUnavailable(EcosystemLocalDataError):
    pass


class EcosystemConflict(EcosystemLocalDataError):
    pass


class LocalDataCryptoBackend(Protocol):
    """Injected key boundary; implementations must keep key bytes out of SQLite."""

    backend_ref: str

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str: ...
    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str: ...
    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes: ...
    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes: ...
    def blind_index(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        normalized_term: str,
    ) -> str: ...
    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str: ...


class InMemoryLocalDataCryptoBackend:
    """Test-only key backend; this is not production keychain readiness."""

    backend_ref = "key-backend-ref:ecosystem:in-memory-test-only"

    def __init__(self) -> None:
        self._keys: dict[tuple[str, str], bytes] = {}
        self.locked = False

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str:
        if self.locked:
            raise EcosystemKeyUnavailable("ECO_KEY_BACKEND_LOCKED")
        self._keys.setdefault((key_item_ref, key_version_ref), secrets.token_bytes(32))
        return _stable_ref(
            "key-receipt-ref:ecosystem:create",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )

    def _key(self, *, key_item_ref: str, key_version_ref: str) -> bytes:
        if self.locked:
            raise EcosystemKeyUnavailable("ECO_KEY_BACKEND_LOCKED")
        try:
            return self._keys[(key_item_ref, key_version_ref)]
        except KeyError as exc:
            raise EcosystemKeyUnavailable("ECO_KEY_NOT_FOUND") from exc

    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str:
        self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return _stable_ref(
            "key-receipt-ref:ecosystem:probe",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )

    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes:
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        nonce = secrets.token_bytes(_NONCE_BYTES)
        return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes:
        if len(ciphertext) <= _NONCE_BYTES:
            raise EcosystemLocalDataError("ECO_CIPHERTEXT_INVALID")
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        try:
            return AESGCM(key).decrypt(
                ciphertext[:_NONCE_BYTES], ciphertext[_NONCE_BYTES:], aad
            )
        except InvalidTag as exc:
            raise EcosystemLocalDataError("ECO_CIPHERTEXT_INTEGRITY_FAILED") from exc

    def blind_index(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        normalized_term: str,
    ) -> str:
        key = self._key(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return hmac.new(
            key, b"eco-search-v1\x00" + normalized_term.encode(), hashlib.sha256
        ).hexdigest()

    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str:
        if self.locked:
            raise EcosystemKeyUnavailable("ECO_KEY_BACKEND_LOCKED")
        self._keys.pop((key_item_ref, key_version_ref), None)
        return _stable_ref(
            "key-receipt-ref:ecosystem:delete",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )


@dataclass(frozen=True)
class PutRecord:
    operation_ref: str
    module_ref: str
    record_ref: str
    record_kind_ref: str
    safe_summary_ref: str
    private_payload: dict[str, Any] = field(repr=False)
    search_terms: tuple[str, ...] = field(default_factory=tuple, repr=False)
    expected_version: int = 0
    retention_ref: str = "retention-ref:workspace-default"
    expires_at: str | None = None


@dataclass(frozen=True)
class ArchiveRecord:
    operation_ref: str
    record_ref: str
    expected_version: int


@dataclass(frozen=True)
class DeleteRecord:
    operation_ref: str
    record_ref: str
    expected_version: int


LocalMutation = PutRecord | ArchiveRecord | DeleteRecord


@dataclass(frozen=True)
class LocalRecord:
    workspace_ref: str
    module_ref: str
    record_ref: str
    record_kind_ref: str
    safe_summary_ref: str
    version: int
    key_version_ref: str
    private_payload: dict[str, Any] = field(repr=False)
    archived: bool = False
    retention_ref: str = "retention-ref:workspace-default"
    expires_at: str | None = None


@dataclass(frozen=True)
class UnitOfWorkReceipt:
    workspace_ref: str
    idempotency_ref: str
    request_fingerprint_ref: str
    receipt_ref: str
    operation_receipt_refs: tuple[str, ...]
    replayed: bool = False


@dataclass(frozen=True)
class IntegrityReport:
    schema_ref: str
    status: Literal["ok"]
    workspace_count: int
    record_count: int
    search_entry_count: int
    orphan_count: int
    report_ref: str


@dataclass(frozen=True)
class BackupReceipt:
    backup_ref: str
    schema_ref: str
    ciphertext_fingerprint_ref: str
    byte_count: int


@dataclass(frozen=True)
class RestorePreview:
    backup_ref: str
    schema_ref: str
    integrity_status: Literal["ok"]
    workspace_count: int
    record_count: int
    preview_only: Literal[True] = True


@dataclass(frozen=True)
class MigrationPreview:
    source_fingerprint_ref: str
    source_format_ref: str
    candidate_count: int
    destination_schema_ref: str
    preview_ref: str
    writes_performed: Literal[False] = False


def _validate_ref(value: str, *, field_name: str = "ref") -> str:
    if not 3 <= len(value) <= 191 or not value[0].isalpha():
        raise ValueError(f"{field_name.upper()}_SAFE_REF_REQUIRED")
    if any(character not in _SAFE_REF_CHARS for character in value):
        raise ValueError(f"{field_name.upper()}_SAFE_REF_REQUIRED")
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE")
    validate_safe_contract_text_shape(value, field_name)
    return value


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("ECO_PRIVATE_PAYLOAD_JSON_REQUIRED") from exc


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value)).hexdigest()
    return f"{prefix}:{digest}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalized_terms(terms: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for term in terms:
        candidate = " ".join(term.casefold().split())
        if not candidate or len(candidate) > 128:
            raise ValueError("ECO_SEARCH_TERM_INVALID")
        normalized.append(candidate)
    if len(normalized) > 64:
        raise ValueError("ECO_SEARCH_TERM_LIMIT_EXCEEDED")
    return tuple(dict.fromkeys(normalized))


def _record_aad(
    *, workspace_ref: str, record_ref: str, key_version_ref: str, version: int
) -> bytes:
    return _canonical_json(
        {
            "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
            "workspace_ref": workspace_ref,
            "record_ref": record_ref,
            "key_version_ref": key_version_ref,
            "version": version,
        }
    )


class EcosystemLocalDataPlatform:
    """Versioned SQLite data plane with an encrypted private-value boundary."""

    def __init__(
        self,
        *,
        database_path: Path,
        crypto_backend: LocalDataCryptoBackend,
        fault_hook: Callable[[str], None] | None = None,
    ) -> None:
        if not database_path.is_absolute() or database_path == Path(
            database_path.anchor
        ):
            raise ValueError("ECO_DATABASE_PATH_UNSAFE")
        self.database_path = database_path
        self.crypto_backend = crypto_backend
        self._fault_hook = fault_hook
        database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path, timeout=5, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        existing = self.database_path.exists()
        connection = self._connect()
        try:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > ECO_LOCAL_DATA_SCHEMA_VERSION:
                raise EcosystemLocalDataError("ECO_SCHEMA_UNSUPPORTED")
            if version == 0:
                connection.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS eco_workspaces (
                        workspace_ref TEXT PRIMARY KEY,
                        key_item_ref TEXT NOT NULL UNIQUE,
                        key_version_ref TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS eco_schema_migrations (
                        schema_version INTEGER PRIMARY KEY,
                        schema_ref TEXT NOT NULL UNIQUE,
                        applied_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS eco_records (
                        workspace_ref TEXT NOT NULL,
                        module_ref TEXT NOT NULL,
                        record_ref TEXT NOT NULL,
                        record_kind_ref TEXT NOT NULL,
                        safe_summary_ref TEXT NOT NULL,
                        version INTEGER NOT NULL CHECK(version >= 1),
                        key_version_ref TEXT NOT NULL,
                        ciphertext BLOB NOT NULL,
                        archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0, 1)),
                        retention_ref TEXT NOT NULL,
                        expires_at TEXT,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (workspace_ref, record_ref),
                        FOREIGN KEY (workspace_ref) REFERENCES eco_workspaces(workspace_ref)
                    );
                    CREATE TABLE IF NOT EXISTS eco_search_tokens (
                        workspace_ref TEXT NOT NULL,
                        record_ref TEXT NOT NULL,
                        token_hash TEXT NOT NULL,
                        PRIMARY KEY (workspace_ref, record_ref, token_hash),
                        FOREIGN KEY (workspace_ref, record_ref)
                            REFERENCES eco_records(workspace_ref, record_ref) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS eco_uow_receipts (
                        workspace_ref TEXT NOT NULL,
                        idempotency_ref TEXT NOT NULL,
                        request_fingerprint_ref TEXT NOT NULL,
                        receipt_ref TEXT NOT NULL,
                        operation_receipt_refs_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (workspace_ref, idempotency_ref),
                        FOREIGN KEY (workspace_ref) REFERENCES eco_workspaces(workspace_ref)
                    );
                    CREATE TABLE IF NOT EXISTS eco_events (
                        event_ref TEXT PRIMARY KEY,
                        workspace_ref TEXT NOT NULL,
                        record_ref TEXT NOT NULL,
                        operation_ref TEXT NOT NULL,
                        event_kind_ref TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_ref) REFERENCES eco_workspaces(workspace_ref)
                    );
                    INSERT INTO eco_schema_migrations VALUES (
                        1, 'schema-ref:ecosystem-local-data:v1',
                        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    );
                    PRAGMA user_version = 1;
                    COMMIT;
                    """
                )
            self._validate_schema(connection)
            if self._fault_hook:
                self._fault_hook("schema-ready")
        except Exception:
            connection.close()
            if not existing and self.database_path.exists():
                self.database_path.unlink()
            raise
        finally:
            try:
                connection.close()
            except Exception:
                pass
        os.chmod(self.database_path, 0o600)

    @staticmethod
    def _validate_schema(connection: sqlite3.Connection) -> None:
        required_tables = {
            "eco_events",
            "eco_records",
            "eco_schema_migrations",
            "eco_search_tokens",
            "eco_uow_receipts",
            "eco_workspaces",
        }
        actual_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not required_tables.issubset(actual_tables):
            raise EcosystemLocalDataError("ECO_SCHEMA_INCOMPLETE")
        migration = connection.execute(
            "SELECT schema_ref FROM eco_schema_migrations WHERE schema_version = ?",
            (ECO_LOCAL_DATA_SCHEMA_VERSION,),
        ).fetchone()
        if migration is None or migration[0] != ECO_LOCAL_DATA_SCHEMA_REF:
            raise EcosystemLocalDataError("ECO_SCHEMA_MIGRATION_LEDGER_INVALID")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED")

    def create_workspace(
        self, *, workspace_ref: str, key_version_ref: str = "key-version-ref:v1"
    ) -> str:
        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(key_version_ref, field_name="key_version_ref")
        key_item_ref = _stable_ref("key-item-ref:ecosystem", workspace_ref)
        receipt_ref = self.crypto_backend.create(
            key_item_ref=key_item_ref, key_version_ref=key_version_ref
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT key_item_ref, key_version_ref FROM eco_workspaces WHERE workspace_ref = ?",
                (workspace_ref,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO eco_workspaces VALUES (?, ?, ?, ?)",
                    (workspace_ref, key_item_ref, key_version_ref, _utc_now()),
                )
            elif (row["key_item_ref"], row["key_version_ref"]) != (
                key_item_ref,
                key_version_ref,
            ):
                raise EcosystemConflict("ECO_WORKSPACE_KEY_CONFLICT")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return receipt_ref

    def _workspace_key(
        self, connection: sqlite3.Connection, workspace_ref: str
    ) -> tuple[str, str]:
        row = connection.execute(
            "SELECT key_item_ref, key_version_ref FROM eco_workspaces WHERE workspace_ref = ?",
            (workspace_ref,),
        ).fetchone()
        if row is None:
            raise EcosystemLocalDataError("ECO_WORKSPACE_NOT_FOUND")
        self.crypto_backend.probe(
            key_item_ref=row["key_item_ref"], key_version_ref=row["key_version_ref"]
        )
        return row["key_item_ref"], row["key_version_ref"]

    def apply(
        self,
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operations: tuple[LocalMutation, ...],
    ) -> UnitOfWorkReceipt:
        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(idempotency_ref, field_name="idempotency_ref")
        if not operations or len(operations) > 64:
            raise ValueError("ECO_UOW_OPERATION_COUNT_INVALID")
        operation_refs = [
            _validate_ref(item.operation_ref, field_name="operation_ref")
            for item in operations
        ]
        if len(operation_refs) != len(set(operation_refs)):
            raise ValueError("ECO_UOW_DUPLICATE_OPERATION_REF")
        fingerprint_ref = self._request_fingerprint(workspace_ref, operations)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            key_item_ref, key_version_ref = self._workspace_key(
                connection, workspace_ref
            )
            replay = connection.execute(
                "SELECT * FROM eco_uow_receipts WHERE workspace_ref = ? AND idempotency_ref = ?",
                (workspace_ref, idempotency_ref),
            ).fetchone()
            if replay is not None:
                if replay["request_fingerprint_ref"] != fingerprint_ref:
                    raise EcosystemConflict("ECO_IDEMPOTENCY_REPLAY_CONFLICT")
                connection.rollback()
                return UnitOfWorkReceipt(
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    request_fingerprint_ref=fingerprint_ref,
                    receipt_ref=replay["receipt_ref"],
                    operation_receipt_refs=tuple(
                        json.loads(replay["operation_receipt_refs_json"])
                    ),
                    replayed=True,
                )
            receipts: list[str] = []
            for index, operation in enumerate(operations):
                receipt = self._apply_one(
                    connection,
                    workspace_ref=workspace_ref,
                    key_item_ref=key_item_ref,
                    key_version_ref=key_version_ref,
                    operation=operation,
                )
                receipts.append(receipt)
                if self._fault_hook:
                    self._fault_hook(f"operation-applied:{index}")
            receipt_ref = _stable_ref(
                "uow-receipt-ref:ecosystem",
                {
                    "workspace_ref": workspace_ref,
                    "idempotency_ref": idempotency_ref,
                    "request_fingerprint_ref": fingerprint_ref,
                    "operation_receipt_refs": receipts,
                },
            )
            connection.execute(
                "INSERT INTO eco_uow_receipts VALUES (?, ?, ?, ?, ?, ?)",
                (
                    workspace_ref,
                    idempotency_ref,
                    fingerprint_ref,
                    receipt_ref,
                    json.dumps(receipts, separators=(",", ":")),
                    _utc_now(),
                ),
            )
            connection.commit()
            return UnitOfWorkReceipt(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                request_fingerprint_ref=fingerprint_ref,
                receipt_ref=receipt_ref,
                operation_receipt_refs=tuple(receipts),
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _request_fingerprint(
        self, workspace_ref: str, operations: tuple[LocalMutation, ...]
    ) -> str:
        encoded: list[dict[str, Any]] = []
        for operation in operations:
            item = dict(vars(operation))
            if isinstance(operation, PutRecord):
                item["private_payload"] = hashlib.sha256(
                    _canonical_json(operation.private_payload)
                ).hexdigest()
                item["search_terms"] = [
                    hashlib.sha256(term.encode()).hexdigest()
                    for term in _normalized_terms(operation.search_terms)
                ]
            item["operation_type"] = type(operation).__name__
            encoded.append(item)
        return _stable_ref(
            "request-fingerprint-ref:ecosystem",
            {"workspace_ref": workspace_ref, "operations": encoded},
        )

    def _apply_one(
        self,
        connection: sqlite3.Connection,
        *,
        workspace_ref: str,
        key_item_ref: str,
        key_version_ref: str,
        operation: LocalMutation,
    ) -> str:
        if isinstance(operation, PutRecord):
            return self._put(
                connection,
                workspace_ref=workspace_ref,
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                operation=operation,
            )
        _validate_ref(operation.record_ref, field_name="record_ref")
        row = connection.execute(
            "SELECT version, key_version_ref, ciphertext FROM eco_records "
            "WHERE workspace_ref = ? AND record_ref = ?",
            (workspace_ref, operation.record_ref),
        ).fetchone()
        if row is None:
            raise EcosystemConflict("ECO_RECORD_NOT_FOUND")
        if row["version"] != operation.expected_version:
            raise EcosystemConflict("ECO_STALE_RECORD_VERSION")
        next_version = operation.expected_version + 1
        if isinstance(operation, ArchiveRecord):
            plaintext = self.crypto_backend.decrypt(
                key_item_ref=key_item_ref,
                key_version_ref=row["key_version_ref"],
                ciphertext=row["ciphertext"],
                aad=_record_aad(
                    workspace_ref=workspace_ref,
                    record_ref=operation.record_ref,
                    key_version_ref=row["key_version_ref"],
                    version=operation.expected_version,
                ),
            )
            ciphertext = self.crypto_backend.encrypt(
                key_item_ref=key_item_ref,
                key_version_ref=row["key_version_ref"],
                plaintext=plaintext,
                aad=_record_aad(
                    workspace_ref=workspace_ref,
                    record_ref=operation.record_ref,
                    key_version_ref=row["key_version_ref"],
                    version=next_version,
                ),
            )
            connection.execute(
                "UPDATE eco_records SET archived = 1, version = ?, ciphertext = ?, "
                "updated_at = ? "
                "WHERE workspace_ref = ? AND record_ref = ?",
                (
                    next_version,
                    ciphertext,
                    _utc_now(),
                    workspace_ref,
                    operation.record_ref,
                ),
            )
            event_kind_ref = "event-kind-ref:record-archived"
        else:
            connection.execute(
                "DELETE FROM eco_records WHERE workspace_ref = ? AND record_ref = ?",
                (workspace_ref, operation.record_ref),
            )
            event_kind_ref = "event-kind-ref:record-deleted"
        return self._event(
            connection,
            workspace_ref=workspace_ref,
            record_ref=operation.record_ref,
            operation_ref=operation.operation_ref,
            event_kind_ref=event_kind_ref,
            version=next_version,
        )

    def _put(
        self,
        connection: sqlite3.Connection,
        *,
        workspace_ref: str,
        key_item_ref: str,
        key_version_ref: str,
        operation: PutRecord,
    ) -> str:
        for field_name in (
            "module_ref",
            "record_ref",
            "record_kind_ref",
            "safe_summary_ref",
            "retention_ref",
        ):
            _validate_ref(getattr(operation, field_name), field_name=field_name)
        if operation.expires_at is not None:
            try:
                expiry = datetime.fromisoformat(operation.expires_at)
            except ValueError as exc:
                raise ValueError("ECO_EXPIRY_TIMESTAMP_INVALID") from exc
            if expiry.tzinfo is None:
                raise ValueError("ECO_EXPIRY_TIMESTAMP_TIMEZONE_REQUIRED")
        row = connection.execute(
            "SELECT version FROM eco_records WHERE workspace_ref = ? AND record_ref = ?",
            (workspace_ref, operation.record_ref),
        ).fetchone()
        actual_version = 0 if row is None else int(row["version"])
        if actual_version != operation.expected_version:
            raise EcosystemConflict("ECO_STALE_RECORD_VERSION")
        version = actual_version + 1
        normalized_terms = _normalized_terms(operation.search_terms)
        plaintext = _canonical_json(
            {
                "private_payload": operation.private_payload,
                "search_terms": normalized_terms,
            }
        )
        if len(plaintext) > _MAX_PRIVATE_PAYLOAD_BYTES:
            raise ValueError("ECO_PRIVATE_PAYLOAD_LIMIT_EXCEEDED")
        ciphertext = self.crypto_backend.encrypt(
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            plaintext=plaintext,
            aad=_record_aad(
                workspace_ref=workspace_ref,
                record_ref=operation.record_ref,
                key_version_ref=key_version_ref,
                version=version,
            ),
        )
        values = (
            workspace_ref,
            operation.module_ref,
            operation.record_ref,
            operation.record_kind_ref,
            operation.safe_summary_ref,
            version,
            key_version_ref,
            ciphertext,
            0,
            operation.retention_ref,
            operation.expires_at,
            _utc_now(),
        )
        connection.execute(
            "INSERT INTO eco_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(workspace_ref, record_ref) DO UPDATE SET "
            "module_ref=excluded.module_ref, record_kind_ref=excluded.record_kind_ref, "
            "safe_summary_ref=excluded.safe_summary_ref, version=excluded.version, "
            "key_version_ref=excluded.key_version_ref, ciphertext=excluded.ciphertext, "
            "archived=0, retention_ref=excluded.retention_ref, "
            "expires_at=excluded.expires_at, updated_at=excluded.updated_at",
            values,
        )
        connection.execute(
            "DELETE FROM eco_search_tokens WHERE workspace_ref = ? AND record_ref = ?",
            (workspace_ref, operation.record_ref),
        )
        for term in normalized_terms:
            token_hash = self.crypto_backend.blind_index(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                normalized_term=term,
            )
            connection.execute(
                "INSERT INTO eco_search_tokens VALUES (?, ?, ?)",
                (workspace_ref, operation.record_ref, token_hash),
            )
        return self._event(
            connection,
            workspace_ref=workspace_ref,
            record_ref=operation.record_ref,
            operation_ref=operation.operation_ref,
            event_kind_ref="event-kind-ref:record-written",
            version=version,
        )

    def _event(
        self,
        connection: sqlite3.Connection,
        *,
        workspace_ref: str,
        record_ref: str,
        operation_ref: str,
        event_kind_ref: str,
        version: int,
    ) -> str:
        event_ref = _stable_ref(
            "event-ref:ecosystem",
            {
                "workspace_ref": workspace_ref,
                "record_ref": record_ref,
                "operation_ref": operation_ref,
                "event_kind_ref": event_kind_ref,
                "version": version,
            },
        )
        connection.execute(
            "INSERT INTO eco_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event_ref,
                workspace_ref,
                record_ref,
                operation_ref,
                event_kind_ref,
                version,
                _utc_now(),
            ),
        )
        return event_ref.replace("event-ref:", "operation-receipt-ref:", 1)

    def read(self, *, workspace_ref: str, record_ref: str) -> LocalRecord:
        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(record_ref, field_name="record_ref")
        connection = self._connect()
        try:
            key_item_ref, _ = self._workspace_key(connection, workspace_ref)
            row = connection.execute(
                "SELECT * FROM eco_records WHERE workspace_ref = ? AND record_ref = ?",
                (workspace_ref, record_ref),
            ).fetchone()
            if row is None:
                raise EcosystemLocalDataError("ECO_RECORD_NOT_FOUND")
            plaintext = self.crypto_backend.decrypt(
                key_item_ref=key_item_ref,
                key_version_ref=row["key_version_ref"],
                ciphertext=row["ciphertext"],
                aad=_record_aad(
                    workspace_ref=workspace_ref,
                    record_ref=record_ref,
                    key_version_ref=row["key_version_ref"],
                    version=row["version"],
                ),
            )
            envelope = json.loads(plaintext)
            if (
                not isinstance(envelope, dict)
                or set(envelope) != {"private_payload", "search_terms"}
                or not isinstance(envelope["private_payload"], dict)
                or not isinstance(envelope["search_terms"], list)
            ):
                raise EcosystemLocalDataError("ECO_PRIVATE_PAYLOAD_INVALID")
            return LocalRecord(
                workspace_ref=workspace_ref,
                module_ref=row["module_ref"],
                record_ref=record_ref,
                record_kind_ref=row["record_kind_ref"],
                safe_summary_ref=row["safe_summary_ref"],
                version=row["version"],
                key_version_ref=row["key_version_ref"],
                private_payload=envelope["private_payload"],
                archived=bool(row["archived"]),
                retention_ref=row["retention_ref"],
                expires_at=row["expires_at"],
            )
        except (EcosystemLocalDataError, EcosystemKeyUnavailable):
            raise
        except Exception as exc:
            raise EcosystemLocalDataError("ECO_RECORD_INTEGRITY_FAILED") from exc
        finally:
            connection.close()

    def search(self, *, workspace_ref: str, term: str) -> tuple[str, ...]:
        normalized = _normalized_terms((term,))[0]
        connection = self._connect()
        try:
            key_item_ref, key_version_ref = self._workspace_key(
                connection, workspace_ref
            )
            token_hash = self.crypto_backend.blind_index(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                normalized_term=normalized,
            )
            rows = connection.execute(
                "SELECT s.record_ref FROM eco_search_tokens s "
                "JOIN eco_records r ON r.workspace_ref=s.workspace_ref AND r.record_ref=s.record_ref "
                "WHERE s.workspace_ref=? AND s.token_hash=? AND r.archived=0 "
                "ORDER BY s.record_ref",
                (workspace_ref, token_hash),
            ).fetchall()
            return tuple(row["record_ref"] for row in rows)
        finally:
            connection.close()

    def retention_candidates(
        self, *, workspace_ref: str, as_of: str
    ) -> tuple[str, ...]:
        """Return archived, expired safe refs without performing deletion."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        try:
            parsed = datetime.fromisoformat(as_of)
        except ValueError as exc:
            raise ValueError("ECO_RETENTION_TIMESTAMP_INVALID") from exc
        if parsed.tzinfo is None:
            raise ValueError("ECO_RETENTION_TIMESTAMP_TIMEZONE_REQUIRED")
        connection = self._connect()
        try:
            self._workspace_key(connection, workspace_ref)
            rows = connection.execute(
                "SELECT record_ref FROM eco_records WHERE workspace_ref = ? "
                "AND archived = 1 AND expires_at IS NOT NULL "
                "AND julianday(expires_at) <= julianday(?) "
                "ORDER BY record_ref",
                (workspace_ref, as_of),
            ).fetchall()
            return tuple(row["record_ref"] for row in rows)
        finally:
            connection.close()

    def rebuild_search(self, *, workspace_ref: str) -> str:
        """Rebuild one workspace's blind index from encrypted record envelopes."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            key_item_ref, key_version_ref = self._workspace_key(
                connection, workspace_ref
            )
            rows = connection.execute(
                "SELECT record_ref, version, key_version_ref, ciphertext "
                "FROM eco_records WHERE workspace_ref = ? ORDER BY record_ref",
                (workspace_ref,),
            ).fetchall()
            rebuilt: list[tuple[str, str]] = []
            for row in rows:
                plaintext = self.crypto_backend.decrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=row["key_version_ref"],
                    ciphertext=row["ciphertext"],
                    aad=_record_aad(
                        workspace_ref=workspace_ref,
                        record_ref=row["record_ref"],
                        key_version_ref=row["key_version_ref"],
                        version=row["version"],
                    ),
                )
                envelope = json.loads(plaintext)
                terms = (
                    envelope.get("search_terms") if isinstance(envelope, dict) else None
                )
                if not isinstance(terms, list) or not all(
                    isinstance(term, str) for term in terms
                ):
                    raise EcosystemLocalDataError("ECO_PRIVATE_PAYLOAD_INVALID")
                for term in _normalized_terms(terms):
                    rebuilt.append(
                        (
                            row["record_ref"],
                            self.crypto_backend.blind_index(
                                key_item_ref=key_item_ref,
                                key_version_ref=key_version_ref,
                                normalized_term=term,
                            ),
                        )
                    )
            connection.execute(
                "DELETE FROM eco_search_tokens WHERE workspace_ref = ?",
                (workspace_ref,),
            )
            connection.executemany(
                "INSERT INTO eco_search_tokens VALUES (?, ?, ?)",
                (
                    (workspace_ref, record_ref, token_hash)
                    for record_ref, token_hash in rebuilt
                ),
            )
            connection.commit()
            return _stable_ref(
                "search-rebuild-receipt-ref:ecosystem",
                {
                    "workspace_ref": workspace_ref,
                    "record_count": len(rows),
                    "search_entry_count": len(rebuilt),
                },
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def rotate_workspace_key(
        self, *, workspace_ref: str, new_key_version_ref: str
    ) -> str:
        """Atomically re-encrypt one workspace and rebuild its blind index."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(new_key_version_ref, field_name="new_key_version_ref")
        connection = self._connect()
        new_key_created = False
        committed = False
        old_key_version_ref = ""
        key_item_ref = ""
        try:
            connection.execute("BEGIN IMMEDIATE")
            key_item_ref, old_key_version_ref = self._workspace_key(
                connection, workspace_ref
            )
            if old_key_version_ref == new_key_version_ref:
                raise EcosystemConflict("ECO_KEY_VERSION_REUSE_DENIED")
            self.crypto_backend.create(
                key_item_ref=key_item_ref, key_version_ref=new_key_version_ref
            )
            new_key_created = True
            rows = connection.execute(
                "SELECT record_ref, version, ciphertext FROM eco_records "
                "WHERE workspace_ref = ? ORDER BY record_ref",
                (workspace_ref,),
            ).fetchall()
            rebuilt: list[tuple[str, str]] = []
            for row in rows:
                plaintext = self.crypto_backend.decrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=old_key_version_ref,
                    ciphertext=row["ciphertext"],
                    aad=_record_aad(
                        workspace_ref=workspace_ref,
                        record_ref=row["record_ref"],
                        key_version_ref=old_key_version_ref,
                        version=row["version"],
                    ),
                )
                envelope = json.loads(plaintext)
                terms = (
                    envelope.get("search_terms") if isinstance(envelope, dict) else None
                )
                if not isinstance(terms, list) or not all(
                    isinstance(term, str) for term in terms
                ):
                    raise EcosystemLocalDataError("ECO_PRIVATE_PAYLOAD_INVALID")
                ciphertext = self.crypto_backend.encrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=new_key_version_ref,
                    plaintext=plaintext,
                    aad=_record_aad(
                        workspace_ref=workspace_ref,
                        record_ref=row["record_ref"],
                        key_version_ref=new_key_version_ref,
                        version=row["version"],
                    ),
                )
                connection.execute(
                    "UPDATE eco_records SET key_version_ref = ?, ciphertext = ?, "
                    "updated_at = ? WHERE workspace_ref = ? AND record_ref = ?",
                    (
                        new_key_version_ref,
                        ciphertext,
                        _utc_now(),
                        workspace_ref,
                        row["record_ref"],
                    ),
                )
                for term in _normalized_terms(terms):
                    rebuilt.append(
                        (
                            row["record_ref"],
                            self.crypto_backend.blind_index(
                                key_item_ref=key_item_ref,
                                key_version_ref=new_key_version_ref,
                                normalized_term=term,
                            ),
                        )
                    )
            connection.execute(
                "DELETE FROM eco_search_tokens WHERE workspace_ref = ?",
                (workspace_ref,),
            )
            connection.executemany(
                "INSERT INTO eco_search_tokens VALUES (?, ?, ?)",
                (
                    (workspace_ref, record_ref, token_hash)
                    for record_ref, token_hash in rebuilt
                ),
            )
            connection.execute(
                "UPDATE eco_workspaces SET key_version_ref = ? WHERE workspace_ref = ?",
                (new_key_version_ref, workspace_ref),
            )
            connection.commit()
            committed = True
        except Exception:
            connection.rollback()
            if new_key_created and not committed:
                self.crypto_backend.delete(
                    key_item_ref=key_item_ref, key_version_ref=new_key_version_ref
                )
            raise
        finally:
            connection.close()
        old_key_delete_receipt = self.crypto_backend.delete(
            key_item_ref=key_item_ref, key_version_ref=old_key_version_ref
        )
        return _stable_ref(
            "key-rotation-receipt-ref:ecosystem",
            {
                "workspace_ref": workspace_ref,
                "new_key_version_ref": new_key_version_ref,
                "old_key_delete_receipt": old_key_delete_receipt,
            },
        )

    def integrity_check(self) -> IntegrityReport:
        connection = self._connect()
        try:
            self._validate_schema(connection)
            result = connection.execute("PRAGMA quick_check").fetchone()[0]
            if result != "ok":
                raise EcosystemLocalDataError("ECO_DATABASE_INTEGRITY_FAILED")
            orphan_count = connection.execute(
                "SELECT COUNT(*) FROM eco_search_tokens s LEFT JOIN eco_records r "
                "ON r.workspace_ref=s.workspace_ref AND r.record_ref=s.record_ref "
                "WHERE r.record_ref IS NULL"
            ).fetchone()[0]
            if orphan_count:
                raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED")
            records = connection.execute(
                "SELECT * FROM eco_records ORDER BY workspace_ref, record_ref"
            ).fetchall()
            expected_tokens: set[tuple[str, str, str]] = set()
            workspace_keys: dict[str, tuple[str, str]] = {}
            for row in records:
                key_item_ref, current_key_version_ref = workspace_keys.setdefault(
                    row["workspace_ref"],
                    self._workspace_key(connection, row["workspace_ref"]),
                )
                if row["key_version_ref"] != current_key_version_ref:
                    raise EcosystemLocalDataError("ECO_RECORD_KEY_VERSION_STALE")
                plaintext = self.crypto_backend.decrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=row["key_version_ref"],
                    ciphertext=row["ciphertext"],
                    aad=_record_aad(
                        workspace_ref=row["workspace_ref"],
                        record_ref=row["record_ref"],
                        key_version_ref=row["key_version_ref"],
                        version=row["version"],
                    ),
                )
                envelope = json.loads(plaintext)
                if not isinstance(envelope, dict) or not isinstance(
                    envelope.get("search_terms"), list
                ):
                    raise EcosystemLocalDataError("ECO_PRIVATE_PAYLOAD_INVALID")
                for term in _normalized_terms(envelope["search_terms"]):
                    expected_tokens.add(
                        (
                            row["workspace_ref"],
                            row["record_ref"],
                            self.crypto_backend.blind_index(
                                key_item_ref=key_item_ref,
                                key_version_ref=current_key_version_ref,
                                normalized_term=term,
                            ),
                        )
                    )
            actual_tokens = {
                tuple(row)
                for row in connection.execute(
                    "SELECT workspace_ref, record_ref, token_hash FROM eco_search_tokens"
                )
            }
            if actual_tokens != expected_tokens:
                raise EcosystemLocalDataError("ECO_SEARCH_INDEX_INTEGRITY_FAILED")
            workspace_count = connection.execute(
                "SELECT COUNT(*) FROM eco_workspaces"
            ).fetchone()[0]
            record_count = len(records)
            search_count = connection.execute(
                "SELECT COUNT(*) FROM eco_search_tokens"
            ).fetchone()[0]
            report_ref = _stable_ref(
                "integrity-report-ref:ecosystem",
                {
                    "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
                    "workspace_count": workspace_count,
                    "record_count": record_count,
                    "search_count": search_count,
                    "orphan_count": orphan_count,
                },
            )
            return IntegrityReport(
                schema_ref=ECO_LOCAL_DATA_SCHEMA_REF,
                status="ok",
                workspace_count=workspace_count,
                record_count=record_count,
                search_entry_count=search_count,
                orphan_count=orphan_count,
                report_ref=report_ref,
            )
        finally:
            connection.close()

    def create_backup(
        self,
        *,
        destination: Path,
        backup_ref: str,
        key_item_ref: str,
        key_version_ref: str,
    ) -> BackupReceipt:
        _validate_ref(backup_ref, field_name="backup_ref")
        _validate_ref(key_item_ref, field_name="key_item_ref")
        _validate_ref(key_version_ref, field_name="key_version_ref")
        if not destination.is_absolute() or destination.exists():
            raise ValueError("ECO_BACKUP_DESTINATION_INVALID")
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.crypto_backend.probe(
            key_item_ref=key_item_ref, key_version_ref=key_version_ref
        )
        with tempfile.TemporaryDirectory(dir=destination.parent) as stage_dir:
            snapshot = Path(stage_dir) / "snapshot.sqlite3"
            source = self._connect()
            target = sqlite3.connect(snapshot)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
            check = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
            try:
                if check.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise EcosystemLocalDataError("ECO_BACKUP_INTEGRITY_FAILED")
            finally:
                check.close()
            plaintext = snapshot.read_bytes()
            header = _canonical_json(
                {
                    "backup_ref": backup_ref,
                    "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
                    "key_item_ref": key_item_ref,
                    "key_version_ref": key_version_ref,
                }
            )
            ciphertext = self.crypto_backend.encrypt(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                plaintext=plaintext,
                aad=header,
            )
            container = (
                _BACKUP_MAGIC + struct.pack(">I", len(header)) + header + ciphertext
            )
            stage = Path(stage_dir) / "backup.stage"
            descriptor = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                view = memoryview(container)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise EcosystemLocalDataError("ECO_BACKUP_WRITE_FAILED")
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(stage, destination)
            os.chmod(destination, 0o600)
        fingerprint = hashlib.sha256(container).hexdigest()
        return BackupReceipt(
            backup_ref=backup_ref,
            schema_ref=ECO_LOCAL_DATA_SCHEMA_REF,
            ciphertext_fingerprint_ref=f"ciphertext-fingerprint-ref:sha256:{fingerprint}",
            byte_count=len(container),
        )

    def restore_preview(self, *, backup_path: Path) -> RestorePreview:
        header, plaintext = self._open_backup(backup_path)
        with tempfile.TemporaryDirectory() as stage_dir:
            snapshot = Path(stage_dir) / "preview.sqlite3"
            snapshot.write_bytes(plaintext)
            connection = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
            try:
                if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise EcosystemLocalDataError("ECO_BACKUP_INTEGRITY_FAILED")
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version != ECO_LOCAL_DATA_SCHEMA_VERSION:
                    raise EcosystemLocalDataError("ECO_BACKUP_SCHEMA_UNSUPPORTED")
                workspaces = connection.execute(
                    "SELECT COUNT(*) FROM eco_workspaces"
                ).fetchone()[0]
                records = connection.execute(
                    "SELECT COUNT(*) FROM eco_records"
                ).fetchone()[0]
            finally:
                connection.close()
        return RestorePreview(
            backup_ref=header["backup_ref"],
            schema_ref=header["schema_ref"],
            integrity_status="ok",
            workspace_count=workspaces,
            record_count=records,
        )

    def restore_to_new(self, *, backup_path: Path, destination: Path) -> str:
        """Restore a verified snapshot to a new path; existing stores are untouched."""

        if not destination.is_absolute() or destination.exists():
            raise ValueError("ECO_RESTORE_DESTINATION_INVALID")
        preview = self.restore_preview(backup_path=backup_path)
        _, plaintext = self._open_backup(backup_path)
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        stage = destination.with_name(
            f".{destination.name}.stage-{secrets.token_hex(8)}"
        )
        descriptor = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            view = memoryview(plaintext)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise EcosystemLocalDataError("ECO_RESTORE_WRITE_FAILED")
                view = view[written:]
            os.fsync(descriptor)
        except Exception:
            os.close(descriptor)
            stage.unlink(missing_ok=True)
            raise
        else:
            os.close(descriptor)
        os.replace(stage, destination)
        os.chmod(destination, 0o600)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return _stable_ref(
            "restore-receipt-ref:ecosystem",
            {
                "backup_ref": preview.backup_ref,
                "schema_ref": preview.schema_ref,
                "record_count": preview.record_count,
            },
        )

    def _open_backup(self, backup_path: Path) -> tuple[dict[str, str], bytes]:
        if backup_path.stat().st_size > _MAX_BACKUP_BYTES:
            raise EcosystemLocalDataError("ECO_BACKUP_SIZE_LIMIT_EXCEEDED")
        container = backup_path.read_bytes()
        prefix = len(_BACKUP_MAGIC)
        if not container.startswith(_BACKUP_MAGIC) or len(container) < prefix + 4:
            raise EcosystemLocalDataError("ECO_BACKUP_CONTAINER_INVALID")
        header_size = struct.unpack(">I", container[prefix : prefix + 4])[0]
        if not 0 < header_size <= 4096 or len(container) <= prefix + 4 + header_size:
            raise EcosystemLocalDataError("ECO_BACKUP_CONTAINER_INVALID")
        header_bytes = container[prefix + 4 : prefix + 4 + header_size]
        try:
            header = json.loads(header_bytes)
            if set(header) != {
                "backup_ref",
                "schema_ref",
                "key_item_ref",
                "key_version_ref",
            }:
                raise ValueError
            for key, value in header.items():
                _validate_ref(value, field_name=key)
            if header["schema_ref"] != ECO_LOCAL_DATA_SCHEMA_REF:
                raise EcosystemLocalDataError("ECO_BACKUP_SCHEMA_UNSUPPORTED")
            plaintext = self.crypto_backend.decrypt(
                key_item_ref=header["key_item_ref"],
                key_version_ref=header["key_version_ref"],
                ciphertext=container[prefix + 4 + header_size :],
                aad=header_bytes,
            )
        except EcosystemLocalDataError:
            raise
        except Exception as exc:
            raise EcosystemLocalDataError("ECO_BACKUP_CONTAINER_INVALID") from exc
        return header, plaintext


class JsonCompatibilityReader:
    """Read-only legacy JSON inventory preview; never writes or interprets records."""

    source_format_ref = "source-format-ref:legacy-json"

    def preview(self, source_path: Path) -> MigrationPreview:
        raw = source_path.read_bytes()
        try:
            payload = json.loads(raw)
        except Exception as exc:
            raise EcosystemLocalDataError("ECO_MIGRATION_SOURCE_INVALID") from exc
        if isinstance(payload, list):
            count = len(payload)
        elif isinstance(payload, dict):
            count = len(payload)
        else:
            raise EcosystemLocalDataError("ECO_MIGRATION_SOURCE_INVALID")
        fingerprint = hashlib.sha256(raw).hexdigest()
        fingerprint_ref = f"source-fingerprint-ref:sha256:{fingerprint}"
        return MigrationPreview(
            source_fingerprint_ref=fingerprint_ref,
            source_format_ref=self.source_format_ref,
            candidate_count=count,
            destination_schema_ref=ECO_LOCAL_DATA_SCHEMA_REF,
            preview_ref=_stable_ref(
                "migration-preview-ref:ecosystem",
                {
                    "source_fingerprint_ref": fingerprint_ref,
                    "source_format_ref": self.source_format_ref,
                    "candidate_count": count,
                    "destination_schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
                },
            ),
        )
