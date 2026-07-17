from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .contracts import stable_matrix_rooms_media_ref


class MatrixMediaError(RuntimeError):
    pass


_ALLOWED = {
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/gif": (".gif", b"GIF8"),
    "text/plain": (".txt", None),
}
_ARCHIVE_SIGNATURES = (b"PK\x03\x04", b"Rar!", b"7z\xbc\xaf\x27\x1c", b"\x1f\x8b")
_EXECUTABLE_SIGNATURES = (b"MZ", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")


@dataclass(frozen=True)
class MatrixMediaInspection:
    media_type: str
    byte_count: int
    content_fingerprint_ref: str


class MatrixMediaStore:
    def __init__(self, *, root: Path) -> None:
        if not root.is_absolute() or root == Path(root.anchor):
            raise ValueError("MATRIX_MEDIA_ROOT_UNSAFE")
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = os.lstat(root)
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
        ):
            raise ValueError("MATRIX_MEDIA_ROOT_UNSAFE")
        os.chmod(root, 0o700)
        info = os.lstat(root)
        self.root = root
        self._identity = (info.st_dev, info.st_ino)
        self._directory_identities: dict[str, tuple[int, int]] = {}
        for name in (
            "media-upload-source",
            "media-quarantine",
            "media-materialized",
        ):
            directory = root / name
            directory.mkdir(mode=0o700, exist_ok=True)
            directory_info = os.lstat(directory)
            if (
                not stat.S_ISDIR(directory_info.st_mode)
                or stat.S_ISLNK(directory_info.st_mode)
                or directory_info.st_uid != os.geteuid()
            ):
                raise ValueError("MATRIX_MEDIA_DIRECTORY_UNSAFE")
            os.chmod(directory, 0o700)
            directory_info = os.lstat(directory)
            self._directory_identities[name] = (
                directory_info.st_dev,
                directory_info.st_ino,
            )
        self.binding_ref = stable_matrix_rooms_media_ref(
            "media-store-binding-ref:matrix", {"root_identity": self._identity}
        )

    def _verify_root(self) -> None:
        try:
            info = os.lstat(self.root)
        except OSError as exc:
            raise MatrixMediaError("MATRIX_MEDIA_ROOT_SUBSTITUTION_DENIED") from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._identity
        ):
            raise MatrixMediaError("MATRIX_MEDIA_ROOT_SUBSTITUTION_DENIED")
        for name, identity in self._directory_identities.items():
            directory = self.root / name
            try:
                info = os.lstat(directory)
            except OSError as exc:
                raise MatrixMediaError(
                    "MATRIX_MEDIA_DIRECTORY_SUBSTITUTION_DENIED"
                ) from exc
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
                or (info.st_dev, info.st_ino) != identity
            ):
                raise MatrixMediaError("MATRIX_MEDIA_DIRECTORY_SUBSTITUTION_DENIED")

    def _open_directory(self, name: str) -> int:
        try:
            descriptor = os.open(
                self.root / name,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as exc:
            raise MatrixMediaError(
                "MATRIX_MEDIA_DIRECTORY_SUBSTITUTION_DENIED"
            ) from exc
        try:
            info = os.fstat(descriptor)
        except OSError as exc:
            os.close(descriptor)
            raise MatrixMediaError(
                "MATRIX_MEDIA_DIRECTORY_SUBSTITUTION_DENIED"
            ) from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._directory_identities[name]
        ):
            os.close(descriptor)
            raise MatrixMediaError("MATRIX_MEDIA_DIRECTORY_SUBSTITUTION_DENIED")
        return descriptor

    @staticmethod
    def quarantine_name(quarantine_ref: str) -> str:
        return hashlib.sha256(quarantine_ref.encode()).hexdigest() + ".quarantine"

    def quarantine_path(self, quarantine_ref: str) -> Path:
        return self.root / "media-quarantine" / self.quarantine_name(quarantine_ref)

    def read_upload_source(
        self, *, path: Path, declared_media_type: str, max_bytes: int
    ) -> tuple[bytes, MatrixMediaInspection]:
        self._verify_root()
        _validate_max_bytes(max_bytes)
        if not path.is_absolute():
            raise MatrixMediaError("MATRIX_MEDIA_SOURCE_ABSOLUTE_REQUIRED")
        upload_root = self.root / "media-upload-source"
        if path.parent != upload_root or path.name in {"", ".", ".."}:
            raise MatrixMediaError("MATRIX_MEDIA_SOURCE_OUTSIDE_APP_ROOT")
        directory_fd = self._open_directory("media-upload-source")
        try:
            descriptor = os.open(
                path.name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=directory_fd,
            )
        except OSError as exc:
            os.close(directory_fd)
            raise MatrixMediaError("MATRIX_MEDIA_SOURCE_PATH_DENIED") from exc
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
            ):
                raise MatrixMediaError("MATRIX_MEDIA_SOURCE_PATH_DENIED")
            if info.st_size > max_bytes:
                raise MatrixMediaError("MATRIX_MEDIA_SIZE_LIMIT_EXCEEDED")
            data = _read_bounded(descriptor, max_bytes=max_bytes)
        finally:
            os.close(descriptor)
            os.close(directory_fd)
        inspection = self.inspect(
            data=data, declared_media_type=declared_media_type, path_suffix=path.suffix
        )
        return data, inspection

    def inspect(
        self, *, data: bytes, declared_media_type: str, path_suffix: str | None = None
    ) -> MatrixMediaInspection:
        if not data:
            raise MatrixMediaError("MATRIX_MEDIA_EMPTY_DENIED")
        if data.startswith(_ARCHIVE_SIGNATURES):
            raise MatrixMediaError("MATRIX_MEDIA_ARCHIVE_DENIED")
        if data.startswith(_EXECUTABLE_SIGNATURES) or b"<script" in data[:1024].lower():
            raise MatrixMediaError("MATRIX_MEDIA_EXECUTABLE_DENIED")
        allowed = _ALLOWED.get(declared_media_type)
        if allowed is None:
            raise MatrixMediaError("MATRIX_MEDIA_TYPE_DENIED")
        expected_suffix, signature = allowed
        if signature is not None and not data.startswith(signature):
            raise MatrixMediaError("MATRIX_MEDIA_MIME_CONFUSION_DENIED")
        if declared_media_type == "text/plain":
            if b"\x00" in data:
                raise MatrixMediaError("MATRIX_MEDIA_MIME_CONFUSION_DENIED")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise MatrixMediaError("MATRIX_MEDIA_MIME_CONFUSION_DENIED") from exc
        if path_suffix is not None and path_suffix.casefold() not in {
            expected_suffix,
            ".jpeg" if expected_suffix == ".jpg" else expected_suffix,
        }:
            raise MatrixMediaError("MATRIX_MEDIA_EXTENSION_MISMATCH")
        return MatrixMediaInspection(
            media_type=declared_media_type,
            byte_count=len(data),
            content_fingerprint_ref=stable_matrix_rooms_media_ref(
                "content-fingerprint-ref:matrix-media",
                {"sha256": hashlib.sha256(data).hexdigest(), "byte_count": len(data)},
            ),
        )

    def inspect_quarantine(
        self, *, quarantine_ref: str, declared_media_type: str, max_bytes: int
    ) -> MatrixMediaInspection:
        self._verify_root()
        _validate_max_bytes(max_bytes)
        directory_fd = self._open_directory("media-quarantine")
        name = self.quarantine_name(quarantine_ref)
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=directory_fd,
            )
        except OSError as exc:
            os.close(directory_fd)
            raise MatrixMediaError("MATRIX_MEDIA_QUARANTINE_REQUIRED") from exc
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
                or info.st_size > max_bytes
            ):
                raise MatrixMediaError("MATRIX_MEDIA_QUARANTINE_INVALID")
            data = _read_bounded(descriptor, max_bytes=max_bytes)
        finally:
            os.close(descriptor)
            os.close(directory_fd)
        return self.inspect(data=data, declared_media_type=declared_media_type)

    def materialize(
        self,
        *,
        quarantine_ref: str,
        declared_media_type: str,
        max_bytes: int,
        materialization_ref: str,
    ) -> tuple[Path, MatrixMediaInspection]:
        self._verify_root()
        inspection = self.inspect_quarantine(
            quarantine_ref=quarantine_ref,
            declared_media_type=declared_media_type,
            max_bytes=max_bytes,
        )
        source_name = self.quarantine_name(quarantine_ref)
        suffix = _ALLOWED[declared_media_type][0]
        destination_name = (
            f"{hashlib.sha256(materialization_ref.encode()).hexdigest()}{suffix}"
        )
        destination = self.root / "media-materialized" / destination_name
        source_directory_fd = self._open_directory("media-quarantine")
        destination_directory_fd = self._open_directory("media-materialized")
        try:
            source_fd = os.open(
                source_name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=source_directory_fd,
            )
        except OSError as exc:
            os.close(source_directory_fd)
            os.close(destination_directory_fd)
            raise MatrixMediaError("MATRIX_MEDIA_QUARANTINE_REQUIRED") from exc
        try:
            source_info = os.fstat(source_fd)
            if (
                not stat.S_ISREG(source_info.st_mode)
                or source_info.st_nlink != 1
                or source_info.st_uid != os.geteuid()
                or source_info.st_mode & 0o077
            ):
                raise MatrixMediaError("MATRIX_MEDIA_QUARANTINE_INVALID")
            data = _read_bounded(source_fd, max_bytes=max_bytes)
            reopened_inspection = self.inspect(
                data=data,
                declared_media_type=declared_media_type,
            )
            if (
                reopened_inspection.content_fingerprint_ref
                != inspection.content_fingerprint_ref
            ):
                raise MatrixMediaError("MATRIX_MEDIA_QUARANTINE_SUBSTITUTION_DENIED")
            try:
                destination_fd = os.open(
                    destination_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=destination_directory_fd,
                )
            except OSError as exc:
                raise MatrixMediaError(
                    "MATRIX_MEDIA_MATERIALIZATION_PATH_DENIED"
                ) from exc
            try:
                try:
                    _write_all(destination_fd, data)
                    os.fsync(destination_fd)
                except OSError as exc:
                    raise MatrixMediaError(
                        "MATRIX_MEDIA_MATERIALIZATION_WRITE_FAILED"
                    ) from exc
            except MatrixMediaError:
                try:
                    os.unlink(destination_name, dir_fd=destination_directory_fd)
                    os.fsync(destination_directory_fd)
                except FileNotFoundError:
                    pass
                raise
            finally:
                os.close(destination_fd)
            os.fsync(destination_directory_fd)
        finally:
            os.close(source_fd)
            os.close(source_directory_fd)
            os.close(destination_directory_fd)
        return destination, inspection

    def cleanup(
        self,
        *,
        quarantine_ref: str,
        materialization_ref: str | None,
        declared_media_type: str | None,
    ) -> str:
        self._verify_root()
        targets = [("media-quarantine", self.quarantine_name(quarantine_ref))]
        if materialization_ref is not None and declared_media_type not in _ALLOWED:
            raise MatrixMediaError("MATRIX_MEDIA_CLEANUP_TYPE_REQUIRED")
        if materialization_ref is not None and declared_media_type in _ALLOWED:
            targets.append(
                (
                    "media-materialized",
                    f"{hashlib.sha256(materialization_ref.encode()).hexdigest()}"
                    f"{_ALLOWED[declared_media_type][0]}",
                )
            )
        for directory_name, name in targets:
            directory_fd = self._open_directory(directory_name)
            try:
                try:
                    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if (
                        not stat.S_ISREG(info.st_mode)
                        or stat.S_ISLNK(info.st_mode)
                        or info.st_nlink != 1
                        or info.st_uid != os.geteuid()
                    ):
                        raise MatrixMediaError("MATRIX_MEDIA_CLEANUP_PATH_DENIED")
                    os.unlink(name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                except FileNotFoundError:
                    pass
                try:
                    os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise MatrixMediaError("MATRIX_MEDIA_INCOMPLETE_CLEANUP")
            finally:
                os.close(directory_fd)
        return stable_matrix_rooms_media_ref(
            "receipt-ref:matrix-media:cleanup",
            {"target_count": len(targets), "path_absent": True},
        )


def _validate_max_bytes(max_bytes: int) -> None:
    if not 1 <= max_bytes <= 24_576:
        raise MatrixMediaError("MATRIX_MEDIA_SIZE_LIMIT_INVALID")


def _read_bounded(descriptor: int, *, max_bytes: int) -> bytes:
    payload = bytearray()
    try:
        while len(payload) <= max_bytes:
            chunk = os.read(descriptor, min(8192, max_bytes + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
    except OSError as exc:
        raise MatrixMediaError("MATRIX_MEDIA_READ_FAILED") from exc
    if len(payload) > max_bytes:
        raise MatrixMediaError("MATRIX_MEDIA_SIZE_LIMIT_EXCEEDED")
    return bytes(payload)


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise MatrixMediaError("MATRIX_MEDIA_MATERIALIZATION_WRITE_FAILED")
        offset += written


__all__ = ["MatrixMediaError", "MatrixMediaInspection", "MatrixMediaStore"]
