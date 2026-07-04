from typing import Any
import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_PATH = ROOT / "scripts" / "dev" / "uaa_launcher.py"
WRAPPER_PATH = ROOT / "scripts" / "dev" / "uaa"
GITIGNORE_PATH = ROOT / ".gitignore"


def load_launcher() -> Any:
    if not LAUNCHER_PATH.exists():
        pytest.fail("scripts/dev/uaa_launcher.py is missing")
    spec = importlib.util.spec_from_file_location("uaa_launcher", LAUNCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_launcher_rejects_non_loopback_hosts() -> None:
    launcher = load_launcher()

    for host in ["127.0.0.1", "localhost", "::1"]:
        assert launcher.validate_local_host(host) == host

    for host in ["0.0.0.0", "192.168.1.20", "control-center.local", "example.com"]:
        with pytest.raises(ValueError):
            launcher.validate_local_host(host)


def test_launcher_builds_localhost_only_command_lists() -> None:
    launcher = load_launcher()

    backend = launcher.build_backend_command(ROOT)
    frontend = launcher.build_frontend_command(ROOT)
    openwebui = launcher.build_openwebui_command(ROOT)

    assert backend[:3] == [str(ROOT / ".venv" / "bin" / "python"), "-m", "uvicorn"]
    assert "ultimate_ai_agent.api.app:app" in backend
    assert "--host" in backend
    assert backend[backend.index("--host") + 1] == "127.0.0.1"
    assert "--port" in backend
    assert backend[backend.index("--port") + 1] == "8000"

    assert Path(frontend[0]).name == "npm"
    assert frontend[1] == "run"
    assert "dev" in frontend
    assert "--host" in frontend
    assert frontend[frontend.index("--host") + 1] == "127.0.0.1"
    assert "--port" in frontend
    assert frontend[frontend.index("--port") + 1] == "5173"

    assert Path(openwebui[0]).name == "docker"
    assert openwebui[1] == "run"
    assert "-p" in openwebui
    assert openwebui[openwebui.index("-p") + 1] == "127.0.0.1:3000:8080"
    assert launcher.OPENWEBUI_IMAGE in openwebui
    assert "@sha256:" in launcher.OPENWEBUI_IMAGE
    assert ":main" not in launcher.OPENWEBUI_IMAGE
    openwebui_env = _docker_env(openwebui)
    assert openwebui_env["OPENAI_API_BASE_URL"] == "http://host.docker.internal:8000/v1"
    assert openwebui_env["OPENAI_API_BASE_URLS"] == "http://host.docker.internal:8000/v1"
    assert openwebui_env["OPENAI_API_KEY"] == "uaa-local-test"
    assert openwebui_env["OPENAI_API_KEYS"] == "uaa-local-test"
    assert openwebui_env["DEFAULT_MODELS"] == "uaa-safe-local"
    assert openwebui_env["DEFAULT_MODEL_PARAMS"] == '{"stream_response":false}'
    assert openwebui_env["ENABLE_OLLAMA_API"] == "False"
    assert openwebui_env["ENABLE_OPENAI_API"] == "True"
    assert openwebui_env["ENABLE_PERSISTENT_CONFIG"] == "False"


def _docker_env(command: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for index, value in enumerate(command):
        if value == "-e":
            raw_value = command[index + 1]
            if "=" in raw_value:
                key, env_value = raw_value.split("=", 1)
                values[key] = env_value
            else:
                values[raw_value] = ""
    return values


def test_launcher_builds_m164_openwebui_command_without_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "local-secret-should-not-be-in-command")
    monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", "uaa-llama-cpp-local")

    openwebui = launcher.build_openwebui_command(ROOT)
    openwebui_env = _docker_env(openwebui)

    assert openwebui_env["OPENAI_API_BASE_URL"] == "http://host.docker.internal:8000/v1"
    assert openwebui_env["OPENAI_API_KEY"] == ""
    assert openwebui_env["OPENAI_API_KEYS"] == ""
    assert openwebui_env["DEFAULT_MODELS"] == "uaa-llama-cpp-local"
    assert "local-secret-should-not-be-in-command" not in " ".join(openwebui)

    env = launcher.safe_env(ROOT, "openwebui")

    assert env["OPENAI_API_KEY"] == "local-secret-should-not-be-in-command"
    assert env["OPENAI_API_KEYS"] == "local-secret-should-not-be-in-command"


def test_launcher_can_discover_macos_docker_desktop_cli_path() -> None:
    launcher = load_launcher()

    assert Path("/Applications/Docker.app/Contents/Resources/bin") in launcher.DEVELOPER_TOOL_PATHS


def test_shell_wrapper_exposes_macos_docker_desktop_cli_path() -> None:
    content = WRAPPER_PATH.read_text(encoding="utf-8")

    assert "/Applications/Docker.app/Contents/Resources/bin" in content


def test_launcher_resolves_only_executable_developer_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    docker = tool_dir / "docker"
    docker.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr(launcher, "DEVELOPER_TOOL_PATHS", (tool_dir,))
    monkeypatch.setenv("PATH", "")

    assert launcher._resolve_developer_tool("docker") is None

    docker.chmod(0o755)

    assert launcher._resolve_developer_tool("docker") == docker


def test_docker_engine_status_reports_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()

    def fake_run(command: str, **kwargs: Any) -> Any:
        assert command[-3:] == ["info", "--format", "{{.ServerVersion}}"]
        assert kwargs["timeout"] == launcher.DOCKER_ENGINE_CHECK_TIMEOUT_SECONDS
        return subprocess.CompletedProcess(command, 0, stdout="27.0.0\n", stderr="")

    monkeypatch.setattr(launcher, "_resolve_developer_tool", lambda command: Path("/tmp/docker"))
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    ready, message = launcher.docker_engine_status()

    assert ready
    assert message == "Docker engine ready: 27.0.0"


def test_docker_engine_status_reports_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()

    def fake_run(command: str, **kwargs: Any) -> None:
        raise launcher.subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(launcher, "_resolve_developer_tool", lambda command: Path("/tmp/docker"))
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    ready, message = launcher.docker_engine_status(timeout_seconds=0.5)

    assert not ready
    assert "did not answer within 0.5s" in message
    assert "finish first-run setup" in message


def test_docker_engine_status_reports_engine_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()

    def fake_run(command: str, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="Cannot connect to the Docker daemon\n")

    monkeypatch.setattr(launcher, "_resolve_developer_tool", lambda command: Path("/tmp/docker"))
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    ready, message = launcher.docker_engine_status()

    assert not ready
    assert "engine is not ready" in message
    assert "Cannot connect to the Docker daemon" in message


def test_docker_image_present_uses_inspect_without_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    calls = []

    def fake_run(command: str, **kwargs: Any) -> Any:
        calls.append(command)
        assert command[:4] == ["/tmp/docker", "image", "inspect", "--format"]
        assert "pull" not in command
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="No such image\n")

    monkeypatch.setattr(launcher, "_resolve_developer_tool", lambda command: Path("/tmp/docker"))
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    ready, message = launcher.docker_image_present()

    assert not ready
    assert "not present locally" in message
    assert "no image was pulled" in message
    assert calls == [["/tmp/docker", "image", "inspect", "--format", "{{.Id}}", launcher.OPENWEBUI_IMAGE]]


def test_stale_pid_cleanup_removes_only_stale_pid_file(tmp_path: Path) -> None:
    launcher = load_launcher()
    pid_path = tmp_path / "backend.pid"
    pid_path.write_text("999999\n", encoding="utf-8")

    result = launcher.cleanup_stale_pid(pid_path, is_running=lambda pid: False)

    assert result == "removed_stale"
    assert not pid_path.exists()


def test_running_pid_cleanup_keeps_pid_file(tmp_path: Path) -> None:
    launcher = load_launcher()
    pid_path = tmp_path / "frontend.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    result = launcher.cleanup_stale_pid(pid_path, is_running=lambda pid: pid == 12345)

    assert result == "running"
    assert pid_path.read_text(encoding="utf-8") == "12345\n"


def test_macos_launcher_content_is_relative_and_safe() -> None:
    launcher = load_launcher()

    content = launcher.render_macos_launcher()

    assert "./scripts/dev/uaa trial-boot" in content
    assert "./scripts/dev/uaa status" in content
    assert "./scripts/dev/uaa openwebui status" in content
    assert "/Users/" not in content
    assert "sudo" not in content
    assert "launchctl" not in content
    assert "LaunchAgent" not in content
    assert "/usr/local/bin" not in content


def test_launcher_openwebui_service_config_is_localhost_only() -> None:
    launcher = load_launcher()

    service = launcher.service_config(ROOT, "openwebui")

    assert service.url == "http://127.0.0.1:3000"
    assert service.health_url == "http://127.0.0.1:3000"
    assert service.pid_file.name == "openwebui.pid"
    assert service.log_file.name == "openwebui.log"


def test_launcher_registers_local_model_subcommands() -> None:
    launcher = load_launcher()

    status_args = launcher.parse_args(["local-model", "status", "--root", "/safe-root", "--json"])
    list_args = launcher.parse_args(["local-model", "list", "--root", "/safe-root"])
    inspect_args = launcher.parse_args(["local-model", "inspect", "local-model:gguf:abc123"])

    assert status_args.command == "local-model"
    assert status_args.local_model_command == "status"
    assert status_args.root == ["/safe-root"]
    assert status_args.json is True
    assert list_args.local_model_command == "list"
    assert inspect_args.local_model_command == "inspect"
    assert inspect_args.model_ref == "local-model:gguf:abc123"


def test_launcher_local_model_status_uses_safe_inventory_refs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = load_launcher()
    model_root = tmp_path / "models"
    model_root.mkdir()
    (model_root / "private-model-name.gguf").write_bytes(b"fixture")

    result = launcher.main(["local-model", "status", "--root", str(model_root), "--json"])

    assert result == 0
    output = capsys.readouterr().out
    data = json.loads(output)
    assert data["schema_version"] == "uaa_local_model_inventory.v1"
    assert data["models"][0]["model_ref"].startswith("local-model:gguf:")
    assert str(tmp_path) not in output
    assert "private-model-name.gguf" not in output


def test_launcher_local_model_inspect_reports_missing_ref_without_crashing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = load_launcher()

    result = launcher.main(
        [
            "local-model",
            "inspect",
            "local-model:gguf:missing",
            "--root",
            str(tmp_path / "missing"),
            "--json",
        ]
    )

    assert result == 1
    output = capsys.readouterr().out
    data = json.loads(output)
    assert data["status"] == "blocked"
    assert data["reason_code"] == "model_ref_not_found"


def test_launch_ui_parser_defaults_to_control_center() -> None:
    launcher = load_launcher()

    args = launcher.parse_args(["launch-ui"])

    assert args.command == "launch-ui"
    assert args.target == "control-center"


def test_trial_boot_parser_is_registered() -> None:
    launcher = load_launcher()

    args = launcher.parse_args(["trial-boot"])

    assert args.command == "trial-boot"


def test_trial_boot_opens_control_center_before_secondary_openwebui(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = load_launcher()
    launched: list[str] = []

    def fake_launch_ui(root: Path, target: str = launcher.DESIGNATED_UI_TARGET) -> int:
        launched.append(target)
        return 0

    monkeypatch.setattr(launcher, "command_launch_ui", fake_launch_ui)
    monkeypatch.setattr(launcher, "command_status", lambda root: 0)
    monkeypatch.setattr(launcher, "command_openwebui_status", lambda root: 0)

    code = launcher.command_trial_boot(ROOT)
    output = capsys.readouterr().out

    assert code == 0
    assert launched == ["control-center", "openwebui"]
    assert "Control Center is the first-party product surface" in output
    assert "secondary local shell" in output


def test_trial_boot_reports_blocked_secondary_without_installing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = load_launcher()

    def fake_launch_ui(root: Path, target: str = launcher.DESIGNATED_UI_TARGET) -> int:
        return 1 if target == "openwebui" else 0

    monkeypatch.setattr(launcher, "command_launch_ui", fake_launch_ui)
    monkeypatch.setattr(launcher, "command_status", lambda root: 0)
    monkeypatch.setattr(launcher, "command_openwebui_status", lambda root: 0)

    code = launcher.command_trial_boot(ROOT)
    output = capsys.readouterr().out

    assert code == 0
    assert "Secondary OpenWebUI shell is blocked or degraded" in output
    assert "primary_ready_secondary_blocked" in output
    assert "No packages were installed and no images were pulled" in output


def test_service_identity_requires_uaa_backend_manifest_and_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = load_launcher()
    service = launcher.service_config(ROOT, "backend")
    statuses = {
        f"{launcher.BACKEND_URL}/api/manifest": 200,
        f"{launcher.BACKEND_URL}/version": 200,
    }

    monkeypatch.setattr(launcher, "url_status", lambda url, **kwargs: statuses.get(url))

    assert launcher.service_identity_ready(service) is True
    statuses[f"{launcher.BACKEND_URL}/api/manifest"] = 404
    assert launcher.service_identity_ready(service) is False


def test_service_identity_requires_control_center_html(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    service = launcher.service_config(ROOT, "frontend")

    monkeypatch.setattr(
        launcher,
        "url_text",
        lambda url, **kwargs: (200, "<title>Ultimate AI Agent Control Center</title>"),
    )
    assert launcher.service_identity_ready(service) is True

    monkeypatch.setattr(launcher, "url_text", lambda url, **kwargs: (200, "<title>Other</title>"))
    assert launcher.service_identity_ready(service) is False


def test_start_service_blocks_unverified_port_occupant(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    service = launcher.service_config(ROOT, "backend")

    monkeypatch.setattr(launcher, "cleanup_stale_pid", lambda pid_path: "missing")
    monkeypatch.setattr(launcher, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(launcher, "service_identity_ready", lambda service: False)

    result = launcher.start_service(ROOT, service)

    assert "backend: blocked" in result
    assert "occupied by an unverified local process" in result


def test_start_service_reuses_verified_uaa_port_occupant(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    service = launcher.service_config(ROOT, "backend")

    monkeypatch.setattr(launcher, "cleanup_stale_pid", lambda pid_path: "missing")
    monkeypatch.setattr(launcher, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(launcher, "service_identity_ready", lambda service: True)

    result = launcher.start_service(ROOT, service)

    assert "already UAA-ready" in result


def test_launch_ui_openwebui_refuses_missing_image(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    launcher = load_launcher()
    started = []
    opened = []
    monkeypatch.setattr(launcher, "docker_engine_status", lambda: (True, "Docker ready"))
    monkeypatch.setattr(launcher, "docker_image_present", lambda: (False, "OpenWebUI image is not present locally; no image was pulled"))
    monkeypatch.setattr(launcher, "start_service", lambda root, service: started.append(service.name) or f"{service.name}: started")
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))

    code = launcher.command_launch_ui(ROOT, target="openwebui")
    captured = capsys.readouterr()

    assert code == 1
    assert started == []
    assert opened == []
    assert "setup install --target openwebui" in captured.out


def test_launch_ui_openwebui_starts_backend_and_openwebui(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    launcher = load_launcher()
    started = []
    opened = []
    statuses = {
        f"{launcher.BACKEND_URL}{launcher.BACKEND_HEALTH_PATH}": None,
        f"{launcher.BACKEND_URL}/v1/models": 200,
    }
    monkeypatch.delenv(launcher.UAA_OPENWEBUI_TEST_GATEWAY_ENV, raising=False)
    monkeypatch.setattr(launcher, "docker_engine_status", lambda: (True, "Docker ready"))
    monkeypatch.setattr(launcher, "docker_image_present", lambda: (True, "OpenWebUI image present locally"))
    monkeypatch.setattr(launcher, "url_status", lambda url, **kwargs: statuses.get(url))
    monkeypatch.setattr(launcher, "start_service", lambda root, service: started.append(service.name) or f"{service.name}: started")
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))

    code = launcher.command_launch_ui(ROOT, target="openwebui")
    captured = capsys.readouterr()

    assert code == 0
    assert started == ["backend", "openwebui"]
    assert opened == [launcher.OPENWEBUI_URL]
    assert f"{launcher.UAA_OPENWEBUI_TEST_GATEWAY_ENV}=1" in captured.out
    assert "No packages were installed and no images were pulled" in captured.out


def test_launcher_backend_env_allows_only_openwebui_gateway_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_KEY", "should-not-pass-through")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "local-gateway-secret")
    monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", "uaa-llama-cpp-local")
    monkeypatch.setenv("UAA_LLAMA_CPP_BASE_URL", "http://127.0.0.1:8080")
    monkeypatch.setenv("UAA_LLAMA_CPP_API_KEY", "local-backend-secret")

    env = launcher.safe_env(ROOT, "backend")

    assert env["UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"] == "1"
    assert "UAA_OPENWEBUI_TEST_GATEWAY_KEY" not in env
    assert env["UAA_LLAMA_CPP_GATEWAY_ENABLED"] == "1"
    assert env["UAA_LLAMA_CPP_GATEWAY_KEY"] == "local-gateway-secret"
    assert env["UAA_LLAMA_CPP_MODEL_ID"] == "uaa-llama-cpp-local"
    assert env["UAA_LLAMA_CPP_BASE_URL"] == "http://127.0.0.1:8080"
    assert env["UAA_LLAMA_CPP_API_KEY"] == "local-backend-secret"


def test_shell_wrapper_exists_and_is_executable() -> None:
    assert WRAPPER_PATH.exists()
    mode = WRAPPER_PATH.stat().st_mode
    assert mode & stat.S_IXUSR


def test_status_includes_openwebui_and_safe_log_refs(capsys: pytest.CaptureFixture[str]) -> None:
    launcher = load_launcher()

    code = launcher.command_status(ROOT)
    output = capsys.readouterr().out

    assert code == 0
    assert "backend:" in output
    assert "frontend:" in output
    assert "openwebui:" in output
    assert "log_ref=launcher-log:backend" in output
    assert "log_ref=launcher-log:frontend" in output
    assert "log_ref=launcher-log:openwebui" in output


def test_stop_includes_openwebui_before_frontend_and_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    stopped: list[str] = []

    monkeypatch.setattr(launcher, "record_launcher_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(launcher, "command_openwebui_stop", lambda root: stopped.append("openwebui") or 0)
    monkeypatch.setattr(
        launcher,
        "stop_service",
        lambda service, root=None: stopped.append(service.name) or f"{service.name}: stopped",
    )

    code = launcher.command_stop(ROOT)

    assert code == 0
    assert stopped == ["openwebui", "frontend", "backend"]


def test_openwebui_stop_removes_only_named_local_container(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    docker_calls: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command: list[str], **kwargs: object) -> Result:
        docker_calls.append(command)
        return Result()

    monkeypatch.setattr(launcher, "stop_service", lambda service, root=None: "openwebui: stopped")
    monkeypatch.setattr(launcher, "docker_engine_status", lambda timeout_seconds=1.5: (True, "Docker ready"))
    monkeypatch.setattr(launcher, "_developer_tool", lambda command: f"/tmp/{command}")
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    code = launcher.command_openwebui_stop(ROOT)

    assert code == 0
    assert docker_calls == [["/tmp/docker", "rm", "-f", launcher.OPENWEBUI_CONTAINER_NAME]]


def test_stop_service_discards_untrusted_pid_metadata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    launcher = load_launcher()
    service = launcher.Service(
        name="backend",
        url=launcher.BACKEND_URL,
        health_url=f"{launcher.BACKEND_URL}/health",
        pid_file=tmp_path / "backend.pid",
        log_file=tmp_path / "backend.log",
        metadata_file=tmp_path / "backend.json",
        cwd=tmp_path,
        command=["python", "-m", "ultimate_ai_agent.api.app"],
    )
    service.pid_file.write_text("123", encoding="utf-8")
    service.metadata_file.write_text("{}", encoding="utf-8")
    kill_calls: list[tuple[int, int]] = []

    monkeypatch.setattr(launcher, "cleanup_stale_pid", lambda pid_path: "running")
    monkeypatch.setattr(launcher, "read_pid_file", lambda pid_path: 123)
    monkeypatch.setattr(launcher, "metadata_matches_service", lambda service, pid: False)
    monkeypatch.setattr(launcher.os, "killpg", lambda pid, signal: kill_calls.append((pid, signal)))

    result = launcher.stop_service(service, root=tmp_path)

    assert result == "backend: removed untrusted pid file"
    assert not service.pid_file.exists()
    assert not service.metadata_file.exists()
    assert kill_calls == []


def test_launcher_runtime_state_is_gitignored() -> None:
    ignored = GITIGNORE_PATH.read_text(encoding="utf-8")

    assert ".uaa/" in ignored
    assert "Ultimate AI Agent.command" in ignored


def test_launcher_records_redacted_session_lifecycle_refs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    from ultimate_ai_agent.core.observability import SessionLogStore, clear_default_session_log_store_cache

    clear_default_session_log_store_cache()
    service = launcher.service_config(ROOT, "backend")

    launcher.record_launcher_event(
        ROOT,
        "service.process_spawned",
        service=service,
        status="started",
        lifecycle_state="started",
        pid=12345,
        reason_codes=["SERVICE_PROCESS_SPAWNED"],
    )

    store = SessionLogStore(root=tmp_path / ".uaa")
    result = store.list_events(event_type="service.process_spawned")

    assert result.returned_count == 1
    event = result.events[0]
    assert event.metadata["service_name"] == "backend"
    assert event.metadata["log_ref"] == "launcher-log:backend"
    assert len(event.evidence_refs) == 1
    assert event.evidence_refs[0].startswith("launcher-log:")
    payload = store.filepath.read_text(encoding="utf-8")
    assert str(service.log_file) not in payload
    assert "stdout" not in payload.lower()
    assert "stderr" not in payload.lower()
