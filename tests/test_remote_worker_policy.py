import pytest

from tests.m7_helpers import actor
from ultimate_ai_agent.core.remote_workers import (
    NodeCapabilitySet,
    NodeIdentity,
    PrivateMeshProviderKind,
    RemoteAuditContext,
    RemoteExecutionPolicy,
    RemoteJobEnvelope,
    RemoteNode,
    RemoteNodeRegistry,
    RemoteNodeStatus,
    RemoteRiskLevel,
    RemoteTransportSelectionPolicy,
    default_remote_transport_registry,
    evaluate_remote_job_policy,
)


def _envelope(**overrides):
    payload = {
        "job_id": "job_policy",
        "correlation_id": "corr_policy",
        "node_id": "node_mock",
        "transport_id": "mock_metadata",
        "task_summary": "Dry-run metadata validation.",
        "requested_capabilities": ["dry_run"],
        "risk_level": RemoteRiskLevel.low,
        "audit_context": RemoteAuditContext(run_id="run_policy", correlation_id="corr_policy", actor_context=actor()),
    }
    payload.update(overrides)
    return RemoteJobEnvelope(**payload)


def _node_registry():
    registry = RemoteNodeRegistry()
    registry.register_node(
        RemoteNode(
            node_id="node_mock",
            identity=NodeIdentity(node_id="node_mock", display_name="Mock Node", owner="tests", source="fixture", version="0.0.0"),
            status=RemoteNodeStatus.mock_available,
            capabilities=NodeCapabilitySet(),
            allowed_transport_ids=["mock_metadata"],
        )
    )
    return registry


def test_remote_policy_defaults_safe_and_denies_unknowns():
    policy = RemoteExecutionPolicy(policy_id="policy_remote")
    decision = evaluate_remote_job_policy(_envelope(), RemoteNodeRegistry(), default_remote_transport_registry(), policy)

    assert policy.remote_workers_enabled is False
    assert policy.remote_dispatch_enabled is False
    assert policy.remote_approvals_enabled is False
    assert policy.allow_network is False
    assert decision.allowed is False
    assert "REMOTE_WORKERS_DISABLED" in decision.reason_codes
    assert "REMOTE_NODE_UNKNOWN" in decision.reason_codes


def test_remote_policy_rejects_tailnet_and_personal_data_enable_flags():
    for field, reason in [
        ("remote_tailnet_enabled", "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5"),
        ("remote_personal_data_enabled", "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5"),
    ]:
        with pytest.raises(ValueError, match=reason):
            RemoteExecutionPolicy(policy_id=f"policy_{field}", **{field: True})


def test_remote_policy_rejects_both_unsupported_enable_flags_safely():
    with pytest.raises(ValueError) as excinfo:
        RemoteExecutionPolicy(
            policy_id="policy_remote_unsupported",
            remote_tailnet_enabled=True,
            remote_personal_data_enabled=True,
        )

    message = str(excinfo.value)
    assert "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" in message
    assert "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" in message


def test_remote_transport_selection_policy_is_open_source_first_and_planned_only():
    policy = RemoteTransportSelectionPolicy(policy_id="mesh_selection")

    assert policy.prefer_open_source_first is True
    assert policy.prefer_self_hosted_control_plane is True
    assert policy.allow_proprietary_control_plane is False
    assert policy.require_explicit_approval_for_proprietary_control_plane is True
    assert policy.allowed_provider_kinds[:2] == [
        PrivateMeshProviderKind.headscale_planned,
        PrivateMeshProviderKind.generic_wireguard_planned,
    ]
    assert PrivateMeshProviderKind.tailscale_planned in policy.blocked_provider_kinds


def test_remote_policy_denies_risky_capabilities_even_when_flagged_on():
    policy = RemoteExecutionPolicy(
        policy_id="policy_remote",
        remote_workers_enabled=True,
        remote_transports_enabled=True,
        remote_accept_jobs=True,
    )

    for capability, reason in [
        ("personal_data", "REMOTE_PERSONAL_DATA_DENIED"),
        ("write", "REMOTE_WRITE_DENIED"),
        ("send", "REMOTE_SEND_DENIED"),
        ("approve", "REMOTE_APPROVAL_DENIED"),
        ("subagent", "REMOTE_SUBAGENT_DENIED"),
    ]:
        decision = evaluate_remote_job_policy(
            _envelope(requested_capabilities=[capability]),
            _node_registry(),
            default_remote_transport_registry(),
            policy,
        )
        assert decision.allowed is False
        assert reason in decision.reason_codes

    critical = evaluate_remote_job_policy(
        _envelope(risk_level=RemoteRiskLevel.critical),
        _node_registry(),
        default_remote_transport_registry(),
        policy,
    )
    assert critical.allowed is False
    assert "REMOTE_CRITICAL_DENIED" in critical.reason_codes
