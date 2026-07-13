from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

from ultimate_ai_agent.core.evidence_signing.portable import (
    PORTABLE_EVIDENCE_SIGNED_MAX_BYTES,
    PortableEvidenceSignedArtifact,
)

PORTABLE_EVIDENCE_SIGNED_ARTIFACT_MAX_FILES = 1_000


class PortableEvidenceSignedArtifactStoreError(RuntimeError):
    pass


class PortableEvidenceSignedArtifactStore:
    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.directory = self.state_dir / "signed_artifacts"

    @property
    def store_ref(self) -> str:
        digest = hashlib.sha256(
            os.fspath(self.state_dir.absolute()).encode("utf-8")
        ).hexdigest()
        return f"artifact-store-ref:portable-evidence:sha256:{digest}"

    def save(
        self,
        *,
        dispatch_ref: str,
        artifact: PortableEvidenceSignedArtifact,
    ) -> PortableEvidenceSignedArtifact:
        self._ensure_directory()
        target = self._path(dispatch_ref)
        temporary = self.directory / f".{target.name}.pending"
        self._reconcile_pending(target=target, temporary=temporary)
        encoded = (artifact.model_dump_json() + "\n").encode("utf-8")
        if len(encoded) > PORTABLE_EVIDENCE_SIGNED_MAX_BYTES:
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_TOO_LARGE"
            )
        if target.exists() or target.is_symlink():
            existing = self.load(dispatch_ref=dispatch_ref)
            if existing != artifact:
                raise PortableEvidenceSignedArtifactStoreError(
                    "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_CONFLICT"
                )
            return existing
        if self._artifact_count() >= PORTABLE_EVIDENCE_SIGNED_ARTIFACT_MAX_FILES:
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_STORE_FULL"
            )
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            if os.write(descriptor, encoded) != len(encoded):
                raise PortableEvidenceSignedArtifactStoreError(
                    "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_SHORT_WRITE"
                )
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(temporary, target, follow_symlinks=False)
            self._fsync_directory()
        finally:
            temporary.unlink(missing_ok=True)
        return self.load(dispatch_ref=dispatch_ref)

    def load(self, *, dispatch_ref: str) -> PortableEvidenceSignedArtifact:
        self._ensure_directory()
        path = self._path(dispatch_ref)
        temporary = self.directory / f".{path.name}.pending"
        self._reconcile_pending(target=path, temporary=temporary)
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0),
        )
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_mode & 0o077
                or metadata.st_size > PORTABLE_EVIDENCE_SIGNED_MAX_BYTES
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise PortableEvidenceSignedArtifactStoreError(
                    "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_FILE_INVALID"
                )
            raw = os.read(descriptor, PORTABLE_EVIDENCE_SIGNED_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
        try:
            return PortableEvidenceSignedArtifact.model_validate_json(raw)
        except ValueError as exc:
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_INVALID"
            ) from exc

    def _path(self, dispatch_ref: str) -> Path:
        digest = hashlib.sha256(dispatch_ref.encode("utf-8")).hexdigest()
        return self.directory / f"{digest}.json"

    def _ensure_directory(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        state_metadata = os.lstat(self.state_dir)
        if (
            not stat.S_ISDIR(state_metadata.st_mode)
            or stat.S_ISLNK(state_metadata.st_mode)
            or state_metadata.st_uid != os.getuid()
            or state_metadata.st_mode & 0o077
        ):
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_STATE_DIR_INVALID"
            )
        self.directory.mkdir(exist_ok=True, mode=0o700)
        metadata = os.lstat(self.directory)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_DIR_INVALID"
            )

    def _artifact_count(self) -> int:
        count = 0
        with os.scandir(self.directory) as entries:
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                count += 1
                if count > PORTABLE_EVIDENCE_SIGNED_ARTIFACT_MAX_FILES:
                    break
        return count

    def _reconcile_pending(self, *, target: Path, temporary: Path) -> None:
        try:
            pending = os.lstat(temporary)
        except FileNotFoundError:
            return
        if (
            not stat.S_ISREG(pending.st_mode)
            or pending.st_uid != os.getuid()
            or pending.st_mode & 0o077
            or pending.st_nlink not in {1, 2}
        ):
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_PENDING_INVALID"
            )
        try:
            committed = os.lstat(target)
        except FileNotFoundError:
            if pending.st_nlink != 1:
                raise PortableEvidenceSignedArtifactStoreError(
                    "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_PENDING_INVALID"
                )
            temporary.unlink()
            self._fsync_directory()
            return
        if (
            not stat.S_ISREG(committed.st_mode)
            or committed.st_uid != os.getuid()
            or committed.st_mode & 0o077
            or committed.st_nlink != 2
            or pending.st_nlink != 2
            or (committed.st_dev, committed.st_ino) != (pending.st_dev, pending.st_ino)
        ):
            raise PortableEvidenceSignedArtifactStoreError(
                "PORTABLE_EVIDENCE_SIGNED_ARTIFACT_PENDING_CONFLICT"
            )
        temporary.unlink()
        self._fsync_directory()

    def _fsync_directory(self) -> None:
        descriptor = os.open(
            self.directory,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
