from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.storage.founder_loop import JsonlLogKind
from ultimate_ai_agent.core.founder_loop_schema import FOUNDER_LOOP_SCHEMA_VERSION


FOUNDER_LOOP_BACKUP_SCHEMA_VERSION = "founder_loop_backup.v1"
FOUNDER_LOOP_BACKUP_MANIFEST_NAME = "manifest.json"
FOUNDER_LOOP_SQLITE_NAMES = (
    "founder_loop.sqlite3",
    "memory_review_recall.sqlite3",
)
FOUNDER_LOOP_BACKUP_SAFETY_MARGIN_BYTES = 1_048_576


class FounderLoopRecoveryError(RuntimeError):
    pass


FaultHook = Callable[[str], None]


def create_founder_loop_backup(
    state_dir: Path,
    backup_dir: Path,
    *,
    available_bytes: int | None = None,
    fault_hook: FaultHook | None = None,
) -> dict[str, Any]:
    source_db = state_dir / "founder_loop.sqlite3"
    if not source_db.is_file():
        raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_SOURCE_MISSING")
    if backup_dir.exists():
        raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_TARGET_EXISTS")

    artifacts = _source_artifacts(state_dir)
    required_bytes = sum(path.stat().st_size for _, path, _ in artifacts)
    _require_capacity(
        backup_dir.parent,
        required_bytes + FOUNDER_LOOP_BACKUP_SAFETY_MARGIN_BYTES,
        available_bytes,
    )
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".uaa-founder-loop-backup-", dir=backup_dir.parent)
    )
    try:
        artifact_records: list[dict[str, Any]] = []
        for index, (relative_name, source, artifact_kind) in enumerate(artifacts):
            target = staging / relative_name
            target.parent.mkdir(parents=True, exist_ok=True)
            if artifact_kind == "sqlite":
                _backup_sqlite(source, target)
                _assert_sqlite_integrity(target)
            else:
                _copy_fsync(source, target)
                _assert_jsonl_integrity(target)
            artifact_records.append(
                _artifact_record(relative_name, target, artifact_kind)
            )
            _fault(fault_hook, f"after_artifact:{index}")

        manifest = {
            "schema_version": FOUNDER_LOOP_BACKUP_SCHEMA_VERSION,
            "storage_schema_version": _storage_schema_version(
                staging / "founder_loop.sqlite3"
            ),
            "backup_ref": "backup-ref:founder-loop:offline-snapshot",
            "source_ref": "storage-ref:founder-loop:local-state",
            "artifact_count": len(artifact_records),
            "artifacts": artifact_records,
            "offline_restore_supported": True,
            "live_restore_supported": False,
            "raw_paths_included": False,
            "raw_content_included": False,
            "integrity_check": "sqlite-quick-check-and-sha256",
        }
        _write_json_fsync(staging / FOUNDER_LOOP_BACKUP_MANIFEST_NAME, manifest)
        _fault(fault_hook, "before_publish")
        os.replace(staging, backup_dir)
        _fsync_directory(backup_dir.parent)
        return _backup_receipt(manifest, "created")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_founder_loop_backup(backup_dir: Path) -> dict[str, Any]:
    manifest = _read_manifest(backup_dir)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_MANIFEST_EMPTY")
    for record in artifacts:
        if not isinstance(record, dict):
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_MANIFEST_INVALID")
        relative_name = record.get("relative_name")
        if (
            not isinstance(relative_name, str)
            or relative_name not in _allowed_relative_names()
        ):
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_ARTIFACT_DENIED")
        artifact = backup_dir / relative_name
        if not artifact.is_file():
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_ARTIFACT_MISSING")
        if _sha256(artifact) != record.get("sha256"):
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_INTEGRITY_MISMATCH")
        if artifact.stat().st_size != record.get("size_bytes"):
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_SIZE_MISMATCH")
        if record.get("artifact_kind") == "sqlite":
            _assert_sqlite_integrity(artifact)
        elif record.get("artifact_kind") == "jsonl":
            _assert_jsonl_integrity(artifact)
        else:
            raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_KIND_INVALID")
    if manifest.get("storage_schema_version") != FOUNDER_LOOP_SCHEMA_VERSION:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_SCHEMA_INCOMPATIBLE")
    return _backup_receipt(manifest, "verified")


def restore_founder_loop_backup(
    backup_dir: Path,
    target_state_dir: Path,
    *,
    available_bytes: int | None = None,
    fault_hook: FaultHook | None = None,
) -> dict[str, Any]:
    if target_state_dir.exists():
        raise FounderLoopRecoveryError("FOUNDER_LOOP_RESTORE_TARGET_EXISTS")
    verification = verify_founder_loop_backup(backup_dir)
    manifest = _read_manifest(backup_dir)
    required_bytes = sum(int(item["size_bytes"]) for item in manifest["artifacts"])
    _require_capacity(
        target_state_dir.parent,
        required_bytes + FOUNDER_LOOP_BACKUP_SAFETY_MARGIN_BYTES,
        available_bytes,
    )
    target_state_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=".uaa-founder-loop-restore-", dir=target_state_dir.parent
        )
    )
    try:
        for index, record in enumerate(manifest["artifacts"]):
            relative_name = str(record["relative_name"])
            source = backup_dir / relative_name
            target = staging / relative_name
            target.parent.mkdir(parents=True, exist_ok=True)
            _copy_fsync(source, target)
            _fault(fault_hook, f"after_restore_artifact:{index}")
        _assert_sqlite_integrity(staging / "founder_loop.sqlite3")
        _fault(fault_hook, "before_restore_publish")
        os.replace(staging, target_state_dir)
        _fsync_directory(target_state_dir.parent)
        return {
            **verification,
            "status": "restored",
            "restore_ref": "restore-ref:founder-loop:offline-snapshot",
            "rollback_posture": "target_untouched_until_atomic_publish",
        }
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _source_artifacts(state_dir: Path) -> list[tuple[str, Path, str]]:
    artifacts: list[tuple[str, Path, str]] = []
    for name in FOUNDER_LOOP_SQLITE_NAMES:
        path = state_dir / name
        if path.is_file():
            artifacts.append((name, path, "sqlite"))
    for kind in JsonlLogKind:
        relative_name = f"logs/{kind.value}.jsonl"
        path = state_dir / relative_name
        if path.is_file():
            artifacts.append((relative_name, path, "jsonl"))
    return artifacts


def _allowed_relative_names() -> set[str]:
    return {
        *FOUNDER_LOOP_SQLITE_NAMES,
        *(f"logs/{kind.value}.jsonl" for kind in JsonlLogKind),
    }


def _backup_sqlite(source: Path, target: Path) -> None:
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as source_conn:
        with sqlite3.connect(target) as target_conn:
            source_conn.backup(target_conn)
            target_conn.commit()


def _assert_sqlite_integrity(path: Path) -> None:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
            result = conn.execute("PRAGMA quick_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_SQLITE_CORRUPT") from exc
    if result is None or result[0] != "ok":
        raise FounderLoopRecoveryError("FOUNDER_LOOP_SQLITE_INTEGRITY_FAILED")


def _storage_schema_version(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        row = conn.execute(
            "SELECT value FROM storage_metadata WHERE key = 'schema_version' LIMIT 1"
        ).fetchone()
    if row is None:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_STORAGE_SCHEMA_MISSING")
    return str(row[0])


def _assert_jsonl_integrity(path: Path) -> None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record must be an object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_JSONL_CORRUPT") from exc


def _artifact_record(
    relative_name: str, path: Path, artifact_kind: str
) -> dict[str, Any]:
    return {
        "artifact_ref": f"backup-artifact-ref:founder-loop:{relative_name.replace('/', ':').replace('.', '-')}",
        "relative_name": relative_name,
        "artifact_kind": artifact_kind,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _backup_receipt(manifest: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "schema_version": FOUNDER_LOOP_BACKUP_SCHEMA_VERSION,
        "status": status,
        "backup_ref": manifest["backup_ref"],
        "storage_schema_version": manifest["storage_schema_version"],
        "artifact_count": manifest["artifact_count"],
        "integrity_check": manifest["integrity_check"],
        "safe_refs_only": True,
        "raw_paths_included": False,
        "raw_content_included": False,
    }


def _read_manifest(backup_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            (backup_dir / FOUNDER_LOOP_BACKUP_MANIFEST_NAME).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FounderLoopRecoveryError(
            "FOUNDER_LOOP_BACKUP_MANIFEST_UNAVAILABLE"
        ) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != FOUNDER_LOOP_BACKUP_SCHEMA_VERSION
    ):
        raise FounderLoopRecoveryError("FOUNDER_LOOP_BACKUP_MANIFEST_INVALID")
    return payload


def _copy_fsync(source: Path, target: Path) -> None:
    with source.open("rb") as source_handle, target.open("xb") as target_handle:
        shutil.copyfileobj(source_handle, target_handle)
        target_handle.flush()
        os.fsync(target_handle.fileno())


def _write_json_fsync(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _require_capacity(
    parent: Path, required_bytes: int, available_bytes: int | None
) -> None:
    probe = parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    available = (
        shutil.disk_usage(probe).free if available_bytes is None else available_bytes
    )
    if available < required_bytes:
        raise FounderLoopRecoveryError("FOUNDER_LOOP_RECOVERY_LOW_DISK")


def _fault(fault_hook: FaultHook | None, phase: str) -> None:
    if fault_hook is not None:
        fault_hook(phase)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
