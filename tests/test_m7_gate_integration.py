from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus, default_foundation_gate_criteria


def test_foundation_gate_criteria_include_m7_policy_only_surface():
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "m7_modules_present",
        "model_router_decision_only",
        "cost_governor_blocks_over_budget",
    }.issubset(by_id)


def test_foundation_gate_evaluator_passes_m7_policy_only_checks():
    report = FoundationGateEvaluator().evaluate()
    results = {result.criterion_id: result for result in report.results}

    assert results["m7_modules_present"].status == FoundationGateStatus.passed
    assert results["model_router_decision_only"].status == FoundationGateStatus.passed
    assert results["cost_governor_blocks_over_budget"].status == FoundationGateStatus.passed


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
