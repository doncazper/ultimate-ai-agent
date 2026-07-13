from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event, Thread

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
    CapabilityInvocationDecision,
    InvocationDecisionOutcome,
)
from ultimate_ai_agent.core.web_access import (
    InMemoryWebCreditLedger,
    WebCreditLedgerConflictError,
    WebCreditLedgerTransitionError,
    WebCreditReservationInProgressError,
    WebCreditReceiptCompleteness,
    WebCreditReservationStatus,
    WebCreditSnapshotFreshness,
    WebProviderAttemptOutcome,
    WebProviderCreditReservationRequest,
    WebProviderCreditSnapshot,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderPlanKind,
    WebProviderRoutingPolicy,
    build_web_provider_capability_state,
    simulate_hybrid_route,
)


NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)


def _ready_state(
    deployment: WebProviderDeploymentKind,
    operation: WebProviderOperation,
):
    return build_web_provider_capability_state(
        state_ref=f"web-provider-state-ref:{deployment.value}:{operation.value}",
        provider_ref=f"web-provider-ref:{deployment.value}",
        deployment=deployment,
        operation=operation,
        version_ref=f"version-ref:{deployment.value}:pinned",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.healthy,
        authority_posture=AuthorityPosture.eligible_for_policy_evaluation,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )


def _snapshot(
    *,
    plan_kind: WebProviderPlanKind = WebProviderPlanKind.free,
    remaining: int = 3,
    concurrency: int = 1,
) -> WebProviderCreditSnapshot:
    return WebProviderCreditSnapshot(
        snapshot_ref="web-credit-snapshot-ref:current",
        provider_ref="web-provider-ref:firecrawl_cloud",
        account_ref="provider-account-ref:firecrawl:private-dogfood",
        credential_ref="credential-ref:firecrawl-cloud:opaque",
        plan_kind=plan_kind,
        plan_credits=1000,
        remaining_credits=remaining,
        max_concurrency=concurrency,
        billing_period_ref="billing-period-ref:firecrawl:current",
        billing_period_start=NOW - timedelta(days=1),
        billing_period_end=NOW + timedelta(days=29),
        fetched_at=NOW - timedelta(seconds=10),
        expires_at=NOW + timedelta(minutes=5),
        freshness=WebCreditSnapshotFreshness.current,
        response_receipt_hash_ref="provider-response-receipt-hash-ref:credit-usage",
    )


def _request(index: int) -> WebProviderCreditReservationRequest:
    return WebProviderCreditReservationRequest(
        request_ref=f"web-request-ref:cloud:{index}",
        idempotency_ref=f"idempotency-ref:web-credit:{index}",
        provider_ref="web-provider-ref:firecrawl_cloud",
        snapshot_ref="web-credit-snapshot-ref:current",
        billing_period_ref="billing-period-ref:firecrawl:current",
        routing_decision_ref=f"web-routing-decision-ref:{index}",
        estimated_credits=1,
    )


def _decision(
    request_ref: str,
    *,
    outcome: InvocationDecisionOutcome = InvocationDecisionOutcome.blocked,
) -> CapabilityInvocationDecision:
    return CapabilityInvocationDecision(
        decision_ref=f"capability-invocation-decision-ref:{outcome.value}:test",
        request_ref=request_ref,
        snapshot_ref="capability-availability-snapshot-ref:test",
        capability_ref="capability-ref:web-access:firecrawl-cloud-markdown:v1",
        provider_ref="web-provider-ref:firecrawl-cloud",
        adapter_ref="web-adapter-ref:firecrawl-cloud-markdown:v1",
        outcome=outcome,
        policy_decision_ref="policy-decision-ref:test",
        budget_decision_ref=(
            "budget-decision-ref:firecrawl-cloud-cost-decision:sha256:test"
        ),
        expected_execution_receipt_ref="execution-receipt-ref:test",
        evaluated_at=NOW,
        blocker_codes=[] if outcome == InvocationDecisionOutcome.allow else ["BLOCKED"],
        safe_summary="Request-scoped test decision.",
    )


def test_atomic_reservation_respects_plan_concurrency() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot(concurrency=1))

    with ThreadPoolExecutor(max_workers=4) as pool:
        reservations = list(
            pool.map(lambda index: ledger.reserve(_request(index), now=NOW), range(4))
        )

    assert (
        sum(item.status == WebCreditReservationStatus.reserved for item in reservations)
        == 1
    )
    assert (
        sum(item.status == WebCreditReservationStatus.denied for item in reservations)
        == 3
    )
    assert all(item.reserved_credits in {0, 1} for item in reservations)


def test_uaa_serializes_cloud_usage_even_when_free_plan_allows_two() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot(concurrency=2))

    first = ledger.reserve(_request(1), now=NOW)
    second = ledger.reserve(_request(2), now=NOW)

    assert first.status == WebCreditReservationStatus.reserved
    assert second.status == WebCreditReservationStatus.denied
    assert (
        "CLOUD_UAA_USAGE_ATTRIBUTION_CONCURRENCY_EXHAUSTED"
        in second.reason_codes
    )


def test_duplicate_in_flight_idempotency_never_shares_dispatch_reservation() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot())
    request = _request(1)

    first = ledger.reserve(request, now=NOW)
    with pytest.raises(
        WebCreditReservationInProgressError,
        match="CLOUD_IDEMPOTENT_RESERVATION_IN_PROGRESS",
    ):
        ledger.reserve(request, now=NOW)

    assert first.status == WebCreditReservationStatus.reserved
    assert len(ledger.list_reservations()) == 1


def test_final_start_fence_blocks_concurrent_reservation_release() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot())
    reservation = ledger.reserve(_request(1), now=NOW)
    release_started = Event()
    release_finished = Event()
    release_codes: list[str] = []

    def release() -> None:
        release_started.set()
        try:
            ledger.release(reservation.reservation_ref)
        except WebCreditLedgerTransitionError as exc:
            release_codes.append(str(exc))
        release_finished.set()

    with ledger.hold_reservation_start(reservation.reservation_ref):
        thread = Thread(target=release)
        thread.start()
        assert release_started.wait(timeout=2)
        assert release_finished.wait(timeout=0.05) is False
        assert (
            ledger.reservation_snapshot(reservation.reservation_ref).status
            == WebCreditReservationStatus.reserved
        )

    thread.join(timeout=2)
    assert release_finished.is_set()
    assert release_codes == ["WEB_CREDIT_RESERVATION_STARTED_RELEASE_DENIED"]
    assert (
        ledger.reservation_snapshot(reservation.reservation_ref).status
        == WebCreditReservationStatus.reserved
    )
    ledger.abort_unstarted(
        reservation.reservation_ref,
        authorized_decision=_decision(
            reservation.request_ref,
            outcome=InvocationDecisionOutcome.allow,
        ),
        final_decision=_decision(reservation.request_ref),
        network_call_performed=False,
    )
    released = ledger.release(reservation.reservation_ref)
    assert released.status == WebCreditReservationStatus.released


def test_durable_start_claim_survives_restart_and_requires_settlement(tmp_path) -> None:
    state_path = tmp_path / "cloud-credit.jsonl"
    ledger = InMemoryWebCreditLedger(state_path=state_path)
    ledger.reconcile(_snapshot())
    reservation = ledger.reserve(_request(1), now=NOW)

    with ledger.hold_reservation_start(reservation.reservation_ref):
        pass

    recovered = InMemoryWebCreditLedger(state_path=state_path)
    assert recovered.recovery_required_reservation_refs() == (
        reservation.reservation_ref,
    )
    with pytest.raises(
        WebCreditLedgerTransitionError,
        match="WEB_CREDIT_RESERVATION_STARTED_RELEASE_DENIED",
    ):
        recovered.release(reservation.reservation_ref)
    with pytest.raises(WebCreditReservationInProgressError):
        recovered.reserve(_request(1), now=NOW)

    settled = recovered.settle(
        reservation.reservation_ref,
        actual_credits=1,
        actual_usage_ref="actual-usage-ref:web-credit:recovered",
    )
    assert settled.status == WebCreditReservationStatus.settled
    assert (
        InMemoryWebCreditLedger(
            state_path=state_path
        ).recovery_required_reservation_refs()
        == ()
    )


def test_durable_ledger_rejects_symlink_fifo_and_invalid_complete_state(
    tmp_path,
) -> None:
    target = tmp_path / "target.jsonl"
    target.write_text("", encoding="utf-8")
    symlink = tmp_path / "symlink.jsonl"
    symlink.symlink_to(target)
    with pytest.raises(WebCreditLedgerConflictError):
        InMemoryWebCreditLedger(state_path=symlink)

    fifo = tmp_path / "fifo.jsonl"
    os.mkfifo(fifo)
    with pytest.raises(WebCreditLedgerConflictError):
        InMemoryWebCreditLedger(state_path=fifo)

    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        WebCreditLedgerConflictError,
        match="WEB_CREDIT_LEDGER_CHAIN_INVALID",
    ):
        InMemoryWebCreditLedger(state_path=invalid)


def test_durable_ledger_recovers_last_complete_record_from_torn_tail(tmp_path) -> None:
    state_path = tmp_path / "torn-tail.jsonl"
    ledger = InMemoryWebCreditLedger(state_path=state_path)
    ledger.reconcile(_snapshot())
    reservation = ledger.reserve(_request(1), now=NOW)
    with ledger.hold_reservation_start(reservation.reservation_ref):
        pass
    with state_path.open("ab") as handle:
        handle.write(b'{"partial_settlement":')

    recovered = InMemoryWebCreditLedger(state_path=state_path)

    assert recovered.recovery_required_reservation_refs() == (
        reservation.reservation_ref,
    )
    assert state_path.read_bytes().endswith(b"\n")


def test_durable_two_instance_reservation_is_serialized(tmp_path) -> None:
    state_path = tmp_path / "shared-credit.jsonl"
    first = InMemoryWebCreditLedger(state_path=state_path)
    second = InMemoryWebCreditLedger(state_path=state_path)
    first.reconcile(_snapshot(concurrency=2))

    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations = list(
            pool.map(
                lambda item: item[0].reserve(item[1], now=NOW),
                ((first, _request(1)), (second, _request(2))),
            )
        )

    assert sum(
        item.status == WebCreditReservationStatus.reserved for item in reservations
    ) == 1
    assert sum(
        item.status == WebCreditReservationStatus.denied for item in reservations
    ) == 1
    starts = 0
    for ledger, reservation in zip((first, second), reservations, strict=True):
        try:
            with ledger.hold_reservation_start(reservation.reservation_ref):
                starts += 1
        except WebCreditLedgerTransitionError:
            pass
    assert starts == 1
    recovered = InMemoryWebCreditLedger(state_path=state_path)
    assert len(recovered.list_reservations()) == 2


def test_durable_append_failure_rolls_back_memory_and_poison_latches(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "append-failure.jsonl"
    ledger = InMemoryWebCreditLedger(state_path=state_path)
    ledger.reconcile(_snapshot())

    def fail_append(_encoded: bytes) -> None:
        raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_WRITE_FAILED")

    monkeypatch.setattr(ledger, "_append_record", fail_append)
    with pytest.raises(WebCreditLedgerTransitionError):
        ledger.reserve(_request(1), now=NOW)
    with pytest.raises(
        WebCreditLedgerTransitionError,
        match="WEB_CREDIT_LEDGER_RELOAD_REQUIRED",
    ):
        ledger.list_reservations()
    assert InMemoryWebCreditLedger(state_path=state_path).list_reservations() == ()


def test_unstarted_abort_rejects_allow_or_network_start_proof() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot())
    reservation = ledger.reserve(_request(1), now=NOW)
    with ledger.hold_reservation_start(reservation.reservation_ref):
        pass

    with pytest.raises(
        WebCreditLedgerTransitionError,
        match="WEB_CREDIT_UNSTARTED_ABORT_PROOF_INVALID",
    ):
        ledger.abort_unstarted(
            reservation.reservation_ref,
            authorized_decision=_decision(
                reservation.request_ref,
                outcome=InvocationDecisionOutcome.allow,
            ),
            final_decision=_decision(
                reservation.request_ref,
                outcome=InvocationDecisionOutcome.allow,
            ),
            network_call_performed=False,
        )

    substituted_budget = _decision(reservation.request_ref).model_copy(
        update={"budget_decision_ref": "budget-decision-ref:other-lane"}
    )
    with pytest.raises(
        WebCreditLedgerTransitionError,
        match="WEB_CREDIT_UNSTARTED_ABORT_PROOF_INVALID",
    ):
        ledger.abort_unstarted(
            reservation.reservation_ref,
            authorized_decision=_decision(
                reservation.request_ref,
                outcome=InvocationDecisionOutcome.allow,
            ),
            final_decision=substituted_budget,
            network_call_performed=False,
        )

    substituted = _decision(reservation.request_ref).model_copy(
        update={"provider_ref": "provider-ref:substituted"}
    )
    with pytest.raises(
        WebCreditLedgerTransitionError,
        match="WEB_CREDIT_UNSTARTED_ABORT_PROOF_INVALID",
    ):
        ledger.abort_unstarted(
            reservation.reservation_ref,
            authorized_decision=_decision(
                reservation.request_ref,
                outcome=InvocationDecisionOutcome.allow,
            ),
            final_decision=substituted,
            network_call_performed=False,
        )


def test_credit_snapshot_and_reservation_aliases_are_immutable() -> None:
    ledger = InMemoryWebCreditLedger()
    snapshot = ledger.reconcile(_snapshot())
    reservation = ledger.reserve(_request(1), now=NOW)

    with pytest.raises(ValidationError, match="frozen"):
        snapshot.remaining_credits = 999
    with pytest.raises(ValidationError, match="frozen"):
        reservation.status = WebCreditReservationStatus.released

    assert ledger.latest_snapshot(snapshot.provider_ref).remaining_credits == 3
    assert (
        ledger.reservation_snapshot(reservation.reservation_ref).status
        == WebCreditReservationStatus.reserved
    )

def test_idempotency_ref_semantic_conflict_fails_closed() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot())
    first = _request(1)
    ledger.reserve(first, now=NOW)
    conflicting = first.model_copy(update={"estimated_credits": 2})

    with pytest.raises(WebCreditLedgerConflictError):
        ledger.reserve(conflicting, now=NOW)


def test_paid_or_unknown_plan_never_reserves_free_credits() -> None:
    for plan_kind in (WebProviderPlanKind.paid, WebProviderPlanKind.unknown):
        ledger = InMemoryWebCreditLedger()
        ledger.reconcile(_snapshot(plan_kind=plan_kind))

        reservation = ledger.reserve(_request(1), now=NOW)

        assert reservation.status == WebCreditReservationStatus.denied
        assert "CLOUD_FREE_PLAN_NOT_PROVEN" in reservation.reason_codes


def test_unknown_plan_concurrency_never_reserves_free_credits() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot().model_copy(update={"max_concurrency": None}))

    reservation = ledger.reserve(_request(1), now=NOW)

    assert reservation.status == WebCreditReservationStatus.denied
    assert "CLOUD_PLAN_CONCURRENCY_UNKNOWN" in reservation.reason_codes


def test_run_credit_ceiling_counts_prior_settlements() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot(concurrency=2))
    first_request = _request(1).model_copy(update={"run_credit_ceiling": 1})
    first = ledger.reserve(first_request, now=NOW)
    ledger.settle(
        first.reservation_ref,
        actual_credits=1,
        actual_usage_ref="actual-usage-ref:web-credit:first",
    )

    second = ledger.reserve(
        _request(2).model_copy(update={"run_credit_ceiling": 1}),
        now=NOW,
    )

    assert second.status == WebCreditReservationStatus.denied
    assert "CLOUD_RUN_CREDIT_CEILING_EXHAUSTED" in second.reason_codes


def test_snapshot_ref_reuse_with_different_semantics_fails_closed() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot(remaining=3))

    with pytest.raises(WebCreditLedgerConflictError):
        ledger.reconcile(_snapshot(remaining=2))


def test_older_snapshot_cannot_replace_newer_provider_truth() -> None:
    ledger = InMemoryWebCreditLedger()
    current = _snapshot()
    ledger.reconcile(current)
    older = current.model_copy(
        update={
            "snapshot_ref": "web-credit-snapshot-ref:older",
            "fetched_at": current.fetched_at - timedelta(minutes=1),
        }
    )

    with pytest.raises(WebCreditLedgerConflictError):
        ledger.reconcile(older)


def test_incomplete_settlement_blocks_follow_on_cloud_reservation() -> None:
    ledger = InMemoryWebCreditLedger()
    ledger.reconcile(_snapshot(concurrency=2))
    reserved = ledger.reserve(_request(1), now=NOW)

    incomplete = ledger.settle(
        reserved.reservation_ref,
        actual_credits=None,
        actual_usage_ref=None,
    )
    follow_on = ledger.reserve(_request(2), now=NOW)

    assert incomplete.status == WebCreditReservationStatus.incomplete
    assert incomplete.receipt_completeness == WebCreditReceiptCompleteness.incomplete
    assert follow_on.status == WebCreditReservationStatus.denied
    assert "CLOUD_PRIOR_USAGE_RECEIPT_INCOMPLETE" in follow_on.reason_codes


def test_sealed_router_simulation_selects_no_provider() -> None:
    decision = simulate_hybrid_route(
        request_ref="web-request-ref:sealed",
        operation=WebProviderOperation.search,
        policy=WebProviderRoutingPolicy.sealed,
        capability_states=(
            _ready_state(
                WebProviderDeploymentKind.searxng_self_hosted,
                WebProviderOperation.search,
            ),
        ),
        now=NOW,
    )

    assert decision.selected_deployment is None
    assert decision.attempt_count_ceiling == 0
    assert decision.execution_authorized is False
    assert "WEB_ROUTING_POLICY_SEALED" in decision.blocker_codes


def test_search_router_simulation_selects_only_searxng_without_authority() -> None:
    decision = simulate_hybrid_route(
        request_ref="web-request-ref:search",
        operation=WebProviderOperation.search,
        policy=WebProviderRoutingPolicy.self_host_only,
        capability_states=(
            _ready_state(
                WebProviderDeploymentKind.searxng_self_hosted,
                WebProviderOperation.search,
            ),
        ),
        now=NOW,
    )

    assert decision.selected_deployment == WebProviderDeploymentKind.searxng_self_hosted
    assert decision.fallback_deployment is None
    assert decision.simulation_only is True
    assert decision.execution_authorized is False


def test_hybrid_router_allows_at_most_one_eligible_cloud_fallback() -> None:
    states = (
        _ready_state(
            WebProviderDeploymentKind.firecrawl_self_hosted,
            WebProviderOperation.scrape_markdown,
        ),
        _ready_state(
            WebProviderDeploymentKind.firecrawl_cloud,
            WebProviderOperation.scrape_markdown,
        ),
    )
    decision = simulate_hybrid_route(
        request_ref="web-request-ref:extract",
        operation=WebProviderOperation.scrape_markdown,
        policy=WebProviderRoutingPolicy.self_host_first_cloud_escalation,
        capability_states=states,
        first_attempt_outcome=WebProviderAttemptOutcome.render_failure,
        cloud_snapshot=_snapshot(),
        now=NOW,
    )

    assert (
        decision.selected_deployment == WebProviderDeploymentKind.firecrawl_self_hosted
    )
    assert decision.fallback_deployment == WebProviderDeploymentKind.firecrawl_cloud
    assert decision.attempt_count_ceiling == 2
    assert decision.execution_authorized is False


def test_terminal_policy_outcome_never_falls_back() -> None:
    states = (
        _ready_state(
            WebProviderDeploymentKind.firecrawl_self_hosted,
            WebProviderOperation.scrape_markdown,
        ),
        _ready_state(
            WebProviderDeploymentKind.firecrawl_cloud,
            WebProviderOperation.scrape_markdown,
        ),
    )
    decision = simulate_hybrid_route(
        request_ref="web-request-ref:private-target",
        operation=WebProviderOperation.scrape_markdown,
        policy=WebProviderRoutingPolicy.self_host_first_cloud_escalation,
        capability_states=states,
        first_attempt_outcome=WebProviderAttemptOutcome.private_target_denied,
        cloud_snapshot=_snapshot(),
        now=NOW,
    )

    assert decision.fallback_deployment is None
    assert decision.attempt_count_ceiling == 1
    assert "TERMINAL_FIRST_ATTEMPT_OUTCOME_NO_FALLBACK" in decision.blocker_codes


def test_unaccepted_cloud_budget_first_policy_is_absent() -> None:
    assert "cloud_budget_first" not in {item.value for item in WebProviderRoutingPolicy}
