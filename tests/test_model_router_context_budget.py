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
