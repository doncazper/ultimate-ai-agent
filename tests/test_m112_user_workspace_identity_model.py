from typing import Any
from importlib import import_module

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)
from ultimate_ai_agent.core.production_readiness import build_production_threat_model_record


def _production_readiness() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M112 production_readiness package missing: {exc}")


def _source_record() -> Any:
    return build_production_threat_model_record(
        source_record=build_mobile_sensor_hardening_freeze_record(
            source_record=build_mobile_sensor_audit_ledger_record(
                source_record=build_mobile_kill_switch_revocation_record(
                    source_report=build_mobile_approval_renewal_ux_report()
                )
            )
        )
    )


def test_m112_user_workspace_identity_model_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_user_workspace_identity_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.UserWorkspaceIdentityStatus.identity_model_contract
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_threat_model_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_threat_model_ref == source_record.threat_model_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
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
    ]
    assert record.user_ref.startswith("user-ref:")
    assert record.workspace_ref.startswith("workspace-ref:")
    assert record.identity_boundary_refs
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.auth_runtime_enabled is False
    assert record.login_enabled is False
    assert record.session_cookie_enabled is False
    assert record.credential_handling_enabled is False
    assert record.persistent_identity_store_enabled is False
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
        "M112_USER_WORKSPACE_IDENTITY_MODEL",
        "M112_CONTRACT_ONLY",
        "M112_REVIEW_ONLY",
        "M112_NO_AUTH_RUNTIME",
        "M113_REMAINS_FUTURE",
    ]


def test_m112_user_workspace_identity_model_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_user_workspace_identity_record(
        source_record=_source_record()
    )

    assert record.identity_model_ref == "user-workspace-identity:m112"
    assert record.source_threat_model_ref == "production-threat-model:m111"
    assert record.source_baseline_ref.startswith("baseline:")
    assert record.user_ref == "user-ref:m112:primary-safe-user"
    assert record.workspace_ref == "workspace-ref:m112:primary-safe-workspace"
    assert record.identity_boundary_refs == [
        "identity-boundary-ref:m112:user-is-not-authority",
        "identity-boundary-ref:m112:workspace-is-not-root",
        "identity-boundary-ref:m112:no-auth-runtime",
    ]
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "password" not in record.safe_summary.lower()
    assert "/users/" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
        ("login_enabled", "LOGIN_DENIED"),
        ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("persistent_identity_store_enabled", "PERSISTENT_IDENTITY_STORE_DENIED"),
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
def test_m112_policy_denies_identity_runtime_authority(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_user_workspace_identity_policy(
            production_readiness.UserWorkspaceIdentityPolicy(**{field: True})
        )


def test_m112_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_user_workspace_identity_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M112_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M112_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M112_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M112_BASELINE_BINDING_REQUIRED"),
        (
            {"source_threat_model_bound": False},
            "M112_SOURCE_THREAT_MODEL_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M112_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"user_ref": ""}, "M112_USER_REF_REQUIRED"),
        ({"workspace_ref": ""}, "M112_WORKSPACE_REF_REQUIRED"),
        ({"identity_boundary_refs": []}, "M112_IDENTITY_BOUNDARY_REF_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
        ({"login_enabled": True}, "LOGIN_DENIED"),
        ({"session_cookie_enabled": True}, "SESSION_COOKIE_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        (
            {"persistent_identity_store_enabled": True},
            "PERSISTENT_IDENTITY_STORE_DENIED",
        ),
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
        ({"side_effects_performed": ["create user account"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_user_workspace_identity_record(
                record.model_copy(update=update)
            )


def test_m112_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_user_workspace_identity_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_threat_model_ref": "production-threat-model:other"},
            "M112_SOURCE_THREAT_MODEL_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M112_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M112_ACTOR_BINDING_MISMATCH"),
        (
            {"identity_model_ref": "identity-model:m112"},
            "M112_IDENTITY_MODEL_REF_REQUIRED",
        ),
        ({"user_ref": "user:m112"}, "M112_USER_REF_REQUIRED"),
        ({"workspace_ref": "workspace:m112"}, "M112_WORKSPACE_REF_REQUIRED"),
        (
            {"identity_boundary_refs": ["identity-boundary:m112"]},
            "M112_IDENTITY_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"no_effect_receipt_plan_ref": "receipt:m112"},
            "M112_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED",
        ),
        (
            {"metadata": {"workspace_token": "abc123supersecret"}},
            "SECRET_LIKE_M112_USER_WORKSPACE_IDENTITY_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_user_workspace_identity_record(
                record.model_copy(update=update)
            )


def test_m112_requires_safe_source_threat_model_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record().model_copy(
        update={"production_authority_enabled": True}
    )

    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        production_readiness.build_user_workspace_identity_record(
            source_record=source_record
        )
