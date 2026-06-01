from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app


client = TestClient(app)


def test_runtime_readiness_api_routes_are_status_and_validation_only():
    readiness = client.get("/runtime/readiness")
    matrix = client.get("/runtime/capability-matrix")

    assert readiness.status_code == 200
    assert matrix.status_code == 200
    assert readiness.json()["success"] is True
    assert matrix.json()["success"] is True
    assert readiness.json()["data"]["production_ready"] is False
    assert matrix.json()["data"]["summary"]["production_runtime_ready"] is False


def test_runtime_smoke_report_validation_rejects_secret_without_echo():
    secret = "api_key='abcdefghijklmnop'"
    response = client.post(
        "/runtime/smoke-reports/validate",
        json={
            "report": {
                "report_id": "manual_smoke_report_secret",
                "run_id": "run_secret",
                "smoke_request_id": "smoke_req_secret",
                "endpoint_summary": "loopback host localhost; no query; no credentials",
                "model_id_summary": "local-smoke-model",
                "response_origin": "fake_manual_loopback_smoke",
                "fixed_prompt_hash": "sha256:0123456789abcdef",
                "response_marker_found": False,
                "response_preview": secret,
                "response_body_sha256": "sha256:abcdef0123456789",
                "model_output_authoritative": False,
            }
        },
    )

    body = response.text
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "SECRET_LIKE_VALUE_REJECTED" in response.json()["data"]["reason_codes"]
    assert secret not in body


def test_runtime_openapi_has_three_m11_routes_and_unique_operation_ids():
    schema = app.openapi()
    paths = schema["paths"]

    assert "/runtime/readiness" in paths
    assert "/runtime/capability-matrix" in paths
    assert "/runtime/smoke-reports/validate" in paths
    for forbidden in [
        "/runtime/execute",
        "/runtime/run",
        "/runtime/smoke-reports/execute",
        "/runtime/plugins/enable",
    ]:
        assert forbidden not in paths

    operation_ids = [
        spec["operationId"]
        for methods in paths.values()
        for spec in methods.values()
        if isinstance(spec, dict) and "operationId" in spec
    ]
    assert len(operation_ids) == len(set(operation_ids))
