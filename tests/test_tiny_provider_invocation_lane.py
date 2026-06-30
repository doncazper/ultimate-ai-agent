import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    DeterministicTinyProviderInvocationAdapter,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationReceipt,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderInvocationTransportReceipt,
    build_tiny_provider_invocation_approval_request,
    build_tiny_provider_invocation_readiness,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_PROVIDER_INVOCATION_ROUTE,
)


def invocation_request(**overrides: object) -> TinyProviderInvocationRequest:
    values: dict[str, object] = {
        "invocation_ref": "provider-invocation-ref:tiny:test",
        "run_id": "run-ref:tiny-provider-test",
        "provider_ref": TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "credential_ref": "credential-ref:openai-compatible:scoped-test",
        "policy_ref": TINY_PROVIDER_INVOCATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-runtime:tiny-test",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:tiny-test",
        "cost_estimate_ref": "cost-estimate-ref:provider-runtime:tiny-test",
        "budget_decision_ref": "budget-decision-ref:provider-runtime:tiny-test",
        "max_approved_usd_ref": "max-approved-usd-ref:provider-runtime:tiny-test",
        "max_approved_usd": 0.01,
        "idempotency_ref": "idempotency:provider-runtime:tiny-test",
        "expected_receipt_ref": "receipt:provider-runtime:tiny-test",
        "usage_receipt_ref": "usage-receipt-ref:provider-runtime:tiny-test",
        "cost_receipt_ref": "cost-receipt-ref:provider-runtime:tiny-test",
        "redacted_input_summary_ref": "redacted-input-summary-ref:provider-runtime:tiny-test",
        "redacted_output_summary_ref": "redacted-output-summary-ref:provider-runtime:tiny-test",
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-test",
        "estimated_input_tokens": 10,
        "estimated_output_tokens": 5,
        "estimated_cost_usd": 0.001,
    }
    values.update(overrides)
    return TinyProviderInvocationRequest(**values)


def exact_authority_for(
    request: TinyProviderInvocationRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_tiny_provider_invocation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def evaluate_with_exact_approval(
    request: TinyProviderInvocationRequest,
    **kwargs: object,
):
    return evaluate_tiny_provider_invocation(
        request,
        approval_authority=exact_authority_for(request),
        **kwargs,
    )


def receipt_payload(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "receipt_ref": "receipt:provider-runtime:tiny-test",
        "invocation_ref": "provider-invocation-ref:tiny:test",
        "run_id": "run-ref:tiny-provider-test",
        "provider_ref": TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "credential_ref": "credential-ref:openai-compatible:scoped-test",
        "approval_ref": "approval-ref:provider-runtime:tiny-test",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:tiny-test",
        "cost_estimate_ref": "cost-estimate-ref:provider-runtime:tiny-test",
        "budget_decision_ref": "budget-decision-ref:provider-runtime:tiny-test",
        "max_approved_usd_ref": "max-approved-usd-ref:provider-runtime:tiny-test",
        "expected_receipt_ref": "receipt:provider-runtime:tiny-test",
        "usage_receipt_ref": "usage-receipt-ref:provider-runtime:tiny-test",
        "cost_receipt_ref": "cost-receipt-ref:provider-runtime:tiny-test",
        "cost_governor_decision_ref": "cost-decision-ref:provider-runtime:tiny-test",
        "idempotency_ref": "idempotency:provider-runtime:tiny-test",
        "redacted_input_summary_ref": "redacted-input-summary-ref:provider-runtime:tiny-test",
        "redacted_output_summary_ref": "redacted-output-summary-ref:provider-runtime:tiny-test",
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-test",
        "status": TinyProviderInvocationStatus.receipt_recorded,
        "invocation_performed": True,
        "safe_summary": (
            "Tiny exact-approved provider lane recorded a redacted receipt using a scoped adapter."
        ),
    }
    values.update(overrides)
    return values


class OverBudgetTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    enabled = True

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=f"provider-transport-ref:tiny-provider:{request.invocation_ref.split(':')[-1]}",
            adapter_ref=self.adapter_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=(request.max_approved_usd or 0) + 0.01,
        )


def test_tiny_provider_lane_default_readiness_is_disabled_and_cost_governed() -> None:
    readiness = build_tiny_provider_invocation_readiness()

    assert readiness.status == TinyProviderInvocationStatus.disabled
    assert readiness.invocation_enabled is False
    assert readiness.provider_sdk_call_enabled is False
    assert readiness.network_call_enabled is False
    assert readiness.exact_approval_required is True
    assert readiness.unknown_paid_cost_blocks is True
    assert readiness.redacted_receipts_only is True
    assert "Cost blocked" in readiness.ui_states
    assert "No provider authority" in readiness.ui_states
    assert "Disabled no execution" in readiness.ui_states
    assert "Live adapter blocked" in readiness.ui_states
    assert "Live receipt required" in readiness.ui_states
    assert "Approved no execution" not in readiness.ui_states


def test_missing_provider_model_credential_cost_and_receipt_refs_block() -> None:
    cases = [
        ("provider_ref", "provider-ref:provider-runtime:not-bound", "blocked_missing_provider_ref"),
        ("model_ref", "model-ref:provider-runtime:not-bound", "blocked_missing_model_ref"),
        ("credential_ref", "credential-ref:provider-runtime:not-configured", "blocked_missing_credential_ref"),
        ("cost_estimate_ref", "cost-estimate-ref:provider-runtime:not-bound", "blocked_missing_cost_estimate_ref"),
        ("budget_decision_ref", "budget-decision-ref:provider-runtime:not-bound", "blocked_missing_budget_decision_ref"),
        ("max_approved_usd_ref", "max-approved-usd-ref:provider-runtime:not-bound", "blocked_missing_max_approved_usd"),
        ("expected_receipt_ref", "receipt-ref:provider-runtime:not-bound", "blocked_missing_expected_receipt_ref"),
    ]

    for field, value, expected_status in cases:
        decision = evaluate_tiny_provider_invocation(invocation_request(**{field: value}))
        assert decision.allowed is False
        assert decision.status == expected_status


def test_unknown_paid_cost_blocks_even_with_exact_approval() -> None:
    decision = evaluate_with_exact_approval(invocation_request(estimated_cost_usd=None))

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.unknown_paid_cost_blocked
    assert "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in decision.reason_codes


def test_estimated_cost_above_max_approved_usd_blocks() -> None:
    decision = evaluate_with_exact_approval(
        invocation_request(estimated_cost_usd=0.02, max_approved_usd=0.01)
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert "HARD_BUDGET_EXCEEDED" in decision.reason_codes


def test_policy_ref_must_match_validated_tiny_provider_policy() -> None:
    decision = evaluate_with_exact_approval(
        invocation_request(policy_ref="policy-ref:provider-runtime:wrong-scope")
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.blocked_missing_policy_validation
    assert "POLICY_REF_NOT_ALLOWED" in decision.reason_codes


def test_exact_approval_binds_numeric_cost_scope_before_adapter_execution() -> None:
    original = invocation_request(estimated_cost_usd=0.001, max_approved_usd=0.01)
    authority = exact_authority_for(original)
    elevated = original.model_copy(
        update={
            "estimated_cost_usd": 0.5,
            "max_approved_usd": 1.0,
        }
    )

    decision = evaluate_tiny_provider_invocation(
        elevated,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=authority,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.approval_invalid
    assert "APPROVAL_RESOURCE_NOT_GRANTED" in decision.reason_codes
    assert decision.receipt is None


def test_actual_adapter_cost_above_approved_budget_blocks_without_receipt() -> None:
    request = invocation_request(estimated_cost_usd=0.001, max_approved_usd=0.01)

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OverBudgetTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert "ACTUAL_USAGE_OR_COST_EXCEEDED_APPROVED_SCOPE" in decision.reason_codes
    assert decision.receipt is None


def test_exact_approval_is_required_before_adapter_execution() -> None:
    decision = evaluate_tiny_provider_invocation(invocation_request())

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.approval_required
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes


def test_default_adapter_remains_approved_no_execution_after_exact_approval() -> None:
    decision = evaluate_with_exact_approval(invocation_request())

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.approved_no_execution
    assert "TINY_PROVIDER_ADAPTER_DISABLED_BY_DEFAULT" in decision.reason_codes
    assert decision.receipt is None


def test_injected_adapter_records_only_redacted_receipt(tmp_path: Path) -> None:
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-provider-receipts.jsonl")
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:success")
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is True
    assert decision.status == TinyProviderInvocationStatus.receipt_recorded
    assert decision.receipt is not None
    assert decision.receipt.receipt_ref == "receipt:provider-runtime:tiny-test"
    assert decision.receipt.provider_sdk_used is False
    assert decision.receipt.network_call_performed is False
    assert decision.receipt.raw_prompt_persisted is False
    assert decision.receipt.raw_response_persisted is False
    assert decision.receipt.raw_provider_exchange_persisted is False
    persisted = store.list_receipts()
    assert len(persisted) == 1
    receipt_json = json.dumps(persisted[0].model_dump(mode="json"), sort_keys=True)
    assert "provider_payload" not in receipt_json
    assert "api_key" not in receipt_json.lower()
    assert "token=" not in receipt_json.lower()


def test_transport_receipt_requires_known_billed_cost() -> None:
    with pytest.raises(ValidationError):
        TinyProviderInvocationTransportReceipt(
            transport_ref="provider-transport-ref:tiny-provider:missing-cost",
            redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-test",
            usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-test",
            cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-test",
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=None,
        )


def test_transport_receipt_allows_network_only_as_scoped_adapter_metadata() -> None:
    receipt = TinyProviderInvocationTransportReceipt(
        transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
        redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-test",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-test",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-test",
        input_tokens_used=1,
        output_tokens_used=1,
        billed_cost_usd=0.001,
        network_call_performed=True,
        adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
    )

    assert receipt.network_call_performed is True
    assert receipt.provider_sdk_used is False
    assert receipt.raw_output_persisted is False


def test_transport_receipt_rejects_network_without_approved_transport_scope() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_TRANSPORT_NETWORK_SCOPE_DENIED",
    ):
        TinyProviderInvocationTransportReceipt(
            transport_ref="provider-transport-ref:tiny-live:unapproved",
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-test",
            usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-test",
            cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-test",
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )


def test_transport_receipt_rejects_unsafe_block_reason_text() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_TRANSPORT_BLOCK_REASON_UNSAFE",
    ):
        TinyProviderInvocationTransportReceipt(
            transport_ref="provider-transport-ref:tiny-provider:block",
            adapter_ref="provider-adapter-ref:tiny-exact-approved:generic",
            status="blocked",
            redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-test",
            usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-test",
            cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-test",
            input_tokens_used=0,
            output_tokens_used=0,
            billed_cost_usd=0.0,
            block_reason_code="raw provider error with token",
        )


def test_receipt_rejects_authority_or_raw_persistence_claims() -> None:
    base = evaluate_with_exact_approval(invocation_request())
    assert base.status == TinyProviderInvocationStatus.approved_no_execution
    with pytest.raises(ValidationError, match="TINY_PROVIDER_INVOCATION_RECEIPT_AUTHORITY_DENIED"):
        TinyProviderInvocationReceipt(**receipt_payload(provider_sdk_used=True))


def test_receipt_allows_scoped_network_flag_but_rejects_raw_persistence() -> None:
    receipt = TinyProviderInvocationReceipt(
        **receipt_payload(
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            network_call_performed=True,
        )
    )

    assert receipt.network_call_performed is True
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_AUTHORITY_DENIED",
    ):
        TinyProviderInvocationReceipt(**receipt_payload(raw_response_persisted=True))


def test_receipt_rejects_network_claim_without_scoped_live_adapter_ref() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_NETWORK_SCOPE_DENIED",
    ):
        TinyProviderInvocationReceipt(**receipt_payload(network_call_performed=True))


def test_receipt_rejects_freeform_safe_summary_text() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_SAFE_SUMMARY_DENIED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                safe_summary="A raw model answer or provider exchange could hide here."
            )
        )


def test_tiny_provider_route_is_mutating_idempotent_and_rate_limited() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    route = {
        (item["method"], item["path"]): item for item in manifest["routes"]
    }[("POST", TINY_PROVIDER_INVOCATION_ROUTE)]

    assert route["route_classification"] == "mutating_requires_authority"
    assert route["side_effect_class"] == "local_dev_workspace_only"
    assert route["idempotency_required"] is True
    assert route["rate_limit_group"] == "provider_exact_approved_lane"


def test_tiny_provider_route_rejects_missing_idempotency_before_handler() -> None:
    client = TestClient(app)

    response = client.post(
        TINY_PROVIDER_INVOCATION_ROUTE,
        json=invocation_request().model_dump(mode="json"),
    )

    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


def test_tiny_provider_route_defaults_to_no_execution_with_idempotency() -> None:
    client = TestClient(app)
    request = invocation_request()

    response = client.post(
        TINY_PROVIDER_INVOCATION_ROUTE,
        headers={"X-UAA-Idempotency-Key": request.idempotency_ref},
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "approval_required"
    assert payload["data"]["receipt"] is None
    evidence_refs = [item["evidence_ref"] for item in payload["evidence"]]
    assert request.expected_receipt_ref not in evidence_refs
    assert request.cost_estimate_ref in evidence_refs
    assert request.budget_decision_ref in evidence_refs


def test_client_supplied_approval_grants_are_not_accepted() -> None:
    values = invocation_request().model_dump(mode="json")
    values["approval_grants"] = []

    with pytest.raises(ValidationError):
        TinyProviderInvocationRequest(**values)


def test_request_rejects_spoofed_actor_context() -> None:
    values = invocation_request().model_dump(mode="json")
    values["actor_context"] = {
        "actor_type": "human_user",
        "actor_id": "operator:spoofed",
        "authority_source": "manual_operator_action",
    }

    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_REQUEST_ACTOR_CONTEXT_DENIED",
    ):
        TinyProviderInvocationRequest(**values)


def test_request_rejects_raw_text_in_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_REQUEST_UNSAFE_REF_REJECTED",
    ):
        invocation_request(
            redacted_input_summary_ref="raw prompt text should not persist"
        )


def test_request_rejects_local_path_shaped_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_REQUEST_UNSAFE_REF_REJECTED",
    ):
        invocation_request(credential_ref="credential-ref:/Users/example/.env")


def test_receipt_rejects_raw_text_in_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_UNSAFE_REF_REJECTED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                redacted_output_summary_ref="raw response text should not persist",
            )
        )
