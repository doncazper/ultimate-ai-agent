from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

import pytest

from tests.test_firecrawl_markdown import (
    _approval_authority,
    _exact_lease,
    _request,
    _state,
)
from ultimate_ai_agent.core.web_access import (
    WebProviderTransportStatus,
    execute_firecrawl_markdown,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL") != "1",
    reason=(
        "Set UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL=1 for the opt-in local "
        "Firecrawl proof."
    ),
)


def test_live_self_hosted_firecrawl_returns_bounded_transient_markdown() -> None:
    now = datetime.now(timezone.utc)
    request = _request(
        request_ref="web-extract-request-ref:live-local-proof",
        task_ref="task-ref:web-extract:live-local-proof",
        approval_ref="approval-ref:web-extract:live-local-proof",
        expected_execution_receipt_ref=(
            "execution-receipt-ref:web-extract:live-local-proof"
        ),
    )
    state = _state(
        state_ref="web-provider-capability-state-ref:firecrawl-markdown:live-local-proof",
        observed_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    lease = _exact_lease(request).model_copy(
        update={
            "issued_at": now - timedelta(minutes=1),
            "expires_at": now + timedelta(minutes=10),
        }
    )

    result = execute_firecrawl_markdown(
        request,
        capability_state=state,
        approval_authority=_approval_authority(request),
        authority_leases=[lease],
        capability_state_provider=lambda: state,
        authority_leases_provider=lambda: [lease],
        evaluated_at=now,
    )

    assert result.status == WebProviderTransportStatus.succeeded, result.reason_codes
    assert result.execution_succeeded is True
    assert result.transport_receipt.network_call_performed is True
    assert result.transport_receipt.target_method == "GET"
    assert result.transport_receipt.provider_transport_method == "POST"
    assert result.evidence is not None
    assert 0 < len(result.evidence.markdown) <= request.max_markdown_chars
    assert result.evidence.content_untrusted is True
    assert result.evidence.instruction_use_allowed is False
    assert result.evidence.memory_write_allowed is False
    assert result.evidence.context_injection_allowed is False
    assert result.evidence.raw_html_returned is False
    receipt_json = result.transport_receipt.model_dump_json()
    assert request.target_url not in receipt_json
    assert result.evidence.markdown not in receipt_json
