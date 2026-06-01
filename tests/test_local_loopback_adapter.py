from tests.m9_helpers import approval_for_runtime, local_manifest, local_runtime_request, loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.model_runtime import (
    FakeModelRuntimeTransport,
    LocalLoopbackModelRuntimeAdapter,
    ModelRuntimeResponseStatus,
    response_is_truth_authority,
)


def test_execution_validation_requires_opt_in_policy_approval_and_no_secret_handles():
    adapter = LocalLoopbackModelRuntimeAdapter()
    request = local_runtime_request(approval_ref="human_approved_ref_123")

    disabled_policy = adapter.validate_execution(
        request,
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(allow_real_loopback_execution=False),
        approval_decision=None,
    )
    arbitrary = adapter.validate_execution(request, local_manifest(), loopback_endpoint(), loopback_policy(), approval_decision=None)
    secret_handle = adapter.validate_execution(
        local_runtime_request(secret_handle_refs=["cred_ref"]),
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(),
        approval_decision=None,
    )

    assert disabled_policy.allowed is False
    assert "REAL_LOOPBACK_EXECUTION_NOT_ENABLED" in disabled_policy.reason_codes
    assert arbitrary.allowed is False
    assert "APPROVAL_DECISION_REQUIRED" in arbitrary.reason_codes
    assert secret_handle.allowed is False
    assert "CREDENTIALS_NOT_ALLOWED_FOR_M9" in secret_handle.reason_codes


def test_valid_approval_and_fake_transport_produce_non_authoritative_local_dev_response():
    adapter = LocalLoopbackModelRuntimeAdapter()
    request = local_runtime_request()
    _, _, grant, approval_decision = approval_for_runtime(request)
    request = request.model_copy(update={"approval_ref": grant.approval_ref})

    decision = adapter.validate_execution(request, local_manifest(), loopback_endpoint(), loopback_policy(), approval_decision)
    response = adapter.execute_dev(
        request,
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(),
        approval_decision,
        transport=FakeModelRuntimeTransport(),
    )

    assert decision.allowed is True
    assert "APPROVAL_VALIDATED" in decision.reason_codes
    assert response.status == ModelRuntimeResponseStatus.local_loopback_success
    assert response.response_origin == "fake_transport"
    assert response.metadata["truth_authority"] is False
    assert response.metadata["runtime_boundary"] == "local_loopback_dev"
    assert response_is_truth_authority(response) is False
    assert request.prompt_summary not in response.output_summary


def test_execute_dev_falls_back_to_simulation_when_blocked():
    response = LocalLoopbackModelRuntimeAdapter().execute_dev(
        local_runtime_request(approval_ref="human_approved_ref_123"),
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(require_simulated_fallback=True),
        approval_decision=None,
        transport=FakeModelRuntimeTransport(),
    )

    assert response.status == ModelRuntimeResponseStatus.simulated_success
    assert response.response_origin == "simulated"
    assert response.metadata["fallback_reason_codes"]
