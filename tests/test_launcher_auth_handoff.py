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
