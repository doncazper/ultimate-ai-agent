import json
from pathlib import Path

from pydantic import SecretStr, ValidationError
import pytest

from ultimate_ai_agent.core.providers import (
    SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
    SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
    SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderReceiptCompletenessStatus,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    AnthropicCompatibleTinyLiveProviderAdapter,
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveProviderTransportResult,
)
from ultimate_ai_agent.core.providers.invocation import (
    TinyProviderInvocationExecutionGrant,
)
from tests.tiny_provider_invocation_helpers import (
    LiveRefWithoutReceiptRequirementAdapter,
    SecondLiveRefWithoutReceiptRequirementAdapter,
    SpoofedNetworkTinyProviderInvocationAdapter,
    available_credential_resolution,
    available_second_credential_resolution,
    exact_authority_for,
    invocation_request,
    second_invocation_request,
)


def test_live_adapter_requires_receipt_store_before_network() -> None:
    request = invocation_request()
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
        ),
        approval_authority=exact_authority_for(request),
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIRED" in decision.reason_codes
    assert decision.receipt is None


def test_live_adapter_direct_execute_blocks_without_execution_grant() -> None:
    request = invocation_request()
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
        )

    receipt = OpenAICompatibleTinyLiveProviderAdapter(
        enabled=True,
        credential_resolver=lambda _credential_ref: available_credential_resolution(
            request
        ),
        transport=mocked_transport,
    ).execute(request)

    assert receipt.status == "blocked"
    assert receipt.block_reason_code == "TINY_LIVE_PROVIDER_EXECUTION_GRANT_REQUIRED"
    assert receipt.network_call_performed is False
    assert transport_called is False


def test_live_adapter_direct_execute_blocks_self_minted_execution_grant() -> None:
    request = invocation_request()
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
        )

    self_minted_grant = TinyProviderInvocationExecutionGrant(
        provider_ref=request.provider_ref,
        model_ref=request.model_ref,
        credential_ref=request.credential_ref,
        policy_ref=request.policy_ref,
        approval_ref=request.approval_ref,
        approval_scope_ref=request.approval_scope_ref,
        cost_estimate_ref=request.cost_estimate_ref,
        budget_decision_ref=request.budget_decision_ref,
        expected_receipt_ref=request.expected_receipt_ref,
        cost_governor_decision_ref="cost-decision-ref:self-minted-test",
        receipt_store_required=True,
    )

    receipt = OpenAICompatibleTinyLiveProviderAdapter(
        enabled=True,
        credential_resolver=lambda _credential_ref: available_credential_resolution(
            request
        ),
        transport=mocked_transport,
    ).execute(request, execution_grant=self_minted_grant)

    assert receipt.status == "blocked"
    assert (
        receipt.block_reason_code
        == "TINY_LIVE_PROVIDER_EXECUTION_GRANT_AUTHORITY_REQUIRED"
    )
    assert receipt.network_call_performed is False
    assert transport_called is False


def test_spoofed_network_adapter_cannot_claim_live_transport_scope(tmp_path: Path) -> None:
    request = invocation_request(idempotency_ref="idempotency:provider-runtime:spoofed-net")
    store = TinyProviderInvocationReceiptStore(tmp_path / "spoofed-net.jsonl")

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=SpoofedNetworkTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_PROVIDER_ADAPTER_SCOPE_MISMATCH" in decision.reason_codes
    assert decision.receipt is None
    assert store.list_receipts() == []


def test_live_network_adapter_must_require_receipt_store_before_network(
    tmp_path: Path,
) -> None:
    request = invocation_request(idempotency_ref="idempotency:provider-runtime:no-store-contract")
    store = TinyProviderInvocationReceiptStore(tmp_path / "no-store-contract.jsonl")

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=LiveRefWithoutReceiptRequirementAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIREMENT_REQUIRED" in decision.reason_codes
    assert decision.receipt is None
    assert store.list_receipts() == []


def test_second_live_network_adapter_must_require_receipt_store_before_network(
    tmp_path: Path,
) -> None:
    request = second_invocation_request(
        idempotency_ref="idempotency:provider-runtime:tiny-second-no-store-contract"
    )
    store = TinyProviderInvocationReceiptStore(
        tmp_path / "tiny-second-no-store-contract.jsonl"
    )
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=SecondLiveRefWithoutReceiptRequirementAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_second_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIREMENT_REQUIRED" in decision.reason_codes
    assert transport_called is False
    assert decision.receipt is None
    assert store.list_receipts() == []


def test_live_adapter_blocks_without_transient_secret_resolver(tmp_path: Path) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-provider-unused.jsonl")
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(enabled=True),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_SECRET_RESOLVER_REQUIRED" in decision.reason_codes
    assert decision.receipt is None


def test_live_adapter_blocks_unavailable_secret_ref_without_network(tmp_path: Path) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-provider-unused.jsonl")
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: None,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_CREDENTIAL_REF_NOT_AVAILABLE" in decision.reason_codes
    assert decision.receipt is not None
    assert decision.receipt.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert len(store.list_receipts()) == 1


def test_live_adapter_blocks_unapproved_provider_model_name(tmp_path: Path) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-model-block.jsonl")
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            provider_model_name="not-the-single-allowed-model",
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_MODEL_NAME_NOT_ALLOWLISTED" in decision.reason_codes
    assert decision.receipt is None


def test_live_adapter_blocks_cross_provider_endpoint_scope_before_transport(
    tmp_path: Path,
) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-cross-endpoint.jsonl")
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            endpoint_url=SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_ENDPOINT_NOT_ALLOWLISTED" in decision.reason_codes
    assert transport_called is False
    assert store.list_receipts() == []


def test_live_adapter_blocks_subclass_endpoint_allowlist_override_before_transport(
    tmp_path: Path,
) -> None:
    class EndpointOverrideAdapter(OpenAICompatibleTinyLiveProviderAdapter):
        allowed_endpoint_url = SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT

    request = invocation_request(
        idempotency_ref="idempotency:provider-runtime:subclass-endpoint-override",
        expected_receipt_ref="receipt:provider-runtime:subclass-endpoint-override",
    )
    store = TinyProviderInvocationReceiptStore(
        tmp_path / "tiny-subclass-endpoint-override.jsonl"
    )
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=EndpointOverrideAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_ENDPOINT_NOT_ALLOWLISTED" in decision.reason_codes
    assert transport_called is False
    assert store.list_receipts() == []


def test_live_adapter_preflight_exception_fails_closed_before_transport(
    tmp_path: Path,
) -> None:
    class PreflightRaisingAdapter(OpenAICompatibleTinyLiveProviderAdapter):
        def preflight_block_reason(
            self,
            request: TinyProviderInvocationRequest,
            *,
            execution_grant=None,
        ) -> str | None:
            raise RuntimeError("preflight failed")

    request = invocation_request(
        idempotency_ref="idempotency:provider-runtime:preflight-exception",
        expected_receipt_ref="receipt:provider-runtime:preflight-exception",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-preflight-exception.jsonl")
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=PreflightRaisingAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_PREFLIGHT_EXCEPTION_BLOCKED" in decision.reason_codes
    assert decision.receipt is None
    assert transport_called is False
    assert store.list_receipts() == []


def test_second_live_adapter_blocks_cross_provider_endpoint_scope_before_transport(
    tmp_path: Path,
) -> None:
    request = second_invocation_request()
    store = TinyProviderInvocationReceiptStore(
        tmp_path / "tiny-second-cross-endpoint.jsonl"
    )
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=AnthropicCompatibleTinyLiveProviderAdapter(
            enabled=True,
            endpoint_url=TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
            credential_resolver=lambda _credential_ref: available_second_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_ENDPOINT_NOT_ALLOWLISTED" in decision.reason_codes
    assert transport_called is False
    assert store.list_receipts() == []


def test_live_transport_result_rejects_unsafe_block_reason_text() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_LIVE_PROVIDER_TRANSPORT_BLOCK_REASON_UNSAFE",
    ):
        TinyLiveProviderTransportResult(
            status="blocked",
            block_reason_code="raw provider error with token",
        )


def test_live_adapter_records_network_receipt_with_mocked_transport(tmp_path: Path) -> None:
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:live-mock")
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-receipts.jsonl")

    def mocked_transport(
        transport_request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        assert transport_request.credential_ref == request.credential_ref
        assert credential.get_secret_value() == "transient-material"
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=transport_request.estimated_cost_usd or 0.0,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is True
    assert decision.status == TinyProviderInvocationStatus.receipt_recorded
    assert decision.receipt is not None
    assert decision.receipt.network_call_performed is True
    assert decision.receipt.actual_usage_captured is True
    assert decision.receipt.actual_cost_captured is True
    assert (
        decision.receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.complete
    )
    assert decision.receipt.actual_usage_ref.startswith("actual-usage-ref:")
    assert decision.receipt.actual_cost_ref.startswith("actual-cost-ref:")
    assert decision.receipt.provider_sdk_used is False
    assert decision.receipt.raw_prompt_persisted is False
    assert decision.receipt.raw_response_persisted is False
    assert decision.receipt.raw_provider_exchange_persisted is False
    persisted = store.list_receipts()
    assert len(persisted) == 1
    persisted_json = json.dumps(persisted[0].model_dump(mode="json"), sort_keys=True)
    assert "transient-material" not in persisted_json
    assert "provider_payload" not in persisted_json


def test_second_live_adapter_records_network_receipt_with_mocked_transport(
    tmp_path: Path,
) -> None:
    request = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:live-mock"
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-second-live.jsonl")

    def mocked_transport(
        transport_request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        assert transport_request.provider_ref == SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF
        assert transport_request.model_ref == SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF
        assert credential.get_secret_value() == "transient-material"
        return TinyLiveProviderTransportResult(
            transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=transport_request.estimated_cost_usd or 0.0,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=AnthropicCompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_second_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is True
    assert decision.status == TinyProviderInvocationStatus.receipt_recorded
    assert decision.receipt is not None
    assert decision.receipt.adapter_ref == SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF
    assert decision.receipt.provider_ref == SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF
    assert decision.receipt.model_ref == SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF
    assert decision.receipt.network_call_performed is True
    assert decision.receipt.provider_sdk_used is False
    assert decision.receipt.raw_prompt_persisted is False
    assert decision.receipt.raw_response_persisted is False
    assert decision.receipt.raw_provider_exchange_persisted is False
    persisted_json = json.dumps(store.list_receipts()[0].model_dump(mode="json"))
    assert "transient-material" not in persisted_json
    assert "provider_payload" not in persisted_json


def test_second_live_adapter_wrong_transport_ref_fails_closed_and_replays(
    tmp_path: Path,
) -> None:
    request = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:wrong-transport",
        idempotency_ref="idempotency:provider-runtime:tiny-second-wrong-transport",
        expected_receipt_ref="receipt:provider-runtime:tiny-second-wrong-transport",
    )
    store = TinyProviderInvocationReceiptStore(
        tmp_path / "tiny-second-wrong-transport.jsonl"
    )
    call_count = 0

    def wrong_transport(
        transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal call_count
        call_count += 1
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=transport_request.estimated_cost_usd or 0.0,
            network_call_performed=True,
        )

    adapter = AnthropicCompatibleTinyLiveProviderAdapter(
        enabled=True,
        credential_resolver=lambda _credential_ref: available_second_credential_resolution(
            request
        ),
        transport=wrong_transport,
    )
    first = evaluate_tiny_provider_invocation(
        request,
        adapter=adapter,
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )
    second = evaluate_tiny_provider_invocation(
        request,
        adapter=adapter,
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert first.allowed is False
    assert first.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_TRANSPORT_SCOPE_MISMATCH" in first.reason_codes
    assert first.receipt is not None
    assert first.receipt.network_call_performed is True
    assert len(store.list_receipts()) == 1
    assert second.allowed is False
    assert "IDEMPOTENCY_REPLAYED_RECEIPT" in second.reason_codes
    assert call_count == 1


def test_first_live_adapter_cannot_execute_second_provider_scope(
    tmp_path: Path,
) -> None:
    request = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:wrong-adapter",
        idempotency_ref="idempotency:provider-runtime:tiny-second-wrong-adapter",
        expected_receipt_ref="receipt:provider-runtime:tiny-second-wrong-adapter",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-second-wrong-adapter.jsonl")
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_second_credential_resolution(
                request
            ),
            transport=mocked_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_LIVE_PROVIDER_ADAPTER_SCOPE_MISMATCH" in decision.reason_codes
    assert transport_called is False
    assert store.list_receipts() == []
