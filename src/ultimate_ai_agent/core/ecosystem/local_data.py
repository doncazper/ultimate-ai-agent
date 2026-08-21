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
from threading import RLock
from typing import Any, Callable, Iterable, Literal, Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.safe_contract_text import validate_safe_contract_text_shape
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_LOCAL_DATA_SCHEMA_VERSION = 1
ECO_LOCAL_DATA_SCHEMA_REF = "schema-ref:ecosystem-local-data:v1"
_BACKUP_MAGIC = b"UAA-ECO-LOCAL-BACKUP-V1\x00"
_NONCE_BYTES = 12
ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES = 1024 * 1024
_MAX_PRIVATE_PAYLOAD_BYTES = ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES
_MAX_BACKUP_BYTES = 512 * 1024 * 1024
_MAX_MIGRATION_SOURCE_BYTES = 64 * 1024 * 1024
_EXPECTED_SCHEMA_SHAPE_FINGERPRINT = (
    "6d0b5cced6cb8ece977f7670a96a914a0792662b96037f509a8bb7f7ad7e53d7"
)
_SAFE_REF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
)
_SCOPED_MUTATION_ACTIONS = {
    "ecosystem.crm.apply": (
        "module-ref:crm",
        frozenset({"record-kind-ref:crm-private-portfolio"}),
    ),
    "ecosystem.calendar.apply": (
        "module-ref:calendar",
        frozenset({"record-kind-ref:calendar-set"}),
    ),
    "ecosystem.boards.apply": (
        "module-ref:boards",
        frozenset(
            {
                "record-kind-ref:canonical-board",
                "record-kind-ref:board-template",
            }
        ),
    ),
    "ecosystem.tasks.apply": (
        "module-ref:tasks",
        frozenset(
            {
                "record-kind-ref:canonical-task",
                "record-kind-ref:task-occurrence",
            }
        ),
    ),
    # Exact compatibility lane for ECO-001 records that used the Tasks module
    # before ECO-002 reserved it for canonical Task kinds. This keeps those
    # records maintainable without reopening the generic mutation action.
    "ecosystem.tasks.legacy_local_data.apply": (
        "module-ref:tasks",
        frozenset({"record-kind-ref:task"}),
    ),
}
_REPOSITORY_ONLY_MUTATION_ACTIONS = frozenset(
    {
        "ecosystem.boards.apply",
        "ecosystem.calendar.apply",
        "ecosystem.crm.apply",
        "ecosystem.tasks.apply",
    }
)
_EXISTING_ONLY_MUTATION_ACTIONS = frozenset({"ecosystem.tasks.legacy_local_data.apply"})
_DOMAIN_VALIDATION_TOKEN = object()


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


class LocalDataPathResolver(Protocol):
    """Trusted safe-ref to local-path boundary for backup and restore writes."""

    def resolve(self, *, destination_ref: str) -> Path: ...


class InMemoryLocalDataPathResolver:
    """Test-only immutable path binding; not a production allowlist."""

    def __init__(self) -> None:
        self._paths: dict[str, Path] = {}

    def bind(self, *, destination_ref: str, destination: Path) -> None:
        resolved = destination.resolve()
        existing = self._paths.setdefault(destination_ref, resolved)
        if existing != resolved:
            raise EcosystemConflict("ECO_DESTINATION_REF_CONFLICT")

    def resolve(self, *, destination_ref: str) -> Path:
        try:
            return self._paths[destination_ref]
        except KeyError as exc:
            raise EcosystemLocalDataError("ECO_DESTINATION_REF_UNRESOLVED") from exc


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
class KeyRotationReceipt:
    receipt_ref: str
    cleanup_ref: str
    cleanup_pending: bool
    replayed: bool = False


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
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("ECO_PRIVATE_PAYLOAD_JSON_REQUIRED") from exc


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value)).hexdigest()
    return f"{prefix}:{digest}"


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def _canonical_utc_timestamp(
    value: str, *, invalid_code: str, timezone_code: str
) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(invalid_code) from exc
    if parsed.tzinfo is None:
        raise ValueError(timezone_code)
    return (
        parsed.astimezone(timezone.utc)
        .isoformat(timespec="auto")
        .replace("+00:00", "Z")
    )


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


def _receipt_aad(
    *, workspace_ref: str, idempotency_ref: str, key_version_ref: str
) -> bytes:
    return _canonical_json(
        {
            "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
            "workspace_ref": workspace_ref,
            "idempotency_ref": idempotency_ref,
            "key_version_ref": key_version_ref,
            "envelope_ref": "envelope-ref:ecosystem-uow-request:v1",
        }
    )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish_new_file(stage: Path, destination: Path, *, exists_code: str) -> None:
    """Atomically publish a complete staged file without replacing any target."""

    try:
        os.link(stage, destination, follow_symlinks=False)
    except FileExistsError as exc:
        raise EcosystemConflict(exists_code) from exc
    _fsync_directory(destination.parent)
    stage.unlink()
    _fsync_directory(destination.parent)


class EcosystemLocalDataPlatform:
    """Versioned SQLite data plane with an encrypted private-value boundary."""

    def __init__(
        self,
        *,
        database_path: Path,
        crypto_backend: LocalDataCryptoBackend,
        approval_authority: LocalApprovalAuthority,
        path_resolver: LocalDataPathResolver,
        fault_hook: Callable[[str], None] | None = None,
    ) -> None:
        if not database_path.is_absolute() or database_path == Path(
            database_path.anchor
        ):
            raise ValueError("ECO_DATABASE_PATH_UNSAFE")
        self.database_path = database_path
        self.crypto_backend = crypto_backend
        self.approval_authority = approval_authority
        self.path_resolver = path_resolver
        self._key_lifecycle_lock = RLock()
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
                        key_version_ref TEXT NOT NULL,
                        request_ciphertext BLOB NOT NULL,
                        approval_ref TEXT NOT NULL,
                        receipt_ref TEXT NOT NULL,
                        operation_receipt_refs_json TEXT NOT NULL,
                        receipt_authenticator_ref TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (workspace_ref, idempotency_ref),
                        FOREIGN KEY (workspace_ref) REFERENCES eco_workspaces(workspace_ref)
                    );
                    CREATE TABLE IF NOT EXISTS eco_record_tombstones (
                        workspace_ref TEXT NOT NULL,
                        record_ref TEXT NOT NULL,
                        deleted_version INTEGER NOT NULL CHECK(deleted_version >= 1),
                        deleted_at TEXT NOT NULL,
                        PRIMARY KEY (workspace_ref, record_ref),
                        FOREIGN KEY (workspace_ref) REFERENCES eco_workspaces(workspace_ref)
                    );
                    CREATE TABLE IF NOT EXISTS eco_key_cleanup (
                        workspace_ref TEXT NOT NULL,
                        old_key_version_ref TEXT NOT NULL,
                        new_key_version_ref TEXT NOT NULL,
                        cleanup_ref TEXT NOT NULL UNIQUE,
                        completed_at TEXT,
                        PRIMARY KEY (workspace_ref, old_key_version_ref, new_key_version_ref),
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
                    """
                )
            self._validate_schema(connection)
            connection.commit()
            if self._fault_hook:
                self._fault_hook("schema-ready")
        except Exception:
            connection.rollback()
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
            "eco_record_tombstones",
            "eco_schema_migrations",
            "eco_search_tokens",
            "eco_key_cleanup",
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
        expected_columns = {
            "eco_workspaces": (
                ("workspace_ref", "TEXT", 0, 1),
                ("key_item_ref", "TEXT", 1, 0),
                ("key_version_ref", "TEXT", 1, 0),
                ("created_at", "TEXT", 1, 0),
            ),
            "eco_schema_migrations": (
                ("schema_version", "INTEGER", 0, 1),
                ("schema_ref", "TEXT", 1, 0),
                ("applied_at", "TEXT", 1, 0),
            ),
            "eco_records": (
                ("workspace_ref", "TEXT", 1, 1),
                ("module_ref", "TEXT", 1, 0),
                ("record_ref", "TEXT", 1, 2),
                ("record_kind_ref", "TEXT", 1, 0),
                ("safe_summary_ref", "TEXT", 1, 0),
                ("version", "INTEGER", 1, 0),
                ("key_version_ref", "TEXT", 1, 0),
                ("ciphertext", "BLOB", 1, 0),
                ("archived", "INTEGER", 1, 0),
                ("retention_ref", "TEXT", 1, 0),
                ("expires_at", "TEXT", 0, 0),
                ("updated_at", "TEXT", 1, 0),
            ),
            "eco_search_tokens": (
                ("workspace_ref", "TEXT", 1, 1),
                ("record_ref", "TEXT", 1, 2),
                ("token_hash", "TEXT", 1, 3),
            ),
            "eco_uow_receipts": (
                ("workspace_ref", "TEXT", 1, 1),
                ("idempotency_ref", "TEXT", 1, 2),
                ("request_fingerprint_ref", "TEXT", 1, 0),
                ("key_version_ref", "TEXT", 1, 0),
                ("request_ciphertext", "BLOB", 1, 0),
                ("approval_ref", "TEXT", 1, 0),
                ("receipt_ref", "TEXT", 1, 0),
                ("operation_receipt_refs_json", "TEXT", 1, 0),
                ("receipt_authenticator_ref", "TEXT", 1, 0),
                ("created_at", "TEXT", 1, 0),
            ),
            "eco_events": (
                ("event_ref", "TEXT", 0, 1),
                ("workspace_ref", "TEXT", 1, 0),
                ("record_ref", "TEXT", 1, 0),
                ("operation_ref", "TEXT", 1, 0),
                ("event_kind_ref", "TEXT", 1, 0),
                ("version", "INTEGER", 1, 0),
                ("created_at", "TEXT", 1, 0),
            ),
            "eco_record_tombstones": (
                ("workspace_ref", "TEXT", 1, 1),
                ("record_ref", "TEXT", 1, 2),
                ("deleted_version", "INTEGER", 1, 0),
                ("deleted_at", "TEXT", 1, 0),
            ),
            "eco_key_cleanup": (
                ("workspace_ref", "TEXT", 1, 1),
                ("old_key_version_ref", "TEXT", 1, 2),
                ("new_key_version_ref", "TEXT", 1, 3),
                ("cleanup_ref", "TEXT", 1, 0),
                ("completed_at", "TEXT", 0, 0),
            ),
        }
        for table, expected in expected_columns.items():
            actual = tuple(
                (row[1], row[2].upper(), row[3], row[5])
                for row in connection.execute(f"PRAGMA table_info({table})")
            )
            if actual != expected:
                raise EcosystemLocalDataError("ECO_SCHEMA_SHAPE_INVALID")
        expected_foreign_keys = {
            "eco_records": {
                ("workspace_ref", "workspace_ref", "eco_workspaces", "NO ACTION")
            },
            "eco_search_tokens": {
                ("workspace_ref", "workspace_ref", "eco_records", "CASCADE"),
                ("record_ref", "record_ref", "eco_records", "CASCADE"),
            },
            "eco_uow_receipts": {
                ("workspace_ref", "workspace_ref", "eco_workspaces", "NO ACTION")
            },
            "eco_events": {
                ("workspace_ref", "workspace_ref", "eco_workspaces", "NO ACTION")
            },
            "eco_record_tombstones": {
                ("workspace_ref", "workspace_ref", "eco_workspaces", "NO ACTION")
            },
            "eco_key_cleanup": {
                ("workspace_ref", "workspace_ref", "eco_workspaces", "NO ACTION")
            },
        }
        for table, expected in expected_foreign_keys.items():
            actual = {
                (row[3], row[4], row[2], row[6])
                for row in connection.execute(f"PRAGMA foreign_key_list({table})")
            }
            if actual != expected:
                raise EcosystemLocalDataError("ECO_SCHEMA_SHAPE_INVALID")
        canonical_shape = "\n".join(
            f"{row[0]}\x00{''.join(str(row[1]).split()).lower()}"
            for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' "
                "AND name LIKE 'eco_%' ORDER BY name"
            )
        )
        shape_fingerprint = hashlib.sha256(canonical_shape.encode()).hexdigest()
        if not hmac.compare_digest(
            shape_fingerprint, _EXPECTED_SCHEMA_SHAPE_FINGERPRINT
        ):
            raise EcosystemLocalDataError("ECO_SCHEMA_SHAPE_INVALID")
        migration = connection.execute(
            "SELECT schema_ref FROM eco_schema_migrations WHERE schema_version = ?",
            (ECO_LOCAL_DATA_SCHEMA_VERSION,),
        ).fetchone()
        if migration is None or migration[0] != ECO_LOCAL_DATA_SCHEMA_REF:
            raise EcosystemLocalDataError("ECO_SCHEMA_MIGRATION_LEDGER_INVALID")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED")

    def _authorize(
        self,
        approval: ApprovalValidationRequest,
        *,
        action: str,
        resource_refs: tuple[str, ...],
    ) -> str:
        if (
            approval.requested_action != action
            or set(approval.resource_refs) != set(resource_refs)
            or approval.subject_type != "kernel_task"
            or approval.risk_level != "high"
            or approval.data_classification.classification != "user_private"
        ):
            raise EcosystemLocalDataError("ECO_APPROVAL_SCOPE_INVALID")
        decision = self.approval_authority.validate_at_trusted_time(
            approval,
            current_time=datetime.now(timezone.utc),
        )
        if not decision.allowed:
            raise EcosystemLocalDataError("ECO_APPROVAL_REQUIRED")
        return approval.approval_ref

    def create_workspace(
        self,
        *,
        workspace_ref: str,
        approval: ApprovalValidationRequest,
        key_version_ref: str = "key-version-ref:v1",
    ) -> str:
        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(key_version_ref, field_name="key_version_ref")
        key_item_ref = _stable_ref("key-item-ref:ecosystem", workspace_ref)
        with self.approval_authority.hold_validation_lock():
            self._authorize(
                approval,
                action="ecosystem.local_data.create_workspace",
                resource_refs=(workspace_ref, key_version_ref),
            )
            connection = self._connect()
            created_key = False
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT key_item_ref, key_version_ref FROM eco_workspaces WHERE workspace_ref = ?",
                    (workspace_ref,),
                ).fetchone()
                if row is not None:
                    if (row["key_item_ref"], row["key_version_ref"]) != (
                        key_item_ref,
                        key_version_ref,
                    ):
                        raise EcosystemConflict("ECO_WORKSPACE_KEY_CONFLICT")
                    receipt_ref = self.crypto_backend.probe(
                        key_item_ref=key_item_ref,
                        key_version_ref=key_version_ref,
                    )
                    connection.rollback()
                    return receipt_ref
                receipt_ref = self.crypto_backend.create(
                    key_item_ref=key_item_ref, key_version_ref=key_version_ref
                )
                created_key = True
                connection.execute(
                    "INSERT INTO eco_workspaces VALUES (?, ?, ?, ?)",
                    (workspace_ref, key_item_ref, key_version_ref, _utc_now()),
                )
                connection.commit()
                return receipt_ref
            except Exception:
                connection.rollback()
                if created_key:
                    self.crypto_backend.delete(
                        key_item_ref=key_item_ref,
                        key_version_ref=key_version_ref,
                    )
                raise
            finally:
                connection.close()

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
        approval: ApprovalValidationRequest,
        requested_action: str = "ecosystem.local_data.apply",
        request_context_ref: str | None = None,
        _domain_validation_token: object | None = None,
    ) -> UnitOfWorkReceipt:
        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(idempotency_ref, field_name="idempotency_ref")
        _validate_ref(requested_action, field_name="requested_action")
        if request_context_ref is not None:
            _validate_ref(request_context_ref, field_name="request_context_ref")
        if not operations or len(operations) > 64:
            raise ValueError("ECO_UOW_OPERATION_COUNT_INVALID")
        operation_refs = [
            _validate_ref(item.operation_ref, field_name="operation_ref")
            for item in operations
        ]
        if len(operation_refs) != len(set(operation_refs)):
            raise ValueError("ECO_UOW_DUPLICATE_OPERATION_REF")
        resource_refs = tuple(
            dict.fromkeys(
                (workspace_ref, idempotency_ref)
                + tuple(operation_refs)
                + tuple(operation.record_ref for operation in operations)
            )
        )
        with self.approval_authority.hold_validation_lock():
            approval_ref = self._authorize(
                approval,
                action=requested_action,
                resource_refs=resource_refs,
            )
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                key_item_ref, key_version_ref = self._workspace_key(
                    connection, workspace_ref
                )
                request_material = self._request_material(
                    workspace_ref,
                    operations,
                    requested_action=requested_action,
                    request_context_ref=request_context_ref,
                )
                fingerprint_ref = self._request_fingerprint(
                    key_item_ref=key_item_ref,
                    key_version_ref=key_version_ref,
                    request_material=request_material,
                )
                replay = connection.execute(
                    "SELECT * FROM eco_uow_receipts WHERE workspace_ref = ? AND idempotency_ref = ?",
                    (workspace_ref, idempotency_ref),
                ).fetchone()
                if replay is not None:
                    previous_material = self.crypto_backend.decrypt(
                        key_item_ref=key_item_ref,
                        key_version_ref=replay["key_version_ref"],
                        ciphertext=replay["request_ciphertext"],
                        aad=_receipt_aad(
                            workspace_ref=workspace_ref,
                            idempotency_ref=idempotency_ref,
                            key_version_ref=replay["key_version_ref"],
                        ),
                    )
                    expected_authenticator = self._receipt_authenticator(
                        key_item_ref=key_item_ref,
                        key_version_ref=replay["key_version_ref"],
                        workspace_ref=workspace_ref,
                        idempotency_ref=idempotency_ref,
                        request_fingerprint_ref=replay["request_fingerprint_ref"],
                        request_ciphertext=replay["request_ciphertext"],
                        approval_ref=replay["approval_ref"],
                        receipt_ref=replay["receipt_ref"],
                        operation_receipt_refs_json=replay[
                            "operation_receipt_refs_json"
                        ],
                        created_at=replay["created_at"],
                    )
                    if not hmac.compare_digest(
                        replay["receipt_authenticator_ref"], expected_authenticator
                    ):
                        raise EcosystemLocalDataError(
                            "ECO_UOW_RECEIPT_INTEGRITY_FAILED"
                        )
                    if not hmac.compare_digest(previous_material, request_material):
                        raise EcosystemConflict("ECO_IDEMPOTENCY_REPLAY_CONFLICT")
                    connection.rollback()
                    return UnitOfWorkReceipt(
                        workspace_ref=workspace_ref,
                        idempotency_ref=idempotency_ref,
                        request_fingerprint_ref=replay["request_fingerprint_ref"],
                        receipt_ref=replay["receipt_ref"],
                        operation_receipt_refs=tuple(
                            json.loads(replay["operation_receipt_refs_json"])
                        ),
                        replayed=True,
                    )
                self._validate_requested_action_scope(
                    connection,
                    workspace_ref=workspace_ref,
                    requested_action=requested_action,
                    operations=operations,
                )
                if (
                    requested_action in _REPOSITORY_ONLY_MUTATION_ACTIONS
                    and _domain_validation_token is not _DOMAIN_VALIDATION_TOKEN
                ):
                    raise EcosystemLocalDataError(
                        "ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION"
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
                        "approval_ref": approval_ref,
                        "operation_receipt_refs": receipts,
                    },
                )
                request_ciphertext = self.crypto_backend.encrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=key_version_ref,
                    plaintext=request_material,
                    aad=_receipt_aad(
                        workspace_ref=workspace_ref,
                        idempotency_ref=idempotency_ref,
                        key_version_ref=key_version_ref,
                    ),
                )
                operation_receipts_json = json.dumps(receipts, separators=(",", ":"))
                created_at = _utc_now()
                receipt_authenticator_ref = self._receipt_authenticator(
                    key_item_ref=key_item_ref,
                    key_version_ref=key_version_ref,
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    request_fingerprint_ref=fingerprint_ref,
                    request_ciphertext=request_ciphertext,
                    approval_ref=approval_ref,
                    receipt_ref=receipt_ref,
                    operation_receipt_refs_json=operation_receipts_json,
                    created_at=created_at,
                )
                connection.execute(
                    "INSERT INTO eco_uow_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        workspace_ref,
                        idempotency_ref,
                        fingerprint_ref,
                        key_version_ref,
                        request_ciphertext,
                        approval_ref,
                        receipt_ref,
                        operation_receipts_json,
                        receipt_authenticator_ref,
                        created_at,
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

    def _apply_registered_domain(
        self,
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operations: tuple[LocalMutation, ...],
        approval: ApprovalValidationRequest,
        requested_action: str,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        """Internal handoff for a domain repository after its invariant checks."""

        return self.apply(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operations=operations,
            approval=approval,
            requested_action=requested_action,
            request_context_ref=request_context_ref,
            _domain_validation_token=_DOMAIN_VALIDATION_TOKEN,
        )

    def replay_receipt(
        self,
        *,
        workspace_ref: str,
        idempotency_ref: str,
        resource_refs: tuple[str, ...],
        approval: ApprovalValidationRequest,
        requested_action: str,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt | None:
        """Return an exact durable replay without reconstructing stale payload state."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(idempotency_ref, field_name="idempotency_ref")
        _validate_ref(requested_action, field_name="requested_action")
        _validate_ref(request_context_ref, field_name="request_context_ref")
        validated_resources = tuple(
            dict.fromkeys(
                _validate_ref(resource_ref, field_name="resource_ref")
                for resource_ref in resource_refs
            )
        )
        with self.approval_authority.hold_validation_lock():
            self._authorize(
                approval,
                action=requested_action,
                resource_refs=validated_resources,
            )
            connection = self._connect()
            try:
                connection.execute("BEGIN")
                key_item_ref, _key_version_ref = self._workspace_key(
                    connection, workspace_ref
                )
                replay = connection.execute(
                    "SELECT * FROM eco_uow_receipts "
                    "WHERE workspace_ref = ? AND idempotency_ref = ?",
                    (workspace_ref, idempotency_ref),
                ).fetchone()
                if replay is None:
                    connection.rollback()
                    return None
                previous_material = self.crypto_backend.decrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=replay["key_version_ref"],
                    ciphertext=replay["request_ciphertext"],
                    aad=_receipt_aad(
                        workspace_ref=workspace_ref,
                        idempotency_ref=idempotency_ref,
                        key_version_ref=replay["key_version_ref"],
                    ),
                )
                expected_authenticator = self._receipt_authenticator(
                    key_item_ref=key_item_ref,
                    key_version_ref=replay["key_version_ref"],
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    request_fingerprint_ref=replay["request_fingerprint_ref"],
                    request_ciphertext=replay["request_ciphertext"],
                    approval_ref=replay["approval_ref"],
                    receipt_ref=replay["receipt_ref"],
                    operation_receipt_refs_json=replay["operation_receipt_refs_json"],
                    created_at=replay["created_at"],
                )
                if not hmac.compare_digest(
                    replay["receipt_authenticator_ref"], expected_authenticator
                ):
                    raise EcosystemLocalDataError("ECO_UOW_RECEIPT_INTEGRITY_FAILED")
                try:
                    material = json.loads(previous_material)
                except (TypeError, ValueError) as exc:
                    raise EcosystemLocalDataError(
                        "ECO_UOW_RECEIPT_REQUEST_INVALID"
                    ) from exc
                if (
                    not isinstance(material, dict)
                    or material.get("workspace_ref") != workspace_ref
                    or material.get("requested_action") != requested_action
                    or material.get("request_context_ref") != request_context_ref
                ):
                    raise EcosystemConflict("ECO_IDEMPOTENCY_REPLAY_CONFLICT")
                connection.rollback()
                return UnitOfWorkReceipt(
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    request_fingerprint_ref=replay["request_fingerprint_ref"],
                    receipt_ref=replay["receipt_ref"],
                    operation_receipt_refs=tuple(
                        json.loads(replay["operation_receipt_refs_json"])
                    ),
                    replayed=True,
                )
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _request_material(
        self,
        workspace_ref: str,
        operations: tuple[LocalMutation, ...],
        *,
        requested_action: str,
        request_context_ref: str | None = None,
    ) -> bytes:
        encoded: list[dict[str, Any]] = []
        for operation in operations:
            item = dict(vars(operation))
            if isinstance(operation, PutRecord):
                item["search_terms"] = _normalized_terms(operation.search_terms)
                if operation.expires_at is not None:
                    item["expires_at"] = _canonical_utc_timestamp(
                        operation.expires_at,
                        invalid_code="ECO_EXPIRY_TIMESTAMP_INVALID",
                        timezone_code="ECO_EXPIRY_TIMESTAMP_TIMEZONE_REQUIRED",
                    )
            item["operation_type"] = type(operation).__name__
            encoded.append(item)
        material: dict[str, Any] = {
            "workspace_ref": workspace_ref,
            "operations": encoded,
        }
        # Preserve exact replay compatibility for pre-ECO-002 receipts while
        # binding every non-default authority lane into new request material.
        if requested_action != "ecosystem.local_data.apply":
            material["requested_action"] = requested_action
        if request_context_ref is not None:
            material["request_context_ref"] = request_context_ref
        return _canonical_json(material)

    def _request_fingerprint(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        request_material: bytes,
    ) -> str:
        material_digest = hashlib.sha256(request_material).hexdigest()
        digest = self.crypto_backend.blind_index(
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            normalized_term=f"uow-request-v1:{material_digest}",
        )
        return f"request-fingerprint-ref:ecosystem-keyed:{digest}"

    def _receipt_authenticator(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        workspace_ref: str,
        idempotency_ref: str,
        request_fingerprint_ref: str,
        request_ciphertext: bytes,
        approval_ref: str,
        receipt_ref: str,
        operation_receipt_refs_json: str,
        created_at: str,
    ) -> str:
        material_digest = hashlib.sha256(
            _canonical_json(
                {
                    "workspace_ref": workspace_ref,
                    "idempotency_ref": idempotency_ref,
                    "request_fingerprint_ref": request_fingerprint_ref,
                    "key_version_ref": key_version_ref,
                    "request_ciphertext_sha256": hashlib.sha256(
                        request_ciphertext
                    ).hexdigest(),
                    "approval_ref": approval_ref,
                    "receipt_ref": receipt_ref,
                    "operation_receipt_refs_json": operation_receipt_refs_json,
                    "created_at": created_at,
                }
            )
        ).hexdigest()
        digest = self.crypto_backend.blind_index(
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            normalized_term=f"uow-receipt-v1:{material_digest}",
        )
        return f"receipt-authenticator-ref:ecosystem-keyed:{digest}"

    @staticmethod
    def _validate_requested_action_scope(
        connection: sqlite3.Connection,
        *,
        workspace_ref: str,
        requested_action: str,
        operations: tuple[LocalMutation, ...],
    ) -> None:
        if requested_action == "ecosystem.local_data.apply":
            protected_modules = {
                module_ref
                for module_ref, _record_kinds in _SCOPED_MUTATION_ACTIONS.values()
            }
            for operation in operations:
                if isinstance(operation, PutRecord):
                    row = connection.execute(
                        "SELECT module_ref FROM eco_records "
                        "WHERE workspace_ref = ? AND record_ref = ?",
                        (workspace_ref, operation.record_ref),
                    ).fetchone()
                    if operation.module_ref in protected_modules or (
                        row is not None and row["module_ref"] in protected_modules
                    ):
                        raise EcosystemLocalDataError(
                            "ECO_MUTATION_REQUIRES_DOMAIN_ACTION"
                        )
                    continue
                row = connection.execute(
                    "SELECT module_ref FROM eco_records "
                    "WHERE workspace_ref = ? AND record_ref = ?",
                    (workspace_ref, operation.record_ref),
                ).fetchone()
                if row is not None and row["module_ref"] in protected_modules:
                    raise EcosystemLocalDataError("ECO_MUTATION_REQUIRES_DOMAIN_ACTION")
            return
        scope = _SCOPED_MUTATION_ACTIONS.get(requested_action)
        if scope is None:
            raise EcosystemLocalDataError("ECO_MUTATION_ACTION_UNREGISTERED")
        module_ref, record_kind_refs = scope
        for operation in operations:
            if isinstance(operation, PutRecord):
                row = connection.execute(
                    "SELECT module_ref, record_kind_ref FROM eco_records "
                    "WHERE workspace_ref = ? AND record_ref = ?",
                    (workspace_ref, operation.record_ref),
                ).fetchone()
                if (
                    (
                        requested_action in _EXISTING_ONLY_MUTATION_ACTIONS
                        and row is None
                    )
                    or operation.module_ref != module_ref
                    or operation.record_kind_ref not in record_kind_refs
                    or (
                        row is not None
                        and (
                            row["module_ref"] != module_ref
                            or row["record_kind_ref"] not in record_kind_refs
                        )
                    )
                ):
                    raise EcosystemLocalDataError(
                        "ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
                    )
                continue
            row = connection.execute(
                "SELECT module_ref, record_kind_ref FROM eco_records "
                "WHERE workspace_ref = ? AND record_ref = ?",
                (workspace_ref, operation.record_ref),
            ).fetchone()
            if (
                row is None
                or row["module_ref"] != module_ref
                or row["record_kind_ref"] not in record_kind_refs
            ):
                raise EcosystemLocalDataError(
                    "ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
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
            connection.execute(
                "INSERT INTO eco_record_tombstones VALUES (?, ?, ?, ?)",
                (workspace_ref, operation.record_ref, next_version, _utc_now()),
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
        expires_at = (
            _canonical_utc_timestamp(
                operation.expires_at,
                invalid_code="ECO_EXPIRY_TIMESTAMP_INVALID",
                timezone_code="ECO_EXPIRY_TIMESTAMP_TIMEZONE_REQUIRED",
            )
            if operation.expires_at is not None
            else None
        )
        tombstone = connection.execute(
            "SELECT deleted_version FROM eco_record_tombstones "
            "WHERE workspace_ref = ? AND record_ref = ?",
            (workspace_ref, operation.record_ref),
        ).fetchone()
        if tombstone is not None:
            raise EcosystemConflict("ECO_DELETED_RECORD_REF_REUSE_DENIED")
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
            expires_at,
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
        with self._key_lifecycle_lock:
            return self._read_unlocked(
                workspace_ref=workspace_ref, record_ref=record_ref
            )

    def _read_unlocked(self, *, workspace_ref: str, record_ref: str) -> LocalRecord:
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
        with self._key_lifecycle_lock:
            return self._search_unlocked(workspace_ref=workspace_ref, term=term)

    def _search_unlocked(self, *, workspace_ref: str, term: str) -> tuple[str, ...]:
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
        canonical_as_of = _canonical_utc_timestamp(
            as_of,
            invalid_code="ECO_RETENTION_TIMESTAMP_INVALID",
            timezone_code="ECO_RETENTION_TIMESTAMP_TIMEZONE_REQUIRED",
        )
        connection = self._connect()
        try:
            self._workspace_key(connection, workspace_ref)
            rows = connection.execute(
                "SELECT record_ref FROM eco_records WHERE workspace_ref = ? "
                "AND archived = 1 AND expires_at IS NOT NULL "
                "AND julianday(expires_at) <= julianday(?) "
                "ORDER BY record_ref",
                (workspace_ref, canonical_as_of),
            ).fetchall()
            return tuple(row["record_ref"] for row in rows)
        finally:
            connection.close()

    def rebuild_search(
        self, *, workspace_ref: str, approval: ApprovalValidationRequest
    ) -> str:
        """Rebuild one workspace's blind index from encrypted record envelopes."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        with self.approval_authority.hold_validation_lock():
            self._authorize(
                approval,
                action="ecosystem.local_data.rebuild_search",
                resource_refs=(workspace_ref,),
            )
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
                        envelope.get("search_terms")
                        if isinstance(envelope, dict)
                        else None
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
        self,
        *,
        workspace_ref: str,
        new_key_version_ref: str,
        approval: ApprovalValidationRequest,
    ) -> KeyRotationReceipt:
        """Atomically re-encrypt one workspace and rebuild its blind index."""

        _validate_ref(workspace_ref, field_name="workspace_ref")
        _validate_ref(new_key_version_ref, field_name="new_key_version_ref")
        with (
            self.approval_authority.hold_validation_lock(),
            self._key_lifecycle_lock,
        ):
            self._authorize(
                approval,
                action="ecosystem.local_data.rotate_workspace_key",
                resource_refs=(workspace_ref, new_key_version_ref),
            )
            connection = self._connect()
            new_key_created = False
            committed = False
            old_key_version_ref = ""
            key_item_ref = ""
            cleanup_ref = ""
            replayed = False
            try:
                connection.execute("BEGIN IMMEDIATE")
                key_item_ref, current_key_version_ref = self._workspace_key(
                    connection, workspace_ref
                )
                pending = connection.execute(
                    "SELECT * FROM eco_key_cleanup WHERE workspace_ref = ? "
                    "AND new_key_version_ref = ? AND completed_at IS NULL",
                    (workspace_ref, new_key_version_ref),
                ).fetchone()
                if current_key_version_ref == new_key_version_ref:
                    if pending is None:
                        raise EcosystemConflict("ECO_KEY_VERSION_REUSE_DENIED")
                    old_key_version_ref = pending["old_key_version_ref"]
                    cleanup_ref = pending["cleanup_ref"]
                    replayed = True
                    connection.rollback()
                else:
                    historical = connection.execute(
                        "SELECT 1 FROM eco_key_cleanup WHERE workspace_ref = ? "
                        "AND (old_key_version_ref = ? OR new_key_version_ref = ?)",
                        (
                            workspace_ref,
                            new_key_version_ref,
                            new_key_version_ref,
                        ),
                    ).fetchone()
                    if historical is not None:
                        raise EcosystemConflict("ECO_KEY_VERSION_REUSE_DENIED")
                    old_key_version_ref = current_key_version_ref
                    self.crypto_backend.create(
                        key_item_ref=key_item_ref,
                        key_version_ref=new_key_version_ref,
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
                            envelope.get("search_terms")
                            if isinstance(envelope, dict)
                            else None
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
                    receipts = connection.execute(
                        "SELECT idempotency_ref, key_version_ref, request_ciphertext, "
                        "approval_ref, receipt_ref, operation_receipt_refs_json, created_at "
                        "FROM eco_uow_receipts WHERE workspace_ref = ?",
                        (workspace_ref,),
                    ).fetchall()
                    for receipt in receipts:
                        material = self.crypto_backend.decrypt(
                            key_item_ref=key_item_ref,
                            key_version_ref=receipt["key_version_ref"],
                            ciphertext=receipt["request_ciphertext"],
                            aad=_receipt_aad(
                                workspace_ref=workspace_ref,
                                idempotency_ref=receipt["idempotency_ref"],
                                key_version_ref=receipt["key_version_ref"],
                            ),
                        )
                        fingerprint_ref = self._request_fingerprint(
                            key_item_ref=key_item_ref,
                            key_version_ref=new_key_version_ref,
                            request_material=material,
                        )
                        ciphertext = self.crypto_backend.encrypt(
                            key_item_ref=key_item_ref,
                            key_version_ref=new_key_version_ref,
                            plaintext=material,
                            aad=_receipt_aad(
                                workspace_ref=workspace_ref,
                                idempotency_ref=receipt["idempotency_ref"],
                                key_version_ref=new_key_version_ref,
                            ),
                        )
                        receipt_authenticator_ref = self._receipt_authenticator(
                            key_item_ref=key_item_ref,
                            key_version_ref=new_key_version_ref,
                            workspace_ref=workspace_ref,
                            idempotency_ref=receipt["idempotency_ref"],
                            request_fingerprint_ref=fingerprint_ref,
                            request_ciphertext=ciphertext,
                            approval_ref=receipt["approval_ref"],
                            receipt_ref=receipt["receipt_ref"],
                            operation_receipt_refs_json=receipt[
                                "operation_receipt_refs_json"
                            ],
                            created_at=receipt["created_at"],
                        )
                        connection.execute(
                            "UPDATE eco_uow_receipts SET request_fingerprint_ref = ?, "
                            "key_version_ref = ?, request_ciphertext = ?, "
                            "receipt_authenticator_ref = ? "
                            "WHERE workspace_ref = ? AND idempotency_ref = ?",
                            (
                                fingerprint_ref,
                                new_key_version_ref,
                                ciphertext,
                                receipt_authenticator_ref,
                                workspace_ref,
                                receipt["idempotency_ref"],
                            ),
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
                        "UPDATE eco_workspaces SET key_version_ref = ? "
                        "WHERE workspace_ref = ?",
                        (new_key_version_ref, workspace_ref),
                    )
                    cleanup_ref = _stable_ref(
                        "key-cleanup-ref:ecosystem",
                        {
                            "workspace_ref": workspace_ref,
                            "old_key_version_ref": old_key_version_ref,
                            "new_key_version_ref": new_key_version_ref,
                        },
                    )
                    connection.execute(
                        "INSERT INTO eco_key_cleanup VALUES (?, ?, ?, ?, NULL)",
                        (
                            workspace_ref,
                            old_key_version_ref,
                            new_key_version_ref,
                            cleanup_ref,
                        ),
                    )
                    connection.commit()
                    committed = True
            except Exception:
                connection.rollback()
                if new_key_created and not committed:
                    self.crypto_backend.delete(
                        key_item_ref=key_item_ref,
                        key_version_ref=new_key_version_ref,
                    )
                raise
            finally:
                connection.close()

            cleanup_pending = False
            try:
                old_key_delete_receipt = self.crypto_backend.delete(
                    key_item_ref=key_item_ref,
                    key_version_ref=old_key_version_ref,
                )
            except EcosystemKeyUnavailable:
                cleanup_pending = True
                old_key_delete_receipt = "key-receipt-ref:ecosystem:delete-pending"
            if not cleanup_pending:
                cleanup = self._connect()
                try:
                    cleanup.execute("BEGIN IMMEDIATE")
                    cleanup.execute(
                        "UPDATE eco_key_cleanup SET completed_at = ? "
                        "WHERE cleanup_ref = ?",
                        (_utc_now(), cleanup_ref),
                    )
                    cleanup.commit()
                except Exception:
                    cleanup.rollback()
                    raise
                finally:
                    cleanup.close()
            receipt_ref = _stable_ref(
                "key-rotation-receipt-ref:ecosystem",
                {
                    "workspace_ref": workspace_ref,
                    "new_key_version_ref": new_key_version_ref,
                    "old_key_delete_receipt": old_key_delete_receipt,
                    "cleanup_ref": cleanup_ref,
                },
            )
            return KeyRotationReceipt(
                receipt_ref=receipt_ref,
                cleanup_ref=cleanup_ref,
                cleanup_pending=cleanup_pending,
                replayed=replayed,
            )

    def integrity_check(self) -> IntegrityReport:
        with self._key_lifecycle_lock:
            connection = self._connect()
            try:
                return self._deep_snapshot_integrity(connection)
            finally:
                connection.close()

    def _deep_snapshot_integrity(
        self, connection: sqlite3.Connection
    ) -> IntegrityReport:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        self._validate_schema(connection)
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise EcosystemLocalDataError("ECO_BACKUP_INTEGRITY_FAILED")
        records = connection.execute(
            "SELECT * FROM eco_records ORDER BY workspace_ref, record_ref"
        ).fetchall()
        workspace_rows = connection.execute(
            "SELECT workspace_ref, key_item_ref, key_version_ref FROM eco_workspaces"
        ).fetchall()
        workspace_keys = {
            row["workspace_ref"]: (row["key_item_ref"], row["key_version_ref"])
            for row in workspace_rows
        }
        for key_item_ref, key_version_ref in workspace_keys.values():
            self.crypto_backend.probe(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
            )
        expected_tokens: set[tuple[str, str, str]] = set()
        for row in records:
            try:
                key_item_ref, current_key_version_ref = workspace_keys[
                    row["workspace_ref"]
                ]
            except KeyError as exc:
                raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED") from exc
            if row["key_version_ref"] != current_key_version_ref:
                raise EcosystemLocalDataError("ECO_RECORD_KEY_VERSION_STALE")
            self.crypto_backend.probe(
                key_item_ref=key_item_ref,
                key_version_ref=current_key_version_ref,
            )
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
            try:
                envelope = json.loads(plaintext)
            except Exception as exc:
                raise EcosystemLocalDataError("ECO_PRIVATE_PAYLOAD_INVALID") from exc
            if (
                not isinstance(envelope, dict)
                or set(envelope) != {"private_payload", "search_terms"}
                or not isinstance(envelope["private_payload"], dict)
                or not isinstance(envelope["search_terms"], list)
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
        for receipt in connection.execute(
            "SELECT workspace_ref, idempotency_ref, request_fingerprint_ref, "
            "key_version_ref, request_ciphertext, approval_ref, receipt_ref, "
            "operation_receipt_refs_json, receipt_authenticator_ref, created_at "
            "FROM eco_uow_receipts"
        ):
            try:
                key_item_ref, _ = workspace_keys[receipt["workspace_ref"]]
            except KeyError as exc:
                raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED") from exc
            material = self.crypto_backend.decrypt(
                key_item_ref=key_item_ref,
                key_version_ref=receipt["key_version_ref"],
                ciphertext=receipt["request_ciphertext"],
                aad=_receipt_aad(
                    workspace_ref=receipt["workspace_ref"],
                    idempotency_ref=receipt["idempotency_ref"],
                    key_version_ref=receipt["key_version_ref"],
                ),
            )
            expected_fingerprint = self._request_fingerprint(
                key_item_ref=key_item_ref,
                key_version_ref=receipt["key_version_ref"],
                request_material=material,
            )
            if not hmac.compare_digest(
                receipt["request_fingerprint_ref"], expected_fingerprint
            ):
                raise EcosystemLocalDataError("ECO_UOW_RECEIPT_INTEGRITY_FAILED")
            expected_authenticator = self._receipt_authenticator(
                key_item_ref=key_item_ref,
                key_version_ref=receipt["key_version_ref"],
                workspace_ref=receipt["workspace_ref"],
                idempotency_ref=receipt["idempotency_ref"],
                request_fingerprint_ref=receipt["request_fingerprint_ref"],
                request_ciphertext=receipt["request_ciphertext"],
                approval_ref=receipt["approval_ref"],
                receipt_ref=receipt["receipt_ref"],
                operation_receipt_refs_json=receipt["operation_receipt_refs_json"],
                created_at=receipt["created_at"],
            )
            if not hmac.compare_digest(
                receipt["receipt_authenticator_ref"], expected_authenticator
            ):
                raise EcosystemLocalDataError("ECO_UOW_RECEIPT_INTEGRITY_FAILED")
            try:
                _validate_ref(receipt["approval_ref"], field_name="approval_ref")
                operation_receipts = json.loads(receipt["operation_receipt_refs_json"])
                if (
                    not isinstance(operation_receipts, list)
                    or not 1 <= len(operation_receipts) <= 64
                    or len(operation_receipts) != len(set(operation_receipts))
                ):
                    raise ValueError
                for operation_receipt_ref in operation_receipts:
                    _validate_ref(
                        operation_receipt_ref,
                        field_name="operation_receipt_ref",
                    )
                    event_ref = operation_receipt_ref.replace(
                        "operation-receipt-ref:", "event-ref:", 1
                    )
                    event = connection.execute(
                        "SELECT * FROM eco_events WHERE event_ref = ? "
                        "AND workspace_ref = ?",
                        (event_ref, receipt["workspace_ref"]),
                    ).fetchone()
                    if event is None:
                        raise ValueError
                    expected_event_ref = _stable_ref(
                        "event-ref:ecosystem",
                        {
                            "workspace_ref": event["workspace_ref"],
                            "record_ref": event["record_ref"],
                            "operation_ref": event["operation_ref"],
                            "event_kind_ref": event["event_kind_ref"],
                            "version": event["version"],
                        },
                    )
                    if not hmac.compare_digest(event_ref, expected_event_ref):
                        raise ValueError
                expected_receipt_ref = _stable_ref(
                    "uow-receipt-ref:ecosystem",
                    {
                        "workspace_ref": receipt["workspace_ref"],
                        "idempotency_ref": receipt["idempotency_ref"],
                        "approval_ref": receipt["approval_ref"],
                        "operation_receipt_refs": operation_receipts,
                    },
                )
            except (TypeError, ValueError) as exc:
                raise EcosystemLocalDataError(
                    "ECO_UOW_RECEIPT_INTEGRITY_FAILED"
                ) from exc
            if not hmac.compare_digest(receipt["receipt_ref"], expected_receipt_ref):
                raise EcosystemLocalDataError("ECO_UOW_RECEIPT_INTEGRITY_FAILED")
        orphan_count = connection.execute(
            "SELECT COUNT(*) FROM eco_search_tokens s LEFT JOIN eco_records r "
            "ON r.workspace_ref=s.workspace_ref AND r.record_ref=s.record_ref "
            "WHERE r.record_ref IS NULL"
        ).fetchone()[0]
        if orphan_count:
            raise EcosystemLocalDataError("ECO_REF_INTEGRITY_FAILED")
        search_count = len(actual_tokens)
        report_ref = _stable_ref(
            "integrity-report-ref:ecosystem",
            {
                "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
                "workspace_count": len(workspace_rows),
                "record_count": len(records),
                "search_count": search_count,
                "orphan_count": orphan_count,
            },
        )
        return IntegrityReport(
            schema_ref=ECO_LOCAL_DATA_SCHEMA_REF,
            status="ok",
            workspace_count=len(workspace_rows),
            record_count=len(records),
            search_entry_count=search_count,
            orphan_count=orphan_count,
            report_ref=report_ref,
        )

    def create_backup(
        self,
        *,
        destination_ref: str,
        backup_ref: str,
        key_item_ref: str,
        key_version_ref: str,
        approval: ApprovalValidationRequest,
    ) -> BackupReceipt:
        _validate_ref(backup_ref, field_name="backup_ref")
        _validate_ref(key_item_ref, field_name="key_item_ref")
        _validate_ref(key_version_ref, field_name="key_version_ref")
        _validate_ref(destination_ref, field_name="destination_ref")
        destination = self.path_resolver.resolve(destination_ref=destination_ref)
        if not destination.is_absolute() or destination.exists():
            raise ValueError("ECO_BACKUP_DESTINATION_INVALID")
        with self.approval_authority.hold_validation_lock():
            self._authorize(
                approval,
                action="ecosystem.local_data.create_backup",
                resource_refs=(
                    backup_ref,
                    destination_ref,
                    key_item_ref,
                    key_version_ref,
                ),
            )
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
                    self._deep_snapshot_integrity(check)
                finally:
                    check.close()
                header = _canonical_json(
                    {
                        "backup_ref": backup_ref,
                        "schema_ref": ECO_LOCAL_DATA_SCHEMA_REF,
                        "key_item_ref": key_item_ref,
                        "key_version_ref": key_version_ref,
                    }
                )
                max_plaintext_bytes = (
                    _MAX_BACKUP_BYTES
                    - len(_BACKUP_MAGIC)
                    - 4
                    - len(header)
                    - _NONCE_BYTES
                    - 16
                )
                if snapshot.stat().st_size > max_plaintext_bytes:
                    raise EcosystemLocalDataError("ECO_BACKUP_SIZE_LIMIT_EXCEEDED")
                plaintext = snapshot.read_bytes()
                ciphertext = self.crypto_backend.encrypt(
                    key_item_ref=key_item_ref,
                    key_version_ref=key_version_ref,
                    plaintext=plaintext,
                    aad=header,
                )
                container = (
                    _BACKUP_MAGIC + struct.pack(">I", len(header)) + header + ciphertext
                )
                if len(container) > _MAX_BACKUP_BYTES:
                    raise EcosystemLocalDataError("ECO_BACKUP_SIZE_LIMIT_EXCEEDED")
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
                _publish_new_file(
                    stage,
                    destination,
                    exists_code="ECO_BACKUP_DESTINATION_EXISTS",
                )
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
        return self._validate_backup_plaintext(header, plaintext)

    def _validate_backup_plaintext(
        self, header: dict[str, str], plaintext: bytes
    ) -> RestorePreview:
        with tempfile.TemporaryDirectory() as stage_dir:
            snapshot = Path(stage_dir) / "preview.sqlite3"
            snapshot.write_bytes(plaintext)
            connection = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
            try:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version != ECO_LOCAL_DATA_SCHEMA_VERSION:
                    raise EcosystemLocalDataError("ECO_BACKUP_SCHEMA_UNSUPPORTED")
                report = self._deep_snapshot_integrity(connection)
            finally:
                connection.close()
        return RestorePreview(
            backup_ref=header["backup_ref"],
            schema_ref=header["schema_ref"],
            integrity_status="ok",
            workspace_count=report.workspace_count,
            record_count=report.record_count,
        )

    def restore_to_new(
        self,
        *,
        backup_path: Path,
        destination_ref: str,
        approval: ApprovalValidationRequest,
    ) -> str:
        """Restore a verified snapshot to a new path; existing stores are untouched."""

        _validate_ref(destination_ref, field_name="destination_ref")
        destination = self.path_resolver.resolve(destination_ref=destination_ref)
        if not destination.is_absolute() or destination.exists():
            raise ValueError("ECO_RESTORE_DESTINATION_INVALID")
        header, plaintext = self._open_backup(backup_path)
        preview = self._validate_backup_plaintext(header, plaintext)
        with self.approval_authority.hold_validation_lock():
            self._authorize(
                approval,
                action="ecosystem.local_data.restore_to_new",
                resource_refs=(
                    preview.backup_ref,
                    preview.schema_ref,
                    destination_ref,
                ),
            )
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
            try:
                _publish_new_file(
                    stage,
                    destination,
                    exists_code="ECO_RESTORE_DESTINATION_EXISTS",
                )
                os.chmod(destination, 0o600)
            finally:
                stage.unlink(missing_ok=True)
        return _stable_ref(
            "restore-receipt-ref:ecosystem",
            {
                "backup_ref": preview.backup_ref,
                "schema_ref": preview.schema_ref,
                "record_count": preview.record_count,
            },
        )

    def _open_backup(self, backup_path: Path) -> tuple[dict[str, str], bytes]:
        try:
            size = backup_path.stat().st_size
        except OSError as exc:
            raise EcosystemLocalDataError("ECO_BACKUP_CONTAINER_INVALID") from exc
        if size > _MAX_BACKUP_BYTES:
            raise EcosystemLocalDataError("ECO_BACKUP_SIZE_LIMIT_EXCEEDED")
        with backup_path.open("rb") as source:
            container = source.read(_MAX_BACKUP_BYTES + 1)
        if len(container) > _MAX_BACKUP_BYTES:
            raise EcosystemLocalDataError("ECO_BACKUP_SIZE_LIMIT_EXCEEDED")
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
        try:
            size = source_path.stat().st_size
        except OSError as exc:
            raise EcosystemLocalDataError("ECO_MIGRATION_SOURCE_INVALID") from exc
        if size > _MAX_MIGRATION_SOURCE_BYTES:
            raise EcosystemLocalDataError("ECO_MIGRATION_SOURCE_SIZE_LIMIT_EXCEEDED")
        with source_path.open("rb") as source:
            raw = source.read(_MAX_MIGRATION_SOURCE_BYTES + 1)
        if len(raw) > _MAX_MIGRATION_SOURCE_BYTES:
            raise EcosystemLocalDataError("ECO_MIGRATION_SOURCE_SIZE_LIMIT_EXCEEDED")
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
