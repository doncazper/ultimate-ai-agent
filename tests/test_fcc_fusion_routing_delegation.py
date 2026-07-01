from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.fusion_routing import (
    FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
    FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS,
    CacheContextEconomics,
    DelegationProposalEnvelope,
    DogfoodOutcome,
    RerouteReason,
    RouteDecisionVisibility,
    WorkClassification,
    WorkClassificationValue,
    build_cache_context_economics,
    build_delegation_proposal,
    build_dogfood_record,
    build_fusion_routing_delegation_read_model,
    build_route_visibility_from_decision,
    build_work_classification,
    forbidden_fusion_claims,
)
from ultimate_ai_agent.core.model_router.decisions import ModelRouteDecision
from ultimate_ai_agent.core.model_router.enums import ModelRouteStatus
from ultimate_ai_agent.core.storage import FounderLoopRepository


@pytest.mark.parametrize("value", list(WorkClassificationValue))
def test_work_classification_values_are_review_aids_only(
    value: WorkClassificationValue,
) -> None:
    classification = build_work_classification(
        value,
        suffix_ref=f"classification:{value.value}",
        source_ref=f"source-ref:fusion:{value.value}",
        evidence_ref=f"evidence-ref:fusion:{value.value}",
    )

    assert classification.classification == value.value
    assert classification.review_aid_only is True
    assert classification.execution_authorized is False
    assert classification.action_execution_enabled is False
    if value in {
        WorkClassificationValue.judgment_required,
        WorkClassificationValue.ambiguous,
        WorkClassificationValue.blocked,
    }:
        assert classification.human_review_required is True
    if value == WorkClassificationValue.blocked:
        assert classification.blocked_authority_refs


def test_work_classification_fails_closed_for_unsafe_posture() -> None:
    with pytest.raises(ValueError):
        build_work_classification(
            "unsupported",
            suffix_ref="classification:bad",
            source_ref="source-ref:fusion:bad",
            evidence_ref="evidence-ref:fusion:bad",
        )

    payload = build_work_classification(
        WorkClassificationValue.ambiguous,
        suffix_ref="classification:ambiguous",
        source_ref="source-ref:fusion:ambiguous",
        evidence_ref="evidence-ref:fusion:ambiguous",
    ).model_dump(mode="json")
    payload["human_review_required"] = False
    with pytest.raises(ValidationError):
        WorkClassification(**payload)

    blocked_payload = build_work_classification(
        WorkClassificationValue.blocked,
        suffix_ref="classification:blocked",
        source_ref="source-ref:fusion:blocked",
        evidence_ref="evidence-ref:fusion:blocked",
    ).model_dump(mode="json")
    blocked_payload["blocked_authority_refs"] = []
    with pytest.raises(ValidationError):
        WorkClassification(**blocked_payload)


def test_delegation_proposal_is_future_only_and_non_executing() -> None:
    mechanical = build_work_classification(
        WorkClassificationValue.mechanical,
        suffix_ref="delegation:mechanical",
        source_ref="source-ref:fusion:mechanical",
        evidence_ref="evidence-ref:fusion:mechanical",
    )
    proposal = build_delegation_proposal(
        work_classification=mechanical,
        suffix_ref="delegation:mechanical",
    )

    assert proposal.proposal_state == "proposed"
    assert proposal.proposed_delegate_kind == "mechanical_worker"
    assert proposal.future_only is True
    assert proposal.creates_approval_ref is False
    assert proposal.creates_execution_ref is False
    assert proposal.worker_execution_enabled is False
    assert proposal.background_dispatch_enabled is False

    unsafe = proposal.model_dump(mode="json")
    unsafe["worker_execution_enabled"] = True
    with pytest.raises(ValidationError):
        DelegationProposalEnvelope(**unsafe)


def test_judgment_or_ambiguous_work_cannot_be_delegate_ready() -> None:
    judgment = build_work_classification(
        WorkClassificationValue.judgment_required,
        suffix_ref="delegation:judgment",
        source_ref="source-ref:fusion:judgment",
        evidence_ref="evidence-ref:fusion:judgment",
    )
    payload = build_delegation_proposal(
        work_classification=judgment,
        suffix_ref="delegation:judgment",
    ).model_dump(mode="json")
    payload["proposal_state"] = "proposed"
    payload["proposed_delegate_kind"] = "mechanical_worker"
    payload["delegated_work_refs"] = ["delegated-work-ref:fusion:judgment"]

    with pytest.raises(ValidationError):
        DelegationProposalEnvelope(**payload)


@pytest.mark.parametrize(
    ("status", "reason_codes", "expected_status", "expected_context"),
    [
        (
            ModelRouteStatus.selected,
            ["SELECTED_PROFILE"],
            "selected",
            "context-posture:preview-only",
        ),
        (
            ModelRouteStatus.privacy_blocked,
            ["CLOUD_BLOCKED_BY_PRIVACY_MODE"],
            "blocked",
            "context-posture:preview-only",
        ),
        (
            ModelRouteStatus.approval_required,
            ["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"],
            "blocked",
            "context-posture:preview-only",
        ),
        (
            ModelRouteStatus.context_too_small,
            ["CONTEXT_TOO_SMALL"],
            "blocked",
            "context-posture:blocked",
        ),
        (
            ModelRouteStatus.denied,
            ["PROFILE_DISABLED"],
            "rejected",
            "context-posture:preview-only",
        ),
    ],
)
def test_route_decision_visibility_is_readable_without_model_invocation(
    status: ModelRouteStatus,
    reason_codes: list[str],
    expected_status: str,
    expected_context: str,
) -> None:
    decision = ModelRouteDecision(
        request_id="route-request:fusion:test",
        run_id="run:fusion:test",
        status=status,
        selected_profile_id="local-preview" if status == ModelRouteStatus.selected else None,
        rejected_profile_ids=["cloud-paid"] if status != ModelRouteStatus.selected else [],
        reason_codes=reason_codes,
        safe_message="Route preview only. No model execution was performed.",
        required_approval=status == ModelRouteStatus.approval_required,
    )

    visibility = build_route_visibility_from_decision(decision)

    assert visibility.status == expected_status
    assert visibility.context_posture_ref == expected_context
    assert visibility.no_execution_performed is True
    assert visibility.model_invocation_performed is False
    assert visibility.provider_call_performed is False
    assert reason_codes[0] in visibility.reason_codes


def test_route_visibility_rejects_execution_claims() -> None:
    visibility = RouteDecisionVisibility(
        status="blocked",
        reason_codes=["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"],
        operator_summary="Cost is blocked for preview only.",
    )
    payload = visibility.model_dump(mode="json")
    payload["provider_call_performed"] = True

    with pytest.raises(ValidationError):
        RouteDecisionVisibility(**payload)


def test_cache_context_economics_are_posture_only() -> None:
    economics = build_cache_context_economics(
        suffix_ref="cache-context:test",
        reroute_reason=RerouteReason.cost_blocked,
        cache_miss_expected=True,
        blocker_refs=["blocked-state:fusion-unknown-paid-cost"],
    )

    assert economics.explanatory_posture_only is True
    assert economics.runtime_model_switch_performed is False
    assert economics.reroute_reason == "cost_blocked"

    payload = economics.model_dump(mode="json")
    payload["runtime_model_switch_performed"] = True
    with pytest.raises(ValidationError):
        CacheContextEconomics(**payload)

    payload = economics.model_dump(mode="json")
    payload["measured_provider_event"] = True
    payload["evidence_refs"] = []
    with pytest.raises(ValidationError):
        CacheContextEconomics(**payload)


def test_private_dogfood_evidence_uses_safe_refs_only() -> None:
    record = build_dogfood_record(
        suffix_ref="dogfood:fusion",
        outcome=DogfoodOutcome.partially_useful,
    )

    assert record.local_private_only is True
    assert record.external_analytics_enabled is False
    assert record.live_learning_claimed is False

    payload = record.model_dump(mode="json")
    payload["redacted_summary_ref"] = "summary-ref:/Users/raw/path"
    with pytest.raises(ValidationError):
        type(record)(**payload)


def test_fusion_read_model_and_founder_loop_bindings(tmp_path: Path) -> None:
    read_model = build_fusion_routing_delegation_read_model()
    payload = read_model.model_dump(mode="json")

    assert payload["contract_ref"] == FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    assert payload["backend_owned"] is True
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_included"] is False
    assert set(FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["action_execution_enabled"] is False
    assert payload["sidekick_execution_enabled"] is False
    assert payload["provider_model_call_enabled"] is False

    repo = FounderLoopRepository(tmp_path / "founder-loop")
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["fusion_routing_delegation_contract_ref"] == (
        FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    )
    assert today["fusion_routing_delegation_read_model"]["backend_owned"] is True
    assert today["governed_code_workbench_work_classification"][
        "classification"
    ] == "validation"
    assert today["governed_code_workbench_delegation_proposal"][
        "proposal_state"
    ] == "proposed"
    assert today["plans_to_actions_bridge_read_model"]["items"][0][
        "work_classification"
    ]["classification"] == "judgment_required"
    assert today["plans_to_actions_bridge_read_model"]["items"][0][
        "delegation_proposal"
    ]["proposal_state"] == "deferred"

    action = inbox["items"][0]
    assert action["work_classification"]["classification"] in {
        "mechanical",
        "blocked",
        "judgment_required",
    }
    assert action["delegation_proposal"]["future_only"] is True
    assert action["cache_context_economics"]["runtime_model_switch_performed"] is False

    timeline_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "fusion_routing_delegation_read_model_ref"
    )
    assert timeline_item["raw_evidence_included"] is False
    assert timeline_item["approval_ref_authority"] is False
    assert timeline_item["rollback_execution_enabled"] is False
    assert FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF in timeline_item["status_refs"]


def test_fusion_product_language_guard_catches_bad_claims() -> None:
    findings = forbidden_fusion_claims(
        "Sidekick execution implemented and cache-aware runtime routing active."
    )

    assert "sidekick execution implemented" in findings
    assert "cache-aware runtime routing active" in findings
