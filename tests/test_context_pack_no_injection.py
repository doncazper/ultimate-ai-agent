import pytest

from ultimate_ai_agent.core.recall import ContextPackBuildRequest, GroundedRecallDecision, build_evidence_linked_context_pack


def test_context_pack_builder_rejects_injection_runtime_flag():
    decision = GroundedRecallDecision(
        decision_id="recall:decision:empty",
        request_id="recall:req:empty",
        selected=[],
        excluded=[],
        reason_codes=["NO_ELIGIBLE_RECALL_CANDIDATES"],
        safe_message="No eligible recall candidates were selected.",
    )

    with pytest.raises(ValueError, match="context_injection_enabled"):
        ContextPackBuildRequest(
            pack_id="ctxpack:inject",
            request_id="ctxpack:req:inject",
            recall_decision=decision,
            context_injection_enabled=True,
        )


def test_empty_context_pack_is_safe_and_non_injecting():
    decision = GroundedRecallDecision(
        decision_id="recall:decision:empty",
        request_id="recall:req:empty",
        selected=[],
        excluded=[],
        reason_codes=["NO_ELIGIBLE_RECALL_CANDIDATES"],
        safe_message="No eligible recall candidates were selected.",
    )

    pack = build_evidence_linked_context_pack(
        ContextPackBuildRequest(
            pack_id="ctxpack:empty",
            request_id="ctxpack:req:empty",
            recall_decision=decision,
        )
    )

    assert pack.items == []
    assert pack.context_injection_performed is False
    assert pack.safe_message == "Evidence-linked context pack contains safe summaries only."
