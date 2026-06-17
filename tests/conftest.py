import pytest

from ultimate_ai_agent.core.gate import FoundationGateEvaluator


@pytest.fixture(scope="session")
def foundation_gate_report():
    return FoundationGateEvaluator().evaluate()


@pytest.fixture(scope="session")
def foundation_gate_results(foundation_gate_report):
    return {result.criterion_id: result for result in foundation_gate_report.results}

