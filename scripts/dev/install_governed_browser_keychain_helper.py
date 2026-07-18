#!/usr/bin/env python3
"""Build and privately install the governed-browser macOS Keychain helper."""

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
PACKAGE = ROOT / "tools" / "macos" / "governed-browser-keychain-helper"
HELPER_NAME = "uaa-governed-browser-keychain-helper"
METADATA_NAME = "governed-browser-keychain-helper.json"
DEFAULT_INSTALL_ROOT = Path.home() / ".local" / "share" / "uaa" / "helpers"
HELPER_MAX_EXECUTABLE_BYTES = 32 * 1024 * 1024
METADATA_MAX_BYTES = 16 * 1024
INSTALL_SCHEMA = "uaa-governed-browser-keychain-helper-install.v1"
HELPER_REF = "helper-ref:governed-browser-keychain:v1"
HELPER_VERSION_REF = "helper-version-ref:governed-browser-keychain:v1"
MANAGED_METADATA_KEYS = frozenset(
    {
        "schema_version",
        "helper_ref",
        "helper_version_ref",
        "helper_fingerprint_ref",
        "platform_ref",
        "credential_material_included",
        "absolute_path_included",
        "browser_session_authority_granted",
        "authentication_authority_granted",
        "network_authority_granted",
        "external_mutation_authority_granted",
    }
)


def install(*, install_root: Path | None = None) -> dict[str, object]:
    """Install one source-built, hash-described helper into the fixed private root."""

    if sys.platform != "darwin" or platform.machine() not in {"arm64", "x86_64"}:
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_MACOS_REQUIRED")
    root = DEFAULT_INSTALL_ROOT if install_root is None else install_root
    if root != DEFAULT_INSTALL_ROOT:
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_CUSTOM_INSTALL_ROOT_DENIED"
        )
    _ensure_private_install_root(root)
    with tempfile.TemporaryDirectory(
        prefix="uaa-browser-keychain-helper-",
        dir="/tmp",
    ) as scratch:
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
        digest = _sha256(source)
        metadata = _build_metadata(digest)
        target = root / HELPER_NAME
        metadata_path = root / METADATA_NAME
        _reconcile_existing_pair(
            source=source,
            target=target,
            metadata_path=metadata_path,
            expected_digest=digest,
            intended_metadata=metadata,
        )
        _install_pair(
            source=source,
            target=target,
            metadata_path=metadata_path,
            expected_digest=digest,
            metadata=metadata,
        )
        _validate_installed_pair(target=target, metadata_path=metadata_path)
    return metadata


def _build_metadata(digest: str) -> dict[str, object]:
    return {
        "schema_version": INSTALL_SCHEMA,
        "helper_ref": HELPER_REF,
        "helper_version_ref": HELPER_VERSION_REF,
        "helper_fingerprint_ref": f"helper-fingerprint-ref:sha256:{digest}",
        "platform_ref": f"platform-ref:macos:{platform.machine()}",
        "credential_material_included": False,
        "absolute_path_included": False,
        "browser_session_authority_granted": False,
        "authentication_authority_granted": False,
        "network_authority_granted": False,
        "external_mutation_authority_granted": False,
    }


def _ensure_private_install_root(root: Path) -> None:
    home = Path.home()
    try:
        relative = root.relative_to(home)
    except ValueError as exc:
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_ROOT_INVALID"
        ) from exc
    home_metadata = os.lstat(home)
    if (
        not stat.S_ISDIR(home_metadata.st_mode)
        or stat.S_ISLNK(home_metadata.st_mode)
        or home_metadata.st_uid != os.getuid()
        or home_metadata.st_mode & 0o022
    ):
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_ROOT_INVALID")
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
            raise RuntimeError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_ROOT_INVALID"
            )
    os.chmod(root, 0o700)


def _reconcile_existing_pair(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    intended_metadata: dict[str, object],
) -> None:
    target_exists = target.exists() or target.is_symlink()
    metadata_exists = metadata_path.exists() or metadata_path.is_symlink()
    if not target_exists and not metadata_exists:
        return
    target_digest: str | None = None
    metadata: dict[str, object] | None = None
    if target_exists:
        _validate_regular_executable(target, owner_required=True)
        target_digest = _sha256(target)
    if metadata_exists:
        metadata = _read_metadata(metadata_path)

    if target_exists and not metadata_exists:
        if target_digest != expected_digest:
            raise RuntimeError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXISTING_INSTALL_INCOMPLETE"
            )
        _atomic_write_json(metadata_path, intended_metadata)
        return
    if metadata_exists and not target_exists:
        assert metadata is not None
        if not _managed_metadata_matches(metadata, expected_digest):
            raise RuntimeError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXISTING_INSTALL_INCOMPLETE"
            )
        _atomic_install_binary(source, target, expected_digest)
        return

    assert metadata is not None and target_digest is not None
    if _managed_metadata_matches(metadata, target_digest):
        return
    if target_digest == expected_digest and _is_managed_metadata(metadata):
        _atomic_write_json(metadata_path, intended_metadata)
        return
    raise RuntimeError(
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXISTING_INSTALL_UNMANAGED"
    )


def _install_pair(
    *,
    source: Path,
    target: Path,
    metadata_path: Path,
    expected_digest: str,
    metadata: dict[str, object],
) -> None:
    binary_temp = target.parent / f".{HELPER_NAME}.installing"
    metadata_temp = metadata_path.with_suffix(".tmp")
    if (
        binary_temp.exists()
        or binary_temp.is_symlink()
        or metadata_temp.exists()
        or metadata_temp.is_symlink()
    ):
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_TEMP_EXISTS"
        )
    try:
        shutil.copyfile(source, binary_temp, follow_symlinks=False)
        os.chmod(binary_temp, 0o700)
        _validate_regular_executable(binary_temp, owner_required=True)
        if _sha256(binary_temp) != expected_digest:
            raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_MISMATCH")
        _fsync_regular_file(binary_temp)
        _write_json_exclusive(metadata_temp, metadata)
        _fsync_directory(target.parent)
        os.replace(binary_temp, target)
        _fsync_directory(target.parent)
        os.replace(metadata_temp, metadata_path)
        _fsync_directory(target.parent)
    finally:
        for temporary in (binary_temp, metadata_temp):
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()


def _atomic_install_binary(
    source: Path,
    target: Path,
    expected_digest: str,
) -> None:
    temporary = target.parent / f".{HELPER_NAME}.installing"
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_TEMP_EXISTS"
        )
    try:
        shutil.copyfile(source, temporary, follow_symlinks=False)
        os.chmod(temporary, 0o700)
        _validate_regular_executable(temporary, owner_required=True)
        if _sha256(temporary) != expected_digest:
            raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_MISMATCH")
        _fsync_regular_file(temporary)
        os.replace(temporary, target)
        _fsync_directory(target.parent)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _atomic_write_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_suffix(".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_INSTALL_TEMP_EXISTS"
        )
    try:
        _write_json_exclusive(temporary, value)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _write_json_exclusive(path: Path, value: dict[str, object]) -> None:
    encoded = (
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    if len(encoded) > METADATA_MAX_BYTES:
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_TOO_LARGE")
    descriptor = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        if os.write(descriptor, encoded) != len(encoded):
            raise RuntimeError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_SHORT_WRITE"
            )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validate_installed_pair(*, target: Path, metadata_path: Path) -> None:
    _validate_regular_executable(target, owner_required=True)
    digest = _sha256(target)
    if not _managed_metadata_matches(_read_metadata(metadata_path), digest):
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXISTING_INSTALL_UNMANAGED"
        )


def _validate_regular_executable(path: Path, *, owner_required: bool) -> None:
    metadata = os.lstat(path)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_size < 1
        or metadata.st_size > HELPER_MAX_EXECUTABLE_BYTES
        or (owner_required and metadata.st_uid != os.getuid())
        or metadata.st_mode & 0o022
        or not metadata.st_mode & stat.S_IXUSR
    ):
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_FILE_UNTRUSTED")


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
            or metadata.st_size > METADATA_MAX_BYTES
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise RuntimeError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_UNTRUSTED"
            )
        chunks: list[bytes] = []
        remaining = METADATA_MAX_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    finally:
        os.close(descriptor)
    raw = b"".join(chunks)
    if len(raw) > METADATA_MAX_BYTES:
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_TOO_LARGE")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_INVALID"
        ) from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) for key in value
    ):
        raise RuntimeError("GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_INVALID")
    return value


def _is_managed_metadata(metadata: dict[str, object]) -> bool:
    return bool(
        set(metadata) == MANAGED_METADATA_KEYS
        and metadata.get("schema_version") == INSTALL_SCHEMA
        and metadata.get("helper_ref") == HELPER_REF
        and metadata.get("helper_version_ref") == HELPER_VERSION_REF
        and metadata.get("platform_ref")
        == f"platform-ref:macos:{platform.machine()}"
        and metadata.get("credential_material_included") is False
        and metadata.get("absolute_path_included") is False
        and metadata.get("browser_session_authority_granted") is False
        and metadata.get("authentication_authority_granted") is False
        and metadata.get("network_authority_granted") is False
        and metadata.get("external_mutation_authority_granted") is False
    )


def _managed_metadata_matches(
    metadata: dict[str, object],
    expected_digest: str,
) -> bool:
    return bool(
        _is_managed_metadata(metadata)
        and metadata.get("helper_fingerprint_ref")
        == f"helper-fingerprint-ref:sha256:{expected_digest}"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_regular_file(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="print content-free install metadata",
    )
    args = parser.parse_args()
    try:
        metadata = install()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"governed-browser Keychain helper install failed: {exc}", file=sys.stderr)
        return 1
    if args.print_json:
        print(json.dumps(metadata, sort_keys=True))
    else:
        print("governed-browser Keychain helper installed and hash-pinned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
