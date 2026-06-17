from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app


client = TestClient(app)


def test_control_center_api_routes_are_read_only_preview_only():
    for path in [
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["success"] is True

    manifest = client.get("/control-center/manifest").json()["data"]
    assert manifest["metadata"]["frontend_implemented"] is False
    assert "runtime_execution" in manifest["blocked_capabilities"]


def test_control_center_action_preview_api_denies_execute_and_does_not_echo_secret():
    secret = "api_key='abcdefghijklmnop'"
    response = client.post(
        "/control-center/actions/preview",
        json={
            "request_id": "cc_api_preview_secret",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": "preview_action",
            "target_ref": "runtime/execute/model",
            "purpose": "try to execute",
            "risk_level": "medium",
            "data_classification": "system_internal",
            "consent_refs": [],
            "metadata": {"claim": secret},
        },
    )

    body = response.text
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "RUNTIME_EXECUTION_BLOCKED" in response.json()["data"]["reason_codes"]
    assert "SECRET_LIKE_VALUE_REJECTED" in response.json()["data"]["reason_codes"]
    assert secret not in body


def test_control_center_openapi_routes_and_operation_ids_are_safe():
    schema = app.openapi()
    paths = schema["paths"]
    required = {
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/actions/preview",
    }
    assert required.issubset(paths)
    for forbidden in [
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/control-center/frontend",
    ]:
        assert forbidden not in paths

    operation_ids = [
        spec["operationId"]
        for methods in paths.values()
        for spec in methods.values()
        if isinstance(spec, dict) and "operationId" in spec
    ]
    assert "/files/review/approvals/capture" in paths
    assert "/v1/models" in paths
    assert "/v1/chat/completions" in paths
    assert len(paths) == 77
    assert len(operation_ids) == len(set(operation_ids)) == 77
