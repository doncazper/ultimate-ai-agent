from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m145_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m145_enterprise_pro_safety_modes_contracts" in ids
    assert "m145_enterprise_pro_safety_modes_static_safety" in ids
    assert "m145_enterprise_pro_safety_modes_route_boundary" in ids
    assert "m145_roadmap_currentness" in ids


def test_m145_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m145_enterprise_pro_safety_modes_contracts",
        "m145_enterprise_pro_safety_modes_static_safety",
        "m145_enterprise_pro_safety_modes_route_boundary",
        "m145_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m145_route_boundary_rejects_enterprise_pro_and_billing_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/enterprise/runtime": {},
        "/enterprise/pro/enable": {},
        "/pro/runtime": {},
        "/safety-modes/enable": {},
        "/safety-modes/enforce": {},
        "/plans/enforce": {},
        "/billing/runtime": {},
        "/billing/plans": {},
        "/accounts/tenants": {},
        "/roles/runtime": {},
        "/auth/login": {},
        "/workspace/share": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m145_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/enterprise/runtime",
        "/enterprise/pro/enable",
        "/pro/runtime",
        "/safety-modes/enable",
        "/plans/enforce",
        "/billing/runtime",
        "/billing/plans",
        "/accounts/tenants",
        "/roles/runtime",
        "/auth/login",
        "/workspace/share",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m145_openapi_route_failures(app.openapi().get("paths", {}))


def test_m145_static_safety_detects_enterprise_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "enterprise_runtime_enabled=True\n"
        "pro_runtime_enabled=True\n"
        "safety_mode_runtime_enabled=True\n"
        "plan_enforcement_enabled=True\n"
        "billing_runtime_enabled=True\n"
        "billing_plan_boundary_enabled=True\n"
        "account_tenant_runtime_enabled=True\n"
        "role_runtime_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "enterprise_runtime_started=True\n"
        "plan_enforcement_performed=True\n"
        "billing_runtime_started=True\n"
        "account_tenant_runtime_started=True\n"
        "auth_runtime_started=True\n"
        "/enterprise/runtime\n"
        "/safety-modes/enable\n"
        "/plans/enforce\n"
        "/billing/runtime\n"
        "/accounts/tenants\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m145_enterprise_pro_safety_modes_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m145_enterprise_pro_safety_modes_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "enterprise_runtime_enabled=True",
        "pro_runtime_enabled=True",
        "safety_mode_runtime_enabled=True",
        "plan_enforcement_enabled=True",
        "billing_runtime_enabled=True",
        "billing_plan_boundary_enabled=True",
        "account_tenant_runtime_enabled=True",
        "role_runtime_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "enterprise_runtime_started=True",
        "plan_enforcement_performed=True",
        "billing_runtime_started=True",
        "account_tenant_runtime_started=True",
        "auth_runtime_started=True",
        "/enterprise/runtime",
        "/safety-modes/enable",
        "/plans/enforce",
        "/billing/runtime",
        "/accounts/tenants",
    ]:
        assert any(fragment in failure for failure in result.failures)
