from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.dependencies import clear_founder_attention_workflow_cache
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.control_center.founder_loop_mission_refs import (
    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.storage.founder_loop_exact_action import (
    FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,
)


client = TestClient(app)
TODAY_ITEM_REF = FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    reset_api_rate_limit_state()
    yield
    reset_api_rate_limit_state()


def _issue_exact_lease(
    *,
    authority_state_dir: Path,
    status: dict[str, object],
    mission_ref: str,
):
    lease_store = AuthorityLeaseStore(authority_state_dir)
    resource_refs = [
        FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
        FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
        str(status["target_ref"]),
        str(status["root_ref"]),
        str(status["path_ref"]),
        mission_ref,
    ]
    lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=mission_ref,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref="constraint-ref:attention-api:resources",
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resource_refs,
                    safe_summary="Allow only the exact attention workflow resources.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:attention-api:path",
                    kind=AuthorityConstraintKind.path_refs,
                    allowed_refs=[str(status["path_ref"])],
                    safe_summary="Allow only the opaque canonical path ref.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:attention-api:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Allow one metadata operation.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:attention-api:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Bound the zero-cost mission.",
                ),
            ],
            decision_reason_ref="reason-ref:attention-api:lease",
            safe_summary="Issue one exact metadata-only attention workflow lease.",
        ),
        idempotency_ref="idempotency-ref:attention-api:lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return lease


def test_exact_action_api_completes_and_refreshes_backend_today(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    founder_state = tmp_path / "founder-loop"
    authority_state = tmp_path / "authority"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(founder_state))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(authority_state))
    clear_founder_attention_workflow_cache()

    status_response = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    )
    assert status_response.status_code == 200
    status = status_response.json()["data"]
    assert status["execution_performed"] is False
    assert status["exact_approval_required"] is True
    mission_ref = "mission-ref:attention-api:success"
    lease = _issue_exact_lease(
        authority_state_dir=authority_state,
        status=status,
        mission_ref=mission_ref,
    )
    source_review_response = client.post(
        "/control-center/today/exact-action/source-review",
        json={
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"],
            "mission_ref": mission_ref,
            "lease_ref": lease.lease_ref,
        },
        headers={
            "x-uaa-idempotency-key": "bad",
            "x-uaa-idempotency-ref": "attention-api-inspect",
        },
    )
    assert source_review_response.status_code == 200, source_review_response.text
    source_review = source_review_response.json()["data"]
    source_review_replay = client.post(
        "/control-center/today/exact-action/source-review",
        json={
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"],
            "mission_ref": mission_ref,
            "lease_ref": lease.lease_ref,
        },
        headers={"x-uaa-idempotency-ref": "attention-api-inspect"},
    ).json()["data"]
    assert (
        source_review_replay["source_review_receipt_ref"]
        == (source_review["source_review_receipt_ref"])
    )
    conflicting_idempotency = client.post(
        "/control-center/today/exact-action/source-review",
        json={
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"],
            "mission_ref": mission_ref,
            "lease_ref": lease.lease_ref,
        },
        headers={
            "x-uaa-idempotency-key": "attention-api-conflict-key",
            "x-uaa-idempotency-ref": "attention-api-conflict-ref",
        },
    )
    assert conflicting_idempotency.status_code == 400
    assert conflicting_idempotency.json()["detail"]["code"] == (
        "API_IDEMPOTENCY_CONFLICT"
    )
    request = {
        "workflow_ref": "founder-loop-attention-workflow:api-success",
        "today_item_ref": TODAY_ITEM_REF,
        "inspected_source_refs": status["required_inspected_source_refs"],
        "source_review_receipt_ref": source_review["source_review_receipt_ref"],
        "mission_ref": mission_ref,
        "run_ref": "run-ref:attention-api:success",
        "lease_ref": lease.lease_ref,
        "start_deadline": (utc_now() + timedelta(minutes=10)).isoformat(),
        "safe_goal_summary": "Private family detail must remain transient only.",
    }
    prepared_response = client.post(
        "/control-center/today/exact-action/prepare",
        json=request,
        headers={"x-uaa-idempotency-key": "attention-api-prepare"},
    )
    assert prepared_response.status_code == 200, prepared_response.text
    prepared = prepared_response.json()["data"]
    prepared_replay_response = client.post(
        "/control-center/today/exact-action/prepare",
        json=request,
        headers={"x-uaa-idempotency-key": "attention-api-prepare"},
    )
    assert prepared_replay_response.status_code == 200
    assert prepared_replay_response.json()["data"] == prepared
    assert prepared["execution_performed"] is False
    decision_payload = {
        "workflow_ref": request["workflow_ref"],
        "today_item_ref": TODAY_ITEM_REF,
        "inspected_source_refs": request["inspected_source_refs"],
        "source_review_receipt_ref": request["source_review_receipt_ref"],
        "proposal_ref": prepared["proposal_ref"],
    }
    approval_response = client.post(
        "/control-center/today/exact-action/approve",
        json=decision_payload,
        headers={"x-uaa-idempotency-key": "attention-api-approve"},
    )
    assert approval_response.status_code == 200, approval_response.text
    approval = approval_response.json()["data"]
    approval_replay_response = client.post(
        "/control-center/today/exact-action/approve",
        json=decision_payload,
        headers={"x-uaa-idempotency-ref": "attention-api-approve-second"},
    )
    assert approval_replay_response.status_code == 200
    assert (
        approval_replay_response.json()["data"]["approval_ref"]
        == approval["approval_ref"]
    )
    assert approval["approval_ref_is_identifier_only"] is True
    assert approval["exact_scope_recorded_by_python_core"] is True
    assert approval["execution_scope_validation_pending"] is True
    pending_status = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]
    assert pending_status["workflow_status"] == (
        "approval_recorded_execution_validation_pending"
    )
    assert pending_status["execution_performed"] is False
    assert pending_status["exact_approval_required"] is False
    assert pending_status["execution_truth_status"] == "execution_not_recorded"
    approval_replay = client.post(
        "/control-center/today/exact-action/approve",
        json=decision_payload,
        headers={"x-uaa-idempotency-key": "attention-api-approve"},
    ).json()["data"]
    assert approval_replay["approval_ref"] == approval["approval_ref"]
    execution_response = client.post(
        "/control-center/today/exact-action/execute",
        json={**decision_payload, "approval_ref": approval["approval_ref"]},
        headers={"x-uaa-idempotency-key": "attention-api-execute"},
    )
    assert execution_response.status_code == 200, execution_response.text
    result = execution_response.json()["data"]
    assert result["status"] == "receipt_recorded"
    assert result["backend_today_refreshed"] is True
    assert result["receipt_refs"]
    assert source_review["source_review_receipt_ref"] in result["receipt_refs"]
    assert result["memory_candidate_ref"] is None
    assert result["memory_candidate_created"] is False
    execution_replay = client.post(
        "/control-center/today/exact-action/execute",
        json={**decision_payload, "approval_ref": approval["approval_ref"]},
        headers={"x-uaa-idempotency-key": "attention-api-execute"},
    ).json()["data"]
    assert execution_replay["completion_ref"] == result["completion_ref"]
    assert execution_replay["terminal_replay"] is True

    today = client.get("/control-center/today/summary").json()["data"]
    action = next(
        item for item in today["actions"] if item["item_ref"] == TODAY_ITEM_REF
    )
    assert action["status"] == "receipt_recorded"
    assert result["completion_ref"] in action["receipt_refs"]
    final_status = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]
    assert final_status["workflow_status"] == "receipt_recorded"
    assert final_status["execution_performed"] is True
    assert final_status["exact_approval_required"] is False
    assert result["completion_ref"] in final_status["receipt_refs"]
    assert str(tmp_path).lower() not in execution_response.text.lower()
    persisted = b"\n".join(
        path.read_bytes()
        for state_root in (founder_state, authority_state)
        for path in state_root.rglob("*")
        if path.is_file()
    )
    assert b"Private family detail" not in persisted
    clear_founder_attention_workflow_cache()


def test_exact_action_api_rejects_source_substitution_before_prepare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder-loop"))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    clear_founder_attention_workflow_cache()
    status = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]
    mission_ref = "mission-ref:attention-api:source-substitution"
    lease = _issue_exact_lease(
        authority_state_dir=tmp_path / "authority",
        status=status,
        mission_ref=mission_ref,
    )
    source_review = client.post(
        "/control-center/today/exact-action/source-review",
        json={
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"],
            "mission_ref": mission_ref,
            "lease_ref": lease.lease_ref,
        },
        headers={"x-uaa-idempotency-key": "attention-api-substitution-inspect"},
    ).json()["data"]
    response = client.post(
        "/control-center/today/exact-action/prepare",
        json={
            "workflow_ref": "founder-loop-attention-workflow:api-substitution",
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"][:-1],
            "source_review_receipt_ref": source_review["source_review_receipt_ref"],
            "mission_ref": mission_ref,
            "run_ref": "run-ref:attention-api:source-substitution",
            "lease_ref": lease.lease_ref,
            "start_deadline": (utc_now() + timedelta(minutes=10)).isoformat(),
        },
        headers={"x-uaa-idempotency-key": "attention-api-substitution"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "FOUNDER_LOOP_ATTENTION_SOURCE_BINDING_REQUIRED"
    )
    clear_founder_attention_workflow_cache()


def test_exact_action_source_review_requires_current_exact_mission_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder-loop"))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    clear_founder_attention_workflow_cache()
    status = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]

    response = client.post(
        "/control-center/today/exact-action/source-review",
        json={
            "today_item_ref": TODAY_ITEM_REF,
            "inspected_source_refs": status["required_inspected_source_refs"],
            "mission_ref": "mission-ref:attention-api:no-lease",
            "lease_ref": "authority-lease:attention-api:missing",
        },
        headers={"x-uaa-idempotency-key": "attention-api-no-lease"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED"
    )
    after = client.get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]
    assert after["workflow_status"] == "review_ready"
    assert not any(
        ref.startswith("source-review-receipt-ref:") for ref in after["receipt_refs"]
    )
    clear_founder_attention_workflow_cache()


def test_exact_action_routes_are_protected_and_exactly_classified() -> None:
    routes = {
        (route["method"], route["path"]): route
        for route in client.get("/api/manifest").json()["routes"]
    }
    status = routes[
        ("GET", "/control-center/today/exact-action/{today_item_ref}/status")
    ]
    assert status["operation_id"] == (
        "get_control_center_today_exact_action_today_item_ref_status"
    )
    assert status["route_classification"] == "local_sensitive"
    assert status["idempotency_required"] is False

    for path in (
        "/control-center/today/exact-action/prepare",
        "/control-center/today/exact-action/source-review",
        "/control-center/today/exact-action/approve",
        "/control-center/today/exact-action/execute",
    ):
        route = routes[("POST", path)]
        assert route["route_classification"] == "mutating_requires_authority"
        assert route["side_effect_class"] == "local_dev_workspace_only"
        assert route["idempotency_required"] is True
        assert route["rate_limit_group"] == "founder_loop_exact_action"


def test_exact_action_mutations_fail_before_handler_without_idempotency() -> None:
    response = client.post(
        "/control-center/today/exact-action/prepare",
        json={},
    )
    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
