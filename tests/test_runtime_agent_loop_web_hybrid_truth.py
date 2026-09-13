from __future__ import annotations

from ultimate_ai_agent.core.control_center.agent_loop import (
    build_external_information_handling_posture,
)
from ultimate_ai_agent.core.capability_availability import (
    CAPABILITY_AVAILABILITY_ROUTE_REF,
    build_web_hybrid_availability_read_model,
)


def test_agent_loop_preserves_exact_web_hybrid_truth_without_global_authority() -> None:
    posture = build_external_information_handling_posture()
    web_hybrid = build_web_hybrid_availability_read_model()
    rows = posture["rows"]
    exact_rows = [row for row in rows if row["existing_exact_network_lane"]]

    assert posture["existing_exact_network_lane_count"] == 1 + len(web_hybrid.lanes)
    assert posture["provider_search_enabled"] is False
    assert posture["exact_bounded_provider_lanes_implemented"] is True
    assert [row["category_id"] for row in exact_rows] == [
        "allowlisted_gateway_preview",
        "provider_search_scrape",
    ]
    assert sum(row["exact_network_lane_count"] for row in rows) == 1 + len(
        web_hybrid.lanes
    )

    provider_search = next(
        row for row in rows if row["category_id"] == "provider_search_scrape"
    )
    assert provider_search["status"] == web_hybrid.status
    assert provider_search["exact_network_lane_count"] == len(web_hybrid.lanes)
    assert provider_search["route_refs"] == [CAPABILITY_AVAILABILITY_ROUTE_REF]
    assert provider_search["cli_refs"] == [web_hybrid.cli_path]
    assert provider_search["safe_summary"] == web_hybrid.safe_summary[:240]
    assert set(web_hybrid.proof_refs).issubset(provider_search["evidence_refs"])

    for row in rows:
        assert row["safe_refs_only"] is True
        assert row["raw_content_included"] is False
        assert row["untrusted_content_can_instruct_agent"] is False
        assert row["external_content_can_grant_authority"] is False
        assert row["new_live_web_fetching_added"] is False
        assert row["browser_action_execution_enabled"] is False
        assert row["provider_sdk_calls_added"] is False
        assert row["connector_writes_added"] is False
        assert row["memory_writes_added"] is False
        assert row["context_injection_added"] is False
        assert row["production_authority_added"] is False
        assert row["exact_network_lane_count"] >= 0
        assert row["evidence_refs"]
        assert row["test_refs"]
        assert row["blocked_authority_refs"]
