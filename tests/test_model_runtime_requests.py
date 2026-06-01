import pytest

from tests.m7_helpers import cloud_profile, policy, route_request
from tests.m8_helpers import runtime_request, selected_route_pair, simulated_manifest
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter
from ultimate_ai_agent.core.model_runtime import (
    ModelRuntimeRequestFactory,
    ModelRuntimeSafetyMode,
    validate_runtime_request,
)


def test_runtime_request_validates_and_keeps_secret_handles_opaque():
    request = runtime_request(secret_handle_refs=["handle_opaque_1"])
    result = validate_runtime_request(request, simulated_manifest())

    assert result.success is True
    assert result.data["secret_handle_refs"] == ["handle_opaque_1"]
    assert "secret_value" not in str(result.model_dump()).lower()


def test_secret_like_prompt_summary_is_rejected():
    with pytest.raises(ValueError, match="secret-like"):
        runtime_request(prompt_summary="api_key='ABCDEFGHIJKLMNOP'")


def test_request_exceeding_adapter_limits_is_denied():
    result = validate_runtime_request(runtime_request(estimated_input_tokens=5000), simulated_manifest(max_input_tokens=1024))

    assert result.success is False
    assert result.error.code == "MODEL_RUNTIME_TOKEN_LIMIT_EXCEEDED"


def test_production_safety_mode_is_not_supported():
    with pytest.raises(ValueError):
        runtime_request(safety_mode=ModelRuntimeSafetyMode.disabled)


def test_factory_creates_request_from_selected_route_and_preserves_warnings():
    profile = cloud_profile(profile_id="cloud_soft", cost_per_1k_input_tokens=0.02, cost_per_1k_output_tokens=0.02)
    route = route_request(
        profiles=[profile],
        routing_policy=policy(
            required_capabilities=[],
            allow_cloud=True,
            allow_paid=True,
            max_estimated_cost_usd=0.01,
            max_estimated_cost_hard_limit=False,
        ),
        credential_availability={},
    )
    decision = ModelRouter().route(route)
    manifest = simulated_manifest()

    request = ModelRuntimeRequestFactory.from_route_decision(decision, route, manifest)

    assert decision.status == ModelRouteStatus.selected
    assert request.route_decision_ref == decision.decision_id
    assert request.metadata["route_reason_codes"] == decision.reason_codes
    assert "SOFT_BUDGET_EXCEEDED" in request.metadata["route_reason_codes"]


def test_factory_rejects_denied_and_approval_required_routes():
    route, decision = selected_route_pair()
    denied = decision.model_copy(update={"status": ModelRouteStatus.denied, "selected_profile_id": None, "selected_model_id": None})
    approval = decision.model_copy(update={"status": ModelRouteStatus.approval_required, "required_approval": True})

    with pytest.raises(ValueError, match="selected"):
        ModelRuntimeRequestFactory.from_route_decision(denied, route, simulated_manifest())
    with pytest.raises(ValueError, match="approval"):
        ModelRuntimeRequestFactory.from_route_decision(approval, route, simulated_manifest())


def test_factory_carries_credential_ref_as_opaque_handle_only():
    profile = cloud_profile(credential_ref="cred_provider_1")
    route = route_request(
        profiles=[profile],
        routing_policy=policy(allow_cloud=True, allow_paid=True),
        credential_availability={"cred_provider_1": True},
    )
    decision = ModelRouter().route(route)

    request = ModelRuntimeRequestFactory.from_route_decision(decision, route, simulated_manifest())

    assert request.secret_handle_refs == ["cred_provider_1"]
    assert "raw" not in str(request.model_dump()).lower()
