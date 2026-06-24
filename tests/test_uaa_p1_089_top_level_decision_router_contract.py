import pytest

from ultimate_ai_agent.core.decision_router import (
    DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    DECISION_ROUTER_REQUIRED_OUTCOME_KINDS,
    DecisionRouterAmbiguityPosture,
    DecisionRouterCandidate,
    DecisionRouterInput,
    DecisionRouterOutcome,
    DecisionRouterOutcomeKind,
    DecisionRouterTrace,
    route_decision,
)


def _candidate(
    candidate_ref: str,
    outcome_kind: str,
    *,
    confidence: float = 0.7,
    downstream_proposal_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> DecisionRouterCandidate:
    return DecisionRouterCandidate(
        candidate_ref=candidate_ref,
        outcome_kind=outcome_kind,
        safe_summary="Safe route outcome proposal for reviewed refs.",
        safe_reason_refs=[f"reason-ref:decision-router:{candidate_ref.rsplit(':', 1)[-1]}"],
        evidence_refs=["evidence:decision-router:test"],
        source_refs=source_refs or ["source:decision-router:test"],
        confidence=confidence,
        ambiguity_posture=DecisionRouterAmbiguityPosture.clear,
        next_safe_operator_action="Review the proposed route outcome; do not execute it.",
        downstream_proposal_refs=downstream_proposal_refs or [],
        module_refs=["module:decision-router"],
        operator_surface_refs=["surface:control-center:review"],
    )


def _input(candidates: list[DecisionRouterCandidate]) -> DecisionRouterInput:
    return DecisionRouterInput(
        router_input_ref="decision-router-input:test",
        safe_request_summary="Reviewed safe request summary.",
        source_refs=["source:reviewed:test"],
        evidence_refs=["evidence:decision-router:test"],
        memory_read_model_refs=["memory-read-model:reviewed:test"],
        plan_refs=["plan:reviewed:test"],
        action_inbox_refs=["action-inbox:proposal:test"],
        approval_refs=["approval-ref:identifier-only:test"],
        tool_decision_refs=["tool-decision:reviewed:test"],
        human_review_refs=["human-review:needed:test"],
        evidence_timeline_refs=["evidence-timeline:event:test"],
        candidates=candidates,
    )


def test_decision_router_models_every_required_outcome_kind() -> None:
    assert set(DECISION_ROUTER_REQUIRED_OUTCOME_KINDS) == {
        "answer_directly",
        "use_reviewed_memory",
        "propose_action_inbox_item",
        "ask_human",
        "escalate_to_review",
        "defer",
        "blocked_unsafe",
        "insufficient_evidence",
    }

    for outcome_kind in DECISION_ROUTER_REQUIRED_OUTCOME_KINDS:
        downstream = ["action-proposal:decision-router:test"] if outcome_kind == "propose_action_inbox_item" else []
        candidate = _candidate(
            f"decision-router-candidate:{outcome_kind}",
            outcome_kind,
            downstream_proposal_refs=downstream,
        )
        assert candidate.outcome_kind == outcome_kind


def test_decision_router_selects_highest_confidence_candidate_without_effects() -> None:
    outcome = route_decision(
        _input(
            [
                _candidate("decision-router-candidate:memory", DecisionRouterOutcomeKind.use_reviewed_memory, confidence=0.6),
                _candidate("decision-router-candidate:direct", DecisionRouterOutcomeKind.answer_directly, confidence=0.9),
            ]
        )
    )

    assert outcome.outcome_kind == "answer_directly"
    assert outcome.selected_candidate_ref == "decision-router-candidate:direct"
    assert outcome.route_authority_granted is False
    assert outcome.execution_performed is False
    assert outcome.no_model_call_performed is True
    assert outcome.no_tool_execution_performed is True
    assert outcome.no_workflow_execution_performed is True
    assert outcome.no_memory_write_performed is True
    assert outcome.no_context_injection_performed is True
    assert set(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS) <= set(outcome.blocked_authority_refs)
    assert outcome.trace.no_effect is True


def test_decision_router_uses_stable_tie_breaking() -> None:
    outcome = route_decision(
        _input(
            [
                _candidate("decision-router-candidate:z-memory", DecisionRouterOutcomeKind.use_reviewed_memory, confidence=0.8),
                _candidate("decision-router-candidate:a-direct", DecisionRouterOutcomeKind.answer_directly, confidence=0.8),
            ]
        )
    )

    assert outcome.outcome_kind == "answer_directly"
    assert outcome.selected_candidate_ref == "decision-router-candidate:a-direct"


def test_decision_router_blocked_unsafe_candidate_overrides_other_candidates() -> None:
    outcome = route_decision(
        _input(
            [
                _candidate("decision-router-candidate:direct", DecisionRouterOutcomeKind.answer_directly, confidence=1.0),
                _candidate(
                    "decision-router-candidate:blocked",
                    DecisionRouterOutcomeKind.blocked_unsafe,
                    confidence=0.2,
                ),
            ]
        )
    )

    assert outcome.outcome_kind == "blocked_unsafe"
    assert outcome.blocked_states
    assert outcome.blocked_states[0].blocked_authority_ref == "blocked-authority:no-unsafe-routing"


def test_decision_router_no_candidates_returns_insufficient_evidence() -> None:
    outcome = route_decision(_input([]))

    assert outcome.outcome_kind == "insufficient_evidence"
    assert outcome.selected_candidate_ref is None
    assert outcome.blocked_states
    assert outcome.trace.candidate_refs == []
    assert outcome.next_safe_operator_action == "Add reviewed evidence or ask a human to clarify the requested path."


def test_decision_router_requires_action_proposal_refs_for_action_inbox_outcomes() -> None:
    with pytest.raises(ValueError, match="downstream_proposal_refs"):
        _candidate(
            "decision-router-candidate:action",
            DecisionRouterOutcomeKind.propose_action_inbox_item,
        )

    candidate = _candidate(
        "decision-router-candidate:action",
        DecisionRouterOutcomeKind.propose_action_inbox_item,
        downstream_proposal_refs=["action-proposal:decision-router:test"],
    )
    outcome = route_decision(_input([candidate]))

    assert outcome.outcome_kind == "propose_action_inbox_item"
    assert outcome.downstream_proposal_refs == ["action-proposal:decision-router:test"]
    assert outcome.no_action_execution_performed is True


def test_decision_router_rejects_authority_flags_and_non_authoritative_sources() -> None:
    with pytest.raises(ValueError, match="runtime_model_call_allowed"):
        DecisionRouterInput(
            router_input_ref="decision-router-input:test",
            safe_request_summary="Reviewed safe request summary.",
            source_refs=["source:reviewed:test"],
            evidence_refs=["evidence:decision-router:test"],
            runtime_model_call_allowed=True,
        )

    with pytest.raises(ValueError, match="non-authoritative source ref"):
        _candidate(
            "decision-router-candidate:model-output",
            DecisionRouterOutcomeKind.answer_directly,
            source_refs=["model:unsafe-output-ref"],
        )


def test_decision_router_outcome_rejects_execution_authority() -> None:
    trace = DecisionRouterTrace(
        trace_ref="decision-router-trace:test",
        router_input_ref="decision-router-input:test",
        safe_reason_refs=["reason-ref:decision-router:test"],
        evidence_refs=["evidence:decision-router:test"],
        source_refs=["source:reviewed:test"],
    )

    with pytest.raises(ValueError, match="action_execution_allowed"):
        DecisionRouterOutcome(
            outcome_ref="decision-router-outcome:test",
            router_input_ref="decision-router-input:test",
            outcome_kind=DecisionRouterOutcomeKind.answer_directly,
            safe_summary="Safe route outcome proposal.",
            safe_reason_refs=["reason-ref:decision-router:test"],
            evidence_refs=["evidence:decision-router:test"],
            source_refs=["source:reviewed:test"],
            next_safe_operator_action="Review the proposed route outcome.",
            trace=trace,
            action_execution_allowed=True,
        )
