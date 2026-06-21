from typing import Any
import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS,
    BillingPlanBoundaryPolicy,
    BillingPlanBoundaryRequest,
    BillingPlanBoundaryStatus,
    build_billing_plan_boundary_record,
    validate_billing_plan_boundary_policy,
    validate_billing_plan_boundary_record,
    validate_billing_plan_boundary_request,
)


def _request(**overrides: Any) -> BillingPlanBoundaryRequest:
    data = {
        "request_ref": "billing-plan-boundary-request:m146",
        "billing_boundary_ref": "billing-plan-boundary:m146",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS),
        "billing_boundary_refs": [
            "billing-boundary:m146:admin-review-only",
            "billing-boundary:m146:no-runtime",
        ],
        "plan_boundary_refs": [
            "plan-boundary:m146:user-visible-policy",
            "plan-boundary:m146:no-plan-enforcement",
        ],
        "entitlement_boundary_refs": [
            "entitlement-boundary:m146:single-workspace-review",
            "entitlement-boundary:m146:no-sharing-runtime",
        ],
        "pricing_disclosure_refs": [
            "pricing-disclosure:m146:payment-provider-boundary",
            "pricing-disclosure:m146:no-rbac-runtime",
        ],
        "payment_provider_boundary_refs": [
            "payment-provider-boundary:m146:no-production",
            "payment-provider-boundary:m146:no-autonomous-upgrade",
        ],
        "upgrade_downgrade_policy_refs": [
            "upgrade-downgrade-policy:m146:safe-summary-only",
            "upgrade-downgrade-policy:m146:no-billing-boundary",
        ],
        "support_refund_policy_refs": [
            "support-refund-policy:m146:human-review",
            "support-refund-policy:m146:no-enforcement-runtime",
        ],
        "audit_ref": "audit:m146:billing-plan-boundary",
        "replay_ref": "replay:m146:billing-plan-boundary",
        "revocation_ref": "revocation:m146:billing-plan-boundary",
        "kill_switch_ref": "kill-switch:m146:billing-plan-boundary",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m146:billing-plan-boundary:no-effect"
        ),
        "safe_summary": "Record billing and plan boundary refs without runtime authority.",
    }
    data.update(overrides)
    return BillingPlanBoundaryRequest(**data)


def test_m146_record_is_contract_only_and_non_authoritative() -> None:
    record = build_billing_plan_boundary_record(_request())

    assert record.status == BillingPlanBoundaryStatus.boundary_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.billing_boundary_only is True
    assert record.disabled_by_default is True
    assert record.m101_m145_covered is True
    assert record.billing_boundaries_bound is True
    assert record.plan_boundaries_bound is True
    assert record.entitlement_boundaries_bound is True
    assert record.pricing_disclosures_bound is True
    assert record.payment_provider_boundaries_bound is True
    assert record.upgrade_downgrade_policies_bound is True
    assert record.support_refund_policies_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_payment_processing is True
    assert record.no_checkout_runtime is True
    assert record.no_plan_enforcement is True
    assert record.no_billing_runtime is True
    assert record.no_account_plan_runtime is True
    assert record.no_entitlement_runtime is True
    assert record.no_auth_runtime is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.payment_processing_started is False
    assert record.checkout_runtime_started is False
    assert record.subscription_management_started is False
    assert record.plan_enforcement_performed is False
    assert record.billing_runtime_started is False
    assert record.external_billing_provider_performed is False
    assert record.account_plan_runtime_started is False
    assert record.entitlement_runtime_started is False
    assert record.auth_runtime_started is False
    assert record.login_enabled is False
    assert record.connector_runtime_started is False
    assert record.plugin_marketplace_runtime_started is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.network_access_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M146_BILLING_PLAN_BOUNDARY_REVIEW_ONLY",
        "M146_M101_M145_COVERED",
        "M146_DISABLED_BY_DEFAULT",
        "M146_NO_PAYMENT_PROCESSING",
        "M146_NO_CHECKOUT_RUNTIME",
        "M146_NO_PLAN_ENFORCEMENT",
        "M146_NO_BILLING_RUNTIME",
        "M146_NO_ACCOUNT_PLAN_RUNTIME",
        "M146_NO_AUTH_RUNTIME",
        "M146_NO_BACKEND_ROUTE",
        "M146_NO_PRODUCTION_AUTHORITY",
        "M147_REMAINS_FUTURE",
    ]


def test_m146_record_uses_safe_refs_only() -> None:
    record = build_billing_plan_boundary_record(_request())

    assert record.record_ref == "billing-plan-boundary-record:m146"
    assert record.billing_boundary_ref == "billing-plan-boundary:m146"
    assert all(
        ref.startswith("billing-boundary:")
        for ref in record.billing_boundary_refs
    )
    assert all(ref.startswith("plan-boundary:") for ref in record.plan_boundary_refs)
    assert all(
        ref.startswith("entitlement-boundary:")
        for ref in record.entitlement_boundary_refs
    )
    assert all(ref.startswith("pricing-disclosure:") for ref in record.pricing_disclosure_refs)
    assert all(
        ref.startswith("payment-provider-boundary:")
        for ref in record.payment_provider_boundary_refs
    )
    assert all(
        ref.startswith("upgrade-downgrade-policy:")
        for ref in record.upgrade_downgrade_policy_refs
    )
    assert all(
        ref.startswith("support-refund-policy:")
        for ref in record.support_refund_policy_refs
    )
    assert record.audit_ref.startswith("audit:")
    assert record.replay_ref.startswith("replay:")
    assert record.revocation_ref.startswith("revocation:")
    assert record.kill_switch_ref.startswith("kill-switch:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "password" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("payment_processing_enabled", "M146_PAYMENT_PROCESSING_DENIED"),
        ("checkout_runtime_enabled", "M146_CHECKOUT_RUNTIME_DENIED"),
        ("subscription_management_enabled", "M146_SUBSCRIPTION_MANAGEMENT_DENIED"),
        ("plan_enforcement_enabled", "M146_PLAN_ENFORCEMENT_DENIED"),
        ("billing_runtime_enabled", "M146_BILLING_RUNTIME_DENIED"),
        ("external_billing_provider_enabled", "M146_EXTERNAL_BILLING_PROVIDER_DENIED"),
        ("account_plan_runtime_enabled", "M146_ACCOUNT_PLAN_RUNTIME_DENIED"),
        ("entitlement_runtime_enabled", "M146_ENTITLEMENT_RUNTIME_DENIED"),
        ("pricing_runtime_enabled", "M146_PRICING_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "M146_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M146_LOGIN_DENIED"),
        ("connector_runtime_enabled", "M146_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M146_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M146_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M146_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M146_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M146_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M146_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M146_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m146_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_billing_plan_boundary_policy(
            BillingPlanBoundaryPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("payment_processing_requested", "M146_PAYMENT_PROCESSING_DENIED"),
        ("checkout_runtime_requested", "M146_CHECKOUT_RUNTIME_DENIED"),
        ("subscription_management_requested", "M146_SUBSCRIPTION_MANAGEMENT_DENIED"),
        ("plan_enforcement_requested", "M146_PLAN_ENFORCEMENT_DENIED"),
        ("billing_runtime_requested", "M146_BILLING_RUNTIME_DENIED"),
        ("external_billing_provider_requested", "M146_EXTERNAL_BILLING_PROVIDER_DENIED"),
        ("account_plan_runtime_requested", "M146_ACCOUNT_PLAN_RUNTIME_DENIED"),
        ("entitlement_runtime_requested", "M146_ENTITLEMENT_RUNTIME_DENIED"),
        ("auth_runtime_requested", "M146_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M146_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M146_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M146_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M146_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M146_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M146_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M146_SECRET_DENIED"),
        ("backend_route_requested", "M146_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M146_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M146_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m146_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_billing_plan_boundary_request(
            _request().model_copy(update={field: True})
        )


def test_m146_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M146_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_billing_plan_boundary_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M146_CHECKPOINT_REF_REQUIRED"):
        validate_billing_plan_boundary_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M146_CHECKPOINT_REF_UNEXPECTED"):
        validate_billing_plan_boundary_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m146",
                ]
            )
        )

    for field, reason in [
        ("billing_boundary_refs", "M146_BILLING_BOUNDARY_REF_REQUIRED"),
        ("plan_boundary_refs", "M146_PLAN_BOUNDARY_REF_REQUIRED"),
        ("entitlement_boundary_refs", "M146_ENTITLEMENT_BOUNDARY_REF_REQUIRED"),
        ("pricing_disclosure_refs", "M146_PRICING_DISCLOSURE_REF_REQUIRED"),
        ("payment_provider_boundary_refs", "M146_PAYMENT_PROVIDER_BOUNDARY_REF_REQUIRED"),
        ("upgrade_downgrade_policy_refs", "M146_UPGRADE_DOWNGRADE_POLICY_REF_REQUIRED"),
        ("support_refund_policy_refs", "M146_SUPPORT_REFUND_POLICY_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_billing_plan_boundary_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"payment_processing_started": True}, "M146_PAYMENT_PROCESSING_DENIED"),
        ({"checkout_runtime_started": True}, "M146_CHECKOUT_RUNTIME_DENIED"),
        ({"subscription_management_started": True}, "M146_SUBSCRIPTION_MANAGEMENT_DENIED"),
        ({"plan_enforcement_performed": True}, "M146_PLAN_ENFORCEMENT_DENIED"),
        ({"billing_runtime_started": True}, "M146_BILLING_RUNTIME_DENIED"),
        (
            {"external_billing_provider_performed": True},
            "M146_EXTERNAL_BILLING_PROVIDER_DENIED",
        ),
        (
            {"account_plan_runtime_started": True},
            "M146_ACCOUNT_PLAN_RUNTIME_DENIED",
        ),
        ({"auth_runtime_started": True}, "M146_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M146_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M146_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M146_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M146_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m146_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_billing_plan_boundary_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_billing_plan_boundary_record(record.model_copy(update=update))


def test_m146_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M146_SIDE_EFFECTS_DENIED"):
        validate_billing_plan_boundary_request(
            _request(side_effects_performed=["enforced billing plan"])
        )

    record = build_billing_plan_boundary_record(_request())
    with pytest.raises(ValueError, match="M146_SIDE_EFFECTS_DENIED"):
        validate_billing_plan_boundary_record(
            record.model_copy(update={"side_effects_performed": ["enabled paid plan"]})
        )

    with pytest.raises(ValueError, match="M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED"):
        validate_billing_plan_boundary_policy(
            BillingPlanBoundaryPolicy(metadata={"api_key": "x"})
        )
