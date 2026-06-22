from typing import Any
import pytest

from ultimate_ai_agent.core.gate import FoundationGateEvaluator


@pytest.fixture(scope="session")
def foundation_gate_report() -> Any:
    return FoundationGateEvaluator().evaluate()


@pytest.fixture(scope="session")
def foundation_gate_results(foundation_gate_report: Any) -> Any:
    return {result.criterion_id: result for result in foundation_gate_report.results}


@pytest.fixture(autouse=True)
def clear_local_api_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UAA_API_LOCAL_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("UAA_API_LOCAL_BEARER", raising=False)
