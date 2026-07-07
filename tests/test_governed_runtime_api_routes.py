import hashlib
import json

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state, route_rate_limit_group
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeCommandExecutionRequest,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RUNTIME_GATEWAY_STATE_DIR_ENV
from ultimate_ai_agent.core.runtime_gateway.local_model import RUNTIME_LOCAL_MODEL_ENABLED_ENV
from ultimate_ai_agent.core.runtime_gateway.interface_mode import (
    HERMES_CHAT_AUTHORITY_CAPABILITY_REF,
    HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF,
    HERMES_INTERFACE_MODE_ENABLED_ENV,
)
from ultimate_ai_agent.core.local_model_management.gateway import UAA_LLAMA_CPP_BASE_URL_ENV


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


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def _runtime_action_inbox_refs(record: dict[str, object]) -> dict[str, str]:
    request = record["request"]
    assert isinstance(request, dict)
    policy = record["policy_decision"]
    assert isinstance(policy, dict)
    exact_scope_ref = _test_hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": record["invocation_ref"],
            "payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "policy_decision_ref": policy["policy_decision_ref"],
            "requested_authority": request["requested_authority"],
        },
    )
    approval_ref = _test_hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": record["invocation_ref"],
            "requested_authority": request["requested_authority"],
            "requested_profile": request["requested_profile"],
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "policy_decision_ref": policy["policy_decision_ref"],
        },
    )
    action_envelope_ref = _test_hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": record["invocation_ref"],
            "approval_ref": approval_ref,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return {
        "approval_ref": approval_ref,
        "action_envelope_ref": action_envelope_ref,
        "exact_scope_ref": exact_scope_ref,
    }


def _activate_workspace_execute_authority(
    tmp_path,
    monkeypatch,
    *,
    suffix: str,
    mission_ref: str | None = None,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    payload = {
        "mode": "approved_safe_local_work_session",
        "requested_domains": {"workspace": ["read", "execute"]},
        "decision_reason_ref": f"reason-ref:authority-runtime-{suffix}",
        "safe_summary": "Authorize exact governed runtime workspace command execution.",
    }
    if mission_ref is not None:
        payload["scope"] = "mission"
        payload["mission_ref"] = mission_ref
    response = client.post(
        "/api/runtime/authority-leases",
        headers={
            "x-uaa-idempotency-key": f"idempotency-ref:authority-runtime-{suffix}"
        },
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


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
    assert data["command_runtime_integration"]["route_ref"] == "/api/runtime/command/run"
    assert data["command_runtime_integration"]["argv_only"] is True
    assert data["command_runtime_integration"]["shell_strings_accepted"] is False
    assert data["command_runtime_integration"]["raw_output_persisted"] is False
    catalog = {
        entry["intent"]: entry for entry in data["command_runtime_integration"]["allowlist_catalog"]
    }
    assert catalog["git_status"]["enabled_for_phase"] is True
    assert catalog["git_status"]["no_op_readonly"] is True
    assert catalog["focused_pytest"]["enabled_for_phase"] is False
    assert catalog["repo_doctor"]["enabled_for_phase"] is False


def test_governed_runtime_post_routes_require_idempotency(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    response = client.post("/api/runtime/invocations", json=_runtime_payload())
    local_model = client.post("/api/runtime/local-model/call", json=_local_model_payload())
    command = client.post(
        "/api/runtime/command/run",
        json={
            "intent": "git_status",
            "safe_summary": "Inspect repo status with redacted output.",
        },
    )
    hermes_chat = client.post(
        "/api/runtime/hermes/chat",
        json={
            "mode": "shell_guarded",
            "query": "summarize current safe runtime posture",
        },
    )
    authority_lease = client.post(
        "/api/runtime/authority-leases",
        json={
            "mode": "approved_safe_local_work_session",
            "decision_reason_ref": "reason-ref:runtime-authority-missing-idempotency",
            "safe_summary": "Select governed runtime authority.",
        },
    )

    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert local_model.status_code == 428
    assert local_model.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert command.status_code == 428
    assert command.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert hermes_chat.status_code == 428
    assert hermes_chat.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert authority_lease.status_code == 428
    assert authority_lease.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


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
        "/api/runtime/parity-loop",
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
    assert routes[("GET", "/api/runtime/parity-loop")].route_classification == (
        "local_sensitive"
    )
    assert routes[("GET", "/api/runtime/parity-loop")].side_effect_class == (
        "local_dev_workspace_only"
    )
    preview_route = routes[("POST", "/api/runtime/authority-decisions/preview")]
    assert "governed-runtime" in preview_route.tags
    assert preview_route.side_effect_class == "validation_only"
    assert preview_route.route_classification == "local_sensitive"
    assert preview_route.idempotency_required is False
    assert preview_route.approval_posture == "not_required_for_route_classification"
    mission_plan_route = routes[("POST", "/api/runtime/authority-missions/plan")]
    assert "governed-runtime" in mission_plan_route.tags
    assert mission_plan_route.side_effect_class == "validation_only"
    assert mission_plan_route.route_classification == "local_sensitive"
    assert mission_plan_route.idempotency_required is False
    assert (
        mission_plan_route.approval_posture
        == "not_required_for_route_classification"
    )

    for path in [
        "/api/runtime/invocations",
        "/api/runtime/authority-leases",
        "/api/runtime/authority-leases/revoke",
        "/api/runtime/command/run",
        "/api/runtime/hermes/chat",
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
    assert route_rate_limit_group("POST", "/api/runtime/command/run") == (
        "governed_runtime_pilot"
    )
    assert route_rate_limit_group("POST", "/api/runtime/hermes/chat") == (
        "governed_runtime_pilot"
    )
    assert route_rate_limit_group("POST", "/api/runtime/authority-leases") == (
        "governed_runtime_pilot"
    )
    assert route_rate_limit_group("POST", "/api/runtime/authority-leases/revoke") == (
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
        "/api/runtime/parity-loop",
        "/api/runtime/authority-decisions/preview",
        "/api/runtime/authority-missions/plan",
        "/api/runtime/invocations",
        "/api/runtime/command/run",
        "/api/runtime/hermes/chat",
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


def test_governed_runtime_parity_loop_exposes_cockpit_cli_api_refs() -> None:
    response = client.get("/api/runtime/parity-loop")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "uaa_goatcitadel_runtime_parity_loop.v1"
    assert data["source"] == "python_core_runtime_parity_loop_read_model"
    assert data["backend_owned"] is True
    assert data["safe_refs_only"] is True
    assert data["raw_content_included"] is False
    assert data["api_route_ref"] == "GET /api/runtime/parity-loop"
    assert data["cli_ref"] == "uaa runtime inspect-parity-loop"
    assert "runtime-loop-stage-ref:signed-evidence" in data["stage_refs"]
    assert data["execution_performed_by_read_model"] is False
    assert data["control_center_mints_authority"] is False
    assert data["broad_runtime_authority_enabled"] is False


def test_governed_runtime_local_model_call_records_safe_failure_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    monkeypatch.setenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, "1")
    monkeypatch.setenv(UAA_LLAMA_CPP_BASE_URL_ENV, "http://127.0.0.1:9")
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
    assert body["data"]["execution_performed"] is False
    assert body["data"]["adapter_execution_enabled"] is False
    assert body["data"]["model_call_performed"] is False
    assert body["data"]["error_category"] == "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
    assert body["data"]["response_preview"] is None
    assert body["data"]["response_preview_persisted"] is False
    assert body["data"]["record"]["receipt"]["model_output_non_authoritative"] is True
    assert body["data"]["record"]["policy_decision"]["authority_decision_outcome"] == (
        "degrade_to_draft"
    )
    assert body["data"]["record"]["policy_decision"]["authority_domain"] == (
        "provider_model_calls"
    )
    assert body["data"]["record"]["policy_decision"]["authority_capability"] == (
        "execute"
    )
    assert body["data"]["record"]["policy_decision"]["authority_required_mode"] == (
        "full_machine_access_session"
    )
    invocation_ref = body["data"]["record"]["invocation_ref"]

    receipt = client.get(f"/api/runtime/invocations/{invocation_ref}/receipt")
    assert receipt.status_code == 200
    receipt_body = receipt.json()
    assert receipt_body["success"] is True
    assert receipt_body["data"]["execution_performed"] is False
    assert receipt_body["data"]["model_call_performed"] is False
    assert receipt_body["data"]["command_execution_performed"] is False
    assert receipt_body["data"]["receipt"]["model_call_performed"] is False
    assert "api prompt should not persist" not in receipt.text

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "api prompt should not persist" not in persisted
    assert "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED" in persisted


def test_governed_runtime_hermes_chat_requires_workspace_execute_authority(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/hermes/chat",
        headers={"x-uaa-idempotency-key": "idempotency-ref:hermes-chat-api-no-lease"},
        json={
            "mode": "shell_guarded",
            "query": "summarize current safe runtime posture",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    data = body["data"]
    assert data["execution_performed"] is False
    assert data["authority_decision_outcome"] == "deny"
    assert data["authority_lease_ref"] is None
    assert data["authority_capability_ref"] == HERMES_CHAT_AUTHORITY_CAPABILITY_REF
    receipt = data["receipt"]
    assert receipt["authority_decision_outcome"] == "deny"
    assert HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF in receipt["blocked_reason_refs"]


def test_governed_runtime_command_run_records_redacted_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/command/run",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-command-api"},
        json={
            "intent": "git_status",
            "safe_summary": "Inspect repo status with redacted output.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["execution_performed"] is True
    assert body["data"]["adapter_execution_enabled"] is True
    assert body["data"]["command_execution_enabled"] is True
    assert body["data"]["command_execution_performed"] is True
    assert body["data"]["shell_strings_accepted"] is False
    assert body["data"]["raw_output_persisted"] is False
    assert body["data"]["output_summary_returned"] is True
    assert body["data"]["output_persisted"] is False
    assert body["data"]["exit_code"] == 0
    assert body["data"]["error_category"] is None
    assert "git status --short" not in response.text
    assert "stdout" not in response.text
    assert "stderr" not in response.text
    invocation_ref = body["data"]["record"]["invocation_ref"]

    receipt = client.get(f"/api/runtime/invocations/{invocation_ref}/receipt")
    assert receipt.status_code == 200
    receipt_body = receipt.json()
    assert receipt_body["success"] is True
    assert receipt_body["data"]["execution_performed"] is True
    assert receipt_body["data"]["command_execution_performed"] is True

    replay = client.post(
        "/api/runtime/command/run",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-command-api"},
        json={
            "intent": "git_status",
            "safe_summary": "Inspect repo status with redacted output.",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is True

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "git status --short" not in persisted
    assert "/Users/" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_governed_runtime_command_run_evaluates_matching_mission_lease(
    tmp_path,
    monkeypatch,
) -> None:
    mission_ref = "mission-ref:test-runtime-command-api"
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()
    _activate_workspace_execute_authority(
        tmp_path,
        monkeypatch,
        suffix="mission-command-api",
        mission_ref=mission_ref,
    )

    matching = client.post(
        "/api/runtime/command/run",
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:runtime-command-mission-api"
        },
        json={
            "intent": "git_status",
            "mission_ref": mission_ref,
            "safe_summary": "Inspect repo status under a matching mission lease.",
        },
    )

    assert matching.status_code == 200
    matching_body = matching.json()
    assert matching_body["success"] is True
    assert matching_body["data"]["command_execution_performed"] is True
    matching_record = matching_body["data"]["record"]
    assert matching_record["request"]["mission_ref"] == mission_ref
    assert matching_record["policy_decision"]["authority_decision_outcome"] == "allow"
    assert matching_record["policy_decision"]["authority_lease_ref"]

    missing = client.post(
        "/api/runtime/command/run",
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:runtime-command-mission-missing-api"
            )
        },
        json={
            "intent": "git_status",
            "safe_summary": "Inspect repo status without the active mission ref.",
        },
    )

    assert missing.status_code == 200
    missing_body = missing.json()
    assert missing_body["success"] is False
    assert missing_body["data"]["command_execution_performed"] is False
    missing_policy = missing_body["data"]["record"]["policy_decision"]
    assert missing_policy["authority_decision_outcome"] == "degrade_to_draft"
    assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in (
        missing_policy["reason_codes"]
    )


def test_governed_runtime_action_inbox_execute_receipt_detail_reports_execution(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()
    _activate_workspace_execute_authority(tmp_path, monkeypatch, suffix="success-api")
    command_request = RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:governed-runtime-contracts"],
        approval_ref=None,
        safe_summary="Run the exact focused governed runtime contract test lane.",
        timeout_seconds=30,
    )
    invocation_request = runtime_command_invocation_request(command_request)

    create = client.post(
        "/api/runtime/invocations",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-success-api-create"},
        json=invocation_request.model_dump(mode="json"),
    )
    assert create.status_code == 200
    record = create.json()["data"]["record"]
    invocation_ref = record["invocation_ref"]
    refs = _runtime_action_inbox_refs(record)

    approve = client.post(
        f"/api/runtime/invocations/{invocation_ref}/approve",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-success-api-approve"},
        json={
            "decision": "approve",
            "action_envelope_ref": refs["action_envelope_ref"],
            "exact_scope_ref": refs["exact_scope_ref"],
            "expected_payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "expected_policy_decision_ref": record["policy_decision"]["policy_decision_ref"],
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "risk_class": "medium",
            "safe_summary": "Action Inbox approved exact focused pytest runtime lane.",
        },
    )
    assert approve.status_code == 200
    envelope = approve.json()["data"]["record"]["action_inbox_envelope"]

    execute_command = command_request.model_copy(
        update={"approval_ref": envelope["approval_ref"]}
    )
    execute = client.post(
        f"/api/runtime/invocations/{invocation_ref}/execute",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-success-api-execute"},
        json={
            "approval_ref": envelope["approval_ref"],
            "action_envelope_ref": envelope["action_envelope_ref"],
            "expected_payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "expected_policy_decision_ref": record["policy_decision"]["policy_decision_ref"],
            "command_request": execute_command.model_dump(mode="json"),
            "safe_summary": "Execute approved runtime command through exact bridge.",
        },
    )

    assert execute.status_code == 200
    body = execute.json()
    assert body["success"] is True
    assert body["data"]["execution_performed"] is True
    assert body["data"]["command_execution_performed"] is True

    receipt = client.get(f"/api/runtime/invocations/{invocation_ref}/receipt")
    assert receipt.status_code == 200
    receipt_body = receipt.json()
    assert receipt_body["success"] is True
    assert receipt_body["data"]["execution_performed"] is True
    assert receipt_body["data"]["command_execution_performed"] is True
    assert receipt_body["data"]["receipt"]["execution_performed"] is True
    assert "stdout" not in receipt.text
    assert "stderr" not in receipt.text


def test_governed_runtime_command_run_blocks_unapproved_command_intent(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/command/run",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-command-blocked-api"},
        json={
            "intent": "focused_pytest",
            "target_refs": ["test-ref:runtime-api"],
            "approval_ref": "approval-ref:identifier-only",
            "safe_summary": "Attempt focused pytest command with approval identifier only.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"]["execution_performed"] is False
    assert body["data"]["command_execution_enabled"] is False
    assert body["data"]["command_execution_performed"] is False
    assert body["data"]["error_category"] == "RUNTIME_COMMAND_APPROVAL_BRIDGE_REQUIRED"


def test_governed_runtime_action_inbox_execute_rejects_changed_scope(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()
    _activate_workspace_execute_authority(
        tmp_path,
        monkeypatch,
        suffix="changed-scope",
    )
    command_request = RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:governed-runtime-contracts"],
        approval_ref=None,
        safe_summary="Run the exact focused governed runtime contract test lane.",
    )
    invocation_request = runtime_command_invocation_request(command_request)

    create = client.post(
        "/api/runtime/invocations",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-api-create"},
        json=invocation_request.model_dump(mode="json"),
    )
    assert create.status_code == 200
    record = create.json()["data"]["record"]
    invocation_ref = record["invocation_ref"]
    refs = _runtime_action_inbox_refs(record)

    approve = client.post(
        f"/api/runtime/invocations/{invocation_ref}/approve",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-api-approve"},
        json={
            "decision": "approve",
            "action_envelope_ref": refs["action_envelope_ref"],
            "exact_scope_ref": refs["exact_scope_ref"],
            "expected_payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "expected_policy_decision_ref": record["policy_decision"]["policy_decision_ref"],
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "risk_class": "medium",
            "safe_summary": "Action Inbox approved exact focused pytest runtime lane.",
        },
    )
    assert approve.status_code == 200
    approve_body = approve.json()
    assert approve_body["success"] is True
    assert approve_body["data"]["approval_validated"] is True
    assert approve_body["data"]["approval_status"] == "approved_pending_execution"
    envelope = approve_body["data"]["record"]["action_inbox_envelope"]

    changed_command = command_request.model_copy(
        update={
            "approval_ref": envelope["approval_ref"],
            "target_refs": ["test-ref:changed-scope"],
        }
    )
    execute = client.post(
        f"/api/runtime/invocations/{invocation_ref}/execute",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-action-inbox-api-execute"},
        json={
            "approval_ref": envelope["approval_ref"],
            "action_envelope_ref": envelope["action_envelope_ref"],
            "expected_payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "expected_policy_decision_ref": record["policy_decision"]["policy_decision_ref"],
            "command_request": changed_command.model_dump(mode="json"),
            "safe_summary": "Execute approved runtime command through exact bridge.",
        },
    )

    assert execute.status_code == 200
    body = execute.json()
    assert body["success"] is False
    assert body["data"]["execution_performed"] is False
    assert body["data"]["command_execution_performed"] is False
    assert body["data"]["error_category"] == "RUNTIME_COMMAND_ACTION_INBOX_SCOPE_CHANGED"
    assert body["data"]["output_summary"] == (
        "Command output redacted; command was blocked before process start."
    )
    inbox = client.get("/control-center/actions/inbox")
    assert inbox.status_code == 200
    bridge = inbox.json()["data"]["runtime_action_inbox_bridge_read_model"]
    assert bridge["item_count"] == 1
    assert bridge["items"][0]["invocation_ref"] == invocation_ref
    assert bridge["items"][0]["action_envelope_ref"] == (
        envelope["action_envelope_ref"]
    )
    assert bridge["items"][0]["receipt_refs"]


def test_governed_runtime_action_inbox_computed_approval_ref_is_identifier_only(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    reset_api_rate_limit_state()
    command_request = RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:governed-runtime-contracts"],
        approval_ref=None,
        safe_summary="Run the exact focused governed runtime contract test lane.",
    )
    invocation_request = runtime_command_invocation_request(command_request)

    create = client.post(
        "/api/runtime/invocations",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-computed-approval-api-create"},
        json=invocation_request.model_dump(mode="json"),
    )
    assert create.status_code == 200
    record = create.json()["data"]["record"]
    refs = _runtime_action_inbox_refs(record)

    approve = client.post(
        f"/api/runtime/invocations/{record['invocation_ref']}/approve",
        headers={"x-uaa-idempotency-key": "idempotency-ref:runtime-computed-approval-api-approve"},
        json={
            "approval_ref": refs["approval_ref"],
            "decision": "approve",
            "action_envelope_ref": refs["action_envelope_ref"],
            "exact_scope_ref": refs["exact_scope_ref"],
            "expected_payload_fingerprint_ref": record["payload_fingerprint_ref"],
            "expected_policy_decision_ref": record["policy_decision"]["policy_decision_ref"],
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "risk_class": "medium",
            "safe_summary": "Computed approval refs are identifiers only.",
        },
    )

    assert approve.status_code == 200
    body = approve.json()
    assert body["success"] is True
    assert body["data"]["approval_validated"] is False
    assert body["data"]["command_execution_enabled"] is False
    assert "blocked-state:runtime-approval-ref-identifier-only" in (
        body["data"]["blocked_reason_refs"]
    )
    assert "blocked-state:runtime-backend-approval-missing" in (
        body["data"]["blocked_reason_refs"]
    )


def test_governed_runtime_local_model_call_is_disabled_by_default(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(RUNTIME_GATEWAY_STATE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
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
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
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
