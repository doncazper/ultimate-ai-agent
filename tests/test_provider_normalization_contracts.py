from ultimate_ai_agent.core.providers import (
    NewsNormalized,
    ProviderCapability,
    ProviderDomain,
    ProviderNormalizationReport,
    SourceMetadata,
    WeatherNormalized,
)


def test_weather_normalized_contract_validates_provider_neutral_shape() -> None:
    weather = WeatherNormalized(
        location_name="San Francisco",
        temperature_c=16.0,
        condition="fog",
        forecast_summary="Cool and cloudy",
    )

    assert weather.location_name == "San Francisco"
    assert weather.temperature_c == 16.0


def test_news_normalized_contract_validates_sources() -> None:
    news = NewsNormalized(
        headline="Provider registry remains contract-only",
        summary="No network fetchers were implemented.",
        source=SourceMetadata(
            source_name="Local Test Source",
            source_url="https://example.com/article",
        ),
        published_at="2026-05-31T12:00:00Z",
    )

    assert news.source.source_name == "Local Test Source"


def test_provider_normalization_report_records_contract_only_status() -> None:
    report = ProviderNormalizationReport(
        report_id="norm_1",
        provider_id="provider_test",
        domain=ProviderDomain.news,
        capability=ProviderCapability.news_search,
        normalizer_ref="normalizer.news.v0",
        normalized=True,
        warnings=["contract-only"],
    )

    assert report.normalized is True
    assert report.normalizer_ref == "normalizer.news.v0"
