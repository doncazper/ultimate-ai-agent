from __future__ import annotations

from datetime import timedelta
from threading import Event, Thread
from typing import Any

import pytest
from pydantic import ValidationError

from tests.test_firecrawl_cloud import (
    NOW,
    _approval as _cloud_approval,
    _credential,
    _credit_payload,
    _lease as _cloud_lease,
    _reconcile,
    _request as _cloud_request,
    _scrape as _cloud_scrape,
    _state as _cloud_state,
)
from tests.test_firecrawl_markdown import (
    _approval_authority as _local_approval,
    _exact_lease as _local_lease,
    _fixture_transport as _local_success,
    _request as _local_request,
    _state as _local_state,
)
from ultimate_ai_agent.core.authority import AuthorityLeaseStatus
from ultimate_ai_agent.core.capability_availability import SafeDisableStatus
from ultimate_ai_agent.core.web_access.firecrawl_cloud import (
    FirecrawlCloudMarkdownRequest,
    FirecrawlCloudTransportError,
)
from ultimate_ai_agent.core.web_access.firecrawl_markdown import (
    FirecrawlMarkdownRequest,
)
from ultimate_ai_agent.core.web_access.hybrid_contracts import (
    WebProviderAttemptOutcome,
    WebProviderCircuitState,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderRoutingPolicy,
    WebProviderTransportStatus,
)
from ultimate_ai_agent.core.web_access.hybrid_execution import (
    HybridMarkdownExecutionRequest,
    InMemoryWebCloudCircuitBreaker,
    InMemoryWebHybridExecutionLedger,
    WebHybridExecutionInProgressError,
    WebHybridExecutionConflictError,
    execute_hybrid_firecrawl_markdown,
)
from ultimate_ai_agent.core.web_access.hybrid_ledger import InMemoryWebCreditLedger
from ultimate_ai_agent.core.web_access.hybrid_router import simulate_hybrid_route


_DEFAULT_PROVIDER = object()


def _empty_local(calls: list[FirecrawlMarkdownRequest]):  # type: ignore[no-untyped-def]
    def transport(request: FirecrawlMarkdownRequest) -> dict[str, Any]:
        calls.append(request)
        return {
            "success": True,
            "data": {
                "markdown": "",
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": request.target_url,
                },
            },
        }

    return transport


def _unknown_local(calls: list[FirecrawlMarkdownRequest]):  # type: ignore[no-untyped-def]
    def transport(request: FirecrawlMarkdownRequest) -> dict[str, Any]:
        calls.append(request)
        return {"success": False}

    return transport


def _route_ref(
    *,
    parent_ref: str,
    outcome: WebProviderAttemptOutcome,
    snapshot: Any,
    circuit_state: WebProviderCircuitState = WebProviderCircuitState.closed,
) -> str:
    return simulate_hybrid_route(
        request_ref=parent_ref,
        operation=WebProviderOperation.scrape_markdown,
        policy=WebProviderRoutingPolicy.self_host_first_cloud_escalation,
        capability_states=(_local_state(), _cloud_state()),
        first_attempt_outcome=outcome,
        cloud_snapshot=snapshot,
        cloud_circuit_state=circuit_state,
        now=NOW,
    ).decision_ref


def _hybrid_request(
    *,
    parent_ref: str = "web-hybrid-request-ref:test",
    idempotency_ref: str = "idempotency-ref:web-hybrid:test",
    outcome: WebProviderAttemptOutcome = WebProviderAttemptOutcome.empty_content,
    snapshot: Any,
    routing_ref: str | None = None,
) -> HybridMarkdownExecutionRequest:
    local = _local_request().model_copy(
        update={
            "mission_ref": "mission-ref:web-hybrid:test",
            "run_ref": "run-ref:web-hybrid:test",
            "idempotency_ref": "idempotency-ref:web-hybrid:local:test",
            "start_deadline": NOW + timedelta(minutes=4),
            "request_fingerprint_ref": "request-fingerprint-ref:pending",
        }
    )
    cloud = _cloud_request(
        routing_decision_ref=routing_ref
        or _route_ref(parent_ref=parent_ref, outcome=outcome, snapshot=snapshot)
    ).model_copy(
        update={
            "mission_ref": "mission-ref:web-hybrid:test",
            "run_ref": "run-ref:web-hybrid:test",
            "start_deadline": NOW + timedelta(minutes=4),
            "request_fingerprint_ref": "request-fingerprint-ref:pending",
        }
    )
    return HybridMarkdownExecutionRequest(
        request_ref=parent_ref,
        idempotency_ref=idempotency_ref,
        local_request=local,
        cloud_request=cloud,
        expected_execution_receipt_ref="execution-receipt-ref:web-hybrid:test",
    )


def _execute(
    request: HybridMarkdownExecutionRequest,
    *,
    snapshot: Any,
    local_transport: Any,
    cloud_transport: Any,
    execution_ledger: InMemoryWebHybridExecutionLedger | None = None,
    circuit: InMemoryWebCloudCircuitBreaker | None = None,
    credit_ledger: InMemoryWebCreditLedger | None = None,
    cloud_leases: list[Any] | None = None,
    before_fallback: Any = None,
    before_local_final_start: Any = None,
    local_state_provider: Any = None,
    local_authority_leases_provider: Any = None,
    cloud_state_provider: Any = None,
    credit_snapshot_provider: Any = None,
    cloud_authority_leases_provider: Any = _DEFAULT_PROVIDER,
    trusted_clock: Any = None,
):  # type: ignore[no-untyped-def]
    if trusted_clock is None:
        clock_offset = 0

        def trusted_clock():  # type: ignore[no-untyped-def]
            nonlocal clock_offset
            clock_offset += 1
            return NOW + timedelta(seconds=clock_offset)

    effective_cloud_leases = cloud_leases or [
        _cloud_lease(request.cloud_request, snapshot)
    ]
    effective_cloud_lease_provider = (
        (lambda: effective_cloud_leases)
        if cloud_authority_leases_provider is _DEFAULT_PROVIDER
        else cloud_authority_leases_provider
    )
    local_state = _local_state(
        state_ref="web-provider-capability-state-ref:firecrawl-markdown:hybrid-test",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    local_lease = _local_lease(request.local_request).model_copy(
        update={
            "issued_at": NOW - timedelta(minutes=1),
            "expires_at": NOW + timedelta(minutes=10),
        }
    )
    return execute_hybrid_firecrawl_markdown(
        request,
        local_capability_state=local_state,
        cloud_capability_state=_cloud_state(),
        credit_snapshot=snapshot,
        credit_ledger=credit_ledger or InMemoryWebCreditLedger(),
        execution_ledger=execution_ledger or InMemoryWebHybridExecutionLedger(),
        cloud_circuit=circuit or InMemoryWebCloudCircuitBreaker(),
        credential=_credential(),
        local_approval_authority=_local_approval(request.local_request),
        cloud_approval_authority=_cloud_approval(request.cloud_request),
        local_authority_leases=[local_lease],
        cloud_authority_leases=effective_cloud_leases,
        local_transport=local_transport,
        cloud_scrape_transport=cloud_transport,
        cloud_credit_transport=lambda _credential: _credit_payload(remaining=9),
        target_validator=lambda _url: None,
        before_local_final_start=before_local_final_start,
        local_state_provider=local_state_provider or (lambda: local_state),
        local_authority_leases_provider=(
            local_authority_leases_provider or (lambda: [local_lease])
        ),
        before_fallback=before_fallback,
        cloud_state_provider=cloud_state_provider or _cloud_state,
        credit_snapshot_provider=credit_snapshot_provider or (lambda: snapshot),
        cloud_authority_leases_provider=effective_cloud_lease_provider,
        trusted_clock=trusted_clock,
        evaluated_at=NOW,
    )


def test_local_success_never_calls_cloud() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(
        snapshot=snapshot,
        outcome=WebProviderAttemptOutcome.succeeded,
    )
    local_calls: list[FirecrawlMarkdownRequest] = []
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_local_success(local_calls),
        cloud_transport=_cloud_scrape(cloud_calls),
    )

    assert len(local_calls) == 1
    assert cloud_calls == []
    assert result.attempt_count == 1
    assert result.final_deployment == WebProviderDeploymentKind.firecrawl_self_hosted
    assert result.first_attempt_outcome == WebProviderAttemptOutcome.succeeded


def test_empty_local_content_uses_one_exact_cloud_fallback() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    local_calls: list[FirecrawlMarkdownRequest] = []
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local(local_calls),
        cloud_transport=_cloud_scrape(cloud_calls),
    )

    assert len(local_calls) == 1
    assert len(cloud_calls) == 1
    assert result.attempt_count == 2
    assert result.final_deployment == WebProviderDeploymentKind.firecrawl_cloud
    assert result.status == WebProviderTransportStatus.simulated
    assert result.evidence is not None
    assert result.evidence.content_untrusted is True


def test_real_cloud_fallback_without_current_lease_provider_fails_closed(
    tmp_path: Any,
) -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    cloud_transport = _cloud_scrape(cloud_calls)
    cloud_transport.real_world_transport_performed = True  # type: ignore[attr-defined]

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=cloud_transport,
        credit_ledger=InMemoryWebCreditLedger(
            state_path=tmp_path / "missing-lease-provider.jsonl"
        ),
        cloud_authority_leases_provider=None,
    )

    assert cloud_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.cloud_receipt is not None
    assert result.cloud_receipt.network_call_performed is False


def test_revoked_current_cloud_lease_blocks_real_fallback_before_transport(
    tmp_path: Any,
) -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    leases = [_cloud_lease(request.cloud_request, snapshot)]
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    cloud_transport = _cloud_scrape(cloud_calls)
    cloud_transport.real_world_transport_performed = True  # type: ignore[attr-defined]

    def revoke() -> None:
        leases[0] = leases[0].model_copy(
            update={"status": AuthorityLeaseStatus.revoked}
        )

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=cloud_transport,
        cloud_leases=leases,
        credit_ledger=InMemoryWebCreditLedger(
            state_path=tmp_path / "revoked-lease.jsonl"
        ),
        before_fallback=revoke,
        cloud_authority_leases_provider=lambda: tuple(leases),
    )

    assert cloud_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.cloud_receipt is not None
    assert result.cloud_receipt.network_call_performed is False


def test_cloud_fallback_uses_fresh_trusted_time_and_credit_snapshot() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    clock_values = iter((NOW, snapshot.expires_at))

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=_cloud_scrape(cloud_calls),
        trusted_clock=lambda: next(clock_values),
        credit_snapshot_provider=lambda: snapshot,
    )

    assert cloud_calls == []
    assert result.attempt_count == 1
    assert result.status == WebProviderTransportStatus.blocked
    assert result.cloud_receipt is None
    assert "FIRECRAWL_CLOUD_FALLBACK_NOT_READY" in result.blocker_codes


def test_unknown_local_failure_is_terminal_and_never_falls_back() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(
        snapshot=snapshot,
        outcome=WebProviderAttemptOutcome.unknown_failure,
    )
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_unknown_local([]),
        cloud_transport=_cloud_scrape(cloud_calls),
    )

    assert cloud_calls == []
    assert result.first_attempt_outcome == WebProviderAttemptOutcome.unknown_failure
    assert result.attempt_count == 1
    assert "TERMINAL_FIRST_ATTEMPT_OUTCOME_NO_FALLBACK" in result.blocker_codes


def test_cloud_routing_ref_mismatch_never_falls_back() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(
        snapshot=snapshot,
        routing_ref="web-provider-routing-decision-ref:different-scope",
    )
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=_cloud_scrape(cloud_calls),
    )

    assert cloud_calls == []
    assert result.attempt_count == 1
    assert "CLOUD_ROUTING_DECISION_REF_MISMATCH" in result.blocker_codes


def test_replay_returns_receipt_only_and_never_calls_either_provider_again() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    local_calls: list[FirecrawlMarkdownRequest] = []
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    execution_ledger = InMemoryWebHybridExecutionLedger()

    first = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local(local_calls),
        cloud_transport=_cloud_scrape(cloud_calls),
        execution_ledger=execution_ledger,
    )
    replay = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local(local_calls),
        cloud_transport=_cloud_scrape(cloud_calls),
        execution_ledger=execution_ledger,
    )

    assert first.evidence is not None
    assert len(local_calls) == 1
    assert len(cloud_calls) == 1
    assert replay.replayed is True
    assert replay.evidence is None
    assert "WEB_HYBRID_IDEMPOTENT_REPLAY" in replay.reason_codes


def test_idempotency_fingerprint_binds_complete_child_request_semantics() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    ledger = InMemoryWebHybridExecutionLedger()

    _execute(
        request,
        snapshot=snapshot,
        local_transport=_local_success([]),
        cloud_transport=_cloud_scrape([]),
        execution_ledger=ledger,
    )
    changed = request.model_copy(
        update={
            "cloud_request": request.cloud_request.model_copy(
                update={
                    "safety_reserve_credits": (
                        request.cloud_request.safety_reserve_credits + 1
                    ),
                    "request_fingerprint_ref": "request-fingerprint-ref:pending",
                }
            )
        }
    )

    with pytest.raises(
        WebHybridExecutionConflictError,
        match="WEB_HYBRID_IDEMPOTENCY_SEMANTIC_CONFLICT",
    ):
        _execute(
            changed,
            snapshot=snapshot,
            local_transport=_local_success([]),
            cloud_transport=_cloud_scrape([]),
            execution_ledger=ledger,
        )


def test_hybrid_request_is_immutable_after_fingerprint_claim() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)

    with pytest.raises(ValidationError, match="frozen"):
        request.idempotency_ref = "idempotency-ref:web-hybrid:mutated"


def test_duplicate_in_flight_hybrid_request_never_dispatches_twice() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    execution_ledger = InMemoryWebHybridExecutionLedger()
    local_calls: list[FirecrawlMarkdownRequest] = []
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    first_started = Event()
    release_first = Event()
    first_results: list[Any] = []

    def blocked_local(
        local_request: FirecrawlMarkdownRequest,
    ) -> dict[str, Any]:
        local_calls.append(local_request)
        first_started.set()
        assert release_first.wait(timeout=5)
        return {
            "success": True,
            "data": {
                "markdown": "",
                "metadata": {
                    "sourceURL": local_request.target_url,
                    "url": local_request.target_url,
                },
            },
        }

    first_thread = Thread(
        target=lambda: first_results.append(
            _execute(
                request,
                snapshot=snapshot,
                local_transport=blocked_local,
                cloud_transport=_cloud_scrape(cloud_calls),
                execution_ledger=execution_ledger,
            )
        )
    )
    first_thread.start()
    assert first_started.wait(timeout=5)

    try:
        with pytest.raises(
            WebHybridExecutionInProgressError,
            match="WEB_HYBRID_IDEMPOTENT_REQUEST_IN_PROGRESS",
        ):
            _execute(
                request,
                snapshot=snapshot,
                local_transport=_empty_local(local_calls),
                cloud_transport=_cloud_scrape(cloud_calls),
                execution_ledger=execution_ledger,
            )
    finally:
        release_first.set()
        first_thread.join(timeout=5)
    assert not first_thread.is_alive()
    assert len(first_results) == 1
    assert len(local_calls) == 1
    assert len(cloud_calls) == 1


def test_revoked_cloud_lease_race_blocks_before_cloud_transport() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    cloud_leases = [_cloud_lease(request.cloud_request, snapshot)]

    def revoke() -> None:
        cloud_leases[0] = cloud_leases[0].model_copy(
            update={"status": AuthorityLeaseStatus.revoked}
        )

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=_cloud_scrape(cloud_calls),
        cloud_leases=cloud_leases,
        before_fallback=revoke,
    )

    assert cloud_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.cloud_receipt is not None
    assert result.cloud_receipt.network_call_performed is False


def test_local_attempt_revalidates_lease_at_final_start() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    local_calls: list[FirecrawlMarkdownRequest] = []
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    local_leases = [_local_lease(request.local_request)]

    def revoke() -> None:
        local_leases[0] = local_leases[0].model_copy(
            update={"status": AuthorityLeaseStatus.revoked}
        )

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local(local_calls),
        cloud_transport=_cloud_scrape(cloud_calls),
        before_local_final_start=revoke,
        local_authority_leases_provider=lambda: tuple(local_leases),
    )

    assert local_calls == []
    assert cloud_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.attempt_count == 1
    assert result.local_receipt is not None
    assert result.local_receipt.network_call_performed is False


def test_safe_disable_race_blocks_before_cloud_transport() -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    request = _hybrid_request(snapshot=snapshot)
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []
    state_holder = {"state": _cloud_state()}

    def safe_disable() -> None:
        state_holder["state"] = _cloud_state(
            state_ref="web-provider-capability-state-ref:firecrawl-cloud:safe-disabled",
            safe_disable_status=SafeDisableStatus.active,
        )

    result = _execute(
        request,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=_cloud_scrape(cloud_calls),
        before_fallback=safe_disable,
        cloud_state_provider=lambda: state_holder["state"],
    )

    assert cloud_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.cloud_receipt is None


def test_circuit_opens_after_bounded_cloud_failures_and_blocks_third_fallback(
    tmp_path: Any,
) -> None:
    snapshot = _reconcile(remaining=10).snapshot
    assert snapshot is not None
    circuit = InMemoryWebCloudCircuitBreaker(failure_threshold=2)
    cloud_calls: list[FirecrawlCloudMarkdownRequest] = []

    def cloud_failure(
        request: FirecrawlCloudMarkdownRequest,
        _credential: Any,
    ) -> dict[str, Any]:
        cloud_calls.append(request)
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_TRANSPORT_FAILED",
            network_call_performed=True,
        )

    cloud_failure.real_world_transport_performed = True  # type: ignore[attr-defined]
    for index in range(2):
        parent_ref = f"web-hybrid-request-ref:circuit:{index}"
        request = _hybrid_request(
            parent_ref=parent_ref,
            idempotency_ref=f"idempotency-ref:web-hybrid:circuit:{index}",
            snapshot=snapshot,
        )
        _execute(
            request,
            snapshot=snapshot,
            local_transport=_empty_local([]),
                cloud_transport=cloud_failure,
                circuit=circuit,
                credit_ledger=InMemoryWebCreditLedger(
                    state_path=tmp_path / f"cloud-credit-{index}.jsonl"
                ),
            )

    assert circuit.inspect().state == WebProviderCircuitState.open
    third_parent = "web-hybrid-request-ref:circuit:third"
    third = _hybrid_request(
        parent_ref=third_parent,
        idempotency_ref="idempotency-ref:web-hybrid:circuit:third",
        snapshot=snapshot,
        routing_ref=_route_ref(
            parent_ref=third_parent,
            outcome=WebProviderAttemptOutcome.empty_content,
            snapshot=snapshot,
            circuit_state=WebProviderCircuitState.open,
        ),
    )
    result = _execute(
        third,
        snapshot=snapshot,
        local_transport=_empty_local([]),
        cloud_transport=cloud_failure,
        circuit=circuit,
    )

    assert len(cloud_calls) == 2
    assert result.attempt_count == 1
    assert "FIRECRAWL_CLOUD_CIRCUIT_OPEN" in result.blocker_codes
    assert circuit.inspect().review_after == circuit.inspect().opened_at + timedelta(
        minutes=5
    )


def test_circuit_closes_only_after_current_free_plan_reconciliation() -> None:
    current = _reconcile(remaining=10).snapshot
    paid = _reconcile(remaining=10, plan=5_000).snapshot
    assert current is not None and paid is not None
    circuit = InMemoryWebCloudCircuitBreaker(failure_threshold=1)
    circuit.record_failure(WebProviderAttemptOutcome.provider_5xx, now=NOW)

    still_open = circuit.close_after_reconciliation(paid, now=NOW)
    closed = circuit.close_after_reconciliation(current, now=NOW)

    assert still_open.state == WebProviderCircuitState.open
    assert closed.state == WebProviderCircuitState.closed
    assert closed.failure_count == 0
