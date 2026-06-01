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

    assert client.post("/remote-workers/policy/validate", json={"policy": {"policy_id": "policy_default"}}).json()["success"] is True
    assert client.post("/remote-workers/jobs/validate", json={"job": envelope.model_dump(mode="json")}).json()["success"] is True
    assert client.get("/remote-workers/tailnet/status").json()["data"]["status"] in {"planned", "disabled", "not_configured"}
    assert client.get("/remote-workers/mesh/status").json()["data"]["live_mesh_enabled"] is False


def test_remote_worker_status_includes_open_source_first_private_mesh_metadata():
    status = client.get("/remote-workers/status").json()["data"]
    mesh = client.get("/remote-workers/mesh/status").json()["data"]
    transport_ids = set(status["transports"]["transport_ids"])

    assert {"headscale_planned", "generic_wireguard_planned", "tailscale_planned", "private_mesh_planned"}.issubset(transport_ids)
    assert status["transports"]["open_source_first"] is True
    assert mesh["preferred_planned_providers"][:2] == ["headscale_planned", "generic_wireguard_planned"]
    assert mesh["live_mesh_enabled"] is False
    assert mesh["headscale_integrated"] is False
    assert mesh["tailscale_integrated"] is False
    assert mesh["wireguard_integrated"] is False


def test_remote_worker_transport_validate_accepts_planned_headscale_descriptor_but_denies_enablement():
    safe = client.post(
        "/remote-workers/transports/validate",
        json={
            "transport": {
                "transport_id": "headscale_planned_test",
                "kind": "headscale_planned",
                "provider_kind": "headscale_planned",
                "status": "planned",
                "display_name": "Headscale Planned",
                "description": "Planned self-hosted private mesh metadata only.",
                "owner": "tests",
                "source": "fixture",
                "version": "0.0.0",
            }
        },
    ).json()
    enabled = client.post(
        "/remote-workers/transports/validate",
        json={
            "transport": {
                "transport_id": "headscale_enabled_test",
                "kind": "headscale_planned",
                "provider_kind": "headscale_planned",
                "status": "available",
                "display_name": "Headscale Enabled",
                "description": "Unsafe enabled private mesh metadata.",
                "enabled": True,
                "requires_network": True,
                "owner": "tests",
                "source": "fixture",
                "version": "0.0.0",
            }
        },
    ).json()

    assert "data" in safe
    assert safe["data"]["allowed"] is False
    assert "REMOTE_TRANSPORT_PLANNED_ONLY" in safe["data"]["reason_codes"]
    assert "data" in enabled
    assert enabled["data"]["allowed"] is False
    assert "REMOTE_TRANSPORT_NETWORK_DENIED" in enabled["data"]["reason_codes"]


def test_remote_worker_policy_validate_rejects_unsupported_enable_flags():
    tailnet = client.post(
        "/remote-workers/policy/validate",
        json={"policy": {"policy_id": "policy_tailnet", "remote_tailnet_enabled": True}},
    )
    personal_data = client.post(
        "/remote-workers/policy/validate",
        json={"policy": {"policy_id": "policy_personal", "remote_personal_data_enabled": True}},
    )
    both = client.post(
        "/remote-workers/policy/validate",
        json={
            "policy": {
                "policy_id": "policy_both",
                "remote_tailnet_enabled": True,
                "remote_personal_data_enabled": True,
            }
        },
    )

    assert tailnet.json()["success"] is False
    assert "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" in tailnet.text
    assert personal_data.json()["success"] is False
    assert "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" in personal_data.text
    assert both.json()["success"] is False
    assert "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" in both.text
    assert "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" in both.text


def test_remote_worker_api_wrappers_reject_top_level_extra_fields():
    requests = [
        ("/remote-workers/nodes/validate", {"node": {}, "unexpected": "extra"}),
        ("/remote-workers/transports/validate", {"transport": {}, "unexpected": "extra"}),
        ("/remote-workers/policy/validate", {"policy": {"policy_id": "policy_extra"}, "unexpected": "extra"}),
        ("/remote-workers/jobs/validate", {"job": _job_payload(), "unexpected": "extra"}),
        ("/remote-workers/dry-run", {"job": _job_payload(), "unexpected": "extra"}),
    ]

    for path, payload in requests:
        response = client.post(path, json=payload)
        body = response.json()
        assert response.status_code == 422
        assert body["success"] is False
        assert body["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_remote_worker_api_top_level_secret_extra_does_not_echo():
    response = client.post(
        "/remote-workers/policy/validate",
        json={"policy": {"policy_id": "policy_extra_secret"}, "api_key": "sk_secret_value_123456"},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "api_key" not in response.text
    assert "sk_secret_value_123456" not in response.text


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
