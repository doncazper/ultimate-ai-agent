from pathlib import Path

from pydantic import SecretStr

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderReceiptCompletenessStatus,
    build_tiny_provider_invocation_approval_request,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveCredentialResolution,
    TinyLiveProviderTransportResult,
)
from ultimate_ai_agent.core.secrets.vault_contracts import ProviderCredentialVaultPosture


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


def exact_authority_for(request: TinyProviderInvocationRequest) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_tiny_provider_invocation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def available_credential_resolution(
    request: TinyProviderInvocationRequest,
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:openai-compatible:tiny-test",
        vault_record_ref="credential-vault-record-ref:openai-compatible:tiny-test",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr("transient-material"),
    )


def test_live_adapter_network_failure_records_incomplete_cost_receipt(
    tmp_path: Path,
) -> None:
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:live-blocked")
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-blocked.jsonl")

    def blocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            status="blocked",
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            network_call_performed=True,
            block_reason_code="TINY_LIVE_PROVIDER_HTTP_503_BLOCKED",
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=blocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert decision.receipt is not None
    assert (
        decision.receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
    )
    assert decision.receipt.incomplete_cost_requires_review is True
    assert decision.receipt.further_provider_use_blocked is True
    assert len(store.list_receipts()) == 1


def test_live_adapter_cost_unavailable_blocks_next_use(tmp_path: Path) -> None:
    request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:live-cost-incomplete",
        idempotency_ref="idempotency:provider-runtime:tiny-live-cost-incomplete",
        expected_receipt_ref="receipt:provider-runtime:tiny-live-cost-incomplete",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-live-cost-incomplete",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-live-cost-incomplete",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-cost-incomplete.jsonl")

    def incomplete_cost_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            status="blocked",
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=8,
            output_tokens_used=3,
            network_call_performed=True,
            block_reason_code="TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE",
        )

    first = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=incomplete_cost_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )
    next_request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:live-after-incomplete",
        idempotency_ref="idempotency:provider-runtime:tiny-live-after-incomplete",
        expected_receipt_ref="receipt:provider-runtime:tiny-live-after-incomplete",
    )
    second = evaluate_tiny_provider_invocation(
        next_request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                next_request
            ),
            transport=incomplete_cost_transport,
        ),
        approval_authority=exact_authority_for(next_request),
        receipt_store=store,
    )

    assert first.receipt is not None
    assert first.receipt.actual_usage_captured is True
    assert first.receipt.actual_cost_captured is False
    assert "ACTUAL_COST_INCOMPLETE" in first.receipt.reason_codes
    assert second.allowed is False
    assert second.status == TinyProviderInvocationStatus.cost_blocked
    assert second.receipt == first.receipt
    assert "FURTHER_PROVIDER_USE_BLOCKED" in second.reason_codes


def test_live_adapter_zero_actual_cost_success_fails_closed(tmp_path: Path) -> None:
    request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:live-zero-cost-success",
        idempotency_ref="idempotency:provider-runtime:tiny-live-zero-cost-success",
        expected_receipt_ref="receipt:provider-runtime:tiny-live-zero-cost-success",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-live-zero-cost-success",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-live-zero-cost-success",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-zero-cost.jsonl")

    def zero_cost_success_transport(
        transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=0.0,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=zero_cost_success_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt is not None
    assert decision.receipt.actual_usage_captured is True
    assert decision.receipt.actual_cost_captured is False
    assert (
        decision.receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
    )
    assert "ACTUAL_PROVIDER_COST_INCOMPLETE" in decision.reason_codes
