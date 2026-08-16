from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.control_center.action_decisions import (
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF,
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)
from tests.authority_helpers import (
    issue_workspace_write_authority_lease,
    workspace_write_authority_lease,
)
from scripts import verify_fcc_v1_002_action_inbox_state_machine as verifier


def _revision(repo: FounderLoopRepository, action_id: str) -> str:
    return str(repo.action_revision(action_id)["revision_ref"])


def _api_revision(client: TestClient, item_ref: str) -> str:
    inbox = client.get("/control-center/actions/inbox").json()["data"]
    return str(
        next(item for item in inbox["items"] if item["item_ref"] == item_ref)[
            "action_revision_ref"
        ]
    )


def test_action_decision_storage_records_receipts_replay_and_conflict(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[workspace_write_authority_lease()],
    )
    request = FounderLoopActionDecisionRequest(
        expected_revision_ref=_revision(repo, "setup-assistant-hardening"),
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
                expected_revision_ref=request.expected_revision_ref,
                decision_reason_ref="decision-reason-ref:test-reject-changed"
            ),
            idempotency_key_ref="idempotency-ref:test-reject-0001",
        )


def test_approval_decision_records_backend_owned_exact_local_approval(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[workspace_write_authority_lease()],
    )

    backend_owned = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=_revision(repo, "setup-assistant-hardening"),
            decision_reason_ref="decision-reason-ref:test-backend-owned-approval"
        ),
        idempotency_key_ref="idempotency-ref:test-backend-owned-approval",
    )
    assert backend_owned["status"] == "approved"
    assert backend_owned["approval_status"] == "approved"
    assert backend_owned["approval_ref"].startswith(
        "approval-ref:founder-loop-action:"
    )
    assert backend_owned["action_executed"] is False
    assert backend_owned["connector_write_performed"] is False

    approved = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=_revision(repo, "setup-assistant-hardening"),
            decision_reason_ref="decision-reason-ref:test-approval-valid",
        ),
        idempotency_key_ref="idempotency-ref:test-approval-approved",
    )

    assert approved["status"] == "approved"
    assert approved["approval_status"] == "approved"
    assert approved["approval_grants_execution"] is False
    assert approved["action_executed"] is False
    assert approved["connector_write_performed"] is False


def test_action_decision_without_workspace_write_authority_blocks_receipt_state(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[],
    )

    blocked = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=_revision(repo, "local-task-create-scorecard"),
            decision_reason_ref="decision-reason-ref:test-authority-missing"
        ),
        idempotency_key_ref="idempotency-ref:test-authority-missing",
    )

    assert blocked["status"] == "blocked"
    assert blocked["approval_status"] == "authority_denied"
    assert blocked["approval_ref"] is None
    assert blocked["authority_decision_outcome"] == "degrade_to_draft"
    assert FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_REQUIRED_BLOCKED_REF in blocked[
        "blocked_state_refs"
    ]
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert action["local_task_commit_eligible"] is False


def test_action_decision_api_requires_idempotency_and_returns_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    issue_workspace_write_authority_lease(authority_state_dir)
    client = TestClient(app)
    body = {
        "expected_revision_ref": _api_revision(
            client,
            "founder-action:setup-assistant-hardening",
        ),
        "decision_reason_ref": "decision-reason-ref:test-api-reject",
    }

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
        json={
            "expected_revision_ref": body["expected_revision_ref"],
            "decision_reason_ref": "decision-reason-ref:test-api-changed",
        },
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


def test_action_decision_api_records_backend_owned_approval_without_frontend_grants(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    issue_workspace_write_authority_lease(authority_state_dir)
    client = TestClient(app)

    response = client.post(
        "/control-center/actions/local-task-create-scorecard/approve",
        json={
            "expected_revision_ref": _api_revision(
                client,
                "founder-action:local-task-create-scorecard",
            ),
            "decision_reason_ref": "decision-reason-ref:test-api-backend-owned-approval",
            "metadata_refs": ["metadata-ref:test-api-backend-owned-approval"],
        },
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:test-api-backend-owned-approval"
        },
    )

    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["status"] == "approved"
    assert receipt["approval_status"] == "approved"
    assert receipt["approval_ref"].startswith("approval-ref:founder-loop-action:")
    assert receipt["action_executed"] is False

    inbox = client.get("/control-center/actions/inbox")
    action = next(
        item
        for item in inbox.json()["data"]["items"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert action["action_group_id"] == "approved_local_task_lane"
    assert action["local_task_commit_eligible"] is True
    assert action["local_task_commit_approval_ref"] == receipt["approval_ref"]


def test_fcc_v1_002_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []


def test_fcc_v1_002_verifier_flags_release_overclaim() -> None:
    release_surface = verifier.load_json(verifier.RELEASE_SURFACE_PATH)
    actions = next(route for route in release_surface["routes"] if route["path"] == "/actions")
    actions["status"] = "ship"
    actions["blocked_capabilities"] = []
    actions["approval_required"] = False
    actions["proof_lanes"] = [
        proof for proof in actions["proof_lanes"] if proof != verifier.FOUNDER_LOOP_V1_PROOF_REF
    ]

    failures = verifier.verify(
        release_surface=release_surface,
        check_files=False,
        check_api_behavior=False,
    )

    assert any("/actions ship status requires FCC-V1-007 proof lane" in failure for failure in failures)
    assert any("must require approval posture" in failure for failure in failures)
