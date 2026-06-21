from ultimate_ai_agent.core.truth import (
    GroundingMode,
    GroundingPolicy,
    TruthRouteRequest,
    TruthSourceRouter,
    TruthTaskClass,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def test_no_required_source_returns_safe_unsupported_decision() -> None:
    request = TruthRouteRequest(
        request_id="trr_none",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        task_class=TruthTaskClass.factual_answer,
        question_or_claim="Unsupported claim",
        grounding_policy=GroundingPolicy(
            policy_id="gp_fact",
            task_class=TruthTaskClass.factual_answer,
            grounding_mode=GroundingMode.sources_required,
            unsupported_claim_behavior="ask_for_source",
        ),
        available_sources=[],
        data_classification="public",
    )

    decision = TruthSourceRouter().route(request)

    assert decision.selected_source_ids == []
    assert decision.required_next_action == "ask_for_source"
    assert "No approved source is available" in decision.safe_message
