from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m95_openapi_route_failures,
)


def test_m95_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m95_authless_network_tool_expansion" in ids
    assert "m95_authless_network_tool_expansion_static_safety" in ids
    assert "m95_authless_network_tool_expansion_route_boundary" in ids
    assert "m95_roadmap_currentness" in ids


def test_m95_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m95_authless_network_tool_expansion",
        "m95_authless_network_tool_expansion_static_safety",
        "m95_authless_network_tool_expansion_route_boundary",
        "m95_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m95_route_boundary_rejects_network_and_sensitive_routes() -> None:
    failures = m95_openapi_route_failures(
        {
            "/api/manifest": {},
            "/network/get": {},
            "/network/fetch": {},
            "/network/post": {},
            "/network/auth": {},
            "/network/account": {},
            "/network/download": {},
            "/tools/network/execute": {},
            "/browser/form-submit": {},
            "/tools/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=12,
    )

    for forbidden in [
        "/network/get",
        "/network/fetch",
        "/network/post",
        "/network/auth",
        "/network/account",
        "/network/download",
        "/tools/network/execute",
        "/browser/form-submit",
        "/tools/execute",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m95_openapi_route_failures(app.openapi().get("paths", {}))


def test_m95_static_safety_detects_authenticated_network_enablement(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/network"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("authenticated_network_allowed=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m95_authless_network_tool_expansion_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m95_authless_network_tool_expansion_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("authenticated_network_allowed=True" in failure for failure in result.failures)
