from __future__ import annotations

import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.providers.routing_intelligence import (
    PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    ProviderRoutingBudgetStatus,
    ProviderRoutingCompatibilityStatus,
    ProviderRoutingConfigurationStatus,
    ProviderRoutingHealthStatus,
    ProviderRoutingNeed,
    ProviderRoutingObservation,
    ProviderRoutingRuntimeClass,
    ProviderRoutingSafeDisableStatus,
    ProviderRoutingStrategy,
    build_provider_routing_proposal,
)


def _observation(
    slug: str,
    *,
    runtime_class: ProviderRoutingRuntimeClass = ProviderRoutingRuntimeClass.hosted,
    compatibility: ProviderRoutingCompatibilityStatus = (
        ProviderRoutingCompatibilityStatus.supported
    ),
    configuration: ProviderRoutingConfigurationStatus = (
        ProviderRoutingConfigurationStatus.configured
    ),
    health: ProviderRoutingHealthStatus = ProviderRoutingHealthStatus.healthy,
    budget: ProviderRoutingBudgetStatus = ProviderRoutingBudgetStatus.available,
    safe_disable: ProviderRoutingSafeDisableStatus = (
        ProviderRoutingSafeDisableStatus.inactive
    ),
    metered: bool = True,
    cost: float | None = 0.01,
    latency: float | None = 100,
    quality: float | None = 80,
    context_tokens: int | None = 32_000,
) -> ProviderRoutingObservation:
    return ProviderRoutingObservation(
        observation_ref=f"provider-routing-observation-ref:{slug}:test",
        provider_ref=f"provider-ref:{slug}:test",
        provider_label=slug.title(),
        provider_manifest_ref=f"provider-manifest-ref:{slug}:test",
        model_ref=f"model-ref:{slug}:test",
        adapter_ref=f"provider-adapter-ref:{slug}:test",
        runtime_class=runtime_class,
        compatibility_status=compatibility,
        configuration_status=configuration,
        health_status=health,
        budget_status=budget,
        safe_disable_status=safe_disable,
        metered=metered,
        estimated_cost_usd=cost,
        estimated_latency_ms=latency,
        quality_score=quality,
        context_tokens=context_tokens,
        capability_refs=["capability-ref:text-generation"],
        evidence_refs=[f"evidence-ref:provider-routing:{slug}"],
        source_ref="source-ref:test:provider-routing",
    )


def test_provider_routing_explains_cost_latency_quality_and_is_deterministic() -> None:
    need = ProviderRoutingNeed(
        strategy=ProviderRoutingStrategy.best_value,
        required_capability_refs=["capability-ref:text-generation"],
        minimum_context_tokens=16_000,
    )
    observations = [
        _observation("quality", cost=0.5, latency=120, quality=95),
        _observation("value", cost=0.01, latency=90, quality=88),
        _observation("fast", cost=0.02, latency=20, quality=75),
    ]

    first = build_provider_routing_proposal(need, observations)
    second = build_provider_routing_proposal(need, reversed(observations))

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.recommended_candidate_ref == first.candidates[0].candidate_ref
    assert first.candidates[0].provider_ref == "provider-ref:value:test"
    assert first.candidates[0].estimated_cost_usd == 0.01
    assert first.candidates[0].estimated_latency_ms == 90
    assert first.candidates[0].quality_score == 88
    assert first.invocation_authorized is False
    assert first.provider_call_performed is False
    assert first.background_fanout_performed is False
    assert first.request_scoped_invocation_decision_required is True


@pytest.mark.parametrize(
    ("change", "blocker"),
    [
        (
            {"compatibility_status": ProviderRoutingCompatibilityStatus.unknown},
            "COMPATIBILITY_UNKNOWN",
        ),
        (
            {"compatibility_status": ProviderRoutingCompatibilityStatus.unsupported},
            "COMPATIBILITY_UNSUPPORTED",
        ),
        (
            {"configuration_status": ProviderRoutingConfigurationStatus.not_configured},
            "PROVIDER_NOT_CONFIGURED",
        ),
        (
            {"health_status": ProviderRoutingHealthStatus.stale},
            "PROVIDER_HEALTH_STALE",
        ),
        (
            {"health_status": ProviderRoutingHealthStatus.unhealthy},
            "PROVIDER_UNHEALTHY",
        ),
        (
            {"budget_status": ProviderRoutingBudgetStatus.unknown},
            "METERED_PROVIDER_BUDGET_UNKNOWN",
        ),
        (
            {"budget_status": ProviderRoutingBudgetStatus.exhausted},
            "PROVIDER_BUDGET_EXHAUSTED",
        ),
        (
            {"safe_disable_status": ProviderRoutingSafeDisableStatus.active},
            "SAFE_DISABLE_ACTIVE",
        ),
    ],
)
def test_provider_routing_unknown_or_unsafe_states_fail_closed(
    change: dict[str, object], blocker: str
) -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("blocked").model_copy(update=change)],
    )

    assert proposal.recommended_candidate_ref is None
    assert proposal.candidates[0].status == "blocked"
    assert blocker in proposal.candidates[0].blocker_codes
    assert proposal.invocation_authorized is False


def test_safe_disable_overrides_otherwise_positive_provider_state() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [
            _observation(
                "disabled",
                cost=0,
                latency=1,
                quality=100,
                safe_disable=ProviderRoutingSafeDisableStatus.active,
            )
        ],
    )

    assert proposal.recommended_candidate_ref is None
    assert "SAFE_DISABLE_ACTIVE" in proposal.candidates[0].blocker_codes


def test_degraded_provider_requires_exact_permitting_policy() -> None:
    blocked = build_provider_routing_proposal(
        ProviderRoutingNeed(allow_degraded=False),
        [_observation("degraded", health=ProviderRoutingHealthStatus.degraded)],
    )
    allowed_for_evaluation = build_provider_routing_proposal(
        ProviderRoutingNeed(allow_degraded=True),
        [_observation("degraded", health=ProviderRoutingHealthStatus.degraded)],
    )

    assert "DEGRADED_USE_NOT_PERMITTED" in blocked.candidates[0].blocker_codes
    assert allowed_for_evaluation.candidates[0].status == (
        "degraded_requires_exact_policy"
    )
    assert allowed_for_evaluation.invocation_authorized is False


def test_provider_routing_presentation_is_bounded_without_fanout_execution() -> None:
    observations = [_observation(f"provider-{index}") for index in range(8)]
    proposal = build_provider_routing_proposal(ProviderRoutingNeed(), observations)

    assert proposal.observed_candidate_count == 8
    assert (
        proposal.presented_candidate_count == PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES
    )
    assert proposal.omitted_candidate_count == 4
    assert proposal.background_fanout_performed is False


def test_provider_routing_rejects_duplicate_or_unsafe_observations() -> None:
    observation = _observation("duplicate")
    with pytest.raises(ValueError, match="DUPLICATE_PROVIDER_REF"):
        build_provider_routing_proposal(
            ProviderRoutingNeed(),
            [observation, observation],
        )
    with pytest.raises(ValidationError):
        _observation("unsafe").model_copy(
            update={"provider_label": "api_key=sk-example-secret-value"}
        )


def test_control_plane_and_cli_expose_same_non_authorizing_provider_intelligence() -> (
    None
):
    read_model = build_model_provider_control_plane_read_model()
    routing = read_model.provider_routing_intelligence

    assert routing.schema_version == "provider_routing_intelligence.v1"
    assert routing.observed_candidate_count == 3
    assert routing.recommended_candidate_ref is None
    assert routing.invocation_authorized is False
    assert routing.provider_call_performed is False
    assert all(candidate.status == "blocked" for candidate in routing.candidates)

    completed = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py", "--json"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["provider_routing_intelligence"] == routing.model_dump(mode="json")

    readable = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "UAA model/provider control plane" in readable.stdout
    assert (
        "Provider selection is a proposal, never invocation authority."
        in readable.stdout
    )
    assert "METERED_PROVIDER_BUDGET_UNKNOWN" in readable.stdout
