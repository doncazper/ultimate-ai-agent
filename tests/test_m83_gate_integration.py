from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m83_openapi_route_failures,
)


def test_m83_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m83_shell_dry_run_classifier_contract" in ids
    assert "m83_shell_dry_run_classifier_static_safety" in ids
    assert "m83_shell_dry_run_classifier_route_boundary" in ids
    assert "m83_roadmap_currentness" in ids


def test_m83_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m83_shell_dry_run_classifier_contract",
        "m83_shell_dry_run_classifier_static_safety",
        "m83_shell_dry_run_classifier_route_boundary",
        "m83_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m83_openapi_route_guard_denies_shell_dry_run_and_execution_routes() -> None:
    failures = m83_openapi_route_failures(
        {
            "/shell/dry-run/classify": {},
            "/shell/dry-run/execute": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/network/fetch/unrestricted": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/remote/execute": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        }
    )

    for forbidden in [
        "/shell/dry-run/classify",
        "/shell/dry-run/execute",
        "/commands/execute",
        "/shell/execute",
        "/process/spawn",
        "/filesystem/write",
        "/network/fetch/unrestricted",
        "/browser/click",
        "/plugins/execute",
        "/remote/execute",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m83_openapi_route_failures(app.openapi().get("paths", {}))


def test_m83_static_gate_scans_shell_dry_run_execution_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/m83_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("dry_run_execution_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m83_shell_dry_run_classifier_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("dry_run_execution_enabled=True" in failure for failure in result.failures)
