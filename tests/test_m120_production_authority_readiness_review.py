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
    build_deployment_mode_matrix_record,
    build_production_audit_retention_policy_record,
    build_production_red_team_harness_record,
    build_production_threat_model_record,
    build_remote_agent_coordination_contract_record,
    build_role_based_authority_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness():
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M120 production_readiness package missing: {exc}")


def _source_record():
    return build_production_red_team_harness_record(
        source_record=build_deployment_mode_matrix_record(
            source_record=build_remote_agent_coordination_contract_record(
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
        )
    )


def test_m120_production_authority_readiness_is_contract_only_and_safe_ref_bound() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_production_authority_readiness_review_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.ProductionAuthorityReadinessReviewStatus.production_authority_readiness_review
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_production_red_team_harness_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.deployment_mode_bound is True
    assert record.environment_bound is True
    assert record.authority_tier_bound is True
    assert record.readiness_check_bound is True
    assert record.launch_blocker_bound is True
    assert record.rollback_readiness_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_production_red_team_harness_ref
        == source_record.production_red_team_harness_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert record.deployment_mode_refs == source_record.deployment_mode_refs
    assert record.environment_refs == source_record.environment_refs
    assert record.authority_tier_refs == source_record.authority_tier_refs
    assert "checkpoint:m119" in record.accepted_checkpoint_refs
    assert record.readiness_check_refs
    assert record.launch_blocker_refs
    assert record.rollback_readiness_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.go_live_enabled is False
    assert record.production_deployment_enabled is False
    assert record.external_distribution_enabled is False
    assert record.traffic_routing_enabled is False
    assert record.account_action_enabled is False
    assert record.credential_handling_enabled is False
    assert record.network_access_enabled is False
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
        "M120_PRODUCTION_AUTHORITY_READINESS_REVIEW",
        "M120_CONTRACT_ONLY",
        "M120_REVIEW_ONLY",
        "M120_NO_PRODUCTION_AUTHORITY_OR_GO_LIVE",
        "M121_REMAINS_FUTURE",
    ]


def test_m120_production_authority_readiness_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_authority_readiness_review_record(
        source_record=_source_record()
    )

    assert (
        record.production_authority_readiness_review_ref
        == "production-authority-readiness-review:m120"
    )
    assert (
        record.source_production_red_team_harness_ref
        == "production-red-team-harness:m119"
    )
    assert record.readiness_check_refs == [
        "readiness-check-ref:m120:authority-boundaries-reviewed",
        "readiness-check-ref:m120:launch-blockers-recorded",
        "readiness-check-ref:m120:rollback-readiness-reviewed",
    ]
    assert record.launch_blocker_refs == [
        "launch-blocker-ref:m120:no-production-authority",
        "launch-blocker-ref:m120:no-live-traffic",
        "launch-blocker-ref:m120:no-credential-runtime",
    ]
    assert record.rollback_readiness_refs
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "oauth token",
        "go live now",
        "route traffic",
        "production deploy",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("go_live_enabled", "GO_LIVE_DENIED"),
        ("production_deployment_enabled", "PRODUCTION_DEPLOYMENT_DENIED"),
        ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
        ("traffic_routing_enabled", "TRAFFIC_ROUTING_DENIED"),
        ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
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
def test_m120_policy_denies_production_authority_and_go_live(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_production_authority_readiness_review_policy(
            production_readiness.ProductionAuthorityReadinessReviewPolicy(
                **{field: True}
            )
        )


def test_m120_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_authority_readiness_review_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M120_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M120_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M120_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M120_BASELINE_BINDING_REQUIRED"),
        (
            {"source_production_red_team_harness_bound": False},
            "M120_SOURCE_PRODUCTION_RED_TEAM_HARNESS_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M120_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M120_WORKSPACE_BINDING_REQUIRED"),
        ({"deployment_mode_bound": False}, "M120_DEPLOYMENT_MODE_BINDING_REQUIRED"),
        ({"environment_bound": False}, "M120_ENVIRONMENT_BINDING_REQUIRED"),
        ({"authority_tier_bound": False}, "M120_AUTHORITY_TIER_BINDING_REQUIRED"),
        ({"readiness_check_bound": False}, "M120_READINESS_CHECK_BINDING_REQUIRED"),
        ({"launch_blocker_bound": False}, "M120_LAUNCH_BLOCKER_BINDING_REQUIRED"),
        (
            {"rollback_readiness_bound": False},
            "M120_ROLLBACK_READINESS_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M120_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"readiness_check_refs": []}, "M120_READINESS_CHECK_REF_REQUIRED"),
        ({"launch_blocker_refs": []}, "M120_LAUNCH_BLOCKER_REF_REQUIRED"),
        ({"rollback_readiness_refs": []}, "M120_ROLLBACK_READINESS_REF_REQUIRED"),
        ({"audit_required": False}, "M120_AUDIT_REQUIRED"),
        ({"replay_safe": False}, "M120_REPLAY_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"go_live_enabled": True}, "GO_LIVE_DENIED"),
        ({"production_deployment_enabled": True}, "PRODUCTION_DEPLOYMENT_DENIED"),
        ({"external_distribution_enabled": True}, "EXTERNAL_DISTRIBUTION_DENIED"),
        ({"traffic_routing_enabled": True}, "TRAFFIC_ROUTING_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
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
        ({"side_effects_performed": ["route traffic"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_authority_readiness_review_record(
                record.model_copy(update=update)
            )


def test_m120_denies_untrusted_or_mutated_source_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="M120_SOURCE_RECORD_REQUIRED"):
        production_readiness.build_production_authority_readiness_review_record(
            source_record=None
        )

    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        production_readiness.build_production_authority_readiness_review_record(
            source_record=source_record.model_copy(
                update={"production_authority_enabled": True}
            )
        )


def test_m120_safe_summary_and_metadata_never_echo_secret_or_launch_payloads() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_authority_readiness_review_record(
        source_record=_source_record()
    )
    forbidden_values = [
        {"metadata": {"token": "secret-token"}},
        {"safe_summary": "go live now with bearer secret-token"},
        {"readiness_check_refs": ["https://prod.example.com/raw"]},
        {"launch_blocker_refs": ["production://account"]},
    ]

    for update in forbidden_values:
        with pytest.raises(ValueError):
            production_readiness.validate_production_authority_readiness_review_record(
                record.model_copy(update=update)
            )
