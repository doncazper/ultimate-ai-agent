from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pydantic import SecretStr, ValidationError
import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    ExactApprovedProviderFallbackAttempt,
    ExactApprovedProviderFallbackRequest,
    ExactApprovedProviderFallbackStatus,
    SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    build_tiny_provider_invocation_approval_request,
    evaluate_exact_approved_provider_fallback,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    AnthropicCompatibleTinyLiveProviderAdapter,
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveProviderTransportResult,
)
from tests.tiny_provider_invocation_helpers import (
    available_credential_resolution,
    available_second_credential_resolution,
    invocation_request,
    second_invocation_request,
)


def _authority_for(
    *requests: TinyProviderInvocationRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    for request in requests:
        approval_request = build_tiny_provider_invocation_approval_request(request)
        authority.create_request(approval_request)
        authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id="operator:local",
            approval_ref=request.approval_ref,
        )
    return authority


def _fallback_request(
    first: TinyProviderInvocationRequest,
    second: TinyProviderInvocationRequest,
) -> ExactApprovedProviderFallbackRequest:
    return ExactApprovedProviderFallbackRequest(
        fallback_run_ref="provider-fallback-run-ref:exact-approved:test",
        idempotency_ref="idempotency-ref:provider-fallback:exact-approved:test",
        attempts=[
            ExactApprovedProviderFallbackAttempt(
                attempt_ref="provider-fallback-attempt-ref:exact-approved:first",
                sequence_index=1,
                request=first,
            ),
            ExactApprovedProviderFallbackAttempt(
                attempt_ref="provider-fallback-attempt-ref:exact-approved:second",
                sequence_index=2,
                request=second,
            ),
        ],
    )


def _success_transport(
    request: TinyProviderInvocationRequest,
    _credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    return TinyLiveProviderTransportResult(
        transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
        input_tokens_used=request.estimated_input_tokens,
        output_tokens_used=request.estimated_output_tokens,
        billed_cost_usd=request.estimated_cost_usd or 0.0,
        network_call_performed=True,
    )


def _second_success_transport(
    request: TinyProviderInvocationRequest,
    _credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    return TinyLiveProviderTransportResult(
        transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
        input_tokens_used=request.estimated_input_tokens,
        output_tokens_used=request.estimated_output_tokens,
        billed_cost_usd=request.estimated_cost_usd or 0.0,
        network_call_performed=True,
    )


def test_fallback_requires_durable_receipt_store_before_any_attempt() -> None:
    first = invocation_request()
    second = second_invocation_request()
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter()
            ),
        },
        approval_authority=_authority_for(first, second),
    )

    assert decision.allowed is False
    assert (
        decision.status
        == ExactApprovedProviderFallbackStatus.blocked_missing_receipt_store
    )
    assert decision.attempt_results == []
    assert "FALLBACK_DURABLE_RECEIPT_STORE_REQUIRED" in decision.reason_codes


def test_fallback_stops_on_first_successful_complete_receipt(tmp_path: Path) -> None:
    first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-first"
    )
    second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:fallback-second"
    )
    second_called = False

    def second_transport(
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal second_called
        second_called = True
        return _second_success_transport(request, credential)

    store = TinyProviderInvocationReceiptStore(tmp_path / "fallback-success.jsonl")
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: available_credential_resolution(first),
                transport=_success_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(second)
                    ),
                    transport=second_transport,
                )
            ),
        },
        approval_authority=_authority_for(first, second),
        receipt_store=store,
    )

    assert decision.allowed is True
    assert decision.status == ExactApprovedProviderFallbackStatus.receipt_recorded
    assert decision.selected_provider_ref == TINY_PROVIDER_INVOCATION_PROVIDER_REF
    assert decision.selected_receipt_ref == first.expected_receipt_ref
    assert len(decision.attempt_results) == 1
    assert second_called is False
    assert len(store.list_receipts()) == 1


def test_fallback_can_try_second_after_first_safe_blocked_receipt(
    tmp_path: Path,
) -> None:
    first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-first-no-secret",
        idempotency_ref="idempotency:provider-runtime:fallback-first-no-secret",
        expected_receipt_ref="receipt:provider-runtime:fallback-first-no-secret",
    )
    second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:fallback-second-success",
        idempotency_ref="idempotency:provider-runtime:fallback-second-success",
        expected_receipt_ref="receipt:provider-runtime:fallback-second-success",
    )
    second_called = False

    def second_transport(
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal second_called
        second_called = True
        return _second_success_transport(request, credential)

    store = TinyProviderInvocationReceiptStore(tmp_path / "fallback-second.jsonl")
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: None,
                transport=_success_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(second)
                    ),
                    transport=second_transport,
                )
            ),
        },
        approval_authority=_authority_for(first, second),
        receipt_store=store,
    )

    assert decision.allowed is True
    assert (
        decision.selected_provider_ref == SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF
    )
    assert decision.selected_receipt_ref == second.expected_receipt_ref
    assert len(decision.attempt_results) == 2
    assert decision.attempt_results[0].allowed is False
    assert decision.attempt_results[0].receipt_ref == first.expected_receipt_ref
    assert second_called is True
    assert len(store.list_receipts()) == 2


def test_fallback_blocks_unknown_paid_cost_without_next_attempt(
    tmp_path: Path,
) -> None:
    first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-unknown-cost",
        estimated_cost_usd=None,
    )
    second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:should-not-run"
    )
    second_called = False

    def second_transport(
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal second_called
        second_called = True
        return _second_success_transport(request, credential)

    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: available_credential_resolution(first),
                transport=_success_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(second)
                    ),
                    transport=second_transport,
                )
            ),
        },
        approval_authority=_authority_for(first, second),
        receipt_store=TinyProviderInvocationReceiptStore(
            tmp_path / "fallback-unknown-cost.jsonl"
        ),
    )

    assert decision.allowed is False
    assert (
        decision.status
        == ExactApprovedProviderFallbackStatus.blocked_missing_attempt_receipt
    )
    assert len(decision.attempt_results) == 1
    assert decision.attempt_results[0].status == (
        TinyProviderInvocationStatus.unknown_paid_cost_blocked
    )
    assert "UNKNOWN_PAID_COST_BLOCKS" in decision.reason_codes
    assert second_called is False


def test_fallback_blocks_incomplete_cost_receipt_without_next_attempt(
    tmp_path: Path,
) -> None:
    first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-incomplete-cost",
        idempotency_ref="idempotency:provider-runtime:fallback-incomplete-cost",
        expected_receipt_ref="receipt:provider-runtime:fallback-incomplete-cost",
    )
    second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:should-not-run-incomplete"
    )
    second_called = False

    def incomplete_cost_transport(
        request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            status="blocked",
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=0.0,
            network_call_performed=True,
            block_reason_code="TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE",
        )

    def second_transport(
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        nonlocal second_called
        second_called = True
        return _second_success_transport(request, credential)

    store = TinyProviderInvocationReceiptStore(
        tmp_path / "fallback-incomplete-cost.jsonl"
    )
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: available_credential_resolution(first),
                transport=incomplete_cost_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(second)
                    ),
                    transport=second_transport,
                )
            ),
        },
        approval_authority=_authority_for(first, second),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert (
        decision.status
        == ExactApprovedProviderFallbackStatus.blocked_incomplete_attempt_receipt
    )
    assert len(decision.attempt_results) == 1
    assert decision.attempt_results[0].incomplete_cost_requires_review is True
    assert decision.attempt_results[0].further_provider_use_blocked is True
    assert "INCOMPLETE_COST_OR_USAGE_BLOCKS_FURTHER_FALLBACK" in decision.reason_codes
    assert second_called is False
    assert len(store.list_receipts()) == 1


def test_fallback_does_not_attribute_prior_blocking_receipt_to_new_attempt(
    tmp_path: Path,
) -> None:
    prior_first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-prior-incomplete-cost",
        idempotency_ref="idempotency:provider-runtime:fallback-prior-incomplete-cost",
        expected_receipt_ref="receipt:provider-runtime:fallback-prior-incomplete-cost",
    )
    prior_second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:fallback-prior-second"
    )
    current_first = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:fallback-current-after-prior",
        idempotency_ref="idempotency:provider-runtime:fallback-current-after-prior",
        expected_receipt_ref="receipt:provider-runtime:fallback-current-after-prior",
    )
    current_second = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:fallback-current-second"
    )

    def incomplete_cost_transport(
        request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            status="blocked",
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=0.0,
            network_call_performed=True,
            block_reason_code="TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE",
        )

    store = TinyProviderInvocationReceiptStore(tmp_path / "fallback-prior-block.jsonl")
    prior_decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(prior_first, prior_second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: available_credential_resolution(
                    prior_first
                ),
                transport=incomplete_cost_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(prior_second)
                    ),
                    transport=_second_success_transport,
                )
            ),
        },
        approval_authority=_authority_for(prior_first, prior_second),
        receipt_store=store,
    )
    assert (
        prior_decision.status
        == ExactApprovedProviderFallbackStatus.blocked_incomplete_attempt_receipt
    )

    current_decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(current_first, current_second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _ref: available_credential_resolution(
                    current_first
                ),
                transport=_success_transport,
            ),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter(
                    enabled=True,
                    credential_resolver=lambda _ref: (
                        available_second_credential_resolution(current_second)
                    ),
                    transport=_second_success_transport,
                )
            ),
        },
        approval_authority=_authority_for(current_first, current_second),
        receipt_store=store,
    )

    assert current_decision.allowed is False
    assert (
        current_decision.status
        == ExactApprovedProviderFallbackStatus.blocked_incomplete_attempt_receipt
    )
    assert "PRIOR_BLOCKING_RECEIPT_REQUIRES_REVIEW" in current_decision.reason_codes
    assert len(current_decision.attempt_results) == 1
    current_result = current_decision.attempt_results[0]
    assert current_result.expected_receipt_ref == current_first.expected_receipt_ref
    assert current_result.receipt_ref is None
    assert current_result.prior_blocking_receipt_ref == prior_first.expected_receipt_ref
    assert current_result.prior_blocking_receipt_requires_review is True


def test_fallback_requires_exactly_two_proven_adapter_scopes(tmp_path: Path) -> None:
    first = invocation_request()
    second = second_invocation_request()
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter()
        },
        approval_authority=_authority_for(first, second),
        receipt_store=TinyProviderInvocationReceiptStore(
            tmp_path / "fallback-adapter-scope.jsonl"
        ),
    )

    assert decision.allowed is False
    assert decision.status == ExactApprovedProviderFallbackStatus.blocked_adapter_scope
    assert "FALLBACK_REQUIRES_EXACTLY_TWO_PROVEN_ADAPTERS" in decision.reason_codes


def test_fallback_rejects_duplicate_attempt_refs() -> None:
    first = invocation_request()
    second = second_invocation_request()

    with pytest.raises(
        ValidationError,
        match="EXACT_APPROVED_PROVIDER_FALLBACK_PER_ATTEMPT_SCOPE_REQUIRED:attempt_ref",
    ):
        ExactApprovedProviderFallbackRequest(
            fallback_run_ref="provider-fallback-run-ref:exact-approved:test",
            idempotency_ref="idempotency-ref:provider-fallback:exact-approved:test",
            attempts=[
                ExactApprovedProviderFallbackAttempt(
                    attempt_ref="provider-fallback-attempt-ref:duplicate",
                    sequence_index=1,
                    request=first,
                ),
                ExactApprovedProviderFallbackAttempt(
                    attempt_ref="provider-fallback-attempt-ref:duplicate",
                    sequence_index=2,
                    request=second,
                ),
            ],
        )


def test_fallback_rejects_duplicate_per_attempt_receipt_scope() -> None:
    first = invocation_request()
    second = second_invocation_request(expected_receipt_ref=first.expected_receipt_ref)

    with pytest.raises(
        ValidationError,
        match="EXACT_APPROVED_PROVIDER_FALLBACK_PER_ATTEMPT_SCOPE_REQUIRED",
    ):
        _fallback_request(first, second)


def test_fallback_decision_rejects_raw_or_authority_claims() -> None:
    first = invocation_request()
    second = second_invocation_request()
    decision = evaluate_exact_approved_provider_fallback(
        _fallback_request(first, second),
        adapters_by_provider_ref=None,
    )

    with pytest.raises(
        ValidationError,
        match="EXACT_APPROVED_PROVIDER_FALLBACK_AUTHORITY_DENIED",
    ):
        decision.model_copy(update={"billing_authority_granted": True})


def test_fallback_cli_inspection_outputs_safe_schema() -> None:
    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/inspect_exact_approved_provider_fallback.py",
            "--fallback-run-ref",
            "provider-fallback-run-ref:exact-approved:test-cli",
            "--idempotency-ref",
            "idempotency-ref:provider-fallback:exact-approved:test-cli",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["contract_ref"].startswith("provider-fallback-contract-ref:")
    assert data["fallback_limited_to_two_adapters"] is True
    assert data["per_attempt_scope_required"] is True
    assert data["unknown_paid_cost_blocks"] is True
    assert data["billing_authority_granted"] is False
    assert data["raw_prompt_persisted"] is False
    assert data["raw_response_persisted"] is False
    assert data["provider_payload_persisted"] is False
    assert "provider_exchange" not in result.stdout.lower()
    assert "sk-" not in result.stdout.lower()
