from __future__ import annotations

from pathlib import Path

import pytest

import scripts.verify_fcc_health_001_self_healing_recommendations_to_inbox as verifier
from ultimate_ai_agent.core.control_center.health_recommendations import (
    FCC_HEALTH_RECOMMENDATION_ACTION_KIND,
    FCC_HEALTH_RECOMMENDATION_BLOCKED_AUTHORITY_REFS,
    FCC_HEALTH_RECOMMENDATION_CONTRACT_REF,
    RecommendationCandidate,
    build_fcc_health_recommendations,
    build_recommendation_candidate,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_health_001_verifier_passes_current_repo() -> None:
    assert FCC_HEALTH_RECOMMENDATION_ACTION_KIND == "self_heal_recommendation"
    assert verifier.validate_fcc_health_001_self_healing_recommendations_to_inbox() == []


def test_recommendation_candidate_denies_authority_flags() -> None:
    candidate = build_recommendation_candidate(
        kind="documentation_currentness_drift",
        severity="low",
        safe_title="Review documentation currentness refs",
        safe_summary="Review safe documentation refs before changing active path copy.",
        source_signal_refs=["signal-ref:documentation-integrity:currentness-review"],
        source_surface_refs=["surface-ref:evidence"],
        source_doc_refs=["docs/README.md"],
        source_route_refs=[],
        source_test_refs=[],
        source_verifier_refs=["scripts/verify_documentation_integrity.py"],
        evidence_refs=["evidence-ref:fcc-health-001:docs-currentness"],
        missing_proof_refs=["missing-proof-ref:fcc-health-001:human-review"],
        owner_ref="owner-ref:docs-discipline",
        scope_ref="scope-ref:fcc-health-001:docs",
        impact_ref="impact-ref:portfolio-truth",
        validation_plan_refs=["validation-plan-ref:verify-documentation-integrity"],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action="Review refs before creating any scoped docs task.",
    )
    payload = candidate.model_dump(mode="json")
    payload["auto_apply_authorized"] = True

    with pytest.raises(ValueError, match="FCC_HEALTH_RECOMMENDATION_AUTHORITY_DENIED"):
        RecommendationCandidate(**payload)


def test_recommendation_candidate_denies_unsafe_human_text() -> None:
    candidate = build_recommendation_candidate(
        kind="documentation_currentness_drift",
        severity="low",
        safe_title="Review documentation currentness refs",
        safe_summary="Review safe documentation refs before changing active path copy.",
        source_signal_refs=["signal-ref:documentation-integrity:currentness-review"],
        source_surface_refs=["surface-ref:evidence"],
        source_doc_refs=["docs/README.md"],
        source_route_refs=[],
        source_test_refs=[],
        source_verifier_refs=["scripts/verify_documentation_integrity.py"],
        evidence_refs=["evidence-ref:fcc-health-001:docs-currentness"],
        missing_proof_refs=["missing-proof-ref:fcc-health-001:human-review"],
        owner_ref="owner-ref:docs-discipline",
        scope_ref="scope-ref:fcc-health-001:docs",
        impact_ref="impact-ref:portfolio-truth",
        validation_plan_refs=["validation-plan-ref:verify-documentation-integrity"],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action="Review refs before creating any scoped docs task.",
    )

    synthetic_absolute_path = "/" + "Users" + "/redacted/example.txt"
    unsafe_prompt_phrase = "raw " + "prompt material"
    unsafe_response_phrase = "raw " + "response content"
    for field_name, unsafe_value in {
        "safe_summary": f"Contains {unsafe_prompt_phrase} from a private session.",
        "safe_title": f"Review {synthetic_absolute_path}",
        "next_safe_action": f"Paste {unsafe_response_phrase} into the task.",
    }.items():
        payload = candidate.model_dump(mode="json")
        payload[field_name] = unsafe_value
        with pytest.raises(
            ValueError,
            match="FCC_HEALTH_RECOMMENDATION_UNSAFE_HUMAN_TEXT_REJECTED",
        ):
            RecommendationCandidate(**payload)


def test_recommendation_candidate_bounds_summary_and_evidence_refs() -> None:
    candidate = build_recommendation_candidate(
        kind="documentation_currentness_drift",
        severity="low",
        safe_title="Review documentation currentness refs",
        safe_summary="Review safe documentation refs before changing active path copy.",
        source_signal_refs=["signal-ref:documentation-integrity:currentness-review"],
        source_surface_refs=["surface-ref:evidence"],
        source_doc_refs=["docs/README.md"],
        source_route_refs=[],
        source_test_refs=[],
        source_verifier_refs=["scripts/verify_documentation_integrity.py"],
        evidence_refs=["evidence-ref:fcc-health-001:docs-currentness"],
        missing_proof_refs=["missing-proof-ref:fcc-health-001:human-review"],
        owner_ref="owner-ref:docs-discipline",
        scope_ref="scope-ref:fcc-health-001:docs",
        impact_ref="impact-ref:portfolio-truth",
        validation_plan_refs=["validation-plan-ref:verify-documentation-integrity"],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action="Review refs before creating any scoped docs task.",
    )

    long_summary = "x" * 361
    payload = candidate.model_dump(mode="json")
    payload["safe_summary"] = long_summary
    with pytest.raises(ValueError):
        RecommendationCandidate(**payload)

    payload = candidate.model_dump(mode="json")
    payload["evidence_refs"] = ["evidence-ref:fcc-health-001/raw-private-path"]
    with pytest.raises(
        ValueError,
        match="FCC_HEALTH_RECOMMENDATION_UNSAFE_EVIDENCE_REF_REJECTED",
    ):
        RecommendationCandidate(**payload)


def test_health_recommendations_are_safe_ref_review_candidates(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    recommendations = build_fcc_health_recommendations(
        source_readiness=repo.source_readiness()
    )

    assert {candidate.kind for candidate in recommendations} >= {
        "source_readiness_gap",
        "documentation_currentness_drift",
        "operational_maturity_gap",
    }
    for candidate in recommendations:
        payload = candidate.model_dump(mode="json")
        assert payload["contract_ref"] == FCC_HEALTH_RECOMMENDATION_CONTRACT_REF
        assert payload["redaction_status"] == "safe_refs_only"
        assert payload["lifecycle_state"] == "queued_for_review"
        assert payload["auto_code_authorized"] is False
        assert payload["auto_apply_authorized"] is False
        assert payload["provider_model_call_authorized"] is False
        assert payload["shell_execution_authorized"] is False
        assert payload["connector_write_authorized"] is False
        assert payload["task_execution_authorized"] is False
        assert payload["production_authority_enabled"] is False
        assert set(FCC_HEALTH_RECOMMENDATION_BLOCKED_AUTHORITY_REFS).issubset(
            set(payload["blocked_authority_refs"])
        )


def test_health_recommendations_project_into_action_inbox_without_execution(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    action_inbox = repo.actions_inbox()
    health_items = [
        item
        for item in action_inbox["items"]
        if item.get("action_kind") == FCC_HEALTH_RECOMMENDATION_ACTION_KIND
    ]

    assert health_items
    assert action_inbox["action_groups"]
    for item in health_items:
        assert item["status"] == "proposed"
        assert item["surface"] == "Actions"
        assert item["approval_required"] is False
        assert item["side_effect_class"] == "local_dev_workspace_only"
        assert item["action_group_id"] == "proposal_only_no_execution_path"
        assert item["approval_envelope_status"] == (
            "not_required_recommendation_review_only"
        )
        assert item["state_change_readiness"] == (
            "recommendation_review_only_no_execution_path"
        )
        assert item["health_recommendation_ref"].startswith(
            "recommendation:fcc-health-001:"
        )
        assert item["health_recommendation_auto_apply_authorized"] is False
        assert item["health_recommendation_auto_code_authorized"] is False
        assert item["health_recommendation_provider_model_call_authorized"] is False
        assert item["health_recommendation_shell_execution_authorized"] is False
        assert item["health_recommendation_connector_write_authorized"] is False
        assert item["health_recommendation_action_execution_authorized"] is False
        assert item["health_recommendation_production_authority_enabled"] is False
        assert "blocked-state:no-auto-apply" in item[
            "health_recommendation_blocked_authority_refs"
        ]
