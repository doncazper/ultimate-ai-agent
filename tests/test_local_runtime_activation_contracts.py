from ultimate_ai_agent.core.model_runtime import (
    LocalModelRuntimeKind,
    LocalModelRuntimeStatus,
    build_default_local_runtime_activation_manifest,
    validate_local_runtime_activation_manifest,
)


EXPECTED_RUNTIME_KINDS = {
    LocalModelRuntimeKind.ollama_planned,
    LocalModelRuntimeKind.llama_cpp_planned,
    LocalModelRuntimeKind.mlx_planned,
    LocalModelRuntimeKind.vllm_planned,
    LocalModelRuntimeKind.lm_studio_planned,
    LocalModelRuntimeKind.openai_compatible_local_planned,
    LocalModelRuntimeKind.generic_loopback_http_planned,
}


def test_default_local_runtime_activation_manifest_is_contract_only() -> None:
    manifest = build_default_local_runtime_activation_manifest()

    assert manifest.baseline_version == "0.26.0"
    assert manifest.status == LocalModelRuntimeStatus.contract_only
    assert manifest.activation_allowed_now is False
    assert manifest.real_model_call_allowed is False
    assert manifest.runtime_execution_allowed is False
    assert manifest.provider_call_allowed is False
    assert manifest.endpoint_probe_allowed is False
    assert manifest.user_content_allowed is False
    assert manifest.tool_call_allowed is False
    assert manifest.memory_write_allowed is False
    assert manifest.secret_material_allowed is False
    assert manifest.no_model_called is True
    assert manifest.no_runtime_activated is True
    assert manifest.no_endpoint_contacted is True

    assert validate_local_runtime_activation_manifest(manifest) is manifest


def test_default_manifest_profiles_cover_planned_local_runtime_families() -> None:
    manifest = build_default_local_runtime_activation_manifest()
    kinds = {profile.kind for profile in manifest.provider_profiles}

    assert kinds == EXPECTED_RUNTIME_KINDS
    for profile in manifest.provider_profiles:
        assert profile.status == LocalModelRuntimeStatus.planned_disabled
        assert profile.activation_allowed_now is False
        assert profile.real_model_call_allowed is False
        assert profile.user_content_allowed is False
        assert profile.tool_call_allowed is False
        assert profile.memory_write_allowed is False
        assert profile.provider_credentials_allowed is False
        assert profile.remote_host_allowed is False
        assert profile.endpoint_probe_allowed is False
        assert profile.health_check_allowed_now is False
