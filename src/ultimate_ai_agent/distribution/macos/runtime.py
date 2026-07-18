"""Installed macOS app and CLI runtime.

The app bundle and the ``uaa`` shell entry point both execute this module.
It serves the Python Core and production-built Control Center on loopback,
checks exact GitHub Releases for updates, and owns install rollback state.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .contracts import (
    APP_BUNDLE_NAME,
    DEFAULT_CHANNEL,
    DEFAULT_REPOSITORY,
    PRODUCT_LINE,
    ContractError,
    ReleaseDescriptor,
    current_architecture,
    normalize_channel,
    select_release,
)
from .github_releases import (
    GitHubReleaseClient,
    ReleaseCatalog,
    ReleaseTransportError,
    discover_github_token,
)
from .installer import (
    InstallError,
    InstallLayout,
    current_manifest,
    current_version_id,
    install_archive,
    rollback,
    uninstall,
)


RUNTIME_STATE_SCHEMA = "uaa.macos.runtime-state.v1"
UPDATE_STATE_SCHEMA = "uaa.macos.update-state.v1"
SETTINGS_SCHEMA = "uaa.macos.settings.v1"
RUNTIME_IDENTITY_SCHEMA = "uaa.macos.runtime-identity.v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_PORT_ATTEMPTS = 32
START_TIMEOUT_SECONDS = 30.0
STOP_TIMEOUT_SECONDS = 12.0
AUTO_UPDATE_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class RuntimePaths:
    install: InstallLayout

    @property
    def state_dir(self) -> Path:
        return self.install.root / "state"

    @property
    def runtime_state(self) -> Path:
        return self.state_dir / "runtime.json"

    @property
    def update_state(self) -> Path:
        return self.state_dir / "update.json"

    @property
    def settings(self) -> Path:
        return self.state_dir / "settings.json"

    @property
    def local_bearer(self) -> Path:
        return self.state_dir / "local-api-bearer"

    @property
    def downloads_dir(self) -> Path:
        return self.install.root / "downloads"


@dataclass(frozen=True)
class UpdateCheck:
    status: str
    catalog: ReleaseCatalog | None
    selected_tag: str | None
    selected_version_ref: str | None
    update_available: bool
    reason_ref: str
    descriptor: ReleaseDescriptor | None
    candidate: Any | None


def command_launch(
    paths: RuntimePaths,
    *,
    skip_update: bool,
    no_browser: bool,
) -> int:
    local_bearer = _ensure_local_bearer(paths)
    if not skip_update:
        update_result = command_update(
            paths,
            channel=None,
            check_only=False,
            force=False,
            quiet=True,
            timeout_seconds=AUTO_UPDATE_TIMEOUT_SECONDS,
        )
        if update_result == 10:
            command_stop(paths, quiet=True)
            executable = (
                paths.install.current_link
                / APP_BUNDLE_NAME
                / "Contents"
                / "MacOS"
                / APP_BUNDLE_NAME.removesuffix(".app")
            )
            os.execv(
                str(executable),
                [str(executable), "launch", "--skip-update"]
                + (["--no-browser"] if no_browser else []),
            )
        if update_result not in {0, 3}:
            print(
                "Update check was unavailable; launching the verified installed version."
            )
    state = _load_runtime_state(paths)
    if state is not None and _runtime_identity_matches(state):
        url = _runtime_url(int(state["port"]))
        if not no_browser:
            webbrowser.open(_session_url(url, local_bearer))
        print(f"Ultimate AI Agent is ready at {url}")
        return 0
    if state is not None:
        paths.runtime_state.unlink(missing_ok=True)
    port = _next_available_port(DEFAULT_HOST, DEFAULT_PORT)
    nonce = secrets.token_hex(16)
    manifest = current_manifest(paths.install)
    if manifest is None:
        print("Ultimate AI Agent is not installed. Run the installer first.")
        return 1
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "ultimate_ai_agent.distribution.macos.runtime",
        "_serve",
        "--port",
        str(port),
        "--nonce",
        nonce,
    ]
    environment = _runtime_environment(local_bearer=local_bearer)
    process = subprocess.Popen(
        command,
        cwd=paths.state_dir,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    state = {
        "schema_version": RUNTIME_STATE_SCHEMA,
        "status": "starting",
        "pid": process.pid,
        "port": port,
        "nonce": nonce,
        "version_ref": f"macos-version:{current_version_id(paths.install)}",
        "tag_ref": f"git-tag:{manifest['tag']}",
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "raw_paths_included": False,
        "credentials_included": False,
    }
    _write_json(paths.runtime_state, state, mode=0o600)
    deadline = time.monotonic() + START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            paths.runtime_state.unlink(missing_ok=True)
            print("Ultimate AI Agent runtime exited before becoming ready.")
            return 1
        if _runtime_identity_matches(state):
            state["status"] = "ready"
            _write_json(paths.runtime_state, state, mode=0o600)
            url = _runtime_url(port)
            if not no_browser:
                webbrowser.open(_session_url(url, local_bearer))
            print(f"Ultimate AI Agent is ready at {url}")
            return 0
        time.sleep(0.2)
    _terminate_owned_process(state)
    paths.runtime_state.unlink(missing_ok=True)
    print("Ultimate AI Agent runtime did not become ready in time.")
    return 1


def command_update(
    paths: RuntimePaths,
    *,
    channel: str | None,
    check_only: bool,
    force: bool,
    quiet: bool,
    timeout_seconds: float = 12.0,
) -> int:
    selected_channel = normalize_channel(channel or _load_channel(paths))
    token = discover_github_token()
    client = GitHubReleaseClient(
        repository=DEFAULT_REPOSITORY,
        token=token,
        timeout_seconds=timeout_seconds,
    )
    try:
        check = check_for_update(
            paths,
            client=client,
            channel=selected_channel,
            force=force,
        )
    except (ContractError, InstallError, ReleaseTransportError) as exc:
        _write_update_state(
            paths,
            status="unavailable",
            channel=selected_channel,
            selected_tag=None,
            reason_ref="reason-ref:update:catalog-unavailable",
            authenticated=bool(token),
        )
        if not quiet:
            print(f"Update unavailable: {exc}")
        return 3
    _write_update_state(
        paths,
        status=check.status,
        channel=selected_channel,
        selected_tag=check.selected_tag,
        reason_ref=check.reason_ref,
        authenticated=bool(token),
    )
    if check.candidate is None:
        if not quiet:
            print("No installable stable or dev macOS release is published yet.")
        return 0
    if not check.update_available:
        if not quiet:
            print(f"Already current: {check.selected_tag}")
        return 0
    if check_only:
        if not quiet:
            print(f"Update available: {check.selected_tag}")
        return 2
    paths.downloads_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".update-",
        dir=paths.downloads_dir,
    ) as temporary:
        archive = Path(temporary) / check.candidate.descriptor.artifact_name
        try:
            client.download_artifact(check.candidate, archive)
            result = install_archive(
                archive,
                check.candidate.descriptor,
                paths.install,
            )
        except (InstallError, ReleaseTransportError) as exc:
            _write_update_state(
                paths,
                status="failed",
                channel=selected_channel,
                selected_tag=check.selected_tag,
                reason_ref="reason-ref:update:install-failed",
                authenticated=bool(token),
            )
            if not quiet:
                print(f"Update failed: {exc}")
            return 1
    _save_channel(paths, selected_channel)
    _write_update_state(
        paths,
        status="installed",
        channel=selected_channel,
        selected_tag=check.selected_tag,
        reason_ref="reason-ref:update:installed",
        authenticated=bool(token),
        receipt_ref=result.receipt_ref,
    )
    if not quiet:
        print(f"Installed update: {result.tag}")
        print("Rollback available: uaa rollback")
    return 10


def check_for_update(
    paths: RuntimePaths,
    *,
    client: GitHubReleaseClient,
    channel: str,
    force: bool = False,
) -> UpdateCheck:
    architecture = current_architecture()
    catalog = client.fetch_catalog(architecture)
    selection = select_release(catalog.candidates, channel)
    candidate = selection.selected
    if candidate is None:
        return UpdateCheck(
            status="no-release",
            catalog=catalog,
            selected_tag=None,
            selected_version_ref=None,
            update_available=False,
            reason_ref="reason-ref:update:no-installable-release",
            descriptor=None,
            candidate=None,
        )
    installed = current_manifest(paths.install)
    update_available = installed is None
    reason_ref = "reason-ref:update:not-installed"
    if installed is not None:
        installed_time = _parse_timestamp(str(installed["source_timestamp"]))
        selected_time = candidate.descriptor.source_datetime
        if force:
            update_available = str(installed.get("tag")) != candidate.descriptor.tag
            reason_ref = "reason-ref:update:forced-candidate"
        elif selected_time > installed_time:
            update_available = True
            reason_ref = "reason-ref:update:newer-tag-commit"
        else:
            update_available = False
            reason_ref = "reason-ref:update:installed-is-current-or-newer"
    return UpdateCheck(
        status="available" if update_available else "current",
        catalog=catalog,
        selected_tag=candidate.descriptor.tag,
        selected_version_ref=(
            f"macos-version:{candidate.descriptor.tag}-"
            f"{candidate.descriptor.source_commit[:12]}"
        ),
        update_available=update_available,
        reason_ref=reason_ref,
        descriptor=candidate.descriptor,
        candidate=candidate,
    )


def command_status(paths: RuntimePaths, *, as_json: bool) -> int:
    manifest = current_manifest(paths.install)
    state = _load_runtime_state(paths)
    running = state is not None and _runtime_identity_matches(state)
    payload = {
        "schema_version": "uaa.macos.status.v1",
        "installed": manifest is not None,
        "tag_ref": f"git-tag:{manifest['tag']}" if manifest else None,
        "version": manifest.get("version") if manifest else None,
        "channel": _load_channel(paths),
        "runtime_status": "ready" if running else "stopped",
        "runtime_url": _runtime_url(int(state["port"])) if running and state else None,
        "rollback_available": paths.install.previous_link.is_symlink(),
        "github_auth_available": discover_github_token() is not None,
        "signing_kind": manifest.get("signing_kind") if manifest else None,
        "notarized": bool(manifest.get("notarized")) if manifest else False,
        "raw_paths_included": False,
        "credentials_included": False,
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Ultimate AI Agent macOS status")
        print(f"Installed: {'yes' if payload['installed'] else 'no'}")
        print(f"Release: {payload['tag_ref'] or 'none'}")
        print(f"Version: {payload['version'] or 'none'}")
        print(f"Update channel: {payload['channel']}")
        print(f"Runtime: {payload['runtime_status']}")
        if payload["runtime_url"]:
            print(f"Control Center: {payload['runtime_url']}")
        print(
            "GitHub update authentication: "
            + ("ready" if payload["github_auth_available"] else "missing")
        )
        print(f"Signature: {payload['signing_kind'] or 'none'}")
        print(f"Notarized: {'yes' if payload['notarized'] else 'no'}")
        print(
            "Rollback: "
            + ("available (`uaa rollback`)" if payload["rollback_available"] else "none")
        )
    return 0


def command_doctor(paths: RuntimePaths, *, as_json: bool) -> int:
    findings: list[dict[str, str]] = []

    def finding(name: str, status: str, summary: str) -> None:
        findings.append({"name": name, "status": status, "summary": summary})

    if platform.system() == "Darwin":
        finding("platform", "pass", "macOS detected")
    else:
        finding("platform", "fail", "the first-class app requires macOS")
    try:
        architecture = current_architecture()
        finding("architecture", "pass", f"{architecture} release lane supported")
    except ContractError:
        finding("architecture", "fail", "Mac architecture is unsupported")
    manifest = current_manifest(paths.install)
    if manifest is None:
        finding("installation", "fail", "no managed current version is installed")
    else:
        finding("installation", "pass", f"installed tag ref git-tag:{manifest['tag']}")
        resources = _resources_dir()
        if (resources / "control-center" / "index.html").is_file():
            finding("control-center", "pass", "production Control Center is packaged")
        else:
            finding("control-center", "fail", "packaged Control Center is missing")
        app = paths.install.current_link / APP_BUNDLE_NAME
        completed = subprocess.run(
            ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30.0,
            check=False,
        )
        if completed.returncode == 0:
            signing_kind = str(manifest.get("signing_kind", "unknown"))
            finding("code-signing", "pass", f"{signing_kind} signature verifies")
        else:
            finding("code-signing", "fail", "application signature verification failed")
        if manifest.get("notarized") is True:
            finding("notarization", "pass", "release records notarization")
        else:
            finding(
                "notarization",
                "warn",
                "not notarized; Developer ID credentials are still required",
            )
    app_entry_marker = (
        paths.install.app_link
        / "Contents"
        / "Resources"
        / "uaa-install-managed.json"
    )
    if paths.install.app_link.is_dir() and app_entry_marker.is_file():
        finding("applications-entry", "pass", "managed Applications entry exists")
    else:
        finding("applications-entry", "fail", "managed Applications entry is missing")
    if paths.install.cli_path.is_file():
        finding("cli-entry", "pass", "managed uaa shell command exists")
    else:
        finding("cli-entry", "fail", "managed uaa shell command is missing")
    if discover_github_token() is not None:
        finding("github-auth", "pass", "private release authentication is available")
    else:
        finding(
            "github-auth",
            "warn",
            "authenticate gh or set the updater token for private auto-updates",
        )
    failed = any(item["status"] == "fail" for item in findings)
    payload = {
        "schema_version": "uaa.macos.doctor.v1",
        "status": "failed" if failed else "ready",
        "findings": findings,
        "raw_paths_included": False,
        "credentials_included": False,
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Ultimate AI Agent macOS doctor")
        for item in findings:
            print(f"{item['status'].upper()}: {item['name']}: {item['summary']}")
    return 1 if failed else 0


def command_stop(paths: RuntimePaths, *, quiet: bool = False) -> int:
    state = _load_runtime_state(paths)
    if state is None:
        if not quiet:
            print("Ultimate AI Agent runtime is already stopped.")
        return 0
    if not _runtime_identity_matches(state):
        paths.runtime_state.unlink(missing_ok=True)
        if not quiet:
            print("Removed stale runtime state; no unverified process was stopped.")
        return 0
    _terminate_owned_process(state)
    paths.runtime_state.unlink(missing_ok=True)
    if not quiet:
        print("Ultimate AI Agent runtime stopped.")
    return 0


def command_rollback(paths: RuntimePaths, *, relaunch: bool) -> int:
    command_stop(paths, quiet=True)
    try:
        result = rollback(paths.install)
    except InstallError as exc:
        print(f"Rollback unavailable: {exc}")
        return 1
    print(f"Rolled back to {result.version_id}")
    print(f"Receipt: {result.receipt_ref}")
    return command_launch(paths, skip_update=True, no_browser=False) if relaunch else 0


def command_install_local(
    paths: RuntimePaths,
    *,
    archive: Path,
    descriptor_path: Path,
) -> int:
    try:
        descriptor = ReleaseDescriptor.from_json_bytes(
            descriptor_path.read_bytes(),
            expected_architecture=current_architecture(),
        )
        result = install_archive(archive, descriptor, paths.install)
    except (OSError, ContractError, InstallError) as exc:
        print(f"Install failed: {exc}")
        return 1
    print(f"Installed {result.tag}")
    print(f"Application entry: {APP_BUNDLE_NAME}")
    print("CLI entry: uaa")
    print(f"Receipt: {result.receipt_ref}")
    return 0


def command_uninstall(paths: RuntimePaths, *, purge_versions: bool) -> int:
    command_stop(paths, quiet=True)
    try:
        receipt_ref = uninstall(paths.install, purge_versions=purge_versions)
    except InstallError as exc:
        print(f"Uninstall failed: {exc}")
        return 1
    print("Removed installer-owned app and CLI entries.")
    if not purge_versions:
        print("Version data retained; use --purge-versions to remove it.")
    print(f"Receipt: {receipt_ref}")
    return 0


def command_serve(*, port: int, nonce: str) -> int:
    if not 1024 <= port <= 65535 or not secrets.compare_digest(
        nonce, nonce.strip()
    ):
        return 2
    if len(nonce) != 32 or any(char not in "0123456789abcdef" for char in nonce):
        return 2
    resources = _resources_dir()
    frontend = resources / "control-center"
    if not (frontend / "index.html").is_file():
        return 1
    from starlette.responses import FileResponse, JSONResponse
    from starlette.staticfiles import StaticFiles
    import uvicorn
    from ultimate_ai_agent.api.app import app as core_app

    assets_app = StaticFiles(directory=frontend / "assets")

    async def installed_app(
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        if scope.get("type") != "http":
            await core_app(scope, receive, send)
            return
        path = str(scope.get("path", ""))
        method = str(scope.get("method", "")).upper()
        if path == "/uaa-runtime-identity" and method == "GET":
            response = JSONResponse(
                {
                    "schema_version": RUNTIME_IDENTITY_SCHEMA,
                    "product_line": PRODUCT_LINE,
                    "nonce": nonce,
                },
                headers=_shell_security_headers(),
            )
            await response(scope, receive, send)
            return
        if path.startswith("/assets/") and method in {"GET", "HEAD"}:
            asset_scope = dict(scope)
            asset_scope["path"] = path.removeprefix("/assets")
            asset_scope["raw_path"] = asset_scope["path"].encode("utf-8")
            await assets_app(asset_scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        accepts_html = "text/html" in headers.get("accept", "")
        if method in {"GET", "HEAD"} and (path == "/" or accepts_html):
            requested = frontend / path.lstrip("/")
            if not (
                requested.is_file()
                and requested.suffix in {".html", ".ico", ".svg", ".png"}
            ):
                requested = frontend / "index.html"
            response = FileResponse(
                requested,
                headers=_shell_security_headers(),
            )
            await response(scope, receive, send)
            return
        await core_app(scope, receive, send)

    uvicorn.run(
        installed_app,
        host=DEFAULT_HOST,
        port=port,
        access_log=False,
        log_level="warning",
        server_header=False,
    )
    return 0


def _runtime_identity_matches(state: dict[str, Any]) -> bool:
    pid = state.get("pid")
    port = state.get("port")
    nonce = state.get("nonce")
    if (
        isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
        or isinstance(port, bool)
        or not isinstance(port, int)
        or not isinstance(nonce, str)
    ):
        return False
    try:
        os.kill(pid, 0)
    except (OSError, PermissionError):
        return False
    payload = _get_loopback_json(
        f"http://{DEFAULT_HOST}:{port}/uaa-runtime-identity",
        timeout=0.8,
    )
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == RUNTIME_IDENTITY_SCHEMA
        and payload.get("product_line") == PRODUCT_LINE
        and secrets.compare_digest(str(payload.get("nonce", "")), nonce)
    )


def _terminate_owned_process(state: dict[str, Any]) -> None:
    if not _runtime_identity_matches(state):
        return
    pid = int(state["pid"])
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + STOP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    if _runtime_identity_matches(state):
        os.kill(pid, signal.SIGKILL)


def _next_available_port(host: str, preferred: int) -> int:
    for port in range(preferred, min(65536, preferred + MAX_PORT_ATTEMPTS)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.1)
            if probe.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("no bounded loopback port is available")


def _runtime_environment(*, local_bearer: str) -> dict[str, str]:
    allowed = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "HOME",
            "LANG",
            "LC_ALL",
            "PATH",
            "TMPDIR",
            "UAA_APP_BUNDLE",
            "UAA_APP_RESOURCES",
            "UAA_API_LOCAL_BEARER",
        }
    }
    allowed.setdefault("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    allowed["PYTHONUNBUFFERED"] = "1"
    allowed["PYTHONDONTWRITEBYTECODE"] = "1"
    allowed["UAA_API_LOCAL_BEARER"] = local_bearer
    return allowed


def _resources_dir() -> Path:
    configured = os.environ.get("UAA_APP_RESOURCES", "").strip()
    if configured:
        return Path(configured)
    raise RuntimeError("packaged app resources are not configured")


def _runtime_url(port: int) -> str:
    return f"http://{DEFAULT_HOST}:{port}/"


def _session_url(url: str, local_bearer: str) -> str:
    return (
        url
        + "#uaa-session-bearer="
        + urllib.parse.quote(local_bearer, safe="")
    )


def _ensure_local_bearer(paths: RuntimePaths) -> str:
    try:
        existing = paths.local_bearer.read_text(encoding="utf-8").strip()
    except OSError:
        existing = ""
    if (
        40 <= len(existing) <= 128
        and all(char.isalnum() or char in "-_" for char in existing)
    ):
        return existing
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(48)
    temporary = paths.local_bearer.with_name(paths.local_bearer.name + ".tmp")
    temporary.write_text(value + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    os.replace(temporary, paths.local_bearer)
    return value


def _shell_security_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "Content-Security-Policy": (
            "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
            "object-src 'none'; form-action 'self'; img-src 'self' data:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* "
            "http://[::1]:*; script-src 'self'; style-src 'self' 'unsafe-inline'"
        ),
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        ),
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }


def _get_loopback_json(url: str, *, timeout: float) -> object | None:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Ultimate-AI-Agent-local-runtime/1"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read(64 * 1024)
        return json.loads(payload)
    except (
        OSError,
        urllib.error.URLError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return None


def _load_runtime_state(paths: RuntimePaths) -> dict[str, Any] | None:
    value = _load_json(paths.runtime_state)
    if not isinstance(value, dict) or value.get("schema_version") != RUNTIME_STATE_SCHEMA:
        return None
    return value


def _load_channel(paths: RuntimePaths) -> str:
    value = _load_json(paths.settings)
    if isinstance(value, dict) and value.get("schema_version") == SETTINGS_SCHEMA:
        try:
            return normalize_channel(str(value.get("update_channel", "")))
        except ContractError:
            pass
    return DEFAULT_CHANNEL


def _save_channel(paths: RuntimePaths, channel: str) -> None:
    _write_json(
        paths.settings,
        {
            "schema_version": SETTINGS_SCHEMA,
            "update_channel": normalize_channel(channel),
            "raw_paths_included": False,
            "credentials_included": False,
        },
        mode=0o600,
    )


def _write_update_state(
    paths: RuntimePaths,
    *,
    status: str,
    channel: str,
    selected_tag: str | None,
    reason_ref: str,
    authenticated: bool,
    receipt_ref: str | None = None,
) -> None:
    _write_json(
        paths.update_state,
        {
            "schema_version": UPDATE_STATE_SCHEMA,
            "status": status,
            "channel": channel,
            "selected_tag_ref": (
                f"git-tag:{selected_tag}" if selected_tag is not None else None
            ),
            "reason_ref": reason_ref,
            "authenticated": authenticated,
            "receipt_ref": receipt_ref,
            "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "raw_paths_included": False,
            "credentials_included": False,
        },
        mode=0o600,
    )


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _write_json(path: Path, value: dict[str, Any], *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(mode)
    os.replace(temporary, path)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ContractError("installed source timestamp is invalid")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="uaa",
        description="Ultimate AI Agent first-class macOS app and CLI",
    )
    subparsers = parser.add_subparsers(dest="command")
    launch_parser = subparsers.add_parser("launch", help="Update, start, and open Control Center")
    launch_parser.add_argument("--skip-update", action="store_true")
    launch_parser.add_argument("--no-browser", action="store_true")
    subparsers.add_parser("stop", help="Stop only the verified UAA local runtime")
    status_parser = subparsers.add_parser("status", help="Show installed/runtime/update status")
    status_parser.add_argument("--json", action="store_true")
    doctor_parser = subparsers.add_parser("doctor", help="Verify the installed app and CLI")
    doctor_parser.add_argument("--json", action="store_true")
    update_parser = subparsers.add_parser("update", help="Check and apply an exact GitHub Release")
    update_parser.add_argument("--channel", choices=["newest", "stable", "dev"])
    update_parser.add_argument("--check", action="store_true")
    update_parser.add_argument("--force", action="store_true")
    rollback_parser = subparsers.add_parser("rollback", help="Atomically restore the prior version")
    rollback_parser.add_argument("--relaunch", action="store_true")
    uninstall_parser = subparsers.add_parser("uninstall", help="Remove managed app and CLI entries")
    uninstall_parser.add_argument("--purge-versions", action="store_true")
    local_parser = subparsers.add_parser(
        "install-local",
        help="Install a locally built, descriptor-verified release artifact",
    )
    local_parser.add_argument("--archive", type=Path, required=True)
    local_parser.add_argument("--descriptor", type=Path, required=True)
    subparsers.add_parser("version", help="Print the installed release tag and package version")
    serve_parser = subparsers.add_parser("_serve")
    serve_parser.add_argument("--port", type=int, required=True)
    serve_parser.add_argument("--nonce", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = RuntimePaths(InstallLayout.default())
    command = args.command or "launch"
    try:
        if command == "launch":
            return command_launch(
                paths,
                skip_update=getattr(args, "skip_update", False),
                no_browser=getattr(args, "no_browser", False),
            )
        if command == "stop":
            return command_stop(paths)
        if command == "status":
            return command_status(paths, as_json=args.json)
        if command == "doctor":
            return command_doctor(paths, as_json=args.json)
        if command == "update":
            return command_update(
                paths,
                channel=args.channel,
                check_only=args.check,
                force=args.force,
                quiet=False,
            )
        if command == "rollback":
            return command_rollback(paths, relaunch=args.relaunch)
        if command == "uninstall":
            return command_uninstall(paths, purge_versions=args.purge_versions)
        if command == "install-local":
            return command_install_local(
                paths,
                archive=args.archive,
                descriptor_path=args.descriptor,
            )
        if command == "version":
            manifest = current_manifest(paths.install)
            if manifest is None:
                print("not-installed")
                return 1
            print(f"{manifest['tag']} ({manifest['version']})")
            return 0
        if command == "_serve":
            return command_serve(port=args.port, nonce=args.nonce)
    except (ContractError, InstallError, ReleaseTransportError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
