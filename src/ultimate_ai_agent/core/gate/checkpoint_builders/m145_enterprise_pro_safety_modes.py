from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS,
    EnterpriseProSafetyModesPolicy,
    EnterpriseProSafetyModesRequest,
    EnterpriseProSafetyModesStatus,
    build_enterprise_pro_safety_modes_record,
    validate_enterprise_pro_safety_modes_policy,
    validate_enterprise_pro_safety_modes_record,
    validate_enterprise_pro_safety_modes_request,
)


def _request(**overrides: Any) -> EnterpriseProSafetyModesRequest:
    data = {
        "request_ref": "enterprise-pro-safety-modes-request:m145",
        "safety_modes_ref": "enterprise-pro-safety-modes:m145",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS),
        "enterprise_safety_mode_refs": [
            "enterprise-safety-mode:m145:admin-review-only",
            "enterprise-safety-mode:m145:no-runtime",
        ],
        "pro_safety_mode_refs": [
            "pro-safety-mode:m145:user-visible-policy",
            "pro-safety-mode:m145:no-plan-enforcement",
        ],
        "workspace_boundary_refs": [
            "workspace-boundary:m145:single-workspace-review",
            "workspace-boundary:m145:no-sharing-runtime",
        ],
        "role_policy_refs": [
            "role-policy:m145:authority-ceiling",
            "role-policy:m145:no-rbac-runtime",
        ],
        "authority_ceiling_refs": [
            "authority-ceiling:m145:no-production",
            "authority-ceiling:m145:no-autonomous-upgrade",
        ],
        "feature_availability_refs": [
            "feature-availability:m145:safe-summary-only",
            "feature-availability:m145:no-billing-boundary",
        ],
        "escalation_policy_refs": [
            "escalation-policy:m145:human-review",
            "escalation-policy:m145:no-enforcement-runtime",
        ],
        "audit_ref": "audit:m145:enterprise-pro-safety-modes",
        "replay_ref": "replay:m145:enterprise-pro-safety-modes",
        "revocation_ref": "revocation:m145:enterprise-pro-safety-modes",
        "kill_switch_ref": "kill-switch:m145:enterprise-pro-safety-modes",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m145:enterprise-pro-safety-modes:no-effect"
        ),
        "safe_summary": "Record Enterprise and Pro safety mode refs without runtime authority.",
    }
    data.update(overrides)
    return EnterpriseProSafetyModesRequest(**data)
