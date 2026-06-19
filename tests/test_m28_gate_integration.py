from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m28_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m28_approval_authority_v2_action_policy_safe" in criterion_ids
    assert "m28_action_policy_openapi_routes_unchanged" in criterion_ids
    assert "m28_m29_remains_future" in criterion_ids

    criterion = next(
        item for item in criteria if item.criterion_id == "m28_approval_authority_v2_action_policy_safe"
    )
    assert "Approval Authority v2" in criterion.pass_condition
    assert "action execution" in criterion.pass_condition
    assert "approval_ref alone denied" in criterion.pass_condition


def test_m28_openapi_route_guard_rejects_action_execution_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M28_OPENAPI_PATH_COUNT, m28_openapi_route_failures

    failures = m28_openapi_route_failures(
        {
            "/actions/execute": {},
            "/actions/run": {},
            "/approval/execute": {},
            "/approvals/execute": {},
            "/action-policy/execute": {},
            "/tools/execute": {},
            "/plugins/enable": {},
        }
    )

    assert any("/actions/execute" in failure for failure in failures)
    assert any("/approval/execute" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M28_OPENAPI_PATH_COUNT == 76
    assert m28_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m28_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m28_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
