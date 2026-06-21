from typing import Any
from importlib import import_module

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)
from ultimate_ai_agent.core.production_readiness import (
    build_account_connector_contract_review_record,
    build_production_audit_retention_policy_record,
    build_production_threat_model_record,
    build_remote_agent_coordination_contract_record,
    build_role_based_authority_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M118 production_readiness package missing: {exc}")


def _source_record() -> Any:
    return build_remote_agent_coordination_contract_record(
        source_record=build_role_based_authority_model_record(
            source_record=build_production_audit_retention_policy_record(
                source_record=build_account_connector_contract_review_record(
                    source_record=build_secrets_boundary_record(
                        source_record=build_user_workspace_identity_record(
                            source_record=build_production_threat_model_record(
                                source_record=build_mobile_sensor_hardening_freeze_record(
                                    source_record=build_mobile_sensor_audit_ledger_record(
                                        source_record=build_mobile_kill_switch_revocation_record(
                                            source_report=build_mobile_approval_renewal_ux_report()
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )


def test_m118_deployment_mode_matrix_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_deployment_mode_matrix_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.DeploymentModeMatrixStatus.deployment_mode_matrix
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_remote_agent_coordination_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.deployment_mode_bound is True
    assert record.environment_bound is True
    assert record.authority_tier_bound is True
    assert record.rollout_stage_bound is True
    assert record.rollback_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_remote_agent_coordination_ref == source_record.remote_coordination_contract_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m117" in record.accepted_checkpoint_refs
    assert record.deployment_mode_refs
    assert record.environment_refs
    assert record.authority_tier_refs
    assert record.rollout_stage_refs
    assert record.rollback_boundary_ref.startswith("rollback-boundary-ref:")
    assert record.production_authority_enabled is False
    assert record.deployment_runtime_enabled is False
    assert record.deployment_execution_enabled is False
    assert record.release_automation_enabled is False
    assert record.external_distribution_enabled is False
    assert record.infrastructure_provisioning_enabled is False
    assert record.ci_cd_execution_enabled is False
    assert record.signing_or_notarization_enabled is False
    assert record.remote_agent_runtime_enabled is False
    assert record.remote_dispatch_enabled is False
    assert record.network_access_enabled is False
    assert record.credential_handling_enabled is False
    assert record.account_action_enabled is False
    assert record.model_call_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.tool_execution_enabled is False
    assert record.shell_execution_enabled is False
    assert record.browser_automation_enabled is False
    assert record.plugin_execution_enabled is False
    assert record.mobile_sensor_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M118_DEPLOYMENT_MODE_MATRIX",
        "M118_CONTRACT_ONLY",
        "M118_REVIEW_ONLY",
        "M118_NO_DEPLOYMENT_RUNTIME_OR_RELEASE_AUTOMATION",
        "M119_REMAINS_FUTURE",
    ]


def test_m118_deployment_mode_matrix_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_deployment_mode_matrix_record(
        source_record=_source_record()
    )

    assert record.deployment_mode_matrix_ref == "deployment-mode-matrix:m118"
    assert record.source_remote_agent_coordination_ref == "remote-agent-coordination:m117"
    assert record.deployment_mode_refs == [
        "deployment-mode-ref:m118:local-dev",
        "deployment-mode-ref:m118:internal-alpha",
        "deployment-mode-ref:m118:future-beta-candidate",
    ]
    assert record.environment_refs == [
        "environment-ref:m118:local-only",
        "environment-ref:m118:internal-review-only",
    ]
    assert record.authority_tier_refs == [
        "authority-tier-ref:m118:no-production-authority",
        "authority-tier-ref:m118:review-only",
    ]
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "oauth token",
        "deploy now",
        "production execution",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("deployment_runtime_enabled", "DEPLOYMENT_RUNTIME_DENIED"),
        ("deployment_execution_enabled", "DEPLOYMENT_EXECUTION_DENIED"),
        ("release_automation_enabled", "RELEASE_AUTOMATION_DENIED"),
        ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
        ("infrastructure_provisioning_enabled", "INFRASTRUCTURE_PROVISIONING_DENIED"),
        ("ci_cd_execution_enabled", "CI_CD_EXECUTION_DENIED"),
        ("signing_or_notarization_enabled", "SIGNING_OR_NOTARIZATION_DENIED"),
        ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
        ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m118_policy_denies_deployment_runtime_and_release_automation(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_deployment_mode_matrix_policy(
            production_readiness.DeploymentModeMatrixPolicy(**{field: True})
        )


def test_m118_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_deployment_mode_matrix_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M118_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M118_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M118_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M118_BASELINE_BINDING_REQUIRED"),
        (
            {"source_remote_agent_coordination_bound": False},
            "M118_SOURCE_REMOTE_AGENT_COORDINATION_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M118_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M118_WORKSPACE_BINDING_REQUIRED"),
        ({"deployment_mode_bound": False}, "M118_DEPLOYMENT_MODE_BINDING_REQUIRED"),
        ({"environment_bound": False}, "M118_ENVIRONMENT_BINDING_REQUIRED"),
        ({"authority_tier_bound": False}, "M118_AUTHORITY_TIER_BINDING_REQUIRED"),
        ({"rollout_stage_bound": False}, "M118_ROLLOUT_STAGE_BINDING_REQUIRED"),
        (
            {"rollback_boundary_bound": False},
            "M118_ROLLBACK_BOUNDARY_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M118_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"deployment_mode_refs": []}, "M118_DEPLOYMENT_MODE_REF_REQUIRED"),
        ({"environment_refs": []}, "M118_ENVIRONMENT_REF_REQUIRED"),
        ({"authority_tier_refs": []}, "M118_AUTHORITY_TIER_REF_REQUIRED"),
        ({"rollout_stage_refs": []}, "M118_ROLLOUT_STAGE_REF_REQUIRED"),
        ({"audit_required": False}, "M118_AUDIT_REQUIRED"),
        ({"replay_safe": False}, "M118_REPLAY_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"deployment_runtime_enabled": True}, "DEPLOYMENT_RUNTIME_DENIED"),
        ({"deployment_execution_enabled": True}, "DEPLOYMENT_EXECUTION_DENIED"),
        ({"release_automation_enabled": True}, "RELEASE_AUTOMATION_DENIED"),
        ({"external_distribution_enabled": True}, "EXTERNAL_DISTRIBUTION_DENIED"),
        (
            {"infrastructure_provisioning_enabled": True},
            "INFRASTRUCTURE_PROVISIONING_DENIED",
        ),
        ({"ci_cd_execution_enabled": True}, "CI_CD_EXECUTION_DENIED"),
        (
            {"signing_or_notarization_enabled": True},
            "SIGNING_OR_NOTARIZATION_DENIED",
        ),
        ({"remote_agent_runtime_enabled": True}, "REMOTE_AGENT_RUNTIME_DENIED"),
        ({"remote_dispatch_enabled": True}, "REMOTE_DISPATCH_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"model_call_enabled": True}, "MODEL_CALL_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
        ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_enabled": True}, "PLUGIN_EXECUTION_DENIED"),
        ({"mobile_sensor_enabled": True}, "MOBILE_SENSOR_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"side_effects_performed": ["deploy"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_deployment_mode_matrix_record(
                record.model_copy(update=update)
            )


def test_m118_denies_untrusted_or_mutated_source_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="M118_SOURCE_RECORD_REQUIRED"):
        production_readiness.build_deployment_mode_matrix_record(source_record=None)

    with pytest.raises(ValueError, match="REMOTE_AGENT_RUNTIME_DENIED"):
        production_readiness.build_deployment_mode_matrix_record(
            source_record=source_record.model_copy(
                update={"remote_agent_runtime_enabled": True}
            )
        )


def test_m118_safe_summary_and_metadata_never_echo_secret_or_deployment_payloads() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_deployment_mode_matrix_record(
        source_record=_source_record()
    )
    forbidden_values = [
        {"metadata": {"token": "secret-token"}},
        {"safe_summary": "deploy using bearer secret-token"},
        {"deployment_mode_refs": ["https://deploy.example.com/raw"]},
        {"environment_refs": ["production://account"]},
    ]

    for update in forbidden_values:
        with pytest.raises(ValueError):
            production_readiness.validate_deployment_mode_matrix_record(
                record.model_copy(update=update)
            )
