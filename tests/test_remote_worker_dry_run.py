from tests.m7_helpers import actor
from ultimate_ai_agent.core.remote_workers import (
    RemoteDryRunBuilder,
    RemoteExecutionPolicy,
    RemoteJobStatus,
    RemoteOutputTrustLevel,
    default_remote_node_registry,
    default_remote_transport_registry,
)


def test_dry_run_builds_envelope_and_dispatches_nothing():
    builder = RemoteDryRunBuilder()
    policy = RemoteExecutionPolicy(
        policy_id="policy_remote",
        remote_workers_enabled=True,
        remote_transports_enabled=True,
        remote_accept_jobs=True,
    )
    envelope = builder.build_envelope(
        task_summary="Validate dry-run only remote foundation.",
        node_id="mock_node",
        transport_id="mock_metadata",
        actor_context=actor(),
        policy=policy,
    )
    result = builder.dry_run(envelope, default_remote_node_registry(), default_remote_transport_registry(), policy)

    assert envelope.correlation_id
    assert result.status == RemoteJobStatus.simulated_result
    assert result.dispatch_performed is False
    assert result.remote_execution_performed is False
    assert result.subagent_launched is False
    assert result.tools_executed == []
    assert result.network_connections_opened == []
    assert result.output_trust_level == RemoteOutputTrustLevel.untrusted_remote_output


def test_dry_run_with_tailnet_planned_transport_is_blocked():
    builder = RemoteDryRunBuilder()
    policy = RemoteExecutionPolicy(
        policy_id="policy_remote",
        remote_workers_enabled=True,
        remote_transports_enabled=True,
        remote_accept_jobs=True,
    )
    envelope = builder.build_envelope(
        task_summary="Validate planned tailnet transport.",
        node_id="mock_node",
        transport_id="tailnet_planned",
        actor_context=actor(),
        policy=policy,
    )
    result = builder.dry_run(envelope, default_remote_node_registry(), default_remote_transport_registry(), policy)

    assert result.status == RemoteJobStatus.dispatch_blocked
    assert "REMOTE_TRANSPORT_PLANNED_ONLY" in result.warnings
    assert result.dispatch_performed is False

