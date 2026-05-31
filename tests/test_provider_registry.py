from ultimate_ai_agent.core.providers import (
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderManifest,
    ProviderRegistry,
    ProviderStatus,
)


def make_provider(provider_id: str, capability: ProviderCapability = ProviderCapability.current_weather):
    return ProviderManifest(
        provider_id=provider_id,
        display_name=provider_id,
        domain=ProviderDomain.weather,
        status=ProviderStatus.enabled,
        auth_requirement=ProviderAuthRequirement.none,
        cost_class=ProviderCostClass.free_no_key,
        capabilities=[capability],
        owner="tests",
        source="tests",
        version="1.0.0",
    )


def test_provider_registry_registers_and_filters_providers():
    registry = ProviderRegistry()
    registry.register_provider(make_provider("weather_current", ProviderCapability.current_weather))
    registry.register_provider(make_provider("weather_forecast", ProviderCapability.weather_forecast))

    current = registry.list_providers(
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        status=ProviderStatus.enabled,
    )

    assert [provider.provider_id for provider in current] == ["weather_current"]
    assert registry.get_provider("weather_forecast").provider_id == "weather_forecast"
