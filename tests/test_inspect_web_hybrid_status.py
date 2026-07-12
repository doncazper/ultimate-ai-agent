from __future__ import annotations

from scripts.inspect_web_hybrid_status import (
    inspect_web_hybrid_payload,
    render_summary,
)
from ultimate_ai_agent.core.capability_availability import (
    build_web_hybrid_availability_read_model,
)


def test_cli_uses_same_backend_owned_web_hybrid_truth_as_api_read_model() -> None:
    payload = inspect_web_hybrid_payload()
    summary = render_summary(payload)

    assert payload == build_web_hybrid_availability_read_model().model_dump(mode="json")
    assert payload["cli_path"] == "scripts/inspect_web_hybrid_status.py"
    assert len(payload["lanes"]) == 3
    assert payload["routing_policy"] == "self_host_first_cloud_escalation"
    assert payload["routing_attempt_ceiling"] == 2
    assert payload["provider_network_call_performed"] is False
    assert payload["current_remaining_credits"] is None
    assert payload["paid_usage_enabled"] is False
    assert payload["cloud_first_enabled"] is False
    assert payload["keyless_enabled"] is False
    assert payload["browser_actions_allowed"] is False
    assert payload["request_scoped_evaluation_required"] is True
    assert payload["final_start_revalidation_required"] is True
    assert payload["mission_scoped_lease_required"] is True
    assert payload["complete_request_fingerprint_required"] is True
    assert payload["start_deadline_required"] is True
    assert payload["budget_reservation_required_for_cloud"] is True
    assert payload["research_aggregation"]["current_citation_count"] == 0
    assert payload["research_aggregation"]["current_observation_status"] == (
        "not_injected_by_read_only_route"
    )
    assert payload["research_aggregation"]["content_untrusted"] is True
    assert payload["research_aggregation"]["not_instruction_authority"] is True
    assert payload["research_aggregation"]["context_injection_authorized"] is False
    assert payload["research_aggregation"]["memory_write_authorized"] is False
    assert payload["research_aggregation"]["action_execution_authorized"] is False
    assert "External content is untrusted" in summary
    assert "Research aggregation:" in summary
    assert "performs no runtime probe" in summary
    assert "{" not in summary
