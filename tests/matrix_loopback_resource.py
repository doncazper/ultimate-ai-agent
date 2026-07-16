from __future__ import annotations

import fcntl
import os
import stat
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


_LOCK_PATH = Path("/tmp") / "uaa-matrix-loopback-test-resource-v1.lock"
_LOCK_WAIT_SECONDS = 60.0


@contextmanager
def matrix_loopback_test_resource() -> Iterator[None]:
    descriptor = _open_shared_lock()
    deadline = time.monotonic() + _LOCK_WAIT_SECONDS
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("MATRIX_TEST_HARNESS_RESOURCE_BUSY") from None
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _open_shared_lock() -> int:
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(_LOCK_PATH, flags, 0o600)
    except OSError as exc:
        raise RuntimeError("MATRIX_TEST_HARNESS_RESOURCE_LOCK_UNSAFE") from exc
    try:
        metadata = os.fstat(descriptor)
        if metadata.st_uid == os.getuid():
            os.fchmod(descriptor, 0o600)
            metadata = os.fstat(descriptor)
        path_metadata = os.lstat(_LOCK_PATH)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("MATRIX_TEST_HARNESS_RESOURCE_LOCK_UNSAFE")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise
