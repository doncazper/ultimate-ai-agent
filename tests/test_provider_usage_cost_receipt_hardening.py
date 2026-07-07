import json
from pathlib import Path

from pydantic import SecretStr

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.providers import (
    TINY_LIVE_PROVIDER_ADAPTER_REF,
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
    authority.issue_authority_lease(
        AuthorityLease(
            lease_ref="authority-lease-ref:provider-model-calls-execute-hardening",
            mode=TrustMode.full_machine_access_session,
            domains={
                AuthorityDomain.provider_model_calls: [
                    AuthorityCapability.read,
                    AuthorityCapability.execute,
                ]
            },
            constraints={
                "provider_lane_ref": "provider-invocation-lane:tiny-exact-approved:v1"
            },
            safe_summary=(
                "Test lease grants exact provider model call execution for "
                "provider receipt hardening checks."
            ),
        )
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


def safe_suffix(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")
    return normalized[-48:] or "local"


def stored_receipt_payload(
    request: TinyProviderInvocationRequest,
    **overrides: object,
) -> dict[str, object]:
    values: dict[str, object] = {
        "receipt_ref": request.expected_receipt_ref,
        "invocation_ref": request.invocation_ref,
        "run_id": request.run_id,
        "provider_ref": request.provider_ref,
        "model_ref": request.model_ref,
        "adapter_ref": TINY_LIVE_PROVIDER_ADAPTER_REF,
        "credential_ref": request.credential_ref,
        "approval_ref": request.approval_ref,
        "approval_scope_ref": request.approval_scope_ref,
        "cost_estimate_ref": request.cost_estimate_ref,
        "budget_decision_ref": request.budget_decision_ref,
        "max_approved_usd_ref": request.max_approved_usd_ref,
        "expected_receipt_ref": request.expected_receipt_ref,
        "usage_receipt_ref": request.usage_receipt_ref,
        "cost_receipt_ref": request.cost_receipt_ref,
        "cost_governor_decision_ref": "cost-decision-ref:provider-runtime:tiny-test",
        "estimated_cost_ref": request.cost_estimate_ref,
        "actual_usage_ref": (
            f"actual-usage-ref:provider-runtime:{safe_suffix(request.usage_receipt_ref)}"
        ),
        "actual_cost_ref": (
            f"actual-cost-ref:provider-runtime:{safe_suffix(request.cost_receipt_ref)}"
        ),
        "idempotency_ref": request.idempotency_ref,
        "redacted_input_summary_ref": request.redacted_input_summary_ref,
        "redacted_output_summary_ref": request.redacted_output_summary_ref,
        "safe_disable_ref": request.safe_disable_ref,
        "status": TinyProviderInvocationStatus.receipt_recorded,
        "invocation_performed": True,
        "network_call_performed": True,
        "input_tokens_used": request.estimated_input_tokens,
        "output_tokens_used": request.estimated_output_tokens,
        "estimated_cost_usd": request.estimated_cost_usd,
        "billed_cost_usd": request.estimated_cost_usd,
        "actual_usage_captured": True,
        "actual_cost_captured": True,
        "receipt_completeness_status": TinyProviderReceiptCompletenessStatus.complete,
        "incomplete_cost_requires_review": False,
        "further_provider_use_blocked": False,
        "reason_codes": ["REDACTED_RECEIPT_RECORDED"],
        "safe_summary": (
            "Tiny exact-approved provider lane recorded a redacted receipt using a scoped adapter."
        ),
    }
    values.update(overrides)
    return values


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


def test_replayed_complete_network_receipt_with_zero_cost_fails_closed(
    tmp_path: Path,
) -> None:
    request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:replayed-zero-cost",
        idempotency_ref="idempotency:provider-runtime:replayed-zero-cost",
        expected_receipt_ref="receipt:provider-runtime:replayed-zero-cost",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:replayed-zero-cost",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:replayed-zero-cost",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "replayed-zero-cost.jsonl")
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text(
        json.dumps(
            stored_receipt_payload(
                request,
                billed_cost_usd=0.0,
            )
        )
        + "\n",
        encoding="utf-8",
    )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt is not None
    assert decision.receipt.status == TinyProviderInvocationStatus.cost_blocked
    assert "REPLAYED_RECEIPT_ACTUAL_COST_MISSING" in decision.receipt.reason_codes
    assert "FURTHER_PROVIDER_USE_BLOCKED" in decision.reason_codes
