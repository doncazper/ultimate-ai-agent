from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import signal
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "tools" / "macos" / "matrix-session-keychain-helper"
HELPER_NAME = "uaa-matrix-session-keychain-helper"
METADATA_NAME = "matrix-session-keychain-helper.json"
DEFAULT_INSTALL_ROOT = Path.home() / ".local" / "share" / "uaa" / "helpers"
MAX_HELPER_BYTES = 32 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024
INSTALL_LOCK_NAME = ".matrix-session-keychain-helper.install.lock"


def _digest(path: Path) -> str:
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
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_FILE_UNSAFE")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _validate_regular(path: Path, *, owned: bool) -> None:
    metadata = os.lstat(path)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_size > MAX_HELPER_BYTES
        or metadata.st_size < 1
        or metadata.st_mode & 0o022
        or not metadata.st_mode & stat.S_IXUSR
        or (owned and metadata.st_uid != os.getuid())
    ):
        raise RuntimeError("MATRIX_SESSION_HELPER_FILE_UNSAFE")


def _ensure_root(root: Path) -> None:
    if root != DEFAULT_INSTALL_ROOT:
        raise RuntimeError("MATRIX_SESSION_HELPER_CUSTOM_INSTALL_ROOT_DENIED")
    home = Path.home()
    try:
        relative = root.relative_to(home)
    except ValueError as exc:
        raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_ROOT_UNSAFE") from exc
    current = home
    home_metadata = os.lstat(home)
    if (
        not stat.S_ISDIR(home_metadata.st_mode)
        or stat.S_ISLNK(home_metadata.st_mode)
        or home_metadata.st_uid != os.getuid()
        or home_metadata.st_mode & 0o022
    ):
        raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_ROOT_UNSAFE")
    for component in relative.parts:
        current = current / component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            os.mkdir(current, mode=0o700)
            metadata = os.lstat(current)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o022
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_ROOT_UNSAFE")
    os.chmod(root, 0o700)


@contextmanager
def _install_lock(root: Path) -> Iterator[None]:
    path = root / INSTALL_LOCK_NAME
    descriptor = os.open(
        path,
        os.O_CREAT
        | os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_LOCK_UNSAFE")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_IN_PROGRESS") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _read_metadata(path: Path) -> dict[str, object]:
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
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
            or metadata.st_size > MAX_METADATA_BYTES
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_METADATA_UNSAFE")
        raw = os.read(descriptor, MAX_METADATA_BYTES + 1)
    finally:
        os.close(descriptor)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("MATRIX_SESSION_HELPER_METADATA_INVALID") from exc
    if not isinstance(value, dict):
        raise RuntimeError("MATRIX_SESSION_HELPER_METADATA_INVALID")
    return value


def _metadata(digest: str) -> dict[str, object]:
    return {
        "schema_version": "uaa-matrix-session-keychain-helper-install.v1",
        "helper_ref": "helper-ref:matrix-session-keychain:v1",
        "helper_version_ref": "helper-version-ref:matrix-session-keychain:v1",
        "helper_fingerprint_ref": f"helper-fingerprint-ref:sha256:{digest}",
        "platform_ref": f"platform-ref:macos:{platform.machine()}",
        "session_material_included": False,
        "absolute_path_included": False,
        "execution_authority_granted": False,
    }


def _managed_metadata_matches(value: dict[str, object], digest: str) -> bool:
    return bool(
        value.get("schema_version") == "uaa-matrix-session-keychain-helper-install.v1"
        and value.get("helper_ref") == "helper-ref:matrix-session-keychain:v1"
        and value.get("helper_version_ref")
        == "helper-version-ref:matrix-session-keychain:v1"
        and value.get("helper_fingerprint_ref")
        == f"helper-fingerprint-ref:sha256:{digest}"
        and value.get("session_material_included") is False
        and value.get("absolute_path_included") is False
        and value.get("execution_authority_granted") is False
    )


def _is_managed_metadata(value: dict[str, object]) -> bool:
    return bool(
        value.get("schema_version") == "uaa-matrix-session-keychain-helper-install.v1"
        and value.get("helper_ref") == "helper-ref:matrix-session-keychain:v1"
        and value.get("helper_version_ref")
        == "helper-version-ref:matrix-session-keychain:v1"
        and value.get("session_material_included") is False
        and value.get("absolute_path_included") is False
        and value.get("execution_authority_granted") is False
    )


def _fsync_file(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_TEMP_UNSAFE")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _stage_json(path: Path, value: dict[str, object]) -> Path:
    temporary = path.with_suffix(".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_TEMP_EXISTS")
    descriptor = os.open(
        temporary,
        os.O_CREAT
        | os.O_EXCL
        | os.O_WRONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        payload = (json.dumps(value, sort_keys=True) + "\n").encode()
        if os.write(descriptor, payload) != len(payload):
            raise RuntimeError("MATRIX_SESSION_HELPER_METADATA_SHORT_WRITE")
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
        raise
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    return temporary


def _stage_binary(source: Path, target: Path, expected_digest: str) -> Path:
    staged = target.parent / f".{HELPER_NAME}.installing"
    if staged.exists() or staged.is_symlink():
        raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_TEMP_EXISTS")
    source_descriptor: int | None = None
    target_descriptor: int | None = None
    try:
        source_descriptor = os.open(
            source,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0),
        )
        target_descriptor = os.open(
            staged,
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o700,
        )
        source_metadata = os.fstat(source_descriptor)
        if (
            not stat.S_ISREG(source_metadata.st_mode)
            or source_metadata.st_nlink != 1
            or not 0 < source_metadata.st_size <= MAX_HELPER_BYTES
        ):
            raise RuntimeError("MATRIX_SESSION_HELPER_FILE_UNSAFE")
        while chunk := os.read(source_descriptor, 1024 * 1024):
            view = memoryview(chunk)
            while view:
                written = os.write(target_descriptor, view)
                if written <= 0:
                    raise RuntimeError("MATRIX_SESSION_HELPER_BINARY_SHORT_WRITE")
                view = view[written:]
        os.fchmod(target_descriptor, 0o700)
        os.fsync(target_descriptor)
        os.close(target_descriptor)
        target_descriptor = None
        os.close(source_descriptor)
        source_descriptor = None
        _validate_regular(staged, owned=True)
        if _digest(staged) != expected_digest:
            raise RuntimeError("MATRIX_SESSION_HELPER_COPY_MISMATCH")
        _fsync_file(staged)
    except Exception:
        if staged.exists() and not staged.is_symlink():
            staged.unlink()
        raise
    finally:
        if target_descriptor is not None:
            os.close(target_descriptor)
        if source_descriptor is not None:
            os.close(source_descriptor)
    return staged


def _run_swift_build(scratch: str) -> None:
    process = subprocess.Popen(
        [
            "/usr/bin/swift",
            "build",
            "--package-path",
            os.fspath(PACKAGE),
            "-c",
            "release",
            "--scratch-path",
            scratch,
        ],
        cwd=ROOT,
        env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        returncode = process.wait(timeout=300)
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
        raise RuntimeError("MATRIX_SESSION_HELPER_BUILD_FAILED") from None
    if returncode != 0:
        raise RuntimeError("MATRIX_SESSION_HELPER_BUILD_FAILED")


def _recover_install_temps(root: Path) -> None:
    target = root / HELPER_NAME
    metadata_path = root / METADATA_NAME
    binary_temp = root / f".{HELPER_NAME}.installing"
    metadata_temp = metadata_path.with_suffix(".tmp")
    binary_pending = binary_temp.exists() or binary_temp.is_symlink()
    metadata_pending = metadata_temp.exists() or metadata_temp.is_symlink()
    if not binary_pending and not metadata_pending:
        return
    if binary_pending:
        _validate_regular(binary_temp, owned=True)
    pending_metadata = _read_metadata(metadata_temp) if metadata_pending else None
    if binary_pending and metadata_pending:
        assert pending_metadata is not None
        digest = _digest(binary_temp)
        if not _managed_metadata_matches(pending_metadata, digest):
            raise RuntimeError("MATRIX_SESSION_HELPER_PENDING_INSTALL_INVALID")
        os.replace(binary_temp, target)
        _fsync_directory(root)
        os.replace(metadata_temp, metadata_path)
        _fsync_directory(root)
        return
    if binary_pending:
        binary_temp.unlink()
        _fsync_directory(root)
        return
    assert pending_metadata is not None
    _validate_regular(target, owned=True)
    if not _managed_metadata_matches(pending_metadata, _digest(target)):
        raise RuntimeError("MATRIX_SESSION_HELPER_PENDING_INSTALL_INVALID")
    os.replace(metadata_temp, metadata_path)
    _fsync_directory(root)


def _atomic_write_json(path: Path, value: dict[str, object]) -> None:
    temporary = _stage_json(path, value)
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _reconcile_existing(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    intended: dict[str, object],
) -> None:
    target_exists = target.exists() or target.is_symlink()
    metadata_exists = metadata_path.exists() or metadata_path.is_symlink()
    if not target_exists and not metadata_exists:
        return
    target_digest: str | None = None
    if target_exists:
        _validate_regular(target, owned=True)
        target_digest = _digest(target)
    existing = _read_metadata(metadata_path) if metadata_exists else None
    if target_exists and not metadata_exists:
        if target_digest != expected_digest:
            raise RuntimeError("MATRIX_SESSION_HELPER_EXISTING_INSTALL_INCOMPLETE")
        _atomic_write_json(metadata_path, intended)
        return
    if metadata_exists and not target_exists:
        assert existing is not None
        if not _managed_metadata_matches(existing, expected_digest):
            raise RuntimeError("MATRIX_SESSION_HELPER_EXISTING_INSTALL_INCOMPLETE")
        staged = _stage_binary(source, target, expected_digest)
        os.replace(staged, target)
        _fsync_directory(target.parent)
        return
    assert existing is not None and target_digest is not None
    if _managed_metadata_matches(existing, target_digest):
        return
    if target_digest == expected_digest and _is_managed_metadata(existing):
        _atomic_write_json(metadata_path, intended)
        return
    raise RuntimeError("MATRIX_SESSION_HELPER_EXISTING_INSTALL_UNMANAGED")


def _install_pair(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    intended: dict[str, object],
) -> None:
    binary_temp = _stage_binary(source, target, expected_digest)
    try:
        metadata_temp = _stage_json(metadata_path, intended)
    except Exception:
        if binary_temp.exists() and not binary_temp.is_symlink():
            binary_temp.unlink()
            _fsync_directory(target.parent)
        raise
    _fsync_directory(target.parent)
    os.replace(binary_temp, target)
    _fsync_directory(target.parent)
    os.replace(metadata_temp, metadata_path)
    _fsync_directory(target.parent)


def install(*, install_root: Path | None = None) -> dict[str, object]:
    if sys.platform != "darwin" or platform.machine() not in {"arm64", "x86_64"}:
        raise RuntimeError("MATRIX_SESSION_HELPER_MACOS_REQUIRED")
    root = DEFAULT_INSTALL_ROOT if install_root is None else install_root
    _ensure_root(root)
    with _install_lock(root):
        _recover_install_temps(root)
        target = root / HELPER_NAME
        metadata_path = root / METADATA_NAME
        with tempfile.TemporaryDirectory(
            prefix="uaa-matrix-session-helper-"
        ) as scratch:
            _run_swift_build(scratch)
            source = Path(scratch) / "release" / HELPER_NAME
            _validate_regular(source, owned=False)
            digest = _digest(source)
            intended = _metadata(digest)

            _reconcile_existing(
                source=source,
                target=target,
                metadata_path=metadata_path,
                expected_digest=digest,
                intended=intended,
            )
            if target.exists() and metadata_path.exists():
                existing = _read_metadata(metadata_path)
                if existing == intended and _digest(target) == digest:
                    return intended
            _install_pair(
                source=source,
                target=target,
                metadata_path=metadata_path,
                expected_digest=digest,
                intended=intended,
            )
            _validate_regular(target, owned=True)
            if _read_metadata(metadata_path) != intended:
                raise RuntimeError("MATRIX_SESSION_HELPER_INSTALL_VERIFY_FAILED")
            return intended


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the hash-bound macOS Matrix session helper."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = install()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Matrix session helper installation failed closed.", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("Matrix session helper installed and hash verified.")
        print(result["helper_fingerprint_ref"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
