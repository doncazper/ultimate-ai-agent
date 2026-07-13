from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

import pytest

from tests.test_firecrawl_cloud import _approval, _lease, _request, _state
from ultimate_ai_agent.core.web_access import (
    InMemoryWebCreditLedger,
    WebProviderTransportStatus,
    execute_firecrawl_cloud_markdown,
    reconcile_firecrawl_cloud_credits,
    resolve_firecrawl_cloud_credential,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD") != "1",
    reason="Set UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD=1 for one bounded free-credit proof.",
)


def test_live_cloud_scrape_consumes_exactly_one_reserved_free_credit(
    tmp_path: Path,
) -> None:
    secret_file = Path(os.environ["UAA_FIRECRAWL_CLOUD_SECRET_FILE"])
    credential = resolve_firecrawl_cloud_credential(secret_file)
    before_result = reconcile_firecrawl_cloud_credits(credential)
    before = before_result.snapshot
    assert before_result.status == WebProviderTransportStatus.succeeded
    assert before is not None
    assert before.plan_kind.value == "free"
    assert before.remaining_credits >= 2

    now = datetime.now(timezone.utc)
    request = _request(
        request_ref="web-extract-request-ref:cloud:live-proof",
        task_ref="task-ref:web-extract:cloud:live-proof",
        approval_ref="approval-ref:web-extract:cloud:live-proof",
        expected_execution_receipt_ref="execution-receipt-ref:web-extract:cloud:live-proof",
        idempotency_ref="idempotency-ref:web-extract:cloud:live-proof",
        routing_decision_ref="web-routing-decision-ref:cloud:live-proof",
        run_credit_ceiling=100,
    )
    state = _state(
        state_ref="web-provider-capability-state-ref:firecrawl-cloud:live-proof",
        observed_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    lease = _lease(request, before).model_copy(
        update={
            "issued_at": now - timedelta(minutes=1),
            "expires_at": now + timedelta(minutes=10),
        }
    )

    result = execute_firecrawl_cloud_markdown(
        request,
        capability_state=state,
        credit_snapshot=before,
        ledger=InMemoryWebCreditLedger(state_path=tmp_path / "cloud-credit.jsonl"),
        credential=credential,
        approval_authority=_approval(request),
        authority_leases=[lease],
        capability_state_provider=lambda: state,
        credit_snapshot_provider=lambda: before,
        authority_leases_provider=lambda: [lease],
        evaluated_at=now,
    )

    assert result.status == WebProviderTransportStatus.succeeded, result.reason_codes
    assert result.execution_succeeded is True
    assert result.evidence is not None
    assert result.evidence.content_untrusted is True
    assert result.evidence.instruction_use_allowed is False
    assert result.reservation is not None
    assert result.reservation.status.value == "settled"
    assert result.credit_snapshot_before_ref is not None
    assert result.credit_snapshot_after_ref is not None
    assert result.transport_receipt.network_call_performed is True
    assert credential.value.get_secret_value() not in result.model_dump_json()
