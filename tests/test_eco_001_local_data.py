from __future__ import annotations

import json
import hashlib
import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

import ultimate_ai_agent.core.ecosystem.local_data as local_data_module
from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.local_data import (
    ArchiveRecord,
    DeleteRecord,
    EcosystemConflict,
    EcosystemKeyUnavailable,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    JsonCompatibilityReader,
    PutRecord,
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
from ultimate_ai_agent.core.time import utc_now


WORKSPACE_A = "workspace-ref:alpha"
WORKSPACE_B = "workspace-ref:beta"


class AuthorizedTestStore(EcosystemLocalDataPlatform):
    """Test-only facade that issues exact grants for each requested mutation."""

    def __init__(self, **kwargs):
        self.test_authority = LocalApprovalAuthority()
        self._approval_counter = 0
        super().__init__(approval_authority=self.test_authority, **kwargs)

    def _approval(self, action: str, resource_refs: tuple[str, ...]):
        self._approval_counter += 1
        suffix = self._approval_counter
        request = ApprovalRequest(
            approval_request_id=f"approval_request_eco_{suffix}",
            run_id="run_eco_001_tests",
            subject_type=ApprovalSubjectType.kernel_task,
            subject_id=f"subject_eco_001_{suffix}",
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="actor_eco_001_test",
                authority_source=AuthoritySource.foundation_test,
            ),
            requested_action=action,
            purpose="Verify the bounded ECO-001 local mutation contract.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.user_private,
                source="source-ref:eco-001-test",
                requires_redaction=True,
            ),
            resource_refs=list(resource_refs),
            expires_at=utc_now() + timedelta(minutes=10),
        )
        self.test_authority.create_request(request)
        grant = self.test_authority.create_test_grant(
            request.approval_request_id,
            approval_ref=f"approval_eco_001_{suffix}",
        )
        return request.to_validation_request(grant.approval_ref)

    def create_workspace(
        self, *, workspace_ref: str, key_version_ref="key-version-ref:v1"
    ):
        return super().create_workspace(
            workspace_ref=workspace_ref,
            key_version_ref=key_version_ref,
            approval=self._approval(
                "ecosystem.local_data.create_workspace",
                (workspace_ref, key_version_ref),
            ),
        )

    def apply(self, *, workspace_ref: str, idempotency_ref: str, operations):
        resources = tuple(
            dict.fromkeys(
                (workspace_ref, idempotency_ref)
                + tuple(operation.operation_ref for operation in operations)
                + tuple(operation.record_ref for operation in operations)
            )
        )
        return super().apply(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operations=operations,
            approval=self._approval("ecosystem.local_data.apply", resources),
        )

    def rebuild_search(self, *, workspace_ref: str):
        return super().rebuild_search(
            workspace_ref=workspace_ref,
            approval=self._approval(
                "ecosystem.local_data.rebuild_search", (workspace_ref,)
            ),
        )

    def rotate_workspace_key(self, *, workspace_ref: str, new_key_version_ref: str):
        return super().rotate_workspace_key(
            workspace_ref=workspace_ref,
            new_key_version_ref=new_key_version_ref,
            approval=self._approval(
                "ecosystem.local_data.rotate_workspace_key",
                (workspace_ref, new_key_version_ref),
            ),
        )

    def create_backup(
        self,
        *,
        destination: Path,
        backup_ref: str,
        key_item_ref: str,
        key_version_ref: str,
    ):
        destination_ref = "destination-ref:test-backup"
        return super().create_backup(
            destination=destination,
            destination_ref=destination_ref,
            backup_ref=backup_ref,
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            approval=self._approval(
                "ecosystem.local_data.create_backup",
                (backup_ref, destination_ref, key_item_ref, key_version_ref),
            ),
        )

    def restore_to_new(self, *, backup_path: Path, destination: Path):
        destination_ref = "destination-ref:test-restore"
        return super().restore_to_new(
            backup_path=backup_path,
            destination=destination,
            destination_ref=destination_ref,
            approval=self._approval(
                "ecosystem.local_data.restore_to_new",
                (
                    "backup-ref:test-one",
                    "schema-ref:ecosystem-local-data:v1",
                    destination_ref,
                ),
            ),
        )


def _store(
    tmp_path: Path,
    *,
    backend: InMemoryLocalDataCryptoBackend | None = None,
    fault_hook=None,
) -> tuple[EcosystemLocalDataPlatform, InMemoryLocalDataCryptoBackend]:
    selected = backend or InMemoryLocalDataCryptoBackend()
    store = AuthorizedTestStore(
        database_path=(tmp_path / "ecosystem.sqlite3").resolve(),
        crypto_backend=selected,
        fault_hook=fault_hook,
    )
    store.create_workspace(workspace_ref=WORKSPACE_A)
    return store, selected


def _put(
    *,
    operation_ref: str = "operation-ref:create-one",
    record_ref: str = "record-ref:one",
    private_value: str = "private customer note",
    expected_version: int = 0,
) -> PutRecord:
    return PutRecord(
        operation_ref=operation_ref,
        module_ref="module-ref:tasks",
        record_ref=record_ref,
        record_kind_ref="record-kind-ref:task",
        safe_summary_ref="summary-ref:task-record",
        private_payload={"title": private_value, "priority": 2},
        search_terms=("private customer", "Quarterly Follow Up"),
        expected_version=expected_version,
    )


def test_private_values_are_encrypted_and_workspace_scoped(tmp_path: Path) -> None:
    store, backend = _store(tmp_path)
    store.create_workspace(workspace_ref=WORKSPACE_B)
    receipt = store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-one",
        operations=(_put(),),
    )

    assert receipt.replayed is False
    assert store.read(
        workspace_ref=WORKSPACE_A, record_ref="record-ref:one"
    ).private_payload == {"title": "private customer note", "priority": 2}
    assert store.search(workspace_ref=WORKSPACE_A, term=" quarterly   FOLLOW up ") == (
        "record-ref:one",
    )
    assert store.search(workspace_ref=WORKSPACE_B, term="Quarterly Follow Up") == ()

    raw_database = (tmp_path / "ecosystem.sqlite3").read_bytes()
    wal_path = tmp_path / "ecosystem.sqlite3-wal"
    raw_wal = wal_path.read_bytes() if wal_path.exists() else b""
    assert b"private customer note" not in raw_database + raw_wal
    assert b"Quarterly Follow Up" not in raw_database + raw_wal
    legacy_item = dict(vars(_put()))
    legacy_item["private_payload"] = hashlib.sha256(
        json.dumps(
            _put().private_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    legacy_item["search_terms"] = [
        hashlib.sha256(term.encode()).hexdigest()
        for term in ("private customer", "quarterly follow up")
    ]
    legacy_item["operation_type"] = "PutRecord"
    legacy_fingerprint = hashlib.sha256(
        json.dumps(
            {"workspace_ref": WORKSPACE_A, "operations": [legacy_item]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert receipt.request_fingerprint_ref != (
        f"request-fingerprint-ref:ecosystem:{legacy_fingerprint}"
    )
    assert receipt.request_fingerprint_ref.startswith(
        "request-fingerprint-ref:ecosystem-keyed:"
    )

    backend.locked = True
    with pytest.raises(EcosystemKeyUnavailable, match="ECO_KEY_BACKEND_LOCKED"):
        store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")


def test_atomic_uow_conflicts_rolls_back_and_replays_exactly(tmp_path: Path) -> None:
    calls = 0

    def fault_hook(stage: str) -> None:
        nonlocal calls
        if stage.startswith("operation-applied"):
            calls += 1
            if calls == 2:
                raise RuntimeError("synthetic-fault")

    store, _ = _store(tmp_path, fault_hook=fault_hook)
    with pytest.raises(RuntimeError, match="synthetic-fault"):
        store.apply(
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:atomic-fault",
            operations=(
                _put(record_ref="record-ref:first"),
                _put(
                    operation_ref="operation-ref:create-two",
                    record_ref="record-ref:second",
                ),
            ),
        )
    for record_ref in ("record-ref:first", "record-ref:second"):
        with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
            store.read(workspace_ref=WORKSPACE_A, record_ref=record_ref)

    clean_store = AuthorizedTestStore(
        database_path=(tmp_path / "ecosystem.sqlite3").resolve(),
        crypto_backend=store.crypto_backend,
    )
    first = clean_store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:exact-replay",
        operations=(_put(),),
    )
    replay = clean_store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:exact-replay",
        operations=(_put(),),
    )
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref
    with pytest.raises(EcosystemConflict, match="ECO_IDEMPOTENCY_REPLAY_CONFLICT"):
        clean_store.apply(
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:exact-replay",
            operations=(_put(private_value="different private value"),),
        )


def test_stale_write_archive_and_exact_delete_lifecycle(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-one",
        operations=(_put(),),
    )
    with pytest.raises(EcosystemConflict, match="ECO_STALE_RECORD_VERSION"):
        store.apply(
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:stale-update",
            operations=(_put(operation_ref="operation-ref:stale"),),
        )
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:archive-one",
        operations=(
            ArchiveRecord(
                operation_ref="operation-ref:archive-one",
                record_ref="record-ref:one",
                expected_version=1,
            ),
        ),
    )
    archived = store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")
    assert archived.archived is True
    assert archived.version == 2
    assert store.search(workspace_ref=WORKSPACE_A, term="Quarterly Follow Up") == ()

    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:delete-one",
        operations=(
            DeleteRecord(
                operation_ref="operation-ref:delete-one",
                record_ref="record-ref:one",
                expected_version=2,
            ),
        ),
    )
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")
    connection = sqlite3.connect(tmp_path / "ecosystem.sqlite3")
    try:
        assert (
            connection.execute("SELECT COUNT(*) FROM eco_search_tokens").fetchone()[0]
            == 0
        )
        assert connection.execute("SELECT COUNT(*) FROM eco_records").fetchone()[0] == 0
    finally:
        connection.close()


def test_integrity_encrypted_backup_and_restore_preview(tmp_path: Path) -> None:
    store, backend = _store(tmp_path)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-one",
        operations=(_put(),),
    )
    report = store.integrity_check()
    assert (report.status, report.record_count, report.orphan_count) == ("ok", 1, 0)

    backend.create(
        key_item_ref="key-item-ref:backup", key_version_ref="key-version-ref:backup-v1"
    )
    backup_path = (tmp_path / "backups" / "snapshot.uaabackup").resolve()
    receipt = store.create_backup(
        destination=backup_path,
        backup_ref="backup-ref:test-one",
        key_item_ref="key-item-ref:backup",
        key_version_ref="key-version-ref:backup-v1",
    )
    assert receipt.byte_count == backup_path.stat().st_size
    assert b"private customer note" not in backup_path.read_bytes()
    preview = store.restore_preview(backup_path=backup_path)
    assert (preview.integrity_status, preview.record_count, preview.preview_only) == (
        "ok",
        1,
        True,
    )
    restored_path = (tmp_path / "restored" / "ecosystem.sqlite3").resolve()
    store.restore_to_new(backup_path=backup_path, destination=restored_path)
    restored = AuthorizedTestStore(
        database_path=restored_path,
        crypto_backend=backend,
    )
    assert (
        restored.read(
            workspace_ref=WORKSPACE_A, record_ref="record-ref:one"
        ).private_payload["title"]
        == "private customer note"
    )

    damaged = bytearray(backup_path.read_bytes())
    damaged[-1] ^= 1
    backup_path.write_bytes(damaged)
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_CIPHERTEXT_INTEGRITY_FAILED"
    ):
        store.restore_preview(backup_path=backup_path)


def test_key_rotation_and_search_rebuild_preserve_private_records(
    tmp_path: Path,
) -> None:
    store, backend = _store(tmp_path)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-one",
        operations=(_put(),),
    )
    connection = sqlite3.connect(tmp_path / "ecosystem.sqlite3")
    connection.execute("DELETE FROM eco_search_tokens")
    connection.commit()
    connection.close()
    assert store.search(workspace_ref=WORKSPACE_A, term="Quarterly Follow Up") == ()
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_SEARCH_INDEX_INTEGRITY_FAILED"
    ):
        store.integrity_check()
    assert store.rebuild_search(workspace_ref=WORKSPACE_A).startswith(
        "search-rebuild-receipt-ref:ecosystem:"
    )
    assert store.search(workspace_ref=WORKSPACE_A, term="Quarterly Follow Up") == (
        "record-ref:one",
    )

    assert store.rotate_workspace_key(
        workspace_ref=WORKSPACE_A, new_key_version_ref="key-version-ref:v2"
    ).receipt_ref.startswith("key-rotation-receipt-ref:ecosystem:")
    record = store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")
    assert record.key_version_ref == "key-version-ref:v2"
    assert record.private_payload["title"] == "private customer note"
    assert store.search(workspace_ref=WORKSPACE_A, term="Quarterly Follow Up") == (
        "record-ref:one",
    )

    connection = sqlite3.connect(tmp_path / "ecosystem.sqlite3")
    key_item_ref = connection.execute(
        "SELECT key_item_ref FROM eco_workspaces WHERE workspace_ref = ?",
        (WORKSPACE_A,),
    ).fetchone()[0]
    connection.close()
    with pytest.raises(EcosystemKeyUnavailable, match="ECO_KEY_NOT_FOUND"):
        backend.probe(key_item_ref=key_item_ref, key_version_ref="key-version-ref:v1")


def test_schema_and_ciphertext_fail_closed(tmp_path: Path) -> None:
    database_path = (tmp_path / "future.sqlite3").resolve()
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA user_version = 999")
    connection.close()
    with pytest.raises(EcosystemLocalDataError, match="ECO_SCHEMA_UNSUPPORTED"):
        AuthorizedTestStore(
            database_path=database_path,
            crypto_backend=InMemoryLocalDataCryptoBackend(),
        )

    store, _ = _store(tmp_path / "tamper")
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-one",
        operations=(_put(),),
    )
    connection = sqlite3.connect(tmp_path / "tamper" / "ecosystem.sqlite3")
    connection.execute(
        "UPDATE eco_records SET ciphertext = zeroblob(length(ciphertext))"
    )
    connection.commit()
    connection.close()
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_CIPHERTEXT_INTEGRITY_FAILED"
    ):
        store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")


def test_safe_plane_rejects_sensitive_or_path_shaped_refs(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    unsafe = _put()
    unsafe = PutRecord(
        **{
            **vars(unsafe),
            "safe_summary_ref": "/Users/example/private-note.txt",
        }
    )
    with pytest.raises(ValueError, match="SAFE_REF_REQUIRED"):
        store.apply(
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:unsafe-summary",
            operations=(unsafe,),
        )


def test_retention_candidates_are_read_only_and_require_archive(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    operation = _put()
    expiring = PutRecord(
        **{**vars(operation), "expires_at": "2026-08-19T00:00:00+00:00"}
    )
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:create-expiring",
        operations=(expiring,),
    )
    assert (
        store.retention_candidates(
            workspace_ref=WORKSPACE_A, as_of="2026-08-20T00:00:00+00:00"
        )
        == ()
    )
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:archive-expiring",
        operations=(
            ArchiveRecord(
                operation_ref="operation-ref:archive-expiring",
                record_ref="record-ref:one",
                expected_version=1,
            ),
        ),
    )
    assert store.retention_candidates(
        workspace_ref=WORKSPACE_A, as_of="2026-08-20T00:00:00+00:00"
    ) == ("record-ref:one",)
    assert store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one").archived


def test_json_compatibility_preview_is_read_only_and_stable(tmp_path: Path) -> None:
    source = tmp_path / "legacy.json"
    source.write_text(json.dumps([{"private": "one"}, {"private": "two"}]))
    reader = JsonCompatibilityReader()
    before = source.read_bytes()
    first = reader.preview(source)
    second = reader.preview(source)
    assert first == second
    assert first.candidate_count == 2
    assert first.writes_performed is False
    assert source.read_bytes() == before


def test_exact_approval_is_required_before_unit_of_work_mutation(
    tmp_path: Path,
) -> None:
    store, _ = _store(tmp_path)
    operation = _put()
    resources = (
        WORKSPACE_A,
        "idempotency-ref:approval-gate",
        operation.operation_ref,
        operation.record_ref,
    )
    approval = store._approval("ecosystem.local_data.apply", resources)
    store.test_authority.revoke(approval.approval_ref, "test revocation")
    with pytest.raises(EcosystemLocalDataError, match="ECO_APPROVAL_REQUIRED"):
        EcosystemLocalDataPlatform.apply(
            store,
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:approval-gate",
            operations=(operation,),
            approval=approval,
        )
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        store.read(workspace_ref=WORKSPACE_A, record_ref=operation.record_ref)


def test_deleted_record_refs_cannot_reset_optimistic_versions(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:tombstone-create",
        operations=(_put(),),
    )
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:tombstone-delete",
        operations=(
            DeleteRecord(
                operation_ref="operation-ref:tombstone-delete",
                record_ref="record-ref:one",
                expected_version=1,
            ),
        ),
    )
    with pytest.raises(EcosystemConflict, match="ECO_DELETED_RECORD_REF_REUSE_DENIED"):
        store.apply(
            workspace_ref=WORKSPACE_A,
            idempotency_ref="idempotency-ref:tombstone-recreate",
            operations=(_put(operation_ref="operation-ref:tombstone-recreate"),),
        )


def test_existing_workspace_never_replaces_a_lost_key(tmp_path: Path) -> None:
    store, backend = _store(tmp_path)
    connection = sqlite3.connect(tmp_path / "ecosystem.sqlite3")
    key_item_ref, key_version_ref = connection.execute(
        "SELECT key_item_ref, key_version_ref FROM eco_workspaces "
        "WHERE workspace_ref = ?",
        (WORKSPACE_A,),
    ).fetchone()
    connection.close()
    backend.delete(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
    with pytest.raises(EcosystemKeyUnavailable, match="ECO_KEY_NOT_FOUND"):
        store.create_workspace(workspace_ref=WORKSPACE_A)


def test_backup_requires_deep_integrity_and_enforces_publication_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, backend = _store(tmp_path)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:backup-integrity",
        operations=(_put(),),
    )
    backend.create(
        key_item_ref="key-item-ref:backup", key_version_ref="key-version-ref:backup-v1"
    )
    connection = sqlite3.connect(tmp_path / "ecosystem.sqlite3")
    connection.execute("DELETE FROM eco_search_tokens")
    connection.commit()
    connection.close()
    destination = (tmp_path / "deep-check.uaabackup").resolve()
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_SEARCH_INDEX_INTEGRITY_FAILED"
    ):
        store.create_backup(
            destination=destination,
            backup_ref="backup-ref:test-one",
            key_item_ref="key-item-ref:backup",
            key_version_ref="key-version-ref:backup-v1",
        )
    assert not destination.exists()

    store.rebuild_search(workspace_ref=WORKSPACE_A)
    monkeypatch.setattr(local_data_module, "_MAX_BACKUP_BYTES", 128)
    with pytest.raises(EcosystemLocalDataError, match="ECO_BACKUP_SIZE_LIMIT_EXCEEDED"):
        store.create_backup(
            destination=destination,
            backup_ref="backup-ref:test-one",
            key_item_ref="key-item-ref:backup",
            key_version_ref="key-version-ref:backup-v1",
        )
    assert not destination.exists()


def test_key_rotation_cleanup_is_retry_safe(tmp_path: Path) -> None:
    class FlakyDeleteBackend(InMemoryLocalDataCryptoBackend):
        fail_old_delete = False

        def delete(self, *, key_item_ref: str, key_version_ref: str) -> str:
            if self.fail_old_delete and key_version_ref == "key-version-ref:v1":
                self.fail_old_delete = False
                raise EcosystemKeyUnavailable("ECO_KEY_BACKEND_LOCKED")
            return super().delete(
                key_item_ref=key_item_ref, key_version_ref=key_version_ref
            )

    backend = FlakyDeleteBackend()
    store, _ = _store(tmp_path, backend=backend)
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:rotation-retry",
        operations=(_put(),),
    )
    backend.fail_old_delete = True
    first = store.rotate_workspace_key(
        workspace_ref=WORKSPACE_A, new_key_version_ref="key-version-ref:v2"
    )
    assert first.cleanup_pending is True
    replay = store.rotate_workspace_key(
        workspace_ref=WORKSPACE_A, new_key_version_ref="key-version-ref:v2"
    )
    assert replay.cleanup_pending is False
    assert replay.replayed is True
    assert replay.cleanup_ref == first.cleanup_ref
    replayed_uow = store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:rotation-retry",
        operations=(_put(),),
    )
    assert replayed_uow.replayed is True


def test_timestamps_are_canonical_for_sqlite_retention(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    operation = PutRecord(**{**vars(_put()), "expires_at": "2026-W34-4T00:00:00+00:00"})
    store.apply(
        workspace_ref=WORKSPACE_A,
        idempotency_ref="idempotency-ref:canonical-expiry",
        operations=(operation,),
    )
    record = store.read(workspace_ref=WORKSPACE_A, record_ref="record-ref:one")
    assert record.expires_at == "2026-08-20T00:00:00Z"


def test_restore_opens_once_and_never_replaces_a_racing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, backend = _store(tmp_path)
    backend.create(
        key_item_ref="key-item-ref:backup", key_version_ref="key-version-ref:backup-v1"
    )
    backup_path = (tmp_path / "snapshot.uaabackup").resolve()
    store.create_backup(
        destination=backup_path,
        backup_ref="backup-ref:test-one",
        key_item_ref="key-item-ref:backup",
        key_version_ref="key-version-ref:backup-v1",
    )
    open_count = 0
    original_open = store._open_backup

    def counted_open(path: Path):
        nonlocal open_count
        open_count += 1
        return original_open(path)

    monkeypatch.setattr(store, "_open_backup", counted_open)
    destination = (tmp_path / "restore-race.sqlite3").resolve()

    def racing_link(_source, target, *, follow_symlinks):
        del follow_symlinks
        Path(target).write_bytes(b"racing-owner")
        raise FileExistsError

    monkeypatch.setattr(local_data_module.os, "link", racing_link)
    with pytest.raises(EcosystemConflict, match="ECO_RESTORE_DESTINATION_EXISTS"):
        store.restore_to_new(backup_path=backup_path, destination=destination)
    assert destination.read_bytes() == b"racing-owner"
    assert open_count == 1


def test_json_preview_rejects_oversize_sources_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "oversize.json"
    source.write_bytes(b"[123456]")
    monkeypatch.setattr(local_data_module, "_MAX_MIGRATION_SOURCE_BYTES", 4)
    with pytest.raises(
        EcosystemLocalDataError,
        match="ECO_MIGRATION_SOURCE_SIZE_LIMIT_EXCEEDED",
    ):
        JsonCompatibilityReader().preview(source)


def test_schema_shape_validation_rejects_name_only_counterfeits(
    tmp_path: Path,
) -> None:
    database_path = (tmp_path / "malformed.sqlite3").resolve()
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE eco_workspaces (workspace_ref TEXT);
        CREATE TABLE eco_schema_migrations (
            schema_version INTEGER PRIMARY KEY,
            schema_ref TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        );
        CREATE TABLE eco_records (workspace_ref TEXT);
        CREATE TABLE eco_search_tokens (workspace_ref TEXT);
        CREATE TABLE eco_uow_receipts (workspace_ref TEXT);
        CREATE TABLE eco_events (event_ref TEXT);
        CREATE TABLE eco_record_tombstones (workspace_ref TEXT);
        CREATE TABLE eco_key_cleanup (workspace_ref TEXT);
        INSERT INTO eco_schema_migrations VALUES (
            1, 'schema-ref:ecosystem-local-data:v1', '2026-08-20T00:00:00Z'
        );
        PRAGMA user_version = 1;
        """
    )
    connection.close()
    with pytest.raises(EcosystemLocalDataError, match="ECO_SCHEMA_SHAPE_INVALID"):
        AuthorizedTestStore(
            database_path=database_path,
            crypto_backend=InMemoryLocalDataCryptoBackend(),
        )


def test_backup_publication_fsyncs_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, backend = _store(tmp_path)
    backend.create(
        key_item_ref="key-item-ref:backup", key_version_ref="key-version-ref:backup-v1"
    )
    destination = (tmp_path / "durable" / "snapshot.uaabackup").resolve()
    fsynced: list[Path] = []
    original_fsync = local_data_module._fsync_directory

    def capture_fsync(path: Path) -> None:
        fsynced.append(path)
        original_fsync(path)

    monkeypatch.setattr(local_data_module, "_fsync_directory", capture_fsync)
    store.create_backup(
        destination=destination,
        backup_ref="backup-ref:test-one",
        key_item_ref="key-item-ref:backup",
        key_version_ref="key-version-ref:backup-v1",
    )
    assert destination.parent in fsynced
