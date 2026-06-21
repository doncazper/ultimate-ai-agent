from tests.m7_helpers import cloud_profile
from tests.m8_helpers import selected_route_pair
from tests.m9_helpers import approval_for_runtime, local_manifest, local_runtime_request, loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.model_runtime import FakeModelRuntimeTransport, LocalLoopbackModelRuntimeAdapter, ModelRuntimeRequestFactory


def test_denied_or_approval_required_routes_cannot_create_runtime_requests() -> None:
    route, decision = selected_route_pair()
    denied = decision.model_copy(update={"status": "denied", "selected_profile_id": None, "selected_model_id": None})
    approval_required = decision.model_copy(update={"status": "approval_required", "required_approval": True})

    for route_decision in [denied, approval_required]:
        try:
            ModelRuntimeRequestFactory.from_route_decision(route_decision, route, local_manifest())
            created = True
        except ValueError:
            created = False
        assert created is False


def test_credentialed_or_cloud_runtime_requests_are_denied_for_loopback_execution() -> None:
    adapter = LocalLoopbackModelRuntimeAdapter()
    credentialed = local_runtime_request(secret_handle_refs=["cred_ref"])
    cloud = local_runtime_request(model_profile_id="cloud_reasoner")
    _, _, grant, approval_decision = approval_for_runtime(cloud)
    cloud = cloud.model_copy(update={"approval_ref": grant.approval_ref})

    credential_result = adapter.validate_execution(credentialed, local_manifest(), loopback_endpoint(), loopback_policy(), None)
    cloud_result = adapter.validate_execution(cloud, local_manifest(), loopback_endpoint(), loopback_policy(), approval_decision)

    assert "CREDENTIALS_NOT_ALLOWED_FOR_M9" in credential_result.reason_codes
    assert "MODEL_PROFILE_NOT_ACCEPTED_BY_ADAPTER" in cloud_result.reason_codes


def test_public_ip_endpoint_is_denied_for_loopback_execution() -> None:
    adapter = LocalLoopbackModelRuntimeAdapter()
    policy = loopback_policy()
    endpoint = loopback_endpoint(base_url="http://8.8.8.8/api/generate", allowed_hosts=["8.8.8.8"])

    decision = adapter.validate_execution(
        local_runtime_request(),
        local_manifest(),
        endpoint,
        policy,
        approval_decision=None,
    )

    assert decision.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in decision.reason_codes


def test_soft_budget_warning_metadata_is_preserved_for_local_dev_execution() -> None:
    request = local_runtime_request(metadata={"route_reason_codes": ["SELECTED_PROFILE", "SOFT_BUDGET_EXCEEDED"]})
    _, _, grant, approval_decision = approval_for_runtime(request)
    response = LocalLoopbackModelRuntimeAdapter().execute_dev(
        request.model_copy(update={"approval_ref": grant.approval_ref}),
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(),
        approval_decision,
        transport=FakeModelRuntimeTransport(),
    )

    assert "SOFT_BUDGET_EXCEEDED" in response.warnings


def test_cloud_profile_fixture_is_not_accidentally_loopback_local() -> None:
    assert cloud_profile().provider_kind == "cloud_provider"
