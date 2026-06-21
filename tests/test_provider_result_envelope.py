from ultimate_ai_agent.core.providers import (
    ProviderCapability,
    ProviderCostClass,
    ProviderCostMetadata,
    ProviderDomain,
    ProviderResultEnvelope,
    ProviderTermsMetadata,
    WeatherNormalized,
    validate_provider_result_envelope,
)


def test_provider_result_envelope_uses_raw_ref_and_normalized_contract() -> None:
    envelope = ProviderResultEnvelope(
        result_id="res_weather_1",
        provider_id="weather_no_key",
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        input_summary="Weather for Paris",
        normalized=WeatherNormalized(
            location_name="Paris",
            temperature_c=18.5,
            condition="cloudy",
            observed_at="2026-05-31T12:00:00Z",
        ),
        raw_ref="ledger://provider/raw/res_weather_1",
        cost=ProviderCostMetadata(cost_class=ProviderCostClass.free_no_key),
        terms=ProviderTermsMetadata(terms_url="https://example.com/terms"),
    )

    assert validate_provider_result_envelope(envelope) is True
    assert envelope.raw_ref == "ledger://provider/raw/res_weather_1"


def test_provider_result_envelope_rejects_obvious_secret_leakage() -> None:
    envelope = ProviderResultEnvelope(
        result_id="res_secret",
        provider_id="weather_no_key",
        domain=ProviderDomain.weather,
        capability=ProviderCapability.current_weather,
        input_summary="api_key='abcdefghijklmnop'",
        normalized={"status": "ok"},
    )

    assert validate_provider_result_envelope(envelope) is False
