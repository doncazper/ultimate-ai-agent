#!/usr/bin/env python3
"""Run a redacted, isolated end-to-end macOS installer lifecycle."""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ultimate_ai_agent.distribution.macos.contracts import (
    APP_BUNDLE_IDENTIFIER,
    APP_BUNDLE_NAME,
    PRODUCT_LINE,
    ReleaseDescriptor,
)


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "packaging" / "macos" / "install.sh"
APP_EXECUTABLE_NAME = APP_BUNDLE_NAME.removesuffix(".app")
E2E_SCHEMA = "uaa.macos.installer-e2e.v1"
MAX_HTTP_BYTES = 4 * 1024 * 1024
SAFE_RECEIPT_STATUSES = {
    "already-current",
    "installed",
    "rolled-back",
    "uninstalled",
}
REQUIRED_SHELL_HEADERS = {
    "cache-control": "no-store",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


class InstallerE2EError(RuntimeError):
    """A lifecycle phase failed without exposing raw command output."""


@dataclass(frozen=True)
class LifecycleLayout:
    workspace: Path
    install_root: Path
    applications_dir: Path
    bin_dir: Path
    home: Path

    @classmethod
    def create(cls, workspace: Path) -> "LifecycleLayout":
        layout = cls(
            workspace=workspace,
            install_root=workspace / "install",
            applications_dir=workspace / "Applications",
            bin_dir=workspace / "bin",
            home=workspace / "home",
        )
        for path in (
            layout.install_root,
            layout.applications_dir,
            layout.bin_dir,
            layout.home,
            workspace / "tmp",
        ):
            path.mkdir(parents=True, exist_ok=True)
        return layout

    @property
    def cli(self) -> Path:
        return self.bin_dir / "uaa"

    @property
    def applications_app(self) -> Path:
        return self.applications_dir / APP_BUNDLE_NAME

    @property
    def current_app(self) -> Path:
        return self.install_root / "current" / APP_BUNDLE_NAME

    @property
    def local_bearer(self) -> Path:
        return self.install_root / "state" / "local-api-bearer"

    @property
    def receipts_dir(self) -> Path:
        return self.install_root / "receipts"

    def environment(self) -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"LANG", "LC_ALL", "PATH"}
        }
        environment.update(
            {
                "HOME": str(self.home),
                "PATH": environment.get(
                    "PATH",
                    "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                ),
                "TMPDIR": str(self.workspace / "tmp"),
                "UAA_APPLICATIONS_DIR": str(self.applications_dir),
                "UAA_INSTALL_BIN_DIR": str(self.bin_dir),
                "UAA_INSTALL_ROOT": str(self.install_root),
            }
        )
        return environment


def run_installer_e2e(
    *,
    archive: Path,
    descriptor_path: Path,
    previous_archive: Path | None = None,
    previous_descriptor_path: Path | None = None,
    check_update: bool = False,
    timeout_seconds: float = 45.0,
) -> dict[str, Any]:
    descriptor = _load_descriptor(descriptor_path)
    previous_descriptor = (
        _load_descriptor(previous_descriptor_path)
        if previous_descriptor_path is not None
        else None
    )
    _validate_input_pair(
        archive=archive,
        descriptor=descriptor,
        previous_archive=previous_archive,
        previous_descriptor=previous_descriptor,
    )
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="uaa-installer-e2e-") as temporary:
        layout = LifecycleLayout.create(Path(temporary))
        environment = layout.environment()
        runtime_started = False
        try:
            if previous_archive is not None and previous_descriptor is not None:
                _install(
                    previous_archive,
                    previous_descriptor_path,
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                _assert_installed_release(
                    layout,
                    previous_descriptor,
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                checks.append("previous-release-installed")

            _install(
                archive,
                descriptor_path,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            _assert_installed_release(
                layout,
                descriptor,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            checks.extend(
                [
                    "current-release-installed",
                    "applications-bundle-verified",
                    "cli-parity-verified",
                    "icon-and-plist-verified",
                ]
            )

            if previous_descriptor is not None:
                _run_cli(
                    layout,
                    ["rollback"],
                    label="rollback-to-previous",
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                _assert_version(
                    layout,
                    previous_descriptor,
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                _run_cli(
                    layout,
                    ["rollback"],
                    label="rollback-to-current",
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                _assert_version(
                    layout,
                    descriptor,
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                )
                checks.append("two-way-rollback-verified")

            receipt_count_before = len(list(layout.receipts_dir.glob("*.json")))
            _install(
                archive,
                descriptor_path,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            receipt_count_after = len(list(layout.receipts_dir.glob("*.json")))
            if receipt_count_after != receipt_count_before + 1:
                raise InstallerE2EError("idempotent install receipt count drifted")
            _assert_installed_release(
                layout,
                descriptor,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            checks.append("idempotent-reinstall-verified")

            _run_cli(
                layout,
                ["launch", "--skip-update", "--no-browser"],
                label="launch",
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            runtime_started = True
            status = _status(
                layout,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            validate_status_payload(
                status,
                expected_tag=descriptor.tag,
                expected_version=descriptor.version,
                expected_runtime_status="ready",
            )
            _verify_http_surfaces(layout, status)
            checks.extend(
                [
                    "runtime-lifecycle-verified",
                    "control-center-html-verified",
                    "protected-api-manifest-verified",
                ]
            )

            if check_update:
                _run_cli(
                    layout,
                    ["update", "--check"],
                    label="update-check",
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                    accepted_returncodes={0, 2},
                )
                checks.append("github-update-check-verified")

            _run_cli(
                layout,
                ["stop"],
                label="stop",
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            runtime_started = False
            stopped = _status(
                layout,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            validate_status_payload(
                stopped,
                expected_tag=descriptor.tag,
                expected_version=descriptor.version,
                expected_runtime_status="stopped",
            )
            _verify_no_runtime_mutation(layout)

            _run_cli(
                layout,
                ["uninstall"],
                label="uninstall",
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            if (
                layout.applications_app.exists()
                or layout.applications_app.is_symlink()
                or layout.cli.exists()
                or layout.cli.is_symlink()
                or not (layout.install_root / "current").is_symlink()
            ):
                raise InstallerE2EError("default uninstall ownership boundary drifted")
            _install(
                archive,
                descriptor_path,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            _assert_installed_release(
                layout,
                descriptor,
                environment=environment,
                timeout_seconds=timeout_seconds,
            )
            _verify_no_runtime_mutation(layout)
            validate_receipts(layout.receipts_dir, forbidden_text=str(layout.workspace))
            checks.extend(
                [
                    "runtime-stop-verified",
                    "uninstall-reinstall-verified",
                    "no-bytecode-mutation-verified",
                    "redacted-receipts-verified",
                ]
            )
        finally:
            if runtime_started and layout.cli.is_file():
                _run(
                    [str(layout.cli), "stop"],
                    label="cleanup-stop",
                    environment=environment,
                    timeout_seconds=timeout_seconds,
                    accepted_returncodes={0, 1},
                )

    return {
        "schema_version": E2E_SCHEMA,
        "status": "passed",
        "current_tag_ref": f"git-tag:{descriptor.tag}",
        "architecture": descriptor.architecture,
        "previous_round_trip": previous_descriptor is not None,
        "checks": checks,
        "raw_paths_included": False,
        "credentials_included": False,
    }


def validate_status_payload(
    payload: object,
    *,
    expected_tag: str,
    expected_version: str,
    expected_runtime_status: str,
) -> None:
    if not isinstance(payload, dict):
        raise InstallerE2EError("status payload is not an object")
    expected = {
        "schema_version": "uaa.macos.status.v1",
        "installed": True,
        "tag_ref": f"git-tag:{expected_tag}",
        "version": expected_version,
        "runtime_status": expected_runtime_status,
        "raw_paths_included": False,
        "credentials_included": False,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise InstallerE2EError("status payload failed the lifecycle contract")


def validate_receipts(receipts_dir: Path, *, forbidden_text: str) -> None:
    receipts = sorted(receipts_dir.glob("*.json"))
    if not receipts:
        raise InstallerE2EError("installer emitted no receipts")
    for receipt_path in receipts:
        try:
            raw = receipt_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InstallerE2EError("installer receipt is unreadable") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != "uaa.macos.install-receipt.v1"
            or payload.get("status") not in SAFE_RECEIPT_STATUSES
            or payload.get("raw_paths_included") is not False
            or payload.get("credentials_included") is not False
            or forbidden_text in raw
        ):
            raise InstallerE2EError("installer receipt failed its redaction contract")


def _load_descriptor(path: Path | None) -> ReleaseDescriptor:
    if path is None:
        raise InstallerE2EError("release descriptor path is required")
    try:
        return ReleaseDescriptor.from_json_bytes(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise InstallerE2EError("release descriptor is invalid") from exc


def _validate_input_pair(
    *,
    archive: Path,
    descriptor: ReleaseDescriptor,
    previous_archive: Path | None,
    previous_descriptor: ReleaseDescriptor | None,
) -> None:
    if not archive.is_file():
        raise InstallerE2EError("current release archive is missing")
    if (previous_archive is None) is not (previous_descriptor is None):
        raise InstallerE2EError("previous release inputs must be provided together")
    if previous_archive is not None and not previous_archive.is_file():
        raise InstallerE2EError("previous release archive is missing")
    if previous_descriptor is not None:
        if previous_descriptor.architecture != descriptor.architecture:
            raise InstallerE2EError("release architectures do not match")
        if previous_descriptor.source_datetime >= descriptor.source_datetime:
            raise InstallerE2EError("previous release is not older than current release")


def _install(
    archive: Path,
    descriptor_path: Path | None,
    *,
    environment: dict[str, str],
    timeout_seconds: float,
) -> None:
    if descriptor_path is None:
        raise InstallerE2EError("installer descriptor is missing")
    _run(
        [
            str(INSTALLER),
            "--local-archive",
            str(archive),
            "--local-descriptor",
            str(descriptor_path),
        ],
        label="install",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )


def _assert_installed_release(
    layout: LifecycleLayout,
    descriptor: ReleaseDescriptor,
    *,
    environment: dict[str, str],
    timeout_seconds: float,
) -> None:
    if (
        not layout.applications_app.is_dir()
        or layout.applications_app.is_symlink()
        or not layout.cli.is_file()
        or layout.cli.is_symlink()
    ):
        raise InstallerE2EError("installer entry points are incomplete")
    if stat.S_IMODE(layout.cli.stat().st_mode) != 0o755:
        raise InstallerE2EError("installer CLI mode drifted")
    current = layout.install_root / "current"
    versions = (layout.install_root / "versions").resolve(strict=True)
    try:
        current.resolve(strict=True).relative_to(versions)
    except (OSError, ValueError) as exc:
        raise InstallerE2EError("current version pointer left the managed root") from exc

    _assert_version(
        layout,
        descriptor,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    _run_cli(
        layout,
        ["doctor", "--json"],
        label="doctor",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    app_executable = (
        layout.applications_app
        / "Contents"
        / "MacOS"
        / APP_EXECUTABLE_NAME
    )
    applications_version = _run(
        [str(app_executable), "version"],
        label="applications-executable",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    if applications_version.strip() != f"{descriptor.tag} ({descriptor.version})":
        raise InstallerE2EError("Applications executable version identity drifted")
    _run(
        [
            "/usr/bin/codesign",
            "--verify",
            "--deep",
            "--strict",
            str(layout.applications_app),
        ],
        label="applications-signature",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    file_kind = _run(
        ["/usr/bin/file", "-b", str(app_executable)],
        label="native-launcher",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    if "Mach-O" not in file_kind:
        raise InstallerE2EError("application launcher is not native Mach-O")
    _verify_plist_and_icon(layout.applications_app, descriptor)


def _verify_plist_and_icon(
    app: Path,
    descriptor: ReleaseDescriptor,
) -> None:
    plist_path = app / "Contents" / "Info.plist"
    try:
        with plist_path.open("rb") as handle:
            plist = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        raise InstallerE2EError("installed Info.plist is invalid") from exc
    icon_name = plist.get("CFBundleIconFile")
    if (
        plist.get("CFBundleIdentifier") != APP_BUNDLE_IDENTIFIER
        or plist.get("CFBundlePackageType") != "APPL"
        or plist.get("CFBundleShortVersionString") != descriptor.version
        or plist.get("UAAReleaseTag") != descriptor.tag
        or plist.get("UAAUpdateChannel") != descriptor.channel
        or not isinstance(icon_name, str)
        or not icon_name.endswith(".icns")
    ):
        raise InstallerE2EError("installed app identity or icon binding drifted")
    icon = app / "Contents" / "Resources" / icon_name
    if not icon.is_file() or icon.stat().st_size < 100_000:
        raise InstallerE2EError("installed macOS icon is missing or incomplete")
    marker = app / "Contents" / "Resources" / "uaa-install-managed.json"
    try:
        ownership = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallerE2EError("installed ownership marker is invalid") from exc
    if not isinstance(ownership, dict) or ownership.get("product_line") != PRODUCT_LINE:
        raise InstallerE2EError("installed ownership marker drifted")


def _assert_version(
    layout: LifecycleLayout,
    descriptor: ReleaseDescriptor,
    *,
    environment: dict[str, str],
    timeout_seconds: float,
) -> None:
    output = _run_cli(
        layout,
        ["version"],
        label="version",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    if output.strip() != f"{descriptor.tag} ({descriptor.version})":
        raise InstallerE2EError("installed version identity drifted")


def _status(
    layout: LifecycleLayout,
    *,
    environment: dict[str, str],
    timeout_seconds: float,
) -> object:
    output = _run_cli(
        layout,
        ["status", "--json"],
        label="status",
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise InstallerE2EError("status output is not valid JSON") from exc


def _verify_http_surfaces(
    layout: LifecycleLayout,
    status: dict[str, Any],
) -> None:
    runtime_url = status.get("runtime_url")
    if not isinstance(runtime_url, str) or not runtime_url.startswith(
        "http://127.0.0.1:"
    ):
        raise InstallerE2EError("runtime URL is not exact loopback")
    html, headers = _http_get(
        runtime_url,
        headers={"Accept": "text/html"},
    )
    if b"Ultimate AI Agent Control Center" not in html:
        raise InstallerE2EError("Control Center production HTML is missing")
    for name, expected in REQUIRED_SHELL_HEADERS.items():
        if headers.get(name) != expected:
            raise InstallerE2EError("Control Center security header drifted")

    try:
        bearer = layout.local_bearer.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise InstallerE2EError("local API bearer is unavailable") from exc
    if (
        len(bearer) < 48
        or stat.S_IMODE(layout.local_bearer.stat().st_mode) != 0o600
    ):
        raise InstallerE2EError("local API bearer contract drifted")
    manifest_bytes, _ = _http_get(
        runtime_url.rstrip("/") + "/api/manifest",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer}",
        },
    )
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallerE2EError("protected API manifest is invalid") from exc
    if not isinstance(manifest, dict) or not manifest:
        raise InstallerE2EError("protected API manifest is empty")


def _http_get(
    url: str,
    *,
    headers: dict[str, str],
) -> tuple[bytes, dict[str, str]]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with opener.open(request, timeout=5.0) as response:
            payload = response.read(MAX_HTTP_BYTES + 1)
            response_headers = {
                name.lower(): value for name, value in response.headers.items()
            }
    except (OSError, urllib.error.URLError) as exc:
        raise InstallerE2EError("loopback HTTP verification failed") from exc
    if len(payload) > MAX_HTTP_BYTES:
        raise InstallerE2EError("loopback HTTP response exceeded its limit")
    return payload, response_headers


def _verify_no_runtime_mutation(layout: LifecycleLayout) -> None:
    for app in (layout.current_app, layout.applications_app):
        if any(app.rglob("__pycache__")) or any(app.rglob("*.pyc")):
            raise InstallerE2EError("installed app was mutated by Python bytecode")


def _run_cli(
    layout: LifecycleLayout,
    arguments: Iterable[str],
    *,
    label: str,
    environment: dict[str, str],
    timeout_seconds: float,
    accepted_returncodes: set[int] | None = None,
) -> str:
    return _run(
        [str(layout.cli), *arguments],
        label=label,
        environment=environment,
        timeout_seconds=timeout_seconds,
        accepted_returncodes=accepted_returncodes,
    )


def _run(
    command: list[str],
    *,
    label: str,
    environment: dict[str, str],
    timeout_seconds: float,
    accepted_returncodes: set[int] | None = None,
) -> str:
    accepted = {0} if accepted_returncodes is None else accepted_returncodes
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallerE2EError(f"{label} command could not run") from exc
    if completed.returncode not in accepted:
        raise InstallerE2EError(f"{label} command failed")
    return completed.stdout


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the complete first-class macOS installer lifecycle"
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--descriptor", type=Path, required=True)
    parser.add_argument("--previous-archive", type=Path)
    parser.add_argument("--previous-descriptor", type=Path)
    parser.add_argument("--check-update", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if (args.previous_archive is None) is not (args.previous_descriptor is None):
        print("FAIL: previous release inputs must be provided together")
        return 2
    try:
        result = run_installer_e2e(
            archive=args.archive,
            descriptor_path=args.descriptor,
            previous_archive=args.previous_archive,
            previous_descriptor_path=args.previous_descriptor,
            check_update=args.check_update,
            timeout_seconds=args.timeout_seconds,
        )
    except InstallerE2EError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
