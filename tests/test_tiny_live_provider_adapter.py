import json
import os
from pathlib import Path

from pydantic import SecretStr
import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    OpenAICompatibleTinyLiveProviderAdapter,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyLiveCredentialResolution,
    TinyLiveProviderTransportResult,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderInvocationTransportReceipt,
    build_tiny_provider_invocation_approval_request,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
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


def available_credential_resolution(
    request: TinyProviderInvocationRequest,
    *,
    secret_value: str = "transient-material",
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:openai-compatible:tiny-test",
        vault_record_ref="credential-vault-record-ref:openai-compatible:tiny-test",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr(secret_value),
    )


class SpoofedNetworkTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    adapter_ref = "provider-adapter-ref:tiny-exact-approved:spoofed"
    enabled = True

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=request.estimated_cost_usd,
            network_call_performed=True,
        )


class LiveRefWithoutReceiptRequirementAdapter(TinyProviderInvocationAdapter):
    adapter_ref = TINY_LIVE_PROVIDER_ADAPTER_REF
    enabled = True
    may_perform_network_call = True
    requires_receipt_store_before_network = False

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            adapter_ref=self.adapter_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=request.estimated_cost_usd,
            network_call_performed=True,
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
    assert "TINY_PROVIDER_TRANSPORT_ADAPTER_REF_MISMATCH" in decision.reason_codes
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
    assert decision.receipt is None


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
    assert decision.receipt.provider_sdk_used is False
    assert decision.receipt.raw_prompt_persisted is False
    assert decision.receipt.raw_response_persisted is False
    assert decision.receipt.raw_provider_exchange_persisted is False
    persisted = store.list_receipts()
    assert len(persisted) == 1
    persisted_json = json.dumps(persisted[0].model_dump(mode="json"), sort_keys=True)
    assert "transient-material" not in persisted_json
    assert "provider_payload" not in persisted_json


def test_live_adapter_replays_existing_receipt_before_second_network_call(
    tmp_path: Path,
) -> None:
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:live-replay")
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-replay.jsonl")
    call_count = 0

    def mocked_transport(
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

    adapter = OpenAICompatibleTinyLiveProviderAdapter(
        enabled=True,
        credential_resolver=lambda _credential_ref: available_credential_resolution(request),
        transport=mocked_transport,
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

    assert first.allowed is True
    assert second.allowed is True
    assert call_count == 1
    assert "IDEMPOTENCY_REPLAYED_RECEIPT" in second.reason_codes


def test_live_adapter_network_failure_records_blocked_attempt_receipt(
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
    assert decision.receipt.network_call_performed is True
    assert decision.receipt.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "REDACTED_BLOCKED_ATTEMPT_RECEIPT_RECORDED" in decision.receipt.reason_codes
    assert len(store.list_receipts()) == 1


def test_live_adapter_blocks_revoked_or_rotation_required_credentials(
    tmp_path: Path,
) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-credential-block.jsonl")
    for posture, reason_code in (
        (
            ProviderCredentialVaultPosture.secret_ref_revoked,
            "TINY_LIVE_PROVIDER_CREDENTIAL_REF_REVOKED",
        ),
        (
            ProviderCredentialVaultPosture.rotation_required,
            "TINY_LIVE_PROVIDER_CREDENTIAL_ROTATION_REQUIRED",
        ),
    ):
        resolution = TinyLiveCredentialResolution(
            credential_ref=request.credential_ref,
            secret_ref=f"secret-ref:openai-compatible:{posture.value}",
            vault_record_ref=f"credential-vault-record-ref:openai-compatible:{posture.value}",
            posture=posture,
        )
        decision = evaluate_tiny_provider_invocation(
            request,
            adapter=OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _credential_ref, resolution=resolution: resolution,
            ),
            approval_authority=exact_authority_for(request),
            receipt_store=store,
        )

        assert decision.allowed is False
        assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
        assert reason_code in decision.reason_codes


def test_live_adapter_unknown_paid_cost_blocks_before_transport() -> None:
    request = invocation_request(estimated_cost_usd=None)
    transport_called = False

    def mocked_transport(
        _transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal transport_called
        transport_called = True
        return TinyLiveProviderTransportResult(
            transport_ref="provider-transport-ref:tiny-live:should-not-run",
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
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
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.unknown_paid_cost_blocked
    assert transport_called is False


@pytest.mark.skipif(
    os.environ.get("UAA_TINY_LIVE_PROVIDER_REAL_NETWORK") != "1"
    or not os.environ.get("UAA_TINY_LIVE_PROVIDER_TRANSIENT_CREDENTIAL"),
    reason="real provider invocation is skipped unless explicit local env is configured",
)
def test_live_adapter_optional_real_network_path_is_exact_approved(tmp_path: Path) -> None:
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:real-network")
    credential = os.environ["UAA_TINY_LIVE_PROVIDER_TRANSIENT_CREDENTIAL"]
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-real-network.jsonl")

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request,
                secret_value=credential,
            ),
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.status in {
        TinyProviderInvocationStatus.receipt_recorded,
        TinyProviderInvocationStatus.live_adapter_blocked,
    }
