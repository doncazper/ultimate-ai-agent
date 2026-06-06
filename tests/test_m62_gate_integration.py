from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m62_openapi_route_failures,
)


def test_m62_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m62_scoped_autonomy_session_contract_review" in ids
    assert "m62_scoped_autonomy_session_static_safety" in ids
    assert "m62_scoped_autonomy_session_route_boundary" in ids
    assert "m62_roadmap_currentness" in ids


def test_m62_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m62_scoped_autonomy_session_contract_review",
        "m62_scoped_autonomy_session_static_safety",
        "m62_scoped_autonomy_session_route_boundary",
        "m62_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m62_openapi_route_guard_denies_session_and_execution_routes() -> None:
    failures = m62_openapi_route_failures(
        {
            "/autonomy/session/start": {},
            "/autonomy/session/activate": {},
            "/autonomy/session/run": {},
            "/autonomy/session/execute": {},
            "/autonomy/session/stop": {},
            "/autonomy/execute": {},
            "/background/start": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/network/fetch": {},
            "/browser/click": {},
        }
    )

    for forbidden in [
        "/autonomy/session/start",
        "/autonomy/session/activate",
        "/autonomy/session/run",
        "/autonomy/session/execute",
        "/autonomy/session/stop",
        "/autonomy/execute",
        "/background/start",
        "/tools/execute",
        "/shell/execute",
        "/network/fetch",
        "/browser/click",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m62_openapi_route_failures(app.openapi().get("paths", {}))


def test_m62_static_gate_scans_session_enablement_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/session_enablement.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("session_start_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m62_scoped_autonomy_session_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("session_start_enabled=True" in failure for failure in result.failures)
