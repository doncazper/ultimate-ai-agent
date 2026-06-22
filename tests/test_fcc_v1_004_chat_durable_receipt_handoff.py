from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from scripts.verification.repo import load_json
from scripts.verify_fcc_v1_004_chat_durable_receipt_handoff import (
    FOUNDER_LOOP_V1_PROOF_REF,
    RELEASE_SURFACE_PATH,
    ROUTE_STATUS_PATH,
    MILESTONE_STATUS_PATH,
    verify,
)
from ultimate_ai_agent.core.chat import (
    CHAT_DURABLE_RECEIPT_CONTRACT_REF,
    CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS,
    ChatHandoffReceipt,
    ChatHandoffRequest,
    ChatTurnReceipt,
    ChatTurnReceiptRequest,
)


def test_fcc_v1_004_verifier_passes() -> None:
    assert verify() == []


def test_chat_receipt_request_rejects_raw_private_content() -> None:
    with pytest.raises(ValidationError):
        ChatTurnReceiptRequest(
            turn_ref="chat-turn:test",
            route_ref="/v1/chat/completions",
            model_ref="model-ref:test",
            runtime_truth="raw prompt visible",
            auth_truth="local-bearer-accepted",
            tool_denial_truth="tools-functions-streaming-denied",
            safe_summary_ref="safe-summary-ref:test",
        )


def test_chat_receipt_rejects_denied_authority_flags() -> None:
    with pytest.raises(ValidationError):
        ChatTurnReceipt(
            contract_ref=CHAT_DURABLE_RECEIPT_CONTRACT_REF,
            turn_ref="chat-turn:test",
            route_ref="/v1/chat/completions",
            model_ref="model-ref:test",
            runtime_truth="local-chat-route-answered",
            auth_truth="local-bearer-accepted",
            tool_denial_truth="tools-functions-streaming-denied",
            safe_summary_ref="safe-summary-ref:test",
            handoff_refs=[
                "handoff-ref:chat-to-actions:test",
                "handoff-ref:chat-to-plans:test",
            ],
            receipt_ref="receipt:chat-turn:test",
            evidence_ref="evidence-ref:chat-turn:test",
            idempotency_key_ref="idempotency-ref:test",
            payload_fingerprint_ref="payload-fingerprint:chat:test",
            blocked_state_refs=list(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS),
            action_execution_enabled=True,
        )


def test_chat_handoff_rejects_password_or_credential_refs() -> None:
    with pytest.raises(ValidationError):
        ChatHandoffRequest(
            handoff_target="actions",
            decision_reason_ref="decision-reason-ref:password",
        )


def test_chat_handoff_receipt_rejects_execution_flags() -> None:
    with pytest.raises(ValidationError):
        ChatHandoffReceipt(
            contract_ref=CHAT_DURABLE_RECEIPT_CONTRACT_REF,
            turn_ref="chat-turn:test",
            handoff_target="actions",
            handoff_ref="handoff-ref:chat-to-actions:test",
            created_ref="founder-action:chat-handoff:test",
            receipt_ref="receipt:chat-handoff:test",
            audit_ref="audit:chat-handoff:test",
            evidence_ref="evidence-ref:chat-handoff:test",
            idempotency_key_ref="idempotency-ref:test",
            payload_fingerprint_ref="payload-fingerprint:chat:test",
            safe_summary_ref="safe-summary-ref:test",
            blocked_state_refs=["blocked-state:no-action-execution"],
            action_executed=True,
        )


def test_verifier_flags_release_surface_missing_chat_handoff_route() -> None:
    release_surface = deepcopy(load_json(RELEASE_SURFACE_PATH))
    chat = next(route for route in release_surface["routes"] if route["path"] == "/chat")
    chat["backend_routes"] = [
        route
        for route in chat["backend_routes"]
        if route.get("path") != "/control-center/chat/turns/{turn_ref}/handoff"
    ]

    failures = verify(
        release_surface=release_surface,
        route_status=load_json(ROUTE_STATUS_PATH),
        milestone_status=load_json(MILESTONE_STATUS_PATH),
        check_behavior=False,
        check_files=False,
    )

    assert any("/chat missing route" in failure for failure in failures)


def test_verifier_flags_milestone_status_drift() -> None:
    milestone_status = deepcopy(load_json(MILESTONE_STATUS_PATH))
    milestone = next(
        item for item in milestone_status["milestones"] if item["id"] == "FCC-V1-004"
    )
    milestone["status"] = "planned"

    failures = verify(
        release_surface=load_json(RELEASE_SURFACE_PATH),
        route_status=load_json(ROUTE_STATUS_PATH),
        milestone_status=milestone_status,
        check_behavior=False,
        check_files=False,
    )

    assert "FCC-V1-004 milestone status must be implemented" in failures


def test_verifier_flags_chat_release_overclaim() -> None:
    release_surface = deepcopy(load_json(RELEASE_SURFACE_PATH))
    chat = next(route for route in release_surface["routes"] if route["path"] == "/chat")
    chat["status"] = "ship"
    chat["proof_lanes"] = [
        proof for proof in chat["proof_lanes"] if proof != FOUNDER_LOOP_V1_PROOF_REF
    ]

    failures = verify(
        release_surface=release_surface,
        route_status=load_json(ROUTE_STATUS_PATH),
        milestone_status=load_json(MILESTONE_STATUS_PATH),
        check_behavior=False,
        check_files=False,
    )

    assert "/chat ship status requires FCC-V1-007 proof lane" in failures
