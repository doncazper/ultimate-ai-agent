import importlib.util
import stat
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_PATH = ROOT / "scripts" / "dev" / "uaa_launcher.py"
WRAPPER_PATH = ROOT / "scripts" / "dev" / "uaa"
GITIGNORE_PATH = ROOT / ".gitignore"


def load_launcher():
    if not LAUNCHER_PATH.exists():
        pytest.fail("scripts/dev/uaa_launcher.py is missing")
    spec = importlib.util.spec_from_file_location("uaa_launcher", LAUNCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_launcher_rejects_non_loopback_hosts():
    launcher = load_launcher()

    for host in ["127.0.0.1", "localhost", "::1"]:
        assert launcher.validate_local_host(host) == host

    for host in ["0.0.0.0", "192.168.1.20", "control-center.local", "example.com"]:
        with pytest.raises(ValueError):
            launcher.validate_local_host(host)


def test_launcher_builds_localhost_only_command_lists():
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

    assert frontend[:2] == ["npm", "run"]
    assert "dev" in frontend
    assert "--host" in frontend
    assert frontend[frontend.index("--host") + 1] == "127.0.0.1"
    assert "--port" in frontend
    assert frontend[frontend.index("--port") + 1] == "5173"

    assert openwebui[:2] == ["docker", "run"]
    assert "-p" in openwebui
    assert openwebui[openwebui.index("-p") + 1] == "127.0.0.1:3000:8080"
    assert "ghcr.io/open-webui/open-webui:main" in openwebui
    assert any(value == "OPENAI_API_BASE_URL=http://host.docker.internal:8000/v1" for value in openwebui)
    assert any(value == "OPENAI_API_KEY=uaa-local-test" for value in openwebui)


def test_stale_pid_cleanup_removes_only_stale_pid_file(tmp_path):
    launcher = load_launcher()
    pid_path = tmp_path / "backend.pid"
    pid_path.write_text("999999\n", encoding="utf-8")

    result = launcher.cleanup_stale_pid(pid_path, is_running=lambda pid: False)

    assert result == "removed_stale"
    assert not pid_path.exists()


def test_running_pid_cleanup_keeps_pid_file(tmp_path):
    launcher = load_launcher()
    pid_path = tmp_path / "frontend.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    result = launcher.cleanup_stale_pid(pid_path, is_running=lambda pid: pid == 12345)

    assert result == "running"
    assert pid_path.read_text(encoding="utf-8") == "12345\n"


def test_macos_launcher_content_is_relative_and_safe():
    launcher = load_launcher()

    content = launcher.render_macos_launcher()

    assert "./scripts/dev/uaa start" in content
    assert "./scripts/dev/uaa ui" in content
    assert "./scripts/dev/uaa status" in content
    assert "/Users/" not in content
    assert "sudo" not in content
    assert "launchctl" not in content
    assert "LaunchAgent" not in content
    assert "/usr/local/bin" not in content


def test_launcher_openwebui_service_config_is_localhost_only():
    launcher = load_launcher()

    service = launcher.service_config(ROOT, "openwebui")

    assert service.url == "http://127.0.0.1:3000"
    assert service.health_url == "http://127.0.0.1:3000"
    assert service.pid_file.name == "openwebui.pid"
    assert service.log_file.name == "openwebui.log"


def test_launcher_backend_env_allows_only_openwebui_gateway_flag(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_KEY", "should-not-pass-through")

    env = launcher.safe_env(ROOT, "backend")

    assert env["UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"] == "1"
    assert "UAA_OPENWEBUI_TEST_GATEWAY_KEY" not in env


def test_shell_wrapper_exists_and_is_executable():
    assert WRAPPER_PATH.exists()
    mode = WRAPPER_PATH.stat().st_mode
    assert mode & stat.S_IXUSR


def test_launcher_runtime_state_is_gitignored():
    ignored = GITIGNORE_PATH.read_text(encoding="utf-8")

    assert ".uaa/" in ignored
    assert "Ultimate AI Agent.command" in ignored
