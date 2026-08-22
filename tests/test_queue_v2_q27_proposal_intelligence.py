from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import (
    CONTROL_CENTER_VALIDATION_ONLY_PATHS,
    route_side_effect_class,
)
from ultimate_ai_agent.core.ecosystem import (
    CanonicalOwnerId,
    EntityKind,
    PrivacyScope,
    ProposalCandidateKind,
    ProposalExtractionRequest,
    ProposalFact,
    ProposalSourceRevisionBinding,
    extract_proposal_candidates,
)


NOW = "2026-08-22T12:00:00Z"


def _fact(
    suffix: str,
    *,
    kind: ProposalCandidateKind = ProposalCandidateKind.task,
    revision_suffix: str = "v1",
    confidence: int = 85,
    subject_ref: str | None = "subject-ref:q27:one",
    participant_refs: tuple[str, ...] = (),
    occurred_at: str | None = None,
    due_at: str | None = None,
    ambiguity_refs: tuple[str, ...] = (),
    missing_evidence_refs: tuple[str, ...] = (),
    privacy_scope: PrivacyScope = PrivacyScope.workspace,
) -> ProposalFact:
    return ProposalFact(
        workspace_ref="workspace-ref:q27:local",
        fact_ref=f"proposal-fact-ref:q27:{suffix}",
        source_artifact_ref=f"source-artifact-ref:q27:{suffix}",
        source_revision_ref=f"source-revision-ref:q27:{suffix}:{revision_suffix}",
        candidate_kind=kind,
        safe_summary=f"Bounded synthetic {kind.value} candidate {suffix}.",
        evidence_refs=(f"evidence-ref:q27:{suffix}",),
        subject_ref=subject_ref,
        participant_refs=participant_refs,
        occurred_at=occurred_at,
        due_at=due_at,
        confidence_percent=confidence,
        privacy_scope=privacy_scope,
        ambiguity_refs=ambiguity_refs,
        missing_evidence_refs=missing_evidence_refs,
    )


def _request(
    *facts: ProposalFact, maximum_candidates: int = 20
) -> ProposalExtractionRequest:
    return ProposalExtractionRequest(
        workspace_ref="workspace-ref:q27:local",
        facts=facts,
        source_revision_bindings=tuple(
            ProposalSourceRevisionBinding(
                source_artifact_ref=fact.source_artifact_ref,
                current_source_revision_ref=fact.source_revision_ref,
            )
            for fact in facts
        ),
        requested_at=NOW,
        maximum_candidates=maximum_candidates,
    )


def test_extracts_all_five_candidate_kinds_with_canonical_owners() -> None:
    facts = (
        _fact(
            "event",
            kind=ProposalCandidateKind.event,
            occurred_at="2026-08-23T16:00:00Z",
        ),
        _fact("task", kind=ProposalCandidateKind.task),
        _fact("person", kind=ProposalCandidateKind.person),
        _fact("commitment", kind=ProposalCandidateKind.commitment),
        _fact(
            "meeting",
            kind=ProposalCandidateKind.meeting,
            occurred_at="2026-08-24T17:00:00Z",
            participant_refs=("person-ref:q27:participant",),
        ),
    )

    result = extract_proposal_candidates(_request(*facts))
    candidates = {item["candidate_kind"]: item for item in result["candidates"]}

    assert set(candidates) == {kind.value for kind in ProposalCandidateKind}
    assert candidates["event"]["target_entity_kind"] == EntityKind.event.value
    assert candidates["event"]["target_owner"] == CanonicalOwnerId.calendar.value
    assert candidates["task"]["target_owner"] == CanonicalOwnerId.tasks.value
    assert candidates["person"]["target_owner"] == CanonicalOwnerId.identity.value
    assert candidates["commitment"]["target_owner"] == CanonicalOwnerId.tasks.value
    assert candidates["meeting"]["target_entity_kind"] == EntityKind.event.value
    assert all(item["citation_refs"] for item in candidates.values())
    assert all(
        item["review_posture"] == "ready_for_review" for item in candidates.values()
    )


def test_stale_revision_blocks_candidate_without_dropping_citations() -> None:
    fact = _fact("stale", revision_suffix="v1")
    request = ProposalExtractionRequest(
        workspace_ref=fact.workspace_ref,
        facts=(fact,),
        source_revision_bindings=(
            ProposalSourceRevisionBinding(
                source_artifact_ref=fact.source_artifact_ref,
                current_source_revision_ref="source-revision-ref:q27:stale:v2",
            ),
        ),
        requested_at=NOW,
    )

    candidate = extract_proposal_candidates(request)["candidates"][0]

    assert candidate["stale_state"] == "stale"
    assert candidate["review_posture"] == "blocked_stale_source"
    assert candidate["citation_refs"] == ["evidence-ref:q27:stale"]
    assert candidate["direct_commit_allowed"] is False


def test_missing_kind_requirements_and_uncertainty_remain_reviewable() -> None:
    meeting = _fact(
        "meeting-gaps",
        kind=ProposalCandidateKind.meeting,
        subject_ref=None,
        confidence=55,
        ambiguity_refs=("ambiguity-ref:q27:meeting-timezone",),
    )

    candidate = extract_proposal_candidates(_request(meeting))["candidates"][0]

    assert candidate["review_posture"] == "needs_review"
    assert candidate["confidence_posture"] == "low"
    assert candidate["missing_evidence_refs"] == [
        "evidence-missing-ref:eco-010:participants",
        "evidence-missing-ref:eco-010:time",
    ]
    assert candidate["ambiguity_refs"] == ["ambiguity-ref:q27:meeting-timezone"]


def test_private_scope_and_no_authority_flags_are_preserved() -> None:
    fact = _fact(
        "private",
        privacy_scope=PrivacyScope.restricted_private,
    )

    result = extract_proposal_candidates(_request(fact))
    candidate = result["candidates"][0]

    assert candidate["privacy_scope"] == "restricted_private"
    assert candidate["proposal_only"] is True
    assert candidate["change_set_eligible"] is False
    assert candidate["model_call_performed"] is False
    assert candidate["source_read_performed"] is False
    assert candidate["target_write_performed"] is False
    assert result["approval_grant_created"] is False
    assert result["external_write_performed"] is False


def test_extraction_is_deterministic_and_bounded() -> None:
    facts = tuple(_fact(f"item-{index}") for index in range(3))
    request = _request(*facts, maximum_candidates=2)

    first = extract_proposal_candidates(request)
    second = extract_proposal_candidates(request)

    assert first == second
    assert first["candidate_count"] == 2
    assert first["truncated"] is True
    assert [item["source_fact_ref"] for item in first["candidates"]] == [
        "proposal-fact-ref:q27:item-0",
        "proposal-fact-ref:q27:item-1",
    ]


def test_request_rejects_unbound_duplicate_and_cross_workspace_facts() -> None:
    fact = _fact("binding")
    with pytest.raises(ValueError, match="SOURCE_REVISION_BINDING_REQUIRED"):
        ProposalExtractionRequest(
            workspace_ref=fact.workspace_ref,
            facts=(fact,),
            source_revision_bindings=(
                ProposalSourceRevisionBinding(
                    source_artifact_ref="source-artifact-ref:q27:other",
                    current_source_revision_ref="source-revision-ref:q27:other:v1",
                ),
            ),
            requested_at=NOW,
        )

    with pytest.raises(ValueError, match="DUPLICATE_FACT_REF"):
        _request(fact, fact)

    foreign = fact.model_copy(update={"workspace_ref": "workspace-ref:q27:foreign"})
    with pytest.raises(ValueError, match="CROSS_WORKSPACE_FACT_DENIED"):
        _request(foreign)


@pytest.mark.parametrize(
    "unsafe_summary_parts",
    (
        ("Contact person", "@", "example", ".", "test for details."),
        ("Read ", "https", ":", "//", "unsafe", ".", "example for details."),
        ("Load private data from ", "/", "Users", "/", "example", "/records."),
        ("Observed endpoint ", "192", ".", "0", ".", "2", ".", "1 for details."),
        ("Observed endpoint ", "local", "host for details."),
        ("Observed endpoint [", "2001", ":", "db8", "::", "1] for details."),
    ),
)
def test_fact_rejects_unredacted_safe_summary(
    unsafe_summary_parts: tuple[str, ...],
) -> None:
    values = _fact("unsafe").model_dump(mode="json")
    values["safe_summary"] = "".join(unsafe_summary_parts)
    with pytest.raises(ValueError, match="SAFE_SUMMARY_REDACTION_REQUIRED"):
        ProposalFact.model_validate(values)


@pytest.mark.parametrize(
    "safe_summary",
    (
        "Budget increased by 2.5 percent.",
        "Release v1.2.3 is planned.",
    ),
)
def test_fact_allows_decimal_and_version_summaries(safe_summary: str) -> None:
    values = _fact("decimal").model_dump(mode="json")
    values["safe_summary"] = safe_summary
    assert ProposalFact.model_validate(values).safe_summary == safe_summary


@pytest.mark.parametrize(
    "unsafe_ref_parts",
    (
        (
            "source-artifact-ref:q27:file:",
            "/",
            "workspace",
            "/",
            "private",
            "/",
            "data",
        ),
        ("source-artifact-ref:q27:", "https", ":private"),
        ("source-artifact-ref:q27:", "https", ":", "//", "private", ".", "example"),
        ("source-artifact-ref:q27:host:", "founder", "-", "machine", ".", "local"),
        ("source-artifact-ref:q27:ip:", "192", ".", "0", ".", "2", ".", "1"),
        ("source-artifact-ref:q27:ip:", "2001", ":", "db8", "::", "1"),
    ),
)
def test_source_binding_rejects_unsafe_ref_forms(
    unsafe_ref_parts: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="SOURCE_ARTIFACT_REF_SAFE_REF_REQUIRED"):
        ProposalSourceRevisionBinding(
            source_artifact_ref="".join(unsafe_ref_parts),
            current_source_revision_ref="source-revision-ref:q27:safe:v1",
        )


def test_candidate_ref_binds_material_review_posture() -> None:
    high = extract_proposal_candidates(_request(_fact("material", confidence=90)))[
        "candidates"
    ][0]
    low = extract_proposal_candidates(_request(_fact("material", confidence=10)))[
        "candidates"
    ][0]

    assert high["review_posture"] == "ready_for_review"
    assert low["review_posture"] == "needs_review"
    assert high["candidate_ref"] != low["candidate_ref"]


def test_validation_only_api_and_cli_contract_shape() -> None:
    request = _request(_fact("api"))
    response = TestClient(app).post(
        "/control-center/proposal-intelligence/extract",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["candidate_count"] == 1
    assert payload["data"]["proposal_only"] is True
    assert payload["data"]["change_set_created"] is False
    assert (
        route_side_effect_class("/control-center/proposal-intelligence/extract").value
        == "validation_only"
    )
    assert (
        "/control-center/proposal-intelligence/extract"
        in CONTROL_CENTER_VALIDATION_ONLY_PATHS
    )
