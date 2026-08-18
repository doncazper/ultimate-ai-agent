"""Crash-safe, content-addressed storage for system map snapshots."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import threading
from typing import Iterator
import uuid

from ultimate_ai_agent.core.system_map.models import SystemMapSnapshot


class SystemMapSnapshotStore:
    """Persist immutable history plus an atomically replaced current snapshot."""

    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.snapshots_dir = self.state_dir / "snapshots"
        self.current_path = self.state_dir / "current.json"
        self.lock_path = self.state_dir / ".system-map.lock"
        self._lock = threading.RLock()

    def save(self, snapshot: SystemMapSnapshot) -> str:
        validated = SystemMapSnapshot.model_validate(snapshot.model_dump(mode="json"))
        payload = (
            json.dumps(validated.model_dump(mode="json"), indent=2, sort_keys=True)
            + "\n"
        )
        digest = validated.snapshot_ref.rsplit(":", 1)[-1]
        history_path = self.snapshots_dir / f"{digest}.json"
        with self._locked_file():
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)
            if history_path.exists():
                existing = history_path.read_text(encoding="utf-8")
                if existing != payload:
                    raise ValueError("SYSTEM_MAP_HISTORY_CONTENT_CONFLICT")
            else:
                self._atomic_write(history_path, payload)
            self._atomic_write(self.current_path, payload)
            self._fsync_directory(self.snapshots_dir)
            self._fsync_directory(self.state_dir)
        return validated.snapshot_ref

    def load_current(self) -> SystemMapSnapshot:
        with self._locked_file():
            if not self.current_path.exists():
                raise FileNotFoundError("SYSTEM_MAP_CURRENT_SNAPSHOT_MISSING")
            snapshot = self._load_path(self.current_path)
            history_path = self.snapshot_path(snapshot.snapshot_ref)
            if not history_path.exists():
                raise ValueError("SYSTEM_MAP_CURRENT_HISTORY_MISSING")
            history = self._load_path(history_path)
            if history != snapshot:
                raise ValueError("SYSTEM_MAP_CURRENT_HISTORY_MISMATCH")
            return snapshot

    def load(self, snapshot_ref: str) -> SystemMapSnapshot:
        with self._locked_file():
            path = self.snapshot_path(snapshot_ref)
            if not path.exists():
                raise FileNotFoundError("SYSTEM_MAP_SNAPSHOT_NOT_FOUND")
            return self._load_history_path(path, snapshot_ref)

    def list_snapshot_refs(self) -> tuple[str, ...]:
        with self._locked_file():
            if not self.snapshots_dir.exists():
                return ()
            refs = []
            for path in sorted(self.snapshots_dir.glob("*.json")):
                expected_ref = f"system-map-snapshot:sha256:{path.stem}"
                refs.append(self._load_history_path(path, expected_ref).snapshot_ref)
            return tuple(refs)

    def snapshot_path(self, snapshot_ref: str) -> Path:
        prefix = "system-map-snapshot:sha256:"
        if not snapshot_ref.startswith(prefix):
            raise ValueError("SYSTEM_MAP_SNAPSHOT_REF_INVALID")
        digest = snapshot_ref.removeprefix(prefix)
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("SYSTEM_MAP_SNAPSHOT_REF_INVALID")
        return self.snapshots_dir / f"{digest}.json"

    @staticmethod
    def _load_path(path: Path) -> SystemMapSnapshot:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return SystemMapSnapshot.model_validate(payload)

    @classmethod
    def _load_history_path(cls, path: Path, expected_ref: str) -> SystemMapSnapshot:
        snapshot = cls._load_path(path)
        if snapshot.snapshot_ref != expected_ref:
            raise ValueError("SYSTEM_MAP_HISTORY_REF_MISMATCH")
        return snapshot

    @staticmethod
    def _atomic_write(path: Path, payload: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp_path.open("x", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        try:
            directory_fd = os.open(path, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    @contextmanager
    def _locked_file(self) -> Iterator[None]:
        with self._lock:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            with self.lock_path.open("a+", encoding="utf-8") as lock_file:
                try:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                except (ImportError, OSError):
                    pass
                try:
                    yield
                finally:
                    try:
                        import fcntl

                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    except (ImportError, OSError):
                        pass
