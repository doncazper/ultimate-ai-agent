import json
import os
from pathlib import Path

from pydantic import SecretStr, ValidationError
import pytest

import ultimate_ai_agent.core.providers.live_invocation_adapter as live_adapter_module
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderReceiptCompletenessStatus,
    TinyProviderInvocationTransportReceipt,
    build_tiny_provider_invocation_approval_request,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveCredentialResolution,
    TinyLiveProviderTransportResult,
)
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TinyProviderInvocationExecutionGrant,
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


def test_live_adapter_actual_cost_over_budget_records_blocked_receipt(
    tmp_path: Path,
) -> None:
    request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:live-over-budget",
        idempotency_ref="idempotency:provider-runtime:tiny-live-over-budget",
        expected_receipt_ref="receipt:provider-runtime:tiny-live-over-budget",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-live-over-budget",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-live-over-budget",
        estimated_cost_usd=0.001,
        max_approved_usd=0.01,
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-live-over-budget.jsonl")

    def over_budget_transport(
        transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=0.02,
            network_call_performed=True,
        )

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: available_credential_resolution(
                request
            ),
            transport=over_budget_transport,
        ),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt is not None
    assert decision.receipt.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt.network_call_performed is True
    assert (
        decision.receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.complete
    )
    assert "REDACTED_BLOCKED_ATTEMPT_RECEIPT_RECORDED" in decision.receipt.reason_codes
    assert len(store.list_receipts()) == 1


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


def test_live_stdlib_transport_uses_no_redirect_opener() -> None:
    source = Path(
        "src/ultimate_ai_agent/core/providers/live_invocation_adapter.py"
    ).read_text(encoding="utf-8")

    assert "_NO_REDIRECT_OPENER.open" in source
    assert "urllib_request.urlopen" not in source
    assert "billed_cost_usd=request.estimated_cost_usd" not in source


def test_live_stdlib_transport_blocks_when_billed_cost_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"usage": {"input_tokens": 11, "output_tokens": 4}}
            ).encode("utf-8")

    class FakeNoRedirectOpener:
        def open(self, _request: object, *, timeout: float) -> FakeResponse:
            assert timeout > 0
            return FakeResponse()

    monkeypatch.setattr(
        live_adapter_module,
        "_NO_REDIRECT_OPENER",
        FakeNoRedirectOpener(),
    )

    result = OpenAICompatibleTinyLiveProviderAdapter(
        enabled=True
    )._stdlib_responses_transport(
        invocation_request(),
        SecretStr("transient-material"),
    )

    assert result.status == "blocked"
    assert result.block_reason_code == "TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE"
    assert result.input_tokens_used == 11
    assert result.output_tokens_used == 4
    assert result.billed_cost_usd == 0.0
    assert result.network_call_performed is True


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
