from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m146_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m146_billing_plan_boundary_contracts" in ids
    assert "m146_billing_plan_boundary_static_safety" in ids
    assert "m146_billing_plan_boundary_route_boundary" in ids
    assert "m146_roadmap_currentness" in ids


def test_m146_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m146_billing_plan_boundary_contracts",
        "m146_billing_plan_boundary_static_safety",
        "m146_billing_plan_boundary_route_boundary",
        "m146_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m146_route_boundary_rejects_billing_plan_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/billing/checkout": {},
        "/billing/subscriptions": {},
        "/billing/invoices": {},
        "/plans/enforce": {},
        "/plans/upgrade": {},
        "/billing/runtime": {},
        "/payments/process": {},
        "/checkout/session": {},
        "/subscriptions/manage": {},
        "/entitlements/runtime": {},
        "/account/plans": {},
        "/external-billing-provider": {},
        "/stripe": {},
        "/auth/login": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m146_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/billing/checkout",
        "/billing/subscriptions",
        "/billing/invoices",
        "/plans/enforce",
        "/plans/upgrade",
        "/billing/runtime",
        "/payments/process",
        "/checkout/session",
        "/subscriptions/manage",
        "/entitlements/runtime",
        "/account/plans",
        "/external-billing-provider",
        "/stripe",
        "/auth/login",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m146_openapi_route_failures(app.openapi().get("paths", {}))


def test_m146_static_safety_detects_payment_processing_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "payment_processing_enabled=True\n"
        "checkout_runtime_enabled=True\n"
        "subscription_management_enabled=True\n"
        "plan_enforcement_enabled=True\n"
        "billing_runtime_enabled=True\n"
        "external_billing_provider_enabled=True\n"
        "account_plan_runtime_enabled=True\n"
        "entitlement_runtime_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "payment_processing_started=True\n"
        "plan_enforcement_performed=True\n"
        "billing_runtime_started=True\n"
        "account_plan_runtime_started=True\n"
        "auth_runtime_started=True\n"
        "/billing/checkout\n"
        "/billing/subscriptions\n"
        "/plans/enforce\n"
        "/billing/runtime\n"
        "/account/plans\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m146_billing_plan_boundary_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m146_billing_plan_boundary_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "payment_processing_enabled=True",
        "checkout_runtime_enabled=True",
        "subscription_management_enabled=True",
        "plan_enforcement_enabled=True",
        "billing_runtime_enabled=True",
        "external_billing_provider_enabled=True",
        "account_plan_runtime_enabled=True",
        "entitlement_runtime_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "payment_processing_started=True",
        "plan_enforcement_performed=True",
        "billing_runtime_started=True",
        "account_plan_runtime_started=True",
        "auth_runtime_started=True",
        "/billing/checkout",
        "/billing/subscriptions",
        "/plans/enforce",
        "/billing/runtime",
        "/account/plans",
    ]:
        assert any(fragment in failure for failure in result.failures)
