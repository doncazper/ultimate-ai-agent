import pytest

from ultimate_ai_agent.core.recall import (
    ContextPackBuildRequest,
    GroundedRecallDecision,
    GroundedRecallRequest,
    RecallCandidate,
    RecallDecisionStatus,
    RecallSelection,
    RecallSourceKind,
    build_evidence_linked_context_pack,
    route_grounded_recall,
)


def test_context_pack_builder_uses_selected_safe_summaries_and_refs_only() -> None:
    recall_decision = route_grounded_recall(
        GroundedRecallRequest(
            request_id="recall:req:pack",
            query_summary="Need M26 context.",
            candidates=[
                RecallCandidate(
                    candidate_ref="recall:candidate:canonical",
                    source_ref="canonical:m26",
                    source_kind=RecallSourceKind.canonical_document,
                    safe_summary="Canonical M26 summary.",
                    evidence_refs=["evidence:m26"],
                    receipt_refs=["receipt:m26"],
                    token_estimate=10,
                ),
                RecallCandidate(
                    candidate_ref="recall:candidate:memory",
                    source_ref="memory:m26",
                    source_kind=RecallSourceKind.reviewed_memory,
                    safe_summary="Reviewed memory reminder.",
                    memory_refs=["memory:m26"],
                    token_estimate=8,
                ),
            ],
        )
    )
    pack = build_evidence_linked_context_pack(
        ContextPackBuildRequest(
            pack_id="ctxpack:m26",
            request_id="ctxpack:req:m26",
            recall_decision=recall_decision,
            max_context_tokens=80,
        )
    )

    assert pack.context_pack_ref == "ctxpack:m26"
    assert [item.safe_summary for item in pack.items] == [
        "Canonical M26 summary.",
        "Reviewed memory reminder.",
    ]
    assert pack.evidence_refs == ["evidence:m26"]
    assert pack.receipt_refs == ["receipt:m26"]
    assert pack.memory_refs == ["memory:m26"]
    assert pack.context_injection_performed is False
    assert pack.raw_content_included is False
    assert pack.model_output_included is False


def test_context_pack_builder_enforces_budget_without_tokenizer_dependency() -> None:
    recall_decision = route_grounded_recall(
        GroundedRecallRequest(
            request_id="recall:req:budget",
            query_summary="Need M26 context.",
            candidates=[
                RecallCandidate(
                    candidate_ref="recall:candidate:canonical",
                    source_ref="canonical:m26",
                    source_kind=RecallSourceKind.canonical_document,
                    safe_summary="Canonical summary.",
                    token_estimate=25,
                ),
                RecallCandidate(
                    candidate_ref="recall:candidate:event",
                    source_ref="event:m26",
                    source_kind=RecallSourceKind.event_ledger,
                    safe_summary="Event summary.",
                    token_estimate=25,
                ),
            ],
        )
    )

    pack = build_evidence_linked_context_pack(
        ContextPackBuildRequest(
            pack_id="ctxpack:m26-budget",
            request_id="ctxpack:req:m26-budget",
            recall_decision=recall_decision,
            max_context_tokens=30,
        )
    )

    assert [item.candidate_ref for item in pack.items] == ["recall:candidate:canonical"]
    assert pack.token_budget_summary == "25/30 estimated tokens used"
    assert "CONTEXT_BUDGET_LIMIT_REACHED" in pack.warnings


def test_context_pack_builder_rejects_mismatched_selected_items() -> None:
    hostile_decision = GroundedRecallDecision(
        decision_id="recall:decision:hostile",
        request_id="recall:req:hostile",
        status=RecallDecisionStatus.allowed,
        selected=[
            RecallSelection(
                candidate_ref="recall:candidate:hostile",
                source_ref="model:m26",
                source_kind=RecallSourceKind.canonical_document,
                safe_summary="Hostile selected summary.",
                priority_rank=0,
                token_estimate=8,
            )
        ],
        safe_message="Hostile decision should not build.",
    )

    with pytest.raises(ValueError, match="source_ref/source_kind"):
        ContextPackBuildRequest(
            pack_id="ctxpack:m26-hostile",
            request_id="ctxpack:req:m26-hostile",
            recall_decision=hostile_decision,
        )
