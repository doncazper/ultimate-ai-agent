from typing import Any
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m166_openapi_route_failures,
)


M166_CRITERIA = {
    "m166_local_model_production_readiness_contracts",
    "m166_local_model_production_readiness_static_safety",
    "m166_local_model_production_readiness_route_boundary",
}


def test_m166_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert M166_CRITERIA.issubset(ids)


def test_m166_foundation_gate_evaluator_accepts_current_repo(
    foundation_gate_results: Any,
) -> None:
    for criterion_id in M166_CRITERIA:
        result = foundation_gate_results[criterion_id]
        assert result.status == FoundationGateStatus.passed, result.failures


def test_m166_route_boundary_rejects_production_release_execution_routes() -> None:
    failures = m166_openapi_route_failures(
        {
            "/api/manifest": {},
            "/production/authority/enable": {},
            "/production/go-live": {},
            "/production/deploy": {},
            "/production/traffic/route": {},
            "/production/rollback/execute": {},
            "/production/release-gate/apply": {},
            "/production/release-gate/run": {},
        },
        expected_path_count=8,
    )

    for forbidden in [
        "/production/authority/enable",
        "/production/go-live",
        "/production/deploy",
        "/production/traffic/route",
        "/production/rollback/execute",
        "/production/release-gate/apply",
        "/production/release-gate/run",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m166_openapi_route_failures(app.openapi().get("paths", {}))


def test_m166_static_safety_detects_unreviewed_release_gate_fragments(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    source_root.mkdir(parents=True)
    (source_root / "unsafe.py").write_text(
        "production_authority_granted=True\n"
        "raw_prompt_exported=True\n"
        "credential_material_exported=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n"
        "unreviewed_dependency_added=True\n",
        encoding="utf-8",
    )

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m166_local_model_production_readiness_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m166_local_model_production_readiness_static_safety(criterion)
    )

    assert result.status == FoundationGateStatus.failed
    assert any("production_authority_granted=True" in failure for failure in result.failures)
    assert any("raw_prompt_exported=True" in failure for failure in result.failures)
    assert any("credential_material_exported=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
    assert any("unreviewed_dependency_added=True" in failure for failure in result.failures)
