from __future__ import annotations

from scripts.inspect_searxng_search import inspect_search_payload, render_summary
from tests.test_searxng_search import (
    NOW,
    _approval_authority,
    _exact_lease,
    _fixture_transport,
    _request,
    _state,
)


def test_cli_and_core_share_backend_owned_search_truth_without_raw_query() -> None:
    request = _request(query="ephemeral CLI query must not echo")
    calls = []

    payload = inspect_search_payload(
        request=request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )
    summary = render_summary(payload)

    assert len(calls) == 1
    assert payload["status"] == "simulated"
    assert payload["invocation_outcome"] == "allow"
    assert len(payload["source_refs"]) == 2
    assert payload["content_untrusted"] is True
    assert payload["instruction_authority"] is False
    assert payload["raw_query_returned"] is False
    assert request.query not in str(payload)
    assert request.query not in summary
    assert "untrusted evidence" in summary
    assert "{" not in summary
