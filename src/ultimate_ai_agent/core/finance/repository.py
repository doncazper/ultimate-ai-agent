"""Encrypted, synthetic-only SQLite repository for the FIN-001 kernel."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
import sqlite3
import stat
import tempfile
from enum import Enum
from pathlib import Path
from collections.abc import Callable
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.finance.crypto import (
    FinanceCryptoBackend,
    FinanceCryptoStatus,
    ciphertext_ref,
)
from ultimate_ai_agent.core.finance.fixtures import (
    FinanceFixture,
    load_finance_fixture,
    load_finance_fixture_manifest,
)
from ultimate_ai_agent.core.finance.models import FinanceSnapshot, stable_finance_ref
from ultimate_ai_agent.core.finance.import_preview import (
    SyntheticImportPreview,
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.import_commit import (
    FinanceImportCommitError,
    FinanceImportCommitProof,
    build_import_commit_proof,
    build_import_commit_record,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)


FINANCE_REPOSITORY_METADATA_FILE = "finance_repository_v1.json"
FINANCE_REPOSITORY_ENCRYPTED_FILE = "finance_repository_v1.enc"
FINANCE_REPOSITORY_RECEIPTS_FILE = "finance_mutation_receipts_v1.jsonl"
FINANCE_REPOSITORY_LOCK_FILE = ".finance_repository_v1.lock"
FINANCE_REPOSITORY_PENDING_COMMIT_FILE = ".finance_repository_pending_commit_v1"
FINANCE_REPOSITORY_SCHEMA_REF = "repository-schema-ref:finance/FIN-001:sqlite:v1"
FINANCE_REPOSITORY_MIGRATION_REF = "migration-ref:finance/FIN-001:v0-to-v1"
FINANCE_REPOSITORY_ENVELOPE_CONTEXT_REF = (
    "crypto-context-ref:finance/FIN-001:repository:v1"
)
FINANCE_BACKUP_ENVELOPE_CONTEXT_REF = "crypto-context-ref:finance/FIN-001:backup:v1"
FINANCE_RECEIPT_LOG_MAX_BYTES = 8 * 1024 * 1024


class FinanceRepositoryError(RuntimeError):
    """Content-free protected repository failure."""


class FinanceMutationOperation(str, Enum):
    create = "create"
    import_commit = "import_commit"
    backup = "backup"
    restore = "restore"
    delete = "delete"


class FinanceMutationPermit(BaseModel):
    """Exact, already-validated permit accepted by repository mutations."""

    schema_version: Literal["uaa-finance-mutation-permit.v1"] = (
        "uaa-finance-mutation-permit.v1"
    )
    permit_ref: str
    operation: FinanceMutationOperation
    repository_ref: str
    fixture_ref: str | None = None
    target_ref: str | None = None
    import_preview_ref: str | None = None
    import_profile_ref: str | None = None
    import_fixture_manifest_ref: str | None = None
    import_candidate_refs: tuple[str, ...] = Field(default=(), max_length=128)
    import_source_fingerprint_refs: tuple[str, ...] = Field(default=(), max_length=128)
    expected_revision: StrictInt = Field(..., ge=0)
    request_ref: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    policy_decision_ref: str
    approval_ref: str
    approval_decision_ref: str
    authority_lease_ref: str
    authority_decision_ref: str
    exact_scope_ref: str
    safe_disable_ref: str
    rollback_ref: str
    capability_ref: Literal[
        "capability-ref:finance/FIN-001/synthetic-book-mutation",
        "capability-ref:finance/FIN-002/synthetic-import-commit",
    ] = "capability-ref:finance/FIN-001/synthetic-book-mutation"
    current_policy_validated: Literal[True] = True
    current_approval_validated: Literal[True] = True
    active_exact_lease_validated: Literal[True] = True
    synthetic_fixture_only: Literal[True] = True
    raw_financial_values_included: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_permit(self) -> "FinanceMutationPermit":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref") and value is not None:
                validate_task_ref(str(value), f"finance_permit_{name}")
            elif name.endswith("_refs"):
                for ref in value:
                    validate_task_ref(str(ref), f"finance_permit_{name}")
        if self.operation == FinanceMutationOperation.create.value:
            if (
                self.fixture_ref is None
                or self.target_ref is not None
                or self.expected_revision != 0
                or self.import_preview_ref is not None
                or self.import_profile_ref is not None
                or self.import_fixture_manifest_ref is not None
                or self.import_candidate_refs
                or self.import_source_fingerprint_refs
                or self.capability_ref
                != "capability-ref:finance/FIN-001/synthetic-book-mutation"
                or self.safe_disable_ref
                != "safe-disable-ref:finance/FIN-001:synthetic-mutations"
                or self.rollback_ref
                != "rollback-ref:finance/FIN-001:reversal-or-restore"
            ):
                raise ValueError("FINANCE_CREATE_PERMIT_SCOPE_INVALID")
        elif self.operation == FinanceMutationOperation.import_commit.value:
            if (
                self.fixture_ref is None
                or self.target_ref is not None
                or self.expected_revision < 1
                or self.import_preview_ref is None
                or self.import_profile_ref is None
                or self.import_fixture_manifest_ref is None
                or not self.import_candidate_refs
                or len(self.import_candidate_refs)
                != len(self.import_source_fingerprint_refs)
                or self.capability_ref
                != "capability-ref:finance/FIN-002/synthetic-import-commit"
                or self.safe_disable_ref
                != "safe-disable-ref:finance/FIN-002/synthetic-import-commit"
                or self.rollback_ref
                != "rollback-contract-ref:finance/FIN-002/reversal-or-restore:v1"
            ):
                raise ValueError("FIN002_IMPORT_COMMIT_PERMIT_SCOPE_INVALID")
        elif self.fixture_ref is not None:
            raise ValueError("FINANCE_NONCREATE_FIXTURE_REF_DENIED")
        elif (
            self.import_preview_ref is not None
            or self.import_profile_ref is not None
            or self.import_fixture_manifest_ref is not None
            or self.import_candidate_refs
            or self.import_source_fingerprint_refs
            or self.capability_ref
            != "capability-ref:finance/FIN-001/synthetic-book-mutation"
            or self.safe_disable_ref
            != "safe-disable-ref:finance/FIN-001:synthetic-mutations"
            or self.rollback_ref != "rollback-ref:finance/FIN-001:reversal-or-restore"
        ):
            raise ValueError("FINANCE_NONIMPORT_BINDING_DENIED")
        if self.operation in {"backup", "restore"} and self.target_ref is None:
            raise ValueError("FINANCE_BACKUP_TARGET_REF_REQUIRED")
        if self.operation == "delete" and self.target_ref is not None:
            raise ValueError("FINANCE_DELETE_TARGET_REF_DENIED")
        expected = stable_finance_ref(
            "finance-mutation-permit-ref",
            self.model_dump(mode="json", exclude={"permit_ref"}),
        )
        if self.permit_ref != expected:
            raise ValueError("FINANCE_MUTATION_PERMIT_REF_INVALID")
        validate_safe_task_payload(payload, "finance_mutation_permit")
        return self


class FinanceMutationReceipt(BaseModel):
    schema_version: Literal["uaa-finance-mutation-receipt.v1"] = (
        "uaa-finance-mutation-receipt.v1"
    )
    receipt_ref: str
    phase: Literal["prepared", "committed", "recovered"]
    operation: FinanceMutationOperation
    repository_ref: str
    request_ref: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    permit_ref: str
    before_revision: StrictInt = Field(..., ge=0)
    after_revision: StrictInt = Field(..., ge=0)
    before_snapshot_ref: str | None = None
    after_snapshot_ref: str | None = None
    policy_decision_ref: str
    approval_decision_ref: str
    authority_lease_ref: str
    authority_decision_ref: str
    rollback_ref: str
    proof_refs: tuple[str, ...] = Field(default=(), max_length=32)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    raw_paths_included: Literal[False] = False
    key_material_included: Literal[False] = False
    real_financial_data_included: Literal[False] = False
    connector_call_performed: Literal[False] = False
    payment_or_transfer_performed: Literal[False] = False
    filing_or_advice_performed: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_receipt(self) -> "FinanceMutationReceipt":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref") and value is not None:
                validate_task_ref(str(value), f"finance_receipt_{name}")
            elif name.endswith("_refs"):
                for ref in value:
                    validate_task_ref(str(ref), f"finance_receipt_{name}")
        expected = stable_finance_ref(
            "finance-mutation-receipt-ref",
            self.model_dump(mode="json", exclude={"receipt_ref", "replayed"}),
        )
        if self.receipt_ref != expected:
            raise ValueError("FINANCE_MUTATION_RECEIPT_REF_INVALID")
        if self.phase == "prepared" and self.after_snapshot_ref is not None:
            raise ValueError("FINANCE_PREPARED_RECEIPT_AFTER_SNAPSHOT_DENIED")
        if self.phase != "prepared" and self.operation != "delete":
            if self.after_snapshot_ref is None:
                raise ValueError("FINANCE_COMMITTED_RECEIPT_AFTER_SNAPSHOT_REQUIRED")
        validate_safe_task_payload(payload, "finance_mutation_receipt")
        return self


class FinanceRepositoryMetadata(BaseModel):
    schema_version: Literal["uaa-finance-repository-metadata.v1"] = (
        "uaa-finance-repository-metadata.v1"
    )
    repository_ref: str
    repository_schema_ref: Literal[
        "repository-schema-ref:finance/FIN-001:sqlite:v1"
    ] = FINANCE_REPOSITORY_SCHEMA_REF
    finance_schema_ref: Literal["finance-schema:v1"] = "finance-schema:v1"
    migration_ref: Literal["migration-ref:finance/FIN-001:v0-to-v1"] = (
        FINANCE_REPOSITORY_MIGRATION_REF
    )
    key_handle_ref: str
    key_version_ref: str
    backup_key_handle_ref: str
    backup_key_version_ref: str
    crypto_adapter_ref: str
    envelope_context_ref: Literal[
        "crypto-context-ref:finance/FIN-001:repository:v1"
    ] = FINANCE_REPOSITORY_ENVELOPE_CONTEXT_REF
    ciphertext_ref: str
    generation: StrictInt = Field(..., ge=1)
    deleted: StrictBool = False
    encrypted_at_rest: Literal[True] = True
    sqlite_plaintext_persisted: Literal[False] = False
    key_material_included: Literal[False] = False
    keychain_handle_opaque: Literal[True] = True
    synchronizing_keychain_allowed: Literal[False] = False
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_metadata(self) -> "FinanceRepositoryMetadata":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref"):
                validate_task_ref(str(value), f"finance_metadata_{name}")
        validate_safe_task_payload(payload, "finance_repository_metadata")
        return self


class FinanceBackupMetadata(BaseModel):
    schema_version: Literal["uaa-finance-encrypted-backup.v1"] = (
        "uaa-finance-encrypted-backup.v1"
    )
    backup_ref: str
    repository_ref: str
    repository_schema_ref: str
    finance_schema_ref: str
    source_key_version_ref: str
    backup_key_version_ref: str
    backup_context_ref: Literal["crypto-context-ref:finance/FIN-001:backup:v1"] = (
        FINANCE_BACKUP_ENVELOPE_CONTEXT_REF
    )
    source_generation: StrictInt = Field(..., ge=1)
    source_revision: StrictInt = Field(..., ge=0)
    source_snapshot_ref: str
    ciphertext_ref: str
    encrypted: Literal[True] = True
    integrity_bound: Literal[True] = True
    raw_paths_included: Literal[False] = False
    key_material_included: Literal[False] = False
    synthetic_only: Literal[True] = True

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_backup(self) -> "FinanceBackupMetadata":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref"):
                validate_task_ref(str(value), f"finance_backup_{name}")
        expected = stable_finance_ref(
            "finance-backup-ref",
            self.model_dump(mode="json", exclude={"backup_ref"}),
        )
        if self.backup_ref != expected:
            raise ValueError("FINANCE_BACKUP_REF_INVALID")
        validate_safe_task_payload(payload, "finance_backup_metadata")
        return self


class FinanceRepository:
    """Encrypt a serialized in-memory SQLite generation after every mutation."""

    def __init__(
        self,
        root: Path,
        *,
        crypto_backend: FinanceCryptoBackend,
    ) -> None:
        self.root = root.expanduser().absolute()
        self.crypto = crypto_backend
        self.metadata_path = self.root / FINANCE_REPOSITORY_METADATA_FILE
        self.encrypted_path = self.root / FINANCE_REPOSITORY_ENCRYPTED_FILE
        self.receipts_path = self.root / FINANCE_REPOSITORY_RECEIPTS_FILE
        self.lock_path = self.root / FINANCE_REPOSITORY_LOCK_FILE
        self.pending_commit_path = self.root / FINANCE_REPOSITORY_PENDING_COMMIT_FILE

    def create_from_fixture(
        self,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._ensure_private_root(create=True)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._create_from_fixture_locked(
                permit=permit,
                revalidate=revalidate,
            )

    def _create_from_fixture_locked(
        self,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._require_permit(permit, FinanceMutationOperation.create)
        replay = self._find_logged_replay(permit)
        if replay is not None:
            return replay.model_copy(update={"replayed": True})
        assert permit.fixture_ref is not None
        fixture = load_finance_fixture(permit.fixture_ref)
        manifest = load_finance_fixture_manifest()
        if self.metadata_path.exists() or self.encrypted_path.exists():
            raise FinanceRepositoryError("FINANCE_REPOSITORY_ALREADY_EXISTS")
        self._ensure_private_root(create=True)
        self._require_crypto_ready()
        self._require_revalidated(permit, revalidate)
        key_handle_ref = stable_finance_ref(
            "key-handle-ref:finance:repository",
            {"repository_ref": permit.repository_ref},
        )
        key_version_ref = "key-version-ref:finance:repository:v1"
        backup_key_handle_ref = stable_finance_ref(
            "key-handle-ref:finance:backup",
            {"repository_ref": permit.repository_ref},
        )
        backup_key_version_ref = "key-version-ref:finance:backup:v1"
        primary_created = False
        backup_created = False
        try:
            primary_key_receipt = self.crypto.create_key(
                key_handle_ref=key_handle_ref,
                key_version_ref=key_version_ref,
                request_ref=permit.request_ref,
            )
            primary_created = True
            backup_key_receipt = self.crypto.create_key(
                key_handle_ref=backup_key_handle_ref,
                key_version_ref=backup_key_version_ref,
                request_ref=permit.request_ref,
            )
            backup_created = True
            snapshot = self._snapshot_from_fixture(
                repository_ref=permit.repository_ref,
                fixture=fixture,
                fixture_manifest_ref=manifest.manifest_ref,
            )
            prepared = self._receipt(
                permit=permit,
                phase="prepared",
                before_revision=0,
                after_revision=snapshot.revision,
                before_snapshot_ref=None,
                after_snapshot_ref=None,
                proof_refs=(
                    primary_key_receipt.receipt_ref,
                    backup_key_receipt.receipt_ref,
                    FINANCE_REPOSITORY_MIGRATION_REF,
                ),
            )
            self._require_revalidated(permit, revalidate)
            self._append_receipt(prepared)
            connection = self._new_connection()
            try:
                self._write_snapshot(connection, snapshot)
                self._record_idempotency(connection, permit, prepared.receipt_ref)
                serialized = connection.serialize()
            finally:
                connection.close()
            ciphertext = self.crypto.seal(
                key_handle_ref=key_handle_ref,
                key_version_ref=key_version_ref,
                context_ref=FINANCE_REPOSITORY_ENVELOPE_CONTEXT_REF,
                request_ref=permit.request_ref,
                plaintext=serialized,
            )
            metadata = FinanceRepositoryMetadata(
                repository_ref=permit.repository_ref,
                key_handle_ref=key_handle_ref,
                key_version_ref=key_version_ref,
                backup_key_handle_ref=backup_key_handle_ref,
                backup_key_version_ref=backup_key_version_ref,
                crypto_adapter_ref=self.crypto.adapter_ref,
                ciphertext_ref=ciphertext_ref(ciphertext),
                generation=snapshot.generation,
            )
            committed = self._receipt(
                permit=permit,
                phase="committed",
                before_revision=0,
                after_revision=snapshot.revision,
                before_snapshot_ref=None,
                after_snapshot_ref=snapshot.snapshot_ref,
                proof_refs=(
                    metadata.ciphertext_ref,
                    primary_key_receipt.receipt_ref,
                    backup_key_receipt.receipt_ref,
                    FINANCE_REPOSITORY_MIGRATION_REF,
                ),
            )
            self._require_revalidated(permit, revalidate)
            self._stage_and_commit_generation(
                metadata=metadata,
                ciphertext=ciphertext,
                committed=committed,
            )
            return committed
        except Exception:
            if not self.pending_commit_path.exists():
                self._rollback_new_keys(
                    key_handle_ref=key_handle_ref,
                    key_version_ref=key_version_ref,
                    backup_key_handle_ref=backup_key_handle_ref,
                    backup_key_version_ref=backup_key_version_ref,
                    request_ref=permit.request_ref,
                    primary_created=primary_created,
                    backup_created=backup_created or primary_created,
                )
            raise

    def commit_import(
        self,
        preview: SyntheticImportPreview,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> tuple[FinanceImportCommitProof, FinanceMutationReceipt]:
        """Atomically commit one current allowlisted synthetic preview."""

        self._ensure_private_root(create=False)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._commit_import_locked(
                preview,
                permit=permit,
                revalidate=revalidate,
            )

    def _commit_import_locked(
        self,
        preview: SyntheticImportPreview,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> tuple[FinanceImportCommitProof, FinanceMutationReceipt]:
        self._require_permit(permit, FinanceMutationOperation.import_commit)
        replay = self._find_logged_replay(permit)
        if replay is not None:
            if replay.after_snapshot_ref is None:
                raise FinanceRepositoryError("FIN002_IMPORT_REPLAY_PROOF_MISSING")
            snapshot = self._load_snapshot_locked(request_ref=permit.request_ref)
            record = next(
                (
                    item
                    for item in snapshot.import_commits
                    if item.preview_ref == permit.import_preview_ref
                    and item.commit_ref in replay.proof_refs
                ),
                None,
            )
            if record is None:
                raise FinanceRepositoryError("FIN002_IMPORT_REPLAY_RECORD_MISSING")
            replayed = replay.model_copy(update={"replayed": True})
            return (
                build_import_commit_proof(
                    record=record,
                    mutation_receipt_ref=replayed.receipt_ref,
                    after_snapshot_ref=replayed.after_snapshot_ref,
                    replayed=True,
                ),
                replayed,
            )

        metadata = self._read_metadata()
        self._require_repository_binding(permit, metadata)
        before = self._load_snapshot_locked(request_ref=permit.request_ref)
        if before.revision != permit.expected_revision:
            raise FinanceRepositoryError("FINANCE_STALE_REVISION")
        self._require_current_import_preview(permit, preview, before)
        try:
            record, entries = build_import_commit_record(preview, before=before)
        except FinanceImportCommitError as exc:
            raise FinanceRepositoryError(str(exc)) from None

        prepared = self._receipt(
            permit=permit,
            phase="prepared",
            before_revision=before.revision,
            after_revision=before.revision + 1,
            before_snapshot_ref=before.snapshot_ref,
            after_snapshot_ref=None,
            proof_refs=(
                preview.preview_ref,
                preview.import_fixture_manifest_ref,
                record.commit_ref,
                record.rollback_ref,
            ),
        )
        self._require_revalidated(permit, revalidate)
        self._require_current_import_preview(permit, preview, before)
        self._append_receipt(prepared)

        applied_fixture_refs = before.applied_fixture_refs
        if preview.fixture_ref not in applied_fixture_refs:
            applied_fixture_refs = (*applied_fixture_refs, preview.fixture_ref)
        after = before.model_copy(
            update={
                "revision": before.revision + 1,
                "generation": before.generation + 1,
                "applied_fixture_refs": applied_fixture_refs,
                "journal_entries": (*before.journal_entries, *entries),
                "import_commits": (*before.import_commits, record),
            }
        )
        # Force all graph, balance, lineage, and safe-ref validators after update.
        after = FinanceSnapshot.model_validate(after.model_dump(mode="python"))

        connection = self._new_connection()
        try:
            self._write_snapshot(connection, after)
            self._record_idempotency(connection, permit, prepared.receipt_ref)
            serialized = connection.serialize()
        finally:
            connection.close()
        ciphertext = self.crypto.seal(
            key_handle_ref=metadata.key_handle_ref,
            key_version_ref=metadata.key_version_ref,
            context_ref=metadata.envelope_context_ref,
            request_ref=permit.request_ref,
            plaintext=serialized,
        )
        updated_metadata = metadata.model_copy(
            update={
                "ciphertext_ref": ciphertext_ref(ciphertext),
                "generation": after.generation,
            }
        )
        committed = self._receipt(
            permit=permit,
            phase="committed",
            before_revision=before.revision,
            after_revision=after.revision,
            before_snapshot_ref=before.snapshot_ref,
            after_snapshot_ref=after.snapshot_ref,
            proof_refs=(
                preview.preview_ref,
                preview.import_fixture_manifest_ref,
                record.commit_ref,
                record.rollback_ref,
                updated_metadata.ciphertext_ref,
            ),
        )
        self._require_revalidated(permit, revalidate)
        self._require_current_import_preview(permit, preview, before)
        self._stage_and_commit_generation(
            metadata=updated_metadata,
            ciphertext=ciphertext,
            committed=committed,
        )
        return (
            build_import_commit_proof(
                record=record,
                mutation_receipt_ref=committed.receipt_ref,
                after_snapshot_ref=after.snapshot_ref,
            ),
            committed,
        )

    @staticmethod
    def _require_current_import_preview(
        permit: FinanceMutationPermit,
        preview: SyntheticImportPreview,
        snapshot: FinanceSnapshot,
    ) -> None:
        existing_fingerprints = tuple(
            ref
            for item in snapshot.import_commits
            for ref in item.source_fingerprint_refs
        )
        try:
            current = preview_synthetic_csv_fixture(
                preview.fixture_ref,
                existing_fingerprint_refs=existing_fingerprints,
            )
        except (ValueError, RuntimeError):
            raise FinanceRepositoryError(
                "FIN002_IMPORT_PREVIEW_REVALIDATION_FAILED"
            ) from None
        expected_bindings = (
            permit.fixture_ref,
            permit.import_preview_ref,
            permit.import_profile_ref,
            permit.import_fixture_manifest_ref,
            permit.import_candidate_refs,
            permit.import_source_fingerprint_refs,
        )
        actual_bindings = (
            current.fixture_ref,
            current.preview_ref,
            current.profile_ref,
            current.import_fixture_manifest_ref,
            tuple(item.candidate_ref for item in current.candidates),
            tuple(item.source_fingerprint_ref for item in current.observations),
        )
        if current != preview or expected_bindings != actual_bindings:
            raise FinanceRepositoryError("FIN002_IMPORT_PREVIEW_STALE")

    def load_snapshot(self, *, request_ref: str) -> FinanceSnapshot:
        self._ensure_private_root(create=False)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._load_snapshot_locked(request_ref=request_ref)

    def load_snapshot_read_only(self, *, request_ref: str) -> FinanceSnapshot:
        """Load a stable generation without creating files or recovering writes."""

        self._ensure_private_root(create=False)
        with self._read_lock():
            try:
                os.lstat(self.pending_commit_path)
            except FileNotFoundError:
                pass
            else:
                raise FinanceRepositoryError(
                    "FINANCE_PENDING_COMMIT_REQUIRES_MUTATING_RECOVERY"
                )
            return self._load_snapshot_locked(request_ref=request_ref)

    def _load_snapshot_locked(self, *, request_ref: str) -> FinanceSnapshot:
        validate_task_ref(request_ref, "finance_read_request_ref")
        metadata = self._read_metadata()
        if metadata.deleted:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_DELETED")
        self._require_crypto_ready()
        try:
            self.crypto.probe_key(
                key_handle_ref=metadata.key_handle_ref,
                key_version_ref=metadata.key_version_ref,
                request_ref=request_ref,
            )
        except Exception:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_KEY_UNAVAILABLE") from None
        ciphertext = self._read_regular(self.encrypted_path, max_bytes=64 * 1024 * 1024)
        if ciphertext_ref(ciphertext) != metadata.ciphertext_ref:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_CIPHERTEXT_DRIFT")
        try:
            plaintext = self.crypto.open(
                key_handle_ref=metadata.key_handle_ref,
                key_version_ref=metadata.key_version_ref,
                context_ref=metadata.envelope_context_ref,
                request_ref=request_ref,
                ciphertext=ciphertext,
            )
        except Exception:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_DECRYPT_FAILED") from None
        connection = self._connection_from_bytes(plaintext)
        try:
            snapshot = self._read_snapshot(connection)
        finally:
            connection.close()
        if snapshot.repository_ref != metadata.repository_ref:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_BINDING_MISMATCH")
        return snapshot

    def check_integrity(self, *, request_ref: str) -> dict[str, Any]:
        snapshot = self.load_snapshot(request_ref=request_ref)
        return {
            "schema_version": "uaa-finance-integrity-check.v1",
            "repository_ref": snapshot.repository_ref,
            "snapshot_ref": snapshot.snapshot_ref,
            "revision": snapshot.revision,
            "generation": snapshot.generation,
            "balanced": True,
            "graph_valid": True,
            "encrypted_at_rest": True,
            "sqlite_plaintext_persisted": False,
            "synthetic_only": True,
            "real_financial_data_included": False,
            "raw_financial_values_included": False,
        }

    def export_redacted(self, *, request_ref: str) -> dict[str, Any]:
        return self.load_snapshot(request_ref=request_ref).redacted_read_model()

    def backup(
        self,
        backup_path: Path,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> tuple[FinanceBackupMetadata, FinanceMutationReceipt]:
        self._ensure_private_root(create=False)
        canonical_backup = backup_path.expanduser().resolve(strict=False)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._backup_locked(
                canonical_backup,
                permit=permit,
                revalidate=revalidate,
            )

    def _backup_locked(
        self,
        backup_path: Path,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> tuple[FinanceBackupMetadata, FinanceMutationReceipt]:
        self._require_permit(permit, FinanceMutationOperation.backup)
        self._require_target_binding(permit, backup_path)
        replay = self._find_logged_replay(permit)
        if replay is not None:
            raw = self._read_regular(backup_path, max_bytes=64 * 1024 * 1024)
            header, _ciphertext = raw.split(b"\n", 1)
            return (
                FinanceBackupMetadata.model_validate_json(header),
                replay.model_copy(update={"replayed": True}),
            )
        metadata = self._read_metadata()
        self._require_repository_binding(permit, metadata)
        snapshot = self._load_snapshot_locked(request_ref=permit.request_ref)
        if snapshot.revision != permit.expected_revision:
            raise FinanceRepositoryError("FINANCE_STALE_REVISION")
        if backup_path.exists() or backup_path.is_symlink():
            raise FinanceRepositoryError("FINANCE_BACKUP_TARGET_EXISTS")
        prepared = self._receipt(
            permit=permit,
            phase="prepared",
            before_revision=snapshot.revision,
            after_revision=snapshot.revision,
            before_snapshot_ref=snapshot.snapshot_ref,
            after_snapshot_ref=None,
            proof_refs=(metadata.ciphertext_ref,),
        )
        self._require_revalidated(permit, revalidate)
        self._append_receipt(prepared)
        try:
            plaintext = self.crypto.open(
                key_handle_ref=metadata.key_handle_ref,
                key_version_ref=metadata.key_version_ref,
                context_ref=metadata.envelope_context_ref,
                request_ref=permit.request_ref,
                ciphertext=self._read_regular(
                    self.encrypted_path, max_bytes=64 * 1024 * 1024
                ),
            )
        except Exception:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_DECRYPT_FAILED") from None
        backup_ciphertext = self.crypto.seal(
            key_handle_ref=metadata.backup_key_handle_ref,
            key_version_ref=metadata.backup_key_version_ref,
            context_ref=FINANCE_BACKUP_ENVELOPE_CONTEXT_REF,
            request_ref=permit.request_ref,
            plaintext=plaintext,
        )
        provisional = FinanceBackupMetadata.model_construct(
            backup_ref="finance-backup-ref:pending",
            repository_ref=metadata.repository_ref,
            repository_schema_ref=metadata.repository_schema_ref,
            finance_schema_ref=metadata.finance_schema_ref,
            source_key_version_ref=metadata.key_version_ref,
            backup_key_version_ref=metadata.backup_key_version_ref,
            source_generation=snapshot.generation,
            source_revision=snapshot.revision,
            source_snapshot_ref=snapshot.snapshot_ref,
            ciphertext_ref=ciphertext_ref(backup_ciphertext),
        )
        backup_ref = stable_finance_ref(
            "finance-backup-ref",
            provisional.model_dump(mode="json", exclude={"backup_ref"}),
        )
        backup_metadata = FinanceBackupMetadata(
            **provisional.model_dump(mode="python", exclude={"backup_ref"}),
            backup_ref=backup_ref,
        )
        header = json.dumps(
            backup_metadata.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._require_revalidated(permit, revalidate)
        self._atomic_write(backup_path, header + b"\n" + backup_ciphertext)
        committed = self._receipt(
            permit=permit,
            phase="committed",
            before_revision=snapshot.revision,
            after_revision=snapshot.revision,
            before_snapshot_ref=snapshot.snapshot_ref,
            after_snapshot_ref=snapshot.snapshot_ref,
            proof_refs=(backup_metadata.backup_ref, backup_metadata.ciphertext_ref),
        )
        self._append_receipt(committed)
        return backup_metadata, committed

    def restore(
        self,
        backup_path: Path,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._ensure_private_root(create=False)
        canonical_backup = backup_path.expanduser().resolve(strict=False)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._restore_locked(
                canonical_backup,
                permit=permit,
                revalidate=revalidate,
            )

    def _restore_locked(
        self,
        backup_path: Path,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._require_permit(permit, FinanceMutationOperation.restore)
        self._require_target_binding(permit, backup_path)
        replay = self._find_logged_replay(permit)
        if replay is not None:
            return replay.model_copy(update={"replayed": True})
        metadata = self._read_metadata()
        self._require_repository_binding(permit, metadata)
        before = self._load_snapshot_locked(request_ref=permit.request_ref)
        if before.revision != permit.expected_revision:
            raise FinanceRepositoryError("FINANCE_STALE_REVISION")
        raw = self._read_regular(backup_path, max_bytes=64 * 1024 * 1024)
        try:
            header, backup_ciphertext = raw.split(b"\n", 1)
            backup_metadata = FinanceBackupMetadata.model_validate_json(header)
        except (ValueError, TypeError):
            raise FinanceRepositoryError("FINANCE_BACKUP_INVALID") from None
        if (
            backup_metadata.repository_ref != metadata.repository_ref
            or backup_metadata.backup_key_version_ref != metadata.backup_key_version_ref
            or ciphertext_ref(backup_ciphertext) != backup_metadata.ciphertext_ref
        ):
            raise FinanceRepositoryError("FINANCE_BACKUP_BINDING_MISMATCH")
        prepared = self._receipt(
            permit=permit,
            phase="prepared",
            before_revision=before.revision,
            after_revision=backup_metadata.source_revision,
            before_snapshot_ref=before.snapshot_ref,
            after_snapshot_ref=None,
            proof_refs=(backup_metadata.backup_ref,),
        )
        self._require_revalidated(permit, revalidate)
        self._append_receipt(prepared)
        try:
            plaintext = self.crypto.open(
                key_handle_ref=metadata.backup_key_handle_ref,
                key_version_ref=metadata.backup_key_version_ref,
                context_ref=backup_metadata.backup_context_ref,
                request_ref=permit.request_ref,
                ciphertext=backup_ciphertext,
            )
        except Exception:
            raise FinanceRepositoryError("FINANCE_BACKUP_DECRYPT_FAILED") from None
        staged = self._connection_from_bytes(plaintext)
        try:
            restored_source = self._read_snapshot(staged)
        finally:
            staged.close()
        if restored_source.snapshot_ref != backup_metadata.source_snapshot_ref:
            raise FinanceRepositoryError("FINANCE_BACKUP_SNAPSHOT_MISMATCH")
        restored = restored_source.model_copy(
            update={"generation": metadata.generation + 1}
        )
        live = self._new_connection()
        try:
            self._write_snapshot(live, restored)
            self._record_idempotency(live, permit, prepared.receipt_ref)
            restored_plaintext = live.serialize()
        finally:
            live.close()
        live_ciphertext = self.crypto.seal(
            key_handle_ref=metadata.key_handle_ref,
            key_version_ref=metadata.key_version_ref,
            context_ref=metadata.envelope_context_ref,
            request_ref=permit.request_ref,
            plaintext=restored_plaintext,
        )
        updated_metadata = metadata.model_copy(
            update={
                "ciphertext_ref": ciphertext_ref(live_ciphertext),
                "generation": metadata.generation + 1,
            }
        )
        committed = self._receipt(
            permit=permit,
            phase="committed",
            before_revision=before.revision,
            after_revision=restored.revision,
            before_snapshot_ref=before.snapshot_ref,
            after_snapshot_ref=restored.snapshot_ref,
            proof_refs=(
                backup_metadata.backup_ref,
                updated_metadata.ciphertext_ref,
            ),
        )
        self._require_revalidated(permit, revalidate)
        self._stage_and_commit_generation(
            metadata=updated_metadata,
            ciphertext=live_ciphertext,
            committed=committed,
        )
        return committed

    def delete(
        self,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._ensure_private_root(create=False)
        with self._mutation_lock():
            self._recover_pending_commit()
            return self._delete_locked(permit=permit, revalidate=revalidate)

    def _delete_locked(
        self,
        *,
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._require_permit(permit, FinanceMutationOperation.delete)
        replay = self._find_logged_replay(permit)
        if replay is not None:
            return replay.model_copy(update={"replayed": True})
        metadata = self._read_metadata()
        self._require_repository_binding(permit, metadata)
        if metadata.deleted:
            prepared = self._find_logged_prepared(permit)
            if prepared is None:
                raise FinanceRepositoryError("FINANCE_DELETE_RECOVERY_RECEIPT_MISSING")
            return self._finish_delete(
                metadata=metadata,
                permit=permit,
                prepared=prepared,
                revalidate=revalidate,
            )
        before = self._load_snapshot_locked(request_ref=permit.request_ref)
        if before.revision != permit.expected_revision:
            raise FinanceRepositoryError("FINANCE_STALE_REVISION")
        prepared = self._receipt(
            permit=permit,
            phase="prepared",
            before_revision=before.revision,
            after_revision=before.revision,
            before_snapshot_ref=before.snapshot_ref,
            after_snapshot_ref=None,
            proof_refs=(
                "deletion-plan-ref:finance/FIN-001:cryptographic-and-explicit",
            ),
        )
        self._require_revalidated(permit, revalidate)
        self._append_receipt(prepared)
        self._require_revalidated(permit, revalidate)
        tombstone = metadata.model_copy(update={"deleted": True})
        self._atomic_write_json(self.metadata_path, tombstone.model_dump(mode="json"))
        return self._finish_delete(
            metadata=tombstone,
            permit=permit,
            prepared=prepared,
            revalidate=revalidate,
        )

    def _finish_delete(
        self,
        *,
        metadata: FinanceRepositoryMetadata,
        permit: FinanceMutationPermit,
        prepared: FinanceMutationReceipt,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> FinanceMutationReceipt:
        self._require_revalidated(permit, revalidate)
        backup = self.crypto.delete_key(
            key_handle_ref=metadata.backup_key_handle_ref,
            key_version_ref=metadata.backup_key_version_ref,
            request_ref=permit.request_ref,
        )
        primary = self.crypto.delete_key(
            key_handle_ref=metadata.key_handle_ref,
            key_version_ref=metadata.key_version_ref,
            request_ref=permit.request_ref,
        )
        self._unlink_private_file(self.encrypted_path, missing_ok=True)
        committed = self._receipt(
            permit=permit,
            phase="committed",
            before_revision=prepared.before_revision,
            after_revision=prepared.after_revision,
            before_snapshot_ref=prepared.before_snapshot_ref,
            after_snapshot_ref=None,
            proof_refs=(primary.receipt_ref, backup.receipt_ref),
        )
        self._append_receipt_if_missing(committed)
        return committed

    def _find_logged_replay(
        self, permit: FinanceMutationPermit
    ) -> FinanceMutationReceipt | None:
        receipts = self._matching_logged_receipts(permit)
        return next(
            (receipt for receipt in reversed(receipts) if receipt.phase == "committed"),
            None,
        )

    def _find_logged_prepared(
        self, permit: FinanceMutationPermit
    ) -> FinanceMutationReceipt | None:
        receipts = self._matching_logged_receipts(permit)
        return next(
            (receipt for receipt in reversed(receipts) if receipt.phase == "prepared"),
            None,
        )

    def _matching_logged_receipts(
        self, permit: FinanceMutationPermit
    ) -> list[FinanceMutationReceipt]:
        if not self.receipts_path.exists():
            return []
        raw = self._read_regular(self.receipts_path, max_bytes=8 * 1024 * 1024)
        matches: list[FinanceMutationReceipt] = []
        for line in raw.splitlines():
            receipt = FinanceMutationReceipt.model_validate_json(line)
            idempotency_matches = receipt.idempotency_ref == permit.idempotency_ref
            request_matches = receipt.request_ref == permit.request_ref
            if not idempotency_matches and not request_matches:
                continue
            if idempotency_matches and not request_matches:
                raise FinanceRepositoryError("FINANCE_IDEMPOTENCY_CONFLICT")
            if request_matches and not idempotency_matches:
                raise FinanceRepositoryError("FINANCE_REQUEST_REF_CONFLICT")
            if (
                receipt.payload_fingerprint_ref != permit.payload_fingerprint_ref
                or receipt.operation != permit.operation
                or receipt.repository_ref != permit.repository_ref
            ):
                raise FinanceRepositoryError("FINANCE_IDEMPOTENCY_CONFLICT")
            matches.append(receipt)
        return matches

    @contextmanager
    def _mutation_lock(self):
        self._ensure_private_root(create=True)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock_path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_mode & 0o077
            ):
                raise FinanceRepositoryError("FINANCE_REPOSITORY_LOCK_INVALID")
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    @contextmanager
    def _read_lock(self):
        """Acquire the existing repository lock without creating or writing it."""

        try:
            linked = os.lstat(self.lock_path)
        except FileNotFoundError:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_LOCK_MISSING") from None
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock_path, flags)
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_mode & 0o077
                or (metadata.st_dev, metadata.st_ino) != (linked.st_dev, linked.st_ino)
            ):
                raise FinanceRepositoryError("FINANCE_REPOSITORY_LOCK_INVALID")
            fcntl.flock(descriptor, fcntl.LOCK_SH)
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    @staticmethod
    def _require_repository_binding(
        permit: FinanceMutationPermit,
        metadata: FinanceRepositoryMetadata,
    ) -> None:
        if metadata.repository_ref != permit.repository_ref:
            raise FinanceRepositoryError("FINANCE_REPOSITORY_BINDING_MISMATCH")

    @staticmethod
    def _require_target_binding(
        permit: FinanceMutationPermit,
        path: Path,
    ) -> None:
        expected = stable_finance_ref(
            "backup-path-ref:finance/FIN-001",
            {"canonical_path": str(path.expanduser().resolve(strict=False))},
        )
        if permit.target_ref != expected:
            raise FinanceRepositoryError("FINANCE_TARGET_REF_PATH_MISMATCH")

    def _stage_and_commit_generation(
        self,
        *,
        metadata: FinanceRepositoryMetadata,
        ciphertext: bytes,
        committed: FinanceMutationReceipt,
    ) -> None:
        if committed.phase != "committed":
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_RECEIPT_INVALID")
        header = {
            "schema_version": "uaa-finance-pending-commit.v1",
            "metadata": metadata.model_dump(mode="json"),
            "receipt": committed.model_dump(mode="json"),
        }
        encoded_header = json.dumps(
            header,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._atomic_write(
            self.pending_commit_path, encoded_header + b"\n" + ciphertext
        )
        self._recover_pending_commit()

    def _recover_pending_commit(self) -> None:
        if not self.pending_commit_path.exists():
            return
        raw = self._read_regular(
            self.pending_commit_path,
            max_bytes=64 * 1024 * 1024,
        )
        try:
            encoded_header, ciphertext = raw.split(b"\n", 1)
            header = json.loads(encoded_header)
        except (ValueError, TypeError, json.JSONDecodeError):
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_INVALID") from None
        if not isinstance(header, dict) or set(header) != {
            "schema_version",
            "metadata",
            "receipt",
        }:
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_INVALID")
        if header["schema_version"] != "uaa-finance-pending-commit.v1":
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_INVALID")
        try:
            metadata = FinanceRepositoryMetadata.model_validate(header["metadata"])
            committed = FinanceMutationReceipt.model_validate(header["receipt"])
        except (ValueError, TypeError):
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_INVALID") from None
        if (
            committed.phase != "committed"
            or committed.repository_ref != metadata.repository_ref
            or committed.after_snapshot_ref is None
            or ciphertext_ref(ciphertext) != metadata.ciphertext_ref
        ):
            raise FinanceRepositoryError("FINANCE_PENDING_COMMIT_BINDING_MISMATCH")
        self._atomic_write(self.encrypted_path, ciphertext)
        self._atomic_write_json(self.metadata_path, metadata.model_dump(mode="json"))
        self._append_receipt_if_missing(committed)
        self._unlink_private_file(self.pending_commit_path, missing_ok=False)

    def _append_receipt_if_missing(self, receipt: FinanceMutationReceipt) -> None:
        if self.receipts_path.exists():
            raw = self._read_regular(
                self.receipts_path,
                max_bytes=FINANCE_RECEIPT_LOG_MAX_BYTES,
            )
            for line in raw.splitlines():
                existing = FinanceMutationReceipt.model_validate_json(line)
                if existing.receipt_ref == receipt.receipt_ref:
                    if existing != receipt:
                        raise FinanceRepositoryError("FINANCE_RECEIPT_REF_CONFLICT")
                    return
        self._append_receipt(receipt)

    def _rollback_new_keys(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        backup_key_handle_ref: str,
        backup_key_version_ref: str,
        request_ref: str,
        primary_created: bool,
        backup_created: bool,
    ) -> None:
        failures: list[Exception] = []
        for created, handle_ref, version_ref in (
            (backup_created, backup_key_handle_ref, backup_key_version_ref),
            (primary_created, key_handle_ref, key_version_ref),
        ):
            if not created:
                continue
            try:
                self.crypto.delete_key(
                    key_handle_ref=handle_ref,
                    key_version_ref=version_ref,
                    request_ref=request_ref,
                )
            except Exception as exc:
                failures.append(exc)
        for path in (self.encrypted_path, self.metadata_path):
            try:
                self._unlink_private_file(path, missing_ok=True)
            except Exception as exc:
                failures.append(exc)
        if failures:
            raise FinanceRepositoryError("FINANCE_CREATE_ROLLBACK_FAILED") from None

    @staticmethod
    def _unlink_private_file(path: Path, *, missing_ok: bool) -> None:
        try:
            metadata = os.lstat(path)
        except FileNotFoundError:
            if missing_ok:
                return
            raise FinanceRepositoryError("FINANCE_REPOSITORY_FILE_MISSING") from None
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise FinanceRepositoryError("FINANCE_REPOSITORY_TARGET_INVALID")
        path.unlink()
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    @staticmethod
    def _require_revalidated(
        permit: FinanceMutationPermit,
        revalidate: Callable[[], FinanceMutationPermit],
    ) -> None:
        current = revalidate()
        if current != permit:
            raise FinanceRepositoryError("FINANCE_PREPERSIST_AUTHORITY_DRIFT")

    @staticmethod
    def _snapshot_from_fixture(
        *,
        repository_ref: str,
        fixture: FinanceFixture,
        fixture_manifest_ref: str,
    ) -> FinanceSnapshot:
        return FinanceSnapshot(
            repository_ref=repository_ref,
            revision=1,
            generation=1,
            fixture_manifest_ref=fixture_manifest_ref,
            applied_fixture_refs=(fixture.fixture_ref,),
            books=(fixture.book,),
            legal_entities=fixture.legal_entities,
            accounts=fixture.accounts,
            journal_entries=fixture.journal_entries,
        )

    @staticmethod
    def _new_connection() -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = MEMORY")
        connection.execute("PRAGMA synchronous = FULL")
        connection.executescript(
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE snapshots (
                revision INTEGER PRIMARY KEY,
                snapshot_ref TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE idempotency (
                idempotency_ref TEXT PRIMARY KEY,
                payload_fingerprint_ref TEXT NOT NULL,
                operation TEXT NOT NULL,
                receipt_ref TEXT NOT NULL
            );
            PRAGMA user_version = 1;
            """
        )
        return connection

    @staticmethod
    def _connection_from_bytes(payload: bytes) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        try:
            connection.deserialize(payload)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            version = connection.execute("PRAGMA user_version").fetchone()
            if integrity != ("ok",) or version != (1,):
                raise FinanceRepositoryError("FINANCE_SQLITE_INTEGRITY_FAILED")
            return connection
        except Exception:
            connection.close()
            raise

    @staticmethod
    def _write_snapshot(
        connection: sqlite3.Connection, snapshot: FinanceSnapshot
    ) -> None:
        payload = json.dumps(
            snapshot.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        with connection:
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("repository_schema_ref", FINANCE_REPOSITORY_SCHEMA_REF),
            )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("finance_schema_ref", snapshot.schema_version),
            )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("current_revision", str(snapshot.revision)),
            )
            connection.execute(
                "INSERT INTO snapshots(revision, snapshot_ref, payload_json) VALUES (?, ?, ?)",
                (snapshot.revision, snapshot.snapshot_ref, payload),
            )

    @staticmethod
    def _read_snapshot(connection: sqlite3.Connection) -> FinanceSnapshot:
        row = connection.execute(
            "SELECT payload_json, snapshot_ref FROM snapshots ORDER BY revision DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise FinanceRepositoryError("FINANCE_SNAPSHOT_MISSING")
        snapshot = FinanceSnapshot.model_validate_json(row[0])
        if snapshot.snapshot_ref != row[1]:
            raise FinanceRepositoryError("FINANCE_SNAPSHOT_REF_MISMATCH")
        return snapshot

    @staticmethod
    def _record_idempotency(
        connection: sqlite3.Connection,
        permit: FinanceMutationPermit,
        receipt_ref: str,
    ) -> None:
        with connection:
            connection.execute(
                "INSERT INTO idempotency(idempotency_ref, payload_fingerprint_ref, operation, receipt_ref) VALUES (?, ?, ?, ?)",
                (
                    permit.idempotency_ref,
                    permit.payload_fingerprint_ref,
                    str(permit.operation),
                    receipt_ref,
                ),
            )

    def _read_metadata(self) -> FinanceRepositoryMetadata:
        return FinanceRepositoryMetadata.model_validate_json(
            self._read_regular(self.metadata_path, max_bytes=64 * 1024)
        )

    def _require_crypto_ready(self) -> None:
        readiness = self.crypto.readiness()
        if readiness.status != FinanceCryptoStatus.ready.value:
            raise FinanceRepositoryError("FINANCE_CRYPTO_BACKEND_NOT_READY")

    @staticmethod
    def _require_permit(
        permit: FinanceMutationPermit, operation: FinanceMutationOperation
    ) -> None:
        validated = FinanceMutationPermit.model_validate(
            permit.model_dump(mode="python")
        )
        if validated.operation != operation.value:
            raise FinanceRepositoryError("FINANCE_MUTATION_PERMIT_OPERATION_MISMATCH")

    def _receipt(
        self,
        *,
        permit: FinanceMutationPermit,
        phase: Literal["prepared", "committed", "recovered"],
        before_revision: int,
        after_revision: int,
        before_snapshot_ref: str | None,
        after_snapshot_ref: str | None,
        proof_refs: tuple[str, ...],
    ) -> FinanceMutationReceipt:
        payload = {
            "phase": phase,
            "operation": permit.operation,
            "repository_ref": permit.repository_ref,
            "request_ref": permit.request_ref,
            "idempotency_ref": permit.idempotency_ref,
            "payload_fingerprint_ref": permit.payload_fingerprint_ref,
            "permit_ref": permit.permit_ref,
            "before_revision": before_revision,
            "after_revision": after_revision,
            "before_snapshot_ref": before_snapshot_ref,
            "after_snapshot_ref": after_snapshot_ref,
            "policy_decision_ref": permit.policy_decision_ref,
            "approval_decision_ref": permit.approval_decision_ref,
            "authority_lease_ref": permit.authority_lease_ref,
            "authority_decision_ref": permit.authority_decision_ref,
            "rollback_ref": permit.rollback_ref,
            "proof_refs": proof_refs,
        }
        provisional = FinanceMutationReceipt.model_construct(
            receipt_ref="finance-mutation-receipt-ref:pending",
            **payload,
        )
        receipt_ref = stable_finance_ref(
            "finance-mutation-receipt-ref",
            provisional.model_dump(mode="json", exclude={"receipt_ref", "replayed"}),
        )
        return FinanceMutationReceipt(receipt_ref=receipt_ref, **payload)

    def _append_receipt(self, receipt: FinanceMutationReceipt) -> None:
        self._ensure_private_root(create=True)
        payload = (
            json.dumps(
                receipt.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.receipts_path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_mode & 0o077
                or metadata.st_size + len(payload) > FINANCE_RECEIPT_LOG_MAX_BYTES
            ):
                raise FinanceRepositoryError("FINANCE_RECEIPT_SINK_INVALID")
            remaining = memoryview(payload)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise FinanceRepositoryError("FINANCE_RECEIPT_WRITE_FAILED")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _ensure_private_root(self, *, create: bool) -> None:
        if create:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = os.lstat(self.root)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise FinanceRepositoryError("FINANCE_REPOSITORY_ROOT_NOT_PRIVATE")

    @staticmethod
    def _read_regular(path: Path, *, max_bytes: int) -> bytes:
        linked = os.lstat(path)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_uid != os.getuid()
                or opened.st_mode & 0o077
                or opened.st_size > max_bytes
                or (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)
            ):
                raise FinanceRepositoryError("FINANCE_REPOSITORY_FILE_INVALID")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(64 * 1024, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise FinanceRepositoryError("FINANCE_REPOSITORY_FILE_INVALID")
            closed_over = os.fstat(descriptor)
            current = os.lstat(path)
            if (
                total != opened.st_size
                or (closed_over.st_size, closed_over.st_mtime_ns)
                != (opened.st_size, opened.st_mtime_ns)
                or (closed_over.st_dev, closed_over.st_ino)
                != (current.st_dev, current.st_ino)
            ):
                raise FinanceRepositoryError("FINANCE_REPOSITORY_FILE_CHANGED")
            return b"".join(chunks)
        finally:
            os.close(descriptor)

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent = os.lstat(path.parent)
        if (
            not stat.S_ISDIR(parent.st_mode)
            or stat.S_ISLNK(parent.st_mode)
            or parent.st_uid != os.getuid()
            or parent.st_mode & 0o077
        ):
            raise FinanceRepositoryError("FINANCE_REPOSITORY_PARENT_NOT_PRIVATE")
        if path.exists() or path.is_symlink():
            existing = os.lstat(path)
            if (
                not stat.S_ISREG(existing.st_mode)
                or stat.S_ISLNK(existing.st_mode)
                or existing.st_uid != os.getuid()
                or existing.st_mode & 0o077
            ):
                raise FinanceRepositoryError("FINANCE_REPOSITORY_TARGET_INVALID")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            dir=path.parent,
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    @classmethod
    def _atomic_write_json(cls, path: Path, payload: dict[str, Any]) -> None:
        cls._atomic_write(
            path,
            (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
                "utf-8"
            ),
        )
