from fastapi.testclient import TestClient

from tests.m7_helpers import actor
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.remote_workers import RemoteAuditContext, RemoteJobEnvelope, RemoteRiskLevel

client = TestClient(app)


def _job_payload(**overrides):
    payload = {
        "job_id": "job_api",
        "correlation_id": "corr_api",
        "node_id": "mock_node",
        "transport_id": "mock_metadata",
        "task_summary": "Validate remote API dry-run.",
        "requested_capabilities": ["dry_run"],
        "risk_level": RemoteRiskLevel.low,
        "audit_context": RemoteAuditContext(run_id="run_api", correlation_id="corr_api", actor_context=actor()).model_dump(mode="json"),
    }
    payload.update(overrides)
    return payload


def test_remote_worker_status_and_dry_run_api_are_validation_only():
    status = client.get("/remote-workers/status").json()
    dry_run = client.post("/remote-workers/dry-run", json={"job": _job_payload()}).json()

    assert status["success"] is True
    assert status["data"]["live_network_enabled"] is False
    assert status["data"]["dispatch_enabled"] is False
    assert dry_run["success"] is True
    assert dry_run["data"]["dispatch_performed"] is False
    assert dry_run["data"]["remote_execution_performed"] is False
    assert dry_run["data"]["subagent_launched"] is False
    assert dry_run["data"]["network_connections_opened"] == []


def test_remote_worker_validate_routes_and_tailnet_status_are_safe():
    envelope = RemoteJobEnvelope(**_job_payload())

    assert client.post("/remote-workers/jobs/validate", json={"job": envelope.model_dump(mode="json")}).json()["success"] is True
    assert client.get("/remote-workers/tailnet/status").json()["data"]["status"] in {"planned", "disabled", "not_configured"}
    assert client.get("/remote-workers/mesh/status").json()["data"]["live_mesh_enabled"] is False


def test_remote_worker_invalid_payload_does_not_echo_secret():
    response = client.post(
        "/remote-workers/jobs/validate",
        json={"job": {**_job_payload(task_summary="api_key='abcdefghijklmnop'")}},
    )

    body = response.json()
    assert body["success"] is False
    assert "api_key" not in response.text
    assert "abcdefghijklmnop" not in response.text


def test_public_api_has_no_remote_execution_routes():
    paths = {route.path for route in app.routes}

    assert "/remote-workers/dry-run" in paths
    assert "/remote-workers/dispatch" not in paths
    assert "/remote-workers/execute" not in paths
    assert "/remote-workers/subagents/launch" not in paths

