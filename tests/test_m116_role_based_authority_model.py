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
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness():
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M116 production_readiness package missing: {exc}")


def _source_record():
    return build_production_audit_retention_policy_record(
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


def test_m116_role_based_authority_model_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_role_based_authority_model_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.RoleBasedAuthorityModelStatus.authority_model
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_production_audit_retention_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.role_bound is True
    assert record.authority_scope_bound is True
    assert record.permission_boundary_bound is True
    assert record.separation_of_duty_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_production_audit_retention_ref
        == source_record.audit_retention_policy_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m115" in record.accepted_checkpoint_refs
    assert record.role_refs
    assert record.authority_scope_refs
    assert record.permission_boundary_refs
    assert record.separation_of_duty_refs
    assert record.reviewer_role_ref.startswith("role-ref:")
    assert record.operator_role_ref.startswith("role-ref:")
    assert record.admin_role_ref.startswith("role-ref:")
    assert record.break_glass_boundary_ref.startswith("break-glass-boundary-ref:")
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.authority_runtime_enabled is False
    assert record.role_enforcement_enabled is False
    assert record.permission_enforcement_enabled is False
    assert record.auth_runtime_enabled is False
    assert record.login_enabled is False
    assert record.session_cookie_handling_enabled is False
    assert record.oauth_flow_enabled is False
    assert record.token_exchange_enabled is False
    assert record.credential_handling_enabled is False
    assert record.account_action_enabled is False
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
    assert record.background_worker_enabled is False
    assert record.remote_execution_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M116_ROLE_BASED_AUTHORITY_MODEL",
        "M116_CONTRACT_ONLY",
        "M116_REVIEW_ONLY",
        "M116_NO_AUTHORITY_RUNTIME_OR_ENFORCEMENT",
        "M117_REMAINS_FUTURE",
    ]


def test_m116_role_based_authority_model_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_role_based_authority_model_record(
        source_record=_source_record()
    )

    assert record.role_authority_model_ref == "role-authority-model:m116"
    assert record.source_production_audit_retention_ref == "audit-retention-policy:m115"
    assert record.role_refs == [
        "role-ref:m116:reviewer",
        "role-ref:m116:operator",
        "role-ref:m116:admin-review-only",
    ]
    assert record.authority_scope_refs == [
        "authority-scope-ref:m116:review-only",
        "authority-scope-ref:m116:no-runtime-enforcement",
    ]
    assert record.permission_boundary_refs == [
        "permission-boundary-ref:m116:no-production-authority",
        "permission-boundary-ref:m116:no-account-actions",
        "permission-boundary-ref:m116:no-credential-handling",
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
        "session cookie",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("authority_runtime_enabled", "AUTHORITY_RUNTIME_DENIED"),
        ("role_enforcement_enabled", "ROLE_ENFORCEMENT_DENIED"),
        ("permission_enforcement_enabled", "PERMISSION_ENFORCEMENT_DENIED"),
        ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
        ("login_enabled", "LOGIN_DENIED"),
        ("session_cookie_handling_enabled", "SESSION_COOKIE_HANDLING_DENIED"),
        ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
        ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m116_policy_denies_authority_runtime_and_enforcement(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_role_based_authority_model_policy(
            production_readiness.RoleBasedAuthorityModelPolicy(**{field: True})
        )


def test_m116_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_role_based_authority_model_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M116_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M116_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M116_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M116_BASELINE_BINDING_REQUIRED"),
        (
            {"source_production_audit_retention_bound": False},
            "M116_SOURCE_PRODUCTION_AUDIT_RETENTION_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M116_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M116_WORKSPACE_BINDING_REQUIRED"),
        ({"role_bound": False}, "M116_ROLE_BINDING_REQUIRED"),
        (
            {"authority_scope_bound": False},
            "M116_AUTHORITY_SCOPE_BINDING_REQUIRED",
        ),
        (
            {"permission_boundary_bound": False},
            "M116_PERMISSION_BOUNDARY_BINDING_REQUIRED",
        ),
        (
            {"separation_of_duty_bound": False},
            "M116_SEPARATION_OF_DUTY_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M116_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"role_refs": []}, "M116_ROLE_REF_REQUIRED"),
        ({"authority_scope_refs": []}, "M116_AUTHORITY_SCOPE_REF_REQUIRED"),
        ({"permission_boundary_refs": []}, "M116_PERMISSION_BOUNDARY_REF_REQUIRED"),
        (
            {"separation_of_duty_refs": []},
            "M116_SEPARATION_OF_DUTY_REF_REQUIRED",
        ),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"authority_runtime_enabled": True}, "AUTHORITY_RUNTIME_DENIED"),
        ({"role_enforcement_enabled": True}, "ROLE_ENFORCEMENT_DENIED"),
        (
            {"permission_enforcement_enabled": True},
            "PERMISSION_ENFORCEMENT_DENIED",
        ),
        ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
        ({"login_enabled": True}, "LOGIN_DENIED"),
        (
            {"session_cookie_handling_enabled": True},
            "SESSION_COOKIE_HANDLING_DENIED",
        ),
        ({"oauth_flow_enabled": True}, "OAUTH_FLOW_DENIED"),
        ({"token_exchange_enabled": True}, "TOKEN_EXCHANGE_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
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
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"side_effects_performed": ["enforce role"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_role_based_authority_model_record(
                record.model_copy(update=update)
            )


def test_m116_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_role_based_authority_model_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_production_audit_retention_ref": "audit-retention-policy:other"},
            "M116_SOURCE_PRODUCTION_AUDIT_RETENTION_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M116_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M116_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M116_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M116_WORKSPACE_BINDING_MISMATCH"),
        (
            {"role_authority_model_ref": "role-authority-model:other"},
            "M116_ROLE_AUTHORITY_MODEL_REF_REQUIRED",
        ),
        ({"role_refs": ["role:m116"]}, "M116_ROLE_REF_REQUIRED"),
        (
            {"authority_scope_refs": ["authority-scope:m116"]},
            "M116_AUTHORITY_SCOPE_REF_REQUIRED",
        ),
        (
            {"permission_boundary_refs": ["permission-boundary:m116"]},
            "M116_PERMISSION_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"separation_of_duty_refs": ["separation-of-duty:m116"]},
            "M116_SEPARATION_OF_DUTY_REF_REQUIRED",
        ),
        ({"reviewer_role_ref": "role:m116"}, "M116_ROLE_REF_REQUIRED"),
        (
            {"break_glass_boundary_ref": "break-glass-boundary:m116"},
            "M116_BREAK_GLASS_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"metadata": {"authorization": "Bearer abc123supersecret"}},
            "SECRET_LIKE_M116_ROLE_AUTHORITY_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_role_based_authority_model_record(
                record.model_copy(update=update)
            )


def test_m116_requires_safe_source_production_audit_retention_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="AUDIT_EXPORT_DENIED"):
        production_readiness.build_role_based_authority_model_record(
            source_record=source_record.model_copy(update={"audit_export_enabled": True})
        )
