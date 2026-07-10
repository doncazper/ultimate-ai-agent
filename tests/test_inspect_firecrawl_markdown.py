from __future__ import annotations

from scripts.inspect_firecrawl_markdown import inspect_markdown_payload, render_summary
from tests.test_firecrawl_markdown import (
    NOW,
    _approval_authority,
    _exact_lease,
    _fixture_transport,
    _request,
    _state,
    _target_validator,
)


def test_cli_and_core_share_safe_markdown_truth_without_raw_target_or_page() -> None:
    request = _request()
    transport_calls = []
    target_calls = []

    payload = inspect_markdown_payload(
        request=request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(transport_calls),
        target_validator=_target_validator(target_calls),
        evaluated_at=NOW,
    )
    summary = render_summary(payload)

    assert len(transport_calls) == 1
    assert payload["status"] == "simulated"
    assert payload["invocation_outcome"] == "allow"
    assert payload["content_hash_ref"].startswith("content-hash-ref:sha256:")
    assert payload["bounded_redacted_preview"]
    assert payload["content_untrusted"] is True
    assert payload["instruction_authority"] is False
    assert payload["raw_target_returned"] is False
    assert payload["full_markdown_returned"] is False
    assert request.target_url not in str(payload)
    assert request.target_url not in summary
    assert "transient untrusted evidence" in summary
    assert "{" not in summary
