from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.control_center.action_decisions import (
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FounderLoopActionDecisionRequest,
    action_approval_request,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)
from scripts import verify_fcc_v1_002_action_inbox_state_machine as verifier


def test_action_decision_storage_records_receipts_replay_and_conflict(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:test-reject"
    )

    receipt = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="reject",
        request=request,
        idempotency_key_ref="idempotency-ref:test-reject-0001",
    )

    assert receipt["contract_ref"] == FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF
    assert receipt["decision"] == "reject"
    assert receipt["status"] == "rejected"
    assert receipt["action_executed"] is False
    assert receipt["connector_write_performed"] is False
    assert receipt["memory_write_performed"] is False
    assert receipt["raw_content_stored"] is False
    assert repo.latest_action_receipt("setup-assistant-hardening")["receipt_ref"] == (
        receipt["receipt_ref"]
    )

    replay = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="reject",
        request=request,
        idempotency_key_ref="idempotency-ref:test-reject-0001",
    )
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == receipt["receipt_ref"]

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_action_decision(
            action_id="setup-assistant-hardening",
            decision="reject",
            request=FounderLoopActionDecisionRequest(
                decision_reason_ref="decision-reason-ref:test-reject-changed"
            ),
            idempotency_key_ref="idempotency-ref:test-reject-0001",
        )


def test_approval_decision_requires_exact_local_approval_scope(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    blocked = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:test-approval-missing"
        ),
        idempotency_key_ref="idempotency-ref:test-approval-blocked",
    )
    assert blocked["status"] == "blocked"
    assert blocked["approval_status"] == "approval_required"
    assert blocked["action_executed"] is False

    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:test-approval-valid"
    )
    approval_request = action_approval_request(
        item_ref=action["item_ref"],
        actor_context=request.actor_context,
        risk_class=action["risk_class"],
        resource_refs=[
            action["item_ref"],
            action["action_envelope_ref"],
            action["action_scope_ref"],
            action["action_approval_requirement_ref"],
        ],
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local-test-reviewer",
        approval_ref="approval-ref:founder-loop-action:test-approve",
    )

    approved = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            approval_ref=grant.approval_ref,
            approval_grants=[grant],
            decision_reason_ref="decision-reason-ref:test-approval-valid",
        ),
        idempotency_key_ref="idempotency-ref:test-approval-approved",
    )

    assert approved["status"] == "approved"
    assert approved["approval_status"] == "approved"
    assert approved["approval_grants_execution"] is False
    assert approved["action_executed"] is False
    assert approved["connector_write_performed"] is False


def test_action_decision_api_requires_idempotency_and_returns_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)
    body = {"decision_reason_ref": "decision-reason-ref:test-api-reject"}

    missing = client.post(
        "/control-center/actions/setup-assistant-hardening/reject",
        json=body,
    )
    assert missing.status_code == 428
    assert missing.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    response = client.post(
        "/control-center/actions/setup-assistant-hardening/reject",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-reject"},
    )
    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["status"] == "rejected"
    assert receipt["action_executed"] is False
    assert receipt["raw_content_stored"] is False

    replay = client.post(
        "/control-center/actions/setup-assistant-hardening/reject",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-reject"},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is True

    conflict = client.post(
        "/control-center/actions/setup-assistant-hardening/reject",
        json={"decision_reason_ref": "decision-reason-ref:test-api-changed"},
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-reject"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "FOUNDER_LOOP_ACTION_IDEMPOTENCY_CONFLICT"

    receipt_response = client.get(
        "/control-center/actions/setup-assistant-hardening/receipt"
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["operation"] == "control_center_action_receipt"
    assert receipt_response.json()["data"]["receipt_ref"] == receipt["receipt_ref"]


def test_fcc_v1_002_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []


def test_fcc_v1_002_verifier_flags_release_overclaim() -> None:
    release_surface = verifier.load_json(verifier.RELEASE_SURFACE_PATH)
    actions = next(route for route in release_surface["routes"] if route["path"] == "/actions")
    actions["status"] = "ship"
    actions["blocked_capabilities"] = []
    actions["approval_required"] = False

    failures = verifier.verify(
        release_surface=release_surface,
        check_files=False,
        check_api_behavior=False,
    )

    assert any("/actions release status must remain partial" in failure for failure in failures)
    assert any("must require approval posture" in failure for failure in failures)
    assert any("missing blocked capability" in failure for failure in failures)
