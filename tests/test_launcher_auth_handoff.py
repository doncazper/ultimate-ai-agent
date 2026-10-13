import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = ROOT / "scripts" / "dev" / "uaa_launcher.py"


def _launcher():
    spec = importlib.util.spec_from_file_location("uaa_launcher_auth_test", LAUNCHER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_control_center_bearer_uses_fragment_handoff(monkeypatch) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", "local-control-center-bearer")

    session_url = launcher.control_center_session_url()

    assert session_url.startswith("http://127.0.0.1:5173#")
    assert "uaa-session-bearer=local-control-center-bearer" in session_url


def test_control_center_launcher_never_hands_gateway_or_provider_keys_to_browser(monkeypatch) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", "fixture-control-center-session")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "fixture-distinct-gateway-key")
    monkeypatch.setenv("UAA_LLAMA_CPP_API_KEY", "fixture-provider-key")

    session_url = launcher.control_center_session_url()

    assert "uaa-session-bearer=fixture-control-center-session" in session_url
    assert "fixture-distinct-gateway-key" not in session_url
    assert "fixture-provider-key" not in session_url
    assert "uaa-model-gateway-bearer" not in session_url


def test_enabled_gateway_uses_validated_local_api_base_and_exact_cors_origin(monkeypatch) -> None:
    launcher = _launcher()
    monkeypatch.setattr(launcher, "verified_source_commit", lambda _root: "a" * 40)
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LAUNCHER_BACKEND_PORT", "8127")
    monkeypatch.setenv("UAA_LAUNCHER_FRONTEND_PORT", "5175")
    monkeypatch.setenv("VITE_UAA_API_BASE_URL", "https://external.invalid")
    monkeypatch.setenv("UAA_CONTROL_CENTER_CORS_ORIGIN", "*")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "fixture-distinct-gateway-key")

    frontend = launcher.safe_env(ROOT, "frontend")
    backend = launcher.safe_env(ROOT, "backend")

    assert frontend["VITE_UAA_API_BASE_URL"] == "http://127.0.0.1:8127"
    assert frontend["VITE_UAA_PROXY_TARGET"] == "http://127.0.0.1:8127"
    assert backend["UAA_CONTROL_CENTER_CORS_ORIGIN"] == "http://127.0.0.1:5175"
    assert "UAA_LLAMA_CPP_GATEWAY_KEY" not in frontend
    assert "UAA_CONTROL_CENTER_CORS_ORIGIN" not in frontend


def test_disabled_gateway_retains_existing_relative_launcher_api_base(monkeypatch) -> None:
    launcher = _launcher()
    monkeypatch.setattr(launcher, "verified_source_commit", lambda _root: "a" * 40)
    monkeypatch.delenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", raising=False)
    monkeypatch.setenv("VITE_UAA_API_BASE_URL", "https://external.invalid")
    monkeypatch.setenv("UAA_CONTROL_CENTER_CORS_ORIGIN", "*")

    assert launcher.safe_env(ROOT, "frontend")["VITE_UAA_API_BASE_URL"] == ""
    assert "UAA_CONTROL_CENTER_CORS_ORIGIN" not in launcher.safe_env(ROOT, "backend")


def test_gateway_resolves_busy_frontend_before_binding_backend_origin(monkeypatch, tmp_path) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LAUNCHER_AUTO_SWITCH_ON_PORT_BLOCK", "1")
    monkeypatch.setenv("UAA_LAUNCHER_FRONTEND_PORT", "5173")
    monkeypatch.setattr(launcher, "cleanup_stale_pid", lambda _path: "missing")
    monkeypatch.setattr(launcher, "is_port_open", lambda _host, port: port == 5173)
    monkeypatch.setattr(launcher, "record_launcher_event", lambda *_args, **_kwargs: None)
    observed = []

    def start(_root, service, **kwargs):
        observed.append((service.name, launcher.frontend_url(), kwargs))
        return service.name + ": running"

    monkeypatch.setattr(launcher, "start_service", start)

    assert launcher.command_start(tmp_path) == 0
    assert observed == [
        ("backend", "http://127.0.0.1:5174", {}),
        ("frontend", "http://127.0.0.1:5174", {"auto_selected_endpoint": True}),
    ]


def test_gateway_rejects_frontend_origin_drift_during_start(monkeypatch, tmp_path) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.delenv("UAA_LAUNCHER_AUTO_SWITCH_ON_PORT_BLOCK", raising=False)
    monkeypatch.setenv("UAA_LAUNCHER_FRONTEND_PORT", "5173")
    monkeypatch.setattr(launcher, "record_launcher_event", lambda *_args, **_kwargs: None)

    def start(_root, service):
        if service.name == "frontend":
            monkeypatch.setenv("UAA_LAUNCHER_FRONTEND_PORT", "5174")
        return service.name + ": running"

    monkeypatch.setattr(launcher, "start_service", start)
    assert launcher.command_start(tmp_path) == 1


def test_gateway_rejects_stale_owned_frontend_connection_metadata(monkeypatch) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setattr(launcher, "metadata_matches_process", lambda *_args: True)
    metadata = {"backend_proxy_url": launcher.backend_url()}
    monkeypatch.setattr(launcher, "_read_service_metadata", lambda _service: metadata)
    service = launcher.service_config(ROOT, "frontend")

    assert not launcher.metadata_matches_service(service, 12345)
    metadata["local_api_base_url"] = launcher.backend_url()
    assert launcher.metadata_matches_service(service, 12345)


def test_gateway_rejects_unverified_origin_on_owned_backend(monkeypatch, tmp_path) -> None:
    launcher = _launcher()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setattr(launcher, "cleanup_stale_pid", lambda _path: "running")
    monkeypatch.setattr(launcher, "read_pid_file", lambda _path: 12345)
    monkeypatch.setattr(launcher, "metadata_matches_service", lambda *_args: True)
    monkeypatch.setattr(launcher, "_read_service_metadata", lambda _service: {})
    monkeypatch.setattr(launcher, "record_launcher_event", lambda *_args, **_kwargs: None)

    result = launcher.start_service(tmp_path, launcher.service_config(tmp_path, "backend"))
    assert "blocked; local Chat frontend origin changed or is unverified" in result
