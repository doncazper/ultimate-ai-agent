from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_runtime.enums import (
    LocalModelRuntimeKind,
    LocalModelRuntimeStatus,
    LocalModelRuntimeTransportKind,
    LocalModelRuntimeTrustLevel,
)
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class _LocalRuntimeProviderModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class LocalRuntimeProviderProfile(_LocalRuntimeProviderModel):
    profile_ref: str = Field(default="local_runtime_profile_m22", min_length=1)
    kind: LocalModelRuntimeKind
    display_name: str = Field(..., min_length=1)
    status: LocalModelRuntimeStatus = LocalModelRuntimeStatus.planned_disabled
    trust_level: LocalModelRuntimeTrustLevel = LocalModelRuntimeTrustLevel.local_metadata_only
    transport_kind: LocalModelRuntimeTransportKind = LocalModelRuntimeTransportKind.loopback_http_metadata
    safe_summary: str = Field(..., min_length=1)
    activation_allowed_now: bool = False
    real_model_call_allowed: bool = False
    user_content_allowed: bool = False
    tool_call_allowed: bool = False
    memory_write_allowed: bool = False
    provider_credentials_allowed: bool = False
    remote_host_allowed: bool = False
    endpoint_probe_allowed: bool = False
    health_check_allowed_now: bool = False
    package_import_allowed: bool = False
    dependency_added: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_default_local_runtime_provider_profiles() -> list[LocalRuntimeProviderProfile]:
    profiles = [
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_ollama_m22",
            kind=LocalModelRuntimeKind.ollama_planned,
            display_name="Ollama planned profile",
            safe_summary="Metadata-only planned profile for a future loopback local runtime.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_llama_cpp_m22",
            kind=LocalModelRuntimeKind.llama_cpp_planned,
            display_name="llama.cpp planned profile",
            safe_summary="Metadata-only planned profile for a future local runtime family.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_mlx_m22",
            kind=LocalModelRuntimeKind.mlx_planned,
            display_name="MLX planned profile",
            safe_summary="Metadata-only planned profile for a future local runtime family.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_vllm_m22",
            kind=LocalModelRuntimeKind.vllm_planned,
            display_name="vLLM planned profile",
            safe_summary="Metadata-only planned profile for a future local runtime family.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_lm_studio_m22",
            kind=LocalModelRuntimeKind.lm_studio_planned,
            display_name="LM Studio planned profile",
            safe_summary="Metadata-only planned profile for a future loopback local runtime.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_openai_compatible_local_m22",
            kind=LocalModelRuntimeKind.openai_compatible_local_planned,
            display_name="OpenAI-compatible local planned profile",
            safe_summary="Metadata-only planned profile for a future local-compatible endpoint.",
        ),
        LocalRuntimeProviderProfile(
            profile_ref="local_runtime_profile_generic_loopback_http_m22",
            kind=LocalModelRuntimeKind.generic_loopback_http_planned,
            display_name="Generic loopback HTTP planned profile",
            safe_summary="Metadata-only planned profile for a future loopback HTTP runtime.",
        ),
    ]
    for profile in profiles:
        validate_local_runtime_provider_profile(profile)
    return profiles


def validate_local_runtime_provider_profile(profile: LocalRuntimeProviderProfile) -> LocalRuntimeProviderProfile:
    assert_secret_clean(profile.safe_summary, field_name="safe_summary")
    for value in profile.metadata_refs:
        assert_secret_clean(value, field_name="metadata_refs")
    _assert_safe_metadata(profile.metadata)
    if profile.status != LocalModelRuntimeStatus.planned_disabled:
        raise ValueError("local runtime provider profile must remain planned-disabled")
    if profile.activation_allowed_now:
        raise ValueError("local runtime activation is not allowed in M22")
    if profile.real_model_call_allowed:
        raise ValueError("real model call is not allowed in M22")
    if profile.user_content_allowed:
        raise ValueError("user content is not allowed in M22")
    if profile.tool_call_allowed:
        raise ValueError("tool call is not allowed in M22")
    if profile.memory_write_allowed:
        raise ValueError("memory write is not allowed in M22")
    if profile.provider_credentials_allowed:
        raise ValueError("provider credentials are not allowed in M22")
    if profile.remote_host_allowed:
        raise ValueError("remote host is not allowed in M22")
    if profile.endpoint_probe_allowed:
        raise ValueError("endpoint probe is not allowed in M22")
    if profile.health_check_allowed_now:
        raise ValueError("health check is not allowed now in M22")
    if profile.package_import_allowed:
        raise ValueError("runtime package import is not allowed in M22")
    if profile.dependency_added:
        raise ValueError("runtime dependency is not added in M22")
    return profile


def _assert_safe_metadata(metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        if _is_secret_metadata_key(str(key)):
            raise ValueError("metadata contains secret-like content.")
        assert_secret_clean(str(key), field_name="metadata")
        if isinstance(value, dict):
            _assert_safe_metadata(value)
        elif isinstance(value, list):
            for item in value:
                assert_secret_clean(str(item), field_name="metadata")
        else:
            assert_secret_clean(str(value), field_name="metadata")


def _is_secret_metadata_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        fragment in lowered
        for fragment in [
            "secret",
            "credential",
            "password",
            "authorization",
            "access_" + "token",
            "refresh_" + "token",
            "admin_" + "token",
            "session_" + "token",
            "api_" + "key",
        ]
    )
