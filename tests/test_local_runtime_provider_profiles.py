import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.model_runtime import (
    LocalModelRuntimeKind,
    LocalRuntimeProviderProfile,
    build_default_local_runtime_provider_profiles,
    validate_local_runtime_provider_profile,
)


def test_provider_profiles_are_metadata_only_and_non_authoritative():
    profiles = build_default_local_runtime_provider_profiles()

    assert profiles
    for profile in profiles:
        assert profile.kind in LocalModelRuntimeKind
        assert "planned" in profile.kind.value
        assert profile.safe_summary
        assert validate_local_runtime_provider_profile(profile) is profile
        assert profile.activation_allowed_now is False
        assert profile.real_model_call_allowed is False
        assert profile.endpoint_probe_allowed is False


def test_llama_cpp_profile_records_m23_manual_openai_completions_shape_only():
    profiles = build_default_local_runtime_provider_profiles()
    profile = next(profile for profile in profiles if profile.kind == LocalModelRuntimeKind.llama_cpp_planned)

    assert profile.activation_allowed_now is False
    assert profile.real_model_call_allowed is False
    assert profile.package_import_allowed is False
    assert profile.dependency_added is False
    assert profile.metadata == {
        "m23_manual_transport_shape": "openai_completions",
        "safe_endpoint_path_ref": "loopback_v1_completions",
        "model_artifact_family": "gguf",
    }


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("activation_allowed_now", "activation"),
        ("real_model_call_allowed", "model call"),
        ("user_content_allowed", "user content"),
        ("tool_call_allowed", "tool call"),
        ("memory_write_allowed", "memory write"),
        ("provider_credentials_allowed", "credentials"),
        ("remote_host_allowed", "remote host"),
        ("endpoint_probe_allowed", "endpoint probe"),
        ("health_check_allowed_now", "health"),
    ],
)
def test_provider_profile_rejects_m22_forbidden_capability_flags(field, message):
    profile = LocalRuntimeProviderProfile(
        kind=LocalModelRuntimeKind.ollama_planned,
        display_name="Ollama planned profile",
        safe_summary="metadata only local runtime profile",
        **{field: True},
    )

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_provider_profile(profile)


def test_provider_profile_rejects_secret_like_metadata():
    profile = LocalRuntimeProviderProfile(
        kind=LocalModelRuntimeKind.lm_studio_planned,
        display_name="LM Studio planned profile",
        safe_summary="metadata only local runtime profile",
        metadata={"credential": "local-secret-ref"},
    )

    with pytest.raises(ValueError, match="secret-like"):
        validate_local_runtime_provider_profile(profile)


def test_provider_profile_forbids_unknown_raw_fields():
    with pytest.raises(ValidationError):
        LocalRuntimeProviderProfile(
            kind=LocalModelRuntimeKind.vllm_planned,
            display_name="vLLM planned profile",
            safe_summary="metadata only local runtime profile",
            raw_payload="not allowed",
        )
