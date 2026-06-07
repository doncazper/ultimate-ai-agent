from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m94_openapi_route_failures,
)


def test_m94_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m94_low_risk_browser_clicks" in ids
    assert "m94_low_risk_browser_clicks_static_safety" in ids
    assert "m94_low_risk_browser_clicks_route_boundary" in ids
    assert "m94_roadmap_currentness" in ids


def test_m94_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m94_low_risk_browser_clicks",
        "m94_low_risk_browser_clicks_static_safety",
        "m94_low_risk_browser_clicks_route_boundary",
        "m94_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m94_route_boundary_rejects_browser_click_and_sensitive_routes() -> None:
    failures = m94_openapi_route_failures(
        {
            "/api/manifest": {},
            "/browser/click": {},
            "/browser/form-submit": {},
            "/browser/download": {},
            "/browser/auth": {},
            "/autonomy/browser/click": {},
            "/tools/browser/execute": {},
            "/tools/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/browser/click",
        "/browser/form-submit",
        "/browser/download",
        "/browser/auth",
        "/autonomy/browser/click",
        "/tools/browser/execute",
        "/tools/execute",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m94_openapi_route_failures(app.openapi().get("paths", {}))


def test_m94_static_safety_detects_browser_form_enablement(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/browser"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("form_submission_allowed=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m94_low_risk_browser_clicks_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m94_low_risk_browser_clicks_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("form_submission_allowed=True" in failure for failure in result.failures)
