import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeDelegationAdapterReadModel,
    build_runtime_delegation_adapter_read_model,
)


client = TestClient(app)


def test_hermes_runtime_delegation_read_model_is_readiness_only() -> None:
    read_model = build_runtime_delegation_adapter_read_model()

    assert read_model.schema_version == "runtime_delegation_adapter.v1"
    assert read_model.runtime_kind == "hermes_agent"
    assert read_model.uaa_controls_authority is True
    assert read_model.runtime_provides_capability_only is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.endpoint_posture.endpoint_configured is False
    assert read_model.endpoint_posture.live_transport_enabled is False
    assert read_model.live_run_submission_enabled is False
    assert read_model.runtime_model_calls_enabled is False
    assert read_model.provider_sdk_calls_enabled is False
    assert read_model.tool_execution_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.browser_automation_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.background_autonomy_enabled is False
    assert read_model.production_authority_enabled is False
    assert read_model.safe_refs_only is True
    assert read_model.raw_prompt_persisted is False
    assert read_model.raw_response_persisted is False
    assert read_model.raw_provider_payload_persisted is False
    assert "blocked-authority:runtime-delegation-live-run-submission" in (
        read_model.blocked_reason_refs
    )
    assert "next-safe-action-ref:runtime-delegation:bind-approval-envelope" in (
        read_model.next_safe_action_refs
    )


def test_hermes_runtime_delegation_rejects_authority_claims() -> None:
    base = build_runtime_delegation_adapter_read_model().model_dump()
    base["live_run_submission_enabled"] = True

    with pytest.raises(ValueError, match="RUNTIME_DELEGATION_AUTHORITY_DENIED"):
        RuntimeDelegationAdapterReadModel(**base)


def test_api_runtime_delegation_adapter_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/delegation-adapter")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_delegation_adapter.v1"
    assert data["runtime_kind"] == "hermes_agent"
    assert data["uaa_controls_authority"] is True
    assert data["control_center_talks_directly_to_runtime"] is False
    assert data["live_run_submission_enabled"] is False
    assert data["endpoint_posture"]["live_transport_enabled"] is False
    assert data["raw_provider_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-delegation-adapter:phase-01"
    )


def test_cli_runtime_delegation_adapter_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-delegation-adapter",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_delegation_adapter"]
    assert payload["execution_performed"] is False
    assert payload["live_run_submission_performed"] is False
    assert read_model["adapter_ref"] == "runtime-delegation-adapter:hermes-agent"
    assert read_model["route_ref"] == "GET /api/runtime/delegation-adapter"
    assert read_model["cli_ref"] == "uaa runtime inspect-delegation-adapter"
    assert read_model["live_run_submission_enabled"] is False
