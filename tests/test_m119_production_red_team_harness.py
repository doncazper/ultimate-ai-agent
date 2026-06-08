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
        pytest.fail(f"M119 production_readiness package missing: {exc}")


def _source_record():
    return build_deployment_mode_matrix_record(
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


def test_m119_production_red_team_harness_is_contract_only_and_safe_ref_bound() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_production_red_team_harness_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.ProductionRedTeamHarnessStatus.production_red_team_harness
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_deployment_mode_matrix_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.deployment_mode_bound is True
    assert record.environment_bound is True
    assert record.authority_tier_bound is True
    assert record.red_team_scenario_bound is True
    assert record.abuse_case_bound is True
    assert record.threat_model_bound is True
    assert record.safety_control_bound is True
    assert record.mitigation_plan_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_deployment_mode_matrix_ref == source_record.deployment_mode_matrix_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert record.deployment_mode_refs == source_record.deployment_mode_refs
    assert record.environment_refs == source_record.environment_refs
    assert record.authority_tier_refs == source_record.authority_tier_refs
    assert "checkpoint:m118" in record.accepted_checkpoint_refs
    assert record.red_team_scenario_refs
    assert record.abuse_case_refs
    assert record.threat_model_refs
    assert record.safety_control_refs
    assert record.mitigation_plan_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.production_authority_enabled is False
    assert record.red_team_execution_enabled is False
    assert record.attack_automation_enabled is False
    assert record.external_probe_enabled is False
    assert record.exploit_generation_enabled is False
    assert record.security_scan_runtime_enabled is False
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
        "M119_PRODUCTION_RED_TEAM_HARNESS",
        "M119_CONTRACT_ONLY",
        "M119_REVIEW_ONLY",
        "M119_NO_RED_TEAM_EXECUTION_OR_SCANNER_RUNTIME",
        "M120_REMAINS_FUTURE",
    ]


def test_m119_production_red_team_harness_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_red_team_harness_record(
        source_record=_source_record()
    )

    assert record.production_red_team_harness_ref == "production-red-team-harness:m119"
    assert record.source_deployment_mode_matrix_ref == "deployment-mode-matrix:m118"
    assert record.red_team_scenario_refs == [
        "red-team-scenario-ref:m119:authority-boundary-review",
        "red-team-scenario-ref:m119:credential-boundary-review",
        "red-team-scenario-ref:m119:connector-abuse-review",
    ]
    assert record.abuse_case_refs == [
        "abuse-case-ref:m119:approval-replay",
        "abuse-case-ref:m119:credential-exfiltration-attempt",
        "abuse-case-ref:m119:production-authority-escalation",
    ]
    assert record.safety_control_refs
    assert record.mitigation_plan_refs
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "oauth token",
        "attack now",
        "exploit payload",
        "scan target",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("red_team_execution_enabled", "RED_TEAM_EXECUTION_DENIED"),
        ("attack_automation_enabled", "ATTACK_AUTOMATION_DENIED"),
        ("external_probe_enabled", "EXTERNAL_PROBE_DENIED"),
        ("exploit_generation_enabled", "EXPLOIT_GENERATION_DENIED"),
        ("security_scan_runtime_enabled", "SECURITY_SCAN_RUNTIME_DENIED"),
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
def test_m119_policy_denies_red_team_execution_and_scanner_runtime(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_production_red_team_harness_policy(
            production_readiness.ProductionRedTeamHarnessPolicy(**{field: True})
        )


def test_m119_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_red_team_harness_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M119_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M119_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M119_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M119_BASELINE_BINDING_REQUIRED"),
        (
            {"source_deployment_mode_matrix_bound": False},
            "M119_SOURCE_DEPLOYMENT_MODE_MATRIX_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M119_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M119_WORKSPACE_BINDING_REQUIRED"),
        ({"deployment_mode_bound": False}, "M119_DEPLOYMENT_MODE_BINDING_REQUIRED"),
        ({"environment_bound": False}, "M119_ENVIRONMENT_BINDING_REQUIRED"),
        ({"authority_tier_bound": False}, "M119_AUTHORITY_TIER_BINDING_REQUIRED"),
        ({"red_team_scenario_bound": False}, "M119_RED_TEAM_SCENARIO_BINDING_REQUIRED"),
        ({"abuse_case_bound": False}, "M119_ABUSE_CASE_BINDING_REQUIRED"),
        ({"threat_model_bound": False}, "M119_THREAT_MODEL_BINDING_REQUIRED"),
        ({"safety_control_bound": False}, "M119_SAFETY_CONTROL_BINDING_REQUIRED"),
        ({"mitigation_plan_bound": False}, "M119_MITIGATION_PLAN_BINDING_REQUIRED"),
        ({"accepted_checkpoint_refs": []}, "M119_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"red_team_scenario_refs": []}, "M119_RED_TEAM_SCENARIO_REF_REQUIRED"),
        ({"abuse_case_refs": []}, "M119_ABUSE_CASE_REF_REQUIRED"),
        ({"threat_model_refs": []}, "M119_THREAT_MODEL_REF_REQUIRED"),
        ({"safety_control_refs": []}, "M119_SAFETY_CONTROL_REF_REQUIRED"),
        ({"mitigation_plan_refs": []}, "M119_MITIGATION_PLAN_REF_REQUIRED"),
        ({"audit_required": False}, "M119_AUDIT_REQUIRED"),
        ({"replay_safe": False}, "M119_REPLAY_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"red_team_execution_enabled": True}, "RED_TEAM_EXECUTION_DENIED"),
        ({"attack_automation_enabled": True}, "ATTACK_AUTOMATION_DENIED"),
        ({"external_probe_enabled": True}, "EXTERNAL_PROBE_DENIED"),
        ({"exploit_generation_enabled": True}, "EXPLOIT_GENERATION_DENIED"),
        ({"security_scan_runtime_enabled": True}, "SECURITY_SCAN_RUNTIME_DENIED"),
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
        ({"side_effects_performed": ["scan target"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_red_team_harness_record(
                record.model_copy(update=update)
            )


def test_m119_denies_untrusted_or_mutated_source_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="M119_SOURCE_RECORD_REQUIRED"):
        production_readiness.build_production_red_team_harness_record(source_record=None)

    with pytest.raises(ValueError, match="RED_TEAM_EXECUTION_DENIED"):
        production_readiness.build_production_red_team_harness_record(
            source_record=source_record.model_copy(
                update={"deployment_runtime_enabled": True}
            )
        )


def test_m119_safe_summary_and_metadata_never_echo_secret_or_attack_payloads() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_red_team_harness_record(
        source_record=_source_record()
    )
    forbidden_values = [
        {"metadata": {"token": "secret-token"}},
        {"safe_summary": "run exploit payload using bearer secret-token"},
        {"red_team_scenario_refs": ["https://scan.example.com/raw"]},
        {"abuse_case_refs": ["production://account"]},
    ]

    for update in forbidden_values:
        with pytest.raises(ValueError):
            production_readiness.validate_production_red_team_harness_record(
                record.model_copy(update=update)
            )
