from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app


def test_m38_adds_no_backend_context_or_openwebui_routes():
    paths = app.openapi().get("paths", {})

    assert "/files/review/approvals/capture" in paths
    for forbidden in [
        "/context/propose",
        "/context/inject",
        "/context/handoff",
        "/openwebui/handoff",
        "/memory/write",
        "/tools/execute",
        "/tool-runtime/execute",
        "/files/read/raw",
        "/files/read/content",
        "/files/read/full",
    ]:
        assert forbidden not in paths


def test_openapi_path_count_remains_at_m37_boundary():
    client = TestClient(app)
    data = client.get("/openapi.json").json()

    assert data["info"]["version"] == "0.42.0"
    assert len(data.get("paths", {})) == 75


def test_control_center_has_no_m39_context_proposal_surface():
    from pathlib import Path

    src_root = Path("apps/control-center/src")
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in src_root.rglob("*") if path.is_file())

    assert "/context/proposals" not in text
    assert "context proposal surface" not in text
    assert "send to openwebui" not in text
    assert "inject context" not in text
