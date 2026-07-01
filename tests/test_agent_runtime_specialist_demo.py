from ultimate_ai_agent.core.agent_runtime import (
    DETERMINISTIC_SPECIALIST_CAPABILITY_ID,
    DeterministicAgentRuntimeSpecialistAdapter,
    build_deterministic_specialist_manifest,
)
from ultimate_ai_agent.core.capabilities import CapabilityRegistry, CoordinationMode, Coordinator


def test_deterministic_specialist_runs_through_existing_coordinator_as_agent_tool() -> None:
    manifest = build_deterministic_specialist_manifest()
    registry = CapabilityRegistry()
    registry.register(manifest, DeterministicAgentRuntimeSpecialistAdapter())
    coordinator = Coordinator(registry)

    plan = coordinator.plan("inspect agent runtime refs", {"capability_ids": [DETERMINISTIC_SPECIALIST_CAPABILITY_ID]})
    artifact = coordinator.execute(plan, {})

    specialist = artifact.content[0]
    assert plan.nodes[0].mode == CoordinationMode.agent_as_tool
    assert specialist["kind"] == "agent_runtime.deterministic_specialist"
    assert specialist["content"]["safe_output_ref"].startswith("agent-runtime-output:")
    assert specialist["content"]["execution_performed"] is False
    assert specialist["content"]["provider_runtime_performed"] is False
    assert specialist["content"]["memory_write_performed"] is False
    assert specialist["content"]["context_injection_performed"] is False
    assert specialist["content"]["connector_write_performed"] is False
