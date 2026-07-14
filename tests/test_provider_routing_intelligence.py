from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.providers import routing_intelligence as routing
from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CatalogStatus,
    CostPosture,
    FreshnessStatus,
    build_capability_availability_snapshot,
)
from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.providers.readiness import (
    ProviderCredentialReadinessPosture,
)
from ultimate_ai_agent.core.providers.routing_intelligence import (
    PROVIDER_ROUTING_MAX_OBSERVATIONS,
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
    observations_from_provider_readiness,
)


CHECKED_AT = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


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
    freshness: FreshnessStatus = FreshnessStatus.current,
    metered: bool = True,
    cost: float | None = 0.01,
    latency: float | None = 100,
    quality: float | None = 80,
    context_tokens: int | None = 32_000,
    adapter_ref: str | None = None,
    provider_label: str | None = None,
    snapshot_reason_codes: list[str] | None = None,
) -> ProviderRoutingObservation:
    provider_ref = f"provider-ref:{slug}:test"
    adapter_ref = adapter_ref or f"provider-adapter-ref:{slug}:test"
    source_ref = "source-ref:test:provider-routing"
    evidence_refs = [f"evidence-ref:provider-routing:{slug}"]
    snapshot = build_capability_availability_snapshot(
        snapshot_ref=f"capability-availability-ref:provider-routing:{slug}",
        capability_ref="capability-ref:provider-model-invocation",
        provider_ref=provider_ref,
        adapter_ref=adapter_ref,
        catalog_status=CatalogStatus.supported,
        compatibility_status=compatibility,
        configuration_status=configuration,
        health_status=health,
        authority_posture=AuthorityPosture.blocked,
        resource_status=budget,
        cost_posture=(CostPosture.metered if metered else CostPosture.not_metered),
        safe_disable_status=safe_disable,
        checked_at=CHECKED_AT,
        freshness_status=freshness,
        source_ref=source_ref,
        safe_summary=(
            "Injected deterministic provider availability for fail-closed routing tests."
        ),
        reason_codes=snapshot_reason_codes,
        evidence_refs=evidence_refs,
    )
    return ProviderRoutingObservation(
        observation_ref=f"provider-routing-observation-ref:{slug}:test",
        provider_ref=provider_ref,
        provider_label=provider_label or slug.title(),
        provider_manifest_ref=f"provider-manifest-ref:{slug}:test",
        model_ref=f"model-ref:{slug}:test",
        adapter_ref=adapter_ref,
        runtime_class=runtime_class,
        availability_snapshot=snapshot,
        metered=metered,
        estimated_cost_usd=cost,
        estimated_latency_ms=latency,
        quality_score=quality,
        context_tokens=context_tokens,
        capability_refs=["capability-ref:text-generation"],
        evidence_refs=evidence_refs,
        source_ref=source_ref,
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
    assert len(first.request_fingerprint_ref.rsplit(":", 1)[-1]) == 64
    assert len(first.observation_set_fingerprint_ref.rsplit(":", 1)[-1]) == 64
    assert first.invocation_authorized is False
    assert first.provider_call_performed is False
    assert first.background_fanout_performed is False
    assert first.request_scoped_invocation_decision_required is True


@pytest.mark.parametrize(
    ("kwargs", "blocker"),
    [
        (
            {"compatibility": ProviderRoutingCompatibilityStatus.unknown},
            "COMPATIBILITY_STATUS_UNKNOWN",
        ),
        (
            {"compatibility": ProviderRoutingCompatibilityStatus.unsupported},
            "COMPATIBILITY_UNSUPPORTED",
        ),
        (
            {"configuration": ProviderRoutingConfigurationStatus.not_configured},
            "NOT_CONFIGURED",
        ),
        ({"health": ProviderRoutingHealthStatus.stale}, "HEALTH_STALE"),
        ({"health": ProviderRoutingHealthStatus.unhealthy}, "HEALTH_UNHEALTHY"),
        (
            {"health": ProviderRoutingHealthStatus.degraded},
            "HEALTH_DEGRADED_NOT_PERMITTED",
        ),
        (
            {"budget": ProviderRoutingBudgetStatus.unknown},
            "METERED_BUDGET_STATUS_UNKNOWN",
        ),
        (
            {"budget": ProviderRoutingBudgetStatus.exhausted},
            "RESOURCE_BUDGET_EXHAUSTED",
        ),
        (
            {"budget": ProviderRoutingBudgetStatus.constrained},
            "RESOURCE_BUDGET_CONSTRAINED",
        ),
        (
            {"safe_disable": ProviderRoutingSafeDisableStatus.active},
            "SAFE_DISABLE_ACTIVE",
        ),
        ({"freshness": FreshnessStatus.stale}, "OBSERVATION_STALE"),
    ],
)
def test_provider_routing_unknown_or_unsafe_states_fail_closed(
    kwargs: dict[str, object], blocker: str
) -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("blocked", **kwargs)],
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
    assert proposal.candidates[0].blocker_codes[0] == "SAFE_DISABLE_ACTIVE"


def test_degraded_and_constrained_provider_states_are_not_rankable() -> None:
    for observation in (
        _observation("degraded", health=ProviderRoutingHealthStatus.degraded),
        _observation("constrained", budget=ProviderRoutingBudgetStatus.constrained),
    ):
        proposal = build_provider_routing_proposal(
            ProviderRoutingNeed(),
            [observation],
        )
        assert proposal.recommended_candidate_ref is None
        assert proposal.candidates[0].status == "blocked"


def test_provider_routing_presentation_and_observation_input_are_bounded() -> None:
    observations = [_observation(f"provider-{index}") for index in range(8)]
    proposal = build_provider_routing_proposal(ProviderRoutingNeed(), observations)

    assert proposal.observed_candidate_count == 8
    assert (
        proposal.presented_candidate_count == PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES
    )
    assert proposal.omitted_candidate_count == 4
    assert proposal.background_fanout_performed is False

    consumed = 0

    def too_many_observations():
        nonlocal consumed
        for index in range(PROVIDER_ROUTING_MAX_OBSERVATIONS + 50):
            consumed += 1
            yield _observation(f"bounded-{index}")

    with pytest.raises(ValueError, match="OBSERVATION_LIMIT_EXCEEDED"):
        build_provider_routing_proposal(
            ProviderRoutingNeed(),
            too_many_observations(),
        )
    assert consumed == PROVIDER_ROUTING_MAX_OBSERVATIONS + 1


def test_provider_routing_rejects_duplicate_or_unsafe_observations() -> None:
    observation = _observation("duplicate")
    with pytest.raises(ValueError, match="DUPLICATE_PROVIDER_REF"):
        build_provider_routing_proposal(
            ProviderRoutingNeed(),
            [
                observation,
                observation.model_copy(
                    update={
                        "observation_ref": "provider-routing-observation-ref:duplicate:second"
                    }
                ),
            ],
        )
    with pytest.raises(ValueError, match="DUPLICATE_OBSERVATION_REF"):
        build_provider_routing_proposal(
            ProviderRoutingNeed(),
            [
                observation,
                _observation("other").model_copy(
                    update={"observation_ref": observation.observation_ref}
                ),
            ],
        )

    unsafe_labels = [
        "api_key=sk-example-secret-value",
        "/private/tmp/provider",
        "provider.example.com",
        "@operator-name",
        "PROVIDER_TOKEN=value",
    ]
    for label in unsafe_labels:
        with pytest.raises((ValidationError, ValueError)):
            _observation("unsafe", provider_label=label)


def test_provider_routing_rejects_non_finite_metrics() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValidationError):
            _observation("non-finite", latency=value)


def test_local_first_uses_explicit_runtime_class_not_adapter_text() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(strategy=ProviderRoutingStrategy.local_first),
        [
            _observation(
                "hosted-local-text",
                runtime_class=ProviderRoutingRuntimeClass.hosted,
                adapter_ref="provider-adapter-ref:contains-local:text",
                cost=0,
            ),
            _observation(
                "local",
                runtime_class=ProviderRoutingRuntimeClass.local,
                adapter_ref="provider-adapter-ref:ordinary:test",
                cost=1,
            ),
            _observation(
                "unknown",
                runtime_class=ProviderRoutingRuntimeClass.unknown,
                cost=0,
            ),
        ],
    )

    assert [candidate.runtime_class for candidate in proposal.candidates[:3]] == [
        "local",
        "hosted",
        "unknown",
    ]
    assert proposal.candidates[0].provider_ref == "provider-ref:local:test"


def test_proposal_identity_binds_all_observations_including_omitted_candidates() -> (
    None
):
    need = ProviderRoutingNeed(maximum_presented_candidates=4)
    observations = [_observation(f"provider-{index}") for index in range(5)]
    first = build_provider_routing_proposal(need, observations)
    changed = [*observations[:4], _observation("replacement")]
    second = build_provider_routing_proposal(need, changed)

    assert first.presented_candidate_count == second.presented_candidate_count == 4
    assert (
        first.observation_set_fingerprint_ref != second.observation_set_fingerprint_ref
    )
    assert first.proposal_ref != second.proposal_ref
    assert len(first.observation_fingerprint_refs) == 5
    assert first.observation_fingerprint_refs == sorted(
        first.observation_fingerprint_refs
    )


def test_candidate_and_proposal_identity_change_with_runtime_truth() -> None:
    ready = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("identity")],
    )
    stale = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("identity", freshness=FreshnessStatus.stale)],
    )

    assert ready.proposal_ref != stale.proposal_ref
    assert ready.candidates[0].candidate_ref != stale.candidates[0].candidate_ref
    assert ready.candidates[0].observation_fingerprint_ref != (
        stale.candidates[0].observation_fingerprint_ref
    )


def test_candidate_deduplicates_normalized_snapshot_reason_codes() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [
            _observation(
                "duplicate-reason",
                snapshot_reason_codes=["PROVIDER_OBSERVATION_EVALUATED"],
            )
        ],
    )

    assert (
        proposal.candidates[0].reason_codes.count("PROVIDER_OBSERVATION_EVALUATED") == 1
    )


def test_candidate_rejects_snapshot_identity_metric_and_fingerprint_tampering() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("tamper")],
    )
    candidate = proposal.candidates[0]

    with pytest.raises(ValidationError, match="CANDIDATE_PROVIDER_REF_MISMATCH"):
        candidate.model_copy(update={"provider_ref": "provider-ref:other:test"})
    with pytest.raises(ValidationError):
        candidate.model_copy(update={"estimated_latency_ms": -1})
    with pytest.raises(ValidationError, match="OBSERVATION_FINGERPRINT_INVALID"):
        candidate.model_copy(
            update={"observation_fingerprint_ref": "observation-fingerprint-ref:short"}
        )
    with pytest.raises(ValidationError, match="CANDIDATE_FINGERPRINT_DRIFT"):
        candidate.model_copy(
            update={"candidate_ref": f"provider-routing-candidate-ref:{'0' * 64}"}
        )
    for update in (
        {"estimated_latency_ms": 999},
        {"quality_score": 1},
        {"model_ref": "model-ref:other:test"},
        {"observation_ref": "provider-routing-observation-ref:other:test"},
    ):
        with pytest.raises(ValidationError, match="CANDIDATE_FINGERPRINT_DRIFT"):
            candidate.model_copy(update=update)


def test_proposal_rejects_unbound_or_malformed_fingerprint_refs() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("binding")],
    )
    with pytest.raises(ValidationError, match="PROPOSAL_FINGERPRINT_INVALID"):
        proposal.model_copy(
            update={"proposal_ref": "provider-routing-proposal-ref:short"}
        )
    with pytest.raises(ValidationError, match="PROPOSAL_FINGERPRINT_DRIFT"):
        proposal.model_copy(
            update={"proposal_ref": f"provider-routing-proposal-ref:{'0' * 64}"}
        )
    for update in (
        {"request_ref": "provider-routing-request-ref:other:test"},
        {"strategy": ProviderRoutingStrategy.lowest_latency},
        {"recommended_candidate_ref": None},
        {"reason_codes": ["PROVIDER_ROUTING_PROPOSAL_ONLY"]},
        {"blocker_codes": ["SYNTHETIC_BLOCKER_NOT_OBSERVED"]},
    ):
        with pytest.raises(ValidationError, match="PROPOSAL_FINGERPRINT_DRIFT"):
            proposal.model_copy(update=update)
    with pytest.raises(ValidationError, match="CANDIDATE_FINGERPRINT_NOT_BOUND"):
        unbound_payload = dict(proposal.candidates[0].__dict__)
        unbound_payload["observation_fingerprint_ref"] = (
            f"observation-fingerprint-ref:{'0' * 64}"
        )
        unbound_draft = routing.ProviderRoutingCandidate.model_construct(
            **unbound_payload
        )
        unbound_payload["candidate_ref"] = routing._candidate_decision_ref(
            unbound_draft
        )
        tampered_candidate = routing.ProviderRoutingCandidate.model_validate(
            unbound_payload
        )
        proposal.model_copy(
            update={"candidates": [tampered_candidate]},
        )

    candidate_payload = dict(proposal.candidates[0].__dict__)
    candidate_payload["quality_score"] = 1
    draft = routing.ProviderRoutingCandidate.model_construct(**candidate_payload)
    candidate_payload["candidate_ref"] = routing._candidate_decision_ref(draft)
    self_consistent_candidate = routing.ProviderRoutingCandidate.model_validate(
        candidate_payload
    )
    with pytest.raises(ValidationError, match="PROPOSAL_FINGERPRINT_DRIFT"):
        proposal.model_copy(update={"candidates": [self_consistent_candidate]})


def test_readiness_adapter_preserves_unknown_and_blocked_truth() -> None:
    source = {
        "provider_id": "provider:reference:test",
        "provider_label": "Reference provider",
        "provider_manifest_ref": "provider-manifest-ref:reference:test",
        "credential_configured": False,
        "provider_model_refs_bound": False,
        "readiness_posture": ProviderCredentialReadinessPosture.not_configured,
        "policy_ref": "policy-ref:provider:test",
        "blocker_codes": ["PROVIDER_CONFIGURATION_REQUIRED"],
        "cost_governor_binding": {
            "binding_ref": "provider-cost-binding-ref:reference:test",
            "model_ref": "model-ref:reference:not-selected",
        },
    }
    observation = observations_from_provider_readiness(
        [source],
        checked_at=CHECKED_AT,
    )[0]
    snapshot = observation.availability_snapshot

    assert observation.runtime_class == "unknown"
    assert snapshot.compatibility_status.value == "unknown"
    assert snapshot.catalog_status.value == "unknown"
    assert snapshot.configuration_status.value == "not_configured"
    assert snapshot.health_status.value == "unknown"
    assert snapshot.resource_status.value == "unknown"
    assert snapshot.safe_disable_status.value == "unknown"
    assert snapshot.freshness_status.value == "unknown"
    assert snapshot.authority_posture.value == "blocked"
    assert "PROVIDER_INVOCATION_AUTHORITY_BLOCKED" in snapshot.blocker_codes


def test_readiness_adapter_input_is_bounded_before_full_materialization() -> None:
    consumed = 0

    def readiness_items():
        nonlocal consumed
        for index in range(PROVIDER_ROUTING_MAX_OBSERVATIONS + 50):
            consumed += 1
            yield {
                "provider_id": f"provider:bounded-{index}:test",
                "provider_label": f"Bounded provider {index}",
                "provider_manifest_ref": f"provider-manifest-ref:bounded-{index}:test",
                "readiness_posture": ProviderCredentialReadinessPosture.not_configured,
                "policy_ref": f"policy-ref:bounded-{index}:test",
                "blocker_codes": ["PROVIDER_CONFIGURATION_REQUIRED"],
                "cost_governor_binding": {
                    "binding_ref": f"provider-cost-binding-ref:bounded-{index}:test",
                    "model_ref": f"model-ref:bounded-{index}:not-selected",
                },
            }

    with pytest.raises(ValueError, match="OBSERVATION_LIMIT_EXCEEDED"):
        observations_from_provider_readiness(
            readiness_items(),
            checked_at=CHECKED_AT,
        )
    assert consumed == PROVIDER_ROUTING_MAX_OBSERVATIONS + 1


def test_control_plane_and_cli_expose_same_non_authorizing_provider_intelligence() -> (
    None
):
    read_model = build_model_provider_control_plane_read_model(observed_at=CHECKED_AT)
    routing = read_model.provider_routing_intelligence

    assert routing.schema_version == "provider_routing_intelligence.v1"
    assert routing.observed_candidate_count == 3
    assert routing.recommended_candidate_ref is None
    assert routing.invocation_authorized is False
    assert routing.provider_call_performed is False
    assert all(candidate.status == "blocked" for candidate in routing.candidates)
    assert all(
        candidate.availability_snapshot.runtime_readiness_status.value != "ready"
        for candidate in routing.candidates
    )

    completed = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py", "--json"],
        check=True,
        text=True,
        capture_output=True,
    )
    cli_routing = json.loads(completed.stdout)["provider_routing_intelligence"]
    assert cli_routing["schema_version"] == routing.schema_version
    assert cli_routing["observed_candidate_count"] == routing.observed_candidate_count
    assert cli_routing["recommended_candidate_ref"] is None
    assert cli_routing["invocation_authorized"] is False
    assert [item["provider_ref"] for item in cli_routing["candidates"]] == [
        item.provider_ref for item in routing.candidates
    ]

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
    assert "PROVIDER_RUNTIME_NOT_READY" in readable.stdout
