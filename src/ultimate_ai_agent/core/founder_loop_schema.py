from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


FOUNDER_LOOP_SCHEMA_VERSION = "founder_loop_storage.v1"
FOUNDER_LOOP_BOOTSTRAP_MIGRATION_REF = "migration-ref:founder-loop:bootstrap-v1"


def require_compatible_schema(
    conn: sqlite3.Connection,
    *,
    migration_error: type[Exception],
) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    row = conn.execute(
        "SELECT value FROM storage_metadata WHERE key = 'schema_version' LIMIT 1"
    ).fetchone()
    if row is not None and str(row[0]) != FOUNDER_LOOP_SCHEMA_VERSION:
        raise migration_error("FOUNDER_LOOP_STORAGE_MIGRATION_REQUIRED")


def record_bootstrap_migration(conn: sqlite3.Connection, *, applied_at: str) -> None:
    conn.execute(
        """
        INSERT INTO storage_migrations (migration_ref, schema_version, applied_at)
        VALUES (?, ?, ?)
        ON CONFLICT(migration_ref) DO NOTHING
        """,
        (
            FOUNDER_LOOP_BOOTSTRAP_MIGRATION_REF,
            FOUNDER_LOOP_SCHEMA_VERSION,
            applied_at,
        ),
    )


def connect_founder_loop_sqlite(
    db_path: Path,
    *,
    read_only: bool,
) -> sqlite3.Connection:
    if read_only:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    else:
        conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def append_durable_jsonl(path: Path, encoded_record: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(encoded_record + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def backup_contract_manifest() -> dict[str, Any]:
    return {
        "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
        "manifest_ref": "backup-manifest:founder-loop-minimum-set",
        "required_artifact_refs": [
            "founder-loop-sqlite:local-state",
            "founder-loop-log:audit",
            "founder-loop-log:transcript",
            "founder-loop-log:realtime",
            "founder-loop-log:receipt",
        ],
        "raw_paths_included": False,
        "raw_logs_included": False,
        "safe_refs_only": True,
    }
