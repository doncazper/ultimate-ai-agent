#!/usr/bin/env python3
"""Local developer launcher for the Ultimate AI Agent prototype.

This module is localhost-only. It starts the existing FastAPI API boundary and
the existing Control Center Vite dev server; it does not add any agent, action,
or tool authority. When the local package is importable, it also records
redacted launcher lifecycle summaries under `.uaa/`.
"""
from __future__ import annotations


import argparse
import importlib.util
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
from typing import Any, Callable


BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173
OPENWEBUI_HOST = "127.0.0.1"
OPENWEBUI_PORT = 3000
OPENWEBUI_CONTAINER_NAME = "uaa-openwebui-local"
OPENWEBUI_IMAGE_REPOSITORY = "ghcr.io/open-webui/open-webui"
OPENWEBUI_IMAGE_DIGEST = "sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e"
OPENWEBUI_IMAGE = f"{OPENWEBUI_IMAGE_REPOSITORY}@{OPENWEBUI_IMAGE_DIGEST}"
OPENWEBUI_MODEL_ID = "uaa-safe-local"
OPENWEBUI_GATEWAY_FOR_CONTAINER = "http://host.docker.internal:8000/v1"
DESIGNATED_UI_TARGET = "control-center"
UI_TARGETS = ("control-center", "openwebui")
PRIMARY_READY_SECONDARY_BLOCKED = "primary_ready_secondary_blocked"
UAA_OPENWEBUI_TEST_GATEWAY_ENV = "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"
UAA_OPENWEBUI_TEST_GATEWAY_VALUE = "uaa-local-test"
UAA_LLAMA_CPP_GATEWAY_ENV = "UAA_LLAMA_CPP_GATEWAY_ENABLED"
UAA_LLAMA_CPP_GATEWAY_KEY_ENV = "UAA_LLAMA_CPP_GATEWAY_KEY"
UAA_LLAMA_CPP_MODEL_ID_ENV = "UAA_LLAMA_CPP_MODEL_ID"
UAA_LLAMA_CPP_BASE_URL_ENV = "UAA_LLAMA_CPP_BASE_URL"
UAA_LLAMA_CPP_API_KEY_ENV = "UAA_LLAMA_CPP_API_KEY"
UAA_LLAMA_CPP_DEFAULT_MODEL_ID = "uaa-llama-cpp-local"
DOCKER_ENGINE_CHECK_TIMEOUT_SECONDS = 3.0
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
DEVELOPER_TOOL_PATHS = (
    Path("/opt/homebrew/bin"),
    Path("/opt/homebrew/sbin"),
    Path("/usr/local/bin"),
    Path("/Applications/Docker.app/Contents/Resources/bin"),
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
        _developer_tool("npm"),
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
    openwebui_env, secret_env_keys = openwebui_container_env()
    env_args = [
        item
        for key, value in openwebui_env.items()
        for item in ["-e", key if key in secret_env_keys else f"{key}={value}"]
    ]
    return [
        _developer_tool("docker"),
        "run",
        "--rm",
        "--name",
        OPENWEBUI_CONTAINER_NAME,
        "-p",
        f"{OPENWEBUI_HOST}:{OPENWEBUI_PORT}:8080",
        "-v",
        f"{data_dir}:/app/backend/data",
        *env_args,
        OPENWEBUI_IMAGE,
    ]


def openwebui_container_env() -> tuple[dict[str, str], set[str]]:
    gateway_key = UAA_OPENWEBUI_TEST_GATEWAY_VALUE
    model_id = OPENWEBUI_MODEL_ID
    secret_env_keys: set[str] = set()
    if llama_cpp_gateway_requested():
        gateway_key = os.environ.get(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "").strip()
        model_id = os.environ.get(UAA_LLAMA_CPP_MODEL_ID_ENV, UAA_LLAMA_CPP_DEFAULT_MODEL_ID).strip()
        model_id = model_id or UAA_LLAMA_CPP_DEFAULT_MODEL_ID
        secret_env_keys = {"OPENAI_API_KEY", "OPENAI_API_KEYS"}
    return {
        "DEFAULT_MODEL_PARAMS": '{"stream_response":false}',
        "DEFAULT_MODELS": model_id,
        "ENABLE_OLLAMA_API": "False",
        "ENABLE_OPENAI_API": "True",
        "ENABLE_PERSISTENT_CONFIG": "False",
        "OPENAI_API_BASE_URL": OPENWEBUI_GATEWAY_FOR_CONTAINER,
        "OPENAI_API_BASE_URLS": OPENWEBUI_GATEWAY_FOR_CONTAINER,
        "OPENAI_API_KEY": gateway_key,
        "OPENAI_API_KEYS": gateway_key,
        "WEBUI_AUTH": "False",
    }, secret_env_keys


def llama_cpp_gateway_requested() -> bool:
    return os.environ.get(UAA_LLAMA_CPP_GATEWAY_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


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
    sensitive_passthrough_keys: set[str] = set()
    env["PATH"] = _developer_path(env.get("PATH", ""))
    env["PYTHONUNBUFFERED"] = "1"
    if service_name == "backend":
        env["PYTHONPATH"] = str(root / "src")
        if os.environ.get(UAA_OPENWEBUI_TEST_GATEWAY_ENV):
            env[UAA_OPENWEBUI_TEST_GATEWAY_ENV] = os.environ[UAA_OPENWEBUI_TEST_GATEWAY_ENV]
        for key in [
            UAA_LLAMA_CPP_GATEWAY_ENV,
            UAA_LLAMA_CPP_MODEL_ID_ENV,
            UAA_LLAMA_CPP_BASE_URL_ENV,
        ]:
            if os.environ.get(key):
                env[key] = os.environ[key]
        for key in [UAA_LLAMA_CPP_GATEWAY_KEY_ENV, UAA_LLAMA_CPP_API_KEY_ENV]:
            if os.environ.get(key):
                env[key] = os.environ[key]
                sensitive_passthrough_keys.add(key)
    if service_name == "frontend":
        env["VITE_UAA_API_BASE_URL"] = ""
    if service_name == "openwebui" and llama_cpp_gateway_requested():
        openwebui_env, secret_env_keys = openwebui_container_env()
        for key in secret_env_keys:
            if openwebui_env.get(key):
                env[key] = openwebui_env[key]
                sensitive_passthrough_keys.add(key)
    return {
        key: value
        for key, value in env.items()
        if key in sensitive_passthrough_keys or not _is_secret_env_key(key)
    }


def _is_secret_env_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in SECRET_ENV_MARKERS)


def ensure_state_dirs(root: Path) -> None:
    base, pid_dir, log_dir = runtime_paths(root)
    base.mkdir(parents=True, exist_ok=True)
    pid_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)


def record_launcher_event(
    root: Path,
    event_type: str,
    *,
    service: Service | None = None,
    status: str = "recorded",
    lifecycle_state: str = "completed",
    pid: int | None = None,
    duration_ms: float | None = None,
    reason_codes: list[str] | None = None,
    error_code: str | None = None,
    error_summary: str | None = None,
) -> None:
    observability = _observability_helpers(root)
    if observability is None:
        return
    build_safe_ref, record_session_event = observability
    service_name = service.name if service is not None else "launcher"
    metadata: dict[str, Any] = {
        "service_name": service_name,
        "launcher_scope": "uaa_managed_dev_services",
    }
    if service is not None:
        metadata["log_ref"] = f"launcher-log:{service.name}"
    if pid is not None:
        metadata["pid"] = pid
    record_session_event(
        fail_closed=False,
        session_id="launcher-session:local",
        trace_id=build_safe_ref("launcher-trace", service_name),
        span_id=build_safe_ref("launcher-span", service_name, event_type, time.perf_counter_ns()),
        correlation_id=build_safe_ref("launcher-correlation", service_name),
        service="dev_launcher",
        surface="launcher" if event_type.startswith("launcher.") else "dev_service",
        event_type=event_type,
        lifecycle_state=lifecycle_state,
        status=status,
        severity="error" if status in {"failed", "timeout"} else "info",
        duration_ms=duration_ms,
        safe_summary="Launcher lifecycle metadata recorded as a redacted summary.",
        reason_codes=reason_codes or ["LAUNCHER_LIFECYCLE_RECORDED"],
        error_code=error_code,
        error_summary=error_summary,
        evidence_refs=[build_safe_ref("launcher-log", service_name)] if service is not None else [],
        redaction_summary={
            "status": "summary_only",
            "process_streams_stored": False,
            "private_paths_stored": False,
        },
        metadata=metadata,
    )


def _observability_helpers(root: Path) -> tuple[Any, ...] | None:
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        from ultimate_ai_agent.core.observability import build_safe_ref, record_session_event
    except Exception:
        return None
    return build_safe_ref, record_session_event


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


def url_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 2.0,
) -> tuple[int | None, str]:
    try:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(4096).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except (OSError, urllib.error.URLError):
        return None, ""


def service_identity_ready(service: Service) -> bool:
    if service.name == "backend":
        return (
            url_status(f"{BACKEND_URL}/api/manifest") == 200
            and url_status(f"{BACKEND_URL}/version") == 200
        )
    if service.name == "frontend":
        status, body = url_text(FRONTEND_URL)
        return status == 200 and "Ultimate AI Agent Control Center" in body
    if service.name == "openwebui":
        pid = read_pid_file(service.pid_file)
        return pid is not None and metadata_matches_service(service, pid)
    return False


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
    docker_ready, docker_message = docker_engine_status()
    if docker_ready:
        ok.append(docker_message)
    else:
        failures.append(docker_message)

    if is_port_open(OPENWEBUI_HOST, OPENWEBUI_PORT):
        ok.append(f"OpenWebUI port already in use on {OPENWEBUI_URL}")
    else:
        ok.append(f"OpenWebUI port is free: {OPENWEBUI_URL}")

    health_status = url_status(f"{BACKEND_URL}{BACKEND_HEALTH_PATH}")
    gateway_mode, gateway_key, model_id = openwebui_gateway_runtime_config()
    if health_status is None:
        if gateway_mode == "m164":
            failures.append("UAA backend is not reachable; restart it with the UAA_LLAMA_CPP_* gateway environment")
        else:
            failures.append("UAA backend is not reachable; run: UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start")
    elif 200 <= health_status < 500:
        ok.append(f"UAA backend reachable at {BACKEND_URL}")
    else:
        failures.append(f"UAA backend health returned HTTP {health_status}")

    if not gateway_key:
        failures.append(f"{UAA_LLAMA_CPP_GATEWAY_KEY_ENV} must be set when using the llama.cpp gateway")
        return ok, failures

    gateway_status = url_status(
        f"{BACKEND_URL}/v1/models",
        headers={"Authorization": f"Bearer {gateway_key}"},
    )
    if gateway_status == 200:
        ok.append(f"UAA {gateway_mode} gateway is enabled for model {model_id}")
    elif gateway_status == 403:
        if gateway_mode == "m164":
            failures.append("UAA llama.cpp gateway is disabled; restart backend with UAA_LLAMA_CPP_GATEWAY_ENABLED=1")
        else:
            failures.append("UAA local OpenWebUI test gateway is disabled; restart backend with UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1")
    elif gateway_status == 401:
        failures.append(f"UAA {gateway_mode} gateway rejected the configured local bearer value")
    elif gateway_status is None:
        failures.append(f"UAA {gateway_mode} gateway is not reachable")
    else:
        failures.append(f"UAA {gateway_mode} gateway returned HTTP {gateway_status}")

    data_dir = root / STATE_DIR / "openwebui-data"
    ok.append(f"OpenWebUI data directory: {data_dir}")
    return ok, failures


def openwebui_gateway_runtime_config() -> tuple[str, str, str]:
    if llama_cpp_gateway_requested():
        gateway_key = os.environ.get(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "").strip()
        model_id = os.environ.get(UAA_LLAMA_CPP_MODEL_ID_ENV, UAA_LLAMA_CPP_DEFAULT_MODEL_ID).strip()
        return "m164-llama-cpp", gateway_key, model_id or UAA_LLAMA_CPP_DEFAULT_MODEL_ID
    return "m151-openwebui-test", UAA_OPENWEBUI_TEST_GATEWAY_VALUE, OPENWEBUI_MODEL_ID


def _command_exists(command: str) -> bool:
    return _resolve_developer_tool(command) is not None


def _developer_tool(command: str) -> str:
    resolved = _resolve_developer_tool(command)
    if resolved is None:
        return command
    return str(resolved)


def _developer_path(path_value: str) -> str:
    entries = [str(path) for path in DEVELOPER_TOOL_PATHS if path.exists()]
    entries.extend(part for part in path_value.split(os.pathsep) if part)
    unique_entries = list(dict.fromkeys(entries))
    return os.pathsep.join(unique_entries)


def _resolve_developer_tool(command: str) -> Path | None:
    for directory in DEVELOPER_TOOL_PATHS:
        candidate = directory / command
        if _is_executable_file(candidate):
            return candidate
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory, command)
        if directory and _is_executable_file(candidate):
            return candidate
    return None


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def docker_engine_status(timeout_seconds: float = DOCKER_ENGINE_CHECK_TIMEOUT_SECONDS) -> tuple[bool, str]:
    docker = _resolve_developer_tool("docker")
    if docker is None:
        return False, "Docker is not available on PATH"
    try:
        result = subprocess.run(
            [str(docker), "info", "--format", "{{.ServerVersion}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            False,
            f"Docker CLI found, but the Docker engine did not answer within {timeout_seconds:g}s; "
            "open Docker Desktop and finish first-run setup",
        )
    except OSError as exc:
        return False, f"Docker CLI found, but could not be started: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if detail:
            return False, f"Docker CLI found, but the Docker engine is not ready: {detail.splitlines()[-1]}"
        return False, "Docker CLI found, but the Docker engine is not ready; open Docker Desktop and finish first-run setup"
    version = result.stdout.strip() or "unknown"
    return True, f"Docker engine ready: {version}"


def docker_image_present(image: str = OPENWEBUI_IMAGE, timeout_seconds: float = DOCKER_ENGINE_CHECK_TIMEOUT_SECONDS) -> tuple[bool, str]:
    docker = _resolve_developer_tool("docker")
    if docker is None:
        return False, "Docker is not available on PATH"
    try:
        result = subprocess.run(
            [str(docker), "image", "inspect", "--format", "{{.Id}}", image],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"Docker image inspect did not answer within {timeout_seconds:g}s"
    except OSError as exc:
        return False, f"Docker image inspect could not be started: {exc}"
    if result.returncode == 0:
        return True, f"OpenWebUI image present locally: {image}"
    return False, f"OpenWebUI image is not present locally: {image}; no image was pulled"


def start_service(root: Path, service: Service) -> str:
    ensure_state_dirs(root)
    start_clock = time.perf_counter()
    record_launcher_event(
        root,
        "service.start_requested",
        service=service,
        status="requested",
        lifecycle_state="requested",
        reason_codes=["SERVICE_START_REQUESTED"],
    )
    state = cleanup_stale_pid(service.pid_file)
    if state == "running":
        return f"{service.name}: already running (pid {read_pid_file(service.pid_file)})"

    service_ports = {
        "backend": (BACKEND_HOST, BACKEND_PORT),
        "frontend": (FRONTEND_HOST, FRONTEND_PORT),
        "openwebui": (OPENWEBUI_HOST, OPENWEBUI_PORT),
    }
    host, port = service_ports[service.name]
    if is_port_open(host, port):
        if service_identity_ready(service):
            return f"{service.name}: {service.url} is already UAA-ready; not starting a duplicate"
        return (
            f"{service.name}: blocked; {service.url} is occupied by an unverified "
            "local process; not starting a duplicate"
        )

    if service.name == "backend" and not Path(service.command[0]).exists():
        record_launcher_event(
            root,
            "service.process_exited",
            service=service,
            status="failed",
            lifecycle_state="failed",
            reason_codes=["SERVICE_PREREQUISITE_MISSING"],
            error_code="SERVICE_PREREQUISITE_MISSING",
            error_summary="Service start failed safely; prerequisite details are redacted.",
        )
        raise RuntimeError("missing .venv/bin/python; run uaa doctor")
    if service.name == "frontend" and not service.cwd.joinpath("node_modules").exists():
        record_launcher_event(
            root,
            "service.process_exited",
            service=service,
            status="failed",
            lifecycle_state="failed",
            reason_codes=["SERVICE_PREREQUISITE_MISSING"],
            error_code="SERVICE_PREREQUISITE_MISSING",
            error_summary="Service start failed safely; prerequisite details are redacted.",
        )
        raise RuntimeError("missing apps/control-center/node_modules; run uaa doctor")
    if service.name == "openwebui":
        docker_ready, docker_message = docker_engine_status()
        if not docker_ready:
            record_launcher_event(
                root,
                "service.process_exited",
                service=service,
                status="failed",
                lifecycle_state="failed",
                reason_codes=["SERVICE_PREREQUISITE_MISSING"],
                error_code="SERVICE_PREREQUISITE_MISSING",
                error_summary="Service start failed safely; prerequisite details are redacted.",
            )
            raise RuntimeError(f"{docker_message}; run uaa openwebui doctor")
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
    record_launcher_event(
        root,
        "service.process_spawned",
        service=service,
        status="started",
        lifecycle_state="started",
        pid=process.pid,
        duration_ms=round((time.perf_counter() - start_clock) * 1000, 3),
        reason_codes=["SERVICE_PROCESS_SPAWNED"],
    )
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
        record_launcher_event(
            root,
            "service.health_timeout",
            service=service,
            status="timeout",
            lifecycle_state="timeout",
            pid=process.pid,
            duration_ms=round((time.perf_counter() - start_clock) * 1000, 3),
            reason_codes=["SERVICE_HEALTH_TIMEOUT"],
            error_code="SERVICE_HEALTH_TIMEOUT",
            error_summary="Service health check timed out safely.",
        )
        return f"{service.name}: started pid {process.pid}, but health check is not ready yet; see {service.log_file}"
    record_launcher_event(
        root,
        "service.health_ready",
        service=service,
        status="ready",
        lifecycle_state="ready",
        pid=process.pid,
        duration_ms=round((time.perf_counter() - start_clock) * 1000, 3),
        reason_codes=["SERVICE_HEALTH_READY"],
    )
    return f"{service.name}: running at {service.url} (pid {process.pid}); log {service.log_file}"


def stop_service(service: Service, root: Path | None = None) -> str:
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
    if root is not None:
        record_launcher_event(
            root,
            "service.process_exited",
            service=service,
            status="completed",
            lifecycle_state="exited",
            pid=pid,
            reason_codes=["SERVICE_PROCESS_EXITED"],
        )
    return f"{service.name}: stopped launcher pid {pid}"


def status_for_service(service: Service) -> str:
    log_ref = f"launcher-log:{service.name}"
    state = cleanup_stale_pid(service.pid_file)
    if state == "running":
        return (
            f"{service.name}: running pid={read_pid_file(service.pid_file)} "
            f"url={service.url} log_ref={log_ref} log={service.log_file}"
        )
    if state == "removed_stale":
        return (
            f"{service.name}: not running (removed stale pid file) "
            f"log_ref={log_ref} log={service.log_file}"
        )
    return f"{service.name}: not running url={service.url} log_ref={log_ref} log={service.log_file}"


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

./scripts/dev/uaa trial-boot
BOOT_STATUS=$?
./scripts/dev/uaa status
./scripts/dev/uaa openwebui status

echo
echo "Logs are under .uaa/dev/logs/"
if [ "$BOOT_STATUS" -ne 0 ]; then
  echo "Trial boot reached a blocked or degraded state. See the status lines above."
fi
echo "Press any key to close..."
read -k 1
exit "$BOOT_STATUS"
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
    record_launcher_event(
        root,
        "launcher.start_requested",
        status="requested",
        lifecycle_state="requested",
        reason_codes=["LAUNCHER_START_REQUESTED"],
    )
    blocked = False
    for name in ["backend", "frontend"]:
        result = start_service(root, service_config(root, name))
        print(result)
        blocked = blocked or ": blocked;" in result
    print(f"\nControl Center: {FRONTEND_URL}")
    print(f"Logs: {root / STATE_DIR / 'logs'}")
    return 1 if blocked else 0


def command_ui(root: Path) -> int:
    frontend = service_config(root, "frontend")
    if cleanup_stale_pid(frontend.pid_file) != "running":
        print("Control Center is not running. Run: uaa start")
        return 1
    webbrowser.open(frontend.url)
    print(f"Opened {frontend.url}")
    return 0


def command_launch_ui(root: Path, target: str = DESIGNATED_UI_TARGET) -> int:
    if target == "control-center":
        start_code = command_start(root)
        if start_code:
            return start_code
        webbrowser.open(FRONTEND_URL)
        print(f"Opened designated UI: {FRONTEND_URL}")
        return 0
    if target == "openwebui":
        return command_launch_openwebui(root)
    raise ValueError(f"Unknown UI target: {target}")


def command_trial_boot(root: Path) -> int:
    print("Ultimate AI Agent private operator trial boot")
    print("Control Center is the first-party product surface.")
    print("OpenWebUI is the secondary local shell and may remain blocked until prerequisites are ready.")
    print()
    control_center_code = command_launch_ui(root, target="control-center")
    if control_center_code:
        return control_center_code
    openwebui_code = command_launch_ui(root, target="openwebui")
    print()
    print("Readiness summary:")
    command_status(root)
    command_openwebui_status(root)
    if openwebui_code:
        print()
        print("Secondary OpenWebUI shell is blocked or degraded; Control Center remains the primary surface.")
        print(f"Boot state: {PRIMARY_READY_SECONDARY_BLOCKED}")
        print("No packages were installed and no images were pulled by uaa trial-boot.")
        return 0
    return 0


def command_launch_openwebui(root: Path) -> int:
    if not llama_cpp_gateway_requested() and not os.environ.get(UAA_OPENWEBUI_TEST_GATEWAY_ENV):
        os.environ[UAA_OPENWEBUI_TEST_GATEWAY_ENV] = "1"
        print(f"Using local smoke gateway for this launch: {UAA_OPENWEBUI_TEST_GATEWAY_ENV}=1")

    gateway_mode, gateway_key, model_id = openwebui_gateway_runtime_config()
    if not gateway_key:
        print(f"{UAA_LLAMA_CPP_GATEWAY_KEY_ENV} must be set before launching OpenWebUI in llama.cpp gateway mode")
        return 1

    docker_ready, docker_message = docker_engine_status()
    if not docker_ready:
        print(f"FAIL: {docker_message}")
        return 1
    image_ready, image_message = docker_image_present()
    if not image_ready:
        print(f"FAIL: {image_message}")
        print("OpenWebUI was not launched. Run uaa setup install --target openwebui to approve the scoped image pull.")
        return 1

    backend_status = url_status(f"{BACKEND_URL}{BACKEND_HEALTH_PATH}")
    if backend_status != 200:
        print(start_service(root, service_config(root, "backend")))
    else:
        print(f"backend: already reachable at {BACKEND_URL}")

    gateway_status = url_status(
        f"{BACKEND_URL}/v1/models",
        headers={"Authorization": f"Bearer {gateway_key}"},
    )
    if gateway_status != 200:
        print(f"FAIL: UAA {gateway_mode} gateway is not ready for model {model_id} (status {gateway_status})")
        print("Restart the backend with the matching local gateway environment, then retry uaa launch-ui.")
        return 1

    openwebui_result = start_service(root, service_config(root, "openwebui"))
    print(openwebui_result)
    if ": blocked;" in openwebui_result:
        return 1
    webbrowser.open(OPENWEBUI_URL)
    print(f"\nOpened designated UI: {OPENWEBUI_URL}")
    print(f"Gateway mode: {gateway_mode}")
    print(f"Model: {model_id}")
    print("No packages were installed and no images were pulled by uaa launch-ui.")
    return 0


def command_status(root: Path) -> int:
    version = _read_version(root)
    print(f"Ultimate AI Agent version: {version}")
    for name in ["backend", "frontend", "openwebui"]:
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
    gateway_mode, gateway_key, model_id = openwebui_gateway_runtime_config()
    if not gateway_key:
        print(f"{UAA_LLAMA_CPP_GATEWAY_KEY_ENV} must be set before starting OpenWebUI in llama.cpp gateway mode")
        return 1
    result = start_service(root, service)
    print(result)
    if ": blocked;" in result:
        return 1
    print(f"\nOpenWebUI: {OPENWEBUI_URL}")
    print(f"UAA gateway for OpenWebUI: {OPENWEBUI_GATEWAY_FOR_CONTAINER}")
    print(f"Gateway mode: {gateway_mode}")
    print(f"Model: {model_id}")
    if gateway_mode == "m164-llama-cpp":
        print(f"Local bearer source: {UAA_LLAMA_CPP_GATEWAY_KEY_ENV}")
    else:
        print(f"Local bearer value: {UAA_OPENWEBUI_TEST_GATEWAY_VALUE}")
    return 0


def command_openwebui_status(root: Path) -> int:
    print(status_for_service(service_config(root, "openwebui")))
    gateway_mode, gateway_key, model_id = openwebui_gateway_runtime_config()
    if not gateway_key:
        print(f"uaa-gateway: not ready ({UAA_LLAMA_CPP_GATEWAY_KEY_ENV} is unset)")
        return 1
    gateway_status = url_status(
        f"{BACKEND_URL}/v1/models",
        headers={"Authorization": f"Bearer {gateway_key}"},
    )
    print(
        f"uaa-gateway: {'reachable' if gateway_status == 200 else f'not ready ({gateway_status})'} "
        f"mode={gateway_mode} model={model_id}"
    )
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
    print(stop_service(service, root=root))
    docker_ready, _ = docker_engine_status(timeout_seconds=1.5)
    if docker_ready:
        try:
            subprocess.run(
                [_developer_tool("docker"), "rm", "-f", OPENWEBUI_CONTAINER_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5.0,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
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
    record_launcher_event(
        root,
        "launcher.stop_requested",
        status="requested",
        lifecycle_state="requested",
        reason_codes=["LAUNCHER_STOP_REQUESTED"],
    )
    command_openwebui_stop(root)
    for name in ["frontend", "backend"]:
        print(stop_service(service_config(root, name), root=root))
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
    for command in ["doctor", "start", "ui", "trial-boot", "status", "stop", "restart", "help"]:
        subparsers.add_parser(command)
    launch_ui_parser = subparsers.add_parser("launch-ui")
    launch_ui_parser.add_argument("--target", choices=UI_TARGETS, default=DESIGNATED_UI_TARGET)
    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("--follow", action="store_true")
    uaa_local_model = _load_local_model_module()
    uaa_local_model.add_local_model_parser(subparsers)
    openwebui_parser = subparsers.add_parser("openwebui")
    openwebui_subparsers = openwebui_parser.add_subparsers(dest="openwebui_command")
    for command in ["doctor", "start", "status", "stop"]:
        openwebui_subparsers.add_parser(command)
    openwebui_logs_parser = openwebui_subparsers.add_parser("logs")
    openwebui_logs_parser.add_argument("--follow", action="store_true")
    uaa_setup = _load_setup_module()
    uaa_setup.add_setup_parser(subparsers)
    runtime_parser = subparsers.add_parser("runtime")
    runtime_parser.add_argument("runtime_args", nargs=argparse.REMAINDER)
    actions_parser = subparsers.add_parser("actions")
    actions_parser.add_argument("action_args", nargs=argparse.REMAINDER)
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
    raw_argv = sys.argv[1:] if argv is None else argv
    if raw_argv and raw_argv[0] == "runtime":
        uaa_runtime = _load_runtime_module()
        return uaa_runtime.main(raw_argv[1:] or ["status"])
    if raw_argv and raw_argv[0] == "actions":
        uaa_runtime = _load_runtime_module()
        action_args = raw_argv[1:] or ["--help"]
        if action_args[:1] == ["--state-dir"] and len(action_args) >= 3:
            return uaa_runtime.main(
                ["--state-dir", action_args[1], "actions", *action_args[2:]]
            )
        return uaa_runtime.main(["actions", *action_args])
    args = parse_args(raw_argv)
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
                "launch-ui",
                "trial-boot",
                "local-model",
                "openwebui",
                "setup",
                "runtime",
                "actions",
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
        if command == "launch-ui":
            return command_launch_ui(root, target=args.target)
        if command == "trial-boot":
            return command_trial_boot(root)
        if command == "status":
            return command_status(root)
        if command == "logs":
            return command_logs(root, follow=args.follow)
        if command == "local-model":
            uaa_local_model = _load_local_model_module()
            return uaa_local_model.command_local_model(root, args)
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
        if command == "setup":
            uaa_setup = _load_setup_module()
            return uaa_setup.command_setup(root, args)
        if command == "runtime":
            uaa_runtime = _load_runtime_module()
            runtime_args = args.runtime_args or ["status"]
            return uaa_runtime.main(runtime_args)
        if command == "actions":
            uaa_runtime = _load_runtime_module()
            action_args = args.action_args or ["--help"]
            return uaa_runtime.main(["actions", *action_args])
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


def _load_setup_module() -> Any:
    module_name = "uaa_setup"
    if module_name in sys.modules:
        return sys.modules[module_name]
    setup_path = Path(__file__).resolve().with_name("uaa_setup.py")
    spec = importlib.util.spec_from_file_location(module_name, setup_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load local setup assistant")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_local_model_module() -> Any:
    module_name = "uaa_local_model"
    if module_name in sys.modules:
        return sys.modules[module_name]
    local_model_path = Path(__file__).resolve().with_name("uaa_local_model.py")
    spec = importlib.util.spec_from_file_location(module_name, local_model_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load local model inventory command")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_runtime_module() -> Any:
    module_name = "uaa_runtime"
    if module_name in sys.modules:
        return sys.modules[module_name]
    runtime_path = Path(__file__).resolve().with_name("uaa_runtime.py")
    spec = importlib.util.spec_from_file_location(module_name, runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load governed runtime CLI")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
