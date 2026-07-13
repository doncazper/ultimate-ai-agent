from __future__ import annotations

from datetime import timedelta

from tests.test_firecrawl_cloud import _reconcile
from tests.test_searxng_search import (
    NOW,
    _approval_authority,
    _exact_lease,
    _fixture_transport,
    _request,
    _state,
)
from tests.test_web_hybrid_execution import (
    _cloud_scrape,
    _empty_local,
    _execute,
    _hybrid_request,
)
from ultimate_ai_agent.core.web_access import (
    FIRECRAWL_CLOUD_ADAPTER_REF,
    FIRECRAWL_CLOUD_PROVIDER_REF,
    SEARXNG_SEARCH_ADAPTER_REF,
    SEARXNG_SEARCH_PROVIDER_REF,
    WebResearchCostPosture,
    WebResearchProviderObservation,
    WebResearchProviderReadiness,
    WebResearchSafeDisableStatus,
    citation_from_hybrid_result,
    citations_from_searxng_result,
    execute_searxng_search,
)


def _provider(
    observation_ref: str,
    provider_ref: str,
    adapter_ref: str,
    *,
    metered: bool,
    budget_decision_ref: str,
) -> WebResearchProviderObservation:
    return WebResearchProviderObservation(
        observation_ref=observation_ref,
        provider_ref=provider_ref,
        adapter_ref=adapter_ref,
        readiness=WebResearchProviderReadiness.ready,
        cost_posture=(
            WebResearchCostPosture.free_plan_within_budget
            if metered
            else WebResearchCostPosture.not_metered
        ),
        safe_disable_status=WebResearchSafeDisableStatus.inactive,
        metered=metered,
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        latency_posture_ref="latency-posture-ref:current",
        context_posture_ref="context-posture-ref:bounded",
        routing_posture_ref="routing-posture-ref:exact-lane",
        budget_decision_ref=budget_decision_ref,
        budget_ref="budget-ref:free-plan-current" if metered else None,
    )


def test_searxng_adapter_binds_receipt_evidence_without_copying_source_text() -> None:
    request = _request()
    result = execute_searxng_search(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport([]),
        evaluated_at=NOW,
    )
    provider = _provider(
        "provider-observation-ref:searxng",
        SEARXNG_SEARCH_PROVIDER_REF,
        SEARXNG_SEARCH_ADAPTER_REF,
        metered=False,
        budget_decision_ref=result.transport_receipt.budget_decision_ref,
    )

    citations = citations_from_searxng_result(
        result,
        provider_observation_ref=provider.observation_ref,
        retrieval_ref="retrieval-ref:searxng-adapter-test",
    )

    assert len(citations) == len(result.evidence)
    assert all(item.adapter_ref == provider.adapter_ref for item in citations)
    assert all("source content remains transient" in item.safe_summary for item in citations)
    assert all(result.evidence[index].title not in item.safe_summary for index, item in enumerate(citations))
    assert all(item.evidence_ref.startswith("web-research-evidence-ref:sha256:") for item in citations)


def test_hybrid_adapter_uses_content_hash_and_generic_non_verbatim_summary() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=_cloud_scrape([]),
    )
    provider = _provider(
        "provider-observation-ref:firecrawl-cloud",
        FIRECRAWL_CLOUD_PROVIDER_REF,
        FIRECRAWL_CLOUD_ADAPTER_REF,
        metered=True,
        budget_decision_ref=(result.cloud_receipt or result.local_receipt).budget_decision_ref,
    )

    citation = citation_from_hybrid_result(
        result,
        provider_observation_ref=provider.observation_ref,
        retrieval_ref="retrieval-ref:hybrid-adapter-test",
    )

    assert citation is not None
    assert result.evidence is not None
    assert citation.evidence_ref == result.evidence.content_hash_ref
    assert citation.adapter_ref == provider.adapter_ref
    assert result.evidence.bounded_redacted_preview not in citation.safe_summary
    assert citation.summary_is_non_verbatim is True
