import pytest

from ultimate_ai_agent.core.recall import (
    GroundedRecallRequest,
    RecallCandidate,
    RecallCandidateStatus,
    RecallDecisionStatus,
    RecallSourceKind,
    route_grounded_recall,
)


def _candidate(
    ref: str,
    source_ref: str,
    source_kind: RecallSourceKind,
    summary: str = "Safe summary.",
    *,
    status: RecallCandidateStatus = RecallCandidateStatus.active,
    reviewed: bool = True,
    token_estimate: int = 8,
) -> RecallCandidate:
    return RecallCandidate(
        candidate_ref=ref,
        source_ref=source_ref,
        source_kind=source_kind,
        safe_summary=summary,
        status=status,
        reviewed=reviewed,
        token_estimate=token_estimate,
        evidence_refs=["evidence:m26"] if source_kind != RecallSourceKind.unreviewed_memory else [],
    )


def test_grounded_recall_router_selects_safe_candidates_by_source_priority():
    request = GroundedRecallRequest(
        request_id="recall:req:priority",
        query_summary="Need M26 context.",
        candidates=[
            _candidate(
                "recall:candidate:memory",
                "memory:m26",
                RecallSourceKind.reviewed_memory,
                "Reviewed memory summary.",
            ),
            _candidate(
                "recall:candidate:event",
                "event:m26",
                RecallSourceKind.event_ledger,
                "Event ledger summary.",
            ),
            _candidate(
                "recall:candidate:canonical",
                "canonical:m26",
                RecallSourceKind.canonical_document,
                "Canonical summary.",
            ),
        ],
        max_candidates=3,
        max_context_tokens=100,
    )

    decision = route_grounded_recall(request)

    assert decision.status == RecallDecisionStatus.allowed
    assert [item.candidate_ref for item in decision.selected] == [
        "recall:candidate:canonical",
        "recall:candidate:event",
        "recall:candidate:memory",
    ]
    assert decision.no_memory_write_performed is True
    assert decision.no_external_retrieval_performed is True
    assert decision.no_vector_search_performed is True
    assert decision.no_context_injection_performed is True


def test_grounded_recall_router_excludes_unknown_and_arbitrary_refs():
    request = GroundedRecallRequest(
        request_id="recall:req:unknown",
        query_summary="Need M26 context.",
        candidates=[
            _candidate(
                "recall:candidate:random",
                "random:source",
                RecallSourceKind.unknown,
                "Unknown source summary.",
            ),
            _candidate(
                "recall:candidate:canonical",
                "canonical:m26",
                RecallSourceKind.canonical_document,
                "Canonical source summary.",
            ),
        ],
    )

    decision = route_grounded_recall(request)

    assert [item.candidate_ref for item in decision.selected] == ["recall:candidate:canonical"]
    assert any(item.candidate_ref == "recall:candidate:random" for item in decision.excluded)
    unknown = next(item for item in decision.excluded if item.candidate_ref == "recall:candidate:random")
    assert "UNKNOWN_SOURCE_KIND_DENIED" in unknown.reason_codes
    assert "ARBITRARY_SOURCE_REF_DENIED" in unknown.reason_codes


@pytest.mark.parametrize(
    ("source_ref", "declared_kind", "expected_reason"),
    [
        ("memory:m26", RecallSourceKind.canonical_document, "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED"),
        ("memory:m26", RecallSourceKind.evidence_manifest, "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED"),
        ("memory:m26", RecallSourceKind.receipt, "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED"),
        ("memory:m26", RecallSourceKind.event_ledger, "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED"),
        ("memory:m26", RecallSourceKind.user_reviewed_source, "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED"),
        ("model:m26", RecallSourceKind.canonical_document, "MODEL_OUTPUT_RECALL_DENIED"),
        ("runtime:m26", RecallSourceKind.canonical_document, "RUNTIME_OUTPUT_RECALL_DENIED"),
        ("openwebui:m26", RecallSourceKind.canonical_document, "OPENWEBUI_OUTPUT_RECALL_DENIED"),
        ("random:m26", RecallSourceKind.canonical_document, "ARBITRARY_SOURCE_REF_DENIED"),
    ],
)
def test_grounded_recall_router_denies_source_ref_kind_mismatches(
    source_ref: str,
    declared_kind: RecallSourceKind,
    expected_reason: str,
):
    request = GroundedRecallRequest(
        request_id="recall:req:source-identity",
        query_summary="Need M26 context.",
        candidates=[
            _candidate(
                "recall:candidate:hostile",
                source_ref,
                declared_kind,
                "Hostile source identity summary.",
            )
        ],
    )

    decision = route_grounded_recall(request)

    assert decision.status == RecallDecisionStatus.blocked
    assert not decision.selected
    assert [item.candidate_ref for item in decision.excluded] == ["recall:candidate:hostile"]
    reason_codes = set(decision.excluded[0].reason_codes)
    assert expected_reason in reason_codes
    if source_ref != "random:m26":
        assert "SOURCE_REF_KIND_MISMATCH_DENIED" in reason_codes


def test_grounded_recall_router_preserves_valid_primary_source_refs():
    request = GroundedRecallRequest(
        request_id="recall:req:valid-primary",
        query_summary="Need M26 context.",
        candidates=[
            _candidate("recall:candidate:receipt", "receipt:m26", RecallSourceKind.receipt, "Receipt summary."),
            _candidate("recall:candidate:evidence", "evidence:m26", RecallSourceKind.evidence_manifest, "Evidence summary."),
            _candidate("recall:candidate:canonical", "canonical:m26", RecallSourceKind.canonical_document, "Canonical summary."),
            _candidate("recall:candidate:event", "event:m26", RecallSourceKind.event_ledger, "Event summary."),
            _candidate(
                "recall:candidate:user-reviewed",
                "user-review:m26",
                RecallSourceKind.user_reviewed_source,
                "User reviewed summary.",
            ),
        ],
        max_candidates=5,
    )

    decision = route_grounded_recall(request)

    assert decision.status == RecallDecisionStatus.allowed
    assert [item.candidate_ref for item in decision.selected] == [
        "recall:candidate:canonical",
        "recall:candidate:evidence",
        "recall:candidate:receipt",
        "recall:candidate:event",
        "recall:candidate:user-reviewed",
    ]
    assert not decision.excluded


def test_grounded_recall_router_excludes_model_runtime_and_openwebui_outputs():
    request = GroundedRecallRequest(
        request_id="recall:req:outputs",
        query_summary="Need M26 context.",
        candidates=[
            _candidate("recall:candidate:model", "model:m26", RecallSourceKind.model_output, "Model output summary."),
            _candidate("recall:candidate:runtime", "runtime:m26", RecallSourceKind.runtime_output, "Runtime output summary."),
            _candidate(
                "recall:candidate:openwebui",
                "openwebui:m26",
                RecallSourceKind.openwebui_output,
                "OpenWebUI output summary.",
            ),
        ],
    )

    decision = route_grounded_recall(request)

    assert decision.status == RecallDecisionStatus.blocked
    assert not decision.selected
    reason_codes = {reason for item in decision.excluded for reason in item.reason_codes}
    assert "MODEL_OUTPUT_EXCLUDED" in reason_codes
    assert "RUNTIME_OUTPUT_EXCLUDED" in reason_codes
    assert "OPENWEBUI_OUTPUT_EXCLUDED" in reason_codes


def test_grounded_recall_router_excludes_stale_conflicted_revoked_deleted_and_superseded():
    request = GroundedRecallRequest(
        request_id="recall:req:states",
        query_summary="Need M26 context.",
        candidates=[
            _candidate("recall:candidate:stale", "canonical:stale", RecallSourceKind.canonical_document, status=RecallCandidateStatus.stale),
            _candidate(
                "recall:candidate:conflicted",
                "canonical:conflicted",
                RecallSourceKind.canonical_document,
                status=RecallCandidateStatus.conflicted,
            ),
            _candidate(
                "recall:candidate:revoked",
                "canonical:revoked",
                RecallSourceKind.canonical_document,
                status=RecallCandidateStatus.revoked,
            ),
            _candidate(
                "recall:candidate:deleted",
                "canonical:deleted",
                RecallSourceKind.canonical_document,
                status=RecallCandidateStatus.deleted,
            ),
            _candidate(
                "recall:candidate:superseded",
                "canonical:superseded",
                RecallSourceKind.canonical_document,
                status=RecallCandidateStatus.superseded,
            ),
        ],
    )

    decision = route_grounded_recall(request)

    assert not decision.selected
    reason_codes = {reason for item in decision.excluded for reason in item.reason_codes}
    assert "STALE_SOURCE_EXCLUDED" in reason_codes
    assert "CONFLICTED_SOURCE_EXCLUDED" in reason_codes
    assert "REVOKED_SOURCE_EXCLUDED" in reason_codes
    assert "DELETED_SOURCE_EXCLUDED" in reason_codes
    assert "SUPERSEDED_SOURCE_EXCLUDED" in reason_codes
