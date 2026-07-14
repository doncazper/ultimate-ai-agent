from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ultimate_ai_agent.core.storage.founder_loop import (
    FOUNDER_LOOP_SCHEMA_VERSION,
    FounderLoopRepository,
    FounderLoopStorageMigrationRequiredError,
    JsonlLogKind,
)
from ultimate_ai_agent.core.storage.founder_loop_recovery import (
    FOUNDER_LOOP_BACKUP_SAFETY_MARGIN_BYTES,
    FounderLoopRecoveryError,
    create_founder_loop_backup,
    restore_founder_loop_backup,
    verify_founder_loop_backup,
)


def _repository_with_state(state_dir: Path) -> FounderLoopRepository:
    repository = FounderLoopRepository(state_dir, seed_defaults=False)
    repository.record_idempotency_key(
        key_ref="idempotency-ref:recovery:roundtrip",
        scope_ref="scope-ref:recovery:roundtrip",
        receipt_ref="receipt-ref:recovery:roundtrip",
    )
    repository.append_log(
        JsonlLogKind.receipt,
        {
            "event_ref": "event-ref:recovery:roundtrip",
            "safe_summary": "Redacted recovery round-trip receipt.",
            "evidence_refs": ["evidence-ref:recovery:roundtrip"],
        },
    )
    return repository


def test_actual_founder_loop_store_backup_and_restore_round_trip(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    backup = tmp_path / "backup"
    restored = tmp_path / "restored"
    source_repository = _repository_with_state(source)

    created = create_founder_loop_backup(source, backup)
    verified = verify_founder_loop_backup(backup)
    restored_receipt = restore_founder_loop_backup(backup, restored)
    restored_repository = FounderLoopRepository(
        restored,
        seed_defaults=False,
        ensure_storage=False,
        read_only=True,
    )

    assert created["status"] == "created"
    assert verified["status"] == "verified"
    assert restored_receipt["status"] == "restored"
    assert (
        restored_receipt["rollback_posture"] == "target_untouched_until_atomic_publish"
    )
    assert (
        restored_repository.storage_status()["counts"]
        == source_repository.storage_status()["counts"]
    )
    restored_log = restored / "logs" / "receipt.jsonl"
    assert json.loads(restored_log.read_text(encoding="utf-8"))["event_ref"] == (
        "event-ref:recovery:roundtrip"
    )
    assert json.dumps(restored_receipt).find(str(tmp_path)) == -1


def test_corrupt_backup_is_rejected_before_restore(tmp_path: Path) -> None:
    source = tmp_path / "source"
    backup = tmp_path / "backup"
    _repository_with_state(source)
    create_founder_loop_backup(source, backup)
    with (backup / "logs" / "receipt.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("not-json\n")

    with pytest.raises(
        FounderLoopRecoveryError,
        match="FOUNDER_LOOP_BACKUP_INTEGRITY_MISMATCH",
    ):
        restore_founder_loop_backup(backup, tmp_path / "restored")

    assert not (tmp_path / "restored").exists()


def test_low_disk_preflight_leaves_source_and_target_untouched(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _repository_with_state(source)

    with pytest.raises(
        FounderLoopRecoveryError,
        match="FOUNDER_LOOP_RECOVERY_LOW_DISK",
    ):
        create_founder_loop_backup(
            source,
            tmp_path / "backup",
            available_bytes=FOUNDER_LOOP_BACKUP_SAFETY_MARGIN_BYTES - 1,
        )

    assert (source / "founder_loop.sqlite3").is_file()
    assert not (tmp_path / "backup").exists()


def test_interrupted_backup_and_restore_are_atomic(tmp_path: Path) -> None:
    source = tmp_path / "source"
    backup = tmp_path / "backup"
    _repository_with_state(source)

    def fail_backup(phase: str) -> None:
        if phase == "before_publish":
            raise RuntimeError("synthetic interruption")

    with pytest.raises(RuntimeError, match="synthetic interruption"):
        create_founder_loop_backup(source, backup, fault_hook=fail_backup)
    assert not backup.exists()

    create_founder_loop_backup(source, backup)

    def fail_restore(phase: str) -> None:
        if phase == "before_restore_publish":
            raise RuntimeError("synthetic interruption")

    restored = tmp_path / "restored"
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        restore_founder_loop_backup(backup, restored, fault_hook=fail_restore)
    assert not restored.exists()


def test_unknown_storage_schema_is_not_silently_overwritten(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    FounderLoopRepository(state_dir, seed_defaults=False)
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        conn.execute(
            "UPDATE storage_metadata SET value = ? WHERE key = 'schema_version'",
            ("founder_loop_storage.v999",),
        )

    with pytest.raises(
        FounderLoopStorageMigrationRequiredError,
        match="FOUNDER_LOOP_STORAGE_MIGRATION_REQUIRED",
    ):
        FounderLoopRepository(state_dir, seed_defaults=False)

    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        stored = conn.execute(
            "SELECT value FROM storage_metadata WHERE key = 'schema_version'"
        ).fetchone()
    assert stored == ("founder_loop_storage.v999",)


def test_storage_bootstrap_records_explicit_migration_history(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    FounderLoopRepository(state_dir, seed_defaults=False)

    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        row = conn.execute(
            "SELECT migration_ref, schema_version FROM storage_migrations"
        ).fetchone()

    assert row == (
        "migration-ref:founder-loop:bootstrap-v1",
        FOUNDER_LOOP_SCHEMA_VERSION,
    )
