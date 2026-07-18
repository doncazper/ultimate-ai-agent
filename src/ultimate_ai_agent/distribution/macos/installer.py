"""Atomic, checksum-verified macOS installation and rollback."""
from __future__ import annotations

import fcntl
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator

from .contracts import (
    APP_BUNDLE_IDENTIFIER,
    APP_BUNDLE_NAME,
    BUNDLE_MANIFEST_SCHEMA,
    INSTALL_RECEIPT_SCHEMA,
    MAX_ARCHIVE_FILES,
    MAX_EXTRACTED_BYTES,
    PRODUCT_LINE,
    ContractError,
    ReleaseDescriptor,
    sha256_file,
)


CLI_MARKER = "# uaa-managed-macos-cli-v1"
APP_MANAGED_MARKER = "uaa-install-managed.json"
DEFAULT_INSTALL_ROOT = Path.home() / "Library" / "Application Support" / "Ultimate AI Agent"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"
KEEP_VERSION_COUNT = 3
_SAFE_VERSION_ID_RE = re.compile(r"^[A-Za-z0-9._+-]{1,160}$")
_LEGACY_REPO_CLI_RE = re.compile(
    r'^#!/usr/bin/env bash\n'
    r"set -euo pipefail\n\n"
    r'exec "(/[^"\n]+/scripts/dev/uaa)" "\$@"\n?$'
)


class InstallError(RuntimeError):
    """The installer refused or failed a macOS filesystem mutation."""


@dataclass(frozen=True)
class InstallLayout:
    root: Path
    applications_dir: Path
    bin_dir: Path

    @classmethod
    def default(
        cls,
        *,
        environ: dict[str, str] | None = None,
    ) -> "InstallLayout":
        environment = os.environ if environ is None else environ
        home = Path(environment.get("HOME", str(Path.home()))).expanduser()
        root = Path(
            environment.get(
                "UAA_INSTALL_ROOT",
                str(home / "Library" / "Application Support" / "Ultimate AI Agent"),
            )
        ).expanduser()
        bin_dir = Path(
            environment.get("UAA_INSTALL_BIN_DIR", str(home / ".local" / "bin"))
        ).expanduser()
        requested_applications = environment.get("UAA_APPLICATIONS_DIR", "").strip()
        if requested_applications:
            applications_dir = Path(requested_applications).expanduser()
        else:
            applications_dir = _select_applications_dir(
                home=home,
                system_applications=Path("/Applications"),
            )
        return cls(
            root=root,
            applications_dir=applications_dir,
            bin_dir=bin_dir,
        )

    @property
    def versions_dir(self) -> Path:
        return self.root / "versions"

    @property
    def current_link(self) -> Path:
        return self.root / "current"

    @property
    def previous_link(self) -> Path:
        return self.root / "previous"

    @property
    def receipts_dir(self) -> Path:
        return self.root / "receipts"

    @property
    def lock_path(self) -> Path:
        return self.root / "install.lock"

    @property
    def app_link(self) -> Path:
        return self.applications_dir / APP_BUNDLE_NAME

    @property
    def cli_path(self) -> Path:
        return self.bin_dir / "uaa"


@dataclass(frozen=True)
class InstallResult:
    status: str
    version_id: str
    tag: str
    channel: str
    previous_version_id: str | None
    receipt_ref: str


@dataclass(frozen=True)
class RollbackResult:
    status: str
    version_id: str
    replaced_version_id: str
    receipt_ref: str


CodeSignatureVerifier = Callable[[Path, ReleaseDescriptor], None]
ApplicationVerifier = Callable[[Path], None]
CliSnapshot = tuple[bytes, int] | None


def install_archive(
    archive: Path,
    descriptor: ReleaseDescriptor,
    layout: InstallLayout,
    *,
    code_signature_verifier: CodeSignatureVerifier | None = None,
    keep_versions: int = KEEP_VERSION_COUNT,
) -> InstallResult:
    """Install one verified release and atomically promote its version."""

    descriptor.validate(expected_architecture=descriptor.architecture)
    if not archive.is_file():
        raise InstallError("release artifact is missing")
    if archive.stat().st_size != descriptor.artifact_size:
        raise InstallError("release artifact size does not match its descriptor")
    if sha256_file(archive) != descriptor.artifact_sha256:
        raise InstallError("release artifact SHA-256 does not match its descriptor")
    verifier = code_signature_verifier or verify_app_code_signature
    layout.root.mkdir(parents=True, exist_ok=True)
    layout.versions_dir.mkdir(parents=True, exist_ok=True)
    layout.receipts_dir.mkdir(parents=True, exist_ok=True)
    version_id = _version_id(descriptor)

    with _install_lock(layout):
        _preflight_entrypoints(layout)
        previous = _resolved_managed_version(layout, layout.current_link)
        prior_previous = _resolved_managed_version(layout, layout.previous_link)
        previous_id = previous.name if previous is not None else None
        prior_previous_id = (
            prior_previous.name if prior_previous is not None else None
        )
        if previous is None and (
            layout.app_link.exists() or layout.app_link.is_symlink()
        ):
            raise InstallError(
                "managed Applications entry has no corresponding installed version"
            )
        cli_snapshot = _snapshot_cli_entry(layout)
        destination = layout.versions_dir / version_id
        if destination.exists():
            manifest = load_bundle_manifest(destination / "bundle-manifest.json")
            validate_bundle_manifest(manifest, descriptor)
            _validate_extracted_bundle(destination, manifest, descriptor, verifier)
        else:
            with tempfile.TemporaryDirectory(
                prefix=".installing-",
                dir=layout.root,
            ) as temporary:
                extraction_root = Path(temporary) / "payload"
                extraction_root.mkdir()
                safe_extract_archive(archive, extraction_root)
                manifest = load_bundle_manifest(
                    extraction_root / "bundle-manifest.json"
                )
                validate_bundle_manifest(manifest, descriptor)
                _validate_extracted_bundle(
                    extraction_root,
                    manifest,
                    descriptor,
                    verifier,
                )
                extraction_root.replace(destination)

        already_current = previous_id == version_id
        if not already_current:
            _promote_version(layout, destination, previous_id)
        application_promoted = False
        try:
            _ensure_application_link(
                layout,
                application_verifier=lambda app: verifier(app, descriptor),
            )
            application_promoted = True
            _ensure_cli(layout)
            receipt_ref = _write_install_receipt(
                layout,
                operation="install",
                status="already-current" if already_current else "installed",
                version_id=version_id,
                tag=descriptor.tag,
                channel=descriptor.channel,
                previous_version_id=(
                    previous_id if previous_id != version_id else None
                ),
            )
        except Exception:
            _compensate_entrypoint_transaction(
                layout,
                current_id=previous_id,
                previous_id=prior_previous_id,
                cli_snapshot=cli_snapshot,
                application_promoted=application_promoted,
                application_verifier=(
                    _verify_installed_application
                    if code_signature_verifier is None
                    else lambda _app: None
                ),
            )
            raise
        _prune_versions(layout, keep=max(2, keep_versions))
        return InstallResult(
            status="already-current" if already_current else "installed",
            version_id=version_id,
            tag=descriptor.tag,
            channel=descriptor.channel,
            previous_version_id=previous_id if previous_id != version_id else None,
            receipt_ref=receipt_ref,
        )


def rollback(
    layout: InstallLayout,
    *,
    application_verifier: ApplicationVerifier | None = None,
) -> RollbackResult:
    layout.root.mkdir(parents=True, exist_ok=True)
    with _install_lock(layout):
        current = _resolved_managed_version(layout, layout.current_link)
        previous = _resolved_managed_version(layout, layout.previous_link)
        if current is None:
            raise InstallError("no managed current version is installed")
        if previous is None or previous == current:
            raise InstallError("no distinct managed rollback version is available")
        current_id = current.name
        previous_id = previous.name
        cli_snapshot = _snapshot_cli_entry(layout)
        _replace_relative_symlink(
            layout.current_link,
            Path("versions") / previous_id,
        )
        _replace_relative_symlink(
            layout.previous_link,
            Path("versions") / current_id,
        )
        application_promoted = False
        try:
            _ensure_application_link(
                layout,
                application_verifier=application_verifier,
            )
            application_promoted = True
            _ensure_cli(layout)
            receipt_ref = _write_install_receipt(
                layout,
                operation="rollback",
                status="rolled-back",
                version_id=previous_id,
                tag=_installed_tag(previous),
                channel=_installed_channel(previous),
                previous_version_id=current_id,
            )
        except Exception:
            _compensate_entrypoint_transaction(
                layout,
                current_id=current_id,
                previous_id=previous_id,
                cli_snapshot=cli_snapshot,
                application_promoted=application_promoted,
                application_verifier=(
                    _verify_installed_application
                    if application_verifier is None
                    else lambda _app: None
                ),
            )
            raise
        return RollbackResult(
            status="rolled-back",
            version_id=previous_id,
            replaced_version_id=current_id,
            receipt_ref=receipt_ref,
        )


def uninstall(layout: InstallLayout, *, purge_versions: bool = False) -> str:
    """Remove only installer-owned entry points, optionally including versions."""

    layout.root.mkdir(parents=True, exist_ok=True)
    with _install_lock(layout):
        if layout.app_link.is_symlink() and _symlink_points_inside(
            layout.app_link, layout.root
        ):
            layout.app_link.unlink()
        elif _is_managed_application_bundle(layout.app_link):
            shutil.rmtree(layout.app_link)
        elif layout.app_link.exists():
            raise InstallError("refusing to remove an application not owned by UAA")
        if layout.cli_path.is_file() and not layout.cli_path.is_symlink():
            if CLI_MARKER in layout.cli_path.read_text(
                encoding="utf-8", errors="replace"
            )[:512]:
                layout.cli_path.unlink()
            else:
                raise InstallError("refusing to remove a CLI not owned by UAA")
        elif layout.cli_path.exists() or layout.cli_path.is_symlink():
            raise InstallError("refusing to remove an unexpected CLI entry")
        if purge_versions:
            for link in (layout.current_link, layout.previous_link):
                if link.is_symlink():
                    link.unlink()
            shutil.rmtree(layout.versions_dir, ignore_errors=True)
        return _write_install_receipt(
            layout,
            operation="uninstall",
            status="uninstalled",
            version_id="none",
            tag="none",
            channel="none",
            previous_version_id=None,
        )


def safe_extract_archive(archive: Path, destination: Path) -> None:
    """Extract only bounded regular files/directories beneath destination."""

    destination.mkdir(parents=True, exist_ok=True)
    file_count = 0
    total_size = 0
    try:
        tar = tarfile.open(archive, mode="r:gz")
    except (OSError, tarfile.TarError) as exc:
        raise InstallError("release artifact is not a valid gzip tar archive") from exc
    with tar:
        for member in tar:
            file_count += 1
            if file_count > MAX_ARCHIVE_FILES:
                raise InstallError("release artifact contains too many files")
            relative = _safe_archive_path(member.name)
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                target.chmod(_safe_mode(member.mode, is_directory=True))
                continue
            if not member.isfile():
                raise InstallError("release artifact contains a link or special file")
            total_size += member.size
            if total_size > MAX_EXTRACTED_BYTES:
                raise InstallError("release artifact expands beyond its size limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                raise InstallError("release artifact member could not be read")
            remaining = member.size
            with target.open("xb") as handle:
                while remaining:
                    chunk = extracted.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise InstallError("release artifact member was truncated")
                    handle.write(chunk)
                    remaining -= len(chunk)
                if extracted.read(1):
                    raise InstallError("release artifact member exceeded declared size")
            target.chmod(_safe_mode(member.mode, is_directory=False))


def load_bundle_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError("bundle manifest is missing or invalid") from exc
    if not isinstance(value, dict):
        raise InstallError("bundle manifest must be a JSON object")
    return value


def validate_bundle_manifest(
    manifest: dict[str, Any],
    descriptor: ReleaseDescriptor,
) -> None:
    expected = {
        "schema_version": BUNDLE_MANIFEST_SCHEMA,
        "product_line": PRODUCT_LINE,
        "tag": descriptor.tag,
        "version": descriptor.version,
        "channel": descriptor.channel,
        "source_commit": descriptor.source_commit,
        "source_timestamp": descriptor.source_timestamp,
        "platform": "macos",
        "architecture": descriptor.architecture,
        "app_bundle": APP_BUNDLE_NAME,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise InstallError(f"bundle manifest {key} does not match release")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise InstallError("bundle manifest must contain a non-empty file inventory")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise InstallError("bundle manifest file entry must be an object")
        path = item.get("path")
        digest = item.get("sha256")
        size = item.get("size")
        mode = item.get("mode")
        if not isinstance(path, str):
            raise InstallError("bundle manifest file path must be a string")
        normalized = _safe_archive_path(path).as_posix()
        if normalized == "bundle-manifest.json":
            raise InstallError("bundle manifest cannot inventory itself")
        if normalized in seen:
            raise InstallError("bundle manifest contains a duplicate path")
        seen.add(normalized)
        if (
            not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or isinstance(mode, bool)
            or not isinstance(mode, int)
            or mode not in {0o644, 0o755}
        ):
            raise InstallError("bundle manifest file metadata is invalid")


def verify_app_code_signature(app_bundle: Path, descriptor: ReleaseDescriptor) -> None:
    codesign = Path("/usr/bin/codesign")
    if not codesign.exists():
        raise InstallError("macOS code-signing verification tool is unavailable")
    completed = subprocess.run(
        [str(codesign), "--verify", "--deep", "--strict", str(app_bundle)],
        text=True,
        capture_output=True,
        timeout=60.0,
        check=False,
    )
    if completed.returncode != 0:
        raise InstallError("application code-signing verification failed")
    details = subprocess.run(
        [str(codesign), "-d", "--verbose=4", str(app_bundle)],
        text=True,
        capture_output=True,
        timeout=30.0,
        check=False,
    )
    detail_text = details.stdout + details.stderr
    if descriptor.signing_kind == "developer-id":
        if (
            details.returncode != 0
            or "Authority=Developer ID Application:" not in detail_text
            or "runtime" not in detail_text.lower()
        ):
            raise InstallError(
                "release descriptor claims Developer ID without matching signature"
            )
    if descriptor.notarized:
        assessment = subprocess.run(
            ["/usr/sbin/spctl", "-a", "-t", "exec", "-vv", str(app_bundle)],
            text=True,
            capture_output=True,
            timeout=30.0,
            check=False,
        )
        if assessment.returncode != 0:
            raise InstallError("release descriptor claims notarization but assessment failed")


def current_version_id(layout: InstallLayout) -> str | None:
    current = _resolved_managed_version(layout, layout.current_link)
    return current.name if current is not None else None


def current_manifest(layout: InstallLayout) -> dict[str, Any] | None:
    current = _resolved_managed_version(layout, layout.current_link)
    if current is None:
        return None
    return load_bundle_manifest(current / "bundle-manifest.json")


def _validate_extracted_bundle(
    root: Path,
    manifest: dict[str, Any],
    descriptor: ReleaseDescriptor,
    verifier: CodeSignatureVerifier,
) -> None:
    expected_files = {
        item["path"]: item
        for item in manifest["files"]
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    actual_files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise InstallError("extracted bundle contains an unexpected symlink")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if relative != "bundle-manifest.json":
                actual_files.add(relative)
    if actual_files != set(expected_files):
        raise InstallError("bundle file inventory does not match extracted files")
    for relative, item in expected_files.items():
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.stat().st_size != item["size"] or sha256_file(path) != item["sha256"]:
            raise InstallError("bundle file failed size or SHA-256 verification")
        expected_mode = item["mode"]
        actual_mode = stat.S_IMODE(path.stat().st_mode)
        if actual_mode != expected_mode:
            raise InstallError("bundle file mode does not match manifest")
    app_bundle = root / APP_BUNDLE_NAME
    executable = app_bundle / "Contents" / "MacOS" / APP_BUNDLE_NAME.removesuffix(
        ".app"
    )
    info_plist = app_bundle / "Contents" / "Info.plist"
    managed_marker = (
        app_bundle / "Contents" / "Resources" / APP_MANAGED_MARKER
    )
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise InstallError("application executable is missing or not executable")
    if not managed_marker.is_file():
        raise InstallError("application installer ownership marker is missing")
    try:
        with info_plist.open("rb") as handle:
            plist = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        raise InstallError("application Info.plist is invalid") from exc
    if (
        plist.get("CFBundleIdentifier") != APP_BUNDLE_IDENTIFIER
        or plist.get("CFBundleShortVersionString") != descriptor.version
        or plist.get("CFBundlePackageType") != "APPL"
    ):
        raise InstallError("application Info.plist does not match release")
    verifier(app_bundle, descriptor)


def _promote_version(
    layout: InstallLayout,
    destination: Path,
    previous_id: str | None,
) -> None:
    if previous_id is not None:
        _replace_relative_symlink(
            layout.previous_link,
            Path("versions") / previous_id,
        )
    _replace_relative_symlink(
        layout.current_link,
        Path("versions") / destination.name,
    )


def _ensure_application_link(
    layout: InstallLayout,
    *,
    application_verifier: ApplicationVerifier | None = None,
) -> None:
    layout.applications_dir.mkdir(parents=True, exist_ok=True)
    source = layout.current_link / APP_BUNDLE_NAME
    if not _is_managed_application_bundle(source):
        raise InstallError("managed current application bundle is invalid")
    temporary = layout.applications_dir / ".Ultimate AI Agent.uaa-new.app"
    backup = layout.applications_dir / ".Ultimate AI Agent.uaa-old.app"
    _remove_stale_managed_application(temporary)
    _remove_stale_managed_application(backup)
    verifier = application_verifier or _verify_installed_application
    try:
        shutil.copytree(source, temporary, symlinks=False)
        verifier(temporary)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    had_existing_bundle = False
    if layout.app_link.is_symlink():
        layout.app_link.unlink()
    elif layout.app_link.exists():
        if not _is_managed_application_bundle(layout.app_link):
            shutil.rmtree(temporary, ignore_errors=True)
            raise InstallError(
                "refusing to overwrite an application not owned by this installer"
            )
        os.replace(layout.app_link, backup)
        had_existing_bundle = True
    try:
        os.replace(temporary, layout.app_link)
    except OSError:
        if had_existing_bundle and backup.exists() and not layout.app_link.exists():
            os.replace(backup, layout.app_link)
        raise
    if had_existing_bundle:
        shutil.rmtree(backup, ignore_errors=True)


def _ensure_cli(layout: InstallLayout) -> None:
    layout.bin_dir.mkdir(parents=True, exist_ok=True)
    if layout.cli_path.exists() or layout.cli_path.is_symlink():
        if layout.cli_path.is_symlink() or not layout.cli_path.is_file():
            raise InstallError("refusing to overwrite an unexpected CLI entry")
        existing = layout.cli_path.read_text(
            encoding="utf-8", errors="replace"
        )[:512]
        if CLI_MARKER not in existing and not _is_legacy_repo_cli(existing):
            raise InstallError("refusing to overwrite a CLI not owned by UAA")
    content = _cli_script()
    temporary = layout.cli_path.with_name(layout.cli_path.name + ".uaa-new")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o755)
    os.replace(temporary, layout.cli_path)


def _snapshot_cli_entry(layout: InstallLayout) -> CliSnapshot:
    if not layout.cli_path.exists() and not layout.cli_path.is_symlink():
        return None
    if layout.cli_path.is_symlink() or not layout.cli_path.is_file():
        raise InstallError("refusing to snapshot an unexpected CLI entry")
    if layout.cli_path.stat().st_size > 4096:
        raise InstallError("refusing an oversized managed CLI entry")
    return (
        layout.cli_path.read_bytes(),
        stat.S_IMODE(layout.cli_path.stat().st_mode),
    )


def _compensate_entrypoint_transaction(
    layout: InstallLayout,
    *,
    current_id: str | None,
    previous_id: str | None,
    cli_snapshot: CliSnapshot,
    application_promoted: bool,
    application_verifier: ApplicationVerifier,
) -> None:
    try:
        _restore_managed_link(layout.current_link, current_id)
        _restore_managed_link(layout.previous_link, previous_id)
        if application_promoted:
            if current_id is None:
                if _is_managed_application_bundle(layout.app_link):
                    shutil.rmtree(layout.app_link)
            else:
                _ensure_application_link(
                    layout,
                    application_verifier=application_verifier,
                )
        _restore_cli_entry(layout, cli_snapshot)
    except Exception as compensation_error:
        raise InstallError(
            "entrypoint promotion failed and automatic compensation was incomplete"
        ) from compensation_error


def _restore_managed_link(link: Path, version_id: str | None) -> None:
    if version_id is None:
        link.unlink(missing_ok=True)
        return
    _replace_relative_symlink(link, Path("versions") / version_id)


def _restore_cli_entry(layout: InstallLayout, snapshot: CliSnapshot) -> None:
    if snapshot is None:
        if layout.cli_path.is_file() and not layout.cli_path.is_symlink():
            existing = layout.cli_path.read_text(
                encoding="utf-8", errors="replace"
            )[:512]
            if CLI_MARKER in existing:
                layout.cli_path.unlink()
        return
    content, mode = snapshot
    temporary = layout.cli_path.with_name(layout.cli_path.name + ".uaa-restore")
    temporary.write_bytes(content)
    temporary.chmod(mode)
    os.replace(temporary, layout.cli_path)


def _preflight_entrypoints(layout: InstallLayout) -> None:
    if layout.app_link.exists() or layout.app_link.is_symlink():
        if not (
            (
                layout.app_link.is_symlink()
                and _symlink_points_inside(layout.app_link, layout.root)
            )
            or _is_managed_application_bundle(layout.app_link)
        ):
            raise InstallError(
                "refusing to overwrite an application not owned by this installer"
            )
    if layout.cli_path.exists() or layout.cli_path.is_symlink():
        if layout.cli_path.is_symlink() or not layout.cli_path.is_file():
            raise InstallError("refusing to overwrite an unexpected CLI entry")
        existing = layout.cli_path.read_text(
            encoding="utf-8", errors="replace"
        )[:512]
        if CLI_MARKER not in existing and not _is_legacy_repo_cli(existing):
            raise InstallError("refusing to overwrite a CLI not owned by UAA")


def _cli_script() -> str:
    return f"""#!/bin/sh
{CLI_MARKER}
set -eu
INSTALL_ROOT="${{UAA_INSTALL_ROOT:-$HOME/Library/Application Support/Ultimate AI Agent}}"
APP="$INSTALL_ROOT/current/{APP_BUNDLE_NAME}"
EXECUTABLE="$APP/Contents/MacOS/{APP_BUNDLE_NAME.removesuffix('.app')}"
if [ ! -x "$EXECUTABLE" ]; then
  echo "Ultimate AI Agent is not installed correctly. Run the installer repair command." >&2
  exit 1
fi
exec "$EXECUTABLE" "$@"
"""


def _is_legacy_repo_cli(value: str) -> bool:
    match = _LEGACY_REPO_CLI_RE.fullmatch(value)
    return match is not None and Path(match.group(1)).is_absolute()


def _replace_relative_symlink(link: Path, relative_target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.with_name(link.name + ".uaa-new")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(relative_target)
    os.replace(temporary, link)


def _resolved_managed_version(layout: InstallLayout, link: Path) -> Path | None:
    if not link.is_symlink():
        return None
    try:
        resolved = link.resolve(strict=True)
        versions = layout.versions_dir.resolve(strict=True)
        resolved.relative_to(versions)
    except (OSError, ValueError):
        return None
    if resolved.parent != versions or not _SAFE_VERSION_ID_RE.fullmatch(resolved.name):
        return None
    return resolved


def _symlink_points_inside(link: Path, root: Path) -> bool:
    try:
        resolved = link.resolve(strict=False)
        resolved.relative_to(root.resolve(strict=False))
        return True
    except (OSError, ValueError):
        return False


def _is_managed_application_bundle(path: Path) -> bool:
    if not path.is_dir():
        return False
    marker = path / "Contents" / "Resources" / APP_MANAGED_MARKER
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("schema_version") == "uaa.macos.install-ownership.v1"
        and value.get("product_line") == PRODUCT_LINE
    )


def _remove_stale_managed_application(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or not _is_managed_application_bundle(path):
        raise InstallError("staged Applications slot contains an unmanaged item")
    shutil.rmtree(path)


def _verify_installed_application(app_bundle: Path) -> None:
    completed = subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app_bundle)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60.0,
        check=False,
    )
    if completed.returncode != 0:
        raise InstallError("staged Applications bundle signature verification failed")


def _write_install_receipt(
    layout: InstallLayout,
    *,
    operation: str,
    status: str,
    version_id: str,
    tag: str,
    channel: str,
    previous_version_id: str | None,
) -> str:
    layout.receipts_dir.mkdir(parents=True, exist_ok=True)
    receipt_id = f"{int(time.time() * 1000)}-{operation}"
    receipt_ref = f"macos-install-receipt:{receipt_id}"
    payload = {
        "schema_version": INSTALL_RECEIPT_SCHEMA,
        "receipt_ref": receipt_ref,
        "operation": operation,
        "status": status,
        "version_ref": f"macos-version:{version_id}",
        "tag_ref": f"git-tag:{tag}",
        "channel": channel,
        "previous_version_ref": (
            f"macos-version:{previous_version_id}"
            if previous_version_id is not None
            else None
        ),
        "idempotent": operation == "install",
        "rollback_available": layout.previous_link.is_symlink(),
        "raw_paths_included": False,
        "credentials_included": False,
    }
    target = layout.receipts_dir / f"{receipt_id}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    os.replace(temporary, target)
    return receipt_ref


def _prune_versions(layout: InstallLayout, *, keep: int) -> None:
    protected = {
        version.name
        for version in (
            _resolved_managed_version(layout, layout.current_link),
            _resolved_managed_version(layout, layout.previous_link),
        )
        if version is not None
    }
    candidates = sorted(
        (
            path
            for path in layout.versions_dir.iterdir()
            if path.is_dir()
            and not path.is_symlink()
            and _SAFE_VERSION_ID_RE.fullmatch(path.name)
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    retained = 0
    for candidate in candidates:
        if candidate.name in protected or retained < keep:
            retained += 1
            continue
        shutil.rmtree(candidate)


def _version_id(descriptor: ReleaseDescriptor) -> str:
    value = f"{descriptor.tag}-{descriptor.source_commit[:12]}"
    if not _SAFE_VERSION_ID_RE.fullmatch(value):
        raise ContractError("release descriptor cannot form a safe version id")
    return value


def _installed_tag(version_root: Path) -> str:
    return str(load_bundle_manifest(version_root / "bundle-manifest.json")["tag"])


def _installed_channel(version_root: Path) -> str:
    return str(
        load_bundle_manifest(version_root / "bundle-manifest.json")["channel"]
    )


def _safe_archive_path(value: str) -> PurePosixPath:
    if not value or "\x00" in value or "\\" in value:
        raise InstallError("release artifact contains an unsafe path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise InstallError("release artifact contains an unsafe path")
    return path


def _safe_mode(value: int, *, is_directory: bool) -> int:
    if is_directory:
        return 0o755
    return 0o755 if value & 0o111 else 0o644


def _directory_is_writable(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.W_OK)


def _select_applications_dir(
    *,
    home: Path,
    system_applications: Path,
) -> Path:
    """Keep using an existing app location even if authority later narrows."""

    user_applications = home / "Applications"
    for applications_dir in (system_applications, user_applications):
        app = applications_dir / APP_BUNDLE_NAME
        if app.exists() or app.is_symlink():
            return applications_dir
    if _directory_is_writable(system_applications):
        return system_applications
    return user_applications


@contextmanager
def _install_lock(layout: InstallLayout) -> Iterator[None]:
    layout.root.mkdir(parents=True, exist_ok=True)
    with layout.lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallError("another UAA install or update is already running") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
