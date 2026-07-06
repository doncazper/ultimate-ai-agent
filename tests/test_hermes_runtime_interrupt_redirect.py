import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS,
    RUNTIME_INTERRUPT_REDIRECT_CONTRACT_REF,
    RuntimeInterruptRedirectReadModel,
    RuntimeRunControlProposal,
    build_runtime_interrupt_redirect_read_model,
)


client = TestClient(app)


def test_interrupt_redirect_is_proposal_only_read_model() -> None:
    read_model = build_runtime_interrupt_redirect_read_model()

    assert read_model.schema_version == "runtime_interrupt_redirect.v1"
    assert read_model.contract_ref == RUNTIME_INTERRUPT_REDIRECT_CONTRACT_REF
    assert read_model.status == "run_control_proposal_only"
    assert read_model.route_ref == "GET /api/runtime/interrupt-redirect"
    assert read_model.cli_ref == "uaa runtime inspect-interrupt-redirect"
    assert read_model.proposal_count == 5
    assert read_model.read_only_proposal_count == 2
    assert read_model.approval_required_future_lane_count == 2
    assert read_model.blocked_count == 1
    assert read_model.run_ownership_visible is True
    assert read_model.stop_scope_visible is True
    assert read_model.idempotency_visible is True
    assert read_model.cancellation_receipt_visible is True
    assert read_model.recovery_state_visible is True
    assert read_model.proof_link_visible is True
    assert read_model.live_stop_post_enabled is False
    assert read_model.process_kill_enabled is False
    assert read_model.runtime_mutation_enabled is False
    assert read_model.background_autonomy_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.browser_automation_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_runtime_payload_persisted is False
    assert read_model.raw_log_persisted is False
    assert set(RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_interrupt_redirect_actions_are_proposal_or_blocked() -> None:
    read_model = build_runtime_interrupt_redirect_read_model()
    statuses_by_kind = {
        proposal.action_kind: proposal.action_status
        for proposal in read_model.proposals
    }

    assert statuses_by_kind == {
        "pause": "approval_required_future_lane",
        "stop": "blocked_until_exact_lane",
        "redirect": "read_only_proposal",
        "revise": "read_only_proposal",
        "recover": "approval_required_future_lane",
    }
    for proposal in read_model.proposals:
        assert proposal.action_ref.startswith("run-control-action-ref:")
        assert proposal.approval_scope_ref.startswith("approval-scope-ref:")
        assert proposal.idempotency_ref.startswith("idempotency-ref:")
        assert proposal.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert proposal.recovery_state_ref.startswith("recovery-state-ref:")
        assert proposal.proof_ref.startswith("proof-ref:")
        assert proposal.visible_in_control_center is True
        assert proposal.proposal_only is True
        assert proposal.live_stop_post_enabled is False
        assert proposal.process_kill_enabled is False
        assert proposal.runtime_mutation_enabled is False
        assert proposal.background_autonomy_enabled is False
        assert proposal.shell_execution_enabled is False
        assert proposal.provider_call_enabled is False
        assert proposal.browser_automation_enabled is False
        assert proposal.connector_write_enabled is False
        assert proposal.control_center_mints_authority is False
        assert proposal.raw_runtime_payload_persisted is False
        assert proposal.raw_log_persisted is False


@pytest.mark.parametrize(
    "field",
    [
        "live_stop_post_enabled",
        "process_kill_enabled",
        "runtime_mutation_enabled",
        "background_autonomy_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_runtime_payload_persisted",
        "raw_log_persisted",
    ],
)
def test_interrupt_redirect_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_interrupt_redirect_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_INTERRUPT_REDIRECT_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeInterruptRedirectReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "live_stop_post_enabled",
        "process_kill_enabled",
        "runtime_mutation_enabled",
        "background_autonomy_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_runtime_payload_persisted",
        "raw_log_persisted",
    ],
)
def test_interrupt_redirect_proposal_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_interrupt_redirect_read_model()
        .proposals[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_INTERRUPT_REDIRECT_ACTION_AUTHORITY_DENIED",
    ):
        RuntimeRunControlProposal(**payload)


def test_interrupt_redirect_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/interrupt-redirect")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_interrupt_redirect"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/interrupt-redirect"
    assert data["proposal_count"] == 5
    assert data["live_stop_post_enabled"] is False
    assert data["process_kill_enabled"] is False
    assert data["runtime_mutation_enabled"] is False
    assert data["raw_runtime_payload_persisted"] is False
    assert data["raw_log_persisted"] is False
    serialized = json.dumps(body).lower()
    assert "process_identifier_value" not in serialized
    assert "raw_runtime_payload_value" not in serialized
    assert "raw_log_value" not in serialized


def test_interrupt_redirect_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-interrupt-redirect",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_interrupt_redirect"]
    assert payload["proposal_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["raw_runtime_payloads_omitted"] is True
    assert payload["raw_logs_omitted"] is True
    assert payload["operator_instruction_text_omitted"] is True
    assert payload["live_stop_post_performed"] is False
    assert payload["process_kill_performed"] is False
    assert payload["runtime_mutation_performed"] is False
    assert payload["background_autonomy_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["provider_call_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["connector_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/interrupt-redirect"
    assert read_model["cli_ref"] == "uaa runtime inspect-interrupt-redirect"
    assert read_model["proposal_count"] == 5
