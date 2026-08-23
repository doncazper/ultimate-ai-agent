from __future__ import annotations

from pathlib import Path

import pytest

from scripts.verify_q29_governed_improvement import _prohibited_imports
from ultimate_ai_agent.core.ecosystem.improvements import (
    ImprovementConflict,
    ImprovementDecision,
    ImprovementError,
    ImprovementEvidenceKind,
    ImprovementEvidenceSource,
    ImprovementImplementationEvidence,
    ImprovementOutcomeRequest,
    ImprovementProposalRequest,
    ImprovementProposalState,
    ImprovementRegressionEvidence,
    ImprovementRegressionStatus,
    ImprovementReviewOutcome,
    ImprovementReviewReceipt,
    ImprovementReviewRequest,
    ImprovementRightsPosture,
    ImprovementSession,
    ImprovementTargetKind,
    ObservedImprovementOutcome,
    build_improvement_proposal,
    build_improvement_status,
)


def _source(
    *, rights: ImprovementRightsPosture = ImprovementRightsPosture.permitted
) -> ImprovementEvidenceSource:
    return ImprovementEvidenceSource(
        source_kind=ImprovementEvidenceKind.evaluation_gap,
        source_receipt_ref="evaluation-receipt-ref:q29:sample",
        source_revision_ref="revision-ref:q29:source:1",
        provenance_ref="provenance-ref:q29:sample",
        rights_posture=rights,
        rights_evidence_ref=(
            "rights-evidence-ref:q29:permitted"
            if rights == ImprovementRightsPosture.permitted
            else None
        ),
        evidence_refs=("evidence-ref:q29:regression-gap",),
    )


def _proposal_request(**overrides: object) -> ImprovementProposalRequest:
    values: dict[str, object] = {
        "workspace_ref": "workspace-ref:q29:local",
        "target_kind": ImprovementTargetKind.evaluation_case,
        "target_ref": "evaluation-case-ref:q29:target",
        "target_revision_ref": "revision-ref:q29:target:1",
        "source_evidence": (_source(),),
        "intended_delta_refs": ("delta-ref:q29:add-regression-case",),
        "expected_regression_refs": ("regression-ref:q29:focused",),
        "rollback_plan_ref": "rollback-plan-ref:q29:revert-change",
    }
    values.update(overrides)
    return ImprovementProposalRequest(**values)


def _review_request(
    proposal_request: ImprovementProposalRequest,
    **overrides: object,
) -> ImprovementReviewRequest:
    proposal = build_improvement_proposal(proposal_request)
    values: dict[str, object] = {
        "proposal": proposal_request,
        "proposal_ref": proposal.proposal_ref,
        "proposal_fingerprint_ref": proposal.proposal_fingerprint_ref,
        "decision": ImprovementDecision.accept,
        "reviewer_ref": "reviewer-ref:q29:human",
        "independent_reviewer_ref": "reviewer-ref:q29:independent-human",
        "independent_review_evidence_ref": "review-evidence-ref:q29:independent",
        "independent_review_verified": True,
        "idempotency_ref": "idempotency-ref:q29:review",
    }
    values.update(overrides)
    return ImprovementReviewRequest(**values)


def _implementation(
    review: ImprovementReviewReceipt, **overrides: object
) -> ImprovementImplementationEvidence:
    assert review.expected_change_review_scope_ref is not None
    values: dict[str, object] = {
        "change_receipt_ref": "change-receipt-ref:q29:implemented",
        "change_scope_ref": review.expected_change_review_scope_ref,
        "target_ref": review.target_ref,
        "base_revision_ref": review.target_revision_ref,
        "implemented_revision_ref": "revision-ref:q29:implemented:2",
        "verification_evidence_ref": "change-verification-ref:q29:implemented",
    }
    values.update(overrides)
    return ImprovementImplementationEvidence(**values)


def _regression(
    *,
    expected_ref: str = "regression-ref:q29:focused",
    evidence_ref: str = "regression-evidence-ref:q29:passed",
    status: ImprovementRegressionStatus = ImprovementRegressionStatus.passed,
) -> ImprovementRegressionEvidence:
    return ImprovementRegressionEvidence(
        expected_regression_ref=expected_ref,
        evidence_ref=evidence_ref,
        status=status,
    )


def _unsafe_ref(*fragments: str) -> str:
    return "".join(fragments)


def test_proposal_is_deterministic_review_only_and_reversible() -> None:
    request = _proposal_request()
    proposal = build_improvement_proposal(request)

    assert build_improvement_proposal(request) == proposal
    assert proposal.state == ImprovementProposalState.ready_for_human_review
    assert proposal.rollback_plan_ref == "rollback-plan-ref:q29:revert-change"
    assert proposal.target_mutated is False
    assert proposal.patch_created is False
    assert proposal.model_trained is False
    assert proposal.approval_granted is False
    assert proposal.proposal_promoted is False
    assert proposal.git_operation_performed is False
    assert proposal.external_write_performed is False


@pytest.mark.parametrize(
    "rights",
    [ImprovementRightsPosture.unknown, ImprovementRightsPosture.denied],
)
def test_unresolved_source_rights_block_review(
    rights: ImprovementRightsPosture,
) -> None:
    proposal = build_improvement_proposal(
        _proposal_request(source_evidence=(_source(rights=rights),))
    )
    assert proposal.state == ImprovementProposalState.blocked_rights


def test_permitted_rights_require_evidence() -> None:
    with pytest.raises(
        ValueError, match="IMPROVEMENT_PERMITTED_RIGHTS_EVIDENCE_REQUIRED"
    ):
        ImprovementEvidenceSource(
            source_kind=ImprovementEvidenceKind.operator_feedback,
            source_receipt_ref="feedback-receipt-ref:q29:sample",
            source_revision_ref="revision-ref:q29:feedback:1",
            provenance_ref="provenance-ref:q29:feedback",
            rights_posture=ImprovementRightsPosture.permitted,
            evidence_refs=("evidence-ref:q29:feedback",),
        )


def test_unsafe_source_ref_is_rejected_without_echoing_input() -> None:
    unsafe_ref = _unsafe_ref("htt", "ps:", "example", ".com")
    with pytest.raises(ValueError) as exc_info:
        ImprovementEvidenceSource(
            source_kind=ImprovementEvidenceKind.operator_feedback,
            source_receipt_ref=unsafe_ref,
            source_revision_ref="revision-ref:q29:feedback:1",
            provenance_ref="provenance-ref:q29:feedback",
            rights_posture=ImprovementRightsPosture.unknown,
            evidence_refs=("evidence-ref:q29:feedback",),
        )
    assert unsafe_ref not in str(exc_info.value)
    assert "IMPROVEMENT_SOURCE_RECEIPT_REF_SAFE_REF_REQUIRED" in str(exc_info.value)


def test_safe_disable_keeps_proposal_inert() -> None:
    proposal = build_improvement_proposal(_proposal_request(safe_disabled=True))
    assert proposal.state == ImprovementProposalState.blocked_safe_disabled


def test_missing_source_evidence_blocks_review() -> None:
    source = _source().model_copy(update={"evidence_refs": ()})
    proposal = build_improvement_proposal(_proposal_request(source_evidence=(source,)))
    assert proposal.state == ImprovementProposalState.blocked_missing_evidence


def test_tcb_proposal_requires_dedicated_adr_and_still_has_no_authority() -> None:
    proposal = build_improvement_proposal(
        _proposal_request(target_kind=ImprovementTargetKind.tcb_change)
    )
    assert proposal.dedicated_adr_required is True
    assert proposal.patch_created is False
    assert proposal.approval_granted is False


def test_acceptance_only_opens_a_separate_change_review() -> None:
    request = _proposal_request()
    receipt = ImprovementSession().review(_review_request(request))
    assert (
        receipt.outcome == ImprovementReviewOutcome.accepted_for_separate_change_review
    )
    assert receipt.expected_change_review_scope_ref is not None
    assert receipt.target_mutated is False
    assert receipt.patch_created is False
    assert receipt.approval_granted is False
    assert receipt.proposal_promoted is False


def test_blocked_proposal_cannot_be_accepted() -> None:
    request = _proposal_request(
        source_evidence=(_source(rights=ImprovementRightsPosture.unknown),)
    )
    receipt = ImprovementSession().review(_review_request(request))
    assert receipt.outcome == ImprovementReviewOutcome.blocked
    assert receipt.expected_change_review_scope_ref is None


def test_unverified_independent_review_cannot_be_accepted() -> None:
    request = _proposal_request()
    receipt = ImprovementSession().review(
        _review_request(request, independent_review_verified=False)
    )
    assert receipt.outcome == ImprovementReviewOutcome.blocked
    assert receipt.independent_review_verified is False
    assert receipt.expected_change_review_scope_ref is None


def test_reviewer_and_independent_reviewer_must_be_distinct() -> None:
    request = _proposal_request()
    with pytest.raises(
        ValueError, match="IMPROVEMENT_DISTINCT_INDEPENDENT_REVIEWER_REQUIRED"
    ):
        _review_request(
            request,
            independent_reviewer_ref="reviewer-ref:q29:human",
        )


def test_review_idempotency_is_stable_and_conflicts_on_changed_payload() -> None:
    request = _proposal_request()
    session = ImprovementSession()
    original = session.review(_review_request(request))
    replay = session.review(_review_request(request))
    assert replay.receipt_ref == original.receipt_ref
    assert replay.replayed is True

    with pytest.raises(
        ImprovementConflict, match="IMPROVEMENT_REVIEW_IDEMPOTENCY_CONFLICT"
    ):
        session.review(_review_request(request, decision=ImprovementDecision.reject))


def test_review_rejects_changed_proposal_binding() -> None:
    request = _proposal_request()
    with pytest.raises(
        ImprovementConflict, match="IMPROVEMENT_PROPOSAL_BINDING_CONFLICT"
    ):
        ImprovementSession().review(
            _review_request(request, proposal_ref="improvement-proposal-ref:wrong")
        )


def test_verified_outcome_is_bound_and_does_not_learn_automatically() -> None:
    request = _proposal_request()
    session = ImprovementSession()
    review = session.review(_review_request(request))
    outcome_request = ImprovementOutcomeRequest(
        proposal_ref=review.proposal_ref,
        proposal_fingerprint_ref=review.proposal_fingerprint_ref,
        accepted_review_receipt_ref=review.receipt_ref,
        implementation=_implementation(review),
        independent_reviewer_ref=review.independent_reviewer_ref,
        independent_review_evidence_ref=review.independent_review_evidence_ref,
        regression_results=(_regression(),),
        observed_outcome=ObservedImprovementOutcome.improved,
        idempotency_ref="idempotency-ref:q29:outcome",
    )
    receipt = session.record_outcome(outcome_request)
    replay = session.record_outcome(outcome_request)
    assert receipt.eligible_as_future_evidence is True
    assert receipt.automatic_learning_performed is False
    assert receipt.historical_fact_rewritten is False
    assert receipt.target_mutated is False
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True


def test_regressed_outcome_is_not_eligible_for_future_evidence() -> None:
    request = _proposal_request()
    session = ImprovementSession()
    review = session.review(_review_request(request))
    receipt = session.record_outcome(
        ImprovementOutcomeRequest(
            proposal_ref=review.proposal_ref,
            proposal_fingerprint_ref=review.proposal_fingerprint_ref,
            accepted_review_receipt_ref=review.receipt_ref,
            implementation=_implementation(
                review,
                change_receipt_ref="change-receipt-ref:q29:regressed",
                implemented_revision_ref="revision-ref:q29:implemented:3",
            ),
            independent_reviewer_ref=review.independent_reviewer_ref,
            independent_review_evidence_ref=review.independent_review_evidence_ref,
            regression_results=(
                _regression(
                    evidence_ref="regression-evidence-ref:q29:failed",
                    status=ImprovementRegressionStatus.failed,
                ),
            ),
            observed_outcome=ObservedImprovementOutcome.regressed,
            rollback_evidence_ref="rollback-evidence-ref:q29:verified",
            reverted=True,
            idempotency_ref="idempotency-ref:q29:regressed-outcome",
        )
    )
    assert receipt.eligible_as_future_evidence is False
    assert receipt.reverted is True
    assert receipt.automatic_learning_performed is False


def test_outcome_requires_an_accepted_review_binding() -> None:
    request = _proposal_request()
    proposal = build_improvement_proposal(request)
    implementation = ImprovementImplementationEvidence(
        change_receipt_ref="change-receipt-ref:q29:missing",
        change_scope_ref=proposal.expected_change_review_scope_ref,
        target_ref=proposal.target_ref,
        base_revision_ref=proposal.target_revision_ref,
        implemented_revision_ref="revision-ref:q29:implemented:2",
        verification_evidence_ref="change-verification-ref:q29:missing",
    )
    with pytest.raises(
        ImprovementConflict, match="IMPROVEMENT_OUTCOME_REVIEW_BINDING_CONFLICT"
    ):
        ImprovementSession().record_outcome(
            ImprovementOutcomeRequest(
                proposal_ref=proposal.proposal_ref,
                proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
                accepted_review_receipt_ref="review-receipt-ref:q29:missing",
                implementation=implementation,
                independent_reviewer_ref="reviewer-ref:q29:independent-human",
                independent_review_evidence_ref=("review-evidence-ref:q29:independent"),
                regression_results=(_regression(),),
                observed_outcome=ObservedImprovementOutcome.improved,
                idempotency_ref="idempotency-ref:q29:missing-review",
            )
        )


def test_regression_requires_revert_and_rollback_evidence() -> None:
    implementation = ImprovementImplementationEvidence(
        change_receipt_ref="change-receipt-ref:q29:implemented",
        change_scope_ref="approval-scope-ref:q29:change-review",
        target_ref="evaluation-case-ref:q29:target",
        base_revision_ref="revision-ref:q29:target:1",
        implemented_revision_ref="revision-ref:q29:implemented:2",
        verification_evidence_ref="change-verification-ref:q29:implemented",
    )
    with pytest.raises(
        ValueError, match="IMPROVEMENT_REGRESSION_ROLLBACK_EVIDENCE_REQUIRED"
    ):
        ImprovementOutcomeRequest(
            proposal_ref="improvement-proposal-ref:q29:sample",
            proposal_fingerprint_ref="improvement-fingerprint-ref:q29:sample",
            accepted_review_receipt_ref="review-receipt-ref:q29:accepted",
            implementation=implementation,
            independent_reviewer_ref="reviewer-ref:q29:independent-human",
            independent_review_evidence_ref="review-evidence-ref:q29:independent",
            regression_results=(
                _regression(
                    evidence_ref="regression-evidence-ref:q29:failed",
                    status=ImprovementRegressionStatus.failed,
                ),
            ),
            observed_outcome=ObservedImprovementOutcome.regressed,
            idempotency_ref="idempotency-ref:q29:regressed",
        )


def test_outcome_requires_exact_implementation_scope_binding() -> None:
    request = _proposal_request()
    session = ImprovementSession()
    review = session.review(_review_request(request))
    with pytest.raises(
        ImprovementConflict, match="IMPROVEMENT_OUTCOME_REVIEW_BINDING_CONFLICT"
    ):
        session.record_outcome(
            ImprovementOutcomeRequest(
                proposal_ref=review.proposal_ref,
                proposal_fingerprint_ref=review.proposal_fingerprint_ref,
                accepted_review_receipt_ref=review.receipt_ref,
                implementation=_implementation(
                    review, change_scope_ref="approval-scope-ref:q29:unrelated"
                ),
                independent_reviewer_ref=review.independent_reviewer_ref,
                independent_review_evidence_ref=(
                    review.independent_review_evidence_ref
                ),
                regression_results=(_regression(),),
                observed_outcome=ObservedImprovementOutcome.improved,
                idempotency_ref="idempotency-ref:q29:wrong-implementation",
            )
        )


def test_outcome_requires_every_planned_regression_result() -> None:
    request = _proposal_request(
        expected_regression_refs=(
            "regression-ref:q29:focused",
            "regression-ref:q29:secondary",
        )
    )
    session = ImprovementSession()
    review = session.review(_review_request(request))
    with pytest.raises(
        ImprovementConflict,
        match="IMPROVEMENT_REGRESSION_EXPECTATION_BINDING_CONFLICT",
    ):
        session.record_outcome(
            ImprovementOutcomeRequest(
                proposal_ref=review.proposal_ref,
                proposal_fingerprint_ref=review.proposal_fingerprint_ref,
                accepted_review_receipt_ref=review.receipt_ref,
                implementation=_implementation(review),
                independent_reviewer_ref=review.independent_reviewer_ref,
                independent_review_evidence_ref=(
                    review.independent_review_evidence_ref
                ),
                regression_results=(_regression(),),
                observed_outcome=ObservedImprovementOutcome.improved,
                idempotency_ref="idempotency-ref:q29:missing-regression",
            )
        )


def test_session_capacity_fails_closed_without_eviction() -> None:
    request = _proposal_request()
    session = ImprovementSession(max_receipts=1)
    original = session.review(_review_request(request))
    with pytest.raises(ImprovementError, match="IMPROVEMENT_SESSION_CAPACITY_REACHED"):
        session.review(
            _review_request(
                request,
                idempotency_ref="idempotency-ref:q29:second-review",
                decision=ImprovementDecision.reject,
            )
        )
    assert session.review(_review_request(request)).receipt_ref == original.receipt_ref


def test_status_keeps_all_automatic_authority_disabled() -> None:
    status = build_improvement_status()
    assert status["source_specific_rights_required"] is True
    assert status["independent_review_required"] is True
    assert status["self_modifying_code_enabled"] is False
    assert status["automatic_training_enabled"] is False
    assert status["automatic_promotion_enabled"] is False
    assert status["automatic_git_publication_enabled"] is False
    assert status["automatic_merge_enabled"] is False


def test_verifier_detects_prohibited_from_imports(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "from urllib import request\nfrom http import client\n",
        encoding="utf-8",
    )
    assert _prohibited_imports(candidate) == {"urllib.request", "http.client"}
