import pytest

from tests.m7_helpers import cloud_profile, policy, route_request
from tests.m8_helpers import runtime_request, selected_route_pair, simulated_manifest
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter
from ultimate_ai_agent.core.model_router.decisions import build_model_route_decision_ref
from ultimate_ai_agent.core.model_runtime import (
    ModelRuntimeRequestFactory,
    ModelRuntimeSafetyMode,
    validate_runtime_request,
)


def test_runtime_request_validates_and_keeps_secret_handles_opaque() -> None:
    request = runtime_request(secret_handle_refs=["handle_opaque_1"])
    result = validate_runtime_request(request, simulated_manifest())

    assert result.success is True
    assert result.data["secret_handle_refs"] == ["handle_opaque_1"]
    assert "secret_value" not in str(result.model_dump()).lower()


def test_secret_like_prompt_summary_is_rejected() -> None:
    with pytest.raises(ValueError, match="secret-like"):
        runtime_request(prompt_summary="api_key='ABCDEFGHIJKLMNOP'")


def test_request_exceeding_adapter_limits_is_denied() -> None:
    result = validate_runtime_request(
        runtime_request(estimated_input_tokens=5000),
        simulated_manifest(max_input_tokens=1024),
    )

    assert result.success is False
    assert result.error.code == "MODEL_RUNTIME_TOKEN_LIMIT_EXCEEDED"


def test_production_safety_mode_is_not_supported() -> None:
    with pytest.raises(ValueError):
        runtime_request(safety_mode=ModelRuntimeSafetyMode.disabled)


def test_factory_creates_request_from_selected_route_and_preserves_warnings() -> None:
    profile = cloud_profile(
        profile_id="cloud_soft",
        cost_per_1k_input_tokens=0.02,
        cost_per_1k_output_tokens=0.02,
    )
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
    manifest = simulated_manifest(
        supported_provider_kinds=["cloud_provider"],
        accepts_model_profile_ids=["cloud_soft"],
    )

    request = ModelRuntimeRequestFactory.from_route_decision(decision, route, manifest)

    assert decision.status == ModelRouteStatus.selected
    assert request.route_decision_ref == build_model_route_decision_ref(decision)
    assert request.metadata["route_decision_ref"] == request.route_decision_ref
    assert request.metadata["route_reason_codes"] == decision.reason_codes
    assert "SOFT_BUDGET_EXCEEDED" in request.metadata["route_reason_codes"]


def test_factory_does_not_trust_caller_controlled_route_decision_id() -> None:
    route, decision = selected_route_pair()
    manifest = simulated_manifest()
    substituted = decision.model_copy(update={"decision_id": "mroute_substituted"})

    original_request = ModelRuntimeRequestFactory.from_route_decision(
        decision,
        route,
        manifest,
    )
    substituted_request = ModelRuntimeRequestFactory.from_route_decision(
        substituted,
        route,
        manifest,
    )

    assert substituted_request.route_decision_ref == original_request.route_decision_ref
    assert substituted_request.runtime_request_id == original_request.runtime_request_id
    assert substituted_request.route_decision_ref != substituted.decision_id


@pytest.mark.parametrize(
    ("field_name", "substituted_value"),
    [
        ("eval_result_id", "evaluation-ref:substituted"),
        ("trace_id", "trace-ref:substituted"),
        ("correlation_id", "correlation-ref:substituted"),
    ],
)
def test_factory_diagnostic_refs_cannot_fork_runtime_identity(
    field_name: str,
    substituted_value: str,
) -> None:
    route, decision = selected_route_pair()
    manifest = simulated_manifest()
    substituted = decision.model_copy(update={field_name: substituted_value})

    original_request = ModelRuntimeRequestFactory.from_route_decision(
        decision,
        route,
        manifest,
    )
    substituted_request = ModelRuntimeRequestFactory.from_route_decision(
        substituted,
        route,
        manifest,
    )

    assert substituted_request.route_decision_ref == original_request.route_decision_ref
    assert substituted_request.runtime_request_id == original_request.runtime_request_id


def test_factory_rejects_denied_and_approval_required_routes() -> None:
    route, decision = selected_route_pair()
    denied = decision.model_copy(
        update={
            "status": ModelRouteStatus.denied,
            "selected_profile_id": None,
            "selected_model_id": None,
        }
    )
    approval = decision.model_copy(
        update={"status": ModelRouteStatus.approval_required, "required_approval": True}
    )

    with pytest.raises(ValueError, match="selected"):
        ModelRuntimeRequestFactory.from_route_decision(
            denied, route, simulated_manifest()
        )
    with pytest.raises(ValueError, match="approval"):
        ModelRuntimeRequestFactory.from_route_decision(
            approval, route, simulated_manifest()
        )


def test_factory_carries_credential_ref_as_opaque_handle_only() -> None:
    profile = cloud_profile(credential_ref="cred_provider_1")
    route = route_request(
        profiles=[profile],
        routing_policy=policy(allow_cloud=True, allow_paid=True),
        credential_availability={"cred_provider_1": True},
    )
    decision = ModelRouter().route(route)

    request = ModelRuntimeRequestFactory.from_route_decision(
        decision,
        route,
        simulated_manifest(
            supported_provider_kinds=["cloud_provider"],
            accepts_model_profile_ids=["cloud_reasoner"],
        ),
    )

    assert request.secret_handle_refs == ["cred_provider_1"]
    assert "raw" not in str(request.model_dump()).lower()


@pytest.mark.parametrize(
    ("decision_update", "request_update", "error"),
    [
        ({"request_id": "route_req_changed"}, {}, "request binding"),
        ({"run_id": "run_changed"}, {}, "run binding"),
        ({"selected_model_id": "model_changed"}, {}, "model binding"),
        ({}, {"request_id": "route_req_changed"}, "request binding"),
    ],
)
def test_factory_rejects_route_request_binding_drift(
    decision_update: dict[str, object],
    request_update: dict[str, object],
    error: str,
) -> None:
    route, decision = selected_route_pair()

    with pytest.raises(ValueError, match=error):
        ModelRuntimeRequestFactory.from_route_decision(
            decision.model_copy(update=decision_update),
            route.model_copy(update=request_update),
            simulated_manifest(),
        )


def test_factory_rejects_adapter_manifest_scope_mismatch() -> None:
    route, decision = selected_route_pair()

    with pytest.raises(ValueError, match="provider kind"):
        ModelRuntimeRequestFactory.from_route_decision(
            decision,
            route,
            simulated_manifest(supported_provider_kinds=["cloud_provider"]),
        )
    with pytest.raises(ValueError, match="model profile"):
        ModelRuntimeRequestFactory.from_route_decision(
            decision,
            route,
            simulated_manifest(accepts_model_profile_ids=["other-profile"]),
        )


def test_factory_rejects_forged_selection_of_disabled_profile() -> None:
    route, decision = selected_route_pair()
    disabled_profile = route.available_profiles[0].model_copy(update={"enabled": False})
    forged_route = route.model_copy(update={"available_profiles": [disabled_profile]})

    with pytest.raises(ValueError, match="not reproducible"):
        ModelRuntimeRequestFactory.from_route_decision(
            decision,
            forged_route,
            simulated_manifest(),
        )
