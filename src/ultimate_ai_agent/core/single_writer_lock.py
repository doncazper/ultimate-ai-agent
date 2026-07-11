from __future__ import annotations

import threading
import uuid
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class SingleWriterLockManager:
    def __init__(self) -> None:
        self._guard = threading.RLock()
        self._locks: dict[str, threading.RLock] = {}

    @contextmanager
    def acquire(self, writer_key: str) -> Iterator[str]:
        with self._guard:
            lock = self._locks.setdefault(writer_key, threading.RLock())
        lease_id = f"lease_{uuid.uuid4().hex[:16]}"
        with lock:
            yield lease_id


class FileSingleWriterLockManager:
    def __init__(self, lock_dir: str | Path) -> None:
        self.lock_dir = Path(lock_dir)

    @contextmanager
    def acquire(self, writer_key: str) -> Iterator[str]:
        safe_name = "".join(
            ch if ch.isalnum() or ch in "._-" else "_" for ch in writer_key
        )
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        directory_metadata = os.lstat(self.lock_dir)
        if not stat.S_ISDIR(directory_metadata.st_mode):
            raise OSError("single-writer lock directory must be a real directory")
        lock_path = self.lock_dir / f"{safe_name}.lock"
        global_key = f"{self.lock_dir.resolve()}:{safe_name}"
        with _FILE_LOCAL_LOCKS.acquire(global_key):
            depths = getattr(_FILE_LOCK_DEPTHS, "values", {})
            if depths.get(global_key, 0):
                depths[global_key] += 1
                _FILE_LOCK_DEPTHS.values = depths
                try:
                    yield f"file_lease_{uuid.uuid4().hex[:16]}"
                finally:
                    depths[global_key] -= 1
                return
            flags = (
                os.O_RDWR
                | os.O_APPEND
                | os.O_CREAT
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
            )
            descriptor = os.open(lock_path, flags, 0o600)
            try:
                metadata = os.fstat(descriptor)
                path_metadata = os.lstat(lock_path)
                if (
                    not stat.S_ISREG(metadata.st_mode)
                    or metadata.st_nlink != 1
                    or (metadata.st_dev, metadata.st_ino)
                    != (path_metadata.st_dev, path_metadata.st_ino)
                ):
                    raise OSError("single-writer lock must be a regular file")
                os.fchmod(descriptor, 0o600)
                try:
                    import fcntl
                except ImportError:
                    fcntl = None
                if fcntl is not None:
                    fcntl.flock(descriptor, fcntl.LOCK_EX)
                depths[global_key] = 1
                _FILE_LOCK_DEPTHS.values = depths
                try:
                    yield f"file_lease_{uuid.uuid4().hex[:16]}"
                finally:
                    depths.pop(global_key, None)
                    if fcntl is not None:
                        fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)


_FILE_LOCAL_LOCKS = SingleWriterLockManager()
_FILE_LOCK_DEPTHS = threading.local()
