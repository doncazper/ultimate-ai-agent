from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "tools" / "macos" / "portable-evidence-keychain-helper"
HELPER_NAME = "uaa-portable-evidence-keychain-helper"
METADATA_NAME = "portable-evidence-keychain-helper.json"
DEFAULT_INSTALL_ROOT = Path.home() / ".local" / "share" / "uaa" / "helpers"
INSTALL_METADATA_MAX_BYTES = 16 * 1024
HELPER_MAX_EXECUTABLE_BYTES = 32 * 1024 * 1024


def install(*, install_root: Path | None = None) -> dict[str, object]:
    if sys.platform != "darwin" or platform.machine() not in {"arm64", "x86_64"}:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_MACOS_REQUIRED")
    root = DEFAULT_INSTALL_ROOT if install_root is None else install_root
    if root != DEFAULT_INSTALL_ROOT:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_CUSTOM_INSTALL_ROOT_DENIED")
    _ensure_private_install_root(root)
    _recover_install_temps(root)
    with tempfile.TemporaryDirectory(prefix="uaa-evidence-helper-") as scratch:
        subprocess.run(
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
            check=True,
            timeout=300,
        )
        source = Path(scratch) / "release" / HELPER_NAME
        _validate_regular_executable(source, owner_required=False)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = root / HELPER_NAME
        metadata_path = root / METADATA_NAME
        metadata = {
            "schema_version": "uaa-portable-evidence-keychain-helper-install.v1",
            "helper_ref": "helper-ref:portable-evidence-keychain:v1",
            "helper_version_ref": "helper-version-ref:portable-evidence-keychain:v1",
            "helper_fingerprint_ref": f"helper-fingerprint-ref:sha256:{digest}",
            "platform_ref": f"platform-ref:macos:{platform.machine()}",
            "private_key_included": False,
            "absolute_path_included": False,
            "execution_authority_granted": False,
        }
        _reconcile_interrupted_install(
            source=source,
            target=target,
            metadata_path=metadata_path,
            expected_digest=digest,
            intended_metadata=metadata,
        )
        _validate_existing_install(target=target, metadata_path=metadata_path)
        _install_helper_pair(
            source=source,
            target=target,
            metadata_path=metadata_path,
            expected_digest=digest,
            metadata=metadata,
        )
        _validate_regular_executable(target, owner_required=True)
        _validate_existing_install(target=target, metadata_path=metadata_path)
        return metadata


def _stage_helper_binary(
    *, source: Path, target: Path, expected_digest: str
) -> Path:
    temporary = target.parent / f".{HELPER_NAME}.installing"
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_INSTALL_TEMP_EXISTS")
    try:
        shutil.copyfile(source, temporary, follow_symlinks=False)
        os.chmod(temporary, 0o700)
        _validate_regular_executable(temporary, owner_required=True)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected_digest:
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_COPY_MISMATCH")
        _fsync_regular_file(temporary)
    except Exception:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
        raise
    return temporary


def _install_helper_binary(
    *, source: Path, target: Path, expected_digest: str
) -> None:
    temporary = _stage_helper_binary(
        source=source,
        target=target,
        expected_digest=expected_digest,
    )
    try:
        os.replace(temporary, target)
        _fsync_directory(target.parent)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _install_helper_pair(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    metadata: dict[str, object],
) -> None:
    binary_temp = _stage_helper_binary(
        source=source,
        target=target,
        expected_digest=expected_digest,
    )
    try:
        metadata_temp = _stage_json(metadata_path, metadata)
    except Exception:
        if binary_temp.exists() and not binary_temp.is_symlink():
            binary_temp.unlink()
            _fsync_directory(target.parent)
        raise
    # Both durable staging files now describe one exact hash-bound pair. Any
    # interruption from here is forward-recovered before the next build.
    _fsync_directory(target.parent)
    os.replace(binary_temp, target)
    _fsync_directory(target.parent)
    os.replace(metadata_temp, metadata_path)
    _fsync_directory(target.parent)


def _recover_install_temps(root: Path) -> None:
    """Forward-recover only strict, owner-controlled installer staging files."""
    target = root / HELPER_NAME
    metadata_path = root / METADATA_NAME
    binary_temp = root / f".{HELPER_NAME}.installing"
    metadata_temp = metadata_path.with_suffix(".tmp")
    binary_pending = binary_temp.exists() or binary_temp.is_symlink()
    metadata_pending = metadata_temp.exists() or metadata_temp.is_symlink()
    if not binary_pending and not metadata_pending:
        return
    if binary_pending:
        _validate_owned_staging_file(binary_temp)
    pending_metadata = (
        _read_existing_metadata(metadata_temp) if metadata_pending else None
    )
    if binary_pending and metadata_pending:
        assert pending_metadata is not None
        _validate_regular_executable(binary_temp, owner_required=True)
        digest = hashlib.sha256(binary_temp.read_bytes()).hexdigest()
        if not _managed_metadata_matches(pending_metadata, digest):
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_PENDING_INSTALL_INVALID")
        _fsync_regular_file(binary_temp)
        os.replace(binary_temp, target)
        _fsync_directory(root)
        os.replace(metadata_temp, metadata_path)
        _fsync_directory(root)
        return
    if binary_pending:
        # No metadata ever committed this staged helper to an identity. Removing
        # this one exact private staging file is safe; the helper will be rebuilt.
        binary_temp.unlink()
        _fsync_directory(root)
        return
    assert pending_metadata is not None
    try:
        _validate_regular_executable(target, owner_required=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_PENDING_INSTALL_INVALID") from exc
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if not _managed_metadata_matches(pending_metadata, digest):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_PENDING_INSTALL_INVALID")
    os.replace(metadata_temp, metadata_path)
    _fsync_directory(root)


def _validate_owned_staging_file(path: Path) -> None:
    metadata = os.lstat(path)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o022
        or metadata.st_size > HELPER_MAX_EXECUTABLE_BYTES
    ):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_PENDING_INSTALL_INVALID")


def _fsync_regular_file(path: Path) -> None:
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
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_PENDING_INSTALL_INVALID")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _reconcile_interrupted_install(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    intended_metadata: dict[str, object],
) -> None:
    """Repair only an exact, source-hash-bound interrupted two-file install."""
    target_exists = target.exists() or target.is_symlink()
    metadata_exists = metadata_path.exists() or metadata_path.is_symlink()
    if not target_exists and not metadata_exists:
        return
    if target_exists:
        _validate_regular_executable(target, owner_required=True)
        target_digest = hashlib.sha256(target.read_bytes()).hexdigest()
    else:
        target_digest = None
    metadata = _read_existing_metadata(metadata_path) if metadata_exists else None

    if target_exists and not metadata_exists:
        if target_digest != expected_digest:
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_INCOMPLETE")
        _atomic_write_json(metadata_path, intended_metadata)
        return
    if metadata_exists and not target_exists:
        assert metadata is not None
        if not _managed_metadata_matches(metadata, expected_digest):
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_INCOMPLETE")
        _install_helper_binary(
            source=source,
            target=target,
            expected_digest=expected_digest,
        )
        return
    assert metadata is not None and target_digest is not None
    if _managed_metadata_matches(metadata, target_digest):
        return
    if target_digest == expected_digest and _is_managed_metadata(metadata):
        _atomic_write_json(metadata_path, intended_metadata)
        return
    raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_UNMANAGED")


def _is_managed_metadata(metadata: dict[str, object]) -> bool:
    return bool(
        metadata.get("schema_version")
        == "uaa-portable-evidence-keychain-helper-install.v1"
        and metadata.get("helper_ref")
        == "helper-ref:portable-evidence-keychain:v1"
        and metadata.get("helper_version_ref")
        == "helper-version-ref:portable-evidence-keychain:v1"
        and metadata.get("private_key_included") is False
        and metadata.get("absolute_path_included") is False
        and metadata.get("execution_authority_granted") is False
    )


def _managed_metadata_matches(
    metadata: dict[str, object], expected_digest: str
) -> bool:
    return bool(
        _is_managed_metadata(metadata)
        and metadata.get("helper_fingerprint_ref")
        == f"helper-fingerprint-ref:sha256:{expected_digest}"
    )


def _ensure_private_install_root(root: Path) -> None:
    home = Path.home()
    try:
        relative = root.relative_to(home)
    except ValueError as exc:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_INSTALL_ROOT_INVALID") from exc
    home_metadata = os.lstat(home)
    if (
        not stat.S_ISDIR(home_metadata.st_mode)
        or stat.S_ISLNK(home_metadata.st_mode)
        or home_metadata.st_uid != os.getuid()
        or home_metadata.st_mode & 0o022
    ):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_INSTALL_ROOT_INVALID")
    current = home
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
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_INSTALL_ROOT_INVALID")
    os.chmod(root, 0o700)


def _validate_existing_install(*, target: Path, metadata_path: Path) -> None:
    target_exists = target.exists() or target.is_symlink()
    metadata_exists = metadata_path.exists() or metadata_path.is_symlink()
    if target_exists != metadata_exists:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_INCOMPLETE")
    if not target_exists:
        return
    _validate_regular_executable(target, owner_required=True)
    metadata = _read_existing_metadata(metadata_path)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if not _managed_metadata_matches(metadata, digest):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_UNMANAGED")


def _read_existing_metadata(path: Path) -> dict[str, object]:
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
            or metadata.st_size > INSTALL_METADATA_MAX_BYTES
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_METADATA_INVALID")
        raw = os.read(descriptor, INSTALL_METADATA_MAX_BYTES + 1)
    finally:
        os.close(descriptor)
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_METADATA_INVALID") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_METADATA_INVALID")
    return parsed


def _validate_regular_executable(path: Path, *, owner_required: bool) -> None:
    metadata = os.lstat(path)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_size < 1
        or metadata.st_size > HELPER_MAX_EXECUTABLE_BYTES
        or metadata.st_mode & 0o022
        or not metadata.st_mode & stat.S_IXUSR
        or (owner_required and metadata.st_uid != os.getuid())
    ):
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_EXECUTABLE_INVALID")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = _stage_json(path, payload)
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _stage_json(path: Path, payload: dict[str, object]) -> Path:
    if path.exists() or path.is_symlink():
        _read_existing_metadata(path)
    temporary = path.with_suffix(".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("PORTABLE_EVIDENCE_HELPER_METADATA_TEMP_EXISTS")
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
        encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        if os.write(descriptor, encoded) != len(encoded):
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_METADATA_SHORT_WRITE")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return temporary


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and install the purpose-specific macOS Keychain signer."
    )
    parser.parse_args()
    try:
        metadata = install()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print(
            "Portable evidence Keychain helper installation failed safely.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
