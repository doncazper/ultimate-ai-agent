from ultimate_ai_agent.core.runtime.local_runtime import LocalRuntimeManifest
from ultimate_ai_agent.core.runtime.capability_profile import PrivacyRoutingPolicy

def validate_runtime_safety(manifest: LocalRuntimeManifest, privacy_policy: PrivacyRoutingPolicy) -> bool:
    """Validate that local runtime capabilities and privacy configurations match policies.

    Rules:
    - Unknown context limit (<=0) is unsafe for long-running mode.
    - Advertised OpenAI-compatible runtime does not automatically imply all features/capabilities.
    - Privacy routing modes must be strictly allowed by policy.
    """
    if manifest.model_profile.context_window <= 0:
        raise ValueError("Unsafe local runtime: model context window must be greater than 0.")
        
    if manifest.privacy_mode not in privacy_policy.allowed_modes:
        raise ValueError(
            f"Privacy policy violation: runtime privacy mode '{manifest.privacy_mode}' "
            f"is not allowed in the configuration (allowed: {privacy_policy.allowed_modes})."
        )
        
    return True
