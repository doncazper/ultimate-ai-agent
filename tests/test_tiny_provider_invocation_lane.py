import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.providers import (
    DeterministicTinyProviderInvocationAdapter,
    SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
    SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF,
    SECOND_TINY_LIVE_PROVIDER_MODEL_NAME_REF,
    SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_ENDPOINT_REF,
    TINY_LIVE_PROVIDER_MODEL_NAME_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationReceipt,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderInvocationTransportReceipt,
    TinyProviderReceiptCompletenessStatus,
    build_tiny_provider_invocation_readiness,
    evaluate_tiny_provider_invocation,
    required_provider_invocation_resource_refs,
)
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_PROVIDER_INVOCATION_ROUTE,
)
from tests.tiny_provider_invocation_helpers import (
    OverBudgetTinyProviderInvocationAdapter,
    exact_approval_only_authority_for,
    exact_authority_for,
    evaluate_with_exact_approval,
    invocation_request,
    provider_model_execute_lease,
    receipt_payload,
    second_invocation_request,
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
    assert readiness.receipt_state_source == "no_receipt_observed"
    assert readiness.provider_scope_refs == [
        TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    ]
    assert readiness.model_scope_refs == [
        TINY_PROVIDER_INVOCATION_MODEL_REF,
        SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    ]
    assert readiness.policy_scope_refs == [
        TINY_PROVIDER_INVOCATION_POLICY_REF,
        SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    ]
    assert readiness.adapter_scope_refs == [
        TINY_LIVE_PROVIDER_ADAPTER_REF,
        SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
    ]
    assert readiness.usage_captured is False
    assert readiness.cost_captured is False
    assert readiness.cost_incomplete is False
    assert readiness.review_required is False
    assert readiness.further_use_blocked is False
    assert "Cost blocked" in readiness.ui_states
    assert "No provider authority" in readiness.ui_states
    assert "Disabled no execution" in readiness.ui_states
    assert "Live adapter blocked" in readiness.ui_states
    assert "Live receipt required" in readiness.ui_states
    assert "Usage captured" not in readiness.ui_states
    assert "Usage captured" in readiness.receipt_observation_supported_states
    assert "Cost incomplete" in readiness.receipt_observation_supported_states
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


def test_second_provider_scope_requires_its_exact_model_and_policy() -> None:
    wrong_model = evaluate_with_exact_approval(
        second_invocation_request(model_ref=TINY_PROVIDER_INVOCATION_MODEL_REF)
    )
    wrong_policy = evaluate_with_exact_approval(
        second_invocation_request(policy_ref=TINY_PROVIDER_INVOCATION_POLICY_REF)
    )

    assert wrong_model.allowed is False
    assert wrong_model.status == TinyProviderInvocationStatus.blocked_model_not_allowed
    assert "MODEL_REF_NOT_ALLOWED" in wrong_model.reason_codes
    assert wrong_policy.allowed is False
    assert (
        wrong_policy.status
        == TinyProviderInvocationStatus.blocked_missing_policy_validation
    )
    assert "POLICY_REF_NOT_ALLOWED" in wrong_policy.reason_codes


def test_second_provider_scope_rejects_unscoped_deterministic_receipt(
    tmp_path: Path,
) -> None:
    request = second_invocation_request(
        invocation_ref="provider-invocation-ref:tiny-second:deterministic",
        idempotency_ref="idempotency:provider-runtime:tiny-second-deterministic",
        expected_receipt_ref="receipt:provider-runtime:tiny-second-deterministic",
    )
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-second-receipts.jsonl")

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_PROVIDER_ADAPTER_SCOPE_MISMATCH" in decision.reason_codes
    assert decision.receipt is None
    assert store.list_receipts() == []


def test_exact_approval_resource_refs_include_adapter_transport_and_endpoint_scope() -> None:
    primary_refs = required_provider_invocation_resource_refs(invocation_request())
    second_refs = required_provider_invocation_resource_refs(second_invocation_request())

    assert TINY_LIVE_PROVIDER_ADAPTER_REF in primary_refs
    assert TINY_LIVE_PROVIDER_TRANSPORT_REF in primary_refs
    assert TINY_LIVE_PROVIDER_ENDPOINT_REF in primary_refs
    assert TINY_LIVE_PROVIDER_MODEL_NAME_REF in primary_refs
    assert SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF in second_refs
    assert SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF in second_refs
    assert SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF in second_refs
    assert SECOND_TINY_LIVE_PROVIDER_MODEL_NAME_REF in second_refs


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


def test_unscoped_cost_adapter_blocks_before_receipt() -> None:
    request = invocation_request(estimated_cost_usd=0.001, max_approved_usd=0.01)

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=OverBudgetTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_PROVIDER_ADAPTER_SCOPE_MISMATCH" in decision.reason_codes
    assert decision.receipt is None


def test_authority_lease_is_required_before_provider_lane_execution() -> None:
    decision = evaluate_tiny_provider_invocation(
        invocation_request(),
        approval_authority=exact_approval_only_authority_for(invocation_request()),
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.authority_required
    assert "AUTHORITY_LEASE_REQUIRED" in decision.reason_codes
    assert decision.authority_decision is not None
    assert decision.authority_decision.outcome == "deny"


def test_exact_approval_is_required_after_authority_lease() -> None:
    decision = evaluate_tiny_provider_invocation(
        invocation_request(),
        active_authority_leases=[provider_model_execute_lease()],
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.approval_required
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes
    assert decision.authority_decision is not None
    assert decision.authority_decision.outcome == "allow"


def test_default_adapter_remains_approved_no_execution_after_exact_approval() -> None:
    decision = evaluate_with_exact_approval(invocation_request())

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.approved_no_execution
    assert "TINY_PROVIDER_ADAPTER_DISABLED_BY_DEFAULT" in decision.reason_codes
    assert decision.receipt is None


def test_unscoped_deterministic_adapter_cannot_record_primary_receipt(
    tmp_path: Path,
) -> None:
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-provider-receipts.jsonl")
    request = invocation_request(invocation_ref="provider-invocation-ref:tiny:success")
    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.live_adapter_blocked
    assert "TINY_PROVIDER_ADAPTER_SCOPE_MISMATCH" in decision.reason_codes
    assert decision.receipt is None
    assert store.list_receipts() == []


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


def test_transport_receipt_allows_second_network_scope_only_with_matching_refs() -> None:
    receipt = TinyProviderInvocationTransportReceipt(
        transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
        adapter_ref=SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
        provider_ref=SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        model_ref=SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-second-test",
        usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-second-test",
        cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-second-test",
        input_tokens_used=1,
        output_tokens_used=1,
        billed_cost_usd=0.001,
        network_call_performed=True,
    )

    assert receipt.network_call_performed is True
    assert receipt.provider_sdk_used is False

    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_TRANSPORT_NETWORK_SCOPE_DENIED",
    ):
        TinyProviderInvocationTransportReceipt(
            transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            provider_ref=SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
            model_ref=SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
            redacted_output_summary_ref="redacted-output-summary-ref:provider-runtime:tiny-second-test",
            usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-second-test",
            cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-second-test",
            input_tokens_used=1,
            output_tokens_used=1,
            billed_cost_usd=0.001,
            network_call_performed=True,
        )


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


def test_receipt_rejects_non_network_unscoped_adapter_ref() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_ADAPTER_SCOPE_DENIED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                adapter_ref="provider-adapter-ref:tiny-exact-approved:deterministic-test",
                network_call_performed=False,
            )
        )


def test_receipt_rejects_success_when_actual_cost_is_incomplete() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_COMPLETENESS_REQUIRED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                actual_cost_captured=False,
                receipt_completeness_status=(
                    TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
                ),
                incomplete_cost_requires_review=True,
                further_provider_use_blocked=True,
            )
        )


def test_incomplete_cost_receipt_requires_review_and_blocks_further_use(
    tmp_path: Path,
) -> None:
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-incomplete-cost.jsonl")
    incomplete_receipt = TinyProviderInvocationReceipt(
        **receipt_payload(
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            invocation_performed=False,
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            network_call_performed=True,
            input_tokens_used=4,
            output_tokens_used=2,
            actual_usage_captured=True,
            actual_cost_captured=False,
            receipt_completeness_status=(
                TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
            ),
            incomplete_cost_requires_review=True,
            further_provider_use_blocked=True,
            reason_codes=[
                "ACTUAL_COST_INCOMPLETE",
                "INCOMPLETE_COST_REQUIRES_REVIEW",
                "FURTHER_PROVIDER_USE_BLOCKED",
            ],
        )
    )
    store.record(incomplete_receipt)
    next_request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:after-incomplete",
        idempotency_ref="idempotency:provider-runtime:after-incomplete",
        expected_receipt_ref="receipt:provider-runtime:after-incomplete",
    )

    decision = evaluate_tiny_provider_invocation(
        next_request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(next_request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt == incomplete_receipt
    assert "INCOMPLETE_COST_REQUIRES_REVIEW" in decision.reason_codes
    assert "FURTHER_PROVIDER_USE_BLOCKED" in decision.reason_codes


def test_incomplete_usage_receipt_blocks_further_use(tmp_path: Path) -> None:
    store = TinyProviderInvocationReceiptStore(tmp_path / "tiny-incomplete-usage.jsonl")
    incomplete_receipt = TinyProviderInvocationReceipt(
        **receipt_payload(
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            invocation_performed=False,
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            network_call_performed=True,
            input_tokens_used=0,
            output_tokens_used=0,
            billed_cost_usd=0.001,
            actual_usage_captured=False,
            actual_cost_captured=True,
            receipt_completeness_status=(
                TinyProviderReceiptCompletenessStatus.incomplete_usage_requires_review
            ),
            incomplete_cost_requires_review=False,
            further_provider_use_blocked=True,
            reason_codes=[
                "ACTUAL_USAGE_INCOMPLETE",
                "REVIEW_REQUIRED",
                "FURTHER_PROVIDER_USE_BLOCKED",
            ],
        )
    )
    store.record(incomplete_receipt)
    next_request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:after-incomplete-usage",
        idempotency_ref="idempotency:provider-runtime:after-incomplete-usage",
        expected_receipt_ref="receipt:provider-runtime:after-incomplete-usage",
    )

    decision = evaluate_tiny_provider_invocation(
        next_request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(next_request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt == incomplete_receipt
    assert "ACTUAL_USAGE_INCOMPLETE" in decision.reason_codes
    assert "REVIEW_REQUIRED" in decision.reason_codes
    assert "FURTHER_PROVIDER_USE_BLOCKED" in decision.reason_codes


def test_legacy_receipt_without_completeness_fields_fails_closed_on_replay(
    tmp_path: Path,
) -> None:
    request = invocation_request()
    store = TinyProviderInvocationReceiptStore(tmp_path / "legacy-receipts.jsonl")
    legacy_payload = receipt_payload(
        status=TinyProviderInvocationStatus.receipt_recorded,
        invocation_performed=True,
        estimated_cost_usd=request.estimated_cost_usd,
        billed_cost_usd=request.estimated_cost_usd,
        reason_codes=["unsafe lowercase reason"],
    )
    for field in (
        "estimated_cost_ref",
        "actual_usage_ref",
        "actual_cost_ref",
        "actual_usage_captured",
        "actual_cost_captured",
        "receipt_completeness_status",
        "incomplete_cost_requires_review",
        "further_provider_use_blocked",
    ):
        legacy_payload.pop(field)
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text(json.dumps(legacy_payload) + "\n", encoding="utf-8")

    decision = evaluate_tiny_provider_invocation(
        request,
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=exact_authority_for(request),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == TinyProviderInvocationStatus.cost_blocked
    assert decision.receipt is not None
    assert decision.receipt.status == TinyProviderInvocationStatus.cost_blocked
    assert (
        decision.receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
    )
    assert decision.receipt.actual_cost_captured is False
    assert decision.receipt.incomplete_cost_requires_review is True
    assert decision.receipt.further_provider_use_blocked is True
    assert "REDACTED_LEGACY_RECEIPT_REASON" in decision.receipt.reason_codes
    assert "LEGACY_RECEIPT_COMPLETENESS_MISSING" in decision.receipt.reason_codes
    assert "unsafe lowercase reason" not in decision.receipt.reason_codes
    assert "FURTHER_PROVIDER_USE_BLOCKED" in decision.reason_codes


def test_receipt_allows_scoped_network_flag_but_rejects_raw_persistence() -> None:
    receipt = TinyProviderInvocationReceipt(
        **receipt_payload(
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            network_call_performed=True,
            billed_cost_usd=0.001,
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
        TinyProviderInvocationReceipt(
            **receipt_payload(
                adapter_ref="provider-adapter-ref:tiny-exact-approved:deterministic-test",
                network_call_performed=True,
                billed_cost_usd=0.001,
            )
        )


def test_receipt_rejects_freeform_safe_summary_text() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_SAFE_SUMMARY_DENIED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                safe_summary="Unsafe freeform non-ref summary should be rejected."
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


def test_tiny_provider_route_defaults_to_no_execution_with_idempotency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
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
    assert payload["data"]["status"] == "authority_required"
    assert payload["data"]["authority_decision"]["outcome"] == "deny"
    assert payload["data"]["receipt"] is None
    evidence_refs = [item["evidence_ref"] for item in payload["evidence"]]
    assert request.expected_receipt_ref not in evidence_refs
    assert request.cost_estimate_ref in evidence_refs
    assert request.budget_decision_ref in evidence_refs


def test_tiny_provider_route_uses_persisted_authority_lease_before_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    lease, receipt = AuthorityLeaseStore(authority_dir).issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_machine_access_session,
            requested_domains={
                AuthorityDomain.provider_model_calls: [AuthorityCapability.execute]
            },
            decision_reason_ref="reason-ref:test-provider-route-authority",
            safe_summary="Select provider execution authority for this session.",
        ),
        idempotency_ref="idempotency-ref:test-provider-route-authority",
    )
    assert lease is not None
    assert receipt.status == "issued"
    client = TestClient(app)
    request = invocation_request(
        invocation_ref="provider-invocation-ref:tiny:route-authority"
    )

    response = client.post(
        TINY_PROVIDER_INVOCATION_ROUTE,
        headers={"X-UAA-Idempotency-Key": request.idempotency_ref},
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "approval_required"
    assert payload["data"]["authority_decision"]["outcome"] == "allow"
    assert payload["data"]["authority_decision"]["lease_ref"] == lease.lease_ref


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
            redacted_input_summary_ref="unsafe freeform summary text"
        )


def test_request_rejects_local_path_shaped_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_REQUEST_UNSAFE_REF_REJECTED",
    ):
        invocation_request(credential_ref="credential-ref:unsafe/value")


def test_receipt_rejects_raw_text_in_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="TINY_PROVIDER_INVOCATION_RECEIPT_UNSAFE_REF_REJECTED",
    ):
        TinyProviderInvocationReceipt(
            **receipt_payload(
                redacted_output_summary_ref="unsafe freeform summary text",
            )
        )
