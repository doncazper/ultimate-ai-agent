from tests.m7_helpers import cloud_profile, local_profile, policy, route_request
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter, ModelTaskCapability


def test_local_model_selected_when_prefer_local_and_capable():
    request = route_request(
        profiles=[
            cloud_profile(capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding]),
            local_profile(capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding]),
        ],
        required_capabilities=[ModelTaskCapability.coding],
        routing_policy=policy(
            required_capabilities=[ModelTaskCapability.coding],
            prefer_local=True,
            allow_cloud=True,
            allow_paid=True,
        ),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "local_coder"
    assert "SELECTED_PROFILE" in decision.reason_codes


def test_disabled_profile_and_capability_miss_are_rejected():
    request = route_request(
        profiles=[
            local_profile(profile_id="disabled_local", enabled=False),
            local_profile(profile_id="chat_only", capabilities=[ModelTaskCapability.chat]),
        ],
        required_capabilities=[ModelTaskCapability.coding],
        routing_policy=policy(required_capabilities=[ModelTaskCapability.coding]),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.capability_missing
    assert set(decision.rejected_profile_ids) == {"disabled_local", "chat_only"}
    assert "PROFILE_DISABLED" in decision.reason_codes
    assert "CAPABILITY_MISSING" in decision.reason_codes


def test_deterministic_tie_breaker_uses_stable_profile_id():
    request = route_request(
        profiles=[
            local_profile(profile_id="z_profile"),
            local_profile(profile_id="a_profile"),
        ],
        routing_policy=policy(prefer_local=True),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "a_profile"


def test_paid_model_blocked_when_policy_disallows_paid_routes():
    request = route_request(
        profiles=[cloud_profile()],
        routing_policy=policy(allow_cloud=True, allow_paid=False),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.denied
    assert "PAID_MODEL_DISALLOWED" in decision.reason_codes


def test_credentialed_profile_skipped_when_credential_metadata_unavailable():
    request = route_request(
        profiles=[cloud_profile(credential_ref="cred_missing")],
        routing_policy=policy(allow_cloud=True, allow_paid=True),
        credential_availability={"cred_missing": False},
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.denied
    assert "CREDENTIAL_NOT_AVAILABLE" in decision.reason_codes


def test_router_selects_candidate_with_soft_budget_warning():
    request = route_request(
        profiles=[
            local_profile(
                cost_per_1k_input_tokens=0.02,
                cost_per_1k_output_tokens=0.02,
            )
        ],
        routing_policy=policy(
            prefer_local=True,
            allow_paid=True,
            max_estimated_cost_usd=0.01,
            max_estimated_cost_hard_limit=False,
        ),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "local_coder"
    assert "SOFT_BUDGET_EXCEEDED" in decision.reason_codes
    assert decision.safe_message == "Model route selected with policy warnings. No model execution was performed."


def test_router_rejects_candidate_with_hard_budget_denial():
    request = route_request(
        profiles=[
            local_profile(
                cost_per_1k_input_tokens=0.02,
                cost_per_1k_output_tokens=0.02,
            )
        ],
        routing_policy=policy(
            prefer_local=True,
            allow_paid=True,
            max_estimated_cost_usd=0.01,
            max_estimated_cost_hard_limit=True,
        ),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.budget_exceeded
    assert decision.selected_profile_id is None
    assert "HARD_BUDGET_EXCEEDED" in decision.reason_codes
