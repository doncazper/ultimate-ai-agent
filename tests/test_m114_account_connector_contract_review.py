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
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness():
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M114 production_readiness package missing: {exc}")


def _source_record():
    return build_secrets_boundary_record(
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


def test_m114_account_connector_review_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_account_connector_contract_review_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.AccountConnectorContractReviewStatus.contract_review
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_secrets_boundary_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.credential_boundary_bound is True
    assert record.auth_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_secrets_boundary_ref == source_record.secrets_boundary_ref
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
        "checkpoint:m113",
    ]
    assert record.connector_contract_refs
    assert record.connector_scope_refs
    assert record.credential_boundary_ref.startswith("credential-boundary-ref:")
    assert record.auth_boundary_ref.startswith("auth-boundary-ref:")
    assert record.data_access_boundary_refs
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.auth_runtime_enabled is False
    assert record.login_enabled is False
    assert record.session_cookie_enabled is False
    assert record.oauth_flow_enabled is False
    assert record.token_exchange_enabled is False
    assert record.credential_handling_enabled is False
    assert record.credential_storage_enabled is False
    assert record.credential_read_enabled is False
    assert record.credential_write_enabled is False
    assert record.secret_material_access_enabled is False
    assert record.secret_export_enabled is False
    assert record.vault_runtime_enabled is False
    assert record.account_connector_runtime_enabled is False
    assert record.account_connector_enabled is False
    assert record.network_access_enabled is False
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
    assert record.background_worker_enabled is False
    assert record.remote_execution_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M114_ACCOUNT_CONNECTOR_CONTRACT_REVIEW",
        "M114_CONTRACT_ONLY",
        "M114_REVIEW_ONLY",
        "M114_NO_AUTH_OR_CONNECTOR_RUNTIME",
        "M115_REMAINS_FUTURE",
    ]


def test_m114_account_connector_review_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_account_connector_contract_review_record(
        source_record=_source_record()
    )

    assert record.account_connector_review_ref == "account-connector-review:m114"
    assert record.source_secrets_boundary_ref == "secrets-boundary:m113"
    assert record.source_baseline_ref.startswith("baseline:")
    assert record.user_ref.startswith("user-ref:")
    assert record.workspace_ref.startswith("workspace-ref:")
    assert record.connector_contract_refs == [
        "connector-contract-ref:m114:read-only-candidate",
        "connector-contract-ref:m114:no-runtime-auth",
        "connector-contract-ref:m114:no-account-action",
    ]
    assert record.connector_scope_refs == [
        "connector-scope-ref:m114:declared-safe-refs-only",
        "connector-scope-ref:m114:no-live-account-data",
    ]
    assert record.credential_boundary_ref == (
        "credential-boundary-ref:m114:no-sensitive-material"
    )
    assert record.auth_boundary_ref == "auth-boundary-ref:m114:no-auth-runtime"
    assert record.data_access_boundary_refs == [
        "data-access-boundary-ref:m114:no-live-account-read",
        "data-access-boundary-ref:m114:no-account-write",
    ]
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "oauth",
        "cookie",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
        ("login_enabled", "LOGIN_DENIED"),
        ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
        ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
        ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
        ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
        ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
        ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
        ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
        ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
        ("account_connector_runtime_enabled", "ACCOUNT_CONNECTOR_RUNTIME_DENIED"),
        ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
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
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m114_policy_denies_account_connector_runtime_authority(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_account_connector_contract_review_policy(
            production_readiness.AccountConnectorContractReviewPolicy(**{field: True})
        )


def test_m114_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_account_connector_contract_review_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M114_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M114_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M114_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M114_BASELINE_BINDING_REQUIRED"),
        (
            {"source_secrets_boundary_bound": False},
            "M114_SOURCE_SECRETS_BOUNDARY_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M114_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M114_WORKSPACE_BINDING_REQUIRED"),
        (
            {"credential_boundary_bound": False},
            "M114_CREDENTIAL_BOUNDARY_BINDING_REQUIRED",
        ),
        ({"auth_boundary_bound": False}, "M114_AUTH_BOUNDARY_BINDING_REQUIRED"),
        ({"accepted_checkpoint_refs": []}, "M114_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"connector_contract_refs": []}, "M114_CONNECTOR_CONTRACT_REF_REQUIRED"),
        ({"connector_scope_refs": []}, "M114_CONNECTOR_SCOPE_REF_REQUIRED"),
        ({"credential_boundary_ref": ""}, "M114_CREDENTIAL_BOUNDARY_REF_REQUIRED"),
        ({"auth_boundary_ref": ""}, "M114_AUTH_BOUNDARY_REF_REQUIRED"),
        ({"data_access_boundary_refs": []}, "M114_DATA_ACCESS_BOUNDARY_REF_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
        ({"login_enabled": True}, "LOGIN_DENIED"),
        ({"session_cookie_enabled": True}, "SESSION_COOKIE_DENIED"),
        ({"oauth_flow_enabled": True}, "OAUTH_FLOW_DENIED"),
        ({"token_exchange_enabled": True}, "TOKEN_EXCHANGE_DENIED"),
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
        (
            {"account_connector_runtime_enabled": True},
            "ACCOUNT_CONNECTOR_RUNTIME_DENIED",
        ),
        ({"account_connector_enabled": True}, "ACCOUNT_CONNECTOR_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
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
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"side_effects_performed": ["connect account"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_account_connector_contract_review_record(
                record.model_copy(update=update)
            )


def test_m114_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_account_connector_contract_review_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_secrets_boundary_ref": "secrets-boundary:other"},
            "M114_SOURCE_SECRETS_BOUNDARY_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M114_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M114_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M114_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M114_WORKSPACE_BINDING_MISMATCH"),
        (
            {"account_connector_review_ref": "account-connector-review:other"},
            "M114_ACCOUNT_CONNECTOR_REVIEW_REF_REQUIRED",
        ),
        (
            {"connector_contract_refs": ["connector-contract:m114"]},
            "M114_CONNECTOR_CONTRACT_REF_REQUIRED",
        ),
        (
            {"connector_scope_refs": ["connector-scope:m114"]},
            "M114_CONNECTOR_SCOPE_REF_REQUIRED",
        ),
        (
            {"credential_boundary_ref": "credential-boundary:m114"},
            "M114_CREDENTIAL_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"auth_boundary_ref": "auth-boundary:m114"},
            "M114_AUTH_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"data_access_boundary_refs": ["data-access-boundary:m114"]},
            "M114_DATA_ACCESS_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"no_effect_receipt_plan_ref": "receipt:m114"},
            "M114_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED",
        ),
        (
            {"metadata": {"oauth_token": "abc123supersecret"}},
            "SECRET_LIKE_M114_ACCOUNT_CONNECTOR_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_account_connector_contract_review_record(
                record.model_copy(update=update)
            )


def test_m114_requires_safe_source_secrets_boundary_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="ACCOUNT_CONNECTOR_DENIED"):
        production_readiness.build_account_connector_contract_review_record(
            source_record=source_record.model_copy(
                update={"account_connector_enabled": True}
            )
        )
