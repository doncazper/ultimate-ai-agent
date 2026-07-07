from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts import verify_fcc_v1_006_evidence_timeline_productization as verifier
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.storage import (
    EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF,
    EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES,
    FRONTIER_AI_COST_USAGE_CONTRACT_REF,
    FounderLoopEvidenceTimelineEvent,
    FounderLoopRepository,
    OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS,
    OPERATOR_RUN_TIMELINE_CONTRACT_REF,
    OPERATOR_RUN_TIMELINE_STATES,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (
    ReadOnlyHttpFetchTransportResponse,
)
from tests.authority_helpers import issue_workspace_write_authority_lease


def _history_answers(ref: str) -> dict:
    return {
        key: {
            "question": question,
            "answer": answer,
            "refs": [ref],
            "status": "present",
        }
        for key, question, answer in [
            ("proposed", "What was proposed?", "A safe-ref proposal was recorded."),
            ("approved", "What was approved?", "Only identifier refs were recorded."),
            ("happened", "What happened?", "A receipt ref was captured."),
            ("changed", "What changed?", "A review projection changed."),
            ("undoable", "What can be undone?", "Rollback remains inspection-only."),
            ("stale", "What is stale?", "Refs must be rechecked."),
            ("blocked", "What remains blocked?", "Execution remains blocked."),
        ]
    }


def _safe_event(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "event_ref": "evidence-event:test-action",
        "event_type": "action_decision_recorded",
        "event_type_ref": "evidence-event-type:action_decision_recorded",
        "group_kind": "action",
        "group_ref": "founder-action:test",
        "group_label": "Action decision receipt",
        "timeline_item_ref": "evidence-timeline:action/founder-action/test",
        "item_kind": "receipt_audit_rollback_ref",
        "title": "Action decision",
        "safe_summary": "Action decision receipt uses safe refs only.",
        "history_answers": _history_answers("founder-action:test"),
        "source_refs": ["founder-action:test"],
        "status_refs": ["status-ref:founder-loop-action-inbox"],
        "related_route_refs": ["GET /control-center/evidence/timeline"],
        "receipt_refs": ["receipt:founder-loop-action:test:reject:key"],
        "approval_refs": ["approval-status:refs-identifiers-only"],
        "idempotency_refs": ["idempotency-ref:test"],
        "audit_refs": ["audit:founder-loop-action:test:reject:key"],
        "rollback_refs": [],
        "rollback_blockers": ["rollback_execution_not_scoped"],
        "blocked_states": ["blocked-state:no-action-execution"],
        "rollback_posture": "rollback_not_applicable_or_not_scoped",
        "authority_posture": "Evidence event is safe-ref metadata only.",
    }
    payload.update(overrides)
    return payload


def _approve_local_task_seed_action() -> dict[str, object]:
    repo = FounderLoopRepository.from_env()
    receipt = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:fcc-v1-006-local-task-approval",
        ),
        idempotency_key_ref="idempotency-ref:fcc-v1-006-local-task-action",
    )
    assert receipt["status"] == "approved"
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def _local_task_commit_body(action: dict[str, object]) -> dict[str, object]:
    request = FounderLoopLocalTaskCommitRequest(
        approval_ref=str(action["local_task_commit_approval_ref"]),
        decision_reason_ref="decision-reason-ref:fcc-v1-006-local-task-commit",
        metadata_refs=["metadata-ref:fcc-v1-006-local-task-commit"],
    )
    return request.model_dump(mode="json")


def _fake_web_evidence_transport(
    _request: Any,
    _policy: Any,
) -> ReadOnlyHttpFetchTransportResponse:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"Public status page for timeline verification.",
    )


_fake_web_evidence_transport.transport_ref = (
    "http-fetch-transport:fake-fcc-v1-006-web-evidence"
)
_fake_web_evidence_transport.real_world_transport_performed = True


def _browser_read_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:fcc-v1-006-web-evidence",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        constraints={
            "web_evidence_lane_ref": "lane-ref:web-evidence-product-slice",
            "https_get_only": True,
            "browser_actions_allowed": False,
        },
        safe_summary=(
            "Test lease grants Browser read authority for one safe-ref "
            "web evidence timeline seed."
        ),
    )


def _record_web_evidence_seed() -> str:
    repo = FounderLoopRepository.from_env()
    previous_allowlist = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV)
    os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = "example.org"
    try:
        receipt = build_web_evidence_product_slice_receipt(
            WebEvidenceProductSliceRequest(
                request_ref="web-evidence-request:fcc-v1-006",
                url="https://example.org/status",
                allowed_host="example.org",
                evidence_refs=["evidence-ref:fcc-v1-006-web-evidence"],
                metadata_refs=["metadata-ref:fcc-v1-006-web-evidence"],
            ),
            transport=_fake_web_evidence_transport,
            active_authority_leases=[_browser_read_lease()],
        )
    finally:
        if previous_allowlist is None:
            os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, None)
        else:
            os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = previous_allowlist
    repo.record_web_evidence_attachment(receipt)
    return receipt.receipt_ref


def test_evidence_timeline_event_model_accepts_safe_event() -> None:
    event = FounderLoopEvidenceTimelineEvent(**_safe_event())

    assert event.event_type == "action_decision_recorded"
    assert event.approval_ref_authority is False
    assert event.rollback_execution_enabled is False
    assert event.context_injection_authorized is False
    assert event.raw_evidence_included is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"safe_summary": "raw prompt content should fail"},
        {"raw_evidence_included": True},
        {"approval_ref_authority": True},
        {"rollback_execution_enabled": True},
        {"memory_truth_authority": True},
        {"context_injection_authorized": True},
    ],
)
def test_evidence_timeline_event_model_rejects_unsafe_authority(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((ValidationError, ValueError)):
        FounderLoopEvidenceTimelineEvent(**_safe_event(**overrides))


def test_evidence_timeline_route_productizes_founder_loop_receipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    issue_workspace_write_authority_lease(authority_state_dir)
    client = TestClient(app)

    action_items = client.get("/control-center/actions/inbox").json()["data"]["items"]
    action_item = next(
        item
        for item in action_items
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    action_response = client.post(
        f"/control-center/actions/{action_item['item_ref']}/reject",
        json={
            "decision_reason_ref": "decision-reason-ref:fcc-v1-006-action",
            "metadata_refs": ["metadata-ref:fcc-v1-006-action"],
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-action"},
    )
    assert action_response.status_code == 200

    chat_response = client.post(
        "/control-center/chat/turns",
        json={
            "turn_ref": "chat-turn:fcc-v1-006",
            "route_ref": "/v1/chat/completions",
            "model_ref": "model-ref:fcc-v1-006-local",
            "runtime_truth": "local-chat-route-answered",
            "auth_truth": "local-bearer-accepted",
            "tool_denial_truth": "tools-functions-streaming-denied",
            "safe_summary_ref": "safe-summary-ref:fcc-v1-006-chat",
            "evidence_refs": ["evidence-ref:fcc-v1-006-chat"],
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-chat"},
    )
    assert chat_response.status_code == 200
    handoff_response = client.post(
        "/control-center/chat/turns/chat-turn:fcc-v1-006/handoff",
        json={"handoff_target": "actions"},
        headers={"x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-handoff"},
    )
    assert handoff_response.status_code == 200

    candidate_ref = (
        client.get("/control-center/memory/review")
        .json()["data"]["items"][0]["business_memory_candidate_ref"]
    )
    memory_response = client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json={
            "reviewer_ref": "actor-ref:fcc-v1-006-memory",
            "source_refs": ["source-ref:fcc-v1-006-memory"],
            "evidence_refs": ["evidence-ref:fcc-v1-006-memory"],
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-memory"},
    )
    assert memory_response.status_code == 200

    local_task_action = _approve_local_task_seed_action()
    local_task_response = client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json=_local_task_commit_body(local_task_action),
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-local-task-commit"
        },
    )
    assert local_task_response.status_code == 200
    web_evidence_receipt_ref = _record_web_evidence_seed()

    response = client.get("/control-center/evidence/timeline")
    assert response.status_code == 200
    body = response.json()
    assert body["operation"] == "control_center_evidence_timeline"
    assert "safe_refs_only" in body["redactions_applied"]

    data = body["data"]
    assert data["contract_ref"] == EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF
    assert data["safe_refs_only"] is True
    assert data["raw_content_stored"] is False
    assert data["approval_ref_authority"] is False
    assert data["rollback_execution_enabled"] is False
    assert data["context_injection_authorized"] is False
    assert data["action_execution_enabled"] is False
    assert data["production_authority_enabled"] is False
    assert set(data["event_types"]) == set(EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES)
    assert "local_task_created" in data["event_types"]
    for event_type in EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES:
        assert data["event_type_counts"][event_type] >= 1
    assert {"today_item", "action", "chat_turn", "memory_candidate"}.issubset(
        {group["group_kind"] for group in data["groups"]}
    )
    assert action_response.json()["data"]["receipt_ref"] in str(data["events"])
    assert local_task_response.json()["data"]["receipt_ref"] in str(data["events"])
    assert web_evidence_receipt_ref in str(data["events"])
    assert chat_response.json()["data"]["receipt_ref"] in str(data["events"])
    assert handoff_response.json()["data"]["receipt_ref"] in str(data["events"])
    assert memory_response.json()["data"]["receipt_ref"] in str(data["events"])
    operator_run_timeline = data["operator_run_timeline"]
    assert operator_run_timeline["contract_ref"] == OPERATOR_RUN_TIMELINE_CONTRACT_REF
    assert (
        operator_run_timeline["status"]
        == "implemented_read_only_operator_run_timeline_safe_refs_only"
    )
    assert operator_run_timeline["source"] == "python_core_evidence_timeline_read_model"
    assert operator_run_timeline["route_ref"] == "GET /control-center/evidence/timeline"
    assert operator_run_timeline["safe_refs_only"] is True
    assert operator_run_timeline["action_execution_enabled"] is False
    assert operator_run_timeline["connector_write_enabled"] is False
    assert operator_run_timeline["runtime_model_calls_enabled"] is False
    assert operator_run_timeline["provider_sdk_call_enabled"] is False
    assert operator_run_timeline["provider_model_authority_allowed"] is False
    assert operator_run_timeline["prompt_content_stored"] is False
    assert operator_run_timeline["response_content_stored"] is False
    assert operator_run_timeline["provider_exchange_content_stored"] is False
    assert operator_run_timeline["event_count"] == len(data["events"])
    assert {
        pattern["pattern_id"]
        for pattern in operator_run_timeline["borrowed_patterns"]
    } == {
        pattern["pattern_id"] for pattern in OPERATOR_RUN_TIMELINE_BORROWED_PATTERNS
    }
    assert set(operator_run_timeline["run_control_summary"]["states"]) == set(
        OPERATOR_RUN_TIMELINE_STATES
    )
    assert (
        operator_run_timeline["run_control_summary"]["receipt_recorded_count"] >= 1
    )
    assert {
        event["event_source"] for event in operator_run_timeline["run_events"]
    } == {"python_core_evidence_timeline"}
    assert {
        event["llm_role_projection"] for event in operator_run_timeline["run_events"]
    } == {"not_sent_to_model"}
    assert any(
        event["completion_state"] == "evidence_refs_present"
        for event in operator_run_timeline["run_events"]
    )
    first_cost_slot = operator_run_timeline["run_events"][0]["cost_usage"]
    assert first_cost_slot["contract_ref"] == FRONTIER_AI_COST_USAGE_CONTRACT_REF
    assert first_cost_slot["provider_ref"] == "provider-ref:not-invoked"
    assert first_cost_slot["model_profile_ref"] == "model-profile-ref:not-invoked"
    assert first_cost_slot["estimated_cost_usd"] == 0.0
    assert first_cost_slot["captured_cost_usd"] == 0.0
    assert first_cost_slot["approval_required_for_unknown_paid_cost"] is True
    frontier_ai_usage = operator_run_timeline["frontier_ai_usage_summary"]
    assert frontier_ai_usage["contract_ref"] == FRONTIER_AI_COST_USAGE_CONTRACT_REF
    assert frontier_ai_usage["status"] == "accounting_slots_ready_no_provider_calls"
    assert frontier_ai_usage["provider_model_authority_allowed"] is False
    assert frontier_ai_usage["provider_sdk_call_enabled"] is False
    assert frontier_ai_usage["runtime_model_calls_enabled"] is False
    assert frontier_ai_usage["prompt_content_stored"] is False
    assert frontier_ai_usage["response_content_stored"] is False
    assert frontier_ai_usage["provider_exchange_content_stored"] is False
    assert frontier_ai_usage["estimated_total_cost_usd"] == 0.0
    assert frontier_ai_usage["captured_total_cost_usd"] == 0.0
    assert frontier_ai_usage["unknown_paid_cost_requires_approval_before_routing"] is True
    assert (
        frontier_ai_usage["budget_status_ref"]
        == "budget-status:unknown-paid-cost-requires-approval"
    )
    assert "raw prompt" not in str(data).lower()
    assert "provider_payload" not in str(data).lower()


def test_fcc_v1_006_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []
