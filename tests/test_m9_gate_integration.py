from tests.m9_helpers import local_manifest, local_runtime_request, loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.gate import FoundationGateStatus
from ultimate_ai_agent.core.model_runtime import FakeModelRuntimeTransport, LocalLoopbackModelRuntimeAdapter


def test_m9_gate_criteria_pass_on_current_repo(foundation_gate_results):
    for criterion_id in [
        "m9_loopback_runtime_files_present",
        "m9_non_loopback_endpoints_denied",
        "m9_non_loopback_policy_override_denied",
        "m9_loopback_policy_model_rejects_hostile_inputs",
        "m9_public_and_private_ip_endpoints_denied",
        "m9_approval_api_uses_public_authority_helper",
        "m9_arbitrary_approval_refs_denied",
        "m9_fake_transport_only_in_gate",
        "m9_simulated_fallback_available",
        "m9_model_output_not_truth_authority",
    ]:
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m9_fake_transport_does_not_make_real_network_call():
    response = LocalLoopbackModelRuntimeAdapter().execute_dev(
        local_runtime_request(),
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(require_approval=False),
        approval_decision=None,
        transport=FakeModelRuntimeTransport(),
    )

    assert response.response_origin == "fake_transport"
    assert response.metadata["network_destination"] == "loopback_only"
