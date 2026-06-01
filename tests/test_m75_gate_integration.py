from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus, default_foundation_gate_criteria


def test_foundation_gate_criteria_include_m75_api_boundary_surface():
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "api_manifest_endpoint_present",
        "openapi_contract_valid",
        "api_operation_ids_unique",
        "forbidden_runtime_routes_absent",
        "agents_md_guidance_present",
        "runtime_agent_config_loading_absent",
    }.issubset(by_id)


def test_foundation_gate_evaluator_passes_m75_api_boundary_checks():
    report = FoundationGateEvaluator().evaluate()
    results = {result.criterion_id: result for result in report.results}

    assert results["api_manifest_endpoint_present"].status == FoundationGateStatus.passed
    assert results["openapi_contract_valid"].status == FoundationGateStatus.passed
    assert results["api_operation_ids_unique"].status == FoundationGateStatus.passed
    assert results["forbidden_runtime_routes_absent"].status == FoundationGateStatus.passed
    assert results["agents_md_guidance_present"].status == FoundationGateStatus.passed
    assert results["runtime_agent_config_loading_absent"].status == FoundationGateStatus.passed
