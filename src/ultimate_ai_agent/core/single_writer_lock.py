from __future__ import annotations

import threading
import uuid
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
        self._local = SingleWriterLockManager()

    @contextmanager
    def acquire(self, writer_key: str) -> Iterator[str]:
        safe_name = "".join(
            ch if ch.isalnum() or ch in "._-" else "_" for ch in writer_key
        )
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.lock_dir / f"{safe_name}.lock"
        with self._local.acquire(writer_key):
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                try:
                    import fcntl
                except ImportError:
                    fcntl = None
                if fcntl is None:
                    yield f"file_lease_{uuid.uuid4().hex[:16]}"
                    return
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield f"file_lease_{uuid.uuid4().hex[:16]}"
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
