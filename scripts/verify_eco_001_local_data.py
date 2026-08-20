#!/usr/bin/env python3
"""Verify the bounded ECO-001 shared local-data foundation."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from ultimate_ai_agent.core.ecosystem.local_data import (
    ECO_LOCAL_DATA_SCHEMA_REF,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    PutRecord,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/local_data.py",
    "tests/test_eco_001_local_data.py",
    "docs/architecture/ECO_001_SHARED_LOCAL_DATA_FOUNDATION.md",
    "docs/decisions/ADR-0056-shared-local-application-data-platform-direction.md",
)
FORBIDDEN_SOURCE_MARKERS = (
    "os.environ",
    "requests.",
    "httpx.",
    "urllib.request",
    "subprocess.",
)


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-001 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in source:
            failures.append(f"forbidden ECO-001 runtime marker: {marker}")
    if "in-memory-test-only" not in source:
        failures.append("test key backend must remain explicitly test-only")

    private_marker = "synthetic-private-marker-eco001"
    try:
        with tempfile.TemporaryDirectory() as directory:
            database_path = (Path(directory) / "ecosystem.sqlite3").resolve()
            backend = InMemoryLocalDataCryptoBackend()
            platform = EcosystemLocalDataPlatform(
                database_path=database_path, crypto_backend=backend
            )
            platform.create_workspace(workspace_ref="workspace-ref:verification")
            platform.apply(
                workspace_ref="workspace-ref:verification",
                idempotency_ref="idempotency-ref:verification",
                operations=(
                    PutRecord(
                        operation_ref="operation-ref:verification",
                        module_ref="module-ref:verification",
                        record_ref="record-ref:verification",
                        record_kind_ref="record-kind-ref:verification",
                        safe_summary_ref="summary-ref:verification",
                        private_payload={"value": private_marker},
                        search_terms=(private_marker,),
                    ),
                ),
            )
            connection = sqlite3.connect(database_path)
            try:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            finally:
                connection.close()
            if version != 1:
                failures.append("ECO-001 schema version mismatch")
            if private_marker.encode() in database_path.read_bytes():
                failures.append("private marker leaked into SQLite data plane")
            if platform.integrity_check().schema_ref != ECO_LOCAL_DATA_SCHEMA_REF:
                failures.append("ECO-001 integrity schema binding mismatch")
    except Exception as exc:
        failures.append(f"ECO-001 smoke verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: ECO-001 shared local-data foundation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
