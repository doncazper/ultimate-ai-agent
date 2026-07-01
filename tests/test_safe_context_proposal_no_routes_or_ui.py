from fastapi.testclient import TestClient

from scripts.verification.api_routes import EXPECTED_ROUTE_COUNT
from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.app import app


def test_m38_adds_no_backend_context_or_openwebui_routes() -> None:
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


def test_openapi_path_count_remains_at_current_boundary() -> None:
    client = TestClient(app)
    data = client.get("/openapi.json").json()

    assert data["info"]["version"] == __version__
    assert len(data.get("paths", {})) == EXPECTED_ROUTE_COUNT
    assert "/v1/models" in data.get("paths", {})
    assert "/v1/chat/completions" in data.get("paths", {})
    assert "/task-decomposition/run" in data.get("paths", {})
    assert "/files/tree/preview" in data.get("paths", {})
    assert "/observability/session-events" in data.get("paths", {})
    assert "/observability/client-errors" in data.get("paths", {})


def test_control_center_context_proposal_surface_has_no_handoff_or_injection_controls() -> None:
    from pathlib import Path

    src_root = Path("apps/control-center/src")
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in src_root.rglob("*")
        if path.is_file() and not path.name.endswith((".test.ts", ".test.tsx"))
    )

    assert "/context/proposals" in text
    assert "context proposal surface" in text
    assert "send to openwebui" not in text
    assert "/context/inject" not in text
    assert "/context/handoff" not in text
    assert "/openwebui/handoff" not in text
