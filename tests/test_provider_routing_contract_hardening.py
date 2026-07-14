from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.test_provider_routing_intelligence import _observation
from ultimate_ai_agent.core.capability_availability import AuthorityPosture
from ultimate_ai_agent.core.providers import routing_intelligence as routing
from ultimate_ai_agent.core.providers.routing_intelligence import (
    ProviderRoutingNeed,
    build_provider_routing_proposal,
)


def _self_consistent_candidate_payload(
    candidate: routing.ProviderRoutingCandidate,
    **updates: object,
) -> dict[str, object]:
    payload = dict(candidate.__dict__)
    payload.update(updates)
    for field_name in ("reason_codes", "blocker_codes", "evidence_refs"):
        if isinstance(payload.get(field_name), list):
            payload[field_name] = tuple(payload[field_name])
    draft = routing.ProviderRoutingCandidate.model_construct(**payload)
    payload["candidate_ref"] = routing._candidate_decision_ref(draft)
    return payload


def test_runtime_ready_but_authority_blocked_is_not_recommended() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("authority-blocked", authority_posture=AuthorityPosture.blocked)],
    )

    assert proposal.recommended_candidate_ref is None
    assert proposal.candidates[0].status == "blocked"
    assert "PROVIDER_INVOCATION_AUTHORITY_BLOCKED" in (
        proposal.candidates[0].blocker_codes
    )
    assert proposal.candidates[0].availability_snapshot.runtime_readiness_status == (
        "ready"
    )


def test_candidate_contract_rejects_reconstructed_blocked_authority_as_eligible() -> (
    None
):
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [
            _observation(
                "contract-authority-blocked",
                authority_posture=AuthorityPosture.blocked,
            )
        ],
    )
    payload = _self_consistent_candidate_payload(
        proposal.candidates[0],
        status="eligible_for_request_scoped_evaluation",
        blocker_codes=[],
    )

    with pytest.raises(
        ValidationError,
        match="BLOCKED_AUTHORITY_CANDIDATE_INVALID",
    ):
        routing.ProviderRoutingCandidate.model_validate(payload)


def test_candidate_contract_preserves_canonical_snapshot_blockers() -> None:
    observation = _observation("snapshot-blocker")
    blocked_snapshot = observation.availability_snapshot.model_copy(
        update={"blocker_codes": ["ADAPTER_SAFE_DISABLE_PENDING"]}
    )
    blocked_observation = observation.model_copy(
        update={"availability_snapshot": blocked_snapshot}
    )
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [blocked_observation],
    )
    assert proposal.candidates[0].status == "blocked"

    payload = _self_consistent_candidate_payload(
        proposal.candidates[0],
        status="eligible_for_request_scoped_evaluation",
        blocker_codes=[],
    )
    with pytest.raises(ValidationError, match="CANDIDATE_BLOCKER_INCOMPLETE"):
        routing.ProviderRoutingCandidate.model_validate(payload)


@pytest.mark.parametrize(
    "authority_posture",
    [AuthorityPosture.approval_required, AuthorityPosture.lease_required],
)
def test_non_authorizing_postures_remain_explicit_in_proposal_candidates(
    authority_posture: AuthorityPosture,
) -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("scoped-authority", authority_posture=authority_posture)],
    )

    assert proposal.recommended_candidate_ref is not None
    assert proposal.invocation_authorized is False
    assert proposal.candidates[0].invocation_authorized is False
    assert any(
        code in proposal.candidates[0].reason_codes
        for code in (
            "PROVIDER_APPROVAL_REQUIRED_BEFORE_INVOCATION",
            "PROVIDER_LEASE_REQUIRED_BEFORE_INVOCATION",
        )
    )


def test_proposal_contract_cannot_hide_presented_candidate_blockers() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("hidden-blocker", authority_posture=AuthorityPosture.blocked)],
    )
    payload = dict(proposal.__dict__)
    payload["blocker_codes"] = []
    payload["proposal_ref"] = routing._proposal_ref(
        request_ref=proposal.request_ref,
        request_fingerprint_ref=proposal.request_fingerprint_ref,
        observation_set_fingerprint_ref=proposal.observation_set_fingerprint_ref,
        strategy=proposal.strategy,
        presented_candidate_refs=[
            candidate.candidate_ref for candidate in proposal.candidates
        ],
        evaluated_candidate_refs=[
            candidate.candidate_ref for candidate in proposal.evaluated_candidates
        ],
        observed_candidate_count=proposal.observed_candidate_count,
        omitted_candidate_count=proposal.omitted_candidate_count,
        recommended_candidate_ref=proposal.recommended_candidate_ref,
        reason_codes=proposal.reason_codes,
        blocker_codes=[],
        maximum_presented_candidates=proposal.maximum_presented_candidates,
        approval_queue_route_ref=proposal.approval_queue_route_ref,
        run_detail_group_ref=proposal.run_detail_group_ref,
        bounded_fanout_presentation_ref=proposal.bounded_fanout_presentation_ref,
        source_ref=proposal.source_ref,
        safe_summary=proposal.safe_summary,
    )

    with pytest.raises(
        ValidationError,
        match="PROPOSAL_BLOCKER_SET_DRIFT",
    ):
        routing.ProviderRoutingProposal.model_validate(payload)


@pytest.mark.parametrize("maximum", [0, 5, 1_000_000])
def test_proposal_contract_bounds_presentation_maximum(maximum: int) -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("presentation-maximum")],
    )

    with pytest.raises(ValidationError):
        proposal.model_copy(update={"maximum_presented_candidates": maximum})


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "/" + "Users/example/private-summary",
        "host.internal supplied provider routing evidence.",
        "@example-user supplied provider routing evidence.",
        "NAME=private-value supplied provider routing evidence.",
    ],
)
def test_provider_routing_proposal_rejects_unsafe_summary_text(
    unsafe_summary: str,
) -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("safe-summary")],
    )

    with pytest.raises(ValidationError):
        proposal.model_copy(update={"safe_summary": unsafe_summary})


def test_provider_routing_requires_exact_invocation_capability_snapshot() -> None:
    observation = _observation("wrong-capability")
    wrong_snapshot = observation.availability_snapshot.model_copy(
        update={"capability_ref": "capability-ref:filesystem-metadata-read"}
    )

    with pytest.raises(ValidationError, match="SNAPSHOT_CAPABILITY_REF_MISMATCH"):
        observation.model_copy(update={"availability_snapshot": wrong_snapshot})


def test_provider_routing_preserves_complete_snapshot_evidence() -> None:
    observation = _observation("complete-evidence")
    expanded_snapshot = observation.availability_snapshot.model_copy(
        update={
            "evidence_refs": [
                *observation.availability_snapshot.evidence_refs,
                "evidence-ref:provider-routing:second",
            ]
        }
    )

    with pytest.raises(ValidationError, match="SNAPSHOT_EVIDENCE_INCOMPLETE"):
        observation.model_copy(update={"availability_snapshot": expanded_snapshot})


@pytest.mark.parametrize(
    "unsafe_ref",
    [
        "provider-routing-request-ref:@private-user",
        "provider-routing-request-ref:host.internal",
        "provider-routing-request-ref:/" + "Users/example/private",
        "provider-routing-request-ref:PRIVATE_VALUE" + "=placeholder",
    ],
)
def test_provider_routing_rejects_unsafe_durable_refs(unsafe_ref: str) -> None:
    with pytest.raises(ValidationError, match="PROVIDER_ROUTING_NEED_REF_INVALID"):
        ProviderRoutingNeed(request_ref=unsafe_ref)


def test_provider_routing_contracts_are_immutable() -> None:
    need = ProviderRoutingNeed()
    proposal = build_provider_routing_proposal(
        need,
        [_observation("immutable")],
    )

    with pytest.raises(ValidationError, match="frozen"):
        proposal.invocation_authorized = True  # type: ignore[misc]
    with pytest.raises(ValidationError, match="frozen"):
        need.maximum_presented_candidates = 999  # type: ignore[misc]
    assert isinstance(proposal.candidates, tuple)
    assert isinstance(proposal.observation_fingerprint_refs, tuple)


def test_proposal_request_projection_rejects_request_truth_drift() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(
            required_capability_refs=("capability-ref:text-generation",),
            minimum_context_tokens=128,
        ),
        [_observation("request-binding")],
    )
    payload = proposal.model_dump(mode="python")
    request_payload = dict(payload["request"])
    request_payload["task_ref"] = "task-ref:provider-routing:changed"
    payload["request"] = request_payload

    with pytest.raises(ValidationError, match="REQUEST_FINGERPRINT_DRIFT"):
        routing.ProviderRoutingProposal.model_validate(payload)


def test_proposal_rejects_request_strategy_or_presentation_limit_drift() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(
            strategy=routing.ProviderRoutingStrategy.lowest_latency,
            maximum_presented_candidates=2,
        ),
        [_observation("request-drift-a"), _observation("request-drift-b")],
    )
    strategy_drift = proposal.model_dump(mode="python")
    strategy_drift["strategy"] = routing.ProviderRoutingStrategy.best_quality
    with pytest.raises(ValidationError, match="REQUEST_STRATEGY_MISMATCH"):
        routing.ProviderRoutingProposal.model_validate(strategy_drift)

    limit_drift = proposal.model_dump(mode="python")
    limit_drift["maximum_presented_candidates"] = 3
    with pytest.raises(ValidationError, match="REQUEST_PRESENTATION_LIMIT_MISMATCH"):
        routing.ProviderRoutingProposal.model_validate(limit_drift)


def test_proposal_rejects_duplicate_or_underfilled_presentations() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("presentation-a"), _observation("presentation-b")],
    )
    duplicate = proposal.model_dump(mode="python")
    duplicate["candidates"] = [
        duplicate["candidates"][0],
        duplicate["candidates"][0],
    ]
    with pytest.raises(ValidationError, match="PRESENTED_CANDIDATE_DUPLICATE"):
        routing.ProviderRoutingProposal.model_validate(duplicate)

    underfilled = proposal.model_dump(mode="python")
    underfilled["candidates"] = underfilled["candidates"][:1]
    underfilled["presented_candidate_count"] = 1
    underfilled["omitted_candidate_count"] = 1
    with pytest.raises(ValidationError, match="PRESENTATION_UNDERFILLED"):
        routing.ProviderRoutingProposal.model_validate(underfilled)


def test_proposal_recomputes_strategy_ranking_from_full_evaluation() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(strategy=routing.ProviderRoutingStrategy.lowest_cost),
        [
            _observation("cheap", cost=0.01),
            _observation("expensive", cost=9.0),
        ],
    )
    payload = proposal.model_dump(mode="python")
    reversed_candidates = list(reversed(proposal.candidates))
    payload["candidates"] = [
        candidate.model_copy(update={"rank": index}).model_dump(mode="python")
        for index, candidate in enumerate(reversed_candidates, start=1)
    ]
    payload["proposal_ref"] = routing._proposal_ref(
        request_ref=proposal.request_ref,
        request_fingerprint_ref=proposal.request_fingerprint_ref,
        observation_set_fingerprint_ref=proposal.observation_set_fingerprint_ref,
        strategy=proposal.strategy,
        presented_candidate_refs=[
            candidate["candidate_ref"] for candidate in payload["candidates"]
        ],
        evaluated_candidate_refs=[
            candidate.candidate_ref for candidate in proposal.evaluated_candidates
        ],
        observed_candidate_count=proposal.observed_candidate_count,
        omitted_candidate_count=proposal.omitted_candidate_count,
        recommended_candidate_ref=proposal.recommended_candidate_ref,
        reason_codes=proposal.reason_codes,
        blocker_codes=proposal.blocker_codes,
        maximum_presented_candidates=proposal.maximum_presented_candidates,
        approval_queue_route_ref=proposal.approval_queue_route_ref,
        run_detail_group_ref=proposal.run_detail_group_ref,
        bounded_fanout_presentation_ref=proposal.bounded_fanout_presentation_ref,
        source_ref=proposal.source_ref,
        safe_summary=proposal.safe_summary,
    )

    with pytest.raises(ValidationError, match="PRESENTATION_SELECTION_DRIFT"):
        routing.ProviderRoutingProposal.model_validate(payload)


def test_recommended_provider_still_requires_fresh_request_authority() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("non-authorizing")],
    )
    candidate = proposal.candidates[0]

    assert proposal.recommended_candidate_ref == candidate.candidate_ref
    assert proposal.invocation_authorized is False
    assert proposal.fresh_local_approval_validation_required is True
    assert proposal.fresh_authority_lease_evaluation_required is True
    assert "PROVIDER_REQUEST_SCOPED_APPROVAL_REVALIDATION_REQUIRED" in (
        candidate.reason_codes
    )
    assert "PROVIDER_REQUEST_SCOPED_AUTHORITY_LEASE_REVALIDATION_REQUIRED" in (
        candidate.reason_codes
    )


def test_provider_routing_nested_availability_truth_is_immutable() -> None:
    proposal = build_provider_routing_proposal(
        ProviderRoutingNeed(),
        [_observation("deep-immutable")],
    )
    snapshot = proposal.observations[0].availability_snapshot

    with pytest.raises(ValidationError, match="frozen"):
        snapshot.authority_posture = AuthorityPosture.blocked  # type: ignore[misc]
    assert isinstance(snapshot.reason_codes, tuple)
    assert isinstance(snapshot.blocker_codes, tuple)
    assert isinstance(snapshot.evidence_refs, tuple)
    assert isinstance(snapshot.probe_refs, tuple)


@pytest.mark.parametrize(
    "unsafe_value",
    [
        "provider-ref:192.168.1.42",
        "provider-ref:localhost",
        "provider-ref:::1",
    ],
)
def test_provider_routing_rejects_network_identity_refs(unsafe_value: str) -> None:
    with pytest.raises(ValidationError, match="PROVIDER_ROUTING_NEED_REF_INVALID"):
        ProviderRoutingNeed(request_ref=unsafe_value)


@pytest.mark.parametrize("unsafe_label", ["192.168.1.42", "localhost", "::1"])
def test_provider_routing_rejects_network_identity_labels(
    unsafe_label: str,
) -> None:
    observation = _observation("network-identity-label")

    with pytest.raises(ValidationError, match="PROVIDER_ROUTING_OBSERVATION_UNSAFE"):
        observation.model_copy(update={"provider_label": unsafe_label})
