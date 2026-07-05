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
    chat_turn_harness_binding_receipt_summary,
)
from ultimate_ai_agent.core.decision_router import build_turn_harness_binding


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


def test_chat_receipt_records_safe_turn_harness_binding_refs_only() -> None:
    binding = build_turn_harness_binding(
        "Find current lumber prices near me.",
        binding_ref="turn-harness-binding:chat-receipt-test",
        decision_ref="turn-decision:chat-receipt-test",
    )
    request = ChatTurnReceiptRequest(
        turn_ref="chat-turn:test-router-binding",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:test",
        runtime_truth="local-chat-route-answered",
        auth_truth="local-bearer-accepted",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref="safe-summary-ref:test",
        turn_harness_binding=binding,
    )
    receipt = ChatTurnReceipt(
        contract_ref=CHAT_DURABLE_RECEIPT_CONTRACT_REF,
        turn_ref="chat-turn:test-router-binding",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:test",
        runtime_truth=request.runtime_truth,
        auth_truth=request.auth_truth,
        tool_denial_truth=request.tool_denial_truth,
        safe_summary_ref=request.safe_summary_ref,
        turn_harness_binding=chat_turn_harness_binding_receipt_summary(
            request.turn_harness_binding
        ),
        handoff_refs=[
            "handoff-ref:chat-to-actions:test-router-binding",
            "handoff-ref:chat-to-plans:test-router-binding",
        ],
        receipt_ref="receipt:chat-turn:test-router-binding",
        evidence_ref="evidence-ref:chat-turn:test-router-binding",
        idempotency_key_ref="idempotency-ref:test-router-binding",
        payload_fingerprint_ref="payload-fingerprint:chat:test-router-binding",
        blocked_state_refs=list(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS),
    )

    payload = receipt.model_dump(mode="json")
    assert payload["turn_harness_binding"]["turn_contract"] == "prepare_tool_or_action"
    assert payload["turn_harness_binding"]["tool_policy"] == "read_only_or_proposal_only"
    assert payload["turn_harness_binding"]["execution_tools_exposed_count"] == 0
    assert (
        payload["turn_harness_binding"]["no_effect_scope"]
        == "turn_harness_binding_compilation_only"
    )
    assert payload["turn_harness_binding"]["prompt_body_persisted"] is False
    assert "current lumber prices" not in repr(payload).lower()


def test_chat_receipt_accepts_router_credential_privacy_safe_ref() -> None:
    binding = build_turn_harness_binding(
        "Review my account privacy boundary.",
        binding_ref="turn-harness-binding:chat-receipt-privacy-boundary",
        decision_ref="turn-decision:chat-receipt-privacy-boundary",
    )
    request = ChatTurnReceiptRequest(
        turn_ref="chat-turn:test-privacy-boundary",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:test",
        runtime_truth="local-chat-route-answered",
        auth_truth="local-bearer-accepted",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref="safe-summary-ref:test",
        turn_harness_binding=binding,
    )
    summary = chat_turn_harness_binding_receipt_summary(
        request.turn_harness_binding
    )

    assert summary is not None
    assert summary.turn_contract == "approval_required"
    assert (
        "reason-ref:turn-contract:credential-account-privacy-boundary"
        in summary.reason_refs
    )
    assert "credential_or_payment" in summary.risk_flags
    assert summary.no_effect_scope == "turn_harness_binding_compilation_only"
    assert summary.no_action_execution_performed is True


def test_chat_receipt_rejects_unsafe_turn_harness_binding_payload() -> None:
    binding = build_turn_harness_binding(
        "How do I build a DIY table?",
        binding_ref="turn-harness-binding:unsafe-chat-receipt-test",
        decision_ref="turn-decision:unsafe-chat-receipt-test",
    ).model_dump(mode="json")
    binding["raw_prompt_persisted"] = True

    with pytest.raises(ValidationError):
        ChatTurnReceiptRequest(
            turn_ref="chat-turn:test",
            route_ref="/v1/chat/completions",
            model_ref="model-ref:test",
            runtime_truth="local-chat-route-answered",
            auth_truth="local-bearer-accepted",
            tool_denial_truth="tools-functions-streaming-denied",
            safe_summary_ref="safe-summary-ref:test",
            turn_harness_binding=binding,
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
