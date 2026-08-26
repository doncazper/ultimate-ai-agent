from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.crm import (
    CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
    expected_crm_local_mutation_approval_ref,
)


CRM_READ_ROUTES = [
    ("/control-center/crm/summary", "control_center_crm_summary"),
    ("/control-center/crm/relationships", "control_center_crm_relationships"),
    ("/control-center/crm/timeline", "control_center_crm_timeline"),
    ("/control-center/crm/follow-ups", "control_center_crm_follow_ups"),
    ("/control-center/crm/pipelines", "control_center_crm_pipelines"),
    ("/control-center/crm/smart-lists", "control_center_crm_smart_lists"),
]


def test_control_center_crm_read_routes_are_backend_owned(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_CRM_STATE_DIR", str(tmp_path / "crm"))
    api_client = TestClient(app)

    for path, operation in CRM_READ_ROUTES:
        response = api_client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert body["service"] == "ControlCenterCrmAPI"
        assert "raw_contact_details_omitted" in body["redactions_applied"]
        assert "raw_message_bodies_omitted" in body["redactions_applied"]
        assert "provider_payloads_omitted" in body["redactions_applied"]
        assert body["data"]["contract_ref"] == CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF

    summary = api_client.get("/control-center/crm/summary").json()["data"]
    assert summary["backend_owned"] is True
    assert summary["safe_refs_only"] is True
    assert summary["authority_posture"]["connector_runtime_enabled"] is False
    assert summary["authority_posture"]["send_enabled"] is False
    assert summary["authority_posture"]["calendar_write_enabled"] is False
    assert summary["authority_posture"]["provider_model_call_enabled"] is False
    assert summary["authority_posture"]["live_web_enabled"] is False
    assert summary["authority_posture"]["browser_runtime_enabled"] is False
    assert summary["authority_posture"]["production_authority_enabled"] is False


def test_control_center_crm_local_mutation_requires_idempotency_and_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_CRM_STATE_DIR", str(tmp_path / "crm"))
    api_client = TestClient(app)
    target_ref = "follow-up-ref:crm-local:alpha:due"
    idempotency_ref = "idempotency-ref:api-crm-local-001"

    missing_idempotency = api_client.post(
        "/control-center/crm/local-mutations",
        json={
            "mutation_kind": "mark_follow_up_complete",
            "target_ref": target_ref,
            "approval_ref": "approval-ref:crm-local:missing",
        },
    )
    assert missing_idempotency.status_code == 428
    assert missing_idempotency.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    denied = api_client.post(
        "/control-center/crm/local-mutations",
        json={
            "mutation_kind": "mark_follow_up_complete",
            "target_ref": target_ref,
            "approval_ref": "approval-ref:crm-local:wrong",
        },
        headers={"x-uaa-idempotency-key": idempotency_ref},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "CRM_LOCAL_MUTATION_APPROVAL_DENIED"

    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    still_denied = api_client.post(
        "/control-center/crm/local-mutations",
        json={
            "mutation_kind": "mark_follow_up_complete",
            "target_ref": target_ref,
            "approval_ref": approval_ref,
        },
        headers={"x-uaa-idempotency-key": idempotency_ref},
    )
    assert still_denied.status_code == 403
    assert still_denied.json()["detail"]["code"] == "CRM_LOCAL_MUTATION_APPROVAL_DENIED"

    changed_denied = api_client.post(
        "/control-center/crm/local-mutations",
        json={
            "mutation_kind": "update_follow_up",
            "target_ref": target_ref,
            "approval_ref": approval_ref,
            "follow_up_status": "blocked",
        },
        headers={"x-uaa-idempotency-key": idempotency_ref},
    )
    assert changed_denied.status_code == 403
    assert (
        changed_denied.json()["detail"]["code"] == "CRM_LOCAL_MUTATION_APPROVAL_DENIED"
    )

    non_human_idempotency_ref = "idempotency-ref:api-crm-local-non-human"
    non_human_target_ref = "person-ref:crm-local:relationship-beta"
    non_human_approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=non_human_target_ref,
        idempotency_ref=non_human_idempotency_ref,
    )
    non_human_denied = api_client.post(
        "/control-center/crm/local-mutations",
        json={
            "actor_context": {
                "actor_type": "subagent",
                "actor_id": "agent-ref:request-controlled",
                "authority_source": "explicit_user_request",
            },
            "mutation_kind": "select_social_context",
            "target_ref": non_human_target_ref,
            "approval_ref": non_human_approval_ref,
        },
        headers={
            "x-uaa-idempotency-key": non_human_idempotency_ref,
            "x-uaa-operator-confirmed": "true",
        },
    )
    assert non_human_denied.status_code == 403
    assert (
        non_human_denied.json()["detail"]["code"]
        == "CRM_LOCAL_MUTATION_HUMAN_OPERATOR_REQUIRED"
    )
