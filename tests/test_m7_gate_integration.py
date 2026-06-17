from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria


def test_foundation_gate_criteria_include_m7_policy_only_surface():
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "m7_modules_present",
        "model_router_decision_only",
        "cost_governor_blocks_over_budget",
        "m7_arbitrary_approval_ref_rejected",
        "m7_context_budget_exhaustion_blocks_route",
        "m7_soft_budget_warning_allows_route",
        "m7_hard_budget_denies_route",
        "m7_cost_warnings_visible_in_route_decision",
    }.issubset(by_id)


def test_foundation_gate_evaluator_passes_m7_policy_only_checks(foundation_gate_results):
    assert foundation_gate_results["m7_modules_present"].status == FoundationGateStatus.passed
    assert foundation_gate_results["model_router_decision_only"].status == FoundationGateStatus.passed
    assert foundation_gate_results["cost_governor_blocks_over_budget"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_arbitrary_approval_ref_rejected"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_context_budget_exhaustion_blocks_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_soft_budget_warning_allows_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_hard_budget_denies_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_cost_warnings_visible_in_route_decision"].status == FoundationGateStatus.passed


def test_m7_does_not_add_runtime_execution_integrations():
    forbidden = [
        "import openai",
        "import anthropic",
        "import requests",
        "import httpx",
        "subprocess.",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in (Path("src") / "ultimate_ai_agent" / "core").rglob("*.py"))

    for marker in forbidden:
        assert marker not in source
