"""Pure provider-routing simulation for WEB-HYBRID-001.

The simulator chooses a provider candidate but always reports no execution
authority and performs no reservation or network call.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ultimate_ai_agent.core.capability_availability.contracts import (
    DerivedRuntimeReadinessStatus,
    ResourceBudgetStatus,
)

from .hybrid_contracts import (
    WebCreditSnapshotFreshness,
    WebProviderAttemptOutcome,
    WebProviderCapabilityState,
    WebProviderCircuitState,
    WebProviderCreditSnapshot,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderPlanKind,
    WebProviderRoutingDecision,
    WebProviderRoutingPolicy,
    stable_web_hybrid_ref,
)


_FALLBACK_ELIGIBLE = {
    WebProviderAttemptOutcome.timeout,
    WebProviderAttemptOutcome.connection_failure,
    WebProviderAttemptOutcome.provider_5xx,
    WebProviderAttemptOutcome.render_failure,
    WebProviderAttemptOutcome.empty_content,
    WebProviderAttemptOutcome.bot_challenge,
}

_TERMINAL_OUTCOMES = {
    WebProviderAttemptOutcome.policy_denied,
    WebProviderAttemptOutcome.private_target_denied,
    WebProviderAttemptOutcome.robots_terms_denied,
    WebProviderAttemptOutcome.authority_denied,
    WebProviderAttemptOutcome.target_4xx,
    WebProviderAttemptOutcome.unsupported_content_type,
    WebProviderAttemptOutcome.scope_exhausted,
    WebProviderAttemptOutcome.incomplete_credit_receipt,
    WebProviderAttemptOutcome.unknown_failure,
}


def simulate_hybrid_route(
    *,
    request_ref: str,
    operation: WebProviderOperation,
    policy: WebProviderRoutingPolicy,
    capability_states: tuple[WebProviderCapabilityState, ...],
    first_attempt_outcome: WebProviderAttemptOutcome = (
        WebProviderAttemptOutcome.not_attempted
    ),
    cloud_snapshot: WebProviderCreditSnapshot | None = None,
    in_flight_reserved_credits: int = 0,
    cloud_safety_reserve_credits: int = 1,
    cloud_circuit_state: WebProviderCircuitState = WebProviderCircuitState.closed,
    now: datetime | None = None,
) -> WebProviderRoutingDecision:
    now = now or datetime.now(timezone.utc)
    state_by_deployment = {
        state.deployment: state
        for state in capability_states
        if state.operation == operation
    }
    reasons: list[str] = []
    blockers: list[str] = []
    selected: WebProviderDeploymentKind | None = None
    fallback: WebProviderDeploymentKind | None = None

    if policy == WebProviderRoutingPolicy.sealed:
        blockers.append("WEB_ROUTING_POLICY_SEALED")
    elif operation == WebProviderOperation.search:
        candidate = state_by_deployment.get(
            WebProviderDeploymentKind.searxng_self_hosted
        )
        if _state_route_ready(candidate):
            selected = WebProviderDeploymentKind.searxng_self_hosted
            reasons.append("SEARXNG_SELECTED_FOR_SEARCH_SIMULATION")
        else:
            blockers.extend(_state_blockers(candidate, "SEARXNG"))
    elif operation == WebProviderOperation.scrape_markdown:
        local = state_by_deployment.get(WebProviderDeploymentKind.firecrawl_self_hosted)
        cloud = state_by_deployment.get(WebProviderDeploymentKind.firecrawl_cloud)
        if _state_route_ready(local):
            selected = WebProviderDeploymentKind.firecrawl_self_hosted
            reasons.append("FIRECRAWL_SELF_HOSTED_SELECTED_FOR_SIMULATION")
        else:
            blockers.extend(_state_blockers(local, "FIRECRAWL_SELF_HOSTED"))

        if policy == WebProviderRoutingPolicy.self_host_first_cloud_escalation:
            if first_attempt_outcome in _TERMINAL_OUTCOMES:
                blockers.append("TERMINAL_FIRST_ATTEMPT_OUTCOME_NO_FALLBACK")
            elif first_attempt_outcome == WebProviderAttemptOutcome.succeeded:
                reasons.append("FIRST_ATTEMPT_SUCCEEDED_NO_FALLBACK")
            elif first_attempt_outcome in _FALLBACK_ELIGIBLE:
                if cloud_circuit_state == WebProviderCircuitState.open:
                    blockers.append("FIRECRAWL_CLOUD_CIRCUIT_OPEN")
                elif cloud_circuit_state == WebProviderCircuitState.unknown:
                    blockers.append("FIRECRAWL_CLOUD_CIRCUIT_UNKNOWN")
                elif _state_route_ready(cloud) and _cloud_credit_route_ready(
                    cloud_snapshot,
                    in_flight_reserved_credits=in_flight_reserved_credits,
                    safety_reserve_credits=cloud_safety_reserve_credits,
                    now=now,
                ):
                    fallback = WebProviderDeploymentKind.firecrawl_cloud
                    reasons.append("FIRECRAWL_CLOUD_FALLBACK_ELIGIBLE_SIMULATION")
                else:
                    blockers.append("FIRECRAWL_CLOUD_FALLBACK_NOT_READY")
            elif first_attempt_outcome != WebProviderAttemptOutcome.not_attempted:
                blockers.append("FIRST_ATTEMPT_OUTCOME_NOT_FALLBACK_ELIGIBLE")
        elif policy != WebProviderRoutingPolicy.self_host_only:
            blockers.append("WEB_ROUTING_POLICY_UNSUPPORTED")
    else:
        blockers.append("WEB_PROVIDER_OPERATION_NOT_ROUTABLE")

    if selected is None:
        fallback = None
    attempt_count = 0 if selected is None else (2 if fallback is not None else 1)
    decision_ref = stable_web_hybrid_ref(
        "web-provider-routing-decision-ref",
        {
            "request_ref": request_ref,
            "operation": operation.value,
            "policy": policy.value,
            "selected": selected.value if selected else None,
            "fallback": fallback.value if fallback else None,
            "first_attempt_outcome": first_attempt_outcome.value,
        },
    )
    return WebProviderRoutingDecision(
        decision_ref=decision_ref,
        request_ref=request_ref,
        policy=policy,
        operation=operation,
        selected_deployment=selected,
        fallback_deployment=fallback,
        attempt_count_ceiling=attempt_count,
        reason_codes=tuple(dict.fromkeys(reasons)),
        blocker_codes=tuple(dict.fromkeys(blockers)),
    )


def _state_route_ready(state: WebProviderCapabilityState | None) -> bool:
    return bool(
        state is not None
        and state.runtime_readiness == DerivedRuntimeReadinessStatus.ready
        and state.resource_status != ResourceBudgetStatus.exhausted
    )


def _state_blockers(
    state: WebProviderCapabilityState | None,
    prefix: str,
) -> list[str]:
    if state is None:
        return [f"{prefix}_CAPABILITY_STATE_MISSING"]
    return list(state.blocker_codes) or [f"{prefix}_CAPABILITY_NOT_READY"]


def _cloud_credit_route_ready(
    snapshot: WebProviderCreditSnapshot | None,
    *,
    in_flight_reserved_credits: int,
    safety_reserve_credits: int,
    now: datetime,
) -> bool:
    return bool(
        snapshot is not None
        and snapshot.plan_kind == WebProviderPlanKind.free
        and snapshot.freshness == WebCreditSnapshotFreshness.current
        and snapshot.max_concurrency is not None
        and snapshot.expires_at > now
        and snapshot.billing_period_start <= now < snapshot.billing_period_end
        and snapshot.remaining_credits
        - in_flight_reserved_credits
        - safety_reserve_credits
        >= 1
    )


__all__ = ["simulate_hybrid_route"]
