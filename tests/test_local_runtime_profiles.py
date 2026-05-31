import pytest
from ultimate_ai_agent.core.runtime import (
    LocalRuntimeManifest,
    LocalModelProfile,
    PrivacyRoutingPolicy,
    validate_runtime_safety,
)

def test_local_runtime_validation():
    profile = LocalModelProfile(
        model_id="llama3-8b",
        model_family="llama3",
        context_window=8192
    )
    manifest = LocalRuntimeManifest(
        runtime_id="rt_ollama",
        runtime_type="ollama",
        model_profile=profile,
        privacy_mode="local_only"
    )
    policy = PrivacyRoutingPolicy(
        policy_id="privacy_policy_1",
        allowed_modes=["local_only"]
    )
    assert validate_runtime_safety(manifest, policy) is True

def test_unsafe_runtime_rejected():
    # Unknown context window (0 or negative)
    profile = LocalModelProfile(
        model_id="llama_unknown",
        context_window=0
    )
    manifest = LocalRuntimeManifest(
        runtime_id="rt_unsafe",
        runtime_type="llama_cpp",
        model_profile=profile
    )
    policy = PrivacyRoutingPolicy(policy_id="p1", allowed_modes=["local_only"])
    with pytest.raises(ValueError, match="model context window must be greater than 0"):
        validate_runtime_safety(manifest, policy)

def test_privacy_routing_violation():
    profile = LocalModelProfile(
        model_id="llama3-8b",
        context_window=8192
    )
    # Manifest configured for cloud but policy allows only local_only
    manifest = LocalRuntimeManifest(
        runtime_id="rt_cloud",
        runtime_type="cloud_provider_placeholder",
        model_profile=profile,
        privacy_mode="cloud_allowed"
    )
    policy = PrivacyRoutingPolicy(
        policy_id="privacy_policy_local",
        allowed_modes=["local_only"]
    )
    with pytest.raises(ValueError, match="Privacy policy violation"):
        validate_runtime_safety(manifest, policy)
