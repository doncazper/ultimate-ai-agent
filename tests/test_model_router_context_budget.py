from tests.m7_helpers import local_profile, policy, route_request
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter


def test_context_requirement_larger_than_model_window_is_rejected():
    request = route_request(
        profiles=[local_profile(max_context_tokens=2048)],
        context_budget=ContextBudget(model_context_limit=4096),
        routing_policy=policy(min_context_tokens=4096),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.context_too_small
    assert "CONTEXT_TOO_SMALL" in decision.reason_codes


def test_request_tokens_must_fit_profile_context_window():
    request = route_request(
        profiles=[local_profile(max_context_tokens=1200)],
        routing_policy=policy(),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.context_too_small
    assert decision.selected_profile_id is None


def test_exhausted_available_history_budget_rejects_otherwise_capable_profile():
    request = route_request(
        profiles=[local_profile()],
        context_budget=ContextBudget(
            model_context_limit=4096,
            system_prompt_tokens=1000,
            tool_schema_tokens=1000,
            world_state_tokens=1000,
            context_pack_tokens=1000,
            completion_reserve_tokens=96,
            safety_margin_tokens=0,
        ),
        routing_policy=policy(),
    )

    decision = ModelRouter().route(request)

    assert request.context_budget.available_history_tokens == 0
    assert decision.status == ModelRouteStatus.context_too_small
    assert decision.selected_profile_id is None
    assert "CONTEXT_BUDGET_EXHAUSTED" in decision.reason_codes


def test_input_tokens_larger_than_available_history_budget_rejects_profile():
    request = route_request(
        profiles=[local_profile()],
        context_budget=ContextBudget(
            model_context_limit=4096,
            system_prompt_tokens=2000,
            completion_reserve_tokens=500,
            safety_margin_tokens=1000,
        ),
        routing_policy=policy(),
    )

    decision = ModelRouter().route(request)

    assert request.context_budget.available_history_tokens == 596
    assert decision.status == ModelRouteStatus.context_too_small
    assert "CONTEXT_BUDGET_INSUFFICIENT" in decision.reason_codes


def test_input_tokens_within_available_history_budget_can_select_profile():
    request = route_request(
        profiles=[local_profile()],
        context_budget=ContextBudget(
            model_context_limit=4096,
            system_prompt_tokens=500,
            completion_reserve_tokens=500,
            safety_margin_tokens=500,
        ),
        routing_policy=policy(),
    )

    decision = ModelRouter().route(request)

    assert request.estimated_input_tokens <= request.context_budget.available_history_tokens
    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "local_coder"
