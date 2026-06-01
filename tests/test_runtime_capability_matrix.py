from ultimate_ai_agent.core.runtime_readiness import (
    RuntimeCapabilityStatus,
    RuntimeSurface,
    build_matrix,
)


def _entries_by_surface():
    matrix = build_matrix(baseline_version="0.15.0")
    return {entry.surface: entry for entry in matrix.entries}


def test_runtime_capability_matrix_has_static_safe_statuses():
    entries = _entries_by_surface()

    local_loopback_policy = entries[RuntimeSurface.local_loopback_policy]
    assert local_loopback_policy.status == RuntimeCapabilityStatus.supported
    assert "validation-only" in local_loopback_policy.description
    assert "manual-only" in local_loopback_policy.description
    assert "approval-gated" in local_loopback_policy.description
    assert local_loopback_policy.metadata["validation_only_contract"] is True
    assert local_loopback_policy.metadata["real_smoke_execution"] == "manual_only"

    assert entries[RuntimeSurface.remote_worker_foundation].status == RuntimeCapabilityStatus.dry_run_only
    assert entries[RuntimeSurface.private_mesh_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.tailnet_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.headscale_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.generic_wireguard_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.tailscale_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.cloud_provider_runtime].status == RuntimeCapabilityStatus.blocked
    assert entries[RuntimeSurface.manual_loopback_smoke].status == RuntimeCapabilityStatus.manual_only
    assert entries[RuntimeSurface.mobile_companion_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.device_capability_broker_planned].status == RuntimeCapabilityStatus.planned_disabled
    assert entries[RuntimeSurface.codex_plugin_governance].metadata["documentation_only"] is True


def test_runtime_capability_matrix_blocks_runtime_expansion():
    matrix = build_matrix(baseline_version="0.15.0")

    assert matrix.assert_no_runtime_expansion() is True
    assert matrix.assert_foundation_gate_coverage() is True
    for entry in matrix.entries:
        assert entry.real_model_call_allowed is False
        assert entry.cloud_allowed is False
        assert entry.secrets_allowed is False
    assert matrix.summary["production_runtime_ready"] is False
