from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS,
    MultiUserProductBoundaryPolicy,
    MultiUserProductBoundaryRequest,
    MultiUserProductBoundaryStatus,
    build_multi_user_product_boundary_record,
    validate_multi_user_product_boundary_policy,
    validate_multi_user_product_boundary_record,
    validate_multi_user_product_boundary_request,
)


def _request(**overrides: Any) -> MultiUserProductBoundaryRequest:
    data = {
        "request_ref": "multi-user-product-boundary-request:m141",
        "product_boundary_ref": "multi-user-product-boundary:m141",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS),
        "user_boundary_refs": [
            "user-boundary:m141:safe-user-refs-only",
            "user-boundary:m141:no-user-account-runtime",
        ],
        "workspace_boundary_refs": [
            "workspace-boundary:m141:safe-workspace-refs-only",
            "workspace-boundary:m141:no-workspace-sharing-runtime",
        ],
        "tenant_boundary_refs": [
            "tenant-boundary:m141:safe-tenant-refs-only",
            "tenant-boundary:m141:no-account-tenancy-runtime",
        ],
        "role_boundary_refs": [
            "role-boundary:m141:role-refs-not-authority",
            "role-boundary:m141:no-org-admin-runtime",
        ],
        "privacy_boundary_refs": [
            "privacy-boundary:m141:no-cross-workspace-content",
            "privacy-boundary:m141:no-identity-federation",
        ],
        "audit_ref": "audit:m141:multi-user-product-boundary",
        "replay_ref": "replay:m141:multi-user-product-boundary",
        "revocation_ref": "revocation:m141:multi-user-product-boundary",
        "kill_switch_ref": "kill-switch:m141:multi-user-product-boundary",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m141:multi-user-product-boundary:no-effect"
        ),
        "safe_summary": (
            "Define multi-user product boundary refs without account tenancy runtime."
        ),
    }
    data.update(overrides)
    return MultiUserProductBoundaryRequest(**data)
