from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m113_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m113_secrets_boundary_contracts" in ids
    assert "m113_secrets_boundary_static_safety" in ids
    assert "m113_secrets_boundary_route_boundary" in ids
    assert "m113_roadmap_currentness" in ids


def test_m113_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m113_secrets_boundary_contracts",
        "m113_secrets_boundary_static_safety",
        "m113_secrets_boundary_route_boundary",
        "m113_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m113_route_boundary_rejects_secret_and_vault_runtime_routes() -> None:
    failures = gate_evaluators.m113_openapi_route_failures(
        {
            "/api/manifest": {},
            "/credentials/read": {},
            "/credentials/write": {},
            "/credentials/vault": {},
            "/secrets/read": {},
            "/secrets/write": {},
            "/identity/login": {},
            "/identity/session": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/credentials/read",
        "/credentials/write",
        "/credentials/vault",
        "/secrets/read",
        "/secrets/write",
        "/identity/login",
        "/identity/session",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m113_openapi_route_failures(app.openapi().get("paths", {}))


def test_m113_static_safety_detects_secret_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "credential_storage_enabled=True\n"
        "credential_read_enabled=True\n"
        "credential_write_enabled=True\n"
        "secret_material_access_enabled=True\n"
        "secret_export_enabled=True\n"
        "vault_runtime_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m113_secrets_boundary_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m113_secrets_boundary_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("credential_storage_enabled=True" in failure for failure in result.failures)
    assert any("credential_read_enabled=True" in failure for failure in result.failures)
    assert any("credential_write_enabled=True" in failure for failure in result.failures)
    assert any(
        "secret_material_access_enabled=True" in failure
        for failure in result.failures
    )
    assert any("secret_export_enabled=True" in failure for failure in result.failures)
    assert any("vault_runtime_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
