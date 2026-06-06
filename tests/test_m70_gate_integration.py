from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m70_openapi_route_failures,
)


def test_m70_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m70_autonomy_foundation_freeze_review" in ids
    assert "m70_autonomy_foundation_freeze_static_safety" in ids
    assert "m70_autonomy_foundation_freeze_route_boundary" in ids
    assert "m70_roadmap_currentness" in ids


def test_m70_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m70_autonomy_foundation_freeze_review",
        "m70_autonomy_foundation_freeze_static_safety",
        "m70_autonomy_foundation_freeze_route_boundary",
        "m70_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m70_openapi_route_guard_denies_autonomy_freeze_escape_routes() -> None:
    failures = m70_openapi_route_failures(
        {
            "/autonomy/freeze/activate": {},
            "/autonomy/session/start": {},
            "/autonomy/policy/activate": {},
            "/autonomy/dry-run/execute": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
        }
    )

    for forbidden in [
        "/autonomy/freeze/activate",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/autonomy/dry-run/execute",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m70_openapi_route_failures(app.openapi().get("paths", {}))


def test_m70_static_gate_scans_freeze_authority_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/autonomy_freeze_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("autonomy_foundation_authority_granted=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m70_autonomy_foundation_freeze_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("autonomy_foundation_authority_granted=True" in failure for failure in result.failures)
