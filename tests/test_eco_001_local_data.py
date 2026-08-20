from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

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


WORKSPACE_A = "workspace-ref:alpha"
WORKSPACE_B = "workspace-ref:beta"


def _store(
    tmp_path: Path,
    *,
    backend: InMemoryLocalDataCryptoBackend | None = None,
    fault_hook=None,
) -> tuple[EcosystemLocalDataPlatform, InMemoryLocalDataCryptoBackend]:
    selected = backend or InMemoryLocalDataCryptoBackend()
    store = EcosystemLocalDataPlatform(
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

    clean_store = EcosystemLocalDataPlatform(
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
    restored = EcosystemLocalDataPlatform(
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
    ).startswith("key-rotation-receipt-ref:ecosystem:")
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
        EcosystemLocalDataPlatform(
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
