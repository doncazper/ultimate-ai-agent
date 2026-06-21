from typing import Any
from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import M151_LOCAL_OPENWEBUI_TEST_ROUTES


def test_m151_gate_criteria_are_registered_and_pass(foundation_gate_results: Any) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m151_local_openwebui_test_shell_contracts",
        "m151_local_openwebui_test_shell_route_boundary",
        "m151_local_openwebui_test_shell_launcher",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m151_route_set_is_exact_local_openwebui_smoke_pair() -> None:
    assert M151_LOCAL_OPENWEBUI_TEST_ROUTES == {
        "/v1/models",
        "/v1/chat/completions",
    }
