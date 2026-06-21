import pytest

from tests.m7_helpers import actor
from ultimate_ai_agent.core.remote_workers import (
    NodeCapabilitySet,
    NodeIdentity,
    RemoteJobEnvelope,
    RemoteJobResult,
    RemoteJobStatus,
    RemoteNode,
    RemoteNodeStatus,
    RemoteOutputTrustLevel,
    RemoteRiskLevel,
    RemoteTransportDescriptor,
    RemoteTransportKind,
    RemoteTransportStatus,
    RemoteAuditContext,
)


def test_remote_node_risky_capabilities_default_false_and_secret_metadata_rejected() -> None:
    capabilities = NodeCapabilitySet()
    node = RemoteNode(
        node_id="node_local_mock",
        identity=NodeIdentity(node_id="node_local_mock", display_name="Local Mock", owner="tests", source="fixture", version="0.0.0"),
        status=RemoteNodeStatus.mock_available,
        capabilities=capabilities,
        allowed_transport_ids=["transport_mock"],
    )

    assert node.capabilities.can_execute_jobs is False
    assert node.capabilities.can_launch_subagents is False
    assert node.capabilities.can_call_tools is False
    assert node.capabilities.can_approve_actions is False
    assert node.capabilities.can_run_critical is False

    with pytest.raises(ValueError):
        NodeIdentity(
            node_id="node_secret",
            display_name="Secret Node",
            owner="tests",
            source="fixture",
            version="0.0.0",
            metadata={"api_key": "abcdefghijklmnop"},
        )


def test_transport_descriptor_defaults_are_disabled_and_planned_only() -> None:
    descriptor = RemoteTransportDescriptor(
        transport_id="tailnet_planned",
        kind=RemoteTransportKind.tailnet_planned,
        status=RemoteTransportStatus.planned,
        display_name="Tailnet Planned",
        description="Metadata only.",
        planned_only=True,
        owner="tests",
        source="fixture",
        version="0.0.0",
    )

    assert descriptor.enabled is False
    assert descriptor.requires_network is False
    assert descriptor.supports_dispatch is False
    assert descriptor.supports_file_transfer is False
    assert descriptor.supports_subagents is False


def test_remote_job_envelope_and_result_are_dry_run_only_and_untrusted() -> None:
    audit = RemoteAuditContext(run_id="run_remote", correlation_id="corr_remote", actor_context=actor())
    envelope = RemoteJobEnvelope(
        job_id="job_remote",
        correlation_id="corr_remote",
        node_id="node_local_mock",
        transport_id="transport_mock",
        task_summary="Validate remote worker foundation metadata.",
        requested_capabilities=["dry_run"],
        risk_level=RemoteRiskLevel.low,
        audit_context=audit,
    )
    result = RemoteJobResult(
        job_id=envelope.job_id,
        correlation_id=envelope.correlation_id,
        status=RemoteJobStatus.simulated_result,
        output_trust_level=RemoteOutputTrustLevel.untrusted_remote_output,
        output_summary="Dry-run only; no remote execution occurred.",
    )

    assert result.dispatch_performed is False
    assert result.remote_execution_performed is False
    assert result.subagent_launched is False
    assert result.tools_executed == []
    assert result.network_connections_opened == []

    with pytest.raises(ValueError):
        RemoteJobEnvelope(
            job_id="job_secret",
            correlation_id="corr_secret",
            node_id="node_local_mock",
            transport_id="transport_mock",
            task_summary="api_key='abcdefghijklmnop'",
            requested_capabilities=["dry_run"],
            risk_level=RemoteRiskLevel.low,
            audit_context=audit,
        )

