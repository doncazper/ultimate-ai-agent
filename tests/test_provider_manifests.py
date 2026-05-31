import pytest

from ultimate_ai_agent.core.providers import (
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderManifest,
    ProviderStatus,
    validate_provider_manifest,
)


def test_provider_manifest_validates_without_raw_secret():
    manifest = ProviderManifest(
        provider_id="weather_no_key",
        display_name="Weather No Key",
        domain=ProviderDomain.weather,
        status=ProviderStatus.enabled,
        auth_requirement=ProviderAuthRequirement.none,
        cost_class=ProviderCostClass.free_no_key,
        capabilities=[ProviderCapability.current_weather],
        allowed_domains=["api.weather.example"],
        owner="core",
        source="tests",
        version="1.0.0",
    )

    assert validate_provider_manifest(manifest) is True


def test_provider_manifest_rejects_credentialed_provider_without_ref():
    manifest = ProviderManifest(
        provider_id="weather_keyed",
        display_name="Weather Keyed",
        domain=ProviderDomain.weather,
        status=ProviderStatus.enabled,
        auth_requirement=ProviderAuthRequirement.required_key,
        cost_class=ProviderCostClass.free_with_key,
        capabilities=[ProviderCapability.current_weather],
        owner="core",
        source="tests",
        version="1.0.0",
    )

    with pytest.raises(ValueError, match="credential_ref"):
        validate_provider_manifest(manifest)


def test_provider_manifest_rejects_raw_secret_metadata():
    manifest = ProviderManifest(
        provider_id="weather_secret",
        display_name="Weather Secret",
        domain=ProviderDomain.weather,
        status=ProviderStatus.enabled,
        auth_requirement=ProviderAuthRequirement.none,
        cost_class=ProviderCostClass.free_no_key,
        capabilities=[ProviderCapability.current_weather],
        owner="core",
        source="tests",
        version="1.0.0",
        metadata={"note": "api_key='abcdefghijklmnop'"},
    )

    with pytest.raises(ValueError, match="raw secrets"):
        validate_provider_manifest(manifest)
