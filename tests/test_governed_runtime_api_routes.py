from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state, route_rate_limit_group
from ultimate_ai_agent.core.runtime_gateway.storage import RUNTIME_GATEWAY_STATE_DIR_ENV
from ultimate_ai_agent.core.runtime_gateway.local_model import RUNTIME_LOCAL_MODEL_ENABLED_ENV


client = TestClient(app)
IDEMPOTENCY_HEADERS = {"x-uaa-idempotency-key": "idempotency-ref:runtime-api"}


def _runtime_payload(summary: str = "safe governed runtime api summary") -> dict[str, object]:
    return {
        "requested_authority": "local_model",
        "requested_profile": "sealed",
        "input_ref": "runtime-input-ref:api",
        "safe_summary": summary,
        "metadata_refs": ["metadata-ref:runtime-api"],
    }


def _local_model_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "base_url": "http://127.0.0.1:9",
        "model_ref": "uaa-local-runtime",
        "messages": [{"role": "user", "content": "api prompt should not persist"}],
        "requested_profile": "local-runtime",
        "safe_summary": "Use local model runtime as an untrusted proposal.",
        "timeout_seconds": 0.1,
        "max_response_bytes": 1024,
    }
    payload.update(overrides)
    return payload


def test_governed_runtime_capabilities_are_sealed_by_default() -> None:
    response = client.get("/api/runtime/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["default_profile"] == "sealed"
    assert data["adapter_execution_enabled"] is False
    assert data["model_call_enabled"] is False
    assert data["command_execution_enabled"] is False
    assert data["safe_disable"]["active"] is True
    assert data["chat_runtime_integration"]["route_ref"] == "/api/runtime/local-model/call"
    assert data["chat_runtime_integration"]["default_status"] == "disabled_by_default"
    assert data["chat_runtime_integration"]["model_output_authority"] == (
        "untrusted_proposal_only"
    )


def test_governed_runtime_post_routes_require_idempotency(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    response = client.post("/api/runtime/invocations", json=_runtime_payload())
    local_model = client.post("/api/runtime/local-model/call", json=_local_model_payload())

    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert local_model.status_code == 428
    assert local_model.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


def test_governed_runtime_generic_invocation_cannot_enable_local_model_runtime(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, "1")
    reset_api_rate_limit_state()

    create = client.post(
        "/api/runtime/invocations",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-generic-local-model"},
        json=_runtime_payload() | {"requested_profile": "local-runtime"},
    )

    assert create.status_code == 200
    body = create.json()
    assert body["success"] is True
    policy = body["data"]["record"]["policy_decision"]
    assert policy["allowed_to_execute"] is False
    assert policy["adapter_execution_enabled"] is False
    assert policy["model_call_enabled"] is False
    assert (
        "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_GATEWAY_VALIDATION_REQUIRED"
        in policy["reason_codes"]
    )


def test_governed_runtime_invocation_flow_records_blocked_receipt(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    create = client.post(
        "/api/runtime/invocations",
        headers=IDEMPOTENCY_HEADERS,
        json=_runtime_payload(),
    )
    assert create.status_code == 200
    create_body = create.json()
    assert create_body["success"] is True
    assert create_body["data"]["execution_performed"] is False
    invocation_ref = create_body["data"]["record"]["invocation_ref"]

    detail = client.get(f"/api/runtime/invocations/{invocation_ref}")
    assert detail.status_code == 200
    assert detail.json()["success"] is True
    assert detail.json()["data"]["invocation_ref"] == invocation_ref

    list_response = client.get("/api/runtime/invocations")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["invocation_count"] == 1

    approve = client.post(
        f"/api/runtime/invocations/{invocation_ref}/approve",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-api-approve"},
        json={
            "approval_ref": "approval-ref:runtime-api",
            "approval_scope_ref": "approval-scope-ref:governed-runtime-exact-envelope",
            "safe_summary": "Approval binding remains an identifier only.",
        },
    )
    assert approve.status_code == 200
    assert approve.json()["success"] is True
    assert approve.json()["data"]["execution_performed"] is False
    assert approve.json()["data"]["approval_ref_is_identifier_only"] is True
    assert approve.json()["data"]["record"]["status"] == "pending_approval"

    approve_replay = client.post(
        f"/api/runtime/invocations/{invocation_ref}/approve",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-api-approve"},
        json={
            "approval_ref": "approval-ref:runtime-api",
            "approval_scope_ref": "approval-scope-ref:governed-runtime-exact-envelope",
            "safe_summary": "Approval binding remains an identifier only.",
        },
    )
    assert approve_replay.status_code == 200

    execute = client.post(
        f"/api/runtime/invocations/{invocation_ref}/execute",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-api-execute"},
        json={"safe_summary": "operator execute api summary should not persist"},
    )
    assert execute.status_code == 200
    assert execute.json()["success"] is False
    assert execute.json()["data"]["execution_performed"] is False
    assert execute.json()["data"]["blocked_reason"] == (
        "RUNTIME_ADAPTER_EXECUTION_BLOCKED_FOR_UNPROMOTED_AUTHORITY"
    )
    execute_replay = client.post(
        f"/api/runtime/invocations/{invocation_ref}/execute",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-api-execute"},
        json={"safe_summary": "operator execute api summary should not persist"},
    )
    assert execute_replay.status_code == 200

    receipt = client.get(f"/api/runtime/invocations/{invocation_ref}/receipt")
    assert receipt.status_code == 200
    assert receipt.json()["success"] is True
    assert receipt.json()["data"]["receipt"]["execution_performed"] is False

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert len(persisted.splitlines()) == 3
    assert "operator execute api summary should not persist" not in persisted


def test_governed_runtime_safe_disable_is_idempotency_bound(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    missing = client.post(
        "/api/runtime/safe-disable",
        json={"reason_ref": "reason-ref:runtime-safe-disable"},
    )
    assert missing.status_code == 428

    response = client.post(
        "/api/runtime/safe-disable",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-safe-disable"},
        json={
            "reason_ref": "reason-ref:runtime-safe-disable",
            "safe_summary": "operator safe disable summary should not persist",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["safe_disable"]["active"] is True
    assert response.json()["data"]["execution_performed"] is False
    replay = client.post(
        "/api/runtime/safe-disable",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-safe-disable"},
        json={
            "reason_ref": "reason-ref:runtime-safe-disable",
            "safe_summary": "operator safe disable summary should not persist",
        },
    )
    assert replay.status_code == 200

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert len(persisted.splitlines()) == 2
    assert "operator safe disable summary should not persist" not in persisted


def test_governed_runtime_routes_are_manifest_visible_with_safe_posture() -> None:
    manifest = build_api_manifest(app)
    routes = {(route.method, route.path): route for route in manifest.routes}

    for path in [
        "/api/runtime/capabilities",
        "/api/runtime/invocations",
        "/api/runtime/invocations/{id}",
        "/api/runtime/invocations/{id}/receipt",
    ]:
        route = routes[("GET", path)]
        assert "governed-runtime" in route.tags
        assert route.idempotency_required is False
        assert route.approval_posture == "not_required_for_route_classification"
        assert route.protected_route is True

    assert routes[("GET", "/api/runtime/capabilities")].route_classification == (
        "local_readonly"
    )
    assert routes[("GET", "/api/runtime/capabilities")].side_effect_class == (
        "validation_only"
    )

    for path in [
        "/api/runtime/invocations",
        "/api/runtime/local-model/call",
        "/api/runtime/invocations/{id}/approve",
        "/api/runtime/invocations/{id}/execute",
        "/api/runtime/safe-disable",
    ]:
        route = routes[("POST", path)]
        assert "governed-runtime" in route.tags
        assert route.side_effect_class == "local_dev_workspace_only"
        assert route.route_classification == "mutating_requires_authority"
        assert route.idempotency_required is True
        assert route.rate_limit_group == "governed_runtime_pilot"


def test_governed_runtime_rate_limit_group_handles_dynamic_routes() -> None:
    assert route_rate_limit_group("POST", "/api/runtime/invocations") == (
        "governed_runtime_pilot"
    )
    assert route_rate_limit_group("POST", "/api/runtime/local-model/call") == (
        "governed_runtime_pilot"
    )
    assert route_rate_limit_group(
        "POST",
        "/api/runtime/invocations/runtime-invocation-ref:abc/execute",
    ) == "governed_runtime_pilot"
    assert route_rate_limit_group("GET", "/api/runtime/invocations") is None


def test_governed_runtime_openapi_contains_exact_contract_routes() -> None:
    paths = app.openapi()["paths"]

    for path in [
        "/api/runtime/capabilities",
        "/api/runtime/invocations",
        "/api/runtime/local-model/call",
        "/api/runtime/invocations/{id}",
        "/api/runtime/invocations/{id}/receipt",
        "/api/runtime/invocations/{id}/approve",
        "/api/runtime/invocations/{id}/execute",
        "/api/runtime/safe-disable",
    ]:
        assert path in paths
    assert "post" in paths["/api/runtime/invocations"]
    assert "get" in paths["/api/runtime/invocations"]


def test_governed_runtime_local_model_call_records_safe_failure_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, "1")
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/local-model/call",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-local-model-api"},
        json=_local_model_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"]["local_model_runtime_enabled"] is True
    assert body["data"]["execution_performed"] is True
    assert body["data"]["adapter_execution_enabled"] is True
    assert body["data"]["model_call_performed"] is True
    assert body["data"]["error_category"] == "M164_LLAMA_CPP_GATEWAY_UNAVAILABLE"
    assert body["data"]["response_preview"] is None
    assert body["data"]["response_preview_persisted"] is False
    assert body["data"]["record"]["receipt"]["model_output_non_authoritative"] is True

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "api prompt should not persist" not in persisted
    assert "M164_LLAMA_CPP_GATEWAY_UNAVAILABLE" in persisted


def test_governed_runtime_local_model_call_is_disabled_by_default(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.delenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, raising=False)
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/local-model/call",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-local-model-disabled"},
        json=_local_model_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"]["local_model_runtime_enabled"] is False
    assert body["data"]["execution_performed"] is False
    assert body["data"]["adapter_execution_enabled"] is False
    assert body["data"]["model_call_performed"] is False
    assert body["data"]["error_category"] == "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
    assert "api prompt should not persist" not in response.text


def test_governed_runtime_local_model_call_blocks_non_loopback_url_redacted(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, "1")
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/local-model/call",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-local-model-remote"},
        json=_local_model_payload(base_url="http://example.com:8080"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"]["execution_performed"] is False
    assert body["data"]["adapter_execution_enabled"] is False
    assert body["data"]["model_call_performed"] is False
    assert body["data"]["error_category"] == "M164_LOOPBACK_ONLY_REQUIRED"
    assert "example.com" not in response.text
    assert "api prompt should not persist" not in response.text

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "example.com" not in persisted
    assert "api prompt should not persist" not in persisted
