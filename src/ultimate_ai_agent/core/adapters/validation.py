from ultimate_ai_agent.core.adapters.sdk_manifest import AgentRuntimeAdapterManifest, SDKAdapterBoundaryPolicy
from ultimate_ai_agent.core.adapters.a2a_manifest import UAAA2AAgentCardMetadataImport

def validate_adapter_boundary_policy(
    manifest: AgentRuntimeAdapterManifest,
    policy: SDKAdapterBoundaryPolicy
) -> bool:
    """Validate that external adapter manifests adhere strictly to the boundary policies.

    Rules:
    - Adapters are adapters/helpers only. They cannot claim or bypass core authority.
    - Boundary policy must reject direct tool, memory, and secret access.
    """
    if policy.bypass_execution_contract_allowed or policy.bypass_context_pack_allowed or policy.bypass_consent_ledger_allowed or policy.bypass_tool_broker_allowed or policy.bypass_secret_broker_allowed:
         raise ValueError(f"Unsafe SDK policy config: Adapter '{manifest.adapter_id}' cannot bypass core authority controls.")

    if policy.direct_tool_access_allowed or policy.direct_memory_access_allowed or policy.direct_secret_access_allowed:
        raise ValueError(f"Boundary policy violation: Adapter '{manifest.adapter_id}' is denied direct tool/memory/secret access.")

    return True

def validate_a2a_delegation_block(card: UAAA2AAgentCardMetadataImport) -> bool:
    """Confirm that real A2A delegation is blocked before the foundation gate."""
    # A2A-shaped metadata imports remain inert metadata only.
    # Real execution delegation returns False/raises error
    raise ValueError(f"Real A2A delegation to agent '{card.agent_id}' is blocked by the Foundation Gate.")
