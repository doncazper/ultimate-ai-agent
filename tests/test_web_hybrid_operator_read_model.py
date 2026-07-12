from __future__ import annotations

from ultimate_ai_agent.core.capability_availability import (
    build_capability_availability_read_model,
    build_web_hybrid_availability_read_model,
)
from ultimate_ai_agent.core.web_access import (
    FIRECRAWL_CLOUD_ADAPTER_REF,
    FIRECRAWL_CLOUD_CAPABILITY_REF,
    FIRECRAWL_CLOUD_LANE_REF,
    FIRECRAWL_CLOUD_PROVIDER_REF,
    FIRECRAWL_MARKDOWN_ADAPTER_REF,
    FIRECRAWL_MARKDOWN_CAPABILITY_REF,
    FIRECRAWL_MARKDOWN_LANE_REF,
    FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
    SEARXNG_SEARCH_ADAPTER_REF,
    SEARXNG_SEARCH_CAPABILITY_REF,
    SEARXNG_SEARCH_LANE_REF,
    SEARXNG_SEARCH_PROVIDER_REF,
)


def test_web_hybrid_read_model_is_backend_owned_and_performs_no_live_probe() -> None:
    read_model = build_web_hybrid_availability_read_model()

    assert read_model.truth_owner == "python_core"
    assert read_model.status == "implemented_runtime_observation_required"
    assert len(read_model.lanes) == 3
    assert read_model.routing_policy == "self_host_first_cloud_escalation"
    assert read_model.routing_attempt_ceiling == 2
    assert read_model.provider_network_call_performed is False
    assert read_model.current_remaining_credits is None
    assert read_model.circuit_state == "unknown_until_runtime_inspection"
    assert (
        read_model.research_aggregation.current_observation_status
        == "not_injected_by_read_only_route"
    )
    assert read_model.research_aggregation.current_citation_count == 0
    assert read_model.research_aggregation.deterministic_injected_observations_only is True


def test_web_hybrid_read_model_reuses_canonical_runtime_refs() -> None:
    lanes = build_web_hybrid_availability_read_model().lanes

    assert [
        (lane.capability_ref, lane.lane_ref, lane.provider_ref, lane.adapter_ref)
        for lane in lanes
    ] == [
        (
            SEARXNG_SEARCH_CAPABILITY_REF,
            SEARXNG_SEARCH_LANE_REF,
            SEARXNG_SEARCH_PROVIDER_REF,
            SEARXNG_SEARCH_ADAPTER_REF,
        ),
        (
            FIRECRAWL_MARKDOWN_CAPABILITY_REF,
            FIRECRAWL_MARKDOWN_LANE_REF,
            FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
            FIRECRAWL_MARKDOWN_ADAPTER_REF,
        ),
        (
            FIRECRAWL_CLOUD_CAPABILITY_REF,
            FIRECRAWL_CLOUD_LANE_REF,
            FIRECRAWL_CLOUD_PROVIDER_REF,
            FIRECRAWL_CLOUD_ADAPTER_REF,
        ),
    ]


def test_web_hybrid_read_model_preserves_authority_and_product_boundaries() -> None:
    read_model = build_web_hybrid_availability_read_model()

    assert read_model.request_scoped_evaluation_required is True
    assert read_model.final_start_revalidation_required is True
    assert read_model.mission_scoped_lease_required is True
    assert read_model.complete_request_fingerprint_required is True
    assert read_model.start_deadline_required is True
    assert read_model.local_approval_required is True
    assert read_model.exact_authority_lease_required is True
    assert read_model.budget_reservation_required_for_cloud is True
    assert read_model.paid_usage_enabled is False
    assert read_model.keyless_enabled is False
    assert read_model.cloud_first_enabled is False
    assert read_model.provider_zero_data_retention_claimed is False
    assert read_model.external_content_untrusted is True
    assert read_model.instruction_authority_granted is False
    assert read_model.memory_write_allowed is False
    assert read_model.context_injection_allowed is False
    assert read_model.browser_actions_allowed is False
    assert read_model.research_aggregation.not_instruction_authority is True
    assert read_model.research_aggregation.memory_write_authorized is False
    assert read_model.research_aggregation.action_execution_authorized is False
    assert read_model.research_aggregation.raw_page_content_persisted is False


def test_canonical_capability_availability_embeds_web_hybrid_truth() -> None:
    full = build_capability_availability_read_model()

    assert full.web_hybrid == build_web_hybrid_availability_read_model()
    assert full.availability_does_not_grant_execution is True
