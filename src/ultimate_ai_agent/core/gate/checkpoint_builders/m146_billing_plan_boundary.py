from __future__ import annotations
from typing import Any
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
