from typing import Any
import pytest

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


def test_m145_record_is_contract_only_and_non_authoritative() -> None:
    record = build_enterprise_pro_safety_modes_record(_request())

    assert record.status == EnterpriseProSafetyModesStatus.safety_modes_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.safety_modes_only is True
    assert record.disabled_by_default is True
    assert record.m101_m144_covered is True
    assert record.enterprise_safety_modes_bound is True
    assert record.pro_safety_modes_bound is True
    assert record.workspace_boundaries_bound is True
    assert record.role_policies_bound is True
    assert record.authority_ceilings_bound is True
    assert record.feature_availability_bound is True
    assert record.escalation_policies_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_enterprise_runtime is True
    assert record.no_pro_runtime is True
    assert record.no_plan_enforcement is True
    assert record.no_billing_runtime is True
    assert record.no_account_tenant_runtime is True
    assert record.no_role_runtime is True
    assert record.no_auth_runtime is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.enterprise_runtime_started is False
    assert record.pro_runtime_started is False
    assert record.safety_mode_runtime_started is False
    assert record.plan_enforcement_performed is False
    assert record.billing_runtime_started is False
    assert record.billing_plan_boundary_performed is False
    assert record.account_tenant_runtime_started is False
    assert record.role_runtime_started is False
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
        "M145_ENTERPRISE_PRO_SAFETY_MODES_REVIEW_ONLY",
        "M145_M101_M144_COVERED",
        "M145_DISABLED_BY_DEFAULT",
        "M145_NO_ENTERPRISE_RUNTIME",
        "M145_NO_PRO_RUNTIME",
        "M145_NO_PLAN_ENFORCEMENT",
        "M145_NO_BILLING_RUNTIME",
        "M145_NO_ACCOUNT_TENANT_RUNTIME",
        "M145_NO_AUTH_RUNTIME",
        "M145_NO_BACKEND_ROUTE",
        "M145_NO_PRODUCTION_AUTHORITY",
        "M146_REMAINS_FUTURE",
    ]


def test_m145_record_uses_safe_refs_only() -> None:
    record = build_enterprise_pro_safety_modes_record(_request())

    assert record.record_ref == "enterprise-pro-safety-modes-record:m145"
    assert record.safety_modes_ref == "enterprise-pro-safety-modes:m145"
    assert all(
        ref.startswith("enterprise-safety-mode:")
        for ref in record.enterprise_safety_mode_refs
    )
    assert all(ref.startswith("pro-safety-mode:") for ref in record.pro_safety_mode_refs)
    assert all(
        ref.startswith("workspace-boundary:")
        for ref in record.workspace_boundary_refs
    )
    assert all(ref.startswith("role-policy:") for ref in record.role_policy_refs)
    assert all(
        ref.startswith("authority-ceiling:")
        for ref in record.authority_ceiling_refs
    )
    assert all(
        ref.startswith("feature-availability:")
        for ref in record.feature_availability_refs
    )
    assert all(
        ref.startswith("escalation-policy:")
        for ref in record.escalation_policy_refs
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
        ("enterprise_runtime_enabled", "M145_ENTERPRISE_RUNTIME_DENIED"),
        ("pro_runtime_enabled", "M145_PRO_RUNTIME_DENIED"),
        ("safety_mode_runtime_enabled", "M145_SAFETY_MODE_RUNTIME_DENIED"),
        ("plan_enforcement_enabled", "M145_PLAN_ENFORCEMENT_DENIED"),
        ("billing_runtime_enabled", "M145_BILLING_RUNTIME_DENIED"),
        ("billing_plan_boundary_enabled", "M145_BILLING_PLAN_BOUNDARY_DENIED"),
        ("account_tenant_runtime_enabled", "M145_ACCOUNT_TENANT_RUNTIME_DENIED"),
        ("role_runtime_enabled", "M145_ROLE_RUNTIME_DENIED"),
        ("workspace_sharing_enabled", "M145_WORKSPACE_SHARING_DENIED"),
        ("auth_runtime_enabled", "M145_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M145_LOGIN_DENIED"),
        ("connector_runtime_enabled", "M145_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M145_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M145_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M145_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M145_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M145_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M145_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M145_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m145_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_enterprise_pro_safety_modes_policy(
            EnterpriseProSafetyModesPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("enterprise_runtime_requested", "M145_ENTERPRISE_RUNTIME_DENIED"),
        ("pro_runtime_requested", "M145_PRO_RUNTIME_DENIED"),
        ("safety_mode_runtime_requested", "M145_SAFETY_MODE_RUNTIME_DENIED"),
        ("plan_enforcement_requested", "M145_PLAN_ENFORCEMENT_DENIED"),
        ("billing_runtime_requested", "M145_BILLING_RUNTIME_DENIED"),
        ("billing_plan_boundary_requested", "M145_BILLING_PLAN_BOUNDARY_DENIED"),
        ("account_tenant_runtime_requested", "M145_ACCOUNT_TENANT_RUNTIME_DENIED"),
        ("role_runtime_requested", "M145_ROLE_RUNTIME_DENIED"),
        ("auth_runtime_requested", "M145_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M145_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M145_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M145_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M145_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M145_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M145_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M145_SECRET_DENIED"),
        ("backend_route_requested", "M145_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M145_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M145_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m145_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_enterprise_pro_safety_modes_request(
            _request().model_copy(update={field: True})
        )


def test_m145_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M145_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_enterprise_pro_safety_modes_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M145_CHECKPOINT_REF_REQUIRED"):
        validate_enterprise_pro_safety_modes_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M145_CHECKPOINT_REF_UNEXPECTED"):
        validate_enterprise_pro_safety_modes_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m146",
                ]
            )
        )

    for field, reason in [
        ("enterprise_safety_mode_refs", "M145_ENTERPRISE_SAFETY_MODE_REF_REQUIRED"),
        ("pro_safety_mode_refs", "M145_PRO_SAFETY_MODE_REF_REQUIRED"),
        ("workspace_boundary_refs", "M145_WORKSPACE_BOUNDARY_REF_REQUIRED"),
        ("role_policy_refs", "M145_ROLE_POLICY_REF_REQUIRED"),
        ("authority_ceiling_refs", "M145_AUTHORITY_CEILING_REF_REQUIRED"),
        ("feature_availability_refs", "M145_FEATURE_AVAILABILITY_REF_REQUIRED"),
        ("escalation_policy_refs", "M145_ESCALATION_POLICY_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_enterprise_pro_safety_modes_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"enterprise_runtime_started": True}, "M145_ENTERPRISE_RUNTIME_DENIED"),
        ({"pro_runtime_started": True}, "M145_PRO_RUNTIME_DENIED"),
        ({"safety_mode_runtime_started": True}, "M145_SAFETY_MODE_RUNTIME_DENIED"),
        ({"plan_enforcement_performed": True}, "M145_PLAN_ENFORCEMENT_DENIED"),
        ({"billing_runtime_started": True}, "M145_BILLING_RUNTIME_DENIED"),
        (
            {"billing_plan_boundary_performed": True},
            "M145_BILLING_PLAN_BOUNDARY_DENIED",
        ),
        (
            {"account_tenant_runtime_started": True},
            "M145_ACCOUNT_TENANT_RUNTIME_DENIED",
        ),
        ({"auth_runtime_started": True}, "M145_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M145_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M145_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M145_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M145_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m145_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_enterprise_pro_safety_modes_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_enterprise_pro_safety_modes_record(record.model_copy(update=update))


def test_m145_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M145_SIDE_EFFECTS_DENIED"):
        validate_enterprise_pro_safety_modes_request(
            _request(side_effects_performed=["enforced enterprise plan"])
        )

    record = build_enterprise_pro_safety_modes_record(_request())
    with pytest.raises(ValueError, match="M145_SIDE_EFFECTS_DENIED"):
        validate_enterprise_pro_safety_modes_record(
            record.model_copy(update={"side_effects_performed": ["enabled pro mode"]})
        )

    with pytest.raises(ValueError, match="M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED"):
        validate_enterprise_pro_safety_modes_policy(
            EnterpriseProSafetyModesPolicy(metadata={"api_key": "x"})
        )
