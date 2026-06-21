import pytest
from ultimate_ai_agent.core.adapters import (
    AgentRuntimeAdapterManifest,
    SDKAdapterBoundaryPolicy,
    validate_adapter_boundary_policy,
)

def test_sdk_adapter_policy_validation() -> None:
    manifest = AgentRuntimeAdapterManifest(
        adapter_id="aider_adapter",
        adapter_type="aider",
        version="0.30.1"
    )
    policy = SDKAdapterBoundaryPolicy(
        policy_id="strict_boundary_1"
    )
    # Default policy with bypass_execution_contract_allowed=False should pass
    assert validate_adapter_boundary_policy(manifest, policy) is True

def test_adapter_bypass_attempt_fails() -> None:
    manifest = AgentRuntimeAdapterManifest(
        adapter_id="unsafe_adapter",
        adapter_type="openai_agents_sdk",
        version="1.0.0"
    )
    policy = SDKAdapterBoundaryPolicy(
        policy_id="bypass_policy",
        bypass_execution_contract_allowed=True
    )
    with pytest.raises(ValueError, match="cannot bypass core authority controls"):
        validate_adapter_boundary_policy(manifest, policy)

def test_adapter_direct_access_fails() -> None:
    manifest = AgentRuntimeAdapterManifest(
        adapter_id="direct_access_adapter",
        adapter_type="openhands",
        version="0.5.0"
    )
    policy = SDKAdapterBoundaryPolicy(
        policy_id="direct_access_policy",
        direct_secret_access_allowed=True
    )
    with pytest.raises(ValueError, match="is denied direct tool/memory/secret access"):
        validate_adapter_boundary_policy(manifest, policy)
