from __future__ import annotations

import os
import stat
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - Windows
    _fcntl = None

try:
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - POSIX
    _msvcrt = None


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
        global_key = _file_local_lock_key(directory_metadata, safe_name)
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
                _set_owner_only_mode(descriptor, lock_path)
                lock_backend = _acquire_interprocess_lock(descriptor)
                depths[global_key] = 1
                _FILE_LOCK_DEPTHS.values = depths
                try:
                    yield f"file_lease_{uuid.uuid4().hex[:16]}"
                finally:
                    depths.pop(global_key, None)
                    _release_interprocess_lock(descriptor, lock_backend)
            finally:
                os.close(descriptor)

    @contextmanager
    def acquire_from_parent(
        self,
        parent_descriptor: int,
        lock_dir_name: str,
        writer_key: str,
    ) -> Iterator[str]:
        """Acquire a lock without reopening an already-pinned parent by path."""

        if (
            not lock_dir_name
            or "/" in lock_dir_name
            or lock_dir_name in {".", ".."}
        ):
            raise OSError("single-writer lock directory name is invalid")
        safe_name = "".join(
            ch if ch.isalnum() or ch in "._-" else "_" for ch in writer_key
        )
        try:
            os.mkdir(lock_dir_name, mode=0o700, dir_fd=parent_descriptor)
        except FileExistsError:
            pass
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        directory_descriptor = os.open(
            lock_dir_name,
            directory_flags,
            dir_fd=parent_descriptor,
        )
        try:
            directory_metadata = os.fstat(directory_descriptor)
            linked_directory_metadata = os.stat(
                lock_dir_name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISDIR(directory_metadata.st_mode)
                or stat.S_ISLNK(linked_directory_metadata.st_mode)
                or (directory_metadata.st_dev, directory_metadata.st_ino)
                != (
                    linked_directory_metadata.st_dev,
                    linked_directory_metadata.st_ino,
                )
            ):
                raise OSError(
                    "single-writer lock directory must be a real directory"
                )
            global_key = _file_local_lock_key(
                directory_metadata,
                safe_name,
            )
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
                lock_name = f"{safe_name}.lock"
                descriptor = os.open(
                    lock_name,
                    flags,
                    0o600,
                    dir_fd=directory_descriptor,
                )
                try:
                    metadata = os.fstat(descriptor)
                    path_metadata = os.stat(
                        lock_name,
                        dir_fd=directory_descriptor,
                        follow_symlinks=False,
                    )
                    if (
                        not stat.S_ISREG(metadata.st_mode)
                        or metadata.st_nlink != 1
                        or (metadata.st_dev, metadata.st_ino)
                        != (path_metadata.st_dev, path_metadata.st_ino)
                    ):
                        raise OSError("single-writer lock must be a regular file")
                    _set_owner_only_mode(
                        descriptor,
                        self.lock_dir / lock_name,
                    )
                    lock_backend = _acquire_interprocess_lock(descriptor)
                    depths[global_key] = 1
                    _FILE_LOCK_DEPTHS.values = depths
                    try:
                        yield f"file_lease_{uuid.uuid4().hex[:16]}"
                    finally:
                        depths.pop(global_key, None)
                        _release_interprocess_lock(descriptor, lock_backend)
                finally:
                    os.close(descriptor)
        finally:
            os.close(directory_descriptor)


_FILE_LOCAL_LOCKS = SingleWriterLockManager()
_FILE_LOCK_DEPTHS = threading.local()


def _set_owner_only_mode(descriptor: int, path: Path) -> None:
    fchmod = getattr(os, "fchmod", None)
    if fchmod is not None:
        fchmod(descriptor, 0o600)
        return
    os.chmod(path, 0o600)


def _acquire_interprocess_lock(descriptor: int) -> str | None:
    if _fcntl is not None:
        _fcntl.flock(descriptor, _fcntl.LOCK_EX)
        return "fcntl"
    if _msvcrt is None:
        return None
    if os.fstat(descriptor).st_size == 0:
        os.write(descriptor, b"\0")
        os.fsync(descriptor)
    os.lseek(descriptor, 0, os.SEEK_SET)
    _msvcrt.locking(descriptor, _msvcrt.LK_LOCK, 1)
    return "msvcrt"


def _release_interprocess_lock(descriptor: int, backend: str | None) -> None:
    if backend == "fcntl":
        assert _fcntl is not None
        _fcntl.flock(descriptor, _fcntl.LOCK_UN)
    elif backend == "msvcrt":
        assert _msvcrt is not None
        os.lseek(descriptor, 0, os.SEEK_SET)
        _msvcrt.locking(descriptor, _msvcrt.LK_UNLCK, 1)


def _file_local_lock_key(directory_metadata: os.stat_result, safe_name: str) -> str:
    return (
        f"dir:{directory_metadata.st_dev}:{directory_metadata.st_ino}:"
        f"{safe_name}"
    )
