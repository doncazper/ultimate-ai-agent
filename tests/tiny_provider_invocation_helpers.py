from __future__ import annotations

from pydantic import SecretStr

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.providers import (
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderInvocationTransportReceipt,
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
    AnthropicCompatibleTinyLiveProviderAdapter,
    TinyLiveCredentialResolution,
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
        "redacted_input_summary_ref": (
            "redacted-input-summary-ref:provider-runtime:tiny-test"
        ),
        "redacted_output_summary_ref": (
            "redacted-output-summary-ref:provider-runtime:tiny-test"
        ),
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-test",
        "estimated_input_tokens": 10,
        "estimated_output_tokens": 5,
        "estimated_cost_usd": 0.001,
    }
    values.update(overrides)
    return TinyProviderInvocationRequest(**values)


def second_invocation_request(**overrides: object) -> TinyProviderInvocationRequest:
    values: dict[str, object] = {
        "invocation_ref": "provider-invocation-ref:tiny-second:test",
        "run_id": "run-ref:tiny-second-provider-test",
        "provider_ref": SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        "model_ref": SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        "credential_ref": "credential-ref:anthropic-compatible:scoped-test",
        "policy_ref": SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-runtime:tiny-second-test",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:tiny-second-test",
        "cost_estimate_ref": "cost-estimate-ref:provider-runtime:tiny-second-test",
        "budget_decision_ref": "budget-decision-ref:provider-runtime:tiny-second-test",
        "max_approved_usd_ref": (
            "max-approved-usd-ref:provider-runtime:tiny-second-test"
        ),
        "max_approved_usd": 0.01,
        "idempotency_ref": "idempotency:provider-runtime:tiny-second-test",
        "expected_receipt_ref": "receipt:provider-runtime:tiny-second-test",
        "usage_receipt_ref": "usage-receipt-ref:provider-runtime:tiny-second-test",
        "cost_receipt_ref": "cost-receipt-ref:provider-runtime:tiny-second-test",
        "redacted_input_summary_ref": (
            "redacted-input-summary-ref:provider-runtime:tiny-second-test"
        ),
        "redacted_output_summary_ref": (
            "redacted-output-summary-ref:provider-runtime:tiny-second-test"
        ),
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-second-test",
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
    authority.issue_authority_lease(provider_model_execute_lease())
    return authority


def exact_approval_only_authority_for(
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


def provider_model_execute_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:provider-model-calls-execute-test",
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
            "Test lease grants exact provider model call execution for scoped "
            "provider invocation lane tests."
        ),
    )


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
        "adapter_ref": TINY_LIVE_PROVIDER_ADAPTER_REF,
        "credential_ref": "credential-ref:openai-compatible:scoped-test",
        "approval_ref": "approval-ref:provider-runtime:tiny-test",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:tiny-test",
        "cost_estimate_ref": "cost-estimate-ref:provider-runtime:tiny-test",
        "budget_decision_ref": "budget-decision-ref:provider-runtime:tiny-test",
        "max_approved_usd_ref": "max-approved-usd-ref:provider-runtime:tiny-test",
        "expected_receipt_ref": "receipt:provider-runtime:tiny-test",
        "usage_receipt_ref": "usage-receipt-ref:provider-runtime:tiny-test",
        "cost_receipt_ref": "cost-receipt-ref:provider-runtime:tiny-test",
        "cost_governor_decision_ref": (
            "cost-decision-ref:provider-runtime:tiny-test"
        ),
        "estimated_cost_ref": "cost-estimate-ref:provider-runtime:tiny-test",
        "actual_usage_ref": (
            "actual-usage-ref:provider-runtime:"
            "usage-receipt-ref-provider-runtime-tiny-test"
        ),
        "actual_cost_ref": (
            "actual-cost-ref:provider-runtime:"
            "cost-receipt-ref-provider-runtime-tiny-test"
        ),
        "idempotency_ref": "idempotency:provider-runtime:tiny-test",
        "redacted_input_summary_ref": (
            "redacted-input-summary-ref:provider-runtime:tiny-test"
        ),
        "redacted_output_summary_ref": (
            "redacted-output-summary-ref:provider-runtime:tiny-test"
        ),
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-test",
        "status": TinyProviderInvocationStatus.receipt_recorded,
        "invocation_performed": True,
        "actual_usage_captured": True,
        "actual_cost_captured": True,
        "receipt_completeness_status": TinyProviderReceiptCompletenessStatus.complete,
        "incomplete_cost_requires_review": False,
        "further_provider_use_blocked": False,
        "safe_summary": (
            "Scoped provider capability recorded a redacted receipt "
            "using a scoped adapter."
        ),
    }
    values.update(overrides)
    return values


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


def available_second_credential_resolution(
    request: TinyProviderInvocationRequest,
    *,
    secret_value: str = "transient-material",
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:anthropic-compatible:tiny-test",
        vault_record_ref="credential-vault-record-ref:anthropic-compatible:tiny-test",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr(secret_value),
    )


class OverBudgetTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    enabled = True
    test_only_contract_adapter = True

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=(
                "provider-transport-ref:tiny-provider:"
                f"{request.invocation_ref.split(':')[-1]}"
            ),
            adapter_ref=self.adapter_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=(request.max_approved_usd or 0) + 0.01,
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


class SecondLiveRefWithoutReceiptRequirementAdapter(
    AnthropicCompatibleTinyLiveProviderAdapter
):
    requires_receipt_store_before_network = False
