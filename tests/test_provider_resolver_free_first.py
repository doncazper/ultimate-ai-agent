from ultimate_ai_agent.core.providers import (
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderManifest,
    ProviderRegistry,
    ProviderResolver,
    ProviderSelectionPolicy,
    ProviderStatus,
)


def provider(
    provider_id: str,
    cost_class: ProviderCostClass,
    auth_requirement: ProviderAuthRequirement,
    *,
    priority: int,
    status: ProviderStatus = ProviderStatus.enabled,
    credential_ref: str | None = None,
) -> ProviderManifest:
    return ProviderManifest(
        provider_id=provider_id,
        display_name=provider_id,
        domain=ProviderDomain.weather,
        status=status,
        auth_requirement=auth_requirement,
        cost_class=cost_class,
        capabilities=[ProviderCapability.current_weather],
        default_priority=priority,
        credential_ref=credential_ref,
        owner="tests",
        source="tests",
        version="1.0.0",
    )


def test_provider_resolver_prefers_free_no_key_and_skips_disabled():
    registry = ProviderRegistry()
    registry.register_provider(provider("paid", ProviderCostClass.paid, ProviderAuthRequirement.required_key, priority=1, credential_ref="cred_paid"))
    registry.register_provider(provider("free_disabled", ProviderCostClass.free_no_key, ProviderAuthRequirement.none, priority=0, status=ProviderStatus.disabled))
    registry.register_provider(provider("free_no_key", ProviderCostClass.free_no_key, ProviderAuthRequirement.none, priority=5))

    decision = ProviderResolver(registry).resolve(
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        policy=ProviderSelectionPolicy(policy_id="free_first", allow_paid=False),
    )

    assert decision.selected_provider_id == "free_no_key"
    assert "SELECTED_FREE_NO_KEY" in decision.reason_codes


def test_provider_resolver_skips_keyed_provider_without_available_credential():
    registry = ProviderRegistry()
    registry.register_provider(provider("free_keyed", ProviderCostClass.free_with_key, ProviderAuthRequirement.required_key, priority=0, credential_ref="cred_keyed"))

    decision = ProviderResolver(registry).resolve(
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        policy=ProviderSelectionPolicy(policy_id="free_first"),
        credential_availability={},
    )

    assert decision.selected_provider_id is None
    assert "CREDENTIAL_NOT_AVAILABLE" in decision.reason_codes


def test_provider_resolver_deterministic_priority_ordering():
    registry = ProviderRegistry()
    registry.register_provider(provider("provider_b", ProviderCostClass.free_no_key, ProviderAuthRequirement.none, priority=1))
    registry.register_provider(provider("provider_a", ProviderCostClass.free_no_key, ProviderAuthRequirement.none, priority=1))

    decision = ProviderResolver(registry).resolve(
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        policy=ProviderSelectionPolicy(policy_id="free_first"),
    )

    assert decision.selected_provider_id == "provider_a"
