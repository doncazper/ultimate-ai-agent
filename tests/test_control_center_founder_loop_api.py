from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest


client = TestClient(app)


def test_control_center_founder_loop_routes_are_storage_backed_and_safe(monkeypatch, tmp_path):
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))

    for path, operation in [
        ("/control-center/today/summary", "control_center_today_summary"),
        ("/control-center/actions/inbox", "control_center_actions_inbox"),
        ("/control-center/morning-briefing/summary", "control_center_morning_briefing_summary"),
        ("/control-center/storage/status", "control_center_storage_status"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert "safe_refs_only" in body["redactions_applied"]
        serialized = response.text.lower()
        assert str(tmp_path).lower() not in serialized
        assert "raw_prompt" not in serialized
        assert "raw_response" not in serialized
        assert "provider_payload" not in serialized
        assert "api_key" not in serialized


def test_control_center_founder_loop_routes_are_in_manifest_with_local_state_class(monkeypatch, tmp_path):
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}

    assert manifest.route_count == 112
    for path in [
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    ]:
        assert path in routes
        assert routes[path].method == "GET"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].operation_id.startswith("get_control_center_")

    assert "control_center_founder_loop_storage_summaries" in manifest.capabilities_declared
