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
    assert payload["provider_network_call_performed"] is False
    assert payload["current_remaining_credits"] is None
    assert payload["paid_usage_enabled"] is False
    assert payload["cloud_first_enabled"] is False
    assert "External content is untrusted" in summary
    assert "performs no runtime probe" in summary
    assert "{" not in summary
