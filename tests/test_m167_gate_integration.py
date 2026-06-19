from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M167_OPENAPI_PATH_COUNT,
    FoundationGateEvaluator,
    TASK_DECOMPOSITION_CANONICAL_ROUTES,
    m167_openapi_route_failures,
)


M167_CRITERIA = {
    "m167_live_model_production_hardening_contracts",
    "m167_live_model_production_hardening_static_safety",
    "m167_live_model_production_hardening_route_boundary",
}


def test_m167_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert M167_CRITERIA.issubset(ids)


def test_m167_foundation_gate_evaluator_accepts_current_repo(
    foundation_gate_results,
) -> None:
    for criterion_id in M167_CRITERIA:
        result = foundation_gate_results[criterion_id]
        assert result.status == FoundationGateStatus.passed, result.failures


def test_m167_route_boundary_rejects_live_hardening_execution_routes() -> None:
    failures = m167_openapi_route_failures(
        {
            "/api/manifest": {},
            "/production/live-model-hardening/run": {},
            "/production/model-matrix/run": {},
            "/production/openwebui/e2e/run": {},
            "/production/load-soak/run": {},
            "/production/llama-server/install": {},
            "/production/model-selection/calibrate": {},
            "/production/tuning/apply": {},
        },
        expected_path_count=8,
    )

    for forbidden in [
        "/production/live-model-hardening/run",
        "/production/model-matrix/run",
        "/production/openwebui/e2e/run",
        "/production/load-soak/run",
        "/production/llama-server/install",
        "/production/model-selection/calibrate",
        "/production/tuning/apply",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m167_openapi_route_failures(app.openapi().get("paths", {}))


def test_m167_route_boundary_allows_exact_task_decomposition_canonical_surface() -> None:
    baseline_paths = {
        f"/m167-contract-path-{index}"
        for index in range(EXPECTED_M167_OPENAPI_PATH_COUNT)
    }
    current_paths = baseline_paths | set(TASK_DECOMPOSITION_CANONICAL_ROUTES)

    assert m167_openapi_route_failures(current_paths) == []

    failures = m167_openapi_route_failures(
        current_paths | {"/task-decomposition/unreviewed-route"}
    )

    assert any("OpenAPI path count" in failure for failure in failures)


def test_m167_static_safety_detects_unreviewed_live_hardening_fragments(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    source_root.mkdir(parents=True)
    (source_root / "unsafe.py").write_text(
        "new_production_authority_granted=True\n"
        "runtime_execution_started_by_report=True\n"
        "model_download_started_by_report=True\n"
        "raw_prompt_exported=True\n"
        "credential_material_exported=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n"
        "dependency_added=True\n",
        encoding="utf-8",
    )

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m167_live_model_production_hardening_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m167_live_model_production_hardening_static_safety(criterion)
    )

    assert result.status == FoundationGateStatus.failed
    assert any("new_production_authority_granted=True" in failure for failure in result.failures)
    assert any("runtime_execution_started_by_report=True" in failure for failure in result.failures)
    assert any("model_download_started_by_report=True" in failure for failure in result.failures)
    assert any("raw_prompt_exported=True" in failure for failure in result.failures)
    assert any("credential_material_exported=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
    assert any("dependency_added=True" in failure for failure in result.failures)
