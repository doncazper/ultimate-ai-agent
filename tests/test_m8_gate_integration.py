from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria


def test_foundation_gate_criteria_include_m8_runtime_surface():
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "m8_model_runtime_files_present",
        "m8_runtime_kinds_stub_only",
        "m8_model_runtime_no_real_calls",
        "m8_simulation_endpoint_safe",
        "m8_runtime_responses_simulated_only",
        "m8_runtime_secret_prompt_blocked",
        "m8_api_validation_secret_echo_absent",
    }.issubset(by_id)


def test_foundation_gate_evaluator_passes_m8_runtime_checks(foundation_gate_results):
    assert foundation_gate_results["m8_model_runtime_files_present"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_runtime_kinds_stub_only"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_model_runtime_no_real_calls"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_simulation_endpoint_safe"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_runtime_responses_simulated_only"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_runtime_secret_prompt_blocked"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m8_api_validation_secret_echo_absent"].status == FoundationGateStatus.passed
