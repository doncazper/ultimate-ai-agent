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
    build_role_based_authority_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M117 production_readiness package missing: {exc}")


def _source_record() -> Any:
    return build_role_based_authority_model_record(
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


def test_m117_remote_agent_coordination_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_remote_agent_coordination_contract_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.RemoteAgentCoordinationContractStatus.coordination_contract
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_role_authority_model_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.remote_agent_bound is True
    assert record.coordination_scope_bound is True
    assert record.trust_boundary_bound is True
    assert record.handoff_protocol_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_role_authority_model_ref == source_record.role_authority_model_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m116" in record.accepted_checkpoint_refs
    assert record.remote_agent_refs
    assert record.coordination_scope_refs
    assert record.trust_boundary_refs
    assert record.handoff_protocol_refs
    assert record.communication_channel_refs
    assert record.revocation_boundary_ref.startswith("revocation-boundary-ref:")
    assert record.production_authority_enabled is False
    assert record.remote_agent_runtime_enabled is False
    assert record.remote_dispatch_enabled is False
    assert record.remote_execution_enabled is False
    assert record.live_connection_enabled is False
    assert record.network_access_enabled is False
    assert record.agent_spawn_enabled is False
    assert record.background_worker_enabled is False
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
        "M117_REMOTE_AGENT_COORDINATION_CONTRACT",
        "M117_CONTRACT_ONLY",
        "M117_REVIEW_ONLY",
        "M117_NO_REMOTE_RUNTIME_OR_DISPATCH",
        "M118_REMAINS_FUTURE",
    ]


def test_m117_remote_agent_coordination_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_remote_agent_coordination_contract_record(
        source_record=_source_record()
    )

    assert record.remote_coordination_contract_ref == "remote-agent-coordination:m117"
    assert record.source_role_authority_model_ref == "role-authority-model:m116"
    assert record.remote_agent_refs == [
        "remote-agent-ref:m117:reviewed-peer-agent",
        "remote-agent-ref:m117:coordination-placeholder",
    ]
    assert record.coordination_scope_refs == [
        "coordination-scope-ref:m117:review-only",
        "coordination-scope-ref:m117:no-live-dispatch",
    ]
    assert record.trust_boundary_refs == [
        "trust-boundary-ref:m117:no-runtime-trust",
        "trust-boundary-ref:m117:no-credential-transfer",
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
        "remote execution",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
        ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("live_connection_enabled", "LIVE_CONNECTION_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("agent_spawn_enabled", "AGENT_SPAWN_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
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
def test_m117_policy_denies_remote_runtime_and_dispatch(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_remote_agent_coordination_contract_policy(
            production_readiness.RemoteAgentCoordinationContractPolicy(**{field: True})
        )


def test_m117_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_remote_agent_coordination_contract_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M117_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M117_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M117_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M117_BASELINE_BINDING_REQUIRED"),
        (
            {"source_role_authority_model_bound": False},
            "M117_SOURCE_ROLE_AUTHORITY_MODEL_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M117_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M117_WORKSPACE_BINDING_REQUIRED"),
        ({"remote_agent_bound": False}, "M117_REMOTE_AGENT_BINDING_REQUIRED"),
        (
            {"coordination_scope_bound": False},
            "M117_COORDINATION_SCOPE_BINDING_REQUIRED",
        ),
        ({"trust_boundary_bound": False}, "M117_TRUST_BOUNDARY_BINDING_REQUIRED"),
        (
            {"handoff_protocol_bound": False},
            "M117_HANDOFF_PROTOCOL_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M117_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"remote_agent_refs": []}, "M117_REMOTE_AGENT_REF_REQUIRED"),
        ({"coordination_scope_refs": []}, "M117_COORDINATION_SCOPE_REF_REQUIRED"),
        ({"trust_boundary_refs": []}, "M117_TRUST_BOUNDARY_REF_REQUIRED"),
        ({"handoff_protocol_refs": []}, "M117_HANDOFF_PROTOCOL_REF_REQUIRED"),
        (
            {"communication_channel_refs": []},
            "M117_COMMUNICATION_CHANNEL_REF_REQUIRED",
        ),
        ({"audit_required": False}, "M117_AUDIT_REQUIRED"),
        ({"replay_safe": False}, "M117_REPLAY_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"remote_agent_runtime_enabled": True}, "REMOTE_AGENT_RUNTIME_DENIED"),
        ({"remote_dispatch_enabled": True}, "REMOTE_DISPATCH_DENIED"),
        ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
        ({"live_connection_enabled": True}, "LIVE_CONNECTION_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"agent_spawn_enabled": True}, "AGENT_SPAWN_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
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
        ({"side_effects_performed": ["dispatch"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_remote_agent_coordination_contract_record(
                record.model_copy(update=update)
            )


def test_m117_denies_untrusted_or_mutated_source_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="M117_SOURCE_RECORD_REQUIRED"):
        production_readiness.build_remote_agent_coordination_contract_record(
            source_record=None
        )

    with pytest.raises(ValueError, match="AUTHORITY_RUNTIME_DENIED"):
        production_readiness.build_remote_agent_coordination_contract_record(
            source_record=source_record.model_copy(
                update={"authority_runtime_enabled": True}
            )
        )


def test_m117_safe_summary_and_metadata_never_echo_secret_or_remote_payloads() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_remote_agent_coordination_contract_record(
        source_record=_source_record()
    )
    forbidden_values = [
        {"metadata": {"token": "secret-token"}},
        {"safe_summary": "connect using bearer secret-token"},
        {"remote_agent_refs": ["https://agent.example.com/raw"]},
        {"communication_channel_refs": ["ssh://agent.example.com"]},
    ]

    for update in forbidden_values:
        with pytest.raises(ValueError):
            production_readiness.validate_remote_agent_coordination_contract_record(
                record.model_copy(update=update)
            )
