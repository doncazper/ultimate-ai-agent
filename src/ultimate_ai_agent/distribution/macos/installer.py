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
from typing import TYPE_CHECKING, Any, Callable, Iterator

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


if TYPE_CHECKING:
    from ...core.finance_managed_profile import VerifiedFinanceHelper


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


# FIN003 source adapters observe only these fixed artifacts. They never build or
# execute a helper, and return captured bytes rather than a path to reopen.
_FINANCE_PACKAGE = "tools/macos/matrix-protected-cache-helper"
_FINANCE_SOURCE_FILES = (
    f"{_FINANCE_PACKAGE}/Package.swift",
    f"{_FINANCE_PACKAGE}/Sources/UAAMatrixProtectedCacheHelper/main.swift",
)
_FINANCE_BUILDER = "scripts/macos/build_finance_helper.py"
_FINANCE_HELPER = "Contents/Helpers/uaa-matrix-protected-cache-helper"
_FINANCE_SOURCE_MAX_BYTES = 1024 * 1024
_FINANCE_METADATA_MAX_BYTES = 64 * 1024
_FINANCE_INVENTORY_MAX_BYTES = 32 * 1024 * 1024


class _FinanceSourceCapture:
    """One retained, bounded observation of fixed source names, never a writer."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.directories: dict[str, tuple[int, os.stat_result]] = {}
        self.files: dict[str, tuple[int, os.stat_result, bytes | None]] = {}

    def __enter__(self) -> "_FinanceSourceCapture":
        from ...core.private_path_security import (
            require_posix_private_path_support,
            require_safe_private_ancestor_chain,
        )

        if not self.root.is_absolute() or ".." in self.root.parts:
            raise InstallError("FIN003_SOURCE_INVALID")
        try:
            require_posix_private_path_support()
            require_safe_private_ancestor_chain(self.root, purpose="Finance source")
            self._directory("")
        except (OSError, ValueError):
            self.__exit__(None, None, None)
            raise InstallError("FIN003_SOURCE_INVALID") from None
        return self

    def __exit__(self, *_args: object) -> None:
        for descriptor, *_ in reversed(tuple(self.files.values())):
            os.close(descriptor)
        for descriptor, _ in reversed(tuple(self.directories.values())):
            os.close(descriptor)
        self.files.clear()
        self.directories.clear()

    @staticmethod
    def _identity(metadata: os.stat_result) -> tuple[int, ...]:
        from ...core.private_path_security import _private_identity

        return _private_identity(metadata)

    @staticmethod
    def _metadata(metadata: os.stat_result, *, directory: bool) -> None:
        valid_type = stat.S_ISDIR if directory else stat.S_ISREG
        if (
            not valid_type(metadata.st_mode)
            or metadata.st_uid not in {0, os.getuid()}
            or stat.S_IMODE(metadata.st_mode) & 0o7022
            or (not directory and metadata.st_nlink != 1)
        ):
            raise InstallError("FIN003_SOURCE_INVALID")

    def _directory(self, relative: str) -> int:
        from ...core.private_path_security import _require_no_extended_acl_grants_fd

        relative = "" if relative == "." else relative
        if (
            PurePosixPath(relative).is_absolute()
            or ".." in PurePosixPath(relative).parts
        ):
            raise InstallError("FIN003_SOURCE_INVALID")
        if relative in self.directories:
            return self.directories[relative][0]
        path = PurePosixPath(relative)
        parent = (
            self._directory(str(path.parent) if str(path.parent) != "." else "")
            if relative
            else None
        )
        name = path.name if relative else self.root
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        self._metadata(before, directory=True)
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent,
        )
        try:
            opened = os.fstat(descriptor)
            if self._identity(before) != self._identity(opened):
                raise InstallError("FIN003_SOURCE_CHANGED")
            _require_no_extended_acl_grants_fd(descriptor, purpose="Finance source")
            self.directories[relative] = (descriptor, opened)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    def retain(self, relative: str, maximum: int, *, executable: bool = False) -> None:
        from ...core.private_path_security import require_no_extended_acl_fd

        if relative in self.files:
            raise InstallError("FIN003_SOURCE_INVALID")
        path = PurePosixPath(relative)
        parent = self._directory(path.parent.as_posix())
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        self._metadata(before, directory=False)
        if not 0 < before.st_size <= maximum or (
            executable and not before.st_mode & stat.S_IXUSR
        ):
            raise InstallError("FIN003_SOURCE_INVALID")
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent,
        )
        try:
            opened = os.fstat(descriptor)
            if self._identity(before) != self._identity(opened):
                raise InstallError("FIN003_SOURCE_CHANGED")
            require_no_extended_acl_fd(descriptor, purpose="Finance source")
            self.files[relative] = (descriptor, opened, None)
        except BaseException:
            os.close(descriptor)
            raise

    def read(self, relative: str, maximum: int, *, executable: bool = False) -> bytes:
        if relative not in self.files:
            self.retain(relative, maximum, executable=executable)
        descriptor, opened, previous = self.files[relative]
        if previous is not None:
            raise InstallError("FIN003_SOURCE_INVALID")
        raw = self._read_bytes(descriptor, maximum)
        if len(raw) != opened.st_size or self._identity(opened) != self._identity(
            os.fstat(descriptor)
        ):
            raise InstallError("FIN003_SOURCE_CHANGED")
        self.files[relative] = (descriptor, opened, raw)
        return raw

    @staticmethod
    def _read_bytes(descriptor: int, maximum: int) -> bytes:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > maximum:
            raise InstallError("FIN003_SOURCE_INVALID")
        return raw

    def recheck(self) -> None:
        from ...core.private_path_security import (
            _require_no_extended_acl_grants_fd,
            require_no_extended_acl_fd,
            require_safe_private_ancestor_chain,
        )

        require_safe_private_ancestor_chain(self.root, purpose="Finance source")
        for relative, (descriptor, before) in self.directories.items():
            path = PurePosixPath(relative)
            parent = (
                self.directories.get(path.parent.as_posix(), self.directories[""])[0]
                if relative
                else None
            )
            name = path.name if relative else self.root
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if any(
                self._identity(before) != self._identity(item)
                for item in (current, os.fstat(descriptor))
            ):
                raise InstallError("FIN003_SOURCE_CHANGED")
            _require_no_extended_acl_grants_fd(descriptor, purpose="Finance source")
        for relative, (descriptor, before, raw) in self.files.items():
            path = PurePosixPath(relative)
            parent = self.directories[
                "" if path.parent.as_posix() == "." else path.parent.as_posix()
            ][0]
            current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if any(
                self._identity(before) != self._identity(item)
                for item in (current, os.fstat(descriptor))
            ):
                raise InstallError("FIN003_SOURCE_CHANGED")
            require_no_extended_acl_fd(descriptor, purpose="Finance source")
            if raw is not None and (
                self._read_bytes(descriptor, len(raw)) != raw
                or self._identity(before) != self._identity(os.fstat(descriptor))
            ):
                raise InstallError("FIN003_SOURCE_CHANGED")


def _finance_source_inputs(
    capture: _FinanceSourceCapture,
) -> tuple[tuple[bytes, ...], bytes]:
    # Ignore only known non-input directories. Extra Swift targets or dependency
    # manifests would change the fixed build recipe and are rejected.
    package = capture._directory(_FINANCE_PACKAGE)
    if set(os.listdir(package)) - {
        "Package.swift",
        "Sources",
        "README.md",
        ".build",
        ".uaa-artifacts",
    }:
        raise InstallError("FIN003_BUILD_RECIPE_CHANGED")
    sources = capture._directory(f"{_FINANCE_PACKAGE}/Sources")
    target = capture._directory(
        f"{_FINANCE_PACKAGE}/Sources/UAAMatrixProtectedCacheHelper"
    )
    if set(os.listdir(sources)) != {"UAAMatrixProtectedCacheHelper"} or set(
        os.listdir(target)
    ) != {"main.swift"}:
        raise InstallError("FIN003_BUILD_RECIPE_CHANGED")
    raw = tuple(
        capture.read(path, _FINANCE_SOURCE_MAX_BYTES) for path in _FINANCE_SOURCE_FILES
    )
    builder = capture.read(_FINANCE_BUILDER, _FINANCE_SOURCE_MAX_BYTES)
    return raw, builder


def _finance_macho_architecture(raw: bytes) -> str:
    import struct

    if len(raw) < 32 or raw[:4] != b"\xcf\xfa\xed\xfe":
        raise InstallError("FIN003_HELPER_ARCHITECTURE_INVALID")
    cpu, _subtype, filetype = struct.unpack_from("<III", raw, 4)
    if filetype != 2 or cpu not in {0x0100000C, 0x01000007}:
        raise InstallError("FIN003_HELPER_ARCHITECTURE_INVALID")
    return {0x0100000C: "arm64", 0x01000007: "x86_64"}[cpu]


def _finance_signature_kind(path: Path) -> str:
    import selectors

    try:
        _verify_installed_application(path)
    except (InstallError, OSError, subprocess.SubprocessError):
        raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID") from None
    # The fixed details process has a hard output bound as well as a deadline.
    # No signing output or raw source path is retained in evidence or exceptions.
    child = subprocess.Popen(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    raw = bytearray()
    deadline = time.monotonic() + 30.0
    try:
        assert child.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
                chunk = os.read(child.stdout.fileno(), 4096)
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > _FINANCE_METADATA_MAX_BYTES:
                    raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
        if child.wait(timeout=max(0.001, deadline - time.monotonic())) != 0:
            raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
    finally:
        try:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5.0)
        finally:
            if child.stdout is not None:
                child.stdout.close()
    lines = bytes(raw).decode("utf-8", errors="strict").splitlines()
    if "Signature=adhoc" in lines:
        return "ad-hoc"
    if any(
        line.startswith("Authority=Developer ID Application:") for line in lines
    ) and any(
        "runtime" in line.lower() for line in lines if line.startswith("CodeDirectory ")
    ):
        return "developer-id"
    raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")


def _finance_json(raw: bytes) -> dict[str, Any]:
    # Check container depth before constructing objects; quoted delimiters do
    # not count. Byte limits are imposed by the fixed descriptor reader.
    depth = 0
    quoted = False
    escaped = False
    for value in raw:
        if quoted:
            if escaped:
                escaped = False
            elif value == 92:
                escaped = True
            elif value == 34:
                quoted = False
        elif value == 34:
            quoted = True
        elif value in (91, 123):
            depth += 1
            if depth > 32:
                raise InstallError("FIN003_SOURCE_METADATA_INVALID")
        elif value in (93, 125):
            depth -= 1

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            if key in value:
                raise InstallError("FIN003_SOURCE_METADATA_INVALID")
            value[key] = item
        return value

    def invalid_constant(_value: str) -> None:
        raise InstallError("FIN003_SOURCE_METADATA_INVALID")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise InstallError("FIN003_SOURCE_METADATA_INVALID")
    return value


def _finance_verified_helper(
    raw: bytes, source: Any, *, architecture: str, signing_kind: str
) -> Any:
    import hashlib
    from dataclasses import replace
    from ...core.finance_managed_profile import (
        MANAGED_HELPER_VERSION_REF,
        FinanceManagedHelperIdentityV1,
        VerifiedFinanceHelper,
        managed_ref,
        managed_wire_payload,
        validate_managed_record,
    )

    helper = FinanceManagedHelperIdentityV1(
        schema_version="uaa-finance-managed-helper.v1",
        helper_ref="pending:helper",
        helper_fingerprint_ref="helper-bytes-ref:sha256:"
        + hashlib.sha256(raw).hexdigest(),
        helper_size_bytes=len(raw),
        helper_version_ref=MANAGED_HELPER_VERSION_REF,
        architecture=architecture,
        source=source,
        signing_kind=signing_kind,
        publisher_verified=False,
        source_attestation_verified=False,
    )
    payload = managed_wire_payload(helper)
    del payload["helper_ref"]
    helper = replace(helper, helper_ref=managed_ref("helper", payload))
    validate_managed_record(helper)
    return VerifiedFinanceHelper(identity=helper, executable_bytes=raw)


def verified_developer_finance_helper(source_root: Path) -> VerifiedFinanceHelper:
    """Verify the fixed current-architecture build artifact without executing it."""
    import hashlib
    from dataclasses import replace
    from ...core.finance_managed_profile import (
        MANAGED_BUILD_MANIFEST_MAX_BYTES,
        MANAGED_HELPER_MAX_BYTES,
        DeveloperBuildSourceV1,
        managed_ref,
        managed_wire_payload,
        parse_helper_build_manifest,
    )
    from .contracts import current_architecture

    try:
        architecture = current_architecture()
        artifact = f"{_FINANCE_PACKAGE}/.uaa-artifacts/{architecture}"
        with _FinanceSourceCapture(source_root) as capture:
            source_bytes, builder_bytes = _finance_source_inputs(capture)
            manifest = parse_helper_build_manifest(
                capture.read(
                    f"{artifact}/helper-manifest-v1.json",
                    MANAGED_BUILD_MANIFEST_MAX_BYTES,
                )
            )
            raw = capture.read(
                f"{artifact}/helper", MANAGED_HELPER_MAX_BYTES, executable=True
            )
            if (
                manifest.architecture != architecture
                or _finance_macho_architecture(raw) != architecture
                or manifest.helper_sha256 != hashlib.sha256(raw).hexdigest()
                or manifest.helper_size_bytes != len(raw)
                or manifest.builder_sha256 != hashlib.sha256(builder_bytes).hexdigest()
                or tuple(
                    (item.source_ref, item.sha256) for item in manifest.source_files
                )
                != tuple(
                    ("repo-ref:" + name, hashlib.sha256(content).hexdigest())
                    for name, content in zip(
                        _FINANCE_SOURCE_FILES, source_bytes, strict=True
                    )
                )
            ):
                raise InstallError("FIN003_BUILD_ARTIFACT_STALE")
            capture.recheck()
            if _finance_signature_kind(source_root / artifact / "helper") != "ad-hoc":
                raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
            capture.recheck()
            source = DeveloperBuildSourceV1(
                kind="verified_developer_artifact",
                source_provenance_ref="pending:source",
                build_manifest_ref=manifest.manifest_ref,
                source_fingerprint_ref=manifest.source_fingerprint_ref,
                builder_fingerprint_ref=managed_ref(
                    "builder",
                    {
                        "builder_source_ref": manifest.builder_source_ref,
                        "builder_sha256": manifest.builder_sha256,
                    },
                ),
                build_recipe_ref=manifest.build_recipe_ref,
                artifact_selector_ref=manifest.artifact_selector_ref,
                verification="current-source-and-build-manifest-match",
            )
            payload = managed_wire_payload(source)
            del payload["source_provenance_ref"]
            source = replace(
                source, source_provenance_ref=managed_ref("source", payload)
            )
            return _finance_verified_helper(
                raw, source, architecture=architecture, signing_kind="ad-hoc"
            )
    except (OSError, ValueError, subprocess.SubprocessError, RecursionError):
        raise InstallError("FIN003_DEVELOPER_SOURCE_INVALID") from None


def verified_installed_finance_helper(layout: InstallLayout) -> VerifiedFinanceHelper:
    """Capture the fixed helper inside two fresh app signature/identity brackets."""
    import hashlib
    from dataclasses import replace
    from ...core.finance_managed_profile import (
        MANAGED_HELPER_MAX_BYTES,
        InstalledBundleSourceV1,
        managed_ref,
        managed_wire_payload,
    )
    from .contracts import _SAFE_TAG_RE, _VERSION_RE, current_architecture

    try:
        with _FinanceSourceCapture(layout.root) as capture:
            root_fd = capture.directories[""][0]
            selector = os.stat("current", dir_fd=root_fd, follow_symlinks=False)
            target = os.readlink("current", dir_fd=root_fd)
            parts = PurePosixPath(target).parts
            if (
                not stat.S_ISLNK(selector.st_mode)
                or selector.st_uid not in {0, os.getuid()}
                or len(parts) != 2
                or parts[0] != "versions"
                or target != "/".join(parts)
                or not _SAFE_VERSION_ID_RE.fullmatch(parts[1])
                or parts[1] in {".", ".."}
            ):
                raise InstallError("FIN003_INSTALLED_SOURCE_INVALID")
            version = parts[1]
            prefix = f"versions/{version}"
            app_relative = f"{prefix}/{APP_BUNDLE_NAME}"
            capture._directory(app_relative)
            capture._directory(f"{app_relative}/Contents/Helpers")
            capture._directory(f"{app_relative}/Contents/Resources")
            app = layout.root / app_relative

            def recheck() -> None:
                capture.recheck()
                if capture._identity(selector) != capture._identity(
                    os.stat("current", dir_fd=root_fd, follow_symlinks=False)
                ) or target != os.readlink("current", dir_fd=root_fd):
                    raise InstallError("FIN003_SOURCE_CHANGED")

            recheck()
            plist_path = f"{app_relative}/Contents/Info.plist"
            boundary_path = (
                f"{app_relative}/Contents/Resources/distribution-boundary.json"
            )
            helper_path = f"{app_relative}/{_FINANCE_HELPER}"
            for relative, maximum, executable in (
                (f"{prefix}/bundle-manifest.json", _FINANCE_INVENTORY_MAX_BYTES, False),
                (plist_path, _FINANCE_METADATA_MAX_BYTES, False),
                (boundary_path, _FINANCE_METADATA_MAX_BYTES, False),
                (helper_path, MANAGED_HELPER_MAX_BYTES, True),
            ):
                capture.retain(relative, maximum, executable=executable)
            recheck()
            first_signing_kind = _finance_signature_kind(app)
            recheck()
            inventory_raw = capture.read(
                f"{prefix}/bundle-manifest.json", _FINANCE_INVENTORY_MAX_BYTES
            )
            plist_raw = capture.read(plist_path, _FINANCE_METADATA_MAX_BYTES)
            boundary_raw = capture.read(boundary_path, _FINANCE_METADATA_MAX_BYTES)
            raw = capture.read(helper_path, MANAGED_HELPER_MAX_BYTES, executable=True)
            recheck()
            if _finance_signature_kind(app) != first_signing_kind:
                raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
            recheck()
            plist = plistlib.loads(plist_raw)
            boundary = _finance_json(boundary_raw)
            inventory = _finance_json(inventory_raw)
            architecture = current_architecture()
            commit = plist.get("UAASourceCommit") if isinstance(plist, dict) else None
            if (
                not isinstance(plist, dict)
                or plist.get("CFBundleIdentifier") != APP_BUNDLE_IDENTIFIER
                or not isinstance(plist.get("CFBundleShortVersionString"), str)
                or _VERSION_RE.fullmatch(plist["CFBundleShortVersionString"]) is None
                or not isinstance(plist.get("UAAReleaseTag"), str)
                or _SAFE_TAG_RE.fullmatch(plist["UAAReleaseTag"]) is None
                or plist.get("UAAUpdateChannel") not in {"stable", "dev"}
                or not isinstance(commit, str)
                or re.fullmatch("[0-9a-f]{40}", commit) is None
                or _finance_macho_architecture(raw) != architecture
                or boundary.get("schema_version")
                != "uaa.macos.distribution-boundary.v1"
                or boundary.get("product_line") != PRODUCT_LINE
                or boundary.get("architecture") != architecture
                or boundary.get("source_commit_ref") != f"git-commit:{commit}"
                or inventory.get("schema_version") != BUNDLE_MANIFEST_SCHEMA
                or inventory.get("product_line") != PRODUCT_LINE
                or inventory.get("app_bundle") != APP_BUNDLE_NAME
                or inventory.get("source_commit") != commit
                or inventory.get("architecture") != architecture
                or inventory.get("signing_kind") != first_signing_kind
                or inventory.get("version") != plist.get("CFBundleShortVersionString")
                or inventory.get("tag") != plist.get("UAAReleaseTag")
                or inventory.get("channel") != plist.get("UAAUpdateChannel")
                or boundary.get("tag_ref")
                != "git-tag:" + str(plist.get("UAAReleaseTag"))
                or boundary.get("channel") != plist.get("UAAUpdateChannel")
            ):
                raise InstallError("FIN003_SOURCE_METADATA_INVALID")
            entries = inventory.get("files")
            if (
                not isinstance(entries, list)
                or not 1 <= len(entries) <= MAX_ARCHIVE_FILES
            ):
                raise InstallError("FIN003_SOURCE_METADATA_INVALID")
            by_path: dict[str, dict[str, Any]] = {}
            for entry in entries:
                if (
                    not isinstance(entry, dict)
                    or set(entry) != {"path", "sha256", "size", "mode"}
                    or not isinstance(entry.get("path"), str)
                    or entry["path"] in by_path
                    or _safe_archive_path(entry["path"]).as_posix() != entry["path"]
                    or not isinstance(entry.get("sha256"), str)
                    or re.fullmatch("[0-9a-f]{64}", entry["sha256"]) is None
                    or type(entry.get("size")) is not int
                    or not 0 <= entry["size"] <= MAX_EXTRACTED_BYTES
                    or type(entry.get("mode")) is not int
                    or entry["mode"] not in {0o644, 0o755}
                ):
                    raise InstallError("FIN003_SOURCE_METADATA_INVALID")
                by_path[entry["path"]] = entry
            for relative, content in (
                (plist_path, plist_raw),
                (boundary_path, boundary_raw),
                (helper_path, raw),
            ):
                entry = by_path.get(relative.removeprefix(prefix + "/"))
                metadata = capture.files[relative][1]
                if (
                    entry is None
                    or entry.get("sha256") != hashlib.sha256(content).hexdigest()
                    or type(entry.get("size")) is not int
                    or entry["size"] != len(content)
                    or type(entry.get("mode")) is not int
                    or entry["mode"] != stat.S_IMODE(metadata.st_mode)
                ):
                    raise InstallError("FIN003_SOURCE_METADATA_INVALID")
            source = InstalledBundleSourceV1(
                kind="verified_installed_bundle",
                source_provenance_ref="pending:source",
                bundle_ref="macos-bundle-ref:sha256:"
                + hashlib.sha256(plist_raw).hexdigest(),
                bundle_inventory_ref="bundle-inventory-ref:sha256:"
                + hashlib.sha256(inventory_raw).hexdigest(),
                source_commit_ref=f"git-commit:{commit}",
                source_version_ref="macos-version-ref:sha256:"
                + hashlib.sha256(version.encode("ascii")).hexdigest(),
                verification="fresh-app-signature-and-exact-helper-bytes",
            )
            payload = managed_wire_payload(source)
            del payload["source_provenance_ref"]
            source = replace(
                source, source_provenance_ref=managed_ref("source", payload)
            )
            return _finance_verified_helper(
                raw, source, architecture=architecture, signing_kind=first_signing_kind
            )
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        RecursionError,
        plistlib.InvalidFileException,
    ):
        raise InstallError("FIN003_INSTALLED_SOURCE_INVALID") from None
