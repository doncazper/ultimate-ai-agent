from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

import pytest

from tests.test_searxng_search import (
    _approval_authority,
    _exact_lease,
    _request,
    _state,
)
from ultimate_ai_agent.core.web_access import (
    WebProviderTransportStatus,
    execute_searxng_search,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("UAA_WEB_HYBRID_LIVE_SEARXNG") != "1",
    reason="Set UAA_WEB_HYBRID_LIVE_SEARXNG=1 for the opt-in local SearXNG proof.",
)


def test_live_searxng_search_is_bounded_untrusted_and_redacted() -> None:
    now = datetime.now(timezone.utc)
    request = _request(
        request_ref="web-search-request-ref:live-local-proof",
        task_ref="task-ref:web-search:live-local-proof",
        approval_ref="approval-ref:web-search:live-local-proof",
        query="privacy preserving metasearch",
        max_results=2,
        expected_execution_receipt_ref=(
            "execution-receipt-ref:web-search:live-local-proof"
        ),
    )
    state = _state(
        state_ref="web-provider-capability-state-ref:searxng-search:live-local-proof",
        observed_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    result = execute_searxng_search(
        request,
        capability_state=state,
        approval_authority=_approval_authority(request),
        authority_leases=[
            _exact_lease(request).model_copy(
                update={
                    "issued_at": now - timedelta(minutes=1),
                    "expires_at": now + timedelta(minutes=10),
                }
            )
        ],
        evaluated_at=now,
    )

    assert result.status == WebProviderTransportStatus.succeeded
    assert result.execution_succeeded is True
    assert result.transport_receipt.network_call_performed is True
    assert len(result.evidence) <= request.max_results
    assert all(item.content_untrusted is True for item in result.evidence)
    assert all(item.instruction_use_allowed is False for item in result.evidence)
    assert all(item.host not in {"localhost", "127.0.0.1"} for item in result.evidence)
    assert request.query not in result.model_dump_json()
    assert result.raw_query_stored is False
    assert result.raw_provider_payload_stored is False
