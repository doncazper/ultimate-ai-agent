#!/usr/bin/env python3
"""Local developer launcher for the Ultimate AI Agent prototype.

This module is intentionally stdlib-only and localhost-only. It starts the
existing FastAPI API boundary and the existing Control Center Vite dev server;
it does not add any agent, action, or tool authority.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173
OPENWEBUI_HOST = "127.0.0.1"
OPENWEBUI_PORT = 3000
OPENWEBUI_CONTAINER_NAME = "uaa-openwebui-local"
OPENWEBUI_IMAGE = "ghcr.io/open-webui/open-webui:main"
OPENWEBUI_GATEWAY_FOR_CONTAINER = "http://host.docker.internal:8000/v1"
UAA_OPENWEBUI_TEST_GATEWAY_ENV = "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"
UAA_OPENWEBUI_TEST_GATEWAY_VALUE = "uaa-local-test"
SAFE_HOSTS = {"127.0.0.1", "localhost", "::1"}
STATE_DIR = Path(".uaa") / "dev"
BACKEND_HEALTH_PATH = "/health"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
OPENWEBUI_URL = f"http://{OPENWEBUI_HOST}:{OPENWEBUI_PORT}"
SECRET_ENV_MARKERS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "PRIVATE",
    "CREDENTIAL",
    "AUTH",
    "COOKIE",
    "API_KEY",
    "KEYCHAIN",
)


@dataclass(frozen=True)
class Service:
    name: str
    url: str
    health_url: str
    pid_file: Path
    log_file: Path
    metadata_file: Path
    cwd: Path
    command: list[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_local_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized not in SAFE_HOSTS:
        raise ValueError(f"Host must be localhost-only, got: {host}")
    return host


def build_backend_command(root: Path) -> list[str]:
    validate_local_host(BACKEND_HOST)
    return [
        str(root / ".venv" / "bin" / "python"),
        "-m",
        "uvicorn",
        "ultimate_ai_agent.api.app:app",
        "--host",
        BACKEND_HOST,
        "--port",
        str(BACKEND_PORT),
    ]


def build_frontend_command(root: Path) -> list[str]:
    _ = root
    validate_local_host(FRONTEND_HOST)
    return [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        FRONTEND_HOST,
        "--port",
        str(FRONTEND_PORT),
    ]


def build_openwebui_command(root: Path) -> list[str]:
    validate_local_host(OPENWEBUI_HOST)
    data_dir = root / STATE_DIR / "openwebui-data"
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        OPENWEBUI_CONTAINER_NAME,
        "-p",
        f"{OPENWEBUI_HOST}:{OPENWEBUI_PORT}:8080",
        "-v",
        f"{data_dir}:/app/backend/data",
        "-e",
        f"OPENAI_API_BASE_URL={OPENWEBUI_GATEWAY_FOR_CONTAINER}",
        "-e",
        f"OPENAI_API_KEY={UAA_OPENWEBUI_TEST_GATEWAY_VALUE}",
        OPENWEBUI_IMAGE,
    ]


def runtime_paths(root: Path) -> tuple[Path, Path, Path]:
    base = root / STATE_DIR
    return base, base / "pids", base / "logs"


def service_config(root: Path, name: str) -> Service:
    base, pid_dir, log_dir = runtime_paths(root)
    if name == "backend":
        return Service(
            name="backend",
            url=BACKEND_URL,
            health_url=f"{BACKEND_URL}{BACKEND_HEALTH_PATH}",
            pid_file=pid_dir / "backend.pid",
            log_file=log_dir / "backend.log",
            metadata_file=base / "backend.json",
            cwd=root,
            command=build_backend_command(root),
        )
    if name == "frontend":
        app_root = root / "apps" / "control-center"
        return Service(
            name="frontend",
            url=FRONTEND_URL,
            health_url=FRONTEND_URL,
            pid_file=pid_dir / "frontend.pid",
            log_file=log_dir / "frontend.log",
            metadata_file=base / "frontend.json",
            cwd=app_root,
            command=build_frontend_command(root),
        )
    if name == "openwebui":
        return Service(
            name="openwebui",
            url=OPENWEBUI_URL,
            health_url=OPENWEBUI_URL,
            pid_file=pid_dir / "openwebui.pid",
            log_file=log_dir / "openwebui.log",
            metadata_file=base / "openwebui.json",
            cwd=root,
            command=build_openwebui_command(root),
        )
    raise ValueError(f"Unknown service: {name}")


def safe_env(root: Path, service_name: str) -> dict[str, str]:
    allowed_keys = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "USER", "SHELL", "TERM"}
    env = {key: value for key, value in os.environ.items() if key in allowed_keys}
    env["PYTHONUNBUFFERED"] = "1"
    if service_name == "backend":
        env["PYTHONPATH"] = str(root / "src")
        if os.environ.get(UAA_OPENWEBUI_TEST_GATEWAY_ENV):
            env[UAA_OPENWEBUI_TEST_GATEWAY_ENV] = os.environ[UAA_OPENWEBUI_TEST_GATEWAY_ENV]
    if service_name == "frontend":
        env["VITE_UAA_API_BASE_URL"] = ""
    return {key: value for key, value in env.items() if not _is_secret_env_key(key)}


def _is_secret_env_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in SECRET_ENV_MARKERS)


def ensure_state_dirs(root: Path) -> None:
    base, pid_dir, log_dir = runtime_paths(root)
    base.mkdir(parents=True, exist_ok=True)
    pid_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)


def read_pid_file(pid_path: Path) -> int | None:
    try:
        text = pid_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def cleanup_stale_pid(pid_path: Path, is_running: Callable[[int], bool] = is_pid_running) -> str:
    pid = read_pid_file(pid_path)
    if pid is None:
        if pid_path.exists():
            pid_path.unlink()
            return "removed_stale"
        return "missing"
    if is_running(pid):
        return "running"
    pid_path.unlink(missing_ok=True)
    return "removed_stale"


def metadata_matches_service(service: Service, pid: int) -> bool:
    try:
        data = json.loads(service.metadata_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    return (
        data.get("name") == service.name
        and data.get("pid") == pid
        and data.get("command") == service.command
        and data.get("cwd") == str(service.cwd)
    )


def is_port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    validate_local_host(host)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def wait_for_url(url: str, timeout_seconds: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    return False


def url_status(url: str, headers: dict[str, str] | None = None, timeout: float = 2.0) -> int | None:
    try:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (OSError, urllib.error.URLError):
        return None


def check_doctor(root: Path) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    failures: list[str] = []
    if root.joinpath("pyproject.toml").exists() and root.joinpath("src", "ultimate_ai_agent").exists():
        ok.append("repo root detected")
    else:
        failures.append("not running from the Ultimate AI Agent repo root")

    python_path = root / ".venv" / "bin" / "python"
    if python_path.exists():
        ok.append(f"Python environment found: {python_path}")
    else:
        failures.append("missing .venv/bin/python; run: python3 -m venv .venv && .venv/bin/python -m pip install -e \".[dev]\"")

    app_root = root / "apps" / "control-center"
    package_json = app_root / "package.json"
    if package_json.exists():
        ok.append("Control Center package.json found")
        text = package_json.read_text(encoding="utf-8")
        if '"dev"' in text:
            ok.append("Control Center dev script found")
        else:
            failures.append("apps/control-center/package.json has no dev script")
    else:
        failures.append("missing apps/control-center/package.json")

    if app_root.joinpath("node_modules").exists():
        ok.append("Control Center node_modules found")
    else:
        failures.append("missing apps/control-center/node_modules; run: cd apps/control-center && npm install")

    if not _command_exists("npm"):
        failures.append("npm is not available on PATH")
    else:
        ok.append("npm found on PATH")

    if is_port_open(BACKEND_HOST, BACKEND_PORT):
        ok.append(f"backend port already in use on {BACKEND_URL}")
    else:
        ok.append(f"backend port is free: {BACKEND_URL}")
    if is_port_open(FRONTEND_HOST, FRONTEND_PORT):
        ok.append(f"frontend port already in use on {FRONTEND_URL}")
    else:
        ok.append(f"frontend port is free: {FRONTEND_URL}")

    return ok, failures


def check_openwebui_doctor(root: Path) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    failures: list[str] = []
    if not _command_exists("docker"):
        failures.append("Docker is not available on PATH")
    else:
        ok.append("Docker found on PATH")

    if is_port_open(OPENWEBUI_HOST, OPENWEBUI_PORT):
        ok.append(f"OpenWebUI port already in use on {OPENWEBUI_URL}")
    else:
        ok.append(f"OpenWebUI port is free: {OPENWEBUI_URL}")

    health_status = url_status(f"{BACKEND_URL}{BACKEND_HEALTH_PATH}")
    if health_status is None:
        failures.append("UAA backend is not reachable; run: UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start")
    elif 200 <= health_status < 500:
        ok.append(f"UAA backend reachable at {BACKEND_URL}")
    else:
        failures.append(f"UAA backend health returned HTTP {health_status}")

    gateway_status = url_status(
        f"{BACKEND_URL}/v1/models",
        headers={"Authorization": f"Bearer {UAA_OPENWEBUI_TEST_GATEWAY_VALUE}"},
    )
    if gateway_status == 200:
        ok.append("UAA local OpenWebUI test gateway is enabled")
    elif gateway_status == 403:
        failures.append("UAA local OpenWebUI test gateway is disabled; restart backend with UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1")
    elif gateway_status == 401:
        failures.append("UAA local OpenWebUI test gateway rejected the local bearer value")
    elif gateway_status is None:
        failures.append("UAA local OpenWebUI test gateway is not reachable")
    else:
        failures.append(f"UAA local OpenWebUI test gateway returned HTTP {gateway_status}")

    data_dir = root / STATE_DIR / "openwebui-data"
    ok.append(f"OpenWebUI data directory: {data_dir}")
    return ok, failures


def _command_exists(command: str) -> bool:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if directory and Path(directory, command).exists():
            return True
    return False


def start_service(root: Path, service: Service) -> str:
    ensure_state_dirs(root)
    state = cleanup_stale_pid(service.pid_file)
    if state == "running":
        return f"{service.name}: already running (pid {read_pid_file(service.pid_file)})"

    if service.name == "backend" and is_port_open(BACKEND_HOST, BACKEND_PORT):
        return f"{service.name}: {service.url} is already responding; not starting a duplicate"
    if service.name == "frontend" and is_port_open(FRONTEND_HOST, FRONTEND_PORT):
        return f"{service.name}: {service.url} is already responding; not starting a duplicate"
    if service.name == "openwebui" and is_port_open(OPENWEBUI_HOST, OPENWEBUI_PORT):
        return f"{service.name}: {service.url} is already responding; not starting a duplicate"

    if service.name == "backend" and not Path(service.command[0]).exists():
        raise RuntimeError("missing .venv/bin/python; run uaa doctor")
    if service.name == "frontend" and not service.cwd.joinpath("node_modules").exists():
        raise RuntimeError("missing apps/control-center/node_modules; run uaa doctor")
    if service.name == "openwebui":
        if not _command_exists("docker"):
            raise RuntimeError("Docker is not available on PATH; install Docker and run uaa openwebui doctor")
        (root / STATE_DIR / "openwebui-data").mkdir(parents=True, exist_ok=True)

    service.log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = service.log_file.open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            service.command,
            cwd=service.cwd,
            env=safe_env(root, service.name),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    finally:
        log_handle.close()
    service.pid_file.write_text(f"{process.pid}\n", encoding="utf-8")
    service.metadata_file.write_text(
        json.dumps(
            {
                "name": service.name,
                "pid": process.pid,
                "command": service.command,
                "cwd": str(service.cwd),
                "url": service.url,
                "log_file": str(service.log_file),
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if not wait_for_url(service.health_url):
        return f"{service.name}: started pid {process.pid}, but health check is not ready yet; see {service.log_file}"
    return f"{service.name}: running at {service.url} (pid {process.pid}); log {service.log_file}"


def stop_service(service: Service) -> str:
    state = cleanup_stale_pid(service.pid_file)
    if state == "missing":
        return f"{service.name}: not running"
    if state == "removed_stale":
        service.metadata_file.unlink(missing_ok=True)
        return f"{service.name}: removed stale pid file"
    pid = read_pid_file(service.pid_file)
    if pid is None:
        return f"{service.name}: not running"
    if not metadata_matches_service(service, pid):
        service.pid_file.unlink(missing_ok=True)
        service.metadata_file.unlink(missing_ok=True)
        return f"{service.name}: removed untrusted pid file"
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise RuntimeError(f"{service.name}: no permission to stop launcher pid {pid}") from exc
    for _ in range(20):
        if not is_pid_running(pid):
            break
        time.sleep(0.1)
    if is_pid_running(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    service.pid_file.unlink(missing_ok=True)
    service.metadata_file.unlink(missing_ok=True)
    return f"{service.name}: stopped launcher pid {pid}"


def status_for_service(service: Service) -> str:
    state = cleanup_stale_pid(service.pid_file)
    if state == "running":
        return f"{service.name}: running pid={read_pid_file(service.pid_file)} url={service.url} log={service.log_file}"
    if state == "removed_stale":
        return f"{service.name}: not running (removed stale pid file) log={service.log_file}"
    return f"{service.name}: not running url={service.url} log={service.log_file}"


def _zsh_single_quote(value: Path) -> str:
    return "'" + str(value).replace("'", "'\\''") + "'"


def render_macos_launcher(repo_path: Path | None = None) -> str:
    repo_cd = f"cd {_zsh_single_quote(repo_path)}" if repo_path is not None else 'cd "$SCRIPT_DIR"'
    return """#!/bin/zsh
set -u
SCRIPT_DIR="${{0:A:h}}"
{repo_cd}

echo "Ultimate AI Agent local launcher"
echo "Developer-only, localhost-only, non-production."
echo
./scripts/dev/uaa doctor
DOCTOR_STATUS=$?
if [ "$DOCTOR_STATUS" -ne 0 ]; then
  echo
  echo "Doctor checks failed. Fix the setup above, then run again."
  echo "Press any key to close..."
  read -k 1
  exit "$DOCTOR_STATUS"
fi

./scripts/dev/uaa start
./scripts/dev/uaa ui
./scripts/dev/uaa status

echo
echo "Logs are under .uaa/dev/logs/"
echo "Press any key to close..."
read -k 1
""".format(repo_cd=repo_cd)


def create_macos_launcher(root: Path, target: str) -> Path:
    if target == "repo":
        output = root / "Ultimate AI Agent.command"
    elif target == "desktop":
        output = Path.home() / "Desktop" / "Ultimate AI Agent.command"
    else:
        raise ValueError("--target must be repo or desktop")
    output.write_text(render_macos_launcher(None if target == "repo" else root), encoding="utf-8")
    output.chmod(0o755)
    return output


def command_doctor(root: Path) -> int:
    ok, failures = check_doctor(root)
    print("Ultimate AI Agent local launcher doctor")
    for line in ok:
        print(f"OK: {line}")
    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        print("\nNo dependencies were installed. Fix the items above and retry.")
        return 1
    return 0


def command_start(root: Path) -> int:
    for host in [BACKEND_HOST, FRONTEND_HOST]:
        validate_local_host(host)
    for name in ["backend", "frontend"]:
        print(start_service(root, service_config(root, name)))
    print(f"\nControl Center: {FRONTEND_URL}")
    print(f"Logs: {root / STATE_DIR / 'logs'}")
    return 0


def command_ui(root: Path) -> int:
    frontend = service_config(root, "frontend")
    if cleanup_stale_pid(frontend.pid_file) != "running":
        print("Control Center is not running. Run: uaa start")
        return 1
    webbrowser.open(frontend.url)
    print(f"Opened {frontend.url}")
    return 0


def command_status(root: Path) -> int:
    version = _read_version(root)
    print(f"Ultimate AI Agent version: {version}")
    for name in ["backend", "frontend"]:
        print(status_for_service(service_config(root, name)))
    return 0


def command_openwebui_doctor(root: Path) -> int:
    ok, failures = check_openwebui_doctor(root)
    print("Ultimate AI Agent OpenWebUI local test doctor")
    for line in ok:
        print(f"OK: {line}")
    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        print("\nOpenWebUI was not started. Fix the items above and retry.")
        return 1
    return 0


def command_openwebui_start(root: Path) -> int:
    service = service_config(root, "openwebui")
    print(start_service(root, service))
    print(f"\nOpenWebUI: {OPENWEBUI_URL}")
    print(f"UAA gateway for OpenWebUI: {OPENWEBUI_GATEWAY_FOR_CONTAINER}")
    print("Model: uaa-safe-local")
    print(f"Local bearer value: {UAA_OPENWEBUI_TEST_GATEWAY_VALUE}")
    return 0


def command_openwebui_status(root: Path) -> int:
    print(status_for_service(service_config(root, "openwebui")))
    gateway_status = url_status(
        f"{BACKEND_URL}/v1/models",
        headers={"Authorization": f"Bearer {UAA_OPENWEBUI_TEST_GATEWAY_VALUE}"},
    )
    print(f"uaa-gateway: {'reachable' if gateway_status == 200 else f'not ready ({gateway_status})'}")
    return 0


def command_openwebui_logs(root: Path, follow: bool = False) -> int:
    service = service_config(root, "openwebui")
    if not service.log_file.exists():
        print(f"No OpenWebUI log yet: {service.log_file}")
        return 0
    print(f"==> {service.log_file}")
    lines = service.log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
    for line in lines:
        print(line)
    if follow:
        position = service.log_file.stat().st_size
        print("\nFollowing OpenWebUI log. Press Ctrl-C to stop.")
        try:
            while True:
                with service.log_file.open("r", encoding="utf-8", errors="replace") as handle:
                    handle.seek(position)
                    chunk = handle.read()
                    position = handle.tell()
                if chunk:
                    print(chunk, end="" if chunk.endswith("\n") else "\n")
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nStopped following OpenWebUI log.")
    return 0


def command_openwebui_stop(root: Path) -> int:
    service = service_config(root, "openwebui")
    print(stop_service(service))
    if _command_exists("docker"):
        subprocess.run(["docker", "rm", "-f", OPENWEBUI_CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


def command_logs(root: Path, follow: bool = False) -> int:
    log_dir = root / STATE_DIR / "logs"
    if not log_dir.exists():
        print(f"No logs yet: {log_dir}")
        return 0
    log_files = sorted(log_dir.glob("*.log"))
    for log_file in log_files:
        print(f"==> {log_file}")
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
        for line in lines:
            print(line)
    if follow:
        positions = {path: path.stat().st_size for path in log_files}
        print("\nFollowing logs. Press Ctrl-C to stop.")
        try:
            while True:
                for path in log_files:
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(positions[path])
                        chunk = handle.read()
                        positions[path] = handle.tell()
                    if chunk:
                        print(f"==> {path}")
                        print(chunk, end="" if chunk.endswith("\n") else "\n")
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nStopped following logs.")
    return 0


def command_stop(root: Path) -> int:
    for name in ["frontend", "backend"]:
        print(stop_service(service_config(root, name)))
    return 0


def _read_version(root: Path) -> str:
    version_file = root / "VERSION.md"
    if not version_file.exists():
        return "unknown"
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if "Current active baseline:" in line:
            return line.split("**")[1] if "**" in line else line
    return "unknown"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="uaa", description="Local Ultimate AI Agent developer launcher")
    subparsers = parser.add_subparsers(dest="command")
    for command in ["doctor", "start", "ui", "status", "stop", "restart", "help"]:
        subparsers.add_parser(command)
    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("--follow", action="store_true")
    openwebui_parser = subparsers.add_parser("openwebui")
    openwebui_subparsers = openwebui_parser.add_subparsers(dest="openwebui_command")
    for command in ["doctor", "start", "status", "stop"]:
        openwebui_subparsers.add_parser(command)
    openwebui_logs_parser = openwebui_subparsers.add_parser("logs")
    openwebui_logs_parser.add_argument("--follow", action="store_true")
    install_parser = subparsers.add_parser("install-shell-command")
    install_parser.add_argument("--bin-dir", default=str(Path.home() / ".local" / "bin"))
    return parser.parse_args(argv)


def install_shell_command(root: Path, bin_dir: Path) -> int:
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "uaa"
    source = root / "scripts" / "dev" / "uaa"
    if target.exists() or target.is_symlink():
        if target.is_symlink() and target.resolve() == source:
            print(f"uaa shell command already installed: {target}")
            return 0
        print(f"Refusing to overwrite existing file: {target}")
        return 1
    target.symlink_to(source)
    print(f"Installed user-local symlink: {target} -> {source}")
    print(f"Add this to PATH if needed: export PATH=\"{bin_dir}:$PATH\"")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = repo_root()
    command = args.command or "help"
    try:
        if command == "help":
            parser = argparse.ArgumentParser(prog="uaa", description="Local Ultimate AI Agent developer launcher")
            subparsers = parser.add_subparsers(dest="command")
            for help_command in [
                "doctor",
                "start",
                "ui",
                "status",
                "logs",
                "openwebui",
                "stop",
                "restart",
                "install-shell-command",
            ]:
                subparsers.add_parser(help_command)
            parser.print_help()
            return 0
        if command == "doctor":
            return command_doctor(root)
        if command == "start":
            return command_start(root)
        if command == "ui":
            return command_ui(root)
        if command == "status":
            return command_status(root)
        if command == "logs":
            return command_logs(root, follow=args.follow)
        if command == "openwebui":
            openwebui_command = args.openwebui_command or "status"
            if openwebui_command == "doctor":
                return command_openwebui_doctor(root)
            if openwebui_command == "start":
                return command_openwebui_start(root)
            if openwebui_command == "status":
                return command_openwebui_status(root)
            if openwebui_command == "logs":
                return command_openwebui_logs(root, follow=args.follow)
            if openwebui_command == "stop":
                return command_openwebui_stop(root)
        if command == "stop":
            return command_stop(root)
        if command == "restart":
            stop_code = command_stop(root)
            start_code = command_start(root)
            return stop_code or start_code
        if command == "install-shell-command":
            return install_shell_command(root, Path(args.bin_dir).expanduser())
    except (RuntimeError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
