"""Lightweight child target for real cross-process file-lock tests.

Keep this module standard-library-only: spawn imports the target module before
the child can signal readiness, so product/test imports consume the lock test's
startup budget without exercising the lock under test.
"""

import fcntl
import os
from pathlib import Path
import time


def hold_file_lock(
    lock_path: Path,
    started_path: Path,
    release_path: Path,
) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        started_path.write_text("started", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not release_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
