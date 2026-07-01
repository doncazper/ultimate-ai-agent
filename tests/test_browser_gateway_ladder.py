from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.web_access import (
    BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS,
    BROWSER_GATEWAY_LADDER_STATES,
    BrowserGatewayBlockedReceipt,
    BrowserGatewayExactApprovalBinding,
    BrowserGatewayIntentMetadata,
    BrowserGatewayLadderState,
    BrowserGatewayLadderStepContract,
    BrowserGatewayRiskClass,
    build_browser_gateway_blocked_receipt,
    build_browser_gateway_intent_metadata,
    build_browser_gateway_ladder_contract,
    build_browser_gateway_replay_audit_record,
    evaluate_browser_gateway_exact_approval_binding,
)


def _binding(**overrides: object) -> BrowserGatewayExactApprovalBinding:
    payload = {
        "approval_ref": "approval-ref:browser:test",
        "intent_ref": "browser-intent-ref:test",
        "action_plan_ref": "browser-action-plan-ref:test",
        "policy_decision_ref": "policy-decision-ref:browser:test",
        "scope_ref": "scope-ref:browser:test",
        "expires_ref": "expires-ref:browser:test",
        "expected_receipt_ref": "receipt-ref:browser:test",
        "revocation_ref": "revocation-ref:browser:test",
    }
    payload.update(overrides)
    return BrowserGatewayExactApprovalBinding(**payload)


def test_browser_gateway_ladder_states_are_ordered_and_non_executing() -> None:
    contract = build_browser_gateway_ladder_contract()

    assert BROWSER_GATEWAY_LADDER_STATES == (
        "declared",
        "discovered",
        "metadata_only",
        "observe_planned",
        "observe_blocked",
        "action_dry_run_planned",
        "action_dry_run_blocked",
        "exact_approved_low_risk_action_planned",
        "high_risk_action_blocked",
        "auth_cookie_download_upload_blocked",
        "mutation_blocked",
        "runtime_disabled",
    )
    assert tuple(step.state.value for step in contract.steps) == BROWSER_GATEWAY_LADDER_STATES
    assert tuple(step.sequence for step in contract.steps) == tuple(range(1, 13))
    assert all(step.web_access_gateway_required is True for step in contract.steps)
    assert all(step.exact_approval_required_before_execution is True for step in contract.steps)
    assert all(step.live_web_fetch_allowed is False for step in contract.steps)
    assert all(step.live_browser_observe_allowed is False for step in contract.steps)
    assert all(step.live_browser_execution_allowed is False for step in contract.steps)
    assert all(step.browser_click_allowed is False for step in contract.steps)
    assert all(step.browser_form_fill_allowed is False for step in contract.steps)
    assert all(step.browser_auth_cookie_allowed is False for step in contract.steps)
    assert all(step.browser_download_upload_allowed is False for step in contract.steps)
    assert all(step.browser_mutation_allowed is False for step in contract.steps)
    assert all(step.raw_page_payload_persistence_allowed is False for step in contract.steps)
    assert all(step.provider_model_authority_allowed is False for step in contract.steps)
    assert all(step.control_center_authority_allowed is False for step in contract.steps)

    with pytest.raises((ValidationError, ValueError)):
        contract.steps[0].model_copy(update={"live_browser_execution_allowed": True})

    with pytest.raises((ValidationError, ValueError)):
        BrowserGatewayLadderStepContract(
            sequence=1,
            state=BrowserGatewayLadderState.DECLARED,
            operator_posture="declared",
            risk_class=BrowserGatewayRiskClass.METADATA,
            safe_mode="Browser capability is named only.",
            blocked_authority_refs=(),
        )


def test_browser_gateway_intent_metadata_uses_safe_refs_and_not_raw_page_payloads() -> None:
    metadata = build_browser_gateway_intent_metadata(
        intent_ref="browser-intent-ref:test",
        requested_state=BrowserGatewayLadderState.OBSERVE_PLANNED,
        risk_class=BrowserGatewayRiskClass.OBSERVE,
        source_ref="source-ref:browser:test",
        safe_url_ref="browser-url-ref:example-page",
        audit_ref="audit-ref:browser:test",
        replay_ref="replay-ref:browser:test",
        revocation_ref="revocation-ref:browser:test",
        safe_disable_ref="safe-disable-ref:browser:test",
    )

    assert metadata.web_access_gateway_required is True
    assert metadata.web_content_instruction_use_allowed is False
    assert metadata.model_output_authority_allowed is False
    assert metadata.provider_output_authority_allowed is False
    assert metadata.control_center_state_authority_allowed is False
    assert metadata.live_browser_execution_allowed is False
    assert metadata.raw_page_payload_persistence_allowed is False

    with pytest.raises((ValidationError, ValueError)):
        build_browser_gateway_intent_metadata(
            intent_ref="browser-intent-ref:raw-url",
            requested_state=BrowserGatewayLadderState.OBSERVE_PLANNED,
            risk_class=BrowserGatewayRiskClass.OBSERVE,
            source_ref="source-ref:browser:test",
            safe_url_ref="https://example.com/private",
            audit_ref="audit-ref:browser:test",
            replay_ref="replay-ref:browser:test",
            revocation_ref="revocation-ref:browser:test",
            safe_disable_ref="safe-disable-ref:browser:test",
        )

    with pytest.raises((ValidationError, ValueError)):
        BrowserGatewayIntentMetadata(
            intent_ref="browser-intent-ref:test",
            requested_state=BrowserGatewayLadderState.MUTATION_BLOCKED,
            risk_class=BrowserGatewayRiskClass.OBSERVE,
            source_ref="source-ref:browser:test",
            audit_ref="audit-ref:browser:test",
            replay_ref="replay-ref:browser:test",
            revocation_ref="revocation-ref:browser:test",
            safe_disable_ref="safe-disable-ref:browser:test",
        )


def test_browser_gateway_exact_approval_binding_blocks_mismatched_refs() -> None:
    binding = _binding()

    matched = evaluate_browser_gateway_exact_approval_binding(
        binding,
        requested_intent_ref="browser-intent-ref:test",
        requested_state=BrowserGatewayLadderState.EXACT_APPROVED_LOW_RISK_ACTION_PLANNED,
        requested_action_plan_ref="browser-action-plan-ref:test",
        policy_decision_ref="policy-decision-ref:browser:test",
    )

    assert matched.approval_binding_valid is True
    assert matched.status.value == "approval_bound"
    assert matched.execution_authorized is False
    assert matched.live_browser_execution_allowed is False
    assert matched.model_output_authority_allowed is False
    assert matched.provider_output_authority_allowed is False
    assert matched.control_center_state_authority_allowed is False

    blocked = evaluate_browser_gateway_exact_approval_binding(
        binding,
        requested_intent_ref="browser-intent-ref:other",
        requested_state=BrowserGatewayLadderState.EXACT_APPROVED_LOW_RISK_ACTION_PLANNED,
        requested_action_plan_ref="browser-action-plan-ref:test",
        policy_decision_ref="policy-decision-ref:browser:test",
    )

    assert blocked.approval_binding_valid is False
    assert blocked.status.value == "blocked"
    assert "BROWSER_GATEWAY_INTENT_REF_MISMATCH" in blocked.reason_codes
    assert blocked.execution_authorized is False

    with pytest.raises((ValidationError, ValueError)):
        _binding(live_browser_execution_allowed=True)

    with pytest.raises((ValidationError, ValueError)):
        _binding(
            allowed_state=BrowserGatewayLadderState.HIGH_RISK_ACTION_BLOCKED,
            risk_class=BrowserGatewayRiskClass.HIGH_RISK_ACTION,
        )


def test_browser_gateway_blocked_receipt_and_replay_are_safe_ref_only() -> None:
    receipt = build_browser_gateway_blocked_receipt(
        receipt_ref="receipt-ref:browser:test",
        intent_ref="browser-intent-ref:test",
        requested_state=BrowserGatewayLadderState.ACTION_DRY_RUN_BLOCKED,
        reason_codes=("BROWSER_GATEWAY_DRY_RUN_BLOCKED",),
        safe_summary="Blocked browser action plan with redacted refs only.",
        redacted_page_ref="redacted-page-ref:browser:test",
        redacted_source_ref="redacted-source-ref:browser:test",
        policy_decision_ref="policy-decision-ref:browser:test",
        audit_ref="audit-ref:browser:test",
        replay_ref="replay-ref:browser:test",
        revocation_ref="revocation-ref:browser:test",
        safe_disable_ref="safe-disable-ref:browser:test",
        approval_missing_ref="approval-missing-ref:browser:test",
    )

    assert isinstance(receipt, BrowserGatewayBlockedReceipt)
    assert receipt.status == "blocked"
    assert receipt.observe_performed is False
    assert receipt.dry_run_executed is False
    assert receipt.click_performed is False
    assert receipt.form_submitted is False
    assert receipt.auth_cookie_accessed is False
    assert receipt.download_upload_performed is False
    assert receipt.mutation_performed is False
    assert receipt.provider_model_called is False
    assert receipt.connector_write_performed is False
    assert receipt.raw_page_payload_persisted is False
    assert tuple(receipt.blocked_authority_refs) == BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS

    replay = build_browser_gateway_replay_audit_record(
        replay_ref="replay-ref:browser:test",
        intent_ref="browser-intent-ref:test",
        policy_decision_ref="policy-decision-ref:browser:test",
        approval_decision_ref="approval-decision-ref:browser:test",
        receipt_ref="receipt-ref:browser:test",
        revocation_ref="revocation-ref:browser:test",
        reason_codes=("BROWSER_GATEWAY_DRY_RUN_BLOCKED",),
    )

    assert replay.reconstructable_from_safe_refs is True
    assert replay.reexecution_allowed is False
    assert replay.raw_page_payload_available is False
    assert replay.model_provider_ui_authority_allowed is False

    with pytest.raises((ValidationError, ValueError)):
        receipt.model_copy(update={"click_performed": True})

    with pytest.raises((ValidationError, ValueError)):
        build_browser_gateway_blocked_receipt(
            receipt_ref="receipt-ref:browser:raw",
            intent_ref="browser-intent-ref:raw",
            requested_state=BrowserGatewayLadderState.OBSERVE_BLOCKED,
            reason_codes=("BROWSER_GATEWAY_OBSERVE_BLOCKED",),
            safe_summary="Blocked raw page payload from https://example.com.",
            redacted_page_ref="redacted-page-ref:browser:test",
            redacted_source_ref="redacted-source-ref:browser:test",
            policy_decision_ref="policy-decision-ref:browser:test",
            audit_ref="audit-ref:browser:test",
            replay_ref="replay-ref:browser:test",
            revocation_ref="revocation-ref:browser:test",
            safe_disable_ref="safe-disable-ref:browser:test",
        )
