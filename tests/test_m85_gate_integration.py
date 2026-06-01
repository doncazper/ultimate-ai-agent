from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus, default_foundation_gate_criteria


def test_foundation_gate_criteria_include_m85_approval_authority():
    criteria = default_foundation_gate_criteria()
    ids = {criterion.criterion_id for criterion in criteria}

    assert {
        "m85_approval_authority_files_present",
        "m85_arbitrary_approval_refs_rejected",
        "m85_local_approval_grant_validates",
        "m85_expired_revoked_approval_denies",
        "m85_router_uses_valid_approval_grant",
        "m85_runtime_factory_rejects_arbitrary_approval",
        "m85_tool_broker_rejects_arbitrary_approval",
        "m85_no_real_auth_oauth_network",
        "m85_approval_api_secret_echo_absent",
    }.issubset(ids)


def test_foundation_gate_evaluator_passes_m85_checks():
    results = {result.criterion_id: result for result in FoundationGateEvaluator().evaluate().results}

    assert results["m85_approval_authority_files_present"].status == FoundationGateStatus.passed
    assert results["m85_arbitrary_approval_refs_rejected"].status == FoundationGateStatus.passed
    assert results["m85_local_approval_grant_validates"].status == FoundationGateStatus.passed
    assert results["m85_expired_revoked_approval_denies"].status == FoundationGateStatus.passed
    assert results["m85_router_uses_valid_approval_grant"].status == FoundationGateStatus.passed
    assert results["m85_runtime_factory_rejects_arbitrary_approval"].status == FoundationGateStatus.passed
    assert results["m85_tool_broker_rejects_arbitrary_approval"].status == FoundationGateStatus.passed
    assert results["m85_no_real_auth_oauth_network"].status == FoundationGateStatus.passed
    assert results["m85_approval_api_secret_echo_absent"].status == FoundationGateStatus.passed
