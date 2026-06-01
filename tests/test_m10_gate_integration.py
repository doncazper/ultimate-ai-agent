from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus


def test_m10_gate_criteria_pass_on_current_repo():
    report = FoundationGateEvaluator(Path(__file__).resolve().parent.parent).evaluate()
    results = {result.criterion_id: result for result in report.results}

    for criterion_id in [
        "m10_manual_smoke_files_present",
        "m10_stdlib_network_isolated",
        "m10_gate_and_verify_do_not_call_smoke_script",
        "m10_public_api_has_no_smoke_execute_endpoint",
        "m10_fixed_prompt_and_loopback_policy_enforced",
        "m10_smoke_approval_required",
        "m10_smoke_response_not_truth_authority",
    ]:
        assert results[criterion_id].status == FoundationGateStatus.passed
