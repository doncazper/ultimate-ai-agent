from pydantic import ValidationError

from tests.m7_helpers import cloud_profile, local_profile
from ultimate_ai_agent.core.model_router import (
    ModelProviderKind,
    ModelTaskCapability,
    validate_model_capability_profile,
)


def test_model_capability_profile_is_metadata_only_and_secret_clean():
    profile = cloud_profile(credential_ref="cred_model_router")

    assert profile.provider_kind == ModelProviderKind.cloud_provider
    assert profile.credential_ref == "cred_model_router"
    assert validate_model_capability_profile(profile) is True


def test_openai_compatible_profile_does_not_imply_tool_support():
    profile = cloud_profile(
        profile_id="openai_compatible_fixture",
        capabilities=[ModelTaskCapability.chat],
    ).model_copy(update={"provider_kind": ModelProviderKind.openai_compatible})

    assert profile.provider_kind == ModelProviderKind.openai_compatible
    assert profile.supports_tools is False
    assert ModelTaskCapability.tool_calling not in profile.capabilities


def test_model_profile_rejects_unknown_fields():
    payload = local_profile().model_dump()
    payload["unexpected"] = True

    try:
        type(local_profile())(**payload)
    except ValidationError as exc:
        assert "extra" in str(exc).lower()
    else:
        raise AssertionError("ModelCapabilityProfile accepted an unknown field")
