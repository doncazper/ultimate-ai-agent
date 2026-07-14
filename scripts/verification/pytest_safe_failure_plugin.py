from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scripts.verification.pytest_shard_artifacts import (
    FAILED_TEST_REFS_SCHEMA_VERSION,
    MAX_FAILED_TEST_REFS_PER_SHARD,
    safe_test_ref,
)


_FAILED_TEST_REFS: list[str] = []


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--uaa-safe-failure-report",
        action="store",
        default=None,
        help="Write bounded content-free failed-test refs.",
    )


def pytest_runtest_logreport(report: Any) -> None:
    if not report.failed or len(_FAILED_TEST_REFS) >= MAX_FAILED_TEST_REFS_PER_SHARD:
        return
    test_ref = safe_test_ref(str(report.nodeid))
    if test_ref not in _FAILED_TEST_REFS:
        _FAILED_TEST_REFS.append(test_ref)


def _write_safe_failure_report(path: Path, refs: list[str]) -> None:
    payload = json.dumps(
        {
            "schema_version": FAILED_TEST_REFS_SCHEMA_VERSION,
            "failed_test_refs": refs[:MAX_FAILED_TEST_REFS_PER_SHARD],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("safe failure report write did not make progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    del exitstatus
    output = session.config.getoption("--uaa-safe-failure-report")
    if not output:
        return
    _write_safe_failure_report(Path(output), _FAILED_TEST_REFS)
