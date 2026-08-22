from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import (
    CONTROL_CENTER_VALIDATION_ONLY_PATHS,
    route_side_effect_class,
)
from ultimate_ai_agent.core.ecosystem.changesets import FieldChangeKind, FieldDiff
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId, EntityKind
from ultimate_ai_agent.core.ecosystem.corrections import (
    AUTOCORRECT_MIN_REVIEW_CONFIDENCE,
    AutocorrectConflict,
    AutocorrectError,
    CorrectionDecision,
    CorrectionProposalRequest,
    CorrectionProposalState,
    CorrectionReviewOutcome,
    CorrectionReviewRequest,
    CorrectionReviewSession,
    build_autocorrect_control_status,
    build_correction_proposal,
)


def _diff(*, after: str = "fingerprint-ref:after") -> FieldDiff:
    return FieldDiff(
        operation_ref="operation-ref:correct-title",
        target_ref="task-ref:sample",
        field_ref="field-ref:title",
        change_kind=FieldChangeKind.updated,
        before_fingerprint_ref="fingerprint-ref:before",
        after_fingerprint_ref=after,
    )


def _proposal_request(**overrides: object) -> CorrectionProposalRequest:
    values: dict[str, object] = {
        "workspace_ref": "workspace-ref:local",
        "source_proposal_ref": "proposal-ref:eco010:sample",
        "target_kind": EntityKind.task,
        "target_owner": CanonicalOwnerId.tasks,
        "target_ref": "task-ref:sample",
        "expected_revision_ref": "revision-ref:task:7",
        "current_revision_ref": "revision-ref:task:7",
        "confidence_percent": 88,
        "field_diffs": (_diff(),),
        "evidence_refs": ("evidence-ref:source:sample",),
        "reason_refs": ("reason-ref:operator-correction",),
        "rejection_history_refs": (),
    }
    values.update(overrides)
    return CorrectionProposalRequest(**values)


def _unsafe_ref(*fragments: str) -> str:
    """Build unsafe test inputs without persisting sensitive-looking literals."""

    return "".join(fragments)


def _review_request(
    proposal_request: CorrectionProposalRequest,
    *,
    decision: CorrectionDecision = CorrectionDecision.accept,
    idempotency_ref: str = "idempotency-ref:correction:sample",
    superseding_proposal_ref: str | None = None,
) -> CorrectionReviewRequest:
    proposal = build_correction_proposal(proposal_request)
    return CorrectionReviewRequest(
        proposal=proposal_request,
        proposal_ref=proposal.proposal_ref,
        proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
        decision=decision,
        reviewer_ref="reviewer-ref:local-operator",
        idempotency_ref=idempotency_ref,
        superseding_proposal_ref=superseding_proposal_ref,
    )


def test_status_is_proposal_only_and_names_exact_supported_targets() -> None:
    status = build_autocorrect_control_status()

    assert status.status == "implemented_proposal_only"
    assert status.minimum_review_confidence == AUTOCORRECT_MIN_REVIEW_CONFIDENCE
    assert status.process_local_review_capacity == 256
    assert status.supported_target_kinds == (
        EntityKind.task,
        EntityKind.task_occurrence,
        EntityKind.board,
        EntityKind.board_template,
        EntityKind.calendar_set,
    )
    assert status.exact_revision_required is True
    assert status.idempotency_conflicts_fail_closed is True
    assert status.canonical_mutation_enabled is False
    assert status.changeset_creation_enabled is False
    assert status.rollback_execution_enabled is False


def test_ready_proposal_has_exact_content_free_diff_and_rollback_plan() -> None:
    proposal = build_correction_proposal(_proposal_request())

    assert proposal.state == CorrectionProposalState.ready_for_review
    assert proposal.confidence.value == "high"
    assert proposal.comparison.exact_revision_match is True
    assert proposal.comparison.changed_field_count == 1
    assert proposal.comparison.raw_values_included is False
    assert proposal.comparison.field_diffs[0].raw_value_included is False
    assert proposal.rollback.rollback_ready is True
    assert proposal.rollback.rollback_execution_available is False
    assert proposal.expected_changeset_plan_ref.startswith("changeset-plan-ref:sha256:")
    assert proposal.expected_approval_scope_ref.startswith("approval-scope-ref:sha256:")
    assert proposal.canonical_state_mutated is False
    assert proposal.changeset_created is False
    assert proposal.approval_granted is False


def test_proposal_refs_bind_all_material_review_fields() -> None:
    original = build_correction_proposal(_proposal_request())
    changed = build_correction_proposal(
        _proposal_request(
            field_diffs=(_diff(after="fingerprint-ref:different"),),
            rejection_history_refs=("learning-ref:prior-rejection",),
        )
    )

    assert changed.proposal_ref != original.proposal_ref
    assert changed.proposal_fingerprint_ref != original.proposal_fingerprint_ref
    assert changed.review_packet_ref != original.review_packet_ref
    assert changed.expected_changeset_plan_ref != original.expected_changeset_plan_ref
    assert changed.rollback.rollback_plan_ref != original.rollback.rollback_plan_ref


@pytest.mark.parametrize(
    ("overrides", "expected_state"),
    [
        (
            {"current_revision_ref": "revision-ref:task:8"},
            CorrectionProposalState.stale,
        ),
        (
            {"confidence_percent": AUTOCORRECT_MIN_REVIEW_CONFIDENCE - 1},
            CorrectionProposalState.blocked_low_confidence,
        ),
        (
            {"safe_disabled": True},
            CorrectionProposalState.blocked_safe_disabled,
        ),
    ],
)
def test_proposal_fails_closed_before_review(
    overrides: dict[str, object], expected_state: CorrectionProposalState
) -> None:
    proposal = build_correction_proposal(_proposal_request(**overrides))

    assert proposal.state == expected_state
    assert proposal.rollback.rollback_ready is False
    assert proposal.canonical_state_mutated is False


def test_target_owner_and_diff_target_are_exactly_bound() -> None:
    with pytest.raises(ValueError, match="AUTOCORRECT_CANONICAL_OWNER_BINDING_INVALID"):
        _proposal_request(target_owner=CanonicalOwnerId.calendar)

    with pytest.raises(ValueError, match="AUTOCORRECT_DIFF_TARGET_BINDING_INVALID"):
        _proposal_request(
            field_diffs=(
                FieldDiff(
                    operation_ref="operation-ref:wrong-target",
                    target_ref="task-ref:other",
                    field_ref="field-ref:title",
                    change_kind=FieldChangeKind.updated,
                    before_fingerprint_ref="fingerprint-ref:before",
                    after_fingerprint_ref="fingerprint-ref:after",
                ),
            )
        )

    with pytest.raises(ValueError, match="AUTOCORRECT_TARGET_KIND_NOT_SUPPORTED"):
        _proposal_request(
            target_kind=EntityKind.person,
            target_owner=CanonicalOwnerId.identity,
        )


@pytest.mark.parametrize(
    "unsafe_ref",
    [
        _unsafe_ref("htt", "ps:", "example", ".com"),
        _unsafe_ref("fi", "le:", "Users:", "op", "erator:item"),
        _unsafe_ref("workspace-ref:host", ".local"),
        _unsafe_ref("workspace-ref:127", ".0.0.1"),
        _unsafe_ref("workspace-ref:2001", ":db8::1"),
        _unsafe_ref(
            "workspace-ref:secret:",
            "gh",
            "p_",
            "abcdefghijkl",
            "mnopqrstuvwxyz123456",
        ),
    ],
)
def test_unsafe_refs_are_rejected_without_echoing_input(unsafe_ref: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        _proposal_request(workspace_ref=unsafe_ref)

    assert unsafe_ref not in str(exc_info.value)
    assert "AUTOCORRECT_WORKSPACE_REF_SAFE_REF_REQUIRED" in str(exc_info.value)


def test_nested_diff_refs_use_the_same_safe_ref_boundary() -> None:
    unsafe_ref = _unsafe_ref("field-ref:host", ".example", ".com")

    with pytest.raises(ValueError) as exc_info:
        _proposal_request(
            field_diffs=(
                FieldDiff(
                    operation_ref="operation-ref:correct-title",
                    target_ref="task-ref:sample",
                    field_ref=unsafe_ref,
                    change_kind=FieldChangeKind.updated,
                    before_fingerprint_ref="fingerprint-ref:before",
                    after_fingerprint_ref="fingerprint-ref:after",
                ),
            )
        )

    assert unsafe_ref not in str(exc_info.value)
    assert "AUTOCORRECT_DIFF_FIELD_REF_SAFE_REF_REQUIRED" in str(exc_info.value)


@pytest.mark.parametrize(
    "diff",
    [
        FieldDiff(
            operation_ref="operation-ref:add-title",
            target_ref="task-ref:sample",
            field_ref="field-ref:title",
            change_kind=FieldChangeKind.added,
            after_fingerprint_ref="fingerprint-ref:after",
        ),
        FieldDiff(
            operation_ref="operation-ref:remove-title",
            target_ref="task-ref:sample",
            field_ref="field-ref:title",
            change_kind=FieldChangeKind.removed,
            before_fingerprint_ref="fingerprint-ref:before",
        ),
    ],
)
def test_added_and_removed_content_free_diffs_remain_supported(diff: FieldDiff) -> None:
    proposal = build_correction_proposal(_proposal_request(field_diffs=(diff,)))

    assert proposal.state == CorrectionProposalState.ready_for_review
    assert proposal.comparison.field_diffs == (diff,)


def test_accept_review_is_idempotent_and_never_applies_the_changeset() -> None:
    session = CorrectionReviewSession()
    request = _review_request(_proposal_request())

    first = session.review(request)
    replay = session.review(request)

    assert first.outcome == CorrectionReviewOutcome.accepted_for_changeset_review
    assert first.expected_changeset_plan_ref is not None
    assert first.expected_approval_scope_ref is not None
    assert first.canonical_state_mutated is False
    assert first.changeset_created is False
    assert first.approval_granted is False
    assert first.rollback_executed is False
    assert first.replayed is False
    assert replay.receipt_ref == first.receipt_ref
    assert replay.replayed is True


def test_same_idempotency_ref_with_changed_payload_fails_closed() -> None:
    session = CorrectionReviewSession()
    first_request = _proposal_request()
    session.review(_review_request(first_request))
    changed_request = _proposal_request(confidence_percent=89)

    with pytest.raises(
        AutocorrectConflict,
        match="AUTOCORRECT_IDEMPOTENCY_PAYLOAD_CONFLICT",
    ):
        session.review(_review_request(changed_request))


def test_process_local_replay_registry_fails_closed_at_capacity() -> None:
    session = CorrectionReviewSession(max_receipts=1)
    first = _review_request(
        _proposal_request(),
        idempotency_ref="idempotency-ref:correction:first",
    )
    session.review(first)

    assert session.review(first).replayed is True
    with pytest.raises(
        AutocorrectError,
        match="AUTOCORRECT_REVIEW_SESSION_CAPACITY_REACHED",
    ):
        session.review(
            _review_request(
                _proposal_request(confidence_percent=89),
                idempotency_ref="idempotency-ref:correction:second",
            )
        )


def test_stale_review_cannot_be_accepted() -> None:
    proposal_request = _proposal_request(current_revision_ref="revision-ref:task:8")
    receipt = CorrectionReviewSession().review(_review_request(proposal_request))

    assert receipt.outcome == CorrectionReviewOutcome.stale
    assert receipt.expected_changeset_plan_ref is None
    assert receipt.expected_approval_scope_ref is None
    assert receipt.canonical_state_mutated is False


def test_reject_and_supersede_emit_content_free_learning_refs() -> None:
    proposal_request = _proposal_request()
    rejected = CorrectionReviewSession().review(
        _review_request(
            proposal_request,
            decision=CorrectionDecision.reject,
            idempotency_ref="idempotency-ref:correction:reject",
        )
    )
    superseded = CorrectionReviewSession().review(
        _review_request(
            proposal_request,
            decision=CorrectionDecision.supersede,
            idempotency_ref="idempotency-ref:correction:supersede",
            superseding_proposal_ref="correction-proposal-ref:replacement",
        )
    )

    assert rejected.outcome == CorrectionReviewOutcome.rejected
    assert rejected.rejection_learning_ref is not None
    assert superseded.outcome == CorrectionReviewOutcome.superseded
    assert superseded.rejection_learning_ref is not None
    assert superseded.superseding_proposal_ref == "correction-proposal-ref:replacement"
    assert rejected.expected_changeset_plan_ref is None
    assert superseded.expected_changeset_plan_ref is None


def test_review_rejects_changed_proposal_binding() -> None:
    proposal_request = _proposal_request()
    request = _review_request(proposal_request).model_copy(
        update={"proposal_fingerprint_ref": "fingerprint-ref:changed"}
    )

    with pytest.raises(
        AutocorrectConflict,
        match="AUTOCORRECT_PROPOSAL_BINDING_CHANGED",
    ):
        CorrectionReviewSession().review(request)


def test_supersede_requires_a_distinct_bound_proposal() -> None:
    proposal_request = _proposal_request()
    proposal = build_correction_proposal(proposal_request)

    with pytest.raises(
        ValueError, match="AUTOCORRECT_SUPERSEDING_PROPOSAL_REF_REQUIRED"
    ):
        CorrectionReviewRequest(
            proposal=proposal_request,
            proposal_ref=proposal.proposal_ref,
            proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
            decision=CorrectionDecision.supersede,
            reviewer_ref="reviewer-ref:local-operator",
            idempotency_ref="idempotency-ref:correction:supersede",
            superseding_proposal_ref=proposal.proposal_ref,
        )


def test_api_exposes_backend_status_and_content_free_preview() -> None:
    client = TestClient(app)
    status_response = client.get("/control-center/autocorrect/status")
    proposal_request = _proposal_request()
    preview_response = client.post(
        "/control-center/autocorrect/proposals/preview",
        json=proposal_request.model_dump(mode="json"),
    )

    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "implemented_proposal_only"
    assert preview_response.status_code == 200
    proposal = preview_response.json()["data"]
    assert proposal["state"] == "ready_for_review"
    assert proposal["comparison"]["raw_values_included"] is False
    assert proposal["changeset_created"] is False
    assert (
        route_side_effect_class("/control-center/autocorrect/proposals/preview").value
        == "validation_only"
    )
    assert (
        "/control-center/autocorrect/proposals/preview"
        in CONTROL_CENTER_VALIDATION_ONLY_PATHS
    )


def test_api_review_preview_replays_and_changed_payload_returns_conflict() -> None:
    client = TestClient(app)
    proposal_request = _proposal_request()
    request = _review_request(
        proposal_request,
        idempotency_ref="idempotency-ref:correction:api-review",
    )
    endpoint = "/control-center/autocorrect/reviews/preview"

    first = client.post(endpoint, json=request.model_dump(mode="json"))
    replay = client.post(endpoint, json=request.model_dump(mode="json"))
    changed_proposal = _proposal_request(confidence_percent=89)
    conflict_request = _review_request(
        changed_proposal,
        idempotency_ref=request.idempotency_ref,
    )
    conflict = client.post(endpoint, json=conflict_request.model_dump(mode="json"))

    assert first.status_code == 200
    assert first.json()["data"]["outcome"] == "accepted_for_changeset_review"
    assert first.json()["data"]["canonical_state_mutated"] is False
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == (
        "AUTOCORRECT_IDEMPOTENCY_PAYLOAD_CONFLICT"
    )
    assert route_side_effect_class(endpoint).value == "validation_only"
    assert endpoint in CONTROL_CENTER_VALIDATION_ONLY_PATHS
