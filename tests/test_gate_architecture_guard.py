from pathlib import Path

from ultimate_ai_agent.core.gate.architecture import (
    GATE_TEST_IMPORT_CEILING,
    evaluate_gate_architecture,
)
from ultimate_ai_agent.core.gate.evaluator_registry import evaluator_registry


ROOT = Path(__file__).resolve().parents[1]


def test_gate_architecture_guard_accepts_current_legacy_evaluator_ceiling() -> None:
    report = evaluate_gate_architecture(ROOT)

    assert report.passed is True
    legacy = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/evaluators.py")
    )
    assert legacy.status == "legacy_facade_ceiling"
    composition = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/legacy_checks.py")
    )
    assert composition.status == "legacy_composition_ceiling"
    support = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/legacy_support.py")
    )
    assert support.status == "legacy_support_ceiling"
    legacy_parts = [
        item
        for item in report.items
        if "/legacy_check_families/part_" in item.relative_path
    ]
    assert len(legacy_parts) == 44
    assert {item.status for item in legacy_parts} == {"legacy_check_family_ceiling"}
    criteria = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/criteria.py")
    )
    assert criteria.status == "criteria_facade_ceiling"
    criteria_families = [
        item for item in report.items if "/criteria_families/" in item.relative_path
    ]
    assert len(criteria_families) == 10
    assert {item.status for item in criteria_families} == {"criteria_family_ceiling"}
    route_boundaries = next(
        item
        for item in report.items
        if item.relative_path.endswith(
            "core/gate/evaluator_modules/route_boundaries.py"
        )
    )
    assert route_boundaries.status == "route_boundary_extraction_ceiling"
    context = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/evaluation_context.py")
    )
    assert context.status == "evaluation_context_ceiling"
    assert not report.failures
    over_ceiling = {
        f"{item.relative_path} has {item.line_count} lines; ceiling is {item.line_ceiling}"
        for item in report.items
        if item.line_count > item.line_ceiling
    }
    assert over_ceiling.issubset(set(report.advisories))


def test_gate_architecture_guard_ratchets_legacy_evaluator_debt() -> None:
    evaluator_path = ROOT / "src/ultimate_ai_agent/core/gate/evaluators.py"
    text = evaluator_path.read_text(encoding="utf-8")

    assert "Path.rglob =" not in text
    assert "Path.read_text =" not in text
    assert "app.openapi =" not in text
    context_text = (
        ROOT / "src/ultimate_ai_agent/core/gate/evaluation_context.py"
    ).read_text(encoding="utf-8")
    assert "Path.rglob =" not in context_text
    assert "Path.read_text =" not in context_text
    assert "app.openapi =" not in context_text
    assert "api_openapi.verify_openapi_contract =" not in context_text
    gate_source = ROOT / "src/ultimate_ai_agent/core/gate"
    import ast

    test_import_count = 0
    for path in gate_source.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                test_import_count += sum(
                    1
                    for alias in node.names
                    if alias.name == "tests" or alias.name.startswith("tests.")
                )
            elif isinstance(node, ast.ImportFrom) and (
                node.module == "tests" or (node.module or "").startswith("tests.")
            ):
                test_import_count += 1
    assert test_import_count <= GATE_TEST_IMPORT_CEILING


def test_evaluator_registry_names_planned_split_boundaries() -> None:
    entries = evaluator_registry()
    names = {entry.name for entry in entries}

    assert "legacy_foundation_gate_evaluator" in names
    assert "route_contract_evaluators" in names
    assert "security_redaction_evaluators" in names
    assert "frontend_product_evaluators" in names
    assert "storage_backup_evaluators" in names
