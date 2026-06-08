from importlib import import_module

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)
from ultimate_ai_agent.core.production_readiness import (
    build_production_threat_model_record,
    build_user_workspace_identity_record,
)


def _production_readiness():
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M113 production_readiness package missing: {exc}")


def _source_record():
    return build_user_workspace_identity_record(
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


def test_m113_secrets_boundary_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_secrets_boundary_record(
        source_record=source_record
    )

    assert record.status == production_readiness.SecretsBoundaryStatus.credential_vault_contract
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_identity_model_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.credential_vault_contract_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_identity_model_ref == source_record.identity_model_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert record.accepted_checkpoint_refs == [
        "checkpoint:m101",
        "checkpoint:m102",
        "checkpoint:m103",
        "checkpoint:m104",
        "checkpoint:m105",
        "checkpoint:m106",
        "checkpoint:m107",
        "checkpoint:m108",
        "checkpoint:m109",
        "checkpoint:m110",
        "checkpoint:m111",
        "checkpoint:m112",
    ]
    assert record.credential_vault_contract_ref.startswith(
        "credential-vault-contract:"
    )
    assert record.secret_boundary_refs
    assert record.credential_scope_refs
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.auth_runtime_enabled is False
    assert record.login_enabled is False
    assert record.session_cookie_enabled is False
    assert record.credential_handling_enabled is False
    assert record.credential_storage_enabled is False
    assert record.credential_read_enabled is False
    assert record.credential_write_enabled is False
    assert record.secret_material_access_enabled is False
    assert record.secret_export_enabled is False
    assert record.vault_runtime_enabled is False
    assert record.account_connector_enabled is False
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
        "M113_SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT",
        "M113_CONTRACT_ONLY",
        "M113_REVIEW_ONLY",
        "M113_NO_SECRET_MATERIAL",
        "M114_REMAINS_FUTURE",
    ]


def test_m113_secrets_boundary_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_secrets_boundary_record(
        source_record=_source_record()
    )

    assert record.secrets_boundary_ref == "secrets-boundary:m113"
    assert record.source_identity_model_ref == "user-workspace-identity:m112"
    assert record.source_baseline_ref.startswith("baseline:")
    assert record.user_ref.startswith("user-ref:")
    assert record.workspace_ref.startswith("workspace-ref:")
    assert record.credential_vault_contract_ref == (
        "credential-vault-contract:m113:no-secret-material"
    )
    assert record.secret_boundary_refs == [
        "secret-boundary-ref:m113:no-secret-material",
        "secret-boundary-ref:m113:no-credential-runtime",
        "secret-boundary-ref:m113:no-account-connector",
    ]
    assert record.credential_scope_refs == [
        "credential-scope-ref:m113:declared-safe-refs-only",
        "credential-scope-ref:m113:no-runtime-values",
    ]
    assert record.redaction_policy_ref == "redaction-policy-ref:m113:credential-safe"
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    summary = record.safe_summary.lower()
    assert "api_key" not in summary
    assert "password" not in summary
    assert "bearer" not in summary
    assert "authorization" not in summary
    assert "/users/" not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
        ("login_enabled", "LOGIN_DENIED"),
        ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
        ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
        ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
        ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
        ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
        ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
        ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
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
def test_m113_policy_denies_credential_vault_runtime_authority(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_secrets_boundary_policy(
            production_readiness.SecretsBoundaryPolicy(**{field: True})
        )


def test_m113_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_secrets_boundary_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M113_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M113_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M113_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M113_BASELINE_BINDING_REQUIRED"),
        (
            {"source_identity_model_bound": False},
            "M113_SOURCE_IDENTITY_MODEL_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M113_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M113_WORKSPACE_BINDING_REQUIRED"),
        (
            {"credential_vault_contract_bound": False},
            "M113_CREDENTIAL_VAULT_CONTRACT_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M113_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        (
            {"credential_vault_contract_ref": ""},
            "M113_CREDENTIAL_VAULT_CONTRACT_REF_REQUIRED",
        ),
        ({"secret_boundary_refs": []}, "M113_SECRET_BOUNDARY_REF_REQUIRED"),
        ({"credential_scope_refs": []}, "M113_CREDENTIAL_SCOPE_REF_REQUIRED"),
        ({"redaction_policy_ref": ""}, "M113_REDACTION_POLICY_REF_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
        ({"login_enabled": True}, "LOGIN_DENIED"),
        ({"session_cookie_enabled": True}, "SESSION_COOKIE_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"credential_storage_enabled": True}, "CREDENTIAL_STORAGE_DENIED"),
        ({"credential_read_enabled": True}, "CREDENTIAL_READ_DENIED"),
        ({"credential_write_enabled": True}, "CREDENTIAL_WRITE_DENIED"),
        (
            {"secret_material_access_enabled": True},
            "SECRET_MATERIAL_ACCESS_DENIED",
        ),
        ({"secret_export_enabled": True}, "SECRET_EXPORT_DENIED"),
        ({"vault_runtime_enabled": True}, "VAULT_RUNTIME_DENIED"),
        ({"account_connector_enabled": True}, "ACCOUNT_CONNECTOR_DENIED"),
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
        ({"side_effects_performed": ["read credential"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_secrets_boundary_record(
                record.model_copy(update=update)
            )


def test_m113_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_secrets_boundary_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_identity_model_ref": "user-workspace-identity:other"},
            "M113_SOURCE_IDENTITY_MODEL_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M113_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M113_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M113_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M113_WORKSPACE_BINDING_MISMATCH"),
        (
            {"secrets_boundary_ref": "secrets-boundary:other"},
            "M113_SECRETS_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"credential_vault_contract_ref": "credential-vault:m113"},
            "M113_CREDENTIAL_VAULT_CONTRACT_REF_REQUIRED",
        ),
        (
            {"secret_boundary_refs": ["secret-boundary:m113"]},
            "M113_SECRET_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"credential_scope_refs": ["credential-scope:m113"]},
            "M113_CREDENTIAL_SCOPE_REF_REQUIRED",
        ),
        (
            {"redaction_policy_ref": "redaction-policy:m113"},
            "M113_REDACTION_POLICY_REF_REQUIRED",
        ),
        (
            {"no_effect_receipt_plan_ref": "receipt:m113"},
            "M113_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED",
        ),
        (
            {"metadata": {"credential_token": "abc123supersecret"}},
            "SECRET_LIKE_M113_SECRETS_BOUNDARY_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_secrets_boundary_record(
                record.model_copy(update=update)
            )


def test_m113_requires_safe_source_identity_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="CREDENTIAL_HANDLING_DENIED"):
        production_readiness.build_secrets_boundary_record(
            source_record=source_record.model_copy(
                update={"credential_handling_enabled": True}
            )
        )
