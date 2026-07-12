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
        _validate_existing_install(target=target, metadata_path=metadata_path)
        temporary = root / f".{HELPER_NAME}.installing"
        if temporary.exists() or temporary.is_symlink():
            raise RuntimeError("PORTABLE_EVIDENCE_HELPER_INSTALL_TEMP_EXISTS")
        try:
            shutil.copyfile(source, temporary, follow_symlinks=False)
            os.chmod(temporary, 0o700)
            _validate_regular_executable(temporary, owner_required=True)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
                raise RuntimeError("PORTABLE_EVIDENCE_HELPER_COPY_MISMATCH")
            os.replace(temporary, target)
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()
        _validate_regular_executable(target, owner_required=True)
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
        _atomic_write_json(metadata_path, metadata)
        return metadata


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
    if (
        metadata.get("schema_version")
        != "uaa-portable-evidence-keychain-helper-install.v1"
        or metadata.get("helper_ref") != "helper-ref:portable-evidence-keychain:v1"
        or metadata.get("helper_fingerprint_ref")
        != f"helper-fingerprint-ref:sha256:{digest}"
    ):
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
    os.replace(temporary, path)
    _fsync_directory(path.parent)


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
